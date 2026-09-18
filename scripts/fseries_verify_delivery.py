"""Check F-series qualification delivery under Slurm; never fit a model."""
import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path('/home/infres/yinwang/EEG_auditory')


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--jobs', nargs='+', required=True)
    args = parser.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'SLURM_REQUIRED'
    assert re.fullmatch(r'[A-Za-z0-9_]+', args.run)
    os.umask(0o077)
    private = ROOT / 'private/auditory_fseries' / args.run
    public = ROOT / 'results/auditory_fseries' / args.run
    assert not private.exists() and not public.exists(), 'RUN_OCCUPIED'
    private.mkdir(mode=0o700)
    public.mkdir(mode=0o700)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    sources = [*sorted((ROOT / 'scripts').glob('fseries_*.py')), *sorted((ROOT / 'docs/auditory_fseries').glob('*.md')),
               ROOT / 'configs/auditory_fseries_qualification_v1.json', ROOT / 'AUDITORY_FUNCTIONAL_DECODING_F1_F4_RESEARCH_PLAN_v1.md']
    for source in sources:
        target = private / 'source' / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copyfile(source, target)
    dump(private / 'start.json', dict(job_id=os.environ['SLURM_JOB_ID'], start_unix=time.time(),
        source_hashes={str(p.relative_to(ROOT)): sha(p) for p in sources}))
    names = json.loads((ROOT / 'private/github_publish_001/known_names.json').read_text())
    identifiers = set()
    for rel, fields in [
        ('private/clinical_003/clinical_rows_clean.csv', ['participant_id', 'clinical_row_id']),
        ('private/phase3_ci_clinical_004/candidate_rows_index.csv', ['participant_id']),
        ('results/phase3_ci_linkage_005/clinical_source_links.csv', ['participant_id', 'container_id', 'clinical_row_ref']),
        ('results/linkage_001/recording_index.csv', ['recording_id', 'participant_id']),
    ]:
        for row in csv.DictReader((ROOT / rel).open()):
            identifiers.update(row[field] for field in fields if row.get(field) and len(row[field]) >= 5)
    issues = []
    payload = []
    prohibited = {'participant_id', 'clinical_row_id', 'recording_id', 'container_id', 'raw_name', 'clinical_row_ref', 'source_worksheet_row', 'original_path', 'raw_clinical_date', 'raw_dob'}
    def inspect(value, path):
        if isinstance(value, dict):
            if set(value) & prohibited:
                issues.append(dict(path=path, type='individual_fields_in_aggregate'))
            for v in value.values():
                inspect(v, path)
        elif isinstance(value, list):
            for v in value:
                inspect(v, path)
    text_files = []
    for directory in ['results/auditory_fseries', 'reports/auditory_fseries', 'docs/auditory_fseries']:
        text_files.extend(p for p in (ROOT / directory).rglob('*') if p.is_file() and p.suffix in {'.json', '.csv', '.md', '.txt'})
    for path in sorted(text_files):
        body = path.read_text()
        rel = str(path.relative_to(ROOT))
        if any(name.casefold() in body.casefold() for name in names):
            issues.append(dict(path=rel, type='known_name'))
        if set(re.findall(r'[\w:.-]+', body)) & identifiers:
            issues.append(dict(path=rel, type='known_identifier'))
        if re.search(r'(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{30,}|-----BEGIN .*PRIVATE KEY-----', body):
            issues.append(dict(path=rel, type='secret_pattern'))
        if path.suffix == '.json':
            inspect(json.loads(body), rel)
        if path.suffix == '.csv':
            if set(csv.DictReader(body.splitlines()).fieldnames or []) & prohibited:
                issues.append(dict(path=rel, type='individual_columns_in_aggregate'))
        if path.suffix == '.md':
            for link in re.findall(r'!?\[[^\]]+\]\(([^)]+)\)', body):
                target = link.split('#', 1)[0]
                if not target or re.match(r'^[a-z]+://', target):
                    continue
                if not (path.parent / target).exists():
                    issues.append(dict(path=rel, type='broken_link:' + target))
        payload.append(dict(path=rel, sha256=sha(path), bytes=path.stat().st_size))
    parsed = 0
    for path in sorted((ROOT / 'scripts').glob('fseries_*.py')):
        ast.parse(path.read_text(), filename=str(path.relative_to(ROOT)))
        parsed += 1
    permissions = []
    for path in (ROOT / 'private/auditory_fseries').rglob('*'):
        if path.stat().st_mode & 0o077:
            permissions.append(str(path.relative_to(ROOT)))
    if permissions:
        issues.append(dict(path='private/auditory_fseries', type='private_permissions'))
    dump(private / 'permission_violations.json', permissions)
    jobs = []
    evidence_path = ROOT / 'private/auditory_fseries/ci_qualification_execution_001/execution_provenance.json'
    evidence = json.loads(evidence_path.read_text())
    requested_jobs = {r['job_id']: r for r in evidence['main_jobs'] + [evidence['supplement_job']]}
    for job in dict.fromkeys(args.jobs + [os.environ['SLURM_JOB_ID']]):
        assert job.isdigit()
        result = subprocess.run(['scontrol', 'show', 'job', job], text=True, capture_output=True)
        saved = private / ('scheduler-' + job + '.txt')
        fallback = ROOT / 'private/auditory_fseries/logs' / ('scheduler-' + job + '.txt')
        scheduler_text = result.stdout
        if result.returncode and fallback.exists() and 'TimeLimit=' in fallback.read_text():
            scheduler_text = fallback.read_text()
        saved.write_text(scheduler_text + result.stderr)
        if 'TimeLimit=' not in scheduler_text:
            if job in requested_jobs:
                r = requested_jobs[job]
                h, m, s = map(int, r['requested_walltime'].split(':'))
                cpus = max(2, r['requested_cpus'])
                jobs.append(dict(job_id=job, state=r['state'], cpus=cpus, partition='CPU',
                    requested_cpu_core_hours=cpus * (h * 3600 + m * 60 + s) / 3600,
                    accounting_source='retained_submission_script_and_execution_provenance;min_two_CPU_conservative_site_allocation'))
            else:
                issues.append(dict(path='scheduler', type='missing_job_reservation:' + job))
            continue
        def field(name):
            match = re.search(r'(?:^|\s)' + name + r'=(\S+)', scheduler_text)
            return match[1] if match else ''
        limit = field('TimeLimit')
        days, clock = limit.split('-', 1) if '-' in limit else ('0', limit)
        h, m, s = map(int, clock.split(':'))
        cpus = int(field('NumCPUs'))
        reservation = cpus * (int(days) * 86400 + h * 3600 + m * 60 + s) / 3600
        jobs.append(dict(job_id=job, state=field('JobState'), cpus=cpus, partition=field('Partition'), requested_cpu_core_hours=reservation))
        if field('Partition') != 'CPU':
            issues.append(dict(path='scheduler', type='unexpected_nonCPU_job'))
    reserved = sum(j['requested_cpu_core_hours'] for j in jobs)
    if reserved > 8:
        issues.append(dict(path='scheduler', type='stage1_reservation_ceiling'))
    report = dict(status='PASS' if not issues else 'FAIL', job_id=os.environ['SLURM_JOB_ID'],
        public_text_files_scanned=len(payload), known_names=len(names), known_identifier_tokens=len(identifiers),
        python_scripts_parsed=parsed, issues=issues, stage1_jobs=jobs,
        requested_cpu_core_hours_upper_bound=reserved, stage1_cpu_core_hour_ceiling=8,
        model_fits=0, gpu_jobs=0, eeg_outcome_associations_computed=False,
        scope='Qualified metadata audit only; known-token scan is bounded, not universal anonymization. The verification job is still running when its own reservation is recorded.')
    dump(public / 'verification.json', report)
    dump(public / 'payload_hashes.json', payload)
    dump(private / 'completion.json', report)
    print(json.dumps(report, ensure_ascii=False))
    return int(bool(issues))


if __name__ == '__main__':
    raise SystemExit(main())
