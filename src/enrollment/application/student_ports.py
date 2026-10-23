from typing import Protocol

from enrollment.domain.outcomes import InvalidStudentDetails
from enrollment.domain.values import (
    ProgrammeId,
    SavedVersion,
    StudentEmail,
    StudentId,
    StudentName,
)

from .student_contracts import StudentResult, StudentSnapshot, StudentWrite


class StudentUnitOfWork(Protocol):
    def snapshot(self, identity: StudentId) -> StudentSnapshot | None: ...
    def email_owner(self, key: str) -> StudentId | None: ...
    def create_student(
        self,
        identity: StudentId,
        programme: ProgrammeId,
        name: StudentName,
        email: StudentEmail,
    ) -> StudentSnapshot | StudentWrite | StudentResult | InvalidStudentDetails: ...
    def replace_student(
        self,
        identity: StudentId,
        programme: ProgrammeId,
        name: StudentName,
        email: StudentEmail,
        expected_version: SavedVersion,
    ) -> StudentSnapshot | StudentWrite | StudentResult | InvalidStudentDetails: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


class StudentSessionFactory(Protocol):
    def __call__(self) -> StudentUnitOfWork: ...
