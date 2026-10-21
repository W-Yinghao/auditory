"""Read-only fleet readiness for the ALN3.6 R2 replication (seed 3407; operational only, the runners are plan-frozen).

Items: FAU group local / CB (6 fits each; the smoke runs once in the local item, as in R1), public feature banks (52),
the matched AP / APwrong pair (aln36.r2_apwrong) and its private window features (plan made after the 10 targets exist).
"""
from __future__ import annotations

from . import common as C, r2 as R, r2_apwrong as RW

GROUP = {'local_L1': ('c3_s35r2a36loc', 's35_r2_aln36_group_local', 'slurm/aln35_r2a36_group_local.sbatch'),
         'CBpre_true_full': ('c3_s35r2a36cb', 's35_r2_aln36_group_cb', 'slurm/aln35_r2a36_group_cb.sbatch')}
FEAT = ('c3_s35r2a36feat', 's35_r2_aln36_features', 'slurm/aln35_r2a36_features.sbatch')
PRIV = ('c3_s35r2a36priv', 's35_r2_aln36_private', 'slurm/aln35_r2a36_private.sbatch')


def item(names, state, ready=0, remaining=None, submit=(), slots=1):
    name, lane, sbatch = names
    return {'name': name, 'lane': lane, 'state': state, 'ready': ready, 'remaining': remaining, 'slots': slots, 'initial': [],
            'submit': [sbatch, *submit] if ready else []}


def group_items():
    out = []
    plan = C.read(R.G.PLAN) if R.G.PLAN.exists() else None
    rec = R.G.receipts()
    for tool, names in GROUP.items():
        if plan is None:
            out.append(item(names, 'plan_missing')); continue
        left = [r for r in plan['rows'] if r['tool'] == tool and not (R.G.BASE / 'units' / f'{r["experiment_id"]}.json').exists()]
        if not left:
            out.append(item(names, 'complete', remaining=0)); continue
        if any((R.G.BASE / 'units' / f'{r["experiment_id"]}.FAILED.json').exists() for r in left):
            out.append(item(names, 'failed_unit_review', remaining=len(left))); continue
        if not rec['pass']:
            if rec['other']:
                out.append(item(names, 'engineering_probe_failed', remaining=len(left)))
            elif tool == 'local_L1':
                out.append(item(names, 'ready', 1, len(left), ['--smoke']))
            else:
                out.append(item(names, 'awaiting_smoke', remaining=len(left)))
            continue
        out.append(item(names, 'ready', len(left), len(left), ['--worker', '--tool', tool], slots=2))
    return out


def feature_item():
    if not R.F.PLAN.exists():
        return item(FEAT, 'plan_missing')
    plan = C.read(R.F.PLAN)
    left = [r for r in plan['rows'] if not (R.F.BASE / 'units' / f'{r["id"]}.json').exists()]
    if not left:
        return item(FEAT, 'complete', remaining=0)
    if any((R.F.BASE / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return item(FEAT, 'failed_unit_review', remaining=len(left))
    rec = R.F.receipts()
    if not rec['pass']:
        return item(FEAT, 'engineering_probe_failed', remaining=len(left)) if rec['other'] else item(FEAT, 'ready', 1, len(left), ['--smoke'])
    ready = [r for r in left if R.F.ready(r)]
    return item(FEAT, 'ready' if ready else 'waiting_for_sources', len(ready), len(left), ['--worker'], slots=2)


def private_item():
    if not R.PFE.PLAN.exists():
        return item(PRIV, 'plan_missing_until_r2_apwrong_targets')
    plan = C.read(R.PFE.PLAN)
    left = [r for r in plan['rows'] if not (R.PFE.BASE / 'units' / f'{r["id"]}.json').exists()]
    if not left:
        return item(PRIV, 'complete', remaining=0)
    rec = R.PFE.receipts()
    if not rec['pass']:
        return item(PRIV, 'engineering_probe_failed', remaining=len(left)) if rec['other'] else item(PRIV, 'ready', 1, len(left), ['--smoke'])
    return item(PRIV, 'ready', 1, len(left), ['--smoke-job', rec['pass'][-1].parent.name])


def fleet_status():
    with R.seeded():
        out = group_items() + [feature_item(), RW.fleet_status(), private_item()]
    return out
