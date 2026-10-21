"""Fail-closed validation of the separately assembled final manifest."""

import ast
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.check_quality import FINAL, commands
from scripts.record import ROOT, digest

REQUIRED_INCREMENTS = {
    "values",
    "records",
    "policies",
    "identity",
    "prerequisites",
    "flow",
    "reads",
    "transactions",
    "provider",
    "graphql",
    "http",
    "conflict",
    "faults",
    "server",
    "gates",
    "boundaries",
}


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
        current = digest(root)
        expected_artifacts = (
            set(state["checks"].values())
            | {str(FINAL / "checks/tests.xml"), str(FINAL / "checks/coverage.json")}
            | {ref for refs in state["increments"].values() for ref in refs}
            | {ref for refs in state.get("observations", {}).values() for ref in refs}
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
                        path == "src/enrollment/application/ports.py"
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
        scenario_ids = [
            int(match.group(1))
            for case in cases
            if case.attrib.get("classname") == "tests.acceptance.test_enrollment"
            and (
                match := re.match(r"test_scenario\[(\d+)-", case.attrib.get("name", ""))
            )
        ]
        if sorted(scenario_ids) != list(range(1, 16)) or state["scenarios"] != 15:
            errors.append("Missing or duplicate acceptance scenarios")
        required = (
            REQUIRED_INCREMENTS if required_increments is None else required_increments
        )
        if set(state["increments"]) != required:
            errors.append("Missing increment evidence")
        for name, references in state["increments"].items():
            stages: list[tuple[str, int]] = []
            for reference in references:
                raw = json.loads((root / reference).read_text())
                if not all(
                    field in raw
                    for field in (
                        "command",
                        "stdout",
                        "stderr",
                        "digest",
                        "revision",
                        "diff",
                    )
                ):
                    errors.append(f"Missing raw increment evidence: {name}")
                stages.append((raw["stage"], raw["exit_code"]))
            if (
                not any(stage == "red" and code != 0 for stage, code in stages)
                or not any(stage == "green" and code == 0 for stage, code in stages)
                or not any(
                    stage in ("refactor", "no-refactor") and code == 0
                    for stage, code in stages
                )
            ):
                errors.append(f"Incomplete Red/Green/Refactor: {name}")
        if state["review"].get("passed") is not True or not state["review"].get(
            "notes"
        ):
            errors.append("Evidence review is missing or has not passed")
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
