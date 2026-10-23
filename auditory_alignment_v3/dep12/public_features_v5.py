"""DEP12 public feature exporter v5 (Agent M; = v4 + encoders_v4 registry (ext3 ssl_continue, M21) + plan_ext3 rows; package v1.2 03 §1, §4.1-4.3, §4.5; 02 §5.2, §6.1).

Inputs: the frozen definitions of dep12/panels.py (panels, partners, noise seeds, 20 s queries) and the shared encoder API
dep12/encoders.py (Agent S; ENC.load(name).represent(x [N, C, 200], channel_names) -> U [N, D], L2 rows).
EEG: the cohort loaders' preprocessed native 128 Hz EEG through the verified lean replicas paper/ext_common._dtu_person /
_fau_person (per-person z-score over ss+cs trials, identical to auditory_alignment.data.load_dtu/load_fau(kinds=('ss','cs'))).
Window: native crop eeg[q-52 : q+76] (the 64 Hz-equivalent source window) -> aln41.timebank.resample to 200 points; no padding.

Descriptors (CPU, encoder independent; descriptors_v1/<ds>.npz, 0444): env / spec / Lz at every panel anchor (125 ms support,
pairwise means -> 8 points; env 8-d, spec 40-d, Lz 40-d; content-fold kcs file of the panel) and attended / ignored env at every
query anchor.

Feature cache (GPU; one directory per encoder x cohort x input support x definitions, keyed by the encoder identity hash):
  STORE/<encoder>__<enc_key>/<ds>/<SUPPORT_ID>/<defs16>/
    panels.npz   ids, d2 [P, n, n] (exact squared distances of U, float64 -> float32) of every in-scope test / calib panel;
                 test-panel partner_d2 [T, 128, 128] (NaN rows/cols where a block has no partner) + partner_mask [T, 4]; noise_d2
    pca.npz      per in-scope (cf, sf): mean [D], comp [16, D] (centred SVD of the training people's calib-panel U), calib_proj
                 [people, 128, 16] and calib_people
    queries.npz  qidx (index into defs queries), d2c [Q, 152*151/2] (condensed upper triangle), proj [Q, 152, 16]
    meta.json    encoder meta / registry spec, scope, hashes, timings, device
U itself is not stored (M5 in DECISIONS: /projects is 98 % full); every kernel quantity of measure.py / attention.py is exact
from D² and the readout uses the stored PCA-16 projections.
Units (plan.json, frozen): per cohort, B0 / REVE0 / MINDMIX_branch, each ALN4.1 seed group (4 arms), each new-round arm, and each
ALN3.4 fold-model group (label x cohort x seed; a fold model is used only for its own (cf, sf): calibration on that fold's
training people, measurement / queries of its held-out people and contents). A unit is ready when all its encoders are
'available' in ENC.refresh(); new-round arms become ready as Agent S's checkpoints complete.
CLI (Slurm only): python -m auditory_alignment_v3.dep12.public_features {descriptors, plan, smoke, worker [--max-units N],
unit --id ID, status}
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import gc
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from ..aln34 import learning_budget as B
from . import panels as PN

OUT = PN.OUT
DESC = OUT / 'descriptors_v1'
FEAT = OUT / 'features_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/dep12/features')
SUPPORT_ID = 'native128_q-52_76_tbresample200_nopad_v1'
SUPPORT_DESC = ('native 128 Hz crop eeg[q-52:q+76] (half-open [-406.25, +593.75) ms = source 64 Hz q+[-26:38]) of the loader '
                'z-scored EEG (DTU eeg_1_20 / FAU eeg_1_20_ica), aln41.timebank.resample -> 200 samples, no padding')
PCA_DIM = 16
DATASETS = PN.DATASETS + ('federici',)
NAME, LANE, SBATCH = 'c3_s35dMfeat', 's35_dep12_pub_features', 'slurm/aln35_dep12_pub_features_v5.sbatch'
ALN34_LABELS = ('aln34_cb_full', 'aln34_cb_random', 'aln34_reve_full')
NEW_ARMS = ('cs_pair@3401', 'cs_pair@3407', 'cs_pair@3413', 'info_nce@3401', 'info_nce@3407', 'info_nce@3413',
            'sigmoid@3401', 'sigmoid@3407', 'sigmoid@3413', 'raw_cs@3401', 'cs_pair_wrong@3401')
sha, write, read, digest = PN.sha, PN.write, PN.read, PN.digest


def sources():
    here = Path(__file__).parent
    files = [here / 'public_features_v5.py', here / 'federici.py', here / 'panels.py', here / 'encoders.py', here / 'encoders_v2.py', here / 'encoders_v3.py',
             here / 'encoders_v4.py',
             Path(core.REPO) / 'auditory_alignment_v3/aln41/timebank.py', Path(core.REPO) / 'auditory_alignment_v3/paper/ext_common.py',
             Path(core.REPO) / 'auditory_alignment/data.py', Path(core.REPO) / 'auditory_alignment_v2/foundation_adapter.py']
    return {str(p.relative_to(core.REPO)): sha(p) for p in files}


def defs_hash(ds):
    return sha(PN.DEFS / ds / 'defs.json')


# ------------------------------------------------------------------------------------------------ descriptors (CPU)
def _pairmean(a):
    return 0.5 * (a[..., 0::2] + a[..., 1::2])


def _take(arr, q, lead):
    """arr [d, T] stream on its own clock; q 128 Hz trial indices; -> [n, d * 8] (dimension-major, 8 points at 64 Hz)."""
    idx = (np.asarray(q) - lead)[:, None] + np.arange(PN.TGT)[None]
    assert idx.min() >= 0 and idx.max() < arr.shape[1], ('descriptor support outside the stimulus', idx.min(), idx.max(), arr.shape)
    w = _pairmean(arr[:, idx].astype(np.float64))            # [d, n, 8]
    return w.transpose(1, 0, 2).reshape(len(q), -1)


def descriptors(ds):
    import h5py
    from auditory_alignment import data as D
    path = DESC / f'{ds}.npz'
    if path.exists():
        return path
    defs = PN.defs(ds); sc = read(PN.DEFS / ds / 'scan.json')
    trials = {(p, r['trial']): r for p, rows in sc['trials'].items() for r in rows}
    root = D.DTU_KCS if ds == 'dtu' else D.FAU_KCS
    tfs = [h5py.File(os.path.join(root, f'{ds}_cf{cf}.h5'), 'r') for cf in PN.CFS]
    cache = {}

    def stream(cf, key, which):
        k = (cf, key, which)
        if k not in cache:
            base = key if ds == 'dtu' else f'{key}/{"attended" if which == "att" else "distractor"}'
            cache[k] = (tfs[cf][f'{base}/Local'][()], tfs[cf][f'{base}/Lz'][()])
        return cache[k]
    ids = sorted(defs['panels']); out = {k: [] for k in ('env', 'spec', 'Lz', 'anchor', 'block')}
    for pid in ids:
        pn = defs['panels'][pid]; assert pn['n'] == 128, ('short panel', pid)
        e, s, z, qa, bl = [], [], [], [], []
        for j, blk in enumerate(pn['blocks']):
            r = trials[(pn['person'], blk['trial'])]; q = PN.anchors_of(blk)
            loc, lz = stream(pn['cf'], r['att'], 'att')
            e.append(_take(loc[5:6], q, r['att_lead'])); s.append(_take(loc[:5], q, r['att_lead'])); z.append(_take(lz, q, r['att_lead']))
            qa.append(q); bl.append(np.full(len(q), j))
        for k, v in (('env', e), ('spec', s), ('Lz', z), ('anchor', qa), ('block', bl)):
            out[k].append(np.concatenate(v))
    arrays = {'panel_ids': np.array(ids), **{k: np.stack(v) for k, v in out.items()}}
    qa_, qi_ = [], []
    for qd in defs['queries']:
        r = trials[(qd['person'], qd['trial'])]; q = qd['st0'] + PN.QUERY_FIRST + PN.QUERY_HOP * np.arange(PN.QUERY_N)
        la, _ = stream(qd['cf'], r['att'], 'att'); li, _ = stream(qd['cf'], r['ign'], 'ign')
        qa_.append(_take(la[5:6], q, r['att_lead'])); qi_.append(_take(li[5:6], q, r['ign_lead']))
    arrays['q_att'] = np.stack(qa_); arrays['q_ign'] = np.stack(qi_)
    for tf in tfs:
        tf.close()
    for k in ('env', 'spec', 'Lz', 'q_att', 'q_ign'):
        assert np.isfinite(arrays[k]).all(), k
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez(path, **arrays); path.chmod(0o444)
    write(DESC / f'{ds}.meta.json', {'version': 'DEP12_PUB_DESC_v1', 'dataset': ds, 'defs_sha256': defs_hash(ds), 'sha256': sha(path),
                                      'shapes': {k: list(v.shape) for k, v in arrays.items()}, 'sources': sources(),
                                      'definition': ('kcs_targets_v1 of the panel / query content fold; env = Local[5], spec = Local[0:5], '
                                                     'Lz = Lz[0:5]; support [q, q+16) at 128 Hz -> pairwise means -> 8 points; '
                                                     'flattened dimension-major')})
    print(ds, 'descriptors', sha(path), {k: v.shape for k, v in arrays.items()}, flush=True)
    return path


def load_descriptors(ds):
    meta = read(DESC / f'{ds}.meta.json'); path = DESC / f'{ds}.npz'
    assert sha(path) == meta['sha256'] and meta['defs_sha256'] == defs_hash(ds)
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


# ------------------------------------------------------------------------------------------------ encoders / plan
def enc_module():
    from . import encoders_v4 as ENC          # v1 + v2 + v3 registries unchanged + ext3 ssl_continue (Agent S)
    return ENC


def enc_key(meta):
    body = {k: meta.get(k) for k in ('name', 'checkpoint_sha256', 'representation', 'api_version', 'layer', 'ln_eps', 'arch', 'step')}
    return digest(body, 16)


def make_plan():
    path = FEAT / 'plan.json'
    ENC = enc_module(); R = ENC.refresh()
    rows = []
    for ds in PN.DATASETS:
        groups = [('B0', ['B0']), ('REVE0', ['REVE0']), ('MINDMIX_branch', ['MINDMIX_branch'])]
        for seed in (3401, 3407, 3413):
            groups.append((f'aln41@{seed}', [f'aln41_{a}@{seed}' for a in ('TCS', 'TNCE', 'GCS', 'WRONG')]))
        groups += [(a, [a]) for a in NEW_ARMS]
        for label in ALN34_LABELS:
            names = sorted(n for n, v in R.items() if n.startswith(label + '@') and v.get('dataset') == ds and v.get('servable'))
            for seed in sorted({R[n]['seed'] for n in names}):
                g = [n for n in names if R[n]['seed'] == seed]
                assert len(g) == 10, (label, ds, seed, len(g))
                groups.append((f'{label}@{ds}.s{seed}', g))
        for gname, names in groups:
            for n in names:
                assert n in R and R[n].get('servable'), n
            body = {'dataset': ds, 'group': gname, 'encoders': names}
            rows.append({**body, 'id': 'DEP12PF_' + digest(body, 16)})
    body = {'version': 'DEP12_PUB_FEATURES_v1', 'rows': rows, 'support_id': SUPPORT_ID, 'support': SUPPORT_DESC, 'pca_dim': PCA_DIM,
            'defs_sha256': {ds: defs_hash(ds) for ds in DATASETS}, 'store': str(STORE)}
    if path.exists():
        old = read(path); assert all(old[k] == v for k, v in body.items()), 'immutable feature plan drift'
        return old
    FEAT.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('feature plan', len(rows), sha(path), flush=True)
    return body


EXT_PLAN = FEAT / 'plan_ext1.json'
EXT_ARMS = ('raw_cs@3407', 'raw_cs@3413', 'cs_pair_wrong@3407', 'cs_pair_wrong@3413')


def make_plan_ext():
    """Supplementary frozen plan (the base plan is immutable): mechanism-control seeds added by Agent S (DECISIONS M17). Rows
    become ready when encoders.py marks the encoders 'available'; names not yet in the registry simply wait."""
    rows = []
    for ds in DATASETS:
        for a in EXT_ARMS:
            body = {'dataset': ds, 'group': a, 'encoders': [a]}
            rows.append({**body, 'id': 'DEP12PF_' + digest(body, 16)})
    body = {'version': 'DEP12_PUB_FEATURES_EXT1', 'base_plan_sha256': sha(FEAT / 'plan.json'), 'rows': rows, 'support_id': SUPPORT_ID}
    if EXT_PLAN.exists():
        old = read(EXT_PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable extension plan drift'
        return old
    write(EXT_PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); EXT_PLAN.chmod(0o444)
    print('feature extension plan', len(rows), sha(EXT_PLAN), flush=True)
    return body


EXT2_PLAN = FEAT / 'plan_ext2.json'
EXT2_ARMS = ('cs_pair_noise@3401', 'cs_pair_noise@3407', 'cs_pair_noise@3413')


def make_plan_ext2():
    """Second supplementary frozen plan: the ext2 follow-up arm cs_pair_noise (coordinator DECISIONS 2026-10-23 10:55; M19)."""
    rows = []
    for ds in DATASETS:
        for a in EXT2_ARMS:
            body = {'dataset': ds, 'group': a, 'encoders': [a]}
            rows.append({**body, 'id': 'DEP12PF_' + digest(body, 16)})
    body = {'version': 'DEP12_PUB_FEATURES_EXT2', 'base_plan_sha256': sha(FEAT / 'plan.json'), 'rows': rows, 'support_id': SUPPORT_ID}
    if EXT2_PLAN.exists():
        old = read(EXT2_PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable ext2 plan drift'
        return old
    write(EXT2_PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); EXT2_PLAN.chmod(0o444)
    print('feature ext2 plan', len(rows), sha(EXT2_PLAN), flush=True)
    return body


FED_PLAN = FEAT / 'plan_fed.json'
FED_GROUPS = (('B0', ['B0']), ('REVE0', ['REVE0']), ('MINDMIX_branch', ['MINDMIX_branch'])) + tuple(
    (f'aln41@{s}', [f'aln41_{a}@{s}' for a in ('TCS', 'TNCE', 'GCS', 'WRONG')]) for s in (3401, 3407, 3413)) + tuple(
    (a, [a]) for a in NEW_ARMS + EXT_ARMS + EXT2_ARMS)


def make_plan_fed():
    """Federici rows (DECISIONS M20): generic encoders only (no ALN3.4 fold models), frozen."""
    from . import federici as FED
    rows = []
    for gname, names in FED_GROUPS:
        body = {'dataset': 'federici', 'group': gname, 'encoders': list(names)}
        rows.append({**body, 'id': 'DEP12PF_' + digest(body, 16)})
    body = {'version': 'DEP12_PUB_FEATURES_FED', 'base_plan_sha256': sha(FEAT / 'plan.json'), 'rows': rows, 'support_id': SUPPORT_ID,
            'defs_sha256': defs_hash('federici')}
    if FED_PLAN.exists():
        old = read(FED_PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable federici plan drift'
        return old
    write(FED_PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); FED_PLAN.chmod(0o444)
    print('feature federici plan', len(rows), sha(FED_PLAN), flush=True)
    return body


EXT3_PLAN = FEAT / 'plan_ext3.json'
EXT3_ARMS = ('ssl_continue@3401', 'ssl_continue@3407', 'ssl_continue@3413')


def make_plan_ext3():
    """Third supplementary frozen plan: ext3 ssl_continue on DTU / FAU / Federici (coordinator 11:55 + 12:20; M21)."""
    rows = []
    for ds in DATASETS:
        for a in EXT3_ARMS:
            body = {'dataset': ds, 'group': a, 'encoders': [a]}
            rows.append({**body, 'id': 'DEP12PF_' + digest(body, 16)})
    body = {'version': 'DEP12_PUB_FEATURES_EXT3', 'base_plan_sha256': sha(FEAT / 'plan.json'), 'rows': rows, 'support_id': SUPPORT_ID}
    if EXT3_PLAN.exists():
        old = read(EXT3_PLAN); assert all(old[k] == v for k, v in body.items()), 'immutable ext3 plan drift'
        return old
    write(EXT3_PLAN, {**body, 'created': datetime.now().astimezone().isoformat()}); EXT3_PLAN.chmod(0o444)
    print('feature ext3 plan', len(rows), sha(EXT3_PLAN), flush=True)
    return body


def plan_rows():
    rows = list(read(FEAT / 'plan.json')['rows'])
    for p in (EXT_PLAN, EXT2_PLAN, FED_PLAN, EXT3_PLAN):
        if p.exists():
            rows += read(p)['rows']
    return rows


def scope_of(spec, ds):
    """{(cf, sf)} where this encoder may be measured on cohort ds."""
    if spec.get('kind') == 'reused_aln34':
        return {(int(spec['content_fold']), int(spec['subject_fold']))} if spec.get('dataset') == ds else set()
    return {(cf, sf) for cf in PN.CFS for sf in PN.SFS}


def unit_ready(row):
    ENC = enc_module(); R = ENC.refresh()
    return all(R.get(n, {}).get('servable') and R.get(n, {}).get('state') == 'available' for n in row['encoders'])


# ------------------------------------------------------------------------------------------------ EEG windows
class Cohort:
    """Per-person loader-equivalent EEG (ext_common lean replicas) and fold structure."""

    def __init__(self, ds):
        import h5py
        from auditory_alignment import data as D
        from auditory_alignment_v2.foundation_adapter import ALIASES, CHANNELS
        from ..paper import ext_common as X
        self.ds, self.X = ds, X
        self.parts = {p['id']: p for p in X._people(ds)}
        root = D.DTU_KCS if ds == 'dtu' else D.FAU_KCS
        self.tfs = [h5py.File(os.path.join(root, f'{ds}_cf{cf}.h5'), 'r') for cf in PN.CFS]
        if ds == 'dtu':
            self.inv = json.load(open(f'{D.PUB}/derived/c3_features_v1/dtu/inventory.json'))
            self.cg = json.load(open(os.path.join(D.DTU_KCS, 'content_groups.json')))['content']
        self.channels = [ALIASES.get(c, c) for c in CHANNELS[ds]]
        c = X.Cache(ds)
        self.train = {sf: set(c.unit_people(sf)[0]) for sf in PN.SFS}
        self.test = {sf: set(c.unit_people(sf)[1]) for sf in PN.SFS}

    def load(self, pid):
        p = self.parts[pid]
        ch, rows = (self.X._dtu_person(p, self.tfs, self.inv, self.cg, False) if self.ds == 'dtu' else self.X._fau_person(p, self.tfs, False))
        from auditory_alignment_v2.foundation_adapter import ALIASES
        assert [ALIASES.get(c, c) for c in ch] == self.channels, f'{pid}: channel order differs from the registered montage'
        return {r['trial']: r['x'] for r in rows}

    def close(self):
        for tf in self.tfs:
            tf.close()


def make_cohort(ds):
    if ds == 'federici':
        from . import federici as FED
        return FED.FedCohort()
    return Cohort(ds)


def pad128(d):
    """Short panels (fewer than 4 blocks): pad the squared-distance matrix to 128 x 128 with NaN (rows beyond n never read)."""
    if d.shape == (128, 128):
        return d
    out = np.full((128, 128), np.nan, np.float32); out[:d.shape[0], :d.shape[1]] = d
    return out


def crops(x, q):
    """x [C, n] float32 numpy, q int array -> float32 numpy [len(q), C, 128] native crops (bounds asserted)."""
    q = np.asarray(q, np.int64)
    idx = q[:, None] + np.arange(PN.WIN[0], PN.WIN[1])[None]
    assert idx.min() >= 0 and idx.max() < x.shape[1], ('crop outside the trial', int(idx.min()), int(idx.max()), x.shape)
    return np.ascontiguousarray(x[:, idx].transpose(1, 0, 2))


def container(w, dev):
    import torch
    from ..aln41 import timebank as TB
    z = TB.resample(torch.as_tensor(w, device=dev, dtype=torch.float32), 200)
    assert z.shape[-1] == 200 and bool(torch.isfinite(z).all())
    return z


def sqd(U):
    """Exact squared Euclidean distances (float64) of rows of U (torch, any device) -> float32 numpy."""
    import torch
    X = U.double(); n = (X * X).sum(1)
    D = (n[:, None] + n[None] - 2.0 * (X @ X.T)).clamp_min_(0.0)
    D.fill_diagonal_(0.0)
    return D.float().cpu().numpy()


def pca_components(Xc, k):
    """Top-k principal axes of centred rows Xc (float64 torch) via eigh of the smaller Gram side; rows of comp are unit vectors."""
    import torch
    n, d = Xc.shape
    if n <= d:
        w, V = torch.linalg.eigh(Xc @ Xc.T)                        # ascending
        w, V = w.flip(0), V.flip(1)
        comp = (Xc.T @ V[:, :k]) / torch.sqrt(w[:k].clamp_min(1e-300))
        comp = comp.T
    else:
        w, V = torch.linalg.eigh(Xc.T @ Xc)
        w, V = w.flip(0), V.flip(1)
        comp = V[:, :k].T
    comp = comp / comp.norm(dim=1, keepdim=True)
    total = float(w.clamp_min(0).sum())
    return comp, float(w[:k].clamp_min(0).sum()) / total if total > 0 else 0.0


def represent_masked(enc, z, channels, mask, chunk=2048):
    """represent() with a declared [200] padding mask (validated by encoders.py: padded samples exactly zero)."""
    import torch
    out = [enc.represent(z[a:a + chunk], channels, mask).float() for a in range(0, len(z), chunk)]
    U = torch.cat(out)
    assert bool(torch.isfinite(U).all())
    return U


def represent(enc, z, channels, chunk=2048):
    import torch
    out = []
    for a in range(0, len(z), chunk):
        out.append(enc.represent(z[a:a + chunk], channels, None).float())
    U = torch.cat(out)
    assert bool(torch.isfinite(U).all())
    return U


# ------------------------------------------------------------------------------------------------ one unit (GPU)
def needs(defs, coh, scope):
    """Panels / partner rows / queries needed for an encoder scope."""
    folds = defs['folds']; test_p, calib_p, queries = [], [], []
    for pid, pn in defs['panels'].items():
        p, cf = pn['person'], pn['cf']
        if pn['kind'] == 'calib' and any((cf, sf) in scope and p in coh.train[sf] for sf in PN.SFS):
            calib_p.append(pid)
        if pn['kind'] == 'test' and folds[p] in PN.SFS and (cf, folds[p]) in scope and p in coh.test[folds[p]]:
            test_p.append(pid)
    for i, qd in enumerate(defs['queries']):
        if (qd['cf'], qd['sf']) in scope and qd['status'] == 'ok':
            assert qd['person'] in coh.test[qd['sf']]
            queries.append(i)
    return sorted(test_p), sorted(calib_p), queries


def _device():
    import torch
    return torch.device(os.environ.get('DEP12_DEVICE', 'cuda'))


def _device_name(dev):
    import torch
    return torch.cuda.get_device_name(0) if dev.type == 'cuda' else 'cpu'


def run_unit(row, probe=False, probe_limit=None, probe_root=None):
    import torch
    t_start = time.time(); dev = _device(); ds = row['dataset']
    ENC = enc_module(); R = ENC.refresh(); defs = PN.defs(ds); dsha = defs_hash(ds)
    coh = make_cohort(ds); timing = {'load_s': 0.0, 'forward_s': 0.0, 'windows': 0}
    encs = {}
    for name in row['encoders']:
        e = ENC.load(name, dev); key = enc_key(e.meta)
        scope = scope_of(R[name], ds)
        if probe_limit:
            scope = scope & probe_limit['scope']
        tp, cp, qs = needs(defs, coh, scope)
        if probe_limit:
            keep = set(probe_limit['people'])
            tp = [p for p in tp if defs['panels'][p]['person'] in keep]
            cp = [p for p in cp if defs['panels'][p]['person'] in keep]
            qs = [i for i in qs if defs['queries'][i]['person'] in keep][:probe_limit['queries']]
        encs[name] = {'enc': e, 'key': key, 'scope': sorted(scope), 'test': tp, 'calib': cp, 'queries': qs,
                      'testset': set(tp), 'panelset': set(tp) | set(cp), 'queryset': set(qs),
                      'calibU': {}, 'd2': {}, 'partnerU': {}, 'noise_d2': {}}
    # ---------------------------------------------------------------- pass 1: panels, partner rows, noise
    rowsof = {}                                                        # person -> [(tag, trial, q array)]
    for name, E in encs.items():
        for pid in E['test'] + E['calib']:
            pn = defs['panels'][pid]
            for j, blk in enumerate(pn['blocks']):
                rowsof.setdefault(pn['person'], []).append((('panel', pid, j), blk['trial'], PN.anchors_of(blk)))
            if pn['kind'] == 'test':
                for j, (blk, par) in enumerate(zip(pn['blocks'], pn['partners'])):
                    if par is not None:
                        rowsof.setdefault(par['person'], []).append((('partner', pid, j), par['trial'], PN.anchors_of(blk)))
    for pid in sorted(rowsof):
        t0 = time.time(); xs = coh.load(pid); timing['load_s'] += time.time() - t0
        seen, groups = {}, []
        for tag, trial, q in rowsof[pid]:
            k = (tag, trial, tuple(q.tolist()))
            if k not in seen:
                seen[k] = len(groups); groups.append((tag, trial, q))
        W = np.concatenate([crops(xs[t], q) for _, t, q in groups]); del xs
        offs = np.cumsum([0] + [len(q) for _, _, q in groups])
        t0 = time.time(); z = container(W, dev)
        for name, E in encs.items():
            want = [g for g, (tag, _, _) in enumerate(groups)
                    if (tag[0] == 'panel' and tag[1] in E['panelset']) or (tag[0] == 'partner' and tag[1] in E['testset'])]
            if not want:
                continue
            sel = np.concatenate([np.arange(offs[g], offs[g + 1]) for g in want])
            U = represent(E['enc'], z[torch.as_tensor(sel, device=dev)], coh.channels).cpu()
            off = 0
            for g in want:
                (kind, panel, j), trial, q = groups[g]
                u = U[off:off + len(q)]; off += len(q)
                if kind == 'panel':
                    E.setdefault('panelU', {}).setdefault(panel, {})[j] = u
                else:
                    E['partnerU'].setdefault(panel, {})[j] = u
            timing['windows'] += len(sel)
        timing['forward_s'] += time.time() - t0
        del W, z; gc.collect()
    for name, E in encs.items():
        for panel, blocks in E.get('panelU', {}).items():
            pn = defs['panels'][panel]; U = torch.cat([blocks[j] for j in range(len(pn['blocks']))])
            E['d2'][panel] = pad128(sqd(U.to(dev)))
            if pn['kind'] == 'calib':
                E['calibU'][panel] = U
        E.pop('panelU', None)
    # noise windows (no person data): N(0, 1) native crops, seeded per test panel
    for name, E in encs.items():
        for panel in E['test']:
            pn = defs['panels'][panel]
            W = np.random.default_rng(pn['noise_seed']).standard_normal((pn['n'], len(coh.channels), PN.WIN[1] - PN.WIN[0])).astype(np.float32)
            t0 = time.time(); U = represent(E['enc'], container(W, dev), coh.channels); timing['forward_s'] += time.time() - t0
            E['noise_d2'][panel] = pad128(sqd(U))
    # ---------------------------------------------------------------- PCA per (cf, sf) on the training people's calib panels
    for name, E in encs.items():
        E['pca'] = {}
        for cf, sf in E['scope']:
            people = sorted(p for p in coh.train[sf] if f'{ds}:{p}:cf{cf}:calib' in E['calibU'])
            if not people:
                continue
            t0 = time.time()
            X = torch.cat([E['calibU'][f'{ds}:{p}:cf{cf}:calib'] for p in people]).to(dev).double()
            mu = X.mean(0); Xc = X - mu
            comp, explained = pca_components(Xc, PCA_DIM)
            proj = (Xc @ comp.T).float().cpu().numpy().reshape(len(people), -1, PCA_DIM)
            E['pca'][(cf, sf)] = {'mean': mu.float().cpu().numpy(), 'comp': comp.float().cpu().numpy(), 'calib_proj': proj,
                                  'calib_people': np.array(people), 'explained': explained, 'n_rows': int(len(X))}
            del X, Xc
            timing['pca_s'] = timing.get('pca_s', 0.0) + time.time() - t0
        E['calibU'] = {}
    # ---------------------------------------------------------------- pass 2: queries
    qrows = {}
    for name, E in encs.items():
        for i in E['queries']:
            qrows.setdefault(defs['queries'][i]['person'], set()).add(i)
    iu = np.triu_indices(PN.QUERY_N, 1)
    for name, E in encs.items():
        E['qd2'], E['qproj'] = {}, {}
    for pid in sorted(qrows):
        t0 = time.time(); xs = coh.load(pid); timing['load_s'] += time.time() - t0
        qi = sorted(qrows[pid])
        W = np.concatenate([crops(xs[defs['queries'][i]['trial']], defs['queries'][i]['st0'] + PN.QUERY_FIRST + PN.QUERY_HOP * np.arange(PN.QUERY_N))
                            for i in qi]); del xs
        t0 = time.time(); z = container(W, dev)
        for name, E in encs.items():
            mine = [k for k, i in enumerate(qi) if i in E['queryset']]
            if not mine:
                continue
            sel = torch.as_tensor(np.concatenate([np.arange(k * PN.QUERY_N, (k + 1) * PN.QUERY_N) for k in mine]), device=dev)
            U = represent(E['enc'], z[sel], coh.channels); timing['windows'] += len(sel)
            for m, k in enumerate(mine):
                i = qi[k]; qd = defs['queries'][i]; u = U[m * PN.QUERY_N:(m + 1) * PN.QUERY_N]
                E['qd2'][i] = sqd(u)[iu]
                p = E['pca'][(qd['cf'], qd['sf'])]
                E['qproj'][i] = ((u.double() - torch.as_tensor(p['mean'], device=dev).double()) @ torch.as_tensor(p['comp'], device=dev).double().T).float().cpu().numpy()
        timing['forward_s'] += time.time() - t0
        del W, z; gc.collect()
    coh.close()
    # ---------------------------------------------------------------- write
    results = {}
    for name, E in encs.items():
        meta = dict(E['enc'].meta)
        dest = ((probe_root or STORE / 'probes') / os.environ['SLURM_JOB_ID'] if probe else STORE) / f'{name}__{E["key"]}' / ds / SUPPORT_ID / dsha[:16]
        tmp = dest.with_name(dest.name + '.tmp'); shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True, mode=0o700)
        ids = E['test'] + E['calib']
        T = len(E['test'])
        pmask = np.zeros((T, PN.PANEL_BLOCKS), bool); pd2 = np.full((T, 128, 128), np.nan, np.float32)
        for t, panel in enumerate(E['test']):
            got = E['partnerU'].get(panel, {})
            js = sorted(got)
            for j in js:
                pmask[t, j] = True
            if js:
                U = torch.cat([got[j] for j in js]).to(dev); d = sqd(U)
                rows = np.concatenate([np.arange(j * 32, (j + 1) * 32) for j in js])
                pd2[t][np.ix_(rows, rows)] = d
        np.savez(tmp / 'panels.npz', ids=np.array(ids), d2=np.stack([E['d2'][p] for p in ids]) if ids else np.zeros((0, 128, 128), np.float32),
                 test_ids=np.array(E['test']), partner_mask=pmask, partner_d2=pd2,
                 noise_d2=np.stack([E['noise_d2'][p] for p in E['test']]) if T else np.zeros((0, 128, 128), np.float32))
        pca = {}
        for (cf, sf), p in E['pca'].items():
            for k in ('mean', 'comp', 'calib_proj', 'calib_people'):
                pca[f'{k}_cf{cf}_sf{sf}'] = p[k]
        np.savez(tmp / 'pca.npz', **pca)
        qidx = np.array(sorted(E['qd2']), np.int64)
        np.savez(tmp / 'queries.npz', qidx=qidx,
                 d2c=np.stack([E['qd2'][i] for i in qidx]) if len(qidx) else np.zeros((0, len(iu[0])), np.float32),
                 proj=np.stack([E['qproj'][i] for i in qidx]) if len(qidx) else np.zeros((0, PN.QUERY_N, PCA_DIM), np.float32))
        info = {'encoder': name, 'enc_key': E['key'], 'meta': {k: (v if isinstance(v, (str, int, float, bool, type(None), list, dict)) else str(v))
                                                                for k, v in meta.items()},
                'registry': {k: R[name].get(k) for k in ('kind', 'input_support', 'input_support_flag', 'data_access', 'state', 'dataset',
                                                         'subject_fold', 'content_fold', 'seed', 'objective', 'training_mode')},
                'dataset': ds, 'support_id': SUPPORT_ID, 'support': SUPPORT_DESC, 'defs_sha256': dsha, 'scope': E['scope'],
                'n_test_panels': T, 'n_calib_panels': len(E['calib']), 'n_queries': int(len(qidx)),
                'partner_blocks': int(pmask.sum()), 'pca': {f'cf{cf}_sf{sf}': {'explained': p['explained'], 'n_rows': p['n_rows'],
                                                                                'people': len(p['calib_people'])}
                                                             for (cf, sf), p in E['pca'].items()},
                'files_sha256': {f: sha(tmp / f) for f in ('panels.npz', 'pca.npz', 'queries.npz')}, 'probe': probe,
                'sources': sources(), 'job': os.environ.get('SLURM_JOB_ID'), 'device': _device_name(dev)}
        write(tmp / 'meta.json', info)
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(tmp, dest)
        results[name] = {'dest': str(dest), 'enc_key': E['key'], 'files_sha256': info['files_sha256'], 'n_queries': info['n_queries'],
                         'n_test_panels': T}
    timing['total_s'] = time.time() - t_start
    timing['gpu_peak_mb'] = torch.cuda.max_memory_allocated() / 2 ** 20 if dev.type == 'cuda' else None
    return results, timing


def cpucheck():
    """CPU dry run of one tiny DTU B0 unit (1 test person, 2 training people, 1 query, scope (0, 0)); not a smoke receipt."""
    os.environ['DEP12_DEVICE'] = 'cpu'
    plan = read(FEAT / 'plan.json'); defs = PN.defs('dtu'); coh = Cohort('dtu')
    test = sorted(coh.test[0])[:1]; train = sorted(coh.train[0])[:2]; coh.close()
    row = next(r for r in plan['rows'] if r['dataset'] == 'dtu' and r['group'] == 'B0')
    res, timing = run_unit(row, probe=True, probe_limit={'scope': {(0, 0)}, 'people': test + train, 'queries': 1},
                           probe_root=FEAT / 'cpucheck')
    write(FEAT / 'cpucheck' / os.environ['SLURM_JOB_ID'] / 'result.json', {'result': res, 'timing': timing})
    print(json.dumps({'result': res, 'timing': timing}, default=str), flush=True)


def feature_dir(name, ds, meta_key=None):
    """Completed cache directory of encoder `name` on cohort ds (from the unit receipts)."""
    for row in plan_rows():
        if row['dataset'] == ds and name in row['encoders']:
            p = FEAT / 'units' / f'{row["id"]}.json'
            if p.exists():
                rec = read(p); r = rec['encoders'][name]
                return Path(r['dest']), r
    return None, None


# ------------------------------------------------------------------------------------------------ fleet
def receipts():
    out = {'pass': [], 'other': []}
    if not (FEAT / 'plan.json').exists():
        return out
    for path in sorted((FEAT / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == sha(FEAT / 'plan.json') and rec.get('sources') == sources():
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 1, 'slots': 1, 'initial': [], 'submit': []}
    if not (FEAT / 'plan.json').exists():
        return st
    remaining = [r for r in plan_rows() if not (FEAT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(remaining)
    if not remaining:
        return {**st, 'state': 'complete'}
    if not any(PF.unit_ready(r) if 'PF' in globals() else unit_ready(r) for r in remaining):
        return {**st, 'state': 'waiting_for_sources'}           # v2: no smoke while every remaining row waits for its encoders
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            return {**st, 'state': 'engineering_probe_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, 'smoke']}
    if any((FEAT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in remaining):
        return {**st, 'state': 'failed_unit_review'}
    ready = [r for r in remaining if unit_ready(r)]
    return {**st, 'state': 'ready' if ready else 'waiting_for_sources', 'ready': len(ready), 'slots': 2,
            'submit': [SBATCH, 'worker', '--max-units', '2']}


def sub(*args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *map(str, args)]).returncode


def claim(uid, fn):
    path = FEAT / 'units' / f'{uid}.json'
    lock = FEAT / 'claims' / f'{uid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock.open('a+') as h:
        try:
            fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists():
            return False
        rc = fn()
        if rc < 0:                          # preempted / signalled: no FAILED marker, the unit is redone elsewhere
            raise SystemExit(rc)
        if rc or not path.exists():
            write(FEAT / 'units' / f'{uid}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc,
                                                           'time': datetime.now().astimezone().isoformat()})
            raise RuntimeError(f'dep12 public feature unit failed: {uid}')
        return True


def worker(max_units):
    assert receipts()['pass'], 'no passing smoke receipt for the current sources / plan'
    count = 0
    order = sorted(plan_rows(), key=lambda r: (r['group'] != 'B0', r['group'].startswith('aln34'), r['dataset'], r['group']))
    for row in order:
        if (FEAT / 'units' / f'{row["id"]}.json').exists() or (FEAT / 'units' / f'{row["id"]}.FAILED.json').exists() or not unit_ready(row):
            continue
        if claim(row['id'], lambda: sub('unit', '--id', row['id'])):
            count += 1
        if count >= max_units:
            return


def unit_main(uid):
    import torch
    row = next(r for r in plan_rows() if r['id'] == uid)
    res, timing = run_unit(row)
    write(FEAT / 'units' / f'{uid}.json', {'status': 'complete', 'row': row, 'plan_sha256': sha(FEAT / 'plan.json'), 'encoders': res,
                                           'ext_plan_sha256': sha(EXT_PLAN) if EXT_PLAN.exists() else None,
                                           'timing': timing, 'job': os.environ['SLURM_JOB_ID'], 'device': _device_name(_device()),
                                           'torch_threads': torch.get_num_threads(),
                                           'sources': sources(), 'time': datetime.now().astimezone().isoformat()})
    print(uid, row['group'], row['dataset'], 'complete', json.dumps(timing), flush=True)


def smoke():
    """Engineering smoke (no outcome threshold): B0 on DTU and FAU, two test people + four training people of (cf0, sf0), three
    queries; checks shapes / finiteness / D2 symmetry / PCA, U equality of a crop recomputed through the encoder twice, and times
    the forward and the loading for the GPU-hour projection."""
    import torch
    job = os.environ['SLURM_JOB_ID']; out = FEAT / 'probes' / job
    receipt = {'status': 'running', 'job': job, 'plan_sha256': sha(FEAT / 'plan.json'), 'sources': sources(),
               'device': torch.cuda.get_device_name(0), 'checks': {}, 'timing': {}}
    try:
        from ..aln41 import timebank as TB
        receipt['checks']['resampler_vs_scipy'] = TB.check_resampler(fs_list=(128,))
        plan = {'rows': plan_rows()}
        for ds in DATASETS:
            defs = PN.defs(ds); coh = make_cohort(ds)
            test = sorted(coh.test[0])[:2]; train = sorted(coh.train[0] - {p for p in coh.train[0] if coh.parts[p].get('dev')})[:4]
            coh.close()
            row = next(r for r in plan['rows'] if r['dataset'] == ds and r['group'] == 'B0')
            res, timing = run_unit(row, probe=True, probe_limit={'scope': {(0, 0)}, 'people': test + train, 'queries': 3})
            r = res['B0']; d = Path(r['dest'])
            with np.load(d / 'panels.npz') as z:
                d2 = z['d2']; v = ~np.isnan(d2)
                assert np.allclose(np.nan_to_num(d2), np.nan_to_num(d2.transpose(0, 2, 1))) and np.isfinite(d2[v]).all()
                assert d2.shape[0] >= 2 and (d2[v] >= 0).all() and (np.nan_to_num(np.diagonal(d2, 0, 1, 2)) == 0).all()
            with np.load(d / 'queries.npz') as z:
                assert z['d2c'].shape == (r['n_queries'], PN.QUERY_N * (PN.QUERY_N - 1) // 2) and np.isfinite(z['d2c']).all()
                assert z['proj'].shape == (r['n_queries'], PN.QUERY_N, PCA_DIM)
            receipt['checks'][ds] = {'test_people': test, 'train_people': train, 'result': r,
                                     'd2_offdiag_median': float(np.nanmedian(d2[:, np.triu_indices(128, 1)[0], np.triu_indices(128, 1)[1]]))}
            receipt['timing'][ds] = timing
        # determinism: the same crops twice through B0 give identical U
        ENC = enc_module(); e = ENC.load('B0', 'cuda')
        x = torch.randn(64, 64, 200, device='cuda'); ch = Cohort('dtu').channels
        u1, u2 = e.represent(x, ch, None), e.represent(x, ch, None)
        receipt['checks']['represent_deterministic_maxabs'] = float((u1 - u2).abs().max())
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(out / 'receipt.json', receipt)


def status():
    plan = {'rows': plan_rows()} if (FEAT / 'plan.json').exists() else {'rows': []}
    done = [r for r in plan['rows'] if (FEAT / 'units' / f'{r["id"]}.json').exists()]
    print(json.dumps(fleet_status()), 'complete', len(done), '/', len(plan['rows']), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=('descriptors', 'plan', 'plan-ext', 'plan-ext2', 'plan-fed', 'plan-ext3', 'smoke', 'worker', 'unit', 'claim-unit', 'status', 'cpucheck'))
    ap.add_argument('--id'); ap.add_argument('--max-units', type=int, default=2)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.step == 'descriptors':
        for ds in PN.DATASETS:
            descriptors(ds)
        from . import federici as FED
        FED.descriptors()
    elif a.step == 'plan':
        make_plan()
    elif a.step == 'plan-ext':
        make_plan_ext()
    elif a.step == 'plan-ext2':
        make_plan_ext2()
    elif a.step == 'plan-fed':
        make_plan_fed()
    elif a.step == 'plan-ext3':
        make_plan_ext3()
    elif a.step == 'smoke':
        smoke()
    elif a.step == 'worker':
        worker(a.max_units)
    elif a.step == 'unit':
        unit_main(a.id)
    elif a.step == 'cpucheck':
        cpucheck()
    elif a.step == 'claim-unit':                    # explicit unit under the same claim lock (CPU fallback; no smoke gate)
        if not claim(a.id, lambda: sub('unit', '--id', a.id)):
            print(a.id, 'already claimed or complete', flush=True)
    else:
        status()


if __name__ == '__main__':
    main()
