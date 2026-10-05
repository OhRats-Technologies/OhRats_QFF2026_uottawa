"""Fresh control tasks for every frozen triplet model and transferred predictor."""
import argparse,datetime,hashlib,json
from pathlib import Path
import numpy as np
import torch
from quantum_world.jepa import JEPAWorld
from quantum_world.readout import PhysicalReadout
from quantum_world.latent_linear import LatentLinear
from quantum_world.control import FrozenModel,ExactPauliModel,plan,exact_states,rollout
from quantum_world.physics import haar_states,state_to_pauli,physical_metrics
from scripts.quantum_world_control_pilot import load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    prior=Path('artifacts/quantum-world-sequence-confirmation-20261003')
    records=json.loads((prior/'results.json').read_text());assert len(records)==json.loads((prior/'completion.json').read_text())['runs']==20
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    config=dict(episodes=32,task_seed=119001,planner_seed=120001,steps=250,restarts=4,
        selection='latent goal distance only; exact outcomes evaluated afterward; all twenty frozen checkpoints retained',
        classical_baseline='periodic affine regression, same frozen encoder and both saved observed training transitions',
        scope='fresh task evaluation conditional on fixed dataset/settings; no additional independent training runs')
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/control.py'),Path('quantum_world/latent_linear.py'),Path('quantum_world/physics.py')]
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for p in sources:(snapshot/p.name).write_bytes(p.read_bytes())
    checkpoint_paths=sorted(prior.glob('world-*.npz'))+sorted(prior.glob('probe-*.npz'))
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        prior_results_sha256=hashlib.sha256((prior/'results.json').read_bytes()).hexdigest(),
        checkpoints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in checkpoint_paths},
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    with np.load(prior/'observed-triplets.npz') as triplet:
        data=dict(x=triplet['observed'][:-1].reshape(-1,15),y=triplet['observed'][1:].reshape(-1,15),
            gate=triplet['gate'].reshape(-1),duration=triplet['duration'].reshape(-1))
    initial=haar_states(32,config['task_seed']);target=haar_states(32,config['task_seed']+1)
    target[:16]=np.array([1,0,0,1])/np.sqrt(2);np.savez_compressed(args.output/'tasks.npz',initial=initial,target=target)
    results=[]
    def evaluate(model,probe,seed,weight,kind):
        result=plan(model,state_to_pauli(initial),state_to_pauli(target),config['planner_seed'],250,4)
        future=exact_states(initial,result['angles']);fidelity=np.abs(np.einsum('ni,ni->n',target.conj(),future))**2
        prediction=None
        if probe is not None:
            with torch.no_grad():pred=probe(rollout(model,model.encode(state_to_pauli(initial)),torch.tensor(result['angles']))).numpy()
            prediction=physical_metrics(pred,target)
        np.savez_compressed(args.output/f'{kind}-w{weight}-{seed}.npz',angles=result['angles'],future=future,
            latent_cost=result['latent_cost'],selected_restart=result['selected_restart'])
        results.append(dict(seed=seed,consistency=weight,kind=kind,seconds=result['seconds'],mean_fidelity=float(fidelity.mean()),
            bell_fidelity=float(fidelity[:16].mean()),arbitrary_fidelity=float(fidelity[16:].mean()),fidelity=fidelity.tolist(),
            predicted_target_metrics=prediction))
        (args.output/'results.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:results[-1][k] for k in ('seed','consistency','kind','mean_fidelity')}),flush=True)
    for r in records:
        seed,weight=r['seed'],r['consistency']
        world=load(JEPAWorld('latent_generator'),prior/f'world-latent_generator-w{weight}-{seed}.npz')
        probe=load(PhysicalReadout(),prior/f'probe-latent_generator-w{weight}-{seed}.npz')
        before={k:v.clone() for k,v in world.state_dict().items()}
        evaluate(FrozenModel(world),probe,seed,weight,'generator')
        evaluate(FrozenModel(LatentLinear(world.encoder).fit(data)),probe,seed,weight,'transferred_linear')
        assert all(torch.equal(v,before[k]) for k,v in world.state_dict().items())
    evaluate(ExactPauliModel(),None,0,0.,'exact_reference');assert len(results)==41
    (args.output/'completion.json').write_text(json.dumps(dict(runs=len(results),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
