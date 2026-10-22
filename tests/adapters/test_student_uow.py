import sqlite3

import pytest

from enrollment.adapters.persistence.sqlite import (
    Session,
    StudentSession,
    connect,
    initialize,
)
from enrollment.application.contracts import StorageFailure
from enrollment.application.student_contracts import EmailKeyConflict, Saved
from enrollment.domain.models import Student
from enrollment.domain.values import ProgrammeId, StudentEmail, StudentId, StudentName


def candidate(identity="s", email="Alex@Example.com"):
    return Student(
        StudentId(identity), ProgrammeId("p"), StudentName("Alex"), StudentEmail(email)
    )


def test_database_functions_delegate_domain(tmp_path, monkeypatch):
    from enrollment.domain import values

    calls = []
    original = values.StudentEmail.create

    def create(raw):
        calls.append(raw)
        return original(raw)

    monkeypatch.setattr(values.StudentEmail, "create", create)
    with connect(tmp_path / "db") as db:
        assert (
            db.execute("SELECT email_key(?)", ("Straße@Example.com",)).fetchone()[0]
            == "strasse@example.com"
        )
    assert calls == ["Straße@Example.com"], "database key must use Domain comparison"


def test_converter_programming_error_propagates(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    session = Session(path)

    def broken(row):
        raise ValueError("converter defect")

    try:
        with pytest.raises(ValueError, match="converter defect"):
            session._read("SELECT 'data'", (), broken)
    finally:
        session.close()


def test_domain_backed_constraints_and_email_conflict(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    session = StudentSession(path)
    assert session.save(candidate(), False) == Saved
    session.commit()
    session.close()
    session = StudentSession(path)
    try:
        assert session.email_owner("alex@example.com") == StudentId("s")
        assert (
            session.save(candidate("other", "aLEX@example.COM"), False)
            == EmailKeyConflict
        )
    finally:
        session.close()
    initialize(path)
    with connect(path) as db:
        for value in [None, b"blob", "", " \t\n", "\u00a0"]:
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO students VALUES ('bad','p',?,'unused')", (value,)
                )
    with sqlite3.connect(path) as db:
        with pytest.raises(sqlite3.OperationalError):
            db.execute("INSERT INTO students VALUES ('bad','p','Bad','bad')")


def test_legacy_refused_unchanged(tmp_path):
    path = tmp_path / "db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE students(student_id TEXT, programme_id TEXT)")
        db.execute("INSERT INTO students VALUES ('s','p')")
    before = path.read_bytes()
    with pytest.raises(StorageFailure, match="Legacy"):
        initialize(path)
    assert path.read_bytes() == before


def test_student_write_success_is_explicit(tmp_path):
    from enrollment.application import student_contracts

    path = tmp_path / "db"
    initialize(path)
    session = StudentSession(path)
    try:
        assert session.save(candidate(), False) == getattr(
            student_contracts, "Saved", "SAVED"
        ), "successful port writes return an explicit Saved outcome"
    finally:
        session.close()


def test_session_close_preserves_rollback_failure(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    session = Session(path)
    real = session.connection

    class Faults:
        in_transaction = True

        def execute(self, sql):
            raise sqlite3.OperationalError("primary rollback")

        def close(self):
            real.close()
            raise sqlite3.OperationalError("secondary close")

    session.connection = Faults()
    with pytest.raises(StorageFailure) as caught:
        session.close()
    assert str(caught.value.__cause__) == "primary rollback", (
        "secondary cleanup must not mask primary rollback failure"
    )
