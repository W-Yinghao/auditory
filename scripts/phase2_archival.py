"""Fixed exploratory archival-label feasibility; not concurrent clinical validation."""
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
from phase1_epochs import digest
from phase1_prepare import table
from phase2_core import ridge_predict

BASE=Path(__file__).resolve().parents[1]
MODELS={'training_mean':[], 'clinical_age_duration':['clinical_age_months','duration_months'],
        'EEG_only':['mean_uv'], 'clinical_plus_EEG':['clinical_age_months','duration_months','mean_uv']}


def repeated_cv(xframe,y,pids,cfg,seed):
    n=len(y)
    assert len(set(pids))==n, 'more than one index record per candidate'
    assert np.isfinite(y).all()
    preds={m:np.full((cfg['repeats'],n),np.nan) for m in MODELS}
    rows=[];rng=np.random.default_rng(seed)
    for rep in range(cfg['repeats']):
        folds=np.array_split(rng.permutation(n),cfg['outer_folds'])
        seen=np.zeros(n,int)
        for fold,test in enumerate(folds):
            train=np.setdiff1d(np.arange(n),test)
            assert not set(pids[train])&set(pids[test])
            seen[test]+=1
            for i in test:rows.append(dict(participant_id=pids[i],repeat=rep,fold=fold))
            for model,cols in MODELS.items():
                x=xframe[cols].to_numpy(float)
                assert np.isfinite(x).all()
                pred=ridge_predict(x[train],y[train],x[test],cfg['ridge_alpha'])
                preds[model][rep,test]=np.clip(pred,*cfg['prediction_clip'])
        assert np.all(seen==1), 'each candidate must be tested exactly once per repeat'
    assert all(np.isfinite(p).all() for p in preds.values())
    return preds,rows


def main():
    assert os.environ.get('SLURM_JOB_ID'),'Slurm required'
    os.umask(0o077)
    cfgpath=BASE/'configs/phase2_v1.json';fullcfg=json.loads(cfgpath.read_text());cfg=fullcfg['archival_analysis']
    out=BASE/'results/phase2_archival_001';out.mkdir(exist_ok=False)
    private=BASE/'private/phase2_archival_001';private.mkdir(mode=0o700,exist_ok=False)
    figs=BASE/'figures/phase2_archival_001';figs.mkdir(exist_ok=False)
    snap=out/'code_snapshot';snap.mkdir()
    for path in [cfgpath,Path(__file__),BASE/'scripts/phase2_core.py',BASE/'docs/PHASE2_PROTOCOL.md']:
        shutil.copy2(path,snap/path.name)
    ixpath=BASE/'results/phase2_cohort_001/index_recordings.csv'
    linkpath=BASE/'private/phase2_cohort_001/linked_index.csv'
    featurepath=BASE/'results/phase2_measurements_001/features.csv'
    ix=pd.read_csv(ixpath); links=pd.read_csv(linkpath)
    features=pd.read_csv(featurepath)
    ff=features[(features.variant=='hp01_avg20')&(features.condition=='code1')][['recording_id','mean_uv','measurement_status']]
    joined=ix.merge(links[['recording_id','participant_id','clinical_row_id','clinical_age_months','duration_months','MUSS','clinical_age_minus_dob_age_months']],on=['recording_id','participant_id'],validate='one_to_one').merge(ff,on='recording_id',how='left',validate='one_to_one')
    reasons=[]
    for _,r in joined.iterrows():
        why=[]
        if r.cohort!='HA':why.append('outside_HA')
        if not r.eligible_measurement_identity_index:why.append('index_identity_source_hold')
        if not r.strong_unique_link:why.append('not_unique_name_plus_label_date')
        if r.measurement_status!='measured' or not np.isfinite(r.mean_uv):why.append('EEG_measurement_missing')
        if not np.isfinite(r.MUSS):why.append('MUSS_missing')
        elif not 0<=r.MUSS<=100:why.append('MUSS_out_of_percentage_range')
        if not np.isfinite(r.clinical_age_months) or r.clinical_age_months<0:why.append('age_missing_or_negative')
        if not np.isfinite(r.duration_months) or r.duration_months<0:why.append('duration_missing_or_negative')
        reasons.append('|'.join(why))
    joined['exclusion_reasons']=reasons
    joined.to_csv(private/'candidate_flow_and_values.csv',index=False)
    table(out/'candidate_eligibility.csv',[dict(recording_id=r.recording_id,participant_id=r.participant_id,
        eligible=r.exclusion_reasons=='',exclusion_reasons=r.exclusion_reasons) for r in joined.itertuples()])
    selected=joined[joined.exclusion_reasons==''].sort_values('participant_id').reset_index(drop=True)
    assert selected.participant_id.nunique()==len(selected)
    assert selected.clinical_row_id.nunique()==len(selected), 'same clinical row linked to multiple candidate people'
    # Never change the index or choose a feature based on MUSS values.
    y=selected.MUSS.to_numpy(float);pids=selected.participant_id.to_numpy()
    agegap=selected.clinical_age_minus_dob_age_months.dropna().to_numpy()
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],config_sha256=digest(cfgpath),scope=cfg['scope'],
        formal_clinical_validity_claim=False,complete_HA_candidates=len(selected),
        index_selection_outcome_blind=True,confirmed_concurrent_scale_links=0,
        no_tuning=True,primary_eeg_condition='code1',window_ms=[50,250],
        clinical_baseline_limitation='age and device-use duration only; no validated hearing/audibility covariate',
        input_sha256={str(p.relative_to(BASE)):digest(p) for p in [ixpath,linkpath,featurepath]},
        exclusions_multilabel=dict(Counter(reason for why in reasons for reason in why.split('|') if reason)),
        selected_label_audit=dict(MUSS_ceiling_n=int(np.sum(y==100)),MUSS_min=float(y.min()) if len(y) else None,
            MUSS_max=float(y.max()) if len(y) else None,age_gap_available=len(agegap),
            age_gap_abs_over_3_months=int(np.sum(abs(agegap)>3)),age_gap_abs_over_12_months=int(np.sum(abs(agegap)>12)),
            duration_greater_than_age_n=int(np.sum(selected.duration_months>selected.clinical_age_months))),
        metric_units='MUSS percentage points')
    if len(selected)<cfg['minimum_complete_candidates']:
        summary['status']='not_run_insufficient_complete_candidates'
    else:
        preds,folds=repeated_cv(selected,y,pids,cfg,fullcfg['random_seed'])
        table(out/'candidate_folds.csv',folds)
        allpred=[];metrics=[];losses={}
        sst=float(np.sum((y-y.mean())**2))
        for model,pred in preds.items():
            error=pred-y[None,:];abs_loss=abs(error).mean(axis=0);sq_loss=(error**2).mean(axis=0)
            losses[model]=abs_loss
            metrics.append(dict(model=model,n_candidates=len(y),MAE_percentage_points=float(abs_loss.mean()),
                RMSE_percentage_points=float(np.sqrt(sq_loss.mean())),R2=float(1-sq_loss.sum()/sst) if sst>0 else np.nan,
                averaging='loss_across_repeats_per_candidate_then_equal_candidate_weight',
                clipped_to_scale=True))
            for rep in range(cfg['repeats']):
                for i,pid in enumerate(pids):allpred.append(dict(participant_id=pid,recording_id=selected.iloc[i].recording_id,
                    repeat=rep,model=model,MUSS_actual=float(y[i]),MUSS_prediction=float(pred[rep,i])))
        table(private/'out_of_fold_predictions.csv',allpred)
        table(out/'model_metrics.csv',metrics)
        rng=np.random.default_rng(fullcfg['random_seed']+1)
        delta=losses['clinical_plus_EEG']-losses['clinical_age_duration']
        draws=rng.integers(len(y),size=(cfg['loss_bootstrap_repetitions'],len(y)))
        bootstrap=delta[draws].mean(axis=1)
        interval=np.quantile(bootstrap,[.025,.975])
        rep_delta=abs(preds['clinical_plus_EEG']-y).mean(axis=1)-abs(preds['clinical_age_duration']-y).mean(axis=1)
        table(out/'repeat_metrics.csv',[dict(repeat=rep,paired_MAE_delta=float(v),scope='dependent_repeat_descriptive_not_independent_sample') for rep,v in enumerate(rep_delta)])
        summary.update(status='exploratory_completed',models=metrics,
            paired_MAE_delta_percentage_points=float(delta.mean()),
            paired_MAE_delta_conditional_bootstrap_ci=[float(v) for v in interval],
            conditional_bootstrap_scope=cfg['bootstrap_scope'],
            repeat_delta_range=[float(rep_delta.min()),float(rep_delta.max())],
            repeats=cfg['repeats'],folds=cfg['outer_folds'],independent_sample_unit='candidate_identity_cluster_not_epoch')
        fig,axs=plt.subplots(1,2,figsize=(11,4))
        labels=['Mean','Age + use','EEG','Age + use + EEG']
        axs[0].bar(labels,[r['MAE_percentage_points'] for r in metrics],color=['.6','C0','C2','C1'])
        axs[0].set(ylabel='MUSS MAE (percentage points)',title=f'Archival-label feasibility | n={len(y)} HA candidates')
        axs[0].tick_params(axis='x',labelsize=8)
        axs[1].hist(bootstrap,bins=45,color='C1',alpha=.75)
        axs[1].axvline(0,color='k',lw=1);axs[1].axvline(delta.mean(),color='C3',ls='--')
        axs[1].set(xlabel='MAE: age + use + EEG minus age + use',ylabel='Fixed-OOF loss bootstrap draws',title='Negative = improvement; interval excludes retraining uncertainty')
        fig.tight_layout();fig.savefig(figs/'archival_feasibility.png',dpi=160);plt.close(fig)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    table(out/'artifact_checksums.csv',[dict(file=str(p.relative_to(BASE)),sha256=digest(p)) for root in [out,private,figs] for p in sorted(root.rglob('*')) if p.is_file()])
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
