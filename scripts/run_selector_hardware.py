"""Prepare, submit once or collect the owner-authorized larger-selector hardware study."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.selector_hardware import prepare, submit, collect


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','submit','collect'])
    parser.add_argument('--output',type=Path,default=ROOT/'results/selector-hardware-v1')
    args = parser.parse_args()
    try:
        result = collect(args.output) if args.mode=='collect' else globals()[args.mode](ROOT,args.output)
        print(json.dumps(result,indent=2))
    except Exception as error:
        print(json.dumps(dict(error_type=type(error).__name__,message='Hardware action failed; preserve intents, no blind retry; private details omitted.')))
        raise SystemExit(1)
