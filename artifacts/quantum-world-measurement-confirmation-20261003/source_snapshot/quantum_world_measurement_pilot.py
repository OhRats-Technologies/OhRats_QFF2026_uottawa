"""Fixed measurement designs, fresh noise draws and equal total-shot budgets."""
import argparse,datetime,hashlib,json,time
from pathlib import Path
import numpy as np
from quantum_world.measurements import tomography_design,tomography_estimate,focused_estimate,assessment,grouped_design,grouped_estimate,single_pauli_estimate


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--stage',choices=['screen','confirmation'],default='screen')
    parser.add_argument('--replicates',type=int,default=40);args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True)
    config=dict(stage=args.stage,replicates=args.replicates,budgets=[4096,16384,65536],rate=1.10,step=.5,
        design_seed=112001 if args.stage=='screen' else 113001,
        noise_seed=202101 if args.stage=='screen' else 203101,
        focused_time=.8,n_states=64,strategies=['random_pauli','grouped_pauli','grouped_fixed_time','targeted_single_pauli','focused_z','focused_bell'],
        interval_methods='random: approximate profile likelihood; focused: exact binomial, all 95% pointwise',
        scope='known global isotropic noise, ideal preparation/readout, separate simulator comparison',
        resource='exact same total measurement shots per strategy; gate/preparation costs are not equated',
        bell_control='focused Bell and separable Z share identical draws; targeted single Pauli is a marginal of those same counts',
        selection='all draws included; fixed time chosen without true-rate optimization; no outcome selection')
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/measurements.py')];snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    records=[];started=time.perf_counter()
    for budget in config['budgets']:
        design=tomography_design(budget,config['design_seed'])
        grouped=grouped_design(budget,config['design_seed'])
        fixed={**grouped,'times':np.full_like(grouped['times'],config['focused_time'])}
        np.savez_compressed(args.output/f'design-{budget}.npz',**design)
        np.savez_compressed(args.output/f'grouped-design-{budget}.npz',**grouped)
        np.savez_compressed(args.output/f'fixed-time-design-{budget}.npz',**fixed)
        for replicate in range(args.replicates):
            seed=config['noise_seed']+replicate
            random=tomography_estimate(design,config['rate'],seed)
            grouped_result=grouped_estimate(grouped,config['rate'],seed+2000000)
            fixed_result=grouped_estimate(fixed,config['rate'],seed+3000000)
            focused=focused_estimate(budget,config['rate'],seed+1000000,config['focused_time'])
            single=single_pauli_estimate(focused,config['focused_time'])
            for kind,estimate in [('random_pauli',random),('grouped_pauli',grouped_result),('grouped_fixed_time',fixed_result),('targeted_single_pauli',single),('focused_z',focused),('focused_bell',focused)]:
                assert estimate['shots']==budget
                # Raw tomography counts are saved in compressed arrays, not giant JSON lists.
                if kind in ('random_pauli','grouped_pauli','grouped_fixed_time'):np.savez_compressed(args.output/f'{kind}-counts-{budget}-{seed}.npz',counts=np.array(estimate['counts']))
                compact={k:v for k,v in estimate.items() if k!='counts'}
                if kind not in ('random_pauli','grouped_pauli','grouped_fixed_time'):compact['basis_counts']=estimate['counts']
                records.append(dict(budget=budget,seed=seed,kind=kind,**compact,**assessment(estimate,config['rate'],config['step'])))
        (args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
        group=[r for r in records if r['budget']==budget]
        print(json.dumps(dict(budget=budget,summary={kind:dict(
            coverage=float(np.mean([r['coverage'] for r in group if r['kind']==kind])),
            resolved_correct=float(np.mean([r['resolved_correct'] for r in group if r['kind']==kind])),
            resolved_wrong=float(np.mean([r['resolved_wrong'] for r in group if r['kind']==kind])),
            rate_rmse=float(np.sqrt(np.mean([r['squared_rate_error'] for r in group if r['kind']==kind])))) for kind in config['strategies']})),flush=True)
    (args.output/'completion.json').write_text(json.dumps(dict(comparisons=len(records),independent_measurement_draws=4*len(config['budgets'])*args.replicates,
        seconds=time.perf_counter()-started,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
