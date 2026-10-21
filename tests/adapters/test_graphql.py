import pytest

from enrollment.adapters.graphql.execution import Executor
from enrollment.application.contracts import Command, Failure
from enrollment.domain.models import Enrollment
from enrollment.domain.outcomes import Rejection
from enrollment.domain.values import CourseId, StudentId
from tests.acceptance.test_enrollment import QUERY


@pytest.mark.parametrize(
    "result,typename,payload",
    [
        (
            Enrollment(StudentId("s"), CourseId("c")),
            "EnrollCourseSuccess",
            {"studentId": "s", "courseId": "c"},
        ),
        *[(r, "EnrollCourseRejected", {"reason": r.value}) for r in Rejection],
        *[
            (
                r,
                "EnrollCourseRejected"
                if r.name.startswith("MISSING")
                else "EnrollCourseFailure",
                {
                    (
                        "reason" if r.name.startswith("MISSING") else "failureReason"
                    ): r.value
                },
            )
            for r in Failure
        ],
    ],
)
def test_explicit_mapping(result, typename, payload):
    calls = []
    engine = Executor(lambda c: calls.append(c) or result)
    assert engine.execute(
        QUERY, {"input": {"studentId": "s", "courseId": "c"}}, "Enroll", "opaque"
    ) == {"data": {"enrollCourse": {"__typename": typename, **payload}}}
    assert calls == [Command("s", "c", "opaque")]


@pytest.mark.parametrize(
    "variables",
    [
        None,
        {"input": None},
        {"input": {"studentId": None, "courseId": "c"}},
        {"input": {"studentId": "s", "courseId": "c", "verified": True}},
        {"input": {"studentId": [], "courseId": "c"}},
    ],
)
def test_invalid_input_never_invokes_core(variables):
    def forbidden(c):
        pytest.fail("invalid document invoked Core")

    assert Executor(forbidden).execute(QUERY, variables).get("errors")


def test_id_coercion_and_placeholder():
    calls = []
    e = Executor(lambda c: calls.append(c) or Rejection.DENIED)
    assert e.execute("{ _empty }") == {"data": {"_empty": None}}
    assert not calls
    assert "errors" not in e.execute(QUERY, {"input": {"studentId": 42, "courseId": 7}})
    assert calls == [Command("42", "7", None)]
    assert e.execute("{ unknown }").get("errors")
    assert e.execute("bad syntax").get("errors")
    assert e.execute(
        QUERY, {"input": {"studentId": "s", "courseId": "c"}}, "Unknown"
    ).get("errors")


def test_internal_error_sanitized():
    def broken(c):
        raise RuntimeError("credential SQL secret")

    result = Executor(broken).execute(
        QUERY, {"input": {"studentId": "s", "courseId": "c"}}
    )
    assert result["data"] is None
    assert result["errors"][0]["message"] == "Internal server error"
    assert "secret" not in str(result)


def test_awaitable_is_rejected():
    async def wrong(c):
        return Rejection.DENIED

    result = Executor(wrong).execute(
        QUERY, {"input": {"studentId": "s", "courseId": "c"}}
    )
    assert result.get("errors")
    assert result["data"] is None
