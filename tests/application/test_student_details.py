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
    assert invoke(path, mode="replace", expected_version=1) == "STUDENT_NOT_FOUND"
    assert isinstance(invoke(path, mode="unknown"), InvalidStudentDetails)
    assert invoke(path).student.student_id == StudentId.create("s")
    assert invoke(path) == "STUDENT_ALREADY_EXISTS"


@pytest.mark.parametrize("stage", ["open", "read", "write", "commit", "close"])
def test_known_storage_failure(stage, tmp_path):
    path = tmp_path / "db"
    initialize(path)

    class Session(StudentSession):
        def snapshot(self, identity):
            if stage == "read":
                raise StorageFailure()
            return super().snapshot(identity)

        def create_student(self, *args):
            if stage == "write":
                raise StorageFailure()
            return super().create_student(*args)

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
        def create_student(self, *args):
            return EmailKeyConflict

    assert save_student(command(), lambda: Conflict(path)) == "EMAIL_CONFLICT"


def test_primary_error_survives_cleanup(tmp_path, caplog):
    path = tmp_path / "db"
    initialize(path)

    class Broken(StudentSession):
        def snapshot(self, identity):
            raise AssertionError("primary error")

        def close(self):
            super().close()
            raise StorageFailure("cleanup error")

    with pytest.raises(AssertionError, match="primary error"):
        save_student(command(), lambda: Broken(path))
    assert "Cleanup failed" in caplog.text


def test_snapshot_creation_ignores_version_and_read_finishes_before_return(tmp_path):
    from enrollment.application.student_details import get_student
    from enrollment.domain.values import SavedVersion

    path = tmp_path / "db"
    initialize(path)
    created = save_student(
        command(expected_version=False), lambda: StudentSession(path)
    )
    assert created.saved_version == SavedVersion.create(1)
    calls = []

    class Read(StudentSession):
        def commit(self):
            calls.append("commit")
            super().commit()

        def close(self):
            calls.append("close")
            super().close()

    result = get_student("s", lambda: Read(path))
    assert calls == ["commit", "close"] and result == created
    assert isinstance(get_student("", lambda: None), InvalidIdentifier)
    assert get_student("absent", lambda: StudentSession(path)) == "STUDENT_NOT_FOUND"


@pytest.mark.parametrize(
    "observation,expected",
    [("version", "OutdatedVersion"), ("email", "EMAIL_CONFLICT")],
)
def test_defensive_replacement_observations_do_not_replay(
    tmp_path, observation, expected
):
    from enrollment.application.student_contracts import VersionConflict

    path = tmp_path / "db"
    initialize(path)
    invoke(path)
    calls = []

    class Observed(StudentSession):
        def replace_student(self, *args):
            calls.append(args)
            return VersionConflict if observation == "version" else EmailKeyConflict

        def commit(self):
            pytest.fail("Rejected replacement must not commit")

    result = save_student(
        command(mode="replace", expected_version=1), lambda: Observed(path)
    )
    assert len(calls) == 1, "No automatic refresh/replay is allowed"
    assert (
        type(result).__name__ == expected
        if observation == "version"
        else result == expected
    )
