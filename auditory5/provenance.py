"""Shared provenance and guarded output handling; no implicit overwrite."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get('AUDITORY5_ROOT',Path(__file__).resolve().parents[1])).resolve()


def require_slurm():
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('All computation must be submitted through Slurm.')
    os.umask(0o077)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def object_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',',':'), allow_nan=False).encode()).hexdigest()


def write_json(path, obj, *, overwrite=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w' if overwrite else 'x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def new_run(stage, config):
    private = ROOT / config['paths']['private_relative'] / stage
    public = ROOT / config['paths']['aggregates_relative'] / stage
    private.mkdir(parents=True, exist_ok=False, mode=0o700)
    public.mkdir(parents=True, exist_ok=False)
    return private, public
