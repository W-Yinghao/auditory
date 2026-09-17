"""Summarize fixed comparisons, reconcile per-epoch bookkeeping and archive metadata."""
import csv
import json
import os
import shutil
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from phase1_prepare import readcsv,table
from phase1_epochs import digest

BASE=Path(__file__).resolve().parents[1]


def describe(values):
    a=np.asarray(values,float);a=a[np.isfinite(a)]
    return dict(n=len(a),median=float(np.median(a)) if len(a) else None,
                q25=float(np.quantile(a,.25)) if len(a) else None,q75=float(np.quantile(a,.75)) if len(a) else None)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    out=BASE/'results/phase1_final_001';out.mkdir(exist_ok=False)
    private=BASE/'private/phase1_final_001';private.mkdir(mode=0o700,exist_ok=False)
    src=BASE/'results/phase1_epochs_001';meas=BASE/'results/phase1_measurements_001'
    config_hash=digest(BASE/'configs/phase1_v1.json')
    manifest=readcsv(BASE/'results/phase1_sources_001/source_manifest.csv')
    records={r['recording_id']:r for r in manifest}
    rows={p.parent.name:json.loads(p.read_text()) for p in src.glob('B*/summary.json')}
    assert set(records)==set(rows) and len(rows)==93
    features=readcsv(meas/'features.csv'); counts=readcsv(meas/'trial_counts.csv')
    halves=readcsv(meas/'split_agreement.csv'); sens=readcsv(meas/'sensitivity.csv')
    primary={r['recording_id']:r for r in counts if r['variant']=='hp01_avg_150'}
    checks=[];rejection=Counter();allledger=[]
    for rid,row in rows.items():
        assert row['config_sha256']==config_hash
        if row['status']!='epochs_created':
            assert row['source_gate']=='hold'
            continue
        led=readcsv(src/rid/'epoch_ledger.csv')
        counts_codes=Counter(r['event_code'] for r in led)
        assert counts_codes==Counter(json.loads(row['annotation_counts']))
        accepted=[r for r in led if r['disposition']=='accepted']
        target=[r for r in led if r['event_code'] in ('1','2')]
        assert len(target)==row['n_target_events']
        assert len(accepted)==row['accepted_150uv']
        assert all(r['accepted_150uv']=='True' for r in accepted)
        q=primary[rid]
        assert int(q['n_code1'])==row['accepted_150uv_code1']
        assert int(q['n_code2'])==row['accepted_150uv_code2']
        if q['measurement_status']=='sufficient_trials_and_blocks':
            assert min(int(q['n_code1']),int(q['n_code2']))>=40
            assert min(int(q['occupied_blocks_code1']),int(q['occupied_blocks_code2']))>=8
        for r in target:
            rejection.update(json.loads(r['reasons']))
        allledger.extend(led)
        checks.append(dict(recording_id=rid,source_event_counts_match=True,target_counts_match=True,
                           primary_acceptance_matches=True,measurement_gate_verified=True))
    table(out/'epoch_ledger.csv',allledger)
    table(out/'bookkeeping_checks.csv',checks)
    enough={rid for rid,q in primary.items() if q['measurement_status']=='sufficient_trials_and_blocks'}
    cohorts=[]
    for group in ('HA','NH'):
        allsource=[r for r in records.values() if r['cohort_label']==group]
        processed=[rows[r['recording_id']] for r in allsource if rows[r['recording_id']]['status']=='epochs_created']
        good=[r for r in processed if r['recording_id'] in enough]
        summary=dict(cohort=group,source_records=len(allsource),source_eligible_records=len(processed),
            stored_epochs_before_amplitude_qc=sum(r['stored_epochs'] for r in processed),
            accepted_epochs_150uv=sum(r['accepted_150uv'] for r in processed),
            records_with_sufficient_trials_and_blocks=len(good),candidate_identity_groups_with_sufficient_measurements=len({r['participant_id'] for r in good}),
            sufficient_records_with_dob_conflict=sum(r['identity_dob_conflict']=='True' for r in good),
            median_retention_fraction=describe([float(primary[r['recording_id']]['retention_fraction']) for r in processed])['median'])
        cohorts.append(summary)
    table(out/'cohort_flow.csv',cohorts)
    comparisons=[]
    for variant in sorted({r['variant'] for r in sens}):
        for condition in ('code1','code2','code2_minus_code1'):
            rr=[r for r in sens if r['variant']==variant and r['condition']==condition and r['window']=='mean_50_250ms' and r['recording_id'] in enough]
            valid=[r for r in rr if np.isfinite(float(r['delta_uv']))]
            delta=[float(r['delta_uv']) for r in valid]
            base=[float(r['baseline_mean_uv']) for r in valid];other=[float(r['variant_mean_uv']) for r in valid]
            corr=float(np.corrcoef(base,other)[0,1]) if len(valid)>=3 and np.std(base)>0 and np.std(other)>0 else np.nan
            d=describe(delta);ad=describe(np.abs(delta))
            comparisons.append(dict(variant=variant,condition=condition,window='mean_50_250ms',n_paired_records=len(valid),
                median_delta_uv=d['median'],median_abs_delta_uv=ad['median'],record_score_correlation=corr,
                unit='records_not_independent_children'))
    table(out/'processing_sensitivity_summary.csv',comparisons)
    # Within-person repeats remain grouped as candidate identities; no reliability ICC is inferred.
    groups=defaultdict(list)
    for rid in enough:groups[rows[rid]['participant_id']].append(rid)
    table(out/'measurement_candidate_groups.csv',[dict(participant_id=pid,recording_ids=json.dumps(sorted(ids)),
        n_records=len(ids),identity_status='candidate_only',repeat_status='acquisition_repeat_candidate_not_confirmed_visit')
        for pid,ids in sorted(groups.items())])
    # Archive the old smoke metadata containing exact source mtime, then remove only that field.
    moved=0
    for folder in ('phase1_smoke_001','phase1_measure_smoke_001'):
        root=BASE/'results'/folder
        if not root.exists():continue
        for p in root.glob('B*/summary.json'):
            value=json.loads(p.read_text())
            if 'source_signal_mtime_ns' in value:
                target=private/folder/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(p,target);value.pop('source_signal_mtime_ns')
                p.write_text(json.dumps(value,indent=2));moved+=1
        p=root/'recording_qc.csv'
        if p.exists():
            rr=readcsv(p)
            if rr and 'source_signal_mtime_ns' in rr[0]:
                target=private/folder/p.name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(p,target)
                for r in rr:r.pop('source_signal_mtime_ns',None)
                table(p,rr);moved+=1
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],status='passed',cohort_flow=cohorts,
        complete_source_records=93,epoch_records_verified=len(checks),canonical_annotation_rows=len(allledger),
        rejection_reason_counts=dict(rejection),rejection_counts_are_nonexclusive=True,
        sufficient_candidate_identity_groups=len(groups),candidate_groups_with_repeat_measurements=sum(len(ids)>1 for ids in groups.values()),
        processing_sensitivity=comparisons,archived_smoke_metadata_tables=moved,
        clinical_outcomes_used=False,source_data_modified=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    # Capture the final methods plus all Phase 1 result tables and summaries.
    paths=[BASE/'configs/phase1_v1.json',BASE/'docs/PHASE1_MEASUREMENT_PROTOCOL.md']
    paths+=list((BASE/'scripts').glob('phase1_*.py'))
    for root in (out,meas,BASE/'results/phase1_sources_001'):
        paths += [p for p in root.glob('*') if p.suffix in ('.json','.csv') and p.name!='artifact_checksums.csv']
    table(out/'artifact_checksums.csv',[dict(artifact=str(p.relative_to(BASE)),sha256=digest(p)) for p in sorted(set(paths))])
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
