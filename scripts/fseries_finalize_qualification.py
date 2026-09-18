"""Aggregate completed F-series metadata audits; zero model fitting."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path('/home/infres/yinwang/EEG_auditory')


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'SLURM_REQUIRED'
    os.umask(0o077)
    private = ROOT / 'private/auditory_fseries/qualification_final_001'
    public = ROOT / 'results/auditory_fseries/qualification_final_001'
    assert not private.exists() and not public.exists(), 'RUN_OCCUPIED'
    private.mkdir(mode=0o700)
    public.mkdir(mode=0o700)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    read = lambda p: json.loads(p.read_text())
    files = {
        'HA': ROOT / 'results/auditory_fseries/ha_qualification_002/qualification_summary.json',
        'MFF': ROOT / 'results/auditory_fseries/ci_qualification_001/summary.json',
        'F4_supplement': ROOT / 'results/auditory_fseries/ci_qualification_001/f4_aggregate_supplement.json',
        'source_documents': ROOT / 'results/auditory_fseries/document_evidence_002/summary.json',
    }
    hashes = {k: sha(p) for k, p in files.items()}
    shutil.copyfile(Path(__file__), private / Path(__file__).name)
    shutil.copyfile(ROOT / 'configs/auditory_fseries_qualification_v1.json', private / 'config.json')
    (private / 'start.json').write_text(json.dumps(dict(job_id=os.environ['SLURM_JOB_ID'], input_hashes=hashes, script_sha256=sha(Path(__file__))), indent=2))
    ha, ci, f4, doc = [read(files[k]) for k in ['HA', 'MFF', 'F4_supplement', 'source_documents']]
    assert ha['clinical_group_counts'] == dict(HA=84, NH=11)
    assert all(v == 'SUPPORT_INSUFFICIENT' for v in ha['decision'].values())
    assert all(v == 'SUPPORT_INSUFFICIENT' for v in ci['route_gates'].values())
    assert (ci['canonical_eligible_sources'], ci['registered_clinical_rows'], ci['candidate_identity_groups']) == (203, 104, 87)
    assert len(doc['declared_scale_definitions']) == 4
    # Independent reconciliation of private pair/series rows, no EEG reads.
    rows = lambda rel: list(csv.DictReader((ROOT / rel).open()))
    series = rows('private/auditory_fseries/ci_qualification_001/f4_followup_evidence.csv')
    pairs = rows('private/auditory_fseries/ci_qualification_001/f3_pair_evidence.csv')
    assert len(series) == f4['f4_identity_endpoint_series'] == 8
    assert len({r['participant_id'] for r in series}) == f4['f4_unique_candidate_identity_groups'] == 2
    assert len(pairs) == ci['f3']['candidate_task_day_pairs'] == 9
    assert sum(bool(r['same_day_clinical_target_endpoints']) and r['pair_unique_per_task'] == 'true' for r in pairs) == ci['f3']['unique_task_day_pairs_with_literal_target'] == 2
    route_rows = []
    for route, scope, denominator, unit, raw, reason in [
        ('F1', 'HA_archive', 84, 'clinical_rows', 84, 'row_scale_assignment_and_functional_assessment_time_unresolved'),
        ('F2', 'HA_archive', 84, 'clinical_rows', 84, 'functional_assessment_time_unresolved;auditory_version_mixed_header'),
        ('F1', 'all_canonical_MFF', 203, 'EEG_sources', 45, 'raw_percent_header_values_0_40;row_version_and_functional_date_role_unresolved'),
        ('F2', 'all_canonical_MFF', 203, 'EEG_sources', 45, 'raw_percent_header_values_0_40;functional_date_role_unresolved'),
        ('F1', 'expanded_CI_evidence_scope', 41, 'EEG_sources', 2, 'source_evidence_not_diagnosis;same_scale_time_limits'),
        ('F2', 'expanded_CI_evidence_scope', 41, 'EEG_sources', 2, 'source_evidence_not_diagnosis;same_scale_time_limits'),
        ('F3', 'MFF_same_candidate_day_puretone_bapa', 9, 'candidate_task_pairs', 2, 'only_two_pairs_with_literal_target;target_comparability_and_time_unresolved'),
        ('F4', 'HA_repeated_vendor_acquisitions', 13, 'candidate_identity_groups', 13, 'fifteen_acquisition_pairs;no_confirmed_functional_assessment_dates'),
        ('F4', 'MFF_repeated_dated_archive_values', 87, 'candidate_identity_groups', 2, 'eight_identity_endpoint_series;functional_date_role_unresolved'),
    ]:
        route_rows.append(dict(route=route, scope=scope, denominator=denominator, count_unit=unit,
            raw_archive_or_historical_EEG_intersection=raw, fully_interpretable_clinical_intersection=0,
            qualification='SUPPORT_INSUFFICIENT', model_execution='NOT_STARTED_DATA_GATE', reason=reason))
    with (public / 'route_support.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(route_rows[0]))
        writer.writeheader()
        writer.writerows(route_rows)
    endpoints = []
    for name, info in ha['scale_definitions'].items():
        x = info['HA']
        endpoints.append(dict(scope='HA_clinical_rows', endpoint=name, denominator=x['rows'], available=x['nonmissing'],
            observed_min=x['observed_min'], observed_max=x['observed_max'], missing=x['missing'],
            literal_100_count=x['ceiling_100_n'] if name in ['MUSS', 'IT-MAIS/MAIS'] else '',
            primary_status='NOT_FROZEN_PENDING_CLINICAL_TIME_AND_VERSION', unit_evidence=info['literal_header']))
    for info in ci['endpoint_definitions']:
        n = info['registered_rows_with_unique_literal_numeric_value']
        endpoints.append(dict(scope='MFF_linked_clinical_archive_rows', endpoint=info['endpoint'], denominator=104, available=n,
            observed_min=info['literal_numeric_min'], observed_max=info['literal_numeric_max'], missing=104-n,
            literal_100_count='', primary_status='NOT_FROZEN_PENDING_CLINICAL_TIME_AND_VERSION', unit_evidence=info['unit_status']))
    with (public / 'endpoint_definitions.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(endpoints[0]))
        writer.writeheader()
        writer.writerows(endpoints)
    summary = dict(status='QUALIFICATION_COMPLETE_SUPPORT_INSUFFICIENT', job_id=os.environ['SLURM_JOB_ID'],
        stage='1_clinical_visit_qualification', input_hashes=hashes, new_model_fits=0, new_signal_features=0, gpu_jobs=0,
        eeg_outcome_associations_computed=False, routes=route_rows,
        interpretation='Data qualification is complete, not F1-F4 prediction experiments. Zero interpretable intersections refer to current evidence requirements, not absence of physiological information or absence of archival scores.',
        important_corrections=['original_HA_document_defines_four_scales', 'MFF_F4_eight_series_are_two_candidate_groups',
            'historical_EEG_measurement_support_not_new_functional_feature_eligibility', 'MFF_row_dates_not_confirmed_questionnaire_dates'],
        automatic_push=False)
    for path in [public / 'summary.json', private / 'completion.json']:
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status=summary['status'], job_id=summary['job_id'], routes=4, model_fits=0)))


if __name__ == '__main__':
    main()
