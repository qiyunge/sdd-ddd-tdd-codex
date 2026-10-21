"""Composition root: explicit host-provided identity dependency."""

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

from flask import Flask
from waitress.server import create_server  # type: ignore[import-untyped]  # Waitress exposes an untyped WSGI server; validate its socket contract in tests.

from enrollment.adapters.graphql.execution import Executor
from enrollment.adapters.http.app import create_app as http_app
from enrollment.adapters.identity.verifier import Verifier
from enrollment.adapters.persistence.sqlite import Session
from enrollment.application.enroll import enroll


def create_app(
    database_path: Path, verifier: Callable[[str | None], str | None] | None
) -> Flask:
    if verifier is None:
        raise ValueError("Host identity verifier must be configured")
    bridge = Verifier(verifier)
    executor = Executor(
        lambda command: enroll(command, bridge, lambda: Session(database_path))
    )
    return http_app(executor)


class Server(Protocol):
    effective_port: str

    def run(self) -> None: ...
    def close(self) -> None: ...


def make_server(app: Flask, host: str = "127.0.0.1", port: int = 8080) -> Server:
    return cast(Server, create_server(app, host=host, port=port, threads=4))
