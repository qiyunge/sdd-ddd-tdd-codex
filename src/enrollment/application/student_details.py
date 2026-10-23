"""Trusted host operation; no HTTP/GraphQL management endpoint."""

from enrollment.domain.models import Student
from enrollment.domain.outcomes import (
    DetailRejection,
    InvalidIdentifier,
    InvalidStudentDetails,
)
from enrollment.domain.policies import email_available
from enrollment.domain.values import ProgrammeId, StudentEmail, StudentId, StudentName

from .cleanup import close_preserving_failure
from .contracts import StorageFailure
from .student_contracts import EmailKeyConflict, StudentResult
from .student_ports import StudentSessionFactory

DetailResult = (
    Student
    | StudentResult
    | DetailRejection
    | InvalidIdentifier
    | InvalidStudentDetails
)


def save_student(
    command: dict[str, object], sessions: StudentSessionFactory
) -> DetailResult:
    student_id = StudentId.create(command.get("student_id"))
    if isinstance(student_id, InvalidIdentifier):
        return student_id
    programme_id = ProgrammeId.create(command.get("programme_id"))
    if isinstance(programme_id, InvalidIdentifier):
        return programme_id
    name = StudentName.create(command.get("name"))
    if isinstance(name, InvalidStudentDetails):
        return name
    email = StudentEmail.create(command.get("email"))
    if isinstance(email, InvalidStudentDetails):
        return email
    mode = command.get("mode")
    if mode not in ("create", "replace"):
        return InvalidStudentDetails("mode")
    candidate = Student.create(student_id, programme_id, name, email)
    identity = student_id
    try:
        session = sessions()
        try:
            existing = session.student(identity)
            if mode == "create" and existing is not None:
                return StudentResult.ALREADY_EXISTS
            if mode == "replace" and existing is None:
                return StudentResult.NOT_FOUND
            rejection = email_available(session.email_owner(email.key), identity)
            if rejection is not None:
                return rejection
            saved = session.save(candidate, mode == "replace")
            if saved == EmailKeyConflict:
                return DetailRejection.EMAIL_CONFLICT
            session.commit()
            return candidate
        finally:
            close_preserving_failure(session)
    except StorageFailure:
        return StudentResult.STORAGE_FAILURE
