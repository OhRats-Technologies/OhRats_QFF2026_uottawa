"""Audit fresh controls and conditional rate intervals; create report figures."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def verified(path,count):
    records=json.loads((path/'results.json').read_text());manifest=json.loads((path/'manifest.json').read_text())
    assert len(records)==json.loads((path/'completion.json').read_text())['runs']==count
    assert hashlib.sha256((path/'protocol.json').read_bytes()).hexdigest()==manifest['protocol_sha256']
    for source,sha in manifest['sources'].items():assert hashlib.sha256((path/'source_snapshot'/Path(source).name).read_bytes()).hexdigest()==sha
    return records


def main():
    root=Path('artifacts');out=root/'quantum-world-sprint-20261003'
    p=root/'quantum-world-control-confirmation-20261003';control=verified(p,23)
    reproduction=json.loads((p/'reproductions.json').read_text());assert len(reproduction)==10
    assert max(r['max_fidelity_discrepancy'] for r in reproduction)==0.
    q=root/'quantum-world-noise-rate-audit-v2-20261003';rates=verified(q,6)
    for r in rates:assert len(r['bootstrap_replicates'])==200
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    fig,ax=plt.subplots(figsize=(7.2,3.7));seeds=list(range(7511,7521))
    for kind,color,label in [('generator','#176f68','Frozen generator'),('transferred_generator_encoder','#7b739f','Same encoder, periodic regression')]:
        values=[next(r['mean_fidelity'] for r in control if r['kind']==kind and r['seed']==seed) for seed in seeds]
        ax.plot(range(10),values,'o-',color=color,lw=1.4,label=label)
    ax.set_xticks(range(10),seeds,rotation=35);ax.set_xlabel('Training seed; 32 shared fresh control tasks each')
    ax.set_ylabel('Exact target-state fidelity');ax.set_ylim(0,1.08);ax.grid(axis='y',alpha=.15)
    ax.set_title('A successful demo is not a reliable training procedure',loc='left',fontsize=11)
    handles,labels=ax.get_legend_handles_labels();fig.legend(handles,labels,ncol=2,frameon=False,loc='lower center',bbox_to_anchor=(.5,-.01))
    fig.tight_layout(rect=(0,.09,1,1));fig.savefig(out/'control-all-seeds.png',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.2,4.2))
    for i,r in enumerate(rates):
        point=r['likelihood_rates'][0];low,high=r['pointwise_parametric_bootstrap_95'][0]
        ax.errorbar(point,i,xerr=[[point-low],[high-point]],fmt='o',capsize=3,color='#176f68')
        ax.scatter(r['sgd_rates'][0],i,marker='x',color='#b6503f',s=30)
    threshold=np.log(5)/1.5
    ax.axvline(threshold,color='#7b739f',ls='--',label='Index 3/4 boundary');ax.axvline(1.1,color='black',ls=':',label='Simulation rate')
    ax.set_yticks(range(6),[f"{r['seed']} / {r['n']} transitions" for r in rates]);ax.invert_yaxis()
    ax.set_xlabel('Depolarization rate; green: likelihood + pointwise bootstrap, red: SGD')
    ax.set_title('Near-perfect prediction can leave the discrete index uncertain',loc='left',fontsize=11)
    ax.grid(axis='x',alpha=.15);handles,labels=ax.get_legend_handles_labels()
    fig.legend(handles,labels,ncol=2,frameon=False,loc='lower center',bbox_to_anchor=(.5,-.01))
    fig.tight_layout(rect=(0,.09,1,1));fig.savefig(out/'noise-index-uncertainty.png',bbox_inches='tight');plt.close(fig)
    (out/'followup-audit.json').write_text(json.dumps(dict(reproduced_seeds=10,max_reproduction_discrepancy=0,
        fresh_control_comparisons=23,rate_fits=6,parametric_bootstrap_fits=1200,
        index_intervals_spanning_3_and_4=sum(r['conditional_index_interval']==[3,4] for r in rates),
        summary={kind:float(np.mean([r['mean_fidelity'] for r in control if r['kind']==kind])) for kind in sorted({r['kind'] for r in control})}),indent=2)+'\n')
    print('Verified 23 control comparisons, ten reproductions, six rate fits and 1200 bootstrap fits.')


if __name__=='__main__':main()
