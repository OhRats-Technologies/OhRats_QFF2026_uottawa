"""Offline policy revision, fresh development/confirmation or saved-only collection."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.evolution_history import replay_history
from wildfire_lab.evolution_study import run
from wildfire_lab.evolution_checks import collect


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage", choices=["replay", "development", "confirmation", "collect"]
    )
    parser.add_argument(
        "--plan", type=Path, default=ROOT / "experiments/policy_evolution.json"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    if args.stage == "replay":
        result = replay_history(ROOT, plan)
        output = args.output or ROOT / "docs/results/policy-evolution-offline.json"
    elif args.stage == "collect":
        result = collect(ROOT, plan)
        output = args.output or ROOT / "docs/results/policy-evolution.json"
    else:
        result = run(ROOT, args.plan, args.stage)
        output = args.output
    if output:
        output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("status", "means", "selected_policy", "seconds")
                if k in result
            }
        )
    )
