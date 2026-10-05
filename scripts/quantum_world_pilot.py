"""Local, reproducible quantum-world screening. No cloud access or credentials.

Default output is a VALIDATION pilot, not final confirmation. Exact transition
and chosen-path supervision are identified separately in the result schema.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import torch
from quantum_world.data import transitions, physical_path, trajectory
from quantum_world.models import LatentModel, PauliLinearBaseline
from quantum_world.physics import (state_to_pauli,physical_metrics,midpoint_collision,
    pauli_to_density,project_density,unitary)

KINDS=['direct','chord','source_chord','generator','hamiltonian']


def digest(data):
    h=hashlib.sha256()
    for k in sorted(data):
        h.update(k.encode()); h.update(np.ascontiguousarray(data[k]).tobytes())
    return h.hexdigest()


def train(kind,seed,data,steps=800,lr=.003,batch=128,freeze_encoder=False,supervision='path'):
    torch.manual_seed(seed)
    model=LatentModel(kind)
    model.encoder.raw.requires_grad_(not freeze_encoder)
    opt=torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=lr)
    sampler=torch.Generator().manual_seed(seed+500000)
    x=torch.tensor(data['x'],dtype=torch.float32)
    y=torch.tensor(data['y'],dtype=torch.float32)
    gates=torch.tensor(data['gate'],dtype=torch.long)
    durations=torch.tensor(data['duration'],dtype=torch.float32)
    if kind in ('generator','hamiltonian') and supervision=='path':
        tau=np.random.default_rng(seed+700000).uniform(0,1,len(x))
        r,v=physical_path(data,tau)
        path_x=torch.tensor(r,dtype=torch.float32)
        path_v=torch.tensor(v,dtype=torch.float32)
    history=[];start=time.perf_counter()
    for step in range(steps):
        idx=torch.randint(len(x),(batch,),generator=sampler)
        z=model.encoder(x[idx]); target=model.encoder(y[idx]).detach()
        if kind=='direct' or (kind in ('generator','hamiltonian') and supervision=='endpoints'):
            loss=(model.advance(z,gates[idx],durations[idx])-target).square().mean()
        elif kind in ('generator','hamiltonian'):
            state=model.encoder(path_x[idx]); velocity=model.encoder(path_v[idx]).detach()
            loss=(model.velocity(state,gates[idx],durations[idx])-velocity).square().mean()
        else:
            tau=torch.rand(batch,generator=sampler)
            interpolated=(1-tau[:,None])*z+tau[:,None]*target
            velocity=target-z
            loss=(model.velocity(interpolated,gates[idx],durations[idx],tau,z)-velocity).square().mean()
        opt.zero_grad();loss.backward()
        norm=torch.nn.utils.clip_grad_norm_(model.parameters(),10)
        if not torch.isfinite(loss) or not torch.isfinite(norm):
            raise RuntimeError(f'Nonfinite training: {kind}, {seed}, {step}')
        opt.step()
        if step%100==0 or step==steps-1:
            history.append(dict(step=step,loss=float(loss.detach()),gradient_norm=float(norm)))
    return model,dict(seconds=time.perf_counter()-start,history=history,
        parameters=sum(p.numel() for p in model.parameters()),
        supervision='chosen quantum path and exact derivative' if kind in ('generator','hamiltonian') and supervision=='path' else 'endpoints only',
        encoder='fixed identity' if freeze_encoder else 'learned orthogonal Cayley basis')


def predict(model,x,gate,duration,steps=16):
    if isinstance(model,PauliLinearBaseline):return model.predict(x,gate,duration)
    dtype=next(model.parameters()).dtype
    with torch.no_grad():
        pieces=[]
        for i in range(0,len(x),256):
            pieces.append(model.predict(torch.tensor(x[i:i+256],dtype=dtype),
                torch.tensor(gate[i:i+256],dtype=torch.long),
                torch.tensor(duration[i:i+256],dtype=dtype),steps).numpy())
        return np.concatenate(pieces)


def negativity(r):
    rho=project_density(pauli_to_density(r))
    pt=rho.reshape(-1,2,2,2,2).transpose(0,1,4,3,2).reshape(-1,4,4)
    return np.maximum(-np.linalg.eigvalsh(pt),0).sum(axis=-1)


def evaluate(model,seed,n=256,length=32,solver_steps=16):
    start=time.perf_counter()
    one=transitions(n,seed)
    one_pred=predict(model,one['x'],one['gate'],one['duration'],solver_steps)
    per_gate={str(g):physical_metrics(one_pred[one['gate']==g],one['future'][one['gate']==g]) for g in range(6)}
    # Rotation-only angles outside the training interval [-1.2,1.2].
    rng=np.random.default_rng(seed+300000)
    gates=rng.integers(4,6,n)
    angles=rng.choice([-1,1],n)*rng.uniform(1.8,np.pi,n)
    future=np.array([unitary(int(g),float(t))@s for g,t,s in zip(gates,angles,one['psi'])])
    extrap=predict(model,one['x'],gates,angles,solver_steps)
    tr=trajectory(n,length,seed+1)
    pred=state_to_pauli(tr['psi'][0]);roll={}
    for k,(g,t) in enumerate(zip(tr['gate'],tr['duration']),1):
        pred=predict(model,pred,g,t,solver_steps)
        if k in (1,4,16,length):roll[str(k)]=physical_metrics(pred,tr['psi'][k])
    # Algebra tests use fresh states, not a training objective.
    x=one['x']; zeros=np.zeros(n,dtype=np.int64); ones=np.ones(n)
    hcycle=predict(model,predict(model,x,zeros,ones,solver_steps),zeros,ones,solver_steps)
    cx=np.full(n,2,dtype=np.int64)
    cxcycle=predict(model,predict(model,x,cx,ones,solver_steps),cx,ones,solver_steps)
    rz0=np.full(n,4,dtype=np.int64);rz1=rz0+1
    a=np.full(n,.71);b=np.full(n,1.31)
    composed=predict(model,predict(model,x,rz0,a,solver_steps),rz0,b,solver_steps)
    summed=predict(model,x,rz0,a+b,solver_steps)
    reversed_rz=predict(model,predict(model,x,rz0,a,solver_steps),rz0,-a,solver_steps)
    commute_ab=predict(model,predict(model,x,rz0,a,solver_steps),rz1,b,solver_steps)
    commute_ba=predict(model,predict(model,x,rz1,b,solver_steps),rz0,a,solver_steps)
    noncomm_ab=predict(model,predict(model,x,zeros,ones,solver_steps),rz0,a,solver_steps)
    noncomm_ba=predict(model,predict(model,x,rz0,a,solver_steps),zeros,ones,solver_steps)
    exact_ab=np.array([unitary(4,.71)@unitary(0)@s for s in one['psi']])
    exact_ba=np.array([unitary(0)@unitary(4,.71)@s for s in one['psi']])
    exact_gap=state_to_pauli(exact_ab)-state_to_pauli(exact_ba)
    ground=np.array([[1,0,0,0]],dtype=complex);bell=np.array([[1,0,0,1]],dtype=complex)/np.sqrt(2)
    bell_pred=predict(model,predict(model,state_to_pauli(ground),np.array([0]),np.array([1.]),solver_steps),np.array([2]),np.array([1.]),solver_steps)
    return dict(one_step=physical_metrics(one_pred,one['future']),per_gate=per_gate,
        unseen_angles=physical_metrics(extrap,future),rollout=roll,
        algebra=dict(h_involution_mse=float(np.mean((hcycle-x)**2)),
            cx_involution_mse=float(np.mean((cxcycle-x)**2)),
            rz_composition_mse=float(np.mean((composed-summed)**2)),
            rz_inverse_mse=float(np.mean((reversed_rz-x)**2)),
            independent_commutation_mse=float(np.mean((commute_ab-commute_ba)**2)),
            noncommutation_gap_error=float(np.mean(((noncomm_ab-noncomm_ba)-exact_gap)**2)),
            true_noncommutation_gap_mse=float(np.mean(exact_gap**2))),
        bell=dict(**physical_metrics(bell_pred,bell),negativity=float(negativity(bell_pred)[0]),true_negativity=.5),
        evaluation_seconds=time.perf_counter()-start)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--steps',type=int,default=800)
    p.add_argument('--seeds',type=int,nargs='+',default=[4101,4102,4103])
    p.add_argument('--models',nargs='+',choices=KINDS,default=KINDS)
    p.add_argument('--lr',type=float,default=.003)
    p.add_argument('--n-train',type=int,default=2048)
    p.add_argument('--n-eval',type=int,default=128)
    p.add_argument('--length',type=int,default=32)
    p.add_argument('--data-seed',type=int,default=90101)
    p.add_argument('--eval-seed',type=int,default=90201)
    p.add_argument('--freeze-encoder',action='store_true')
    args=p.parse_args()
    if args.output.exists():raise SystemExit('Use a fresh output directory')
    args.output.mkdir(parents=True)
    torch.set_num_threads(1)
    data=transitions(args.n_train,args.data_seed)
    config=vars(args).copy();config['output']=str(args.output)
    manifest=dict(config=config,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        stage='validation screening',training_data_sha256=digest(data),
        sources={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in
                 sorted([*Path('quantum_world').glob('*.py'),Path(__file__)])},
        versions=dict(torch=torch.__version__,numpy=np.__version__),device='cpu',threads=1)
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result=dict(midpoint_collision=midpoint_collision(),runs=[])
    baseline=PauliLinearBaseline().fit(data)
    result['classical_linear']=evaluate(baseline,args.eval_seed,args.n_eval,args.length)
    for seed in args.seeds:
        for kind in args.models:
            model,training=train(kind,seed,data,args.steps,args.lr,freeze_encoder=args.freeze_encoder)
            model=model.double()
            try:
                metrics=evaluate(model,args.eval_seed,args.n_eval,args.length)
            except FloatingPointError as exc:
                result['runs'].append(dict(seed=seed,kind=kind,training=training,status='failed',reason=str(exc)))
                (args.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
                print(json.dumps(dict(kind=kind,seed=seed,status='failed',reason=str(exc))),flush=True)
                continue
            record=dict(seed=seed,kind=kind,training=training,metrics=metrics)
            result['runs'].append(record)
            (args.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            np.savez_compressed(args.output/f'{kind}-{seed}.npz',**{k:v.detach().numpy() for k,v in model.state_dict().items()})
            print(json.dumps(dict(kind=kind,seed=seed,seconds=training['seconds'],
                fidelity=metrics['one_step']['mean_projected_fidelity'],
                extrapolation=metrics['unseen_angles']['mean_projected_fidelity'],
                rollout=metrics['rollout'][str(args.length)]['mean_projected_fidelity'],
                validity=metrics['rollout'][str(args.length)]['raw_valid_fraction'])),flush=True)
    rows=['# Two-qubit world model: validation pilot','',
          'Local exact simulation. This is screening, not final confirmation.','',
          '| Model | Seed | One-step fidelity | Unseen-angle fidelity | Long-rollout fidelity | Raw valid fraction |',
          '|---|---:|---:|---:|---:|---:|']
    for r in result['runs']:
        if r.get('status')=='failed':
            rows.append(f"| {r['kind']} | {r['seed']} | FAILED | FAILED | FAILED | FAILED |")
            continue
        m=r['metrics'];roll=m['rollout'][str(args.length)]
        rows.append(f"| {r['kind']} | {r['seed']} | {m['one_step']['mean_projected_fidelity']:.6f} | {m['unseen_angles']['mean_projected_fidelity']:.6f} | {roll['mean_projected_fidelity']:.6f} | {roll['raw_valid_fraction']:.3f} |")
    rows+=['','Fidelity uses spectral simplex projection; raw validity and correction size are recorded separately.',
           'Generator models receive chosen physical-path derivative supervision. Endpoint models receive endpoints only.',
           'The orthogonal latent encoder cannot collapse; it is a learned basis, not representation compression.',
           'An action-conditioned linear least-squares baseline with periodic RZ features is included.']
    (args.output/'REPORT.md').write_text('\n'.join(rows)+'\n')


if __name__=='__main__':main()
