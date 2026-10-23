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
    assert ownership(VerifiedIdentity.create(SubjectId("s")), StudentId("s")) is None
    assert (
        ownership(VerifiedIdentity.create(SubjectId("other")), StudentId("s"))
        == Rejection.DENIED
    )


def test_duplicate():
    assert duplicate(None) is None
    assert (
        duplicate(Enrollment.create(StudentId("s"), CourseId("c")))
        == Rejection.ALREADY_ENROLLED
    )


def test_eligibility():
    assert (
        eligibility(ProgrammeCourseOffering.create(ProgrammeId("p"), CourseId("c")))
        is None
    )
    assert eligibility(None) == Rejection.COURSE_NOT_OFFERED
