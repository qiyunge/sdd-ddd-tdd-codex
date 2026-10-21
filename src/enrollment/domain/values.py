from dataclasses import dataclass


@dataclass(frozen=True)
class Identifier:
    value: str

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
class VerifiedIdentity:
    subject_id: SubjectId

    def __post_init__(self) -> None:
        if not isinstance(self.subject_id, SubjectId):
            raise ValueError("Verified identity requires SubjectId")
