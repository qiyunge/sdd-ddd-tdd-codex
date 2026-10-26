import pytest

from enrollment.application.contracts import Command, Failure
from enrollment.application.enroll import enroll
from enrollment.domain.models import Course, Programme, Student
from enrollment.domain.values import ProgrammeId, StudentEmail, StudentName
from tests.application.test_identity import Verifier


class Session:
    def __init__(self, missing=None):
        self.missing = missing
        self.calls = []

    def student(self, s):
        self.calls.append("student")
        return (
            None
            if self.missing == "student"
            else Student.create(
                s,
                ProgrammeId.create("p"),
                StudentName.create("Alex"),
                StudentEmail.create("alex@example.com"),
            )
        )

    def programme(self, p):
        self.calls.append("programme")
        return None if self.missing == "programme" else Programme.create(p)

    def course(self, c):
        self.calls.append("course")
        return None if self.missing == "course" else Course.create(c)

    def close(self):
        self.calls.append("close")


@pytest.mark.parametrize(
    "missing,reason,trace",
    [
        ("student", Failure.MISSING_STUDENT, ["student", "close"]),
        ("programme", Failure.MISSING_PROGRAMME, ["student", "programme", "close"]),
        ("course", Failure.MISSING_COURSE, ["student", "programme", "course", "close"]),
    ],
)
def test_missing(missing, reason, trace):
    session = Session(missing)
    assert enroll(Command("s", "c", "s"), Verifier("s"), lambda: session) == reason
    assert session.calls == trace
