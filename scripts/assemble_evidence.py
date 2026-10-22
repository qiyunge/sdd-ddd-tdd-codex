"""Assemble actual final checks and lightweight execution references; do not approve them."""

import hashlib
import json

from scripts.check_quality import FINAL, commands
from scripts.record import ROOT, digest


def assemble() -> None:
    evidence = ROOT / "specs/001-enroll-course/evidence"
    records = []
    for path in (evidence / "reconciliation").glob("*.json"):
        raw = json.loads(path.read_text())
        if raw.get("stage") in {"red", "green", "refactor"} and "increment" in raw:
            records.append((raw["started_ns"], str(path.relative_to(ROOT))))
    execution = [ref for _, ref in sorted(records)]
    refs = {name: str(FINAL / "checks" / f"{name}.json") for name in commands(ROOT)}
    review_ref = "specs/001-enroll-course/evidence/reconciliation/review.json"
    review = json.loads((ROOT / review_ref).read_text())
    historical = review.get("historical_records", [])
    artifacts = (
        set(refs.values())
        | set(execution)
        | set(historical)
        | {
            str(FINAL / "checks/tests.xml"),
            str(FINAL / "checks/coverage.json"),
            review_ref,
        }
    )
    state = {
        "digest": digest(ROOT),
        "checks": refs,
        "scenarios": 15,
        "execution_records": execution,
        "review_reference": review_ref,
        "review": review,
        "historical_records": historical,
        "artifacts": {
            ref: hashlib.sha256((ROOT / ref).read_bytes()).hexdigest()
            for ref in sorted(artifacts)
        },
    }
    (ROOT / FINAL / "manifest.json").write_text(json.dumps(state, indent=2))
    print("Manifest assembled; run evidence validation next.")


if __name__ == "__main__":
    assemble()
