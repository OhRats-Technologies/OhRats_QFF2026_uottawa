"""Collect saved annual SVR signal and train-only Gram diagnostics."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_signal import describe


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--run', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    receipt = describe(ROOT, args.run)
    with args.output.open('x') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(models=len(receipt['main_kernel_signals']),
                         kernels=len(receipt['kernel_diagnostics']), new_quantum_states=0)))
