"""Endpoint-only noise calibration with independent mixed-state evaluation."""
import argparse,datetime,hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from quantum_world.channels import ChannelWorld,transitions,states,channel,RATES,density_to_pauli,mixed_metrics,anchor_conflict


def evaluate(model,seed,n=128):
    data=transitions(n,seed);rng=np.random.default_rng(seed+200000);g=data['gate']
    t=rng.uniform(1.2,2.,n);future=np.array([channel(r,int(k),float(d),RATES[k]) for r,k,d in zip(data['rho'],g,t)])
    def predict(x,g,t):
        with torch.no_grad():return model(torch.tensor(x),torch.tensor(g),torch.tensor(t)).numpy()
    one=mixed_metrics(predict(data['x'],g,data['duration']),data['future'])
    extrap=mixed_metrics(predict(data['x'],g,t),future)
    pred=data['x'].copy();rho=data['rho'].copy();rolls={};nulls={}
    for step in range(1,33):
        g=rng.integers(0,2,n);t=rng.uniform(.05,.8,n)
        pred=predict(pred,g,t);rho=np.array([channel(r,int(k),float(d),RATES[k]) for r,k,d in zip(rho,g,t)])
        if step in (1,4,16,32):
            rolls[str(step)]=mixed_metrics(pred,rho)
            nulls[str(step)]=mixed_metrics(np.zeros_like(pred),rho)
    return dict(one_step=one,unseen_times=extrap,rollout=rolls,maximally_mixed_baseline=nulls)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',default=[8811,8812,8813]);parser.add_argument('--steps',type=int,default=1200)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit('Fresh output required')
    args.output.mkdir(parents=True);torch.set_num_threads(1)
    config=dict(seeds=args.seeds,steps=args.steps,n_train=[128,512],shots=[0,128],models=['physical','skew','affine'],lr=.01,batch=64,
        training_times=[.05,.8],evaluation_times=[1.2,2.],training_seed_offset=1000000,evaluation_seed_offset=2000000,
        scope='physical-coordinate calibration, known channel dictionary; no learned perception or quantum advantage',
        counts='128 shots per each of fifteen output Pauli observables, not 128 total shots',
        negative_times='forbidden for all models; irreversible noise semigroups',tuning='fixed common optimizer, exploratory comparison')
    (args.output/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    sources=[Path(__file__),Path('quantum_world/channels.py')];snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for source in sources:(snapshot/source.name).write_bytes(source.read_bytes())
    (args.output/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_sha256=hashlib.sha256((args.output/'protocol.json').read_bytes()).hexdigest(),
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    records=[]
    for seed in args.seeds:
        for n in config['n_train']:
            for shots in config['shots']:
                data=transitions(n,seed+1000000,shots)
                for kind in config['models']:
                    torch.manual_seed(seed);model=ChannelWorld(kind);optimizer=torch.optim.Adam(model.parameters(),lr=.01)
                    rng=torch.Generator().manual_seed(seed+3000000);start=time.perf_counter()
                    x=torch.tensor(data['x'],dtype=torch.float32);y=torch.tensor(data['y'],dtype=torch.float32)
                    g=torch.tensor(data['gate']);t=torch.tensor(data['duration'],dtype=torch.float32)
                    for _ in range(args.steps):
                        idx=torch.randint(n,(64,),generator=rng)
                        loss=(model(x[idx],g[idx],t[idx])-y[idx]).square().mean()
                        if not torch.isfinite(loss):raise FloatingPointError('Nonfinite channel training')
                        optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
                    seconds=time.perf_counter()-start;model=model.double()
                    metrics=evaluate(model,seed+2000000)
                    rates=torch.nn.functional.softplus(model.raw_rate).detach().numpy().tolist() if kind=='physical' else None
                    records.append(dict(seed=seed,n=n,shots=shots,kind=kind,seconds=seconds,parameters=sum(p.numel() for p in model.parameters()),
                        final_training_loss=float(loss.detach()),learned_rates=rates,metrics=metrics))
                    np.savez_compressed(args.output/f'{kind}-{seed}-n{n}-s{shots}.npz',**{k:v.detach().numpy() for k,v in model.state_dict().items()})
                    (args.output/'results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
                    print(json.dumps(dict(seed=seed,n=n,shots=shots,kind=kind,angle=metrics['unseen_times']['mean_fidelity'],roll32=metrics['rollout']['32']['mean_fidelity'],rates=rates)),flush=True)
    (args.output/'anchor-conflict.json').write_text(json.dumps([anchor_conflict(float(p)) for p in [.9,.7,.5,.3]],indent=2)+'\n')
    (args.output/'completion.json').write_text(json.dumps(dict(runs=len(records),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')


if __name__=='__main__':main()
