"""Verify saved exact matrices and recompute analytic shot diagnostics; no fit."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.evaluation import split,sample_indices
from wildfire_lab.shot_noise import describe


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(cache,output):
    start=time.perf_counter();record=json.loads((cache/'outcome.json').read_text());intent=json.loads((cache/'intent.json').read_text())
    assert record['status']=='complete' and record['intent']==intent
    plan,parent=intent['plan'],intent['parent_plan'];commit=intent['git_commit']
    for name,expected in intent['recipe_sha256'].items():
        raw=subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT);assert hashlib.sha256(raw).hexdigest()==expected,name
        if name=='experiments/shot_feasibility.json':assert json.loads(raw)==plan
        if name==plan['parent_plan']:assert json.loads(raw)==parent
    assert sha(ROOT/'wildfire_lab/shot_noise.py')==intent['recipe_sha256']['wildfire_lab/shot_noise.py']
    source=ROOT/parent['dataset']/'features.csv';assert sha(source)==parent['dataset_sha256']
    frame=pd.read_csv(source,usecols=['incident_id','year']);assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
    train,valid=split(frame,parent['fold'],train_window=(1988,2018));rows=[];conditions=set()
    for row in record['conditions']:
        key=(row['seed'],row['angle_scale']);assert key not in conditions;conditions.add(key)
        ti=sample_indices(len(train),parent['train_cap'],row['seed']);vi=sample_indices(len(valid),parent['validation_cap'],row['seed'])
        for prefix,indices in [('train',ti),('validation',vi)]:assert hashlib.sha256(indices.tobytes()).hexdigest()==row[prefix+'_indices_sha256']
        path=cache/row['matrix_file'];assert path.parent==cache and sha(path)==row['matrix_sha256']
        with np.load(path,allow_pickle=False) as arrays:gram,cross=arrays['gram'],arrays['cross']
        assert gram.shape==(len(ti),len(ti)) and cross.shape==(len(vi),len(ti))
        measured=describe(gram,cross,plan['shots'],plan['relative_frobenius_targets'])
        assert all(row[k]==v for k,v in measured.items())
        rows.append({k:v for k,v in row.items() if k!='matrix_file'})
    assert conditions=={(s,a) for s in plan['seeds'] for a in plan['angle_scales']}
    preparations=sum(r['training_rows']+r['validation_rows'] for r in rows)
    assert preparations==record['simulated_state_preparations']<=plan['max_simulated_state_preparations']
    assert record['seconds']<=plan['max_wall_seconds']
    result=dict(status='audited_analytic_shot_feasibility',opening_commit=commit,outcome_sha256=sha(cache/'outcome.json'),
        intent_sha256=sha(cache/'intent.json'),dataset_sha256=parent['dataset_sha256'],plan=plan,
        fold=parent['fold'],features=parent['features'],preprocessing=parent['preprocessing'],
        audit_recipe_sha256={name:sha(ROOT/name) for name in ['scripts/collect_shot_feasibility.py','wildfire_lab/shot_noise.py']},
        runner_seconds=record['seconds'],audit_seconds=time.perf_counter()-start,simulated_state_preparations=preparations,
        labels_used=False,model_fits=0,final_test_access=False,pair_circuits_executed=0,shots_executed=0,hardware_jobs_submitted=0,
        conditions=rows,limitations=plan['interpretation'])
    output.parent.mkdir(parents=True,exist_ok=True)
    header={k:v for k,v in result.items() if k!='conditions'}
    output.write_text(json.dumps(header,separators=(',',':'))[:-1]+',"conditions":[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n]}\n')
    print(json.dumps(dict(status=result['status'],conditions=len(rows),runner_seconds=record['seconds'],audit_seconds=result['audit_seconds'])))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'.cache/wildfire/shot-feasibility')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/results/shot-feasibility.json')
    args=parser.parse_args();collect(args.cache.resolve(),args.output)
