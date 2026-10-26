from .models import Enrollment, ProgrammeCourseOffering
from .outcomes import DetailRejection, OutdatedVersion, Rejection
from .values import SavedVersion, StudentId, VerifiedIdentity


def version_current(
    expected: SavedVersion, current: SavedVersion
) -> OutdatedVersion | None:
    return OutdatedVersion() if expected != current else None


def ownership(identity: VerifiedIdentity, target: StudentId) -> Rejection | None:
    return Rejection.DENIED if identity.subject_id.value != target.value else None


def duplicate(existing: Enrollment | None) -> Rejection | None:
    return Rejection.ALREADY_ENROLLED if existing is not None else None


def eligibility(offering: ProgrammeCourseOffering | None) -> Rejection | None:
    return Rejection.COURSE_NOT_OFFERED if offering is None else None


def email_available(
    owner: StudentId | None, candidate: StudentId
) -> DetailRejection | None:
    return (
        DetailRejection.EMAIL_CONFLICT
        if owner is not None and owner != candidate
        else None
    )
