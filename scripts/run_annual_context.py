"""Run the frozen training-only annual climate context sensitivities."""

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_data import digest
from wildfire_lab.annual_context import screen


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--dataset', type=Path, default=ROOT / 'docs/data/annual_training.csv')
    cli.add_argument('--weather', type=Path, default=ROOT / '.cache/wildfire/processed/weather/52f047eb76b948cf66d5/weather_months.csv')
    cli.add_argument('--plan', type=Path, default=ROOT / 'experiments/annual_context.json')
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    plan = json.loads(args.plan.read_text())
    parent_path = ROOT / plan['parent']
    for path, expected in [(args.dataset, plan['dataset_sha256']),
                           (args.weather, plan['weather_sha256']),
                           (parent_path, plan['parent_sha256'])]:
        if digest(path) != expected:
            raise ValueError(f'Frozen context source changed: {path.name}')
    labels = pd.read_csv(args.dataset)
    if labels.year.tolist() != list(range(1988, 2019)):
        raise ValueError('Context study requires only the frozen 31 training years')
    weather = pd.read_csv(args.weather, dtype={'climate_id': str})
    weather = weather[pd.to_datetime(weather.month).dt.year.between(1987, 2018)]
    start = time.perf_counter()
    results, datasets, resources = screen(labels, weather, json.loads(parent_path.read_text()), plan, args.output)
    outcome = dict(study='annual-context', plan_sha256=digest(args.plan),
                   recipe_sha256=digest(ROOT / 'wildfire_lab/annual_context.py'),
                   results=results, datasets=datasets, resources=resources,
                   wall_seconds=time.perf_counter() - start,
                   hardware_jobs_submitted=0, final_test_accessed=False,
                   interpretation=plan['interpretation'])
    (args.output / 'outcome.json').write_text(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(dict(comparisons=len(results), wall_seconds=outcome['wall_seconds'])))


if __name__ == '__main__':
    main()
