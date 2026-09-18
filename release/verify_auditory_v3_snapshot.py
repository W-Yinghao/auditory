"""Verify the V3 publication allowlist and historical scientific evidence.

Run through Slurm. Optional private dictionaries and receipts strengthen the
checks; only aggregate counts/public paths enter the public verification file.
No tests are rerun, and no participant models or EEG arrays are loaded.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--known-names', type=Path)
    parser.add_argument('--identifier-table', type=Path, action='append', default=[])
    parser.add_argument('--science-root', type=Path)
    parser.add_argument('--previous-manifest', type=Path)
    args = parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('SLURM_REQUIRED')
    os.umask(0o077)
    root = Path(__file__).resolve().parents[1]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    read = lambda p: json.loads(p.read_text())
    manifest = read(root / 'release/manifest.json')
    changes = read(root / 'release/auditory_v3_publication_changes.json')
    entries = {e['path']: e for e in manifest['files']}
    allowed = set(entries) | set(manifest['self_exclusions'])
    names = read(args.known_names) if args.known_names else []
    identifiers = set()
    for path in args.identifier_table:
        import pandas as pd
        import pyarrow.parquet as pq
        columns = set(pq.read_schema(path).names) & {'trial_id', 'bag_id', 'candidate_id', 'record_id', 'split_group_id', 'matched_pair_id'}
        frame = pd.read_parquet(path, columns=sorted(columns))
        identifiers.update(str(v) for c in frame for v in frame[c].dropna().unique() if len(str(v)) >= 6)
    issues = []
    def issue(rel, kind):
        issues.append(dict(path=rel, type=kind))
    blocked = {'participant_id', 'recording_id', 'container_id', 'raw_name', 'source_row', 'source_worksheet_row',
        'clinical_row_ref', 'unique_same_day_pid', 'absolute_path', 'raw_dob', 'candidate_id', 'split_group_id',
        'record_id', 'trial_id', 'bag_id', 'matched_pair_id', 'raw_locator_key', 'fit_groups', 'test_groups',
        'validation_groups', 'train_groups', 'training_groups', 'signal_path', 'event_path', 'original_path',
        'source_path', 'p0', 'p1', 'logit', 'prediction', 'model_weights'}
    count_fields = {'fit_groups', 'test_groups', 'validation_groups', 'train_groups', 'training_groups'}
    secrets = [r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{30,}',
               r'AKIA[A-Z0-9]{16}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    opaque = re.compile(r'(?<![A-Za-z0-9])(?:B|P|G|M)[0-9a-f]{12,16}(?![A-Za-z0-9])')
    counts = dict(python_files_parsed=0, slurm_scripts_syntax_checked=0, local_links_checked=0,
                  pdfs_text_checked=0, pngs_structurally_checked=0, text_files_identifier_scanned=0)
    def inspect(value, rel):
        if isinstance(value, dict):
            bad = set(value) & blocked
            bad -= {k for k in bad & count_fields if type(value[k]) is int and value[k] >= 0}
            if bad:
                issue(rel, 'restricted_aggregate_fields')
            for v in value.values():
                inspect(v, rel)
        elif isinstance(value, list):
            for v in value:
                inspect(v, rel)
    for rel, e in entries.items():
        p = root / rel
        if not p.is_file() or p.is_symlink():
            issue(rel, 'missing_or_symlink')
            continue
        blob = p.read_bytes()
        if sha(p) != e['sha256'] or len(blob) != e['bytes']:
            issue(rel, 'manifest_mismatch')
        if len(blob) > 10 * 1024 * 1024:
            issue(rel, 'oversized_file')
        if rel.startswith('private/') or p.suffix.lower() in {'.pt', '.pth', '.pkl', '.parquet', '.npz', '.npy', '.bdf', '.edf', '.set', '.fdt', '.mat', '.xlsx', '.xls'}:
            issue(rel, 'restricted_payload')
        if p.suffix == '.pdf':
            from pdfminer.high_level import extract_text
            content = extract_text(str(p))
            counts['pdfs_text_checked'] += 1
        elif p.suffix == '.png':
            from PIL import Image
            with Image.open(p) as im:
                content = json.dumps(im.info, default=str)
                im.verify()
            counts['pngs_structurally_checked'] += 1
        else:
            try:
                content = blob.decode('utf-8')
            except UnicodeDecodeError:
                issue(rel, 'unexpected_binary')
                continue
        if any(re.search(pattern, content) for pattern in secrets):
            issue(rel, 'credential_pattern')
        if any(name.casefold() in content.casefold() for name in names):
            issue(rel, 'known_name')
        if set(re.findall(r'[\w:.-]+', content)) & identifiers:
            issue(rel, 'known_individual_identifier')
        counts['text_files_identifier_scanned'] += 1
        if p.suffix == '.py':
            ast.parse(content, filename=rel)
            counts['python_files_parsed'] += 1
        if p.suffix == '.sbatch':
            subprocess.run(['bash', '-n', str(p)], check=True, capture_output=True)
            counts['slurm_scripts_syntax_checked'] += 1
        if p.suffix == '.md':
            for link in re.findall(r'!?\[[^\]]+\]\(([^)]+)\)', content):
                target = unquote(link.split('#', 1)[0].strip('<>'))
                if not target or re.match(r'^[a-z]+://', target):
                    continue
                counts['local_links_checked'] += 1
                if not (p.parent / target).exists():
                    issue(rel, 'broken_local_link:' + target)
        if rel.startswith(('results/auditory_v3/', 'reports/auditory_v3/')):
            if opaque.search(content):
                issue(rel, 'opaque_individual_identifier')
            if re.search(r'/(?:home|projects|mnt|tmp)/', content):
                issue(rel, 'absolute_path_in_aggregate')
            if p.suffix == '.json':
                inspect(json.loads(content), rel)
            if p.suffix == '.csv':
                reader = csv.DictReader(io.StringIO(content))
                rows = list(reader)
                bad = set(reader.fieldnames or []) & blocked
                bad -= {k for k in bad & count_fields if rows and all(re.fullmatch(r'[0-9]+', r.get(k, '')) for r in rows)}
                if bad:
                    issue(rel, 'restricted_aggregate_columns')
    for p in root.rglob('*'):
        if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts or '.pytest_cache' in p.parts:
            continue
        rel = str(p.relative_to(root))
        if not rel.startswith('private/') and rel not in allowed:
            issue(rel, 'outside_manifest')
    preserved = 0
    if args.previous_manifest:
        editorial = {'.gitignore', 'README.md', 'PUBLICATION.md', 'AGENTS.md', 'results/README.md'}
        for e in read(args.previous_manifest)['files']:
            if e['path'] in editorial:
                continue
            if sha(root / e['path']) != e['sha256']:
                issue(e['path'], 'historical_payload_changed')
            preserved += 1
    exact = 0
    for rel in changes['source_files']:
        if not rel.startswith('docs/'):
            if entries[rel]['sha256'] != entries[rel]['source_sha256']:
                issue(rel, 'source_copy_mismatch')
            exact += 1
        if args.science_root and sha(args.science_root / rel) != entries[rel]['source_sha256']:
            issue(rel, 'source_changed_since_export')
    final = read(root / 'results/auditory_v3/final_002/summary.json')
    assert final['status'] == 'V3_EXECUTION_COMPLETE' and final['resources']['within_budget']
    assert all(r['support'] == r['capability'] == 'PASS' and r['execution'] == 'COMPLETE' for r in final['primaries'])
    assert final['resources']['fit_attempts'] == dict(head=2357, encoder=30, synthetic_encoder=3)
    primary = list(csv.DictReader((root / 'results/auditory_v3/final_002/primary_results.csv').open()))
    for row, expected in zip(primary, final['primaries'], strict=True):
        assert row['packet'] == expected['packet']
        for key in ['gain_bits', 'ci_low', 'ci_high']:
            assert abs(float(row[key]) - expected[key]) < 1e-12
    tests = []
    bindings = 0
    for packet, run, expected in [('P0', 'tests_P0_002', 16), ('N2R', 'tests_N2R_002', 24), ('R3', 'tests_R3_005', 33), ('R3_SCORING', 'tests_R3_scoring_001', 6)]:
        receipt = read(root / f'results/auditory_v3/{run}/summary.json')
        assert receipt['status'] == 'PASS' and receipt['tests'] == dict(testcase=expected, failure=0, error=0, skipped=0)
        matched = 0
        if args.science_root:
            folder = args.science_root / f'private/auditory_v3/{run}'
            xml = ET.parse(folder / 'tests.xml').getroot()
            assert len(xml.findall('.//testcase')) == expected
            assert not any(xml.findall('.//' + k) for k in ['failure', 'error', 'skipped'])
            source = read(folder / 'start.json')['source_hashes']
            gate_tree = ast.parse((root / 'auditory_v3/gates.py').read_text())
            gate_sources = next(ast.literal_eval(n.value) for n in gate_tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PACKET_SOURCES' for t in n.targets))
            modules = ['auditory_v3/' + n + '.py' for n in gate_sources.get(packet, ['r3_stable_risk', 'r3_scoring'])]
            if packet == 'R3':
                modules += ['auditory5/models/small_cnn.py']
            common = ['linear', 'statistics', 'support']
            test_modules = {'P0': common + ['pca'], 'N2R': common + ['bags', 'n2r_capability', 'n2r_execution'],
                'R3': common + ['objectives', 'representation_data', 'train_contract', 'r3_evaluate', 'r3_execution', 'deterministic_pool'],
                'R3_SCORING': ['r3_stable_risk']}[packet]
            modules += ['tests/auditory_v3/test_' + n + '.py' for n in test_modules]
            for rel in modules:
                if rel not in entries or sha(root / rel) != source.get(rel):
                    issue(rel, 'tested_source_hash_mismatch:' + run)
                matched += 1
            assert receipt == read(folder / 'completion.json')
        tests.append(dict(run=run, tests=expected, status='PASS', source_bindings_checked=matched, publication_rerun=False))
    if args.science_root:
        for packet, binding in final['input_receipts'].items():
            folder = args.science_root / 'private/auditory_v3' / binding['run']
            assert sha(folder / 'completion.json') == binding['completion_sha256']
            receipt = read(folder / 'completion.json')
            cap = args.science_root / 'private/auditory_v3' / receipt['capability_run'] / 'completion.json'
            assert sha(cap) == binding['capability_receipt_sha256']
            assert read(cap)['status'] == 'PASS'
            bindings += 2
    assert sha(root / 'auditory_v3_plan.yaml') == sha(root / 'configs/auditory_v3_plan.yaml') == final['config_sha256']
    scoring_hash = hashlib.sha256()
    for name in ['r3_stable_risk.py', 'r3_scoring.py']:
        scoring_hash.update(name.encode())
        scoring_hash.update((root / 'auditory_v3' / name).read_bytes())
    assert scoring_hash.hexdigest() == read(root / 'results/auditory_v3/tests_R3_scoring_001/summary.json')['scoring_algorithm_sha256']
    selection = read(root / 'results/auditory_v3/R3_probe_selection_002/summary.json')
    assert selection['selected_choices'] == 60 and selection['new_head_fits'] == 0
    encoders = [read(root / f'results/auditory_v3/R3_{stage}_001_task{i:03d}/summary.json') for stage in ['selection', 'final'] for i in range(15)]
    assert all(r['status'] == 'ENCODER_COMPLETE' and 'A100' in r['device'] for r in encoders)
    report = dict(status='passed' if not issues else 'failed', job_id=os.environ['SLURM_JOB_ID'],
        files_hashed=len(entries), total_bytes=manifest['total_bytes'], **counts,
        known_name_dictionary_size=len(names), known_identifier_dictionary_size=len(identifiers),
        historical_payload_files_preserved=preserved, v3_source_exact_copies_checked=exact,
        scientific_test_receipts=tests, private_final_capability_bindings_checked=bindings,
        encoder_completion_receipts_checked=len(encoders), primary_values_reconciled=3,
        publication_new_model_fits=0, publication_new_encoder_fits=0, issues=issues,
        limits='Bounded allowlist/name/identifier/schema/hash checks, not an anonymization certificate. Historical tests matched to gated source, not rerun. PNG metadata/structure checked; final figure visually reviewed. Exact staged content requires separate index verification. Self-finalization execution_jobs rows retain the running/incomplete state observed before their own completion receipts.')
    (root / 'release/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return int(bool(issues))


if __name__ == '__main__':
    raise SystemExit(main())
