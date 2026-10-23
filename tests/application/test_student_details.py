import pytest

from enrollment.adapters.persistence.sqlite import StudentSession, initialize
from enrollment.application.contracts import StorageFailure
from enrollment.application.student_contracts import EmailKeyConflict
from enrollment.application.student_details import save_student
from enrollment.domain.outcomes import InvalidIdentifier, InvalidStudentDetails
from enrollment.domain.values import StudentId
from tests.acceptance.test_student_details import invoke


def command(**changes):
    result = dict(
        mode="create",
        student_id="s",
        programme_id="p",
        name="Alex",
        email="alex@example.com",
    )
    result.update(changes)
    return result


def test_first_defect_stops_before_later_defects():
    def forbidden():
        pytest.fail("first defect opened storage")

    assert isinstance(
        save_student(command(student_id="", name=" "), forbidden), InvalidIdentifier
    )
    assert (
        save_student(command(name=" ", email="taken@example.com"), forbidden).field
        == "name"
    )


@pytest.mark.parametrize("field", ["student_id", "programme_id"])
def test_invalid_identifier_does_not_open(field):
    def forbidden():
        pytest.fail("invalid input opened storage")

    assert isinstance(
        save_student(command(**{field: ""}), forbidden), InvalidIdentifier
    )


def test_operation_modes_and_precise_outcomes(tmp_path):
    path = tmp_path / "db"
    initialize(path)
    assert invoke(path, mode="replace") == "STUDENT_NOT_FOUND"
    assert isinstance(invoke(path, mode="unknown"), InvalidStudentDetails)
    assert getattr(invoke(path), "student_id", None) == StudentId("s")
    assert invoke(path) == "STUDENT_ALREADY_EXISTS"


@pytest.mark.parametrize("stage", ["open", "read", "write", "commit", "close"])
def test_known_storage_failure(stage, tmp_path):
    path = tmp_path / "db"
    initialize(path)

    class Session(StudentSession):
        def student(self, identity):
            if stage == "read":
                raise StorageFailure()
            return super().student(identity)

        def save(self, candidate, replace):
            if stage == "write":
                raise StorageFailure()
            return super().save(candidate, replace)

        def commit(self):
            if stage == "commit":
                raise StorageFailure()
            super().commit()

        def close(self):
            super().close()
            if stage == "close":
                raise StorageFailure()

    def factory():
        if stage == "open":
            raise StorageFailure()
        return Session(path)

    assert save_student(command(), factory) == "STUDENT_STORAGE_FAILURE"


def test_returned_email_conflict(tmp_path):
    path = tmp_path / "db"
    initialize(path)

    class Conflict(StudentSession):
        def save(self, candidate, replace):
            return EmailKeyConflict

    assert save_student(command(), lambda: Conflict(path)) == "EMAIL_CONFLICT"


def test_primary_error_survives_cleanup(tmp_path, caplog):
    path = tmp_path / "db"
    initialize(path)

    class Broken(StudentSession):
        def student(self, identity):
            raise AssertionError("primary error")

        def close(self):
            super().close()
            raise StorageFailure("cleanup error")

    with pytest.raises(AssertionError, match="primary error"):
        save_student(command(), lambda: Broken(path))
    assert "Cleanup failed" in caplog.text
