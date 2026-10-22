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
    files = [
        p
        for folder in ("src", "tests", "scripts")
        for p in (root / folder).rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ]
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
    started = time.time_ns()
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
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
    )
    (target / f"{started}-{increment}-{stage}.json").write_text(
        json.dumps(record, indent=2)
    )
    print(result.stdout + result.stderr)
    return result.returncode


def main() -> int:
    increment, stage, *command = sys.argv[1:]
    return capture(ROOT, increment, stage, command)


if __name__ == "__main__":
    raise SystemExit(main())
