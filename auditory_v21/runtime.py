"""Immutable Slurm-run snapshots and conservative submission ledger."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

ROOT=Path(os.environ.get('AUDITORY5_ROOT','/home/infres/yinwang/EEG_auditory'))


def require_slurm():
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('SLURM_REQUIRED')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''): h.update(part)
    return h.hexdigest()


def write_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def create(run, config_path, command):
    require_slurm(); os.umask(0o077)
    if not run or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in run):
        raise ValueError('INVALID_RUN_NAME')
    paths=[ROOT/b/'auditory_v21'/run for b in ('private','results','reports')]
    if any(p.exists() for p in paths): raise FileExistsError('RUN_ALREADY_EXISTS')
    for path in paths:path.mkdir(parents=True,mode=0o700)
    private,public,report=paths
    config=json.loads((ROOT/config_path).read_text())
    source=private/'source';source.mkdir(mode=0o700)
    hashes={}
    for folder in ('auditory_v21','tests/auditory_v21','auditory_next','auditory5'):
        for path in sorted((ROOT/folder).rglob('*.py')):
            if '__pycache__' in path.parts:continue
            rel=path.relative_to(ROOT);target=source/rel
            target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            shutil.copyfile(path,target);hashes[str(rel)]=digest(target)
    documents=[config_path,config['amendment'],'docs/auditory_v21/V2_1_CHANGELOG.md',
                'docs/auditory_v21/ESTIMATOR_CONTRACT_DRAFT.md']
    documents+=config.get('frozen_documents',[])
    for rel in dict.fromkeys(documents):
        target=source/rel;target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        shutil.copyfile(ROOT/rel,target);hashes[rel]=digest(target)
    write_json(private/'start.json',dict(run=run,command=command,job_id=os.environ['SLURM_JOB_ID'],
        start_unix=time.time(),config_path=config_path,config_hash=digest(ROOT/config_path),source_hashes=hashes))
    write_json(private/'config.json',config)
    return paths


def finish(private,public,summary):
    start=json.loads((private/'start.json').read_text())
    summary=dict(summary,job_id=os.environ['SLURM_JOB_ID'],config_hash=start['config_hash'],
                 elapsed_seconds=time.time()-start['start_unix'])
    write_json(private/'completion.json',summary);write_json(public/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    return summary
