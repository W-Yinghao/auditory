"""DEP12 public measurement panels, null banks and 20 s attention queries (Agent M; package v1.2 03 §4.1-4.3, 02 §5.2 / §6.1).

Everything here is defined from trial metadata and stimulus features only (no EEG value, no model, no attention label), and is
frozen (0444) before any representation is measured or any query is scored.

Cohorts and clock. DTU (44 people, 64 ch) and FAU (81 people, 31 ch) at their preprocessed native 128 Hz (c3_preproc_v1:
DTU eeg_1_20, FAU eeg_1_20_ica; per-person z-score of the cohort loaders). Physical sample 0 of a trial is stimulus sample 0 of
the attended stream (DTU target at lead 0, masker at lead round(offset_s * 128); FAU attended / distractor from 0).
Encoder input (03 §1, "64 Hz-equivalent" source window): for an anchor q (128 Hz index, q even = 64 Hz index q/2) the native
crop eeg[q-52 : q+76] (128 samples, half-open [-406.25, +593.75) ms = the source q64+[-26:38]) is resampled to the 200-point 1 s
container by the source path (aln41.timebank.resample); no padding. Descriptor support [q, q+16) = [0, 125) ms (the source env
target support), reduced to 8 points at 64 Hz by pairwise means. Full support width = 1000 ms.
Guards (filter support): the full EEG window must lie in [g, n - g) of the trial with the loaders' standardisation / filter-edge
guards g = 64 (DTU) and 314 (FAU) samples at 128 Hz, n = usable trial length (FAU: min(EEG, stimulus streams) as load_fau);
the descriptor support must lie inside the real stimulus (no zero-padded stimulus sample).

Measurement panels (03 §4.2): per person x content fold cf, two fixed panels of 4 contiguous sub-blocks x 32 anchors at a regular
0.5 s hop (64 samples) on the physical clock of one single-talker (ss) trial each: 'test' (ss trials whose content role in cf is
test; measured for the people whose person fold is the scored fold) and 'calib' (role fit; unlabelled calibration / readout
fitting for the people that are training people of a fold). Candidate block starts in a trial: b_m = g + 52 + m * (2112 + 256)
(block window span 2112 samples, >= 2 s gap between blocks); blocks are taken round-robin over the eligible trials in a fixed
seeded trial order (round m takes candidate m of each trial). Fewer than 4 blocks -> the actual n with coverage recorded
(never padded or repeated).
Null banks (03 §4.3): circular shifts of the descriptor rows inside each block (rows stay in their block, so every shifted row is a
legal row of the same panel); shift k legal iff min(k, 32 - k) * 0.5 s >= MIN_SHIFT (max(2 s, support width 1 s), raised before any
query if the source-fit autocorrelation check requires it). n128: 199 distinct tuples (k_1..k_4) drawn without replacement with a
fixed seed (identical bank for every panel / encoder / descriptor); sensitivity n64 (first 2 blocks): 199 distinct pairs; n32
(first block): every legal single shift (actual count, no duplicates).
Same-stimulus cross-listener control (03 §4.5): for each test block the first other person, in a fixed seeded order of all other
people of the cohort, whose ss trial of the same stimulus covers the same positions; that person's EEG at the same positions is
paired with the same descriptor rows (sharedness, not a null). Noise control: i.i.d. N(0, 1) native windows (seeded per panel).
Attention queries (03 §4.3; 02 §6.1): the common ext_common / ALN4.1 partition. A 20 s query is one window of 4 consecutive 5 s
competing-talker segments of one trial (aln42.external_eval.integrate -> run_attention._runs / _windows, k = 4), i.e. EEG
[st0, st0 + 2560) at 128 Hz; anchors q = st0 + 64 + 16 j, j = 0..151 (64 Hz q = 32, 40, ..., 1240 in query time), every EEG window
and both candidates' descriptor supports inside the query. Scored: for content fold cf and person fold sf, the test people of sf
(ext_common index, = aln41 frozen meta) and their cf test-role windows; per person the accuracy is averaged over both content folds
(both required). Attention null: shifts k in [16, 136] of the 152 rows (min(k, 152 - k) * 0.125 s >= 2 s): 121 legal shifts, all
used, identical for both candidates.
CLI (Slurm only): python -m auditory_alignment_v3.dep12.panels {scan, acf, freeze, status}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

from .. import core
from ..aln34 import learning_budget as B

VERSION = 'DEP12_PUB_DEFS_v1'
OUT = Path(core.OUT) / 'dep12' / 'public'
DEFS = OUT / 'defs_v1'
DATASETS = ('dtu', 'fau')
CFS, SFS = (0, 1), (0, 1, 2, 3, 4)
FS = 128
WIN = (-52, 76)
TGT = 16
SUPPORT_MS = (-406.25, 593.75)
SUPPORT_WIDTH_S = 1.0
GUARD = {'dtu': 64, 'fau': 314}
PANEL_BLOCKS, BLOCK_N, PANEL_HOP = 4, 32, 64
BLOCK_SPAN = (BLOCK_N - 1) * PANEL_HOP + WIN[1] - WIN[0]          # 2112 samples: window coverage of one block
BLOCK_GAP = 256
N_NULL = 199
QUERY_SEGS, SEG128, QUERY_LEN, QUERY_HOP, QUERY_FIRST, QUERY_N = 4, 640, 2560, 16, 64, 152
MIN_SHIFT_S_DEFAULT = 2.0
ACF_THRESHOLD, ACF_MAX_LAG_S = 0.1, 8.0
SEED = 20261023
sha, write, dumps = B.sha, B.write, B.dumps


def read(p):
    return json.loads(Path(p).read_text())


def digest(v, n=64):
    return hashlib.sha256(dumps(v).encode()).hexdigest()[:n]


def seed_of(*parts):
    return int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:12], 16)


def sources():
    repo = Path(core.REPO)
    files = [Path(__file__), repo / 'auditory_alignment/data.py', repo / 'auditory_alignment_v3/paper/ext_common.py',
             repo / 'auditory_alignment_v3/run_attention.py', repo / 'auditory_alignment_v2/train.py']
    return {str(p.relative_to(repo)): sha(p) for p in files}


# ------------------------------------------------------------------------------------------------ trial scan (metadata only)
def scan_dtu():
    import h5py
    from auditory_alignment import data as D
    from ..paper import ext_common as X
    parts = X._people('dtu')
    tfs = [h5py.File(os.path.join(D.DTU_KCS, f'dtu_cf{cf}.h5'), 'r') for cf in CFS]
    inv = json.load(open(f'{D.PUB}/derived/c3_features_v1/dtu/inventory.json'))
    cg = json.load(open(os.path.join(D.DTU_KCS, 'content_groups.json')))['content']
    shaof = {(r['file'], r['trial'], r['kind']): (r.get('sha'), r['offset_s']) for r in inv}
    out = {}
    for p in parts:
        rows = []
        with h5py.File(os.path.join(D.DTU_PRE, f"{p['id']}.h5"), 'r') as f:
            for k in sorted(f.keys()):
                g = f[k]; two = str(g.attrs['talkers']) == 'twotalker'
                th, _ = shaof.get((p['id'], k, 'target'), (None, 0)); mh, moff = shaof.get((p['id'], k, 'masker'), (None, 0))
                if th is None or th not in cg or any(th not in tf for tf in tfs) or (two and (mh is None or any(mh not in tf for tf in tfs))):
                    continue
                n = int(g['eeg_1_20'].shape[1]); c = cg[th]
                roles = ['test' if c['half'] == cf else ('es' if c['early_stop'] else 'fit') for cf in CFS]
                lt = int(tfs[0][f'{th}/Local'].shape[1])
                row = {'trial': k, 'kind': 'cs' if two else 'ss', 'n': n, 'roles': roles, 'att': th, 'att_lead': 0, 'att_len': lt,
                       'g0': GUARD['dtu'], 'g1': n - GUARD['dtu']}
                if two:
                    mon = float(g.attrs['masker_onset_rel_s']); lead = int(round(moff * FS))
                    a0 = max(GUARD['dtu'], int(np.ceil((mon + 1.7) * FS)))
                    row.update(ign=mh, ign_lead=lead, ign_len=int(tfs[0][f'{mh}/Local'].shape[1]),
                               sts=D._segments_of(a0, n, SEG128, int(D.MAX_WIN_S * FS) + 1 + D.AUDIO_FRAMES))
                rows.append(row)
        out[p['id']] = rows
    for tf in tfs:
        tf.close()
    return parts, out


def scan_fau():
    import h5py
    from auditory_alignment import data as D
    from ..paper import ext_common as X
    parts = X._people('fau')
    tfs = [h5py.File(os.path.join(D.FAU_KCS, f'fau_cf{cf}.h5'), 'r') for cf in CFS]
    out = {}
    for p in parts:
        rows = []
        with h5py.File(os.path.join(D.STAGEB, p['group'], f"{p['id']}.h5"), 'r') as f:
            ch = [str(c) for c in f.attrs['channels']]
            assert len(ch) == 31 and 'IO2' not in ch
            trials = [(str(f[t].attrs['stimulus']), t, int(f[t]['eeg_1_20_ica'].shape[1])) for t in sorted(f.keys())]
        for code, tkey, n_eeg in trials:
            if code[0] not in '12':
                continue
            kind = 'ss' if code[0] == '1' else 'cs'
            roles = [next(r for r, ps in D.FAU_CF[cf][kind].items() if code[2] in ps) for cf in CFS]
            lens = []
            for stream in (('attended', 'distractor') if kind == 'cs' else ('attended',)):
                ls = [min(tf[f'{code}/{stream}/{t}'].shape[1] for t in ('Ac', 'Lz', 'Local')) for tf in tfs]
                assert len(set(ls)) == 1; lens.append(ls[0])
            n = min([n_eeg] + lens); g = GUARD['fau']
            row = {'trial': tkey, 'kind': kind, 'n': n, 'n_eeg': n_eeg, 'roles': roles, 'att': code, 'att_lead': 0, 'att_len': lens[0],
                   'g0': g, 'g1': n - g}
            if kind == 'cs':
                row.update(ign=code, ign_lead=0, ign_len=lens[1],
                           sts=D._segments_of(g, n - g, SEG128, int(D.MAX_WIN_S * FS) + 1 + D.AUDIO_FRAMES))
            rows.append(row)
        out[p['id']] = rows
    for tf in tfs:
        tf.close()
    return parts, out


def check_against_cache(ds, trials):
    """The cs segment list derived here equals the ext_common input cache (itself asserted against the ALN4.1 frozen B0 units)."""
    from ..paper import ext_common as X
    c = X.Cache(ds); a = c.arr
    mine = [(pid, r['trial'], int(st), r['roles'][0], r['roles'][1]) for pid, rows in trials.items() for r in rows if r['kind'] == 'cs'
            for st in r['sts']]
    theirs = list(zip(a['cs_person'].tolist(), a['cs_trial'].tolist(), a['cs_st'].astype(int).tolist(), a['cs_role0'].tolist(),
                      a['cs_role1'].tolist()))
    assert sorted(mine) == sorted(theirs), f'{ds}: cs segment list differs from the ext_common cache ({len(mine)} vs {len(theirs)})'
    return {'cs_segments': len(mine), 'equal_to_ext_common_cache': True, 'cache_index_sha256': c.index['index_sha256']}


def scan(ds):
    parts, trials = (scan_dtu if ds == 'dtu' else scan_fau)()
    check = check_against_cache(ds, trials)
    body = {'version': VERSION, 'dataset': ds, 'people': parts, 'trials': trials, 'cache_check': check, 'sources': sources()}
    write(DEFS / ds / 'scan.json', body)
    n_ss = sum(r['kind'] == 'ss' for rows in trials.values() for r in rows)
    print(ds, 'people', len(parts), 'ss trials', n_ss, 'cs segments', check['cs_segments'], flush=True)
    return body


# ------------------------------------------------------------------------------------------------ autocorrelation (before any query)
def _acf(x, max_lag):
    """Biased, mean-removed autocorrelation of each row of x [d, T] at lags 0..max_lag (sum over the record, normalised by lag 0)."""
    x = x - x.mean(1, keepdims=True); T = x.shape[1]; nfft = 1 << int(math.ceil(math.log2(2 * T)))
    F = np.fft.rfft(x, nfft, axis=1); r = np.fft.irfft(F * np.conj(F), nfft, axis=1)[:, :max_lag + 1]
    return r, r[:, :1]


def acf_check():
    """Descriptor autocorrelation on the training-side (role fit) single-talker stimuli of both cohorts and content folds, plus the
    SparrKULee source-fit envelope (prior33 contract streams of the fit families). Decides MIN_SHIFT before any query is opened."""
    import h5py
    from auditory_alignment import data as D
    out = {'version': VERSION, 'threshold_abs_acf': ACF_THRESHOLD, 'max_lag_s': ACF_MAX_LAG_S, 'grid_s': PANEL_HOP / FS,
           'rule': ('min shift = max(2 s, support width 1 s, L) with L the smallest lag on the 0.5 s grid such that the stream-pooled '
                    'autocorrelation of every descriptor dimension has |acf| <= 0.1 at every lag in [L, 8 s]'),
           'cohorts': {}}
    worst = 0.0
    for ds in DATASETS:
        sc = read(DEFS / ds / 'scan.json')
        for cf in CFS:
            path = os.path.join(D.DTU_KCS if ds == 'dtu' else D.FAU_KCS, f'{ds}_cf{cf}.h5')
            keys = sorted({r['att'] for rows in sc['trials'].values() for r in rows if r['kind'] == 'ss' and r['roles'][cf] == 'fit'})
            ml = int(ACF_MAX_LAG_S * FS); acc = {}
            with h5py.File(path, 'r') as tf:
                for k in keys:
                    base = f'{k}/attended' if ds == 'fau' else k
                    loc = tf[f'{base}/Local'][()].astype(np.float64); lz = tf[f'{base}/Lz'][()].astype(np.float64)
                    for name, arr in (('env', loc[5:6]), ('spec', loc[:5]), ('Lz', lz)):
                        r, r0 = _acf(arr, ml)
                        a = acc.setdefault(name, [np.zeros((arr.shape[0], ml + 1)), np.zeros((arr.shape[0], 1))])
                        a[0] += r; a[1] += r0
            res = {}
            for name, (r, r0) in acc.items():
                rho = r / r0; lags = np.arange(0, ml + 1, PANEL_HOP)
                curve = np.abs(rho[:, lags]).max(0)
                ok = [l for i, l in enumerate(lags) if np.all(curve[i:] <= ACF_THRESHOLD)]
                L = (ok[0] / FS) if ok else None
                res[name] = {'n_streams': len(keys), 'max_abs_acf_by_lag_s': {f'{l / FS:g}': float(v) for l, v in zip(lags, curve)},
                             'max_abs_acf_at_2s': float(curve[list(lags).index(256)]), 'L_s': L}
                worst = max(worst, L if L is not None else ACF_MAX_LAG_S + 1)
            out['cohorts'][f'{ds}_cf{cf}'] = res
    try:
        out['sparrkulee_source_fit_env'] = _sparrkulee_env_acf()
        L = out['sparrkulee_source_fit_env']['L_s']; worst = max(worst, L if L is not None else ACF_MAX_LAG_S + 1)
    except Exception as exc:  # recorded, the cohort descriptors still decide
        out['sparrkulee_source_fit_env'] = {'status': 'not_computed', 'error': repr(exc)[:300]}
    min_shift = max(MIN_SHIFT_S_DEFAULT, SUPPORT_WIDTH_S, worst)
    out['decision'] = {'L_max_s': worst, 'min_shift_s': min_shift,
                       'raised_above_2s': bool(min_shift > MIN_SHIFT_S_DEFAULT)}
    write(DEFS / 'acf_check.json', out)
    print(json.dumps(out['decision']), flush=True)
    return out


def _sparrkulee_env_acf():
    from ..aln41 import source as SRC
    from ..prior33 import views as V, contract as PC
    man = SRC.open_manifest(); pools, _ = SRC.pool(man)
    idx = V.manifest_index(man); seg = idx.seg['sparrkulee']
    fams = {f for p in pools['fit'].values() for f in p}
    streams = V.cohort_streams(man, 'sparrkulee')
    env = np.load(os.path.join(V.cohort_dir(man, 'sparrkulee'), 'env_f32.npy'), mmap_mode='r', allow_pickle=False)
    ml = int(ACF_MAX_LAG_S * PC.FS); r_acc = np.zeros((1, ml + 1)); r0_acc = np.zeros((1, 1)); n = 0
    for s in streams:
        if s.get('kind') != 'attended' or int(s['family']) not in fams:
            continue
        x = np.asarray(env[int(s['offset']):int(s['offset']) + int(s['length'])], np.float64)[None]
        if x.shape[1] <= ml:
            continue
        r, r0 = _acf(x, ml); r_acc += r; r0_acc += r0; n += 1
    rho = (r_acc / r0_acc)[0]; lags = np.arange(0, ml + 1, PC.FS // 2); curve = np.abs(rho[lags])
    ok = [l for i, l in enumerate(lags) if np.all(curve[i:] <= ACF_THRESHOLD)]
    return {'n_streams': n, 'fs': PC.FS, 'max_abs_acf_by_lag_s': {f'{l / PC.FS:g}': float(v) for l, v in zip(lags, curve)},
            'L_s': (ok[0] / PC.FS) if ok else None, 'families': len(fams)}


# ------------------------------------------------------------------------------------------------ panels / partners / nulls
def block_starts(row):
    """Candidate block first anchors of one ss trial (window and descriptor supports fully inside guards / real stimulus)."""
    hi_eeg = row['g1'] - (BLOCK_SPAN + WIN[0])                      # b + (31*64 + 76) <= g1
    hi_stim = row['att_lead'] + row['att_len'] - ((BLOCK_N - 1) * PANEL_HOP + TGT)
    hi = min(hi_eeg, hi_stim, row['n'] - ((BLOCK_N - 1) * PANEL_HOP + TGT))
    out, b = [], row['g0'] - WIN[0]
    while b <= hi:
        out.append(int(b)); b += BLOCK_SPAN + BLOCK_GAP
    return out


def make_panel(ds, pid, rows, cf, kind):
    role = 'test' if kind == 'test' else 'fit'
    elig = [r for r in rows if r['kind'] == 'ss' and r['roles'][cf] == role]
    rng = np.random.default_rng(seed_of(SEED, ds, pid, cf, kind))
    order = [elig[i] for i in rng.permutation(len(elig))]
    cand = {r['trial']: block_starts(r) for r in order}
    blocks, m = [], 0
    while len(blocks) < PANEL_BLOCKS and any(len(v) > m for v in cand.values()):
        for r in order:
            if len(blocks) < PANEL_BLOCKS and len(cand[r['trial']]) > m:
                blocks.append({'trial': r['trial'], 'stim': r['att'], 'b': cand[r['trial']][m]})
        m += 1
    return {'person': pid, 'cf': cf, 'kind': kind, 'blocks': blocks, 'n': len(blocks) * BLOCK_N,
            'coverage': 'full' if len(blocks) == PANEL_BLOCKS else f'short_{len(blocks)}_blocks', 'n_eligible_trials': len(elig)}


def anchors_of(block):
    return block['b'] + PANEL_HOP * np.arange(BLOCK_N)


def make_partners(ds, trials, panel):
    """Per test block: the first other person (fixed seeded order) with an ss trial of the same stimulus covering the block."""
    others = sorted(p for p in trials if p != panel['person'])
    rng = np.random.default_rng(seed_of(SEED, ds, panel['person'], panel['cf'], 'partner'))
    order = [others[i] for i in rng.permutation(len(others))]
    out = []
    for blk in panel['blocks']:
        lo, hi = blk['b'] + WIN[0], blk['b'] + (BLOCK_N - 1) * PANEL_HOP + WIN[1]
        pick = None
        for q in order:
            for r in trials[q]:
                if r['kind'] == 'ss' and r['att'] == blk['stim'] and lo >= r['g0'] and hi <= r['g1'] and \
                        blk['b'] + (BLOCK_N - 1) * PANEL_HOP + TGT <= min(r['n'], r['att_len']):
                    pick = {'person': q, 'trial': r['trial']}
                    break
            if pick:
                break
        out.append(pick)
    return out


def legal_shifts(n_rows, hop_s, min_shift_s):
    return [k for k in range(1, n_rows) if min(k, n_rows - k) * hop_s >= min_shift_s - 1e-9]


def draw_bank(n_blocks, shifts, n_draw, seed):
    """Distinct tuples of per-block shifts, uniform without replacement (all tuples if fewer exist)."""
    total = len(shifts) ** n_blocks
    rng = np.random.default_rng(seed)
    if total <= n_draw:
        codes = np.arange(total)
    else:
        codes = np.sort(rng.choice(total, size=n_draw, replace=False))
    tup = np.stack(np.unravel_index(codes, (len(shifts),) * n_blocks), 1)
    return np.asarray(shifts)[tup].astype(np.int64)


def perms_from_shifts(shift_tuples, n_blocks, block_n=BLOCK_N):
    """Row permutations (descriptor row index paired with EEG row i) for block-wise circular shifts."""
    base = np.arange(block_n)
    out = []
    for t in shift_tuples:
        out.append(np.concatenate([b * block_n + (base + int(k)) % block_n for b, k in enumerate(t[:n_blocks])]))
    return np.stack(out).astype(np.int64)


def make_queries(ds, trials):
    from ..paper import ext_common as X
    from ..run_attention import _runs, _windows
    c = X.Cache(ds); a = c.arr
    bytrial = {(p, r['trial']): r for p, rows in trials.items() for r in rows}
    out = []
    for cf in CFS:
        for sf in SFS:
            _, test = c.unit_people(sf)
            segs = [{'p': p, 'code': code, 'e0': int(e), 'role': role, 'trial': t, 'st': int(st)}
                    for p, code, e, role, t, st in zip(a['cs_person'], a['cs_code'], a['cs_e0'], a[f'cs_role{cf}'], a['cs_trial'], a['cs_st'])
                    if p in set(test) and role == 'test']
            for w in _windows(_runs(segs, SEG128), QUERY_SEGS):
                p, t, st0 = w[0]['p'], w[0]['trial'], w[0]['st']
                assert all(s['trial'] == t and s['st'] == st0 + i * SEG128 for i, s in enumerate(w))
                r = bytrial[(p, t)]; q = st0 + QUERY_FIRST + QUERY_HOP * np.arange(QUERY_N)
                assert q[0] + WIN[0] >= st0 and q[-1] + WIN[1] <= st0 + QUERY_LEN and q[-1] + TGT <= st0 + QUERY_LEN
                assert st0 >= r['g0'] - 0 and st0 + QUERY_LEN <= r['n']
                ok_att = q[0] - r['att_lead'] >= 0 and q[-1] + TGT - r['att_lead'] <= r['att_len']
                ok_ign = q[0] - r['ign_lead'] >= 0 and q[-1] + TGT - r['ign_lead'] <= r['ign_len']
                out.append({'person': p, 'cf': cf, 'sf': sf, 'trial': t, 'st0': int(st0), 'code': w[0]['code'],
                            'status': 'ok' if ok_att and ok_ign else 'stimulus_not_covered'})
    return out


def freeze(ds):
    """Panels, partners, null banks and queries for one cohort -> defs_v1/<ds>/defs.json (0444)."""
    path = DEFS / ds / 'defs.json'
    if path.exists():
        print('frozen', path, sha(path)); return read(path)
    sc = read(DEFS / ds / 'scan.json'); trials = sc['trials']
    acf = read(DEFS / 'acf_check.json'); min_shift = acf['decision']['min_shift_s']
    folds = {p['id']: p['fold'] for p in sc['people']}
    panels = {}
    for pid in sorted(trials):
        for cf in CFS:
            for kind in ('test', 'calib'):
                pn = make_panel(ds, pid, trials[pid], cf, kind)
                if kind == 'test':
                    pn['partners'] = make_partners(ds, trials, pn)
                    pn['noise_seed'] = seed_of(SEED, ds, pid, cf, 'noise')
                pn['id'] = f'{ds}:{pid}:cf{cf}:{kind}'
                panels[pn['id']] = pn
    hop_s = PANEL_HOP / FS
    sh = legal_shifts(BLOCK_N, hop_s, min_shift)
    banks = {'n128': draw_bank(4, sh, N_NULL, seed_of(SEED, 'bank', 4)).tolist(),
             'n64': draw_bank(2, sh, N_NULL, seed_of(SEED, 'bank', 2)).tolist(),
             'n32': draw_bank(1, sh, N_NULL, seed_of(SEED, 'bank', 1)).tolist()}
    att_shifts = legal_shifts(QUERY_N, QUERY_HOP / FS, min_shift)
    queries = make_queries(ds, trials)
    body = {'version': VERSION, 'dataset': ds, 'scan_sha256': sha(DEFS / ds / 'scan.json'), 'acf_sha256': sha(DEFS / 'acf_check.json'),
            'min_shift_s': min_shift, 'geometry': {'fs': FS, 'window': list(WIN), 'window_ms': list(SUPPORT_MS), 'target': TGT,
                                                    'descriptor_points': TGT // 2, 'guard': GUARD[ds], 'block_n': BLOCK_N,
                                                    'panel_blocks': PANEL_BLOCKS, 'panel_hop': PANEL_HOP, 'block_gap': BLOCK_GAP,
                                                    'query_len': QUERY_LEN, 'query_first': QUERY_FIRST, 'query_hop': QUERY_HOP,
                                                    'query_n': QUERY_N},
            'folds': folds, 'panels': panels, 'block_shifts_legal': sh, 'null_banks': banks,
            'null_design': {'n128': f'blockwise_circular_shift_4x32_hop0.5s_min{min_shift:g}s_{len(banks["n128"])}draws',
                            'n64': f'blockwise_circular_shift_2x32_hop0.5s_min{min_shift:g}s_{len(banks["n64"])}draws',
                            'n32': f'blockwise_circular_shift_1x32_hop0.5s_min{min_shift:g}s_{len(banks["n32"])}draws',
                            'attention': f'query_circular_shift_152_hop0.125s_min{min_shift:g}s_{len(att_shifts)}shifts'},
            'attention_shifts': att_shifts, 'queries': queries, 'sources': sources()}
    body['panels_sha256'] = digest(panels); body['queries_sha256'] = digest(queries); body['banks_sha256'] = digest(banks)
    write(path, body); path.chmod(0o444)
    cov = {}
    for pn in panels.values():
        cov[(pn['kind'], pn['coverage'])] = cov.get((pn['kind'], pn['coverage']), 0) + 1
    npart = sum(x is not None for pn in panels.values() if pn['kind'] == 'test' for x in pn['partners'])
    ntb = sum(len(pn['blocks']) for pn in panels.values() if pn['kind'] == 'test')
    print(ds, 'frozen', sha(path), {f'{k}/{c}': v for (k, c), v in cov.items()}, 'partners', npart, '/', ntb,
          'queries', len(queries), 'not_covered', sum(q['status'] != 'ok' for q in queries), 'att shifts', len(att_shifts), flush=True)
    return body


def defs(ds):
    path = DEFS / ds / 'defs.json'
    assert path.exists() and not os.access(path, os.W_OK), f'{path} must be frozen (0444)'
    return read(path)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=('scan', 'acf', 'freeze', 'status'))
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.step == 'scan':
        for ds in DATASETS:
            scan(ds)
    elif a.step == 'acf':
        acf_check()
    elif a.step == 'freeze':
        for ds in DATASETS:
            freeze(ds)
    else:
        for ds in DATASETS:
            p = DEFS / ds / 'defs.json'
            print(ds, p.exists() and sha(p))


if __name__ == '__main__':
    main()
