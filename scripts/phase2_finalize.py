"""Independent table reconciliation and compact Phase2 result summaries."""
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
from phase1_epochs import digest
from phase1_prepare import table

BASE=Path(__file__).resolve().parents[1]


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    out=BASE/'results/phase2_final_001';out.mkdir(exist_ok=False)
    cfg=json.loads((BASE/'configs/phase2_v1.json').read_text());chash=digest(BASE/'configs/phase2_v1.json')
    assert digest(BASE/'configs/phase1_v1.json')==cfg['phase1_config_sha256']
    sums={name:json.loads((BASE/'results'/('phase2_'+name+'_001')/'summary.json').read_text()) for name in ['cohort','measurements','archival']}
    assert all(s['config_sha256']==chash for s in sums.values())
    ix=pd.read_csv(BASE/'results/phase2_cohort_001/index_recordings.csv')
    assert len(ix)==93 and ix.recording_id.nunique()==93
    assert ix.groupby('participant_id').index_recording_flag.sum().eq(1).all()
    eligible=ix[ix.eligible_measurement_identity_index]
    assert eligible.index_recording_flag.all() and not eligible.identity_dob_conflict.any()
    assert (eligible.source_gate=='eligible_technical_measurement').all()
    ledger=pd.read_csv(BASE/'results/phase2_measurements_001/epoch_sensitivity_ledger.csv')
    assert len(ledger)==80441 and ledger.recording_id.nunique()==84
    assert ledger.primary_accepted.sum()==57879
    assert (ledger.frontoposterior100_accepted<=ledger.primary_accepted).all()
    assert (ledger.scalp100_accepted<=ledger.primary_accepted).all()
    assert not ledger.duplicated(['recording_id','stored_epoch_0based']).any()
    assert np.isfinite(ledger.frontoposterior_ptp_uv).all()
    features=pd.read_csv(BASE/'results/phase2_measurements_001/features.csv')
    halves=pd.read_csv(BASE/'results/phase2_measurements_001/half_scores.csv')
    qc=pd.read_csv(BASE/'results/phase2_measurements_001/recording_qc.csv')
    for variant in ['hp05_avg20_matched','hp01_avg18_matched']:
        primary=halves[halves.variant=='hp01_avg20'].set_index(['recording_id','split','sampling','condition'])
        other=halves[halves.variant==variant].set_index(['recording_id','split','sampling','condition'])
        cols=['n_a_code1','n_a_code2','n_b_code1','n_b_code2','half_status']
        assert primary[cols].equals(other[cols])
    # Per-record ledger counts must agree with all sensitivity tables.
    for name,field in [('hp01_avg20','primary_accepted'),('hp01_frontoposterior100','frontoposterior100_accepted'),('hp01_scalp100','scalp100_accepted')]:
        for r in qc[qc.variant==name].itertuples():
            ll=ledger[(ledger.recording_id==r.recording_id)&ledger[field]]
            assert (ll.code==1).sum()==r.n_code1 and (ll.code==2).sum()==r.n_code2
    n_hashes=0
    for name in ['measurements','archival']:
        checks=pd.read_csv(BASE/'results'/('phase2_'+name+'_001')/'artifact_checksums.csv')
        for r in checks.itertuples():
            assert digest(BASE/r.file)==r.sha256
            n_hashes+=1
    arch=sums['archival']
    if arch['status']=='exploratory_completed':
        folds=pd.read_csv(BASE/'results/phase2_archival_001/candidate_folds.csv')
        pred=pd.read_csv(BASE/'private/phase2_archival_001/out_of_fold_predictions.csv')
        elig=pd.read_csv(BASE/'results/phase2_archival_001/candidate_eligibility.csv')
        chosen=set(elig[elig.eligible].participant_id)
        assert len(chosen)==arch['complete_HA_candidates']
        assert set(folds.participant_id)==chosen and set(pred.participant_id)==chosen
        assert not folds.duplicated(['participant_id','repeat']).any()
        assert folds.groupby('repeat').size().eq(len(chosen)).all()
        assert folds.groupby('repeat').fold.nunique().eq(cfg['archival_analysis']['outer_folds']).all()
        assert pred.groupby(['repeat','model']).size().eq(len(chosen)).all()
        assert pred.groupby('participant_id').MUSS_actual.nunique().eq(1).all()
        assert pred.MUSS_prediction.between(0,100).all()
        assert not pred.duplicated(['participant_id','repeat','model']).any()
        pred['loss']=abs(pred.MUSS_prediction-pred.MUSS_actual)
        mae=pred.groupby('model').loss.mean()
        for r in arch['models']:
            assert abs(mae[r['model']]-r['MAE_percentage_points'])<1e-10
        assert abs(mae['clinical_plus_EEG']-mae['clinical_age_duration']-arch['paired_MAE_delta_percentage_points'])<1e-10
    r=pd.read_csv(BASE/'results/phase2_measurements_001/amplitude_agreement.csv')
    subset=r[(r.cohort_label=='HA')&(r.sampling=='all_accepted')]
    cols=['variant','split','condition','support','n_candidates','icc_a1','icc_a1_ci_low','icc_a1_ci_high','pearson_r','bias_b_minus_a_uv']
    table(out/'HA_agreement_summary.csv',subset[cols].to_dict('records'))
    support=[]
    for (cohort,variant),frame in qc[qc.selected_index].groupby(['cohort_label','variant']):
        support.append(dict(cohort=cohort,variant=variant,index_candidates=len(frame),measurable=int(frame.full_measurement.sum()),
            accepted_epochs=int((frame.n_code1+frame.n_code2).sum()),additional_rejected_epochs=int(frame.primary_extra_rejected.sum()),
            median_code1_trials=float(frame.n_code1.median()),median_code2_trials=float(frame.n_code2.median())))
    table(out/'candidate_measurement_support.csv',support)
    sens=pd.read_csv(BASE/'results/phase2_measurements_001/paired_processing_sensitivity.csv')
    primary_common=subset[(subset.split=='early_late')&(subset.condition=='code1')&(subset.support=='all_variants_common')]
    balanced=r[(r.cohort_label=='HA')&(r.variant=='hp01_avg20')&(r.sampling=='balanced_per_code')&(r.support=='variant_available')]
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],status='passed',config_sha256=chash,hashed_artifacts_verified=n_hashes,
        source_records=len(ix),candidate_indices=int(ix.index_recording_flag.sum()),source_identity_eligible_indices=len(eligible),
        epochs_reconciled=len(ledger),primary_accepted_reconciled=int(ledger.primary_accepted.sum()),
        candidate_support=support,
        primary_HA_early_late_common_support=primary_common[cols].to_dict('records'),
        primary_HA_balanced_halves=balanced[cols].to_dict('records'),
        primary_HA_processing_sensitivity=sens[(sens.cohort_label=='HA')&(sens.condition=='code1')][['variant','n_candidates','matched_trials','icc_a1','pearson_r','median_abs_delta_uv']].to_dict('records'),
        archival_status=arch['status'],archival_candidates=arch['complete_HA_candidates'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
