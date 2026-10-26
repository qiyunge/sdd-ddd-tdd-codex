import re
import sqlite3
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path
from typing import TypeVar, cast

from enrollment.application.cleanup import close_preserving_failure
from enrollment.application.contracts import (
    DataIntegrityFailure,
    PairConflict,
    StorageFailure,
    WriteResult,
)
from enrollment.application.student_contracts import (
    EmailKeyConflict,
    StudentResult,
    StudentSnapshot,
    StudentWrite,
    VersionConflict,
)
from enrollment.domain.models import (
    Course,
    Enrollment,
    Programme,
    ProgrammeCourseOffering,
    Student,
)
from enrollment.domain.outcomes import (
    InvalidIdentifier,
    InvalidPersistedState,
    InvalidSavedVersion,
    InvalidStudentDetails,
    Rejection,
)
from enrollment.domain.values import (
    CourseId,
    Identifier,
    ProgrammeId,
    RequiredText,
    SavedVersion,
    StudentEmail,
    StudentId,
    StudentName,
)

T = TypeVar("T")


class Session:
    def __init__(self, path: Path, timeout: float = 5.0) -> None:
        self._canceled = False
        try:
            self.connection = connect(path, autocommit=True, timeout=timeout)
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.connection.execute("BEGIN IMMEDIATE")
        except sqlite3.Error as exc:
            try:
                if hasattr(self, "connection"):
                    self.connection.close()
            except sqlite3.Error:
                pass  # Preserve the original open/lock failure as a Core storage error.
            raise StorageFailure() from exc

    def _read(
        self, sql: str, args: tuple[str, ...], convert: Callable[[tuple[str, ...]], T]
    ) -> T | None:
        self._usable()
        try:
            row = self.connection.execute(sql, args).fetchone()
            return None if row is None else convert(row)
        except sqlite3.Error as exc:
            raise StorageFailure() from exc

    def student(self, s: StudentId) -> Student | None:
        snapshot = self._student_snapshot(s)
        return None if snapshot is None else snapshot.student

    def _student_snapshot(self, identity: StudentId) -> StudentSnapshot | None:
        return self._read(
            "SELECT student_id,programme_id,name,email,saved_version FROM students WHERE student_id=?",
            (identity.value,),
            snapshot_from_row,
        )

    def programme(self, p: ProgrammeId) -> Programme | None:
        return self._read(
            "SELECT programme_id FROM programmes WHERE programme_id=?",
            (p.value,),
            lambda r: restored(Programme.reconstitute(decode(ProgrammeId, r[0]))),
        )

    def course(self, c: CourseId) -> Course | None:
        return self._read(
            "SELECT course_id FROM courses WHERE course_id=?",
            (c.value,),
            lambda r: restored(Course.reconstitute(decode(CourseId, r[0]))),
        )

    def enrollment(self, s: StudentId, c: CourseId) -> Enrollment | None:
        return self._read(
            "SELECT student_id,course_id FROM enrollments WHERE student_id=? AND course_id=?",
            (s.value, c.value),
            lambda r: restored(
                Enrollment.reconstitute(decode(StudentId, r[0]), decode(CourseId, r[1]))
            ),
        )

    def offering(self, p: ProgrammeId, c: CourseId) -> ProgrammeCourseOffering | None:
        return self._read(
            "SELECT programme_id,course_id FROM programme_course_offerings WHERE programme_id=? AND course_id=?",
            (p.value, c.value),
            lambda r: restored(
                ProgrammeCourseOffering.reconstitute(
                    decode(ProgrammeId, r[0]), decode(CourseId, r[1])
                )
            ),
        )

    def create_enrollment(
        self, student: StudentId, course: CourseId
    ) -> Enrollment | WriteResult | Rejection:
        self._usable()
        try:
            self.connection.execute(
                "INSERT INTO enrollments(student_id,course_id) VALUES (?,?)",
                (student.value, course.value),
            )
        except sqlite3.IntegrityError as exc:
            if (
                exc.sqlite_errorname
                in ("SQLITE_CONSTRAINT_PRIMARYKEY", "SQLITE_CONSTRAINT_UNIQUE")
                and str(exc)
                == "UNIQUE constraint failed: enrollments.student_id, enrollments.course_id"
            ):
                self._cancel()
                return PairConflict
            self._cancel_preserving_failure()
            raise StorageFailure() from exc
        except sqlite3.Error as exc:
            self._cancel_preserving_failure()
            raise StorageFailure() from exc
        except Exception:
            self._cancel_preserving_failure()
            raise
        try:
            row = self.connection.execute(
                "SELECT student_id,course_id FROM enrollments WHERE student_id=? AND course_id=?",
                (student.value, course.value),
            ).fetchone()
            pending: Enrollment | Rejection = Enrollment.create(
                decode(StudentId, row[0]), decode(CourseId, row[1])
            )
            if not isinstance(pending, Enrollment):
                self._cancel()
            return pending
        except sqlite3.Error as exc:
            self._cancel_preserving_failure()
            raise StorageFailure() from exc
        except Exception:
            self._cancel_preserving_failure()
            raise

    def create_programme(self, programme: ProgrammeId) -> Programme:
        return self._provision(
            "INSERT INTO programmes(programme_id) VALUES (?)",
            (programme.value,),
            "SELECT programme_id FROM programmes WHERE programme_id=?",
            lambda row: Programme.create(decode(ProgrammeId, row[0])),
        )

    def create_course(self, course: CourseId) -> Course:
        return self._provision(
            "INSERT INTO courses(course_id) VALUES (?)",
            (course.value,),
            "SELECT course_id FROM courses WHERE course_id=?",
            lambda row: Course.create(decode(CourseId, row[0])),
        )

    def create_offering(
        self, programme: ProgrammeId, course: CourseId
    ) -> ProgrammeCourseOffering:
        return self._provision(
            "INSERT INTO programme_course_offerings(programme_id,course_id) VALUES (?,?)",
            (programme.value, course.value),
            "SELECT programme_id,course_id FROM programme_course_offerings WHERE programme_id=? AND course_id=?",
            lambda row: ProgrammeCourseOffering.create(
                decode(ProgrammeId, row[0]), decode(CourseId, row[1])
            ),
        )

    def _provision(
        self,
        sql: str,
        args: tuple[str, ...],
        query: str,
        factory: Callable[[tuple[str, ...]], T],
    ) -> T:
        self._usable()
        try:
            self.connection.execute(sql, args)
            row = self.connection.execute(query, args).fetchone()
            return factory(row)
        except sqlite3.Error as exc:
            self._cancel_preserving_failure()
            raise StorageFailure() from exc
        except Exception:
            self._cancel_preserving_failure()
            raise

    def _usable(self) -> None:
        if self._canceled:
            raise StorageFailure("Canceled unit of work")

    def _cancel(self) -> None:
        self._canceled = True
        self.rollback()

    def _cancel_preserving_failure(self) -> None:
        try:
            self._cancel()
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Rollback failed while preserving creation error"
            )

    def commit(self) -> None:
        self._usable()
        try:
            self.connection.execute("COMMIT")
        except sqlite3.Error as exc:
            raise StorageFailure() from exc

    def rollback(self) -> None:
        try:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
        except sqlite3.Error as exc:
            raise StorageFailure() from exc

    def close(self) -> None:
        try:
            try:
                self.rollback()
            finally:
                close_preserving_failure(self.connection)
        except sqlite3.Error as exc:
            raise StorageFailure() from exc


def initialize(path: Path) -> None:
    connection = connect(path, autocommit=True)
    try:
        schema = (
            files("enrollment.adapters.persistence").joinpath("schema.sql").read_text()
        )
        existing = schema_objects(connection)
        if existing:
            reference = connect(Path(":memory:"), autocommit=True)
            try:
                reference.executescript(schema)
                expected = schema_objects(reference)
            finally:
                reference.close()
            if any(existing.get(key) != sql for key, sql in expected.items()):
                raise StorageFailure(
                    "Legacy or incompatible schema requires external migration"
                )
            for (version,) in connection.execute("SELECT saved_version FROM students"):
                decode(SavedVersion, version)
        else:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.executescript(schema)
    except sqlite3.Error as exc:
        raise StorageFailure("Incompatible persistence schema") from exc
    finally:
        close_preserving_failure(connection)


def schema_objects(connection: sqlite3.Connection) -> dict[str, str]:
    return {
        name: re.sub(r"\s+", "", sql).lower()
        for name, sql in connection.execute(
            "SELECT name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
        )
    }


def snapshot_from_row(row: tuple[object, ...]) -> StudentSnapshot:
    version = decode(SavedVersion, row[4])
    student = restored(
        Student.reconstitute(
            decode(StudentId, row[0]),
            decode(ProgrammeId, row[1]),
            decode(StudentName, row[2]),
            decode(StudentEmail, row[3]),
        )
    )
    return StudentSnapshot(student, version)


def restored[R](record: R | InvalidPersistedState) -> R:
    if isinstance(record, InvalidPersistedState):
        raise DataIntegrityFailure("Invalid persisted Domain value")
    return record


def decode[V: Identifier | RequiredText | SavedVersion](
    kind: type[V], raw: object
) -> V:
    result = kind.create(raw)
    if isinstance(
        result, (InvalidIdentifier, InvalidStudentDetails, InvalidSavedVersion)
    ):
        raise DataIntegrityFailure("Invalid persisted Domain value")
    # Factory Self is preserved at runtime; mypy erases the union-bound generic.
    return cast(V, result)


def sql_email_key(raw: object) -> str | None:
    result = StudentEmail.create(raw)
    return None if isinstance(result, InvalidStudentDetails) else result.key


def connect(
    path: Path, *, autocommit: bool | None = None, timeout: float = 5.0
) -> sqlite3.Connection:
    if autocommit is None:
        connection = sqlite3.connect(path, timeout=timeout)
    else:
        connection = sqlite3.connect(path, autocommit=autocommit, timeout=timeout)
    connection.create_function(
        "required_text",
        1,
        lambda value: not isinstance(StudentName.create(value), InvalidStudentDetails),
        deterministic=True,
    )
    connection.create_function("email_key", 1, sql_email_key, deterministic=True)
    return connection


class StudentSession(Session):
    def snapshot(self, identity: StudentId) -> StudentSnapshot | None:
        return self._student_snapshot(identity)

    def email_owner(self, key: str) -> StudentId | None:
        return self._read(
            "SELECT student_id FROM students WHERE email_key(email)=?",
            (key,),
            lambda r: decode(StudentId, r[0]),
        )

    def replace_student(
        self,
        identity: StudentId,
        programme: ProgrammeId,
        name: StudentName,
        email: StudentEmail,
        expected_version: SavedVersion,
    ) -> StudentSnapshot | StudentResult | StudentWrite | InvalidStudentDetails:
        """Even identical-detail replacement consumes a new saved version; old field values restored later cannot revive an old token.

        Reaching the maximum on a requested replacement is a technical persistence limitation: no update, no version wrap/reuse.
        """
        self._usable()
        try:
            current = self.snapshot(identity)
            if current is None:
                return StudentResult.NOT_FOUND
            if expected_version.value == SavedVersion.maximum:
                raise StorageFailure("Saved version exhausted")
            changed: Student | InvalidStudentDetails = current.student.replace_details(
                programme, name, email
            )
            if isinstance(changed, InvalidStudentDetails):
                self._cancel()
                return changed
            cursor = self.connection.execute(
                "UPDATE students SET programme_id=?,name=?,email=?,saved_version=saved_version+1 WHERE student_id=? AND saved_version=?",
                (
                    programme.value,
                    name.value,
                    email.value,
                    identity.value,
                    expected_version.value,
                ),
            )
            if cursor.rowcount != 1:
                self._cancel()
                return VersionConflict
            row = self.connection.execute(
                "SELECT saved_version FROM students WHERE student_id=?",
                (identity.value,),
            ).fetchone()
            return StudentSnapshot(changed, decode(SavedVersion, row[0]))
        except sqlite3.IntegrityError as exc:
            self._cancel()
            if (
                exc.sqlite_errorname
                in ("SQLITE_CONSTRAINT_UNIQUE", "SQLITE_CONSTRAINT_PRIMARYKEY")
                and str(exc) == "UNIQUE constraint failed: index 'students_email_key'"
            ):
                return EmailKeyConflict
            raise StorageFailure() from exc
        except sqlite3.Error as exc:
            self._cancel_preserving_failure()
            raise StorageFailure() from exc
        except Exception:
            self._cancel_preserving_failure()
            raise

    def create_student(
        self,
        identity: StudentId,
        programme: ProgrammeId,
        name: StudentName,
        email: StudentEmail,
    ) -> StudentSnapshot | StudentResult | StudentWrite | InvalidStudentDetails:
        """Repositories insert 1 explicitly for fresh Students; no silent version assignment is applied to existing schemas."""
        self._usable()
        try:
            self.connection.execute(
                "INSERT INTO students(student_id,programme_id,name,email,saved_version) VALUES (?,?,?,?,1)",
                (identity.value, programme.value, name.value, email.value),
            )
            row = self.connection.execute(
                "SELECT student_id,saved_version FROM students WHERE student_id=?",
                (identity.value,),
            ).fetchone()
            pending: Student | InvalidStudentDetails = Student.create(
                decode(StudentId, row[0]), programme, name, email
            )
            if isinstance(pending, InvalidStudentDetails):
                self._cancel()
                return pending
            return StudentSnapshot(pending, decode(SavedVersion, row[1]))
        except sqlite3.IntegrityError as exc:
            self._cancel()
            if str(exc) == "UNIQUE constraint failed: students.student_id":
                return StudentResult.ALREADY_EXISTS
            if str(exc) == "UNIQUE constraint failed: index 'students_email_key'":
                return EmailKeyConflict
            raise StorageFailure() from exc
        except sqlite3.Error as exc:
            self._cancel_preserving_failure()
            raise StorageFailure() from exc
        except Exception:
            self._cancel_preserving_failure()
            raise
