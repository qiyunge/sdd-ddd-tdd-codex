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
        + "".join(
            f'<testcase classname="tests.acceptance.test_student_details" name="{name}"><properties><property name="scenario" value="{family}" /></properties></testcase>'
            for name, family in __import__(
                "scripts.acceptance_inventory", fromlist=["STUDENT_CASES"]
            ).STUDENT_CASES.items()
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
                    "stdout": "AssertionError: required behavior"
                    if code
                    else "1 passed",
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


def test_lightweight_recording(tmp_path):
    recorder = module("record")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_case.py").write_text("def test_case(): assert True\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "fixture",
        ],
        cwd=tmp_path,
        check=True,
    )
    request = dict(
        increment_id="cohesive",
        behavior="cohesive",
        test_ids=["tests/test_case.py::test_case"],
        previous_event=None,
    )
    code = recorder.capture(
        tmp_path,
        "cohesive",
        "green",
        [sys.executable, "-m", "pytest", "tests/test_case.py::test_case", "-q"],
        request,
    )
    assert code == 0
    assert not list(tmp_path.rglob("snapshots")), (
        "capture must not require intermediate snapshots"
    )
    records = list(
        (tmp_path / "specs/001-enroll-course/evidence/reconciliation").glob("*.json")
    )
    assert len(records) == 1
    raw = json.loads(records[0].read_text())
    assert raw["command"] and "passed" in raw["stdout"]
    assert "before" not in raw and "previous_event" not in raw


def test_consolidated_red_green_without_snapshots():
    validator = module("check_evidence")
    assert hasattr(validator, "validate_runs"), "lightweight validation unavailable"
    runs = [
        dict(
            increment="coherent",
            stage="red",
            exit_code=1,
            stdout="AssertionError: required behavior",
            stderr="",
            command=["pytest", "test_behavior"],
            started_ns=1,
            finished_ns=2,
        ),
        dict(
            increment="coherent",
            stage="green",
            exit_code=0,
            stdout="passed",
            stderr="",
            command=["pytest", "test_behavior"],
            started_ns=3,
            finished_ns=4,
        ),
    ]
    assert validator.validate_runs(runs) == []
    assert validator.validate_runs(runs[1:])
    assert validator.validate_runs([runs[0], dict(runs[1], exit_code=1)])
    assert validator.validate_runs([dict(runs[0], stdout="ImportError"), runs[1]])
    assert validator.validate_runs(list(reversed(runs)))
    assert validator.validate_runs(runs + [dict(runs[0], started_ns=5, finished_ns=6)])


def test_assembly_reads_consolidated_files_and_current_review(tmp_path):
    root, manifest = fixture(tmp_path)
    evidence = root / "specs/001-enroll-course/evidence"
    log = evidence / "reconciliation"
    log.mkdir()
    for stage in ("red", "green"):
        raw = json.loads((root / f"{stage}.json").read_text())
        raw.update(
            increment="coherent",
            started_ns=1 if stage == "red" else 3,
            finished_ns=2 if stage == "red" else 4,
        )
        (log / f"{stage}.json").write_text(json.dumps(raw))
    (log / "review.json").write_text(
        json.dumps(
            {
                "passed": True,
                "notes": "current review",
                "historical_records": ["specs/001-enroll-course/evidence/review.json"],
            }
        )
    )
    (evidence / "review.json").write_text(
        json.dumps({"passed": False, "notes": "historical"})
    )
    assembler = module("assemble_evidence")
    assembler.ROOT = root
    assembler.assemble()
    state = json.loads(manifest.read_text())
    assert state["review"]["passed"] is True
    assert "specs/001-enroll-course/evidence/review.json" in state["artifacts"], (
        "historical review references must be preserved and verified"
    )
    assert state["execution_records"] and "runs" not in state
    assert all(ref in state["artifacts"] for ref in state["execution_records"])
    validator = module("check_evidence")
    assert validator.validate(manifest, root) == []
    (root / state["execution_records"][0]).write_text("{}")
    assert validator.validate(manifest, root)


def test_missing_student_variant_cannot_pass_by_family_count(tmp_path):
    import xml.etree.ElementTree as ET

    root, manifest = fixture(tmp_path)
    report = root / "specs/001-enroll-course/evidence/final/checks/tests.xml"
    tree = ET.parse(report)
    suite = tree.find("testsuite")
    victim = next(
        case
        for case in suite
        if case.get("name") == "test_student_details_2[unicode-email]"
    )
    suite.remove(victim)
    tree.write(report)
    state = json.loads(manifest.read_text())
    ref = str(report.relative_to(root))
    state["artifacts"][ref] = hashlib.sha256(report.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(state))
    assert module("check_evidence").validate(manifest, root), (
        "missing Student detail variant must fail despite all seven families existing"
    )
