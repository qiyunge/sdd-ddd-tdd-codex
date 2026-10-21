import pytest

from enrollment.application.contracts import Command, Failure, UniqueConflict
from enrollment.application.enroll import enroll
from enrollment.domain.outcomes import Rejection
from tests.application.test_enrollment_flow import FlowSession
from tests.application.test_identity import Verifier


class Conflicting(FlowSession):
    def add(self, e):
        self.calls.append("add")
        raise UniqueConflict()


@pytest.mark.parametrize(
    "missing,expected",
    [
        (None, Rejection.ALREADY_ENROLLED),
        ("student", Failure.MISSING_STUDENT),
        ("programme", Failure.MISSING_PROGRAMME),
        ("course", Failure.MISSING_COURSE),
    ],
)
def test_conflict_rechecks_full_order(missing, expected):
    first = Conflicting()
    second = FlowSession(existing=True)
    second.missing = missing
    sessions = iter([first, second])

    def factory():
        if not first.calls:
            return next(sessions)
        assert first.calls[-1] == "close"
        return next(sessions)

    assert enroll(Command("s", "c", "s"), Verifier("s"), factory) == expected
    assert second.calls[0] == "student"
    assert second.calls[-1] == "close"


def test_conflict_retry_bounded():
    sessions = [Conflicting(), Conflicting()]
    opened = []

    def factory():
        opened.append(True)
        return sessions[len(opened) - 1]

    assert (
        enroll(Command("s", "c", "s"), Verifier("s"), factory)
        == Failure.PERSISTENCE_FAILURE
    )
    assert len(opened) == 2
