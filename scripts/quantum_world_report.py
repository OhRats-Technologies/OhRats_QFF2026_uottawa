"""Regenerate figures and paired summaries from frozen endpoint evidence."""
from pathlib import Path
import hashlib,json,itertools
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from quantum_world.physics import unitary,pauli_rotation,state_to_pauli

ROOT=Path('artifacts/quantum-world-endpoint-confirmation-20261003')
OUT=Path('artifacts/quantum-world-sprint-20261003')
NAMES={'direct':'Direct MLP','generator':'Skew generator','hamiltonian':'Hamiltonian flow','linear':'Periodic linear'}
COLORS={'direct':'#99919f','generator':'#a387c3','hamiltonian':'#563281','linear':'#db8658'}


def paired(a,b,seed=60134):
    d=np.array(a)-np.array(b);rng=np.random.default_rng(seed)
    boot=d[rng.integers(len(d),size=(10000,len(d)))].mean(axis=1)
    null=np.array([np.mean(d*np.array(sign)) for sign in itertools.product([-1,1],repeat=len(d))])
    return dict(paired_seeds=len(d),differences=d.tolist(),mean_difference=float(d.mean()),
        wins=int((d>0).sum()),pointwise_bootstrap_95=np.quantile(boot,[.025,.975]).tolist(),
        exact_two_sided_sign_flip_p=float(np.mean(np.abs(null)>=abs(d.mean())-1e-12)))


def main():
    OUT.mkdir(exist_ok=True)
    runs=json.loads((ROOT/'final.json').read_text())
    config=json.loads((ROOT/'manifest.json').read_text())['config']
    completion=json.loads((ROOT/'completion.json').read_text())
    assert len(runs)==120 and completion['validation_runs']==144
    assert hashlib.sha256((ROOT/'selection.json').read_bytes()).hexdigest()==completion['selection_sha256']
    summaries=[];comparisons=[]
    for n in config['sizes']:
        for shots in config['shots']:
            by_kind={kind:sorted([r for r in runs if r['n']==n and r['shots']==shots and r['kind']==kind],key=lambda r:r['seed']) for kind in NAMES}
            assert all([r['seed'] for r in group]==config['final_seeds'] for group in by_kind.values())
            for seed in config['final_seeds']:
                assert len({r['data_sha256'] for r in runs if r['n']==n and r['shots']==shots and r['seed']==seed})==1
            for kind,group in by_kind.items():
                summaries.append(dict(n=n,shots=shots,kind=kind,
                    extrapolation=float(np.mean([r['metrics']['unseen_angles']['mean_projected_fidelity'] for r in group])),
                    rollout=float(np.mean([r['metrics']['rollout']['64']['mean_projected_fidelity'] for r in group])),
                    validity=float(np.mean([r['metrics']['rollout']['64']['raw_valid_fraction'] for r in group]))))
            for competitor in ('generator','linear'):
                for metric in ('unseen_angles','rollout'):
                    def extract(group):
                        if metric=='rollout':
                            return [r['metrics']['rollout']['64']['mean_projected_fidelity'] for r in group]
                        return [r['metrics'][metric]['mean_projected_fidelity'] for r in group]
                    comparisons.append(dict(n=n,shots=shots,competitor=competitor,metric=metric,
                        **paired(extract(by_kind['hamiltonian']),extract(by_kind[competitor]))))
    (OUT/'endpoint-summary.json').write_text(json.dumps(dict(summaries=summaries,comparisons=comparisons,
        caveat='Five independent paired seeds; pointwise bootstrap intervals, no multiplicity adjustment. All five wins alone have two-sided exact p=.0625.'),indent=2)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#322a3e','text.color':'#322a3e','axes.edgecolor':'#d3ced8','xtick.color':'#776c82','ytick.color':'#776c82','figure.facecolor':'#fbfafc','axes.facecolor':'#fbfafc'})
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
    for ax,metric,title in zip(axes,['unseen_angles','rollout'],['Unseen rotation angles','After 64 gates']):
        for kind in NAMES:
            means=[];low=[];high=[]
            for n in config['sizes']:
                group=[r for r in runs if r['n']==n and r['shots']==128 and r['kind']==kind]
                vals=[r['metrics']['unseen_angles']['mean_projected_fidelity'] if metric=='unseen_angles' else r['metrics']['rollout']['64']['mean_projected_fidelity'] for r in group]
                means.append(np.mean(vals));low.append(min(vals));high.append(max(vals))
            ax.plot(config['sizes'],means,'o-',color=COLORS[kind],label=NAMES[kind],lw=2,markersize=4)
            ax.fill_between(config['sizes'],low,high,color=COLORS[kind],alpha=.09)
        ax.set_xscale('log',base=2);ax.set_xticks(config['sizes'],[str(n) for n in config['sizes']])
        ax.set_ylim(.2,1.02);ax.set_title(title,loc='left',fontsize=14);ax.set_xlabel('Training transitions')
        ax.set_ylabel('Projected state fidelity');ax.grid(axis='y',alpha=.15)
    handles,labels=axes[1].get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,loc='lower center',bbox_to_anchor=(.5,-.08),ncol=4,fontsize=9)
    fig.suptitle('Known prepared inputs · simulated 128 shots per observable',fontsize=12)
    fig.savefig(OUT/'endpoint-learning-curves.png',dpi=200,bbox_inches='tight');plt.close(fig)
    psi=np.eye(4,dtype=complex)[0];other=unitary(0)@psi
    a=state_to_pauli(psi);b=state_to_pauli(other);tau=np.linspace(0,1,201)
    chord=[np.linalg.norm(((1-t)*a+t*b)-((1-t)*b+t*a)) for t in tau]
    physical=[np.linalg.norm(pauli_rotation(unitary(0,float(t)))@(a-b)) for t in tau]
    fig,ax=plt.subplots(figsize=(7.5,4.2),layout='constrained')
    ax.plot(tau,chord,color=COLORS['linear'],lw=2.5,label='Straight interpolation')
    ax.plot(tau,physical,color=COLORS['hamiltonian'],lw=2.5,label='Continuous unitary path')
    ax.axvline(.5,color='#aaa1b1',ls=':',lw=1)
    ax.set_xlabel('Flow time');ax.set_ylabel('Distance between two encoded states')
    ax.set_title('An involution exchanges two states; their chords collide',loc='left',fontsize=12)
    ax.legend(frameon=False);ax.grid(axis='y',alpha=.15)
    fig.savefig(OUT/'midpoint-collision.png',dpi=200);plt.close(fig)
    print('Verified paired data, frozen selections, counts; regenerated summaries and two figures.')


if __name__=='__main__':main()
