"""ALN4.1 R2 cross-stimulus question (F_CROSS_STIM). Decision fixed before any result:
docs/auditory_alignment_v3/aln41/R2_CROSS_STIM_DECISION.md (its sha256 is bound in the plan).

Route A, deviance-relation transfer: MFF pure-tone (source lane) -> MFF bapa (target lane), label deviant vs standard.
Data: GX_stage_001 epochs of the gated records (status OK, >= 40 accepted per class, >= 4 blocks); accepted trials with a
known since-last-deviant bin; per-record per-channel z-score over trials x time. This is the hc.load_children rule of the
private BDF lane, applied per record; a child's gated records in one lane are pooled.
GPU unit per frozen core-3 backbone (B0; TCS / TNCE x seeds 3401, 3407, 3413). Raw tokens of every kept trial of both lanes
come from the three crops of frozen.private_unit (onset 50, timebank layout at 250 Hz). CBraMod reads no channel names; the
E1-E128 order is stored. Then 15 PCA64 fits (frozen.pca_fit, <= 2730 rows per slot) project every kept trial:
- transfer f: pure-tone ids not in bapa fold f;
- refit f: bapa ids outside fold f;
- within g: pure-tone ids outside pure-tone fold g (for the same-day description).
Folds: ids ranked by sha256(identity key), fold = rank mod 5.
CPU readout: the private BDF contract per slot, mixed with q0, fitted on every kept row of the fit's training ids:
private_current_time_v2.Probe; history = 6-bin base rate + B1 intercept + history_interface.fit_offset. Per test child:
AUC of the q0 mixture (primary) and the history increment in bits/trial (secondary).
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from . import frozen as FZ, r2 as R2, source as SRC

OUT = SRC.OUT / 'cross_stim_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln41/cross_stim_v1')
STAGE = Path(core.REPO) / 'private/auditory_gx/GX_stage_001'
DECISION = Path(core.REPO) / 'docs/auditory_alignment_v3/aln41/R2_CROSS_STIM_DECISION.md'
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/aln41/r2_cross_stim'
LANES = ('mff_puretone', 'mff_bapa')
UNITS = [('B0', None)] + [(arm, s) for arm in ('TCS', 'TNCE') for s in (3401, 3407, 3413)]
FITS = [('transfer', f) for f in range(5)] + [('refit', f) for f in range(5)] + [('within', g) for g in range(5)]
PCA_OFFSET = {'transfer': 200, 'refit': 300, 'within': 400}
NAME, LANE, SBATCH = 'c3_s35a41xs', 's35_aln41_cross_stim', 'slurm/aln35_aln41_cross.sbatch'
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest


def sources():
    here = Path(__file__).parent
    files = [here / 'cross_stim.py', here / 'frozen.py', here / 'timebank.py', here / 'time_access.py', here / 'r2.py', here / 'readout.py',
             Path(core.REPO) / 'auditory_c3/private_mi2.py', Path(core.REPO) / 'auditory_alignment_v2/foundation_adapter.py',
             Path(core.REPO) / 'auditory_alignment_v3/aln34/private_current_time_v2.py',
             Path(core.REPO) / 'auditory_alignment_v3/aln35/history_interface.py']
    return {str(p.relative_to(core.REPO)): sha(p) for p in sorted(set(files))}


# ----------------------------------------------------------------------------------------------- data
def gated_records():
    out = []
    for p in sorted((STAGE / 'summaries').glob('M*.json')):
        d = read(p)
        if d['lane'] not in LANES or d['status'] != 'OK':
            continue
        a = d['accepted_per_class']
        if min(int(a.get('0', 0)), int(a.get('1', 0))) >= 40 and int(d['blocks']) >= 4:
            out.append({'lane': d['lane'], 'record_id': d['record_id'], 'identity': d['identity_group'],
                        'npz_sha256': sha(STAGE / 'epochs' / f'{d["record_id"]}.npz')})
    return out


def fold_of(ids):
    ranked = sorted(ids, key=lambda i: hashlib.sha256(i.encode()).hexdigest())
    return {i: r % 5 for r, i in enumerate(ranked)}


def load(records):
    """Row arrays over both lanes (lane-major, record order) and the child table; x float32 [n, 128, 200]."""
    from auditory_c3.private_mi2 import hist_codes
    X, rows = [], {k: [] for k in ('lane', 'child', 'y', 'bin', 'block', 'record')}
    children = []
    key = {}
    for ri, r in enumerate(records):
        with np.load(STAGE / 'epochs' / f'{r["record_id"]}.npz', allow_pickle=False) as s:
            acc = s['accepted'].astype(bool)
            x = s['x'][acc].astype(np.float32); y = s['y'][acc].astype(np.int64); blk = s['block_id'][acc].astype(np.int64)
            h = hist_codes(s['previous_code'][acc], s['previous_run_length'][acc])['since_last_deviant']
            assert str(s['lane']) == r['lane'] and x.shape[1:] == (128, 200)
        ok = h >= 0
        x = x[ok]; mu = x.mean(axis=(0, 2), keepdims=True); sd = x.std(axis=(0, 2), keepdims=True); sd[sd == 0] = 1
        X.append((x - mu) / sd)
        c = key.setdefault((r['lane'], r['identity']), len(children))
        if c == len(children):
            children.append({'lane': r['lane'], 'identity': r['identity']})
        n = int(ok.sum())
        for k, v in (('lane', np.full(n, LANES.index(r['lane']))), ('child', np.full(n, c)), ('y', y[ok]), ('bin', h[ok].astype(np.int64)),
                     ('block', blk[ok]), ('record', np.full(n, ri))):
            rows[k].append(v)
    return np.concatenate(X), {k: np.concatenate(v) for k, v in rows.items()}, children


def fit_rows(rows, children, kind, f):
    """Training rows of one PCA/readout fit and the test children it serves."""
    lane = np.array([c['lane'] for c in children]); ident = [c['identity'] for c in children]
    bfold = fold_of([i for i, l in zip(ident, lane) if l == 'mff_bapa']); pfold = fold_of([i for i, l in zip(ident, lane) if l == 'mff_puretone'])
    test_ids = {i for i, v in bfold.items() if v == f} if kind != 'within' else {i for i, v in pfold.items() if v == f}
    if kind == 'transfer':
        train = [c for c, (i, l) in enumerate(zip(ident, lane)) if l == 'mff_puretone' and i not in test_ids]
        test = [c for c, (i, l) in enumerate(zip(ident, lane)) if l == 'mff_bapa' and i in test_ids]
    elif kind == 'refit':
        train = [c for c, (i, l) in enumerate(zip(ident, lane)) if l == 'mff_bapa' and i not in test_ids]
        test = [c for c, (i, l) in enumerate(zip(ident, lane)) if l == 'mff_bapa' and i in test_ids]
    else:
        train = [c for c, (i, l) in enumerate(zip(ident, lane)) if l == 'mff_puretone' and i not in test_ids]
        test = [c for c, (i, l) in enumerate(zip(ident, lane)) if l == 'mff_puretone' and i in test_ids]
    assert not {ident[c] for c in train} & {ident[c] for c in test}
    return np.flatnonzero(np.isin(rows['child'], train)), test


# ----------------------------------------------------------------------------------------------- plan
def make_plan():
    recs = gated_records()
    n = {l: (sum(r['lane'] == l for r in recs), len({r['identity'] for r in recs if r['lane'] == l})) for l in LANES}
    assert n == {'mff_puretone': (35, 33), 'mff_bapa': (25, 24)}, n
    rows = []
    for arm, seed in UNITS:
        body = {'arm': arm, 'seed': seed, 'route': 'deviance_transfer_puretone_to_bapa'}
        rows.append({**body, 'id': 'ALN41X_' + digest(body, 16)})
    body = {'version': 'ALN41_CROSS_STIM_v1', 'rows': rows, 'decision_sha256': sha(DECISION), 'sources': sources(),
            'records': recs, 'records_sha256': digest(recs), 'store': str(STORE), 'fits': [list(x) for x in FITS],
            'pca': {'dim': FZ.PCA_DIM, 'rows_per_slot': FZ.PCA_ROWS_PER_SLOT, 'seed': {k: FZ.PCA_SEED + v for k, v in PCA_OFFSET.items()}},
            'folds': 'ids ranked by sha256(identity key); fold = rank mod 5 (bapa folds for transfer/refit, pure-tone for within)',
            'counts': {l: {'records': v[0], 'ids': v[1]} for l, v in n.items()}}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        OUT.mkdir(parents=True, exist_ok=True, mode=0o700); STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
        write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    print('ALN41 cross-stim plan', len(rows), 'units', n, sha(plan), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen source drift'
    assert plan['decision_sha256'] == sha(DECISION), 'decision record changed'


def arm_state(row):
    if row['arm'] == 'B0' or row['seed'] == SRC.SEED:
        return FZ.arm_state(row['arm'])
    with R2.seeded(row['seed']):
        return FZ.arm_state(row['arm'])


def ready(row):
    if row['arm'] == 'B0' or row['seed'] == SRC.SEED:
        return True
    with R2.seeded(row['seed']):
        return FZ.ready({'arm': row['arm']})


# ----------------------------------------------------------------------------------------------- GPU unit
def run_unit(row, plan, probe=False):
    import torch
    from . import timebank as TB
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    recs = plan['records']
    if probe:
        recs = [r for r in recs if r['lane'] == 'mff_puretone'][:6] + [r for r in recs if r['lane'] == 'mff_bapa'][:6]
    for r in recs:
        assert sha(STAGE / 'epochs' / f'{r["record_id"]}.npz') == r['npz_sha256'], r['record_id']
    X, rows, children = load(recs)
    Xt = torch.as_tensor(X); lay = TB.layout(250)

    def crops_fn(s, t):
        return [Xt[s:t, :, 50 + lo:50 + hi].to(dev) for lo, hi, _ in lay]
    net, q0, prov = arm_state(row)
    bb = FZ.backbone('private_bdf', net, dev)            # CBraMod: the key only names channels; tokens follow the input order
    T = FZ.tokens(bb, crops_fn, len(X), 250)
    assert T.shape[1:] == (3, 128 * 200) and bool(torch.isfinite(T[:256].float()).all())
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    arrays = dict(rows); meta = {'row': row, 'arm_provenance': prov, 'q0': np.asarray(q0).tolist(), 'children': children,
                                 'crop_layout': lay, 'n_trials': int(len(X)), 'pca': {}, 'probe': probe}
    for kind, f in FITS:
        train, test = fit_rows(rows, children, kind, f)
        if probe and (len(train) < 50 or not test):
            continue
        p = FZ.pca_fit(T, train, FZ.PCA_SEED + PCA_OFFSET[kind] + f)
        arrays[f'pca_{kind}{f}'] = FZ.pca_apply(T.reshape(len(T) * 3, -1), p).reshape(len(T), 3, -1).astype(np.float16)
        meta['pca'][f'{kind}{f}'] = {k: v for k, v in p.items() if k in ('n_rows', 'dim', 'explained_variance')}
        meta['pca'][f'{kind}{f}'].update(row_ids_sha256=digest(p['row_ids']), train_children=len(set(rows['child'][train].tolist())),
                                         test_children=len(test))
        assert np.isfinite(arrays[f'pca_{kind}{f}']).all()
    np.savez_compressed(dest / 'arrays.npz', **arrays)
    meta['array_sha256'] = sha(dest / 'arrays.npz'); write(dest / 'meta.json', meta)
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'dest': str(dest),
           'meta_sha256': sha(dest / 'meta.json'), 'array_sha256': meta['array_sha256'], 'seconds': time.time() - t0,
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job}
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], row['arm'], row['seed'], 'complete', len(X), 'trials', round(rec['seconds'], 1), flush=True)
    del T, Xt; gc.collect()
    return rec


# ----------------------------------------------------------------------------------------------- CPU readout
def readout(row):
    from sklearn.metrics import roc_auc_score
    from scipy.special import expit
    from ..aln34 import private_current_time_v2 as PV2
    from ..aln35 import history_interface as HI
    unit = read(OUT / 'units' / f'{row["id"]}.json'); dest = Path(unit['dest'])
    assert sha(dest / 'arrays.npz') == unit['array_sha256']
    meta = read(dest / 'meta.json'); q0 = np.asarray(meta['q0']); children = meta['children']
    LN2 = math.log(2)
    with np.load(dest / 'arrays.npz') as z:
        A = {k: z[k] for k in z.files}
    y_all, bins, owner = A['y'], A['bin'], A['child']

    def ll(p, y):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return np.where(y == 1, np.log(p), np.log(1 - p)) / LN2
    out = {kind: {} for kind in ('transfer', 'refit', 'within')}
    for kind, f in FITS:
        train, test = fit_rows(A, children, kind, f)
        X = A[f'pca_{kind}{f}'].astype(np.float64); yt = y_all[train]
        q0h = np.array([(yt[bins[train] == h].sum() + .5) / ((bins[train] == h).sum() + 1.) for h in range(6)])
        off = np.log(np.clip(q0h[bins], 1e-12, 1)) - np.log(np.clip(1 - q0h[bins], 1e-12, 1))
        b1, _ = HI.fit_intercept(yt, off[train])
        probes, hist = [], []
        for k in range(3):
            probes.append(PV2.Probe(X[train, k], yt))
            mu, sd = X[train, k].mean(0), X[train, k].std(0) + 1e-8
            w, _ = HI.fit_offset((X[train, k] - mu) / sd, yt, off[train]); hist.append((mu, sd, w))
        for c in test:
            rows = np.flatnonzero(owner == c); y = y_all[rows]
            cur = np.stack([expit(probes[k].cal.logits(probes[k].score(X[rows, k]))) for k in range(3)])
            ph = np.stack([expit(off[rows] + np.column_stack([np.ones(len(rows)), (X[rows, k] - hist[k][0]) / hist[k][1]]) @ hist[k][2])
                           for k in range(3)])
            mix = q0 @ cur; hmix = q0 @ ph; pb1 = expit(off[rows] + b1)
            out[kind][children[c]['identity']] = {
                'fold': f, 'n_trials': int(len(rows)), 'class_counts': {'0': int((y == 0).sum()), '1': int((y == 1).sum())},
                'auc_q0': float(roc_auc_score(y, mix)), 'auc_slots': [float(roc_auc_score(y, cur[k])) for k in range(3)],
                'history_increment_bits_q0': float((ll(hmix, y) - ll(pb1, y)).mean())}
    return {'row': row, 'q0': q0.tolist(), 'children': out}


# ----------------------------------------------------------------------------------------------- workers / fleet
def receipts():
    out = {'pass': [], 'other': []}
    if not (OUT / 'plan.json').exists():
        return out
    for path in sorted((OUT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == sha(OUT / 'plan.json'):
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': len(UNITS), 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'plan.json').exists():
        return st
    plan = read(OUT / 'plan.json')
    left = [r for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return {**st, 'state': 'failed_unit_review'}
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    avail = [r for r in left if ready(r)]
    if not avail:
        return {**st, 'state': 'waiting_for_r2_sources'}
    return {**st, 'state': 'ready', 'ready': len(avail), 'slots': 2, 'submit': [SBATCH, '--worker']}


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'smoke', 'worker', 'readout'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); verify(plan)
    if a.unit or a.probe_unit:
        run_unit(next(r for r in plan['rows'] if r['id'] in (a.unit, a.probe_unit)), plan, probe=bool(a.probe_unit)); return
    if a.smoke:
        job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
        try:
            row = plan['rows'][0]
            assert subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['id']]).returncode == 0
            rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
            receipt['units'].append({'id': row['id'], 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb']})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            write(OUT / 'probes' / job / 'receipt.json', receipt)
        return
    if a.readout:
        done = []
        for row in plan['rows']:
            path = OUT / 'readout' / f'{row["id"]}.json'
            if path.exists() or not (OUT / 'units' / f'{row["id"]}.json').exists():
                continue
            write(path, {**readout(row), 'unit_sha256': sha(OUT / 'units' / f'{row["id"]}.json')}); done.append(row['id'])
            print('readout', row['arm'], row['seed'], flush=True)
        return
    assert a.worker and receipts()['pass'], 'no passing smoke for this plan'
    for row in plan['rows']:
        path = OUT / 'units' / f'{row["id"]}.json'
        if path.exists() or (OUT / 'units' / f'{row["id"]}.FAILED.json').exists() or not ready(row):
            continue
        lock = OUT / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc or not path.exists():
                write(OUT / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln41 cross-stim unit failed')
        break


if __name__ == '__main__':
    main()
