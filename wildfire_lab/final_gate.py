"""One global final-test opening, after the protocol and recipes are committed."""
import hashlib
import json
import re
import subprocess
from datetime import datetime,timezone
from pathlib import Path


def validate_plan(plan):
    if plan['status']!='frozen_final':raise ValueError('Final protocol is still a draft')
    if plan['train_years']!=[1988,2018] or plan['test_years']!=[2019,2024]:raise ValueError('Unexpected final year windows')
    if plan['hardware_default'] is not False:raise ValueError('Final evaluation is local only')
    if plan['cover_policy']['mode'] not in {'fixed_historical','previous_year'}:raise ValueError('Cover policy must be settled')
    if not plan['training_dataset_fingerprint']:raise ValueError('Training snapshot must be settled')
    if not re.fullmatch('[0-9a-f]{64}',plan.get('training_data_sha256') or ''):raise ValueError('Training hash must be settled')
    if plan['threshold_ha']!=10:raise ValueError('Keep the declared 10 ha target')


def reserve(plan_path,cache,root,recipes):
    raw=plan_path.read_bytes();plan=json.loads(raw);validate_plan(plan)
    frozen={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [plan_path,*recipes]}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()
    for path,digest in frozen.items():
        result=subprocess.run(['git','show',f'{commit}:{path}'],cwd=root,capture_output=True)
        if result.returncode or hashlib.sha256(result.stdout).hexdigest()!=digest:
            raise ValueError('Commit final protocol and recipes before opening: '+path)
    cache.mkdir(parents=True,exist_ok=True)
    intent=dict(status='opened',opened_utc=datetime.now(timezone.utc).isoformat(),plan_sha256=hashlib.sha256(raw).hexdigest(),git_commit=commit,recipe_sha256=frozen)
    with (cache/'intent.json').open('x') as stream:json.dump(intent,stream,indent=2);stream.write('\n')
    return plan,intent
