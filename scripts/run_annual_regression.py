"""Prepare the annual macro table and run its classical development controls."""

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_data import prepare, digest
from wildfire_lab.annual_classical import screen


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--plan', type=Path, default=ROOT / 'experiments/annual_qsvr.json')
    cli.add_argument('--dataset', type=Path, help='Replay a prepared 31-year training CSV without raw acquisition')
    cli.add_argument('--weather', type=Path, help='Explicit prepared station-month CSV')
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    plan = json.loads(args.plan.read_text())
    if args.output.exists():
        raise FileExistsError(args.output)
    start = time.perf_counter()
    if args.dataset:
        table = pd.read_csv(args.dataset)
        if table.year.tolist() != list(range(1988, 2019)):
            raise ValueError('Prepared replay requires exactly the 31 training years')
        args.output.mkdir(parents=True)
        manifest = dict(mode='prepared_csv_replay', table_sha256=digest(args.dataset),
                        rows=31, years=[1988, 2018], input_precision='Parsed CSV values')
    else:
        weather = args.weather
        if weather is None:
            from wildfire_lab.weather_preparation import prepare_weather
            weather_directory, _ = prepare_weather(ROOT / 'configs/wildfires/ontario.json',
                                                   ROOT / 'data/raw/weather', ROOT / '.cache/wildfire')
            weather = weather_directory / 'weather_months.csv'
        table, manifest = prepare(ROOT / 'data/raw/nfdb-audit/source.zip', weather,
                                  args.plan, args.output / 'data')
    preparation_seconds = time.perf_counter() - start
    start = time.perf_counter()
    results = screen(table, plan)
    outcome = dict(study='annual-qsvr', stage='classical_development',
                   unit='Ontario province-year', target='mean_reported_size_ha',
                   plan_sha256=digest(args.plan), dataset_manifest=manifest,
                   preparation_seconds=preparation_seconds,
                   fitting_seconds=time.perf_counter() - start, results=results,
                   hardware_jobs_submitted=0, final_test_accessed=False)
    (args.output / 'classical.json').write_text(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(dict(rows=len(table), comparisons=len(results),
                         preparation_seconds=preparation_seconds,
                         fitting_seconds=outcome['fitting_seconds'], output=str(args.output))))


if __name__ == '__main__':
    main()
