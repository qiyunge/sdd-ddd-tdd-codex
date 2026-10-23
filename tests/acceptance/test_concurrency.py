from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from enrollment.adapters.persistence.sqlite import connect
from enrollment.bootstrap import create_app
from tests.acceptance.test_enrollment import request
from tests.support.database import rows


def concurrent(app, requests):
    with ThreadPoolExecutor(2) as workers:
        jobs = [workers.submit(request, app, **kwargs) for kwargs in requests]
        return [job.result(5)["data"]["enrollCourse"] for job in jobs]


def test_same_pair_overlap(database):
    together = Barrier(2)

    def verify(c):
        together.wait(2)
        return c

    outcomes = concurrent(create_app(database, verify), [{}, {}])
    assert sorted(o["__typename"] for o in outcomes) == [
        "EnrollCourseRejected",
        "EnrollCourseSuccess",
    ]
    assert next(o["reason"] for o in outcomes if "reason" in o) == "ALREADY_ENROLLED"
    assert rows(database) == [("s", "c")]


def test_invalid_overlaps_unrelated_success(database):
    with connect(database) as db:
        db.execute(
            "INSERT INTO students(student_id,programme_id,name,email,saved_version) VALUES ('other','p','Other','other@example.com',1)"
        )
        db.execute("INSERT INTO courses VALUES ('unoffered')")
    together = Barrier(2)

    def verify(c):
        together.wait(2)
        return c

    outcomes = concurrent(
        create_app(database, verify),
        [{"course": "unoffered"}, {"token": "other", "student": "other"}],
    )
    assert outcomes[0]["reason"] == "COURSE_NOT_OFFERED"
    assert outcomes[1]["__typename"] == "EnrollCourseSuccess"
    assert rows(database) == [("other", "c")]
