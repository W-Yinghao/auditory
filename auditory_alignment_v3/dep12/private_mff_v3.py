"""VERSION 3 (DECISIONS P24): v2 plus the ext2 follow-up arm cs_pair_noise@{3401,3407,3413} via dep12/encoders_v3.py;
receipt smoke_v3; mechanism stage private_mechanism_v2 (shared marker REC/mechanism_v2).

--- v2 description ---
VERSION 2 (DECISIONS P23): private_mff (v1, untouched) plus the extension-1 mechanism controls raw_cs@3407/3413 and
cs_pair_wrong@3407/3413, resolved through dep12/encoders_v2.py (which imports encoders.py unchanged). Same binding, specs,
units, use and analysis directories and unit-id rule. The v1 GPU smoke (complete B0 MFF unit) passed; v2 adds a CPU
equivalence receipt (smoke_v2). Added CPU stage: private_mechanism whenever its inputs change (shared marker with the
feature lane).

--- v1 description ---
DEP12 Agent P: MFF pediatric lanes as a second private cohort and the cross-stimulus question for the DEP12 representations
(DECISIONS P21; researcher scope widening 2026-10-23). Lane c3_s35dPmff (shim aln35/dep12_priv_mff_fleet.py).

Data / identities: aln41.cross_stim.gated_records (pure tone 35 records / 33 identities; bapa 25 / 24); per-record z-score and
since-last-deviant >= 0 exactly as aln41.cross_stim.load; child = (lane, identity) pooling its gated records; identity folds =
cross_stim.fold_of (sha256 rank mod 5). Pseudonym mff_<sha256(identity)[:10]>_pt|_ba per (person, lane) in results (shared person stem links the same-day
pairs); identity keys only in private/.
Fits (as ALN4.1 F_CROSS_STIM): within g (pure tone), transfer f (pure tone -> bapa fold f, identity-disjoint), refit f (bapa).
Input: real 0.8 s -> 160 samples (aln41.timebank.resample) -> 40 leading zeros, montage 'mff' (E1..E128); no extra
training-side standardisation (P21). Representation: dep12.encoders.represent (final-layer tokens, LN, flatten, L2).
Per fit: PCA64 (z-score + SVD) on <= 8190 seeded training rows; q0 / B1 / history offset logistic (C = 1) on all training
rows; per test child AUC of the EEG part of the readout (P22; AUC of p_E / p_B1 beside it) and G = mean log2 p_E(y) - log2 p_B1(y); δ profile n128 (4 x 32-trial runs in distinct
record-blocks, run-wise cyclic shifts >= max(ceil(2 s / SOA), 7), <= 199 maps) with σ grouped over the fit's training panels.
Commands (Slurm only): --make-binding | --register | --smoke | --worker | --unit ID | --use NAME | --analyze | --post | --status
"""
from __future__ import annotations

import argparse
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
from scipy.special import expit

from . import private_features as PF

BASE = PF.REC / 'mff_v1'
STORE = PF.STORE / 'mff_v1'
BINDING = BASE / 'binding' / 'binding_mff_v1.json'
BINDING_NPZ = BASE / 'binding' / 'binding_mff_v1_arrays.npz'
NAME, LANE, SBATCH = 'c3_s35dPmff', 's35_dep12_private_mff', 'slurm/aln35_dep12_priv_mff_v3.sbatch'
VERSION = 'DEP12_PRIVATE_MFF_v1'
ENCODERS = ['B0'] + [f'{o}@{s}' for s in (3401, 3407, 3413) for o in ('cs_pair', 'info_nce', 'sigmoid')] + ['raw_cs@3401', 'cs_pair_wrong@3401']
EXT1 = ['raw_cs@3407', 'raw_cs@3413', 'cs_pair_wrong@3407', 'cs_pair_wrong@3413']     # encoders_v2 extension 1
ENCODERS = ENCODERS + EXT1
EXT2 = ['cs_pair_noise@3401', 'cs_pair_noise@3407', 'cs_pair_noise@3413']     # encoders_v3 follow-up ext2
ENCODERS = ENCODERS + EXT2
LANES = ('mff_puretone', 'mff_bapa')
FITS = [('within', g) for g in range(5)] + [('transfer', f) for f in range(5)] + [('refit', f) for f in range(5)]
PCA_MAX_ROWS, PCA_SEED = 8190, 3437 + 500
SEEDS = (3401, 3407, 3413)
NULL_DESIGN = 'dep12_private_mff_profile_v1: independent cyclic shift of each 32-trial run (label+history), shift >= max(ceil(2s/SOA),7)'
read, write, sha, digest = PF.read, PF.write, PF.sha, PF.digest


def sources():
    files = [Path(__file__), Path(PF.__file__), PF.ROOT / 'auditory_alignment_v3/aln41/cross_stim.py',
             PF.ROOT / 'auditory_alignment_v3/aln35/history_interface.py', PF.ROOT / 'auditory_alignment_v3/dep12/dependence_measure.py']
    return {str(p.relative_to(PF.ROOT)): sha(p) for p in files}


def pseudonym(identity):
    return 'mff_' + hashlib.sha256(identity.encode()).hexdigest()[:10]


# ----------------------------------------------------------------------------------------------- binding (CPU)
def meta_rows(records):
    """Row metadata in aln41.cross_stim.load order, without loading EEG."""
    from auditory_c3.private_mi2 import hist_codes
    from ..aln41 import cross_stim as XS
    rows = {k: [] for k in ('child', 'y', 'bin', 'block', 'record', 'onset')}
    children, key = [], {}
    for ri, r in enumerate(records):
        with np.load(XS.STAGE / 'epochs' / f'{r["record_id"]}.npz', allow_pickle=False) as s:
            acc = s['accepted'].astype(bool)
            h = hist_codes(s['previous_code'][acc], s['previous_run_length'][acc])['since_last_deviant']
            y, blk, on = s['y'][acc].astype(np.int64), s['block_id'][acc].astype(np.int64), s['onset_seconds'][acc].astype(np.float64)
            assert str(s['lane']) == r['lane'] and float(s['rate_hz']) == 250 and int(s['pre_samples']) == 50
        ok = h >= 0
        c = key.setdefault((r['lane'], r['identity']), len(children))
        if c == len(children):
            children.append({'lane': r['lane'], 'identity': r['identity']})
        n = int(ok.sum())
        for k, v in (('child', np.full(n, c)), ('y', y[ok]), ('bin', h[ok].astype(np.int64)), ('block', blk[ok]),
                     ('record', np.full(n, ri)), ('onset', on[ok])):
            rows[k].append(v)
    return {k: np.concatenate(v) for k, v in rows.items()}, children


def child_panel(rows, ix):
    """ix: the child's global rows (record-major, trial order). Same run rule as private_features.panel_runs on record-blocks."""
    rec, blk, t = rows['record'][ix], rows['block'][ix], rows['onset'][ix]
    keys = list(dict.fromkeys(zip(rec.tolist(), blk.tolist())))
    B = len(keys)
    pos_of = {k: np.flatnonzero((rec == k[0]) & (blk == k[1])) for k in keys}
    d = np.diff(t); same = (rec[1:] == rec[:-1]) & (blk[1:] == blk[:-1])
    soa = float(np.median(d[same]))
    eligible = [i for i, k in enumerate(keys) if len(pos_of[k]) >= PF.RUN_LEN]
    chosen = []
    for j in range(PF.PANEL_RUNS):
        target = math.floor((j + .5) * B / PF.PANEL_RUNS)
        left = [i for i in eligible if i not in chosen]
        if not left:
            break
        chosen.append(min(left, key=lambda i: (abs(i - target), i)))
    runs = []
    for i in sorted(chosen):
        p = pos_of[keys[i]]; L = len(p)
        assert np.all(np.diff(p) == 1)
        gaps = np.diff(t[p]) > 1.5 * soa; centre = (L - PF.RUN_LEN) / 2
        s = min(range(L - PF.RUN_LEN + 1), key=lambda s_: (int(gaps[s_:s_ + PF.RUN_LEN - 1].sum()), abs(s_ - centre), s_))
        runs.append({'record_block': [int(keys[i][0]), int(keys[i][1])], 'local_rows': p[s:s + PF.RUN_LEN].tolist(),
                     'n_gaps': int(gaps[s:s + PF.RUN_LEN - 1].sum())})
    m = max(int(math.ceil(PF.MIN_SEP_S / soa)), PF.HISTORY_SPAN + 1)
    return runs, soa, m


def panel_maps(cid, runs, m):
    legal = [list(range(m, PF.RUN_LEN - m + 1)) for _ in runs]
    n = PF.RUN_LEN * len(runs)
    total = int(np.prod([len(x) for x in legal])) if runs else 0
    if not runs or total == 0:
        return np.zeros((0, n), np.int64)
    rng = np.random.default_rng(PF.child_seed(PF.MAP_SEED, cid, 'mff_n128')); seen = set(); combos = []
    if total <= PF.MAX_MAPS:
        combos = [list(c) for c in np.array(np.meshgrid(*legal, indexing='ij')).reshape(len(runs), -1).T]
    while len(combos) < min(PF.MAX_MAPS, total):
        c = tuple(int(rng.choice(x)) for x in legal)
        if c not in seen:
            seen.add(c); combos.append(list(c))
    perms = np.stack([np.concatenate([r * PF.RUN_LEN + (np.arange(PF.RUN_LEN) + s) % PF.RUN_LEN for r, s in enumerate(c)]) for c in combos])
    assert np.all(perms != np.arange(n)[None])
    return perms.astype(np.int64)


def fit_split(children, kind, f):
    from ..aln41 import cross_stim as XS
    lane = [c['lane'] for c in children]; ident = [c['identity'] for c in children]
    bfold = XS.fold_of([i for i, l in zip(ident, lane) if l == 'mff_bapa'])
    pfold = XS.fold_of([i for i, l in zip(ident, lane) if l == 'mff_puretone'])
    test_ids = {i for i, v in (pfold if kind == 'within' else bfold).items() if v == f}
    src_lane = 'mff_bapa' if kind == 'refit' else 'mff_puretone'
    dst_lane = 'mff_puretone' if kind == 'within' else 'mff_bapa'
    train = [c for c, (i, l) in enumerate(zip(ident, lane)) if l == src_lane and i not in test_ids]
    test = [c for c, (i, l) in enumerate(zip(ident, lane)) if l == dst_lane and i in test_ids]
    assert not {ident[c] for c in train} & {ident[c] for c in test}
    return train, test


def make_binding():
    from ..aln41 import cross_stim as XS
    if BINDING.exists():
        raise FileExistsError(BINDING)
    recs = XS.gated_records()
    rows, children = meta_rows(recs)
    assert {l: len({c['identity'] for c in children if c['lane'] == l}) for l in LANES} == {'mff_puretone': 33, 'mff_bapa': 24}
    arrays = {k: v for k, v in rows.items()}
    kids = []
    for ci, c in enumerate(children):
        ix = np.flatnonzero(rows['child'] == ci)
        runs, soa, m = child_panel(rows, ix)
        pid = pseudonym(c['identity']) + ('_pt' if c['lane'] == 'mff_puretone' else '_ba')
        arrays[f'{pid}/rows'] = ix.astype(np.int64)
        arrays[f'{pid}/panel_local'] = np.concatenate([r['local_rows'] for r in runs]).astype(np.int64) if runs else np.zeros(0, np.int64)
        arrays[f'{pid}/maps'] = panel_maps(pid, runs, m)
        kids.append({'index': ci, 'id': pid, 'person': pseudonym(c['identity']), 'lane': c['lane'], 'n_trials': int(len(ix)), 'n_deviant': int(rows['y'][ix].sum()),
                     'median_soa_s': soa, 'min_shift_trials': m, 'panel_runs': runs, 'n_panel': int(PF.RUN_LEN * len(runs)),
                     'n_maps': int(len(arrays[f'{pid}/maps'])), 'n_records': int(len(np.unique(rows['record'][ix])))})
    assert len({k['id'] for k in kids}) == len(kids)
    fits = {}
    for kind, f in FITS:
        tr, te = fit_split(children, kind, f)
        fits[f'{kind}{f}'] = {'train': [kids[i]['id'] for i in tr], 'test': [kids[i]['id'] for i in te]}
    BINDING.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = BINDING_NPZ.with_name(BINDING_NPZ.name + '.tmp.npz')
    np.savez_compressed(tmp, **arrays); os.replace(tmp, BINDING_NPZ); BINDING_NPZ.chmod(0o444)
    priv = BASE / 'binding' / 'identity_map_private.json'
    write(priv, {k['id']: c['identity'] for k, c in zip(kids, children)}); priv.chmod(0o400)
    PF.write_frozen(BINDING, {'version': VERSION, 'created': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID'),
                              'records': recs, 'records_sha256': digest(recs), 'children': kids, 'fits': fits, 'arrays_sha256': sha(BINDING_NPZ),
                              'sources': sources(), 'results_seen': False,
                              'rules': {'input': 'real 0.8 s -> 160 (timebank.resample) -> 40 leading zeros; montage mff; no extra standardisation',
                                        'pca': f'z-score + SVD on <= {PCA_MAX_ROWS} seeded training rows per fit (seed {PCA_SEED} + fit index)',
                                        'readout': 'q0 / B1 / history offset logistic (C=1) on all training rows of the fit',
                                        'profile': 'n128 x1, δ kernel, σ grouped lower median over the fit training children panels'}})
    print(json.dumps({'binding': str(BINDING), 'sha256': sha(BINDING), 'children': len(kids),
                      'n_panel': sorted({k['n_panel'] for k in kids}), 'n_maps': sorted({k['n_maps'] for k in kids})}), flush=True)


class Binding:
    def __init__(self):
        self.meta = read(BINDING)
        assert sha(BINDING_NPZ) == self.meta['arrays_sha256']
        self.sha256 = sha(BINDING)
        with np.load(BINDING_NPZ, allow_pickle=False) as z:
            self.a = {k: z[k] for k in z.files}
        self.kids = self.meta['children']; self.by_id = {k['id']: k for k in self.kids}

    def rows(self, cid):
        return self.a[f'{cid}/rows']

    def panel_global(self, cid):
        return self.rows(cid)[self.a[f'{cid}/panel_local']]


# ----------------------------------------------------------------------------------------------- export (GPU)
def export(name, dest, device='cuda', batch=256):
    import torch
    import gc
    from ..aln41 import cross_stim as XS
    from . import encoders_v3 as E
    from . import encoders as E1
    bind = Binding(); dev = torch.device(device)
    X, rows, children = XS.load(bind.meta['records'])
    for k in ('y', 'bin', 'block', 'record', 'child'):
        assert np.array_equal(rows[k], bind.a[k]), f'row drift: {k}'
    t0 = time.time()
    XR = torch.cat([PF.resample_real(torch.as_tensor(X[a:a + 2048]).to(dev)).float().cpu() for a in range(0, len(X), 2048)])
    del X; gc.collect()
    enc = E.load(name, dev)
    names = [f'E{i}' for i in range(1, 129)]
    pm = PF.pad_mask(); pm_t = torch.as_tensor(pm).to(dev)
    U = None
    for a in range(0, len(XR), batch):
        import torch.nn.functional as F
        xb = F.pad(XR[a:a + batch].to(dev), (PF.PAD_FRONT, 0))
        u = enc.represent(xb, names, pm_t).float()
        assert torch.isfinite(u).all()
        if U is None:
            U = torch.empty((len(XR), u.shape[1]), dtype=torch.float32)
        U[a:a + len(u)] = u.cpu()
    del XR; gc.collect()
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    out = {}; fit_meta = {}
    child_of = {k['id']: k['index'] for k in bind.kids}
    for j, (kind, f) in enumerate(FITS):
        tr = [child_of[c] for c in bind.meta['fits'][f'{kind}{f}']['train']]
        rows_tr = np.flatnonzero(np.isin(bind.a['child'], tr))
        rng = np.random.default_rng(PCA_SEED + j)
        pick = np.sort(rows_tr if len(rows_tr) <= PCA_MAX_ROWS else rng.choice(rows_tr, PCA_MAX_ROWS, replace=False))
        P = PF.pca_fit(U, pick, dev)
        out[f'pca/{kind}{f}'] = PF.pca_apply(U, P, dev).astype(np.float32)
        fit_meta[f'{kind}{f}'] = {'pca_rows': int(len(pick)), 'pca_rows_sha256': digest(pick.tolist()), 'explained': P['explained']}
    kidx = np.concatenate([bind.panel_global(k['id']) for k in bind.kids])
    out['kernel_index'] = kidx.astype(np.int64)
    out['U_kernel'] = U[torch.as_tensor(kidx)].numpy().astype(np.float32)
    np.savez(dest / 'features.npz', **out)
    meta = {'encoder': name, 'encoder_meta': enc.meta, 'last_call': enc.last_call, 'encoders_py_sha256': sha(E1.__file__), 'encoders_v3_py_sha256': sha(E.__file__), 'binding_sha256': bind.sha256,
            'n_trials': int(len(U)), 'U_dim': int(U.shape[1]), 'fits': fit_meta, 'array_sha256': sha(dest / 'features.npz'), 'seconds': time.time() - t0,
            'device': torch.cuda.get_device_name(0) if dev.type == 'cuda' else 'cpu', 'sources': sources(),
            'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20 if dev.type == 'cuda' else None}
    write(dest / 'meta.json', meta)
    return meta


# ----------------------------------------------------------------------------------------------- analysis (CPU)
def use_encoder(name, force=False):
    from ..aln35 import history_interface as HI
    from auditory_c3.c3dl import hc
    from . import private_use as PU
    DM = PU.measure_module(); bind = Binding()
    sp = next(s for s in specs() if s['encoder'] == name)
    rec = read(BASE / 'units' / f'{sp["id"]}.json')
    dest = Path(sp['store']); assert sha(dest / 'features.npz') == rec['array_sha256']
    out_path = BASE / 'use' / (name.replace('@', '_at_') + '.json')
    if out_path.exists() and not force:
        return read(out_path)
    with np.load(dest / 'features.npz', allow_pickle=False) as z:
        F_ = {k: z[k] for k in z.files}
    kpos = {int(g): i for i, g in enumerate(F_['kernel_index'])}
    y_all, bin_all = bind.a['y'], bind.a['bin']
    res = {'encoder': name, 'unit_id': sp['id'], 'binding_sha256': bind.sha256, 'fits': {}, 'encoder_meta': rec['encoder_meta']}
    for kind, f in FITS:
        key = f'{kind}{f}'; fit = bind.meta['fits'][key]; S = F_[f'pca/{key}'].astype(np.float64)
        tr_rows = np.concatenate([bind.rows(c) for c in fit['train']])
        q0 = hc.q0_table([{'y': y_all[bind.rows(c)], 'bin': bin_all[bind.rows(c)]} for c in fit['train']])
        X = S[tr_rows]; y = y_all[tr_rows].astype(np.float64); off = PU.logit(q0[bin_all[tr_rows]])
        mu, sd = X.mean(0), X.std(0) + 1e-8
        w, rec_e = HI.fit_offset((X - mu) / sd, y, off); b1, _ = HI.fit_intercept(y, off)
        panels = {c: F_['U_kernel'][[kpos[int(g)] for g in bind.panel_global(c)]].astype(np.float64) for c in fit['train']}
        full = max(len(v) for v in panels.values())
        try:
            cal = DM.calibrate_grouped_overlap_sigma({c: v for c, v in panels.items() if len(v) == full}, calibration_scope='target_train_unlabelled',
                                                     panel_id=f'dep12_mff/{name}/{key}/n128_train_panels')
            cal.pop('person_ids', None); sigma = cal['overlap_sigma']
        except ValueError as exc:
            cal, sigma = {'calibration_status': 'calibration_degenerate', 'reason': str(exc)}, None
        per = {}
        for c in fit['test']:
            r = bind.rows(c); yy = y_all[r]; o = PU.logit(q0[bin_all[r]])
            lE = o + np.column_stack([np.ones(len(r)), (S[r] - mu) / sd]) @ w; lB = o + b1
            m = PU.g_metrics(lE, lB, yy)
            pg = bind.panel_global(c); perms = bind.a[f'{c}/maps']
            prof = (PU.measure_cell(DM, F_['U_kernel'][[kpos[int(g)] for g in pg]].astype(np.float64), y_all[pg].astype(np.int64), perms, sigma, 1.0, keep_null=False)
                    if sigma is not None else {'status': 'calibration_degenerate'})
            per[c] = {'lane': bind.by_id[c]['lane'], **m, 'profile_n128_x1': prof}
        res['fits'][key] = {'n_train_children': len(fit['train']), 'n_train_rows': int(len(tr_rows)), 'readout_fit': rec_e[-1], 'retries': len(rec_e) - 1,
                            'q0': q0.tolist(), 'profile_calibration': cal, 'children': per}
    write(out_path, res)
    return res


def child_values(res, kinds, key):
    """Child mean over the fits of the given kinds (each child is a test child once per kind)."""
    out = {}
    for fk, fit in res['fits'].items():
        if any(fk.startswith(k) for k in kinds):
            for c, v in fit['children'].items():
                val = v.get(key) if key != 'profile' else v['profile_n128_x1'].get('excess_cs_nats')
                out.setdefault(c, []).append(val)
    return {c: (float(np.mean(v)) if all(x is not None for x in v) else None) for c, v in out.items()}


def analyze():
    from . import private_analysis as PA
    res = {n: read(BASE / 'use' / (n.replace('@', '_at_') + '.json')) for n in ENCODERS if (BASE / 'use' / (n.replace('@', '_at_') + '.json')).exists()}
    bind = Binding()
    pure = [k['id'] for k in bind.kids if k['lane'] == 'mff_puretone']; bapa = [k['id'] for k in bind.kids if k['lane'] == 'mff_bapa']
    ends = {'within_G': (('within',), 'G_bits', pure), 'within_AUC': (('within',), 'auc_EEG_part', pure),
            'transfer_AUC': (('transfer',), 'auc_EEG_part', bapa), 'transfer_G': (('transfer',), 'G_bits', bapa),
            'refit_AUC': (('refit',), 'auc_EEG_part', bapa), 'refit_G': (('refit',), 'G_bits', bapa),
            'profile_pure': (('within',), 'profile', pure), 'profile_bapa_refit': (('refit',), 'profile', bapa)}
    V = {n: {e: child_values(r, k, key) for e, (k, key, _) in ends.items()} for n, r in res.items()}
    fams, levels = [], {n: {e: PA.describe(v) for e, v in V[n].items()} for n in V}
    for fid, ep in (('F_MFF_WITHIN', 'within_G'), ('F_CROSS_STIM_DEP12', 'transfer_AUC')):
        people = ends[ep][2]
        for s in SEEDS:
            need = ['B0', f'cs_pair@{s}', f'info_nce@{s}', f'sigmoid@{s}']
            if all(n in V for n in need):
                fams.append(PA.family(f'{fid}[{s}]', ep, [(f'cs_pair-{o}', PA.diff(V[f'cs_pair@{s}'][ep], V[n][ep]))
                                                          for o, n in zip(('B0', 'info_nce', 'sigmoid'), need[:1] + need[2:])], people))
        if all(f'{a}@{s}' in V for a in ('cs_pair', 'info_nce', 'sigmoid') for s in SEEDS) and 'B0' in V:
            fams.append(PA.family(f'{fid}[merged]', ep + ', child mean over seeds',
                                  [(f'cs_pair-{o}', PA.mean_over([PA.diff(V[f'cs_pair@{s}'][ep], V['B0' if o == 'B0' else f'{o}@{s}'][ep]) for s in SEEDS]))
                                   for o in ('B0', 'info_nce', 'sigmoid')], people))
    if 'B0' in V:
        for ep in ('transfer_AUC', 'refit_AUC', 'within_AUC'):
            fams.append(PA.family(f'DESCRIPTIVE_MFF_AUC_MINUS_HALF:{ep}', 'AUC − 0.5 (descriptive)',
                                  [(f'{n}', {c: (v - .5) if v is not None else None for c, v in V[n][ep].items()}) for n in V], ends[ep][2]))
    rows = []
    for n, r in res.items():
        m = r['encoder_meta']
        for fk, fit in r['fits'].items():
            for c, v in fit['children'].items():
                for ep in ('G_bits', 'auc_EEG_part', 'auc_E', 'auc_B1', 'logscore_E', 'logscore_B1', 'clipped_fraction_E'):
                    rows.append({'schema_version': 'dep12_private_rows_v1', 'experiment_id': 'DEP12_PRIVATE_MFF', 'arm': n, 'backbone': m.get('arch'),
                                 'training_mode': m.get('mode'), 'train_seed': m.get('seed'), 'cohort': 'private_mff_' + v['lane'].split('_')[1],
                                 'participant_id': c, 'outer_fold': fk, 'support_seed': None, 'support_budget': 'U0', 'task': 'mff_' + fk.rstrip('01234'),
                                 'descriptor': 'deviant_vs_standard', 'feature_layer': m.get('layer'), 'window_support_ms': PA.WINDOW, 'endpoint': ep,
                                 'value': v.get(ep), 'n_trials': v.get('n'), 'n_anchors': None, 'access_level': m.get('data_access'),
                                 'checkpoint_sha256': m.get('checkpoint_sha256'), 'split_sha256': bind.sha256, 'query_sha256': None, 'calibration_sha256': None,
                                 'code_commit': 'no git; see private_mff_contrasts.json:sources', 'status': 'complete' if v.get(ep) is not None else 'not_estimable',
                                 'missing_reason': None})
                p = v['profile_n128_x1']
                rows.append({'schema_version': 'dep12_private_rows_v1', 'experiment_id': 'DEP12_PRIVATE_MFF_DELTA_PROFILE', 'arm': n, 'train_seed': m.get('seed'),
                             'cohort': 'private_mff_' + v['lane'].split('_')[1], 'participant_id': c, 'outer_fold': fk, 'task': 'mff_delta_profile',
                             'endpoint': 'excess_cs_nats/n128_x1', 'value': p.get('excess_cs_nats'), 'raw_cs': p.get('raw_cs_nats'), 'null_mean': p.get('null_mean_nats'),
                             'null_sd': p.get('null_sd_nats'), 'excess_cs': p.get('excess_cs_nats'), 'z': p.get('z'), 'z_status': p.get('z_status'),
                             'null_design_id': NULL_DESIGN, 'actual_null_draws': p.get('n_null_draws'), 'sigma_u': p.get('sigma_u'), 'sigma_y': None,
                             'kernel_diagnostics': p.get('k_diagnostics'), 'panel_id': f'{c}/n128', 'n_anchors': p.get('n'), 'split_sha256': bind.sha256,
                             'status': 'complete' if p.get('excess_cs_nats') is not None else 'missing', 'missing_reason': None if p.get('status') == 'measured' else p.get('status')})
    body = {'version': VERSION, 'time': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID'), 'binding_sha256': bind.sha256,
            'encoders_with_results': sorted(res), 'families': fams, 'levels': levels, 'sources': sources(),
            'notes': ['MFF pure tone / bapa (DECISIONS P21); children = (lane, identity); pseudonymous ids; not pooled with BDF',
                      'transfer = pure-tone readout applied to bapa (deviant vs standard), refit = bapa readout; endpoints averaged per child over its single test fit']}
    write(PF.RESULTS / 'private_mff_contrasts.json', body)
    with open(PF.RESULTS / 'per_person_private_mff.jsonl', 'w') as fh:
        for r_ in rows:
            fh.write(json.dumps(r_, sort_keys=True, allow_nan=False) + '\n')
    L = ['# DEP12 private MFF extension (pure tone / bapa; DECISIONS P21)', '', f"Generated {body['time']}; encoders {len(res)}.", '']
    for f_ in fams:
        L += [f"## {f_['family_id']} — {f_['unit']}", '', f"status {f_['status']}, n = {f_['complete_n']}/{f_['expected_n']}", '',
              '| member | n | estimate | simultaneous 95% |', '|---|---:|---:|---|']
        for m_ in f_['members']:
            sm = m_.get('simultaneous_95')
            L.append(f"| {m_['name']} | {m_['n']} | {PA.fmt(m_.get('estimate'))} | {('[' + PA.fmt(sm[0]) + ', ' + PA.fmt(sm[1]) + ']') if sm else 'NA'} |")
        L.append('')
    L += ['## Levels (child means)', '', '| encoder | ' + ' | '.join(ends) + ' |', '|---|' + '---:|' * len(ends)]
    for n, lv in sorted(levels.items()):
        L.append(f'| {n} | ' + ' | '.join(PA.fmt(lv[e]['mean'], 5) for e in ends) + ' |')
    (PF.RESULTS / 'private_mff_contrasts.md').write_text('\n'.join(L) + '\n')
    print(json.dumps({'families': [f_['family_id'] for f_ in fams], 'rows': len(rows)}), flush=True)


# ----------------------------------------------------------------------------------------------- lane
def unit_id(name, bsha):
    return 'DEP12M_' + digest({'encoder': name, 'binding_sha256': bsha, 'version': VERSION}, 16)


def specs():
    return sorted((read(p) for p in (BASE / 'specs').glob('*.json')), key=lambda s: s['order']) if (BASE / 'specs').exists() else []


def register():
    bsha = sha(BINDING); have = {s['encoder'] for s in specs()}
    for j, n in enumerate(n for n in ENCODERS if n not in have):
        uid = unit_id(n, bsha)
        PF.write_frozen(BASE / 'specs' / f'{uid}.json', {'id': uid, 'encoder': n, 'binding_sha256': bsha, 'version': VERSION, 'order': len(have) + j,
                                                         'store': str(STORE / 'units' / uid), 'results_seen': False,
                                                         'created': datetime.now().astimezone().isoformat()})
        print('registered', n, uid, flush=True)


def lane_sources():
    return {str(Path(p).relative_to(PF.ROOT)): sha(p) for p in (Path(__file__), Path(PF.__file__), PF.ROOT / 'auditory_alignment_v3/dep12/encoders.py',
                                                                PF.ROOT / 'auditory_alignment_v3/dep12/encoders_v2.py',
                                                                PF.ROOT / 'auditory_alignment_v3/dep12/encoders_v3.py',
                                                                PF.ROOT / 'auditory_alignment_v3/dep12/private_fleet_v3.py')}


def unit_state(s):
    from . import private_fleet_v3 as FL
    if (BASE / 'units' / f'{s["id"]}.json').exists():
        return 'complete'
    if (BASE / 'units' / f'{s["id"]}.FAILED.json').exists():
        return 'failed'
    st = FL.encoder_state(s['encoder'])
    return 'ready' if st == 'available' else 'waiting_encoder:' + str(st)


def smoke_pass():
    """v2: a passing v1 GPU smoke (any v1 sources) AND a passing v2 CPU equivalence receipt for these sources."""
    v1 = [p for p in sorted((BASE / 'smoke').glob('*/receipt.json')) if read(p).get('status') == 'pass'] if (BASE / 'smoke').exists() else []
    v2 = [p for p in sorted((BASE / 'smoke_v3').glob('*/receipt.json')) if read(p).get('status') == 'pass' and read(p).get('sources') == lane_sources()] \
        if (BASE / 'smoke_v3').exists() else []
    return v2 if v1 else []


def post_pending():
    done = [s['encoder'] for s in specs() if unit_state(s) == 'complete']
    failed = {p.name for p in (BASE / 'post_failed').glob('*.json')} if (BASE / 'post_failed').exists() else set()
    todo = [('use', n) for n in done if not (BASE / 'use' / (n.replace('@', '_at_') + '.json')).exists() and f'use_{n}.json' not in failed]
    cur = digest([[p.name, sha(p)] for p in sorted((BASE / 'use').glob('*.json'))]) if (BASE / 'use').exists() else None
    last = BASE / 'analysis_inputs.json'
    if cur and (not last.exists() or read(last).get('digest') != cur) and 'analysis.json' not in failed:
        todo.append(('analysis', cur))
    from . import private_fleet_v3 as FL
    if FL.mechanism_pending(failed):
        todo.append(('mechanism',))
    return todo


def post():
    for _ in range(2):
        todo = post_pending()
        if not todo:
            return
        for item in todo:
            if item[0] in ('analysis', 'mechanism') and any(t[0] == 'use' for t in post_pending()):
                continue
            if item[0] == 'mechanism':
                mod, args, tag = 'auditory_alignment_v3.dep12.private_mechanism_v2', [], 'mechanism'
            else:
                mod = __spec__.name
                args, tag = (['--use', item[1]], f'use_{item[1]}') if item[0] == 'use' else (['--analyze'], 'analysis')
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', mod, *args]).returncode
            if rc < 0:
                raise SystemExit(rc)
            if rc:
                write(BASE / 'post_failed' / f'{tag}.json', {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc})
            elif item[0] == 'analysis':
                write(BASE / 'analysis_inputs.json', {'digest': item[1], 'job': os.environ.get('SLURM_JOB_ID')})


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 0, 'slots': 1, 'initial': [], 'submit': []}
    sp = specs()
    if not BINDING.exists() or not sp:
        return st
    from . import encoders_v3 as E
    E.refresh()
    states = [unit_state(s) for s in sp]
    left = [x for x in states if x != 'complete']
    st['remaining'] = len(left)
    if 'failed' in left:
        return {**st, 'state': 'failed_unit_review'}
    if not smoke_pass():
        if (BASE / 'smoke_v3').exists() and any(read(p).get('status') == 'failed' for p in (BASE / 'smoke_v3').glob('*/receipt.json')):
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    ready = sum(x == 'ready' for x in left)
    if ready:
        return {**st, 'state': 'ready', 'ready': ready, 'slots': 1, 'submit': [SBATCH, '--worker']}
    failed_post = (BASE / 'post_failed').exists() and any((BASE / 'post_failed').glob('*.json'))
    if failed_post:
        return {**st, 'state': 'failed_unit_review'}
    if post_pending():
        return {**st, 'state': 'ready', 'ready': 1, 'remaining': max(1, len(left)), 'slots': 1, 'submit': [SBATCH, '--post']}
    return {**st, 'state': 'complete' if not left else 'waiting_for_encoders'}


def run_unit(uid):
    s = read(BASE / 'specs' / f'{uid}.json'); assert s['binding_sha256'] == sha(BINDING)
    meta = export(s['encoder'], s['store'])
    write(BASE / 'units' / f'{uid}.json', {'status': 'complete', 'spec': s, 'array_sha256': meta['array_sha256'], 'encoder_meta': meta['encoder_meta'],
                                           'U_dim': meta['U_dim'], 'seconds': meta['seconds'], 'gpu_peak_mb': meta['gpu_peak_mb'], 'device': meta['device'],
                                           'job': os.environ.get('SLURM_JOB_ID'), 'sources': lane_sources(), 'fleet_version': 'v3',
                                           'time': datetime.now().astimezone().isoformat()})


def claim(uid):
    path = BASE / 'units' / f'{uid}.json'
    lock = BASE / 'claims' / f'{uid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists() or (BASE / 'units' / f'{uid}.FAILED.json').exists():
            return False
        rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', uid]).returncode
        if rc < 0:
            raise SystemExit(rc)
        if rc or not path.exists():
            write(BASE / 'units' / f'{uid}.FAILED.json', {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc})
            raise RuntimeError(f'DEP12 MFF unit failed: {uid}')
        return True


def worker(max_units=3):
    assert smoke_pass(), 'no passing smoke'
    n = 0
    for s in specs():
        if n >= max_units:
            break
        if unit_state(s) == 'ready' and claim(s['id']):
            n += 1
    post()


def smoke():
    """v3 equivalence receipt (CPU or GPU): B0 through encoders_v3 and encoders gives identical U on the 'mff' montage for one
    child's panel rows, reproducing the stored production B0 MFF kernel rows (max |diff| <= 1e-5); the four extension names
    are in the v2 registry."""
    import numpy as np
    import torch
    import torch.nn.functional as F
    from ..aln41 import cross_stim as XS
    from . import encoders as E1, encoders_v3 as E2
    job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'sources': lane_sources(), 'job': job}
    try:
        assert set(EXT1 + EXT2) <= set(E2.refresh()) and not set(EXT1 + EXT2) & set(E1.refresh())
        bind = Binding(); b0 = next(s_ for s_ in specs() if s_['encoder'] == 'B0')
        with np.load(Path(b0['store']) / 'features.npz', allow_pickle=False) as z:
            kidx, Uk = z['kernel_index'], z['U_kernel']
        kpos = {int(g): i for i, g in enumerate(kidx)}
        kid = bind.kids[0]; cid = kid['id']
        recs = [r for ri, r in enumerate(bind.meta['records']) if ri in set(bind.a['record'][bind.rows(cid)].tolist())]
        X, rows, _ = XS.load(recs)
        assert len(X) == len(bind.rows(cid)) and np.array_equal(rows['y'], bind.a['y'][bind.rows(cid)])
        loc = bind.a[f'{cid}/panel_local'][:64]
        dev = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        xb = F.pad(PF.resample_real(torch.as_tensor(X[loc]).to(dev)).float(), (PF.PAD_FRONT, 0))
        names = [f'E{i}' for i in range(1, 129)]; pm = torch.as_tensor(PF.pad_mask()).to(dev)
        u1 = E1.load('B0', dev).represent(xb, names, pm).cpu(); u2 = E2.load('B0', dev).represent(xb, names, pm).cpu()
        assert torch.equal(u1, u2)
        ref = Uk[[kpos[int(g)] for g in bind.rows(cid)[loc]]]
        worst = float(np.max(np.abs(u2.numpy() - ref)))
        assert worst <= 1e-4, worst                 # stored MFF B0 is GPU-made (V100); DECISIONS P23a
        receipt.update(status='pass', B0={'child': cid, 'rows_checked': int(len(loc)), 'v1_v2_identical': True,
                                          'max_abs_diff_vs_stored_production': worst, 'device': str(dev)})
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(BASE / 'smoke_v3' / job / 'receipt.json', receipt)


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_binding', 'register', 'smoke', 'worker', 'analyze', 'post', 'status'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--use')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    if a.make_binding:
        make_binding()
    elif a.register:
        register()
    elif a.smoke:
        smoke()
    elif a.unit:
        run_unit(a.unit)
    elif a.worker:
        worker()
    elif a.use:
        use_encoder(a.use)
    elif a.analyze:
        analyze()
    elif a.post:
        assert smoke_pass(); post()
    elif a.status:
        print(json.dumps({'fleet': fleet_status(), 'units': [(s['encoder'], unit_state(s)) for s in specs()]}, indent=1))


if __name__ == '__main__':
    main()
