"""Seven stable host integration scenario families using real persisted state."""

import pytest

from enrollment.adapters.persistence.sqlite import connect, initialize
from enrollment.application.student_details import save_student


@pytest.fixture(autouse=True)
def scenario_identity(request):
    import re

    match = re.fullmatch(r"test_student_details_(\d+)", request.node.originalname or "")
    if match:
        request.node.user_properties.append(("scenario", "student-details-" + match[1]))


def invoke(path, **overrides):
    from enrollment.adapters.persistence import sqlite

    command = dict(
        mode="create",
        student_id="s",
        programme_id="p",
        name="Alex",
        email="Alex@Example.com",
    )
    command.update(overrides)
    factory = getattr(sqlite, "StudentSession", sqlite.Session)
    return save_student(command, lambda: factory(path))


def test_student_details_1(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    result = invoke(path)
    assert result is not None, "valid student must be committed and returned"
    assert result.student_id.value == "s"
    with connect(path) as c:
        assert c.execute("SELECT name,email FROM students").fetchone() == (
            "Alex",
            "Alex@Example.com",
        )


@pytest.mark.parametrize("field", ["name", "email"])
@pytest.mark.parametrize(
    "value",
    [None, 3, "", " \t\n", "\u00a0"],
    ids=["missing", "nontext", "empty", "whitespace", "unicode"],
)
def test_student_details_2(tmp_path, field, value):
    path = tmp_path / "db"
    initialize(path)
    result = invoke(path, **{field: value})
    assert getattr(result, "field", None) == field, (
        "invalid text must return field rejection"
    )


@pytest.mark.parametrize(
    "email",
    ["Alex@Example.com", "alex@Example.com", "Alex@example.COM", "aLEX@EXAMPLE.COM"],
    ids=["exact", "local", "domain", "mixed"],
)
def test_student_details_3(tmp_path, email):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    assert (
        invoke(path, student_id="other", programme_id="other", email=email)
        == "EMAIL_CONFLICT"
    )


@pytest.mark.parametrize(
    "email",
    ["alex+other@example.com", "alex@other.example", " Alex@Example.com "],
    ids=["tag", "domain", "spaces"],
)
def test_student_details_4(tmp_path, email):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    result = invoke(path, student_id="other", email=email)
    assert result is not None and getattr(result, "student_id", None) is not None


def test_student_details_5(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    result = invoke(path, mode="replace", email="aLEX@EXAMPLE.COM")
    assert result is not None and getattr(result, "email", None) is not None
    assert result.email.value == "aLEX@EXAMPLE.COM"


def test_student_details_6(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    path = tmp_path / "db"
    initialize(path)
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(lambda identity: invoke(path, student_id=identity), ["a", "b"])
        )
    assert sum(getattr(r, "student_id", None) is not None for r in results) == 1
    assert results.count("EMAIL_CONFLICT") == 1


def test_student_details_7(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    invoke(path, student_id="other", email="other@example.com")
    accepted = invoke(path, mode="replace", name="New", email="new@example.com")
    assert getattr(accepted, "name", None) is not None
    assert invoke(path, mode="replace", email="other@example.com") == "EMAIL_CONFLICT"
    with connect(path) as c:
        assert c.execute(
            "SELECT name,email FROM students WHERE student_id='s'"
        ).fetchone() == ("New", "new@example.com")


def test_replacement_claims_are_atomic(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    path = tmp_path / "db"
    initialize(path)
    invoke(path, student_id="a", email="a@example.com")
    invoke(path, student_id="b", email="b@example.com")
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(
                lambda identity: invoke(
                    path,
                    student_id=identity,
                    mode="replace",
                    email="shared@example.com",
                ),
                ["a", "b"],
            )
        )
    assert sum(getattr(r, "student_id", None) is not None for r in results) == 1
    assert results.count("EMAIL_CONFLICT") == 1
    with connect(path) as db:
        rows = db.execute(
            "SELECT student_id,email FROM students ORDER BY student_id"
        ).fetchall()
    assert sum(email == "shared@example.com" for _, email in rows) == 1
    assert any(email == identity + "@example.com" for identity, email in rows)


def test_invalid_replacement_preserves_details(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    assert getattr(invoke(path, mode="replace", name=" "), "field", None) == "name"
    with connect(path) as db:
        assert db.execute("SELECT name,email FROM students").fetchone() == (
            "Alex",
            "Alex@Example.com",
        )
