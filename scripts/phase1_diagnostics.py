"""Post-run descriptive checks; no changes to v1 processing or clinical analyses."""
import json
import os
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from phase1_prepare import readcsv,table
from phase1_epochs import digest

BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
os.umask(0o077)
out=BASE/'results/phase1_diagnostics_001';out.mkdir(exist_ok=False)
figs=BASE/'figures/phase1_diagnostics_001';figs.mkdir(exist_ok=False)
meas=BASE/'results/phase1_measurements_001';epochs=BASE/'results/phase1_epochs_001'
counts=readcsv(meas/'trial_counts.csv');halves=readcsv(meas/'split_agreement.csv')
features=readcsv(meas/'features.csv');sens=readcsv(meas/'sensitivity.csv')
primary={r['recording_id']:r for r in counts if r['variant']=='hp01_avg_150'}
good={rid for rid,r in primary.items() if r['measurement_status']=='sufficient_trials_and_blocks'}
agreements=[]
for cohort in ('HA','NH','pooled'):
 for condition in ('code1','code2','code2_minus_code1'):
  for split in ('alternating_30s_blocks','early_late'):
   rr=[r for r in halves if r['variant']=='hp01_avg_150' and r['condition']==condition and r['split']==split and r['recording_id'] in good and (cohort=='pooled' or r['cohort_label']==cohort)]
   rvals=np.array([float(r['waveform_r']) for r in rr]);rvals=rvals[np.isfinite(rvals)]
   agreements.append(dict(cohort=cohort,condition=condition,split=split,n_attempted=len(rr),n_valid=len(rvals),
       n_missing=len(rr)-len(rvals),median_waveform_r=float(np.median(rvals)) if len(rvals) else np.nan,
       q25=float(np.quantile(rvals,.25)) if len(rvals) else np.nan,q75=float(np.quantile(rvals,.75)) if len(rvals) else np.nan,
       scope='record_level_waveform_shape_agreement'))
table(out/'agreement_by_condition_and_cohort.csv',agreements)
eventmap=defaultdict(list)
for e in readcsv(BASE/'results/other_eeg_001/event_ledger.csv'):
 if e['event_code_token'] in ('1','2'):eventmap[e['file_id']].append((e['event_code_token'],float(e['onset_s'])))
timing=[]
for link in readcsv(BASE/'results/processed_link_001/processed_to_raw_candidates.csv'):
 if link['data_level']!='preprocessed_continuous' or link['exact_stimulus_code_sequence_match']!='True':continue
 a=eventmap[link['file_id']];b=eventmap[link['raw_event_file_id']]
 assert [x[0] for x in a]==[x[0] for x in b]
 d=np.array([x[1]-y[1] for x,y in zip(a,b)]);median=float(np.median(d));res=float(np.max(abs(d-median)))
 timing.append(dict(processed_file_id=link['file_id'],recording_id=link['candidate_acquisition_id'],
    paired_events=len(d),processed_minus_raw_event_median_s=median,max_deviation_from_constant_offset_s=res,
    timing_relation='constant_offset_within_1ms' if res<=.001 else 'not_constant',
    scope='candidate_processed_timeline_not_acoustic_alignment'))
table(out/'processed_event_timing_crosscheck.csv',timing)
references=[];reference_stats=[]
for rid,q in primary.items():
 rows=readcsv(epochs/rid/'epoch_ledger.csv');accepted=[r for r in rows if r['disposition']=='accepted']
 references.append(dict(recording_id=rid,cohort_label=q['cohort_label'],primary_accepted=len(accepted),
     accepted_with_saturated_ear=sum(r['ear_raw_saturation']=='True' for r in accepted),
     accepted_with_ear_filtered_ptp_above_150uv=sum(float(r['ear_filtered_max_ptp_uv'])>150 for r in accepted)))
table(out/'ear_reference_diagnostics.csv',references)
fig,axs=plt.subplots(1,2,figsize=(10,4))
for ax,variant,label in zip(axs,('hp05_avg_matched','hp01_ears_matched'),('High-pass 0.5 Hz, same trials','Ear reference, same trials')):
 rr=[r for r in sens if r['variant']==variant and r['condition']=='code2_minus_code1' and r['window']=='mean_50_250ms' and r['recording_id'] in good and np.isfinite(float(r['delta_uv']))]
 x=np.array([float(r['baseline_mean_uv']) for r in rr]);y=np.array([float(r['variant_mean_uv']) for r in rr])
 rho=float(spearmanr(x,y).statistic) if len(x)>=3 else np.nan
 reference_stats.append(dict(variant=variant,n_records=len(rr),spearman_record_scores=rho,
     primary_score_range_uv=[float(x.min()),float(x.max())] if len(x) else [],
     variant_score_range_uv=[float(y.min()),float(y.max())] if len(y) else []))
 ax.scatter(x,y,s=20,alpha=.75)
 lo=min(x.min(),y.min());hi=max(x.max(),y.max());ax.plot([lo,hi],[lo,hi],ls='--',color='gray')
 ax.set(xlabel='Primary code 2 - code 1, 50-250 ms (uV)',ylabel='Variant score (uV)',title=f'{label}\nn={len(x)}, Spearman={rho:.2f}')
fig.tight_layout();fig.savefig(figs/'reference_filter_sensitivity.png',dpi=180);plt.close(fig)
# Deterministic illustrations span each cohort's retention, including poor records.
chosen=[]
for cohort in ('HA','NH'):
 rr=sorted([r for r in primary.values() if r['cohort_label']==cohort],key=lambda r:(float(r['retention_fraction']),r['recording_id']))
 for index,label in [(0,'lowest retention'),(len(rr)//2,'middle retention'),(len(rr)-1,'highest retention')]:
  if rr:chosen.append((rr[index],label))
fig,axs=plt.subplots(2,3,figsize=(12,6),sharex=True)
for ax,(q,label) in zip(axs.ravel(),chosen):
 rid=q['recording_id']
 with np.load(meas/(rid+'_evoked.npz'),allow_pickle=False) as data:
  for j,condition in enumerate(('code1','code2','code2-code1')):ax.plot(data['times_s'],data['waveforms_uv'][0,j],label=condition,lw=.9)
 ax.axvline(0,color='black',lw=.5);ax.axhline(0,color='black',lw=.5)
 ax.set(title=f'{q["cohort_label"]}: {label}\n{rid}, n1={q["n_code1"]}, n2={q["n_code2"]}',xlabel='Recorded-event time (s)',ylabel='Fz/Cz (uV)')
 ax.legend(fontsize=6)
fig.tight_layout();fig.savefig(figs/'retention_stratified_waveforms.png',dpi=180);plt.close(fig)
table(out/'figure_record_selection.csv',[dict(recording_id=q['recording_id'],cohort_label=q['cohort_label'],selection=label,
    measurement_status=q['measurement_status']) for q,label in chosen])
# Recheck hashes of the final method/code snapshot after documentation-independent work.
checkrows=readcsv(BASE/'results/phase1_final_001/artifact_checksums.csv')
verified=0
for r in checkrows:
 assert digest(BASE/r['artifact'])==r['sha256'],r['artifact']
 verified+=1
summary=dict(job_id=os.environ['SLURM_JOB_ID'],reference_filter_rank_sensitivity=reference_stats,
    primary_records_with_any_ear_saturation=sum(r['accepted_with_saturated_ear']>0 for r in references),
    primary_records_with_ear_ptp_above_150uv=sum(r['accepted_with_ear_filtered_ptp_above_150uv']>0 for r in references),
    processed_event_crosscheck_count=len(timing),processed_event_relations=dict(Counter(r['timing_relation'] for r in timing)),
    final_artifact_checksums_verified=verified,clinical_outcomes_used=False,
    interpretation='Post-run diagnostics; no changes to v1 selection, windows, masks, or feature scores')
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2),flush=True)
