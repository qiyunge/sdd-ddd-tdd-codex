"""Real SQLite proves confirmation and atomicity; pure Domain tests do not."""

import pytest

from enrollment.adapters.persistence.sqlite import Session, connect
from enrollment.application.contracts import PairConflict, StorageFailure
from enrollment.domain.models import Enrollment
from enrollment.domain.outcomes import Rejection
from enrollment.domain.values import CourseId, StudentId
from tests.support.database import rows


def test_insert_acknowledged_before_factory_and_no_partial_commit(
    database, monkeypatch
):
    session = Session(database)
    original = Enrollment.create
    observed = []

    def factory(student, course):
        observed.append(
            session.connection.execute(
                "SELECT student_id,course_id FROM enrollments"
            ).fetchall()
        )
        assert rows(database) == [], "Repository must not commit any part of the UoW"
        return original(student, course)

    monkeypatch.setattr(Enrollment, "create", staticmethod(factory))
    try:
        pending = session.create_enrollment(StudentId.create("s"), CourseId.create("c"))
        assert observed == [[("s", "c")]], "INSERT must precede Entity factory"
        assert isinstance(pending, Enrollment)
        assert pending.student_id.value == "s" and pending.course_id.value == "c"
        session.connection.execute("INSERT INTO courses VALUES ('following')")
        assert rows(database) == []
    finally:
        session.close()
    assert rows(database) == []
    with connect(database) as db:
        assert (
            db.execute(
                "SELECT course_id FROM courses WHERE course_id='following'"
            ).fetchone()
            is None
        )


@pytest.mark.parametrize("fault", ["rejection", "exception"])
def test_factory_failure_cancels_entire_enclosing_transaction(
    database, monkeypatch, fault
):
    session = Session(database)
    session.connection.execute("INSERT INTO courses VALUES ('preceding')")

    def factory(student, course):
        assert session.connection.execute("SELECT * FROM enrollments").fetchall() == [
            ("s", "c")
        ]
        if fault == "exception":
            raise RuntimeError("factory defect")
        return Rejection.COURSE_NOT_OFFERED

    monkeypatch.setattr(Enrollment, "create", staticmethod(factory))
    try:
        if fault == "exception":
            with pytest.raises(RuntimeError, match="factory defect"):
                session.create_enrollment(StudentId.create("s"), CourseId.create("c"))
        else:
            assert (
                session.create_enrollment(StudentId.create("s"), CourseId.create("c"))
                == Rejection.COURSE_NOT_OFFERED
            )
        with pytest.raises(StorageFailure):
            session.commit()
    finally:
        session.close()
    assert rows(database) == []
    with connect(database) as db:
        assert (
            db.execute(
                "SELECT course_id FROM courses WHERE course_id='preceding'"
            ).fetchone()
            is None
        )


def test_duplicate_pair_preserves_confirmed_record(database):
    with connect(database) as db:
        db.execute("INSERT INTO enrollments VALUES ('s','c')")
    session = Session(database)
    try:
        assert (
            session.create_enrollment(StudentId.create("s"), CourseId.create("c"))
            == PairConflict
        )
    finally:
        session.close()
    assert rows(database) == [("s", "c")]


def test_failed_insert_cancels_preceding_writes(database):
    session = Session(database)
    session.connection.execute("INSERT INTO courses VALUES ('preceding')")
    try:
        with pytest.raises(StorageFailure):
            session.create_enrollment(StudentId.create("missing"), CourseId.create("c"))
        with pytest.raises(StorageFailure):
            session.commit()
    finally:
        session.close()
    with connect(database) as db:
        assert (
            db.execute(
                "SELECT course_id FROM courses WHERE course_id='preceding'"
            ).fetchone()
            is None
        )


@pytest.mark.parametrize("fault", ["rejection", "exception"])
def test_student_factory_failure_rolls_back_whole_uow(database, monkeypatch, fault):
    from enrollment.adapters.persistence.sqlite import StudentSession
    from enrollment.domain.models import Student
    from enrollment.domain.outcomes import InvalidStudentDetails
    from enrollment.domain.values import ProgrammeId, StudentEmail, StudentName

    session = StudentSession(database)
    session.create_course(CourseId.create("preceding"))

    def factory(*args):
        assert session.connection.execute(
            "SELECT student_id FROM students WHERE student_id='new'"
        ).fetchone() == ("new",)
        if fault == "exception":
            raise RuntimeError("Domain defect")
        return InvalidStudentDetails("name")

    monkeypatch.setattr(Student, "create", staticmethod(factory))
    try:
        if fault == "exception":
            with pytest.raises(RuntimeError, match="Domain defect"):
                session.create_student(
                    StudentId.create("new"),
                    ProgrammeId.create("p"),
                    StudentName.create("New"),
                    StudentEmail.create("new@example.com"),
                )
        else:
            assert session.create_student(
                StudentId.create("new"),
                ProgrammeId.create("p"),
                StudentName.create("New"),
                StudentEmail.create("new@example.com"),
            ) == InvalidStudentDetails("name")
        with pytest.raises(StorageFailure):
            session.commit()
    finally:
        session.close()
    with connect(database) as db:
        assert db.execute("SELECT student_id FROM students").fetchall() == [("s",)]
        assert db.execute("SELECT course_id FROM courses").fetchall() == [("c",)]
