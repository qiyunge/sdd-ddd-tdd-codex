from enrollment.domain.models import Enrollment, ProgrammeCourseOffering
from enrollment.domain.outcomes import Rejection
from enrollment.domain.policies import duplicate, eligibility, ownership
from enrollment.domain.values import (
    CourseId,
    ProgrammeId,
    StudentId,
    SubjectId,
    VerifiedIdentity,
)


def test_ownership():
    assert ownership(VerifiedIdentity(SubjectId("s")), StudentId("s")) is None
    assert (
        ownership(VerifiedIdentity(SubjectId("other")), StudentId("s"))
        == Rejection.DENIED
    )


def test_duplicate():
    assert duplicate(None) is None
    assert (
        duplicate(Enrollment(StudentId("s"), CourseId("c")))
        == Rejection.ALREADY_ENROLLED
    )


def test_eligibility():
    assert eligibility(ProgrammeCourseOffering(ProgrammeId("p"), CourseId("c"))) is None
    assert eligibility(None) == Rejection.COURSE_NOT_OFFERED
