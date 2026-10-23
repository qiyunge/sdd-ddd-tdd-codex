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


CONSTRUCTORS = {
    "Student",
    "Programme",
    "Course",
    "ProgrammeCourseOffering",
    "Enrollment",
    "VerifiedIdentity",
}


def direct_constructors(root: Path) -> list[str]:
    allowed = {
        root / "src/enrollment/domain/models.py",
        root / "src/enrollment/domain/values.py",
    }
    repository = root / "src/enrollment/adapters/persistence/sqlite.py"
    findings = []
    for path in (root / "src/enrollment").rglob("*.py"):
        if path in allowed:
            continue
        tree = ast.parse(path.read_text())
        aliases = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    aliases[alias.asname or alias.name] = (
                        (node.module or "") + "." + alias.name
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name.split(".")[0]] = (
                        alias.name if alias.asname else alias.name.split(".")[0]
                    )

        def resolve(node, aliases=aliases):
            if isinstance(node, ast.Name):
                return aliases.get(node.id, node.id)
            if isinstance(node, ast.Attribute):
                return resolve(node.value) + "." + node.attr
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and len(node.args) == 2
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                return resolve(node.args[0]) + "." + node.args[1].value
            return ""

        assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
        for _ in range(len(assignments) + 1):
            for node in assignments:
                value = resolve(node.value)
                if value:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            aliases[target.id] = value
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and resolve(node.func).split(".")[-1] in CONSTRUCTORS
            ):
                findings.append(
                    f"{path.relative_to(root)}:{node.lineno}: unsupported constructor"
                )
            if path != repository and isinstance(
                node, (ast.Name, ast.Attribute, ast.Call)
            ):
                parts = resolve(node).split(".")
                if (
                    len(parts) >= 2
                    and parts[-2] in CONSTRUCTORS - {"VerifiedIdentity"}
                    and parts[-1] in {"create", "reconstitute"}
                ):
                    findings.append(
                        f"{path.relative_to(root)}:{node.lineno}: Entity outside Repository"
                    )
    return sorted(set(findings))


def test_supported_factory_and_reconstitution_calls():
    assert direct_constructors(ROOT) == []


def test_repository_only_factories_and_alias_references(tmp_path):
    package = tmp_path / "src/enrollment"
    production = package / "application/probe.py"
    production.parent.mkdir(parents=True)
    invalid = [
        "from enrollment.domain.models import Student\nx = Student.create(s,p,n,e)",
        "from enrollment.domain.models import Student as Learner\nx = Learner.reconstitute(s,p,n,e)",
        "from enrollment.domain import models as m\nfactory = m.Student.create",
        "import enrollment.domain.models as m\nAlias=m.Enrollment\nf=Alias.reconstitute\nx=f(s,c)",
        "import enrollment.domain.models\nx=enrollment.domain.models.Course(c)",
        "from enrollment.domain.models import Student\nAlias=Student\nx=Alias(s,p,n,e)",
        "from enrollment.domain.models import Student\nf=getattr(Student,'create')",
    ]
    for source in invalid:
        production.write_text(source)
        assert direct_constructors(tmp_path), source
    for source in [
        "from enrollment.domain.values import StudentId as ID\nx=ID.create(raw)",
        "from enrollment.domain.values import StudentEmail\nf=StudentEmail.create",
    ]:
        production.write_text(source)
        assert direct_constructors(tmp_path) == []
    production.unlink()
    repository = package / "adapters/persistence/sqlite.py"
    repository.parent.mkdir(parents=True)
    repository.write_text(
        "from enrollment.domain.models import Student as S\nx=S.create(s,p,n,e)\ny=S.reconstitute(s,p,n,e)"
    )
    assert direct_constructors(tmp_path) == []
    repository.write_text(
        "from enrollment.domain.models import Student as S\nx=S(s,p,n,e)"
    )
    assert direct_constructors(tmp_path), (
        "Repositories must use supported Domain factories"
    )
