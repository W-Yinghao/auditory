"""ALN3.6 R1 public readout (CPU): source cross-fit, frozen shared readout, and per-person H0/E0/HP/EC/ET.

Per feature bank (one source model):
  coordinate  current envelope (Local row 5) standardised by the mean/sd over the unique audio positions of the source
              people's role=fit content (8 fixed anchors per segment); the four past-envelope lags use the same scale.
  H0          OLS of y on [1, lag20, lag100, lag200, lag500] (EEG-free history predictor), source rows only.
  probes      one ridge per window centre from the 32-d frozen representation to the history residual y - H0;
              ridge grid content_time ALPHAS (8 points), chosen by MSE on source ES rows after fitting on source fit
              rows, then refitted on fit+ES (content_time.fitted pattern, MSE instead of r).
  cross-fit   3 source-person folds (stable sha256 of seed|person); within each, H0 and probes use the other two
              folds only and produce OOF offset/scores on the held-out fold's role=es rows.
  a0, Z       score scaler = mean/sd of the OOF scores (frozen); a0 = least squares of (y - OOF offset) on scaled OOF
              scores (no intercept); TemporalBasis from the OOF rows with history design [1, 4 scaled lags].
  final       H0 and probes refitted on all source people (same rules); target rows use the frozen OOF scaler, a0, basis.
Per target person: support = first ceil(0.3 n) of the person's role=fit segments in physical order (all 8 anchors);
query = every role=test segment. Nested fit (aln36.nested, the package reference, byte-identical), lambda = 1 for all
three penalties. M0: query scores rolled by one whole segment in physical order, fixed E0 parameters.
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

from ..aln34 import content_time as CT
from . import common as C
from . import nested as N
from . import public_features as F

BASE = C.OUT / 'public_readout_v1'
RIDGE = {'history': 1.0, 'scale': 1.0, 'time': 1.0}
READOUT_FOLDS = 3
SUPPORT_FRACTION = 0.3
PRE, POST = 0.4, 0.6


def sources():
    files = [Path(__file__), Path(C.__file__), Path(N.__file__), Path(F.__file__), Path(CT.__file__)]
    return {str(p.relative_to(C.REPO)): C.sha(p) for p in sorted(set(files))}


def ols(X, y):
    return np.linalg.lstsq(X, y, rcond=None)[0]


def ridge_fit(x, y, alpha):
    return CT.ridge(x, y[:, None], alpha)


def ridge_apply(model, x):
    w, b = model
    return (x @ w + b)[:, 0]


def probe(x, r, fit, es):
    """content_time.fitted with MSE: alpha by ES MSE after fitting on fit rows, then refit on fit+ES."""
    curve = []
    for alpha in CT.ALPHAS:
        m = ridge_fit(x[fit], r[fit], alpha)
        curve.append(float(np.mean((r[es] - ridge_apply(m, x[es])) ** 2)))
    k = int(np.argmin(curve))
    both = fit | es
    return ridge_fit(x[both], r[both], CT.ALPHAS[k]), {'alpha_relative': float(CT.ALPHAS[k]), 'es_mse_curve': curve}


def readout_folds(people, seed):
    order = sorted(people, key=lambda p: hashlib.sha256(f'{seed}|{p}'.encode()).hexdigest())
    return {p: k % READOUT_FOLDS for k, p in enumerate(order)}


def load(row):
    unit = C.read(F.BASE / 'units' / f'{row["id"]}.json'); bank = Path(unit['bank'])
    assert C.sha(bank / 'arrays.npz') == unit['array_sha256'] and C.sha(bank / 'meta.json') == unit['meta_sha256']
    with np.load(bank / 'arrays.npz', allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    return arrays, C.read(bank / 'meta.json'), unit


def access_intervals(e0, offsets, fs):
    """Physical EEG samples read by any of the 5 windows at any anchor of a segment: [start, stop)."""
    shifts = [round(c * fs / 1000) for c in CT.CENTERS]
    lo = int(offsets.min() + min(shifts) - round(PRE * fs)); hi = int(offsets.max() + max(shifts) + round(POST * fs))
    return np.stack([e0 + lo, e0 + hi], 1)


def overlaps(a, b):
    if not len(a) or not len(b):
        return False
    a = a[np.argsort(a[:, 0])]
    for s, t in b:
        k = np.searchsorted(a[:, 0], t)
        if k and a[:k, 1].max() > s:
            return True
    return False


def analyse(row):
    t0 = time.time()
    A, meta, unit = load(row)
    nt = int(meta['n_anchors_per_segment']); offsets = A['anchor_offsets']
    seg_side, seg_role, seg_person = A['side'], A['role'], A['person']
    side, role, person = np.repeat(seg_side, nt), np.repeat(seg_role, nt), np.repeat(seg_person, nt)
    segment = np.repeat(np.arange(len(seg_side)), nt)
    audio = (A['s0'][:, None] + offsets[None]).reshape(-1)
    env = A['env'].reshape(-1); lags = A['env_history'].reshape(-1, A['env_history'].shape[-1])
    src_fit = (side == 'source') & (role == 'fit'); src_es = (side == 'source') & (role == 'es')
    _, first = np.unique(audio[src_fit], return_index=True)
    coord_values = env[src_fit][first]
    mu, sd = float(coord_values.mean()), float(coord_values.std())
    y = (env - mu) / sd
    Hd = np.column_stack([np.ones(len(y)), (lags - mu) / sd])
    X = {c: A[f'model_{c}'].reshape(-1, A[f'model_{c}'].shape[-1]).astype(np.float64) for c in CT.CENTERS}
    source_people = sorted(set(seg_person[seg_side == 'source'].tolist()))
    folds = readout_folds(source_people, row['seed'])
    fold_of = np.array([folds.get(p, -1) for p in person])
    oof = np.zeros(len(y), bool); oof_offset = np.full(len(y), np.nan); oof_scores = np.full((len(y), len(CT.CENTERS)), np.nan)
    fold_records = []
    for f in range(READOUT_FOLDS):
        train = (side == 'source') & (fold_of != f); held = src_es & (fold_of == f)
        fit, es = train & (role == 'fit'), train & (role == 'es')
        h = ols(Hd[fit], y[fit]); r = y - Hd @ h
        rec = {'fold': f, 'train_people': sorted(p for p, k in folds.items() if k != f),
               'heldout_people': sorted(p for p, k in folds.items() if k == f), 'history_coef': h.tolist(), 'probes': {}}
        for k, c in enumerate(CT.CENTERS):
            m, sel = probe(X[c], r, fit, es)
            oof_scores[held, k] = ridge_apply(m, X[c][held]); rec['probes'][str(c)] = sel
        oof_offset[held] = Hd[held] @ h; oof |= held
        fold_records.append(rec)
    assert oof.sum() == src_es.sum() and np.isfinite(oof_scores[oof]).all()
    s_mean, s_sd = oof_scores[oof].mean(0), oof_scores[oof].std(0)
    assert (s_sd > 0).all()
    Z_oof = (oof_scores[oof] - s_mean) / s_sd
    a0 = np.linalg.lstsq(Z_oof, y[oof] - oof_offset[oof], rcond=None)[0]
    basis = N.build_time_basis(a0=a0, source_scores=Z_oof, source_history_design=Hd[oof])
    # Final source refit on every legal source person.
    h_full = ols(Hd[src_fit], y[src_fit]); r_full = y - Hd @ h_full
    offset = Hd @ h_full
    scores = np.zeros((len(y), len(CT.CENTERS))); final_probes = {}
    for k, c in enumerate(CT.CENTERS):
        m, sel = probe(X[c], r_full, src_fit, src_es)
        scores[:, k] = ridge_apply(m, X[c]); final_probes[str(c)] = sel
    Z = (scores - s_mean) / s_sd
    source_record = {'coordinate': {'mean': mu, 'sd': sd, 'n_unique_audio_positions': int(len(first)),
                                    'rule': 'unique audio positions of source role=fit segments, 8 fixed anchors'},
                     'readout_folds': folds, 'fold_fits': fold_records, 'n_oof_rows': int(oof.sum()),
                     'oof_score_mean': s_mean.tolist(), 'oof_score_sd': s_sd.tolist(), 'a0': a0.tolist(),
                     'time_basis': basis.as_dict(), 'final_history_coef': h_full.tolist(), 'final_probes': final_probes,
                     'oof_source_mse': {'H0': float(np.mean((y[oof] - oof_offset[oof]) ** 2)),
                                        'E0': float(np.mean((y[oof] - oof_offset[oof] - Z_oof @ a0) ** 2))}}
    source_record['a0_and_basis_sha256'] = C.digest({'a0': source_record['a0'], 'basis': source_record['time_basis'],
                                                     'scaler': [source_record['oof_score_mean'], source_record['oof_score_sd']]}, 64)
    fs = meta['fs']; e0 = A['e0']
    people = {}
    for p in sorted(set(seg_person[seg_side == 'target'].tolist())):
        segs_fit = np.flatnonzero((seg_side == 'target') & (seg_person == p) & (seg_role == 'fit'))
        segs_q = np.flatnonzero((seg_side == 'target') & (seg_person == p) & (seg_role == 'test'))
        segs_fit = segs_fit[np.argsort(e0[segs_fit])]; segs_q = segs_q[np.argsort(e0[segs_q])]
        n_sup = math.ceil(SUPPORT_FRACTION * len(segs_fit)); sup = segs_fit[:n_sup]
        res = {'group': meta['groups'][p], 'person_fold': meta['target_person_fold'].get(p),
               'n_fit_segments_available': int(len(segs_fit)), 'support_segments': int(len(sup)),
               'support_anchors': int(len(sup) * nt), 'support_seconds_of_eeg': float(len(sup) * 5.0),
               'support_fraction_of_fit_segments': float(len(sup) / len(segs_fit)) if len(segs_fit) else None,
               'support_codes': sorted(set(A['code'][sup].tolist())), 'query_segments': int(len(segs_q)),
               'query_anchors': int(len(segs_q) * nt)}
        assert len(segs_q), p
        qa = access_intervals(e0[segs_q], offsets, fs); sa = access_intervals(e0[sup], offsets, fs)
        assert not overlaps(qa, sa), 'support and query EEG access overlap'
        assert not set(A['uid'][sup].tolist()) & set(A['uid'][segs_q].tolist()), 'support/query sound content overlap'
        qrows = np.concatenate([np.arange(s * nt, (s + 1) * nt) for s in segs_q])
        res['query_set_id'] = C.digest(A['uid'][segs_q].tolist() + [p], 64)
        res['support_set_id'] = C.digest(A['uid'][sup].tolist() + [p], 64)
        Hq, Zq, oq, yq = Hd[qrows], Z[qrows], offset[qrows], y[qrows]
        e0_pred = oq + Zq @ a0
        res['risk_E0_shared_only'] = float(np.mean((yq - e0_pred) ** 2))
        res['risk_H0'] = float(np.mean((yq - oq) ** 2))
        if len(segs_q) >= 2:
            Zm = Zq.reshape(len(segs_q), nt, -1)[np.roll(np.arange(len(segs_q)), 1)].reshape(len(qrows), -1)
            res['M0'] = {'risk_M0': float(np.mean((yq - oq - Zm @ a0) ** 2)),
                         'M0_minus_E0': float(np.mean((yq - oq - Zm @ a0) ** 2) - res['risk_E0_shared_only']),
                         'rule': 'query segments in physical order, scores rolled by one whole segment, fixed E0'}
        else:
            res['M0'] = {'status': 'not_estimable_fewer_than_2_query_segments'}
        if not len(sup):
            res['status'] = 'not_estimable_no_legal_support'; people[p] = res; continue
        srows = np.concatenate([np.arange(s * nt, (s + 1) * nt) for s in sup])
        try:
            fit = N.fit_nested_readout(family='gaussian', support_offset=offset[srows], support_history=Hd[srows],
                                       support_scores=Z[srows], support_y=y[srows], a0=a0, time_basis=basis,
                                       ridge_history=RIDGE['history'], ridge_scale=RIDGE['scale'], ridge_time=RIDGE['time'])
        except N.FitFailure as exc:
            res.update(status='fit_failure', error=str(exc)[:2000]); people[p] = res; continue
        ev = N.evaluate_readout(fit=fit, query_offset=oq, query_history=Hq, query_scores=Zq, query_y=yq)
        assert abs(ev['risk']['E0'] - res['risk_E0_shared_only']) < 1e-9 and abs(ev['risk']['H0'] - res['risk_H0']) < 1e-9
        pred = fit.predict(offset=oq, history_design=Hq, scores=Zq)
        resid = yq - oq
        res['residual_pearson_r'] = {s: (float(np.corrcoef(resid, pred[s] - oq)[0, 1]) if np.std(pred[s] - oq) > 0 else None)
                                     for s in ('E0', 'HP', 'EC', 'ET')}
        res.update(status='complete', evaluation=ev, fit=fit.as_dict())
        people[p] = res
    return {'status': 'complete', 'row': row, 'bank_unit': unit, 'plan_sha256': C.sha(F.PLAN), 'sources': sources(),
            'analysis_origin': C.ORIGIN, 'family': 'gaussian', 'ridge': RIDGE, 'support_rule': 'first ceil(0.3 n) role=fit segments, physical order',
            'query_rule': 'all role=test segments', 'source_readout': source_record, 'people': people,
            'seconds': round(time.time() - t0, 1), 'job': os.environ.get('SLURM_JOB_ID')}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--bank', action='append'); ap.add_argument('--all-ready', action='store_true')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    plan = C.read(F.PLAN)
    rows = [r for r in plan['rows'] if (a.all_ready or r['id'] in (a.bank or []))]
    for row in rows:
        out = BASE / 'units' / f'{row["id"]}.json'
        if out.exists() or not (F.BASE / 'units' / f'{row["id"]}.json').exists():
            continue
        try:
            C.write(out, analyse(row))
            print(row['id'], 'readout complete', flush=True)
        except Exception:
            C.write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'traceback': traceback.format_exc(), 'job': os.environ.get('SLURM_JOB_ID')})
            raise


if __name__ == '__main__':
    main()
