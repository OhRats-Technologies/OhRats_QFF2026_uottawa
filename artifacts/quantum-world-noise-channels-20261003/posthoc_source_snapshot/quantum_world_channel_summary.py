"""Posthoc structural channel audit, separate from the frozen fitting manifest."""
import hashlib,json,datetime
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from quantum_world.channels import ChannelWorld,choi_from_transfer,depolarizing_certificate,RATES
from scripts.quantum_world_control_pilot import load


def main():
    p=Path('artifacts/quantum-world-noise-channels-20261003')
    records=json.loads((p/'results.json').read_text());assert len(records)==36
    manifest=json.loads((p/'manifest.json').read_text())
    assert json.loads((p/'completion.json').read_text())['runs']==36
    assert hashlib.sha256((p/'protocol.json').read_bytes()).hexdigest()==manifest['protocol_sha256']
    for source,sha in manifest['sources'].items():assert hashlib.sha256((p/'source_snapshot'/Path(source).name).read_bytes()).hexdigest()==sha
    diagnostics=[];certificates=[]
    for record in records:
        path=p/f"{record['kind']}-{record['seed']}-n{record['n']}-s{record['shots']}.npz"
        model=load(ChannelWorld(record['kind']),path)
        generators=model.matrices().detach().numpy();tests=[]
        for gate in (0,1):
            for t in (.1,.8,1.6,5.):
                choi=choi_from_transfer(expm(generators[gate]*t))
                marginal=np.trace(choi.reshape(4,4,4,4),axis1=1,axis2=3)
                tests.append(dict(gate=gate,time=t,min_choi_eigenvalue=float(np.linalg.eigvalsh(choi).min()),
                    trace_preservation_residual=float(np.linalg.norm(marginal-np.eye(4)/4))))
        diagnostics.append(dict(seed=record['seed'],n=record['n'],shots=record['shots'],kind=record['kind'],
            checkpoint_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),choi_tests=tests))
        if record['kind']=='physical':certificates.append(dict(seed=record['seed'],n=record['n'],shots=record['shots'],
            **depolarizing_certificate(record['learned_rates'][0])))
    summary=[]
    for n in (128,512):
        for shots in (0,128):
            for kind in ('physical','skew','affine'):
                group=[r for r in records if (r['n'],r['shots'],r['kind'])==(n,shots,kind)];assert len(group)==3
                def avg(fn):return float(np.mean([fn(r) for r in group]))
                summary.append(dict(n=n,shots=shots,kind=kind,
                    unseen_time_fidelity=avg(lambda r:r['metrics']['unseen_times']['mean_fidelity']),
                    raw_valid_fraction=avg(lambda r:r['metrics']['unseen_times']['raw_valid_fraction']),
                    rollout32_fidelity=avg(lambda r:r['metrics']['rollout']['32']['mean_fidelity']),
                    maximally_mixed_rollout32=avg(lambda r:r['metrics']['maximally_mixed_baseline']['32']['mean_fidelity'])))
    result=dict(scope='posthoc structural diagnostics, not additional tuning or experimental samples',
        sources={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),Path('quantum_world/channels.py')]},
        summary=summary,choi_diagnostics=diagnostics,depolarizing_certificates=certificates,
        true_depolarizing_certificate=depolarizing_certificate(RATES[0]),
        source='https://link.springer.com/article/10.1007/s00023-020-00906-4',
        note='Tiny fidelity overshoots below 3e-9 are retained in frozen numerical outputs; later metrics clip roundoff to [0,1].')
    (p/'structural-audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    snapshot=p/'posthoc_source_snapshot';snapshot.mkdir(exist_ok=True)
    for f in [Path(__file__),Path('quantum_world/channels.py')]:(snapshot/f.name).write_bytes(f.read_bytes())
    print(json.dumps(dict(verified_runs=36,conditional_eb_indices=[r['entanglement_breaking_index'] for r in certificates],
        inferred_eb_time_range=[min(r['entanglement_breaking_time'] for r in certificates),max(r['entanglement_breaking_time'] for r in certificates)])))


if __name__=='__main__':main()
