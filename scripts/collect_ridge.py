"""Reconstruct training-only kernels and audit saved coefficients without fitting."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from wildfire_lab.evaluation import split
from wildfire_lab.ridge_inputs import build
from wildfire_lab.ridge_checks import verify
from wildfire_lab.ridge_review import review
ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'.cache/wildfire/kernel-ridge/outcome.json')
    args=parser.parse_args();outcome=json.loads(args.input.read_text());assert outcome['status']=='complete'
    intent=json.loads(args.input.with_name('intent.json').read_text());assert intent==outcome['intent']
    plan,parent=intent['plan'],intent['parent_plan'];assert not plan['hardware'] and not plan['final_test_access']
    assert sha(ROOT/plan['parent_evidence'])==intent['parent_evidence_sha256']
    source=ROOT/parent['dataset']/'features.csv';assert sha(source)==parent['dataset_sha256']
    for name,digest in intent['recipe_hashes'].items():
        raw=subprocess.check_output(['git','show',f"{intent['git_commit']}:{name}"],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==digest,name
        assert (ROOT/name).read_bytes()==raw,name
    import pandas as pd
    frame=pd.read_csv(source);assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
    train,valid=split(frame,parent['fold'],train_window=(1988,2018))
    expected=[('diagnostic',s) for s in plan['diagnostic_seeds']]+[('sampling_check',s) for s in plan['sampling_check_seeds']]
    assert [(s['group'],s['seed']) for s in outcome['seeds']]==expected
    before=time.perf_counter();public=[];means=defaultdict(lambda:defaultdict(list));certificates=[]
    for sample in outcome['seeds']:
        kernels,y,target,meta=build(train,valid,parent,plan,sample['seed'])
        for key,value in meta.items():assert sample[key]==value,key
        assert [r['predictor'] for r in sample['rows']]==list(kernels)
        clean={k:v for k,v in sample.items() if k not in ['rows','validation_target']};clean['rows']=[]
        for row in sample['rows']:
            gram,cross,features,extra=kernels[row['predictor']]
            certificate=verify(row,gram,cross,features,y,target,plan['kernel_ridge'])
            certificates.append(dict(seed=sample['seed'],predictor=row['predictor'],**certificate))
            for key,value in extra.items():np.testing.assert_allclose(row[key],value,atol=1e-10)
            clean['rows'].append({k:v for k,v in row.items() if k not in ['predictions','coefficients','primal_coefficients']})
            means[sample['group']][row['predictor']].append(row['metric']['average_precision'])
        public.append(clean)
    checks=review(public,plan);assert checks==outcome['review']
    states=sum(s['simulated_state_preparations'] for s in public)
    assert states<=plan['max_simulated_state_preparations'] and outcome['seconds']<=plan['max_wall_seconds']
    evidence=dict(status='audited_training_only_ridge',plan=plan,parent_plan=parent,
        recipe_commit=intent['git_commit'],recipe_hashes=intent['recipe_hashes'],
        outcome_sha256=sha(args.input),intent_sha256=sha(args.input.with_name('intent.json')),
        audit_recipe_sha256=sha(Path(__file__)),audit_checks_sha256=sha(ROOT/'wildfire_lab/ridge_checks.py'),
        seeds=public,means={g:{k:float(np.mean(v)) for k,v in values.items()} for g,values in means.items()},
        review=checks,runner_seconds=outcome['seconds'],runner_state_preparations=states,
        audit_reconstruction_seconds=time.perf_counter()-before,audit_state_preparations=states,
        certificate_checks=certificates,checks=['source/committed recipes','actual capped labels and landmark indices',
            'reconstructed kernels and stored coefficient equations','primal/dual agreement','saved metrics','fixed gates'],
        limitations='Post-final training-only comparison. Fresh sampling seeds reuse chronological years; no final-performance or hardware-speed claim. Audit reconstructs simulated states but performs no model fits or solves. Original SVM/landmark outcomes remain frozen.')
    (ROOT/'docs/results/kernel-ridge.json').write_text(json.dumps(evidence,separators=(',',':'))+'\n')
    print(json.dumps(dict(means=evidence['means'],review=checks,seconds=evidence['runner_seconds'],audit_seconds=evidence['audit_reconstruction_seconds'])))


if __name__=='__main__':main()
