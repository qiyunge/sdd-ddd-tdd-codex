from dataclasses import dataclass
from enum import StrEnum


class Rejection(StrEnum):
    DENIED = "DENIED"
    ALREADY_ENROLLED = "ALREADY_ENROLLED"
    COURSE_NOT_OFFERED = "COURSE_NOT_OFFERED"


@dataclass(frozen=True)
class InvalidIdentifier:
    pass


@dataclass(frozen=True)
class InvalidStudentDetails:
    field: str


@dataclass(frozen=True)
class InvalidPersistedState:
    """Stored state violates a persisted invariant."""


class DetailRejection(StrEnum):
    EMAIL_CONFLICT = "EMAIL_CONFLICT"
