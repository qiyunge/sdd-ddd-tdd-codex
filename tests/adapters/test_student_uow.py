import sqlite3

import pytest

from enrollment.adapters.persistence.sqlite import (
    Session,
    StudentSession,
    connect,
    initialize,
)
from enrollment.application.contracts import StorageFailure
from enrollment.application.student_contracts import EmailKeyConflict, StudentSnapshot
from enrollment.domain.values import ProgrammeId, StudentEmail, StudentId, StudentName


def create(session, identity="s", email="Alex@Example.com"):
    return session.create_student(
        StudentId.create(identity),
        ProgrammeId.create("p"),
        StudentName.create("Alex"),
        StudentEmail.create(email),
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
    assert isinstance(create(session), StudentSnapshot)
    session.commit()
    session.close()
    session = StudentSession(path)
    try:
        assert session.email_owner("alex@example.com") == StudentId.create("s")
        assert create(session, "other", "aLEX@example.COM") == EmailKeyConflict
    finally:
        session.close()
    initialize(path)
    with connect(path) as db:
        for value in [None, b"blob", "", " \t\n", "\u00a0"]:
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO students VALUES ('bad','p',?,'unused',1)", (value,)
                )
    with sqlite3.connect(path) as db:
        with pytest.raises(sqlite3.OperationalError):
            db.execute("INSERT INTO students VALUES ('bad','p','Bad','bad',1)")


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
    path = tmp_path / "db"
    initialize(path)
    session = StudentSession(path)
    try:
        pending = create(session)
        assert isinstance(pending, StudentSnapshot), (
            "Repository creation returns an explicit pending snapshot"
        )
        assert pending.saved_version.value == 1
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


@pytest.mark.parametrize("corruption", ["legacy", "guard", "constraint", "stored"])
def test_version_schema_refusal_is_byte_preserving(tmp_path, corruption):
    path = tmp_path / "db"
    initialize(path)
    with connect(path) as db:
        sql = db.execute(
            "SELECT sql FROM sqlite_master WHERE name='students'"
        ).fetchone()[0]
        assert "saved_version" in sql, (
            "Student schema must contain constrained saved versions"
        )
        if corruption == "guard":
            db.execute("DROP TRIGGER students_saved_version_guard")
        elif corruption in ("legacy", "constraint"):
            db.execute("PRAGMA writable_schema=ON")
            replacement = (
                sql.replace("saved_version INTEGER NOT NULL", "saved_version INTEGER")
                if corruption == "constraint"
                else sql.replace("saved_version", "old_version")
            )
            db.execute(
                "UPDATE sqlite_master SET sql=? WHERE name='students'", (replacement,)
            )
        else:
            db.execute("PRAGMA ignore_check_constraints=ON")
            db.execute(
                "INSERT INTO students(student_id,programme_id,name,email,saved_version) VALUES ('s','p','Alex','a@b',0)"
            )
    before = path.read_bytes()
    with pytest.raises(StorageFailure):
        initialize(path)
    assert path.read_bytes() == before


def test_fresh_version_constraints_and_guard(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    with connect(path) as db:
        for raw in (None, 0, -1, 1.5, "invalid", b"blob"):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO students(student_id,programme_id,name,email,saved_version) VALUES ('s','p','Alex','a@b',?)",
                    (raw,),
                )
        db.execute(
            "INSERT INTO students(student_id,programme_id,name,email,saved_version) VALUES ('s','p','Alex','a@b',1)"
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE students SET name='New'")
        db.execute("UPDATE students SET name='New',saved_version=saved_version+1")
        assert db.execute("SELECT name,saved_version FROM students").fetchone() == (
            "New",
            2,
        )
    initialize(path)


def test_conditional_write_guards_identity_version_and_full_state(tmp_path):
    from enrollment.domain.values import SavedVersion

    path = tmp_path / "db"
    initialize(path)
    session = StudentSession(path)
    create(session)
    session.commit()
    session.close()
    session = StudentSession(path)
    trace = []
    session.connection.set_trace_callback(trace.append)
    try:
        pending = session.replace_student(
            StudentId.create("s"),
            ProgrammeId.create("new"),
            StudentName.create("New"),
            StudentEmail.create("new@example.com"),
            SavedVersion.create(1),
        )
        assert pending.saved_version.value == 2
        assert pending.student.name.value == "New"
        update = next(sql for sql in trace if sql.startswith("UPDATE students"))
        assert "student_id='s'" in update and "saved_version=1" in update
        session.commit()
    finally:
        session.close()
    with connect(path) as db:
        assert db.execute(
            "SELECT programme_id,name,email,saved_version FROM students"
        ).fetchone() == ("new", "New", "new@example.com", 2)


def test_defensive_zero_row_conflict_and_exhaustion(tmp_path):
    from enrollment.application.student_contracts import VersionConflict
    from enrollment.domain.values import SavedVersion

    path = tmp_path / "db"
    initialize(path)
    with connect(path) as db:
        db.execute(
            "INSERT INTO students VALUES ('s','p','Alex','a@b',9223372036854775807)"
        )
    session = StudentSession(path)
    try:
        with pytest.raises(StorageFailure):
            session.replace_student(
                StudentId.create("s"),
                ProgrammeId.create("p"),
                StudentName.create("New"),
                StudentEmail.create("a@b"),
                SavedVersion.create(9223372036854775807),
            )
    finally:
        session.close()
    with connect(path) as db:
        assert db.execute("SELECT name,saved_version FROM students").fetchone() == (
            "Alex",
            9223372036854775807,
        )
    other = tmp_path / "other"
    initialize(other)
    session = StudentSession(other)
    create(session)
    session.commit()
    session.close()
    session = StudentSession(other)
    real = session.connection

    class ZeroRow:
        rowcount = 0

        def __getattr__(self, key):
            return getattr(real, key)

        def execute(self, sql, *args):
            return (
                self if sql.startswith("UPDATE students") else real.execute(sql, *args)
            )

    session.connection = ZeroRow()
    try:
        assert (
            session.replace_student(
                StudentId.create("s"),
                ProgrammeId.create("p"),
                StudentName.create("New"),
                StudentEmail.create("a@b"),
                SavedVersion.create(1),
            )
            == VersionConflict
        )
    finally:
        session.close()
