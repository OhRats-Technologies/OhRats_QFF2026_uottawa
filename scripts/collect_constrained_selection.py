"""Collect the frozen constrained selector diagnostic; no optimizer/model refit."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.evaluation import split
from wildfire_lab.constrained_checks import validate_seed,review


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(cache,output):
    start=time.perf_counter();record=json.loads((cache/'outcome.json').read_text());intent=json.loads((cache/'intent.json').read_text())
    assert record['status']=='complete' and record['intent']==intent;plan,parent=intent['plan'],intent['parent_plan']
    for name,expected in intent['recipe_sha256'].items():
        raw=subprocess.check_output(['git','show',f'{intent["git_commit"]}:{name}'],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==expected,name
        if name=='experiments/constrained_selection.json':assert json.loads(raw)==plan
        if name==plan['parent_plan']:assert json.loads(raw)==parent
    for name in ['wildfire_lab/constrained_qaoa.py','wildfire_lab/constrained_checks.py','wildfire_lab/constrained_selection.py',
        'wildfire_lab/selection.py','wildfire_lab/evaluation.py']:assert sha(ROOT/name)==intent['recipe_sha256'][name]
    source=ROOT/parent['dataset']/'features.csv';assert sha(source)==parent['dataset_sha256']
    frame=pd.read_csv(source);assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
    train,valid=split(frame,parent['fold'],train_window=(1988,2018));totals=dict(quantum_state_evaluations=0,predictor_fits=0,audit_reconstruction_states=0)
    seen=set();public=[]
    for row in record['seeds']:
        key=(row['group'],row['seed']);assert key not in seen;seen.add(key)
        counts=validate_seed(train,valid,parent,plan,row)
        for name,value in counts.items():totals[name]+=value
        public.append({**{k:v for k,v in row.items() if k not in ['preprocessing','quantum','rows']},
            'quantum':[{k:v for k,v in q.items() if k not in ['probabilities','draws']} for q in row['quantum']],
            'rows':[{k:v for k,v in r.items() if k not in ['predictions','draws','coefficient','intercept','l1_coefficient']} for r in row['rows']]})
    assert seen=={(g,s) for g,k in [('diagnostic','diagnostic_seeds'),('sampling_check','sampling_check_seeds')] for s in plan[k]}
    for name in ['quantum_state_evaluations','predictor_fits']:assert totals[name]==record[name]<=plan['max_'+name]
    assert record['l1_selector_fits']==len(seen)<=plan['max_l1_selector_fits'] and record['seconds']<=plan['max_wall_seconds']
    summary=dict(status='audited_constrained_selection',opening_commit=intent['git_commit'],outcome_sha256=sha(cache/'outcome.json'),
        intent_sha256=sha(cache/'intent.json'),dataset_sha256=parent['dataset_sha256'],plan=plan,fold=parent['fold'],
        runner_seconds=record['seconds'],audit_seconds=time.perf_counter()-start,**totals,l1_selector_fits=record['l1_selector_fits'],
        synthetic_quantum_draws=len(seen)*len(plan['initial_states'])*len(plan['mixers'])*plan['shots'],
        hardware_jobs_submitted=0,final_test_access=False,predictive_model_refits_in_collection=0,
        audit_recipe_sha256={name:sha(ROOT/name) for name in ['scripts/collect_constrained_selection.py','wildfire_lab/constrained_checks.py']},
        review=review(record['seeds']),seeds=public,limitations=plan['interpretation'])
    # One logical record per line, keeping generated evidence readable and compact.
    header={k:v for k,v in summary.items() if k!='seeds'}
    lines=[json.dumps(header,separators=(',',':'))[:-1]+',"seeds":[']
    for i,seed in enumerate(public):
        context={k:v for k,v in seed.items() if k not in ['quantum','rows']}
        lines.append(json.dumps(context,separators=(',',':'))[:-1]+',"quantum":[')
        lines.extend(json.dumps(q,separators=(',',':'))+(',' if j<len(seed['quantum'])-1 else '') for j,q in enumerate(seed['quantum']))
        lines.append('],"rows":[')
        lines.extend(json.dumps(r,separators=(',',':'))+(',' if j<len(seed['rows'])-1 else '') for j,r in enumerate(seed['rows']))
        lines.append(']}'+(',' if i<len(public)-1 else ''))
    lines.append(']}');output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:summary[k] for k in ['status','runner_seconds','audit_seconds','quantum_state_evaluations','predictor_fits','review']}))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'.cache/wildfire/constrained-selection')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/results/constrained-selection.json')
    args=parser.parse_args();collect(args.cache,args.output)
