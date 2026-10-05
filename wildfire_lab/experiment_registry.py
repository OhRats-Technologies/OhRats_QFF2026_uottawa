"""Append-only, budgeted experiment reservations."""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from wildfire_lab.weather_preparation import sha

ROOT = Path(__file__).resolve().parents[1]


def reserve(plan_path, cache, parent=None, hypothesis=None, change=None):
    if (cache / "final-test/intent.json").exists():
        raise ValueError(
            "Final test opened; adaptive reservations are closed in this workspace"
        )
    raw = plan_path.read_bytes()
    plan = json.loads(raw)
    for field in (
        "id",
        "hypothesis",
        "research_model",
        "primary_metric",
        "final_test_sealed",
        "screen_max_proposals",
    ):
        if field not in plan:
            raise ValueError("Missing plan field: " + field)
    if plan["final_test_sealed"] is not True:
        raise ValueError("Adaptive search must keep final test sealed")
    if (
        type(plan["screen_max_proposals"]) is not int
        or plan["screen_max_proposals"] < 1
    ):
        raise ValueError("Proposal budget must be a positive integer")
    if parent and not re.fullmatch(r"attempt-[a-f0-9]{12}", parent):
        raise ValueError("Invalid parent attempt ID")
    for fold in plan.get("validation_folds", []):
        start, train_end, val_start, val_end = fold
        if (
            not plan["train_years"][0]
            <= start
            <= train_end
            < val_start
            <= val_end
            <= plan["train_years"][1]
        ):
            raise ValueError("Validation fold crosses training window or overlaps")
    base = cache / "experiments" / sha(raw)[:20]
    base.mkdir(parents=True, exist_ok=True)
    # Serialize reservation counting across local processes.
    import fcntl

    with (base / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (
            len(
                [
                    p
                    for p in base.glob("attempt-*.json")
                    if not p.stem.endswith("-outcome")
                ]
            )
            >= plan["screen_max_proposals"]
        ):
            raise ValueError("Proposal reservation budget exhausted")
        if parent and not (base / (parent + ".json")).exists():
            raise ValueError("Parent must be an existing attempt in this study")
        attempt = "attempt-" + uuid4().hex[:12]
        commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip()
        )
        record = dict(
            id=attempt,
            parent=parent,
            status="planned",
            plan_sha256=sha(raw),
            created_utc=datetime.now(timezone.utc).isoformat(),
            git_commit=commit,
            preferred_research_model=plan["research_model"],
            actual_model=None,
            metrics=None,
            quality_checks=None,
            plan=plan,
            hypothesis=hypothesis or plan["hypothesis"],
            proposed_change=change,
        )
        with (base / (attempt + ".json")).open("x") as f:
            json.dump(record, f, indent=2)
            f.write("\n")
        with (base / "events.jsonl").open("a") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
        return base / (attempt + ".json")
