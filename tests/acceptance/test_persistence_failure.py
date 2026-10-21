import sqlite3

import pytest

from enrollment.adapters.persistence import sqlite as adapter
from enrollment.application.contracts import StorageFailure
from enrollment.bootstrap import create_app
from tests.acceptance.test_enrollment import request
from tests.support.database import rows


@pytest.mark.parametrize(
    "point,committed",
    [
        ("insert", False),
        ("commit", False),
        ("ambiguous", True),
        ("rollback", False),
        ("close", True),
    ],
)
def test_faults(database, monkeypatch, point, committed):
    original_connect = sqlite3.connect

    class Connection:
        def __init__(self, real):
            self.real = real

        @property
        def in_transaction(self):
            return self.real.in_transaction

        def execute(self, sql, *args):
            if point == "insert" and sql.startswith("INSERT"):
                raise sqlite3.OperationalError("SQL secret")
            if point == "commit" and sql == "COMMIT":
                raise sqlite3.OperationalError("SQL secret")
            if point == "rollback" and sql == "ROLLBACK":
                raise sqlite3.OperationalError("SQL secret")
            result = self.real.execute(sql, *args)
            if point == "ambiguous" and sql == "COMMIT":
                raise sqlite3.OperationalError("connection lost")
            return result

        def close(self):
            self.real.close()
            if point == "close":
                raise sqlite3.OperationalError("close secret")

    with monkeypatch.context() as patch:
        patch.setattr(
            adapter.sqlite3,
            "connect",
            lambda *a, **kw: Connection(original_connect(*a, **kw)),
        )
        if point == "rollback":
            patch.setattr(
                adapter.Session,
                "add",
                lambda self, e: (_ for _ in ()).throw(StorageFailure()),
            )
        result = request(create_app(database, lambda c: c))
    assert result["data"]["enrollCourse"]["failureReason"] == "PERSISTENCE_FAILURE"
    assert "secret" not in str(result)
    assert rows(database) == ([("s", "c")] if committed else [])


def test_lock_failure(database):
    locked = adapter.Session(database)
    try:
        from enrollment.application.contracts import Command, Failure
        from enrollment.application.enroll import enroll
        from tests.application.test_identity import Verifier

        assert (
            enroll(
                Command("s", "c", "s"),
                Verifier("s"),
                lambda: adapter.Session(database, timeout=0.01),
            )
            == Failure.PERSISTENCE_FAILURE
        )
    finally:
        locked.close()
