"""DEP12 source fleet: frozen unit plan, GPU smoke, workers, E0 selection, fleet_status (package 02 §4-§5.1, 04 §4).

Units (logical, 04 §6 statuses): E0 = cs_pair / info_nce x full / lora, seed 3401, updates 0 -> 2500 (schedule fixed to
10,000). After E0: E0_SELECTION.json (frozen rule below), then production = cs_pair / info_nce / sigmoid x 3401/3407/3413
(the selected mode's cs_pair@3401 and info_nce@3401 continue the E0 runs 2500 -> 10000) + raw_cs@3401 + cs_pair_wrong@3401
(0 -> 10000). Total 4 x 2,500 + 2 x 7,500 + 9 x 10,000 = 115,000 source updates.
Selection rule (02 §4, frozen in the plan before any E0 result): per mode, mean over {cs_pair, info_nce} of the step-2500
dev-listener-mean envelope r (devprobe.py); higher mode wins, exact tie -> full. A mode with a technical failure is repaired,
never scored.
Workers claim units with fcntl locks; a unit that exits non-zero leaves a FAILED marker (needs review); a signal exit
(preemption / requeue) leaves none, and the next worker resumes from resume.pt. GPU workers need a passing smoke receipt for
the current sources.
CLI (Slurm only): plan | smoke | worker --lane {E0,P} [--max-units N] | select | status
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

import numpy as np

from . import source_common as SC

OUT = SC.SOURCE_OUT
PLAN = OUT / 'plan.json'
SMOKE = OUT / 'smoke'
CLAIMS = OUT / 'claims'
E0_END, TOTAL = 2500, 10000
LANES = {'E0': ('c3_s35dSe0', 's35_dep12_src_e0', 'slurm/aln35_dep12_src_e0.sbatch', 2),
         'P': ('c3_s35dSprd', 's35_dep12_src_prod', 'slurm/aln35_dep12_src_prod.sbatch', 2)}
SELECTION_RULE = ('per mode: mean over objectives {cs_pair, info_nce} of the step-2500 dev-listener-mean 125 ms envelope r '
                  '(PCA16 refit per checkpoint + ridge 0.1, devprobe.py); select the higher mode; exact tie -> full; '
                  'CS values never enter; a technically failed unit blocks selection until repaired')
read, write, sha = SC.read, SC.write, SC.sha


def unit_id(objective, mode, seed, end):
    return f'{SC.run_name(objective, mode, seed)}.to{end}'


def provider_sources():
    here = Path(__file__).parent
    return {f: sha(here / f) for f in ('source_fleet.py', 'trainer.py', 'objectives.py', 'training_objectives_torch.py',
                                         'dependence_measure.py', 'source_sampler.py', 'source_common.py', 'devprobe.py',
                                         'source_tests.py')}


def e0_units():
    return [{'id': unit_id(o, m, 3401, E0_END), 'lane': 'E0', 'objective': o, 'mode': m, 'seed': 3401, 'start': 0, 'end': E0_END}
            for o in ('cs_pair', 'info_nce') for m in ('full', 'lora')]


def production_units(mode):
    us = []
    for o in ('cs_pair', 'info_nce', 'sigmoid'):
        for s in (3401, 3407, 3413):
            start = E0_END if (o in ('cs_pair', 'info_nce') and s == 3401) else 0
            us.append({'id': unit_id(o, mode, s, TOTAL), 'lane': 'P', 'objective': o, 'mode': mode, 'seed': s, 'start': start,
                       'end': TOTAL, 'resumes': unit_id(o, mode, s, E0_END) if start else None, 'role': 'main'})
    for o in ('raw_cs', 'cs_pair_wrong'):
        us.append({'id': unit_id(o, mode, 3401, TOTAL), 'lane': 'P', 'objective': o, 'mode': mode, 'seed': 3401, 'start': 0,
                   'end': TOTAL, 'resumes': None, 'role': 'diagnostic'})
    return us


def make_plan():
    from . import source_sampler as SS
    body = {'version': 'DEP12_SOURCE_PLAN_v1', 'e0_units': e0_units(), 'selection_rule': SELECTION_RULE,
            'production_units_template': production_units('SELECTED'),
            'budget_updates': 4 * E0_END + 2 * (TOTAL - E0_END) + 9 * TOTAL,
            'coverage_sha256': sha(SS.COVERAGE), 'anchors_per_person': SS.anchors_per_person(),
            'streams': {str(s): read(SS.stream_receipt(s))['sha256'] for s in (3401, 3407, 3413)},
            'panels_sha256': read(SS.PANELS_RECEIPT)['sha256'], 'provider_sources': provider_sources(),
            'checkpoints': [0, 500, 2500, 5000, 10000], 'transfer_checkpoint': TOTAL}
    assert body['budget_updates'] == 115000
    if PLAN.exists():
        old = read(PLAN)
        drift = [k for k in body if k != 'provider_sources' and old.get(k) != body[k]]
        assert not drift, f'plan drift {drift}'
        return old
    write(PLAN, {**body, 'created_utc': SC.now()}, freeze=True)
    return read(PLAN)


# ----------------------------------------------------------------------------------------------- unit state
def run_out(u):
    return OUT / 'runs' / SC.run_name(u['objective'], u['mode'], u['seed'])


def done(u):
    r = run_out(u) / 'receipt.json'
    return r.exists() and str(u['end']) in read(r).get('checkpoints', {})


def failed(u):
    return (run_out(u) / f"FAILED_to{u['end']}.json").exists()


def selection():
    return read(SC.E0_SELECTION) if SC.E0_SELECTION.exists() else None


def units(lane):
    if lane == 'E0':
        return e0_units()
    sel = selection()
    return production_units(sel['selected_mode']) if sel else []


def smoke_pass():
    """Latest passing smoke receipt whose provider sources equal the current files."""
    cur = provider_sources()
    for p in sorted(SMOKE.glob('*/receipt.json'), key=lambda p: p.stat().st_mtime, reverse=True):
        r = read(p)
        if r.get('status') == 'pass' and r.get('provider_sources') == cur:
            return p, r
    return None, None


def ready_units(lane):
    us = units(lane)
    out = []
    for u in us:
        if done(u) or failed(u):
            continue
        if u.get('resumes'):
            e0 = dict(u, end=E0_END)
            if not done(e0):
                continue
        out.append(u)
    return out


def fleet_status(lane='E0'):
    name, lane_name, sbatch, slots = LANES[lane]
    st = {'name': name, 'lane': lane_name, 'state': 'plan_missing', 'ready': 0, 'remaining': 4 if lane == 'E0' else 11,
          'slots': slots, 'initial': [], 'submit': []}
    if not PLAN.exists():
        return st
    p, _ = smoke_pass()
    if p is None:
        cur = [(read(q), time.time() - q.stat().st_mtime) for q in SMOKE.glob('*/receipt.json')]
        cur = [(r, age) for r, age in cur if r.get('provider_sources') == provider_sources()]
        if any(r.get('status') == 'failed' for r, _ in cur):
            return {**st, 'state': 'engineering_probe_failed'}
        # a 'running' receipt untouched for 3 h is a preempted smoke (receipts are rewritten after every check)
        if lane == 'E0' and not any(r.get('status') == 'running' and age < 3 * 3600 for r, age in cur):
            return {**st, 'state': 'ready', 'ready': 1, 'slots': 1, 'submit': [sbatch, 'smoke']}
        return {**st, 'state': 'waiting_smoke'}
    us = units(lane)
    if lane == 'P' and not us:
        e0_done = all(done(u) for u in e0_units())
        return {**st, 'state': 'waiting_e0_selection' if not e0_done else 'selection_pending',
                'ready': 0, 'remaining': 11}
    remaining = [u for u in us if not done(u)]
    st['remaining'] = len(remaining)
    if not remaining:
        if lane == 'E0' and selection() is None:
            return {**st, 'state': 'selection_pending', 'ready': 1, 'remaining': 1, 'slots': 1,
                    'submit': [sbatch, 'worker', '--lane', 'E0', '--max-units', '1']}
        return {**st, 'state': 'complete'}
    if any(failed(u) for u in remaining):
        return {**st, 'state': 'failed_unit_review'}
    ready = ready_units(lane)
    return {**st, 'state': 'ready' if ready else 'waiting_dependencies', 'ready': len(ready),
            'submit': [sbatch, 'worker', '--lane', lane, '--max-units', '1']}


# ----------------------------------------------------------------------------------------------- selection
def select():
    """Frozen E0 rule -> results/auditory_alignment_v3/dep12/E0_SELECTION.json (0444)."""
    if SC.E0_SELECTION.exists():
        return read(SC.E0_SELECTION)
    plan = read(PLAN); us = e0_units()
    for u in us:
        assert done(u) and not failed(u), f"E0 unit {u['id']} not complete"
    traj, scores = {}, {}
    for u in us:
        rd = run_out(u); rec = read(rd / 'receipt.json')
        dp = {s: read(rd / f'devprobe_step{s}.json') for s in (0, 500, 2500)}
        assert all(d['finite'] for d in dp.values()), f"non-finite dev probe in {u['id']}: technical failure, repair first"
        diags = read(rd / 'diagnostics.json')['diags']
        key = f"{u['objective']}.{u['mode']}"
        scores[key] = dp[2500]['dev_listener_mean_r']
        traj[key] = {'devprobe': {str(s): {'dev_listener_mean_r': d['dev_listener_mean_r'], 'per_dev_listener_r': d['per_dev_listener_r'],
                                           'fit_mse': d['fit_mse'], 'explained_fraction_top16': d['explained_fraction_top16']}
                                  for s, d in dp.items()},
                     'diagnostics': diags, 'checkpoints': rec['checkpoints'], 'units': rec['units'],
                     'loss_log_every_25': [{k: x[k] for k in ('update', 'loss', 'grad_norm_backbone', 'grad_norm_heads', 'lr')}
                                           for x in read_state_logs(u)]}
    mode_score = {m: float(np.mean([scores[f'cs_pair.{m}'], scores[f'info_nce.{m}']])) for m in ('full', 'lora')}
    chosen = 'full' if mode_score['full'] >= mode_score['lora'] else 'lora'
    body = {'version': 'DEP12_E0_SELECTION_v1', 'created_utc': SC.now(), 'rule': SELECTION_RULE, 'selected_mode': chosen,
            'mode_scores': mode_score, 'per_objective_mode_step2500_dev_mean_r': scores, 'tie': mode_score['full'] == mode_score['lora'],
            'plan_sha256': sha(PLAN), 'trajectories': traj,
            'scope': ('chooses the common training recipe of this round only; not evidence that one update mode is generally '
                      'stronger; the unselected mode keeps its two 2,500-update pilots'),
            'production_units': production_units(chosen)}
    write(SC.E0_SELECTION, body, freeze=True)
    return read(SC.E0_SELECTION)


def read_state_logs(u):
    import torch
    rd = SC.SOURCE_STORE / 'runs' / SC.run_name(u['objective'], u['mode'], u['seed'])
    st = torch.load(rd / f"step{u['end']}.state.pt", map_location='cpu', weights_only=False)
    return st['logs']


# ----------------------------------------------------------------------------------------------- smoke (GPU, manual)
def smoke():
    import torch
    from . import source_sampler as SS, source_tests as TS, trainer as TR
    job = os.environ['SLURM_JOB_ID']; d = SMOKE / job; d.mkdir(parents=True, exist_ok=True, mode=0o700)
    rec = {'status': 'running', 'job': job, 'provider_sources': provider_sources(), 'device': torch.cuda.get_device_name(0),
           'started_utc': SC.now(), 'checks': {}, 'timing': {}}
    probe = SC.SOURCE_STORE / 'smoke' / job
    try:
        make_plan()
        rec['checks']['reference'] = TS.reference(); assert rec['checks']['reference']['equal']
        pool = SS.Pool(); n = SS.anchors_per_person()
        rec['checks']['access'] = TS.access(pool)
        stream = SS.load_stream(3401); P, _ = SS.load_panels()
        data = SS.SourceData(pool, np.r_[stream['rows'][:4].reshape(-1), P['fit_rows'], P['dev_rows']], torch.device('cuda'))
        model, groups, info = TR.build_model('full', 3401, 'cuda')
        sig, _ = TR.calibrate_sigmas(3401, model, TR.Panels(pool, data))
        rec['sigmas_s3401'] = {v: {k: sig['views'][v][k] for k in ('sigma_u', 'sigma_y')} for v in TR.VIEWS}
        rec['checks']['objectives'] = TS.objectives(model, data, sig, stream, n)
        del model
        rec['checks']['params'] = TS.params(3401, data, stream, sig, n)
        rec['checks']['montage'] = TS.montage()
        del data; torch.cuda.empty_cache()
        write(d / 'receipt.json', rec)
        rec['checks']['resume'] = TS.resume(probe)
        r = rec['checks']['resume']['cs_pair.lora.s3401']
        rec['checks']['resume_equal'] = r['max_abs_diff_model'] == 0.0 and r['max_abs_diff_adam_moments'] == 0.0
        assert r['max_abs_diff_model'] < 1e-5, r
        write(d / 'receipt.json', rec)
        for o, m, k in (('cs_pair', 'full', 60), ('cs_pair', 'lora', 60), ('info_nce', 'full', 60), ('info_nce', 'lora', 60),
                        ('sigmoid', 'full', 20), ('raw_cs', 'full', 20), ('cs_pair_wrong', 'full', 20)):
            t = time.time()
            r = TR.train(o, m, 3401, k, probe_dir=probe / 'timing', log=lambda *a, **kw: None)
            un = r['units'][-1]
            rec['timing'][f'{o}.{m}'] = {'updates': k, 'seconds_per_update': un['seconds_per_update'], 'gpu_peak_mb': un['gpu_peak_mb'],
                                         'wall_seconds_incl_setup': time.time() - t, 'final_loss': None}
            write(d / 'receipt.json', rec)
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc())
        raise
    finally:
        rec['finished_utc'] = SC.now()
        write(d / 'receipt.json', rec)


# ----------------------------------------------------------------------------------------------- worker
_stop = {'signal': None}


def _on_term(signum, frame):
    _stop['signal'] = signum


def claim_and_run(u):
    CLAIMS.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = CLAIMS / f"{SC.run_name(u['objective'], u['mode'], u['seed'])}.lock"   # one process per run directory
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 'busy'
        if done(u) or failed(u):
            return 'skip'
        cmd = [sys.executable, '-B', '-u', '-m', 'auditory_alignment_v3.dep12.trainer', 'run', '--objective', u['objective'],
               '--mode', u['mode'], '--seed', str(u['seed']), '--end', str(u['end'])]
        rc = subprocess.run(cmd).returncode
        if rc == 0 and done(u):
            return 'complete'
        if rc < 0 or _stop['signal'] is not None:          # killed by a signal: preemption / requeue, not a failure
            return 'interrupted'
        write(run_out(u) / f"FAILED_to{u['end']}.json", {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc, 'unit': u,
                                                          'utc': SC.now(), 'note': 'non-zero exit; review before release'})
        return 'failed'


def worker(lane, max_units):
    signal.signal(signal.SIGTERM, _on_term)
    p, _ = smoke_pass(); assert p is not None, 'no passing smoke receipt for the current sources'
    make_plan()
    if lane == 'E0' and all(done(u) for u in e0_units()) and selection() is None:
        _select_locked(); return
    count = 0
    for u in ready_units(lane):
        res = claim_and_run(u)
        print(u['id'], res, flush=True)
        if res == 'failed':
            raise RuntimeError(f"unit {u['id']} failed")
        if res == 'interrupted':
            return
        if res == 'complete':
            count += 1
        if count >= max_units:
            break
    if lane == 'E0' and all(done(u) for u in e0_units()) and selection() is None:
        _select_locked()


def _select_locked():
    CLAIMS.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (CLAIMS / 'select.lock').open('a+') as h:
        fcntl.flock(h, fcntl.LOCK_EX)
        s = select()
        print('E0 selection', s['selected_mode'], json.dumps(s['mode_scores']), flush=True)


def status():
    out = {'plan': PLAN.exists(), 'smoke': str(smoke_pass()[0]), 'selection': (selection() or {}).get('selected_mode')}
    for lane in LANES:
        out[lane] = fleet_status(lane)
        out[lane + '_units'] = {u['id']: ('complete' if done(u) else 'FAILED' if failed(u) else 'planned') for u in units(lane)}
    print(json.dumps(out, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['plan', 'smoke', 'worker', 'select', 'status'])
    ap.add_argument('--lane', choices=list(LANES), default='E0'); ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm only'
    os.umask(0o077)
    if a.cmd == 'plan':
        print(json.dumps({k: v for k, v in make_plan().items() if k != 'production_units_template'}, default=str)[:1500])
    elif a.cmd == 'smoke':
        smoke()
    elif a.cmd == 'worker':
        worker(a.lane, a.max_units)
    elif a.cmd == 'select':
        print(json.dumps({k: v for k, v in select().items() if k != 'trajectories'}, indent=1, default=str))
    else:
        status()


if __name__ == '__main__':
    main()
