"""Collect goal evidence and measured cost from saved local records; no fitting."""
import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime,timezone
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0,str(ROOT))
from wildfire_lab.goal_handoff import deadline_handoff


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def read(root,name):return json.loads((root/name).read_text())


def selection_stability(rows,feature_budget):
    """One subset per selector/seed, independent of repeated predictor rows."""
    selected={}
    for row in rows:
        key=(row['group'],row['seed']);features=frozenset(row['features'])
        if len(features)!=feature_budget:raise ValueError('Changed selection feature budget')
        if key in selected and selected[key]!=features:raise ValueError('Predictors disagree on selected subset')
        selected[key]=features
    result={}
    for group in sorted({key[0] for key in selected}):
        subsets=[features for key,features in sorted(selected.items()) if key[0]==group]
        pairs=[len(a&b)/len(a|b) for a,b in combinations(subsets,2)]
        result[group]=dict(seeds=len(subsets),pairwise_jaccard=pairs,
            mean_pairwise_jaccard=sum(pairs)/len(pairs) if pairs else None,
            feature_seed_counts=dict(sorted(Counter(f for subset in subsets for f in subset).items())))
    return result


def measured_library_queries(seeds):
    # Repaired matrices reuse the raw measurements; never charge both rows.
    rows=[r for s in seeds for r in s['kernel_rows'] if not r.get('shared_measurements',False)]
    return dict(pair_circuits=sum(r.get('pair_circuits',0) for r in rows),
                synthetic_shots=sum(r.get('synthetic_shots') or 0 for r in rows))


def collect(root):
    evidence_names=['docs/data/experiment_audit.json','docs/results/final-evaluation.json',
        'docs/results/library-followup.json','docs/results/quantum-landmarks.json',
        'docs/results/kernel-convergence.json','docs/results/kernel-ridge.json']
    original,final,library,landmarks,convergence,ridge=[read(root,n) for n in evidence_names]
    receipts=[]
    def receipt(name,path,expected_hash,seconds,seconds_field='seconds',expected_status='complete'):
        if digest(path)!=expected_hash:raise ValueError('Changed saved outcome: '+name)
        saved=json.loads(path.read_text())
        if saved['status']!=expected_status or not math.isclose(saved[seconds_field],seconds,abs_tol=1e-9):
            raise ValueError('Changed status/time: '+name)
        receipts.append(dict(name=name,status=saved['status'],seconds=seconds,outcome_sha256=expected_hash))
    for row in original['results']:
        paths=list((root/'.cache/wildfire/experiments').glob('*/'+row['attempt']+'-outcome.json'))
        if len(paths)!=1:raise ValueError('Missing or ambiguous original attempt')
        receipt(row['attempt'],paths[0],row['outcome_sha256'],row['seconds'])
    receipt('final-test',root/'.cache/wildfire/final-test/outcome.json',final['outcome_sha256'],
            final['timings']['total_seconds'],'total_seconds')
    for row in library['attempts']:
        receipt(row['name'],root/'.cache/wildfire'/row['name']/'outcome.json',row['outcome_sha256'],
                row['seconds'],expected_status=row['status'])
    for name,public,seconds in [('quantum-landmarks',landmarks,landmarks['runner_seconds']),
        ('kernel-convergence',convergence,convergence['seconds']),('kernel-ridge',ridge,ridge['runner_seconds'])]:
        receipt(name,root/'.cache/wildfire'/name/'outcome.json',public['outcome_sha256'],seconds)
    seasonal_name='docs/results/seasonal-baseline.json';seasonal=None
    if (root/seasonal_name).exists():
        seasonal=read(root,seasonal_name);evidence_names.append(seasonal_name)
        receipt('seasonal-baseline',root/'.cache/wildfire/seasonal-baseline/outcome.json',
                seasonal['outcome_sha256'],seasonal['runner_seconds'])
    shot_name='docs/results/shot-feasibility.json';shot=None
    if (root/shot_name).exists():
        shot=read(root,shot_name);evidence_names.append(shot_name)
        receipt('shot-feasibility',root/'.cache/wildfire/shot-feasibility/outcome.json',
                shot['outcome_sha256'],shot['runner_seconds'])
    constrained_name='docs/results/constrained-selection.json';constrained=None
    if (root/constrained_name).exists():
        constrained=read(root,constrained_name);evidence_names.append(constrained_name)
        receipt('constrained-selection',root/'.cache/wildfire/constrained-selection/outcome.json',
                constrained['outcome_sha256'],constrained['runner_seconds'])
    geometry_name='docs/results/local-geometry.json';geometry=None
    if (root/geometry_name).exists():
        geometry=read(root,geometry_name);evidence_names.append(geometry_name)
        receipt('local-geometry',root/'.cache/wildfire/local-geometry/outcome.json',
                geometry['outcome_sha256'],geometry['runner_seconds'])
    tangent_name='docs/results/tangent-prediction.json';tangent=None
    if (root/tangent_name).exists():
        tangent=read(root,tangent_name);evidence_names.append(tangent_name)
        receipt('tangent-prediction',root/'.cache/wildfire/tangent-prediction/outcome.json',
                tangent['outcome_sha256'],tangent['runner_seconds'])
    shot_ridge_name='docs/results/landmark-shot-ridge.json';shot_ridge=None
    if (root/shot_ridge_name).exists():
        shot_ridge=read(root,shot_ridge_name);evidence_names.append(shot_ridge_name)
        receipt('landmark-shot-ridge',root/'.cache/wildfire/landmark-shot-ridge/outcome.json',
                shot_ridge['outcome_sha256'],shot_ridge['runner_seconds'])
    label_name='docs/data/label_quality.json';label=None
    policy_name='docs/results/policy-evolution.json';policy=None
    if (root/policy_name).exists():
        policy=read(root,policy_name);evidence_names.append(policy_name)
        for stage in policy['stages']:
            receipt('policy-evolution-'+stage['stage'],root/'.cache/wildfire'/('policy-evolution-'+stage['stage'])/'outcome.json',
                    stage['outcome_sha256'],stage['runner_seconds'],expected_status=stage['status'])
    proxy_name='docs/results/proxy-alignment.json';proxy=None
    if (root/proxy_name).exists():
        proxy=read(root,proxy_name);evidence_names.append(proxy_name)
        receipt('proxy-alignment',root/'.cache/wildfire/proxy-alignment/outcome.json',
                proxy['outcome_sha256'],proxy['runner_seconds'])
    if (root/label_name).exists():
        label=read(root,label_name);evidence_names.append(label_name)
        assert label['plan']['years']==[1988,2018] and not label['final_test_access']
        assert label['model_fits']==0 and label['quantum_calls']==0
    probability_name='docs/data/probability_report.json';probability=None
    if (root/probability_name).exists():
        probability=read(root,probability_name);evidence_names.append(probability_name)
        assert probability['plan']['final_outcome_sha256']==final['outcome_sha256']
        assert probability['plan']['final_evidence_sha256']==digest(root/'docs/results/final-evaluation.json')
        assert all(probability[name]==0 for name in ['model_fits','calibrator_fits','quantum_calls','hardware_jobs_submitted'])
        assert not probability['final_predictions_changed']
    original_seconds=sum(r['seconds'] for r in original['results'])
    if not math.isclose(original_seconds,original['measured_attempt_wall_seconds'],abs_tol=1e-9):
        raise ValueError('Changed original cost summary')
    with (root/'docs/data/coverage.csv').open() as incoming:coverage=list(csv.DictReader(incoming))
    expected_years=list(range(1988,2025))
    if [int(r['year']) for r in coverage]!=expected_years:raise ValueError('Changed requested years')
    if any(int(r['weather_months_downloaded'])!=12 or int(r['nfdb_incident_rows'])<=0 for r in coverage):
        raise ValueError('Missing reported source-year coverage')
    library_cost=measured_library_queries(library['seeds'])
    code_files=subprocess.check_output(['git','ls-files','*.py'],cwd=root,text=True).splitlines()
    lines={name:len((root/name).read_text().splitlines()) for name in code_files}
    handoff=deadline_handoff(root)
    return dict(status='final_evidence_audit' if handoff['published'] else 'interim_evidence_audit',deadline_handoff=handoff,created_utc=datetime.now(timezone.utc).isoformat(),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        goal_sha256=digest(root/'GOAL.md'),audit_recipe_sha256=digest(root/'scripts/audit_goal.py'),
        evidence_sha256={n:digest(root/n) for n in evidence_names},
        recorded_runner_intervals=len(receipts),runner_status_counts=dict(Counter(r['status'] for r in receipts)),
        summed_recorded_runner_seconds=sum(r['seconds'] for r in receipts),runner_receipts=receipts,
        completed_library_queries=library_cost,
        completed_landmark_queries=dict(pair_circuits=landmarks['pair_circuits'],synthetic_shots=landmarks['synthetic_shots']),
        ridge_audit_reconstruction_seconds=ridge['audit_reconstruction_seconds'],
        analytic_shot_diagnostic=dict(state_preparations=shot['simulated_state_preparations'],pair_circuits=shot['pair_circuits_executed'],
            experimental_shots=shot['shots_executed'],audit_seconds=shot['audit_seconds']) if shot else None,
        constrained_selector_diagnostic={name:constrained[name] for name in ['quantum_state_evaluations','predictor_fits',
            'l1_selector_fits','synthetic_quantum_draws','audit_reconstruction_states','audit_seconds']} if constrained else None,
        local_geometry_diagnostic={name:geometry[name] for name in ['simulated_state_preparations','audit_simulated_state_preparations','audit_seconds']} if geometry else None,
        tangent_prediction_control={name:tangent[name] for name in ['predictor_fits','primal_reference_solves',
            'audit_predictor_fits','new_state_preparations','audit_seconds']} if tangent else None,
        landmark_shot_ridge_model={name:shot_ridge[name] for name in ['predictor_fits','primal_reference_solves',
            'binomial_pair_estimates','modeled_shot_exposure','pair_circuits_executed','individually_executed_shots','audit_seconds']} if shot_ridge else None,
        label_quality_status=label['status'] if label else 'not_collected',
        policy_evolution_diagnostic=dict(stages=len(policy['stages']),
            predictor_fits=sum(s['predictor_fits'] for s in policy['stages']),
            simulated_state_preparations=sum(s['simulated_state_preparations'] for s in policy['stages']),
            hardware_jobs_submitted=policy['hardware_jobs_submitted'],final_test_access=policy['final_test_access']) if policy else None,
        proxy_alignment_diagnostic={name:proxy[name] for name in ['predictor_fits',
            'audit_predictor_fits','new_selector_fits','quantum_calls','audit_seconds']} if proxy else None,
        probability_reporting_audit={name:probability[name] for name in ['status','audit_seconds',
            'model_fits','calibrator_fits','quantum_calls','final_predictions_changed']} if probability else None,
        final_selector_stability=selection_stability(final['rows']['capped_crossed_matrix'],final['plan']['feature_budget']),
        coverage=dict(train_years=31,test_years=6,requested_weather_months=444,nfdb_incident_years=37,
            operational_update_years=sum(bool(r['fire_update_rows']) for r in coverage),
            requested_matching_year_maps=sum(r['woodland_status']=='downloaded' for r in coverage),
            matching_year_map_gaps=[int(r['year']) for r in coverage if r['woodland_status']=='outside_product_years']),
        python_files_over_300_lines={n:v for n,v in lines.items() if v>300},
        pure_seasonal_control_status='audited_reference_matches' if seasonal and seasonal['combined_reference_matches'] else 'missing_or_reference_mismatch',
        open_items=([] if seasonal and seasonal['combined_reference_matches'] else
            ['Pure seasonal baseline missing or original combined-control reproduction unresolved.'])+
            ([] if handoff['published'] else [handoff['open_item']]),
        limitations=['Summed runner intervals are not elapsed project time; some original runs overlapped.',
            'Acquisition, preparation, startup, repeated collection/QA and unrecorded failed circuit work are excluded.',
            'Query counts cover completed library/landmark runs only; PSD repair shares measurements.',
            'Stability summarizes three dependent seeds, not confidence intervals or independent time periods.',
            'Receipt hashes link earlier audits; this collection does not refit, re-audit source completeness or validate as-of covariates.',
            'Original proposal-model identifier is unavailable; policy-agent is configured gpt-6.1-sol. The bounded code-revision study is not full Dream-RSI reproduction.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/data/goal_audit.json')
    args=parser.parse_args();result=collect(ROOT)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','recorded_runner_intervals','runner_status_counts',
        'summed_recorded_runner_seconds','coverage','python_files_over_300_lines','open_items')}))
