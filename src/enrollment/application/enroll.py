from enrollment.domain import policies
from enrollment.domain.models import Enrollment
from enrollment.domain.outcomes import Rejection
from enrollment.domain.values import CourseId, StudentId

from .contracts import (
    Command,
    Failure,
    IdentityUnavailable,
    Result,
    StorageFailure,
    UniqueConflict,
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
    try:
        student_id = StudentId(command.student_id)
    except ValueError:
        return Failure.INVALID_REQUEST
    denial = policies.ownership(identity, student_id)
    if denial is not None:
        return denial
    try:
        course_id = CourseId(command.course_id)
    except ValueError:
        return Failure.INVALID_REQUEST
    try:
        return _attempt(student_id, course_id, sessions)
    except UniqueConflict:
        try:
            return _attempt(student_id, course_id, sessions)
        except StorageFailure:
            return Failure.PERSISTENCE_FAILURE
    except StorageFailure:
        return Failure.PERSISTENCE_FAILURE


def _attempt(
    student_id: StudentId, course_id: CourseId, sessions: UnitOfWorkFactory
) -> Result:
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
        session.add(enrollment)
        session.commit()
        return enrollment
    finally:
        session.close()
