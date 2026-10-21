"""Assemble references after raw quality capture; this is not validation."""

import hashlib
import json

from scripts.check_quality import FINAL, commands
from scripts.record import ROOT, digest

PAIRS = {
    "values": ("T011", "T012"),
    "records": ("T013", "T014"),
    "policies": ("T015", "T016"),
    "identity": ("T018", "T019"),
    "prerequisites": ("T020", "T021"),
    "flow": ("T022", "T023"),
    "reads": ("T024", "T025"),
    "transactions": ("T026", "T027"),
    "provider": ("T028", "T029"),
    "graphql": ("T030", "T031"),
    "http": ("T032", "T033"),
    "conflict": ("T037",),
    "faults": ("T040", "T041"),
    "server": ("T042",),
    "gates": ("T045",),
    "boundaries": ("T046",),
}


def assemble() -> None:
    evidence = ROOT / "specs/001-enroll-course/evidence"
    increments = {
        name: [
            str(p.relative_to(ROOT))
            for task in tasks
            for p in sorted((evidence / task).glob("*.json"))
        ]
        for name, tasks in PAIRS.items()
    }
    refs = {name: str(FINAL / "checks" / f"{name}.json") for name in commands(ROOT)}
    observations = {
        task: [
            str(p.relative_to(ROOT)) for p in sorted((evidence / task).glob("*.json"))
        ]
        for task in ["T034", "T035", "T036", "T038", "T039", "T043", "T044"]
    }
    artifacts = (
        set(refs.values())
        | {str(FINAL / "checks/tests.xml"), str(FINAL / "checks/coverage.json")}
        | {ref for paths in increments.values() for ref in paths}
        | {ref for paths in observations.values() for ref in paths}
    )
    state = {
        "digest": digest(),
        "checks": refs,
        "scenarios": 15,
        "increments": increments,
        "artifacts": {
            ref: hashlib.sha256((ROOT / ref).read_bytes()).hexdigest()
            for ref in sorted(artifacts)
        },
        "review": json.loads((evidence / "review.json").read_text()),
        "observations": observations,
    }
    (ROOT / FINAL / "manifest.json").write_text(json.dumps(state, indent=2))
    print("Manifest assembled; run evidence validation next.")


if __name__ == "__main__":
    assemble()
