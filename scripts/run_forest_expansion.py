"""Run or collect the separately frozen training-only forest panel."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['run','collect'])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bundle',type=Path)
    args=parser.parse_args()
    if args.mode=='run':
        from wildfire_lab.forest_run import run
        result=run(ROOT,args.output.resolve(),ROOT/'experiments/forest_expansion.json')
        print(json.dumps({k:result[k] for k in ['status','seconds','model_fits','pair_circuits']}))
    else:
        from wildfire_lab.forest_collect import collect
        print(json.dumps(collect(ROOT,args.output.resolve(),args.bundle),indent=2))


if __name__=='__main__':
    main()
