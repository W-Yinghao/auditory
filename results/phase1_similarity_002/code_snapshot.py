"""Targeted source-integrity follow-up prompted by similar averaged waveforms."""
import json
import os
from pathlib import Path
import numpy as np
from phase1_prepare import readcsv,table

BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
os.umask(0o077)
out=BASE/'results'/os.environ.get('PHASE1_SIMILARITY_RUN','phase1_similarity_001');out.mkdir(exist_ok=False)
epochs=BASE/'results/phase1_epochs_001'
counts=[r for r in readcsv(BASE/'results/phase1_measurements_001/trial_counts.csv')
        if r['variant']=='hp01_avg_150' and r['measurement_status']=='sufficient_trials_and_blocks']
counts.sort(key=lambda r:r['recording_id'])
means=[];roi_means=[]
for r in counts:
 with np.load(epochs/r['recording_id']/'epochs.npz',allow_pickle=False) as d:
  mask=d['accepted'][:,0] & (d['codes']==1)
  times=d['times_s'];tw=(times>=0)&(times<=.4)
  means.append(d['data_uv'][mask].mean(axis=0)[:,tw].flatten())
  roi_means.append(d['roi_uv'][mask,0].mean(axis=0)[tw])
corr=np.corrcoef(np.asarray(means));roi_corr=np.corrcoef(np.asarray(roi_means))
pairs=[]
for i in range(len(counts)):
 for j in range(i+1,len(counts)):
  pairs.append(dict(recording_a=counts[i]['recording_id'],recording_b=counts[j]['recording_id'],
    candidate_identity_equal=counts[i]['participant_id']==counts[j]['participant_id'],
    cohort_a=counts[i]['cohort_label'],cohort_b=counts[j]['cohort_label'],
    code1_mean_20channel_r=float(corr[i,j]),code1_mean_roi_r=float(roi_corr[i,j])))
pairs.sort(key=lambda r:r['code1_mean_20channel_r'],reverse=True)
table(out/'all_record_mean_similarity.csv',pairs)
selected=pairs[:10]
# Include the visually noted HA/NH pair even if not among the top full-scalp pairs.
visual={r['recording_id'] for r in readcsv(BASE/'results/phase1_diagnostics_001/figure_record_selection.csv')
        if r['selection']=='highest retention'}
assert len(visual)==2
visual_found=False
for p in pairs:
 if {p['recording_a'],p['recording_b']}==visual:
  visual_found=True
  if p not in selected:selected.append(p)
assert visual_found
checks=[]
for p in selected:
 data=[]
 for rid in (p['recording_a'],p['recording_b']):
  with np.load(epochs/rid/'epochs.npz',allow_pickle=False) as d:
   accepted=d['accepted'][:,0]
   ids=d['event_indices_1based'][accepted];codes=d['codes'][accepted]
   wave=d['roi_uv'][accepted,0].astype(float)
   # Remove each recording's condition mean and trial mean to isolate residual shape.
   for code in (1,2):
    chosen=codes==code
    wave[chosen]-=wave[chosen].mean(axis=0)
   wave-=wave.mean(axis=1,keepdims=True)
   data.append((ids,codes,wave))
 common,ia,ib=np.intersect1d(data[0][0],data[1][0],return_indices=True)
 samecode=data[0][1][ia]==data[1][1][ib];ia=ia[samecode];ib=ib[samecode]
 a=data[0][2][ia];b=data[1][2][ib]
 if len(a)<20:continue
 actual=float(np.corrcoef(a.ravel(),b.ravel())[0,1])
 rng=np.random.default_rng(20260916);null=[]
 for _ in range(100):
  perm=rng.permutation(len(b))
  null.append(float(np.corrcoef(a.ravel(),b[perm].ravel())[0,1]))
 checks.append(dict(p,matched_ordinal_same_code_trials=len(a),
    residual_roi_correlation=actual,shuffled_trial_r_q025=float(np.quantile(null,.025)),
    shuffled_trial_r_q975=float(np.quantile(null,.975)),
    scope='ordinal_aligned_residual_check_not_exhaustive_duplicate_detection'))
table(out/'targeted_residual_similarity.csv',checks)
summary=dict(job_id=os.environ['SLURM_JOB_ID'],records_with_measurements=len(counts),record_pairs=len(pairs),
    targeted_pairs=len(checks),maximum_mean_roi_r=max(p['code1_mean_roi_r'] for p in pairs),
    figure_selected_pair_included=visual_found,
    maximum_targeted_residual_r=max(p['residual_roi_correlation'] for p in checks),
    targeted_pairs_residual_r_above_0_9=sum(p['residual_roi_correlation']>.9 for p in checks),
    threshold_0_9_status='diagnostic_flag_only_not_confirmed_identity_or_duplication',
    clinical_outcomes_used=False)
(out/'summary.json').write_text(json.dumps(summary,indent=2))
(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(summary,indent=2),flush=True)
