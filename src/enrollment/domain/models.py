from dataclasses import dataclass

from .values import CourseId, ProgrammeId, StudentId


@dataclass(frozen=True)
class Student:
    student_id: StudentId
    programme_id: ProgrammeId

    def __post_init__(self) -> None:
        if not isinstance(self.student_id, StudentId):
            raise ValueError("student_id requires StudentId")
        if not isinstance(self.programme_id, ProgrammeId):
            raise ValueError("programme_id requires ProgrammeId")


@dataclass(frozen=True)
class Programme:
    programme_id: ProgrammeId

    def __post_init__(self) -> None:
        if not isinstance(self.programme_id, ProgrammeId):
            raise ValueError("programme_id requires ProgrammeId")


@dataclass(frozen=True)
class Course:
    course_id: CourseId

    def __post_init__(self) -> None:
        if not isinstance(self.course_id, CourseId):
            raise ValueError("course_id requires CourseId")


@dataclass(frozen=True)
class ProgrammeCourseOffering:
    programme_id: ProgrammeId
    course_id: CourseId

    def __post_init__(self) -> None:
        if not isinstance(self.programme_id, ProgrammeId):
            raise ValueError("programme_id requires ProgrammeId")
        if not isinstance(self.course_id, CourseId):
            raise ValueError("course_id requires CourseId")


@dataclass(frozen=True)
class Enrollment:
    student_id: StudentId
    course_id: CourseId

    def __post_init__(self) -> None:
        if not isinstance(self.student_id, StudentId):
            raise ValueError("student_id requires StudentId")
        if not isinstance(self.course_id, CourseId):
            raise ValueError("course_id requires CourseId")
