"""ALN4.1 R1 frozen readouts (CPU): content, 3x3 time transfer, history/twin and q0/uniform mixtures per person.

Public (per arm x dataset x content fold, each of the 5 pooled person folds): within the fold, the training side is the
fold's training people (role fit for fitting, role es for ridge selection; content_time.fitted, 8 alphas by ES r, refit
fit+es), the query the outer people's role=test anchors. Targets: current envelope (direct) and its history-conditional
residual (ridge on the four past-envelope lags fitted on the same training side), both standardised on training rows.
One readout per slot on the fold's PCA64 features; mixture predictions = q-weighted sum of the slot predictions
(q0 = softmax(source a); uniform reset reported beside it). Time: readout fitted at slot r applied to slot s (fixed),
same-window r->r and refit s->s; per person Pearson r over the person's query anchors.
Private (per arm x outer fold): source children = other folds, rows = their ES blocks (the existing private contract:
private_current_time_v2.Probe = standardise, L2 logistic C=1, positive-affine calibration on the same ES scores; history:
logit q0[6 bins] + one ES intercept (B1), EEG offset logistic history_interface.fit_offset). Mixtures over slots as for the
public side. Strict twin: same child, same history bin, other block, non-self (history_interface.strict_twin_map over all
of the outer child's trials; seed 361900 + sha256(child)).
"""
from __future__ import annotations

import argparse
import hashlib
import math
import os
from pathlib import Path
import time
import traceback

import numpy as np
from scipy.special import expit

from ..aln34 import content_time as CT
from . import frozen as FZ
from . import source as SRC

BASE = SRC.OUT / 'readout_v1'
SLOTS = ('W0', 'W1', 'W2')
read, write, sha = SRC.read, SRC.write, SRC.sha


def load(row):
    unit = read(FZ.BASE / 'units' / f'{row["id"]}.json'); dest = Path(unit['dest'])
    assert sha(dest / 'meta.json') == unit['meta_sha256'] and sha(dest / 'arrays.npz') == unit['array_sha256']
    with np.load(dest / 'arrays.npz', allow_pickle=False) as z:
        A = {k: z[k] for k in z.files}
    return A, read(dest / 'meta.json')


def corr(y, p):
    return CT.correlation(y[:, None], p[:, None])


def rowcorr(a, b):
    a = a - a.mean(1, keepdims=True); b = b - b.mean(1, keepdims=True)
    return (a * b).sum(1) / np.sqrt(np.maximum((a * a).sum(1) * (b * b).sum(1), 1e-24))


def attention(A, meta, sf, fits, q, train_people, test_people):
    """Mean-score evidence integration of attended-minus-ignored envelope-readout correlations (aln34.attention_transfer
    mean integrator: tau on training-side windows by double-order log loss; ties credit 0.5)."""
    from ..run_attention import _runs, _windows
    from ..aln34 import attention_order as AO
    key = f'cs_pca_sf{sf}'
    if key not in A or not len(A['cs_person']):
        return None
    F = A[key].astype(np.float64)
    pred = np.einsum('k,knt->nt', q, np.stack([(F[:, :, k] @ fits[k][0] + fits[k][1])[..., 0] for k in range(3)]))
    margin = rowcorr(pred, A['cs_env_att']) - rowcorr(pred, A['cs_env_ign'])
    seg_len = meta['cs']['seg_len']
    segs = [{'p': p, 'code': c, 'e0': int(e), 'role': r, 'i': i}
            for i, (p, c, e, r) in enumerate(zip(A['cs_person'], A['cs_code'], A['cs_e0'], A['cs_role']))]
    tr = [s_ for s_ in segs if s_['p'] in train_people and s_['role'] in ('fit', 'es')]
    te = [s_ for s_ in segs if s_['p'] in test_people and s_['role'] == 'test']
    out = {}
    for sec in (5, 10, 20):
        k = sec // 5
        wt = [w for role in ('es', 'fit') for w in _windows(_runs([s_ for s_ in tr if s_['role'] == role], seg_len), k)]
        we = _windows(_runs(te, seg_len), k)
        if not wt or not we:
            out[str(sec)] = {'status': 'no_windows'}; continue
        xt = np.array([[margin[s_['i']] for s_ in w] for w in wt]); xe = np.array([[margin[s_['i']] for s_ in w] for w in we])
        rms = AO.train_scale(xt); grid = np.logspace(-3, 2, 41) * (rms if rms > 0 else 1.0)
        loss = [AO.order_logloss_bits(xt.mean(1) / t, -xt.mean(1) / t).mean() for t in grid]; tau = float(grid[int(np.argmin(loss))])
        z = xe.mean(1) / tau; acc = AO.order_credit(z, -z); ll = AO.order_logloss_bits(z, -z)
        per = {}
        for j, w in enumerate(we):
            per.setdefault(w[0]['p'], []).append(j)
        out[str(sec)] = {'tau': tau, 'training_windows': len(wt),
                         'people': {p: {'accuracy': float(acc[ix].mean()), 'nll_bits': float(ll[ix].mean()), 'n_windows': len(ix)} for p, ix in per.items()}}
    return out


def public(row):
    A, meta = load(row); q0 = np.asarray(meta['q0']); qu = np.full(3, 1 / 3)
    person, role = A['person'], A['role']
    folds, dev = meta['folds'], set(meta['dev_people'])
    out = {}
    for sf in range(5):
        X = A[f'pca_sf{sf}'].astype(np.float64)
        train_people = set(meta['pca'][str(sf)]['train_people'])
        trn = np.isin(person, list(train_people)); fit = trn & (role == 'fit'); es = trn & (role == 'es')
        r2 = np.where(fit, 'fit', np.where(es, 'es', 'other'))
        targets = {}
        y = A['env']; m, s = y[fit | es].mean(), y[fit | es].std() + 1e-12; targets['env/direct'] = (y - m) / s
        w, b, _ = CT.fitted(A['env_history'], A['env'][:, None], r2)
        res = A['env'] - (A['env_history'] @ w + b)[:, 0]; m, s = res[fit | es].mean(), res[fit | es].std() + 1e-12
        targets['env/history_conditional'] = (res - m) / s
        test_people = sorted(p for p in set(person.tolist()) if folds.get(p) == sf and p not in dev)
        for tname, t in targets.items():
            fits = [CT.fitted(X[:, k], t[:, None], r2) for k in range(3)]
            pred = np.stack([np.stack([(X[:, s_] @ fits[r][0] + fits[r][1])[:, 0] for s_ in range(3)]) for r in range(3)])  # [r, s, n]
            if tname == 'env/direct':
                att = {'q0': attention(A, meta, sf, fits, q0, train_people, set(test_people)),
                       'uniform': attention(A, meta, sf, fits, qu, train_people, set(test_people))}
                for mode, res_ in att.items():
                    for sec, val in (res_ or {}).items():
                        for p, v in val.get('people', {}).items():
                            out.setdefault(p, {'person_fold': sf, 'content_fold': row['content_fold'], 'group': meta['groups'][p]}) \
                               .setdefault('attention', {}).setdefault(mode, {})[sec] = {**v, 'tau': val['tau']}
            mix = {'q0': np.einsum('k,kn->n', q0, pred[np.arange(3), np.arange(3)]),
                   'uniform': np.einsum('k,kn->n', qu, pred[np.arange(3), np.arange(3)])}
            for p in test_people:
                ix = (person == p) & (role == 'test')
                if not ix.any():
                    continue
                rec = out.setdefault(p, {'person_fold': sf, 'content_fold': row['content_fold'], 'group': meta['groups'][p]})
                tt = t[ix]
                grid = [[corr(tt, pred[r, s_, ix]) for s_ in range(3)] for r in range(3)]
                rec[tname] = {'mixture_q0_r': corr(tt, mix['q0'][ix]), 'mixture_uniform_r': corr(tt, mix['uniform'][ix]),
                              'slot_r': [grid[k][k] for k in range(3)], 'transfer_r': grid, 'n_query_anchors': int(ix.sum()),
                              'W0_to_W2_fixed_loss': grid[0][0] - grid[0][2], 'W0_to_W2_refit_recovery': grid[2][2] - grid[0][2],
                              'alphas': [f_[2]['alpha_relative'] for f_ in fits]}
    return {'kind': 'public', 'people': out, 'q0': q0.tolist()}


def private(row):
    from auditory_alignment import data
    from ..aln34 import private_current_time_v2 as PV2
    from ..aln35 import history_interface as HI
    from sklearn.metrics import roc_auc_score
    A, meta = load(row); q0 = np.asarray(meta['q0']); qu = np.full(3, 1 / 3)
    kids = data.load_private(); assert meta['children'] == {str(i): k['id'] for i, k in enumerate(kids)}
    owner = A['child_index']; folds = np.array([k['fold'] for k in kids])
    y_all = np.concatenate([k['y'] for k in kids]); bins = np.concatenate([k['bin'] for k in kids])
    es_all = np.concatenate([k['es_mask'] for k in kids])
    out = {}
    LN2 = math.log(2)

    def ll(p, y):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return np.where(y == 1, np.log(p), np.log(1 - p)) / LN2
    for f in range(5):
        X = A[f'pca_f{f}'].astype(np.float64)
        src = np.isin(owner, np.flatnonzero(folds != f)); es = src & es_all
        y_es = y_all[es]
        tr = [kids[i] for i in np.flatnonzero(folds != f)]
        yy = np.concatenate([k['y'] for k in tr]); bb = np.concatenate([k['bin'] for k in tr])
        q0h = np.array([(yy[bb == h].sum() + .5) / ((bb == h).sum() + 1.) for h in range(6)])
        off = np.log(np.clip(q0h[bins], 1e-12, 1)) - np.log(np.clip(1 - q0h[bins], 1e-12, 1))
        b1, _ = HI.fit_intercept(y_es, off[es])
        probes = [PV2.Probe(X[es, k], y_es) for k in range(3)]
        hist = []
        for k in range(3):
            mu, sd = X[es, k].mean(0), X[es, k].std(0) + 1e-8
            w, _ = HI.fit_offset((X[es, k] - mu) / sd, y_es, off[es]); hist.append((mu, sd, w))
        test = np.flatnonzero(folds == f)

        def p_cur(k_src, k_dst, rows):
            return expit(probes[k_src].cal.logits(probes[k_src].score(X[rows, k_dst])))

        def p_hist(k, rows, rows_x=None):
            rx = rows if rows_x is None else rows_x
            mu, sd, w = hist[k]
            return expit(off[rows] + np.column_stack([np.ones(len(rows)), (X[rx, k] - mu) / sd]) @ w)
        for i in test:
            rows = np.flatnonzero(owner == i); y = y_all[rows]; k_ = kids[i]
            cur = np.stack([[p_cur(r, s_, rows) for s_ in range(3)] for r in range(3)])        # [r, s, n]
            auc = lambda p: float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None
            grid_auc = [[auc(cur[r, s_]) for s_ in range(3)] for r in range(3)]
            mixq = np.einsum('k,kn->n', q0, cur[np.arange(3), np.arange(3)]); mixu = np.einsum('k,kn->n', qu, cur[np.arange(3), np.arange(3)])
            ph = np.stack([p_hist(k, rows) for k in range(3)]); hmix = np.einsum('k,kn->n', q0, ph); hmixu = np.einsum('k,kn->n', qu, ph)
            pb1 = expit(off[rows] + b1)
            rec = {'group': k_['group'], 'outer_fold': f, 'n_trials': int(len(rows)),
                   'class_counts': {'0': int((y == 0).sum()), '1': int((y == 1).sum())},
                   'current_auc_mixture_q0': auc(mixq), 'current_auc_mixture_uniform': auc(mixu), 'current_auc_slots': [grid_auc[k][k] for k in range(3)],
                   'current_transfer_auc': grid_auc,
                   'W0_to_W2_fixed_loss_auc': (grid_auc[0][0] - grid_auc[0][2]) if None not in (grid_auc[0][0], grid_auc[0][2]) else None,
                   'W0_to_W2_refit_recovery_auc': (grid_auc[2][2] - grid_auc[0][2]) if None not in (grid_auc[2][2], grid_auc[0][2]) else None,
                   'history_increment_bits_q0': float((ll(hmix, y) - ll(pb1, y)).mean()),
                   'history_increment_bits_uniform': float((ll(hmixu, y) - ll(pb1, y)).mean()),
                   'history_increment_bits_slots': [float((ll(ph[k], y) - ll(pb1, y)).mean()) for k in range(3)]}
            seed = 361900 + int(hashlib.sha256(k_['id'].encode()).hexdigest()[:8], 16)
            twin = HI.strict_twin_map(k_['bin'], k_['block'], np.arange(len(rows)), seed)
            el = np.flatnonzero(twin >= 0)
            if len(el):
                real = np.einsum('k,kn->n', q0, np.stack([p_hist(k, rows[el]) for k in range(3)]))
                tw = np.einsum('k,kn->n', q0, np.stack([p_hist(k, rows[el], rows[twin[el]]) for k in range(3)]))
                rec['strict_twin'] = {'n_eligible': int(len(el)), 'EEG_minus_twin_bits_q0': float((ll(real, y[el]) - ll(tw, y[el])).mean()),
                                      'EEG_minus_B1_bits_on_subset': float((ll(real, y[el]) - ll(expit(off[rows[el]] + b1), y[el])).mean())}
            else:
                rec['strict_twin'] = {'status': 'not_estimable_no_partner'}
            out[k_['id']] = rec
    return {'kind': 'private', 'people': out, 'q0': q0.tolist()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--all-ready', action='store_true')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    plan = read(FZ.BASE / 'plan.json')
    for row in plan['rows']:
        out = BASE / 'units' / f'{row["id"]}.json'
        if out.exists() or not (FZ.BASE / 'units' / f'{row["id"]}.json').exists():
            continue
        t0 = time.time()
        try:
            res = private(row) if row['dataset'] == 'private_bdf' else public(row)
            write(out, {'status': 'complete', 'row': row, 'frozen_unit_sha256': sha(FZ.BASE / 'units' / f'{row["id"]}.json'),
                        'source_sha256': sha(__file__), **res, 'seconds': time.time() - t0, 'job': os.environ['SLURM_JOB_ID']})
            print(row['id'], row['arm'], row['dataset'], 'readout complete', round(time.time() - t0, 1), flush=True)
        except Exception:
            write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'traceback': traceback.format_exc(), 'job': os.environ['SLURM_JOB_ID']})
            raise


if __name__ == '__main__':
    main()
