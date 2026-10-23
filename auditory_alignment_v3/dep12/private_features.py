"""DEP12 Agent P: private children, frozen binding and the 03 §1 private feature exporter.

Package contract: private/auditory_alignment_v3/dep12/package (v1.2), docs 02 §6.2, §7.1 and 03 §1, §4.4, §5.

Binding (CPU, frozen 0444 before any private feature or result exists; `--make-binding`):
- Children: aln35.support_runtime.load_kids() = auditory_alignment.data.load_private() (64 children, the existing approved
  preprocessing: GX_stage_001 accepted epochs, since-last-deviant >= 0, per-record z-score of the inherited loader) plus the
  audited onset times. Outer folds = the existing 5 person folds (hc.folds seed 20261005); source-ES rows = es_mask.
- Protocol registered per child: child60 = audited alternative sequence (EVENT_AUDIT_REPORT §5), all others regular.
- U0 queries: 'all_trials' (primary; the existing ALN3.5 / ALN4.1 query set) and 'contract_query' (the support-contract
  query rows, shared with U10).
- U10: aln35.support_contract.private_split(kid) and select_support(pool, n10, id) with seeds 351410..351414.
- Profile panels (03 §4.2/4.4): four runs of 32 consecutive accepted trials, one run per physical block; target block
  positions floor((j + 0.5) * B / 4), j = 0..3, nearest eligible (>= 32 trials) unused block, ties to the earlier block;
  within a block the start minimising (number of onset gaps > 1.5 x child median SOA, distance to the centred start, start).
  Nesting: n32 = {r0}, n64 = {r0, r2}, n128 = {r0, r1, r2, r3} (runs in time order).
- Profile null: legal block-relative cyclic shifts of the complete (label, history) run sequence relative to the EEG rows,
  per run s in [7, 25] (minimum shift 7 = max(ceil(2 s / SOA), history span 6 + 1)); runs shifted independently; all
  combinations when <= 199, otherwise 199 distinct combinations from a fixed per-child RNG. Labels and history move together.
- Support-only delta maps (03 §5.3 step 3): per U10 draw, per physical block the selected rows in time order; legal cyclic
  remaps s in 1..m-1 with every paired time distance >= 2.0 s (max(2 s, 0.8 s real input support)); blocks combined;
  blocks without a legal remap stay in place (fixed rows); at most 199 distinct maps. Only selected rows are touched.
- Support CV (03 §5.3 step 2): groups = physical blocks of the selected rows in time order, K = min(5, blocks) contiguous
  groups; if fewer than 2 blocks, K = min(5, n) contiguous time chunks; training rows within 2.0 s of any validation row are
  removed; a fold is usable with >= 1 training and >= 1 validation row; CV executes with >= 2 groups and >= 2 usable folds.
- Fixed-policy inner split: hc.inner_split(outer-training children, seed 351600 + outer fold, frac 0.2).
- Strict twins: history_interface.strict_twin_map with the history_interface seed rule, source role (allowed = ES rows) and
  query role (allowed = all rows).

Input (03 §1): the real [-0.2, +0.6) s epoch (20 x 200 at 250 Hz) -> resample to 160 points (200 Hz; resampler named in the
binding) -> per-channel standardisation with the outer-training children's real samples of that outer fold -> prepend 40
zeros -> 1 s container [20, 200] with pad_mask (True = padding, first 40 samples). The padding never enters the statistics.

Exporter (GPU, one unit per encoder): for each outer fold, U = encoder.represent(x, channel_names, pad_mask) for all trials;
PCA64 on the outer-training children's source-ES rows (aln41.frozen.pca_fit rule: z-score on those rows, SVD); stores the
PCA scores of every trial and the full U of the kernel rows (profile-panel rows of every child + support-pool rows of the
fold's test children).
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import numpy as np

from .. import core
from ..aln34 import learning_budget as LB

ROOT = Path(core.REPO)
REC = ROOT / 'private/auditory_alignment_v3/dep12/private'
BIND_DIR = REC / 'binding'
BINDING = BIND_DIR / 'binding_v1.json'
BINDING_NPZ = BIND_DIR / 'binding_v1_arrays.npz'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/dep12/private_features')
RESULTS = ROOT / 'results/auditory_alignment_v3/dep12'
PACKAGE = ROOT / 'private/auditory_alignment_v3/dep12/package'

VERSION = 'DEP12_PRIVATE_BINDING_v1'
FOLDS = (0, 1, 2, 3, 4)
SUPPORT_SEEDS = (351410, 351411, 351412, 351413, 351414)
PANEL_RUNS, RUN_LEN = 4, 32
NEST = {'n32': (0,), 'n64': (0, 2), 'n128': (0, 1, 2, 3)}
HISTORY_SPAN = 6
MIN_SEP_S = 2.0
REAL_SUPPORT_S = 0.8
MAX_MAPS = 199
PROFILE_MIN_SHIFT = None          # computed per child: max(ceil(2 s / median SOA), HISTORY_SPAN + 1)
CV_GAP_S = 2.0
CV_MAX_FOLDS = 5
INNER_SEED, INNER_FRAC = 351600, 0.2
MAP_SEED = 3512000
ALT_PROTOCOL = {'child60': 'alt_sequence_child60_audited'}
FS_IN, N_IN, N_REAL, PAD_FRONT, N_CONTAINER = 250, 200, 160, 40, 200
PCA_DIM, PCA_SEED = 64, 3437
RESAMPLER = 'fft_scipy_resample_v1'   # aln41.timebank.resample (verified against scipy.signal.resample)
sha, dumps = LB.sha, LB.dumps


def digest(value, n=64):
    return hashlib.sha256(dumps(value).encode()).hexdigest()[:n]


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    LB.write(path, value)


def write_frozen(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f'frozen file exists: {path}')
    LB.write(path, value)
    path.chmod(0o444)


def child_seed(base, *parts):
    return base + int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:8], 16) % 1_000_000


def sources():
    files = [Path(__file__), ROOT / 'auditory_alignment_v3/aln35/support_contract.py',
             ROOT / 'auditory_alignment_v3/aln35/support_runtime.py', ROOT / 'auditory_alignment_v3/aln35/history_interface.py',
             ROOT / 'auditory_alignment/data.py', ROOT / 'auditory_c3/c3dl/hc.py', ROOT / 'auditory_c3/private_mi2.py',
             ROOT / 'auditory_alignment_v3/aln41/timebank.py']
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}


# ----------------------------------------------------------------------------------------------- children
def load_children():
    from ..aln35 import support_runtime as SR
    return SR.load_kids()


def protocol(kid):
    return ALT_PROTOCOL.get(kid['id'], 'regular')


def block_order(kid):
    return list(dict.fromkeys(kid['block'].tolist()))


def median_soa(kid):
    t, b = kid['_s35_onset_seconds'], kid['block']
    d = np.diff(t)[b[1:] == b[:-1]]
    return float(np.median(d))


# ----------------------------------------------------------------------------------------------- profile panels
def panel_runs(kid):
    """Four contiguous 32-trial runs in distinct physical blocks (rule in the module docstring)."""
    blocks = block_order(kid); B = len(blocks)
    t = kid['_s35_onset_seconds']; soa = median_soa(kid)
    rows_of = {b: np.flatnonzero(kid['block'] == b) for b in blocks}
    eligible = [i for i, b in enumerate(blocks) if len(rows_of[b]) >= RUN_LEN]
    chosen = []
    for j in range(PANEL_RUNS):
        target = math.floor((j + .5) * B / PANEL_RUNS)
        left = [i for i in eligible if i not in chosen]
        if not left:
            break
        chosen.append(min(left, key=lambda i: (abs(i - target), i)))
    runs = []
    for i in sorted(chosen):
        rows = rows_of[blocks[i]]; L = len(rows)
        assert np.all(np.diff(rows) == 1), 'block rows not contiguous in trial order'
        gaps = np.diff(t[rows]) > 1.5 * soa
        centre = (L - RUN_LEN) / 2

        def key(s):
            return (int(gaps[s:s + RUN_LEN - 1].sum()), abs(s - centre), s)
        s = min(range(L - RUN_LEN + 1), key=key)
        r = rows[s:s + RUN_LEN]
        runs.append({'block': int(blocks[i]), 'block_position': i, 'start_in_block': int(s), 'rows': r.tolist(),
                     'n_gaps': key(s)[0], 'span_s': float(t[r[-1]] - t[r[0]])})
    return runs


def min_profile_shift(kid):
    return max(int(math.ceil(MIN_SEP_S / median_soa(kid))), HISTORY_SPAN + 1)


def profile_maps(kid, runs, panel):
    """Permutations of the panel rows (indices into the panel order) = independent legal cyclic shifts per run."""
    idx = NEST[panel]
    use = [runs[i] for i in idx if i < len(runs)]
    m = min_profile_shift(kid)
    legal = [list(range(m, RUN_LEN - m + 1)) for _ in use]
    n = RUN_LEN * len(use)
    total = int(np.prod([len(x) for x in legal])) if use else 0
    if not use or total == 0:
        return np.zeros((0, n), np.int64), {'n_runs': len(use), 'legal_per_run': [len(x) for x in legal], 'combinations': total}
    if total <= MAX_MAPS:
        combos = [list(c) for c in np.array(np.meshgrid(*legal, indexing='ij')).reshape(len(use), -1).T]
    else:
        rng = np.random.default_rng(child_seed(MAP_SEED, kid['id'], panel)); seen = set(); combos = []
        while len(combos) < MAX_MAPS:
            c = tuple(int(rng.choice(x)) for x in legal)
            if c not in seen:
                seen.add(c); combos.append(list(c))
    perms = []
    for c in combos:
        p = np.empty(n, np.int64)
        for r, s in enumerate(c):
            o = r * RUN_LEN
            p[o:o + RUN_LEN] = o + (np.arange(RUN_LEN) + s) % RUN_LEN
        perms.append(p)
    perms = np.stack(perms)
    assert np.all(perms != np.arange(n)[None]), 'profile map with a fixed row'
    return perms, {'n_runs': len(use), 'legal_per_run': [len(x) for x in legal], 'combinations': total,
                   'min_shift_trials': m, 'n_maps': int(len(perms))}


# ----------------------------------------------------------------------------------------------- support-only maps and CV
def support_maps(kid, rows, seed_tag):
    """Support-only cyclic remaps of the selected rows (never touching unselected rows)."""
    rows = np.sort(np.asarray(rows)); t = kid['_s35_onset_seconds']; blk = kid['block']
    pos = {int(r): i for i, r in enumerate(rows)}
    per_block = []
    for b in dict.fromkeys(blk[rows].tolist()):
        r = rows[blk[rows] == b]; m = len(r); legal = []
        for s in range(1, m):
            if np.min(np.abs(t[r] - t[np.roll(r, -s)])) >= MIN_SEP_S - 1e-9:
                legal.append(s)
        per_block.append({'block': int(b), 'rows': r.tolist(), 'legal_shifts': legal})
    movable = [pb for pb in per_block if pb['legal_shifts']]
    fixed_rows = sum(len(pb['rows']) for pb in per_block if not pb['legal_shifts'])
    info = {'n_rows': int(len(rows)), 'n_blocks': len(per_block), 'n_movable_blocks': len(movable),
            'fixed_row_fraction': fixed_rows / max(1, len(rows)),
            'legal_per_block': [len(pb['legal_shifts']) for pb in per_block]}
    if not movable:
        return np.zeros((0, len(rows)), np.int64), {**info, 'combinations': 0, 'n_maps': 0}
    total = int(np.prod([len(pb['legal_shifts']) for pb in movable]))
    if total <= MAX_MAPS:
        combos = [list(c) for c in np.array(np.meshgrid(*[pb['legal_shifts'] for pb in movable], indexing='ij')).reshape(len(movable), -1).T]
    else:
        rng = np.random.default_rng(child_seed(MAP_SEED, kid['id'], 'support', seed_tag)); seen = set(); combos = []
        while len(combos) < MAX_MAPS:
            c = tuple(int(rng.choice(pb['legal_shifts'])) for pb in movable)
            if c not in seen:
                seen.add(c); combos.append(list(c))
    perms = []
    for c in combos:
        p = np.arange(len(rows))
        for pb, s in zip(movable, c):
            r = np.asarray(pb['rows']); src = np.roll(r, -s)
            for a, bb in zip(r, src):
                p[pos[int(a)]] = pos[int(bb)]
        perms.append(p)
    perms = np.stack(perms).astype(np.int64)
    moved = np.concatenate([[pos[int(x)] for x in pb['rows']] for pb in movable])
    assert np.all(perms[:, moved] != moved[None]), 'support map keeps a movable row'
    for p in perms:
        assert np.min(np.abs(t[rows[moved]] - t[rows[p[moved]]])) >= MIN_SEP_S - 1e-9
    return perms, {**info, 'combinations': total, 'n_maps': int(len(perms))}


def cv_folds(kid, rows):
    """[(train_rows, val_rows)] in global row ids, plus coverage metadata; labels never read."""
    rows = np.sort(np.asarray(rows)); t = kid['_s35_onset_seconds']; blk = kid['block']
    blocks = list(dict.fromkeys(blk[rows].tolist()))
    if len(blocks) >= 2:
        K = min(CV_MAX_FOLDS, len(blocks))
        groups = [np.concatenate([rows[blk[rows] == b] for b in g]) for g in np.array_split(np.array(blocks), K)]
        mode = 'physical_block_groups'
    else:
        K = min(CV_MAX_FOLDS, len(rows))
        groups = [g for g in np.array_split(rows, K) if len(g)]
        mode = 'contiguous_time_chunks'
    folds, usable = [], 0
    for g in groups:
        rest = rows[~np.isin(rows, g)]
        if len(rest) and len(g):
            near = np.min(np.abs(t[rest][:, None] - t[g][None, :]), axis=1) < CV_GAP_S
            train = rest[~near]
        else:
            train = rest[:0]
        ok = len(train) >= 1 and len(g) >= 1
        usable += ok
        folds.append({'train': train.tolist(), 'val': g.tolist(), 'usable': bool(ok), 'gap_removed': int(len(rest) - len(train))})
    execute = len(groups) >= 2 and usable >= 2
    validated = sum(len(f['val']) for f in folds if f['usable'])
    return folds, {'mode': mode, 'n_groups': len(groups), 'n_usable_folds': usable, 'executes': bool(execute),
                   'validated_fraction': validated / max(1, len(rows)), 'gap_s': CV_GAP_S}


# ----------------------------------------------------------------------------------------------- binding
def make_binding():
    """CPU; freezes every split / panel / map / fold definition before any private feature exists."""
    from ..aln35 import support_contract as SC, history_interface as HI, science_binding as SB
    from auditory_c3.c3dl import hc
    if BINDING.exists():
        raise FileExistsError(BINDING)
    kids = load_children()
    assert len(kids) == 64 and sum(k['group'] == 'HA' for k in kids) == 55
    children, arrays = [], {}
    for i, k in enumerate(kids):
        cid = k['id']; n = len(k['y'])
        split = SC.private_split(k)
        sel = SC.select_support(split['pool'], split['n10'], cid, groups=k['block'][split['pool']])
        runs = panel_runs(k)
        panel_rows = np.concatenate([np.asarray(r['rows']) for r in runs]) if runs else np.zeros(0, np.int64)
        assert len(np.unique(panel_rows)) == len(panel_rows)
        rec = {'index': i, 'id': cid, 'group': k['group'], 'fold': int(k['fold']), 'protocol': protocol(k), 'n_trials': n,
               'n_es': int(k['es_mask'].sum()), 'median_soa_s': median_soa(k), 'n_blocks': len(block_order(k)),
               'geometry_sha256': k['_s35_geometry_sha256'],
               'split': {'n_pool': len(split['pool']), 'n_query': len(split['query']), 'n10': int(split['n10']),
                         'guard_excluded': [int(x) for x in split['guard_excluded']],
                         'boundary_removed_support': split['boundary_removed_support'],
                         'boundary_removed_query': split['boundary_removed_query']},
               'panel': {'runs': runs, 'n_rows': int(len(panel_rows)), 'min_shift_trials': min_profile_shift(k)},
               'profile_maps': {}, 'support': {}}
        arrays[f'{cid}/pool'] = np.asarray(split['pool'], np.int64)
        arrays[f'{cid}/query'] = np.asarray(split['query'], np.int64)
        arrays[f'{cid}/panel_rows'] = panel_rows.astype(np.int64)
        for panel in NEST:
            perms, info = profile_maps(k, runs, panel)
            arrays[f'{cid}/profile_maps/{panel}'] = perms
            rec['profile_maps'][panel] = info
        for s in SUPPORT_SEEDS:
            rows = np.asarray(sel[f'U10_{s}'], np.int64)
            arrays[f'{cid}/U10_{s}'] = rows
            perms, minfo = support_maps(k, rows, s)
            arrays[f'{cid}/U10_{s}/maps'] = perms
            folds, cinfo = cv_folds(k, rows)
            for j, f in enumerate(folds):
                arrays[f'{cid}/U10_{s}/cv{j}/train'] = np.asarray(f['train'], np.int64)
                arrays[f'{cid}/U10_{s}/cv{j}/val'] = np.asarray(f['val'], np.int64)
            rec['support'][str(s)] = {'n': int(len(rows)), 'rows_sha256': digest(rows.tolist()), 'delta_maps': minfo,
                                      'cv': {**cinfo, 'folds': [{'usable': f['usable'], 'n_train': len(f['train']), 'n_val': len(f['val']),
                                                                 'gap_removed': f['gap_removed']} for f in folds]}}
        seed = HI.SEED + int(SB.digest(cid)[:8], 16)
        arrays[f'{cid}/twin_source_es'] = HI.strict_twin_map(k['bin'], k['block'], np.flatnonzero(k['es_mask']), seed)
        arrays[f'{cid}/twin_query_all'] = HI.strict_twin_map(k['bin'], k['block'], np.arange(n), seed)
        for name in ('y', 'bin', 'block'):
            arrays[f'{cid}/{name}'] = np.asarray(k[name], np.int64)
        arrays[f'{cid}/es_mask'] = np.asarray(k['es_mask'], bool)
        arrays[f'{cid}/onset_s'] = np.asarray(k['_s35_onset_seconds'], np.float64)
        children.append(rec)
    inner = {}
    for f in FOLDS:
        train = [k for k in kids if k['fold'] != f]
        itr, idev = hc.inner_split(train, INNER_SEED + f, INNER_FRAC)
        inner[str(f)] = {'inner_train': sorted(k['id'] for k in itr), 'inner_dev': sorted(k['id'] for k in idev),
                         'seed': INNER_SEED + f, 'frac': INNER_FRAC}
    BIND_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = BINDING_NPZ.with_name(BINDING_NPZ.name + '.tmp.npz')
    np.savez_compressed(tmp, **arrays); os.replace(tmp, BINDING_NPZ); BINDING_NPZ.chmod(0o444)
    body = {'version': VERSION, 'created': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID'),
            'package_zip_sha256': (ROOT / 'private/auditory_alignment_v3/dep12/PACKAGE_ZIP.sha256').read_text().split()[0],
            'sources': sources(), 'arrays_sha256': sha(BINDING_NPZ), 'children': children, 'inner_split': inner,
            'constants': {'support_seeds': list(SUPPORT_SEEDS), 'panel_runs': PANEL_RUNS, 'run_len': RUN_LEN, 'nest': {k: list(v) for k, v in NEST.items()},
                          'history_span_trials': HISTORY_SPAN, 'min_sep_s': MIN_SEP_S, 'real_support_s': REAL_SUPPORT_S, 'max_maps': MAX_MAPS,
                          'cv_gap_s': CV_GAP_S, 'cv_max_folds': CV_MAX_FOLDS, 'map_seed': MAP_SEED,
                          'input': {'fs_in': FS_IN, 'n_in': N_IN, 'n_real': N_REAL, 'pad_front': PAD_FRONT, 'container': N_CONTAINER,
                                    'resampler': RESAMPLER, 'standardisation': 'per channel, outer-training children real samples, per outer fold',
                                    'pad_mask': 'True = zero padding; samples 0..39'},
                          'pca': {'dim': PCA_DIM, 'rows': 'outer-training children source-ES rows', 'rule': 'aln41.frozen.pca_fit (z-score, SVD)'},
                          'u0_queries': ['all_trials', 'contract_query'],
                          'twin_seed_rule': 'history_interface.SEED + int(science_binding.digest(child_id)[:8], 16)'},
            'results_seen': False}
    write_frozen(BINDING, body)
    print(json.dumps({'binding': str(BINDING), 'sha256': sha(BINDING), 'arrays_sha256': body['arrays_sha256']}), flush=True)


class Binding:
    """Read-only view of the frozen binding (verifies both hashes)."""

    def __init__(self):
        self.meta = read(BINDING)
        assert sha(BINDING_NPZ) == self.meta['arrays_sha256'], 'binding arrays changed'
        self.sha256 = sha(BINDING)
        with np.load(BINDING_NPZ, allow_pickle=False) as z:
            self.a = {k: z[k] for k in z.files}
        self.children = self.meta['children']
        self.ids = [c['id'] for c in self.children]
        self.by_id = {c['id']: c for c in self.children}
        self.fold = {c['id']: c['fold'] for c in self.children}

    def arr(self, cid, name):
        return self.a[f'{cid}/{name}']

    def train_ids(self, f):
        return [c for c in self.ids if self.fold[c] != f]

    def test_ids(self, f):
        return [c for c in self.ids if self.fold[c] == f]

    def offsets(self):
        """Global row offset of each child in the concatenated trial order (binding child order)."""
        out, o = {}, 0
        for c in self.children:
            out[c['id']] = o; o += c['n_trials']
        return out, o

    def kernel_rows(self, f):
        """Local (child, row) pairs whose full U is stored for fold f: panel rows of every child + pool rows of test children."""
        out = {}
        for c in self.ids:
            rows = set(self.arr(c, 'panel_rows').tolist())
            if self.fold[c] == f:
                rows |= set(self.arr(c, 'pool').tolist())
            out[c] = np.array(sorted(rows), np.int64)
        return out


# ----------------------------------------------------------------------------------------------- input preparation (03 §1)
def resample_real(x):
    """x [N, 20, 200] at 250 Hz (torch) -> [N, 20, 160] at 200 Hz, FFT method (scipy.signal.resample semantics)."""
    from ..aln41 import timebank as TB
    assert x.shape[-1] == N_IN
    return TB.resample(x, N_REAL)


def fold_stats(xr, owner, train_index):
    """Per-channel mean / SD over the real samples of outer-training children (float64)."""
    import torch
    m = torch.as_tensor(np.isin(owner, train_index))
    s = torch.zeros(xr.shape[1], dtype=torch.float64); ss = torch.zeros_like(s); n = 0
    idx = torch.nonzero(m).flatten()
    for a in range(0, len(idx), 4096):
        b = xr[idx[a:a + 4096]].to(torch.float64)
        s += b.sum((0, 2)); ss += (b * b).sum((0, 2)); n += b.shape[0] * b.shape[2]
    mu = s / n; sd = torch.sqrt(torch.clamp(ss / n - mu * mu, min=0))
    assert torch.all(sd > 0)
    return mu.float(), sd.float(), int(n)


def container(xr_batch, mu, sd):
    """[B, 20, 160] -> standardised, 40 leading zeros -> [B, 20, 200]; pad_mask [200] True = padding."""
    import torch
    import torch.nn.functional as F
    z = (xr_batch - mu[None, :, None]) / sd[None, :, None]
    out = F.pad(z, (PAD_FRONT, 0))
    assert out.shape[-1] == N_CONTAINER
    return out


def pad_mask():
    m = np.zeros(N_CONTAINER, bool); m[:PAD_FRONT] = True
    return m


def channel_names():
    from auditory_alignment_v2.foundation_adapter import CHANNELS, ALIASES
    return [ALIASES.get(c, c) for c in CHANNELS['private_bdf']]


# ----------------------------------------------------------------------------------------------- encoders
def load_encoder(name, device):
    """dep12/encoders.py (Agent S, INTERFACES.md v1); B0 included. No temporary path remains."""
    from . import encoders as E
    return E.load(name, device)


def encoder_spec(name):
    from . import encoders as E
    spec = E.REGISTRY.get(name) or E.refresh().get(name)
    return spec


# ----------------------------------------------------------------------------------------------- export (GPU)
def export(name, dest, probe=False, batch=512, device='cuda', folds=FOLDS):
    """All five outer folds for one encoder; returns meta. probe=True restricts to 6 children (engineering only)."""
    import torch
    import gc
    bind = Binding(); dev = torch.device(device)
    kids = load_children()
    assert [k['id'] for k in kids] == bind.ids
    for k in kids:
        c = bind.by_id[k['id']]
        assert c['n_trials'] == len(k['y']) and np.array_equal(bind.arr(k['id'], 'y'), k['y'])
        assert c['geometry_sha256'] == k['_s35_geometry_sha256']
    use = kids if not probe else [k for k in kids if k['fold'] in (0, 1)][:6]
    ids = [k['id'] for k in use]
    owner = np.concatenate([[i] * len(k['y']) for i, k in enumerate(use)])
    local = np.concatenate([np.arange(len(k['y'])) for k in use])
    X = torch.as_tensor(np.concatenate([k['x'] for k in use]).astype(np.float32))
    del kids, use; gc.collect()
    t0 = time.time()
    XR = torch.cat([resample_real(X[a:a + 4096].to(dev)).float().cpu() for a in range(0, len(X), 4096)])
    del X; gc.collect()
    enc = load_encoder(name, dev)
    from . import encoders as E
    names, pm = channel_names(), pad_mask()
    pm_t = torch.as_tensor(pm)
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    meta = {'encoder': name, 'encoder_meta': enc.meta, 'encoder_spec': encoder_spec(name), 'encoders_py_sha256': sha(E.__file__),
            'probe': probe,
            'binding_sha256': bind.sha256, 'children': ids, 'n_trials': int(len(owner)), 'folds': {}, 'pad_mask_front': PAD_FRONT,
            'resampler': RESAMPLER, 'sources': sources(), 'device': torch.cuda.get_device_name(0) if dev.type == 'cuda' else 'cpu'}
    if dev.type == 'cuda':
        torch.cuda.reset_peak_memory_stats()
    for f in folds:
        tf = time.time()
        train_ix = [i for i, c in enumerate(ids) if bind.fold[c] != f]
        mu, sd, n_samp = fold_stats(XR, owner, train_ix)
        U = None
        for a in range(0, len(XR), batch):
            xb = container(XR[a:a + batch].to(dev), mu.to(dev), sd.to(dev))
            u = enc.represent(xb, names, pm_t.to(dev)).float()
            assert torch.isfinite(u).all(), 'non-finite representation'
            if U is None:
                U = torch.empty((len(XR), u.shape[1]), dtype=torch.float32)
            U[a:a + len(u)] = u.cpu()
        meta.setdefault('last_call', enc.last_call)
        es = np.concatenate([bind.arr(c, 'es_mask') for c in ids])
        fit_rows = np.flatnonzero(np.isin(owner, train_ix) & es)
        P = pca_fit(U, fit_rows, dev)
        scores = pca_apply(U, P, dev)
        krows = bind.kernel_rows(f)
        sel = np.concatenate([np.flatnonzero((owner == i) & np.isin(local, krows[c])) for i, c in enumerate(ids)])
        np.savez(dest / f'fold{f}.npz', pca=scores.astype(np.float32), kernel_index=sel.astype(np.int64),
                 U_kernel=U[sel].numpy().astype(np.float32), owner=owner.astype(np.int64), local=local.astype(np.int64),
                 pca_mu=P['mu'].numpy(), pca_sd=P['sd'].numpy(), pca_components=P['components'].numpy(),
                 std_mu=mu.numpy(), std_sd=sd.numpy(), pad_mask=pm)
        meta['folds'][str(f)] = {'std_n_samples': n_samp, 'std_mu': mu.tolist(), 'std_sd': sd.tolist(), 'pca_rows': int(len(fit_rows)),
                                 'pca_row_sha256': digest(fit_rows.tolist()), 'pca_explained': P['explained'], 'U_dim': int(U.shape[1]),
                                 'U_norm_range': [float(U.norm(dim=1).min()), float(U.norm(dim=1).max())], 'n_kernel_rows': int(len(sel)),
                                 'array_sha256': sha(dest / f'fold{f}.npz'), 'seconds': time.time() - tf}
        del U, scores; gc.collect()
    meta['gpu_peak_mb'] = torch.cuda.max_memory_allocated() / 2 ** 20 if dev.type == 'cuda' else None
    meta['seconds'] = time.time() - t0
    write(dest / 'meta.json', meta)
    return meta


def pca_fit(U, rows, dev):
    import torch
    X = U[torch.as_tensor(rows)].to(dev)
    mu = X.mean(0); sd = X.std(0) + 1e-6; Z = (X - mu) / sd
    dim = min(PCA_DIM, Z.shape[1], len(Z) - 1)
    _, S, Vh = torch.linalg.svd(Z, full_matrices=False)
    return {'mu': mu.cpu(), 'sd': sd.cpu(), 'components': Vh[:dim].cpu(), 'explained': float((S[:dim] ** 2).sum() / (S ** 2).sum())}


def pca_apply(U, P, dev, chunk=20000):
    import torch
    mu, sd, comp = P['mu'].to(dev), P['sd'].to(dev), P['components'].to(dev).T
    return torch.cat([(((U[a:a + chunk].to(dev) - mu) / sd) @ comp).cpu() for a in range(0, len(U), chunk)]).numpy()


def load_fold(dest, f):
    with np.load(Path(dest) / f'fold{f}.npz', allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--make-binding', action='store_true')
    ap.add_argument('--show-binding', action='store_true')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    if a.make_binding:
        make_binding()
    if a.show_binding:
        b = Binding()
        print(json.dumps({'sha256': b.sha256, 'children': len(b.children)}))


if __name__ == '__main__':
    main()
