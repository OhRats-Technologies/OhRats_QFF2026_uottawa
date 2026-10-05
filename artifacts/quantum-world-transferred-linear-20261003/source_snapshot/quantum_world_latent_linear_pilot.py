"""Strong periodic predictor on the exact same frozen learned encoders."""
import argparse,datetime,hashlib,json
from pathlib import Path
from quantum_world.jepa import JEPAWorld
from quantum_world.readout import PhysicalReadout
from quantum_world.latent_linear import LatentLinear
from quantum_world.data import transitions
from scripts.quantum_world_control_pilot import load
from scripts.quantum_world_jepa_confirm import physical_evaluate
import torch


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    cases=[('smoke',Path('artifacts/quantum-world-jepa-physical-readout-smoke-20261003'),7501),
           ('confirmation',Path('artifacts/quantum-world-jepa-confirmation-20261003'),7511)]
    config=dict(cases=[dict(name=name,path=str(p),seed=s) for name,p,s in cases],ridge=1e-6,
        selection='first predefined checkpoint seeds, all available architecture/invariance conditions',
        scope='transferred representation comparator; encoder previously trained jointly with original dynamics',
        evaluation_seed=399901,n_eval=128)
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/latent_linear.py')]
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    records=[]
    for name,p,seed in cases:
        protocol=json.loads((p/'protocol.json').read_text());data=transitions(4096,protocol['train_seed'])
        for kind in protocol['models']:
            for inv in (0.,1.):
                checkpoint=p/f'{kind}-inv{inv}-{seed}.npz'
                world=load(JEPAWorld(kind),checkpoint)
                probe=load(PhysicalReadout(),p/f'{kind}-inv{inv}-probe-{seed}.npz')
                linear=LatentLinear(world.encoder).fit(data)
                original=physical_evaluate(world,probe,config['evaluation_seed'],128)
                transferred=physical_evaluate(linear,probe,config['evaluation_seed'],128)
                records.append(dict(case=name,seed=seed,kind=kind,invariance=inv,
                    checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                    original=original,transferred=transferred))
                (args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
                print(json.dumps(dict(case=name,kind=kind,invariance=inv,
                    original=original['rollout']['64']['mean_projected_fidelity'],
                    transferred=transferred['rollout']['64']['mean_projected_fidelity'])),flush=True)
    (args.output/'completion.json').write_text(json.dumps(dict(runs=len(records),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
