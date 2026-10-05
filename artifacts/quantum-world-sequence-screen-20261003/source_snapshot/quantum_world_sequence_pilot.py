"""Matched-data short-trajectory intervention with positive frozen readouts."""
import argparse,datetime,hashlib,json
from pathlib import Path
import numpy as np
import torch
from quantum_world.sequence_jepa import triplets,train_sequence
from quantum_world.physics import haar_states,state_to_pauli
from quantum_world.readout import fit_physical_readout
from scripts.quantum_world_jepa_confirm import physical_evaluate,linearization


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',default=[7711,7712,7713,7714]);parser.add_argument('--steps',type=int,default=4000)
    parser.add_argument('--models',nargs='+',default=['direct','latent_generator'])
    parser.add_argument('--train-seed',type=int,default=114001);parser.add_argument('--probe-seed',type=int,default=115001)
    parser.add_argument('--stage',choices=['exploration','confirmation'],default='exploration');args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    config={**vars(args),'output':str(args.output),'triplets':4096,'consistency_weights':[0.,1.],
        'batch':64,'anchor':20.,'agreement':1.,'lr':.003,'probe_steps':1800,'n_eval':128,
        'scope':'same observed state/action triplets; short rollout adds compute, not labels; no novelty or tuned global architecture claim'}
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/sequence_jepa.py'),Path('quantum_world/jepa.py'),Path('quantum_world/readout.py'),Path('scripts/quantum_world_jepa_confirm.py')]
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    data=triplets(4096,args.train_seed);np.savez_compressed(args.output/'observed-triplets.npz',**data)
    data_hash=hashlib.sha256(data['observed'].tobytes()+data['gate'].tobytes()+data['duration'].tobytes()).hexdigest()
    calibration=torch.tensor(state_to_pauli(haar_states(4096,args.probe_seed)),dtype=torch.float32);records=[]
    for seed in args.seeds:
        for kind in args.models:
            for weight in (0.,1.):
                model,training=train_sequence(kind,seed,data,args.steps,weight)
                before={k:v.clone() for k,v in model.state_dict().items()}
                probe=fit_physical_readout(model,calibration,seed+1000000,1800)
                assert all(torch.equal(v,before[k]) for k,v in model.state_dict().items())
                model=model.double();probe=probe.double()
                metrics=physical_evaluate(model,probe,seed+2000000,128);diagnostics=linearization(model,seed+3000000)
                for name,module in (('world',model),('probe',probe)):
                    np.savez_compressed(args.output/f'{name}-{kind}-w{weight}-{seed}.npz',**{k:v.detach().numpy() for k,v in module.state_dict().items()})
                records.append(dict(seed=seed,kind=kind,consistency=weight,data_sha256=data_hash,training=training,metrics=metrics,linearization=diagnostics))
                (args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
                print(json.dumps(dict(seed=seed,kind=kind,consistency=weight,ceiling=metrics['readout_ceiling']['mean_projected_fidelity'],
                    angle=metrics['unseen_angles']['mean_projected_fidelity'],roll64=metrics['rollout']['64']['mean_projected_fidelity'],
                    linearization=diagnostics['relative_linear_fit_error'])),flush=True)
    (args.output/'completion.json').write_text(json.dumps(dict(runs=len(records),data_sha256=data_hash,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
