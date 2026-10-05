"""Exploratory gate-algebra intervention, separate from frozen prior confirmation."""
import argparse,datetime,hashlib,json
from pathlib import Path
import numpy as np
import torch
from quantum_world.data import transitions
from quantum_world.physics import haar_states,state_to_pauli
from quantum_world.jepa import train_world
from quantum_world.readout import fit_physical_readout
from scripts.quantum_world_jepa_confirm import physical_evaluate,linearization


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',default=[7611,7612,7613,7614])
    parser.add_argument('--weights',type=float,nargs='+',default=[0.,10.])
    parser.add_argument('--steps',type=int,default=4000)
    parser.add_argument('--train-seed',type=int,default=99701);parser.add_argument('--probe-seed',type=int,default=99801)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    config={**vars(args),'output':str(args.output),'invariance':1.,'anchor':20.,'lr':.003,
        'probe_steps':1800,'n_eval':128,'selection':'all seeds reported; no best-outcome checkpoint selection',
        'prior':'H0,H1,CX01,CX10 have order two; the two RZ generators commute',
        'scope':'new exploratory intervention, motivated by previously frozen holdout failures'}
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/jepa.py'),Path('quantum_world/algebra.py'),Path('quantum_world/readout.py'),Path('scripts/quantum_world_jepa_confirm.py')]
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        sources={str(source):hashlib.sha256(source.read_bytes()).hexdigest() for source in sources}),indent=2)+'\n')
    data=transitions(4096,args.train_seed)
    r=torch.tensor(state_to_pauli(haar_states(4096,args.probe_seed)),dtype=torch.float32)
    records=[]
    for seed in args.seeds:
        for weight in args.weights:
            world,training=train_world('latent_generator',seed,data,args.steps,anchor_weight=20,invariance_weight=1.,algebra_weight=weight)
            before={k:v.clone() for k,v in world.state_dict().items()}
            probe=fit_physical_readout(world,r,seed+1000000,steps=1800)
            assert all(torch.equal(v,before[k]) for k,v in world.state_dict().items())
            world=world.double();probe=probe.double()
            metrics=physical_evaluate(world,probe,seed+2000000,128)
            diagnostics=linearization(world,seed+3000000)
            for name,module in (('world',world),('probe',probe)):
                np.savez_compressed(args.output/f'{name}-w{weight}-{seed}.npz',**{k:v.detach().numpy() for k,v in module.state_dict().items()})
            records.append(dict(seed=seed,weight=weight,training=training,metrics=metrics,linearization=diagnostics))
            (args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
            print(json.dumps(dict(seed=seed,weight=weight,ceiling=metrics['readout_ceiling']['mean_projected_fidelity'],
                angle=metrics['unseen_angles']['mean_projected_fidelity'],roll64=metrics['rollout']['64']['mean_projected_fidelity'],
                linearization=diagnostics['relative_linear_fit_error'])),flush=True)
    (args.output/'completion.json').write_text(json.dumps(dict(runs=len(records),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
