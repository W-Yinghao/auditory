"""ALN3.6 R1 private readout (CPU): history-controlled current-sound evidence, personal calibration and timing.

Per bundle (matched AP or APwrong target, one outer child fold; optional existing S):
  source      children with fold != outer fold; ES rows = their last ~20% physical blocks (training-time ES).
  H0          logit q0[history bin] (6-bin since-last-deviant table over the source children's trials, (k+.5)/(n+1))
              + one source-ES intercept (history_interface.fit_intercept).
  probes      per input-mask window (0-200, 200-400, 400-600 ms nominal), history_interface.fit_offset on the
              standardised 32-d frozen features of source-ES rows with the H0 offset (sum NLL + 0.5|slopes|^2);
              score = intercept + slopes . z (source logit evidence beyond H0).
  cross-fit   3 source-child folds (sha256 of seed|child); OOF offset/scores on held-out children's ES rows.
  a0, Z       OOF score scaler frozen; a0 = maximum-likelihood logistic coefficients of y on scaled OOF scores with the
              OOF offset (no intercept); TemporalBasis on OOF rows with history design [1, 5 standardised bin dummies].
  final       H0 and probes refitted on all source children; target rows use the frozen OOF scaler, a0 and basis.
Target child: support/query = support_contract.private_split (first ceil(0.3 blocks) blocks, support[:-1], query[1:],
full-epoch guard), all trials available (outer child). Strict twin: same child, same bin, other block, non-self; support
partners only within support and query partners only within query (history_interface.strict_twin_map; fixed seeds).
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
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.metrics import roc_auc_score

from ..aln34 import prior_science as PS
from ..aln35 import history_interface as HI, support_contract as SC
from . import common as C
from . import nested as N
from . import private_features as PF

BASE = C.OUT / 'private_readout_v1'
WINDOWS = ('0_200', '200_400', '400_600')
RIDGE = {'history': 1.0, 'scale': 1.0, 'time': 1.0}
READOUT_FOLDS = 3
N_BINS = 6
TWIN_SEED = 361819


def sources():
    files = [Path(__file__), Path(C.__file__), Path(N.__file__), Path(PF.__file__), Path(HI.__file__), Path(SC.__file__)]
    return {str(p.relative_to(C.REPO)): C.sha(p) for p in sorted(set(files))}


def q0_table(kids):
    y = np.concatenate([k['y'] for k in kids]); b = np.concatenate([k['bin'] for k in kids])
    return np.array([(y[b == h].sum() + 0.5) / ((b == h).sum() + 1.0) for h in range(N_BINS)])


def logit(p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return np.log(p) - np.log1p(-p)


def child_seed(child, salt):
    return TWIN_SEED + int(hashlib.sha256(f'{salt}|{child}'.encode()).hexdigest()[:8], 16)


def fit_a0(Z, y, offset):
    def f(a):
        z = offset + Z @ a
        return float(np.sum(np.logaddexp(0, z) - y * z)), Z.T @ (expit(z) - y)
    res = minimize(f, np.zeros(Z.shape[1]), jac=True, method='L-BFGS-B', options={'maxiter': 5000, 'ftol': 1e-15, 'gtol': 1e-10})
    value, grad = f(res.x)
    per = float(np.max(np.abs(grad)) / len(y))
    assert res.success and np.isfinite(res.x).all() and per <= 1e-7, (res.message, per)
    return res.x, {'objective': value, 'gradient_maxabs_per_row': per, 'iterations': int(res.nit),
                   'definition': 'unpenalised logistic MLE of y on scaled OOF scores with the OOF H0 offset, no intercept'}


def load_bank(row, kids):
    if row['kind'] == 'matched_target':
        unit = C.read(PF.BASE / 'units' / f'{row["id"]}.json'); bank = Path(unit['bank'])
        assert C.sha(bank / 'arrays.npz') == unit['array_sha256'] and C.sha(bank / 'meta.json') == unit['meta_sha256']
        meta = C.read(bank / 'meta.json')
    else:
        bank = PS.STORE / 'cache' / row['prior_science_unit']
        assert C.sha(bank / 'meta.json') == row['cache_meta_sha256']
        meta = C.read(bank / 'meta.json'); assert C.sha(bank / 'arrays.npz') == meta['array_sha256'] == row['array_sha256']
    assert meta['children'] == {str(i): k['id'] for i, k in enumerate(kids)}, 'child order differs from the extraction'
    with np.load(bank / 'arrays.npz', allow_pickle=False) as z:
        U = {w: [z[f'{w}_{i}'].astype(np.float64) for i in range(len(kids))] for w in WINDOWS}
    for w in WINDOWS:
        assert all(U[w][i].shape == (len(k['y']), 32) for i, k in enumerate(kids))
    return U, meta


def design_history(kids, source, mean=None, sd=None):
    dummies = [np.stack([(k['bin'] == h).astype(float) for h in range(1, N_BINS)], 1) for k in kids]
    if mean is None:
        allsrc = np.concatenate([dummies[i] for i in source])
        mean, sd = allsrc.mean(0), allsrc.std(0); sd[sd == 0] = 1.0
    return [np.column_stack([np.ones(len(d)), (d - mean) / sd]) for d in dummies], mean, sd


def source_readout(kids, U, source, folds):
    """H0 offset parameters and probe parameters on a set of source children (ES rows)."""
    q0 = q0_table([kids[i] for i in source])
    es = {i: np.flatnonzero(kids[i]['es_mask']) for i in source}
    y = np.concatenate([kids[i]['y'][es[i]] for i in source])
    off_q = np.concatenate([logit(q0[kids[i]['bin'][es[i]]]) for i in source])
    b1, b1_receipt = HI.fit_intercept(y, off_q)
    off = off_q + b1
    probes = {}
    for w in WINDOWS:
        x = np.concatenate([U[w][i][es[i]] for i in source]); mu, sd = x.mean(0), x.std(0) + 1e-8
        coef, receipts = HI.fit_offset((x - mu) / sd, y, off)
        probes[w] = {'mu': mu, 'sd': sd, 'coef': coef, 'receipts': receipts}
    return {'q0': q0, 'b1': b1, 'b1_receipt': b1_receipt, 'probes': probes, 'n_es_rows': int(len(y)),
            'es_class_counts': {'0': int((y == 0).sum()), '1': int((y == 1).sum())}}


def apply_readout(sr, kid, Uk, rows):
    offset = logit(sr['q0'][kid['bin'][rows]]) + sr['b1']
    scores = np.column_stack([np.column_stack([np.ones(len(rows)), (Uk[w][rows] - sr['probes'][w]['mu']) / sr['probes'][w]['sd']])
                              @ sr['probes'][w]['coef'] for w in WINDOWS])
    return offset, scores


def counts(kid, rows):
    return {'trials': int(len(rows)), 'blocks': int(len(set(kid['block'][rows].tolist()))),
            'class': {str(c): int((kid['y'][rows] == c).sum()) for c in (0, 1)},
            'history': {str(h): int((kid['bin'][rows] == h).sum()) for h in range(N_BINS)}}


def aux_metrics(fit, offset, H, Z, y):
    pred = fit.predict(offset=offset, history_design=H, scores=Z)
    out = {}
    for s, p in pred.items():
        out[s] = {'auc': float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None, 'brier': float(np.mean((p - y) ** 2))}
    return out


def analyse(row, kids):
    t0 = time.time()
    U, meta = load_bank(row, kids)
    sf = row['person_fold']
    source = [i for i, k in enumerate(kids) if k['fold'] != sf]; target = [i for i, k in enumerate(kids) if k['fold'] == sf]
    assert len(source) + len(target) == 64 and target
    order = sorted(source, key=lambda i: hashlib.sha256(f'{row["seed"]}|{kids[i]["id"]}'.encode()).hexdigest())
    rfold = {i: n % READOUT_FOLDS for n, i in enumerate(order)}
    Hd, hmean, hsd = design_history(kids, source)
    oof_off, oof_scores, oof_y, oof_H, fold_records = [], [], [], [], []
    for f in range(READOUT_FOLDS):
        train = [i for i in source if rfold[i] != f]; held = [i for i in source if rfold[i] == f]
        sr = source_readout(kids, U, train, None)
        for i in held:
            rows = np.flatnonzero(kids[i]['es_mask'])
            o, s = apply_readout(sr, kids[i], {w: U[w][i] for w in WINDOWS}, rows)
            oof_off.append(o); oof_scores.append(s); oof_y.append(kids[i]['y'][rows]); oof_H.append(Hd[i][rows])
        fold_records.append({'fold': f, 'train_children': [kids[i]['id'] for i in train], 'heldout_children': [kids[i]['id'] for i in held],
                             'q0': sr['q0'].tolist(), 'b1': sr['b1'], 'n_es_rows': sr['n_es_rows'],
                             'probe_receipts': {w: sr['probes'][w]['receipts'] for w in WINDOWS}})
    oof_off, oof_scores, oof_y, oof_H = map(np.concatenate, (oof_off, oof_scores, oof_y, oof_H))
    s_mean, s_sd = oof_scores.mean(0), oof_scores.std(0); assert (s_sd > 0).all()
    Z_oof = (oof_scores - s_mean) / s_sd
    a0, a0_receipt = fit_a0(Z_oof, oof_y.astype(float), oof_off)
    basis = N.build_time_basis(a0=a0, source_scores=Z_oof, source_history_design=oof_H)
    final = source_readout(kids, U, source, None)
    source_record = {'readout_folds': {kids[i]['id']: rfold[i] for i in source}, 'fold_fits': fold_records,
                     'n_oof_rows': int(len(oof_y)), 'oof_score_mean': s_mean.tolist(), 'oof_score_sd': s_sd.tolist(),
                     'a0': a0.tolist(), 'a0_receipt': a0_receipt, 'time_basis': basis.as_dict(),
                     'history_design_mean': hmean.tolist(), 'history_design_sd': hsd.tolist(),
                     'final': {'q0': final['q0'].tolist(), 'b1': final['b1'], 'b1_receipt': final['b1_receipt'],
                               'n_es_rows': final['n_es_rows'], 'es_class_counts': final['es_class_counts'],
                               'probes': {w: {'mu': final['probes'][w]['mu'].tolist(), 'sd': final['probes'][w]['sd'].tolist(),
                                              'coef': final['probes'][w]['coef'].tolist(), 'receipts': final['probes'][w]['receipts']}
                                          for w in WINDOWS}},
                     'oof_source_bits': {'H0': float(np.mean(np.logaddexp(0, oof_off) - oof_y * oof_off) / math.log(2)),
                                         'E0': float(np.mean(np.logaddexp(0, oof_off + Z_oof @ a0) - oof_y * (oof_off + Z_oof @ a0)) / math.log(2))}}
    source_record['a0_and_basis_sha256'] = C.digest({'a0': source_record['a0'], 'basis': source_record['time_basis'],
                                                     'scaler': [source_record['oof_score_mean'], source_record['oof_score_sd']]}, 64)
    people = {}
    for i in target:
        k = kids[i]; Uk = {w: U[w][i] for w in WINDOWS}
        split = SC.private_split(k, fit_only=False)
        p, q = np.asarray(split['pool']), np.asarray(split['query'])
        res = {'group': k['group'], 'person_fold': sf, 'support_counts': counts(k, p), 'query_counts': counts(k, q),
               'support_fraction_of_trials': float(len(p) / len(k['y'])), 'split_guard': split['guard'],
               'support_set_id': C.digest([k['id'], np.round(k['_s35_onset_seconds'][p], 4).tolist()], 64),
               'query_set_id': C.digest([k['id'], np.round(k['_s35_onset_seconds'][q], 4).tolist()], 64)}
        if not len(q):
            res['status'] = 'not_estimable_no_query'; people[k['id']] = res; continue
        off_all, s_all = apply_readout(final, k, Uk, np.arange(len(k['y'])))
        Z_all = (s_all - s_mean) / s_sd; H_all = Hd[i]; y_all = k['y'].astype(float)
        bits = lambda eta, rows: float(np.mean(np.logaddexp(0, eta) - y_all[rows] * eta) / math.log(2))
        res['risk_H0'] = bits(off_all[q], q); res['risk_E0'] = bits(off_all[q] + Z_all[q] @ a0, q)
        twin_s = HI.strict_twin_map(k['bin'], k['block'], p, child_seed(k['id'], 'support')) if len(p) else np.full(len(k['y']), -1)
        twin_q = HI.strict_twin_map(k['bin'], k['block'], q, child_seed(k['id'], 'query'))
        s_int = p[twin_s[p] >= 0] if len(p) else p; q_int = q[twin_q[q] >= 0]
        assert np.all(np.isin(twin_s[s_int], p)) and np.all(np.isin(twin_q[q_int], q))
        res['twin'] = {'support_eligible': int(len(s_int)), 'query_eligible': int(len(q_int)),
                       'twin_map_sha256': C.digest([twin_s.tolist(), twin_q.tolist()], 64),
                       'query_intersection_id': C.digest([k['id'], np.round(k['_s35_onset_seconds'][q_int], 4).tolist()], 64)}
        if len(q_int):
            res['twin']['E0_real'] = bits(off_all[q_int] + Z_all[q_int] @ a0, q_int)
            res['twin']['E0_twin'] = bits(off_all[q_int] + Z_all[twin_q[q_int]] @ a0, q_int)
        else:
            res['twin']['status_query'] = 'not_estimable_no_query_partner'
        if not len(p):
            res['status'] = 'not_estimable_no_legal_support'; people[k['id']] = res; continue
        try:
            fit = N.fit_nested_readout(family='bernoulli', support_offset=off_all[p], support_history=H_all[p], support_scores=Z_all[p],
                                       support_y=y_all[p], a0=a0, time_basis=basis, ridge_history=RIDGE['history'],
                                       ridge_scale=RIDGE['scale'], ridge_time=RIDGE['time'])
        except N.FitFailure as exc:
            res.update(status='fit_failure', error=str(exc)[:2000]); people[k['id']] = res; continue
        ev = N.evaluate_readout(fit=fit, query_offset=off_all[q], query_history=H_all[q], query_scores=Z_all[q], query_y=y_all[q])
        assert abs(ev['risk']['E0'] - res['risk_E0']) < 1e-9 and abs(ev['risk']['H0'] - res['risk_H0']) < 1e-9
        res.update(status='complete', evaluation=ev, fit=fit.as_dict(),
                   auxiliary=aux_metrics(fit, off_all[q], H_all[q], Z_all[q], y_all[q]))
        if len(s_int) and len(q_int):
            controls = {}
            for name, s_rows, q_rows in (('real_control', s_int, q_int), ('twin_control', twin_s[s_int], twin_q[q_int])):
                try:
                    cf = N.fit_nested_readout(family='bernoulli', support_offset=off_all[s_int], support_history=H_all[s_int],
                                              support_scores=Z_all[s_rows], support_y=y_all[s_int], a0=a0, time_basis=basis,
                                              ridge_history=RIDGE['history'], ridge_scale=RIDGE['scale'], ridge_time=RIDGE['time'])
                    controls[name] = N.evaluate_readout(fit=cf, query_offset=off_all[q_int], query_history=H_all[q_int],
                                                        query_scores=Z_all[q_rows], query_y=y_all[q_int])
                except N.FitFailure as exc:
                    controls[name] = {'status': 'fit_failure', 'error': str(exc)[:1000]}
            res['twin']['controls'] = controls
            assert 'risk' not in controls.get('real_control', {}) or abs(controls['real_control']['risk']['E0'] - res['twin']['E0_real']) < 1e-9
        else:
            res['twin']['status_personal'] = 'not_estimable_no_support_partner' if not len(s_int) else 'not_estimable_no_query_partner'
        people[k['id']] = res
    return {'status': 'complete', 'row': row, 'bank_meta_sha256': C.digest(meta, 64), 'sources': sources(), 'analysis_origin': C.ORIGIN,
            'family': 'bernoulli', 'ridge': RIDGE, 'windows': list(WINDOWS), 'source_readout': source_record, 'people': people,
            'seconds': round(time.time() - t0, 1), 'job': os.environ.get('SLURM_JOB_ID')}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--include-s', action='store_true')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    plan = C.read(PF.PLAN); kids = PF.load_children()
    rows = plan['rows'] + (plan['optional_S'] if a.include_s else [])
    for row in rows:
        out = BASE / 'units' / f'{row["id"]}.json'
        if out.exists() or (row['kind'] == 'matched_target' and not (PF.BASE / 'units' / f'{row["id"]}.json').exists()):
            continue
        try:
            C.write(out, analyse(row, kids)); print(row['id'], row['arm'], row['person_fold'], 'readout complete', flush=True)
        except Exception:
            C.write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'traceback': traceback.format_exc(), 'job': os.environ.get('SLURM_JOB_ID')})
            raise


if __name__ == '__main__':
    main()
