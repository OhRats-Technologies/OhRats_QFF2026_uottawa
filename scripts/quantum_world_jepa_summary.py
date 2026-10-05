"""Verify completed latent evidence and regenerate two report figures."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    root=Path('artifacts');out=root/'quantum-world-sprint-20261003'
    expected={'jepa-confirmation':60,'jepa-physical-readout-smoke':4,'control-smoke':3,'transferred-linear':10,'algebra-exploration':8}
    audit={}
    for short,count in expected.items():
        p=root/f'quantum-world-{short}-20261003'
        records=json.loads((p/'results.json').read_text());completion=json.loads((p/'completion.json').read_text())
        manifest=json.loads((p/'manifest.json').read_text())
        assert len(records)==completion['runs']==count,short
        sha=hashlib.sha256((p/'protocol.json').read_bytes()).hexdigest()
        assert sha==manifest['protocol_sha256'],short
        for source,h in manifest['sources'].items():
            assert hashlib.sha256((p/'source_snapshot'/Path(source).name).read_bytes()).hexdigest()==h,source
        for source,h in manifest.get('inputs',{}).items():assert hashlib.sha256(Path(source).read_bytes()).hexdigest()==h,source
        audit[short]=dict(runs=count,protocol_sha256=sha,snapshots_verified=True)
    records=json.loads((root/'quantum-world-jepa-confirmation-20261003/results.json').read_text())
    assert len({(r['seed'],r['kind'],r['invariance']) for r in records})==60
    labels={'direct':'Direct','gaussian':'Conditional flow','latent_generator':'Generator'}
    colors={'direct':'#b6503f','gaussian':'#7b739f','latent_generator':'#176f68'}
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    fig,axes=plt.subplots(1,2,figsize=(10,4));summary=[];times=[1,4,16,32,64];index=0
    for kind in labels:
        for inv in (0.,1.):
            group=[r for r in records if r['kind']==kind and r['invariance']==inv];assert len(group)==10
            for r in group:
                for key in ('readout_ceiling','one_step','unseen_angles'):
                    assert r['metrics'][key]['raw_valid_fraction']==1.
                    assert r['metrics'][key]['projection_frobenius_mean']<1e-10
            values=np.array([[r['metrics']['rollout'][str(t)]['mean_projected_fidelity'] for t in times] for r in group])
            axes[0].plot(times,values.mean(axis=0),'-' if inv else '--',color=colors[kind],lw=1.7,label=labels[kind]+(' + agreement' if inv else ''))
            axes[1].scatter(index+np.linspace(-.12,.12,10),values[:,-1],color=colors[kind],s=22,alpha=.7,marker='o' if inv else 'x')
            axes[1].plot([index-.18,index+.18],[values[:,-1].mean()]*2,color='black',lw=1.6)
            summary.append(dict(kind=kind,invariance=inv,mean_roll64=float(values[:,-1].mean()),min_roll64=float(values[:,-1].min()),max_roll64=float(values[:,-1].max()),
                mean_angle=float(np.mean([r['metrics']['unseen_angles']['mean_projected_fidelity'] for r in group])),successes=int((values[:,-1]>.95).sum())))
            index+=1
    for ax in axes:ax.set_ylim(0,1.03);ax.grid(axis='y',alpha=.15);ax.set_ylabel('True-state fidelity')
    axes[0].set_xlabel('Unseen rollout steps');axes[0].set_title('Mean across ten paired seeds',loc='left',fontsize=11)
    axes[1].set_xticks(range(6),['Direct','Direct\n+ agreement','Flow','Flow\n+ agreement','Generator','Generator\n+ agreement'],rotation=35,ha='right')
    axes[1].set_title('Every seed at step 64',loc='left',fontsize=11)
    handles,legend_labels=axes[0].get_legend_handles_labels();fig.legend(handles,legend_labels,ncol=3,loc='lower center',frameon=False,bbox_to_anchor=(.5,-.01))
    fig.tight_layout(rect=(0,.14,1,1));fig.savefig(out/'jepa-confirmation.png',bbox_inches='tight');plt.close(fig)
    control=json.loads((root/'quantum-world-control-smoke-20261003/results.json').read_text())
    fig,ax=plt.subplots(figsize=(6.8,3.8));positions=np.arange(3)
    true=[r['mean_fidelity'] for r in control];prediction=[r['predicted_target_metrics']['mean_projected_fidelity'] if r['predicted_target_metrics'] else np.nan for r in control]
    ax.bar(positions-.16,true,width=.30,color='#176f68',label='Exact post-selection outcome');ax.bar(positions+.16,prediction,width=.30,color='#a3aaa8',label='Model prediction')
    for i,v in enumerate(true):ax.text(i-.16,v+.02,f'{v:.3f}',ha='center',fontsize=9)
    ax.set_xticks(positions,['Direct model','Generator','Exact reference']);ax.set_ylim(0,1.12);ax.set_ylabel('Target-state fidelity')
    ax.set_title('Planning can exploit a model’s errors',loc='left',fontsize=12);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    handles,legend_labels=ax.get_legend_handles_labels();fig.legend(handles,legend_labels,frameon=False,ncol=1,loc='lower center',bbox_to_anchor=(.5,-.02))
    fig.tight_layout(rect=(0,.13,1,1));fig.savefig(out/'control-model-exploitation.png',bbox_inches='tight');plt.close(fig)
    (out/'latent-study-audit.json').write_text(json.dumps(dict(audit=audit,summary=summary),indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(verified_runs=sum(expected.values()),figures=['jepa-confirmation.png','control-model-exploitation.png'])))


if __name__=='__main__':main()
