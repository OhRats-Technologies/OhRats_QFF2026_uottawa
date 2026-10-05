"""Execute a frozen pilot plan with immutable cached evidence; no hardware calls."""

import argparse
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pipeline import reserve
from wildfire_lab.evaluation import split
from wildfire_lab.selector_screen import run as selectors
from wildfire_lab.predictor_screen import run as predictors
from wildfire_lab.group_screen import run as groups
from wildfire_lab.spatial import split as spatial_split, matched_control
from wildfire_lab.climatology import MonthlyBaseline
from wildfire_lab.encoding_screen import run as encodings
from wildfire_lab.combination_screen import run as combinations


def run(plan_path, dataset, axis):
    import pandas as pd

    plan_path, dataset = plan_path.resolve(), dataset.resolve()
    plan = json.loads(plan_path.read_text())
    manifest = json.loads((dataset / "manifest.json").read_text())
    raw = (dataset / "features.csv").read_bytes()
    if (dataset / "INVALID.json").exists() or hashlib.sha256(
        raw
    ).hexdigest() != manifest["data_sha256"]:
        raise ValueError("Invalid or changed feature snapshot")
    recipe_paths = [
        Path(__file__),
        ROOT / "scripts/pipeline.py",
        ROOT / "uv.lock",
        ROOT / "pyproject.toml",
        *sorted((ROOT / "wildfire_lab").glob("*.py")),
        plan_path,
    ]
    frozen = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in recipe_paths
    }
    attempt = reserve(
        plan_path,
        ROOT / ".cache/wildfire",
        hypothesis=plan["hypothesis"],
        change="Matched "
        + axis
        + " screen on verified historical/operational snapshot",
    )
    frame = pd.read_csv(
        io.BytesIO(raw), dtype={f"station_lag{lag}": str for lag in [1, 2, 3, 4]}
    )
    if (
        frame.year.min() < plan["train_years"][0]
        or frame.year.max() > plan["train_years"][1]
        or frame.incident_id.duplicated().any()
    ):
        raise ValueError("Unexpected dates or repeated fire identities")
    eligibility_rows = len(frame)
    if plan.get("exclude_center_water"):
        frame = frame.loc[frame.cover_center_water.eq(0)].copy()
    output = attempt.parent / (attempt.stem + "-outcome.json")
    record = dict(
        id=attempt.stem,
        status="running",
        axis=axis,
        started_utc=datetime.now(timezone.utc).isoformat(),
        dataset=manifest,
        code_hashes=frozen,
        plan=plan,
        eligibility=dict(
            before=eligibility_rows,
            after=len(frame),
            excluded=eligibility_rows - len(frame),
        ),
        actual_research_model="Codex session; exact model identifier not independently exposed",
        rows=[],
    )
    baseline_config = plan.get("weather_baseline")
    weather_path = (
        ROOT
        / ".cache/wildfire/processed/weather"
        / manifest["protocol"]["weather_fingerprint"]
        if baseline_config
        else None
    )
    if weather_path:
        weather_manifest = json.loads((weather_path / "manifest.json").read_text())
        if (
            hashlib.sha256(
                (weather_path / "weather_months.csv").read_bytes()
            ).hexdigest()
            != weather_manifest["output_sha256"]
        ):
            raise ValueError("Changed weather baseline source")
        record["weather_baseline_source_sha256"] = weather_manifest["output_sha256"]
    start = time.perf_counter()
    try:
        for fold in plan["validation_folds"]:
            base_train, base_valid = split(frame, fold, plan["train_years"])
            if baseline_config:
                baseline = MonthlyBaseline(
                    weather_path / "weather_months.csv",
                    fold[1],
                    baseline_config["min_samples"],
                )
                base_train, train_baseline = baseline.attach(
                    base_train, baseline_config["lags"]
                )
                base_valid, valid_baseline = baseline.attach(
                    base_valid, baseline_config["lags"]
                )
                record.setdefault("baseline_fits", []).append(
                    dict(fold=fold, train=train_baseline, validation=valid_baseline)
                )
            spatial = plan.get("spatial")
            for side in spatial["sides"] if spatial else [None]:
                train, valid = base_train, base_valid
                metadata = None
                if spatial:
                    train, valid, metadata = spatial_split(
                        train, valid, side, spatial["width_m"], spatial["guard_m"]
                    )
                for seed in plan["seeds"]:
                    variants = [(train, metadata)]
                    if spatial and spatial.get("matched_random_control"):
                        variants.append(
                            matched_control(
                                base_train, valid, len(train), seed, metadata
                            )
                        )
                    for chosen, meta in variants:
                        if (
                            time.perf_counter() - start
                            > plan["screen_wall_seconds_per_attempt"]
                        ):
                            raise TimeoutError("Frozen screen budget exhausted")
                        if meta and not meta.get("control"):
                            meta = dict(meta, control="guarded_blocks")
                        rows = {
                            "selection": selectors,
                            "prediction": predictors,
                            "groups": groups,
                            "encoding": encodings,
                            "combinations": combinations,
                        }[axis](chosen, valid, plan, seed)
                        for row in rows:
                            row.update(
                                fold=fold,
                                full_train_rows=len(chosen),
                                full_validation_rows=len(valid),
                                spatial=meta,
                            )
                        record["rows"].extend(rows)
                        print(
                            json.dumps(
                                dict(
                                    fold=fold,
                                    seed=seed,
                                    side=side,
                                    control=meta.get("control") if meta else None,
                                    axis=axis,
                                    rows=len(rows),
                                    seconds=round(time.perf_counter() - start, 2),
                                )
                            ),
                            flush=True,
                        )
        if frozen != {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in recipe_paths
        }:
            raise RuntimeError("Recipe changed during run; outcome cannot be promoted")
        record["status"] = "complete"
        record["quality_checks"] = dict(
            dataset_hash=True,
            unique_incidents=True,
            chronological_folds=True,
            final_test_sealed=True,
            frozen_recipe=True,
        )
    except Exception as error:
        record.update(status="failed", error=str(error))
        raise
    finally:
        record.update(
            seconds=time.perf_counter() - start,
            finished_utc=datetime.now(timezone.utc).isoformat(),
        )
        with output.open("x") as f:
            json.dump(record, f, indent=2)
            f.write("\n")
        import fcntl

        with (attempt.parent / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            with (attempt.parent / "events.jsonl").open("a") as f:
                f.write(
                    json.dumps(
                        dict(
                            event="outcome",
                            id=attempt.stem,
                            status=record["status"],
                            file=output.name,
                            sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                        ),
                        separators=(",", ":"),
                    )
                    + "\n"
                )
        print(output, flush=True)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "axis",
        choices=["selection", "prediction", "groups", "encoding", "combinations"],
    )
    parser.add_argument(
        "--plan", type=Path, default=ROOT / "experiments/operational_pilot.json"
    )
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    run(args.plan, args.dataset, args.axis)
