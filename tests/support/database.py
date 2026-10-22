from importlib.resources import files
from pathlib import Path

from enrollment.adapters.persistence.sqlite import connect

SCHEMA = files("enrollment.adapters.persistence").joinpath("schema.sql").read_text()


def seed(path: Path) -> None:
    with connect(path) as c:
        c.executescript(SCHEMA)
        c.execute("INSERT INTO programmes VALUES ('p')")
        c.execute(
            "INSERT INTO students(student_id,programme_id,name,email) VALUES ('s','p','Alex','alex@example.com')"
        )
        c.execute("INSERT INTO courses VALUES ('c')")
        c.execute("INSERT INTO programme_course_offerings VALUES ('p','c')")


def rows(path: Path) -> list[tuple[str, str]]:
    with connect(path) as c:
        return c.execute(
            "SELECT * FROM enrollments ORDER BY student_id,course_id"
        ).fetchall()
