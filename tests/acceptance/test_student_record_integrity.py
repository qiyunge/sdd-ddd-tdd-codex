from enrollment.adapters.persistence.sqlite import connect
from enrollment.bootstrap import create_app
from tests.acceptance.test_enrollment import request


def test_corrupt_student_is_technical_failure(database):
    with connect(database) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute("UPDATE students SET name=' '")
    result = request(create_app(database, lambda credential: credential))
    assert result["data"]["enrollCourse"]["failureReason"] == "PERSISTENCE_FAILURE"
    with connect(database) as db:
        assert db.execute("SELECT * FROM enrollments").fetchall() == []
