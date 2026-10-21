from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Thread

import httpx

from enrollment.bootstrap import create_app, make_server
from tests.acceptance.test_enrollment import QUERY
from tests.support.database import rows


def test_waitress_real_workers(database):
    overlap = Barrier(2)

    def verify(c):
        overlap.wait(3)
        return c

    app = create_app(database, verify)
    assert app.debug is False
    server = make_server(app, port=0)
    assert server is not None, "Production WSGI server wiring is not implemented"
    worker = Thread(target=server.run, daemon=True)
    worker.start()

    def send():
        with httpx.Client(timeout=5) as client:
            response = client.post(
                f"http://127.0.0.1:{server.effective_port}/graphql",
                json={
                    "query": QUERY,
                    "variables": {"input": {"studentId": "s", "courseId": "c"}},
                },
                headers={"Authorization": "s"},
            )
            assert response.status_code == 200
            return response.json()["data"]["enrollCourse"]["__typename"]

    try:
        with ThreadPoolExecutor(2) as pool:
            jobs = [pool.submit(send) for _ in range(2)]
            assert sorted(j.result(8) for j in jobs) == [
                "EnrollCourseRejected",
                "EnrollCourseSuccess",
            ]
    finally:
        server.close()
        worker.join(3)
    assert not worker.is_alive()
    assert rows(database) == [("s", "c")]
