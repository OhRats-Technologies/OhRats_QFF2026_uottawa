"""Verify fixed annual predictions and metrics from saved states and matrices."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_final_audit import collect


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--run', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    receipt = collect(ROOT, args.run, ROOT / 'experiments/annual_final.json')
    with args.output.open('x') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key: receipt[key] for key in ['status', 'prediction_records_checked',
                                                 'kernel_records_checked', 'new_quantum_states']}))


if __name__ == '__main__':
    main()
