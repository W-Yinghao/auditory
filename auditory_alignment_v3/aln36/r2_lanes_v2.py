"""Read-only fleet readiness for the ALN3.6 R2 replication, v2 (engineering fix, 2026-10-21; r2_lanes.py unchanged).

Only the private window-feature item changes: it submits slurm/aln35_r2a36_private_v2.sbatch (aln36.r2_inproc, which forwards
`--smoke` / `--smoke-job` to the R1 private_features main; see r2_inproc.py) under the new job name c3_s35r2a36priv2, and it
stops at a unit FAILED marker like the other items. Group, feature and AP / APwrong items are r2_lanes' own.
"""
from __future__ import annotations

from . import common as C, r2 as R, r2_apwrong as RW, r2_lanes as L

PRIV = ('c3_s35r2a36priv2', 's35_r2_aln36_private', 'slurm/aln35_r2a36_private_v2.sbatch')


def private_item():
    if not R.PFE.PLAN.exists():
        return L.item(PRIV, 'plan_missing_until_r2_apwrong_targets')
    plan = C.read(R.PFE.PLAN)
    left = [r for r in plan['rows'] if not (R.PFE.BASE / 'units' / f'{r["id"]}.json').exists()]
    if not left:
        return L.item(PRIV, 'complete', remaining=0)
    if any((R.PFE.BASE / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return L.item(PRIV, 'failed_unit_review', remaining=len(left))
    rec = R.PFE.receipts()
    if not rec['pass']:
        return L.item(PRIV, 'engineering_probe_failed', remaining=len(left)) if rec['other'] else L.item(PRIV, 'ready', 1, len(left), ['--smoke'])
    return L.item(PRIV, 'ready', 1, len(left), ['--smoke-job', rec['pass'][-1].parent.name])


def fleet_status():
    with R.seeded():
        out = L.group_items() + [L.feature_item(), RW.fleet_status(), private_item()]
    return out
