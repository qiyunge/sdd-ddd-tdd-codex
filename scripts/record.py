"""Capture actual commands and ordered execution evidence."""

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(root: Path = ROOT) -> str:
    files = []
    for folder in ("src", "tests", "scripts"):
        base = root / folder
        if not base.exists():
            continue
        files.extend(
            p for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts
        )
    files += [root / "pyproject.toml", root / "uv.lock"]
    return hashlib.sha256(
        b"".join(
            str(p.relative_to(root)).encode() + p.read_bytes()
            for p in sorted(files)
            if p.exists()
        )
    ).hexdigest()


def capture(
    root: Path,
    increment: str,
    stage: str,
    command: list[str],
    request: dict | None = None,
) -> int:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", increment):
        raise ValueError("Invalid increment name")
    stage = stage.lower()
    if stage not in {"red", "green", "refactor", "verification"}:
        raise ValueError("Invalid stage")
    test_id = _test_id(command, request)
    before = digest(root)
    started = time.time_ns()
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    after = digest(root)
    target = root / "specs/001-enroll-course/evidence/reconciliation"
    target.mkdir(parents=True, exist_ok=True)
    record = dict(
        increment=increment,
        stage=stage,
        command=command,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        started_ns=started,
        finished_ns=time.time_ns(),
        implementation_state=before,
        implementation_state_after=after,
        test_id=test_id,
        activity=_activity(command, request),
    )
    (target / f"{started}-{increment}-{stage}.json").write_text(
        json.dumps(record, indent=2)
    )
    print(result.stdout + result.stderr)
    return result.returncode


def _test_id(command: list[str], request: dict | None) -> str:
    """Identify the requested selection; a command alone cannot prove one test ran."""
    start = next(
        (
            index + 1
            for index, part in enumerate(command)
            if Path(part).name in {"pytest", "py.test"}
            and (index == 0 or command[index - 1] == "-m")
        ),
        None,
    )
    if start is None:
        raise ValueError("Missing meaningful test identity")
    selected = []
    index = start
    while index < len(command):
        part = command[index]
        if part in {"-k", "-m"} and index + 1 < len(command):
            selected.extend([part, command[index + 1]])
            index += 2
            continue
        if part.startswith(("-k=", "-m=")):
            selected.append(part)
        elif not part.startswith("-") and (part.startswith("tests/") or ".py" in part):
            selected.append(part)
        index += 1
    if not selected:
        raise ValueError("Missing meaningful test identity")
    identity = "selection: " + " ".join(selected)
    if request and request.get("test_id") not in (None, identity):
        raise ValueError("Explicit test identity does not identify the full selection")
    return identity


def _activity(command: list[str], request: dict | None) -> str:
    if request and request.get("activity") in {"acceptance", "inner"}:
        return str(request["activity"])
    return "acceptance" if "tests/acceptance" in " ".join(command) else "inner"


def main() -> int:
    increment, stage, *command = sys.argv[1:]
    return capture(ROOT, increment, stage, command)


if __name__ == "__main__":
    raise SystemExit(main())
