import pytest

from enrollment.application.contracts import Command, Failure, StorageFailure
from enrollment.application.enroll import enroll
from enrollment.domain.models import Enrollment, ProgrammeCourseOffering
from enrollment.domain.outcomes import Rejection
from enrollment.domain.values import CourseId, StudentId
from tests.application.test_identity import Verifier
from tests.application.test_prerequisites import Session


class FlowSession(Session):
    def __init__(self, existing=False, offered=True, fail=False):
        super().__init__()
        self.existing = existing
        self.offered = offered
        self.fail = fail

    def enrollment(self, s, c):
        self.calls.append("enrollment")
        return Enrollment(s, c) if self.existing else None

    def offering(self, p, c):
        self.calls.append("offering")
        return ProgrammeCourseOffering(p, c) if self.offered else None

    def add(self, e):
        self.calls.append("add")

    def commit(self):
        self.calls.append("commit")
        if self.fail:
            raise StorageFailure()


@pytest.mark.parametrize(
    "existing,offered,expected,tail",
    [
        (True, False, Rejection.ALREADY_ENROLLED, ["enrollment", "close"]),
        (
            False,
            False,
            Rejection.COURSE_NOT_OFFERED,
            ["enrollment", "offering", "close"],
        ),
        (
            False,
            True,
            Enrollment(StudentId("s"), CourseId("c")),
            ["enrollment", "offering", "add", "commit", "close"],
        ),
    ],
)
def test_flow(existing, offered, expected, tail):
    session = FlowSession(existing, offered)
    assert enroll(Command("s", "c", "s"), Verifier("s"), lambda: session) == expected
    assert session.calls == ["student", "programme", "course"] + tail


def test_commit_failure():
    session = FlowSession(fail=True)
    assert (
        enroll(Command("s", "c", "s"), Verifier("s"), lambda: session)
        == Failure.PERSISTENCE_FAILURE
    )
    assert session.calls[-1] == "close"


def test_open_failure():
    def failed():
        raise StorageFailure()

    assert (
        enroll(Command("s", "c", "s"), Verifier("s"), failed)
        == Failure.PERSISTENCE_FAILURE
    )
