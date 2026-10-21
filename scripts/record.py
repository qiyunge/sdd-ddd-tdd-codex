"""Capture actual commands and ordered execution evidence."""

import hashlib
import json
import subprocess
import sys
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


if __name__ == "__main__":
    task, stage, *cmd = sys.argv[1:]
    target = ROOT / "specs/001-enroll-course/evidence" / task
    target.mkdir(parents=True, exist_ok=True)
    count = len(list(target.glob("*.json"))) + 1
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    state = {
        "command": cmd,
        "stage": stage,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "digest": digest(),
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "diff": subprocess.check_output(
            ["git", "diff", "--", "."], cwd=ROOT, text=True
        ),
    }
    (target / f"{count:03d}-{stage}.json").write_text(json.dumps(state, indent=2))
    print(result.stdout + result.stderr)
    sys.exit(result.returncode)
