"""Flask transport; the injected engine owns GraphQL execution."""

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import BadRequest, HTTPException
from werkzeug.wrappers import Response as WerkzeugResponse

from enrollment.adapters.graphql.execution import Executor


def create_app(executor: Executor) -> Flask:
    app = Flask(__name__, static_folder=None)

    @app.post("/graphql", provide_automatic_options=False)
    def graphql() -> Response:
        body = request.get_json()
        if (
            not isinstance(body, dict)
            or not isinstance(body.get("query"), str)
            or set(body) - {"query", "variables", "operationName"}
            or (
                body.get("variables") is not None
                and not isinstance(body["variables"], dict)
            )
            or (
                body.get("operationName") is not None
                and not isinstance(body["operationName"], str)
            )
        ):
            raise BadRequest()
        return jsonify(
            executor.execute(
                body["query"],
                body.get("variables"),
                body.get("operationName"),
                request.headers.get("Authorization"),
            )
        )

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException) -> WerkzeugResponse:
        response = error.get_response()
        response.data = app.json.dumps({"errors": [{"message": error.name}]})
        response.content_type = "application/json"
        if error.code == 405:
            response.headers["Allow"] = "POST"
        return response

    @app.errorhandler(Exception)
    def internal_error(error: Exception) -> tuple[Response, int]:
        return jsonify({"errors": [{"message": "Internal server error"}]}), 500

    return app
