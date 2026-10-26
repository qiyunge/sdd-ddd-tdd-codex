from dataclasses import dataclass
from enum import StrEnum

from enrollment.domain.models import Student
from enrollment.domain.values import SavedVersion


@dataclass(frozen=True)
class StudentSnapshot:
    """Immutable Application result containing a Repository-issued Student and SavedVersion from one saved row/atomic operation."""

    student: Student
    saved_version: SavedVersion


class StudentResult(StrEnum):
    ALREADY_EXISTS = "STUDENT_ALREADY_EXISTS"
    NOT_FOUND = "STUDENT_NOT_FOUND"
    STORAGE_FAILURE = "STUDENT_STORAGE_FAILURE"


class StudentWrite(StrEnum):
    EMAIL_KEY_CONFLICT = "EMAIL_KEY_CONFLICT"
    VERSION_CONFLICT = "VERSION_CONFLICT"


EmailKeyConflict = StudentWrite.EMAIL_KEY_CONFLICT
VersionConflict = StudentWrite.VERSION_CONFLICT
