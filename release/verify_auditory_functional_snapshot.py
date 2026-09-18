"""Slurm-only publication checks; bind existing evidence without scientific refits.

The V3 verifier supplies full-tree hashes, syntax, links, images, known-name
checks and preservation checks. This extension adds the new aggregate schemas,
broader identifier dictionary and functional/PTA/retraining receipt bindings.
Private dictionaries and science-root bindings are optional for public use.
"""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys

import verify_auditory_v3_snapshot as previous


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--known-names', type=Path)
    parser.add_argument('--known-identifiers', type=Path)
    parser.add_argument('--identifier-table', type=Path, action='append', default=[])
    parser.add_argument('--science-root', type=Path)
    parser.add_argument('--previous-manifest', type=Path)
    args = parser.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'SLURM_REQUIRED'
    os.umask(0o077)
    root = Path(__file__).resolve().parents[1]
    read = lambda p: json.loads(p.read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    base_args = [sys.argv[0]]
    for opt in ['known_names', 'science_root', 'previous_manifest']:
        if getattr(args, opt): base_args += ['--' + opt.replace('_', '-'), str(getattr(args, opt))]
    for path in args.identifier_table: base_args += ['--identifier-table', str(path)]
    sys.argv = base_args
    with contextlib.redirect_stdout(io.StringIO()):
        previous.main()
    report = read(root / 'release/verification.json')
    issues = report['issues']
    manifest = read(root / 'release/manifest.json')
    entries = {row['path']: row for row in manifest['files']}
    changes = read(root / 'release/auditory_functional_publication_changes.json')
    selected = changes['source_files']
    identifiers = set(read(args.known_identifiers)) if args.known_identifiers else set()
    opaque = re.compile(r'(?<![A-Za-z0-9])(?:B|P|G|M)[0-9a-f]{12,16}(?![A-Za-z0-9])')
    blocked = {'participant_id', 'recording_id', 'container_id', 'raw_name', 'normalized_name',
        'source_row', 'source_worksheet_row', 'clinical_row_ref', 'clinical_row_id', 'absolute_path',
        'raw_dob', 'raw_clinical_date', 'candidate_id', 'split_group_id', 'record_id', 'trial_id',
        'bag_id', 'matched_pair_id', 'candidate_key', 'raw_locator_key', 'fit_groups', 'test_groups',
        'validation_groups', 'train_groups', 'training_groups', 'signal_path', 'event_path',
        'original_path', 'source_path', 'prediction', 'model_weights', 'name', 'group'}
    counts = {'fit_groups', 'test_groups', 'validation_groups', 'train_groups', 'training_groups'}
    def issue(rel, kind): issues.append(dict(path=rel, type=kind))
    def inspect(value, rel, location=()):
        if isinstance(value, dict):
            if rel == 'results/auditory_fseries_archival/prepare_001/summary.json' and location == ('source_schema', 'literal_headers'):
                assert value['name'] == '姓名' and value['group'] == '分组'
                return
            bad = set(value) & blocked
            bad -= {k for k in bad & counts if type(value[k]) is int and value[k] >= 0}
            if bad: issue(rel, 'restricted_aggregate_fields:' + ','.join(sorted(bad)))
            for k, v in value.items(): inspect(v, rel, (*location, k))
        elif isinstance(value, list):
            for v in value: inspect(v, rel, location)
    exact = transformed = schemas = 0
    # Known IDs and opaque ID patterns apply to the complete current payload.
    for rel in entries:
        path = root / rel
        if path.suffix == '.pdf':
            from pdfminer.high_level import extract_text
            content = extract_text(str(path))
        elif path.suffix == '.png':
            from PIL import Image
            with Image.open(path) as im: content = json.dumps(im.info, default=str)
        else: content = path.read_text()
        if set(re.findall(r'[\w:.-]+', content)) & identifiers: issue(rel, 'expanded_known_identifier')
        if opaque.search(content): issue(rel, 'opaque_identifier_current_tree')
        if rel not in selected: continue
        if rel.startswith(('results/', 'reports/')):
            if re.search(r'/(?:home|projects|mnt|tmp)/', content): issue(rel, 'absolute_path_in_new_aggregate')
            if path.suffix == '.json':
                inspect(json.loads(content), rel); schemas += 1
            if path.suffix == '.csv':
                reader = csv.DictReader(io.StringIO(content)); rows = list(reader)
                bad = set(reader.fieldnames or []) & blocked
                bad -= {k for k in bad & counts if rows and all(re.fullmatch(r'[0-9]+', row.get(k, '')) for row in rows)}
                if bad: issue(rel, 'restricted_aggregate_columns')
                schemas += 1
        if args.science_root:
            source = args.science_root / rel
            if sha(source) != entries[rel]['source_sha256']: issue(rel, 'source_changed_after_export')
            if rel in changes['documentation_changes']:
                expected = source.read_text()
                recorded = changes['documentation_changes'][rel]
                for link in recorded['unavailable_links_as_text']:
                    pattern = r'!?\[([^\]]+)\]\(' + re.escape(link) + r'\)'
                    expected = re.sub(pattern, lambda m: m.group(1) + ' (server-only reference: `' + link + '`)', expected)
                if path.read_text().split('\n\n', 1)[1] != expected: issue(rel, 'undocumented_markdown_change')
                transformed += 1
            else:
                if sha(path) != sha(source): issue(rel, 'source_copy_mismatch')
                exact += 1
    fseries = read(root / 'results/auditory_fseries/verification_002/verification.json')
    archival = read(root / 'results/auditory_fseries_archival/verification_003/summary.json')
    repair = read(root / 'results/auditory_repair/verification_001/verification.json')
    retrain = read(root / 'results/auditory_retrain_v1/verification_001/summary.json')
    assert fseries['status'] == archival['status'] == repair['status'] == 'PASS'
    assert archival['verified_task_model_combinations'] == 24
    assert repair['all_declared_model_comparisons_complete'] and repair['head_refits_in_verification'] == 0
    assert retrain['status'] == 'VERIFIED' and retrain['tasks'] == dict(expected=45, completed=45, learned_encoders=40, L0_outer_representations=5)
    assert retrain['new_D_groups'] == 52 and retrain['changed_outer_assignments_vs_old'] == 37
    assert not retrain['independent_validation'] and retrain['no_model_refit']
    controls = read(root / 'results/auditory_retrain_v1/controls_001/control_status.json')
    fp32 = read(root / 'results/auditory_retrain_v1/controls_001/fp32_invariance.json')
    assert len(controls) == 121 and all(row['status'] == 'PASS' for row in controls)
    assert len(fp32) == 60 and all(row['status'] == 'PASS' for row in fp32)
    metrics = list(csv.DictReader((root / 'results/auditory_retrain_v1/verification_001/model_metrics.csv').open()))
    assert len(metrics) == 180 and all(int(row['n']) == 52 for row in metrics)
    sim = next(row for row in retrain['modes'] if row['mode'] == 'R_SIM')
    assert abs(sim['D2_CV_vs_D3_CVN']['estimate'] - 0.019687257343925887) < 1e-12
    assert abs(sim['D1_C_vs_D3_CVN']['estimate'] + 0.09423441754730409) < 1e-12
    accounting = read(root / 'results/auditory_retrain_v1/verification_001/report_accounting.json')
    assert accounting['clinical_head_calls'] == dict(core_001=48105, controls_001=53865)
    assert accounting['report_model_refits'] == 0
    source_bindings = task_receipts = repair_bindings = 0
    tested_count = 0
    if args.science_root:
        science = args.science_root
        plan_dir = science / 'private/auditory_retrain_v1/jobs/plan_001'
        plan = read(plan_dir / 'plan.json')
        assert sha(plan_dir / 'plan.json') == retrain['plan_hash']
        assert plan['tests_status'] == 'PASS' and sha(plan_dir / 'tests.log') == plan['tests_log_hash']
        assert re.search(r'\b43 passed\b', (plan_dir / 'tests.log').read_text())
        tested_count = 43
        assert plan['config']['corrected_retraining'] == read(root / 'configs/auditory_retrain_v1.json')
        for rel, expected in plan['code_hashes'].items():
            if rel.startswith(('auditory5/', 'tests/auditory5/')) or rel in {'auditory_retrain/run.py', 'auditory_retrain/__init__.py'}:
                assert sha(root / rel) == sha(plan_dir / 'source' / rel) == expected, rel
                source_bindings += 1
        review = science / 'private/auditory_retrain_v1/reviews/verification_001'
        completion = read(review / 'completion.json')
        assert completion['status'] == 'PASS' and completion['plan_hash'] == retrain['plan_hash'] and completion['model_refits'] == 0
        original_report = science / 'reports/auditory_retrain_v1/verification_001/REPORT.md'
        assert sha(original_report) == completion['report_hash']
        for rel, expected in read(review / 'source_receipt.json')['hashes'].items():
            assert sha(root / rel) == sha(review / 'source' / rel) == expected, rel
            source_bindings += 1
        for task in plan['tasks']:
            receipt = read(plan_dir / 'outputs' / task['name'] / 'completion.json')
            assert receipt['status'] == 'PASS' and receipt['plan_hash'] == retrain['plan_hash']
            if task['mode'] in {'R_SUP', 'R_SIM'}: assert receipt['gpu_name'] == 'NVIDIA L40S'
            task_receipts += 1
        assert task_receipts == 45
        for raw, expected in read(science / 'private/auditory_repair/verification_001/output_hashes.json').items():
            rel = str(Path(raw).relative_to(science))
            if rel in selected:
                assert sha(science / rel) == expected
                repair_bindings += 1
        assert repair_bindings > 0
    report.update(status='passed' if not issues else 'failed',
        release_scope='functional_qualification_archival_PTA_repair_corrected_cohort_retraining',
        selected_new_source_files=len(selected), new_exact_copies_checked=exact,
        new_markdown_transforms_checked=transformed, new_aggregate_schemas_checked=schemas,
        expanded_identifier_dictionary_size=len(identifiers),
        latest_scientific_receipts=dict(qualification='PASS', archival='PASS', repair='PASS', retraining='VERIFIED'),
        retraining_historical_tests_bound=tested_count, retraining_source_bindings_checked=source_bindings,
        retraining_task_receipts_checked=task_receipts, repair_final_output_bindings_checked=repair_bindings,
        retraining_control_states_checked=121, retraining_fp32_states_checked=60, retraining_metric_rows_checked=180,
        publication_new_model_fits=0, publication_new_encoder_fits=0, publication_tests_rerun=0,
        limits='Bounded current-tree known-name/identifier/schema checks, not an anonymity certificate or full Git-history clearance. Existing scientific receipts/source bindings checked; no scientific tests or models rerun. Exact Git index requires separate receipt. Current source does not replace historical frozen snapshots.')
    (root / 'release/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return int(bool(issues))


if __name__ == '__main__':
    raise SystemExit(main())
