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
        return Enrollment.create(s, c) if self.existing else None

    def offering(self, p, c):
        self.calls.append("offering")
        return ProgrammeCourseOffering.create(p, c) if self.offered else None

    def create_enrollment(self, student, course):
        self.calls.append("add")
        return Enrollment.create(student, course)

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
            Enrollment.create(StudentId.create("s"), CourseId.create("c")),
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


def test_second_unobservable_conflict_keeps_the_saved_pair():
    from enrollment.application.contracts import PairConflict

    class SavedConflict(FlowSession):
        def create_enrollment(self, student, course):
            self.calls.append("add")
            self.retained = Enrollment.create(student, course)
            return PairConflict

    sessions = [SavedConflict(), SavedConflict()]
    opened = []

    def factory():
        opened.append(True)
        return sessions[len(opened) - 1]

    assert (
        enroll(Command("s", "c", "s"), Verifier("s"), factory)
        == Failure.PERSISTENCE_FAILURE
    )
    assert all(
        session.retained
        == Enrollment.create(StudentId.create("s"), CourseId.create("c"))
        for session in sessions
    )


def test_open_failure():
    def failed():
        raise StorageFailure()

    assert (
        enroll(Command("s", "c", "s"), Verifier("s"), failed)
        == Failure.PERSISTENCE_FAILURE
    )


def test_repository_receives_validated_values_and_commits_once():
    class Requested(FlowSession):
        requested = None

        def create_enrollment(self, student, course):
            self.requested = (student, course)
            return Enrollment.create(student, course)

    session = Requested()
    result = enroll(Command("s", "c", "s"), Verifier("s"), lambda: session)
    assert session.requested == (StudentId.create("s"), CourseId.create("c")), (
        "Application must request Repository creation using validated values"
    )
    assert result.student_id.value == "s"
    assert session.calls.count("commit") == 1


def test_rejected_repository_creation_never_commits():
    class Rejected(FlowSession):
        def create_enrollment(self, student, course):
            return Rejection.COURSE_NOT_OFFERED

    session = Rejected()
    assert (
        enroll(Command("s", "c", "s"), Verifier("s"), lambda: session)
        == Rejection.COURSE_NOT_OFFERED
    )
    assert "commit" not in session.calls
