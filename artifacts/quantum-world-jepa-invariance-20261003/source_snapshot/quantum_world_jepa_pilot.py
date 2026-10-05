"""Exploratory nonlinear representation test; physical readout never trains E."""
from __future__ import annotations
import argparse,json,hashlib,datetime
from pathlib import Path
import numpy as np
import torch
from quantum_world.jepa import train_world,fit_readout,observations
from quantum_world.data import transitions,trajectory
from quantum_world.physics import haar_states,state_to_pauli,physical_metrics,unitary
from scripts.quantum_world_pilot import digest


def evaluate(model,readout,seed,n=128,length=32):
    model.eval();readout.eval()
    d=transitions(n,seed);rng=torch.Generator().manual_seed(seed+200000)
    x=torch.tensor(d['x'],dtype=torch.float32)
    clean=torch.cat([x,torch.zeros(n,8)],dim=-1)
    with torch.no_grad():
        z=model.encoder(clean)
        noisy_z=model.encoder(observations(x,rng))
        decoded=readout(z).numpy()
        noisy_decoded=readout(noisy_z).numpy()
        eig=torch.linalg.eigvalsh(torch.cov(z.T)).numpy()
        positive=np.maximum(eig,0);weights=positive/positive.sum() if positive.sum()>0 else positive
        rank=float(np.exp(-np.sum(weights[weights>0]*np.log(weights[weights>0])))) if positive.sum()>0 else 0.
        pred=readout(model.advance(z,torch.tensor(d['gate']),torch.tensor(d['duration'],dtype=torch.float32))).numpy()
        noisy_pred=readout(model.advance(noisy_z,torch.tensor(d['gate']),torch.tensor(d['duration'],dtype=torch.float32))).numpy()
        stochastic=None
        if model.kind=='gaussian':
            samples=[]
            for _ in range(4):
                noise=torch.randn(z.shape,generator=rng)
                samples.append(readout(model.advance(z,torch.tensor(d['gate']),torch.tensor(d['duration'],dtype=torch.float32),noise=noise)).numpy())
            stochastic=dict(mean_sample_fidelity=float(np.mean([physical_metrics(s,d['future'])['mean_projected_fidelity'] for s in samples])),
                mean_prediction=physical_metrics(np.mean(samples,axis=0),d['future']))
        angles=np.random.default_rng(seed+300000).uniform(1.8,np.pi,n)
        gates=np.random.default_rng(seed+300001).integers(4,6,n)
        future=np.array([unitary(int(g),float(t))@s for g,t,s in zip(gates,angles,d['psi'])])
        extrap=readout(model.advance(z,torch.tensor(gates),torch.tensor(angles,dtype=torch.float32))).numpy()
        tr=trajectory(n,length,seed+1)
        initial=torch.tensor(state_to_pauli(tr['psi'][0]),dtype=torch.float32)
        rollout_z=model.encoder(torch.cat([initial,torch.zeros(n,8)],dim=-1))
        rolls={};ceilings={}
        for k,(g,t) in enumerate(zip(tr['gate'],tr['duration']),1):
            rollout_z=model.advance(rollout_z,torch.tensor(g),torch.tensor(t,dtype=torch.float32))
            if k in (1,4,16,length):
                try:
                    rolls[str(k)]=physical_metrics(readout(rollout_z).numpy(),tr['psi'][k])
                except FloatingPointError:
                    rolls[str(k)]=dict(status='nonfinite rollout',mean_projected_fidelity=None,raw_valid_fraction=0.)
                truth_r=torch.tensor(state_to_pauli(tr['psi'][k]),dtype=torch.float32)
                oracle=model.encoder(torch.cat([truth_r,torch.zeros(n,8)],dim=-1))
                ceilings[str(k)]=physical_metrics(readout(oracle).numpy(),tr['psi'][k])
    return dict(readout_ceiling=physical_metrics(decoded,d['psi']),noisy_readout=physical_metrics(noisy_decoded,d['psi']),
        one_step=physical_metrics(pred,d['future']),noisy_one_step=physical_metrics(noisy_pred,d['future']),
        stochastic_one_step=stochastic,
        unseen_angles=physical_metrics(extrap,future),rollout=rolls,rollout_readout_ceiling=ceilings,
        representation=dict(effective_rank=rank,min_covariance_eigenvalue=float(eig.min()),
                            nuisance_latent_mse=float((z-noisy_z).square().mean()),variance=float(z.var(dim=0).mean())))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    p.add_argument('--steps',type=int,default=2000);p.add_argument('--anchor',type=float,default=1.)
    p.add_argument('--seeds',type=int,nargs='+',default=[7101,7102,7103]);p.add_argument('--n-eval',type=int,default=128)
    p.add_argument('--models',nargs='+',default=['direct','source_chord','gaussian','latent_generator'])
    p.add_argument('--target-grad',choices=['stop','joint','stop_velocity'],default='stop')
    p.add_argument('--invariance',type=float,default=0.)
    args=p.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in (Path(__file__),Path('quantum_world/jepa.py')):
        (snapshot/source.name).write_bytes(source.read_bytes())
    data=transitions(4096,97101)
    config=vars(args).copy();config['output']=str(args.output)
    (args.output/'manifest.json').write_text(json.dumps(dict(config=config,stage='exploratory validation',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),data_sha256=digest(data),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('quantum_world/jepa.py')]},
        physical_readout='independently trained after freezing E, not a reconstruction training objective',
        gaussian_inference='zero-source rollouts plus four independent Gaussian source draws for one-step evaluation'),indent=2)+'\n')
    results=[]
    probe_r=torch.tensor(state_to_pauli(haar_states(4096,97201)),dtype=torch.float32)
    for seed in args.seeds:
        for kind in args.models:
            model,training=train_world(kind,seed,data,args.steps,anchor_weight=args.anchor,
                target_grad=args.target_grad,invariance_weight=args.invariance)
            before={k:v.clone() for k,v in model.state_dict().items()}
            readout=fit_readout(model,probe_r,seed+1000000)
            assert all(torch.equal(v,before[k]) for k,v in model.state_dict().items())
            metrics=evaluate(model,readout,97301,args.n_eval)
            results.append(dict(seed=seed,kind=kind,training=training,metrics=metrics))
            (args.output/'results.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
            np.savez_compressed(args.output/f'{kind}-{seed}.npz',**{k:v.detach().numpy() for k,v in model.state_dict().items()})
            np.savez_compressed(args.output/f'{kind}-readout-{seed}.npz',**{k:v.detach().numpy() for k,v in readout.state_dict().items()})
            print(json.dumps(dict(kind=kind,seed=seed,training_seconds=training['seconds'],
                ceiling=metrics['readout_ceiling']['mean_projected_fidelity'],
                fidelity=metrics['one_step']['mean_projected_fidelity'],
                extrapolation=metrics['unseen_angles']['mean_projected_fidelity'],
                rollout=metrics['rollout']['32']['mean_projected_fidelity'],rank=metrics['representation']['effective_rank'])),flush=True)


if __name__=='__main__':main()
