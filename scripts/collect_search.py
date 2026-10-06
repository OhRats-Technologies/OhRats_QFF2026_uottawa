"""Verify published comprehensive-search evidence without running experiments."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.saved_search import collect

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('study', choices=['selector-multistart', 'expanded-tuning',
    'expanded-tuning-distinct', 'expanded-proxy-controls', 'shallow-preparation', 'objective-alignment'])
parser.add_argument('--output', type=Path, help='Optional directory for the arithmetic audit receipt')
args = parser.parse_args()
result = collect(ROOT, args.study)
if args.output is not None:
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
