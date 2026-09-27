"""Candidate-level amplitude agreement and matched processing sensitivity."""
import csv
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from phase1_core import block_bootstrap_scores
from phase1_prepare import readcsv, table
from phase1_epochs import digest
from phase2_core import frontal_variant, balanced_selection, pair_summary

BASE=Path(__file__).resolve().parents[1]
CONDITIONS=('code1','code2','code2_minus_code1')


def seed_for(seed, token):
    return np.random.default_rng(seed+int(hashlib.sha256(token.encode()).hexdigest()[:8],16))


def condition_scores(scores,codes):
    a=scores[codes==1].mean() if np.any(codes==1) else np.nan
    b=scores[codes==2].mean() if np.any(codes==2) else np.nan
    return [a,b,b-a]


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm required'
    os.umask(0o077)
    cfgpath=BASE/'configs/phase2_v1.json'; cfg=json.loads(cfgpath.read_text())
    src=BASE/'results'/cfg['epoch_run']; out=BASE/'results/phase2_measurements_001'
    out.mkdir(exist_ok=False); figs=BASE/'figures/phase2_measurements_001';figs.mkdir(exist_ok=False)
    snapshot=out/'code_snapshot';snapshot.mkdir()
    for p in [cfgpath,BASE/'scripts/phase2_core.py',Path(__file__),BASE/'docs/PHASE2_PROTOCOL.md']:
        shutil.copy2(p,snapshot/p.name)
    indices={r['recording_id']:r for r in readcsv(BASE/'results'/cfg['cohort_run']/'index_recordings.csv')}
    source=readcsv(BASE/'results/phase1_sources_001/source_manifest.csv')
    assert len(source)==93 and len(indices)==93
    feature_rows=[];half_rows=[];block_rows=[];qc_rows=[];verified=[]
    markerfields=['recording_id','stored_epoch_0based','source_event_index_1based','code','sample_0based',
                  'frontoposterior_ptp_uv','primary_accepted','frontoposterior100_accepted','scalp100_accepted']
    with (out/'epoch_sensitivity_ledger.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=markerfields);writer.writeheader()
        for row in source:
            rid=row['recording_id'];folder=src/rid;summary=json.loads((folder/'summary.json').read_text())
            assert summary['config_sha256']==cfg['phase1_config_sha256']
            if summary['status']!='epochs_created': continue
            assert digest(folder/'epochs.npz')==summary['epoch_data_sha256']
            with np.load(folder/'epochs.npz',allow_pickle=False) as ds:
                data=ds['data_uv'].astype(float);roi=ds['roi_uv'].astype(float)
                t=ds['times_s'];codes=ds['codes'];samples=ds['samples_0based'];blocks=ds['blocks']
                masks=ds['accepted'];events=ds['event_indices_1based'];channels=ds['channels']
                assert str(ds['config_sha256'])==cfg['phase1_config_sha256']
            avg18,proxy=frontal_variant(data,channels)
            ptp=np.ptp(proxy,axis=-1);frontalmask=masks[:,0]&(ptp<=cfg['frontoposterior_ptp_threshold_uv'])
            assert np.all(frontalmask<=masks[:,0])
            window=(t>=cfg['window_s'][0]-1e-10)&(t<=cfg['window_s'][1]+1e-10)
            waves=[roi[:,0],roi[:,1],avg18,roi[:,0],roi[:,0]]
            vmasks=[masks[:,0],masks[:,0],masks[:,0],frontalmask,masks[:,1]]
            scores=[w[:,window].mean(axis=1) for w in waves]
            base=dict(recording_id=rid,participant_id=row['participant_id'],cohort_label=row['cohort_label'],
                      selected_index=indices[rid]['eligible_measurement_identity_index']=='True')
            for i in range(len(codes)):
                writer.writerow(dict(recording_id=rid,stored_epoch_0based=i,source_event_index_1based=int(events[i]),
                    code=int(codes[i]),sample_0based=int(samples[i]),frontoposterior_ptp_uv=float(ptp[i]),
                    primary_accepted=bool(masks[i,0]),frontoposterior100_accepted=bool(frontalmask[i]),scalp100_accepted=bool(masks[i,1])))
            splits={'alternating_30s_blocks':blocks%2==1,'early_late':samples>(samples.min()+samples.max())/2}
            for vi,variant in enumerate(cfg['variants']):
                mask=vmasks[vi];score=scores[vi]
                counts=[int(np.sum(mask&(codes==c))) for c in (1,2)]
                nblocks=[len(np.unique(blocks[mask&(codes==c)])) for c in (1,2)]
                enough=min(counts)>=cfg['minimum_trials_each_code'] and min(nblocks)>=cfg['minimum_occupied_30s_blocks_each_code']
                means=condition_scores(score[mask],codes[mask])
                qc_rows.append(dict(**base,variant=variant,n_code1=counts[0],n_code2=counts[1],
                    occupied_blocks_code1=nblocks[0],occupied_blocks_code2=nblocks[1],full_measurement=bool(enough),
                    primary_extra_rejected=int(np.sum(masks[:,0]&~mask)),primary_marker_ptp_median_uv=float(np.median(ptp[masks[:,0]]))))
                for ci,condition in enumerate(CONDITIONS):
                    feature_rows.append(dict(**base,variant=variant,condition=condition,mean_uv=float(means[ci]) if enough else np.nan,
                        measurement_status='measured' if enough else 'insufficient_both_code_support',n_code1=counts[0],n_code2=counts[1]))
                for split,half_b in splits.items():
                    counts_half=[int(np.sum(mask&(codes==c)&(half_b==side))) for side in (False,True) for c in (1,2)]
                    halfok=enough and min(counts_half)>=cfg['minimum_trials_each_code_each_half']
                    # Same RNG token across references => exactly the same matched trial subset.
                    balanced=balanced_selection(codes,mask,half_b,seed_for(cfg['random_seed'],rid+split))
                    for sampling,selected in [('all_accepted',mask),('balanced_per_code',balanced)]:
                        aa=condition_scores(score[selected&~half_b],codes[selected&~half_b])
                        bb=condition_scores(score[selected&half_b],codes[selected&half_b])
                        ns=[int(np.sum(selected&(codes==c)&(half_b==side))) for side in (False,True) for c in (1,2)]
                        for ci,condition in enumerate(CONDITIONS):
                            half_rows.append(dict(**base,variant=variant,split=split,sampling=sampling,condition=condition,
                                half_a_uv=float(aa[ci]) if halfok else np.nan,half_b_uv=float(bb[ci]) if halfok else np.nan,
                                n_a_code1=ns[0],n_a_code2=ns[1],n_b_code1=ns[2],n_b_code2=ns[3],
                                half_status='measured' if halfok else 'insufficient_full_or_half_support'))
                if vi==0 and enough:
                    for length in cfg['uncertainty_block_lengths_s']:
                        block=np.floor(samples[mask]/float(row['sfreq_hz'])/length).astype(int)
                        boot=block_bootstrap_scores(score[mask,None],codes[mask],block,cfg['block_bootstrap_repetitions'],seed_for(cfg['random_seed'],rid+str(length)))
                        for ci,condition in enumerate(CONDITIONS):
                            bs=boot[:,ci,0];bs=bs[np.isfinite(bs)]
                            valid=len(bs)>=.95*cfg['block_bootstrap_repetitions']
                            block_rows.append(dict(**base,condition=condition,block_length_s=length,n_blocks=len(np.unique(block)),
                                bootstrap_valid=len(bs),se_uv=float(bs.std(ddof=1)) if valid else np.nan,
                                ci_low_uv=float(np.quantile(bs,.025)) if valid else np.nan,ci_high_uv=float(np.quantile(bs,.975)) if valid else np.nan))
            verified.append(dict(recording_id=rid,epoch_hash_verified=True,nested_marker_mask=True,epochs=len(codes)))
            print(json.dumps({'recording_id':rid,'epochs':len(codes)}),flush=True)
    features=pd.DataFrame(feature_rows);halves=pd.DataFrame(half_rows)
    for name,rows in [('features',feature_rows),('half_scores',half_rows),('block_uncertainty',block_rows),('recording_qc',qc_rows),('verification',verified)]:
        table(out/(name+'.csv'),rows)
    # Independent agreement with executed Phase1 primary scoring, on common valid support.
    old=pd.read_csv(BASE/'results/phase1_measurements_001/features.csv')
    old=old[(old.variant=='hp01_avg_150')&(old.window=='mean_50_250ms')][['recording_id','condition','mean_uv']]
    cross=features[features.variant=='hp01_avg20'].merge(old,on=['recording_id','condition'],suffixes=('_new','_old')).dropna(subset=['mean_uv_new','mean_uv_old'])
    max_delta=float(abs(cross.mean_uv_new-cross.mean_uv_old).max())
    assert max_delta<1e-6
    eligible=halves[halves.selected_index].copy()
    assert eligible.groupby('participant_id').recording_id.nunique().max()==1
    reliability=[]
    keys=['cohort_label','split','sampling','condition']
    for group,frame in eligible.groupby(keys):
        meta=dict(zip(keys,group))
        complete=frame.dropna(subset=['half_a_uv','half_b_uv'])
        common=complete.groupby('recording_id').variant.nunique()
        common_ids=set(common[common==len(cfg['variants'])].index)
        for support in ('variant_available','all_variants_common'):
            for variant in cfg['variants']:
                ff=complete[complete.variant==variant]
                if support=='all_variants_common': ff=ff[ff.recording_id.isin(common_ids)]
                row=dict(**meta,variant=variant,support=support,n_candidates=len(ff),status='insufficient_candidates')
                if len(ff)>=cfg['minimum_candidates_for_reliability']:
                    row.update(pair_summary(ff[['half_a_uv','half_b_uv']].to_numpy(),seed_for(cfg['random_seed'],str(group)+support),cfg['reliability_bootstrap_repetitions']))
                    row['status']='estimated_within_acquisition_only'
                reliability.append(row)
    table(out/'amplitude_agreement.csv',reliability)
    sensitivity=[]
    person_features=features[features.selected_index]
    for (cohort,condition),frame in person_features.groupby(['cohort_label','condition']):
        wide=frame.pivot(index='recording_id',columns='variant',values='mean_uv')
        for variant in cfg['variants'][1:]:
            pairs=wide[['hp01_avg20',variant]].dropna()
            row=dict(cohort_label=cohort,condition=condition,variant=variant,n_candidates=len(pairs),
                     matched_trials=variant.endswith('_matched'))
            if len(pairs)>=cfg['minimum_candidates_for_reliability']:
                row.update(pair_summary(pairs.to_numpy(),seed_for(cfg['random_seed'],cohort+condition+variant),cfg['reliability_bootstrap_repetitions']))
                row['median_abs_delta_uv']=float(np.median(abs(pairs[variant]-pairs.hp01_avg20)))
            sensitivity.append(row)
    table(out/'paired_processing_sensitivity.csv',sensitivity)
    # Plots show every eligible HA candidate; no outlier removal or axis clipping.
    selected=eligible[(eligible.cohort_label=='HA')&(eligible.variant=='hp01_avg20')&(eligible.sampling=='all_accepted')]
    fig,axs=plt.subplots(2,3,figsize=(12,7))
    rel=pd.DataFrame(reliability)
    for si,split in enumerate(cfg['split_definitions']):
        for ci,condition in enumerate(CONDITIONS):
            ff=selected[(selected.split==split)&(selected.condition==condition)].dropna(subset=['half_a_uv','half_b_uv'])
            ax=axs[si,ci];ax.scatter(ff.half_a_uv,ff.half_b_uv,s=16,alpha=.7)
            if len(ff):
                lim=[ff[['half_a_uv','half_b_uv']].to_numpy().min(),ff[['half_a_uv','half_b_uv']].to_numpy().max()]
                ax.plot(lim,lim,'k--',lw=.7)
            rr=rel[(rel.cohort_label=='HA')&(rel.variant=='hp01_avg20')&(rel.sampling=='all_accepted')&(rel.support=='variant_available')&(rel.split==split)&(rel.condition==condition)].iloc[0]
            ax.set(title=f'{condition} | n={len(ff)} | ICC={rr.get("icc_a1",np.nan):.2f}',xlabel='Half A score (uV)',ylabel='Half B score (uV)')
            if ci==0:ax.text(0,1.14,split,transform=ax.transAxes,fontsize=10)
    fig.suptitle('HA candidate index records: amplitude agreement within one acquisition')
    fig.tight_layout();fig.savefig(figs/'half_amplitude_agreement.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for ax,condition in zip(axs,['code1','code2_minus_code1']):
        rr=rel[(rel.cohort_label=='HA')&(rel.condition==condition)&(rel.sampling=='all_accepted')&(rel.split=='early_late')&(rel.support=='all_variants_common')]
        for j,variant in enumerate(cfg['variants']):
            r=rr[rr.variant==variant].iloc[0]
            if r.status.startswith('estimated'):
                ax.plot([r.icc_a1_ci_low,r.icc_a1_ci_high],[j,j],color='C0');ax.plot(r.icc_a1,j,'o',color='C0')
        ax.set_yticks(range(len(cfg['variants'])),cfg['variants'],fontsize=8)
        ax.axvline(0,color='k',lw=.5);ax.set(xlabel='ICC(A,1), bootstrap percentile interval',title=f'{condition} | common n={rr.iloc[0].n_candidates}')
    fig.tight_layout();fig.savefig(figs/'common_support_sensitivity.png',dpi=160);plt.close(fig)
    br=pd.DataFrame(block_rows);blocksummary=[]
    for (cohort,condition),frame in br[br.selected_index].groupby(['cohort_label','condition']):
        wide=frame.pivot(index='recording_id',columns='block_length_s',values='se_uv')
        for length in cfg['uncertainty_block_lengths_s']:
            vv=wide[[30,length]].iloc[:,[0,-1]].dropna().to_numpy()
            ratios=vv[:,1]/vv[:,0] if len(vv) else np.array([])
            blocksummary.append(dict(cohort_label=cohort,condition=condition,block_length_s=length,n=len(vv),
                median_se_uv=float(np.median(vv[:,1])) if len(vv) else None,
                median_ratio_to_30s=float(np.median(ratios)) if len(vv) else None))
    table(out/'block_uncertainty_summary.csv',blocksummary)
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],config_sha256=digest(cfgpath),recordings_processed=len(verified),
        input_index_sha256=digest(BASE/'results'/cfg['cohort_run']/'index_recordings.csv'),
        input_source_manifest_sha256=digest(BASE/'results/phase1_sources_001/source_manifest.csv'),
        epochs_examined=sum(r['epochs'] for r in verified),phase1_score_max_abs_difference_uv=max_delta,
        primary_measurable_index_by_cohort=dict(Counter(r['cohort_label'] for r in feature_rows if r['selected_index'] and r['variant']=='hp01_avg20' and r['condition']=='code1' and r['measurement_status']=='measured')),
        primary_HA_agreement=[r for r in reliability if r['cohort_label']=='HA' and r['variant']=='hp01_avg20' and r['sampling']=='all_accepted' and r['support']=='variant_available'],
        primary_HA_block_uncertainty=[r for r in blocksummary if r['cohort_label']=='HA'],
        clinical_outcomes_used=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=True))
    checks=[dict(file=str(p.relative_to(BASE)),sha256=digest(p)) for p in sorted(out.rglob('*')) if p.is_file()]
    checks += [dict(file=str(p.relative_to(BASE)),sha256=digest(p)) for p in sorted(figs.iterdir())]
    table(out/'artifact_checksums.csv',checks)
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
