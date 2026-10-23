"""Trusted host operations; snapshots leave only after commit and resource cleanup."""

from enrollment.domain.outcomes import (
    DetailRejection,
    InvalidIdentifier,
    InvalidSavedVersion,
    InvalidStudentDetails,
    OutdatedVersion,
)
from enrollment.domain.policies import email_available, version_current
from enrollment.domain.values import (
    ProgrammeId,
    SavedVersion,
    StudentEmail,
    StudentId,
    StudentName,
)

from .cleanup import close_preserving_failure
from .contracts import StorageFailure
from .student_contracts import (
    EmailKeyConflict,
    StudentResult,
    StudentSnapshot,
    StudentWrite,
)
from .student_ports import StudentSessionFactory

DetailResult = (
    StudentSnapshot
    | StudentResult
    | DetailRejection
    | InvalidIdentifier
    | InvalidStudentDetails
    | InvalidSavedVersion
    | OutdatedVersion
)


def get_student(
    student_id: object, sessions: StudentSessionFactory
) -> StudentSnapshot | StudentResult | InvalidIdentifier:
    identity = StudentId.create(student_id)
    if isinstance(identity, InvalidIdentifier):
        return identity
    try:
        session = sessions()
        try:
            result = session.snapshot(identity)
            session.commit()
            return StudentResult.NOT_FOUND if result is None else result
        finally:
            close_preserving_failure(session)
    except StorageFailure:
        return StudentResult.STORAGE_FAILURE


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
    expected = None
    if mode == "replace":
        version = SavedVersion.create(command.get("expected_version"))
        if isinstance(version, InvalidSavedVersion):
            return version
        expected = version
    try:
        session = sessions()
        try:
            existing = session.snapshot(student_id)
            if mode == "create" and existing is not None:
                return StudentResult.ALREADY_EXISTS
            if mode == "replace" and existing is None:
                return StudentResult.NOT_FOUND
            if expected is not None:
                assert existing is not None
                outdated = version_current(expected, existing.saved_version)
                if outdated is not None:
                    return outdated
            rejection = email_available(session.email_owner(email.key), student_id)
            if rejection is not None:
                return rejection
            if expected is None:
                pending = session.create_student(student_id, programme_id, name, email)
            else:
                pending = session.replace_student(
                    student_id, programme_id, name, email, expected
                )
            if isinstance(pending, StudentWrite):
                return (
                    DetailRejection.EMAIL_CONFLICT
                    if pending == EmailKeyConflict
                    else OutdatedVersion()
                )
            if not isinstance(pending, StudentSnapshot):
                return pending
            session.commit()
            return pending
        finally:
            close_preserving_failure(session)
    except StorageFailure:
        return StudentResult.STORAGE_FAILURE
