"""Trial-efficiency assay using the already frozen HA amplitude definition."""
import json,os,shutil
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from phase2_core import agreement_metrics
from phase1_prepare import table
BASE=Path(__file__).resolve().parents[1]
def main():
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
    cfgpath=BASE/'configs/phase3_trial_budget_v1.json';cfg=json.loads(cfgpath.read_text())
    out=BASE/'results/phase3_trial_budget_001';out.mkdir(exist_ok=False)
    f=pd.read_csv(BASE/'results/phase2_measurements_001/features.csv')
    f=f[(f.cohort_label=='HA')&(f.variant=='hp01_avg20')&(f.condition=='code1')&(f.measurement_status=='measured')&(f.selected_index.astype(str).str.lower()=='true')]
    assert f.participant_id.nunique()==len(f)
    halves=[];available=[]
    for r in f.itertuples():
        with np.load(BASE/'results/phase1_epochs_001'/r.recording_id/'epochs.npz',allow_pickle=False) as d:
            roi=d['roi_uv'][:,0,:];t=d['times_s'];keep=d['accepted'][:,0]&(d['codes']==1);block=d['blocks']
            score=roi[:,(t>=.05-1e-10)&(t<.25-1e-10)].mean(axis=1)
        a=score[keep&(block%2==0)];b=score[keep&(block%2==1)];halves.append((a,b))
        available.append(dict(participant_id=r.participant_id,recording_id=r.recording_id,half_a_trials=len(a),half_b_trials=len(b)))
    table(out/'candidate_trial_support.csv',available);rng=np.random.default_rng(cfg['seed']);rows=[];draws=[]
    common=max(cfg['common_support_budgets'])
    for scope in ['budget_specific','common_through_160']:
        for n in cfg['trials_per_half']:
            if scope=='common_through_160' and n>common:continue
            choose=[h for h in halves if min(len(h[0]),len(h[1]))>=max(n,common if scope=='common_through_160' else n)]
            if len(choose)<8:rows.append(dict(scope=scope,trials_per_half=n,n_candidates=len(choose),status='insufficient_candidates'));continue
            vals=[]
            for rep in range(cfg['trial_resampling_repetitions']):
                a=np.array([rng.choice(h[0],n,replace=False).mean() for h in choose]);b=np.array([rng.choice(h[1],n,replace=False).mean() for h in choose])
                val=float(agreement_metrics(np.column_stack([a,b]))['icc_a1']);vals.append(val);draws.append(dict(scope=scope,trials_per_half=n,repeat=rep,n_candidates=len(choose),icc_a1=val))
            rows.append(dict(scope=scope,trials_per_half=n,total_selected_trials=2*n,n_candidates=len(choose),status='measured',median_icc_a1=float(np.median(vals)),trial_selection_q025=float(np.quantile(vals,.025)),trial_selection_q975=float(np.quantile(vals,.975))))
    table(out/'summary.csv',rows);table(out/'resampling_draws.csv',draws)
    fig,ax=plt.subplots(figsize=(6,4),layout='constrained')
    for scope,color in [('budget_specific','#355c7d'),('common_through_160','#a15a3a')]:
        rr=[r for r in rows if r['scope']==scope and r['status']=='measured'];x=[r['trials_per_half'] for r in rr];y=[r['median_icc_a1'] for r in rr]
        ax.plot(x,y,'o-',label=scope.replace('_',' '),color=color);ax.fill_between(x,[r['trial_selection_q025'] for r in rr],[r['trial_selection_q975'] for r in rr],alpha=.13,color=color)
        if scope=='budget_specific':
            for xx,yy,r in zip(x,y,rr):ax.annotate(f"n={r['n_candidates']}",(xx,yy),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
    ax.set(xscale='log',xticks=cfg['trials_per_half'],xticklabels=cfg['trials_per_half'],xlabel='Code 1 trials per temporal half (total = twice this)',ylabel='Absolute-agreement ICC(A,1)',title='HA fixed amplitude: trial budget and within-record agreement')
    ax.legend(fontsize=8);fig.savefig(out/'trial_budget.pdf');fig.savefig(out/'trial_budget.png',dpi=180);plt.close(fig)
    for p in [Path(__file__),cfgpath]:shutil.copy2(p,out/p.name)
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],candidate_indices=len(f),rows=rows,interval_scope=cfg['uncertainty']);(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
