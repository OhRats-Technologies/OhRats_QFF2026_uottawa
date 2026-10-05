"""Matched endpoint-only study with explicit validation/confirmation separation.

Training inputs are exact known prepared states. Optional independent finite-shot
Pauli estimates corrupt ONLY future-state targets; this is calibration, not a
claim to reconstruct partially observed world states. No hardware is contacted.
"""
from __future__ import annotations
import argparse,hashlib,json,time,datetime
from pathlib import Path
import numpy as np
import torch
from quantum_world.data import transitions
from quantum_world.models import PauliLinearBaseline
from scripts.quantum_world_pilot import train,evaluate,digest

METHODS=('direct','generator','hamiltonian','linear')


def shot_targets(data,shots,seed):
    out={k:v.copy() for k,v in data.items()}
    if shots:
        rng=np.random.default_rng(seed)
        out['y']=2*rng.binomial(shots,np.clip((data['y']+1)/2,0,1))/shots-1
    return out


def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--sizes',nargs='+',type=int,default=[48,192,768])
    p.add_argument('--shots',nargs='+',type=int,default=[0,128])
    p.add_argument('--lrs',nargs='+',type=float,default=[.001,.003,.01])
    p.add_argument('--ridges',nargs='+',type=float,default=[1e-6,.01,1.])
    p.add_argument('--steps',type=int,default=1200)
    p.add_argument('--validation-seeds',nargs='+',type=int,default=[5101,5102])
    p.add_argument('--final-seeds',nargs='+',type=int,default=[6101,6102,6103,6104,6105])
    p.add_argument('--final-n',type=int,default=128)
    p.add_argument('--final-length',type=int,default=64)
    args=p.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    if set(args.validation_seeds)&set(args.final_seeds):raise SystemExit('Seed overlap')
    if len(args.lrs)!=len(args.ridges):raise SystemExit('Equal-count tuning grids required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    config=vars(args).copy();config['output']=str(args.output)
    dump(args.output/'manifest.json',dict(config=config,stage='endpoint-only validation then independent confirmation',
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        selection_metric='mean unseen-angle projected fidelity on validation; identical equal-count LR search',
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
          sorted([*Path('quantum_world').glob('*.py'),Path(__file__),Path('scripts/quantum_world_pilot.py')])},
        target_noise='independent binomial per Pauli; known exact input states',
        shots_total_per_target='15 * shots; different measurements for each observable',
        final_inputs='independent clean prepared states; noisy-input inference is not evaluated'))
    validation=[];selected={}
    for n in args.sizes:
        for shots in args.shots:
            for kind in METHODS:
                scores={}
                grid=args.ridges if kind=='linear' else args.lrs
                for lr in grid:
                    values=[]
                    for seed in args.validation_seeds:
                        data=shot_targets(transitions(n,seed+900000),shots,seed+1100000)
                        if kind=='linear':
                            start=time.perf_counter();model=PauliLinearBaseline().fit(data,ridge=lr)
                            training=dict(seconds=time.perf_counter()-start,supervision='endpoints only',ridge=lr)
                        else:
                            model,training=train(kind,seed,data,args.steps,lr,supervision='endpoints')
                            model=model.double()
                        metrics=evaluate(model,920001,64,8)
                        values.append(metrics['unseen_angles']['mean_projected_fidelity'])
                        validation.append(dict(n=n,shots=shots,kind=kind,seed=seed,lr=lr,training=training,
                            data_sha256=digest(data),metrics=metrics))
                        dump(args.output/'validation.json',validation)
                    scores[str(lr)]=float(np.mean(values))
                lr=max(grid,key=lambda lr:scores[str(lr)])
                key=f'{n}:{shots}:{kind}'
                selected[key]=dict(lr=lr,scores=scores)
                print(json.dumps(dict(stage='selection',key=key,lr=lr,scores=scores)),flush=True)
    dump(args.output/'selection.json',selected)
    selection_sha=hashlib.sha256((args.output/'selection.json').read_bytes()).hexdigest()
    # No final observations generated/evaluated before selection is frozen.
    final=[]
    for n in args.sizes:
        for shots in args.shots:
            for seed in args.final_seeds:
                data=shot_targets(transitions(n,seed+1000000),shots,seed+1300000)
                for kind in METHODS:
                    lr=selected[f'{n}:{shots}:{kind}']['lr']
                    if kind=='linear':
                        start=time.perf_counter();model=PauliLinearBaseline().fit(data,ridge=lr)
                        training=dict(seconds=time.perf_counter()-start,supervision='endpoints only',ridge=lr)
                    else:
                        model,training=train(kind,seed,data,args.steps,lr,supervision='endpoints')
                        model=model.double()
                    metrics=evaluate(model,seed+1500000,args.final_n,args.final_length)
                    final.append(dict(n=n,shots=shots,kind=kind,seed=seed,lr=lr,training=training,
                        data_sha256=digest(data),metrics=metrics))
                    if kind!='linear' and n==max(args.sizes) and seed==args.final_seeds[0]:
                        np.savez_compressed(args.output/f'{kind}-shots{shots}-{seed}.npz',**{k:v.detach().numpy() for k,v in model.state_dict().items()})
                    print(json.dumps(dict(stage='final',n=n,shots=shots,seed=seed,kind=kind,
                        extrapolation=metrics['unseen_angles']['mean_projected_fidelity'],
                        rollout=metrics['rollout'][str(args.final_length)]['mean_projected_fidelity'])),flush=True)
                dump(args.output/'final.json',final)
    assert hashlib.sha256((args.output/'selection.json').read_bytes()).hexdigest()==selection_sha
    dump(args.output/'completion.json',dict(selection_sha256=selection_sha,
        validation_runs=len(validation),final_runs=len(final),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    rows=['# Endpoint-only quantum-world study','',
          'Model learning rates selected using independent validation seeds before final states were generated.','',
          '| Transitions | Shots / observable | Model | Unseen-angle fidelity | Long-rollout fidelity | Raw validity |',
          '|---:|---:|---|---:|---:|---:|']
    for n in args.sizes:
        for shots in args.shots:
            for kind in METHODS:
                runs=[r for r in final if r['n']==n and r['shots']==shots and r['kind']==kind]
                fidelity=np.mean([r['metrics']['unseen_angles']['mean_projected_fidelity'] for r in runs])
                roll=np.mean([r['metrics']['rollout'][str(args.final_length)]['mean_projected_fidelity'] for r in runs])
                valid=np.mean([r['metrics']['rollout'][str(args.final_length)]['raw_valid_fraction'] for r in runs])
                rows.append(f'| {n} | {shots} | {kind} | {fidelity:.6f} | {roll:.6f} | {valid:.3f} |')
    rows+=['','All methods receive the same endpoint data. Inputs are exact known preparations; only targets receive simulated shot noise.',
       'All four families receive equal-count hyperparameter searches; linear ridge and neural learning rates are selected on the same validation criterion.',
       'Hamiltonian and skew-generator composition are structural constraints, not independently discovered laws.',
       'Fidelity is reported after spectral projection, alongside raw validity. No quantum hardware or quantum computational advantage.']
    (args.output/'REPORT.md').write_text('\n'.join(rows)+'\n')


if __name__=='__main__':main()
