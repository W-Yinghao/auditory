"""Paper line, Table 2 external decoders: generic frozen-plan / smoke-receipt / claim / worker machinery (pattern of paper/arms.py).

A system module S provides: NAME (lane job name), LANE, SBATCH, OUT (Path), make_plan() -> plan dict (immutable, 0444, written
before any result), verify(plan), run_unit(row, plan, probe) -> record written to OUT/units/<id>.json (probe: OUT/probes/<job>/
units/<id>.json; a probe never scores a test segment), smoke() -> writes OUT/probes/<job>/receipt.json {status, plan_sha256}.
Units run as subprocesses (`python -m auditory_alignment_v3.paper.external_decoders unit --system S --id ID`) under a
non-blocking flock claim; a non-zero return writes <id>.FAILED.json (a signal / preemption does not, so the unit resumes).
"""
from __future__ import annotations

import fcntl
import os
import subprocess
import sys

from . import ext_common as XC

read, write, sha = XC.read, XC.write, XC.sha
DISPATCH = 'auditory_alignment_v3.paper.external_decoders'


def receipts(S):
    out = {'pass': [], 'other': []}
    if not (S.OUT / 'plan.json').exists():
        return out
    ps = sha(S.OUT / 'plan.json')
    for path in sorted((S.OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == ps:
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def open_rows(S):
    plan = read(S.OUT / 'plan.json')
    return [(r, (S.OUT / 'units' / f'{r["id"]}.FAILED.json').exists()) for r in plan['rows']
            if not (S.OUT / 'units' / f'{r["id"]}.json').exists()]


def fleet_status(S, ready_fn=None, slots=1, max_units=4):
    st = {'name': S.NAME, 'lane': S.LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 20, 'slots': 1, 'initial': [], 'submit': []}
    if not (S.OUT / 'plan.json').exists():
        return st
    left = open_rows(S)
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any(f for _, f in left):
        return {**st, 'state': 'failed_unit_review'}
    rec = receipts(S)
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [S.SBATCH, 'smoke', '--system', S.SYSTEM]}
    ready = [r for r, _ in left if ready_fn is None or ready_fn(r)]
    if not ready:
        return {**st, 'state': 'waiting_for_dependencies'}
    return {**st, 'state': 'ready', 'ready': len(ready), 'slots': slots,
            'submit': [S.SBATCH, 'worker', '--system', S.SYSTEM, '--max-units', str(max_units)]}


def sub(system, *args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', DISPATCH, *map(str, args), '--system', system]).returncode


def claim(S, uid, fn):
    path = S.OUT / 'units' / f'{uid}.json'
    lock = S.OUT / 'claims' / f'{uid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists():
            return False
        rc = fn()
        if rc < 0:                           # preempted / signalled: no FAILED marker, the unit resumes elsewhere
            raise SystemExit(rc)
        if rc or not path.exists():
            write(S.OUT / 'units' / f'{uid}.FAILED.json', {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc})
            raise RuntimeError(f'{S.SYSTEM} unit failed: {uid}')
        return True


def worker(S, max_units, ready_fn=None):
    assert receipts(S)['pass'], 'no passing smoke'
    plan = read(S.OUT / 'plan.json'); S.verify(plan)
    count = 0
    for row, failed in open_rows(S):
        if failed or (ready_fn is not None and not ready_fn(row)):
            continue
        if claim(S, row['id'], lambda: sub(S.SYSTEM, 'unit', '--id', row['id'])):
            count += 1
        if count >= max_units:
            break
