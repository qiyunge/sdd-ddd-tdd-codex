import sqlite3
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path
from typing import TypeVar

from enrollment.application.contracts import StorageFailure, UniqueConflict
from enrollment.domain.models import (
    Course,
    Enrollment,
    Programme,
    ProgrammeCourseOffering,
    Student,
)
from enrollment.domain.values import CourseId, ProgrammeId, StudentId

T = TypeVar("T")


class Session:
    def __init__(self, path: Path, timeout: float = 5.0) -> None:
        try:
            self.connection = sqlite3.connect(path, autocommit=True, timeout=timeout)
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
        except (sqlite3.Error, ValueError) as exc:
            raise StorageFailure() from exc

    def student(self, s: StudentId) -> Student | None:
        return self._read(
            "SELECT student_id,programme_id FROM students WHERE student_id=?",
            (s.value,),
            lambda r: Student(StudentId(r[0]), ProgrammeId(r[1])),
        )

    def programme(self, p: ProgrammeId) -> Programme | None:
        return self._read(
            "SELECT programme_id FROM programmes WHERE programme_id=?",
            (p.value,),
            lambda r: Programme(ProgrammeId(r[0])),
        )

    def course(self, c: CourseId) -> Course | None:
        return self._read(
            "SELECT course_id FROM courses WHERE course_id=?",
            (c.value,),
            lambda r: Course(CourseId(r[0])),
        )

    def enrollment(self, s: StudentId, c: CourseId) -> Enrollment | None:
        return self._read(
            "SELECT student_id,course_id FROM enrollments WHERE student_id=? AND course_id=?",
            (s.value, c.value),
            lambda r: Enrollment(StudentId(r[0]), CourseId(r[1])),
        )

    def offering(self, p: ProgrammeId, c: CourseId) -> ProgrammeCourseOffering | None:
        return self._read(
            "SELECT programme_id,course_id FROM programme_course_offerings WHERE programme_id=? AND course_id=?",
            (p.value, c.value),
            lambda r: ProgrammeCourseOffering(ProgrammeId(r[0]), CourseId(r[1])),
        )

    def add(self, e: Enrollment) -> None:
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
                raise UniqueConflict() from exc
            raise StorageFailure() from exc
        except sqlite3.Error as exc:
            raise StorageFailure() from exc

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
                self.connection.close()
        except sqlite3.Error as exc:
            raise StorageFailure() from exc


def initialize(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(
            files("enrollment.adapters.persistence").joinpath("schema.sql").read_text()
        )
