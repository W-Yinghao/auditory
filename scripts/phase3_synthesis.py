"""Scientific feasibility synthesis with explicit record/candidate denominators."""
import json,os,shutil
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from phase1_prepare import readcsv,table
from phase1_epochs import digest
BASE=Path(__file__).resolve().parents[1]
def distribution(values):
    z=np.asarray([v for v in values if v is not None and np.isfinite(v)],float)
    return dict(n=len(z),median=float(np.median(z)) if len(z) else None,q25=float(np.quantile(z,.25)) if len(z) else None,q75=float(np.quantile(z,.75)) if len(z) else None)
def main():
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_synthesis_001';out.mkdir(exist_ok=False)
    private=BASE/'private/phase3_synthesis_001';private.mkdir(mode=0o700,exist_ok=False)
    figdir=BASE/'figures/phase3';figdir.mkdir(parents=True,exist_ok=False)
    ha=json.loads((BASE/'results/phase3_ha_science_001/summary.json').read_text());sens=json.loads((BASE/'results/phase3_ha_sensitivity_001/summary.json').read_text())
    source=readcsv(BASE/'results/phase3_ci_sources_001/source_manifest.csv');labels={r['container_id']:r for r in readcsv(BASE/'results/phase3_ci_linkage_005/canonical_source_labels.csv')}
    dates={r['container_id']:r['record_time'] for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv')}
    measurements=BASE/'results/phase3_ci_measurements_001'
    ci=json.loads((measurements/'summary.json').read_text());dec=pd.read_csv(measurements/'decoder_scores.csv');half=pd.read_csv(measurements/'half_scores.csv')
    records=[]
    for r in source:
        if r['source_status']!='eligible':continue
        mid=r['container_id'];s=json.loads((BASE/'results/phase3_ci_epochs_001'/mid/'summary.json').read_text())
        records.append(dict(container_id=mid,**{k:v for k,v in labels[mid].items() if k!='container_id'},
            target_epochs=s['target_annotations'],stored_epochs=s['stored_epochs'],primary_retained=s['primary_retained'],strict_retained=s['strict_retained'],
            channel_gate=s['record_channel_gate'],roi_gate=s['roi_channel_gate'],retention_fraction=s['primary_retained']/max(s['target_annotations'],1),
            stad_trials=s['accepted_counts'].get('stad',0),devt_trials=s['accepted_counts'].get('devt',0),hdev_trials=s['accepted_counts'].get('hdev',0),ldev_trials=s['accepted_counts'].get('ldev',0)))
    table(out/'source_record_quality.csv',records)
    rf=pd.DataFrame(records);df=dec.merge(rf,on='container_id',validate='many_to_one');table(out/'decoder_with_source_labels.csv',df.to_dict('records'))
    grouped=[]
    for keys,g in df.groupby(['source_cohort_evidence','protocol_task','variant','deviant_literal_code','window'],dropna=False):
        good=g[g.status=='all_folds_measured'];grouped.append(dict(zip(['source_cohort_evidence','protocol_task','variant','deviant_literal_code','window'],keys),candidate_records=len(g),all_folds_records=len(good),**distribution(good.mean_fold_auc.tolist())))
    table(out/'decoder_stratified_summary.csv',grouped)
    halfgroup=[]
    hf=half.merge(rf[['container_id','source_cohort_evidence','protocol_task']],on='container_id',validate='many_to_one')
    for keys,g in hf.groupby(['source_cohort_evidence','protocol_task','variant','event_code','split'],dropna=False):
        good=g[g.status=='measured'];halfgroup.append(dict(zip(['source_cohort_evidence','protocol_task','variant','event_code','split'],keys),candidate_records=len(g),**distribution(good.waveform_r.tolist())))
    table(out/'reliability_stratified_summary.csv',halfgroup)
    index={}
    eligible=[r for r in records if r['source_candidate_ambiguity']=='unique_participant' and r['unique_same_day_pid'] and r['protocol_task']!='unknown']
    for r in sorted(eligible,key=lambda r:(dates[r['container_id']],r['container_id'])):
        key=(r['unique_same_day_pid'],r['source_cohort_evidence'],r['protocol_task']);index.setdefault(key,r)
    idx=[dict(participant_id=k[0],source_cohort_evidence=k[1],protocol_task=k[2],container_id=r['container_id']) for k,r in index.items()]
    table(out/'candidate_task_indices.csv',idx)
    # Source index selection uses metadata; incomplete measurement indices remain visible.
    indexdec=df[df.container_id.isin([r['container_id'] for r in idx])]
    table(out/'candidate_task_index_decoder.csv',indexdec.to_dict('records'))
    # First record per participant/day/task, then first pairable day per candidate.
    daytask={};dayconfig={}
    for r in sorted(eligible,key=lambda r:(dates[r['container_id']],r['container_id'])):
        pid=r['unique_same_day_pid'];day=r['candidate_acquisition_day_id'];task=r['protocol_task'];group=r['source_cohort_evidence']
        daytask.setdefault((pid,day,task),r)
        dayconfig.setdefault((pid,day,task,group),r)
    pair_candidates=[]
    for pid,day,task in daytask:
        if task=='bapa' and (pid,day,'puretone') in daytask:
            pair_candidates.append((dates[daytask[(pid,day,task)]['container_id']],pid,day,'task_bapa_minus_puretone',daytask[(pid,day,'puretone')],daytask[(pid,day,'bapa')]))
    for pid,day,task,group in dayconfig:
        if group=='CI' and (pid,day,task,'CIHA_label') in dayconfig:
            pair_candidates.append((dates[dayconfig[(pid,day,task,group)]['container_id']],pid,day,'configuration_CIHA_minus_CI/'+task,dayconfig[(pid,day,task,'CI')],dayconfig[(pid,day,task,'CIHA_label')]))
    chosen={}
    for date,pid,day,kind,a,b in sorted(pair_candidates,key=lambda p:(p[0],p[1],p[3])):chosen.setdefault((pid,kind),(day,a,b))
    pairrows=[];pairavailability=[]
    for (pid,kind),(day,a,b) in chosen.items():
        aid=a['container_id'];bid=b['container_id'];pairavailability.append(dict(participant_id=pid,contrast=kind,container_a=aid,container_b=bid,source_group_a=a['source_cohort_evidence'],source_group_b=b['source_cohort_evidence']))
        da=df[(df.container_id==aid)&(df.status=='all_folds_measured')];db=df[(df.container_id==bid)&(df.status=='all_folds_measured')]
        merged=da.merge(db,on=['variant','deviant_literal_code','window'],suffixes=('_a','_b'),validate='one_to_one')
        for r in merged.to_dict('records'):
            pairrows.append(dict(participant_id=pid,contrast=kind,container_a=aid,container_b=bid,variant=r['variant'],deviant_literal_code=r['deviant_literal_code'],window=r['window'],auc_a=r['mean_fold_auc_a'],auc_b=r['mean_fold_auc_b'],delta_auc_b_minus_a=r['mean_fold_auc_b']-r['mean_fold_auc_a']))
    table(out/'pair_availability.csv',pairavailability);table(out/'paired_decoder_contrasts.csv',pairrows)
    pair_summary=[]
    if pairrows:
        for keys,g in pd.DataFrame(pairrows).groupby(['contrast','variant','deviant_literal_code','window']):pair_summary.append(dict(zip(['contrast','variant','deviant_literal_code','window'],keys),**distribution(g.delta_auc_b_minus_a.tolist())))
    table(out/'paired_decoder_summary.csv',pair_summary)
    # Paired primary/strict comparisons retain identical record/code support.
    matched_qc=dec[dec.status=='all_folds_measured'].pivot(index=['container_id','deviant_literal_code','window'],columns='variant',values='mean_fold_auc').dropna()
    matched_qc['delta_strict_minus_primary']=matched_qc['strict']-matched_qc['primary'];table(out/'matched_qc_decoder.csv',matched_qc.reset_index().to_dict('records'))
    common_windows=dec[(dec.variant=='primary')&(dec.status=='all_folds_measured')].pivot(index=['container_id','deviant_literal_code'],columns='window',values='mean_fold_auc').dropna()
    common_windows['delta_post_minus_pre']=common_windows.poststim-common_windows.prestim;table(out/'matched_window_decoder.csv',common_windows.reset_index().to_dict('records'))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,ax=plt.subplots(figsize=(8,4.5),layout='constrained')
    rows=[(r['model'],r['MAE']) for r in ha['targets_models'] if r['target']=='MUSS']+[(r['model'],r['MAE']) for r in sens['models'] if r['model'] in ['clinical_age_duration','post_separate_penalty','pre_separate_penalty']]
    display={'clinical':'Age + log(use) + PTA','clinical_plus_fixed_amplitude':'+ fixed EEG amplitude','clinical_plus_poststim_pattern':'+ EEG pattern, shared penalty','clinical_plus_prestim_pattern':'+ prestimulus pattern, shared penalty','clinical_age_duration':'Age + log(use)','post_separate_penalty':'+ EEG pattern, separate penalties','pre_separate_penalty':'+ prestimulus, separate penalties'}
    ax.barh([display[k] for k,v in rows],[v for k,v in rows],color=['#355c7d','#6b8eab','#aa4b4b','#c69797','#355c7d','#568b72','#9fb8aa']);ax.invert_yaxis()
    for i,(k,v) in enumerate(rows):ax.text(v+.12,i,f'{v:.2f}',va='center')
    ax.set(xlabel='MUSS mean absolute error (lower is better)',xlim=(0,16),title='HA: 50 candidates, repeated nested child-level validation\nSeparate-penalty results are a post-v1 sensitivity analysis')
    fig.savefig(figdir/'ha_clinical_increment.pdf');fig.savefig(figdir/'ha_clinical_increment.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4.4),layout='constrained')
    for code,g in common_windows.reset_index().groupby('deviant_literal_code'):axes[0].scatter(g.prestim,g.poststim,s=15,alpha=.6,label=f'{code}: {len(g)} records')
    axes[0].plot([0,1],[0,1],color='gray',lw=1);axes[0].axhline(.5,color='gray',ls=':',lw=.7);axes[0].axvline(.5,color='gray',ls=':',lw=.7);axes[0].set(xlabel='Prestimulus mean temporal-fold AUC',ylabel='50–250 ms mean temporal-fold AUC',xlim=(.2,1),ylim=(.2,1),title='Same record/code support');axes[0].legend(fontsize=8)
    axes[1].hist(rf.retention_fraction,bins=np.linspace(0,1,21),color='#527f94');axes[1].set(xlabel='Primary retained / annotated target trials',ylabel='Canonical records',title='MFF archive: mixed / unresolved cohort labels')
    fig.savefig(figdir/'mff_event_decoding_quality.pdf');fig.savefig(figdir/'mff_event_decoding_quality.png',dpi=180);plt.close(fig)
    grouped_quality=[]
    for label,g in rf.groupby('source_cohort_evidence'):grouped_quality.append(dict(source_label=label,records=len(g),channel_gate_pass=int(g.channel_gate.sum()),roi_gate_pass=int(g.roi_gate.sum()),target_trials=int(g.target_epochs.sum()),retained_trials=int(g.primary_retained.sum()),retention_distribution=distribution(g.retention_fraction.tolist())))
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],canonical_records=len(records),quality_by_source_label=grouped_quality,unique_candidate_known_task_indices=len(idx),unique_candidate_ids=len({r['participant_id'] for r in idx}),pair_counts=dict(Counter(r['contrast'] for r in pairavailability)),pair_results=pair_summary,matched_primary_strict_auc_delta=distribution(matched_qc.delta_strict_minus_primary.tolist()),matched_pre_post_auc_delta=distribution(common_windows.delta_post_minus_pre.tolist()),HA_sensitivity_post_null_EEG_folds=sum(x['alpha_eeg']=='infinity_null_eeg' for r in sens['models'] if r['model']=='post_separate_penalty' for x in r['alpha_pairs']),scope='Exploratory feasibility; source labels and candidate links are not adjudicated clinical identities; no device/cortical/causal claims')
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    for p in [Path(__file__),BASE/'docs/PHASE3_CI_SUMMARY_RULES.md']:shutil.copy2(p,out/p.name)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
