"""ALN4.1 R2 private CE runner v2: the plan-frozen R2 private fits through the resumable run_unit (private_ft_resume.py).

r2.py, r2_lanes.py and private_ft.py stay byte-identical; seeds, plans, per-seed smoke receipts and unit claims are r2's own
(the same claims/<id>.lock files, so an old-path job and a new-path job never run one unit at once). Differences from r2:
  * a unit runs private_ft_resume.run_unit, which continues an interrupted fit from its last completed epoch;
  * a unit process killed by a signal (preemption) leaves no FAILED marker; any other failure writes one, as before;
  * `--resume-smoke` (seed 3413, the B0 fold-0 row, 3 epochs x 3 updates; nothing it writes is a production unit):
      A  uninterrupted run, A2 its repeat (GPU non-determinism floor),
      B  run stopped after epoch 1 (simulated preemption) and restarted -> must resume at epoch 2,
      C  the original private_ft.run_unit probe (1 epoch x 3 updates) and D the resumable probe, same settings.
    Pass: B resumed; |curve(A) - curve(B)| and |curve(C) - curve(D)| <= 1e-4 bits; equal selected epochs;
    the final-parameter difference A-B is reported next to the A-A2 floor.
Usage: `python -m auditory_alignment_v3.aln41.r2_private_resume <--resume-smoke | --smoke --seed S | --worker [--arm A] | --unit ID --seed S>`.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

import numpy as np

from . import r2 as R, private_ft as PF, private_ft_resume as PR

SMOKE_ROOT = R.ROOT / 'private_resume_v1'
SMOKE_SEED = 3413
TOL_BITS = 1e-4


def sources():
    return {f: R.sha(Path(__file__).parent / f) for f in ('private_ft.py', 'private_ft_resume.py', 'r2.py', 'r2_private_resume.py')}


def smoke_passed():
    for path in sorted((SMOKE_ROOT / 'probes').glob('*/receipt.json')):
        rec = R.read(path)
        if rec.get('status') == 'pass' and rec.get('sources') == sources():
            return True
    return False


def resume_smoke():
    import torch
    job = os.environ['SLURM_JOB_ID']; out = SMOKE_ROOT / 'probes' / job
    receipt = {'status': 'running', 'job': job, 'sources': sources(), 'seed': SMOKE_SEED}
    try:
        with R.seeded(SMOKE_SEED):
            plan = R.read(PF.BASE / 'plan.json'); PF.verify(plan)
            row = next(r for r in plan['rows'] if r['arm'] == 'B0' and r['outer_fold'] == 0)
            store = PF.STORE / 'probes' / f'resume_{job}'
            ov = {'epochs': 3, 'per_epoch': 3}

            def go(tag, **extra):
                return PR.run_unit(row, plan, dest=store / tag, record_dir=out / tag, overrides={**ov, **extra})
            A = go('A'); A2 = go('A2')
            try:
                go('B', stop_after=1); raise AssertionError('simulated preemption did not stop the run')
            except PR.Interrupted:
                pass
            B = go('B')
            C = PF.run_unit(row, plan, probe=True)
            D = PR.run_unit(row, plan, probe=True, dest=store / 'D', record_dir=out / 'D')

            def curve_diff(x, y):
                assert [c['epoch'] for c in x['curve']] == [c['epoch'] for c in y['curve']]
                return max(abs(a['es_nll_bits'] - b['es_nll_bits']) for a, b in zip(x['curve'], y['curve']))

            def param_diff(x, y):
                sx = torch.load(x['checkpoints']['last'], map_location='cpu'); sy = torch.load(y['checkpoints']['last'], map_location='cpu')
                return max(float((sx[k].float() - sy[k].float()).abs().max()) for k in sx)
            checks = {'B_segments': [s['first_epoch'] for s in B['resume']['segments']],
                      'curve_A_B': curve_diff(A, B), 'curve_A_A2': curve_diff(A, A2), 'curve_C_D': curve_diff(C, D),
                      'selected_epoch_A_B': [A['selected_epoch'], B['selected_epoch']], 'selected_epoch_C_D': [C['selected_epoch'], D['selected_epoch']],
                      'param_maxabs_A_B': param_diff(A, B), 'param_maxabs_A_A2': param_diff(A, A2), 'param_maxabs_C_D': param_diff(C, D),
                      'resume_file_removed': not (store / 'B' / 'resume.pt').exists()}
            receipt['checks'] = checks
            assert checks['B_segments'] == [1, 2], checks
            assert checks['curve_A_B'] <= TOL_BITS and checks['curve_C_D'] <= TOL_BITS, checks
            assert A['selected_epoch'] == B['selected_epoch'] and C['selected_epoch'] == D['selected_epoch'], checks
            assert checks['resume_file_removed'] and all(np.isfinite(c['es_nll_bits']) for c in B['curve']), checks
            receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        R.write(out / 'receipt.json', receipt)
    print(json.dumps(receipt['checks'], indent=1), flush=True)


def claim_and_run(seed, base, row):
    path = base / 'units' / f'{row["id"]}.json'
    lock = base / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists():
            return False
        rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id'], '--seed', str(seed)]).returncode
        if rc < 0:
            raise SystemExit(f'unit process ended by signal {-rc}; resume state kept, no FAILED marker')
        if rc or not path.exists():
            R.write(base / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc, 'seed': seed,
                                                                  'runner': 'r2_private_resume'})
            raise RuntimeError('aln41 R2 private unit failed')
    return True


def worker(arm, max_units):
    assert smoke_passed(), 'resume smoke has not passed for these sources'
    count = 0
    for seed in R.SEEDS:
        with R.seeded(seed):
            M, base, rows, ready = R.stage_rows('private', arm)
            M.verify(R.read(base / 'plan.json'))
            if not M.receipts()['pass']:
                continue
            for row in rows:
                if (base / 'units' / f'{row["id"]}.json').exists() or (base / 'units' / f'{row["id"]}.FAILED.json').exists() or not ready(row):
                    continue
                count += claim_and_run(seed, base, row)
                if count >= max_units:
                    return


def run_one(seed, unit):
    with R.seeded(seed):
        plan = R.read(PF.BASE / 'plan.json'); PF.verify(plan)
        PR.run_unit(next(r for r in plan['rows'] if r['id'] == unit), plan)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--resume-smoke', action='store_true'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--worker', action='store_true'); ap.add_argument('--unit'); ap.add_argument('--seed', type=int)
    ap.add_argument('--arm', choices=PF.ARMS); ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.resume_smoke:
        resume_smoke()
    elif a.smoke:
        with R.seeded(a.seed):
            R.private_smoke(a.seed)
    elif a.unit:
        run_one(a.seed, a.unit)
    else:
        assert a.worker
        worker(a.arm, a.max_units)


if __name__ == '__main__':
    main()
