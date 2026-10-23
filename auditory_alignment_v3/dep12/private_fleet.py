"""DEP12 Agent P GPU lane: private feature export units (one per encoder), fleet-ready (paper/encoders.py convention).

Unit = one encoder x all 5 outer folds (private_features.export). Specs are frozen one file per unit (0444) under
REC/features_v1/specs before the unit runs; the unit id hashes the encoder name, the frozen binding sha256 and the export
version. Readiness = dep12.encoders REGISTRY state 'available' after refresh(). Order: B0, REVE0, MINDMIX_branch, the twelve
ALN4.1 arms (seed 3401 first), then the eleven new-round production arms as they become available.

Smoke (GPU, engineering only, no outcome threshold): resampler checks; probe export (6 children, fold 0) for one encoder of
each family (aln41_TCS@3401, REVE0, MINDMIX_branch): strict loads, finite U, pad check, timing and peak memory; then the
complete B0 unit through the ordinary claim / run_unit path (full-scale memory and per-fold time on all 64 children).
A failed unit writes units/<id>.FAILED.json; a preempted / signalled subprocess (negative return code) does not.

Post-processing (CPU work inside the lane's jobs, never blocking GPU units): after its units, every worker runs `post`:
private_use for each complete unit without U0/δ outputs, selection for each (candidate set, seed) whose four candidates have
U0 outputs, then private_analysis whenever its inputs changed. Each stage is a subprocess; a failure writes
post_failed/<stage>.json and does not mark the GPU unit failed.

Commands (Slurm only): --register | --smoke | --worker [--max-units N] | --unit ID | --post | --status
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from . import private_features as PF

BASE = PF.REC / 'features_v1'
STORE = PF.STORE / 'features_v1'
EXPORT_VERSION = 'DEP12_PRIVATE_EXPORT_v1'
NAME, LANE, SBATCH = 'c3_s35dPfeat', 's35_dep12_private_features', 'slurm/aln35_dep12_priv_feat.sbatch'
SLOTS, PER_JOB = 2, 4
REUSED = (['B0', 'REVE0', 'MINDMIX_branch']
          + [f'aln41_{a}@{s}' for s in (3401, 3407, 3413) for a in ('TCS', 'TNCE', 'GCS', 'WRONG')])
NEW = ([f'{o}@{s}' for s in (3401, 3407, 3413) for o in ('cs_pair', 'info_nce', 'sigmoid')]
       + ['raw_cs@3401', 'cs_pair_wrong@3401'])
SMOKE_ENCODERS = ('aln41_TCS@3401', 'REVE0', 'MINDMIX_branch')
read, write, sha, digest = PF.read, PF.write, PF.sha, PF.digest


def sources():
    files = [Path(__file__), Path(PF.__file__)]
    return {str(p.relative_to(PF.ROOT)): sha(p) for p in files}


POST_SEEDS = (3401, 3407, 3413)


def post_candidates(seed, cset):
    if cset == 'primary':
        return ['B0', f'cs_pair@{seed}', f'info_nce@{seed}', f'sigmoid@{seed}']
    return ['B0', f'aln41_TCS@{seed}', f'aln41_TNCE@{seed}', f'aln41_GCS@{seed}']


def use_done(name):
    return (PF.REC / 'use_v1' / name.replace('@', '_at_') / 'complete.json').exists()


def sel_done(cset, seed):
    return (PF.REC / 'selection_v1' / f'{cset}_s{seed}' / 'complete.json').exists()


def post_failed():
    return sorted(p.name for p in (BASE / 'post_failed').glob('*.json')) if (BASE / 'post_failed').exists() else []


def analysis_inputs():
    files = sorted((PF.REC / 'use_v1').glob('*/complete.json')) + sorted((PF.REC / 'selection_v1').glob('*/complete.json'))
    return digest([[str(p.relative_to(PF.REC)), sha(p)] for p in files]) if files else None


def post_pending():
    done = {s['encoder'] for s in specs() if unit_state(s) == 'complete'}
    failed = set(post_failed())
    todo = [('use', n) for n in [s['encoder'] for s in specs()] if n in done and not use_done(n) and f'use_{n}.json' not in failed]
    for cset in ('primary', 'aln41'):
        for seed in POST_SEEDS:
            if all(use_done(n) for n in post_candidates(seed, cset)) and not sel_done(cset, seed) \
                    and f'selection_{cset}_{seed}.json' not in failed:
                todo.append(('selection', cset, seed))
    last = BASE / 'analysis_inputs.json'
    cur = analysis_inputs()
    if cur and (not last.exists() or read(last).get('digest') != cur) and 'analysis.json' not in failed:
        todo.append(('analysis',))
    return todo


def post():
    """Run every pending CPU stage once (subprocesses; failures recorded, not raised)."""
    for _ in range(3):
        todo = post_pending()
        if not todo:
            return
        for item in todo:
            if item[0] == 'use':
                cmd, tag = ['auditory_alignment_v3.dep12.private_use', '--encoders', item[1]], f'use_{item[1]}'
            elif item[0] == 'selection':
                cmd, tag = ['auditory_alignment_v3.dep12.selection', '--set', item[1], '--seeds', str(item[2])], f'selection_{item[1]}_{item[2]}'
            else:
                if any(t[0] != 'analysis' for t in post_pending()):
                    continue
                cur = analysis_inputs()
                cmd, tag = ['auditory_alignment_v3.dep12.private_analysis'], 'analysis'
            t0 = time.time()
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', *cmd]).returncode
            if rc < 0:
                raise SystemExit(rc)
            if rc:
                write(BASE / 'post_failed' / f'{tag}.json', {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc, 'cmd': cmd,
                                                             'time': datetime.now().astimezone().isoformat()})
            elif item[0] == 'analysis':
                write(BASE / 'analysis_inputs.json', {'digest': cur, 'job': os.environ.get('SLURM_JOB_ID'), 'seconds': time.time() - t0})
            print('post', tag, 'rc', rc, round(time.time() - t0, 1), flush=True)


def unit_id(name, binding_sha):
    return 'DEP12P_' + digest({'encoder': name, 'binding_sha256': binding_sha, 'version': EXPORT_VERSION}, 16)


def specs():
    out = []
    for p in sorted((BASE / 'specs').glob('*.json')):
        out.append(read(p))
    return sorted(out, key=lambda s: s['order'])


def register(names):
    """Freeze one spec per encoder (append-only; existing specs are never rewritten)."""
    bind_sha = PF.sha(PF.BINDING)
    existing = {s['encoder'] for s in specs()}
    order0 = len(existing)
    for j, name in enumerate(n for n in names if n not in existing):
        uid = unit_id(name, bind_sha)
        body = {'id': uid, 'encoder': name, 'binding_sha256': bind_sha, 'version': EXPORT_VERSION, 'order': order0 + j,
                'family': 'new_round' if name in NEW else 'reused', 'created': datetime.now().astimezone().isoformat(),
                'sources_at_registration': sources(), 'store': str(STORE / 'units' / uid), 'results_seen': False}
        PF.write_frozen(BASE / 'specs' / f'{uid}.json', body)
        print('registered', name, uid, flush=True)


def encoder_state(name):
    from . import encoders as E
    spec = E.REGISTRY.get(name) or E.refresh().get(name)
    if spec is None:
        return 'unknown'
    if not spec.get('servable'):
        return 'not_servable'
    return spec.get('state')


def unit_state(spec, refreshed=None):
    rec = BASE / 'units' / f'{spec["id"]}.json'
    if rec.exists():
        return 'complete'
    if (BASE / 'units' / f'{spec["id"]}.FAILED.json').exists():
        return 'failed'
    st = (refreshed or {}).get(spec['encoder'])
    if st is None:
        st = encoder_state(spec['encoder'])
    return 'ready' if st == 'available' else 'waiting_encoder:' + str(st)


def smoke_receipts():
    out = {'pass': [], 'other': []}
    for p in sorted((BASE / 'smoke').glob('*/receipt.json')):
        r = read(p)
        if r.get('sources') == sources() and r.get('binding_sha256') == PF.sha(PF.BINDING):
            out['pass' if r.get('status') == 'pass' else 'other'].append(p)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 0, 'slots': 1, 'initial': [], 'submit': []}
    if not PF.BINDING.exists() or not (BASE / 'specs').exists():
        return st
    sp = specs()
    if not sp:
        return st
    from . import encoders as E
    E.refresh()
    refreshed = {s['encoder']: encoder_state(s['encoder']) for s in sp}
    states = [unit_state(s, refreshed) for s in sp]
    left = [x for x in states if x != 'complete']
    st['remaining'] = len(left)
    if not left:
        if post_failed():
            return {**st, 'state': 'failed_unit_review'}
        if post_pending():
            if not smoke_receipts()['pass']:
                return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
            return {**st, 'state': 'ready', 'ready': 1, 'remaining': 1, 'slots': 1, 'submit': [SBATCH, '--post']}
        return {**st, 'state': 'complete'}
    if 'failed' in left:
        return {**st, 'state': 'failed_unit_review'}
    rec = smoke_receipts()
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    ready = sum(x == 'ready' for x in left)
    if ready:
        return {**st, 'state': 'ready', 'ready': ready, 'slots': min(SLOTS, ready),
                'submit': [SBATCH, '--worker', '--max-units', str(PER_JOB)]}
    if post_failed():
        return {**st, 'state': 'failed_unit_review'}
    if post_pending():
        return {**st, 'state': 'ready', 'ready': 1, 'slots': 1, 'submit': [SBATCH, '--post']}
    return {**st, 'state': 'waiting_for_encoders'}


# ----------------------------------------------------------------------------------------------- execution
def sub(*args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *map(str, args)]).returncode


def run_unit(uid):
    spec = read(BASE / 'specs' / f'{uid}.json')
    assert spec['binding_sha256'] == PF.sha(PF.BINDING), 'binding drift'
    dest = Path(spec['store'])
    t0 = time.time()
    meta = PF.export(spec['encoder'], dest)
    arrays = {str(f): meta['folds'][str(f)]['array_sha256'] for f in PF.FOLDS}
    write(BASE / 'units' / f'{uid}.json', {'status': 'complete', 'spec': spec, 'spec_sha256': sha(BASE / 'specs' / f'{uid}.json'),
                                            'meta_sha256': sha(dest / 'meta.json'), 'arrays_sha256': arrays,
                                            'encoder_checkpoint_sha256': meta['encoder_meta'].get('checkpoint_sha256'),
                                            'encoder_meta': meta['encoder_meta'], 'U_dim': meta['folds']['0']['U_dim'],
                                            'gpu_peak_mb': meta['gpu_peak_mb'], 'seconds': time.time() - t0, 'device': meta['device'],
                                            'job': os.environ.get('SLURM_JOB_ID'), 'sources': sources(),
                                            'time': datetime.now().astimezone().isoformat()})
    print('unit complete', spec['encoder'], uid, round(time.time() - t0, 1), flush=True)


def claim(uid, fn):
    path = BASE / 'units' / f'{uid}.json'
    lock = BASE / 'claims' / f'{uid}.lock'
    lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists() or (BASE / 'units' / f'{uid}.FAILED.json').exists():
            return False
        rc = fn()
        if rc < 0:                      # preempted / signalled: no FAILED marker; the unit restarts from scratch later
            raise SystemExit(rc)
        if rc or not path.exists():
            write(BASE / 'units' / f'{uid}.FAILED.json', {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc,
                                                          'time': datetime.now().astimezone().isoformat()})
            raise RuntimeError(f'DEP12 private feature unit failed: {uid}')
        return True


def worker(max_units):
    assert smoke_receipts()['pass'], 'no passing smoke for the current sources / binding'
    from . import encoders as E
    E.refresh()
    count = 0
    for spec in specs():
        if count >= max_units:
            break
        if unit_state(spec) != 'ready':
            continue
        if claim(spec['id'], lambda: sub('--unit', spec['id'])):
            count += 1
    post()


def smoke():
    import torch
    job = os.environ['SLURM_JOB_ID']
    out = BASE / 'smoke' / job
    receipt = {'status': 'running', 'sources': sources(), 'binding_sha256': PF.sha(PF.BINDING), 'job': job, 'encoders': []}
    try:
        from ..aln41 import timebank as TB
        rs = TB.check_resampler(fs_list=(250,))
        receipt['resampler_check'] = rs
        import numpy as np
        x = torch.randn(3, 20, 200, dtype=torch.float64)
        from scipy.signal import resample as sres
        receipt['resample_160_max_abs_error'] = float(np.max(np.abs(sres(x.numpy(), 160, axis=-1) - PF.resample_real(x).numpy())))
        assert receipt['resample_160_max_abs_error'] < 1e-9
        for name in SMOKE_ENCODERS:
            t0 = time.time()
            meta = PF.export(name, PF.STORE / 'smoke' / job / name, probe=True, folds=(0,))
            f0 = meta['folds']['0']
            receipt['encoders'].append({'encoder': name, 'seconds': time.time() - t0, 'fold_seconds': f0['seconds'],
                                        'n_trials': meta['n_trials'], 'U_dim': f0['U_dim'], 'gpu_peak_mb': meta['gpu_peak_mb'],
                                        'last_call': meta['last_call'], 'U_norm_range': f0['U_norm_range'],
                                        'device': meta['device'], 'checkpoint_sha256': meta['encoder_meta'].get('checkpoint_sha256')})
        b0 = next(s_ for s_ in specs() if s_['encoder'] == 'B0')
        if unit_state(b0) == 'ready':
            claim(b0['id'], lambda: sub('--unit', b0['id']))      # False when another process holds the claim
        per = {e['encoder']: e['fold_seconds'] / e['n_trials'] for e in receipt['encoders']}
        receipt['projection'] = {'seconds_per_trial_fold_probe': per,
                                 'unit_hours_estimate_from_probe': {k: v * 56426 * 5 / 3600 + 0.05 for k, v in per.items()}}
        if (BASE / 'units' / f'{b0["id"]}.json').exists():
            rec = read(BASE / 'units' / f'{b0["id"]}.json')
            receipt['full_unit_B0'] = {'id': b0['id'], 'seconds': rec['seconds'], 'gpu_peak_mb': rec['gpu_peak_mb'], 'device': rec['device']}
        else:
            receipt['full_unit_B0'] = {'id': b0['id'], 'status': 'claimed_by_another_process; probe exports carry the smoke'}
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc())
        raise
    finally:
        write(out / 'receipt.json', receipt)


def status():
    sp = specs()
    print(json.dumps({'fleet': fleet_status(), 'units': [(s['encoder'], unit_state(s)) for s in sp]}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--register', action='store_true')
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--worker', action='store_true')
    ap.add_argument('--max-units', type=int, default=PER_JOB)
    ap.add_argument('--unit')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--post', action='store_true')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    if a.register:
        register(REUSED + NEW)
    elif a.smoke:
        smoke()
    elif a.unit:
        run_unit(a.unit)
    elif a.worker:
        worker(a.max_units)
    elif a.post:
        assert smoke_receipts()['pass'], 'no passing smoke for the current sources / binding'
        post()
    elif a.status:
        status()


if __name__ == '__main__':
    main()
