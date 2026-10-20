"""Operational resume fix: restore serialized CUDA RNG bytes from CPU tensors.

The original plan, trainer, update schedule and identities remain unchanged.
Every new execution has a separate loader-provenance receipt.
"""
from contextlib import contextmanager
from datetime import datetime
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import torch

from . import matched_updates as M

SOURCE_SHA = '33f5c4d8b766e7b84f7b14c45c64240b493c6d9c2b00f2862a111190df99a4cf'
PLAN_SHA = 'b2442196bf98a2a321d8406ea2f829611bb10c6876cfff16849a8fb9ff46014e'
AUDIT = M.BASE / 'resume_loader_v2'


@contextmanager
def cpu_rng_state_restore():
    original = torch.cuda.set_rng_state_all
    def restore(states):
        assert all(isinstance(state, torch.Tensor) and state.dtype == torch.uint8 for state in states)
        return original([state.cpu() for state in states])
    torch.cuda.set_rng_state_all = restore
    try:
        yield
    finally:
        torch.cuda.set_rng_state_all = original


def verify():
    assert M.B.sha(M.__file__) == SOURCE_SHA
    assert M.B.sha(M.PLAN) == PLAN_SHA
    plan = M.A.read(M.PLAN)
    M.verify(plan)
    return plan


def check_rng():
    assert torch.cuda.is_available()
    before = torch.cuda.get_rng_state_all()
    expected = torch.rand(17, device='cuda')
    loaded = [state.to('cuda') for state in before]
    original_rejected = False
    try:
        torch.cuda.set_rng_state_all(loaded)
    except TypeError:
        original_rejected = True
    assert original_rejected, 'expected original resumed-state device error was not reproduced'
    with cpu_rng_state_restore():
        torch.cuda.set_rng_state_all(loaded)
        actual = torch.rand(17, device='cuda')
        assert torch.equal(expected, actual), 'restored RNG bytes do not reproduce the continuation'
        torch.cuda.set_rng_state_all(before)
    receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'],
               'device': torch.cuda.get_device_name(0), 'old_error_reproduced': True,
               'continuation_exact': True, 'source_sha256': M.B.sha(__file__)}
    M.B.write(AUDIT / 'checks' / (os.environ['SLURM_JOB_ID'] + '.json'), receipt)
    print('RNG RESTORE CHECK PASS', flush=True)


def run_one(unit):
    verify()
    checkpoint = M.STORE / 'production' / unit['id'] / 'resume.pt'
    receipt = {'id': unit['id'], 'job': os.environ['SLURM_JOB_ID'], 'status': 'running',
               'started': datetime.now().astimezone().isoformat(), 'plan_sha256': PLAN_SHA,
               'original_entrypoint_sha256': SOURCE_SHA, 'loader_sha256': M.B.sha(__file__),
               'device': torch.cuda.get_device_name(0), 'checkpoint_before': str(checkpoint),
               'checkpoint_before_sha256': M.B.sha(checkpoint) if checkpoint.exists() else None,
               'change': 'CUDA RNG byte tensors moved to CPU before the original setter; no reseeding or state reset'}
    target = AUDIT / 'executions' / os.environ['SLURM_JOB_ID'] / (unit['id'] + '.json')
    M.B.write(target, receipt)
    try:
        with cpu_rng_state_restore():
            M.run_unit(unit)
        result = M.A.read(M.BASE / 'units' / (unit['id'] + '.json'))
        assert result['status'] == 'complete' and not result['probe'] and result['plan_sha256'] == PLAN_SHA
        receipt.update(status='complete', result_sha256=M.B.sha(M.BASE / 'units' / (unit['id'] + '.json')))
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc())
        raise
    finally:
        receipt['finished'] = datetime.now().astimezone().isoformat()
        M.B.write(target, receipt)


def fleet_status():
    assert M.B.sha(M.__file__) == SOURCE_SHA and M.B.sha(M.PLAN) == PLAN_SHA
    status = M.fleet_status()
    checks = list((AUDIT / 'checks').glob('*.json'))
    checks = [p for p in checks if M.A.read(p).get('status') == 'pass'
              and M.A.read(p).get('source_sha256') == M.B.sha(__file__)]
    if not checks:
        return {**status, 'state': 'engineering_resume_check_required', 'ready': 0}
    if status['state'] == 'ready':
        status['submit'] = ['slurm/aln35_matched_resume_v2.sbatch', *status['submit'][1:]]
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--unit')
    parser.add_argument('--retry-unit')
    parser.add_argument('--check-rng', action='store_true')
    parser.add_argument('--smoke-job')
    parser.add_argument('--max-units', type=int, default=1)
    args = parser.parse_args()
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    plan = verify()
    if args.check_rng:
        check_rng()
    if args.unit:
        run_one(next(u for u in plan['rows'] if u['id'] == args.unit))
        return
    if args.retry_unit:
        unit = next(u for u in plan['rows'] if u['id'] == args.retry_unit)
        failure = M.BASE / 'units' / (unit['id'] + '.FAILED.json')
        lock = M.BASE / 'claims' / (unit['id'] + '.lock')
        with lock.open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            assert M.A.read(failure) == {'job': '1050185', 'returncode': 1}
            previous_sha = M.B.sha(failure)
            run_one(unit)
            archive = AUDIT / 'failure_history' / (unit['id'] + '.' + previous_sha + '.json')
            archive.parent.mkdir(parents=True, exist_ok=True)
            assert M.B.sha(failure) == previous_sha and not archive.exists()
            os.replace(failure, archive)
        # The ordinary matched worker is the sole writer of selection refresh.
        # The retry itself does not race that writer; the next ordinary unit
        # refresh includes this completed trajectory automatically.
        return
    if args.check_rng and not args.smoke_job:
        return
    probe = M.A.read(M.BASE / 'probes' / str(args.smoke_job) / 'receipt.json')
    assert probe['status'] == 'pass' and probe['plan_sha256'] == PLAN_SHA
    done = 0
    ordered = sorted(plan['rows'], key=lambda u: (u['stage'] != 'inner', not u['reuse_existing'], u['id']))
    for unit in ordered:
        output = M.BASE / 'units' / (unit['id'] + '.json')
        failure = output.with_name(unit['id'] + '.FAILED.json')
        if output.exists() or failure.exists() or not M.ready(unit):
            continue
        lock = M.BASE / 'claims' / (unit['id'] + '.lock')
        with lock.open('a+') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if output.exists() or failure.exists():
                continue
            result = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', unit['id']])
            if result.returncode or not output.exists():
                M.B.write(failure, {'job': os.environ['SLURM_JOB_ID'], 'returncode': result.returncode})
                raise RuntimeError('matched trajectory failed; resume-loader provenance retained')
        from . import selection_policy
        selection_policy.refresh()
        done += 1
        if done >= args.max_units:
            break


if __name__ == '__main__':
    main()
