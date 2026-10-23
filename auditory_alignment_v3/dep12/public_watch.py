"""DEP12 public follow-up CPU driver (Agent M): ext2 cs_pair_noise (M19), Federici (M20) and ext3 ssl_continue (M21) items.

worker   : poll every 5 min; for every target item (cohort, encoder) whose feature unit is complete: measure -> attention under the
           public_stage claim lock, then the K = 8 debiased score under its own lock; exits when every target row has a unit and
           every item is done (or after --hours).
reporter : waits until every target item is done, runs public_report (F_EXT2, Federici descriptive families, EXT2_PUBLIC.md, gzip
           copy), then waits for the ext2 perturbation units, runs perturb_v3 measure-all and public_report again.
CLI (Slurm only): python -m auditory_alignment_v3.dep12.public_watch {worker, reporter} [--hours H]
"""
from __future__ import annotations

import argparse
import fcntl
import os
import time

from . import attention as AT
from . import attention_debiased as AD
from . import public_features_v5 as PF
from . import public_stage as ST


def targets():
    rows = [r for r in PF.plan_rows() if r['dataset'] == 'federici' or any(n.startswith(('cs_pair_noise@', 'ssl_continue@')) for n in r['encoders'])]
    ready = [(r['dataset'], n) for r in rows if (PF.FEAT / 'units' / f'{r["id"]}.json').exists() for n in r['encoders']]
    return rows, ready


def item_done(ds, n):
    return AT.done(n, ds) and AD.done(n, ds)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def worker(hours):
    t_end = time.time() + hours * 3600
    while time.time() < t_end:
        rows, ready = targets(); did = 0
        for ds, n in ready:
            if item_done(ds, n):
                continue
            ST.process(ds, n)                                  # measure -> attention (locked; skips when done / locked)
            if AT.done(n, ds) and not AD.done(n, ds):
                AD.LOCKS.mkdir(parents=True, exist_ok=True, mode=0o700)
                with (AD.LOCKS / f'deb__{ds}__{n}.lock').open('a+') as h:
                    try:
                        fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        continue
                    if not AD.done(n, ds):
                        AD.run(n, ds); did += 1
        n_rows_done = sum((PF.FEAT / 'units' / f'{r["id"]}.json').exists() for r in rows)
        if n_rows_done == len(rows) and all(item_done(ds, n) for ds, n in targets()[1]):
            log('worker: all target items done'); return
        if not did:
            log(f'worker: waiting (units {n_rows_done}/{len(rows)}, items done {sum(item_done(d, n) for d, n in ready)}/{len(ready)})')
            time.sleep(300)


def reporter(hours):
    from . import perturb_v4 as PT
    from . import public_report as RP
    t_end = time.time() + hours * 3600
    while time.time() < t_end:
        rows, ready = targets()
        if sum((PF.FEAT / 'units' / f'{r["id"]}.json').exists() for r in rows) == len(rows) and all(item_done(ds, n) for ds, n in ready):
            break
        time.sleep(300)
    log('reporter: report 1'); RP.main()
    from . import manipulation as MC
    MC.main(); RP.main()                                        # manipulation check, then the report again (EXT3_PUBLIC.md includes it)
    while time.time() < t_end:
        prow = [r for r in PT.plan_rows() if any(n.startswith(('cs_pair_noise@', 'ssl_continue@')) for n in r['encoders'])]
        if prow and all((PT.BASE / 'units' / f'{r["id"]}.json').exists() for r in prow):
            log('reporter: perturbation measure-all'); PT.measure_all(); log('reporter: report 2'); RP.main(); return
        time.sleep(300)
    log('reporter: perturbation ext2 units not complete before the deadline')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('role', choices=('worker', 'reporter')); ap.add_argument('--hours', type=float, default=36.0)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    (worker if a.role == 'worker' else reporter)(a.hours)


if __name__ == '__main__':
    main()
