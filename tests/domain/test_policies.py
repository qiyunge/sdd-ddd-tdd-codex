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
    assert (
        ownership(VerifiedIdentity.create(SubjectId.create("s")), StudentId.create("s"))
        is None
    )
    assert (
        ownership(
            VerifiedIdentity.create(SubjectId.create("other")), StudentId.create("s")
        )
        == Rejection.DENIED
    )


def test_duplicate():
    assert duplicate(None) is None
    assert (
        duplicate(Enrollment.create(StudentId.create("s"), CourseId.create("c")))
        == Rejection.ALREADY_ENROLLED
    )


def test_eligibility():
    assert (
        eligibility(
            ProgrammeCourseOffering.create(
                ProgrammeId.create("p"), CourseId.create("c")
            )
        )
        is None
    )
    assert eligibility(None) == Rejection.COURSE_NOT_OFFERED


def test_expected_saved_version_policy():
    from enrollment.domain.outcomes import OutdatedVersion
    from enrollment.domain.policies import version_current
    from enrollment.domain.values import SavedVersion

    assert version_current(SavedVersion.create(1), SavedVersion.create(1)) is None
    assert isinstance(
        version_current(SavedVersion.create(1), SavedVersion.create(2)), OutdatedVersion
    )
