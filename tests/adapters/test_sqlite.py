import sqlite3

import pytest

from enrollment.adapters.persistence.sqlite import Session, StorageFailure
from enrollment.domain.models import (
    Course,
    Programme,
    ProgrammeCourseOffering,
    Student,
)
from enrollment.domain.values import CourseId, ProgrammeId, StudentId


def test_reads(database):
    s = Session(database)
    try:
        assert s.student(StudentId("s")) == Student(StudentId("s"), ProgrammeId("p"))
        assert s.student(StudentId("absent")) is None
        assert s.programme(ProgrammeId("p")) == Programme(ProgrammeId("p"))
        assert s.programme(ProgrammeId("absent")) is None
        assert s.course(CourseId("c")) == Course(CourseId("c"))
        assert s.course(CourseId("absent")) is None
        assert s.offering(ProgrammeId("p"), CourseId("c")) == ProgrammeCourseOffering(
            ProgrammeId("p"), CourseId("c")
        )
        assert s.offering(ProgrammeId("p"), CourseId("absent")) is None
        assert s.enrollment(StudentId("s"), CourseId("c")) is None
    finally:
        s.close()


def test_corrupt_row(database):
    with sqlite3.connect(database) as c:
        c.execute("UPDATE students SET programme_id='' WHERE student_id='s'")
    s = Session(database)
    try:
        with pytest.raises(StorageFailure):
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
    with sqlite3.connect(path) as db:
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
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("INSERT INTO programmes VALUES ('p')")
        db.execute("INSERT INTO students VALUES ('s','dangling')")
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
