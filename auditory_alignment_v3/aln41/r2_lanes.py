"""Read-only fleet readiness for the ALN4.1 R2 replication (operational only; the runner aln41/r2.py is plan-frozen).

Items: source (8 fits over both seeds), private CE per arm (B0 / TCS / TNCE, 10 fits each) and frozen (40 units). Each
seed's plan needs its own passing smoke receipt; a pending smoke is submitted before work of the other seed (smokes are
minutes long). Private smokes are owned by the B0 item; the frozen smoke waits for that seed's TCS source.
"""
from __future__ import annotations

from . import r2 as R

NAMES = {'source': ('c3_s35r2a41src', 's35_r2_aln41_source', 'slurm/aln35_r2a41_source.sbatch'),
         'frozen': ('c3_s35r2a41frz', 's35_r2_aln41_frozen', 'slurm/aln35_r2a41_frozen.sbatch')}
PRIVATE_NAMES = {arm: ('c3_s35r2a41p' + tag, 's35_r2_aln41_private_' + tag, f'slurm/aln35_r2a41_private_{tag}.sbatch')
                 for arm, tag in (('B0', 'b0'), ('TCS', 'tcs'), ('TNCE', 'tnc'))}


def item(name, lane, sbatch, state, ready=0, remaining=None, submit=(), slots=1):
    return {'name': name, 'lane': lane, 'state': state, 'ready': ready, 'remaining': remaining, 'slots': slots,
            'initial': [], 'submit': [sbatch, *submit] if ready else []}


def stage_status(stage, name, lane, sbatch, arm=None, smoke_owner=True):
    remaining, ready, smoke, failed, waiting = 0, 0, None, [], False
    for seed in R.SEEDS:
        with R.seeded(seed):
            plan_dir = {'source': R.SRC.BASE, 'private': R.PF.BASE, 'frozen': R.FZ.BASE}[stage]
            if not (plan_dir / 'plan.json').exists():
                waiting = True; continue
            M, base, rows, ok = R.stage_rows(stage, arm)
            left = [r for r in rows if not (base / 'units' / f'{r["id"]}.json').exists()]
            remaining += len(left)
            if not left:
                continue
            if any((base / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
                failed.append(seed)
            rec = M.receipts()
            if not rec['pass']:
                if rec['other']:
                    failed.append(seed)
                elif smoke is None and smoke_owner and (stage != 'frozen' or any(ok(r) for r in rows if r['arm'] == 'TCS')):
                    smoke = seed
                continue
            ready += sum(1 for r in left if ok(r) and not (base / 'units' / f'{r["id"]}.FAILED.json').exists())
    if remaining == 0 and not waiting:
        return item(name, lane, sbatch, 'complete', remaining=0)
    if failed:
        return item(name, lane, sbatch, 'engineering_or_unit_failure_review', remaining=remaining)
    if smoke is not None:
        return item(name, lane, sbatch, 'ready', 1, remaining, ['--smoke', '--seed', str(smoke)])
    if ready:
        return item(name, lane, sbatch, 'ready', ready, remaining, ['--worker', *(['--arm', arm] if arm else [])], slots=2)
    return item(name, lane, sbatch, 'waiting_for_sources_or_smoke', remaining=remaining)


def fleet_status():
    out = [stage_status('source', *NAMES['source'])]
    for arm, names in PRIVATE_NAMES.items():
        out.append(stage_status('private', *names, arm=arm, smoke_owner=arm == 'B0'))
    out.append(stage_status('frozen', *NAMES['frozen']))
    return out
