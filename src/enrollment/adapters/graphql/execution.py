"""SDL-first synchronous engine and explicit Core result bridge."""

from collections.abc import Callable
from importlib.resources import files
from inspect import isawaitable, iscoroutine
from typing import cast

from graphql import (
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLUnionType,
    assert_valid_schema,
    build_schema,
    graphql_sync,
)

from enrollment.application.contracts import Command, Failure, Result
from enrollment.domain.models import Enrollment


def output(result: Result) -> dict[str, str]:
    if isinstance(result, Enrollment):
        return {
            "tag": "EnrollCourseSuccess",
            "studentId": result.student_id.value,
            "courseId": result.course_id.value,
        }
    failure = result in (
        Failure.PERSISTENCE_FAILURE,
        Failure.IDENTITY_UNAVAILABLE,
        Failure.INVALID_REQUEST,
    )
    return {
        "tag": "EnrollCourseFailure" if failure else "EnrollCourseRejected",
        "reason": result.value,
    }


class Executor:
    def __init__(self, use_case: Callable[[Command], Result]) -> None:
        self.use_case = use_case
        self.schema = build_schema(
            files(__package__).joinpath("schema.graphqls").read_text()
        )
        assert_valid_schema(self.schema)
        mutation = cast(GraphQLObjectType, self.schema.get_type("Mutation"))
        mutation.fields["enrollCourse"].resolve = self.resolve
        union = cast(GraphQLUnionType, self.schema.get_type("EnrollCourseResult"))
        union.resolve_type = lambda value, info, abstract: value["tag"]
        query = cast(GraphQLObjectType, self.schema.get_type("Query"))
        query.fields["_empty"].resolve = lambda source, info: None

    def resolve(
        self,
        source: object,
        info: GraphQLResolveInfo[str | None],
        input: dict[str, str],
    ) -> dict[str, str]:
        result: object = self.use_case(
            Command(input["studentId"], input["courseId"], info.context)
        )
        if isawaitable(result):
            if iscoroutine(result):
                result.close()
            raise RuntimeError("Synchronous use case required")
        return output(cast(Result, result))

    def execute(
        self,
        query: str,
        variables: dict[str, object] | None = None,
        operation_name: str | None = None,
        credential: str | None = None,
    ) -> dict[str, object]:
        result = graphql_sync(
            self.schema,
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=credential,
            check_sync=True,
        )
        response: dict[str, object] = {"data": result.data}
        if result.errors:
            response["errors"] = [
                (
                    {"message": "Internal server error", "path": e.path}
                    if e.original_error is not None and e.path is not None
                    else e.formatted
                )
                for e in result.errors
            ]
        return response
