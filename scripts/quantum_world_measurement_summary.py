"""Verify shot accounting, shared controls, coverage, and readout stress outcomes."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.stats import binomtest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def verified(path,count):
    records=json.loads((path/'results.json').read_text());manifest=json.loads((path/'manifest.json').read_text())
    assert len(records)==json.loads((path/'completion.json').read_text())['comparisons']==count
    assert hashlib.sha256((path/'protocol.json').read_bytes()).hexdigest()==manifest['protocol_sha256']
    for source,sha in manifest['sources'].items():assert hashlib.sha256((path/'source_snapshot'/Path(source).name).read_bytes()).hexdigest()==sha
    return records


def proportion(group,key):
    k=sum(bool(r[key]) for r in group);n=len(group)
    ci=binomtest(k,n).proportion_ci(.95,method='wilson')
    return dict(estimate=k/n,successes=k,trials=n,pointwise_mc_wilson_95=[float(ci.low),float(ci.high)])


def main():
    root=Path('artifacts');out=root/'quantum-world-sprint-20261003'
    p=root/'quantum-world-measurement-confirmation-20261003';measurements=verified(p,7200)
    shots_audit=[]
    for budget in (4096,16384,65536):
        for name in ('design','grouped-design','fixed-time-design'):
            with np.load(p/f'{name}-{budget}.npz') as d:assert d['shots'].sum()==budget
        group=[r for r in measurements if r['budget']==budget]
        for seed in sorted({r['seed'] for r in group}):
            records={r['kind']:r for r in group if r['seed']==seed};assert len(records)==6
            z,bell,single=(records[k] for k in ('focused_z','focused_bell','targeted_single_pauli'))
            assert z['rate']==bell['rate'] and z['interval']==bell['interval'] and z['basis_counts']==bell['basis_counts']
            assert single['basis_counts'][0]==sum(z['basis_counts'][:2])
            for kind in ('random_pauli','grouped_pauli','grouped_fixed_time'):
                with np.load(p/f'{kind}-counts-{budget}-{seed}.npz') as c:
                    if kind=='random_pauli':assert np.all(c['counts']<=np.load(p/f'design-{budget}.npz')['shots'])
                    else:assert c['counts'].sum()==budget
        for kind in sorted({r['kind'] for r in group}):
            a=[r for r in group if r['kind']==kind];assert len(a)==400 and all(r['shots']==budget for r in a)
            shots_audit.append(dict(budget=budget,kind=kind,coverage=proportion(a,'coverage'),
                resolved_correct=proportion(a,'resolved_correct'),resolved_wrong=proportion(a,'resolved_wrong'),
                rate_rmse=float(np.sqrt(np.mean([r['squared_rate_error'] for r in a])))))
    q=root/'quantum-world-readout-stress-v2-20261003';stress=verified(q,3600);stress_audit=[]
    for r in stress:
        if r['kind']=='calibrated':assert sum(r['reference_counts'])+sum(r['probe_counts'])==r['budget']
        else:assert sum(r['raw_counts'])==r['budget']
    for scenario in ('ideal','misspecified'):
        for budget in (16384,65536,262144):
            for kind in ('blind','guarded','calibrated'):
                a=[r for r in stress if r['scenario']==scenario and r['budget']==budget and r['kind']==kind];assert len(a)==200
                stress_audit.append(dict(scenario=scenario,budget=budget,kind=kind,coverage=proportion(a,'coverage'),
                    resolved_correct=proportion(a,'resolved_correct'),resolved_wrong=proportion(a,'resolved_wrong'),withheld=proportion(a,'withheld')))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    fig,ax=plt.subplots(figsize=(7.2,4.1));budgets=[4096,16384,65536]
    styles=[('random_pauli','#b6503f','Independent Paulis'),('grouped_pauli','#a98b50','Grouped Paulis'),
        ('grouped_fixed_time','#7b739f','Grouped, matched time'),('targeted_single_pauli','#648da2','Targeted single Pauli'),('focused_z','#176f68','Focused full basis')]
    for kind,color,label in styles:
        values=[next(r for r in shots_audit if r['kind']==kind and r['budget']==b)['resolved_correct']['estimate'] for b in budgets]
        ax.plot(range(3),values,'o-',color=color,label=label,lw=1.5)
    ax.set_xticks(range(3),['4,096','16,384','65,536']);ax.set_xlabel('Total shots; Bell and separable focused probes are equivalent')
    ax.set_ylabel('Fraction resolving the correct index');ax.set_ylim(0,1.04);ax.grid(axis='y',alpha=.15)
    ax.set_title('Match the measurement to the channel question',loc='left',fontsize=11)
    handles,labels=ax.get_legend_handles_labels();fig.legend(handles,labels,ncol=2,frameon=False,loc='lower center',bbox_to_anchor=(.5,-.035))
    fig.tight_layout(rect=(0,.19,1,1));fig.savefig(out/'measurement-design.png',bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9.7,3.8));budgets=[16384,65536,262144]
    for kind,color,label in [('blind','#b6503f','Blind'),('guarded','#7b739f','Goodness-of-fit guard'),('calibrated','#176f68','Independent calibration')]:
        rows=[next(r for r in stress_audit if r['scenario']=='misspecified' and r['kind']==kind and r['budget']==b) for b in budgets]
        for ax,key in zip(axes,['resolved_wrong','resolved_correct']):ax.plot(range(3),[r[key]['estimate'] for r in rows],'o-',color=color,label=label,lw=1.5)
    for ax in axes:ax.set_xticks(range(3),['16,384','65,536','262,144']);ax.set_xlabel('Total shots');ax.set_ylim(-.02,1.04);ax.grid(axis='y',alpha=.15)
    axes[0].set_ylabel('Fraction confidently resolving an index');axes[0].set_title('Wrong index',loc='left',fontsize=11);axes[1].set_title('Correct index',loc='left',fontsize=11)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,ncol=3,frameon=False,loc='lower center',bbox_to_anchor=(.5,-.01))
    fig.suptitle('More shots cannot fix an incorrect readout model',x=.08,ha='left',fontsize=12)
    fig.tight_layout(rect=(0,.1,1,.95));fig.savefig(out/'readout-model-stress.png',bbox_inches='tight');plt.close(fig)
    (out/'measurement-audit.json').write_text(json.dumps(dict(measurement_comparisons=7200,readout_comparisons=3600,
        independent_replicates_per_measurement_budget_design=400,independent_replicates_per_readout_scenario_budget=200,
        cross_budget='shared seeds; budgets and equivalence controls must not be pooled as independent observations',
        measurements=shots_audit,readout=stress_audit,guard_note='guard coverage refers to underlying interval, not conditional coverage after selective withholding'),indent=2)+'\n')
    print('Verified equal-shot accounting, shared controls, 7200 measurement comparisons and 3600 readout comparisons.')


if __name__=='__main__':main()
