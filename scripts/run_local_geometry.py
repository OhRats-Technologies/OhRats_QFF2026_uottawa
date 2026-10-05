"""Frozen labels-free tangent-kernel diagnostic over saved exact matrices."""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wildfire_lab.kernel import angle_states
from wildfire_lab.geometry_inputs import load,sha
from wildfire_lab.local_geometry import derivative_points,quantum_metric,describe

RECIPES=['scripts/run_local_geometry.py','scripts/collect_local_geometry.py','wildfire_lab/local_geometry.py',
    'wildfire_lab/geometry_inputs.py','wildfire_lab/kernel.py','wildfire_lab/encoding_screen.py',
    'wildfire_lab/shot_noise.py','wildfire_lab/evaluation.py','experiments/local_geometry.json','pyproject.toml','uv.lock']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'.cache/wildfire/local-geometry')
    args=parser.parse_args();plan=json.loads((ROOT/'experiments/local_geometry.json').read_text())
    assert not any(plan[k] for k in ['labels_used','model_fits','pair_circuits','shots','hardware','final_test_access'])
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();hashes={}
    for name in RECIPES:
        raw=(ROOT/name).read_bytes();assert raw==subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT),name
        hashes[name]=sha(ROOT/name)
    intent=dict(plan=plan,git_commit=commit,recipe_sha256=hashes,started_utc=datetime.now(timezone.utc).isoformat())
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'intent.json').open('x') as f:json.dump(intent,f,indent=2)
    outcome=dict(status='running',intent=intent,conditions=[],simulated_state_preparations=0);start=time.perf_counter()
    def save():
        tmp=args.output/'outcome.tmp';tmp.write_text(json.dumps(outcome,indent=2)+'\n');os.replace(tmp,args.output/'outcome.json')
    def timeout(*_):raise TimeoutError('Local-geometry wall budget reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['max_wall_seconds'])
    try:
        parent,conditions=load(ROOT,plan);n=len(parent['parent_plan']['features'])
        points=np.stack([derivative_points(np.full(n,np.pi/2),step) for step in plan['finite_difference_steps']])
        assert len(points.reshape(-1,n))<=plan['max_simulated_state_preparations']
        vectors=angle_states(points.reshape(-1,n),parent['plan']['reps']).reshape(len(points),2*n+1,-1)
        outcome['simulated_state_preparations']=len(points.reshape(-1,n))
        with (args.output/'derivatives.npz').open('xb') as f:np.savez_compressed(f,points=points,states=vectors)
        metrics=[quantum_metric(states,step) for states,step in zip(vectors,plan['finite_difference_steps'])]
        ref=plan['finite_difference_steps'].index(plan['reference_step']);metric=metrics[ref]
        differences=[float(np.linalg.norm(g-metric)/np.linalg.norm(metric)) for g in metrics]
        assert differences[-1]<=plan['reference_to_finest_relative_tolerance']
        outcome.update(metric=metric.tolist(),metric_eigenvalues=np.linalg.eigvalsh(metric).tolist(),
            derivative_relative_differences=differences,derivative_archive_sha256=sha(args.output/'derivatives.npz'))
        for row,x,v,gram,cross in conditions:
            outcome['conditions'].append(dict(seed=row['seed'],angle_scale=row['angle_scale'],matrix_sha256=row['matrix_sha256'],
                **describe(gram,cross,x,v,metric,row['angle_scale']),
                inherited_cross_shot_rms=[dict(shots=s['shots'],rms=s['expected_relative_frobenius_error']['cross'],
                    scale_times_rms=row['angle_scale']*s['expected_relative_frobenius_error']['cross']) for s in row['shot_conditions']]))
            save()
        outcome['status']='complete'
    except Exception as error:
        outcome.update(status='failed_preserved',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);outcome['seconds']=time.perf_counter()-start;save()
    print(json.dumps({k:outcome[k] for k in ['status','seconds','simulated_state_preparations','derivative_relative_differences']}))


if __name__=='__main__':main()
