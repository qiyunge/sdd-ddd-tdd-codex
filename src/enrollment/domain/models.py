from __future__ import annotations

from dataclasses import dataclass

from .outcomes import InvalidIdentifier, InvalidStudentDetails
from .values import CourseId, ProgrammeId, StudentEmail, StudentId, StudentName


@dataclass(frozen=True, eq=False)
class Student:
    student_id: StudentId
    programme_id: ProgrammeId
    name: StudentName
    email: StudentEmail

    @classmethod
    def create(
        cls, student_id: object, programme_id: object, name: object, email: object
    ) -> Student | InvalidIdentifier | InvalidStudentDetails:
        identity = StudentId.create(student_id)
        if isinstance(identity, InvalidIdentifier):
            return identity
        programme = ProgrammeId.create(programme_id)
        if isinstance(programme, InvalidIdentifier):
            return programme
        parsed_name = StudentName.create(name)
        if isinstance(parsed_name, InvalidStudentDetails):
            return parsed_name
        parsed_email = StudentEmail.create(email)
        if isinstance(parsed_email, InvalidStudentDetails):
            return parsed_email
        return cls(identity, programme, parsed_name, parsed_email)

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

    @classmethod
    def create(
        cls, student_id: object, course_id: object
    ) -> Enrollment | InvalidIdentifier:
        student = StudentId.create(student_id)
        if isinstance(student, InvalidIdentifier):
            return student
        course = CourseId.create(course_id)
        if isinstance(course, InvalidIdentifier):
            return course
        return cls(student, course)

    def __post_init__(self) -> None:
        if not isinstance(self.student_id, StudentId):
            raise ValueError("student_id requires StudentId")
        if not isinstance(self.course_id, CourseId):
            raise ValueError("course_id requires CourseId")
