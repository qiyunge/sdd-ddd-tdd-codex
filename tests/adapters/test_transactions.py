import sqlite3

import pytest

from enrollment.adapters.persistence.sqlite import Session, StorageFailure
from enrollment.domain.models import Enrollment
from enrollment.domain.values import CourseId, StudentId
from tests.support.database import rows

PAIR = Enrollment(StudentId("s"), CourseId("c"))


def test_commit_and_reconstitution(database):
    s = Session(database)
    s.add(PAIR)
    s.commit()
    s.close()
    assert rows(database) == [("s", "c")]
    s = Session(database)
    try:
        assert s.enrollment(StudentId("s"), CourseId("c")) == PAIR
    finally:
        s.close()


def test_rollback(database):
    s = Session(database)
    s.add(PAIR)
    s.close()
    assert rows(database) == []


def test_early_writer_lock(database):
    s = Session(database)
    try:
        with pytest.raises(StorageFailure):
            Session(database, timeout=0.01)
    finally:
        s.close()


def test_explicit_rollback_and_sql_trace(database):
    session = Session(database)
    trace = []
    session.connection.set_trace_callback(trace.append)
    assert session.connection.autocommit is True
    assert session.connection.in_transaction is True
    assert session.connection.execute("PRAGMA busy_timeout").fetchone() == (5000,)
    session.add(PAIR)
    session.rollback()
    session.close()
    assert "ROLLBACK" in trace
    assert rows(database) == []


def test_non_pair_unique_is_storage_failure(database):
    from enrollment.application.contracts import UniqueConflict

    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO courses VALUES ('other')")
        db.execute("INSERT INTO enrollments VALUES ('s','other')")
        db.execute(
            "CREATE UNIQUE INDEX legacy_unique_student ON enrollments(student_id)"
        )
    session = Session(database)
    try:
        with pytest.raises(StorageFailure) as failure:
            session.add(PAIR)
        assert not isinstance(failure.value, UniqueConflict)
    finally:
        session.close()


def test_pair_unique_and_foreign_key_classification(tmp_path):
    from enrollment.adapters.persistence.sqlite import initialize
    from enrollment.application.contracts import UniqueConflict

    path = tmp_path / "real.db"
    initialize(path)
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO students VALUES ('s','p')")
        db.execute("INSERT INTO courses VALUES ('c')")
        db.execute("INSERT INTO enrollments VALUES ('s','c')")
    session = Session(path)
    try:
        with pytest.raises(UniqueConflict):
            session.add(PAIR)
        with pytest.raises(StorageFailure) as failure:
            session.add(Enrollment(StudentId("missing"), CourseId("c")))
        assert not isinstance(failure.value, UniqueConflict)
    finally:
        session.close()
