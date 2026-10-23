"""Paper line (manuscript v2, 2026-10-22): new common-backbone Stage2 arms on the unchanged ALN4.1 machinery.

Arms
- THSIC  : temporal HSIC with temporal-mass correction (manuscript Table 6 / Appendix A.2, B.2; paper/temporal_hsic_torch.py).
           New criterion -> the source-only calibration allowance of every ALN4.1 objective: LR 1e-4 vs 3e-4 over 1,000
           updates at seed 3401, selected by the common dev ridge probe (aln41/source.py select rule, exact tie -> 1e-4),
           plus one fixed scalar objective scale (first-order match to TCS at the seed-3401 initial state, below).
- SV_env / SV_ss / SV_sc : TCS restricted to one acoustic view (work item W4, approved 2026-10-22); TCS's R1 LR inherited.
Seeds 3401 / 3407 / 3413 reuse that seed's ALN4.1 episode stream, panels and sigma receipt (byte copies, hash-checked; the
initial state is the same seeded TimeBankModel), 10,000 updates, snapshots 0/2500/5000/10000, the final one transferred.
Downstream = aln41/frozen.py (DTU/FAU content folds + private children) and aln41/readout.py, re-pointed per arm x seed,
like aln41/r2.py does for its seeds. Nothing in aln41 is edited; module attributes are re-pointed inside one process.

CLI (`python -m auditory_alignment_v3.paper.arms ...`, Slurm only):
  plan | smoke | worker [--max-units N] | unit --arm A --seed S --id ID [--probe] | frozen-worker [--max-units N] |
  frozen-unit --arm A --seed S --id ID | readout [--arm A] (CPU) | status
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

import numpy as np

from .. import core
from ..aln41 import frozen as FZ, r2 as R2, readout as RO, source as SRC, temporal_objectives_torch as TO
from . import temporal_hsic_torch as TH

SEEDS = (3401, 3407, 3413)
SPEC = {'THSIC': {'kind': 'THSIC', 'views': ('env', 'ss', 'sc'), 'calibrate': True},
        'SV_env': {'kind': 'TCS', 'views': ('env',), 'calibrate': False},
        'SV_ss': {'kind': 'TCS', 'views': ('ss',), 'calibrate': False},
        'SV_sc': {'kind': 'TCS', 'views': ('sc',), 'calibrate': False}}
ARMS = tuple(SPEC)
OUT = Path(core.OUT) / 'paper' / 'arms_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/arms_v1')
SCALE = OUT / 'THSIC' / 'objective_scale.json'
SCALE_UPDATES = 16
LANES = {'A': ('c3_s35pasrcA', 's35_paper_arms_src_a', 'slurm/aln35_paper_arms_src_a.sbatch'),
         'B': ('c3_s35pasrcB', 's35_paper_arms_src_b', 'slurm/aln35_paper_arms_src_b.sbatch'),
         'Z': ('c3_s35pafrz', 's35_paper_arms_frozen', 'slurm/aln35_paper_arms_frozen.sbatch')}
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest
_ORIGINAL_VIEW_BATCHES = SRC.view_batches


def paper_sources():
    here = Path(__file__).parent
    return {str(p.relative_to(core.REPO)): sha(p) for p in (here / 'arms.py', here / 'temporal_hsic_torch.py')}


def seed_source(seed):
    """(base, store, plan, selection) of the ALN4.1 source run of this seed (R1 for 3401, R2 otherwise)."""
    base = SRC.OUT / 'source_v1' if seed == 3401 else R2.ROOT / f'seed{seed}' / 'source_v1'
    plan = read(base / 'plan.json')
    return base, Path(plan['store']), plan, read(base / 'selection.json')


def tcs_lr():
    return read(SRC.OUT / 'source_v1' / 'selection.json')['choice']['TCS']['lr']


def scale_value():
    return read(SCALE)['scale'] if SCALE.exists() else None


@contextlib.contextmanager
def ctx(arm, seed):
    """Re-point aln41 source / frozen / readout to one paper arm x seed; restores everything on exit."""
    assert arm in SPEC and seed in SEEDS
    saved = [(m, k, getattr(m, k)) for m, keys in ((SRC, ('SEED', 'STREAM_SEED', 'BASE', 'STORE', 'view_batches')),
                                                     (FZ, ('BASE', 'STORE', 'ARMS')), (RO, ('BASE',)), (TO, ('episode_loss_fo',)))
             for k in keys]
    spec = SPEC[arm]; root, sroot = OUT / arm / f'seed{seed}', STORE / arm / f'seed{seed}'
    try:
        SRC.SEED, SRC.STREAM_SEED = seed, seed + 41000
        SRC.BASE, SRC.STORE = root / 'source_v1', sroot / 'source_v1'
        FZ.BASE, FZ.STORE, FZ.ARMS = root / 'frozen_v1', sroot / 'frozen_v1', (arm,)
        RO.BASE = root / 'readout_v1'
        if spec['views'] != ('env', 'ss', 'sc'):
            keep = spec['views']
            SRC.view_batches = lambda U, A, sig, wrong=None: [b for b in _ORIGINAL_VIEW_BATCHES(U, A, sig, wrong) if b.name in keep]
        TO.episode_loss_fo = TH.make_episode_loss({arm: spec['kind']}, scale_value() if spec['kind'] == 'THSIC' else None)
        yield
    finally:
        for m, k, v in saved:
            setattr(m, k, v)


# ----------------------------------------------------------------------------------------------- plans (CPU)
def production_row(arm, seed, lr):
    body = {'stage': 'production', 'arm': arm, 'lr': lr, 'updates': SRC.PROD_STEPS, 'seed': seed}
    return {**body, 'id': 'PAPA_P_' + digest(body, 16)}


def selected_lr(arm):
    """None while a calibrated arm has no seed-3401 selection yet."""
    if not SPEC[arm]['calibrate']:
        return tcs_lr()
    path = OUT / arm / 'seed3401' / 'source_v1' / 'selection.json'
    return read(path)['choice'][arm]['lr'] if path.exists() else None


def make_plan(arm, seed):
    base0, store0, plan0, _ = seed_source(seed)
    lr = selected_lr(arm)
    calib = SPEC[arm]['calibrate'] and seed == 3401
    if lr is None and not calib:
        return False
    with ctx(arm, seed):
        for d in (SRC.BASE, SRC.STORE):
            d.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name, key in (('stream.npz', 'stream_sha256'), ('panels.npz', 'panels_sha256')):
            if not (SRC.STORE / name).exists():
                shutil.copyfile(store0 / name, SRC.STORE / name)
            assert sha(SRC.STORE / name) == plan0[key], name
        if not SRC.sigmas_path().exists():
            shutil.copyfile(base0 / 'sigmas.json', SRC.sigmas_path()); SRC.sigmas_path().chmod(0o444)
        assert sha(SRC.sigmas_path()) == sha(base0 / 'sigmas.json')
        rows = []
        if calib:
            for clr in SRC.CAL_LRS:
                body = {'stage': 'calibration', 'arm': arm, 'lr': clr, 'updates': SRC.CAL_STEPS, 'seed': seed}
                rows.append({**body, 'id': 'PAPA_C_' + digest(body, 16)})
        keep = ('package_zip_sha256', 'manifest_sha256', 'rich_sha256', 'stage1', 'stage1_gate_sha256', 'pool', 'eligible_people',
                'excluded_people', 'panel_seed', 'inner', 'optimizer', 'production_updates', 'production_snapshots')
        body = {'version': 'PAPER_ARMS_SOURCE_v1', 'arm': arm, 'seed': seed, 'spec': {**SPEC[arm], 'views': list(SPEC[arm]['views'])},
                'rows': rows, 'sources': SRC.sources(), 'paper_sources': paper_sources(), 'store': str(SRC.STORE),
                **{k: plan0[k] for k in keep}, 'views': list(SPEC[arm]['views']), 'stream_seed': SRC.STREAM_SEED,
                'stream_sha256': plan0['stream_sha256'], 'panels_sha256': plan0['panels_sha256'],
                'seed_source_plan_sha256': sha(base0 / 'plan.json'), 'sigmas_sha256': sha(SRC.sigmas_path()),
                'lr_rule': ('source-only calibration at seed 3401 (1e-4 vs 3e-4, 1000 updates, common dev ridge probe); other seeds inherit'
                            if SPEC[arm]['calibrate'] else 'TCS R1 selection inherited (not re-selected)')}
        plan = SRC.BASE / 'plan.json'
        if plan.exists():
            old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        else:
            write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
        if lr is not None and not (SRC.BASE / 'selection.json').exists() and not calib:
            write_selection(arm, seed, lr, 'inherited' if SPEC[arm]['calibrate'] else 'inherits_TCS_R1')
    return True


def write_selection(arm, seed, lr, status, probe=None):
    rows = [production_row(arm, seed, lr)]
    sel = {'version': 'PAPER_ARMS_SELECTION_v1', 'plan_sha256': sha(SRC.BASE / 'plan.json'),
           'choice': {arm: {'lr': lr, 'status': status, **({'probe': probe} if probe else {})}}, 'production_rows': rows,
           'created': datetime.now().astimezone().isoformat()}
    path = SRC.BASE / 'selection.json'
    if path.exists():
        old = read(path); assert old['choice'][arm]['lr'] == lr and old['production_rows'] == rows
        return old
    write(path, sel); path.chmod(0o444)
    return sel


def select(arm):
    """Seed-3401 calibration -> LR (aln41/source.py rule); then the other seeds' plans inherit it."""
    with ctx(arm, 3401):
        plan = read(SRC.BASE / 'plan.json'); recs = {}
        for r in plan['rows']:
            u = read(SRC.BASE / 'units' / f'{r["id"]}.json'); assert u['status'] == 'complete'
            recs[r['lr']] = u['selection_probe']
        finite = all(math.isfinite(recs[lr]['mean']) for lr in SRC.CAL_LRS)
        best = min(SRC.CAL_LRS, key=lambda lr: (recs[lr]['mean'], lr)) if finite else 1e-4
        write_selection(arm, 3401, best, 'selected' if finite else 'uninformative_selection', {str(k): v for k, v in recs.items()})
    for seed in SEEDS[1:]:
        make_plan(arm, seed)


def plans():
    for arm in ARMS:
        for seed in SEEDS:
            make_plan(arm, seed)


# ----------------------------------------------------------------------------------------------- state
def source_rows(arm, seed):
    base = OUT / arm / f'seed{seed}' / 'source_v1'
    if not (base / 'plan.json').exists():
        return base, []
    rows = list(read(base / 'plan.json')['rows'])
    if (base / 'selection.json').exists():
        rows += read(base / 'selection.json')['production_rows']
    return base, rows


def production_done(arm, seed):
    base, rows = source_rows(arm, seed)
    prod = [r for r in rows if r['stage'] == 'production']
    return bool(prod) and all((base / 'units' / f'{r["id"]}.json').exists() for r in prod)


def calibration_pending_selection(arm):
    base, rows = source_rows(arm, 3401)
    calib = [r for r in rows if r['stage'] == 'calibration']
    return bool(calib) and all((base / 'units' / f'{r["id"]}.json').exists() for r in calib) and not (base / 'selection.json').exists()


def open_source_units():
    out = []
    for arm in ARMS:
        for seed in SEEDS:
            base, rows = source_rows(arm, seed)
            for r in rows:
                if not (base / 'units' / f'{r["id"]}.json').exists():
                    out.append((arm, seed, r, (base / 'units' / f'{r["id"]}.FAILED.json').exists()))
    return out


def frozen_rows(arm, seed):
    base = OUT / arm / f'seed{seed}' / 'frozen_v1'
    return base, (read(base / 'plan.json')['rows'] if (base / 'plan.json').exists() else [])


def open_frozen_units():
    out = []
    for arm in ARMS:
        for seed in SEEDS:
            if not production_done(arm, seed):
                continue
            base, rows = frozen_rows(arm, seed)
            if not rows:
                out.append((arm, seed, None, False)); continue
            for r in rows:
                if not (base / 'units' / f'{r["id"]}.json').exists():
                    out.append((arm, seed, r, (base / 'units' / f'{r["id"]}.FAILED.json').exists()))
    return out


def receipts():
    out = {'pass': [], 'other': []}
    for path in sorted((OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('paper_sources') == paper_sources():
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status(lane='A'):
    name, lane_name, sbatch = LANES[lane]
    st = {'name': name, 'lane': lane_name, 'state': 'plan_missing', 'ready': 0, 'remaining': 1, 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'THSIC' / 'seed3401' / 'source_v1' / 'plan.json').exists():
        return st
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [sbatch, 'smoke']} if lane == 'A' else {**st, 'state': 'waiting_smoke'}
    if lane == 'Z':
        units = open_frozen_units()
        st['remaining'] = len(units) + sum(1 for a in ARMS for s in SEEDS if not production_done(a, s))
        if not st['remaining']:
            return {**st, 'state': 'complete'}
        if any(f for *_, f in units):
            return {**st, 'state': 'failed_unit_review'}
        ready = len(units)
        return {**st, 'state': 'ready' if ready else 'waiting_for_sources', 'ready': ready, 'slots': 2,
                'submit': [sbatch, 'frozen-worker', '--max-units', '3']}
    units = open_source_units()
    pending_plans = sum(1 for a in ARMS for s in SEEDS if not (OUT / a / f'seed{s}' / 'source_v1' / 'plan.json').exists())
    st['remaining'] = len(units) + pending_plans
    if not st['remaining']:
        return {**st, 'state': 'complete'}
    if any(f for *_, f in units):
        return {**st, 'state': 'failed_unit_review'}
    ready = len(units) + sum(1 for a in ARMS if calibration_pending_selection(a))
    if lane == 'B':
        ready = max(0, ready - 2)          # lane B only takes work beyond lane A's two slots
    return {**st, 'state': 'ready' if ready else 'waiting_calibration', 'ready': ready, 'slots': 2,
            'submit': [sbatch, 'worker', '--max-units', '2']}


# ----------------------------------------------------------------------------------------------- GPU steps
def fix_scale():
    """THSIC objective scale: mean TCS score / mean mass-corrected HSIC over the support and query blocks of the first 16
    seed-3401 updates (both people, three views), uniform q, initial state, eval mode. Written once, then frozen."""
    import torch
    dev = torch.device('cuda')
    with ctx('THSIC', 3401):
        man = SRC.open_manifest(); stream = SRC.load_arrays(SRC.STORE / 'stream.npz'); sig = read(SRC.sigmas_path())['sigmas']
        src = SRC.Source(man, stream['rows'][:SCALE_UPDATES].reshape(-1), dev); model, a = SRC.build_model(dev); model.eval()
        init = SRC.state_digest(model); assert init == read(SRC.sigmas_path())['initial_state_sha256']
        D, H = [], []
        with torch.no_grad():
            for u in range(SCALE_UPDATES):
                for j in range(2):
                    for k in range(2):
                        rows, off = stream['rows'][u, j, k], stream['off'][u, j, k]
                        U, _ = model(src.crops(rows, off)); A, _ = src.audio(rows, off)
                        for vb in _ORIGINAL_VIEW_BATCHES(U, A, sig):
                            D.append(float(TO.temporal_cs_score(vb, a.detach())[0]))
                            H.append(float(TH.temporal_hsic_score(vb, a.detach(), 1.0)[0]))
    D, H = np.array(D), np.array(H)
    value = {'scale': float(D.mean() / H.mean()), 'mean_tcs_nats': float(D.mean()), 'mean_hsic': float(H.mean()), 'n_blocks': len(D),
             'tcs_quantiles': np.quantile(D, [0, .5, 1]).tolist(), 'hsic_quantiles': np.quantile(H, [0, .5, 1]).tolist(),
             'initial_state_sha256': init, 'updates': SCALE_UPDATES,
             'rule': 'mean TCS / mean mass-corrected HSIC, S and Q blocks of the first 16 seed-3401 updates, uniform q, initial state',
             'device': torch.cuda.get_device_name(0), 'job': os.environ.get('SLURM_JOB_ID')}
    assert math.isfinite(value['scale']) and value['scale'] > 0
    if SCALE.exists():
        old = read(SCALE); assert abs(old['scale'] - value['scale']) <= 1e-4 * old['scale'], 'scale drift'
        return old
    write(SCALE, value); SCALE.chmod(0o444)
    return value


def run_one(arm, seed, uid, probe=False):
    with ctx(arm, seed):
        plan = read(SRC.BASE / 'plan.json'); SRC.verify(plan); assert plan['paper_sources'] == paper_sources(), 'paper source drift'
        if SPEC[arm]['kind'] == 'THSIC':
            assert scale_value() is not None, 'THSIC scale not fixed'
        _, rows = source_rows(arm, seed)
        return SRC.run_unit(next(r for r in rows if r['id'] == uid), plan, probe=probe)


def run_frozen(arm, seed, uid):
    with ctx(arm, seed):
        plan = read(FZ.BASE / 'plan.json'); FZ.verify(plan)
        return FZ.run_unit(next(r for r in plan['rows'] if r['id'] == uid), plan)


def sub(*args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *map(str, args)]).returncode


def smoke():
    job = os.environ['SLURM_JOB_ID']
    receipt = {'status': 'running', 'paper_sources': paper_sources(), 'units': []}
    try:
        plans()
        receipt['scale'] = fix_scale()
        for arm in ('THSIC', 'SV_env'):
            _, rows = source_rows(arm, 3401)
            row = rows[0]
            assert sub('unit', '--arm', arm, '--seed', 3401, '--id', row['id'], '--probe') == 0, arm
            with ctx(arm, 3401):
                rec = read(SRC.BASE / 'probes' / job / 'units' / f'{row["id"]}.json')
            receipt['units'].append({'arm': arm, 'id': row['id'], 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'],
                                     'losses': [x['loss'] for x in rec['log']],
                                     'views_in_log': sorted({v['view'] for x in rec['log'] for q in x['query'] for v in q['views']})})
        assert receipt['units'][1]['views_in_log'] == ['env'] and receipt['units'][0]['views_in_log'] == ['env', 'sc', 'ss']
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)


def claim(base, uid, fn):
    path = base / 'units' / f'{uid}.json'
    lock = base / 'claims' / f'{uid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists():
            return False
        rc = fn()
        if rc < 0:                          # preempted / signalled: no FAILED marker, the unit resumes elsewhere
            raise SystemExit(rc)
        if rc or not path.exists():
            write(base / 'units' / f'{uid}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
            raise RuntimeError(f'paper arm unit failed: {uid}')
        return True


def worker(max_units):
    assert receipts()['pass'], 'no passing smoke'
    count = 0
    for arm in ARMS:
        if calibration_pending_selection(arm):
            lock = OUT / arm / 'select.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with lock.open('a+') as h:
                fcntl.flock(h, fcntl.LOCK_EX)
                if calibration_pending_selection(arm):
                    select(arm)
    for arm, seed, row, failed in open_source_units():
        if failed:
            continue
        base = OUT / arm / f'seed{seed}' / 'source_v1'
        if claim(base, row['id'], lambda: sub('unit', '--arm', arm, '--seed', seed, '--id', row['id'])):
            count += 1
        if count >= max_units:
            break


def frozen_worker(max_units):
    assert receipts()['pass'], 'no passing smoke'
    count = 0
    for arm, seed, row, failed in open_frozen_units():
        if failed:
            continue
        if row is None:
            with ctx(arm, seed):
                FZ.make_plan()
            continue
    for arm, seed, row, failed in open_frozen_units():
        if failed or row is None:
            continue
        base = OUT / arm / f'seed{seed}' / 'frozen_v1'
        if claim(base, row['id'], lambda: sub('frozen-unit', '--arm', arm, '--seed', seed, '--id', row['id'])):
            count += 1
        if count >= max_units:
            break


def readout(arms):
    """CPU: aln41 readout for every arm x seed whose frozen units are complete."""
    argv = sys.argv
    try:
        for arm in arms:
            for seed in SEEDS:
                base, rows = frozen_rows(arm, seed)
                if rows and all((base / 'units' / f'{r["id"]}.json').exists() for r in rows):
                    with ctx(arm, seed):
                        sys.argv = ['readout', '--all-ready']; RO.main()
    finally:
        sys.argv = argv


def status():
    out = {}
    for arm in ARMS:
        for seed in SEEDS:
            base, rows = source_rows(arm, seed); fb, frows = frozen_rows(arm, seed)
            out[f'{arm}/{seed}'] = {'source': f"{sum((base / 'units' / (r['id'] + '.json')).exists() for r in rows)}/{len(rows)}",
                                    'frozen': f"{sum((fb / 'units' / (r['id'] + '.json')).exists() for r in frows)}/{len(frows)}"}
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'smoke', 'worker', 'unit', 'frozen-worker', 'frozen-unit', 'readout', 'status'))
    ap.add_argument('--arm'); ap.add_argument('--seed', type=int); ap.add_argument('--id'); ap.add_argument('--probe', action='store_true')
    ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.cmd == 'plan':
        plans(); status()
    elif a.cmd == 'smoke':
        smoke()
    elif a.cmd == 'worker':
        worker(a.max_units)
    elif a.cmd == 'unit':
        run_one(a.arm, a.seed, a.id, a.probe)
    elif a.cmd == 'frozen-worker':
        frozen_worker(a.max_units)
    elif a.cmd == 'frozen-unit':
        run_frozen(a.arm, a.seed, a.id)
    elif a.cmd == 'readout':
        readout([a.arm] if a.arm else ARMS)
    else:
        status()


if __name__ == '__main__':
    main()
