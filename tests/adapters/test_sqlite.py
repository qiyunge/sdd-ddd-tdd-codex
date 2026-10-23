import sqlite3
from unittest.mock import patch

import pytest

from enrollment.adapters.persistence.sqlite import (
    DataIntegrityFailure,
    Session,
    StorageFailure,
    connect,
    decode,
)
from enrollment.domain.models import (
    Course,
    Programme,
    ProgrammeCourseOffering,
    Student,
)
from enrollment.domain.values import (
    CourseId,
    ProgrammeId,
    SavedVersion,
    StudentEmail,
    StudentId,
    StudentName,
    SubjectId,
)


@pytest.mark.parametrize(
    "kind,valid,invalid",
    [
        (StudentId, " s ", ""),
        (ProgrammeId, " p ", None),
        (CourseId, " c ", 1),
        (SubjectId, " subject ", b"subject"),
        (StudentName, " Alex ", "\u00a0"),
        (StudentEmail, "Straße@Example.com", ""),
        (SavedVersion, 9223372036854775807, True),
    ],
)
def test_persisted_values_use_shared_validation(kind, valid, invalid):
    with patch.object(kind, "create", wraps=kind.create) as create:
        value = decode(kind, valid)
        assert isinstance(value, kind)
        assert value.value == valid
        create.assert_called_once_with(valid)

    with patch.object(kind, "create", wraps=kind.create) as create:
        with pytest.raises(DataIntegrityFailure):
            decode(kind, invalid)
        create.assert_called_once_with(invalid)


def test_reads(database):
    s = Session(database)
    try:
        assert s.student(StudentId("s")) == Student.create(
            StudentId("s"),
            ProgrammeId("p"),
            StudentName("Alex"),
            StudentEmail("alex@example.com"),
        )
        assert s.student(StudentId("absent")) is None
        assert s.programme(ProgrammeId("p")) == Programme.create(ProgrammeId("p"))
        assert s.programme(ProgrammeId("absent")) is None
        assert s.course(CourseId("c")) == Course.create(CourseId("c"))
        assert s.course(CourseId("absent")) is None
        assert s.offering(ProgrammeId("p"), CourseId("c")) == (
            ProgrammeCourseOffering.create(ProgrammeId("p"), CourseId("c"))
        )
        assert s.offering(ProgrammeId("p"), CourseId("absent")) is None
        assert s.enrollment(StudentId("s"), CourseId("c")) is None
    finally:
        s.close()


def test_valid_enrollment_restores_after_offering_removed(database):
    from enrollment.domain.models import Enrollment

    with connect(database) as c:
        c.execute("INSERT INTO enrollments VALUES ('s','c')")
        c.execute("DELETE FROM programme_course_offerings")
    s = Session(database)
    try:
        assert s.enrollment(StudentId("s"), CourseId("c")) == Enrollment.create(
            StudentId("s"), CourseId("c")
        )
        assert s.offering(ProgrammeId("p"), CourseId("c")) is None
        assert s.student(StudentId("absent")) is None
    finally:
        s.close()


@pytest.mark.parametrize(
    "column,value", [("name", " "), ("name", "\u00a0"), ("email", "")]
)
def test_invalid_persisted_student_text(database, column, value):
    with connect(database) as c:
        c.execute("DROP TRIGGER students_saved_version_guard")
        c.execute("PRAGMA ignore_check_constraints=ON")
        c.execute(f"UPDATE students SET {column}=? WHERE student_id='s'", (value,))
    s = Session(database)
    try:
        with pytest.raises(DataIntegrityFailure):
            s.student(StudentId("s"))
    finally:
        s.close()


def test_dangling_programme_remains_representable(tmp_path):
    from enrollment.adapters.persistence.sqlite import initialize

    path = tmp_path / "db"
    initialize(path)
    with connect(path) as c:
        c.execute(
            "INSERT INTO students(student_id,programme_id,name,email,saved_version) VALUES ('s','missing','Alex','alex@example.com',1)"
        )
    s = Session(path)
    try:
        student = s.student(StudentId("s"))
        assert student is not None
        assert student.programme_id.value == "missing"
        assert student.name.value == "Alex"
    finally:
        s.close()


def test_corrupt_student_is_sanitized_persistence_failure(database):
    from enrollment.application.contracts import Command, Failure
    from enrollment.application.enroll import enroll
    from tests.application.test_identity import Verifier

    with connect(database) as c:
        c.execute("DROP TRIGGER students_saved_version_guard")
        c.execute("PRAGMA ignore_check_constraints=ON")
        c.execute("UPDATE students SET programme_id='' WHERE student_id='s'")
    assert (
        enroll(Command("s", "c", "s"), Verifier("s"), lambda: Session(database))
        == Failure.PERSISTENCE_FAILURE
    )
    with connect(database) as c:
        assert c.execute("SELECT student_id FROM students").fetchone() == ("s",)


def test_corrupt_row(database):
    with connect(database) as c:
        c.execute("DROP TRIGGER students_saved_version_guard")
        c.execute("PRAGMA ignore_check_constraints=ON")
        c.execute("UPDATE students SET programme_id='' WHERE student_id='s'")
    s = Session(database)
    try:
        with pytest.raises(DataIntegrityFailure):
            s.student(StudentId("s"))
    finally:
        s.close()


@pytest.mark.parametrize("value", [None, "", b"blob"])
@pytest.mark.parametrize(
    "table,columns",
    [
        ("programmes", ["programme_id"]),
        ("students", ["student_id", "programme_id"]),
        ("courses", ["course_id"]),
        ("programme_course_offerings", ["programme_id", "course_id"]),
        ("enrollments", ["student_id", "course_id"]),
    ],
)
def test_schema_id_constraints(tmp_path, table, columns, value):
    from enrollment.adapters.persistence.sqlite import initialize

    path = tmp_path / "schema.db"
    initialize(path)
    with connect(path) as db:
        # No FK configuration here: test each column's own NOT NULL/TEXT/nonempty constraint.
        for column in columns:
            data = {key: "valid" for key in columns}
            data[column] = value
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                    tuple(data.values()),
                )


def test_restrictive_schema_and_pair_uniqueness(tmp_path):
    from enrollment.adapters.persistence.sqlite import initialize

    path = tmp_path / "schema.db"
    initialize(path)
    with connect(path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("INSERT INTO programmes VALUES ('p')")
        db.execute(
            "INSERT INTO students(student_id,programme_id,name,email,saved_version) VALUES ('s','dangling','Alex','alex@example.com',1)"
        )
        db.execute("INSERT INTO courses VALUES ('c')")
        db.execute("INSERT INTO programme_course_offerings VALUES ('p','c')")
        db.execute("INSERT INTO enrollments VALUES ('s','c')")
        for sql in [
            "INSERT INTO enrollments VALUES ('s','c')",
            "INSERT INTO programme_course_offerings VALUES ('p','c')",
            "DELETE FROM students WHERE student_id='s'",
            "DELETE FROM courses WHERE course_id='c'",
        ]:
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(sql)
        assert db.execute("SELECT * FROM enrollments").fetchall() == [("s", "c")]


def test_parameter_binding_and_thread_ownership(database):
    from concurrent.futures import ThreadPoolExecutor

    session = Session(database)
    try:
        assert session.student(StudentId("s' OR 1=1 --")) is None
        with ThreadPoolExecutor(1) as workers:
            with pytest.raises(StorageFailure):
                workers.submit(session.student, StudentId("s")).result(2)
    finally:
        session.close()
