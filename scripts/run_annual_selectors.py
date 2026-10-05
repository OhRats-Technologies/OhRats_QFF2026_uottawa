"""Run the frozen continuous-target annual feature-selection comparison."""

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_data import digest
from wildfire_lab.annual_selectors import screen


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--dataset', type=Path, default=ROOT / 'docs/data/annual_training.csv')
    cli.add_argument('--plan', type=Path, default=ROOT / 'experiments/annual_selectors.json')
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    plan = json.loads(args.plan.read_text())
    parent_path = ROOT / plan['parent']
    if digest(args.dataset) != plan['dataset_sha256'] or digest(parent_path) != plan['parent_sha256']:
        raise ValueError('Annual parent data or plan changed')
    parent = json.loads(parent_path.read_text())
    table = pd.read_csv(args.dataset)
    start = time.perf_counter()
    results, records = screen(table, parent, plan)
    outcome = dict(study='annual-selectors', plan_sha256=digest(args.plan),
                   dataset_sha256=digest(args.dataset), recipe_sha256=digest(ROOT / 'wildfire_lab/annual_selectors.py'),
                   results=results, selection_records=records,
                   wall_seconds=time.perf_counter() - start, hardware_jobs_submitted=0,
                   final_test_accessed=False, interpretation=plan['fairness'])
    args.output.mkdir(parents=True)
    (args.output / 'outcome.json').write_text(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(dict(comparisons=len(results), wall_seconds=outcome['wall_seconds'],
                         output=str(args.output))))


if __name__ == '__main__':
    main()
