"""Fresh paired confirmation of architecture-by-invariance effects.

Settings are selected from exploratory pilots, frozen before this holdout.
This confirms those settings, not globally optimal tuned architecture rankings.
"""
import argparse,datetime,hashlib,json
from pathlib import Path
import numpy as np
import torch
from quantum_world.data import transitions,trajectory
from quantum_world.jepa import train_world,fit_readout
from quantum_world.readout import fit_physical_readout
from quantum_world.physics import (haar_states,state_to_pauli,physical_metrics,
    pauli_to_density,unitary,GENERATORS,pauli_rotation)
from scripts.quantum_world_report import paired


def physical_evaluate(model,probe,seed,n=128,length=64):
    model.eval();probe.eval()
    dtype=next(model.parameters()).dtype
    d=transitions(n,seed)
    flow_rng=torch.Generator().manual_seed(seed+4000000)
    def latent(r):
        r=torch.tensor(r,dtype=dtype)
        return model.encoder(torch.cat([r,torch.zeros(len(r),8,dtype=dtype)],dim=-1))
    def advance(z,g,t):
        noise=torch.randn(z.shape,dtype=dtype,generator=flow_rng) if model.kind=='gaussian' else None
        return model.advance(z,torch.tensor(g,dtype=torch.long),torch.tensor(t,dtype=dtype),noise=noise)
    with torch.no_grad():
        z=latent(d['x']);readout=physical_metrics(probe(z).numpy(),d['psi'])
        one=physical_metrics(probe(advance(z,d['gate'],d['duration'])).numpy(),d['future'])
        rng=np.random.default_rng(seed+300000);g=rng.integers(4,6,n)
        angles=rng.choice([-1,1],n)*rng.uniform(1.8,np.pi,n)
        future=np.array([unitary(int(k),float(t))@s for k,t,s in zip(g,angles,d['psi'])])
        extrap=physical_metrics(probe(advance(z,g,angles)).numpy(),future)
        tr=trajectory(n,length,seed+1);roll_z=latent(state_to_pauli(tr['psi'][0]));rolls={}
        for k,(g,t) in enumerate(zip(tr['gate'],tr['duration']),1):
            roll_z=advance(roll_z,g,t)
            if k in (1,4,16,32,length):rolls[str(k)]=physical_metrics(probe(roll_z).numpy(),tr['psi'][k])
        # Algebra evaluated in latent space; separately test decoded quantum order.
        g0=np.zeros(n,dtype=np.int64);g1=np.full(n,2,dtype=np.int64);rz=np.full(n,4,dtype=np.int64)
        one_t=np.ones(n);a=np.full(n,.71);b=np.full(n,1.31)
        hcycle=advance(advance(z,g0,one_t),g0,one_t)
        cxcycle=advance(advance(z,g1,one_t),g1,one_t)
        rcycle=advance(advance(z,rz,a),rz,-a)
        composed=advance(advance(z,rz,a),rz,b);summed=advance(z,rz,a+b)
        commute_ab=advance(advance(z,rz,a),rz+1,b)
        commute_ba=advance(advance(z,rz+1,b),rz,a)
        ab=probe(advance(advance(z,g0,one_t),rz,a)).numpy()
        ba=probe(advance(advance(z,rz,a),g0,one_t)).numpy()
        trueab=np.array([unitary(4,.71)@unitary(0)@s for s in d['psi']])
        trueba=np.array([unitary(0)@unitary(4,.71)@s for s in d['psi']])
        bell=np.array([[1,0,0,1]],dtype=complex)/np.sqrt(2)
        ground=latent(state_to_pauli(np.array([[1,0,0,0]],dtype=complex)))
        bell_pred=probe(advance(advance(ground,np.array([0]),np.array([1.])),np.array([2]),np.array([1.]))).numpy()
        rho=pauli_to_density(bell_pred)
        pt=rho.reshape(1,2,2,2,2).transpose(0,1,4,3,2).reshape(1,4,4)
        negativity=float(np.maximum(-np.linalg.eigvalsh(pt),0).sum())
    def mse(a,b):return float((a-b).square().mean())
    return dict(readout_ceiling=readout,one_step=one,unseen_angles=extrap,rollout=rolls,
        algebra=dict(h_involution_latent_mse=mse(hcycle,z),cx_involution_latent_mse=mse(cxcycle,z),
          rz_inverse_latent_mse=mse(rcycle,z),rz_composition_latent_mse=mse(composed,summed),
          independent_commutation_latent_mse=mse(commute_ab,commute_ba),
          noncommuting_ab=physical_metrics(ab,trueab),noncommuting_ba=physical_metrics(ba,trueba)),
        bell=dict(**physical_metrics(bell_pred,bell),negativity=negativity,true_negativity=.5))


def linearization(model,seed,n=4096):
    """Independent calibration of latent Pauli coordinates; no model updates."""
    dtype=next(model.parameters()).dtype
    r=state_to_pauli(haar_states(n,seed));test=state_to_pauli(haar_states(512,seed+1))
    with torch.no_grad():
        def encode(x):return model.encoder(torch.cat([torch.tensor(x,dtype=dtype),torch.zeros(len(x),8,dtype=dtype)],dim=-1)).numpy()
        z=encode(r);truth=encode(test)
    design=np.column_stack([r,np.ones(n)]);coeff=np.linalg.lstsq(design,z,rcond=None)[0]
    pred=np.column_stack([test,np.ones(len(test))])@coeff
    result=dict(relative_linear_fit_error=float(np.mean((pred-truth)**2)/np.var(truth)),
        intercept_norm=float(np.linalg.norm(coeff[-1])))
    if model.kind=='latent_generator':
        q=coeff[:-1].T
        singular=np.linalg.svd(q,compute_uv=False)
        result['coordinate_condition']=float(singular[0]/singular[-1])
        raw=model.raw_generator.detach().numpy();a=(raw-raw.transpose(0,2,1))/2
        residual=[];maps=[]
        for g in range(6):
            physical=q@GENERATORS[g]@np.linalg.inv(q)
            residual.append(float(np.linalg.norm(a[g]-physical)/np.linalg.norm(physical)))
            from scipy.linalg import expm
            maps.append(float(np.linalg.norm(expm(a[g])-q@pauli_rotation(unitary(g))@np.linalg.inv(q))/np.linalg.norm(q@pauli_rotation(unitary(g))@np.linalg.inv(q))))
        result['generator_relative_errors']=residual
        result['unit_duration_map_relative_errors']=maps
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    p.add_argument('--seeds',nargs='+',type=int,default=list(range(7501,7511)))
    p.add_argument('--steps',type=int,default=4000);p.add_argument('--n-eval',type=int,default=128)
    p.add_argument('--physical-readout',action='store_true')
    p.add_argument('--train-seed',type=int,default=99301);p.add_argument('--probe-seed',type=int,default=99401)
    p.add_argument('--models',nargs='+',default=['direct','gaussian','latent_generator'])
    args=p.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    config=vars(args).copy();config['output']=str(args.output)
    config.update(anchor=20,lr=.003,target_grad='stop',invariance=[0.,1.],
                  evaluation_seed_offset=2000000,probe_steps=1800 if args.physical_readout else 1200,
                  gaussian_inference='fresh independent Gaussian source at every prediction, shared noise seeds across invariance conditions')
    protocol=args.output/'protocol.json';protocol.write_text(json.dumps(config,indent=2)+'\n')
    protocol_sha=hashlib.sha256(protocol.read_bytes()).hexdigest()
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    sources=[Path(__file__),Path('quantum_world/jepa.py'),Path('quantum_world/readout.py')]
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(protocol_sha256=protocol_sha,
        stage='independent confirmation of pilot-selected settings',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        sources={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},
        prior_art='invariance is established; no novelty or globally optimal architecture claim'),indent=2)+'\n')
    data=transitions(4096,config['train_seed']);r=torch.tensor(state_to_pauli(haar_states(4096,config['probe_seed'])),dtype=torch.float32)
    records=[]
    for seed in args.seeds:
        for kind in config['models']:
            for weight in config['invariance']:
                model,training=train_world(kind,seed,data,args.steps,anchor_weight=20,invariance_weight=weight)
                before={k:v.clone() for k,v in model.state_dict().items()}
                probe=fit_physical_readout(model,r,seed+1000000,steps=1800) if args.physical_readout else fit_readout(model,r,seed+1000000)
                assert all(torch.equal(v,before[k]) for k,v in model.state_dict().items())
                model=model.double();probe=probe.double()
                metrics=physical_evaluate(model,probe,seed+config['evaluation_seed_offset'],args.n_eval)
                diagnostics=linearization(model,seed+3000000)
                records.append(dict(seed=seed,kind=kind,invariance=weight,training=training,metrics=metrics,linearization=diagnostics))
                (args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
                if seed==args.seeds[0]:
                    np.savez_compressed(args.output/f'{kind}-inv{weight}-{seed}.npz',**{k:v.detach().numpy() for k,v in model.state_dict().items()})
                    np.savez_compressed(args.output/f'{kind}-inv{weight}-probe-{seed}.npz',**{k:v.detach().numpy() for k,v in probe.state_dict().items()})
                print(json.dumps(dict(seed=seed,kind=kind,invariance=weight,
                    ceiling=metrics['readout_ceiling']['mean_projected_fidelity'],
                    extrapolation=metrics['unseen_angles']['mean_projected_fidelity'],
                    rollout=metrics['rollout']['64']['mean_projected_fidelity'],
                    linearization=diagnostics['relative_linear_fit_error'])),flush=True)
    assert hashlib.sha256(protocol.read_bytes()).hexdigest()==protocol_sha
    comparisons=[]
    for key in ('unseen_angles','rollout'):
        contrasts=['generator_invariance','direct_invariance','invariant_architecture']
        if 'gaussian' in config['models']:contrasts += ['gaussian_invariance','invariant_generator_vs_gaussian']
        for contrast in contrasts:
            def values(kind,weight):
                group=sorted([r for r in records if r['kind']==kind and r['invariance']==weight],key=lambda r:r['seed'])
                return [r['metrics']['rollout']['64']['mean_projected_fidelity'] if key=='rollout' else r['metrics'][key]['mean_projected_fidelity'] for r in group]
            if contrast=='generator_invariance':a,b=values('latent_generator',1.),values('latent_generator',0.)
            elif contrast=='direct_invariance':a,b=values('direct',1.),values('direct',0.)
            elif contrast=='invariant_architecture':a,b=values('latent_generator',1.),values('direct',1.)
            elif contrast=='gaussian_invariance':a,b=values('gaussian',1.),values('gaussian',0.)
            else:a,b=values('latent_generator',1.),values('gaussian',1.)
            comparisons.append(dict(metric=key,contrast=contrast,**paired(a,b)))
    # Holm family adjustment across all predeclared contrasts.
    order=np.argsort([r['exact_two_sided_sign_flip_p'] for r in comparisons]);last=0.
    for rank,i in enumerate(order):
        adjusted=max(last,min(1.,(len(comparisons)-rank)*comparisons[i]['exact_two_sided_sign_flip_p']))
        comparisons[i]['holm_p']=adjusted;last=adjusted
    (args.output/'statistics.json').write_text(json.dumps(comparisons,indent=2)+'\n')
    (args.output/'completion.json').write_text(json.dumps(dict(protocol_sha256=protocol_sha,runs=len(records),
        finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
