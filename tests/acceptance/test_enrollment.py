import sqlite3

import pytest

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
def test_scenario(database, scenario, expected, monkeypatch):
    with sqlite3.connect(database) as c:
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
        with sqlite3.connect(database) as db:
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
