"""Audit saved local derivatives and tangent matrices; no quantum-state calls."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.geometry_inputs import load,sha
from wildfire_lab.local_geometry import derivative_points,quantum_metric,describe


def collect(cache,output):
    start=time.perf_counter();record=json.loads((cache/'outcome.json').read_text());intent=json.loads((cache/'intent.json').read_text())
    assert record['status']=='complete' and record['intent']==intent
    plan=intent['plan'];commit=intent['git_commit']
    for name,expected in intent['recipe_sha256'].items():
        raw=subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT);assert sha_bytes(raw)==expected,name
        if name.startswith('wildfire_lab/'):assert sha(ROOT/name)==expected,name
        if name=='experiments/local_geometry.json':assert json.loads(raw)==plan
    parent,conditions=load(ROOT,plan);n=len(parent['parent_plan']['features'])
    assert sha(cache/'derivatives.npz')==record['derivative_archive_sha256']
    with np.load(cache/'derivatives.npz',allow_pickle=False) as arrays:points,vectors=arrays['points'],arrays['states']
    expected=np.stack([derivative_points(np.full(n,np.pi/2),step) for step in plan['finite_difference_steps']])
    np.testing.assert_array_equal(points,expected);assert vectors.shape==(len(points),2*n+1,2**n)
    assert record['simulated_state_preparations']==len(points.reshape(-1,n))<=plan['max_simulated_state_preparations']
    metrics=[quantum_metric(states,step) for states,step in zip(vectors,plan['finite_difference_steps'])]
    metric=metrics[plan['finite_difference_steps'].index(plan['reference_step'])]
    np.testing.assert_allclose(record['metric'],metric,atol=1e-10);np.testing.assert_allclose(record['metric_eigenvalues'],np.linalg.eigvalsh(metric),atol=1e-10)
    differences=[float(np.linalg.norm(g-metric)/np.linalg.norm(metric)) for g in metrics]
    np.testing.assert_allclose(record['derivative_relative_differences'],differences,atol=1e-10)
    assert differences[-1]<=plan['reference_to_finest_relative_tolerance'] and record['seconds']<=plan['max_wall_seconds']
    assert len(conditions)==len(record['conditions']);rows=[]
    for (parent_row,x,v,gram,cross),row in zip(conditions,record['conditions']):
        assert (row['seed'],row['angle_scale'],row['matrix_sha256'])==(parent_row['seed'],parent_row['angle_scale'],parent_row['matrix_sha256'])
        actual=describe(gram,cross,x,v,metric,row['angle_scale'])
        for key,value in actual.items():np.testing.assert_allclose(row[key],value,atol=1e-9,rtol=1e-9)
        assert len(row['inherited_cross_shot_rms'])==len(parent_row['shot_conditions'])
        for inherited,previous in zip(row['inherited_cross_shot_rms'],parent_row['shot_conditions']):
            assert inherited==dict(shots=previous['shots'],rms=previous['expected_relative_frobenius_error']['cross'],
                scale_times_rms=row['angle_scale']*previous['expected_relative_frobenius_error']['cross'])
        rows.append(row)
    result=dict(status='audited_local_kernel_geometry',opening_commit=commit,intent_sha256=sha(cache/'intent.json'),
        outcome_sha256=sha(cache/'outcome.json'),parent_outcome_sha256=plan['parent_outcome_sha256'],dataset_sha256=parent['parent_plan']['dataset_sha256'],
        plan=plan,metric=record['metric'],metric_eigenvalues=record['metric_eigenvalues'],derivative_relative_differences=differences,
        runner_seconds=record['seconds'],audit_seconds=time.perf_counter()-start,simulated_state_preparations=record['simulated_state_preparations'],
        audit_simulated_state_preparations=0,model_fits=0,labels_used=False,final_test_access=False,pair_circuits_executed=0,
        shots_executed=0,hardware_jobs_submitted=0,conditions=rows,limitations=plan['interpretation'],
        audit_recipe_sha256={name:sha(ROOT/name) for name in ['scripts/collect_local_geometry.py','wildfire_lab/geometry_inputs.py','wildfire_lab/local_geometry.py']})
    output.parent.mkdir(parents=True,exist_ok=True);header={k:v for k,v in result.items() if k!='conditions'}
    output.write_text(json.dumps(header,separators=(',',':'))[:-1]+',"conditions":[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n]}\n')
    print(json.dumps({k:result[k] for k in ['status','runner_seconds','audit_seconds','simulated_state_preparations','audit_simulated_state_preparations']}));return result


def sha_bytes(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'.cache/wildfire/local-geometry')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/results/local-geometry.json')
    args=parser.parse_args();collect(args.cache.resolve(),args.output)
