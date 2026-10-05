"""Validate saved library pilot predictions and export aggregate evidence; no fits."""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from wildfire_lab.evaluation import scores,sample_indices,split

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'.cache/wildfire/library-followup-v3/outcome.json')
    args=parser.parse_args();outcome=json.loads(args.input.read_text())
    assert outcome['status']=='complete'
    intent=json.loads(args.input.with_name('intent.json').read_text())
    assert intent==outcome['intent'];plan=intent['plan']
    assert not plan['final_test_access'] and not plan['hardware']
    source=ROOT/plan['dataset']/'features.csv';assert sha(source)==plan['dataset_sha256']
    for name,digest in intent['recipe_hashes'].items():
        raw=subprocess.check_output(['git','show',f"{intent['git_commit']}:{name}"],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==digest,name
    import pandas as pd
    train,valid=split(pd.read_csv(source),plan['fold'],train_window=(1988,2018))
    means=defaultdict(list);public=[]
    for row in outcome['seeds']:
        assert row['status']=='complete'
        ti=sample_indices(len(train),plan['train_cap'],row['seed'])
        vi=sample_indices(len(valid),plan['validation_cap'],row['seed'])
        assert row['train_indices_sha256']==hashlib.sha256(ti.tobytes()).hexdigest()
        assert row['validation_indices_sha256']==hashlib.sha256(vi.tobytes()).hexdigest()
        y=valid.iloc[vi].target.to_numpy();np.testing.assert_array_equal(y,row['validation_target'])
        clean={key:value for key,value in row.items() if key not in ['kernel_rows','validation_target']}
        clean['kernel_rows']=[]
        for result in row['kernel_rows']:
            recomputed=scores(y,np.array(result['predictions']),False)
            for key,value in result['metric'].items():np.testing.assert_allclose(value,recomputed[key],atol=1e-12)
            clean['kernel_rows'].append({k:v for k,v in result.items() if k!='predictions'})
            means[result['predictor']].append(result['metric']['average_precision'])
        public.append(clean)
    assert [r['seed'] for r in public]==plan['seeds']
    attempts=[]
    for name in ['library-followup','library-followup-v2','library-followup-v3']:
        path=ROOT/'.cache/wildfire'/name/'outcome.json'
        if path.exists():
            record=json.loads(path.read_text())
            attempts.append(dict(name=name,status=record['status'],seconds=record['seconds'],
                outcome_sha256=sha(path),error_type=record.get('error_type')))
    evidence=dict(status='audited_training_only_followup',outcome_sha256=sha(args.input),
        intent_sha256=sha(args.input.with_name('intent.json')),plan=plan,
        recipe_commit=intent['git_commit'],recipe_hashes=intent['recipe_hashes'],
        means={k:float(np.mean(v)) for k,v in means.items()},seeds=public,
        attempts=attempts,total_recorded_runner_seconds=sum(a['seconds'] for a in attempts),
        checks=['source hash','committed recipes','sample hashes','saved-prediction metrics'],
        limitations='Post-final training-only exploration. Same seeds rerun for repairs are not replications. First failed attempt did not retain inner kernel rows; later partial failures are preserved. Synthetic shots, no hardware.')
    (ROOT/'docs/results/library-followup.json').write_text(json.dumps(evidence,separators=(',',':'))+'\n')
    print(json.dumps(dict(means=evidence['means'],total_runner_seconds=evidence['total_recorded_runner_seconds'])))


if __name__=='__main__':main()
