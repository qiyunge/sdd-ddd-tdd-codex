from dataclasses import dataclass
from typing import ClassVar, Self

from .outcomes import (
    InvalidIdentifier,
    InvalidSavedVersion,
    InvalidStudentDetails,
)


@dataclass(frozen=True)
class Identifier:
    value: str

    @classmethod
    def create(cls, raw: object) -> Self | InvalidIdentifier:
        if not isinstance(raw, str) or not raw:
            return InvalidIdentifier()
        return cls(raw)

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("Identifier must be a nonempty string")


class StudentId(Identifier):
    pass


class ProgrammeId(Identifier):
    pass


class CourseId(Identifier):
    pass


class SubjectId(Identifier):
    pass


@dataclass(frozen=True)
class SavedVersion:
    """SavedVersion is a Domain Value Object containing an integer from 1 through 9,223,372,036,854,775,807.

    Bool, missing input, strings, floats and out-of-range values are invalid; no coercion.
    The shared factory returns InvalidSavedVersion for unusable input.
    """

    value: int
    maximum: ClassVar[int] = 9223372036854775807

    @staticmethod
    def usable(raw: object) -> bool:
        return type(raw) is int and 1 <= raw <= SavedVersion.maximum

    @classmethod
    def create(cls, raw: object) -> Self | InvalidSavedVersion:
        if not cls.usable(raw):
            return InvalidSavedVersion()
        assert isinstance(raw, int)
        return cls(raw)

    def __post_init__(self) -> None:
        if not self.usable(self.value):
            raise ValueError(
                "Saved version must be a strict positive signed-64 integer"
            )


@dataclass(frozen=True)
class VerifiedIdentity:
    subject_id: SubjectId

    @classmethod
    def create(cls, subject_id: SubjectId) -> Self:
        if not isinstance(subject_id, SubjectId):
            raise ValueError("VerifiedIdentity.create requires SubjectId")
        return cls(subject_id)

    def __post_init__(self) -> None:
        if not isinstance(self.subject_id, SubjectId):
            raise ValueError("Verified identity requires SubjectId")


@dataclass(frozen=True)
class RequiredText:
    value: str
    field: ClassVar[str] = "text"

    @classmethod
    def create(cls, raw: object) -> Self | InvalidStudentDetails:
        if not isinstance(raw, str) or not raw.strip():
            return InvalidStudentDetails(cls.field)
        return cls(raw)

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Required text must contain a non-whitespace character")


class StudentName(RequiredText):
    field = "name"


@dataclass(frozen=True, eq=False)
class StudentEmail(RequiredText):
    field = "email"

    @property
    def key(self) -> str:
        return self.value.casefold()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StudentEmail):
            return NotImplemented
        return self.key == other.key

    def __hash__(self) -> int:
        return hash(self.key)
