"""Controlled fixtures verify fail-closed gates; never final execution evidence."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def test_capture_does_not_require_manifest(tmp_path):
    quality = module("check_quality")
    assert (
        quality.run_checks(
            tmp_path, {"ok": [sys.executable, "-c", 'print("raw result")']}
        )
        == 0
    )
    checks = tmp_path / "specs/001-enroll-course/evidence/final/checks"
    result = json.loads((checks / "ok.json").read_text())
    assert result["stdout"] == "raw result\n"
    assert result["exit_code"] == 0
    assert not (checks.parent / "manifest.json").exists()
    assert (
        quality.run_checks(
            tmp_path, {"bad": [sys.executable, "-c", "raise SystemExit(7)"]}
        )
        != 0
    )
    assert json.loads((checks / "bad.json").read_text())["exit_code"] == 7


def fixture(tmp_path):
    root = tmp_path
    for layer in ["domain", "application"]:
        p = root / f"src/enrollment/{layer}/example.py"
        p.parent.mkdir(parents=True)
        p.write_text("value = 1\n")
    (root / "src/enrollment/application/ports.py").write_text(
        "from typing import Protocol\nclass Port(Protocol):\n    def read(self) -> None: ...\n"
    )
    (root / "pyproject.toml").write_text("")
    (root / "uv.lock").write_text("")
    final = root / "specs/001-enroll-course/evidence/final"
    checks = final / "checks"
    checks.mkdir(parents=True)
    quality = module("check_quality")
    digest = module("record").digest(root)
    refs = {}
    for name, command in quality.commands(root).items():
        p = checks / f"{name}.json"
        p.write_text(
            json.dumps(
                {
                    "command": command,
                    "stage": name,
                    "exit_code": 0,
                    "stdout": "fixture",
                    "stderr": "",
                    "digest": digest,
                }
            )
        )
        refs[name] = str(p.relative_to(root))
    coverage = {
        "files": {
            f"src/enrollment/{layer}/example.py": {
                "missing_lines": [],
                "missing_branches": [],
                "excluded_lines": [],
            }
            for layer in ["domain", "application"]
        },
        "totals": {
            "num_statements": 2,
            "missing_lines": 0,
            "missing_branches": 0,
            "percent_covered": 100,
        },
    }
    coverage["files"]["src/enrollment/application/ports.py"] = {
        "missing_lines": [],
        "missing_branches": [],
        "excluded_lines": [3],
    }
    (checks / "coverage.json").write_text(json.dumps(coverage))
    (checks / "tests.xml").write_text(
        "<testsuites><testsuite>"
        + "".join(
            f'<testcase classname="tests.acceptance.test_enrollment" name="test_scenario[{i}-outcome]" />'
            for i in range(1, 16)
        )
        + "</testsuite></testsuites>"
    )
    # The fixture explicitly supplies its own required cycles to the validator.
    cycles = []
    for stage, code in [("red", 1), ("green", 0), ("no-refactor", 0)]:
        p = root / f"{stage}.json"
        p.write_text(
            json.dumps(
                {
                    "stage": stage,
                    "exit_code": code,
                    "command": ["pytest"],
                    "stdout": "1 failed" if code else "1 passed",
                    "stderr": "",
                    "digest": digest,
                    "revision": "fixture",
                    "diff": "",
                }
            )
        )
        cycles.append(str(p.relative_to(root)))
    manifest = final / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "digest": digest,
                "checks": refs,
                "scenarios": 15,
                "increments": {"fixture": cycles},
                "review": {"passed": True, "notes": "controlled test fixture"},
                "artifacts": {
                    ref: hashlib.sha256((root / ref).read_bytes()).hexdigest()
                    for ref in [
                        *refs.values(),
                        *cycles,
                        str((checks / "coverage.json").relative_to(root)),
                        str((checks / "tests.xml").relative_to(root)),
                    ]
                },
            }
        )
    )
    return root, manifest


def test_sequence_and_tampering(tmp_path):
    root, manifest = fixture(tmp_path)
    validator = module("check_evidence")
    assert validator.validate(manifest, root, required_increments={"fixture"}) == []
    for mutation in [
        "missing",
        "failed",
        "digest",
        "skipped",
        "coverage",
        "unimported",
        "suppression",
        "empty",
        "increment",
        "tampered-output",
        "missing-review",
        "failed-review",
        "protocol-business",
        "missing-scenario",
    ]:
        trial = tmp_path / mutation
        trial.mkdir()
        _, copy = fixture(trial)
        assert validator.validate(copy, trial, required_increments={"fixture"}) == []
        state = json.loads(copy.read_text())
        if mutation == "missing":
            state["checks"].pop("typing")
        elif mutation == "failed":
            p = trial / state["checks"]["typing"]
            r = json.loads(p.read_text())
            r["exit_code"] = 1
            p.write_text(json.dumps(r))
        elif mutation == "digest":
            state["digest"] = "old"
        elif mutation == "skipped":
            p = trial / "specs/001-enroll-course/evidence/final/checks/tests.xml"
            p.write_text(p.read_text().replace(" />", "><skipped /></testcase>", 1))
        elif mutation == "coverage":
            p = trial / "specs/001-enroll-course/evidence/final/checks/coverage.json"
            r = json.loads(p.read_text())
            r["totals"]["missing_branches"] = 1
            p.write_text(json.dumps(r))
        elif mutation == "unimported":
            (trial / "src/enrollment/domain/unimported.py").write_text("uncovered = 1")
        elif mutation == "suppression":
            (trial / "src/enrollment/domain/example.py").write_text(
                "value = 1 # pragma: no cover"
            )
        elif mutation == "empty":
            p = trial / "specs/001-enroll-course/evidence/final/checks/coverage.json"
            r = json.loads(p.read_text())
            r["totals"]["num_statements"] = 0
            p.write_text(json.dumps(r))
        elif mutation == "increment":
            state["increments"] = {}
        elif mutation == "tampered-output":
            p = trial / state["checks"]["typing"]
            raw = json.loads(p.read_text())
            raw["stdout"] = "tampered pass"
            p.write_text(json.dumps(raw))
        elif mutation == "missing-review":
            state.pop("review")
        elif mutation == "failed-review":
            state["review"]["passed"] = False
        elif mutation == "protocol-business":
            (trial / "src/enrollment/application/ports.py").write_text(
                "from typing import Protocol\nclass Port(Protocol):\n    def read(self) -> None:\n        ...\n        return None\n"
            )
        elif mutation == "missing-scenario":
            p = trial / "specs/001-enroll-course/evidence/final/checks/tests.xml"
            p.write_text(
                p.read_text().replace("test_scenario[15-outcome]", "unrelated")
            )
        copy.write_text(json.dumps(state))
        assert validator.validate(copy, trial, required_increments={"fixture"}), (
            mutation
        )


def test_real_coverage_rejects_unimported_module_and_missed_branch(tmp_path):
    package = tmp_path / "business"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "policy.py").write_text(
        "def policy(flag):\n    if flag:\n        return 1\n    return 2\n"
    )
    (package / "unimported.py").write_text("value = 42\n")
    (tmp_path / "driver.py").write_text(
        "from business.policy import policy\nassert policy(True)==1\n"
    )
    python = str(ROOT / ".venv/bin/python")
    result = subprocess.run(
        [python, "-m", "coverage", "run", "--branch", "--source=business", "driver.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    result = subprocess.run(
        [python, "-m", "coverage", "report", "--fail-under=100"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "business/unimported.py" in result.stdout
    assert "business/policy.py" in result.stdout
