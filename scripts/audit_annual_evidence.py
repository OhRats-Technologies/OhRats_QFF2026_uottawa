"""Audit annual aggregation, metrics and fixed cached-kernel prediction replay."""

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_evidence import audit


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    start = time.perf_counter()
    receipt = audit(ROOT, args.output)
    receipt['wall_seconds'] = time.perf_counter() - start
    (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(checked=receipt['metric_records_checked'],
                         new_quantum_states=receipt['new_quantum_states'],
                         wall_seconds=receipt['wall_seconds'])))


if __name__ == '__main__':
    main()
