"""Run or collect the separately frozen local annual pipeline mitigation study."""
import argparse
import json
from pathlib import Path
import sys
import hashlib
from zipfile import ZipFile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['run', 'collect'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, default=ROOT/'docs/data/annual_training.csv')
    parser.add_argument('--bundle', type=Path, help='Collect published evidence into a fresh directory')
    args = parser.parse_args()
    if args.mode=='run':
        from wildfire_lab.mitigation_run import run
        data = run(ROOT,args.dataset,args.output,ROOT/'experiments/pipeline_mitigation.json')
        result = dict(prediction_records=len(data['predictions']), wall_seconds=data['wall_seconds'])
    else:
        from wildfire_lab.mitigation_collect import collect
        if args.bundle:
            summary = json.loads((ROOT/'docs/results/pipeline-mitigation.json').read_text())
            if hashlib.sha256(args.bundle.read_bytes()).hexdigest() != summary['bundle_sha256']:
                raise ValueError('Published bundle differs')
            with ZipFile(args.bundle) as archive:
                expected = {'evidence.json','intent.json','manifest.json','kernel_base.qpy','selector_base.qpy','audit.json'}
                if set(archive.namelist()) != expected or len(archive.namelist()) != len(expected):
                    raise ValueError('Unexpected bundle members')
                args.output.mkdir(parents=True,exist_ok=False)
                archive.extractall(args.output)
        result = collect(ROOT,args.output)
        (args.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
