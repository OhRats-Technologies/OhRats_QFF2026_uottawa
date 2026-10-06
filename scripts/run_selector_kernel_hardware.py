"""Prepare, submit once or collect actual QSVR kernels for hardware-selected subsets."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.selector_kernel_hardware import prepare, submit, collect


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','submit','collect'])
    parser.add_argument('--output',type=Path,default=ROOT/'results/selector-kernel-hardware-v1')
    args = parser.parse_args()
    try:
        result = collect(args.output) if args.mode=='collect' else globals()[args.mode](ROOT,args.output)
        print(json.dumps(result,indent=2))
    except Exception as error:
        print(json.dumps(dict(error_type=type(error).__name__,message='Hardware action failed; preserve records/intents; private details omitted.')))
        raise SystemExit(1)
