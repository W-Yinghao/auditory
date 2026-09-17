"""Verify the curated v2 release with Slurm CPU jobs and synthetic fixtures.

Optional identifiers/names remain private; reports contain counts and affected
publication file paths, never identifier values. No participant models are fit.
"""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--known-names', type=Path)
    parser.add_argument('--identifier-table', type=Path)
    args = parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Submit verification through Slurm.')
    os.umask(0o077)
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, str(root/'release/verify_snapshot.py')]
    if args.known_names:
        command += ['--known-names', str(args.known_names)]
    baseline = subprocess.run(command, cwd=root, capture_output=True, text=True)
    private = root/'private/release_v2_verification'/os.environ['SLURM_JOB_ID']
    private.mkdir(parents=True, exist_ok=False, mode=0o700)
    (private/'baseline.log').write_text(baseline.stdout+'\n'+baseline.stderr)
    report = json.loads((root/'release/verification.json').read_text())
    issues = report['issues']
    if baseline.returncode and not issues:
        issues.append(dict(type='baseline_verification_process_failure'))
    manifest = json.loads((root/'release/manifest.json').read_text())
    changes = json.loads((root/'release/auditory_next_v2_publication_changes.json').read_text())
    rows = {r['path']:r for r in manifest['files']}
    exact = 0
    for rel in changes['source_files']:
        if rel.startswith('docs/'):
            continue
        if rows[rel]['sha256'] != rows[rel]['source_sha256']:
            issues.append(dict(path=rel, type='v2_exact_source_copy_mismatch'))
        exact += 1
    final_rows = list(csv.DictReader((root/'results/auditory_next_v2/public_audit_002/audited_artifact_hashes.csv').open()))
    for row in final_rows:
        if hashlib.sha256((root/row['artifact']).read_bytes()).hexdigest() != row['sha256']:
            issues.append(dict(path=row['artifact'], type='final_scientific_audit_hash_mismatch'))
    identifiers = set()
    if args.identifier_table:
        import pandas as pd
        table = pd.read_parquet(args.identifier_table, columns=['trial_id','record_id','candidate_id','split_group_id'])
        identifiers = {str(v) for col in table for v in table[col].dropna().unique()}
        if any(len(s)<6 for s in identifiers):
            raise ValueError('SHORT_IDENTIFIER_REQUIRES_REVIEW')
    opaque = re.compile(r'(?<![A-Za-z0-9])(?:B|P|G|M)[0-9a-f]{12,16}(?![A-Za-z0-9])')
    forbidden = {'trial_id','record_id','candidate_id','split_group_id','original_path','source_path','p0','p1','logit','prediction','model_weights'}
    def keys(obj):
        if isinstance(obj,dict):
            return set(obj).union(*(keys(v) for v in obj.values()))
        if isinstance(obj,list):
            return set().union(*(keys(v) for v in obj))
        return set()
    scanned = 0
    for rel in changes['source_files']:
        p = root/rel
        if p.suffix not in {'.md','.csv','.json','.yaml','.py','.sbatch'}:
            continue
        text = p.read_text()
        if set(re.findall(r'[\w:.-]+', text)) & identifiers:
            issues.append(dict(path=rel, type='known_restricted_identifier'))
        if rel.startswith(('results/', 'reports/')):
            if opaque.search(text):
                issues.append(dict(path=rel, type='opaque_individual_identifier'))
            if re.search(r'/(?:home|projects|mnt|tmp)/',text):
                issues.append(dict(path=rel, type='absolute_path_in_aggregate'))
            fields = set()
            if p.suffix=='.csv' and text.strip():
                fields=set(csv.DictReader(io.StringIO(text)).fieldnames or [])
            elif p.suffix=='.json':
                fields=keys(json.loads(text))
            if fields & forbidden:
                issues.append(dict(path=rel, type='restricted_fields_in_aggregate'))
        scanned += 1
    env = dict(os.environ, AUDITORY5_ROOT=str(root), AUDITORY_NEXT_ROOT=str(root),
               PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
               AUDITORY_NEXT_TEST_FIT_LEDGER=str(private/'test_fit_counts.json'))
    tested = subprocess.run([sys.executable,'-m','pytest','tests/auditory_next','-q','-p','no:cacheprovider',
                             '--basetemp='+str(private/'tmp'), '--junitxml='+str(private/'junit.xml')],
                            cwd=root, env=env, capture_output=True, text=True)
    (private/'pytest.log').write_text(tested.stdout+'\n'+tested.stderr)
    test_count = 0
    successful = False
    if (private/'junit.xml').exists():
        tree=ET.parse(private/'junit.xml').getroot()
        test_count=len(tree.findall('.//testcase'))
        successful=(tested.returncode==0 and test_count>=137 and not tree.findall('.//failure')
                    and not tree.findall('.//error') and not tree.findall('.//skipped'))
    if not successful:
        issues.append(dict(type='published_v2_contract_tests_failed'))
    test_fits = json.loads((private/'test_fit_counts.json').read_text()) if (private/'test_fit_counts.json').exists() else None
    report.update(status='passed' if not issues else 'failed',
        auditory_next_tests_run=test_count, auditory_next_tests_successful=successful,
        v2_source_exact_copies_checked=exact, scientific_final_audit_hashes_checked=len(final_rows),
        v2_text_files_identifier_scanned=scanned, known_identifier_dictionary_size=len(identifiers),
        publication_synthetic_test_fit_calls=test_fits, new_participant_model_fits=0,
        publication_verification_scope='Curated release and data-independent fixtures; separate from frozen scientific budget/fit receipts.',
        issues=issues)
    (root/'release/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return int(bool(issues))


if __name__=='__main__':
    raise SystemExit(main())
