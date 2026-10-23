from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from enrollment.adapters.persistence.sqlite import Session, StudentSession, connect
from enrollment.application.student_details import get_student, save_student
from enrollment.bootstrap import create_app
from tests.acceptance.test_enrollment import request
from tests.support.database import rows


@pytest.mark.parametrize("change", ["offering", "membership"])
def test_change_before_lock(database, change):
    original = get_student("s", lambda: StudentSession(database))

    def verify(c):
        with connect(database) as db:
            if change == "offering":
                db.execute("DELETE FROM programme_course_offerings")
            else:
                db.execute("INSERT INTO programmes VALUES ('new')")
        if change == "membership":
            save_student(
                dict(
                    mode="replace",
                    expected_version=original.saved_version.value,
                    student_id="s",
                    programme_id="new",
                    name="Alex",
                    email="alex@example.com",
                ),
                lambda: StudentSession(database),
            )
        return c

    assert (
        request(create_app(database, verify))["data"]["enrollCourse"]["reason"]
        == "COURSE_NOT_OFFERED"
    )
    assert rows(database) == []


@pytest.mark.parametrize("change", ["offering", "membership"])
def test_writer_waits_until_commit(database, monkeypatch, change):
    snapshot = get_student("s", lambda: StudentSession(database))
    locked = Event()
    attempting = Event()
    finished = Event()
    original = Session.student

    def read(self, s):
        locked.set()
        assert attempting.wait(2)
        assert not finished.wait(0.05)
        return original(self, s)

    monkeypatch.setattr(Session, "student", read)

    def writer():
        assert locked.wait(2)
        with connect(database, timeout=3) as db:
            attempting.set()
            if change == "offering":
                db.execute("DELETE FROM programme_course_offerings")
        if change == "membership":
            save_student(
                dict(
                    mode="replace",
                    expected_version=snapshot.saved_version.value,
                    student_id="s",
                    programme_id="later",
                    name="Alex",
                    email="alex@example.com",
                ),
                lambda: StudentSession(database),
            )
        finished.set()

    with ThreadPoolExecutor(2) as workers:
        update = workers.submit(writer)
        response = workers.submit(request, create_app(database, lambda c: c)).result(4)
        update.result(4)
    assert response["data"]["enrollCourse"]["__typename"] == "EnrollCourseSuccess"
    assert rows(database) == [("s", "c")]
    assert finished.is_set()
