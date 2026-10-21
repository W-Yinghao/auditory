"""Per-arm scheduling for the ALN4.1 private CE fits (operational only; private_ft.py and its plan stay frozen).

One readiness item per arm (B0 / TCS / TNCE), each <= 2 workers with its own job name, so the 15 fits can use up to six
released runfill slots. A worker claims one unit of its arm with the same lock files as private_ft's own loop and runs the
unchanged `python -m auditory_alignment_v3.aln41.private_ft --unit <id>` (which re-verifies the frozen plan).
"""
from __future__ import annotations

import argparse
import fcntl
import os
import subprocess
import sys

from . import private_ft as PF

ARM_TAG = {'B0': 'b0', 'TCS': 'tcs', 'TNCE': 'tnc'}


def fleet_status():
    items = []
    plan = PF.read(PF.BASE / 'plan.json') if (PF.BASE / 'plan.json').exists() else None
    rec = PF.receipts()
    for arm in PF.ARMS:
        tag = ARM_TAG[arm]
        st = {'name': 'c3_s35a41p' + tag, 'lane': 's35_aln41_private_' + tag, 'state': 'plan_missing', 'ready': 0, 'remaining': 5,
              'slots': 1, 'initial': [], 'submit': []}
        items.append(st)
        if plan is None:
            continue
        remaining = [r for r in plan['rows'] if r['arm'] == arm and not (PF.BASE / 'units' / f'{r["id"]}.json').exists()]
        st['remaining'] = len(remaining)
        if not remaining:
            st['state'] = 'complete'; continue
        if not rec['pass']:
            st['state'] = 'engineering_probe_failed' if rec['other'] else 'awaiting_smoke'; continue
        available = [r for r in remaining if PF.ready(r) and not (PF.BASE / 'units' / f'{r["id"]}.FAILED.json').exists()]
        st.update(state='ready' if available else 'waiting_for_sources', ready=len(available), slots=2,
                  submit=[f'slurm/aln35_aln41_private_{tag}.sbatch', '--smoke-job', rec['pass'][-1].parent.name, '--arm', arm])
    return items


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--smoke-job', required=True); ap.add_argument('--arm', choices=PF.ARMS, required=True)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    plan = PF.read(PF.BASE / 'plan.json'); PF.verify(plan)
    rec = PF.read(PF.BASE / 'probes' / str(a.smoke_job) / 'receipt.json'); assert rec['status'] == 'pass' and rec['plan_sha256'] == PF.sha(PF.BASE / 'plan.json')
    for row in plan['rows']:
        path = PF.BASE / 'units' / f'{row["id"]}.json'
        if row['arm'] != a.arm or path.exists() or (PF.BASE / 'units' / f'{row["id"]}.FAILED.json').exists() or not PF.ready(row):
            continue
        lock = PF.BASE / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', 'auditory_alignment_v3.aln41.private_ft', '--unit', row['id']]).returncode
            if rc or not path.exists():
                PF.write(PF.BASE / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln41 private FT unit failed')
        break


if __name__ == '__main__':
    main()
