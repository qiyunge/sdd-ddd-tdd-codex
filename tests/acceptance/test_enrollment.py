import pytest

from enrollment.adapters.persistence.sqlite import connect
from enrollment.bootstrap import create_app
from tests.support.database import rows

QUERY = """mutation Enroll($input: EnrollCourseInput!) { enrollCourse(input:$input) {
__typename ... on EnrollCourseSuccess { studentId courseId }
... on EnrollCourseRejected { reason } ... on EnrollCourseFailure { failureReason: reason } } }"""


def request(app, token="s", student="s", course="c"):
    return (
        app.test_client()
        .post(
            "/graphql",
            json={
                "query": QUERY,
                "variables": {"input": {"studentId": student, "courseId": course}},
            },
            headers={"Authorization": token},
        )
        .get_json()
    )


@pytest.mark.parametrize(
    "scenario,expected",
    [
        (1, "SUCCESS"),
        (2, "SUCCESS"),
        (3, "COURSE_NOT_OFFERED"),
        (4, "MISSING_STUDENT"),
        (5, "MISSING_PROGRAMME"),
        (6, "MISSING_COURSE"),
        (7, "COURSE_NOT_OFFERED"),
        (8, "ALREADY_ENROLLED"),
        (9, "ALREADY_ENROLLED"),
        (10, "SUCCESS"),
        (11, "PERSISTENCE_FAILURE"),
        (12, "ALREADY_ENROLLED"),
        (13, "DENIED"),
        (14, "DENIED"),
        (15, "COURSE_NOT_OFFERED"),
    ],
    ids=lambda value: str(value),
)
def test_scenario(database, scenario, expected, monkeypatch, record_property):
    record_property("scenario", f"enrollment-{scenario}")
    with connect(database) as c:
        if scenario == 2:
            c.execute("INSERT INTO programmes VALUES ('p2')")
            c.execute("INSERT INTO programme_course_offerings VALUES ('p2','c')")
        if scenario in (3, 7, 12, 15):
            c.execute("DELETE FROM programme_course_offerings")
        if scenario == 4:
            c.execute("DELETE FROM students")
        if scenario == 5:
            c.execute("DELETE FROM programmes")
        if scenario == 6:
            c.execute("DELETE FROM courses")
        if scenario in (8, 9, 12):
            c.execute("INSERT INTO enrollments VALUES ('s','c')")

    def prerequisites():
        with connect(database) as db:
            return {
                table: db.execute(
                    f"SELECT * FROM {table} ORDER BY 1,2"
                    if table in ("students", "programme_course_offerings")
                    else f"SELECT * FROM {table} ORDER BY 1"
                ).fetchall()
                for table in (
                    "students",
                    "programmes",
                    "courses",
                    "programme_course_offerings",
                )
            }

    facts = prerequisites()
    before = rows(database)
    if scenario == 11:
        # Fail a real pending transaction before commit, without simulating response loss.
        from enrollment.adapters.persistence import sqlite as adapter

        monkeypatch.setattr(
            adapter.Session,
            "commit",
            lambda self: (_ for _ in ()).throw(adapter.StorageFailure()),
        )
    app = create_app(
        database, lambda credential: None if credential == "invalid" else credential
    )
    result = request(
        app, token="invalid" if scenario == 13 else "other" if scenario == 14 else "s"
    )
    assert result is not None, "Enrollment HTTP boundary has not been implemented"
    assert "errors" not in result
    assert prerequisites() == facts
    outcome = result["data"]["enrollCourse"]
    if expected == "SUCCESS":
        assert outcome == {
            "__typename": "EnrollCourseSuccess",
            "studentId": "s",
            "courseId": "c",
        }
        assert rows(database) == [("s", "c")]
    else:
        assert outcome.get("reason", outcome.get("failureReason")) == expected
        assert rows(database) == before


def test_unusable_identifiers_are_invalid_requests(database):
    app = create_app(database, lambda credential: credential)
    empty_student = request(app, student="", course="c")
    empty_course = request(app, student="s", course="")
    assert "errors" not in empty_student
    assert "errors" not in empty_course
    assert empty_student["data"]["enrollCourse"]["failureReason"] == "INVALID_REQUEST"
    assert empty_course["data"]["enrollCourse"]["failureReason"] == "INVALID_REQUEST"
    non_text = (
        app.test_client()
        .post(
            "/graphql",
            json={
                "query": QUERY,
                "variables": {"input": {"studentId": False, "courseId": "c"}},
            },
            headers={"Authorization": "s"},
        )
        .get_json()
    )
    assert "errors" in non_text
    assert not (non_text.get("data") or {}).get("enrollCourse")


@pytest.mark.parametrize("fault", ["rejection", "exception"])
def test_enrollment_16_factory_failure_after_insert(
    database, monkeypatch, fault, record_property
):
    from enrollment.adapters.persistence import sqlite as adapter
    from enrollment.domain.models import Enrollment
    from enrollment.domain.outcomes import Rejection

    record_property("scenario", "enrollment-16")
    active = []
    acknowledged = []
    original = adapter.Session.__init__

    def opened(self, *args, **kwargs):
        original(self, *args, **kwargs)
        active.append(self)

    def factory(student, course):
        acknowledged.append(
            active[-1]
            .connection.execute("SELECT student_id,course_id FROM enrollments")
            .fetchall()
            == [("s", "c")]
        )
        if fault == "exception":
            raise RuntimeError("factory secret")
        return Rejection.COURSE_NOT_OFFERED

    monkeypatch.setattr(adapter.Session, "__init__", opened)
    monkeypatch.setattr(Enrollment, "create", staticmethod(factory))
    result = request(create_app(database, lambda c: c))
    assert acknowledged == [True], (
        "Repository must acknowledge INSERT before Domain construction"
    )
    assert rows(database) == []
    assert "secret" not in str(result)
    if fault == "rejection":
        assert result["data"]["enrollCourse"]["reason"] == "COURSE_NOT_OFFERED"
    else:
        assert result["errors"][0]["message"] == "Internal server error"


def test_enrollment_17_definite_commit_failure(database, monkeypatch, record_property):
    from enrollment.adapters.persistence import sqlite as adapter

    record_property("scenario", "enrollment-17")
    monkeypatch.setattr(
        adapter.Session,
        "commit",
        lambda self: (_ for _ in ()).throw(adapter.StorageFailure("definite failure")),
    )
    result = request(create_app(database, lambda c: c))
    assert result["data"]["enrollCourse"]["failureReason"] == "PERSISTENCE_FAILURE"
    assert rows(database) == []


def test_enrollment_18_restore_historical_pair(database, record_property):
    from enrollment.adapters.persistence.sqlite import Session
    from enrollment.domain.values import CourseId, StudentId

    record_property("scenario", "enrollment-18")
    app = create_app(database, lambda c: c)
    assert request(app)["data"]["enrollCourse"]["__typename"] == "EnrollCourseSuccess"
    with connect(database) as db:
        db.execute("DELETE FROM programme_course_offerings")
    session = Session(database)
    try:
        saved = session.enrollment(StudentId.create("s"), CourseId.create("c"))
        assert saved.student_id.value == "s" and saved.course_id.value == "c"
    finally:
        session.close()
    assert request(app)["data"]["enrollCourse"]["reason"] == "ALREADY_ENROLLED"


@pytest.mark.parametrize("missing", ["student", "programme"])
@pytest.mark.parametrize(
    "token,expected",
    [("s", "INVALID_REQUEST"), ("other", "DENIED"), ("invalid", "DENIED")],
)
def test_enrollment_19_invalid_course_precedes_lookup(
    database, missing, token, expected, record_property
):
    record_property("scenario", "enrollment-19")
    with connect(database) as db:
        db.execute(
            "DELETE FROM students" if missing == "student" else "DELETE FROM programmes"
        )
    app = create_app(database, lambda c: None if c == "invalid" else c)
    result = request(app, token=token, course="")["data"]["enrollCourse"]
    assert result.get("failureReason", result.get("reason")) == expected
    assert rows(database) == []
