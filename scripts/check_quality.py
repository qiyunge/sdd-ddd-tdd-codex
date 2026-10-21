"""Capture raw quality results before a final manifest exists."""

import json
import subprocess
import time
from pathlib import Path

from scripts.record import ROOT, digest

FINAL = Path("specs/001-enroll-course/evidence/final")


def commands(root: Path) -> dict[str, list[str]]:
    bin_dir = root / ".venv/bin"
    checks = root / FINAL / "checks"
    return {
        "tests": [
            str(bin_dir / "coverage"),
            "run",
            "-m",
            "pytest",
            "--junitxml=" + str(checks / "tests.xml"),
            "-q",
        ],
        "architecture": [str(bin_dir / "pytest"), "tests/architecture", "-q"],
        "imports": [str(bin_dir / "lint-imports")],
        "typing": [str(bin_dir / "mypy"), "src"],
        "lint": [str(bin_dir / "ruff"), "check", "."],
        "format": [str(bin_dir / "ruff"), "format", "--check", "."],
        "coverage-report": [str(bin_dir / "coverage"), "report", "--fail-under=100"],
        "coverage-data": [
            str(bin_dir / "coverage"),
            "json",
            "-o",
            str(checks / "coverage.json"),
        ],
    }


def run_checks(
    root: Path, selected_commands: dict[str, list[str]] | None = None
) -> int:
    selected = selected_commands if selected_commands is not None else commands(root)
    target = root / FINAL / "checks"
    target.mkdir(parents=True, exist_ok=True)
    failed = False
    for name, command in selected.items():
        before = digest(root)
        started = time.time_ns()
        try:
            result = subprocess.run(command, cwd=root, text=True, capture_output=True)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except OSError as exc:
            code, stdout, stderr = 127, "", str(exc)
        state = {
            "command": command,
            "stage": name,
            "exit_code": code,
            "stdout": stdout,
            "stderr": stderr,
            "digest": before,
            "digest_after": digest(root),
            "started_ns": started,
            "finished_ns": time.time_ns(),
        }
        output = target / f"{name}.json"
        if output.exists():
            archive = target / "history"
            archive.mkdir(exist_ok=True)
            (archive / f"{started}-{name}.json").write_bytes(output.read_bytes())
        output.write_text(json.dumps(state, indent=2))
        print(f"{name}: exit {code}\n{stdout}{stderr}", flush=True)
        failed |= code != 0 or before != state["digest_after"]
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(run_checks(ROOT))
