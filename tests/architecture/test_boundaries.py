import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def violations(source, layer):
    bad = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.level >= 2:
            name = "enrollment." + (node.module or "")
            if name.startswith(
                (
                    "enrollment.application",
                    "enrollment.adapters",
                    "enrollment.bootstrap",
                )
            ) and (layer == "domain" or not name.startswith("enrollment.application")):
                bad.append(name)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith(
                ("flask.", "werkzeug.", "graphql.", "sqlite3.", "httpx.", "waitress.")
            ):
                bad.append(node.value)
        if isinstance(node, ast.Call) and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id in {"__import__", "eval", "exec"}
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            )
        ):
            bad.append("dynamic dependency")
        names = (
            [node.module or ""]
            if isinstance(node, ast.ImportFrom)
            else [n.name for n in node.names]
            if isinstance(node, ast.Import)
            else []
        )
        for name in names:
            if layer in ("domain", "application") and name.split(".")[0] in {
                "flask",
                "werkzeug",
                "graphql",
                "sqlite3",
                "httpx",
                "waitress",
                "importlib",
            }:
                bad.append(name)
            if layer == "domain" and name.startswith("enrollment.application"):
                bad.append(name)
            if layer in ("domain", "application") and name.startswith(
                ("enrollment.adapters", "enrollment.bootstrap")
            ):
                bad.append(name)
    return bad


def test_boundaries():
    for layer in ("domain", "application"):
        files = list((ROOT / "src/enrollment" / layer).glob("*.py"))
        assert files
        for path in files:
            assert not violations(path.read_text(), layer), path


def test_negative_fixtures():
    assert violations("from flask import request", "domain")
    assert violations(
        "from enrollment.application.ports import IdentityVerifier", "domain"
    )
    assert violations("import enrollment.adapters.persistence", "application")
    assert not violations(
        "from enrollment.domain.values import StudentId", "application"
    )


def test_relative_dynamic_and_annotation_fixtures():
    assert violations("from ..application.ports import IdentityVerifier", "domain")
    assert violations("from ..adapters.identity import verifier", "application")
    assert violations('def policy(x: "flask.Request"): pass', "domain")
    assert violations(
        'import importlib\nimportlib.import_module("flask")', "application"
    )
    assert violations('__import__("sqlite3")', "domain")
    assert not violations("from .values import StudentId", "domain")


def test_core_annotations_and_ownership():
    import importlib
    import inspect
    import typing

    for layer in ("domain", "application"):
        for path in (ROOT / "src/enrollment" / layer).glob("*.py"):
            module = importlib.import_module(f"enrollment.{layer}.{path.stem}")
            for value in vars(module).values():
                if (inspect.isclass(value) or inspect.isfunction(value)) and getattr(
                    value, "__module__", None
                ) == module.__name__:
                    hints = typing.get_type_hints(value)
                    assert not any(
                        prefix in str(hints)
                        for prefix in ["flask.", "graphql.", "sqlite3.", "werkzeug."]
                    )
    domain = "\n".join(
        p.read_text() for p in (ROOT / "src/enrollment/domain").glob("*.py")
    )
    assert "IdentityVerifier" not in domain and "UnverifiedIdentity" not in domain
    from enrollment.application import enroll

    tree = ast.parse(inspect.getsource(enroll))
    # Actual orchestration must invoke all policies, without an actor comparison.
    calls = {
        n.func.attr
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "policies"
    }
    assert calls == {"ownership", "duplicate", "eligibility"}
    comparisons = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.Compare)]
    assert not any(
        "subject" in comparison or ".value" in comparison for comparison in comparisons
    )
