"""Fail-closed validation of the separately assembled final manifest."""

import ast
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.acceptance_inventory import ENROLLMENT_CASES, STUDENT_CASES
from scripts.check_quality import FINAL, commands
from scripts.record import ROOT, _test_id, digest

DECLARATION = "specs/001-enroll-course/evidence/reconciliation/v300-increments.json"
BASELINE = (
    "specs/001-enroll-course/evidence/reconciliation/v300-baseline-inventory.json"
)


def chronology_errors(run: dict) -> list[str]:
    """Historical output-only records stay valid. Opted-in records must be associated."""
    if "activity" not in run and "implementation_state" not in run:
        return []
    errors = []
    state = run.get("implementation_state")
    if not isinstance(state, str) or not state or set(state) <= {"0"}:
        errors.append("Missing or defaulted implementation state")
    elif run.get("implementation_state_after") != state:
        errors.append("Implementation changed during run")
    test_id = run.get("test_id")
    command = " ".join(str(part) for part in run.get("command") or [])
    if (
        not isinstance(test_id, str)
        or not test_id
        or test_id.removeprefix("selection: ") not in command
    ):
        errors.append("Unrelated or missing test identity")
    if run.get("activity") not in {"acceptance", "inner"}:
        errors.append("Missing activity role")
    started, finished = run.get("started_ns"), run.get("finished_ns")
    if (
        not isinstance(started, int)
        or not isinstance(finished, int)
        or started > finished
    ):
        errors.append("Invalid execution times")
    return errors


def required_run_errors(runs: list[dict], required: dict) -> list[str]:
    """New declared work never inherits the output-only historical path."""
    errors = []
    if any(run.get("increment") not in required for run in runs):
        errors.append("Unknown required increment association")
    for name, associations in required.items():
        group = [r for r in runs if r.get("increment") == name]
        if not group or not associations or set(associations) - {"acceptance", "inner"}:
            errors.append(f"Missing required increment/associations: {name}")
            continue
        previous_end = 0
        for run in group:
            errors.extend(chronology_errors(dict(run, activity=run.get("activity"))))
            try:
                if run.get("test_id") != _test_id(run.get("command", []), None):
                    errors.append(f"Invalid selection identity: {name}")
            except ValueError:
                errors.append(f"Missing test selection: {name}")
            activity = run.get("activity")
            targets = associations.get(activity, [])
            selection = str(run.get("test_id", ""))
            if not targets or not any(target in selection for target in targets):
                errors.append(f"Unrelated test/activity association: {name}")
            if activity == "inner" and "tests/acceptance" in selection:
                errors.append(f"Mislabeled acceptance activity: {name}")
            if run.get("started_ns", 0) < previous_end:
                errors.append(f"Overlapping/reversed executions: {name}")
            previous_end = run.get("finished_ns", 0)
        for activity in associations:
            subset = [r for r in group if r.get("activity") == activity]
            errors.extend(validate_runs(subset))
            reds = [r for r in subset if r.get("stage") == "red"]
            greens = [
                r
                for r in subset
                if r.get("stage") == "green" and r.get("exit_code") == 0
            ]
            if reds and greens and reds[-1].get("test_id") != greens[-1].get("test_id"):
                errors.append(f"Unrelated Red/Green selections: {name}")
        if "acceptance" in associations and group[0].get("activity") != "acceptance":
            errors.append(f"Missing acceptance-first execution: {name}")
    return errors


def rejected_run_errors(root: Path, rejected: dict, required: dict) -> list[str]:
    """Retain unusable attempts for review; never hide a valid required cycle."""
    errors = []
    for reference, reason in rejected.items():
        path = root / reference
        if not path.resolve().is_relative_to(root.resolve()):
            errors.append("Invalid rejected execution reference")
            continue
        run = json.loads(path.read_text())
        if (
            not isinstance(reason, str)
            or not reason.strip()
            or run.get("increment") not in required
            or run.get("stage") not in {"red", "green", "refactor"}
        ):
            errors.append("Invalid rejected execution classification")
        invalid = chronology_errors(run)
        try:
            if run.get("test_id") != _test_id(run.get("command", []), None):
                invalid.append("Invalid selection identity")
        except ValueError:
            invalid.append("Missing test selection")
        if not invalid:
            errors.append("Valid execution cannot be rejected")
    return errors


def validate_runs(runs: list[dict]) -> list[str]:
    errors = []
    groups = {}
    for run in runs:
        if (
            not run.get("command")
            or not isinstance(run.get("stdout"), str)
            or not isinstance(run.get("stderr"), str)
        ):
            errors.append("Missing execution command/output")
        errors.extend(chronology_errors(run))
        groups.setdefault(run.get("increment"), []).append(run)
    if not groups:
        return ["Missing behavioral execution evidence"]
    for name, group in groups.items():
        reds = [
            r
            for r in group
            if r.get("stage") == "red"
            and r.get("exit_code") == 1
            and any(
                assertion in r.get("stdout", "")
                for assertion in ("AssertionError", "Failed: DID NOT RAISE")
            )
        ]
        greens = [
            r for r in group if r.get("stage") == "green" and r.get("exit_code") == 0
        ]
        if (
            not reds
            or not greens
            or group.index(reds[-1]) >= group.index(greens[-1])
            or reds[-1].get("finished_ns", 0) > greens[-1].get("started_ns", 0)
        ):
            errors.append(f"Missing ordered behavioral Red/Green: {name}")
    return errors


def declarative_ports(path: Path) -> bool:
    """Coverage's default ellipsis exclusion is valid only for pure Protocol signatures."""
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if not isinstance(node, ast.ClassDef) or not any(
            isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases
        ):
            return False
        for method in node.body:
            if (
                not isinstance(method, ast.FunctionDef)
                or len(method.body) != 1
                or not isinstance(method.body[0], ast.Expr)
                or not isinstance(method.body[0].value, ast.Constant)
                or method.body[0].value.value is not Ellipsis
            ):
                return False
    return bool(tree.body)


def validate(
    manifest: Path, root: Path, required_increments: set[str] | None = None
) -> list[str]:
    errors: list[str] = []
    try:
        state = json.loads(manifest.read_text())
        required = state.get("required_increments", {})
        declaration_ref = state.get("increment_declaration")
        declaration_path = root / DECLARATION
        declaration = json.loads(declaration_path.read_text())
        if declaration_ref != DECLARATION or not required:
            errors.append("Missing required increment declaration")
        elif declaration.get("increments") != required:
            errors.append("Required increment declaration mismatch")
        baseline_ref = state.get("baseline_inventory")
        if (
            baseline_ref != BASELINE
            or declaration.get("baseline_inventory") != BASELINE
        ):
            errors.append("Missing or inconsistent baseline inventory")
        if required != state.get("review", {}).get("required_increments", {}):
            errors.append("Required increment review mismatch")
        if required_increments is not None and not required_increments <= set(
            state.get("increments", {})
        ) | set(required):
            errors.append("Missing explicit required increments")
        current = digest(root)
        if (
            state.get("review", {}).get("constitution") != "3.0.0"
            or state.get("review", {}).get("source_digest") != current
        ):
            errors.append("Missing or stale final implementation review")
        rejected = state.get("rejected_execution_records", {})
        if rejected != state.get("review", {}).get("rejected_execution_records", {}):
            errors.append("Rejected execution review mismatch")
        active_refs = set(state.get("execution_records", [])) | {
            ref for refs in state.get("increments", {}).values() for ref in refs
        }
        if set(rejected) & (active_refs | set(state.get("historical_records", []))):
            errors.append("Rejected execution used as active or historical proof")
        errors.extend(rejected_run_errors(root, rejected, required))
        expected_artifacts = (
            set(state["checks"].values())
            | {str(FINAL / "checks/tests.xml"), str(FINAL / "checks/coverage.json")}
            | {ref for refs in state.get("increments", {}).values() for ref in refs}
            | set(state.get("execution_records", []))
            | set(state.get("historical_records", []))
            | ({state["review_reference"]} if "review_reference" in state else set())
            | {ref for refs in state.get("observations", {}).values() for ref in refs}
            | ({declaration_ref} if declaration_ref else set())
            | ({baseline_ref} if baseline_ref else set())
            | set(rejected)
        )
        if set(state["artifacts"]) != expected_artifacts:
            errors.append("Missing artifact hashes")
        for reference, expected_hash in state["artifacts"].items():
            path = root / reference
            if (
                not path.resolve().is_relative_to(root.resolve())
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash
            ):
                errors.append(f"Tampered evidence: {reference}")
        if state["digest"] != current:
            errors.append("Stale source/config/test digest")
        expected = commands(root)
        if set(state["checks"]) != set(expected):
            errors.append("Missing or unknown mandatory checks")
        for name, command in expected.items():
            reference = state["checks"].get(name)
            if reference is None:
                continue
            path = root / reference
            if not path.resolve().is_relative_to((root / FINAL / "checks").resolve()):
                errors.append("Invalid check reference")
                continue
            raw = json.loads(path.read_text())
            if (
                raw["command"] != command
                or raw["stage"] != name
                or raw["exit_code"] != 0
                or raw["digest"] != current
                or raw.get("digest_after", current) != current
            ):
                errors.append(f"Failed, inconsistent or stale check: {name}")
            for field in ("stdout", "stderr"):
                if not isinstance(raw[field], str):
                    errors.append("Missing raw output")
        report = json.loads((root / FINAL / "checks/coverage.json").read_text())
        totals = report["totals"]
        if (
            totals["num_statements"] <= 0
            or totals["percent_covered"] != 100
            or totals["missing_lines"]
            or totals["missing_branches"]
        ):
            errors.append("Incomplete or empty Core coverage")
        scope = {
            p.relative_to(root).as_posix()
            for layer in ("domain", "application")
            for p in (root / "src/enrollment" / layer).rglob("*.py")
        }
        if not scope or set(report["files"]) != scope:
            errors.append("Coverage excludes Core files (including unimported modules)")
        for path, coverage in report["files"].items():
            if (
                coverage["missing_lines"]
                or coverage["missing_branches"]
                or (
                    coverage["excluded_lines"]
                    and not (
                        path
                        in {
                            "src/enrollment/application/ports.py",
                            "src/enrollment/application/student_ports.py",
                        }
                        and declarative_ports(root / path)
                    )
                )
            ):
                errors.append(f"Incomplete coverage: {path}")
        for source in (root / "src").rglob("*.py"):
            text = source.read_text()
            if re.search(r"pragma:\s*no (cover|branch)|\bnoqa\b|@no_type_check", text):
                errors.append(f"Unjustified suppression: {source}")
            if "# type: ignore" in text and not (
                source.name == "bootstrap.py"
                and "ignore[import-untyped]" in text
                and "Waitress" in text
            ):
                errors.append(f"Unjustified typing suppression: {source}")
        suite = ET.parse(root / FINAL / "checks/tests.xml")
        cases = list(suite.iter("testcase"))
        if any(
            list(case)
            for case in cases
            if any(child.tag in ("skipped", "failure", "error") for child in case)
        ):
            errors.append("Skipped or failed mandatory test")
        if state["scenarios"] != 19:
            errors.append("Missing or duplicate acceptance scenarios")
        for filename, mapping in (
            ("test_enrollment", ENROLLMENT_CASES),
            ("test_student_details", STUDENT_CASES),
        ):
            names = []
            for case in cases:
                if case.get("classname") != "tests.acceptance." + filename:
                    continue
                name = case.get("name")
                properties = case.findall("./properties/property[@name='scenario']")
                if name in mapping:
                    names.append(name)
                    if (
                        len(properties) != 1
                        or properties[0].get("value") != mapping[name]
                    ):
                        errors.append("Missing or invalid acceptance scenario identity")
                elif properties:
                    errors.append("Unknown acceptance scenario identity")
            if sorted(names) != sorted(mapping):
                errors.append("Missing or duplicate acceptance variants: " + filename)
        baseline = json.loads((root / BASELINE).read_text())
        nodes = [
            case.get("classname", "").replace(".", "/") + ".py::" + case.get("name", "")
            for case in cases
        ]
        for original in baseline["cases"]:
            node = original["node_id"]
            if node.startswith("tests/acceptance/") and nodes.count(node) != 1:
                errors.append(
                    "Missing or duplicate baseline acceptance variant: " + node
                )
        if "execution_records" in state:
            runs = [
                json.loads((root / ref).read_text())
                for ref in state["execution_records"]
            ]
            errors.extend(validate_runs(runs))
            if state["review"] != json.loads(
                (root / state["review_reference"]).read_text()
            ):
                errors.append("Review reference mismatch")
        else:
            runs = []
            for name, references in state["increments"].items():
                for reference in references:
                    raw = json.loads((root / reference).read_text())
                    runs.append(dict(raw, increment=name))
            errors.extend(validate_runs(runs))
        if state["review"].get("passed") is not True or not state["review"].get(
            "notes"
        ):
            errors.append("Evidence review is missing or has not passed")
        if required:
            errors.extend(required_run_errors(runs, required))
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        errors.append(f"Missing or invalid evidence: {exc}")
    return errors


def main() -> int:
    manifest = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / FINAL / "manifest.json"
    )
    errors = validate(manifest, ROOT)
    target = ROOT / FINAL / "validation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {"passed": not errors, "errors": errors, "digest": digest()}, indent=2
        )
    )
    print("Evidence validation passed" if not errors else "\n".join(errors))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
