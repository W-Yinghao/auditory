"""Immutable Slurm-only orchestration for archival functional-score tests."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import traceback
import xml.etree.ElementTree as ET

ROOT = Path(os.environ.get('AUDITORY_ROOT', '/home/infres/yinwang/EEG_auditory'))
NAMESPACE = 'auditory_fseries_archival'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, obj):
    def scalar(value):
        if hasattr(value, 'item'):
            return value.item()
        raise TypeError(f'Unsupported serialization type: {type(value).__name__}')
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False, default=scalar) + '\n')


class Ledger:
    def __init__(self, private, config):
        self.private = private
        self.handle = (ROOT / 'private' / NAMESPACE / 'fit_events.jsonl').open('a+')
        fcntl.flock(self.handle, fcntl.LOCK_EX)
        self.handle.seek(0)
        self.previous = sum(1 for line in self.handle if line.strip())
        self.count = 0
        self.limit = config['limits']['head_fit_attempts']

    def __call__(self, details):
        if self.previous + self.count >= self.limit:
            raise RuntimeError('HEAD_FIT_BUDGET_EXCEEDED')
        self.count += 1
        self.handle.write(json.dumps(dict(run=self.private.name, count=self.previous + self.count, details=details)) + '\n')
        self.handle.flush()

    def close(self):
        self.handle.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['test', 'prepare', 'fit', 'recover', 'report'])
    parser.add_argument('--run', required=True)
    parser.add_argument('--config', default='configs/auditory_fseries_archival_v1.json')
    parser.add_argument('--test-run')
    parser.add_argument('--input-run')
    args = parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('SLURM_REQUIRED')
    if any(not r or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in r)
           for r in [args.run] + [r for r in [args.test_run, args.input_run] if r]):
        raise ValueError('UNSAFE_RUN_NAME')
    os.umask(0o077)
    private, public, report = [ROOT / directory / NAMESPACE / args.run for directory in ['private', 'results', 'reports']]
    if any(p.exists() for p in [private, public, report]):
        raise FileExistsError('RUN_OCCUPIED')
    for path in [private, public, report]:
        path.mkdir(mode=0o700)
    config_path = ROOT / args.config
    config = json.loads(config_path.read_text())
    paths = [*sorted((ROOT / 'auditory_fseries').glob('*.py')), *sorted((ROOT / 'tests/auditory_fseries').glob('*.py')),
             config_path, ROOT / 'docs/auditory_fseries_archival/PROTOCOL_v1.md']
    hashes = {}
    for path in paths:
        rel = path.relative_to(ROOT)
        target = private / 'source' / rel
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copyfile(path, target)
        hashes[str(rel)] = digest(path)
    start = dict(job_id=os.environ['SLURM_JOB_ID'], command=args.command, run=args.run, start_unix=time.time(),
                 config_sha256=digest(config_path), source_hashes=hashes, arguments=vars(args))
    start['resources'] = {key: os.environ.get(key) for key in ['SLURM_CPUS_PER_TASK', 'SLURM_MEM_PER_NODE', 'SLURM_JOB_PARTITION', 'SLURM_JOB_NODELIST']}
    dump(private / 'start.json', start)
    ledger = None
    try:
        from . import models
        if args.command in ['test', 'fit']:
            ledger = Ledger(private, config)
            models.set_recorder(ledger)
        if args.command in ['prepare', 'fit']:
            if not args.test_run:
                raise ValueError('TEST_GATE_REQUIRED')
            tested = ROOT / 'private' / NAMESPACE / args.test_run
            receipt = json.loads((tested / 'completion.json').read_text())
            reference = json.loads((tested / 'start.json').read_text())
            if receipt['status'] != 'PASS' or reference['config_sha256'] != start['config_sha256']:
                raise ValueError('INVALID_TEST_GATE')
            for rel in ['auditory_fseries/models.py', 'auditory_fseries/data.py']:
                if reference['source_hashes'].get(rel) != hashes.get(rel):
                    raise ValueError('TESTED_SOURCE_MISMATCH')
        if args.command == 'test':
            import pytest
            with (private / 'pytest.log').open('w') as handle, contextlib.redirect_stdout(handle), contextlib.redirect_stderr(handle):
                rc = pytest.main(['-q', '--import-mode=importlib', '-p', 'no:cacheprovider', '--basetemp=' + str(private / 'tmp'),
                    '--junitxml=' + str(private / 'tests.xml'), 'tests/auditory_fseries'])
            tree = ET.parse(private / 'tests.xml').getroot()
            counts = {k: len(tree.findall('.//' + k)) for k in ['testcase', 'failure', 'error', 'skipped']}
            result = dict(status='PASS' if rc == 0 and not any(counts[k] for k in ['failure', 'error', 'skipped']) else 'FAIL',
                          tests=counts, scope='synthetic_identity_isolation_readout_and_feature_contracts')
        elif args.command == 'prepare':
            from .data import prepare
            result = prepare(ROOT, private, public, config)
            if (private / 'data.npz').exists():
                result['data_sha256'] = digest(private / 'data.npz')
        elif args.command == 'fit':
            import numpy as np
            source = ROOT / 'private' / NAMESPACE / args.input_run
            receipt = json.loads((source / 'completion.json').read_text())
            prepared_start = json.loads((source / 'start.json').read_text())
            if receipt['status'] != 'READY' or prepared_start['source_hashes'].get('auditory_fseries/data.py') != hashes.get('auditory_fseries/data.py'):
                raise ValueError('PREPARED_SOURCE_OR_STATUS_MISMATCH')
            if receipt['config_sha256'] != start['config_sha256'] or digest(source / 'data.npz') != receipt['data_sha256']:
                raise ValueError('FROZEN_INPUT_MISMATCH')
            with np.load(source / 'data.npz', allow_pickle=False) as arrays:
                data = {k: arrays[k] for k in arrays.files}
            dump(private / 'input_binding.json', dict(run=args.input_run, data_sha256=receipt['data_sha256'], completion_sha256=digest(source / 'completion.json')))
            result = models.run_models(data, config, private, public)
        elif args.command == 'recover':
            from .reporting import recover
            result = recover(ROOT, private, public, config, args.input_run)
        else:
            from .reporting import finalize
            result = finalize(ROOT, private, public, report, config, args.input_run)
        if ledger:
            result.update(head_fit_attempts_this_run=ledger.count, head_fit_attempts_round=ledger.previous + ledger.count)
        result.update(job_id=start['job_id'], config_sha256=start['config_sha256'], elapsed_seconds=time.time()-start['start_unix'])
        dump(private / 'completion.json', result)
        dump(public / 'summary.json', result)
        print(json.dumps({k: result[k] for k in ['status', 'job_id', 'elapsed_seconds', 'head_fit_attempts_this_run', 'head_fit_attempts_round', 'identity_groups'] if k in result}))
        return 0 if result['status'] not in ['FAIL', 'FAILED'] else 1
    except Exception as exc:
        dump(private / 'failure.json', dict(type=type(exc).__name__, traceback=traceback.format_exc(),
            fits_this_run=ledger.count if ledger else 0))
        dump(public / 'failure.json', dict(status='FAILED', type=type(exc).__name__, details='private'))
        print(json.dumps(dict(status='FAILED', job_id=start['job_id'], details='private')))
        return 1
    finally:
        if ledger:
            ledger.close()


if __name__ == '__main__':
    raise SystemExit(main())
