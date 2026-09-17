"""Post-plot influence diagnostic, without exclusions or model changes."""
import json
import os
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from phase2_core import agreement_metrics
from phase1_prepare import table
from phase1_epochs import digest

BASE=Path(__file__).resolve().parents[1]


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    out=BASE/'results/phase2_diagnostics_001';out.mkdir(exist_ok=False)
    figs=BASE/'figures/phase2_diagnostics_001';figs.mkdir(exist_ok=False)
    halves=pd.read_csv(BASE/'results/phase2_measurements_001/half_scores.csv')
    selected=halves[(halves.selected_index)&(halves.cohort_label=='HA')&(halves.variant=='hp01_avg20')&(halves.sampling=='all_accepted')].dropna(subset=['half_a_uv','half_b_uv'])
    rows=[];summaries=[]
    for (split,condition),ff in selected.groupby(['split','condition']):
        xy=ff[['half_a_uv','half_b_uv']].to_numpy()
        original=float(agreement_metrics(xy)['icc_a1'])
        loo=[]
        for i,r in enumerate(ff.itertuples()):
            icc=float(agreement_metrics(np.delete(xy,i,axis=0))['icc_a1']);loo.append(icc)
            rows.append(dict(split=split,condition=condition,omitted_candidate_id=r.participant_id,
                omitted_recording_id=r.recording_id,icc_a1_without_one=icc,original_icc_a1=original,
                diagnostic_scope='post_plot_influence_diagnostic_no_exclusion_or_refit'))
        summaries.append(dict(split=split,condition=condition,n=len(ff),original_icc_a1=original,
            leave_one_out_min=float(min(loo)),leave_one_out_max=float(max(loo)),max_absolute_change=float(max(abs(np.array(loo)-original)))))
    table(out/'leave_one_candidate_out.csv',rows)
    table(out/'influence_summary.csv',summaries)
    archpath=BASE/'results/phase2_archival_001/summary.json';arch=json.loads(archpath.read_text())
    if arch['status']=='exploratory_completed':
        fig,axs=plt.subplots(1,2,figsize=(10,4.2),gridspec_kw={'width_ratios':[1.5,1]})
        labels=['Mean','Age + use','EEG','Age + use\n+ EEG']
        vals=[r['MAE_percentage_points'] for r in arch['models']]
        axs[0].bar(labels,vals,color=['.6','C0','C2','C1'])
        for i,v in enumerate(vals):axs[0].text(i,v+.25,f'{v:.2f}',ha='center',fontsize=9)
        axs[0].set_ylim(0,max(vals)*1.15)
        axs[0].set(ylabel='MUSS MAE (percentage points)',title=f'Archival-label feasibility\n{arch["complete_HA_candidates"]} HA candidate index records')
        delta=arch['paired_MAE_delta_percentage_points'];lo,hi=arch['paired_MAE_delta_conditional_bootstrap_ci']
        axs[1].plot([lo,hi],[0,0],color='C1',lw=2);axs[1].plot(delta,0,'o',color='C1',ms=7)
        axs[1].axvline(0,color='k',lw=.8);axs[1].set_yticks([])
        axs[1].set_ylim(-.8,.8)
        axs[1].set(xlabel='MAE: age + use + EEG minus age + use\nNegative values indicate improvement',
            title='Paired change in error\n95% conditional interval')
        axs[1].text(.5,.25,f'{delta:+.3f} [{lo:+.3f}, {hi:+.3f}]',ha='center',transform=axs[1].transAxes,fontsize=10)
        fig.text(.5,.01,'Interval resamples candidate-level fixed OOF losses; it does not include model-retraining uncertainty.',ha='center',fontsize=9)
        fig.tight_layout(rect=[0,.06,1,1])
        for ext in ['png','pdf']:fig.savefig(figs/('archival_feasibility.'+ext),dpi=170,bbox_inches='tight')
        plt.close(fig)
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],purpose='post_plot_influence_diagnostic_without_exclusions_or_model_changes',
        analysis_config_unchanged=True,influence=summaries,archival_figure_replaces_clipped_title_only=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));shutil.copy2(Path(__file__),out/'code_snapshot.py')
    table(out/'artifact_checksums.csv',[dict(file=str(p.relative_to(BASE)),sha256=digest(p)) for root in [out,figs] for p in sorted(root.iterdir()) if p.is_file()])
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
