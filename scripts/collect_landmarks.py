"""Read-only landmark evidence audit and compact public export; no model fitting."""
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
from wildfire_lab.landmarks import indices,pair_count
from wildfire_lab.landmark_review import review

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'.cache/wildfire/quantum-landmarks/outcome.json')
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
    frame=pd.read_csv(source);assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
    train,valid=split(frame,plan['fold'],train_window=(1988,2018))
    means=defaultdict(list);public=[];used=0;synthetic=0
    for row in outcome['seeds']:
        ti=sample_indices(len(train),plan['train_cap'],row['seed'])
        vi=sample_indices(len(valid),plan['validation_cap'],row['seed'])
        assert row['train_indices_sha256']==hashlib.sha256(ti.tobytes()).hexdigest()
        assert row['validation_indices_sha256']==hashlib.sha256(vi.tobytes()).hexdigest()
        y=valid.iloc[vi].target.to_numpy();np.testing.assert_array_equal(y,row['validation_target'])
        assert row['train_rows']==len(ti) and row['validation_rows']==len(vi)
        assert row['train_positive']==int(train.iloc[ti].target.sum()) and row['validation_positive']==int(y.sum())
        for count in plan['landmark_counts']:
            np.testing.assert_array_equal(row['landmark_indices'][str(count)],indices(len(ti),count,row['seed']))
        expected=pair_count(len(ti),len(vi),plan['shot_landmarks'])
        dense=len(ti)*(len(ti)-1)//2+len(ti)*len(vi)
        assert row['dense_pair_reference']==dense
        np.testing.assert_allclose(row['per_shot_pair_fraction'],expected/dense,atol=1e-15)
        clean={key:value for key,value in row.items() if key not in ['rows','validation_target']};clean['rows']=[]
        names=[];seed_pairs=0
        for result in row['rows']:
            names.append(result['predictor'])
            recomputed=scores(y,np.array(result['predictions']),result['probability'])
            for key,value in result['metric'].items():np.testing.assert_allclose(value,recomputed[key],atol=1e-12)
            if 'pair_circuits' in result:
                assert result['pair_circuits']==expected and result['hardware_jobs_submitted']==0
                assert result['synthetic_shots']==expected*result['shots_per_pair']
                seed_pairs+=expected;synthetic+=result['synthetic_shots']
            clean['rows'].append({k:v for k,v in result.items() if k!='predictions'})
            means[result['predictor']].append(result['metric']['average_precision'])
        expected_names=['logistic','tree','rbf/dense','ZZ/dense']
        expected_names += [f'{name}/ideal/{count}' for count in plan['landmark_counts'] for name in ['rbf','ZZ']]
        expected_names += [f"ZZ/{shots}/{plan['shot_landmarks']}" for shots in plan['shots']]
        assert names==expected_names and seed_pairs==row['pair_circuits'];used+=seed_pairs;public.append(clean)
    assert [r['seed'] for r in public]==plan['seeds']
    assert used==outcome['pair_circuits'] and used<=plan['max_pair_circuits']
    assert review(outcome['seeds'],plan)==outcome['review']
    assert outcome['seconds']<=plan['max_wall_seconds']
    evidence=dict(status='audited_training_only_followup',outcome_sha256=sha(args.input),
        intent_sha256=sha(args.input.with_name('intent.json')),plan=plan,
        recipe_commit=intent['git_commit'],recipe_hashes=intent['recipe_hashes'],
        means={k:float(np.mean(v)) for k,v in means.items()},seeds=public,review=outcome['review'],
        runner_seconds=outcome['seconds'],pair_circuits=used,synthetic_shots=synthetic,
        checks=['source hash','committed recipes','sample hashes','landmark indices','saved-prediction metrics',
            'query and wall caps','frozen quality gates'],
        limitations='Post-final training-only exploration on reused chronological years. Synthetic shots; no hardware. Gates measure approximation, not superiority over classical predictors.')
    (ROOT/'docs/results/quantum-landmarks.json').write_text(json.dumps(evidence,separators=(',',':'))+'\n')
    print(json.dumps(dict(means=evidence['means'],review=evidence['review'],seconds=evidence['runner_seconds'],pair_circuits=used)))


if __name__=='__main__':main()
