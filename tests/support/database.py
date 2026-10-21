import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE programmes(programme_id TEXT PRIMARY KEY);
CREATE TABLE students(student_id TEXT PRIMARY KEY, programme_id TEXT NOT NULL);
CREATE TABLE courses(course_id TEXT PRIMARY KEY);
CREATE TABLE programme_course_offerings(programme_id TEXT, course_id TEXT, PRIMARY KEY(programme_id,course_id));
CREATE TABLE enrollments(student_id TEXT, course_id TEXT, PRIMARY KEY(student_id,course_id));
"""


def seed(path: Path) -> None:
    with sqlite3.connect(path) as c:
        c.executescript(SCHEMA)
        c.execute("INSERT INTO programmes VALUES ('p')")
        c.execute("INSERT INTO students VALUES ('s','p')")
        c.execute("INSERT INTO courses VALUES ('c')")
        c.execute("INSERT INTO programme_course_offerings VALUES ('p','c')")


def rows(path: Path) -> list[tuple[str, str]]:
    with sqlite3.connect(path) as c:
        return c.execute(
            "SELECT * FROM enrollments ORDER BY student_id,course_id"
        ).fetchall()
