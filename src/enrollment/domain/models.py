from __future__ import annotations

from dataclasses import dataclass

from .outcomes import InvalidPersistedState
from .values import CourseId, ProgrammeId, StudentEmail, StudentId, StudentName


@dataclass(frozen=True, eq=False)
class Student:
    student_id: StudentId
    programme_id: ProgrammeId
    name: StudentName
    email: StudentEmail

    @classmethod
    def create(
        cls,
        student_id: StudentId,
        programme_id: ProgrammeId,
        name: StudentName,
        email: StudentEmail,
    ) -> Student:
        if not isinstance(student_id, StudentId) or not isinstance(
            programme_id, ProgrammeId
        ):
            raise ValueError("Student.create requires validated identifiers")
        if not isinstance(name, StudentName) or not isinstance(email, StudentEmail):
            raise ValueError("Student.create requires validated name and email")
        return cls(student_id, programme_id, name, email)

    @classmethod
    def reconstitute(
        cls,
        student_id: object,
        programme_id: object,
        name: object,
        email: object,
    ) -> Student | InvalidPersistedState:
        if (
            not isinstance(student_id, StudentId)
            or not isinstance(programme_id, ProgrammeId)
            or not isinstance(name, StudentName)
            or not isinstance(email, StudentEmail)
        ):
            return InvalidPersistedState()
        return cls(student_id, programme_id, name, email)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Student):
            return NotImplemented
        return self.student_id == other.student_id

    def __hash__(self) -> int:
        return hash(self.student_id)

    def __post_init__(self) -> None:
        if not isinstance(self.student_id, StudentId):
            raise ValueError("student_id requires StudentId")
        if not isinstance(self.programme_id, ProgrammeId):
            raise ValueError("programme_id requires ProgrammeId")
        if not isinstance(self.name, StudentName) or not isinstance(
            self.email, StudentEmail
        ):
            raise ValueError("Student requires typed name and email")


@dataclass(frozen=True)
class Programme:
    programme_id: ProgrammeId

    @classmethod
    def create(cls, programme_id: ProgrammeId) -> Programme:
        if not isinstance(programme_id, ProgrammeId):
            raise ValueError("Programme.create requires ProgrammeId")
        return cls(programme_id)

    @classmethod
    def reconstitute(cls, programme_id: object) -> Programme | InvalidPersistedState:
        if not isinstance(programme_id, ProgrammeId):
            return InvalidPersistedState()
        return cls(programme_id)

    def __post_init__(self) -> None:
        if not isinstance(self.programme_id, ProgrammeId):
            raise ValueError("programme_id requires ProgrammeId")


@dataclass(frozen=True)
class Course:
    course_id: CourseId

    @classmethod
    def create(cls, course_id: CourseId) -> Course:
        if not isinstance(course_id, CourseId):
            raise ValueError("Course.create requires CourseId")
        return cls(course_id)

    @classmethod
    def reconstitute(cls, course_id: object) -> Course | InvalidPersistedState:
        if not isinstance(course_id, CourseId):
            return InvalidPersistedState()
        return cls(course_id)

    def __post_init__(self) -> None:
        if not isinstance(self.course_id, CourseId):
            raise ValueError("course_id requires CourseId")


@dataclass(frozen=True)
class ProgrammeCourseOffering:
    programme_id: ProgrammeId
    course_id: CourseId

    @classmethod
    def create(
        cls, programme_id: ProgrammeId, course_id: CourseId
    ) -> ProgrammeCourseOffering:
        if not isinstance(programme_id, ProgrammeId) or not isinstance(
            course_id, CourseId
        ):
            raise ValueError(
                "ProgrammeCourseOffering.create requires validated identifiers"
            )
        return cls(programme_id, course_id)

    @classmethod
    def reconstitute(
        cls, programme_id: object, course_id: object
    ) -> ProgrammeCourseOffering | InvalidPersistedState:
        if not isinstance(programme_id, ProgrammeId) or not isinstance(
            course_id, CourseId
        ):
            return InvalidPersistedState()
        return cls(programme_id, course_id)

    def __post_init__(self) -> None:
        if not isinstance(self.programme_id, ProgrammeId):
            raise ValueError("programme_id requires ProgrammeId")
        if not isinstance(self.course_id, CourseId):
            raise ValueError("course_id requires CourseId")


@dataclass(frozen=True)
class Enrollment:
    student_id: StudentId
    course_id: CourseId

    @classmethod
    def create(cls, student_id: StudentId, course_id: CourseId) -> Enrollment:
        if not isinstance(student_id, StudentId) or not isinstance(course_id, CourseId):
            raise ValueError("Enrollment.create requires validated identifiers")
        return cls(student_id, course_id)

    @classmethod
    def reconstitute(
        cls, student_id: object, course_id: object
    ) -> Enrollment | InvalidPersistedState:
        if not isinstance(student_id, StudentId) or not isinstance(course_id, CourseId):
            return InvalidPersistedState()
        return cls(student_id, course_id)

    def __post_init__(self) -> None:
        if not isinstance(self.student_id, StudentId):
            raise ValueError("student_id requires StudentId")
        if not isinstance(self.course_id, CourseId):
            raise ValueError("course_id requires CourseId")
