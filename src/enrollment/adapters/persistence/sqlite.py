import sqlite3
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path
from typing import TypeVar, cast

from enrollment.application.cleanup import close_preserving_failure
from enrollment.application.contracts import (
    Added,
    DataIntegrityFailure,
    PairConflict,
    StorageFailure,
    WriteResult,
)
from enrollment.application.student_contracts import (
    EmailKeyConflict,
    Saved,
    StudentWrite,
)
from enrollment.domain.models import (
    Course,
    Enrollment,
    Programme,
    ProgrammeCourseOffering,
    Student,
)
from enrollment.domain.outcomes import InvalidPersistedState, InvalidStudentDetails
from enrollment.domain.values import (
    CourseId,
    Identifier,
    ProgrammeId,
    RequiredText,
    StudentEmail,
    StudentId,
    StudentName,
)

T = TypeVar("T")


class Session:
    def __init__(self, path: Path, timeout: float = 5.0) -> None:
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
        try:
            row = self.connection.execute(sql, args).fetchone()
            return None if row is None else convert(row)
        except sqlite3.Error as exc:
            raise StorageFailure() from exc

    def student(self, s: StudentId) -> Student | None:
        return self._read(
            "SELECT student_id,programme_id,name,email FROM students WHERE student_id=?",
            (s.value,),
            lambda r: restored(
                Student.reconstitute(
                    decode(StudentId, r[0]),
                    decode(ProgrammeId, r[1]),
                    decode(StudentName, r[2]),
                    decode(StudentEmail, r[3]),
                )
            ),
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

    def add(self, e: Enrollment) -> WriteResult:
        try:
            self.connection.execute(
                "INSERT INTO enrollments(student_id,course_id) VALUES (?,?)",
                (e.student_id.value, e.course_id.value),
            )
        except sqlite3.IntegrityError as exc:
            if (
                exc.sqlite_errorname
                in ("SQLITE_CONSTRAINT_PRIMARYKEY", "SQLITE_CONSTRAINT_UNIQUE")
                and str(exc)
                == "UNIQUE constraint failed: enrollments.student_id, enrollments.course_id"
            ):
                return PairConflict
            raise StorageFailure() from exc
        except sqlite3.Error as exc:
            raise StorageFailure() from exc
        return Added

    def commit(self) -> None:
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
    with connect(path) as connection:
        columns = {r[1] for r in connection.execute("PRAGMA table_info(students)")}
        if columns and not {"name", "email"} <= columns:
            raise StorageFailure("Legacy Student schema requires external migration")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(
            files("enrollment.adapters.persistence").joinpath("schema.sql").read_text()
        )


def restored[R](record: R | InvalidPersistedState) -> R:
    if isinstance(record, InvalidPersistedState):
        raise DataIntegrityFailure("Invalid persisted Domain value")
    return record


def decode[V: Identifier | RequiredText](kind: type[V], raw: object) -> V:
    result = kind.reconstitute(raw)
    if isinstance(result, InvalidPersistedState):
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
    def email_owner(self, key: str) -> StudentId | None:
        return self._read(
            "SELECT student_id FROM students WHERE email_key(email)=?",
            (key,),
            lambda r: decode(StudentId, r[0]),
        )

    def save(self, candidate: Student, replace: bool) -> StudentWrite:
        args = (
            candidate.programme_id.value,
            candidate.name.value,
            candidate.email.value,
            candidate.student_id.value,
        )
        try:
            if replace:
                self.connection.execute(
                    "UPDATE students SET programme_id=?,name=?,email=? WHERE student_id=?",
                    args,
                )
            else:
                self.connection.execute(
                    "INSERT INTO students(programme_id,name,email,student_id) VALUES (?,?,?,?)",
                    args,
                )
            return Saved
        except sqlite3.IntegrityError as exc:
            if str(exc) == "UNIQUE constraint failed: index 'students_email_key'":
                return EmailKeyConflict
            raise StorageFailure() from exc
        except sqlite3.Error as exc:
            raise StorageFailure() from exc
