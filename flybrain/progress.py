"""Timed, append-only experiment stages with explicit evidence and quality gates."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import time
from zoneinfo import ZoneInfo

from .data import REPO

LOG = REPO / "docs/EXPERIMENT_LOG.jsonl"
BUILD_DEADLINE = datetime(2026, 10, 3, 5, 50, tzinfo=ZoneInfo("America/Toronto"))
REPORT_DEADLINE = datetime(2026, 10, 3, 6, 0, tzinfo=ZoneInfo("America/Toronto"))


def record(idea, stage, status, **evidence):
    now = datetime.now(timezone.utc)
    entry = {
        "ts_utc": now.isoformat(),
        "ts_toronto": now.astimezone(ZoneInfo("America/Toronto")).isoformat(),
        "idea": idea,
        "stage": stage,
        "status": status,
        **evidence,
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, separators=(",", ":"), allow_nan=False) + "\n")
    return entry


@contextmanager
def timed_stage(idea, stage, **evidence):
    start = time.perf_counter()
    record(idea, stage, "started", **evidence)
    details = {}
    try:
        yield details
    except Exception as error:
        record(
            idea,
            stage,
            "failed",
            elapsed_seconds=time.perf_counter() - start,
            error_type=type(error).__name__,
        )
        raise
    else:
        record(
            idea,
            stage,
            "passed",
            elapsed_seconds=time.perf_counter() - start,
            **details,
        )


def time_remaining():
    now = datetime.now(timezone.utc)
    return {
        "implementation_minutes": (BUILD_DEADLINE - now).total_seconds() / 60,
        "report_minutes": (REPORT_DEADLINE - now).total_seconds() / 60,
    }
