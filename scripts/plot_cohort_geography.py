"""Plot descriptive latitude-band exclusions in two fixed training cohorts."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(source,output):
    evidence=json.loads(source.read_text());assert evidence['status']=='audited_training_cohort_geography'
    minimum=evidence['plan']['minimum_plot_denominator'];fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    for ax,(name,stage) in zip(axes,evidence['stages'].items()):
        bins=stage['latitude_bins'];labels=[]
        for i,row in enumerate(bins):
            labels.append(f"<{row['upper']}" if i==0 else f"≥{row['lower_inclusive']}" if i==len(bins)-1 else f"{row['lower_inclusive']}–{row['upper']}")
        for target,color,text in [('0','#24664e','<10 ha'),('1','#b48252','≥10 ha')]:
            fractions=[row['by_target'][target]['excluded_fraction'] if row['by_target'][target]['before_rows']>=minimum else float('nan') for row in bins]
            ax.plot(range(len(bins)),fractions,'o-',lw=1.4,markersize=4,color=color,
                label=f"{text} · n={stage['by_target'][target]['before_rows']:,}")
        ax.set_xticks(range(len(bins)),labels,rotation=25,ha='right')
        ax.set(title='Weather eligibility' if name=='weather' else 'Woodland eligibility',
            xlabel='Reported latitude band (°N)',ylabel='Excluded within each recorded-size class',ylim=(-.015,1.025))
        ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(frameon=False,fontsize=9)
        ax.set_axisbelow(True);ax.grid(axis='y',alpha=.12);ax.spines[['top','right']].set_visible(False)
    output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(output,dpi=180,bbox_inches='tight');plt.close(fig)
    output.with_suffix('.json').write_text(json.dumps(dict(source_sha256=sha(source),plot_recipe_sha256=sha(Path(__file__)),
        figure_sha256=sha(output),
        caption=f'Training 1988–2018 only. Left denominator: eligible NFDB incidents; right: weather-matched incidents. Markers show observed class-specific exclusion fractions by approximate reported latitude, with connecting lines as guides. Ratios with denominator <{minimum} are omitted from this plot but all counts remain in evidence. No confidence intervals, station-cause inference, geographic accuracy or province-completeness claim; no model fitted.'),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=Path('docs/data/cohort_geography.json'))
    parser.add_argument('--output',type=Path,default=Path('docs/figures/cohort-geography.png'))
    args=parser.parse_args();plot(args.summary,args.output)
