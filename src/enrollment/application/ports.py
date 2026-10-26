from typing import Protocol

from enrollment.domain.models import (
    Course,
    Enrollment,
    Programme,
    ProgrammeCourseOffering,
    Student,
)
from enrollment.domain.outcomes import Rejection
from enrollment.domain.values import CourseId, ProgrammeId, StudentId, VerifiedIdentity

from .contracts import WriteResult


class IdentityVerifier(Protocol):
    def verify(self, credential: str | None) -> VerifiedIdentity | None: ...


class UnitOfWork(Protocol):
    def student(self, identity: StudentId) -> Student | None: ...
    def programme(self, identity: ProgrammeId) -> Programme | None: ...
    def course(self, identity: CourseId) -> Course | None: ...
    def enrollment(self, student: StudentId, course: CourseId) -> Enrollment | None: ...
    def offering(
        self, programme: ProgrammeId, course: CourseId
    ) -> ProgrammeCourseOffering | None: ...
    def create_enrollment(
        self, student: StudentId, course: CourseId
    ) -> Enrollment | WriteResult | Rejection: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...


class Closable(Protocol):
    def close(self) -> None: ...
