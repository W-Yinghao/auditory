"""DEP12 Agent P: private U0 use (03 §5.1), strict other-block twin, and the private δ profile (03 §4.4) per encoder (CPU).

Per encoder x outer fold f (features from private_fleet unit; binding_v1 definitions):
- q0 = hc.q0_table(outer-training children) (labels + pre-QC since-last-deviant bins of those children only).
- Source rows = the outer-training children's source-ES rows. B1: logit p = logit q0(H) + b (history_interface.fit_intercept).
  EEG: logit p = logit q0(H) + b_E + w^T z, z = standardised PCA64 scores (mu/sd on the same rows), history_interface.fit_offset
  (sum NLL + 0.5 |w|^2, intercept free). auditory_c3/c3dl/hc.py::fit_b1 is NOT used (it contains EEG evidence).
- Query: 'all_trials' (primary) and 'contract_query' of each outer-test child. G = mean log2 p_E(y) - log2 p_B1(y) bits/trial,
  probabilities clipped to [1e-6, 1-1e-6] (clipped fraction reported); AUC of p_E and of p_B1.
- Strict twin (history_interface rule): readouts refitted on the source-ES rows that have a same-child / same-history-bin /
  other-block / non-self ES partner; twin readout on the partners' features with the same labels/offsets/scaler; query = the
  test child's rows with a partner among all its rows. Reports subset E-B1, E-twin, twin-B1 and the full-query G beside it.
- δ profile: σ_u = calibrate_grouped_overlap_sigma over the outer-training children's n128 panels (scope
  target_train_unlabelled); per test child raw / null / excess CS of U vs the current label (δ kernel) with the frozen profile
  maps. Sensitivity (B0 and *@3401 encoders): n32 / n64 at σ x 1 and σ x 0.5 / 2 at n128.
  Added (DECISIONS P17/P18): the same n128 x1 cell for the outer-training children of the fold (training-side, feeds the
  population selector), and a kernel variant on the fold PCA64 scores standardised with the training source-ES mean / SD.
Outputs: REC/use_v1/<encoder>/fold{f}.json (+ readout parameters npz, private) and the per-child rows consumed by
private_analysis. Nothing reads a test child's labels before its readout and σ are fixed.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import time

import numpy as np
from scipy.special import expit

from . import private_features as PF
from . import private_fleet as FL

BASE = PF.REC / 'use_v1'
CLIP = 1e-6
NULL_DESIGN = 'dep12_private_profile_v1: independent cyclic shift of each 32-trial run (label+history), shift in [7,25]'
SENS_MULT = (0.5, 1.0, 2.0)
read, write, sha, digest = PF.read, PF.write, PF.sha, PF.digest
LN2 = math.log(2)


def measure_module():
    from . import dependence_measure as DM
    ref = PF.PACKAGE / 'reference/dependence_measure.py'
    assert sha(DM.__file__) == sha(ref), 'dependence_measure.py is not the package reference byte copy'
    return DM


def sources():
    files = [Path(__file__), Path(PF.__file__), Path(FL.__file__), PF.ROOT / 'auditory_alignment_v3/dep12/dependence_measure.py',
             PF.ROOT / 'auditory_alignment_v3/aln35/history_interface.py', PF.ROOT / 'auditory_c3/c3dl/hc.py']
    return {str(p.relative_to(PF.ROOT)): sha(p) for p in files}


# ----------------------------------------------------------------------------------------------- shared helpers
def log2_score(p, y):
    """Clipped log2 probability of the true label, and the clipped indicator."""
    q = np.clip(p, CLIP, 1 - CLIP)
    clipped = (p < CLIP) | (p > 1 - CLIP)
    return np.where(y == 1, np.log(q), np.log1p(-q)) / LN2, clipped


def auc(y, s):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else None


def logit(p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return np.log(p) - np.log1p(-p)


class Features:
    """Fold features of one encoder unit, indexed by (child, local row)."""

    def __init__(self, bind, dest, f):
        self.z = PF.load_fold(dest, f)
        self.bind = bind
        self.off, self.n = bind.offsets()
        assert len(self.z['owner']) == self.n, 'unit was not exported on the full cohort'
        self.kpos = {int(g): i for i, g in enumerate(self.z['kernel_index'])}

    def pca(self, cid, rows=None):
        o = self.off[cid]; n = self.bind.by_id[cid]['n_trials']
        X = self.z['pca'][o:o + n].astype(np.float64)
        return X if rows is None else X[np.asarray(rows)]

    def U(self, cid, rows):
        o = self.off[cid]
        return self.z['U_kernel'][[self.kpos[o + int(r)] for r in rows]].astype(np.float64)


def unit_for(name):
    sp = next((s for s in FL.specs() if s['encoder'] == name), None)
    assert sp is not None, f'no registered unit for {name}'
    rec_path = FL.BASE / 'units' / f'{sp["id"]}.json'
    assert rec_path.exists(), f'unit not complete: {name}'
    rec = read(rec_path)
    dest = Path(sp['store'])
    for f in PF.FOLDS:
        assert sha(dest / f'fold{f}.npz') == rec['arrays_sha256'][str(f)], f'feature array changed: {name} fold {f}'
    return sp, rec, dest


def q0_for(bind, ids):
    from auditory_c3.c3dl import hc
    return hc.q0_table([{'y': bind.arr(c, 'y'), 'bin': bind.arr(c, 'bin')} for c in ids])


class Readout:
    """B1 + EEG offset logistic on given source rows {cid: local rows}."""

    def __init__(self, feats, q0, rows_by_child, twin_rows_by_child=None):
        from ..aln35 import history_interface as HI
        bind = feats.bind
        cids = list(rows_by_child)
        X = np.concatenate([feats.pca(c, rows_by_child[c]) for c in cids])
        y = np.concatenate([bind.arr(c, 'y')[rows_by_child[c]] for c in cids]).astype(np.float64)
        bins = np.concatenate([bind.arr(c, 'bin')[rows_by_child[c]] for c in cids])
        off = logit(q0[bins])
        self.q0 = q0
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-8
        self.w, rec_e = HI.fit_offset((X - self.mu) / self.sd, y, off)
        self.b1, rec_b = HI.fit_intercept(y, off)
        self.w_twin = None; rec_t = None
        if twin_rows_by_child is not None:
            Xt = np.concatenate([feats.pca(c, twin_rows_by_child[c]) for c in cids])
            self.w_twin, rec_t = HI.fit_offset((Xt - self.mu) / self.sd, y, off)
        self.receipt = {'n_source_rows': int(len(y)), 'class_counts': [int((y == 0).sum()), int((y == 1).sum())],
                        'source_row_sha256': digest({c: np.asarray(rows_by_child[c]).tolist() for c in cids}),
                        'fits': {'EEG': rec_e[-1], 'B1': rec_b, 'twin': rec_t[-1] if rec_t else None},
                        'retries': {'EEG': len(rec_e) - 1, 'twin': (len(rec_t) - 1) if rec_t else None}}

    def logits(self, feats, cid, rows, rows_x=None, twin=False):
        bind = feats.bind
        off = logit(self.q0[bind.arr(cid, 'bin')[rows]])
        X = feats.pca(cid, rows if rows_x is None else rows_x)
        w = self.w_twin if twin else self.w
        return {'EEG': off + np.column_stack([np.ones(len(X)), (X - self.mu) / self.sd]) @ w, 'B1': off + self.b1}

    def params(self):
        return {'mu': self.mu, 'sd': self.sd, 'w': self.w, 'b1': np.array([self.b1]), 'q0': self.q0,
                'w_twin': self.w_twin if self.w_twin is not None else np.zeros(0)}


def g_metrics(lE, lB, y, prefix=''):
    pE, pB = expit(lE), expit(lB)
    sE, cE = log2_score(pE, y); sB, cB = log2_score(pB, y)
    return {prefix + 'G_bits': float((sE - sB).mean()), prefix + 'logscore_E': float(sE.mean()), prefix + 'logscore_B1': float(sB.mean()),
            prefix + 'auc_E': auc(y, lE), prefix + 'auc_B1': auc(y, lB), prefix + 'auc_EEG_part': auc(y, lE - lB), prefix + 'n': int(len(y)),
            prefix + 'clipped_fraction_E': float(cE.mean()), prefix + 'clipped_fraction_B1': float(cB.mean())}


# ----------------------------------------------------------------------------------------------- U0 + twin
def u0_fold(bind, feats, f):
    train, test = bind.train_ids(f), bind.test_ids(f)
    q0 = q0_for(bind, train)
    es_rows = {c: np.flatnonzero(bind.arr(c, 'es_mask')) for c in train}
    full = Readout(feats, q0, es_rows)
    tw = {c: bind.arr(c, 'twin_source_es') for c in train}
    el = {c: es_rows[c][tw[c][es_rows[c]] >= 0] for c in train}
    strict = Readout(feats, q0, el, {c: tw[c][el[c]] for c in train})
    out, logits_store = {}, {}
    for c in test:
        y = bind.arr(c, 'y'); n = len(y)
        rec = {'child': c, 'outer_fold': f, 'group': bind.by_id[c]['group'], 'protocol': bind.by_id[c]['protocol'], 'n_trials': n}
        allr = np.arange(n); L = full.logits(feats, c, allr)
        rec['all_trials'] = g_metrics(L['EEG'], L['B1'], y)
        q = bind.arr(c, 'query')
        rec['contract_query'] = g_metrics(L['EEG'][q], L['B1'][q], y[q])
        twq = bind.arr(c, 'twin_query_all'); e = np.flatnonzero(twq >= 0)
        if len(e):
            Ls = strict.logits(feats, c, e); Lt = strict.logits(feats, c, e, rows_x=twq[e], twin=True)
            sE, _ = log2_score(expit(Ls['EEG']), y[e]); sT, _ = log2_score(expit(Lt['EEG']), y[e]); sB, _ = log2_score(expit(Ls['B1']), y[e])
            sB_full, _ = log2_score(expit(L['B1'][e]), y[e]); sE_full, _ = log2_score(expit(L['EEG'][e]), y[e])
            rec['strict_twin'] = {'n_subset': int(len(e)), 'subset_fraction': len(e) / n,
                                  'E_minus_B1_bits': float((sE - sB).mean()), 'E_minus_twin_bits': float((sE - sT).mean()),
                                  'twin_minus_B1_bits': float((sT - sB).mean()), 'auc_E': auc(y[e], Ls['EEG']), 'auc_twin': auc(y[e], Lt['EEG']),
                                  'full_readout_G_on_subset_bits': float((sE_full - sB_full).mean()),
                                  'twin_pair_sha256': digest(np.c_[e, twq[e]].tolist())}
        else:
            rec['strict_twin'] = {'n_subset': 0, 'status': 'no_partner'}
        out[c] = rec
        logits_store[c] = {'EEG': L['EEG'], 'B1': L['B1']}
    receipts = {'full': full.receipt, 'strict': strict.receipt, 'q0': q0.tolist(), 'train_children': train, 'test_children': test}
    return out, receipts, full, logits_store


# ----------------------------------------------------------------------------------------------- δ profile
def panel_rows(bind, c, panel):
    runs = bind.by_id[c]['panel']['runs']
    return np.concatenate([np.asarray(runs[i]['rows']) for i in PF.NEST[panel] if i < len(runs)])


def space_rows(feats, full, space):
    """Representation rows for the δ kernel: 'U' = the frozen-layer vector (main); 'pca64' = the fold PCA64 scores
    standardised with the outer-training source-ES mean / SD (unsupervised, training side; P18)."""
    if space == 'U':
        return lambda c, rows: feats.U(c, rows)
    return lambda c, rows: (feats.pca(c, rows) - full.mu) / full.sd


def calibrate_sigma(DM, bind, X, f, name, space):
    rows = {c: X(c, panel_rows(bind, c, 'n128')) for c in bind.train_ids(f)}
    n = {c: len(v) for c, v in rows.items()}
    full = max(n.values())
    used = {c: v for c, v in rows.items() if len(v) == full}
    cal = DM.calibrate_grouped_overlap_sigma(used, calibration_scope='target_train_unlabelled',
                                             panel_id=f'dep12_private/{name}/fold{f}/{space}/n128_train_panels')
    cal['excluded_short_panels'] = sorted(set(rows) - set(used))
    cal['space'] = space
    cal.pop('person_ids', None)
    return cal


def measure_cell(DM, M, lab, perms, sigma, mult, keep_null=True):
    n = int(len(lab))
    if len(perms) == 0:
        return {'status': 'no_legal_maps', 'n': n}
    if np.allclose(M, M[:1]):
        return {'status': 'constant_representation', 'raw_cs_nats': 0.0, 'null_mean_nats': 0.0, 'excess_cs_nats': 0.0,
                'z': None, 'z_status': 'constant_representation', 'n': n}
    m = DM.measure_dependence(M, labels=lab, sigma_u=sigma * mult, permutations=perms, null_design=NULL_DESIGN)
    rec = {k: m[k] for k in ('raw_cs_nats', 'null_mean_nats', 'null_sd_nats', 'excess_cs_nats', 'z', 'z_status', 'n_null_draws',
                             'n_unique_permutations', 'joint_square', 'marginal_product_square', 'cross_overlap')}
    rec.update(n=n, sigma_u=sigma * mult, sigma_multiplier=mult, k_diagnostics=m['k_diagnostics'], l_diagnostics=m['l_diagnostics'],
               n_deviant=int(lab.sum()), status='measured', null_scores_sha256=digest([round(v, 12) for v in m['null_scores_nats']]))
    if keep_null:
        rec['null_scores_nats'] = m['null_scores_nats']
    return rec


def profile_fold(DM, bind, feats, f, name, sensitivity, full):
    """Test children: main cells (+ sensitivity) and the pca64 variant; training children: n128 x1 in both spaces (P17/P18)."""
    cals, X = {}, {}
    for space in ('U', 'pca64'):
        X[space] = space_rows(feats, full, space)
        try:
            cals[space] = calibrate_sigma(DM, bind, X[space], f, name, space)
        except ValueError as exc:
            cals[space] = {'calibration_status': 'calibration_degenerate', 'reason': str(exc), 'space': space}
    out, out_train = {}, {}
    for c in bind.ids:
        y = bind.arr(c, 'y'); test = bind.fold[c] == f
        cells = [('U', 'n128', 1.0), ('pca64', 'n128', 1.0)]
        if test and sensitivity:
            cells += [('U', 'n32', 1.0), ('U', 'n64', 1.0), ('U', 'n128', 0.5), ('U', 'n128', 2.0)]
        rec = {}
        for space, panel, mult in cells:
            key = (f'{panel}_x{mult:g}' if space == 'U' else f'pca64_{panel}_x{mult:g}')
            if 'overlap_sigma' not in cals[space]:
                rec[key] = {'status': 'calibration_degenerate'}; continue
            rows = panel_rows(bind, c, panel)
            rec[key] = measure_cell(DM, X[space](c, rows), y[rows].astype(np.int64), bind.arr(c, f'profile_maps/{panel}'),
                                    cals[space]['overlap_sigma'], mult, keep_null=test)
        (out if test else out_train)[c] = rec
    return cals, out, out_train


def sensitivity_for(name):
    return name == 'B0' or name.endswith('@3401')


# ----------------------------------------------------------------------------------------------- driver
def run_encoder(name, force=False):
    DM = measure_module()
    bind = PF.Binding()
    sp, unit, dest = unit_for(name)
    odir = BASE / name.replace('@', '_at_')
    done = odir / 'complete.json'
    if done.exists() and not force:
        print('skip complete', name, flush=True); return read(done)
    t0 = time.time(); folds = {}; preds = {}
    for f in PF.FOLDS:
        feats = Features(bind, dest, f)
        u0, receipts, full, logits_store = u0_fold(bind, feats, f)
        cals, prof, prof_train = profile_fold(DM, bind, feats, f, name, sensitivity_for(name), full)
        body = {'encoder': name, 'unit_id': sp['id'], 'unit_record_sha256': sha(FL.BASE / 'units' / f'{sp["id"]}.json'),
                'fold': f, 'binding_sha256': bind.sha256, 'u0': u0, 'readout_receipts': receipts, 'profile_calibration': cals['U'],
                'profile_calibration_pca64': cals['pca64'], 'profile': prof, 'profile_train_children': prof_train,
                'sources': sources(), 'encoder_meta': unit['encoder_meta']}
        write(odir / f'fold{f}.json', body)
        np.savez(odir / f'fold{f}_readout.npz', **full.params(),
                 **{f'logit_EEG/{c}': v['EEG'] for c, v in logits_store.items()},
                 **{f'logit_B1/{c}': v['B1'] for c, v in logits_store.items()})
        folds[str(f)] = sha(odir / f'fold{f}.json')
        for c, v in logits_store.items():
            preds[f'{c}/y'] = bind.arr(c, 'y').astype(np.int8)
            preds[f'{c}/p_E'] = expit(v['EEG']).astype(np.float32)
            preds[f'{c}/p_B1'] = expit(v['B1']).astype(np.float32)
            preds[f'{c}/outer_fold'] = np.array([f], np.int8)
        print(name, 'fold', f, 'done', round(time.time() - t0, 1), flush=True)
    pdir = PF.RESULTS / 'predictions' / 'private_u0'
    pdir.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(pdir / (name.replace('@', '_at_') + '.npz'), **preds)
    rec = {'status': 'complete', 'encoder': name, 'folds_sha256': folds, 'binding_sha256': bind.sha256, 'sources': sources(),
           'job': os.environ.get('SLURM_JOB_ID'), 'seconds': time.time() - t0, 'time': datetime.now().astimezone().isoformat()}
    write(done, rec)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--encoders', nargs='*')
    ap.add_argument('--all-ready', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    names = a.encoders or []
    if a.all_ready:
        names = [s['encoder'] for s in FL.specs() if (FL.BASE / 'units' / f'{s["id"]}.json').exists()]
    for n in names:
        run_encoder(n, force=a.force)


if __name__ == '__main__':
    main()
