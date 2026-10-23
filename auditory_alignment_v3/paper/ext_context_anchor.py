"""Paper line, Table 2 POST-HOC appendum 01 to the context-matched sensitivity: 16-anchor scoring of the mTRF decoders (CPU, no
fitting).  Requested by the researcher on 2026-10-22 ~19:45 after the mTRF-ctx numbers had been seen; frozen before computing:
results/.../context_matched/APPENDUM_01_ANCHOR_SAMPLING.json.

Question: how much of mTRF's accuracy survives when its segment margin is computed only at the proposed system's 16 anchor times
instead of on every reconstructable sample?  Anchors (aln41/frozen.py, verified by ext_context.span_check): a = 51 + 32 k, k = 0..15
(128 Hz, segment-relative); the matching 64 Hz sample is j = a // 2 = 25 + 16 k (the ext_common pairwise-mean sample whose 128 Hz pair
{2j, 2j+1} contains a; centre 0.5 sample at 128 Hz = 3.9 ms before a).  Prediction and envelopes at j are the decoder's own 64 Hz
prediction and the 64 Hz (pairwise-mean) attended / ignored envelopes used for its training and Table 2 margin.
  primary   mtrf_ctx_anchor16: the mTRF-ctx units' stored weights (context_matched/mtrf, decoder.npz, sha256-verified), predictions
            recomputed from the cache EEG; margin = r(pred, att) - r(pred, ign) over the 16 samples j of each segment.
  secondary mtrf_main_anchor16: the Table 2 mTRF units' stored weights (external_decoders/mtrf), same 16 samples.
Reproduction gate (engineering, not outcome): from the same recomputed predictions, the full-window margins (ctx: t in [13, 271];
main: t in [0, 319]) must equal the stored margins of TABLE2_MTRF_CTX / TABLE2_MTRF within 1e-9 on every scored segment.
Integration / aggregation: ext_context.score_units (ext_common.integrate_unit = aln42.external_eval.integrate, tau refitted on the
training-side windows of the new margins by the unchanged rule; ext_common.summarize).
CLI (Slurm only): python -m auditory_alignment_v3.paper.ext_context_anchor appendum | run --dataset {dtu,fau} | table
"""
from __future__ import annotations

from datetime import datetime
import argparse
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

from .. import core
from . import ext_common as XC
from . import ext_context as CX
from . import ext_context_mtrf as CM
from . import ext_mtrf as MT

ANALYSIS = 'mtrf_ctx_anchor16'
APPENDUM = CX.RES / 'APPENDUM_01_ANCHOR_SAMPLING.json'
OUTPUT = CX.RES / 'TABLE2_MTRF_CTX_ANCHOR16.json'
OUT = CX.OUT / 'anchor16'
STORE = CX.STORE / 'anchor16'
TABLES_MD = XC.RESULTS.parent / 'manuscript_v2' / 'TABLES.md'
REPRO_TOL = 1e-9
SYSTEMS = {'mtrf_ctx': {'plan': CM.OUT / 'plan.json', 'units': CM.OUT / 'units', 'window': (CM.T0, CM.T0 + CM.NT)},
           'mtrf': {'plan': MT.OUT / 'plan.json', 'units': MT.OUT / 'units', 'window': (0, XC.SEG64)}}
# Cited, not recomputed: manuscript_v2/TABLES.md Table 2 row 'TCS' (aln41 readout q0 attention, seeds 3401 / 3407 / 3413), 20 s.
TCS_20S = {'dtu': {'nh': (0.610, 0.945), 'hi': (0.614, 0.939), 'all': (0.612, 0.942)},
           'fau': {'th': (0.542, 0.993), 'ha': (0.519, 0.999), 'ci': (0.495, 1.004), 'all': (0.515, 1.000)}}
MODULE_FILES = ('auditory_alignment_v3/paper/ext_context_anchor.py', 'auditory_alignment_v3/paper/ext_context.py',
                'auditory_alignment_v3/paper/ext_context_mtrf.py', 'auditory_alignment_v3/paper/ext_mtrf.py', 'auditory_alignment_v3/paper/ext_common.py',
                'auditory_alignment_v3/aln42/external_eval.py')
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def anchors():
    a = np.array(CX.span_check()['anchors_128hz'])
    assert np.array_equal(a, 51 + 32 * np.arange(16)) and (a % 2 == 1).all()
    j = a // 2
    assert np.array_equal(j, 25 + 16 * np.arange(16))
    for w in SYSTEMS.values():
        assert j.min() >= w['window'][0] and j.max() < w['window'][1]
    return a, j


# ------------------------------------------------------------------------------------------------ appendum
def appendum_body():
    a, j = anchors()
    ctx = read(CX.RES / 'TABLE2_MTRF_CTX.json')
    seen_ctx = {ds: {sec: {g: [round(v['accuracy_mean'], 4), round(v['nll_bits_mean'], 4)] for g, v in d['summary_by_window_s'][sec].items()}
                     for sec in ('5', '10', '20')} for ds, d in ctx['datasets'].items()}
    return {
        'post_hoc': True, 'appendum_to': {'file': 'PROTOCOL.json', 'sha256': CX.protocol_sha()},
        'requested': '2026-10-22 ~19:45 by the researcher, after the mTRF-ctx numbers (TABLE2_MTRF_CTX.json) had been seen',
        'seen_before_request': {'mtrf_ctx_by_window_s_acc_nll': seen_ctx, 'mtrf_ctx_file_sha256': sha(CX.RES / 'TABLE2_MTRF_CTX.json'),
                                'also_seen': 'Table 2 main rows (mTRF, VLAAI, TCS, B0, TNCE, MindMix) and the earlier post-hoc sensitivity rows '
                                             '(manuscript_v2/TABLES.md); VLAAI-ctx not seen (lane registered, no output read)'},
        'question': "how much of mTRF's accuracy survives when its segment margin is computed only at the proposed system's 16 anchor "
                    'times instead of on all reconstructable samples?',
        'anchors': {'anchors_128hz_segment_relative': a.tolist(), 'samples_64hz': j.tolist(),
                    'mapping': '64 Hz sample j = a // 2: the ext_common pairwise-mean sample whose 128 Hz pair {2j, 2j+1} contains a (centre 3.9 ms before a)',
                    'targets': "the decoder's 64 Hz prediction and the 64 Hz pairwise-mean attended / ignored envelopes at j (its own training target), "
                               'not the 128 Hz envelope sample at a'},
        'primary': {'analysis': ANALYSIS, 'output': OUTPUT.name, 'decoder': 'mTRF-ctx units (context_matched/mtrf), stored decoder.npz, no re-fit',
                    'margin': 'r(pred, att) - r(pred, ign) over the 16 samples j of each 5 s segment',
                    'integration': 'ext_context.score_units = ext_common.integrate_unit (aln42.external_eval.integrate, 5 / 10 / 20 s, tau refitted '
                                   'on training-side windows by the unchanged rule) + ext_common.summarize; 20 s primary'},
        'secondary': {'analysis': 'mtrf_main_anchor16', 'decoder': 'Table 2 mTRF units (external_decoders/mtrf), stored decoder.npz, no re-fit',
                      'margin': 'same 16 samples', 'location': 'inside the output file, key secondary_mtrf_main_anchor16'},
        'reference_cited_not_recomputed': {'TCS_20s_acc_nll': TCS_20S, 'source': 'results/auditory_alignment_v3/paper/manuscript_v2/TABLES.md, row TCS',
                                           'source_sha256_at_freeze': sha(TABLES_MD)},
        'reproduction_gate': f'full-window margins recomputed from the stored weights == stored margins (max abs diff <= {REPRO_TOL}) on every scored '
                             'segment of every unit, both decoders; engineering check, not an outcome gate',
        'pre_stated_reading': {'large_drop': "a large drop of mTRF toward the proposed system's level means sparse 4 Hz (16-point) scoring "
                                             'explains much of the gap',
                               'small_drop': 'a small drop means it does not',
                               'descriptive_quantity': 'per cohort / group at 20 s: share of the mTRF-ctx minus TCS accuracy gap removed by 16-anchor '
                                                       'scoring = (mtrf_ctx - mtrf_ctx_anchor16) / (mtrf_ctx - TCS); reported, no threshold',
                               'caveat': 'the proposed system still differs in features, readout training data (ss) and 128 Hz anchor targets; '
                                         'this isolates only the number / rate of scored points'},
        'module_sha256_at_freeze': CX.file_shas(MODULE_FILES),
        'plans_sha256': {k: sha(v['plan']) for k, v in SYSTEMS.items()},
        'input_index_sha256': {ds: sha(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS}}


def freeze_appendum():
    body = appendum_body()
    if APPENDUM.exists():
        old = read(APPENDUM); drift = [k for k, v in body.items() if k not in ('module_sha256_at_freeze',) and old.get(k) != v]
        assert not drift, f'appendum drift: {drift}'
        return old
    os.umask(0o022)
    APPENDUM.write_text(json.dumps({**body, 'frozen_at': datetime.now().astimezone().isoformat(), 'frozen_by_job': os.environ.get('SLURM_JOB_ID')},
                                   indent=1) + '\n')
    APPENDUM.chmod(0o444); os.umask(0o077)
    return read(APPENDUM)


def appendum_sha():
    assert APPENDUM.exists() and (APPENDUM.stat().st_mode & 0o222) == 0, 'appendum missing or writable'
    return sha(APPENDUM)


def selftest():
    """Synthetic: full-design rows at j equal the ctx design rows at j - 13 (same predictions for the ctx decoder)."""
    _, j = anchors()
    E = np.random.default_rng(0).standard_normal((2, 4, XC.BLOCK64)).astype(np.float32)
    full = MT.design(E).reshape(2, XC.SEG64, -1); ctx = CM.design_ctx(E).reshape(2, CM.NT, -1)
    ok = bool(np.array_equal(full[:, j], ctx[:, j - CM.T0]) and np.array_equal(full[:, CM.T0:CM.T0 + CM.NT], ctx))
    assert ok
    return ok


# ------------------------------------------------------------------------------------------------ run (per dataset, both content folds)
def unit_rows(system, ds):
    plan = read(SYSTEMS[system]['plan']); out = []
    for row in plan['rows']:
        if row['dataset'] != ds:
            continue
        rec = read(SYSTEMS[system]['units'] / f'{row["id"]}.json'); assert rec['status'] == 'complete'
        dest = Path(rec['dest']); assert sha(dest / 'decoder.npz') == rec['decoder_sha256'] and sha(dest / 'margins.npz') == rec['npz_sha256']
        with np.load(dest / 'decoder.npz') as z:
            w, b = z['w'], float(z['b'])
        with np.load(dest / 'margins.npz', allow_pickle=False) as z:
            stored, scored = z['margin'], z['scored']
        out.append({'system': system, 'row': row, 'rec': rec, 'w': w, 'b': b, 'stored': stored, 'scored': scored})
    assert len(out) == len(XC.CFS) * len(XC.SFS)
    return out


def run(ds):
    t0 = time.time(); aps = appendum_sha(); _, J = anchors(); assert selftest()
    cache = XC.Cache(ds); arr = cache.arr; person = arr['cs_person']; n = len(person)
    units = unit_rows('mtrf_ctx', ds) + unit_rows('mtrf', ds)
    W = np.stack([u['w'] for u in units], 1); B = np.array([u['b'] for u in units])
    for u in units:
        u['full'] = np.full(n, np.nan); u['a16'] = np.full(n, np.nan)
    for pid in sorted(set(person.tolist())):
        rows_ = cache.person_rows(pid); E, att, ign = cache.load(pid, check=True); loc = arr['cs_row'][rows_]
        for s in range(0, len(rows_), MT.CHUNK):
            gi = rows_[s:s + MT.CHUNK]; b = loc[s:s + MT.CHUNK]
            P = (MT.design(E[b]) @ W + B).reshape(len(b), XC.SEG64, len(units))
            A, I = att[b].astype(np.float64), ign[b].astype(np.float64)
            for k, u in enumerate(units):
                m = u['scored'][gi] != ''
                if not m.any():
                    continue
                lo, hi = SYSTEMS[u['system']]['window']; p = P[m, :, k]; g = gi[m]
                u['full'][g] = XC.rowcorr(p[:, lo:hi], A[m, lo:hi]) - XC.rowcorr(p[:, lo:hi], I[m, lo:hi])
                u['a16'][g] = XC.rowcorr(p[:, J], A[m][:, J]) - XC.rowcorr(p[:, J], I[m][:, J])
        del E
    recs = []
    for u in units:
        sc = u['scored'] != ''
        diff = float(np.abs(u['full'][sc] - u['stored'][sc]).max())
        assert np.isnan(u['stored'][~sc]).all() and np.isfinite(u['a16'][sc]).all() and np.isnan(u['a16'][~sc]).all()
        assert diff <= REPRO_TOL, (u['row']['id'], diff)
        row = u['row']; body = {'analysis': 'anchor16', 'system': u['system'], 'dataset': ds, 'content_fold': row['content_fold'],
                                'person_fold': row['person_fold']}
        uid = 'PXA16_' + digest(body, 16); dest = STORE / 'units' / uid; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
        np.savez_compressed(dest / 'margins.npz', cs_person=person, cs_code=arr['cs_code'], cs_e0=arr['cs_e0'], cs_role=cache.role(row['content_fold']),
                            margin=u['a16'], scored=u['scored'])
        rec = {**body, 'id': uid, 'status': 'complete', 'source_unit': row['id'], 'source_record_sha256': sha(SYSTEMS[u['system']]['units'] / f'{row["id"]}.json'),
               'decoder_sha256': u['rec']['decoder_sha256'], 'dest': str(dest), 'npz_sha256': sha(dest / 'margins.npz'),
               'reproduction_full_window_max_abs_diff': diff, 'n_scored': int(sc.sum()), 'anchors_64hz': J.tolist(),
               'appendum_sha256': aps, 'module_sha256': sha(Path(__file__)), 'job': os.environ.get('SLURM_JOB_ID'), 'seconds_dataset': round(time.time() - t0, 1)}
        write(OUT / 'units' / f'{uid}.json', rec); recs.append(rec)
        print(uid, u['system'], ds, row['content_fold'], row['person_fold'], 'repro', diff, flush=True)
    return recs


# ------------------------------------------------------------------------------------------------ table
def records(system):
    out = {}
    for p in sorted((OUT / 'units').glob('PXA16_*.json')):
        r = read(p)
        if r['system'] == system:
            out[(r['dataset'], r['content_fold'], r['person_fold'])] = r
    return out


def summarize(system):
    recs = records(system); assert len(recs) == len(XC.DATASETS) * len(XC.CFS) * len(XC.SFS), (system, len(recs))
    rows = [{'id': r['id'], 'dataset': ds, 'content_fold': cf, 'person_fold': sf} for (ds, cf, sf), r in recs.items()]
    by = CX.score_units(rows, lambda row: recs[(row['dataset'], row['content_fold'], row['person_fold'])])
    return {ds: {'summary_by_window_s': {sec: v['groups'] for sec, v in summ.items()},
                 'per_person_by_window_s': {sec: v['people'] for sec, v in summ.items()}, 'tau': taus} for ds, (summ, taus) in by.items()}, recs


def versus(new, ref_file):
    ref = read(ref_file)['datasets']; out = {}
    for ds, d in new.items():
        out[ds] = {}
        for sec, people in d['per_person_by_window_s'].items():
            rp = ref[ds]['per_person_by_window_s'][sec]; assert sorted(rp) == sorted(people)
            out[ds][sec] = {}
            for grp in d['summary_by_window_s'][sec]:
                ps = [p for p, x in people.items() if grp == 'all' or x['group'] == grp]
                da = np.array([people[p]['accuracy'] - rp[p]['accuracy'] for p in ps]); dn = np.array([people[p]['nll_bits'] - rp[p]['nll_bits'] for p in ps])
                out[ds][sec][grp] = {'n_people': len(ps), 'reference_accuracy_mean': ref[ds]['summary_by_window_s'][sec][grp]['accuracy_mean'],
                                     'reference_nll_bits_mean': ref[ds]['summary_by_window_s'][sec][grp]['nll_bits_mean'],
                                     'minus_reference_accuracy_mean': float(da.mean()), 'minus_reference_nll_bits_mean': float(dn.mean()),
                                     'n_people_accuracy_lower': int((da < 0).sum()), 'n_people_accuracy_higher': int((da > 0).sum())}
    return out


def make_table():
    aps = appendum_sha(); _, J = anchors()
    prim, prec = summarize('mtrf_ctx'); sec_, srec = summarize('mtrf')
    ctx_file, main_file = CX.RES / 'TABLE2_MTRF_CTX.json', XC.RESULTS / 'mtrf' / 'TABLE2_MTRF.json'
    vs_ctx, vs_main = versus(prim, ctx_file), versus(sec_, main_file)
    gap = {}
    for ds, groups in TCS_20S.items():
        gap[ds] = {}
        for grp, (tcs_acc, _) in groups.items():
            c = vs_ctx[ds]['20'][grp]['reference_accuracy_mean']; a16 = prim[ds]['summary_by_window_s']['20'][grp]['accuracy_mean']
            gap[ds][grp] = {'tcs_cited': tcs_acc, 'mtrf_ctx': c, 'mtrf_ctx_anchor16': a16, 'share_of_gap_removed': (c - a16) / (c - tcs_acc)}
    for ds in prim:
        prim[ds]['versus_mtrf_ctx_by_window_s'] = vs_ctx[ds]
        sec_[ds]['versus_mtrf_main_by_window_s'] = vs_main[ds]
    out = {'system': ANALYSIS, 'post_hoc': True, 'protocol_sha256': CX.protocol_sha(), 'appendum_sha256': aps, 'module_sha256': CX.file_shas(MODULE_FILES),
           'anchors_128hz': (51 + 32 * np.arange(16)).tolist(), 'anchors_64hz': J.tolist(),
           'definition': read(APPENDUM)['primary'], 'reference_files': {'mtrf_ctx': {'file': str(ctx_file.relative_to(core.REPO)), 'sha256': sha(ctx_file)},
                                                                        'mtrf_main': {'file': str(main_file.relative_to(core.REPO)), 'sha256': sha(main_file)}},
           'reproduction_full_window_max_abs_diff': {'mtrf_ctx': max(r['reproduction_full_window_max_abs_diff'] for r in prec.values()),
                                                     'mtrf_main': max(r['reproduction_full_window_max_abs_diff'] for r in srec.values())},
           'tcs_20s_cited': TCS_20S, 'gap_20s_accuracy': gap, 'datasets': prim,
           'secondary_mtrf_main_anchor16': {'definition': read(APPENDUM)['secondary'], 'datasets': sec_}}
    os.umask(0o022)
    OUTPUT.write_text(json.dumps(out, indent=1, default=float) + '\n'); os.umask(0o077)
    cells = {ds: {g: (round(v['accuracy_mean'], 4), round(v['nll_bits_mean'], 4), v['n_people']) for g, v in d['summary_by_window_s']['20'].items()}
             for ds, d in prim.items()}
    print(ANALYSIS, json.dumps(cells), flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('appendum', 'run', 'table')); ap.add_argument('--dataset', choices=XC.DATASETS)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.cmd == 'appendum':
        assert selftest(); p = freeze_appendum(); print(json.dumps({k: p[k] for k in ('post_hoc', 'anchors', 'frozen_at')}, indent=1)); print(sha(APPENDUM))
    elif a.cmd == 'run':
        run(a.dataset)
    elif a.cmd == 'table':
        make_table()


if __name__ == '__main__':
    main()
