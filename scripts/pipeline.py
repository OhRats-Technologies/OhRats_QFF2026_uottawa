"""Front door for source preparation, saved evidence and bounded experiments."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab import workflow
from wildfire_lab.experiment_registry import reserve
from wildfire_lab.workflow_status import status
from wildfire_lab.weather_preparation import normalized, prepare_weather
from wildfire_lab import annual_workflow


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    stages = cli.add_subparsers(dest="stage", required=True)
    annual = stages.add_parser("annual", help="Annual macro development or frozen public collection")
    annual.add_argument("operation", choices=list(annual_workflow.OPERATIONS))
    annual.add_argument("--output", type=Path, required=True)
    annual.add_argument("--dataset", type=Path)
    annual.add_argument("--qubits", type=int, choices=[4, 10], default=4)
    annual.add_argument("--execute", action="store_true")
    saved = stages.add_parser("status", help="Read saved cache state")
    saved.add_argument("--cache", type=Path, default=ROOT / ".cache/wildfire")
    inputs = stages.add_parser(
        "doctor", help="List missing/mismatched reproduction inputs"
    )
    inputs.add_argument("--verify", action="store_true")
    preview = stages.add_parser(
        "run", help="Preview or execute preparation and an optional bounded screen"
    )
    preview.add_argument("--execute", action="store_true")
    preview.add_argument(
        "--plan", type=Path, help="Optional declared training-only screen"
    )
    preview.add_argument(
        "--axis",
        choices=["selection", "prediction", "groups", "encoding", "combinations"],
    )
    stages.add_parser(
        "prepare", help="Build training features from existing verified inputs"
    )
    evidence = stages.add_parser(
        "collect", help="Recollect existing results without training"
    )
    evidence.add_argument(
        "--output", type=Path, required=True, help="New output directory"
    )
    stages.add_parser("check", help="Run fixture tests and every CLI help path")
    screen = stages.add_parser(
        "screen", help="Preview or execute a bounded frozen screen"
    )
    screen.add_argument("--dataset", type=Path, required=True)
    screen.add_argument("--plan", type=Path, required=True)
    screen.add_argument(
        "--axis",
        choices=["selection", "prediction", "groups", "encoding", "combinations"],
        required=True,
    )
    screen.add_argument("--execute", action="store_true")
    weather = stages.add_parser("prepare-weather", help="Prepare typed weather only")
    weather.add_argument(
        "--config", type=Path, default=ROOT / "configs/wildfires/ontario.json"
    )
    weather.add_argument("--raw-weather", type=Path, default=ROOT / "data/raw/weather")
    weather.add_argument("--cache", type=Path, default=ROOT / ".cache/wildfire")
    experiment = stages.add_parser(
        "new-experiment", help="Reserve an adaptive proposal before final opening"
    )
    experiment.add_argument(
        "--plan", type=Path, default=ROOT / "experiments/screen.json"
    )
    experiment.add_argument("--cache", type=Path, default=ROOT / ".cache/wildfire")
    experiment.add_argument("--parent")
    experiment.add_argument("--hypothesis")
    experiment.add_argument("--change")
    return cli


def main():
    args = parser().parse_args()
    if args.stage == "annual":
        result = annual_workflow.run(ROOT, args.operation, args.output, args.dataset,
                                     args.qubits, args.execute)
    elif args.stage == "status":
        result = status(args.cache)
    elif args.stage == "doctor":
        result = workflow.doctor(ROOT, args.verify)
        print(json.dumps(result, indent=2))
        return 0 if result["ready"] else 1
    elif args.stage == "run":
        result = workflow.run(ROOT, args.execute, args.plan, args.axis)
    elif args.stage == "prepare":
        result = workflow.prepare(ROOT)
    elif args.stage == "collect":
        result = workflow.collect(ROOT, args.output.resolve())
    elif args.stage == "check":
        result = workflow.check(ROOT)
    elif args.stage == "screen":
        command = [
            sys.executable,
            str(ROOT / "scripts/run_pilot_screen.py"),
            args.axis,
            "--dataset",
            str(args.dataset),
            "--plan",
            str(args.plan),
        ]
        if args.execute:
            subprocess.run(command, cwd=ROOT, check=True)
        result = dict(command=command, executes=args.execute)
    elif args.stage == "prepare-weather":
        path, manifest = prepare_weather(args.config, args.raw_weather, args.cache)
        result = dict(
            dataset=str(path),
            **{
                k: manifest[k] for k in ("rows_by_split", "flagged_rows", "limitations")
            },
        )
    else:
        result = dict(
            reservation=str(
                reserve(
                    args.plan, args.cache, args.parent, args.hypothesis, args.change
                )
            )
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
