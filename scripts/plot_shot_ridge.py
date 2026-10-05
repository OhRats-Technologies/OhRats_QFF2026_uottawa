"""Show every fixed noise replicate and its matched ideal/classical references."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(source,output):
    r=json.loads(source.read_text());assert r['status']=='audited_landmark_shot_ridge_model'
    fig,axes=plt.subplots(1,len(r['seeds']),figsize=(10.4,3.9),sharey=True,layout='constrained')
    for ax,cohort in zip(axes,r['seeds']):
        rows=cohort['rows'];get=lambda name:next(v['metric']['average_precision'] for v in rows if v['predictor']==name)
        ideal=get('ZZ/ideal/16');ax.plot(0,ideal,'o',color='#315d86',label='Exact ZZ-16')
        for x,shots in enumerate(r['plan']['shots'],1):
            values=np.array([v['metric']['average_precision'] for v in rows if v.get('shots')==shots]);mean=values.mean()
            ax.scatter(x+np.linspace(-.1,.1,len(values)),values,s=28,color='#b48252',label='Noise replicates' if x==1 else None)
            ax.errorbar(x,mean,yerr=[[mean-values.min()],[values.max()-mean]],fmt='D',markersize=5,color='#b48252',capsize=4,label='Mean / range' if x==1 else None)
        ax.axhline(get('rbf/ideal/16'),ls='--',lw=1.4,color='#24664e',label='Exact RBF-16')
        ax.axhline(ideal-.05,ls=':',lw=1,color='#89929a',label='Ideal ZZ − .05')
        ax.set(title=f'Cohort seed {cohort["seed"]}',xticks=[0,1,2],xticklabels=['Ideal','512','4,096'],xlabel='Modeled shots / pair',ylim=(0,.65))
        ax.grid(axis='y',alpha=.12);ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel('Average precision');axes[-1].legend(frameon=False,fontsize=8,loc='lower right')
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    output.with_suffix('.json').write_text(json.dumps(dict(source_sha256=sha(source),plot_recipe_sha256=sha(Path(__file__)),figure_sha256=sha(output),
        caption='Three dependent training-period samples, each with three fixed independent Binomial noise replicates at each shot count. All points shown; bars are ranges, not confidence intervals. Exact RBF shares labels, inputs and landmark indices. Reference threshold is descriptive per-cohort ideal minus .05; the declared gate averages noise replicates. No Qiskit sampler/device execution, model tuning or final access.'),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=Path('docs/results/landmark-shot-ridge.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/landmark-shot-ridge.png'))
    args=parser.parse_args();plot(args.summary,args.output)
