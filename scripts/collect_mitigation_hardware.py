"""Collect the two accepted IBM jobs and publish their fixed comparison once ready."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.mitigation_hardware import collect
from wildfire_lab.mitigation_hardware_analysis import analyze

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results/annual-mitigation-ibm-v1')
    args=parser.parse_args()
    try:
        status=collect(args.output)
        if all(value=='DONE' for value in status.values()):
            result=analyze(ROOT,args.output)
            print(json.dumps(dict(status='collected',quantum_seconds=result['quantum_seconds_total'],
                                  comparisons=len(result['rows']),hardware_jobs=2,
                                  report=result['public_result_path'])))
        else:
            print(json.dumps(status))
    except Exception as error:
        print(json.dumps(dict(error_type=type(error).__name__,
                              message='Collection failed; private records preserved, no new hardware submission.')))
        raise SystemExit(1)

if __name__=='__main__':
    main()
