from enrollment.domain import policies
from enrollment.domain.models import Enrollment
from enrollment.domain.outcomes import InvalidIdentifier, Rejection
from enrollment.domain.values import CourseId, StudentId

from .cleanup import close_preserving_failure
from .contracts import (
    Command,
    Failure,
    IdentityUnavailable,
    PairConflict,
    Result,
    StorageFailure,
    WriteResult,
)
from .ports import IdentityVerifier, UnitOfWorkFactory


def enroll(
    command: Command, verifier: IdentityVerifier, sessions: UnitOfWorkFactory
) -> Result:
    try:
        identity = verifier.verify(command.credential)
    except IdentityUnavailable:
        return Failure.IDENTITY_UNAVAILABLE
    if identity is None:
        return Rejection.DENIED
    student_id = StudentId.create(command.student_id)
    if isinstance(student_id, InvalidIdentifier):
        return Failure.INVALID_REQUEST
    denial = policies.ownership(identity, student_id)
    if denial is not None:
        return denial
    course_id = CourseId.create(command.course_id)
    if isinstance(course_id, InvalidIdentifier):
        return Failure.INVALID_REQUEST
    try:
        result = _attempt(student_id, course_id, sessions)
        if result == PairConflict:
            result = _attempt(student_id, course_id, sessions)
        return (
            Failure.PERSISTENCE_FAILURE if isinstance(result, WriteResult) else result
        )
    except StorageFailure:
        return Failure.PERSISTENCE_FAILURE


def _attempt(
    student_id: StudentId, course_id: CourseId, sessions: UnitOfWorkFactory
) -> Result | WriteResult:
    session = sessions()
    try:
        student = session.student(student_id)
        if student is None:
            return Failure.MISSING_STUDENT
        programme = session.programme(student.programme_id)
        if programme is None:
            return Failure.MISSING_PROGRAMME
        course = session.course(course_id)
        if course is None:
            return Failure.MISSING_COURSE
        rejection = policies.duplicate(session.enrollment(student_id, course_id))
        if rejection is not None:
            return rejection
        rejection = policies.eligibility(
            session.offering(programme.programme_id, course_id)
        )
        if rejection is not None:
            return rejection
        enrollment = Enrollment(student_id, course_id)
        if session.add(enrollment) == PairConflict:
            return PairConflict
        session.commit()
        return enrollment
    finally:
        close_preserving_failure(session)
