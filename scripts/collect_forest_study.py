"""Collect public forest or selector evidence without fitting, sampling or downloads."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wildfire_lab.forest_publication import STUDIES, collect


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study',choices=list(STUDIES))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(collect(ROOT,args.study,args.output.resolve()),indent=2))
