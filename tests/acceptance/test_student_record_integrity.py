import pytest

from enrollment.adapters.persistence.sqlite import connect
from enrollment.bootstrap import create_app
from tests.acceptance.test_enrollment import request


def test_corrupt_student_is_technical_failure(database):
    with connect(database) as db:
        db.execute("DROP TRIGGER students_saved_version_guard")
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute("UPDATE students SET name=' '")
    result = request(create_app(database, lambda credential: credential))
    assert result["data"]["enrollCourse"]["failureReason"] == "PERSISTENCE_FAILURE"
    with connect(database) as db:
        assert db.execute("SELECT * FROM enrollments").fetchall() == []


@pytest.mark.parametrize("version", [0, -1, 1.5, "corrupt"])
def test_corrupt_saved_version_fails_both_boundaries(database, version):
    from enrollment.adapters.persistence.sqlite import StudentSession
    from enrollment.application.student_details import get_student

    with connect(database) as db:
        db.execute("DROP TRIGGER students_saved_version_guard")
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute("UPDATE students SET saved_version=?", (version,))
    assert (
        get_student("s", lambda: StudentSession(database)) == "STUDENT_STORAGE_FAILURE"
    )
    result = request(create_app(database, lambda c: c))
    assert result["data"]["enrollCourse"]["failureReason"] == "PERSISTENCE_FAILURE"
    with connect(database) as db:
        assert db.execute("SELECT * FROM enrollments").fetchall() == []
