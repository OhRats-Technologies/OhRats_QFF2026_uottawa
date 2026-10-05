"""Frozen-model control demonstration with exact outcomes revealed afterward."""
import argparse,datetime,hashlib,json
from pathlib import Path
import numpy as np
import torch
from quantum_world.control import FrozenModel,ExactPauliModel,plan,exact_states,control_template
from quantum_world.jepa import JEPAWorld
from quantum_world.readout import PhysicalReadout
from quantum_world.physics import haar_states,state_to_pauli,concurrence


def load(module,path):
    with np.load(path) as checkpoint:
        module.load_state_dict({key:torch.tensor(checkpoint[key]) for key in checkpoint.files})
    return module.double().eval()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--checkpoint-dir',type=Path,default=Path('artifacts/quantum-world-jepa-physical-readout-smoke-20261003'))
    parser.add_argument('--seed',type=int,default=99501);parser.add_argument('--episodes',type=int,default=8)
    parser.add_argument('--steps',type=int,default=250);parser.add_argument('--restarts',type=int,default=4)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output directory required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    config={**vars(args),'output':str(args.output),'checkpoint_dir':str(args.checkpoint_dir),
            'selection':'minimum learned latent goal distance; exact outcomes evaluated only after selection',
            'scope':'utility demonstration using one preselected smoke seed, not a multi-seed training comparison',
            'checkpoint_seed':7501,'invariance':1.,'template':control_template(),'lr':.05}
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    inputs=[args.checkpoint_dir/f'{kind}-inv1.0-7501.npz' for kind in ('direct','latent_generator')]
    inputs += [args.checkpoint_dir/f'{kind}-inv1.0-probe-7501.npz' for kind in ('direct','latent_generator')]
    sources=[Path(__file__),Path('quantum_world/control.py')]
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    initial=haar_states(args.episodes,args.seed)
    target=haar_states(args.episodes,args.seed+1)
    target[:args.episodes//2]=np.array([1,0,0,1])/np.sqrt(2)
    np.savez_compressed(args.output/'tasks.npz',initial=initial,target=target)
    records=[]
    for kind in ('direct','latent_generator','exact_reference'):
        probe=None
        if kind=='exact_reference':model=ExactPauliModel()
        else:
            world=load(JEPAWorld(kind),args.checkpoint_dir/f'{kind}-inv1.0-7501.npz')
            model=FrozenModel(world)
            probe=load(PhysicalReadout(),args.checkpoint_dir/f'{kind}-inv1.0-probe-7501.npz')
        result=plan(model,state_to_pauli(initial),state_to_pauli(target),args.seed+2,args.steps,args.restarts)
        future=exact_states(initial,result['angles']);random=exact_states(initial,result['random_angles'])
        fidelity=np.abs(np.einsum('ni,ni->n',target.conj(),future))**2
        random_fidelity=np.abs(np.einsum('ni,ni->n',target.conj(),random))**2
        predicted=None
        if probe is not None:
            from quantum_world.control import rollout
            from quantum_world.physics import physical_metrics
            with torch.no_grad():r=probe(rollout(model,model.encode(state_to_pauli(initial)),torch.tensor(result['angles']))).numpy()
            predicted=physical_metrics(r,target)
        np.savez_compressed(args.output/f'{kind}-controls.npz',**{k:v for k,v in result.items() if isinstance(v,np.ndarray)},future=future)
        record=dict(kind=kind,seconds=result['seconds'],steps=args.steps,restarts=args.restarts,
            latent_cost=result['latent_cost'].tolist(),fidelity=fidelity.tolist(),
            random_fidelity=random_fidelity.tolist(),concurrence=concurrence(future).tolist(),
            mean_fidelity=float(fidelity.mean()),bell_mean_fidelity=float(fidelity[:args.episodes//2].mean()),
            arbitrary_mean_fidelity=float(fidelity[args.episodes//2:].mean()),
            fraction_above_99=float((fidelity>.99).mean()),predicted_target_metrics=predicted)
        records.append(record)
        (args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
        print(json.dumps(record),flush=True)
    (args.output/'completion.json').write_text(json.dumps(dict(runs=len(records),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
