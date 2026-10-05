"""Plot selector feasibility versus compiled logical cost; no device claims."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(source,output):
    evidence=json.loads(source.read_text());assert evidence['status']=='audited_constrained_selection'
    names=['all/X','all/XY','feasible/X','feasible/XY'];colors=['#77858e','#b48252','#765b8e','#24664e']
    rows=[[q for s in evidence['seeds'] for q in s['quantum'] if q['initial']+'/'+q['mixer']==name] for name in names]
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,key,title,label in [(axes[0],'feasible_probability','Valid four-feature probability','Probability'),
        (axes[1],'cx','Feasible preparation adds logical cost','CX gates, all-to-all compilation')]:
        values=[[q[key] if key!='cx' else q['logical_gate_counts'].get('cx',0) for q in part] for part in rows]
        means=np.array([np.mean(v) for v in values]);low=np.array([min(v) for v in values]);high=np.array([max(v) for v in values])
        ax.bar(np.arange(4),means,color=colors,width=.65)
        ax.errorbar(np.arange(4),means,yerr=[means-low,high-means],fmt='none',ecolor='#26343d',capsize=3,lw=1)
        ax.set(title=title,ylabel=label,xticks=np.arange(4),xticklabels=['All / X','All / XY','Feasible / X','Feasible / XY'])
        ax.tick_params(axis='x',labelsize=9);ax.set_xlabel('Initialization / mixer');ax.grid(axis='y',alpha=.12);ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
        for i,value in enumerate(means):ax.annotate(f'{value:.1%}' if key!='cx' else f'{value:.0f}',(i,high[i]),xytext=(0,5),textcoords='offset points',ha='center',fontsize=9)
    axes[0].set_ylim(0,1.12);axes[0].yaxis.set_major_formatter(PercentFormatter(1));axes[1].set_ylim(0,370)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    output.with_suffix('.json').write_text(json.dumps(dict(source_sha256=sha(source),plot_recipe_sha256=sha(Path(__file__)),
        figure_sha256=sha(output),caption='Six fixed 256/256 training-period sampling conditions. Bars average them; whiskers span conditions, not confidence intervals. Same objective and 40-call/512-draw caps. Generic feasible-state preparation contributes 247 CX gates in this compiler; not an optimal dedicated Dicke circuit or device runtime. Guaranteed ideal feasibility does not establish useful feature selection; see matched classical controls in the report.'),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=Path('docs/results/constrained-selection.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/constrained-selection.png'))
    args=parser.parse_args();plot(args.summary,args.output)
