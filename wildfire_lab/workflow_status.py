"""Read saved run state without inspecting private hardware records."""

import json
from collections import Counter
from wildfire_lab.followup_status import summarize as followup_status


def saved_status(path, missing):
    if not path.exists():
        return missing
    try:
        return json.loads(path.read_text())["status"]
    except (json.JSONDecodeError, KeyError):
        return "unreadable"


def status(cache):
    reservations = [
        p
        for p in (cache / "experiments").glob("*/attempt-*.json")
        if not p.stem.endswith("-outcome")
    ]
    counts = Counter(
        saved_status(p.with_name(p.stem + "-outcome.json"), "pending")
        for p in reservations
    )
    final = cache / "final-test/outcome.json"
    final_status = saved_status(
        final,
        "opened_without_outcome"
        if (final.parent / "intent.json").exists()
        else "unopened",
    )
    return dict(
        prepared_weather=len(
            list((cache / "processed/weather").glob("*/manifest.json"))
        ),
        reserved_attempts=len(reservations),
        attempts_by_status=dict(counts),
        final_evaluation_status=final_status,
        bounded_followups=followup_status(cache),
        note="Saved state only; pending is not proof of a live process. No training, API calls or hardware submission.",
    )
