"""Verify this curated snapshot. Run through Slurm; no raw data are loaded.

Optional --known-names reads a restricted JSON list locally. Only affected
publication paths, never dictionary values, are written to the report.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--known-names', type=Path)
    args = parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Submit this verification through Slurm.')
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'release/manifest.json').read_text())
    names = json.loads(args.known_names.read_text()) if args.known_names else []
    issues = []
    files = manifest['files']
    allowed = {item['path'] for item in files} | set(manifest['self_exclusions'])
    secret_patterns = [r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{30,}',
                       r'AKIA[A-Z0-9]{16}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    blocked_columns = {'participant_id', 'recording_id', 'container_id', 'raw_name',
                       'source_row', 'source_worksheet_row', 'clinical_row_ref',
                       'unique_same_day_pid', 'absolute_path', 'raw_dob',
                       'candidate_id', 'split_group_id', 'record_id', 'trial_id',
                       'raw_locator_key', 'fit_groups', 'test_groups', 'validation_groups',
                       'train_groups', 'training_groups', 'signal_path', 'event_path'}
    scope_count_fields={'fit_groups','test_groups','validation_groups','train_groups','training_groups'}
    link_re = re.compile(r'!?\[[^\]]+\]\(([^)]+)\)')
    links = 0
    py_files = 0
    bash_files = 0
    pdf_files = 0
    image_files = 0
    git_paths = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')
    tracked = {p for p in git_paths if p}
    if tracked and tracked != allowed:
        issues.append({'type':'tracked_set_mismatch', 'missing':sorted(allowed-tracked), 'extra':sorted(tracked-allowed)})
    for entry in files:
        rel = entry['path']
        p = root / rel
        if p.suffix.lower() in {'.pt','.pth','.pkl','.parquet','.npz','.npy','.bdf','.edf','.set','.fdt','.mat','.xlsx','.xls'}:
            issues.append({'path':rel, 'type':'restricted_data_or_model_extension'})
        if p.is_symlink() or not p.is_file():
            issues.append({'path':rel, 'type':'missing_or_symlink'})
            continue
        blob = p.read_bytes()
        if hashlib.sha256(blob).hexdigest() != entry['sha256']:
            issues.append({'path':rel, 'type':'hash_mismatch'})
        if len(blob) != entry['bytes'] or len(blob) > 10*1024*1024:
            issues.append({'path':rel, 'type':'size_mismatch_or_over_10MiB'})
        content = ''
        if p.suffix == '.pdf':
            from pdfminer.high_level import extract_text
            content = extract_text(str(p))
            pdf_files += 1
        elif p.suffix == '.png':
            from PIL import Image
            with Image.open(p) as im:
                im.verify()
                content = json.dumps(im.info, default=str)
            image_files += 1
        else:
            try:
                content = blob.decode('utf-8')
            except UnicodeDecodeError:
                issues.append({'path':rel, 'type':'unexpected_binary'})
        for pattern in secret_patterns:
            if re.search(pattern, content):
                issues.append({'path':rel, 'type':'credential_pattern'})
        if any(name.casefold() in content.casefold() for name in names):
            issues.append({'path':rel, 'type':'known_name_match'})
        if p.suffix == '.py':
            ast.parse(content, filename=rel)
            py_files += 1
        if p.suffix == '.sbatch':
            subprocess.run(['bash','-n',str(p)],check=True,capture_output=True)
            bash_files += 1
        if p.suffix == '.md':
            for target in link_re.findall(content):
                target = target.split('#',1)[0]
                if not target or re.match(r'^[a-z]+://',target):
                    continue
                links += 1
                if not (p.parent / target).exists():
                    issues.append({'path':rel, 'type':'unresolved_local_link','target':target})
        if rel.startswith('results/') and p.suffix == '.csv':
            reader=csv.DictReader(io.StringIO(content))
            rows=list(reader)
            restricted=blocked_columns.intersection(reader.fieldnames or [])
            for key in scope_count_fields.intersection(restricted):
                if rows and all(re.fullmatch(r'[0-9]+', row.get(key, '')) for row in rows):
                    restricted.remove(key)
            if restricted:
                issues.append({'path':rel, 'type':'individual_data_columns'})
        if rel.startswith('results/') and p.suffix == '.json':
            obj = json.loads(content)
            def inspect(value):
                if isinstance(value,dict):
                    restricted = blocked_columns.intersection(value)
                    # These names denote aggregate counts in route summaries,
                    # but actual fit/test group lists remain restricted.
                    for key in scope_count_fields:
                        if key in restricted and type(value[key]) is int and value[key]>=0:
                            restricted.remove(key)
                    if restricted:
                        issues.append({'path':rel, 'type':'individual_data_keys'})
                    for child in value.values(): inspect(child)
                elif isinstance(value,list):
                    for child in value: inspect(child)
            inspect(obj)
        if rel.startswith(('results/auditory5_v1/','reports/auditory5_v1/')):
            if re.search(r'(?<![A-Za-z0-9])(?:B|P|G|M)[0-9a-f]{12,16}(?![A-Za-z0-9])', content):
                issues.append({'path':rel, 'type':'opaque_participant_or_record_identifier'})
    for p in root.rglob('*'):
        if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts or '.pytest_cache' in p.parts:
            continue
        rel = str(p.relative_to(root))
        if rel.startswith('private/'):
            continue
        if rel not in allowed:
            issues.append({'path':rel,'type':'file_outside_manifest'})
    restart = root / 'server_restart_en_v1'
    restart_hashes = 0
    for line in (restart/'MANIFEST.sha256').read_text().splitlines():
        expected, rel = line.split(None, 1)
        if hashlib.sha256((restart/rel.strip()).read_bytes()).hexdigest() != expected:
            issues.append({'path':'server_restart_en_v1/'+rel, 'type':'historical_manifest_mismatch'})
        restart_hashes += 1
    sys.path.insert(0,str(root/'scripts'))
    suite = unittest.defaultTestLoader.discover(str(root/'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        issues.append({'type':'unit_test_failure'})
    auditory_tests = 0
    auditory_success = False
    if (root/'auditory5').is_dir():
        private = root/'private/release_verification'/os.environ['SLURM_JOB_ID']
        private.mkdir(parents=True, exist_ok=False, mode=0o700)
        environment=dict(os.environ, AUDITORY5_ROOT=str(root), PYTHONPATH=str(root))
        checked = subprocess.run([sys.executable, '-m', 'pytest', 'tests/auditory5', '-q',
                                  '-p', 'no:cacheprovider', '--junitxml='+str(private/'junit.xml')],
                                 cwd=root, env=environment, capture_output=True, text=True)
        (private/'pytest.log').write_text(checked.stdout+'\n'+checked.stderr)
        if (private/'junit.xml').exists():
            tree=ET.parse(private/'junit.xml').getroot()
            auditory_tests=len(tree.findall('.//testcase'))
            auditory_success=(checked.returncode==0 and auditory_tests>=173 and
                              not tree.findall('.//failure') and not tree.findall('.//error') and
                              not tree.findall('.//skipped'))
        if not auditory_success:
            issues.append({'type':'published_auditory5_contract_tests_failed'})
    report = {'status':'passed' if not issues else 'failed',
              'job_id':os.environ['SLURM_JOB_ID'], 'files_hashed':len(files),
              'total_bytes':sum(e['bytes'] for e in files),
              'tracked_set_verified':bool(tracked),
              'python_files_parsed':py_files, 'slurm_scripts_syntax_checked':bash_files,
              'local_links_checked':links, 'historical_restart_hashes_checked':restart_hashes,
              'pdfs_text_checked':pdf_files, 'pngs_structurally_checked':image_files,
              'known_name_dictionary_size':len(names),
              'unit_tests_run':result.testsRun, 'unit_tests_successful':result.wasSuccessful(),
              'auditory5_tests_run':auditory_tests, 'auditory5_tests_successful':bool(auditory_success),
              'issues':issues,
              'limits':'Allowlist, content and hash checks are not a formal anonymization certificate. Raw data analyses were not rerun.'}
    (root/'release/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return int(bool(issues))


if __name__ == '__main__':
    raise SystemExit(main())
