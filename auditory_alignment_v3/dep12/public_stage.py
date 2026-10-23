"""DEP12 public CPU stage driver with claim locks (Agent M): measure -> attention per (cohort, encoder) item.

Each item is processed under an exclusive fcntl lock (private/.../dep12/public/stage_locks/<ds>__<encoder>.lock) and skipped when
already done (measure.done / attention.done), so parallel steps never compute the same item. Outputs are written by the
unchanged measure.run / attention.run (calibration.json and people.json last, atomically), i.e. identical to run-all.
CLI (Slurm only): python -m auditory_alignment_v3.dep12.public_stage --items ds:encoder [ds:encoder ...]
                  python -m auditory_alignment_v3.dep12.public_stage --todo        (lists items not yet measured / scored)
"""
from __future__ import annotations

import argparse
import fcntl
import os
import time

from . import attention as AT
from . import measure_v5 as M
from . import panels as PN
from . import public_features_v5 as PF

LOCKS = PN.OUT / 'stage_locks'


def todo():
    out = []
    for r in PF.plan_rows():
        if not (PF.FEAT / 'units' / f'{r["id"]}.json').exists():
            continue
        for n in r['encoders']:
            if not AT.done(n, r['dataset']):
                out.append((r['dataset'], n, 'measured' if M.done(n, r['dataset']) else 'unmeasured'))
    return out


def process(ds, name):
    LOCKS.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = LOCKS / f'{ds}__{name}.lock'
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(ds, name, 'locked elsewhere', flush=True); return
        t0 = time.time()
        if not M.done(name, ds):
            M.run(name, ds)
        if not AT.done(name, ds):
            AT.run(name, ds)
        print(ds, name, 'stage done', round(time.time() - t0, 1), flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--items', nargs='*', default=[]); ap.add_argument('--todo', action='store_true')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    if a.todo:
        for t in todo():
            print(*t)
        return
    for it in a.items:
        ds, name = it.split(':', 1)
        process(ds, name)


if __name__ == '__main__':
    main()
