"""Run creation and private receipts. Numerical entry points require Slurm."""
import json
import os
from pathlib import Path
import shutil
import time

from auditory5.provenance import ROOT, digest, object_hash, require_slurm, write_json


def config_load(path):
    import yaml
    snapshot_run=os.environ.get('AUDITORY_NEXT_SNAPSHOT_RUN')
    base=ROOT/'private/auditory_next_v2'/snapshot_run/'source' if snapshot_run else ROOT
    path = base / path
    config = yaml.safe_load(path.read_text())
    registry = yaml.safe_load((base / config['project']['source_registry']).read_text())
    site = yaml.safe_load((ROOT / config['project']['site_config']).read_text())
    if Path(site['root']).resolve() != ROOT:
        raise ValueError('SITE_ROOT_MISMATCH')
    return config, registry, site


def create_run(run, config_path):
    require_slurm()
    if not run or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in run):
        raise ValueError('INVALID_RUN_NAME')
    private = ROOT / 'private/auditory_next_v2' / run
    public = ROOT / 'results/auditory_next_v2' / run
    report = ROOT / 'reports/auditory_next_v2' / run
    for path in (private, public, report):
        if path.exists():
            raise FileExistsError(path)
    for path in (private, public, report):
        path.mkdir(parents=True, mode=0o700)
    source = private / 'source'
    source.mkdir()
    hashes = {}
    for folder in ('auditory_next', 'tests/auditory_next', 'auditory5'):
        for path in sorted((ROOT / folder).rglob('*.py')):
            rel = path.relative_to(ROOT)
            target = source / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            hashes[str(rel)] = digest(target)
    for path in (ROOT / config_path, ROOT / 'configs/auditory_next_sources_v2.yaml', ROOT / 'AUDITORY_NEXT_ROUND_SERVER_PLAN_v2.md'):
        target = source / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        hashes[str(path.relative_to(ROOT))] = digest(target)
    write_json(private / 'start.json', dict(run=run, job_id=os.environ['SLURM_JOB_ID'],
               source_hashes=hashes, start_unix=time.time(), config_hash=digest(ROOT / config_path),
               clinical_inputs=False, legacy_read_only=True))
    return private, public, report


def finish(private, public, summary):
    start = json.loads((private / 'start.json').read_text())
    summary = dict(summary, job_id=os.environ['SLURM_JOB_ID'],
                   elapsed_seconds=time.time() - start['start_unix'],
                   source_snapshot_hash=object_hash(start['source_hashes']))
    write_json(private / 'completion.json', summary)
    write_json(public / 'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return summary
