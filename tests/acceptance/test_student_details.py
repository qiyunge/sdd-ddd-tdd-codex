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
    assert result.student.student_id.value == "s"
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
    "existing,email",
    [
        ("Alex@Example.com", "Alex@Example.com"),
        ("Alex@Example.com", "alex@Example.com"),
        ("Alex@Example.com", "Alex@example.COM"),
        ("Alex@Example.com", "aLEX@EXAMPLE.COM"),
        ("Straße@example.com", "STRASSE@EXAMPLE.COM"),
    ],
    ids=["exact", "local", "domain", "mixed", "unicode-expansion"],
)
def test_student_details_3(tmp_path, existing, email):
    path = tmp_path / "db"
    initialize(path)
    invoke(path, email=existing)
    assert (
        invoke(path, student_id="other", programme_id="other", email=email)
        == "EMAIL_CONFLICT"
    )
    with connect(path) as db:
        assert db.execute("SELECT student_id,email FROM students").fetchall() == [
            ("s", existing)
        ]


@pytest.mark.parametrize(
    "existing,email",
    [
        ("Alex@Example.com", "alex+other@example.com"),
        ("Alex@Example.com", "alex@other.example"),
        ("Alex@Example.com", " Alex@Example.com "),
        ("caf\u00e9@example.com", "cafe\u0301@example.com"),
    ],
    ids=["tag", "domain", "spaces", "unicode-composition"],
)
def test_student_details_4(tmp_path, existing, email):
    path = tmp_path / "db"
    initialize(path)
    invoke(path, email=existing)
    result = invoke(path, student_id="other", email=email)
    assert (
        result is not None
        and getattr(getattr(result, "student", None), "student_id", None) is not None
    )
    with connect(path) as db:
        assert db.execute(
            "SELECT student_id,email FROM students ORDER BY student_id"
        ).fetchall() == [("other", email), ("s", existing)]


def test_student_details_5(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    result = invoke(path, mode="replace", expected_version=1, email="aLEX@EXAMPLE.COM")
    assert (
        result is not None
        and getattr(getattr(result, "student", None), "email", None) is not None
    )
    assert result.student.email.value == "aLEX@EXAMPLE.COM"


def test_student_details_6(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    path = tmp_path / "db"
    initialize(path)
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(lambda identity: invoke(path, student_id=identity), ["a", "b"])
        )
    assert (
        sum(
            getattr(getattr(r, "student", None), "student_id", None) is not None
            for r in results
        )
        == 1
    )
    assert results.count("EMAIL_CONFLICT") == 1


def test_student_details_7(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    invoke(path, student_id="other", email="other@example.com")
    accepted = invoke(
        path, mode="replace", expected_version=1, name="New", email="new@example.com"
    )
    assert getattr(getattr(accepted, "student", None), "name", None) is not None
    assert (
        invoke(path, mode="replace", expected_version=2, email="other@example.com")
        == "EMAIL_CONFLICT"
    )
    with connect(path) as c:
        assert c.execute(
            "SELECT name,email FROM students WHERE student_id='s'"
        ).fetchone() == ("New", "new@example.com")


def test_student_details_8(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    assert invoke(path) == "STUDENT_ALREADY_EXISTS"


def test_student_details_9(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    assert invoke(path, mode="replace", expected_version=1) == "STUDENT_NOT_FOUND"


def test_student_details_10(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    assert type(invoke(path, student_id="", name=" ")).__name__ == "InvalidIdentifier"
    assert (
        type(invoke(path, student_id="other", programme_id="", email=" ")).__name__
        == "InvalidIdentifier"
    )
    assert (
        getattr(
            invoke(path, student_id="other", name=" ", email="Alex@Example.com"),
            "field",
            None,
        )
        == "name"
    )


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
                    expected_version=1,
                    email="shared@example.com",
                ),
                ["a", "b"],
            )
        )
    assert (
        sum(
            getattr(getattr(r, "student", None), "student_id", None) is not None
            for r in results
        )
        == 1
    )
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


def test_student_details_11(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    result = invoke(path)
    assert getattr(result, "saved_version", None) is not None, (
        "Committed creation must return a saved-version snapshot"
    )
    assert result.saved_version.value == 1
    assert result.student.student_id.value == "s"
    assert result.student.name.value == "Alex"
    from enrollment.application.student_details import get_student

    assert (
        get_student(
            "s",
            lambda: __import__(
                "enrollment.adapters.persistence.sqlite", fromlist=["StudentSession"]
            ).StudentSession(path),
        )
        == result
    )


@pytest.mark.parametrize("fault", ["rejection", "exception", "commit"])
def test_student_details_12(tmp_path, monkeypatch, fault):
    from enrollment.adapters.persistence import sqlite as adapter
    from enrollment.domain.models import Student
    from enrollment.domain.outcomes import InvalidStudentDetails

    path = tmp_path / "db"
    initialize(path)
    active = []
    confirmed = []
    original = adapter.StudentSession.__init__

    def opened(self, *args, **kwargs):
        original(self, *args, **kwargs)
        active.append(self)

    def factory(*args):
        confirmed.append(
            active[-1].connection.execute("SELECT student_id FROM students").fetchall()
            == [("s",)]
        )
        if fault == "exception":
            raise RuntimeError("creation defect")
        return InvalidStudentDetails("name")

    monkeypatch.setattr(adapter.StudentSession, "__init__", opened)
    if fault == "commit":
        monkeypatch.setattr(
            adapter.StudentSession,
            "commit",
            lambda self: (_ for _ in ()).throw(adapter.StorageFailure()),
        )
        assert invoke(path) == "STUDENT_STORAGE_FAILURE"
    else:
        monkeypatch.setattr(Student, "create", staticmethod(factory))
        if fault == "exception":
            with pytest.raises(RuntimeError, match="creation defect"):
                invoke(path)
        else:
            assert invoke(path) == InvalidStudentDetails("name")
        assert confirmed == [True], (
            "Student INSERT acknowledgment must precede construction"
        )
    with connect(path) as db:
        assert db.execute("SELECT * FROM students").fetchall() == []


def test_student_details_13(tmp_path, monkeypatch):
    from enrollment.adapters.persistence import sqlite as adapter

    path = tmp_path / "db"
    initialize(path)
    initial = invoke(path)
    with monkeypatch.context() as patch:
        patch.setattr(
            adapter.StudentSession,
            "commit",
            lambda self: (_ for _ in ()).throw(adapter.StorageFailure()),
        )
        assert (
            invoke(path, mode="replace", expected_version=1, name="Changed")
            == "STUDENT_STORAGE_FAILURE"
        )
    with connect(path) as db:
        assert db.execute("SELECT name,email FROM students").fetchone() == (
            "Alex",
            "Alex@Example.com",
        )
    assert getattr(initial, "saved_version", None) is not None
    from enrollment.application.student_details import get_student

    assert get_student("s", lambda: adapter.StudentSession(path)) == initial


def test_initial_stale_replacement_is_rejected(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    assert (
        type(invoke(path, mode="replace", expected_version=9)).__name__
        == "OutdatedVersion"
    ), "Domain version policy must reject stale input"


def read_student(path, identity="s"):
    from enrollment.adapters.persistence.sqlite import StudentSession
    from enrollment.application.student_details import get_student

    return get_student(identity, lambda: StudentSession(path))


def test_student_details_14(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    path = tmp_path / "db"
    initialize(path)
    saved = invoke(path)
    original_version = saved.saved_version.value
    start = Barrier(2)

    def replace(label):
        start.wait(3)
        return invoke(
            path,
            mode="replace",
            expected_version=original_version,
            programme_id=label,
            name=label,
            email=label + "@example.com",
        )

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(replace, ["a", "b"]))
    winners = [r for r in results if getattr(r, "saved_version", None) is not None]
    assert len(winners) == 1, "Exactly one same-version replacement must commit"
    assert sum(type(r).__name__ == "OutdatedVersion" for r in results) == 1
    winner = winners[0]
    assert winner.saved_version.value == original_version + 1
    current = read_student(path)
    assert current.student.name == winner.student.name
    assert current.student.programme_id == winner.student.programme_id
    assert current.student.email.value == winner.student.email.value
    assert current.saved_version == winner.saved_version


def test_student_details_15(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    initial = invoke(path)
    changed = invoke(
        path, mode="replace", expected_version=initial.saved_version.value, name="B"
    )
    assert getattr(changed, "saved_version", None) is not None, (
        "Replacement must commit a new snapshot"
    )
    assert (
        type(
            invoke(path, mode="replace", expected_version=initial.saved_version.value)
        ).__name__
        == "OutdatedVersion"
    )
    reloaded = read_student(path)
    restored = invoke(
        path, mode="replace", expected_version=reloaded.saved_version.value
    )
    assert restored.saved_version.value == 3 and restored.student.name.value == "Alex"
    identical = invoke(
        path, mode="replace", expected_version=restored.saved_version.value
    )
    assert identical.saved_version.value == 4
    assert (
        type(
            invoke(path, mode="replace", expected_version=reloaded.saved_version.value)
        ).__name__
        == "OutdatedVersion"
    )


@pytest.mark.parametrize(
    "version", [None, True, False, "1", 1.0, 0, -1, 9223372036854775808]
)
def test_student_details_16(tmp_path, version):
    path = tmp_path / "db"
    initialize(path)
    initial = invoke(path)
    assert (
        type(invoke(path, mode="replace", expected_version=version)).__name__
        == "InvalidSavedVersion"
    )
    assert read_student(path) == initial


@pytest.mark.parametrize("loss", ["response", "uncertain"])
def test_student_details_17(tmp_path, monkeypatch, loss):
    from enrollment.adapters.persistence import sqlite as adapter

    path = tmp_path / "db"
    initialize(path)
    original = invoke(path)
    commit = adapter.StudentSession.commit

    def uncertain(self):
        commit(self)
        raise adapter.StorageFailure("acknowledgment lost")

    with monkeypatch.context() as patch:
        if loss == "uncertain":
            patch.setattr(adapter.StudentSession, "commit", uncertain)
        response = invoke(
            path,
            mode="replace",
            expected_version=original.saved_version.value,
            name="Committed",
        )
    if loss == "uncertain":
        assert response == "STUDENT_STORAGE_FAILURE"
    current = read_student(path)
    assert current.student.name.value == "Committed", (
        "Potentially committed state must survive response uncertainty"
    )
    assert current.saved_version.value == 2
    assert (
        type(
            invoke(path, mode="replace", expected_version=original.saved_version.value)
        ).__name__
        == "OutdatedVersion"
    )
    assert read_student(path) == current


def test_version_existence_and_email_precedence(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    initial = invoke(path)
    invoke(path, student_id="other", email="other@example.com")
    assert (
        type(
            invoke(path, mode="replace", expected_version=9, email="other@example.com")
        ).__name__
        == "OutdatedVersion"
    )
    assert (
        invoke(
            path,
            mode="replace",
            student_id="missing",
            expected_version=9,
            email="other@example.com",
        )
        == "STUDENT_NOT_FOUND"
    )
    assert (
        type(
            invoke(
                path, mode="replace", student_id="missing", email="other@example.com"
            )
        ).__name__
        == "InvalidSavedVersion"
    )
    assert (
        getattr(
            invoke(path, mode="replace", name=" ", expected_version=None), "field", None
        )
        == "name"
    )
    assert read_student(path) == initial


@pytest.mark.parametrize(
    "identity",
    ["\0", "\0student", "student\0suffix"],
    ids=["nul", "leading", "embedded"],
)
def test_exact_identifiers_with_nul_round_trip(tmp_path, identity, record_property):
    from enrollment.adapters.persistence.sqlite import Session
    from enrollment.application.student_contracts import StudentSnapshot
    from enrollment.bootstrap import create_app
    from enrollment.domain.values import CourseId, ProgrammeId, StudentId
    from tests.acceptance.test_enrollment import request

    path = tmp_path / "db"
    initialize(path)
    record_property("scenario", "student-details-11")
    programme = identity + "programme"
    course = identity + "course"
    created = invoke(path, student_id=identity, programme_id=programme)
    assert isinstance(created, StudentSnapshot), (
        "Every nonempty text identity, including leading NUL, must commit"
    )
    assert created.student.student_id.value == identity
    assert created.student.programme_id.value == programme
    assert created.saved_version.value == 1
    assert read_student(path, identity) == created

    replacement_programme = programme + "replacement"
    replaced = invoke(
        path,
        mode="replace",
        student_id=identity,
        programme_id=replacement_programme,
        expected_version=created.saved_version.value,
        name="Updated",
    )
    assert isinstance(replaced, StudentSnapshot)
    assert replaced.student.student_id.value == identity
    assert replaced.student.programme_id.value == replacement_programme
    assert replaced.student.name.value == "Updated"
    assert replaced.saved_version.value == 2
    reloaded = read_student(path, identity)
    assert reloaded == replaced
    assert reloaded.student.student_id.value == identity
    assert reloaded.student.programme_id.value == replacement_programme
    assert reloaded.student.name.value == "Updated"

    session = Session(path)
    try:
        session.create_programme(ProgrammeId.create(replacement_programme))
        session.create_course(CourseId.create(course))
        session.create_offering(
            ProgrammeId.create(replacement_programme), CourseId.create(course)
        )
        session.commit()
    finally:
        session.close()
    app = create_app(
        path, lambda credential: identity if credential == "trusted" else None
    )
    response = request(app, token="trusted", student=identity, course=course)
    assert "errors" not in response
    assert response["data"]["enrollCourse"] == {
        "__typename": "EnrollCourseSuccess",
        "studentId": identity,
        "courseId": course,
    }
    session = Session(path)
    try:
        enrollment = session.enrollment(
            StudentId.create(identity), CourseId.create(course)
        )
        assert enrollment.student_id.value == identity
        assert enrollment.course_id.value == course
    finally:
        session.close()
    assert (
        request(app, token="trusted", student=identity, course=course)["data"][
            "enrollCourse"
        ]["reason"]
        == "ALREADY_ENROLLED"
    )
    assert read_student(path, identity) == replaced
