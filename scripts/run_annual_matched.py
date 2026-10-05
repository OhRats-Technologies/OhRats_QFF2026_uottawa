"""Compare equally budgeted classical/quantum kernel selection on annual data."""

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_data import digest
from wildfire_lab.annual_matched import load_inputs, screen


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--dataset', type=Path, default=ROOT / 'docs/data/annual_training.csv')
    cli.add_argument('--plan', type=Path, default=ROOT / 'experiments/annual_matched.json')
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    table, plan, parent, quantum = load_inputs(args.dataset, args.plan, ROOT)
    start = time.perf_counter()
    results = screen(table, plan, parent, quantum)
    outcome = dict(study='annual-matched', dataset_sha256=digest(args.dataset),
                   plan_sha256=digest(args.plan), recipe_sha256=digest(ROOT / 'wildfire_lab/annual_matched.py'),
                   results=results, wall_seconds=time.perf_counter() - start,
                   classical_svr_fits=654, candidates_per_family_per_fold=36,
                   new_quantum_kernels=0, hardware_jobs_submitted=0, final_test_accessed=False,
                   selection_rule=plan['selection'], limitations=plan['limitations'])
    args.output.mkdir(parents=True)
    (args.output / 'outcome.json').write_text(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(dict(results=len(results), wall_seconds=outcome['wall_seconds'],
                         output=str(args.output))))


if __name__ == '__main__':
    main()
