from dataclasses import dataclass
from enum import StrEnum

from enrollment.domain.models import Enrollment
from enrollment.domain.outcomes import Rejection


class Failure(StrEnum):
    MISSING_STUDENT = "MISSING_STUDENT"
    MISSING_PROGRAMME = "MISSING_PROGRAMME"
    MISSING_COURSE = "MISSING_COURSE"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"
    IDENTITY_UNAVAILABLE = "IDENTITY_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"


@dataclass(frozen=True)
class Command:
    student_id: str
    course_id: str
    credential: str | None


Result = Enrollment | Rejection | Failure


class StorageFailure(Exception):
    """A technical persistence failure, not a business rejection."""


class UniqueConflict(StorageFailure):
    """The persisted enrollment pair conflicts."""


class IdentityUnavailable(Exception):
    """Identity provider could not complete verification."""
