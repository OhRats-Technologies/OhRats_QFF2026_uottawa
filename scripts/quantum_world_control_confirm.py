"""Reproduce every frozen generator seed and audit planning on fresh shared tasks."""
import argparse,datetime,hashlib,json
from pathlib import Path
import numpy as np
import torch
from quantum_world.jepa import JEPAWorld,train_world
from quantum_world.readout import PhysicalReadout,fit_physical_readout
from quantum_world.latent_linear import LatentLinear
from quantum_world.control import FrozenModel,ExactPauliModel,plan,exact_states,rollout
from quantum_world.data import transitions
from quantum_world.physics import haar_states,state_to_pauli,physical_metrics
from scripts.quantum_world_jepa_confirm import physical_evaluate
from scripts.quantum_world_control_pilot import load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--episodes',type=int,default=32);args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    prior=Path('artifacts/quantum-world-jepa-confirmation-20261003')
    original=json.loads((prior/'results.json').read_text());previous=json.loads((prior/'protocol.json').read_text())
    seeds=previous['seeds']
    config=dict(seeds=seeds,episodes=args.episodes,task_seed=109501,planner_seed=110001,steps=250,restarts=4,
        prior_protocol_sha256=hashlib.sha256((prior/'protocol.json').read_bytes()).hexdigest(),
        reproduction='same frozen training settings/data/seeds; each saved rollout metric must match to 1e-8',
        selection='latent goal distance only; all training seeds retained',
        scope='fresh control tasks; reproduced models are not additional independent training evidence',
        transferred_predictor='periodic affine regression on same frozen encoder/training endpoints',
        direct_checkpoint='first predefined seed 7511, agreement=1')
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/jepa.py'),Path('quantum_world/control.py'),Path('quantum_world/latent_linear.py'),Path('quantum_world/readout.py')]
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        prior_results_sha256=hashlib.sha256((prior/'results.json').read_bytes()).hexdigest(),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    data=transitions(4096,previous['train_seed'])
    calibration=torch.tensor(state_to_pauli(haar_states(4096,previous['probe_seed'])),dtype=torch.float32)
    initial=haar_states(args.episodes,config['task_seed']);target=haar_states(args.episodes,config['task_seed']+1)
    target[:args.episodes//2]=np.array([1,0,0,1])/np.sqrt(2)
    np.savez_compressed(args.output/'tasks.npz',initial=initial,target=target)
    records=[];reproductions=[]
    def evaluate_planner(model,probe,seed,label):
        result=plan(model,state_to_pauli(initial),state_to_pauli(target),config['planner_seed'],250,4)
        future=exact_states(initial,result['angles'])
        fidelity=np.abs(np.einsum('ni,ni->n',target.conj(),future))**2
        prediction=None
        if probe is not None:
            with torch.no_grad():pred=probe(rollout(model,model.encode(state_to_pauli(initial)),torch.tensor(result['angles']))).numpy()
            prediction=physical_metrics(pred,target)
        np.savez_compressed(args.output/f'{label}-{seed}-controls.npz',angles=result['angles'],latent_cost=result['latent_cost'],selected_restart=result['selected_restart'],future=future)
        record=dict(seed=seed,kind=label,seconds=result['seconds'],mean_fidelity=float(fidelity.mean()),
            bell_fidelity=float(fidelity[:args.episodes//2].mean()),arbitrary_fidelity=float(fidelity[args.episodes//2:].mean()),
            fidelity=fidelity.tolist(),fraction_above_99=float((fidelity>.99).mean()),
            predicted_target_metrics=prediction,latent_cost=result['latent_cost'].tolist())
        records.append(record);(args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(stage='planning',seed=seed,kind=label,fidelity=record['mean_fidelity'])),flush=True)
    for seed in seeds:
        world,training=train_world('latent_generator',seed,data,previous['steps'],anchor_weight=20,invariance_weight=1.)
        before={k:v.clone() for k,v in world.state_dict().items()}
        probe=fit_physical_readout(world,calibration,seed+1000000,1800)
        assert all(torch.equal(v,before[k]) for k,v in world.state_dict().items())
        world=world.double();probe=probe.double()
        metric=physical_evaluate(world,probe,seed+previous['evaluation_seed_offset'],previous['n_eval'])
        earlier=next(r for r in original if r['seed']==seed and r['kind']=='latent_generator' and r['invariance']==1.)
        discrepancy=max(abs(metric['rollout'][str(t)]['mean_projected_fidelity']-earlier['metrics']['rollout'][str(t)]['mean_projected_fidelity']) for t in (1,4,16,32,64))
        if discrepancy>1e-8:raise RuntimeError(f'Reproduction discrepancy for seed {seed}: {discrepancy}')
        reproductions.append(dict(seed=seed,max_fidelity_discrepancy=discrepancy,training=training))
        (args.output/'reproductions.json').write_text(json.dumps(reproductions,indent=2)+'\n')
        for name,module in (('world',world),('probe',probe)):
            np.savez_compressed(args.output/f'{name}-{seed}.npz',**{k:v.detach().numpy() for k,v in module.state_dict().items()})
        evaluate_planner(FrozenModel(world),probe,seed,'generator')
        linear=LatentLinear(world.encoder).fit(data)
        evaluate_planner(FrozenModel(linear),probe,seed,'transferred_generator_encoder')
    direct=load(JEPAWorld('direct'),prior/'direct-inv1.0-7511.npz')
    probe=load(PhysicalReadout(),prior/'direct-inv1.0-probe-7511.npz')
    evaluate_planner(FrozenModel(direct),probe,7511,'direct')
    evaluate_planner(FrozenModel(LatentLinear(direct.encoder).fit(data)),probe,7511,'transferred_direct_encoder')
    evaluate_planner(ExactPauliModel(),None,0,'exact_reference')
    assert len(records)==2*len(seeds)+3 and len(reproductions)==len(seeds)
    (args.output/'completion.json').write_text(json.dumps(dict(runs=len(records),reproduced_seeds=len(reproductions),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
