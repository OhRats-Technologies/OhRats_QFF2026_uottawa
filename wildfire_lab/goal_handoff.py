"""Verify the separately published deadline handoff; never infer it from time."""

import hashlib
import json
from datetime import datetime, timezone

DEADLINE = datetime(2026, 10, 5, 17, tzinfo=timezone.utc)
ARTIFACTS = (
    "GOAL.md",
    "docs/HANDOFF.md",
    "docs/REPORT.md",
    "docs/GOAL_AUDIT.md",
    "docs/DATA_SCHEMA.md",
    "docs/PIPELINE.md",
    "docs/REPRODUCIBILITY.md",
    "docs/QUANTUM_METHODS.md",
    "docs/results/final-evaluation.json",
    "docs/results/policy-evolution.json",
    "docs/data/workflow_repository_checks.json",
    "web/presentation/README.md",
)


def deadline_handoff(root, now=None):
    now = now or datetime.now(timezone.utc)
    result = dict(deadline_utc=DEADLINE.isoformat(), published=False)
    if now < DEADLINE:
        return dict(
            result, open_item="Deadline handoff is pending until 2026-10-05T17:00:00Z."
        )
    path = root / "docs/data/goal_handoff.json"
    if not path.is_file():
        return dict(
            result,
            open_item="Deadline passed; publish the requirement-audited handoff.",
        )
    saved = json.loads(path.read_text())
    completed = datetime.fromisoformat(saved["completed_utc"])
    if saved["status"] != "completed_goal_handoff" or not DEADLINE <= completed <= now:
        raise ValueError("Invalid handoff status or completion time")
    if set(saved["files_sha256"]) != set(ARTIFACTS):
        raise ValueError("Incomplete handoff artifact manifest")
    for name, expected in saved["files_sha256"].items():
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("Changed handoff artifact: " + name)
    return dict(
        result,
        published=True,
        completed_utc=saved["completed_utc"],
        manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
