import pytest

from enrollment.application.contracts import Command, Failure, IdentityUnavailable
from enrollment.application.enroll import enroll
from enrollment.domain import policies
from enrollment.domain.outcomes import Rejection
from enrollment.domain.values import SubjectId, VerifiedIdentity


class Verifier:
    def __init__(self, subject):
        self.subject = subject

    def verify(self, credential):
        return (
            None
            if self.subject is None
            else VerifiedIdentity.create(SubjectId(self.subject))
        )


def forbidden(*args):
    raise AssertionError("must not be called")


def test_unverified(monkeypatch):
    monkeypatch.setattr(policies, "ownership", forbidden)
    assert enroll(Command("", "", None), Verifier(None), forbidden) == Rejection.DENIED


def test_mismatch():
    assert (
        enroll(Command("s", "", None), Verifier("other"), forbidden) == Rejection.DENIED
    )


@pytest.mark.parametrize("student,course", [("", "c"), ("s", "")])
def test_invalid_ids(student, course):
    assert (
        enroll(Command(student, course, None), Verifier("s"), forbidden)
        == Failure.INVALID_REQUEST
    )


def test_non_text_identifier_is_invalid_request():
    command = Command("s", "c", None)
    object.__setattr__(command, "student_id", 1)
    assert enroll(command, Verifier("s"), forbidden) == Failure.INVALID_REQUEST


def test_unavailable(monkeypatch):
    class Down:
        def verify(self, c):
            raise IdentityUnavailable()

    monkeypatch.setattr(policies, "ownership", forbidden)
    assert (
        enroll(Command("s", "c", None), Down(), forbidden)
        == Failure.IDENTITY_UNAVAILABLE
    )
