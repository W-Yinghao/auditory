"""Paper line, Table 2 row 'Linear mTRF decoder' (CPU): subject-independent backward model (Crosse et al. 2016 style).

Per unit (dataset x content fold cf x person fold sf; ext_common partition): EEG -> attended envelope reconstruction
  env_hat(t) = b + sum_c sum_{l=0..32} w[c, l] EEG_c(t + l / 64 s)        (lags 0..500 ms, 64 Hz, cohort EEG, all channels)
fitted on the train people's competing-speaker role=fit segments (attended envelope), ridge as aln34.content_time.ridge
(standardised lagged features, gram/n + alpha I, alpha in logspace(-3, 4, 8)) with alpha selected by the mean per-segment
Pearson r on the train people's role=es segments, then refit on fit + es (content_time.fitted rule).  Exact closed form from
sufficient statistics (per fold-key and role, summed over the unit's train people).
Segment margin = r(env_hat, attended) - r(env_hat, ignored) over the 5 s segment (320 samples at 64 Hz); decision
integration, tau and scoring = ext_common.integrate_unit (aln42.external_eval.integrate).
Native context per segment margin: 5.5 s of EEG (5 s + 0.5 s lag tail inside the same trial); 20 s decision: 20.5 s.
"""
from __future__ import annotations

from datetime import datetime
import os
import time
import traceback

import numpy as np

from . import ext_common as XC

NLAG = 33
ALPHAS = np.logspace(-3, 4, 8)          # == aln34.content_time.ALPHAS
OUT = XC.OUT / 'mtrf'
STORE = XC.STORE / 'mtrf'
CHUNK = 24
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def sources():
    from pathlib import Path
    return {**XC.sources(), 'auditory_alignment_v3/paper/ext_mtrf.py': sha(Path(__file__))}


def rows():
    out = []
    for ds in XC.DATASETS:
        for cf in XC.CFS:
            for sf in XC.SFS:
                body = {'system': 'mtrf', 'dataset': ds, 'content_fold': cf, 'person_fold': sf}
                out.append({**body, 'id': 'PXMTRF_' + digest(body, 16)})
    return out


def make_plan():
    from ..aln34 import content_time as CT
    assert np.array_equal(ALPHAS, CT.ALPHAS)
    idx = {ds: read(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS}
    for ds in XC.DATASETS:
        assert read(XC.INPUT / ds / 'verify_eeg.json')['pass'], f'verify_eeg {ds}'
    body = {'version': 'PAPER_EXT_MTRF_v1', 'rows': rows(), 'sources': sources(),
            'input_index_sha256': {ds: sha(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS},
            'input_npz_sha256': {ds: idx[ds]['index_sha256'] for ds in XC.DATASETS},
            'recipe': {'fs': XC.FS, 'lags_samples': [0, NLAG - 1], 'lags_ms': [0, 500], 'direction': 'backward (EEG after stimulus)',
                       'features': 'all cohort EEG channels x 33 lags, standardised on the training rows',
                       'alphas': ALPHAS.tolist(), 'ridge': 'aln34.content_time.ridge (gram/n + alpha I on standardised features)',
                       'train': 'train people, cs role=fit, attended envelope', 'selection': 'mean per-segment Pearson r on train people cs role=es',
                       'refit': 'fit + es with the selected alpha', 'margin': 'r(hat, attended) - r(hat, ignored) over the 5 s segment',
                       'integration': 'aln42.external_eval.integrate (5/10/20 s, tau by double-order log loss on train-side windows)'},
            'context': {'eeg_per_segment_s': 5.5, 'eeg_per_20s_decision_s': 20.5, 'lag_window_ms': 500}}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        return old
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    return read(plan)


def verify(plan):
    assert plan['sources'] == sources(), 'mtrf source drift'
    for ds in XC.DATASETS:
        assert sha(XC.INPUT / ds / 'index.json') == plan['input_index_sha256'][ds]


def design(E):
    """E [n, C, 352] -> X [n * 320, C * 33] with X[i * 320 + t, c * 33 + l] = E[i, c, t + l]."""
    n, C, _ = E.shape
    ix = np.arange(XC.SEG64)[:, None] + np.arange(NLAG)[None]
    return E[:, :, ix].transpose(0, 2, 1, 3).reshape(n * XC.SEG64, C * NLAG).astype(np.float64)


class Stats:
    def __init__(self, D):
        self.n = 0; self.sx = np.zeros(D); self.sy = 0.0; self.sxx = np.zeros((D, D)); self.sxy = np.zeros(D)

    def add(self, X, y):
        self.n += len(X); self.sx += X.sum(0); self.sy += float(y.sum()); self.sxx += X.T @ X; self.sxy += X.T @ y

    def __add__(self, o):
        s = Stats(len(self.sx)); s.n = self.n + o.n; s.sx = self.sx + o.sx; s.sy = self.sy + o.sy; s.sxx = self.sxx + o.sxx; s.sxy = self.sxy + o.sxy
        return s


def moments(st):
    mx = st.sx / st.n; my = st.sy / st.n
    cov = st.sxx / st.n - np.outer(mx, mx)
    sd = np.sqrt(np.maximum(np.diag(cov), 0.0)) + 1e-8
    gram = cov / np.outer(sd, sd); rhs = (st.sxy / st.n - mx * my) / sd
    return mx, my, sd, gram, rhs


def solve(st, alphas):
    """content_time.ridge from sufficient statistics for every alpha: ([D, k] weights, [k] intercepts)."""
    mx, my, sd, gram, rhs = moments(st)
    w, V = np.linalg.eigh(gram)
    proj = V.T @ rhs
    W = np.stack([V @ (proj / (w + a)) for a in alphas], 1) / sd[:, None]
    return W, my - mx @ W


def fold_key(index, pid):
    return 'dev' if pid in index['dev_people'] else str(index['folds'][pid])


def run_group(ds, cf, plan):
    """All five person-fold units of (ds, cf): shared per-fold-key statistics, then per unit selection, refit, margins."""
    t0 = time.time(); job = os.environ.get('SLURM_JOB_ID')
    cache = XC.Cache(ds); arr = cache.arr; role = cache.role(cf); person = arr['cs_person']
    D = len(cache.index['channels']) * NLAG
    people = sorted(set(person.tolist()))
    stats = {}
    # pass 1: sufficient statistics of fit / es rows per fold key
    for pid in people:
        rows_ = cache.person_rows(pid); E, att, _ = cache.load(pid, check=True)
        loc = arr['cs_row'][rows_]; k = fold_key(cache.index, pid)
        for r in ('fit', 'es'):
            sel = loc[role[rows_] == r]
            st = stats.setdefault((k, r), Stats(D))
            for s in range(0, len(sel), CHUNK):
                b = sel[s:s + CHUNK]
                st.add(design(E[b]), att[b].reshape(-1).astype(np.float64))
        del E
    t_stats = time.time() - t0
    units = {}
    for sf in XC.SFS:
        train, test = cache.unit_people(sf)
        keys = sorted({fold_key(cache.index, p) for p in train})
        assert str(sf) not in keys
        fit = sum((stats[(k, 'fit')] for k in keys[1:]), stats[(keys[0], 'fit')])
        es = sum((stats[(k, 'es')] for k in keys[1:]), stats[(keys[0], 'es')])
        Wa, ba = solve(fit, ALPHAS)
        units[sf] = {'train': set(train), 'test': set(test), 'Wa': Wa, 'ba': ba, 'fit_rows': fit.n, 'es_rows': es.n,
                     'es_r': [[] for _ in ALPHAS], 'stats_all': fit + es}
    # pass 2: per-segment ES correlation for every alpha
    for pid in people:
        rows_ = cache.person_rows(pid)
        need = [sf for sf in XC.SFS if pid in units[sf]['train']]
        if not need:
            continue
        E, att, _ = cache.load(pid); loc = arr['cs_row'][rows_]; sel = loc[role[rows_] == 'es']
        for s in range(0, len(sel), CHUNK):
            b = sel[s:s + CHUNK]; X = design(E[b])
            for sf in need:
                P = (X @ units[sf]['Wa'] + units[sf]['ba']).reshape(len(b), XC.SEG64, len(ALPHAS))
                r = XC.rowcorr(np.moveaxis(P, 2, 1), att[b][:, None, :].astype(np.float64))      # [n, k]
                for a in range(len(ALPHAS)):
                    units[sf]['es_r'][a].extend(r[:, a].tolist())
        del E
    for sf, u in units.items():
        curve = [float(np.mean(v)) for v in u['es_r']]
        u['curve'] = curve; u['alpha_index'] = int(np.argmax(curve)); u['alpha'] = float(ALPHAS[u['alpha_index']])
        W, b = solve(u['stats_all'], [u['alpha']]); u['w'], u['b'] = W[:, 0], float(b[0]); u['n_es_segments'] = len(u['es_r'][0])
        del u['stats_all'], u['Wa'], u['ba'], u['es_r']
    # pass 3: margins of every scored segment
    n = len(person)
    for sf, u in units.items():
        u['margin'] = np.full(n, np.nan); u['r_att'] = np.full(n, np.nan); u['r_ign'] = np.full(n, np.nan)
    for pid in people:
        rows_ = cache.person_rows(pid); E, att, ign = cache.load(pid); loc = arr['cs_row'][rows_]; rl = role[rows_]
        for sf, u in units.items():
            if pid in u['train']:
                m = np.isin(rl, ('fit', 'es'))
            elif pid in u['test']:
                m = rl == 'test'
            else:
                continue
            for s in range(0, int(m.sum()), CHUNK):
                gi = rows_[m][s:s + CHUNK]; b = loc[m][s:s + CHUNK]
                P = (design(E[b]) @ u['w'] + u['b']).reshape(len(b), XC.SEG64)
                ra = XC.rowcorr(P, att[b].astype(np.float64)); ri = XC.rowcorr(P, ign[b].astype(np.float64))
                u['r_att'][gi], u['r_ign'][gi], u['margin'][gi] = ra, ri, ra - ri
        del E
    recs = []
    for sf, u in units.items():
        row = next(r for r in plan['rows'] if r['dataset'] == ds and r['content_fold'] == cf and r['person_fold'] == sf)
        dest = STORE / 'units' / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
        tr, te = cache.scored(cf, sf)
        scored = np.full(n, '', dtype='<U10'); scored[tr] = 'train_side'; scored[te] = 'test'
        assert np.isfinite(u['margin'][tr]).all() and np.isfinite(u['margin'][te]).all()
        assert np.isnan(u['margin'][scored == '']).all()
        np.savez_compressed(dest / 'margins.npz', cs_person=person, cs_code=arr['cs_code'], cs_e0=arr['cs_e0'], cs_role=role,
                            margin=u['margin'], r_att=u['r_att'], r_ign=u['r_ign'], scored=scored)
        np.savez_compressed(dest / 'decoder.npz', w=u['w'], b=np.array(u['b']))
        rec = {'status': 'complete', 'row': row, 'plan_sha256': sha(OUT / 'plan.json'), 'dest': str(dest),
               'npz_sha256': sha(dest / 'margins.npz'), 'decoder_sha256': sha(dest / 'decoder.npz'),
               'alpha_relative': u['alpha'], 'es_mean_r_curve': u['curve'], 'n_es_segments': u['n_es_segments'],
               'fit_rows': int(u['fit_rows']), 'es_rows': int(u['es_rows']), 'n_train_people': len(u['train']), 'n_test_people': len(u['test']),
               'n_scored_segments': {'train_side': int(len(tr)), 'test': int(len(te))},
               'seconds_group': round(time.time() - t0, 1), 'seconds_stats': round(t_stats, 1), 'job': job}
        write(OUT / 'units' / f'{row["id"]}.json', rec); recs.append(rec)
        print(row['id'], ds, 'cf', cf, 'sf', sf, 'alpha', u['alpha'], flush=True)
    return recs


def run_all():
    plan = make_plan(); verify(plan)
    for ds in XC.DATASETS:
        for cf in XC.CFS:
            todo = [r for r in plan['rows'] if r['dataset'] == ds and r['content_fold'] == cf
                    and not (OUT / 'units' / f'{r["id"]}.json').exists()]
            if not todo:
                continue
            try:
                run_group(ds, cf, plan)
            except Exception:
                for r in todo:
                    write(OUT / 'units' / f'{r["id"]}.FAILED.json', {'traceback': traceback.format_exc(), 'job': os.environ.get('SLURM_JOB_ID')})
                raise


def margins_of(rec):
    from pathlib import Path
    path = Path(rec['dest']) / 'margins.npz'; assert sha(path) == rec['npz_sha256']
    with np.load(path) as z:
        return z['margin']
