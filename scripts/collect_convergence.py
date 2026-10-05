"""Audit saved convergence predictions and compare fixed tolerances; no fitting."""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.stats import spearmanr
from wildfire_lab.evaluation import scores,sample_indices,split
ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'.cache/wildfire/kernel-convergence/outcome.json')
    args=parser.parse_args();record=json.loads(args.input.read_text());assert record['status']=='complete'
    intent=json.loads(args.input.with_name('intent.json').read_text());assert intent==record['intent']
    plan,parent=intent['plan'],intent['parent_plan'];assert not plan['hardware'] and not plan['final_test_access']
    assert sha(ROOT/plan['parent_evidence'])==intent['parent_evidence_sha256']
    original_path=ROOT/'.cache/wildfire/quantum-landmarks/outcome.json'
    assert sha(original_path)==intent['parent_outcome_sha256'];original=json.loads(original_path.read_text())
    source=ROOT/parent['dataset']/'features.csv';assert sha(source)==parent['dataset_sha256']
    for name,digest in intent['recipe_hashes'].items():
        assert hashlib.sha256(subprocess.check_output(['git','show',f"{intent['git_commit']}:{name}"],cwd=ROOT)).hexdigest()==digest
    import pandas as pd
    train,valid=split(pd.read_csv(source),parent['fold'],train_window=(1988,2018))
    public=[];comparisons=[];means=defaultdict(list);rules=plan['decision_rules']
    assert [r['seed'] for r in record['seeds']]==plan['seeds']
    for row,prior in zip(record['seeds'],original['seeds']):
        assert row['seed']==prior['seed']
        ti=sample_indices(len(train),parent['train_cap'],row['seed']);vi=sample_indices(len(valid),parent['validation_cap'],row['seed'])
        y=valid.iloc[vi].target.to_numpy();np.testing.assert_array_equal(y,row['validation_target'])
        assert row['train_rows']==len(ti) and row['train_positive']==int(train.iloc[ti].target.sum())
        assert row['validation_rows']==len(vi) and row['validation_positive']==int(y.sum())
        assert row['new_pair_circuits']==0 and row['hardware_jobs_submitted']==0
        lookup={};clean=dict(row);clean.pop('validation_target');clean['rows']=[]
        parent_rows={r['predictor']:r for r in prior['rows']}
        for result in row['rows']:
            key=(result['predictor'],result['tolerance'],result['representation']);assert key not in lookup
            lookup[key]=result;p=np.asarray(result['predictions']);recomputed=scores(y,p,False)
            for k,v in result['metric'].items():np.testing.assert_allclose(v,recomputed[k],atol=1e-12)
            np.testing.assert_allclose(np.std(p),result['validation_decision_std'],atol=1e-15)
            np.testing.assert_allclose(np.ptp(p),result['validation_decision_range'],atol=1e-15)
            assert int((p>0).sum())==result['validation_positive_predictions']
            if 'parent_prediction_max_abs_difference' in result:
                difference=float(np.max(np.abs(p-parent_rows[result['predictor']]['predictions'])))
                np.testing.assert_allclose(difference,result['parent_prediction_max_abs_difference'],atol=1e-15)
                assert difference<=rules['default_reproduction_atol']
            clean['rows'].append({k:v for k,v in result.items() if k!='predictions'})
            means[f"{key[0]}/{key[1]}/{key[2]}"].append(result['metric']['average_precision'])
        assert len(lookup)==18
        for name in plan['kernels']:
            representation='linear' if '/ideal/' in name else 'precomputed'
            default,middle,tight=[lookup[name,t,representation] for t in plan['tolerances']]
            ap=lambda r:r['metric']['average_precision']
            d=float(ap(tight)-ap(default));stability=float(abs(ap(tight)-ap(middle)))
            check=dict(seed=row['seed'],predictor=name,default_to_tight_ap_delta=d,
                rank_sensitive=abs(d)>rules['rank_sensitivity_ap_delta'],middle_to_tight_ap_abs_difference=stability,
                tight_pair_ap_stable=stability<=rules['tight_pair_ap_stability'],
                prediction_spearman=float(spearmanr(default['predictions'],tight['predictions']).statistic),
                tight_duality_gap=tight['duality_gap'],tight_fit_status=tight['fit_status'],
                tight_verified=tight['fit_status']==0 and abs(tight['duality_gap'])<=rules['tight_duality_gap_max'])
            if name==plan['representation_control']:
                precomputed=lookup[name,plan['tolerances'][-1],'precomputed']
                difference=float(np.max(np.abs(np.asarray(tight['predictions'])-precomputed['predictions'])))
                check.update(tight_representation_prediction_max_abs_difference=difference,
                    tight_representations_agree=difference<=rules['tight_representation_prediction_atol'])
            comparisons.append(check)
        public.append(clean)
    assert record['seconds']<=plan['max_wall_seconds']
    evidence=dict(status='audited_training_only_numerical_check',plan=plan,parent_plan=parent,
        recipe_commit=intent['git_commit'],recipe_hashes=intent['recipe_hashes'],
        outcome_sha256=sha(args.input),intent_sha256=sha(args.input.with_name('intent.json')),
        parent_outcome_sha256=intent['parent_outcome_sha256'],seeds=public,comparisons=comparisons,
        means={k:float(np.mean(v)) for k,v in means.items()},seconds=record['seconds'],
        checks=['source and committed recipes','parent predictions reproduced','saved metrics and score spreads',
            'fixed comparison thresholds','no new pair circuits or hardware'],
        limitations='Training-only post-final numerical audit; solver objectives/KKT diagnostics are recorded by the committed runner, not independently recomputed by this collector. Tolerance is not chosen by best AP. No original final or landmark outcome was rewritten.')
    (ROOT/'docs/results/kernel-convergence.json').write_text(json.dumps(evidence,separators=(',',':'))+'\n')
    print(json.dumps(dict(seconds=evidence['seconds'],means=evidence['means'],comparisons=comparisons)))


if __name__=='__main__':main()
