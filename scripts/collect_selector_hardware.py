"""Verify public IBM selector/kernel counts and predictions without new execution."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.saved_hardware_selector import audit as selector_audit
from wildfire_lab.saved_hardware_kernels import audit as kernel_audit, audit_shards


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['selector','kernels','both','all','shards'],default='all')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    receipt = {}
    if args.stage in {'selector','both','all'}:
        receipt['selector'] = selector_audit(ROOT)
    if args.stage in {'kernels','both','all'}:
        receipt['kernels'] = kernel_audit(ROOT)
    if args.stage in {'shards','all'}:
        receipt['shards'] = audit_shards(ROOT)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
