"""Labels-free exact-matrix signal/shot-budget diagnostic; no pair circuits."""
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
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.evaluation import split,sample_indices
from wildfire_lab.encoding_screen import preprocess
from wildfire_lab.kernel import angle_states,fidelity
from wildfire_lab.shot_noise import describe

RECIPES=['scripts/run_shot_feasibility.py','scripts/collect_shot_feasibility.py','wildfire_lab/shot_noise.py','wildfire_lab/evaluation.py',
    'wildfire_lab/encoding_screen.py','wildfire_lab/kernel.py','experiments/shot_feasibility.json',
    'experiments/quantum_landmarks.json','pyproject.toml','uv.lock']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/shot-feasibility')
    args=parser.parse_args();plan=json.loads((ROOT/'experiments/shot_feasibility.json').read_text())
    parent=json.loads((ROOT/plan['parent_plan']).read_text())
    assert not any(plan[k] for k in ['hardware','final_test_access','labels_used','model_fits','pair_circuits'])
    assert len(plan['seeds'])*len(plan['angle_scales'])*(parent['train_cap']+parent['validation_cap'])<=plan['max_simulated_state_preparations']
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes();assert raw==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name
        hashes[name]=hashlib.sha256(raw).hexdigest()
    source=ROOT/parent['dataset']/'features.csv';assert sha(source)==parent['dataset_sha256']
    intent=dict(plan=plan,parent_plan=parent,git_commit=commit,recipe_sha256=hashes,started_utc=datetime.now(timezone.utc).isoformat())
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    outcome=dict(status='running',intent=intent,conditions=[],simulated_state_preparations=0)
    start=time.perf_counter()
    def save():
        tmp=args.output/'outcome.tmp';tmp.write_text(json.dumps(outcome,indent=2)+'\n');os.replace(tmp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Declared diagnostic wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    try:
        frame=pd.read_csv(source,usecols=['incident_id','year',*parent['features']])
        assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
        train,valid=split(frame,parent['fold'],train_window=(1988,2018))
        for seed in plan['seeds']:
            ti=sample_indices(len(train),parent['train_cap'],seed);vi=sample_indices(len(valid),parent['validation_cap'],seed)
            _,_,bx,bv=preprocess(train.iloc[ti],valid.iloc[vi],parent['features'],parent['preprocessing'])
            for scale in plan['angle_scales']:
                a=angle_states(np.pi*(.5+scale*bx),plan['reps']);b=angle_states(np.pi*(.5+scale*bv),plan['reps'])
                gram,cross=fidelity(a,a),fidelity(b,a);name=f'seed-{seed}-scale-{scale}.npz'
                with (args.output/name).open('xb') as f:np.savez_compressed(f,gram=gram,cross=cross)
                outcome['conditions'].append(dict(seed=seed,angle_scale=scale,training_rows=len(ti),validation_rows=len(vi),
                    train_indices_sha256=hashlib.sha256(ti.tobytes()).hexdigest(),validation_indices_sha256=hashlib.sha256(vi.tobytes()).hexdigest(),
                    matrix_file=name,matrix_sha256=sha(args.output/name),**describe(gram,cross,plan['shots'],plan['relative_frobenius_targets'])))
                outcome['simulated_state_preparations']+=len(a)+len(b);save()
        outcome['status']='complete'
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps(dict(status=outcome['status'],conditions=len(outcome['conditions']),seconds=outcome['seconds'],simulated_state_preparations=outcome['simulated_state_preparations'])))


if __name__=='__main__':main()
