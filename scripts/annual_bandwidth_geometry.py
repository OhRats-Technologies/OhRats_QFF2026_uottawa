"""Execute or collect the frozen input-only annual bandwidth diagnostic."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.annual_bandwidth_geometry import run, collect

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run', 'collect'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan = ROOT / 'experiments/annual_bandwidth_geometry.json'
    result = run(ROOT, plan, args.output) if args.action == 'run' else collect(ROOT, plan, args.output)
    if args.action == 'collect':
        (args.output / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result if args.action == 'collect' else {k:v for k,v in result.items() if k != 'results'}, indent=2))
