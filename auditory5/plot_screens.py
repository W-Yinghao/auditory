"""Aggregate scientific figures from an explicit screening output, Slurm only."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,digest,write_json


def main():
    require_slurm();p=argparse.ArgumentParser();p.add_argument('--screen-run',required=True);a=p.parse_args()
    folder=ROOT/'results/auditory5_v1'/a.screen_run;source=folder/'screen_metrics.csv'
    frame=pd.read_csv(source);required=['route','mode','statistic','estimate','ci_lower','ci_upper','n_candidates','units','run']
    if not set(required)<=set(frame):raise ValueError('Aggregate screening table schema mismatch')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
    titles={'A':'A: response repeatability','B':'B: conditional history gain',
            'C':'C: sensor complementarity','D':'D: clinical increment','E':'E0: within-record decoding'}
    thresholds={'A':.05,'B':.01,'C':.01,'D':.5}
    colors={'L0':'#6b7280','R_SUP':'#2563eb','R_SIM':'#15803d','R_RAND':'#ca8a04'}
    for ax,route in zip(axes.flat,list('ABCDE')):
        rows=frame[frame.route.eq(route)].copy()
        if route=='C':rows=rows[~rows.statistic.astype(str).str.endswith('_raw')]
        ax.set_title(titles[route],loc='left',fontweight='bold')
        if rows.empty:
            ax.text(.5,.5,'No complete estimable result',ha='center',va='center',transform=ax.transAxes);ax.set_axis_off();continue
        values=rows[['estimate','ci_lower','ci_upper']].to_numpy(float)
        if not np.isfinite(values).all():raise ValueError('Incomplete numerical values cannot become a zero-effect plot')
        labels=[]
        for i,row in enumerate(rows.to_dict('records')):
            color=colors.get(row['mode'],'#7c3aed')
            ax.plot([row['ci_lower'],row['ci_upper']],[i,i],color=color,lw=1.8)
            ax.plot(row['estimate'],i,'o',color=color,markersize=5)
            label=str(row['mode'])
            if route=='C':label+=' / '+('MLP32' if 'mlp32' in row['statistic'] else 'linear')
            if route=='E':label='Pure tone' if row['statistic'].endswith('puretone') else 'bapa'
            labels.append(label+' (n='+str(int(row['n_candidates']))+')')
        ax.axvline(0,color='#475569',lw=.8)
        if route in thresholds:ax.axvline(thresholds[route],color='#9ca3af',ls='--',lw=.8)
        unit={'A':'Cosine difference','B':'bits/trial','C':'bits/trial','D':'MUSS source points','E':'bits/trial'}[route]
        ax.set_yticks(np.arange(len(rows)),labels,fontsize=8);ax.invert_yaxis();ax.set_xlabel(unit)
        ax.grid(axis='x',alpha=.18)
    ax=axes.flat[-1];ax.set_axis_off()
    ax.text(0,.98,'Exploratory first pass\n\nPoints: prespecified readout estimates\nBars: 95% fixed-OOF bootstrap intervals\nDashed lines: screening thresholds\n\nR_SIM is the primary representation.\nA lacks history-balanced support.\nC linear output does not replace MLP controls.\nE0 does not estimate child-level transfer.\nNumerical failures are not zero effects.\nThese cohorts have already been explored.',va='top',fontsize=8.5,linespacing=1.4)
    fig.suptitle('Auditory EEG: first-pass estimates and uncertainty',fontsize=14)
    for extension in ['png','pdf']:
        path=folder/('screen_estimates.'+extension)
        if path.exists():raise FileExistsError(path)
        fig.savefig(path,dpi=300)
    plt.close(fig)
    write_json(folder/'figure_provenance.json',{'source':source.name,'source_sha256':digest(source),
        'code_sha256':digest(Path(__file__)),'scope':'aggregate-only; fixed OOF intervals, not workflow refitting',
        'outputs':{name:digest(folder/name) for name in ['screen_estimates.png','screen_estimates.pdf']}})
    print(json.dumps({'figure_directory':str(folder)}))

if __name__=='__main__':main()
