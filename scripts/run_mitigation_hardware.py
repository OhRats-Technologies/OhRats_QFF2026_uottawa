"""Prepare, submit once or collect the owner-budgeted IBM pipeline experiment."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.mitigation_hardware import prepare,submit,collect

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','submit','collect'])
    parser.add_argument('--output',type=Path,default=ROOT/'results/annual-mitigation-ibm-v1')
    parser.add_argument('--plan',type=Path,help='Separately frozen backend-specific hardware plan')
    args=parser.parse_args()
    try:
        if args.mode=='prepare':
            result=prepare(ROOT,args.output,args.plan)
        elif args.mode=='submit':
            result=submit(ROOT,args.output)
        else:
            result=collect(args.output)
        print(json.dumps(result,indent=2))
    except Exception as error:
        print(json.dumps(dict(error_type=type(error).__name__,
            message='Hardware action failed; preserve every intent, do not retry an existing submission. Private identifiers omitted.')))
        raise SystemExit(1)

if __name__=='__main__':
    main()
