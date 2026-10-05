"""Exclusive training-only landmark experiment; no final access or hardware."""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

ROOT=Path(__file__).resolve().parents[1]
RECIPES=['scripts/run_landmark_screen.py','wildfire_lab/landmark_screen.py',
    'wildfire_lab/landmarks.py','wildfire_lab/landmark_review.py','wildfire_lab/library_kernel.py',
    'wildfire_lab/evaluation.py','wildfire_lab/encoding_screen.py','wildfire_lab/kernel.py',
    'experiments/quantum_landmarks.json','pyproject.toml','uv.lock']


def digest(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/quantum-landmarks')
    args=parser.parse_args()
    plan=json.loads((ROOT/'experiments/quantum_landmarks.json').read_text())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes()
        assert raw==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name
        hashes[name]=digest(raw)
    source=ROOT/plan['dataset']/'features.csv'
    assert digest(source.read_bytes())==plan['dataset_sha256']
    assert not plan['hardware'] and not plan['final_test_access']
    from wildfire_lab.landmarks import pair_count
    expected=pair_count(plan['train_cap'],plan['validation_cap'],plan['shot_landmarks'])
    assert expected*len(plan['shots'])*len(plan['seeds'])<=plan['max_pair_circuits']
    args.output.mkdir(parents=True,exist_ok=True)
    intent=dict(plan=plan,git_commit=commit,recipe_hashes=hashes,
        started_utc=datetime.now(timezone.utc).isoformat())
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    start=time.perf_counter();outcome=dict(status='running',intent=intent,seeds=[])
    def save():
        tmp=args.output/'outcome.tmp';tmp.write_text(json.dumps(outcome,indent=2)+'\n')
        os.replace(tmp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Declared local wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    def checkpoint(progress=None):
        if progress is not None:outcome['progress']=progress;save()
        if time.perf_counter()-start>=plan['max_wall_seconds']:timeout()
    try:
        import pandas as pd
        from wildfire_lab.evaluation import split
        from wildfire_lab.landmark_screen import run
        from wildfire_lab.landmark_review import review
        frame=pd.read_csv(source)
        assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
        train,valid=split(frame,plan['fold'],train_window=(1988,2018))
        used=0
        for seed in plan['seeds']:
            checkpoint()
            result=run(train,valid,plan,seed,checkpoint,plan['max_pair_circuits']-used)
            used+=result['pair_circuits'];outcome['seeds'].append(result);save()
            print(json.dumps(dict(seed=seed,pair_circuits=used,status='complete')),flush=True)
        outcome.update(status='complete',review=review(outcome['seeds'],plan),pair_circuits=used)
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps(dict(status=outcome['status'],seconds=outcome['seconds'],review=outcome['review'])))


if __name__=='__main__':main()
