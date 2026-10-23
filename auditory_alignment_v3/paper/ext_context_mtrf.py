"""Paper line, Table 2 POST-HOC context-matched sensitivity, mTRF row (CPU).  Protocol: results/.../context_matched/PROTOCOL.json.

ext_mtrf's backward decoder (64 Hz, lags 0..32 samples = 0..500 ms, all channels, aln34.content_time ridge on standardised lagged
features, alpha grid logspace(-3, 4, 8), alpha by mean per-segment Pearson r on train people cs role=es, refit fit + es) restricted
to the proposed system's EEG span [13, 304) at 64 Hz (ext_context.SPAN64): envelope sample t enters training, alpha selection and
the margin only if EEG t..t+32 lies inside the span, i.e. t in [13, 271] (NT = 259 samples).  EEG outside the span is set to NaN
before the design matrix is built (mask_outside), so any use of it would make the sufficient statistics / predictions non-finite;
finiteness is asserted.  Margin = r(hat, attended) - r(hat, ignored) over t in [13, 271]; integration / aggregation =
ext_context.score_units (ext_common.integrate_unit, ext_common.summarize).  Otherwise the code path is ext_mtrf.run_group.
CLI (Slurm only): python -m auditory_alignment_v3.paper.ext_context_mtrf plan | run --dataset {dtu,fau} [--cf N] | table
"""
from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import time
import traceback

import numpy as np

from . import ext_common as XC
from . import ext_context as CX
from . import ext_mtrf as MT

SYSTEM = 'mtrf_ctx'
OUT = CX.OUT / 'mtrf'
STORE = CX.STORE / 'mtrf'
T0 = CX.SPAN64[0]
NT = CX.SPAN64[1] - (MT.NLAG - 1) - T0          # 259: t in [13, 271]
MODULE_FILES = ('auditory_alignment_v3/paper/ext_context_mtrf.py', 'auditory_alignment_v3/paper/ext_context.py',
                'auditory_alignment_v3/paper/ext_mtrf.py', 'auditory_alignment_v3/paper/ext_common.py', 'auditory_alignment_v3/aln42/external_eval.py')
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def sources():
    return CX.file_shas(MODULE_FILES)


def rows():
    out = []
    for ds in XC.DATASETS:
        for cf in XC.CFS:
            for sf in XC.SFS:
                body = {'system': SYSTEM, 'dataset': ds, 'content_fold': cf, 'person_fold': sf, 'span_64hz': list(CX.SPAN64)}
                out.append({**body, 'id': 'PXMCTX_' + digest(body, 16)})
    return out


def make_plan():
    body = {'version': 'PAPER_EXT_MTRF_CTX_v1', 'post_hoc': True, 'protocol_sha256': CX.protocol_sha(), 'rows': rows(), 'sources': sources(),
            'reference_plan_sha256': sha(XC.OUT / 'mtrf' / 'plan.json'),
            'input_index_sha256': {ds: sha(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS},
            'span': {'eeg_64hz_half_open': list(CX.SPAN64), 'envelope_t_inclusive': [T0, T0 + NT - 1], 'n_envelope_samples': NT,
                     'lags_samples': [0, MT.NLAG - 1]}}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        return old
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    return read(plan)


def verify(plan):
    assert plan['sources'] == sources(), 'mtrf_ctx source drift'
    assert plan['protocol_sha256'] == CX.protocol_sha()
    for ds in XC.DATASETS:
        assert sha(XC.INPUT / ds / 'index.json') == plan['input_index_sha256'][ds]


def mask_outside(E):
    """Copy of E [n, C, 352] with every 64 Hz sample outside [13, 304) set to NaN."""
    E = np.array(E, dtype=np.float32, copy=True)
    E[:, :, :CX.SPAN64[0]] = np.nan; E[:, :, CX.SPAN64[1]:] = np.nan
    return E


def design_ctx(E):
    """E [n, C, 352] -> X [n * NT, C * 33] with X[i * NT + j, c * 33 + l] = E[i, c, T0 + j + l] (== ext_mtrf.design rows T0..T0+NT-1)."""
    n, C, _ = E.shape
    ix = (T0 + np.arange(NT))[:, None] + np.arange(MT.NLAG)[None]
    assert ix.min() == CX.SPAN64[0] and ix.max() == CX.SPAN64[1] - 1
    return E[:, :, ix].transpose(0, 2, 1, 3).reshape(n * NT, C * MT.NLAG).astype(np.float64)


def load(cache, pid, check=False):
    E, att, ign = cache.load(pid, check=check)
    return mask_outside(E), att[:, T0:T0 + NT], ign[:, T0:T0 + NT]


def run_group(ds, cf, plan):
    """ext_mtrf.run_group on the span: shared per-fold-key statistics, then per unit selection, refit, margins."""
    t0 = time.time(); job = os.environ.get('SLURM_JOB_ID')
    cache = XC.Cache(ds); arr = cache.arr; role = cache.role(cf); person = arr['cs_person']
    D = len(cache.index['channels']) * MT.NLAG
    people = sorted(set(person.tolist()))
    stats = {}
    for pid in people:                                                             # pass 1: fit / es statistics
        rows_ = cache.person_rows(pid); E, att, _ = load(cache, pid, check=True)
        loc = arr['cs_row'][rows_]; k = MT.fold_key(cache.index, pid)
        for r in ('fit', 'es'):
            sel = loc[role[rows_] == r]
            st = stats.setdefault((k, r), MT.Stats(D))
            for s in range(0, len(sel), MT.CHUNK):
                b = sel[s:s + MT.CHUNK]
                st.add(design_ctx(E[b]), att[b].reshape(-1).astype(np.float64))
        del E
    for key, st in stats.items():
        assert np.isfinite(st.sxx).all() and np.isfinite(st.sxy).all() and np.isfinite(st.sx).all(), ('non-finite statistics', key)
    t_stats = time.time() - t0
    units = {}
    for sf in XC.SFS:
        train, test = cache.unit_people(sf)
        keys = sorted({MT.fold_key(cache.index, p) for p in train})
        assert str(sf) not in keys
        fit = sum((stats[(k, 'fit')] for k in keys[1:]), stats[(keys[0], 'fit')])
        es = sum((stats[(k, 'es')] for k in keys[1:]), stats[(keys[0], 'es')])
        Wa, ba = MT.solve(fit, MT.ALPHAS)
        units[sf] = {'train': set(train), 'test': set(test), 'Wa': Wa, 'ba': ba, 'fit_rows': fit.n, 'es_rows': es.n,
                     'es_r': [[] for _ in MT.ALPHAS], 'stats_all': fit + es}
    for pid in people:                                                             # pass 2: per-segment ES r for every alpha
        rows_ = cache.person_rows(pid)
        need = [sf for sf in XC.SFS if pid in units[sf]['train']]
        if not need:
            continue
        E, att, _ = load(cache, pid); loc = arr['cs_row'][rows_]; sel = loc[role[rows_] == 'es']
        for s in range(0, len(sel), MT.CHUNK):
            b = sel[s:s + MT.CHUNK]; X = design_ctx(E[b])
            for sf in need:
                P = (X @ units[sf]['Wa'] + units[sf]['ba']).reshape(len(b), NT, len(MT.ALPHAS))
                r = XC.rowcorr(np.moveaxis(P, 2, 1), att[b][:, None, :].astype(np.float64))
                assert np.isfinite(r).all()
                for a in range(len(MT.ALPHAS)):
                    units[sf]['es_r'][a].extend(r[:, a].tolist())
        del E
    for sf, u in units.items():
        curve = [float(np.mean(v)) for v in u['es_r']]
        u['curve'] = curve; u['alpha_index'] = int(np.argmax(curve)); u['alpha'] = float(MT.ALPHAS[u['alpha_index']])
        W, b = MT.solve(u['stats_all'], [u['alpha']]); u['w'], u['b'] = W[:, 0], float(b[0]); u['n_es_segments'] = len(u['es_r'][0])
        del u['stats_all'], u['Wa'], u['ba'], u['es_r']
    n = len(person)                                                                # pass 3: margins of every scored segment
    for sf, u in units.items():
        u['margin'] = np.full(n, np.nan); u['r_att'] = np.full(n, np.nan); u['r_ign'] = np.full(n, np.nan)
    for pid in people:
        rows_ = cache.person_rows(pid); E, att, ign = load(cache, pid); loc = arr['cs_row'][rows_]; rl = role[rows_]
        for sf, u in units.items():
            if pid in u['train']:
                m = np.isin(rl, ('fit', 'es'))
            elif pid in u['test']:
                m = rl == 'test'
            else:
                continue
            for s in range(0, int(m.sum()), MT.CHUNK):
                gi = rows_[m][s:s + MT.CHUNK]; b = loc[m][s:s + MT.CHUNK]
                P = (design_ctx(E[b]) @ u['w'] + u['b']).reshape(len(b), NT)
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
        rec = {'status': 'complete', 'row': row, 'plan_sha256': sha(OUT / 'plan.json'), 'protocol_sha256': CX.protocol_sha(), 'dest': str(dest),
               'npz_sha256': sha(dest / 'margins.npz'), 'decoder_sha256': sha(dest / 'decoder.npz'),
               'alpha_relative': u['alpha'], 'es_mean_r_curve': u['curve'], 'n_es_segments': u['n_es_segments'],
               'fit_rows': int(u['fit_rows']), 'es_rows': int(u['es_rows']), 'n_train_people': len(u['train']), 'n_test_people': len(u['test']),
               'n_scored_segments': {'train_side': int(len(tr)), 'test': int(len(te))}, 'envelope_samples_per_segment': NT,
               'seconds_group': round(time.time() - t0, 1), 'seconds_stats': round(t_stats, 1), 'job': job, 'sources': sources()}
        write(OUT / 'units' / f'{row["id"]}.json', rec); recs.append(rec)
        print(row['id'], ds, 'cf', cf, 'sf', sf, 'alpha', u['alpha'], flush=True)
    return recs


def run(ds, cfs):
    plan = make_plan(); verify(plan)
    for cf in cfs:
        todo = [r for r in plan['rows'] if r['dataset'] == ds and r['content_fold'] == cf and not (OUT / 'units' / f'{r["id"]}.json').exists()]
        if not todo:
            continue
        try:
            run_group(ds, cf, plan)
        except Exception:
            for r in todo:
                write(OUT / 'units' / f'{r["id"]}.FAILED.json', {'traceback': traceback.format_exc(), 'job': os.environ.get('SLURM_JOB_ID')})
            raise


def make_table():
    plan = read(OUT / 'plan.json'); verify(plan)
    by = CX.score_units(plan['rows'], lambda row: read(OUT / 'units' / f'{row["id"]}.json'))
    alphas = {f"{r['dataset']}_cf{r['content_fold']}_sf{r['person_fold']}": read(OUT / 'units' / f'{r["id"]}.json')['alpha_relative'] for r in plan['rows']}
    return CX.table(SYSTEM, by, MODULE_FILES, extra={'plan_sha256': sha(OUT / 'plan.json'), 'alphas_relative': alphas,
                                                      'definition': read(CX.PROTOCOL)['analyses'][SYSTEM]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'run', 'table'))
    ap.add_argument('--dataset', choices=XC.DATASETS); ap.add_argument('--cf', type=int, choices=XC.CFS)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.cmd == 'plan':
        make_plan(); print(sha(OUT / 'plan.json'))
    elif a.cmd == 'run':
        run(a.dataset, XC.CFS if a.cf is None else (a.cf,))
    elif a.cmd == 'table':
        make_table()


if __name__ == '__main__':
    main()
