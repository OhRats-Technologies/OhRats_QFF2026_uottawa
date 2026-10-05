"""Summarize Ontario cover on an equal-area coarse grid and run a bounded ablation."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_data import digest
from wildfire_lab.annual_woodland import file_hash, province_geometry, summarize, resolution_gate
from wildfire_lab.annual_cover_models import screen


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--plan', type=Path, default=ROOT / 'experiments/annual_woodland.json')
    cli.add_argument('--dataset', type=Path, default=ROOT / 'docs/data/annual_training.csv')
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--time-limit-seconds', type=float, default=1800)
    args = cli.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    plan = json.loads(args.plan.read_text())
    boundary = ROOT / plan['boundary']['path']
    parent_path = ROOT / plan['parent']
    for path, expected in [(boundary, plan['boundary']['sha256']),
                           (parent_path, plan['parent_sha256']),
                           (args.dataset, plan['dataset_sha256'])]:
        if digest(path) != expected:
            raise ValueError(f'Woodland parent changed: {path.name}')
    args.output.mkdir(parents=True)
    (args.output / 'intent.json').write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(), plan_sha256=digest(args.plan)), indent=2) + '\n')
    start = time.perf_counter()
    geometry = province_geometry(boundary)
    policy = plan['aggregation']
    summaries, gate, fine = [], None, None
    for year in range(plan['source_years'][0], plan['source_years'][1] + 1):
        path = ROOT / f'data/raw/woodland/woodland-{year}.tif'
        if file_hash(path) != plan['raster_sha256'][str(year)]:
            raise ValueError(f'Raster snapshot changed: {year}')
        record = dict(map_year=year, year=year + 1, source_sha256=plan['raster_sha256'][str(year)],
                      **summarize(path, geometry, policy['resolution_m'], policy['treed_codes'],
                                  args.output / f'cover-{year}.tif'))
        summaries.append(record)
        if year == policy['probe_year']:
            fine = summarize(path, geometry, policy['probe_resolution_m'], policy['treed_codes'])
            gate = resolution_gate(record, fine, policy)
        (args.output / 'progress.json').write_text(json.dumps(dict(summaries=summaries, gate=gate), indent=2) + '\n')
        print(json.dumps(dict(year=year, completed=len(summaries), seconds=time.perf_counter() - start,
                              treed_fraction=record['treed_fraction'], gate=gate)), flush=True)
        if not gate['accepted'] or record['uncovered_fraction'] > policy['max_uncovered_fraction']:
            break
        if time.perf_counter() - start > args.time_limit_seconds:
            break
    complete = (len(summaries) == 31 and gate['accepted']
                and all(r['uncovered_fraction'] <= policy['max_uncovered_fraction'] for r in summaries))
    results, resources = [], []
    if complete:
        table = pd.read_csv(args.dataset).merge(pd.DataFrame(summaries)[['year', 'map_year', 'treed_fraction']],
                                               on='year', validate='one_to_one')
        table.to_csv(args.output / 'annual.csv', index=False)
        results, resources = screen(table, json.loads(parent_path.read_text()), args.output / 'models')
    outcome = dict(study='annual-woodland', status='complete' if complete else 'pruned',
                   plan_sha256=digest(args.plan), recipe_sha256=digest(ROOT / 'wildfire_lab/annual_woodland.py'),
                   summaries=summaries, resolution_probe=fine, gate=gate, results=results, resources=resources,
                   wall_seconds=time.perf_counter() - start, hardware_jobs_submitted=0,
                   final_test_accessed=False, information=plan['information'], rejection_rule=plan['rejection'])
    (args.output / 'outcome.json').write_text(json.dumps(outcome, indent=2) + '\n')


if __name__ == '__main__':
    main()
