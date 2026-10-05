"""Classical full-batch likelihood/uncertainty audit of the known noise dictionary."""
import argparse,datetime,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
from quantum_world.channels import transitions,pauli_to_density,density_to_pauli,depolarizing_certificate


def expected_pauli(x,gate,duration,rate):
    p=np.exp(-rate*duration)
    if gate==0:return p[:,None]*x
    rho=pauli_to_density(x);diagonal=np.column_stack([np.ones((len(x),2)),np.sqrt(p)[:,None]*np.ones((len(x),2))])
    future=rho*diagonal[:,:,None]*diagonal[:,None,:]
    future[:,:2,:2]+=(1-p)[:,None,None]*rho[:,2:,2:]
    return density_to_pauli(future)


def fit(x,gate,duration,counts,shots):
    rates=[]
    for g in (0,1):
        mask=gate==g
        def objective(rate):
            probs=np.clip((expected_pauli(x[mask],g,duration[mask],rate)+1)/2,1e-12,1-1e-12)
            return float(-np.sum(counts[mask]*np.log(probs)+(shots-counts[mask])*np.log1p(-probs)))
        optimum=minimize_scalar(objective,bounds=(1e-5,4.),method='bounded',options={'xatol':1e-7})
        if not optimum.success:raise RuntimeError('Rate likelihood optimization failed')
        # Numerical grid audit; not a theorem of global optimality.
        if objective(optimum.x)>min(objective(v) for v in np.linspace(.001,4.,41))+1e-5:
            raise RuntimeError('Rate fit is worse than a fixed grid candidate')
        rates.append(float(optimum.x))
    return np.array(rates)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bootstrap',type=int,default=200);args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True)
    prior=Path('artifacts/quantum-world-noise-channels-20261003/results.json')
    config=dict(bootstrap=args.bootstrap,shots=128,scope='posthoc classical optimizer/uncertainty audit, no additional independent datasets',
        interval='pointwise percentile parametric bootstrap conditional on known channel family, prepared inputs, binomial measurement model',
        selection='all six noisy physical fits; no omitted seeds',bounds=[1e-5,4.],
        limitations='approximate intervals, no simultaneous coverage or hardware model-misspecification guarantee')
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/channels.py')];snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        input_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    original=json.loads(prior.read_text());records=[]
    for old in original:
        if old['kind']!='physical' or old['shots']!=128:continue
        data=transitions(old['n'],old['seed']+1000000,128)
        counts=np.rint((data['y']+1)*64).astype(int)
        rates=fit(data['x'],data['gate'],data['duration'],counts,128)
        probs=np.empty_like(data['x'])
        for g in (0,1):
            mask=data['gate']==g
            probs[mask]=(expected_pauli(data['x'][mask],g,data['duration'][mask],rates[g])+1)/2
        rng=np.random.default_rng(old['seed']+4000000+old['n']);boot=[]
        for _ in range(args.bootstrap):
            simulated=rng.binomial(128,np.clip(probs,0,1))
            boot.append(fit(data['x'],data['gate'],data['duration'],simulated,128))
        interval=np.quantile(boot,[.025,.975],axis=0).T
        index_range=[depolarizing_certificate(interval[0,1])['entanglement_breaking_index'],
                     depolarizing_certificate(interval[0,0])['entanglement_breaking_index']]
        record=dict(seed=old['seed'],n=old['n'],sgd_rates=old['learned_rates'],likelihood_rates=rates.tolist(),
            pointwise_parametric_bootstrap_95=interval.tolist(),bootstrap_replicates=np.asarray(boot).tolist(),
            sgd_conditional_certificate=depolarizing_certificate(old['learned_rates'][0]),
            likelihood_conditional_certificate=depolarizing_certificate(rates[0]),
            conditional_index_interval=index_range)
        records.append(record);(args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(seed=old['seed'],n=old['n'],sgd=old['learned_rates'],likelihood=rates.tolist(),interval=interval.tolist(),index_range=index_range)),flush=True)
    assert len(records)==6
    (args.output/'completion.json').write_text(json.dumps(dict(runs=len(records),bootstrap_fits=6*args.bootstrap,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
