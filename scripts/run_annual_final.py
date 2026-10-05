"""Train final annual states first, then execute one frozen reused-year evaluation."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_final_protocol import train, evaluate


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('stage', choices=['train', 'evaluate'])
    cli.add_argument('--plan', type=Path, default=ROOT / 'experiments/annual_final.json')
    cli.add_argument('--output', type=Path, required=True,
                     help='New training namespace, or that same namespace for one evaluation')
    args = cli.parse_args()
    action = train if args.stage == 'train' else evaluate
    print(json.dumps(action(ROOT, args.plan, args.output)))


if __name__ == '__main__':
    main()
