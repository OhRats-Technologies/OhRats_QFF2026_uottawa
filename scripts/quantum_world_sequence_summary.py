"""Audit fixed triplet studies and summarize every seed without selection."""
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.quantum_world_report import paired


def verified(path,count):
    protocol=json.loads((path/'protocol.json').read_text());manifest=json.loads((path/'manifest.json').read_text())
    records=json.loads((path/'results.json').read_text());completion=json.loads((path/'completion.json').read_text())
    assert len(records)==completion['runs']==count
    assert hashlib.sha256((path/'protocol.json').read_bytes()).hexdigest()==manifest['protocol_sha256']
    for name,sha in manifest['sources'].items():assert hashlib.sha256((path/'source_snapshot'/Path(name).name).read_bytes()).hexdigest()==sha
    with np.load(path/'observed-triplets.npz') as data:
        sha=hashlib.sha256(data['observed'].tobytes()+data['gate'].tobytes()+data['duration'].tobytes()).hexdigest()
    assert all(r['data_sha256']==sha for r in records) and completion['data_sha256']==sha
    for record in records:
        assert record['training']['reconstruction_loss'] is False
        assert np.isfinite(record['metrics']['rollout']['64']['mean_projected_fidelity'])
    return protocol,records,sha


def main():
    root=Path('artifacts');out=root/'quantum-world-sprint-20261003';summaries=[];studies=[]
    for name,count in [('screen',16),('normalized',8),('confirmation',20)]:
        path=root/f'quantum-world-sequence-{name}-20261003';protocol,records,data_hash=verified(path,count)
        studies.append(dict(stage=name,runs=count,train_seed=protocol['train_seed'],probe_seed=protocol['probe_seed'],data_sha256=data_hash,
            training_seconds=sum(r['training']['seconds'] for r in records)))
        for kind in sorted({r['kind'] for r in records}):
            for weight in (0.,1.):
                group=sorted([r for r in records if r['kind']==kind and r['consistency']==weight],key=lambda r:r['seed'])
                vals=[r['metrics']['rollout']['64']['mean_projected_fidelity'] for r in group]
                summaries.append(dict(stage=name,kind=kind,consistency=weight,seeds=[r['seed'] for r in group],rollout=vals,
                    mean_rollout=float(np.mean(vals)),seeds_above_095=sum(v>.95 for v in vals),
                    mean_angle=float(np.mean([r['metrics']['unseen_angles']['mean_projected_fidelity'] for r in group])),
                    mean_readout=float(np.mean([r['metrics']['readout_ceiling']['mean_projected_fidelity'] for r in group]))))
    assert studies[0]['data_sha256']==studies[1]['data_sha256']!=studies[2]['data_sha256']
    original=json.loads((root/'quantum-world-jepa-confirmation-20261003/protocol.json').read_text())
    assert studies[2]['train_seed']!=original['train_seed'] and studies[2]['probe_seed']!=original['probe_seed']
    rows=[r for r in summaries if r['stage']=='confirmation'];assert len(rows)==2
    zero,one=sorted(rows,key=lambda r:r['consistency']);assert zero['seeds']==one['seeds']
    comparisons={}
    for metric in ('rollout',):comparisons[metric]=paired(one[metric],zero[metric],seed=118001)
    caveat='Fresh paired diagnostic after failed screen advancement gate; one prespecified rollout contrast; no general reliability or novelty claim.'
    (out/'sequence-audit.json').write_text(json.dumps(dict(studies=studies,summaries=summaries,comparisons=comparisons,caveat=caveat),indent=2)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(8.0,3.8))
    for r,color,label in [(zero,'#7b739f','Teacher forcing'),(one,'#176f68','Normalized two-step mixture')]:
        ax.plot(r['seeds'],r['rollout'],'o-',color=color,label=label,lw=1.5)
    ax.axhline(.95,color='#a5adab',ls=':',lw=1);ax.set_ylim(.2,1.025);ax.set_xticks(zero['seeds']);ax.tick_params(axis='x',rotation=45)
    ax.set_xlabel('Fresh paired seed');ax.set_ylabel('64-step state fidelity');ax.set_title('Trajectory consistency does not automatically repair coordinates',loc='left',fontsize=11)
    ax.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.37),ncol=2,fontsize=9)
    ax.grid(axis='y',alpha=.15);fig.tight_layout()
    fig.savefig(out/'sequence-confirmation.png',dpi=200,bbox_inches='tight');plt.close(fig)
    print(json.dumps(dict(studies=studies,confirmation=rows,comparisons=comparisons),indent=2))


if __name__=='__main__':main()
