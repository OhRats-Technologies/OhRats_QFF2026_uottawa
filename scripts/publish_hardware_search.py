"""Package already analyzed hardware evidence, excluding service/job identifiers."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wildfire_lab.saved_hardware_search import collect

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('study')
parser.add_argument('--output', type=Path, required=True, help='Existing private analyzed namespace')
args = parser.parse_args()
result = json.loads((args.output/'analysis.json').read_text())
receipt = json.loads((args.output/'prepared.json').read_text())
evidence = dict(analysis=result, plan=receipt['plan'], code_sha256=receipt['code_sha256'])
raw = json.dumps(evidence, separators=(',', ':')).encode()
assert not re.search(rb'"(?:job_id|instance_crn|token|api_key)"\s*:', raw)
assert b'crn:v1:' not in raw
bundle = ROOT/f'docs/data/{args.study}-evidence.zip'
assert not bundle.exists(), 'Published evidence is immutable'
with ZipFile(bundle, 'w', compression=ZIP_DEFLATED) as archive:
    archive.writestr('evidence.json', raw)
index = dict(study=args.study, bundle=str(bundle.relative_to(ROOT)),
    bundle_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),
    evidence_sha256=hashlib.sha256(raw).hexdigest(), status='complete',
    backend=result['backend'], hardware_jobs=result['hardware_jobs'],
    physical_shots=result['physical_shots'], charged_seconds=result['charged_seconds'],
    final_test_accessed=False, limitation=result['limitation'])
(ROOT/f'docs/results/{args.study}.json').write_text(json.dumps(index, indent=2)+'\n')
print(json.dumps(collect(ROOT, args.study)))
