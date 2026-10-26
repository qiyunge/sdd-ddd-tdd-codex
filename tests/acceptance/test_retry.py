from enrollment.adapters.persistence.sqlite import connect
from enrollment.bootstrap import create_app
from tests.acceptance.test_enrollment import request
from tests.support.database import rows


def test_response_loss_repeat_preserves_committed_pair(database):
    app = create_app(database, lambda c: c)
    request(app)  # The caller loses the response, after real commit.
    assert rows(database) == [("s", "c")]
    with connect(database) as db:
        db.execute("DELETE FROM programme_course_offerings")
    assert request(app)["data"]["enrollCourse"]["reason"] == "ALREADY_ENROLLED"
    assert rows(database) == [("s", "c")]


def test_retry_rechecks_higher_priority_missing_record(database):
    app = create_app(database, lambda c: c)
    assert request(app)["data"]["enrollCourse"]["__typename"] == "EnrollCourseSuccess"
    # Legacy/corrupt fixture, foreign keys deliberately disabled outside production.
    with connect(database) as db:
        db.execute("DELETE FROM students")
    assert request(app)["data"]["enrollCourse"]["reason"] == "MISSING_STUDENT"
    assert rows(database) == [("s", "c")]


def test_response_serialization_loss_does_not_compensate(database, monkeypatch):
    from enrollment.adapters.graphql import execution

    monkeypatch.setattr(
        execution,
        "output",
        lambda result: (_ for _ in ()).throw(RuntimeError("serialize secret")),
    )
    result = request(create_app(database, lambda c: c))
    assert result["data"] is None
    assert result["errors"][0]["message"] == "Internal server error"
    assert rows(database) == [("s", "c")]
