"""Block-aware measurement precision, temporal agreement and fixed sensitivities."""
import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from phase1_core import block_bootstrap_scores, waveform_comparison, ear_reference_valid
from phase1_prepare import readcsv, table
from phase1_epochs import digest

BASE = Path(__file__).resolve().parents[1]
VARIANTS = [('hp01_avg_150',0,0), ('hp05_avg_matched',1,0),
            ('hp01_ears_matched',2,0), ('hp01_avg_100',0,1), ('hp01_avg_200',0,2)]
CONDITIONS = ('code1','code2','code2_minus_code1')


def window_means(waves, times, cfg):
    return np.stack([waves[..., (times >= lo-1e-10) & (times <= hi+1e-10)].mean(axis=-1)
                     for lo,hi in cfg['windows_s'].values()],axis=-1)


def condition_means(waves, codes):
    a = waves[codes==1].mean(axis=0) if np.any(codes==1) else np.full(waves.shape[1:],np.nan)
    b = waves[codes==2].mean(axis=0) if np.any(codes==2) else np.full(waves.shape[1:],np.nan)
    return np.stack([a,b,b-a])


def measure(row, folder, cfg):
    rid = row['recording_id']
    seed = cfg['random_seed'] + int(hashlib.sha256(rid.encode()).hexdigest()[:8],16)
    rng = np.random.default_rng(seed)
    with np.load(folder/'epochs.npz',allow_pickle=False) as ds:
        times = ds['times_s']; roi = ds['roi_uv'].astype(float)
        masks = ds['accepted']; codes = ds['codes']; blocks = ds['blocks']; samples = ds['samples_0based']
        assert str(ds['config_sha256']) == row['config_sha256']
        assert np.all(np.isfinite(roi))
        assert np.all(masks[:,1] <= masks[:,0]) and np.all(masks[:,0] <= masks[:,2])
        # Verify the saved ROI agrees with the actual primary scalp epochs.
        rr = [list(ds['channels']).index(c) for c in cfg['roi_channels']]
        saved_roi_channels = ds['data_uv'][:,rr,:].astype(float)
        difference = abs(saved_roi_channels.mean(axis=1)-roi[:,0])
        float32_bound = 3*np.finfo(np.float32).eps*np.maximum(1,np.max(abs(saved_roi_channels),axis=1))
        assert np.all(difference <= float32_bound), 'saved ROI differs beyond float32 rounding'
    features = []; halves = []; curves = []; evokeds = []
    counts_rows = []; statuses = {}
    ledger = [r for r in readcsv(folder/'epoch_ledger.csv') if r['stored_epoch_0based'] != '']
    ledger.sort(key=lambda r:int(r['stored_epoch_0based']))
    assert len(ledger)==len(codes)
    saturation = np.array([r['ear_raw_saturation']=='True' for r in ledger])
    flat_ears = bool(set(json.loads(row['channels_flat_in_at_least_20pct_blocks'])) & {'A1','A2'})
    ear_valid = ear_reference_valid(masks[:,0],saturation,flat_ears)
    wavewin = (times>=cfg['waveform_similarity_window_s'][0]-1e-10)&(times<=cfg['waveform_similarity_window_s'][1]+1e-10)
    for variant, vi, mi in VARIANTS:
        invalid_reference = variant=='hp01_ears_matched' and not ear_valid
        selected = np.zeros(len(codes),dtype=bool) if invalid_reference else masks[:,mi]
        w = roi[selected,vi]; c = codes[selected]; b = blocks[selected]; s = samples[selected]
        counts = [int(np.sum(c==code)) for code in (1,2)]
        occupied = [len(np.unique(b[c==code])) for code in (1,2)]
        valid = [counts[j]>=cfg['minimum_trials_per_code'] and occupied[j]>=cfg['minimum_occupied_blocks'] for j in (0,1)]
        status = ('invalid_reference_channels' if invalid_reference else
                  'sufficient_trials_and_blocks' if all(valid) else 'insufficient_trials_or_blocks')
        statuses[variant] = status
        counts_rows.append(dict(recording_id=rid,participant_id=row['participant_id'],cohort_label=row['cohort_label'],
            variant=variant,n_code1=counts[0],n_code2=counts[1],occupied_blocks_code1=occupied[0],
            occupied_blocks_code2=occupied[1],measurement_status=status,
            retention_fraction=float(selected.sum()/int(row['n_target_events']))))
        means = condition_means(w,c); evokeds.append(means)
        scores = window_means(w,times,cfg)
        boot = block_bootstrap_scores(scores,c,b,cfg['bootstrap_repetitions'],rng) if all(valid) else None
        for ci, condition in enumerate(CONDITIONS):
            enough = valid[ci] if ci<2 else all(valid)
            if enough:
                estimate = window_means(means[ci],times,cfg)
                if ci<2:
                    iid_se = np.std(scores[c==ci+1],axis=0,ddof=1)/np.sqrt(counts[ci])
                else:
                    iid_se = np.sqrt(np.var(scores[c==1],axis=0,ddof=1)/counts[0] + np.var(scores[c==2],axis=0,ddof=1)/counts[1])
            for wi, window in enumerate(cfg['windows_s']):
                bs = boot[:,ci,wi] if boot is not None else np.array([])
                finite = bs[np.isfinite(bs)]
                features.append(dict(recording_id=rid,participant_id=row['participant_id'],cohort_label=row['cohort_label'],
                    variant=variant,condition=condition,window=window,n_code1=counts[0],n_code2=counts[1],
                    feature_status='measured' if enough else status,
                    mean_uv=float(estimate[wi]) if enough else np.nan,
                    iid_sme_uv=float(iid_se[wi]) if enough else np.nan,
                    block_bootstrap_se_uv=float(np.std(finite,ddof=1)) if len(finite)>=.95*cfg['bootstrap_repetitions'] else np.nan,
                    block_ci_low_uv=float(np.quantile(finite,.025)) if len(finite)>=.95*cfg['bootstrap_repetitions'] else np.nan,
                    block_ci_high_uv=float(np.quantile(finite,.975)) if len(finite)>=.95*cfg['bootstrap_repetitions'] else np.nan,
                    valid_bootstrap_repetitions=len(finite),
                    bootstrap_status=('available' if len(finite)>=.95*cfg['bootstrap_repetitions'] else
                                      'not_attempted_both_conditions_required' if boot is None else 'too_many_empty_condition_draws'),
                    inference_scope='within_record_precision_not_cortical_or_clinical_validity'))
        if not len(samples): continue
        midtime = (samples.min()+samples.max())/2
        for split, halfb in [('alternating_30s_blocks',b%2==1),('early_late',s>midtime)]:
            a = ~halfb
            halfcounts = [int(np.sum(side & (c==code))) for side in (a,halfb) for code in (1,2)]
            am = condition_means(w[a],c[a]); bm = condition_means(w[halfb],c[halfb])
            for ci, condition in enumerate(CONDITIONS):
                relevant = [halfcounts[ci],halfcounts[ci+2]] if ci<2 else halfcounts
                enough = min(relevant)>=cfg['minimum_trials_each_half_per_code']
                corr,rmse = waveform_comparison(am[ci,wavewin],bm[ci,wavewin]) if enough else (np.nan,np.nan)
                delta = window_means(bm[ci]-am[ci],times,cfg) if enough else [np.nan]*len(cfg['windows_s'])
                item = dict(recording_id=rid,participant_id=row['participant_id'],cohort_label=row['cohort_label'],
                    variant=variant,split=split,condition=condition,n_a_code1=halfcounts[0],n_a_code2=halfcounts[1],
                    n_b_code1=halfcounts[2],n_b_code2=halfcounts[3],
                    split_status='measured' if enough else 'insufficient_trials_in_half',
                    waveform_r=corr,waveform_rmse_uv=rmse,
                    metric_scope='waveform_agreement_not_person_level_psychometric_reliability')
                item.update({f'b_minus_a_{window}_uv':float(delta[wi]) for wi,window in enumerate(cfg['windows_s'])})
                halves.append(item)
        if variant == 'hp01_avg_150' and all(valid):
            pools = [[np.flatnonzero((b%2==half)&(c==code)) for code in (1,2)] for half in (0,1)]
            for trial_count in cfg['trial_curve_counts_per_code_per_half']:
                if min(len(p) for half in pools for p in half)<trial_count: continue
                repetitions = []
                for rep in range(cfg['trial_curve_repetitions']):
                    means_by_half = []
                    for half in pools:
                        first = w[rng.choice(half[0],trial_count,replace=False)].mean(axis=0)
                        second = w[rng.choice(half[1],trial_count,replace=False)].mean(axis=0)
                        means_by_half.append(np.stack([first,second,second-first]))
                    repetitions.append([waveform_comparison(means_by_half[0][j,wavewin],means_by_half[1][j,wavewin]) for j in range(3)])
                repstats = np.asarray(repetitions)
                for ci, condition in enumerate(CONDITIONS):
                    curves.append(dict(recording_id=rid,cohort_label=row['cohort_label'],condition=condition,
                        trials_per_code_per_half=trial_count,repetitions=cfg['trial_curve_repetitions'],
                        finite_correlation_repetitions=int(np.isfinite(repstats[:,ci,0]).sum()),
                        finite_rmse_repetitions=int(np.isfinite(repstats[:,ci,1]).sum()),
                        median_waveform_r=float(np.nanmedian(repstats[:,ci,0])),
                        median_waveform_rmse_uv=float(np.nanmedian(repstats[:,ci,1]))))
    return features,halves,curves,counts_rows,times,np.array(evokeds),statuses


def quantile_summary(values):
    a=np.array([v for v in values if np.isfinite(v)],float)
    return {'n_attempted':len(values),'n':len(a),'n_missing':len(values)-len(a),'median':float(np.median(a)) if len(a) else None,
            'q25':float(np.quantile(a,.25)) if len(a) else None,'q75':float(np.quantile(a,.75)) if len(a) else None}


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('--input',default='phase1_epochs_001')
    parser.add_argument('--output',default='phase1_measurements_001');parser.add_argument('--expected-records',type=int,default=93)
    args=parser.parse_args(); src=BASE/'results'/args.input
    out=BASE/'results'/args.output;out.mkdir(exist_ok=False)
    figs=BASE/'figures'/args.output;figs.mkdir(exist_ok=False)
    cfg=json.loads((BASE/'configs/phase1_v1.json').read_text())
    rows=[json.loads(p.read_text()) for p in sorted(src.glob('B*/summary.json'))]
    assert len(rows)==args.expected_records
    assert all(r['config_sha256']==digest(BASE/'configs/phase1_v1.json') for r in rows)
    completed=list(src.glob('completion_*.json'))
    assert completed and all(json.loads(p.read_text())['errors']==0 for p in completed)
    table(out/'recording_qc.csv',rows)
    duplicate=defaultdict(list)
    for r in rows: duplicate[r['signal_numeric_sha256']].append(r['recording_id'])
    duplicated=[ids for ids in duplicate.values() if len(ids)>1]
    # No implicit duplicate merge is allowed in the primary descriptive report.
    if duplicated:
        (out/'duplicate_signal_groups.json').write_text(json.dumps(duplicated,indent=2))
        raise ValueError('Duplicate signal exports require provenance adjudication before aggregation')
    features=[];halves=[];curves=[];counts=[];statuses={};verify=[]
    with PdfPages(figs/'record_waveforms.pdf') as pdf:
        for row in rows:
            if row['status']!='epochs_created':continue
            rid=row['recording_id']; folder=src/rid
            assert digest(folder/'epochs.npz')==row['epoch_data_sha256']
            ff,hh,cc,nn,t,ev,ss=measure(row,folder,cfg)
            features.extend(ff);halves.extend(hh);curves.extend(cc);counts.extend(nn);statuses[rid]=ss
            np.savez_compressed(out/(rid+'_evoked.npz'),times_s=t,waveforms_uv=ev,
                                variant_names=np.array([v[0] for v in VARIANTS]),conditions=np.array(CONDITIONS))
            fig,axs=plt.subplots(1,3,figsize=(12,3.4))
            for ci,label in enumerate(CONDITIONS):axs[0].plot(t,ev[0,ci],label=label,lw=1)
            for vi,name in enumerate([v[0] for v in VARIANTS]):axs[1].plot(t,ev[vi,2],label=name,lw=.8)
            axs[2].bar(['100','150','200'],[int(row[f'accepted_{v}uv']) for v in (100,150,200)])
            axs[2].set(xlabel='Peak-to-peak threshold (uV)',ylabel='Accepted target epochs')
            for ax in axs[:2]:
                ax.axvline(0,color='k',lw=.5);ax.axhline(0,color='k',lw=.5)
                ax.set(xlabel='Time relative to recorded event (s)',ylabel='Fz/Cz mean (uV)');ax.legend(fontsize=6)
            axs[0].set_title('Primary: numeric event codes');axs[1].set_title('Code 2 - code 1: fixed sensitivities')
            fig.suptitle(f'{rid} | {row["cohort_label"]} candidate | {ss["hp01_avg_150"]}',fontsize=10)
            fig.tight_layout();pdf.savefig(fig);plt.close(fig)
            verify.append(dict(recording_id=rid,epoch_hash_verified=True,roi_from_saved_channels_verified=True,
                               nested_rejection_masks_verified=True))
            print(json.dumps({'recording_id':rid,'measurement_status':ss['hp01_avg_150']}),flush=True)
    for name,data in [('features',features),('split_agreement',halves),('trial_count_curves',curves),('trial_counts',counts),('verification',verify)]:
        table(out/(name+'.csv'),data)
    sensitivity=[]
    lookup={(r['recording_id'],r['variant'],r['condition'],r['window']):r for r in features}
    for r in features:
        if r['variant']=='hp01_avg_150':continue
        ref=lookup[(r['recording_id'],'hp01_avg_150',r['condition'],r['window'])]
        sensitivity.append(dict(recording_id=r['recording_id'],cohort_label=r['cohort_label'],variant=r['variant'],
            condition=r['condition'],window=r['window'],baseline_mean_uv=ref['mean_uv'],variant_mean_uv=r['mean_uv'],
            delta_uv=r['mean_uv']-ref['mean_uv'],
            matched_trials=r['variant'] in ('hp05_avg_matched','hp01_ears_matched')))
    table(out/'sensitivity.csv',sensitivity)
    primary=[r for r in counts if r['variant']=='hp01_avg_150']
    enough=[r for r in primary if r['measurement_status']=='sufficient_trials_and_blocks']
    eligible_ids={r['recording_id'] for r in enough}
    primary_feature=[r for r in features if r['variant']=='hp01_avg_150' and r['window']=='mean_50_250ms' and r['condition']=='code2_minus_code1' and r['recording_id'] in eligible_ids]
    comparison={split:quantile_summary([r['waveform_r'] for r in halves if r['variant']=='hp01_avg_150' and r['condition']=='code2_minus_code1' and r['split']==split and r['recording_id'] in eligible_ids]) for split in ('alternating_30s_blocks','early_late')}
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],config_sha256=digest(BASE/'configs/phase1_v1.json'),
        input_run=args.input,records=len(rows),source_gate_counts=dict(Counter(r['status'] for r in rows)),
        full_signal_samples_examined=sum(int(r['raw_samples_examined']) for r in rows),
        total_target_events_reconstructed=sum(int(r.get('stored_epochs',0)) for r in rows),
        primary_accepted_epochs=sum(int(r.get('accepted_150uv',0)) for r in rows),
        sufficient_measurement_records=len(enough),sufficient_by_cohort=dict(Counter(r['cohort_label'] for r in enough)),
        sufficient_candidate_identity_groups=len({r['participant_id'] for r in enough}),
        measurement_counts_by_variant={v[0]:sum(r['variant']==v[0] and r['measurement_status']=='sufficient_trials_and_blocks' for r in counts) for v in VARIANTS},
        invalid_ear_reference_records=sum(r['measurement_status']=='invalid_reference_channels' for r in counts),
        retention_fraction_record_summary=quantile_summary([r['retention_fraction'] for r in primary]),
        code2_minus_code1_primary_window_block_se_uv=quantile_summary([r['block_bootstrap_se_uv'] for r in primary_feature]),
        code2_minus_code1_primary_window_iid_sme_uv=quantile_summary([r['iid_sme_uv'] for r in primary_feature]),
        code2_minus_code1_waveform_r=comparison,duplicate_signal_groups=duplicated,
        records_verified=len(verify),clinical_outcomes_used=False,
        limitations=['record-level counts, candidate identities','waveform correlations are not person-level psychometric reliability',
                     'unknown acoustic mapping, trigger delay and device state','no inference that reproducible signals are cortical'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    # Record-level descriptive figures, with no EEG-outcome relationship.
    fig,axs=plt.subplots(1,3,figsize=(12,3.5))
    for group,color in [('HA','#377eb8'),('NH','#e89a3c')]:
        pts=[r for r in primary if r['cohort_label']==group]
        axs[0].scatter([r['n_code1'] for r in pts],[r['n_code2'] for r in pts],label=group,alpha=.7,s=22,color=color)
    axs[0].axhline(cfg['minimum_trials_per_code'],color='gray',ls='--');axs[0].axvline(cfg['minimum_trials_per_code'],color='gray',ls='--')
    axs[0].set(xlabel='Accepted code 1 epochs',ylabel='Accepted code 2 epochs',title='Primary trial retention');axs[0].legend()
    for split,color in [('alternating_30s_blocks','#377eb8'),('early_late','#e89a3c')]:
        vals=[r['waveform_r'] for r in halves if r['variant']=='hp01_avg_150' and r['condition']=='code2_minus_code1' and r['split']==split and r['recording_id'] in eligible_ids and np.isfinite(r['waveform_r'])]
        axs[1].hist(vals,bins=np.linspace(-1,1,16),alpha=.5,label=split,color=color)
    axs[1].set(xlabel='Waveform correlation',ylabel='Records',title='Code 2 - code 1 agreement');axs[1].legend(fontsize=6)
    axs[2].scatter([r['iid_sme_uv'] for r in primary_feature],[r['block_bootstrap_se_uv'] for r in primary_feature],s=20)
    axs[2].set(xlabel='IID analytic SME (uV)',ylabel='Block bootstrap SE (uV)',title='50-250 ms difference score precision')
    fig.tight_layout();fig.savefig(figs/'measurement_overview.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(9,3.5))
    for ci,condition in enumerate(CONDITIONS):
        xs=[];ys=[];ns=[]
        for k in cfg['trial_curve_counts_per_code_per_half']:
            rr=[r for r in curves if r['condition']==condition and r['trials_per_code_per_half']==k]
            if rr:
                xs.append(k);ys.append(np.nanmedian([r['median_waveform_r'] for r in rr]));ns.append(len(rr))
        axs[0].plot(xs,ys,'o-',label=condition);axs[1].plot(xs,ns,'o-',label=condition)
    axs[0].set(xlabel='Trials per code per half',ylabel='Median record waveform r',title='Different support at each count; descriptive')
    axs[1].set(xlabel='Trials per code per half',ylabel='Records contributing');axs[0].legend(fontsize=7)
    fig.tight_layout();fig.savefig(figs/'trial_count_curves.png',dpi=170);plt.close(fig)
    snapshot=out/'code_snapshot';snapshot.mkdir()
    for name in ('phase1_measurements.py','phase1_core.py'):(snapshot/name).write_bytes((BASE/'scripts'/name).read_bytes())
    (snapshot/'phase1_v1.json').write_bytes((BASE/'configs/phase1_v1.json').read_bytes())
    table(out/'artifact_checksums.csv',[dict(artifact=str(p.relative_to(BASE)),sha256=digest(p))
        for p in sorted(out.glob('*')) if p.is_file()])
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
