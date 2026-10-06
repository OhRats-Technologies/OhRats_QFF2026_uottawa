"""Verify published IBM exploration/confirmation without credentials or new jobs."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.saved_hardware_search import collect

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('study', choices=['shallow-hardware-search', 'basis-confirmation-marrakesh',
                                    'basis-confirmation-quebec', 'tuned-kernel-hardware',
                                    'shot-sweep-marrakesh', 'shot-sweep-quebec'])
args = parser.parse_args()
print(json.dumps(collect(ROOT, args.study), indent=2))
