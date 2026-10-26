import pytest

from enrollment.bootstrap import create_app
from tests.acceptance.test_enrollment import request
from tests.support.database import rows


@pytest.mark.parametrize(
    "method,path,kwargs,status",
    [
        ("GET", "/graphql", {}, 405),
        ("HEAD", "/graphql", {}, 405),
        ("OPTIONS", "/graphql", {}, 405),
        ("POST", "/other", {}, 404),
        ("GET", "/static/x", {}, 404),
        ("POST", "/graphql", {"data": "{}", "content_type": "text/plain"}, 415),
        ("POST", "/graphql", {"data": "{bad", "content_type": "application/json"}, 400),
        *[
            ("POST", "/graphql", {"json": obj}, 400)
            for obj in [
                [],
                {},
                {"query": 1},
                {"query": "{ _empty }", "variables": []},
                {"query": "{ _empty }", "operationName": 4},
                {"query": "{ _empty }", "verified": True},
            ]
        ],
    ],
)
def test_transport(database, method, path, kwargs, status):
    response = (
        create_app(database, lambda c: c)
        .test_client()
        .open(path, method=method, **kwargs)
    )
    assert response.status_code == status
    if method != "HEAD":
        assert response.is_json
    if status == 405:
        assert response.headers["Allow"] == "POST"
    assert rows(database) == []


def test_success_and_credentials(database):
    app = create_app(database, lambda c: "s" if c == "opaque" else None)
    assert request(app, token="invalid")["data"]["enrollCourse"]["reason"] == "DENIED"
    assert (
        request(app, token="opaque")["data"]["enrollCourse"]["__typename"]
        == "EnrollCourseSuccess"
    )
    assert not app.debug


def test_provider_failure_is_sanitized(database):
    def down(c):
        raise RuntimeError("secret credentials")

    result = request(create_app(database, down))
    assert result["data"]["enrollCourse"]["failureReason"] == "IDENTITY_UNAVAILABLE"
    assert "secret" not in str(result)


def test_absent_verifier_configuration(database):
    with pytest.raises(ValueError):
        create_app(database, None)
