"""W7 §2.2 decision rule R (CPU): CS dependence as a two-candidate attention decision rule on the stored frozen cs features.

Frozen design docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md §2.2 (sha256 DESIGN_SHA), families
results/auditory_alignment_v3/paper/w7/W7_FAMILIES_v1.json (W7_RULE:dtu / W7_RULE:fau), implementation choices frozen in
private/auditory_alignment_v3/paper/w7_v1/APPENDUM_RAD_01.md before any R output existed.

Systems: B0 (seed-free, R1 frozen unit), TCS and TNCE (seeds 3401 / 3407 / 3413; R2 seeds through aln41.r2.seeded).
Per frozen public unit (arm x seed x dataset x content fold) and pooled person fold sf:
  X = cs_pca_sf<sf> [segments, 16 anchors, 3 slots, 64]; candidate audio = cs_env_att / cs_env_ign [segments, 16] (current
  envelope, the downstream direct target; no history, F3).
  sigma_X: lower median of within-slot distinct-anchor distances pooled over the 3 slots (aln41.source.calibrate_sigmas rule) on
  <= SIGMA_ROWS anchors (fixed RNG per unit-fold) of the fold's training people's role fit / es cs segments; sigma_A: lower median of
  distinct-pair distances of the pooled attended + ignored envelope values at the same anchors (one bandwidth for both candidates).
  Segment margin m = sum_s q0_s [CS(X^s; a_att) - CS(X^s; a_ign)] over the segment's 16 anchors, CS = paper.cs_atlas estimator
  (= aln41.cs_qmi_reference.cs_qmi: uniform weights, V-statistic, natural logs); q0 = softmax(source a) (B0 uniform).
  Decision: aln42.external_eval.integrate (= aln41.readout.attention with a precomputed margin): mean evidence over 1 / 2 / 4
  consecutive segments (5 / 10 / 20 s), tau by double-order log loss on the training people's fit + es windows, ties 0.5.
Per person: content folds averaged (both required), then seeds (all three for TCS / TNCE). Reference: the stored aln41 ridge readout
(readout_v1 q0 attention records of the same units), aggregated identically.
Gates (written before the run): estimator == cs_qmi_reference on random data and on real segments; the integration path fed the
recomputed ss-trained ridge margin reproduces the stored ridge records of one unit exactly.
CLI (Slurm CPU): python -m auditory_alignment_v3.paper.w7_rule gates | run | aggregate
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

from .. import core

ROOT = Path(core.REPO)
W7 = Path(core.OUT) / 'paper' / 'w7_v1'
OUT = W7 / 'rule'
RESULTS = ROOT / 'results/auditory_alignment_v3/paper/w7'
DESIGN = ROOT / 'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md'
DESIGN_SHA = 'c4b461b0a6754af0ba04720320b0acc3f8c907a37f90369a4a250a612a92746c'
FAMILIES = RESULTS / 'W7_FAMILIES_v1.json'
FAMILIES_SHA = 'a95aa35f0f47733f9b1ad57427bd1cc477056459c6555c94cb980fb730982421'
APPENDUM = W7 / 'APPENDUM_RAD_01.md'
ARMS = {'B0': (3401,), 'TCS': (3401, 3407, 3413), 'TNCE': (3401, 3407, 3413)}
DATASETS, CFS, SFS = ('dtu', 'fau'), (0, 1), (0, 1, 2, 3, 4)
GROUPS = {'dtu': ('nh', 'hi'), 'fau': ('th', 'ha', 'ci')}
WINDOWS = ('5', '10', '20')
SIGMA_ROWS, RNG_SEED = 2000, 20261022


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def write(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + '.tmp'); tmp.write_text(json.dumps(obj, indent=1, default=float) + '\n'); os.replace(tmp, path)


def bindings():
    assert sha(DESIGN) == DESIGN_SHA and sha(FAMILIES) == FAMILIES_SHA, 'frozen W7 design / families drift'
    assert APPENDUM.exists() and not os.access(APPENDUM, os.W_OK), 'APPENDUM_RAD_01 must exist and be read-only'
    return {'design_sha256': DESIGN_SHA, 'families_sha256': FAMILIES_SHA, 'appendum_rad_01_sha256': sha(APPENDUM),
            'module_sha256': sha(__file__)}


# ----------------------------------------------------------------------------------------------- estimator
def gram_batch(X, s):
    """X [n, m, d] -> Gaussian overlap Grams [n, m, m] (cs_atlas.gram per segment)."""
    X = np.asarray(X, np.float64)
    sq = np.einsum('nmd,nmd->nm', X, X)
    D = sq[:, :, None] + sq[:, None, :] - 2.0 * np.einsum('nid,njd->nij', X, X)
    np.maximum(D, 0.0, out=D); i = np.arange(X.shape[1]); D[:, i, i] = 0.0
    return np.exp(-D / (2.0 * s * s))


def cs_batch(K, L):
    """cs_atlas.cs_value per segment: log mean(K∘L) + log[mean K mean L] - 2 log mean_i(k̄_i l̄_i)."""
    kb, lb = K.mean(2), L.mean(2)
    return np.log((K * L).mean((1, 2))) + np.log(K.mean((1, 2)) * L.mean((1, 2))) - 2.0 * np.log((kb * lb).mean(1))


def lower_median(d):
    d = np.asarray(d, np.float64).ravel(); k = (len(d) - 1) // 2
    return float(np.partition(d, k)[k])


def pdist(x):
    from scipy.spatial.distance import pdist as _p
    return _p(np.asarray(x, np.float64))


def sigmas(F, att, ign, rows_seg, key):
    """(sigma_X, sigma_A, info) from the training segments rows_seg (fixed RNG keyed by the unit-fold)."""
    nseg, m = F.shape[:2]
    anchors = (rows_seg[:, None] * m + np.arange(m)[None]).ravel()
    rng = np.random.default_rng(RNG_SEED + int(hashlib.sha256(key.encode()).hexdigest()[:8], 16))
    pick = anchors if len(anchors) <= SIGMA_ROWS else np.sort(rng.choice(anchors, SIGMA_ROWS, replace=False))
    si, ai = pick // m, pick % m
    dx = np.concatenate([pdist(F[si, ai, k]) for k in range(F.shape[2])])
    da = pdist(np.r_[att[si, ai], ign[si, ai]][:, None])
    sx, sa = lower_median(dx), lower_median(da)
    assert np.isfinite(sx) and sx > 0 and np.isfinite(sa) and sa > 0, (key, sx, sa)
    return sx, sa, {'n_anchor_rows': int(len(pick)), 'n_training_segments': int(len(rows_seg)), 'sigma_X': sx, 'sigma_A': sa}


def margins(F, att, ign, q, sx, sa, chunk=2048):
    """Segment margin sum_s q_s [CS(X^s; att) - CS(X^s; ign)] and the per-slot terms [n, 3, 2]."""
    n = len(F); out = np.zeros((n, F.shape[2], 2))
    for s0 in range(0, n, chunk):
        sl = slice(s0, min(n, s0 + chunk))
        La = np.exp(-(att[sl, :, None] - att[sl, None, :]) ** 2 / (2 * sa * sa))
        Li = np.exp(-(ign[sl, :, None] - ign[sl, None, :]) ** 2 / (2 * sa * sa))
        for k in range(F.shape[2]):
            K = gram_batch(F[sl, :, k], sx)
            out[sl, k, 0] = cs_batch(K, La); out[sl, k, 1] = cs_batch(K, Li)
    m = np.einsum('k,nk->n', np.asarray(q, np.float64), out[:, :, 0] - out[:, :, 1])
    return m, out


# ----------------------------------------------------------------------------------------------- frozen units
def frozen_unit(arm, ds, cf, seed):
    from ..aln41 import frozen as FZ, r2 as R2
    ctx = R2.seeded(seed) if seed != 3401 else contextlib.nullcontext()
    with ctx:
        plan = FZ.read(FZ.BASE / 'plan.json')
        row = next(r for r in plan['rows'] if r['arm'] == arm and r['dataset'] == ds and r['content_fold'] == cf)
        unit = FZ.read(FZ.BASE / 'units' / f'{row["id"]}.json'); assert unit['status'] == 'complete' and not unit['probe']
        ro = FZ.BASE.parent / 'readout_v1' / 'units' / f'{row["id"]}.json'
    dest = Path(unit['dest'])
    assert sha(dest / 'meta.json') == unit['meta_sha256'] and sha(dest / 'arrays.npz') == unit['array_sha256']
    return row, dest, FZ.read(dest / 'meta.json'), ro


def people_sets(meta, person, sf):
    folds, dev = meta['folds'], set(meta['dev_people'])
    train = set(meta['pca'][str(sf)]['train_people'])
    test = {p for p in set(person.tolist()) if folds.get(p) == sf and p not in dev}
    return train, test


def unit_id(arm, ds, cf, seed):
    return f'W7R_{arm}_{ds}_cf{cf}_s{seed}'


def run_unit(arm, ds, cf, seed, bind):
    from ..aln42 import external_eval as XE
    t0 = time.time(); row, dest, meta, ro = frozen_unit(arm, ds, cf, seed)
    q = np.asarray(meta['q0'], np.float64); assert q.shape == (3,) and abs(q.sum() - 1) < 1e-9
    if arm == 'B0':
        assert np.allclose(q, 1 / 3)
    z = np.load(dest / 'arrays.npz', allow_pickle=False)
    A = {k: z[k] for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role', 'cs_env_att', 'cs_env_ign', 'person')}
    att, ign = A['cs_env_att'].astype(np.float64), A['cs_env_ign'].astype(np.float64)
    seg_len = meta['cs']['seg_len']; folds = {}
    for sf in SFS:
        F = z[f'cs_pca_sf{sf}'].astype(np.float64); assert F.shape[1:] == (16, 3, 64) and len(F) == len(att)
        train, test = people_sets(meta, A['person'], sf)
        tr_seg = np.flatnonzero(np.isin(A['cs_person'], sorted(train)) & np.isin(A['cs_role'], ('fit', 'es')))
        key = f'{arm}|{seed}|{ds}|{cf}|{sf}'
        sx, sa, sinfo = sigmas(F, att, ign, tr_seg, key)
        m, slot = margins(F, att, ign, q, sx, sa)
        assert np.isfinite(m).all()
        res = XE.integrate(m, A['cs_person'], A['cs_role'], A['cs_code'], A['cs_e0'], seg_len, train, test)
        te_seg = np.isin(A['cs_person'], sorted(test)) & (A['cs_role'] == 'test')
        folds[str(sf)] = {'sigma': sinfo, 'tau': {sec: v['tau'] for sec, v in res.items()},
                          'people': {sec: v['people'] for sec, v in res.items()},
                          'test_segments': int(te_seg.sum()),
                          'margin_test_mean': float(m[te_seg].mean()) if te_seg.any() else None,
                          'cs_att_test_mean_by_slot': slot[te_seg, :, 0].mean(0).tolist() if te_seg.any() else None,
                          'cs_ign_test_mean_by_slot': slot[te_seg, :, 1].mean(0).tolist() if te_seg.any() else None}
        del F
    z.close()
    rec = {'status': 'complete', 'id': unit_id(arm, ds, cf, seed), 'arm': arm, 'dataset': ds, 'content_fold': cf, 'seed': seed,
           'frozen_unit': row['id'], 'frozen_array_sha256': sha(dest / 'arrays.npz'), 'q0': q.tolist(),
           'stored_readout': str(ro), 'stored_readout_sha256': sha(ro), 'folds': folds, 'groups': meta['groups'],
           'bindings': bind, 'seconds': time.time() - t0, 'job': os.environ.get('SLURM_JOB_ID')}
    write(OUT / 'units' / f'{rec["id"]}.json', rec)
    print(rec['id'], 'complete', round(rec['seconds'], 1), flush=True)
    return rec


# ----------------------------------------------------------------------------------------------- gates
def gates():
    """(1) estimator equality with cs_qmi_reference (random + 6 real segments); (2) the integration path fed the recomputed
    ss-trained ridge margin of B0 dtu cf0 reproduces the stored readout records (every person, window and tau)."""
    import torch
    from ..aln41.cs_qmi_reference import cs_qmi
    from ..aln41 import readout as RO
    from ..aln34 import content_time as CT
    from ..aln42 import external_eval as XE
    rng = np.random.default_rng(RNG_SEED + 7); worst = 0.0
    X = rng.normal(size=(4, 16, 64)); a = rng.normal(size=(4, 16)); sx, sa = 9.0, 0.8
    mine = cs_batch(gram_batch(X, sx), np.exp(-(a[:, :, None] - a[:, None, :]) ** 2 / (2 * sa * sa)))
    for i in range(4):
        ref = float(cs_qmi(torch.as_tensor(X[i]), torch.as_tensor(a[i][:, None]), sigma_u=sx, sigma_v=sa)[0])
        worst = max(worst, abs(ref - mine[i]))
    row, dest, meta, ro = frozen_unit('B0', 'dtu', 0, 3401)
    z = np.load(dest / 'arrays.npz', allow_pickle=False)
    A = {k: z[k] for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role', 'cs_env_att', 'cs_env_ign', 'person', 'role', 'env')}
    F = z['cs_pca_sf0'].astype(np.float64); att, ign = A['cs_env_att'], A['cs_env_ign']
    train, test = people_sets(meta, A['person'], 0)
    tr_seg = np.flatnonzero(np.isin(A['cs_person'], sorted(train)) & np.isin(A['cs_role'], ('fit', 'es')))
    sx, sa, _ = sigmas(F, att, ign, tr_seg, 'gate')
    pick = tr_seg[:6]; _, slot = margins(F[pick], att[pick], ign[pick], np.full(3, 1 / 3), sx, sa)
    for j, i in enumerate(pick):
        for k in range(3):
            for c, y in ((0, att), (1, ign)):
                ref = float(cs_qmi(torch.as_tensor(F[i, :, k]), torch.as_tensor(y[i][:, None].astype(np.float64)), sigma_u=sx, sigma_v=sa)[0])
                worst = max(worst, abs(ref - slot[j, k, c]))
    est = {'max_abs_diff_vs_cs_qmi_reference': worst, 'pass': worst < 1e-9}
    # (2) integration path vs stored ridge readout
    stored = json.loads(Path(ro).read_text()); q0 = np.asarray(meta['q0']); maxdiff, n = 0.0, 0
    person, role = A['person'], A['role']
    for sf in SFS:
        X = z[f'pca_sf{sf}'].astype(np.float64); Fc = z[f'cs_pca_sf{sf}'].astype(np.float64)
        tr, te = people_sets(meta, person, sf)
        strn = np.isin(person, sorted(tr)); sfit = strn & (role == 'fit'); ses = strn & (role == 'es')
        r2 = np.where(sfit, 'fit', np.where(ses, 'es', 'other')); ye = A['env']; mu, sd = ye[sfit | ses].mean(), ye[sfit | ses].std() + 1e-12
        fits = [CT.fitted(X[:, k], ((ye - mu) / sd)[:, None], r2) for k in range(3)]
        pred = np.einsum('k,knt->nt', q0, np.stack([(Fc[:, :, k] @ fits[k][0] + fits[k][1])[..., 0] for k in range(3)]))
        mrg = RO.rowcorr(pred, A['cs_env_att']) - RO.rowcorr(pred, A['cs_env_ign'])
        res = XE.integrate(mrg, A['cs_person'], A['cs_role'], A['cs_code'], A['cs_e0'], meta['cs']['seg_len'], tr, te)
        for sec, val in res.items():
            for p, v in val['people'].items():
                sv = stored['people'][p]['attention']['q0'][sec]; n += 1
                maxdiff = max(maxdiff, abs(v['accuracy'] - sv['accuracy']), abs(v['nll_bits'] - sv['nll_bits']), abs(val['tau'] - sv['tau']),
                              abs(v['n_windows'] - sv['n_windows']))
        del X, Fc
    z.close()
    pipe = {'unit': row['id'], 'cells_compared': n, 'max_abs_diff_vs_stored_readout': maxdiff, 'pass': maxdiff < 1e-9}
    rec = {'estimator': est, 'pipeline': pipe, 'status': 'pass' if est['pass'] and pipe['pass'] else 'failed', 'bindings': bindings(),
           'job': os.environ.get('SLURM_JOB_ID')}
    write(OUT / 'GATES.json', rec); print(json.dumps(rec, indent=1, default=float), flush=True)
    assert rec['status'] == 'pass'
    return rec


# ----------------------------------------------------------------------------------------------- run / aggregate
def run():
    bind = bindings(); g = json.loads((OUT / 'GATES.json').read_text()); assert g['status'] == 'pass' and g['bindings'] == bind
    for arm, seeds in ARMS.items():
        for ds in DATASETS:
            for seed in seeds:
                for cf in CFS:
                    if not (OUT / 'units' / f'{unit_id(arm, ds, cf, seed)}.json').exists():
                        run_unit(arm, ds, cf, seed, bind)


def per_person(units, metric_of):
    """units[(seed, cf)] -> {sec: {person: {metric: value}}}; cf mean (both) then seed mean (all seeds)."""
    seeds = sorted({s for s, _ in units}); out = {}
    for sec in WINDOWS:
        people = set().union(*[set(u[sec]) for u in units.values()])
        for p in people:
            if all(p in units[(s, c)][sec] for s in seeds for c in CFS):
                out.setdefault(sec, {})[p] = {k: float(np.mean([np.mean([metric_of(units[(s, c)][sec][p], k) for c in CFS]) for s in seeds]))
                                              for k in ('accuracy', 'nll_bits')}
    return out


def summary(people, groups, ds):
    g = {}
    for grp in GROUPS[ds] + ('all',):
        vals = [v for p, v in people.items() if grp == 'all' or groups[p] == grp]
        if vals:
            a = np.array([v['accuracy'] for v in vals]); nl = np.array([v['nll_bits'] for v in vals])
            g[grp] = {'n_people': len(vals), 'accuracy_mean': float(a.mean()), 'accuracy_sd': float(a.std(ddof=1)) if len(a) > 1 else None,
                      'nll_bits_mean': float(nl.mean()), 'nll_bits_sd': float(nl.std(ddof=1)) if len(nl) > 1 else None}
    return g


def aggregate():
    from ..aln41 import analysis as AN
    bind = bindings(); fams_frozen = {f['id']: f for f in json.loads(FAMILIES.read_text())['families']}
    table, fam_inputs, families = {}, {}, []
    for ds in DATASETS:
        groups = None; table[ds] = {}
        for arm, seeds in ARMS.items():
            R, ridge = {}, {}
            for seed in seeds:
                for cf in CFS:
                    rec = json.loads((OUT / 'units' / f'{unit_id(arm, ds, cf, seed)}.json').read_text())
                    assert rec['status'] == 'complete' and rec['bindings']['design_sha256'] == DESIGN_SHA
                    groups = rec['groups']; R[(seed, cf)] = {sec: {} for sec in WINDOWS}
                    for f in rec['folds'].values():
                        for sec in WINDOWS:
                            R[(seed, cf)][sec].update(f['people'][sec])
                    st = json.loads(Path(rec['stored_readout']).read_text()); assert sha(rec['stored_readout']) == rec['stored_readout_sha256']
                    ridge[(seed, cf)] = {sec: {p: v['attention']['q0'][sec] for p, v in st['people'].items()
                                               if v.get('attention', {}).get('q0', {}).get(sec)} for sec in WINDOWS}
            pr, pg = per_person(R, lambda v, k: v[k]), per_person(ridge, lambda v, k: v[k])
            table[ds][arm] = {'seeds': list(seeds),
                              'R': {sec: {'groups': summary(pr[sec], groups, ds), 'people': pr[sec]} for sec in WINDOWS},
                              'ridge': {sec: {'groups': summary(pg[sec], groups, ds), 'people': pg[sec]} for sec in WINDOWS}}
        fid = f'W7_RULE:{ds}'; fz = fams_frozen[fid]
        people = sorted(set().union(*[set(table[ds][a]['R']['20']['people']) | set(table[ds][a]['ridge']['20']['people']) for a in ARMS]))
        members = []
        for name in fz['members']:
            arm = name.split(':')[0]; r, g = table[ds][arm]['R']['20']['people'], table[ds][arm]['ridge']['20']['people']
            members.append((name, {p: (r[p]['accuracy'] - g[p]['accuracy']) if p in r and p in g else None for p in people}))
        fam_inputs[fid] = {'people': people, 'members': {n: v for n, v in members}, 'endpoint': fz['endpoint'], 'sign': fz['sign']}
        f = AN.family(fid, '20-s two-candidate accuracy, R - ridge (two-sided)', members, people)
        f['method'] = ('aln41.analysis.family: person bootstrap-t B=4000, family max-|T*| simultaneous 95%; per person content folds '
                       'averaged then seeds (TCS / TNCE 3401 / 3407 / 3413; B0 seed-free)')
        nll = {}
        for arm in ARMS:
            r, g = table[ds][arm]['R']['20']['people'], table[ds][arm]['ridge']['20']['people']
            d = [r[p]['nll_bits'] - g[p]['nll_bits'] for p in people if p in r and p in g]
            nll[f'{arm}:R-ridge'] = {'mean_nll_bits_difference': float(np.mean(d)), 'n': len(d), 'note': 'descriptive; lower = R better'}
        f['descriptive_nll_bits'] = nll; families.append(f)
    out = {'version': 'W7_RULE_v1', 'bindings': bind, 'gates': json.loads((OUT / 'GATES.json').read_text()),
           'definition': __doc__, 'table': table, 'family_inputs': fam_inputs, 'groups_note': 'hearing groups as cohort participant group'}
    os.umask(0o022); RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'W7_RULE.json').write_text(json.dumps(out, indent=1, default=float) + '\n')
    (RESULTS / 'W7_RULE_FAMILIES.json').write_text(json.dumps({'version': 'W7_RULE_FAMILIES_v1', 'bindings': bind,
                                                               'input': 'W7_RULE.json family_inputs', 'input_sha256': sha(RESULTS / 'W7_RULE.json'),
                                                               'families': families}, indent=1, default=float) + '\n')
    for ds in DATASETS:
        for arm in ARMS:
            for sec in WINDOWS:
                for kind in ('R', 'ridge'):
                    a = table[ds][arm][kind][sec]['groups']
                    print(ds, arm, sec, kind, {g: (round(v['accuracy_mean'], 4), round(v['nll_bits_mean'], 4), v['n_people']) for g, v in a.items()})
    for f in families:
        print(f['family_id'], f['status'], f['complete_n'], [(m['name'], round(m.get('estimate', float('nan')), 4), m.get('simultaneous_95')) for m in f['members']])


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    cmd = sys.argv[1]
    {'gates': gates, 'run': run, 'aggregate': aggregate}[cmd]()


if __name__ == '__main__':
    main()
