import re
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
        assert s.student(StudentId.create("s")) == Student.create(
            StudentId.create("s"),
            ProgrammeId.create("p"),
            StudentName.create("Alex"),
            StudentEmail.create("alex@example.com"),
        )
        assert s.student(StudentId.create("absent")) is None
        assert s.programme(ProgrammeId.create("p")) == Programme.create(
            ProgrammeId.create("p")
        )
        assert s.programme(ProgrammeId.create("absent")) is None
        assert s.course(CourseId.create("c")) == Course.create(CourseId.create("c"))
        assert s.course(CourseId.create("absent")) is None
        assert s.offering(ProgrammeId.create("p"), CourseId.create("c")) == (
            ProgrammeCourseOffering.create(
                ProgrammeId.create("p"), CourseId.create("c")
            )
        )
        assert s.offering(ProgrammeId.create("p"), CourseId.create("absent")) is None
        assert s.enrollment(StudentId.create("s"), CourseId.create("c")) is None
    finally:
        s.close()


def test_valid_enrollment_restores_after_offering_removed(database):
    from enrollment.domain.models import Enrollment

    with connect(database) as c:
        c.execute("INSERT INTO enrollments VALUES ('s','c')")
        c.execute("DELETE FROM programme_course_offerings")
    s = Session(database)
    try:
        assert s.enrollment(
            StudentId.create("s"), CourseId.create("c")
        ) == Enrollment.create(StudentId.create("s"), CourseId.create("c"))
        assert s.offering(ProgrammeId.create("p"), CourseId.create("c")) is None
        assert s.student(StudentId.create("absent")) is None
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
            s.student(StudentId.create("s"))
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
        student = s.student(StudentId.create("s"))
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
            s.student(StudentId.create("s"))
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
            if table == "students":
                data.update(name="Alex", email="alex@example.com", saved_version=1)
            data[column] = value
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    f"INSERT INTO {table} ({','.join(data)}) VALUES ({','.join('?' for _ in data)})",
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
        assert session.student(StudentId.create("s' OR 1=1 --")) is None
        with ThreadPoolExecutor(1) as workers:
            with pytest.raises(StorageFailure):
                workers.submit(session.student, StudentId.create("s")).result(2)
    finally:
        session.close()


@pytest.mark.parametrize("raw", ["\0", "\0key", "key\0suffix"])
def test_repository_nul_identifiers_round_trip(tmp_path, raw):
    from enrollment.adapters.persistence.sqlite import StudentSession, initialize
    from enrollment.application.student_contracts import StudentSnapshot
    from enrollment.domain.models import Enrollment

    path = tmp_path / "db"
    initialize(path)
    programme = ProgrammeId.create(raw)
    course = CourseId.create(raw)
    student = StudentId.create(raw)
    session = StudentSession(path)
    try:
        assert session.create_programme(programme).programme_id.value == raw
        assert session.create_course(course).course_id.value == raw
        offering = session.create_offering(programme, course)
        assert offering.programme_id.value == offering.course_id.value == raw
        saved = session.create_student(
            student,
            programme,
            StudentName.create("Alex"),
            StudentEmail.create("alex@example.com"),
        )
        assert isinstance(saved, StudentSnapshot)
        assert saved.student.student_id.value == raw
        assert saved.student.programme_id.value == raw
        assert saved.saved_version.value == 1
        enrollment = session.create_enrollment(student, course)
        assert isinstance(enrollment, Enrollment)
        assert enrollment.student_id.value == enrollment.course_id.value == raw
        session.commit()
    finally:
        session.close()
    initialize(path)  # Corrected schema remains compatible and idempotent.
    session = StudentSession(path)
    try:
        assert session.programme(programme).programme_id.value == raw
        assert session.course(course).course_id.value == raw
        assert session.offering(programme, course) == offering
        assert session.snapshot(student) == saved
        assert session.enrollment(student, course) == enrollment
        # Values sharing the prefix before NUL still represent distinct keys.
        assert session.create_course(
            CourseId.create(raw + "other")
        ).course_id.value == (raw + "other")
        assert session.course(course).course_id.value == raw
        session.commit()
    finally:
        session.close()


def test_pre_nul_fix_schema_is_refused_without_changes(tmp_path):
    from importlib.resources import files

    from enrollment.adapters.persistence.sqlite import initialize

    path = tmp_path / "old.db"
    schema = files("enrollment.adapters.persistence").joinpath("schema.sql").read_text()
    old_schema = re.sub(r"length\(CAST\((\w+) AS BLOB\)\)", r"length(\1)", schema)
    with connect(path) as db:
        db.executescript(old_schema)
        db.execute("INSERT INTO programmes VALUES ('preserved')")
    before = path.read_bytes()
    with pytest.raises(StorageFailure, match="incompatible schema"):
        initialize(path)
    assert path.read_bytes() == before
