from importlib.resources import files
from pathlib import Path

from enrollment.adapters.persistence.sqlite import Session, connect
from enrollment.domain.values import CourseId, ProgrammeId

SCHEMA = files("enrollment.adapters.persistence").joinpath("schema.sql").read_text()


def seed(path: Path) -> None:
    with connect(path) as c:
        c.executescript(SCHEMA)
        c.execute(
            "INSERT INTO students(student_id,programme_id,name,email,saved_version) VALUES ('s','p','Alex','alex@example.com',1)"
        )
    session = Session(path)
    try:
        session.create_programme(ProgrammeId.create("p"))
        session.create_course(CourseId.create("c"))
        session.create_offering(ProgrammeId.create("p"), CourseId.create("c"))
        session.commit()
    finally:
        session.close()


def rows(path: Path) -> list[tuple[str, str]]:
    with connect(path) as c:
        return c.execute(
            "SELECT * FROM enrollments ORDER BY student_id,course_id"
        ).fetchall()
