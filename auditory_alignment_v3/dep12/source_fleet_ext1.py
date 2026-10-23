"""DEP12 source fleet, extension 1: raw_cs@3407, raw_cs@3413, cs_pair_wrong@3407, cs_pair_wrong@3413.

Coordinator decision DECISIONS.md 2026-10-23 07:30 (beyond the package budget: +40,000 updates; decided before any raw_cs /
WRONG measurement was looked at). Only the plan differs from production: the units run the unchanged trainer_v2 (same
model, LoRA mode from E0_SELECTION.json, objectives, optimiser, 10,000-update schedule, checkpoints 0/500/2500/5000/10000 and
resume state), on the frozen seed streams and the frozen seed sigmas (sigmas_s3407 / sigmas_s3413, written by the first
production units of those seeds). Execution (claim locks, FAILED markers, preemption handling) is source_fleet_v2's.
GPU units require the passing source_fleet_v2 smoke receipt for the current, unchanged training sources (no new smoke:
the executed code path is byte-identical; this module adds only the unit list and the lane identity).
CLI (Slurm only): plan | worker [--max-units N] | status
"""
from __future__ import annotations

import argparse
import json
import os
import signal

from . import source_common as SC, source_fleet_v2 as F2

PLAN = SC.SOURCE_OUT / 'plan_ext1.json'
NAME, LANE, SBATCH, SLOTS = 'c3_s35dSx1', 's35_dep12_src_ext1', 'slurm/aln35_dep12_src_ext1.sbatch', 2
EXT = (('raw_cs', 3407), ('raw_cs', 3413), ('cs_pair_wrong', 3407), ('cs_pair_wrong', 3413))
read, write, sha = SC.read, SC.write, SC.sha


def units():
    sel = F2.selection()
    assert sel is not None, 'E0 selection missing'
    m = sel['selected_mode']
    return [{'id': F2.unit_id(o, m, s, F2.TOTAL), 'lane': 'X1', 'objective': o, 'mode': m, 'seed': s, 'start': 0,
             'end': F2.TOTAL, 'resumes': None, 'role': 'mechanism_control_extension1'} for o, s in EXT]


def make_plan():
    from . import source_sampler as SS, trainer_v2 as TR
    us = units()
    body = {'version': 'DEP12_SOURCE_PLAN_EXT1_v1', 'units': us, 'budget_updates': len(us) * F2.TOTAL,
            'decision': 'DECISIONS.md 2026-10-23 07:30 (coordinator; extension beyond the package budget)',
            'base_plan_sha256': sha(F2.PLAN), 'e0_selection_sha256': sha(SC.E0_SELECTION), 'selected_mode': us[0]['mode'],
            'streams': {str(s): read(SS.stream_receipt(s))['sha256'] for s in (3407, 3413)},
            'sigma_receipts': {str(s): sha(TR.sigma_path(s)) for s in (3407, 3413)},
            'panels_sha256': read(SS.PANELS_RECEIPT)['sha256'], 'coverage_sha256': sha(SS.COVERAGE),
            'training_sources': TR.source_files(), 'provider_sources_v2': F2.provider_sources(),
            'lane_module_sha256': sha(__file__), 'checkpoints': [0, 500, 2500, 5000, 10000], 'transfer_checkpoint': F2.TOTAL}
    assert body['budget_updates'] == 40000 and all(u['mode'] == body['selected_mode'] for u in us)
    for s in (3407, 3413):
        assert TR.sigma_path(s).exists(), f'frozen sigma for seed {s} missing'
    if PLAN.exists():
        old = read(PLAN)
        drift = [k for k in body if k not in ('lane_module_sha256',) and old.get(k) != body[k]]
        assert not drift, f'ext1 plan drift {drift}'
        return old
    write(PLAN, {**body, 'created_utc': SC.now()}, freeze=True)
    return read(PLAN)


def plan_ok():
    """Frozen plan exists and the executed training sources still equal the ones it bound."""
    from . import trainer_v2 as TR
    return PLAN.exists() and read(PLAN)['training_sources'] == TR.source_files()


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': len(EXT), 'slots': SLOTS,
          'initial': [], 'submit': []}
    if not PLAN.exists():
        return st
    if not plan_ok():
        return {**st, 'state': 'source_drift_review'}
    p, _ = F2.smoke_pass()
    if p is None:
        return {**st, 'state': 'waiting_smoke'}
    us = units()
    remaining = [u for u in us if not F2.done(u)]
    st['remaining'] = len(remaining)
    if not remaining:
        return {**st, 'state': 'complete'}
    if any(F2.failed(u) for u in remaining):
        return {**st, 'state': 'failed_unit_review'}
    ready = [u for u in remaining]
    return {**st, 'state': 'ready', 'ready': len(ready), 'submit': [SBATCH, 'worker', '--max-units', '1']}


def worker(max_units):
    signal.signal(signal.SIGTERM, F2._on_term)
    p, _ = F2.smoke_pass(); assert p is not None, 'no passing source_fleet_v2 smoke receipt for the current sources'
    assert plan_ok(), 'ext1 plan missing or training sources drifted'
    count = 0
    for u in units():
        if F2.done(u) or F2.failed(u):
            continue
        res = F2.claim_and_run(u)
        print(u['id'], res, flush=True)
        if res == 'failed':
            raise RuntimeError(f"unit {u['id']} failed")
        if res == 'interrupted':
            return
        if res == 'complete':
            count += 1
        if count >= max_units:
            break


def status():
    out = {'plan': PLAN.exists(), 'plan_ok': plan_ok() if PLAN.exists() else None, 'smoke': str(F2.smoke_pass()[0]),
           'lane': fleet_status(), 'units': {u['id']: ('complete' if F2.done(u) else 'FAILED' if F2.failed(u) else 'planned')
                                              for u in units()}}
    print(json.dumps(out, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['plan', 'worker', 'status'])
    ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm only'
    os.umask(0o077)
    if a.cmd == 'plan':
        print(json.dumps({k: v for k, v in make_plan().items() if k not in ('training_sources', 'provider_sources_v2')}, default=str))
    elif a.cmd == 'worker':
        worker(a.max_units)
    else:
        status()


if __name__ == '__main__':
    main()
