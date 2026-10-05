"""Can more shots give confident wrong indices under misspecified readout?"""
import argparse,datetime,hashlib,json,time
from pathlib import Path
import numpy as np
from quantum_world.measurement_readout import probabilities,blind_estimate,calibrated_estimate,goodness_of_fit
from quantum_world.measurements import assessment


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replicates',type=int,default=200);args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True)
    config=dict(replicates=args.replicates,budgets=[16384,65536,262144],probe_time=.8,step=.5,
        scenarios=[dict(name='ideal',rate=1.10,readout_error=0.),dict(name='misspecified',rate=1.05,readout_error=.01)],
        noise_seed=211101,calibration_fraction=.25,
        inference='blind exact binomial; blind plus Pearson nonreturn guard; propagated exact calibrated interval',
        resource='same total shots; calibrated policy reserves one quarter for independent |00> reference readout',
        scope='fixed model-assumption stress scenarios, not empirical hardware noise or arbitrary-channel certification',
        cross_budget='common seed streams; independently sampled replicates within each scenario/budget, no pooled independent sample claim')
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/measurement_readout.py'),Path('quantum_world/measurements.py')]
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    records=[];started=time.perf_counter()
    for scenario_index,scenario in enumerate(config['scenarios']):
        rate=scenario['rate'];error=scenario['readout_error'];probe_time=config['probe_time']
        q=probabilities(rate,probe_time,error);ref=probabilities(0.,probe_time,error)
        for budget in config['budgets']:
            for replicate in range(args.replicates):
                seed=config['noise_seed']+replicate+scenario_index*100000
                raw=np.random.default_rng(seed).multinomial(budget,q)
                n_ref=budget//4
                calibration=np.random.default_rng(seed+1000000).multinomial(n_ref,ref)
                probe=np.random.default_rng(seed+2000000).multinomial(budget-n_ref,q)
                blind=blind_estimate(raw,probe_time);calibrated=calibrated_estimate(calibration,probe,probe_time)
                guard=goodness_of_fit(raw)
                for kind,estimate in [('blind',blind),('guarded',blind),('calibrated',calibrated)]:
                    result=assessment(estimate,rate,config['step'])
                    withheld=kind=='guarded' and guard['reject']
                    if withheld:result['resolved_correct']=False;result['resolved_wrong']=False
                    records.append(dict(scenario=scenario['name'],budget=budget,seed=seed,kind=kind,
                        true_rate=rate,true_readout_error=error,withheld=withheld,
                        **estimate,**result,guard=guard,raw_counts=raw.tolist(),
                        reference_counts=calibration.tolist() if kind=='calibrated' else None,
                        probe_counts=probe.tolist() if kind=='calibrated' else None))
            (args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
            group=[r for r in records if r['scenario']==scenario['name'] and r['budget']==budget]
            print(json.dumps(dict(scenario=scenario['name'],budget=budget,summary={kind:dict(
                interval_coverage=float(np.mean([r['coverage'] for r in group if r['kind']==kind])),
                resolved_correct=float(np.mean([r['resolved_correct'] for r in group if r['kind']==kind])),
                resolved_wrong=float(np.mean([r['resolved_wrong'] for r in group if r['kind']==kind])),
                withheld=float(np.mean([r['withheld'] for r in group if r['kind']==kind]))) for kind in ('blind','guarded','calibrated')})),flush=True)
    (args.output/'completion.json').write_text(json.dumps(dict(comparisons=len(records),
        measurement_draws=3*len(config['budgets'])*len(config['scenarios'])*args.replicates,
        independent_noise_seed_families=3*len(config['scenarios'])*args.replicates,
        seconds=time.perf_counter()-started,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
