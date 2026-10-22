"""Supplement Import Linter with dynamic dependency and public-type checks."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = {"flask", "werkzeug", "graphql", "sqlite3", "httpx", "waitress"}


def violations(source):
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            if name in {"__import__", "eval", "exec", "import_module"}:
                bad.append("dynamic dependency")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(prefix + "." in node.value for prefix in EXTERNAL):
                bad.append("external annotation")
    return bad


def test_dynamic_and_forward_annotation_isolation():
    assert violations('__import__("sqlite3")')
    assert violations('importlib.import_module("flask")')
    assert violations('def policy(x: "flask.Request"): pass')
    assert not violations('def policy(x: "StudentId"): pass')
    for layer in ("domain", "application"):
        files = list((ROOT / "src/enrollment" / layer).rglob("*.py"))
        assert files
        for path in files:
            assert not violations(path.read_text()), path


def test_public_annotations_are_core_owned():
    import importlib
    import inspect
    import typing

    for layer in ("domain", "application"):
        for path in (ROOT / "src/enrollment" / layer).rglob("*.py"):
            name = ".".join(path.relative_to(ROOT / "src").with_suffix("").parts)
            module = importlib.import_module(name)
            for value in vars(module).values():
                if not (inspect.isclass(value) or inspect.isfunction(value)):
                    continue
                if getattr(value, "__module__", None) != module.__name__:
                    continue
                targets = [value]
                if inspect.isclass(value):
                    targets += [
                        v
                        for k, v in vars(value).items()
                        if not k.startswith("_") and inspect.isfunction(v)
                    ]
                for target in targets:
                    hints = str(typing.get_type_hints(target))
                    assert not any(prefix + "." in hints for prefix in EXTERNAL)
                    assert "typing.Any" not in hints


def test_primary_checker_detects_direction_and_framework_leaks(tmp_path):
    import os
    import shutil
    import subprocess

    for name, source, statement, expected in [
        ("outward", "domain", "from enrollment.application import ports", 1),
        ("framework", "domain", "from flask import Request", 1),
        ("inward", "application", "from enrollment.domain import values", 0),
        (
            "adapter-domain",
            "adapters/identity",
            "from enrollment.domain import values",
            0,
        ),
    ]:
        trial = tmp_path / name
        shutil.copytree(ROOT / "src", trial / "src")
        shutil.copyfile(ROOT / "pyproject.toml", trial / "pyproject.toml")
        (trial / "src/enrollment" / source / "fitness_probe.py").write_text(
            statement + "\n"
        )
        result = subprocess.run(
            [str(ROOT / ".venv/bin/lint-imports"), "--no-cache"],
            cwd=trial,
            env=dict(os.environ, PYTHONPATH=str(trial / "src")),
            text=True,
            capture_output=True,
        )
        assert result.returncode == expected, result.stdout + result.stderr
