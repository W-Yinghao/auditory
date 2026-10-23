"""W7 §2.1 audit A: does the dependence of the frozen representation on the stimulus views survive noise EEG / wrong audio?

Frozen design docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md §2.1 (sha256 DESIGN_SHA), descriptive family
W7_AUDIT:dtu of results/auditory_alignment_v3/paper/w7/W7_FAMILIES_v1.json; implementation choices frozen in
private/auditory_alignment_v3/paper/w7_v1/APPENDUM_RAD_03.md (+ count erratum APPENDUM_RAD_04.md) before any audit output.

Systems: B0, TCS, TNCE at seed 3401 (the R1 frozen units; CALRA is quoted from W5 audit v2, not recomputed).
Geometry (W5 audit_dtu, paper.calra_cbramod): the frozen DTU cs list (aln41/frozen.py public_unit), role=test segments of each
content fold cf, anchors = every 4th of the 16 frozen cs anchors, blocks = one anchor offset x up to 32 consecutive test
segments of one person.
Representation U: the frozen PCA64 slot features of the person's own pooled fold (pca_sf<fold> of the unit), three slots.
Audio views V: the prior33 contract views of the attended stream at the anchor's 64 Hz tick floor((st + off) / 2): env (8
samples), ss (8 frames x 4 PCA), sc (8) from the DTU cohort bank of the C6 manifest, through the fixed prior33 heads
(normalize((y / sigma) P^T), the audio side of the TCS objective). The rich views (ss, sc) exist only for the NH original streams;
HI rows carry env only (masked, never fabricated).
Conditions: real (stored U), noise_eeg (U of Gaussian EEG with each anchor-channel's mean / SD over the crop span, W5 noise_like,
forwarded through the arm's backbone and projected with the same PCA), wrong_audio (real U, each row's audio taken from another
segment by a person-level cross-family bijection over the person's test segments of the content fold (the aln41.source TCS_WRONG shift
construction; families = DTU content groups), shared by the 4 offsets and 3 views), identical_rows (row 0's crops forwarded 32 times, row 0's audio repeated).
Statistic: CS(U_k; V_v) = paper.cs_atlas estimator (aln41.cs_qmi_reference.cs_qmi) per block, slot k and view v; block value
= sum_k q0_k mean_{v present} CS; per person: blocks averaged within content fold, then the two content folds. Null: 1,000
permutations, each an independent uniform permutation of every block's audio rows (shared by slots, views and conditions);
quantile = (#null < true + 0.5 #null == true) / 1000. Bandwidths: per (arm, cf, person fold) on the fold's training people's
fit / es cs anchors (real stored U, the same 4 offsets), lower median, U pooled over the 3 slots, one per view; reused for every
condition.
CLI: --views (CPU) | --make-plan | --smoke | --worker | --unit ID | --summarize (CPU)
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core

ROOT = Path(core.REPO)
W7 = Path(core.OUT) / 'paper' / 'w7_v1'
OUT = W7 / 'audit'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/w7_v1/audit')
RESULTS = ROOT / 'results/auditory_alignment_v3/paper/w7'
DESIGN = ROOT / 'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md'
DESIGN_SHA = 'c4b461b0a6754af0ba04720320b0acc3f8c907a37f90369a4a250a612a92746c'
FAMILIES = RESULTS / 'W7_FAMILIES_v1.json'
FAMILIES_SHA = 'a95aa35f0f47733f9b1ad57427bd1cc477056459c6555c94cb980fb730982421'
APPENDUM = W7 / 'APPENDUM_RAD_03.md'
ERRATUM = W7 / 'APPENDUM_RAD_04.md'
ARMS, SEED, CFS = ('B0', 'TCS', 'TNCE'), 3401, (0, 1)
EVERY, BLOCK, N_PERM = 4, 32, 1000
VIEWS = ('env', 'ss', 'sc')
CONDITIONS = ('real', 'noise_eeg', 'wrong_audio', 'identical_rows')
SIGMA_ROWS, RNG_SEED = 2000, 20261023
NAME, LANE, SBATCH = 'c3_s35pw7audit', 's35_paper_w7_audit', 'slurm/aln35_paper_w7_audit.sbatch'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def write(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + '.tmp'); tmp.write_text(json.dumps(obj, indent=1, default=float) + '\n'); os.replace(tmp, path)


def digest(v, n=16):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:n]


def keyed_rng(*key):
    return np.random.default_rng(RNG_SEED + int(hashlib.sha256('|'.join(map(str, key)).encode()).hexdigest()[:8], 16))


def sources():
    a = ROOT / 'auditory_alignment_v3'
    files = [Path(__file__), a / 'aln41/frozen.py', a / 'aln41/timebank.py', a / 'aln41/time_access.py', a / 'aln41/cs_qmi_reference.py',
             a / 'paper/cs_atlas.py', a / 'paper/ext_common.py', a / 'prior33/views.py', a / 'prior33/model.py',
             ROOT / 'auditory_alignment/data.py', ROOT / 'auditory_alignment_v2/run.py', ROOT / 'auditory_alignment_v2/foundation_adapter.py']
    return {str(p.relative_to(ROOT)): sha(p) for p in files}


def bindings():
    assert sha(DESIGN) == DESIGN_SHA and sha(FAMILIES) == FAMILIES_SHA, 'frozen W7 design / families drift'
    for a in (APPENDUM, ERRATUM):
        assert a.exists() and not os.access(a, os.W_OK), f'{a.name} must exist and be read-only'
    return {'design_sha256': DESIGN_SHA, 'families_sha256': FAMILIES_SHA, 'appendum_rad_03_sha256': sha(APPENDUM),
            'appendum_rad_04_sha256': sha(ERRATUM)}


# ----------------------------------------------------------------------------------------------- frozen units / geometry
def frozen_unit(arm, cf):
    from ..aln41 import frozen as FZ
    plan = FZ.read(FZ.BASE / 'plan.json')
    row = next(r for r in plan['rows'] if r['arm'] == arm and r['dataset'] == 'dtu' and r['content_fold'] == cf)
    unit = FZ.read(FZ.BASE / 'units' / f'{row["id"]}.json'); assert unit['status'] == 'complete' and not unit['probe']
    dest = Path(unit['dest']); assert sha(dest / 'arrays.npz') == unit['array_sha256'] and sha(dest / 'meta.json') == unit['meta_sha256']
    return row, dest, FZ.read(dest / 'meta.json')


def cs_arrays(dest):
    with np.load(dest / 'arrays.npz', allow_pickle=False) as z:
        return {k: z[k] for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role', 'cs_env_att', 'cs_offsets', 'person')}


def blocks_of(A, meta):
    """[(person, offset index j (0..3 of the audit offsets), segment indices)] for role=test, non-dev people (W5 order)."""
    dev = set(meta['dev_people']); test = np.flatnonzero((A['cs_role'] == 'test') & ~np.isin(A['cs_person'], sorted(dev)))
    by = {}
    for i in test:
        by.setdefault(str(A['cs_person'][i]), []).append(int(i))
    out = []
    for p, js in sorted(by.items()):
        for j in range(len(A['cs_offsets'][::EVERY])):
            for k in range(0, len(js), BLOCK):
                out.append((p, j, np.asarray(js[k:k + BLOCK])))
    return out


def cross_family_bijection(fam, rng):
    """aln41.source.cross_family_bijection generalised to any family sizes: rows grouped by family (largest first, ties in a
    shuffled order, rows shuffled within family) and shifted by the largest family size m; fam[pi] != fam everywhere iff n >= 2m."""
    labels = list(dict.fromkeys(fam.tolist())); rng.shuffle(labels)
    labels.sort(key=lambda f: -int((fam == f).sum()))
    order = []
    for f in labels:
        rows = np.flatnonzero(fam == f); rng.shuffle(rows); order.extend(rows.tolist())
    order = np.array(order); n = len(order); m = int(max((fam == f).sum() for f in labels)); pi = np.empty(n, np.int64)
    pi[order] = order[(np.arange(n) + m) % n]
    return pi, bool(np.all(fam[pi] != fam))


# ----------------------------------------------------------------------------------------------- audio views (CPU, once)
def stream_maps():
    import os as _os
    from auditory_alignment import data as D
    from ..aln41 import source as SRC
    from ..prior33 import views as V
    man = SRC.open_manifest(); d = V.cohort_dir(man, 'dtu')
    st = V.cohort_streams(man, 'dtu', None, 'streams'); rs = V.cohort_streams(man, 'dtu', None, 'rich_streams')
    att = [s for s in st if s['kind'] == 'attended']
    pref = {}
    for s in att:
        assert s['key'][:10] not in pref, 'attended stream code prefix not unique'; pref[s['key'][:10]] = s
    rich_ok = {r['key']: bool(r['available']) for r in rs}
    cg = json.load(open(_os.path.join(D.DTU_KCS, 'content_groups.json')))['content']
    return man, d, pref, rich_ok, cg


def build_views():
    """Raw contract views y_env [n_cs, 4, 8], y_ss [n_cs, 4, 32], y_sc [n_cs, 4, 8] (NaN where rich is absent) of every frozen DTU
    cs segment at the 4 audit offsets, the content-group family of each segment, and the alignment check against cs_env_att."""
    from . import ext_common as XC
    out = STORE / 'views.npz'
    if out.exists():
        return read(OUT / 'views.json')
    man, d, pref, rich_ok, cg = stream_maps()
    env = np.load(os.path.join(d, 'env_f32.npy'), mmap_mode='r'); rich = np.load(os.path.join(d, 'rich_f32.npy'), mmap_mode='r')
    cache = XC.Cache('dtu'); ca = cache.arr
    _, dest, meta = frozen_unit('B0', 0); A = cs_arrays(dest)
    assert np.array_equal(ca['cs_e0'], A['cs_e0']) and np.array_equal(ca['cs_person'], A['cs_person']) and np.array_equal(ca['cs_code'], A['cs_code'])
    offs = A['cs_offsets'][::EVERY]; n = len(A['cs_e0'])
    Y = {'env': np.full((n, len(offs), 8), np.nan), 'ss': np.full((n, len(offs), 32), np.nan), 'sc': np.full((n, len(offs), 8), np.nan)}
    fam = np.empty(n, object); present = np.zeros(n, bool); lag_r = {L: [] for L in range(-4, 5)}; ref = []
    for i in range(n):
        s = pref[str(A['cs_code'][i])]; fam[i] = str(cg[s['key']]['group']); present[i] = rich_ok.get(s['key'], False)
        for j, o in enumerate(offs):
            t = (int(ca['cs_st'][i]) + int(o)) // 2; assert 0 <= t and t + 8 <= s['length'], (i, t)
            a = int(s['offset']) + t
            Y['env'][i, j] = env[a:a + 8]
            if present[i]:
                R = np.asarray(rich[a:a + 8], np.float64); Y['ss'][i, j] = R[:, 0:4].reshape(-1); Y['sc'][i, j] = R[:, 4]
            if j == 0:
                for L in lag_r:
                    lag_r[L].append(float(env[a + L]) if 0 <= t + L < s['length'] else np.nan)
                ref.append(A['cs_env_att'][i, int(np.flatnonzero(A['cs_offsets'] == o)[0])])
    ref = np.asarray(ref); corr = {}
    for L, v in lag_r.items():
        v = np.asarray(v); ok = np.isfinite(v); corr[L] = float(np.corrcoef(v[ok], ref[ok])[0, 1])
    best = max(corr, key=corr.get)
    check = {'lag_ticks_vs_pearson_r_first_anchor': corr, 'best_lag': best, 'r_at_0': corr[0], 'pass': abs(best) <= 1 and corr[0] >= 0.5}
    STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(out, y_env=Y['env'], y_ss=Y['ss'], y_sc=Y['sc'], family=fam.astype(str), rich_present=present, cs_e0=A['cs_e0'],
                        offsets=offs)
    rec = {'views_sha256': sha(out), 'n_cs': int(n), 'offsets_128hz': offs.tolist(), 'rich_present_fraction': float(present.mean()),
           'rich_present_by_group': {g: float(present[np.array([meta['groups'][p] == g for p in A['cs_person']])].mean()) for g in ('nh', 'hi')},
           'n_families': int(len(set(fam.tolist()))), 'alignment_check': check, 'bindings': bindings(), 'module_sha256': sha(__file__)}
    write(OUT / 'views.json', rec); print(json.dumps(rec, indent=1, default=float), flush=True)
    assert check['pass'], check
    return rec


def head_views(Yraw):
    """Fixed prior33 heads (the TCS audio side): {view: [.., 32] float64}, NaN rows kept NaN."""
    import torch
    from ..aln41 import source as SRC
    from ..prior33 import model as M
    man = SRC.open_manifest(); heads = M.fixed_heads(man, man.root)
    out = {}
    for v in VIEWS:
        y = Yraw[v]; flat = y.reshape(-1, y.shape[-1]); ok = np.isfinite(flat).all(1); res = np.full((len(flat), 32), np.nan)
        with torch.no_grad():
            res[ok] = heads[v](torch.as_tensor(flat[ok], dtype=torch.float32)).double().numpy()
        out[v] = res.reshape(*y.shape[:-1], 32)
    return out


# ----------------------------------------------------------------------------------------------- plan
def make_plan():
    v = read(OUT / 'views.json'); assert sha(STORE / 'views.npz') == v['views_sha256'] and v['alignment_check']['pass']
    rows = []
    for arm in ARMS:
        for cf in CFS:
            fr, dest, meta = frozen_unit(arm, cf)
            body = {'arm': arm, 'seed': SEED, 'content_fold': cf, 'frozen_unit': fr['id']}
            rows.append({**body, 'id': 'W7A_' + digest(body), 'dest': str(dest), 'array_sha256': sha(dest / 'arrays.npz'),
                         'pca_sha256': {sf: sha(dest / f'pca_sf{sf}.pt') for sf in range(5)}})
    body = {'version': 'W7_AUDIT_v1', 'rows': rows, 'sources': sources(), 'bindings': bindings(), 'views_sha256': v['views_sha256'],
            'settings': {'every': EVERY, 'block': BLOCK, 'n_perm': N_PERM, 'sigma_rows': SIGMA_ROWS, 'rng_seed': RNG_SEED,
                         'conditions': list(CONDITIONS), 'views': list(VIEWS)}}
    path = OUT / 'plan.json'
    if path.exists():
        old = read(path); assert all(old[k] == v_ for k, v_ in body.items()), 'immutable plan drift'
    else:
        write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('W7 audit plan', len(rows), sha(path), flush=True)


# ----------------------------------------------------------------------------------------------- GPU: noise / identical features
def noise_like(span, gen):
    """paper.calra_cbramod.noise_like: Gaussian [n, C, L] with each anchor-channel's mean and SD over its span."""
    import torch
    z = torch.randn(span.shape, generator=gen).to(span.device)
    return span.mean(-1, keepdim=True) + span.std(-1, keepdim=True) * z


def features(row, dev, max_blocks=None):
    """Stored real U, recomputed real U, noise U and identical-row U for the unit's audit blocks (PCA of the person's fold)."""
    import torch
    from auditory_alignment_v2.run import load_cohort
    from ..aln41 import frozen as FZ, timebank as TB
    dest = Path(row['dest']); meta = FZ.read(dest / 'meta.json'); A = cs_arrays(dest); cf = row['content_fold']
    b = {'experiment_id': row['frozen_unit'], 'family_id': 'ALN41', 'dataset': 'dtu', 'subject_fold': 0, 'content_fold': cf, 'seed': SEED,
         'spec': {'architecture': 'cbramod', 'window': 'full', 'objective': 'NCE', 'target': 'local', 'audio_head': 'fixed_features',
                  'training_task': 'paired_alignment', 'epochs': 1, 'adaptation': 'pretrained_full'}}
    coh = load_cohort(b); segs, parts = coh.segments, coh.participants
    cs = [i for i, s in enumerate(segs) if s['kind'] == 'cs' and s.get('s0_ign') is not None and s['role'] in ('fit', 'es', 'test')
          and not parts[s['p']].get('test_only')]
    assert np.array_equal(np.array([segs[i]['e0'] for i in cs]), A['cs_e0']) and np.array_equal(np.array([segs[i]['role'] for i in cs]), A['cs_role'])
    E = torch.as_tensor(coh.eeg, dtype=torch.float32); lay = TB.layout(coh.fs); lo, hi = lay[0][0], lay[2][1]
    offs = A['cs_offsets'][::EVERY]; blocks = blocks_of(A, meta)
    if max_blocks is not None:
        blocks = blocks[:max_blocks]
    net, q0, prov = FZ.arm_state(row['arm']); bb = FZ.backbone('dtu', net, dev)
    pcas = {sf: {k: v.to(dev) for k, v in torch.load(dest / f'pca_sf{sf}.pt', map_location='cpu').items()} for sf in range(5)}
    for sf in range(5):
        assert sha(dest / f'pca_sf{sf}.pt') == row['pca_sha256'][str(sf)]
    gen = torch.Generator().manual_seed(RNG_SEED + 17 + cf)

    def project(tok, sf):            # tok [B, 3, C*200] float16 -> [B, 3, 64] (frozen.pca_apply)
        p = pcas[sf]; X = tok.float().to(dev)
        return ((((X - p['mu']) / p['sd']) @ p['components'].T)).cpu().numpy().astype(np.float32)

    def tok_of(crops):
        with torch.no_grad():
            B = crops[0].shape[0]; h = bb(TB.crop_inputs(crops, coh.fs))[:, :, 0]
            return h.reshape(3, B, -1).transpose(0, 1).half()
    rows_real, rows_rec, rows_noise, ident, info = [], [], [], [], []
    with np.load(dest / 'arrays.npz', allow_pickle=False) as z:
        stored = {sf: z[f'cs_pca_sf{sf}'] for sf in range(5)}
    for bi, (p, j, js) in enumerate(blocks):
        sf = int(meta['folds'][p]); o = int(offs[j]); kk = int(np.flatnonzero(A['cs_offsets'] == o)[0])
        anc = torch.as_tensor(A['cs_e0'][js] + o)
        span = E[:, anc[:, None] + torch.arange(lo, hi)[None]].permute(1, 0, 2).to(dev)
        c = [span[..., s - lo:t - lo] for s, t, _ in lay]; nz = noise_like(span, gen); cn = [nz[..., s - lo:t - lo] for s, t, _ in lay]
        ci = [x[:1].expand(BLOCK, *x.shape[1:]).contiguous() for x in c]
        rows_real.append(stored[sf][js, kk]); rows_rec.append(project(tok_of(c), sf)); rows_noise.append(project(tok_of(cn), sf))
        ui = project(tok_of(ci), sf); ident.append(ui)
        info.append({'person': p, 'offset_index': j, 'segments': js.tolist(), 'person_fold': sf, 'anchor_index': kk,
                     'identical_rows_max_abs_spread': float(np.abs(ui - ui[:1]).max())})
    del E, coh
    return {'real': rows_real, 'real_recomputed': rows_rec, 'noise_eeg': rows_noise, 'identical_rows': ident}, info, np.asarray(q0), prov


# ----------------------------------------------------------------------------------------------- CS and permutation null (torch)
def lower_median(d):
    d = np.asarray(d, np.float64).ravel(); k = (len(d) - 1) // 2
    return float(np.partition(d, k)[k])


def calibrate(row, meta, A, views_h):
    """{sf: (sigma_U, {view: sigma_v})} on the fold's training people's fit / es anchors at the audit offsets (real stored U)."""
    from scipy.spatial.distance import pdist
    out = {}
    offs_k = np.flatnonzero(np.isin(A['cs_offsets'], A['cs_offsets'][::EVERY]))
    with np.load(Path(row['dest']) / 'arrays.npz', allow_pickle=False) as z:
        for sf in range(5):
            train = sorted(meta['pca'][str(sf)]['train_people'])
            segs = np.flatnonzero(np.isin(A['cs_person'], train) & np.isin(A['cs_role'], ('fit', 'es')))
            pairs = np.array([(s, j) for s in segs for j in range(len(offs_k))])
            rng = keyed_rng(row['arm'], row['content_fold'], sf, 'sigma')
            pick = pairs if len(pairs) <= SIGMA_ROWS else pairs[np.sort(rng.choice(len(pairs), SIGMA_ROWS, replace=False))]
            U = z[f'cs_pca_sf{sf}'][pick[:, 0], offs_k[pick[:, 1]]].astype(np.float64)       # [n, 3, 64]
            su = lower_median(np.concatenate([pdist(U[:, k]) for k in range(U.shape[1])]))
            sv = {}
            for v in VIEWS:
                X = views_h[v][pick[:, 0], pick[:, 1]]; X = X[np.isfinite(X).all(1)]
                sv[v] = lower_median(pdist(X))
            out[sf] = (su, sv, {'n_anchor_rows': int(len(pick)), 'n_training_segments': int(len(segs))})
    return out


def block_stats(U, Vs, su, sv, q, perms, dev):
    """U [n, 3, 64]; Vs {view: [n, 32] or None}; perms [P, n]. Returns (true [3 slots, views], null [P, 3, views])."""
    import torch
    U = torch.as_tensor(np.asarray(U, np.float64), device=dev)
    K = torch.stack([torch.exp(-torch.cdist(U[:, k], U[:, k]).square() / (2 * su * su)) for k in range(U.shape[1])])   # [3, n, n]
    pv = torch.as_tensor(perms, device=dev)
    true, null = [], []
    for v, X in Vs.items():
        if X is None:
            true.append(torch.full((K.shape[0],), float('nan'), dtype=torch.float64, device=dev))
            null.append(torch.full((len(perms), K.shape[0]), float('nan'), dtype=torch.float64, device=dev)); continue
        X = torch.as_tensor(np.asarray(X, np.float64), device=dev)
        L = torch.exp(-torch.cdist(X, X).square() / (2 * sv[v] * sv[v]))
        kb, lb = K.mean(2), L.mean(1); logB = torch.log(K.mean((1, 2)) * L.mean())
        t = torch.log((K * L[None]).mean((1, 2))) + logB - 2 * torch.log((kb * lb[None]).mean(1))
        Lp = L[pv[:, :, None], pv[:, None, :]]                                         # [P, n, n]
        A_ = torch.einsum('kij,pij->pk', K, Lp) / L.numel(); C_ = torch.einsum('ki,pi->pk', kb, lb[pv]) / L.shape[0]
        nl = torch.log(A_) + logB[None] - 2 * torch.log(C_)
        true.append(t); null.append(nl)
    return torch.stack(true, 1).cpu().numpy(), torch.stack(null, 2).cpu().numpy()


def run_unit(row, probe=False):
    import torch
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    from ..aln41 import frozen as FZ
    dest = Path(row['dest']); meta = FZ.read(dest / 'meta.json'); A = cs_arrays(dest)
    with np.load(STORE / 'views.npz', allow_pickle=False) as z:
        assert np.array_equal(z['cs_e0'], A['cs_e0'])
        Yraw = {v: z[f'y_{v}'] for v in VIEWS}; fam = z['family']
    V = head_views(Yraw)
    tf = time.time(); feats, info, q0, prov = features(row, dev, max_blocks=4 if probe else None); tf = time.time() - tf
    sig = calibrate(row, meta, A, V); tb = time.time()
    wrong_src, wrong_ok = {}, {}                                             # person-level cross-family bijection (all test segments)
    for p in sorted({inf['person'] for inf in info}):
        js_all = np.flatnonzero((A['cs_person'] == p) & (A['cs_role'] == 'test'))
        pi, ok = cross_family_bijection(fam[js_all], keyed_rng(row['content_fold'], p, 'wrong'))
        wrong_src.update(zip(js_all.tolist(), js_all[pi].tolist())); wrong_ok[p] = ok
    per_block, acc = [], {}
    for bi, inf in enumerate(info):
        js = np.asarray(inf['segments']); j = inf['offset_index']; n = len(js); sf = inf['person_fold']
        su, sv, _ = sig[sf]
        rng = keyed_rng(row['content_fold'], inf['person'], j, bi)             # shared by the three arms (same blocks)
        perms = np.stack([rng.permutation(n) for _ in range(N_PERM)])
        ws = np.array([wrong_src[int(i)] for i in js]); wok = wrong_ok[inf['person']]
        Vb = {v: (V[v][js, j] if np.isfinite(V[v][js, j]).all() else None) for v in VIEWS}
        conds = {'real': (feats['real'][bi], Vb), 'noise_eeg': (feats['noise_eeg'][bi], Vb),
                 'wrong_audio': (feats['real'][bi], {v: (V[v][ws, j] if x is not None else None) for v, x in Vb.items()}),
                 'identical_rows': (feats['identical_rows'][bi][:n], {v: (np.repeat(x[:1], n, 0) if x is not None else None) for v, x in Vb.items()}),
                 'real_recomputed': (feats['real_recomputed'][bi], Vb)}
        scale = float(np.abs(feats['real'][bi]).max())
        rec = {'person': inf['person'], 'offset_index': j, 'n': int(n), 'person_fold': sf,
               'rich_present': bool(Vb['ss'] is not None), 'wrong_cross_family_ok': wok,
               'wrong_same_family_rows': int((fam[ws] == fam[js]).sum()),
               'identical_rows_max_abs_spread': inf['identical_rows_max_abs_spread'],
               'real_recompute_max_abs_diff': float(np.abs(feats['real_recomputed'][bi] - feats['real'][bi]).max()),
               'real_recompute_rel_diff': float(np.abs(feats['real_recomputed'][bi] - feats['real'][bi]).max()) / max(scale, 1e-12)}
        for c, (U, Vs) in conds.items():
            tr, nl = block_stats(U, Vs, su, sv, q0, perms, dev)
            vals = {'all': (float(q0 @ np.nanmean(tr, -1)), q0 @ np.nanmean(nl, -1).T)}
            for i, v in enumerate(VIEWS):
                if np.isfinite(tr[:, i]).all():
                    vals[v] = (float(q0 @ tr[:, i]), q0 @ nl[:, :, i].T)
            rec[c] = {'cs_slot_view': tr.tolist(), **{f'value_{v}': x[0] for v, x in vals.items()}}
            for v, (x, nn) in vals.items():
                d = acc.setdefault((c, v, inf['person']), {'val': [], 'null': []}); d['val'].append(x); d['null'].append(nn)
        per_block.append(rec)
    store = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; store.mkdir(parents=True, exist_ok=True, mode=0o700)
    people = {}
    nulls = {}
    for (c, v, p), d in acc.items():
        people.setdefault(p, {}).setdefault(c, {})[v] = {'value': float(np.mean(d['val'])), 'n_blocks': len(d['val'])}
        nulls[f'{c}|{v}|{p}'] = np.mean(np.stack(d['null']), 0).astype(np.float64)
    np.savez_compressed(store / 'person_nulls.npz', **nulls)
    out = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'q0': q0.tolist(), 'arm_provenance': prov,
           'sigmas': {str(sf): {'sigma_U': s[0], 'sigma_v': s[1], **s[2]} for sf, s in sig.items()}, 'people': people, 'blocks': per_block,
           'nulls_npz': str(store / 'person_nulls.npz'), 'nulls_sha256': sha(store / 'person_nulls.npz'),
           'checks': {'real_recompute_max_abs_diff': max(b['real_recompute_max_abs_diff'] for b in per_block),
                      'real_recompute_max_rel_diff': max(b['real_recompute_rel_diff'] for b in per_block),
                      'identical_rows_max_abs_spread': max(b['identical_rows_max_abs_spread'] for b in per_block),
                      'wrong_blocks_not_fully_cross_family': sum(not b['wrong_cross_family_ok'] for b in per_block),
                      'wrong_same_family_rows': sum(b['wrong_same_family_rows'] for b in per_block)},
           'timing': {'features_s': tf, 'cs_and_null_s': time.time() - tb, 'n_blocks': len(per_block),
                      'blocks_full_unit': len(blocks_of(A, meta))},
           'seconds': time.time() - t0, 'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job}
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', out)
    print(row['id'], row['arm'], row['content_fold'], 'complete', round(out['seconds'], 1), out['checks'], flush=True)
    return out


# ----------------------------------------------------------------------------------------------- fleet
def receipts():
    out = {'pass': [], 'other': []}
    if (OUT / 'plan.json').exists():
        ps = sha(OUT / 'plan.json')
        for p in sorted((OUT / 'probes').glob('*/receipt.json')):
            r = read(p)
            if r.get('plan_sha256') == ps:
                out['pass' if r.get('status') == 'pass' else 'other'].append(p)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 6, 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'plan.json').exists():
        return st
    plan = read(OUT / 'plan.json'); left = [r for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return {**st, 'state': 'failed_unit_review'}
    rec = receipts()
    if not rec['pass']:
        return {**st, 'state': 'engineering_probe_failed'} if rec['other'] else {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    return {**st, 'state': 'ready', 'ready': len(left), 'slots': 1, 'submit': [SBATCH, '--worker']}


def worker(plan):
    assert receipts()['pass'], 'no passing smoke'
    for row in plan['rows']:
        path = OUT / 'units' / f'{row["id"]}.json'
        if path.exists() or (OUT / 'units' / f'{row["id"]}.FAILED.json').exists():
            continue
        lock = OUT / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc < 0:
                raise SystemExit(f'unit ended by signal {-rc}')
            if rc or not path.exists():
                write(OUT / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('W7 audit unit failed')


def smoke(plan):
    """TCS cf0 on its first 4 blocks: finite CS, identical rows exactly identical, recomputed real U close to the stored U."""
    job = os.environ['SLURM_JOB_ID']; rec = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        row = next(r for r in plan['rows'] if r['arm'] == 'TCS' and r['content_fold'] == 0)
        u = run_unit(row, probe=True)
        assert all(np.isfinite(b[c]['value_all']) for b in u['blocks'] for c in CONDITIONS)
        assert u['checks']['identical_rows_max_abs_spread'] < 1e-4 and u['checks']['real_recompute_max_rel_diff'] < 1e-2, u['checks']
        rec['units'].append({k: u[k] for k in ('checks', 'timing', 'seconds', 'gpu_peak_mb', 'device')} | {'row': row['id'], 'blocks': len(u['blocks'])})
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', rec)


# ----------------------------------------------------------------------------------------------- summary (CPU)
def summarize():
    plan = read(OUT / 'plan.json'); groups = None; per = {}
    fz = next(f for f in read(FAMILIES)['families'] if f['id'] == 'W7_AUDIT:dtu')
    for row in plan['rows']:
        u = read(OUT / 'units' / f'{row["id"]}.json'); assert u['status'] == 'complete' and not u['probe']
        assert sha(u['nulls_npz']) == u['nulls_sha256']
        if groups is None:
            from ..aln41 import frozen as FZ
            groups = FZ.read(Path(row['dest']) / 'meta.json')['groups']
        with np.load(u['nulls_npz']) as z:
            for p, conds in u['people'].items():
                for c, views in conds.items():
                    for v, x in views.items():
                        per.setdefault((row['arm'], c, v, p), {})[row['content_fold']] = {'val': x['value'], 'null': z[f'{c}|{v}|{p}']}
    cells = {}
    for (arm, c, v, p), byc in per.items():
        if sorted(byc) != list(CFS):
            continue
        val = float(np.mean([byc[cf]['val'] for cf in CFS]))
        null = np.mean([byc[cf]['null'] for cf in CFS], 0)
        q = float(((null < val).sum() + 0.5 * (null == val).sum()) / len(null))
        cells.setdefault(f'{arm}:{c}', {}).setdefault(v, {})[p] = {'cs': val, 'null_mean': float(null.mean()), 'null_sd': float(null.std(ddof=1)),
                                                                   'quantile': q, 'group': groups[p]}
    summ = {}
    for key, views in cells.items():
        summ[key] = {}
        for v, people in views.items():
            s = {}
            for g in ('nh', 'hi', 'all'):
                vals = [x for x in people.values() if g == 'all' or x['group'] == g]
                if vals:
                    s[g] = {'n_people': len(vals), 'cs_mean': float(np.mean([x['cs'] for x in vals])),
                            'excess_over_null_mean': float(np.mean([x['cs'] - x['null_mean'] for x in vals])),
                            'quantile_mean': float(np.mean([x['quantile'] for x in vals])),
                            'fraction_quantile_ge_0.95': float(np.mean([x['quantile'] >= 0.95 for x in vals]))}
            summ[key][v] = s
    out = {'version': 'W7_AUDIT_v1', 'bindings': plan['bindings'], 'plan_sha256': sha(OUT / 'plan.json'), 'definition': __doc__,
           'per_person': cells, 'summary': summ, 'family_inputs': {fz['id']: {'members': fz['members'], 'descriptive': True,
                                                                              'value': 'per-person CS (view "all") and its null quantile'}},
           'calra_reference': 'W5 audit v2 (results/auditory_alignment_v3/paper/calra_cbramod/W5_AUDIT_v2.json), quoted, not recomputed'}
    fam = {'family_id': fz['id'], 'descriptive': True, 'members': []}
    for m in fz['members']:
        s = summ.get(m, {}).get('all', {}).get('all')
        fam['members'].append({'name': m, **(s or {'status': 'missing'})})
    os.umask(0o022); RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'W7_AUDIT.json').write_text(json.dumps(out, indent=1, default=float) + '\n')
    (RESULTS / 'W7_AUDIT_FAMILIES.json').write_text(json.dumps({'version': 'W7_AUDIT_FAMILIES_v1', 'input_sha256': sha(RESULTS / 'W7_AUDIT.json'),
                                                                'families': [fam]}, indent=1, default=float) + '\n')
    print(json.dumps(fam, indent=1, default=float))


def main():
    ap = argparse.ArgumentParser()
    for flag in ('views', 'make_plan', 'smoke', 'worker', 'summarize'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.views:
        build_views(); return
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); assert plan['sources'] == sources(), 'frozen source drift'
    assert plan['bindings'] == bindings()
    if a.unit:
        run_unit(next(r for r in plan['rows'] if r['id'] == a.unit)); return
    if a.smoke:
        smoke(plan); return
    if a.summarize:
        summarize(); return
    assert a.worker
    worker(plan)


if __name__ == '__main__':
    main()
