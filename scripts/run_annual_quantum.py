"""Run a separately cached four- or ten-qubit annual QSVR development screen."""

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_data import digest
from wildfire_lab.annual_quantum import screen


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--plan', type=Path, default=ROOT / 'experiments/annual_qsvr.json')
    cli.add_argument('--dataset', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--qubits', type=int, choices=[4, 10], required=True)
    args = cli.parse_args()
    plan = json.loads(args.plan.read_text())
    table = pd.read_csv(args.dataset)
    if table.year.min() < 1988 or table.year.max() > 2018:
        raise ValueError('Development accepts only the frozen training years')
    start = time.perf_counter()
    results, resources = screen(table, plan, args.output, args.qubits)
    outcome = dict(study='annual-qsvr', stage='quantum_development',
                   dataset_sha256=digest(args.dataset), plan_sha256=digest(args.plan),
                   recipe_sha256=digest(ROOT / 'wildfire_lab/annual_quantum.py'),
                   wall_seconds=time.perf_counter() - start, results=results,
                   resources=resources, hardware_jobs_submitted=0, final_test_accessed=False)
    (args.output / 'outcome.json').write_text(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(dict(qubits=args.qubits, comparisons=len(results),
                         wall_seconds=outcome['wall_seconds'], output=str(args.output))))


if __name__ == '__main__':
    main()
