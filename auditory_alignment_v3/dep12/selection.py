"""DEP12 Agent P: private U10 representation selection, four policies on identical data (03 §5.2-5.3; CPU).

Candidate set per training seed s (primary): B0, cs_pair@s, info_nce@s, sigmoid@s (B0 shared, counted once); tie order as
listed. Exploratory set 'aln41' (declared before any selection result): B0, aln41_TCS@s, aln41_TNCE@s, aln41_GCS@s.
Each candidate keeps its own U0 source readout (private_use: PCA64 + history offset logistic on the outer-training
children's source-ES rows); B1 = the history-only single intercept on the same rows.
Per outer-test child x support seed (U10 rows S from the frozen binding; common query Q = support-contract query):
1. Calibration: logit p_cal = logit p_source + c, c = argmin mean NLL + 0.1 c^2 (Newton from 0, <= 100 steps), fitted on S
   for B1 and for every candidate (and inside every CV training fold); slopes / encoders never updated.
2. fixed: the candidate with the best inner-dev score (outer-training children only; inner readouts + q0 from inner-train
   children; score = mean over inner-dev children of the mean over the 5 U10 draws of the calibrated query log2-score).
3. uniform: mean of the four calibrated query probabilities.
4. support-CV: frozen block-grouped folds of S (gap 2 s); trial-weighted validation NLL after a fold-trained offset; argmin;
   fallback fixed when the binding marks CV non-executable.
5. δ-CS: on S only, raw CS(U_S, y_S) - mean over the frozen support-only maps, δ kernel, the encoder's fold σ_u (private_use
   calibration on outer-training panels); argmax; fallback fixed for a one-class support or no movable block.
6. (added, DECISIONS P17) delta_train_profile: per fold, the candidate with the largest mean n128 δ excess over the
   outer-training children (private_use profile_train_children); same calibration.
7. (added, DECISIONS P18) delta_cs_pca64: policy 5 with the δ kernel on the fold PCA64 scores standardised by the training
   source-ES mean / SD (σ from private_use profile_calibration_pca64).
All query probabilities with the true label are written; metrics per child x training seed x support seed, then averaged
within the child.
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
from . import private_use as PU

BASE = PF.REC / 'selection_v1'
PRED = PF.RESULTS / 'predictions' / 'private_u10'
SEL_RESULTS = PF.RESULTS / 'selection'
L2C, MAX_STEPS, GRAD_TOL = 0.1, 100, 1e-12
POLICIES = ('fixed', 'uniform', 'support_cv', 'delta_cs', 'delta_train_profile', 'delta_cs_pca64')   # last two: DECISIONS P17/P18
NULL_DESIGN = 'dep12_private_support_only_v1: per-block cyclic remaps of selected U10 rows, paired distance >= 2 s'
read, write, sha, digest = PF.read, PF.write, PF.sha, PF.digest


def candidates(seed, cset='primary'):
    if cset == 'primary':
        return ['B0', f'cs_pair@{seed}', f'info_nce@{seed}', f'sigmoid@{seed}']
    if cset == 'aln41':
        return ['B0', f'aln41_TCS@{seed}', f'aln41_TNCE@{seed}', f'aln41_GCS@{seed}']
    raise ValueError(cset)


def sources():
    files = [Path(__file__), Path(PU.__file__), Path(PF.__file__), Path(FL.__file__),
             PF.ROOT / 'auditory_alignment_v3/dep12/dependence_measure.py', PF.ROOT / 'auditory_alignment_v3/aln35/history_interface.py']
    return {str(p.relative_to(PF.ROOT)): sha(p) for p in files}


def calibrate(l, y):
    """c minimising mean NLL(sigmoid(l + c), y) + 0.1 c^2; Newton, deterministic, <= 100 steps."""
    l = np.asarray(l, float); y = np.asarray(y, float); c = 0.0; steps = 0
    while steps < MAX_STEPS:
        p = expit(l + c)
        g = float(np.mean(p - y) + 2 * L2C * c)
        if abs(g) <= GRAD_TOL:
            break
        h = float(np.mean(p * (1 - p)) + 2 * L2C)
        c = c - g / h; steps += 1
        if not math.isfinite(c):
            return 0.0, {'status': 'numeric_failure', 'steps': steps}
    p = expit(l + c)
    obj = float(np.mean(np.logaddexp(0, l + c) - y * (l + c)) + L2C * c * c)
    return float(c), {'status': 'ok', 'steps': int(steps), 'grad': float(np.mean(p - y) + 2 * L2C * c), 'objective_nats': obj}


def pick(scores, order, best='max'):
    """Deterministic argmax/argmin with the declared tie order; None-valued candidates are skipped."""
    vals = [(n, scores[n]) for n in order if scores.get(n) is not None]
    if not vals:
        return None
    target = max(v for _, v in vals) if best == 'max' else min(v for _, v in vals)
    return next(n for n, v in vals if v == target)


def query_metrics(p, y):
    s, clipped = PU.log2_score(p, y)
    return {'logscore_bits': float(s.mean()), 'auc': PU.auc(y, p), 'clipped_fraction': float(clipped.mean()), 'n': int(len(y))}


class Cand:
    """One candidate encoder's fold-f source logits (U0 readout) and kernel features."""

    def __init__(self, bind, name, f):
        self.name = name
        sp, unit, dest = PU.unit_for(name)
        self.feats = PU.Features(bind, dest, f)
        odir = PU.BASE / name.replace('@', '_at_')
        done = read(odir / 'complete.json')
        assert sha(odir / f'fold{f}.json') == done['folds_sha256'][str(f)]
        fold = read(odir / f'fold{f}.json')
        assert fold['unit_id'] == sp['id']
        self.cal = fold['profile_calibration']
        self.sigma = self.cal.get('overlap_sigma')
        self.sigma_pca = fold['profile_calibration_pca64'].get('overlap_sigma')
        tp = [v['n128_x1'].get('excess_cs_nats') for v in fold['profile_train_children'].values()]
        self.train_profile = float(np.mean(tp)) if tp and all(x is not None for x in tp) else None
        self.train_profile_n = len(tp)
        with np.load(odir / f'fold{f}_readout.npz', allow_pickle=False) as z:
            self.lE = {k.split('/', 1)[1]: z[k] for k in z.files if k.startswith('logit_EEG/')}
            self.lB = {k.split('/', 1)[1]: z[k] for k in z.files if k.startswith('logit_B1/')}
            self.mu, self.sd = z['mu'], z['sd']
        self.unit_id, self.checkpoint = sp['id'], unit.get('encoder_checkpoint_sha256')

    def zpca(self, c, rows):
        return (self.feats.pca(c, rows) - self.mu) / self.sd


def inner_fixed(bind, cands, f, order):
    """Fixed policy for (training seed, outer fold f): inner-dev only, outer-training children only."""
    inner = bind.meta['inner_split'][str(f)]
    itr, idev = inner['inner_train'], inner['inner_dev']
    assert not set(idev) & set(bind.test_ids(f)) and not set(itr) & set(bind.test_ids(f))
    q0 = PU.q0_for(bind, itr)
    scores, detail = {}, {}
    for name in order:
        R = PU.Readout(cands[name].feats, q0, {c: np.flatnonzero(bind.arr(c, 'es_mask')) for c in itr})
        per_child = {}
        for c in idev:
            y = bind.arr(c, 'y'); n = len(y)
            L = R.logits(cands[name].feats, c, np.arange(n))['EEG']
            q = bind.arr(c, 'query'); vals = []
            for ss in PF.SUPPORT_SEEDS:
                S = bind.arr(c, f'U10_{ss}')
                cc, _ = calibrate(L[S], y[S])
                vals.append(query_metrics(expit(L[q] + cc), y[q])['logscore_bits'])
            per_child[c] = float(np.mean(vals))
        scores[name] = float(np.mean(list(per_child.values())))
        detail[name] = {'inner_dev_mean_logscore_bits': scores[name], 'per_child': per_child, 'readout': R.receipt}
    choice = pick(scores, order, 'max')
    return choice, {'inner_train': itr, 'inner_dev': idev, 'scores': scores, 'detail': detail, 'choice': choice,
                    'criterion': 'max mean inner-dev calibrated U10 query log2-score; ties B0>cs_pair>info_nce>sigmoid order'}


def cv_risk(bind, c, ss, L, y):
    meta = bind.by_id[c]['support'][str(ss)]['cv']
    num, den, used = 0.0, 0, 0
    j = 0
    while f'{c}/U10_{ss}/cv{j}/val' in bind.a:
        tr = bind.arr(c, f'U10_{ss}/cv{j}/train'); va = bind.arr(c, f'U10_{ss}/cv{j}/val'); j += 1
        if len(tr) == 0 or len(va) == 0:
            continue
        cc, _ = calibrate(L[tr], y[tr])
        p = np.clip(expit(L[va] + cc), PU.CLIP, 1 - PU.CLIP)
        num += float(-(y[va] * np.log(p) + (1 - y[va]) * np.log1p(-p)).sum() / math.log(2)); den += len(va); used += 1
    return (num / den if den else None), {'executes': meta['executes'], 'usable_folds': used, 'validated_rows': den}


def run_fold(DM, bind, seed, f, cset):
    order = candidates(seed, cset)
    cands = {n: Cand(bind, n, f) for n in order}
    for n in order[1:]:          # B1 logits must not depend on the encoder
        for c in cands[n].lB:
            assert np.allclose(cands[n].lB[c], cands[order[0]].lB[c], atol=1e-10), 'B1 differs across candidates'
    fixed, fixed_info = inner_fixed(bind, cands, f, order)
    tp_scores = {n: cands[n].train_profile for n in order}
    tp_choice = pick(tp_scores, order, 'max') or fixed
    fixed_info['delta_train_profile'] = {'scores': tp_scores, 'choice': tp_choice, 'n_train_children': {n: cands[n].train_profile_n for n in order},
                                         'criterion': 'max mean outer-training-children n128 x1 δ excess (main kernel); ties in candidate order'}
    children, preds = {}, {}
    for c in bind.test_ids(f):
        y = bind.arr(c, 'y'); q = bind.arr(c, 'query'); draws = {}
        P = {'y': y[q].astype(np.int8), 'rows': q.astype(np.int32)}
        for ss in PF.SUPPORT_SEEDS:
            S = bind.arr(c, f'U10_{ss}'); yS = y[S]
            lB = cands[order[0]].lB[c]
            cB, cBi = calibrate(lB[S], yS)
            pB = expit(lB[q] + cB)
            cal, pq, cand_rec = {}, {}, {}
            for n in order:
                L = cands[n].lE[c]
                cc, ci = calibrate(L[S], yS)
                pq[n] = expit(L[q] + cc)
                risk, cvi = cv_risk(bind, c, ss, L, y)
                cand_rec[n] = {'offset_c': cc, 'calibration': ci, 'cv_risk_bits': risk, 'query': query_metrics(pq[n], y[q])}
            maps = bind.arr(c, f'U10_{ss}/maps')
            one_class = len(np.unique(yS)) < 2
            for n in order:
                if one_class or len(maps) == 0 or cands[n].sigma is None:
                    cand_rec[n]['delta'] = {'status': 'one_class_support' if one_class else 'no_movable_block' if len(maps) == 0 else 'sigma_unavailable'}
                    continue
                U = cands[n].feats.U(c, S)
                if np.allclose(U, U[:1]):
                    cand_rec[n]['delta'] = {'status': 'constant_representation', 'excess_cs_nats': 0.0}; continue
                m = DM.measure_dependence(U, labels=yS.astype(np.int64), sigma_u=cands[n].sigma, permutations=maps, null_design=NULL_DESIGN)
                cand_rec[n]['delta'] = {'status': 'measured', **{k: m[k] for k in ('raw_cs_nats', 'null_mean_nats', 'null_sd_nats', 'excess_cs_nats',
                                                                                   'z', 'z_status', 'n_null_draws', 'n_unique_permutations')},
                                        'sigma_u': cands[n].sigma, 'k_offdiag_mean': m['k_diagnostics']['offdiag_mean']}
            for n in order:
                if one_class or len(maps) == 0 or cands[n].sigma_pca is None:
                    cand_rec[n]['delta_pca64'] = {'status': 'one_class_support' if one_class else 'no_movable_block' if len(maps) == 0 else 'sigma_unavailable'}
                    continue
                Z = cands[n].zpca(c, S)
                m = DM.measure_dependence(Z, labels=yS.astype(np.int64), sigma_u=cands[n].sigma_pca, permutations=maps, null_design=NULL_DESIGN)
                cand_rec[n]['delta_pca64'] = {'status': 'measured', **{k: m[k] for k in ('raw_cs_nats', 'null_mean_nats', 'null_sd_nats', 'excess_cs_nats',
                                                                                         'z', 'z_status', 'n_null_draws')},
                                              'sigma_u': cands[n].sigma_pca, 'k_offdiag_mean': m['k_diagnostics']['offdiag_mean']}
            cvmeta = bind.by_id[c]['support'][str(ss)]['cv']
            decision = {'fixed': fixed}
            if cvmeta['executes']:
                decision['support_cv'] = pick({n: cand_rec[n]['cv_risk_bits'] for n in order}, order, 'min'); cv_fb = None
            else:
                decision['support_cv'] = fixed; cv_fb = 'cv_not_executable'
            dscores = {n: cand_rec[n]['delta'].get('excess_cs_nats') for n in order}
            if one_class or len(maps) == 0 or all(v is None for v in dscores.values()):
                decision['delta_cs'] = fixed; d_fb = 'one_class_support' if one_class else 'no_movable_block' if len(maps) == 0 else 'no_delta_score'
            else:
                decision['delta_cs'] = pick(dscores, order, 'max'); d_fb = None
            pscores = {n: cand_rec[n]['delta_pca64'].get('excess_cs_nats') for n in order}
            if one_class or len(maps) == 0 or all(v is None for v in pscores.values()):
                decision['delta_cs_pca64'] = fixed; dp_fb = 'one_class_support' if one_class else 'no_movable_block' if len(maps) == 0 else 'no_delta_score'
            else:
                decision['delta_cs_pca64'] = pick(pscores, order, 'max'); dp_fb = None
            decision['delta_train_profile'] = tp_choice
            pol = {'fixed': pq[decision['fixed']], 'uniform': np.mean([pq[n] for n in order], axis=0),
                   'support_cv': pq[decision['support_cv']], 'delta_cs': pq[decision['delta_cs']],
                   'delta_train_profile': pq[decision['delta_train_profile']], 'delta_cs_pca64': pq[decision['delta_cs_pca64']]}
            sB = PU.log2_score(pB, y[q])[0]
            met = {}
            for k, p in pol.items():
                qm = query_metrics(p, y[q]); qm['G_vs_B1cal_bits'] = float((PU.log2_score(p, y[q])[0] - sB).mean()); met[k] = qm
            draws[str(ss)] = {'n_support': int(len(S)), 'support_class_counts': [int((yS == 0).sum()), int((yS == 1).sum())],
                              'B1': {'offset_c': cB, 'calibration': cBi, 'query': query_metrics(pB, y[q])},
                              'candidates': cand_rec, 'decision': decision, 'fallback': {'support_cv': cv_fb, 'delta_cs': d_fb, 'delta_cs_pca64': dp_fb,
                                                                                      'delta_train_profile': None if tp_scores.get(tp_choice) is not None else 'no_train_profile'},
                              'cv_coverage': cvmeta, 'delta_maps': bind.by_id[c]['support'][str(ss)]['delta_maps'], 'policies': met}
            P[f'B1cal/{ss}'] = pB.astype(np.float32)
            for n in order:
                P[f'{n}/{ss}'] = pq[n].astype(np.float32)
            for k, p in pol.items():
                P[f'policy:{k}/{ss}'] = p.astype(np.float32)
        mean = {}
        for k in POLICIES:
            for m_ in ('logscore_bits', 'G_vs_B1cal_bits', 'auc', 'clipped_fraction'):
                vals = [draws[str(ss)]['policies'][k][m_] for ss in PF.SUPPORT_SEEDS]
                mean.setdefault(k, {})[m_] = float(np.mean(vals)) if all(v is not None for v in vals) else None
        for n in order:
            vals = [draws[str(ss)]['candidates'][n]['query']['logscore_bits'] for ss in PF.SUPPORT_SEEDS]
            mean.setdefault('candidate:' + n, {})['logscore_bits'] = float(np.mean(vals))
        mean['B1cal'] = {'logscore_bits': float(np.mean([draws[str(ss)]['B1']['query']['logscore_bits'] for ss in PF.SUPPORT_SEEDS]))}
        children[c] = {'child': c, 'outer_fold': f, 'group': bind.by_id[c]['group'], 'protocol': bind.by_id[c]['protocol'],
                       'n_query': int(len(q)), 'query_sha256': digest(q.tolist()), 'draws': draws, 'child_mean_over_support_seeds': mean}
        preds[c] = P
    return {'fixed': fixed_info, 'children': children,
            'candidates': {n: {'unit_id': cands[n].unit_id, 'checkpoint_sha256': cands[n].checkpoint, 'sigma_u': cands[n].sigma,
                               'sigma_u_pca64': cands[n].sigma_pca, 'train_profile_excess_nats': cands[n].train_profile} for n in order}}, preds


def run(seed, cset='primary', force=False):
    DM = PU.measure_module(); bind = PF.Binding()
    tag = f'{cset}_s{seed}'
    out = BASE / tag
    if (out / 'complete.json').exists() and not force:
        print('skip complete', tag, flush=True); return
    t0 = time.time(); shas = {}; table = []
    for f in PF.FOLDS:
        res, preds = run_fold(DM, bind, seed, f, cset)
        body = {'tag': tag, 'seed': seed, 'candidate_set': cset, 'order': candidates(seed, cset), 'fold': f, 'binding_sha256': bind.sha256,
                'sources': sources(), **res}
        write(out / f'fold{f}.json', body); shas[str(f)] = sha(out / f'fold{f}.json')
        for c, ch in res['children'].items():
            for ss, d in ch['draws'].items():
                table.append({'tag': tag, 'train_seed': seed, 'candidate_set': cset, 'outer_fold': f, 'participant_id': c, 'support_seed': int(ss),
                              'group': ch['group'], 'protocol': ch['protocol'], 'query_sha256': ch['query_sha256'], 'n_query': ch['n_query'],
                              'n_support': d['n_support'], 'support_class_counts': d['support_class_counts'], 'decision': d['decision'],
                              'fallback': d['fallback'], 'fixed_inner_dev_scores': res['fixed']['scores'], 'train_profile_scores': res['fixed']['delta_train_profile']['scores'],
                              'cv_coverage': {k: d['cv_coverage'][k] for k in ('mode', 'n_groups', 'n_usable_folds', 'executes', 'validated_fraction')},
                              'delta_maps': d['delta_maps'],
                              'candidates': {n: {'offset_c': r['offset_c'], 'cv_risk_bits': r['cv_risk_bits'], 'query_logscore_bits': r['query']['logscore_bits'],
                                                 'query_auc': r['query']['auc'], 'delta': {k: r['delta'].get(k) for k in ('status', 'raw_cs_nats', 'null_mean_nats',
                                                                                                                      'null_sd_nats', 'excess_cs_nats', 'z', 'z_status',
                                                                                                                      'n_null_draws')},
                                                 'delta_pca64': {k: r['delta_pca64'].get(k) for k in ('status', 'raw_cs_nats', 'null_mean_nats', 'excess_cs_nats', 'z_status')}}
                                             for n, r in d['candidates'].items()},
                              'B1cal_query_logscore_bits': d['B1']['query']['logscore_bits'], 'policies': d['policies']})
        PRED.mkdir(parents=True, exist_ok=True, mode=0o700)
        np.savez_compressed(PRED / f'{tag}_fold{f}.npz', **{f'{c}/{k}': v for c, P in preds.items() for k, v in P.items()})
        print(tag, 'fold', f, round(time.time() - t0, 1), flush=True)
    SEL_RESULTS.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(SEL_RESULTS / f'private_u10_{tag}.jsonl', 'w') as fh:
        for r in table:
            fh.write(json.dumps(r, sort_keys=True, allow_nan=False) + '\n')
    write(out / 'complete.json', {'status': 'complete', 'tag': tag, 'folds_sha256': shas, 'binding_sha256': bind.sha256, 'sources': sources(),
                                  'job': os.environ.get('SLURM_JOB_ID'), 'seconds': time.time() - t0,
                                  'time': datetime.now().astimezone().isoformat()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', nargs='*', type=int, default=[3401, 3407, 3413])
    ap.add_argument('--set', default='primary', choices=('primary', 'aln41'))
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    for s in a.seeds:
        run(s, a.set, a.force)


if __name__ == '__main__':
    main()
