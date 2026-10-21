"""ALN4.1 R1 source Stage2: within-person S32/Q32 episodes, three native crops, five arms (B0 has no Stage2).

Source pool: SparrKULee fit rows of prior33 core+rich manifests with the downstream-overlap presentations excluded
(aln34.cb_auditory.eligible). Each update draws 2 people; each person 3 content families with 11/11/10 distinct 5 s
segments for support and another 11/11/10 for query, one anchor per segment from TICK_OFFS within [26, 281], so every
crop [off-12, off+39) lies inside its own segment and S/Q access intervals are disjoint (asserted per anchor pair).
The whole stream (people, families, segments, offsets, wrong bijections) is pre-generated from one seed, hashed and
shared by every arm. Audio: env (8 samples), ss (8 frames x 4 PCA), sc (8 frame-difference norms) through the fixed
prior33 heads; all three views must be present for every anchor.
Objectives come from the package reference (temporal_objectives_torch, byte-identical copy): TCS / TNCE / GCS with the
same first-order support delta (5 steps, lr 0.1, L2 0.1) and 0.01 KL(softmax(a) || uniform); TCS_WRONG = TCS with the
audio rows of each support and query permuted by a cross-family bijection shared by the three views.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import gc
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
from ..aln34 import learning_budget as B

OUT = Path(core.OUT) / 'aln41'
BASE = OUT / 'source_v1'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln41/source_v1')
PACKAGE = Path(core.REPO) / 'AUDITORY_ALN4_SERVER_PACKAGE_v4_1_20261021'
PACKAGE_ZIP_SHA256 = 'eb9b343beb81994bf564a81b65577f0160547005a162db7894766e36e7971b2c'
MANIFEST = Path(core.OUT) / 'aln34/prior33/manifest.json'
MANIFEST_SHA = 'b751976b9238590026f26a6fbe6c84177b69802ef9e55e687425af210b627426'
RICH = Path(core.OUT) / 'aln34/prior33/manifest_rich.json'
RICH_SHA = 'c8f11c28b4014aec3f06f52e3c058640409d8fa9d0d8a91c95f2f05505eabcfd'
STAGE1_GATE = OUT / 'intake/STAGE1_GATE.json'
SEED = 3401
STREAM_SEED = 3401 + 41000
PANEL_SEED = 3420
CAL_LRS = (1e-4, 3e-4)
CAL_STEPS, PROD_STEPS = 1000, 10000
PROD_SNAPSHOTS = (0, 2500, 5000, 10000)
FAMILY_COUNTS = (11, 11, 10)
OFF_LO, OFF_HI = 26, 281
INNER = {'steps': 5, 'step_size': 0.1, 'delta_l2': 0.1, 'prior_kl_weight': 0.01, 'temperature': 0.1}
ARMS = ('TCS', 'TNCE', 'GCS', 'TCS_WRONG')
UNUSED_WITHOUT_MASK = ('net.patch_embedding.mask_encoding',)
NAME, LANE, SBATCH = 'c3_s35a41src', 's35_aln41_source', 'slurm/aln35_aln41_source.sbatch'

sha, write, dumps = B.sha, B.write, B.dumps


def read(p):
    return json.loads(Path(p).read_text())


def digest(v, n=64):
    return hashlib.sha256(dumps(v).encode()).hexdigest()[:n]


def sources():
    here = Path(__file__).parent
    files = [here / f for f in ('source.py', 'timebank.py', 'temporal_objectives_torch.py', 'cs_qmi_reference.py', 'time_access.py')]
    files += [Path(core.REPO) / 'auditory_alignment_v3/prior33' / f for f in ('views.py', 'model.py', 'contract.py', 'losses.py')]
    files += [Path(core.REPO) / 'auditory_alignment_v3/aln34/cb_auditory.py', Path(core.REPO) / 'auditory_alignment_v3/fm_aligned.py',
              Path(core.REPO) / 'auditory_alignment_v2/foundation_adapter.py']
    return {str(p.relative_to(core.REPO)): sha(p) for p in sorted(set(files))}


def open_manifest():
    from ..prior33 import views as V
    assert sha(MANIFEST) == MANIFEST_SHA and sha(RICH) == RICH_SHA
    return V.open_with_rich(V.open_manifest(MANIFEST, MANIFEST_SHA), RICH_SHA, str(RICH))


def ticks():
    from ..prior33 import contract as PC
    t = PC.TICK_OFFS.astype(np.int64)
    t = t[(t >= OFF_LO) & (t <= OFF_HI)]
    assert len(t) == 200 and t[-1] == 280
    return t


# ----------------------------------------------------------------------------------------------- sampling pool and stream
def pool(man):
    """Eligible fit segments with complete rich streams, grouped person -> family -> segment rows (sorted)."""
    from ..aln34 import cb_auditory as CA
    from ..prior33 import views as V
    idx = V.manifest_index(man); seg = idx.seg['sparrkulee']; elig = CA.eligible(man)
    rs = V.cohort_streams(man, 'sparrkulee', None, 'rich_streams')
    available = np.array([bool(r['available']) for r in rs], dtype=bool)
    out, dropped = {}, {'rich_unavailable': 0}
    excluded = set(elig['excluded_presentations'])
    # dev = the manifest's pools.dev.sparrkulee (package: 6,332 / 10 / 9), not cb_auditory's 400 fixed dev queries
    dev_rows = [int(r) for r in man['pools']['dev']['sparrkulee'] if int(seg['presentation'][int(r)]) not in excluded]
    assert all(seg['role'][r] == 'dev' for r in dev_rows)
    for split, rows in (('fit', elig['fit']), ('dev', dev_rows)):
        groups = {}
        for r in rows:
            st = int(idx.stream[seg['presentation'][r]])
            if st < 0 or not available[st]:
                dropped['rich_unavailable'] += 1; continue
            groups.setdefault(str(seg['participant'][r]), {}).setdefault(int(seg['family'][r]), []).append(int(r))
        out[split] = {p: {f: sorted(v) for f, v in sorted(fs.items())} for p, fs in sorted(groups.items())}
    fit_people, dev_people = set(out['fit']), set(out['dev'])
    fit_fams = {f for p in out['fit'].values() for f in p}; dev_fams = {f for p in out['dev'].values() for f in p}
    assert not fit_people & dev_people and not fit_fams & dev_fams, 'source fit/dev people or content overlap'
    return out, {'excluded_presentations': elig['excluded_presentations'], 'dropped': dropped,
                 'fit_people': len(fit_people), 'fit_families': len(fit_fams), 'dev_people': len(dev_people), 'dev_families': len(dev_fams),
                 'fit_segments': sum(len(v) for p in out['fit'].values() for v in p.values()),
                 'dev_segments': sum(len(v) for p in out['dev'].values() for v in p.values())}


def eligible_people(fit):
    """People with >= 3 families holding >= 22 segments (11 support + 11 query); others are listed, not used."""
    need = 2 * max(FAMILY_COUNTS)
    ok, excluded = {}, {}
    for p, fams in fit.items():
        good = [f for f, rows in fams.items() if len(rows) >= need]
        if len(good) >= 3:
            ok[p] = good
        else:
            excluded[p] = {'families_with_22_segments': len(good)}
    return ok, excluded


def cross_family_bijection(fam, rng):
    """Permutation pi with fam[pi[i]] != fam[i] for all i (families of sizes 11/11/10): shift by 11 in a shuffled family order."""
    order = []
    labels = list(dict.fromkeys(fam.tolist()))
    rng.shuffle(labels)
    labels.sort(key=lambda f: -int((fam == f).sum()))  # the two 11-families first, then the 10-family
    for f in labels:
        rows = np.flatnonzero(fam == f); rng.shuffle(rows); order.extend(rows.tolist())
    order = np.array(order); n = len(order); pi = np.empty(n, np.int64)
    pi[order] = order[(np.arange(n) + max(FAMILY_COUNTS)) % n]
    assert np.all(fam[pi] != fam) and len(set(pi.tolist())) == n
    return pi


def make_stream(fit, people, n_updates, seed=STREAM_SEED):
    """[U, 2 people, 2 splits (S, Q), 32] segment rows / offsets / wrong permutations; one anchor per segment."""
    from ..prior33 import views as V
    rng = np.random.default_rng(seed); offs = ticks(); names = sorted(people)
    rows = np.zeros((n_updates, 2, 2, 32), np.int64); off = np.zeros_like(rows); wrong = np.zeros_like(rows)
    who = np.zeros((n_updates, 2), np.int64); fams = np.zeros((n_updates, 2, 3), np.int64)
    for u in range(n_updates):
        pair = rng.choice(len(names), size=2, replace=False); who[u] = pair
        for j, pi in enumerate(pair):
            p = names[pi]; chosen = rng.choice(people[p], size=3, replace=False)
            counts = np.array(FAMILY_COUNTS)[rng.permutation(3)]
            fams[u, j] = chosen
            S, Q, fS, fQ = [], [], [], []
            for f, c in zip(chosen, counts):
                pick = rng.choice(fit[p][int(f)], size=2 * c, replace=False)
                S += pick[:c].tolist(); Q += pick[c:].tolist(); fS += [f] * c; fQ += [f] * c
            for k, (r, fl) in enumerate(((S, fS), (Q, fQ))):
                rows[u, j, k] = r; off[u, j, k] = rng.choice(offs, size=32, replace=True)
                wrong[u, j, k] = cross_family_bijection(np.array(fl), rng)
    return {'rows': rows, 'off': off, 'wrong': wrong, 'who': who, 'families': fams, 'people': np.array(names)}


def access_intervals(seg, rows, off):
    s = seg['s'][rows]
    return seg['piece'][rows], s + off - 12, s + off + 39


def check_stream(man, stream, sample=None):
    """S/Q disjoint segments and physical access, one anchor per segment, crops inside the 5 s segment, wrong bijection."""
    from ..prior33 import views as V, contract as PC
    seg = V.manifest_index(man).seg['sparrkulee']
    U = len(stream['rows']); idx = range(U) if sample is None else sample
    for u in idx:
        for j in range(2):
            S, Q = stream['rows'][u, j]
            assert len(set(S.tolist())) == 32 and len(set(Q.tolist())) == 32 and not set(S.tolist()) & set(Q.tolist())
            assert len({str(seg['participant'][r]) for r in np.r_[S, Q]}) == 1
            pS, aS, bS = access_intervals(seg, S, stream['off'][u, j, 0]); pQ, aQ, bQ = access_intervals(seg, Q, stream['off'][u, j, 1])
            assert np.all(aS >= seg['s'][S]) and np.all(bS <= seg['s'][S] + PC.SEG_STEP)
            assert np.all(aQ >= seg['s'][Q]) and np.all(bQ <= seg['s'][Q] + PC.SEG_STEP)
            same = pS[:, None] == pQ[None, :]
            overlap = (aS[:, None] < bQ[None, :]) & (aQ[None, :] < bS[:, None])
            assert not np.any(same & overlap), 'support/query physical access overlap'
            for k, rr in enumerate((S, Q)):
                fam = seg['family'][rr]; pi = stream['wrong'][u, j, k]
                assert np.all(fam[pi] != fam) and sorted(pi.tolist()) == list(range(32))
    return True


def make_panel(split_pool, n, seed, offs):
    """n anchors spread round-robin over people, then over each person's families; one anchor per segment."""
    rng = np.random.default_rng(seed); people = sorted(split_pool); picks = []
    lanes = {}
    for p in people:            # per person: segments interleaved over a shuffled family order
        fams = list(split_pool[p]); rng.shuffle(fams); queues = [list(rng.permutation(split_pool[p][f])) for f in fams]
        order = []
        while any(queues):
            for q in queues:
                if q:
                    order.append(int(q.pop()))
        lanes[p] = order
    assert sum(len(v) for v in lanes.values()) >= n, 'panel larger than the pool'
    while len(picks) < n:      # global round-robin over people (people with few segments simply run out)
        for p in people:
            if len(picks) < n and lanes[p]:
                picks.append((lanes[p].pop(0), int(rng.choice(offs))))
    rows = np.array([r for r, _ in picks]); off = np.array([o for _, o in picks])
    assert len(set(rows.tolist())) == n
    return rows, off


# ----------------------------------------------------------------------------------------------- data access on the device
class Source:
    def __init__(self, man, segment_rows, device):
        from ..prior33 import views as V, model as M, losses as L
        self.man, self.idx = man, V.manifest_index(man); self.seg = self.idx.seg['sparrkulee']
        self.bank = V.DonorBank(man, 'sparrkulee', ('fit', 'dev'), device=device, rich=True, segments=np.unique(segment_rows))
        from ..prior33 import contract as PC
        assert self.bank.layout == PC.BIOSEMI64
        self.heads = {k: h.to(device).requires_grad_(False).eval() for k, h in M.fixed_heads(man, man.root).items()}
        assert set(self.heads) == {'env', 'ss', 'sc'}
        self.unknown = tuple(L.unknown_clock_families(man)); self.device = device

    def crops(self, rows, off):
        """Native 64 Hz bank [off-12, off+39) -> the three crops (window-relative slices of the 51 samples)."""
        import torch
        piece, start = self.seg['piece'][rows], self.seg['s'][rows]
        a = self.bank.gather(piece, start, off - 12)          # [n, C, 38]: off-12 .. off+25
        b = self.bank.gather(piece, start, off + 13)          # [n, C, 38]: off+13 .. off+50
        x = torch.cat([a, b[..., 13:26]], dim=-1).float()     # off-12 .. off+38 (51 samples)
        assert x.shape[-1] == 51 and bool(torch.isfinite(x).all())
        return [x[..., 0:25], x[..., 12:38], x[..., 25:51]]   # [-12,13), [0,26), [13,39) relative to off

    @property
    def nbytes(self):
        return self.bank.nbytes

    def audio(self, rows, off):
        import torch
        pres, start = self.seg['presentation'][rows], self.seg['s'][rows]
        env = self.bank.targets(pres, start, off); ss, sc, ok = self.bank.rich_targets(pres, start, off)
        assert bool(ok.all()), 'a rich view is missing for a sampled anchor'
        raw = {'env': env, 'ss': ss, 'sc': sc}
        with torch.no_grad():
            heads = {k: self.heads[k](v) for k, v in raw.items()}
        return heads, raw

    def keys(self, rows, off):
        import torch
        return torch.as_tensor(self.idx.keys(self.seg['presentation'][rows], self.seg['s'][rows] + off), device=self.device)


# ----------------------------------------------------------------------------------------------- plan and fixed panels
def make_plan():
    """Calibration rows (3 objectives x 2 LR x 1000 updates); production rows are added by select() after calibration."""
    man = open_manifest(); split_pool, pool_info = pool(man); people, excluded = eligible_people(split_pool['fit'])
    stream = make_stream(split_pool['fit'], people, PROD_STEPS)
    check_stream(man, stream)
    offs = ticks()
    panels = {k: make_panel(split_pool[k], 512, PANEL_SEED + i, offs) for i, k in enumerate(('fit', 'dev'))}
    STORE.mkdir(parents=True, exist_ok=True, mode=0o700); BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(STORE / 'stream.npz', **stream)
    np.savez_compressed(STORE / 'panels.npz', fit_rows=panels['fit'][0], fit_off=panels['fit'][1], dev_rows=panels['dev'][0], dev_off=panels['dev'][1])
    gate = read(STAGE1_GATE); assert gate['asset_gate'] == 'not_passed' and gate['stage1_selected']['arch'] == 'cbramod'
    rows = []
    for obj in ('TCS', 'TNCE', 'GCS'):
        for lr in CAL_LRS:
            body = {'stage': 'calibration', 'arm': obj, 'lr': lr, 'updates': CAL_STEPS, 'seed': SEED}
            rows.append({**body, 'id': 'ALN41C_' + digest(body, 16)})
    body = {'version': 'ALN41_SOURCE_v1', 'rows': rows, 'sources': sources(), 'store': str(STORE), 'package_zip_sha256': PACKAGE_ZIP_SHA256,
            'manifest_sha256': MANIFEST_SHA, 'rich_sha256': RICH_SHA, 'stage1': gate['stage1_selected'], 'stage1_gate_sha256': sha(STAGE1_GATE),
            'pool': pool_info, 'eligible_people': len(people), 'excluded_people': excluded, 'stream_sha256': sha(STORE / 'stream.npz'),
            'panels_sha256': sha(STORE / 'panels.npz'), 'panel_seed': PANEL_SEED, 'stream_seed': STREAM_SEED, 'inner': INNER,
            'optimizer': {'kind': 'AdamW', 'weight_decay': 1e-4, 'no_decay': 'biases, norm parameters, gate logits a', 'cosine': True, 'clip': 5.0},
            'calibration_lrs': list(CAL_LRS), 'calibration_updates': CAL_STEPS, 'production_updates': PROD_STEPS,
            'production_snapshots': list(PROD_SNAPSHOTS), 'arms': list(ARMS), 'views': ['env', 'ss', 'sc']}
    plan = BASE / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    print('ALN41 source plan', len(rows), 'calibration fits;', len(people), 'eligible fit people;', pool_info, sha(plan), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen source drift'
    assert sha(STORE / 'stream.npz') == plan['stream_sha256'] and sha(STORE / 'panels.npz') == plan['panels_sha256']


def load_arrays(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def build_model(device):
    import torch
    from . import timebank as TB
    torch.manual_seed(SEED)
    model = TB.TimeBankModel('dtu', 64, 64).to(device)
    a = torch.zeros(3, device=device, requires_grad=True)
    return model, a


def state_digest(model):
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode()); h.update(v.detach().float().cpu().numpy().tobytes())
    return h.hexdigest()


def panel_features(src, model, rows, off, chunk=128):
    """Projected EEG [n,3,32] per view, audio heads [n,32] per view, raw backbone tokens [n, 3*C*E] (float32 CPU), raw audio."""
    import torch
    U = {v: [] for v in ('env', 'ss', 'sc')}; T = []; A = {v: [] for v in U}; R = {v: [] for v in U}
    model.eval()
    with torch.no_grad():
        for k in range(0, len(rows), chunk):
            r, o = rows[k:k + chunk], off[k:k + chunk]
            proj, tok = model(src.crops(r, o)); heads, raw = src.audio(r, o)
            for v in U:
                U[v].append(proj[v].double().cpu()); A[v].append(heads[v].double().cpu()); R[v].append(raw[v].double().cpu())
            T.append(tok.flatten(1).float().cpu())
    return ({v: torch.cat(x) for v, x in U.items()}, {v: torch.cat(x) for v, x in A.items()}, torch.cat(T), {v: torch.cat(x) for v, x in R.items()})


def lower_median(d):
    d = np.sort(np.asarray(d, np.float64).ravel())
    return float(d[(len(d) - 1) // 2])


def calibrate_sigmas(U, A):
    """Per view: one EEG sigma over within-window distinct-anchor pairs pooled over the 3 windows; audio sigma; pooled GCS sigma."""
    import torch
    out = {}
    for v in U:
        u = U[v]; n = len(u); off = ~torch.eye(n, dtype=torch.bool)
        dist = torch.cat([torch.cdist(u[:, k], u[:, k])[off] for k in range(u.shape[1])])
        da = torch.cdist(A[v], A[v])[off]
        pooled = torch.nn.functional.normalize(u.mean(1), dim=-1); dp = torch.cdist(pooled, pooled)[off]
        out[v] = {'sigma_u': lower_median(dist.numpy()), 'sigma_v': lower_median(da.numpy()), 'sigma_pooled_u': lower_median(dp.numpy()),
                  'eeg_distance_quantiles': np.quantile(dist.numpy(), [0, .1, .5, .9, 1]).tolist(),
                  'audio_distance_quantiles': np.quantile(da.numpy(), [0, .1, .5, .9, 1]).tolist(),
                  'pooled_norm_before_normalisation': [float(x) for x in torch.linalg.vector_norm(u.mean(1), dim=-1).quantile(torch.tensor([0., .5, 1.], dtype=u.dtype))]}
        for key in ('sigma_u', 'sigma_v', 'sigma_pooled_u'):
            assert math.isfinite(out[v][key]) and out[v][key] > 0, (v, key)
    return out


def ridge_probe(Tf, Rf, Td, Rd):
    """Common LR-selection probe: standardised raw tokens -> standardised raw acoustic views; dual ridge with intercept,
    lambda = 1e-3 trace(X X^T)/n; dev normalised MSE (relative to the fit mean) per view, equal-weight mean."""
    import torch
    X = Tf.double(); mu = X.mean(0); sd = X.std(0) + 1e-8; X = (X - mu) / sd; Xd = (Td.double() - mu) / sd
    K = X @ X.T; lam = 1e-3 * float(torch.trace(K)) / len(X)
    alpha = torch.linalg.solve(K + lam * torch.eye(len(X), dtype=K.dtype), torch.eye(len(X), dtype=K.dtype))
    out = {}
    for v in Rf:
        Y = Rf[v].double(); ym = Y.mean(0); ys = Y.std(0) + 1e-8; Yz = (Y - ym) / ys; Ydz = (Rd[v].double() - ym) / ys
        W = X.T @ (alpha @ Yz); P = Xd @ W
        out[v] = float(((P - Ydz) ** 2).mean() / (Ydz ** 2).mean())
    out['mean'] = float(np.mean([out[v] for v in Rf]))
    out['lambda'] = lam
    return out


def view_batches(U, A, sig, wrong=None):
    from .temporal_objectives_torch import ViewBatch
    return [ViewBatch(U[v], (A[v] if wrong is None else A[v][wrong]).double(), sig[v]['sigma_u'], sig[v]['sigma_v'],
                      sig[v]['sigma_pooled_u'], v) for v in ('env', 'ss', 'sc')]


def sigmas_path():
    return BASE / 'sigmas.json'


def fix_sigmas(plan, device):
    """Initial-state source-fit panel bandwidths (identical init for all arms); written once, then frozen."""
    import torch
    man = open_manifest(); P = load_arrays(STORE / 'panels.npz')
    src = Source(man, np.r_[P['fit_rows'], P['dev_rows']], device); model, a = build_model(device)
    U, A, _, _ = panel_features(src, model, P['fit_rows'], P['fit_off'])
    sig = calibrate_sigmas(U, A)
    body = {'plan_sha256': sha(BASE / 'plan.json'), 'initial_state_sha256': state_digest(model), 'panel': 'fit 512 anchors, seed 3420',
            'rule': 'lower median of distinct-anchor distances; EEG pooled over the 3 same-window blocks; GCS: uniform-mean pooled then L2',
            'sigmas': sig, 'device': torch.cuda.get_device_name(0), 'job': os.environ.get('SLURM_JOB_ID')}
    path = sigmas_path()
    if path.exists():
        old = read(path)
        assert old['initial_state_sha256'] == body['initial_state_sha256'], 'initial state differs from the frozen sigma receipt'
        for v in sig:
            for k in ('sigma_u', 'sigma_v', 'sigma_pooled_u'):
                assert abs(old['sigmas'][v][k] - sig[v][k]) <= 1e-6 * max(1, abs(sig[v][k])), (v, k)
        return old
    write(path, body); path.chmod(0o444)
    return body


# ----------------------------------------------------------------------------------------------- one source fit
def param_groups(model, a, lr):
    decay, no = [], []
    for n, p in model.named_parameters():
        (no if (p.ndim <= 1 or n.endswith('.bias')) else decay).append(p)
    return [{'params': decay, 'lr': lr, 'weight_decay': 1e-4, 'name': 'decay'},
            {'params': no, 'lr': lr, 'weight_decay': 0.0, 'name': 'no_decay'},
            {'params': [a], 'lr': lr, 'weight_decay': 0.0, 'name': 'gate_logits'}]


def run_unit(row, plan, probe=False):
    import torch
    from . import temporal_objectives_torch as TO
    started = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    sig = read(sigmas_path())['sigmas']
    stream = load_arrays(STORE / 'stream.npz'); P = load_arrays(STORE / 'panels.npz'); man = open_manifest()
    steps = 3 if probe else row['updates']
    used = stream['rows'][:steps].reshape(-1)
    src = Source(man, np.r_[used, P['fit_rows'], P['dev_rows']], dev)
    model, a = build_model(dev)
    init_digest = state_digest(model); assert init_digest == read(sigmas_path())['initial_state_sha256']
    initial = {k: v.detach().cpu().clone() for k, v in model.bb.state_dict().items()}
    kind = 'TCS' if row['arm'] == 'TCS_WRONG' else row['arm']
    opt = torch.optim.AdamW(param_groups(model, a, row['lr']), lr=row['lr']); sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    params = [p for g in opt.param_groups for p in g['params']]
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    out = BASE / 'probes' / job if probe else BASE
    snapshots = (0, steps) if (probe or row['stage'] == 'calibration') else PROD_SNAPSHOTS
    log, begin, ckpts = [], 0, {}
    resume = dest / 'resume.pt'

    def save(step):
        path = dest / f'update{step}.pt'
        B_atomic(path, {'backbone': model.bb.state_dict(), 'heads': model.heads.state_dict(), 'a': a.detach().cpu(), 'step': step,
                        'row': row, 'plan_sha256': sha(BASE / 'plan.json'), 'probe': probe})
        ckpts[str(step)] = {'path': str(path), 'sha256': sha(path)}

    if resume.exists():
        st = torch.load(resume, map_location=dev, weights_only=False)
        assert st['row'] == row and st['plan_sha256'] == sha(BASE / 'plan.json')
        model.load_state_dict(st['model']); a.data.copy_(st['a']); opt.load_state_dict(st['opt']); sched.load_state_dict(st['sched'])
        begin, log, ckpts = st['step'], st['log'], st['ckpts']
        torch.set_rng_state(st['torch_rng'].cpu()); torch.cuda.set_rng_state(st['cuda_rng'].cpu())
    else:
        save(0)
    for u in range(begin, steps):
        model.train(); total = 0.0; reps = []
        for j in range(2):
            S, Q = stream['rows'][u, j]; oS, oQ = stream['off'][u, j]
            AS, _ = src.audio(S, oS); AQ, _ = src.audio(Q, oQ)
            with torch.no_grad():
                US, _ = model(src.crops(S, oS))
            UQ, _ = model(src.crops(Q, oQ))
            wS = wQ = None
            if row['arm'] == 'TCS_WRONG':
                wS = torch.as_tensor(stream['wrong'][u, j, 0], device=dev); wQ = torch.as_tensor(stream['wrong'][u, j, 1], device=dev)
            sv = view_batches({v: x.detach() for v, x in US.items()}, AS, sig, wS); qv = view_batches(UQ, AQ, sig, wQ)
            kw = dict(steps=INNER['steps'], step_size=INNER['step_size'], delta_l2=INNER['delta_l2'], prior_kl_weight=INNER['prior_kl_weight'],
                      temperature=INNER['temperature'])
            if kind == 'TNCE':
                kw.update(support_keys=src.keys(S, oS), query_keys=src.keys(Q, oQ), unknown_clock_families=src.unknown)
            loss, rep = TO.episode_loss_fo(kind, sv, qv, a, **kw)
            total = total + loss / 2; reps.append(rep)
        opt.zero_grad(set_to_none=True); total.backward()
        gn = torch.nn.utils.clip_grad_norm_(params, 5.0)
        if not torch.isfinite(total) or not torch.isfinite(gn):
            raise FloatingPointError(f'nonfinite source objective or gradient at update {u}')
        if u == begin and begin == 0:
            # CBraMod's masked-pretraining token is only read when a mask is passed (never in Stage2): no gradient is expected.
            missing = [n for n, p in model.bb.named_parameters() if n not in UNUSED_WITHOUT_MASK
                       and (p.grad is None or not bool(torch.any(p.grad != 0)))]
            assert not missing, f'backbone tensors without gradient: {missing[:5]}'
        opt.step(); sched.step()
        if (u + 1) % 25 == 0 or u < 3 or probe:
            log.append({'update': u + 1, 'loss': float(total.detach()), 'grad_norm': float(gn), 'lr': float(sched.get_last_lr()[0]),
                        'a': a.detach().cpu().tolist(), 'q_prior': torch.softmax(a.detach(), 0).cpu().tolist(),
                        'people': [str(stream['people'][stream['who'][u, j]]) for j in range(2)],
                        'delta': [r['delta'].cpu().tolist() for r in reps],
                        'query': [{'loss_nats': r['query']['loss_nats'],
                                   'views': [{k: w[k] for k in w if k in ('view', 'score_nats', 'loss_nats', 'q', 'log_A', 'log_B', 'log_C',
                                                                            'slot_scores_nats', 'slot_loss_nats', 'pooled_norm_min')}
                                             for w in r['query']['views']]} for r in reps]})
        if (u + 1) in snapshots:
            save(u + 1)
        if (u + 1) % 100 == 0 and not probe:
            B_atomic(resume, {'model': model.state_dict(), 'a': a.detach(), 'opt': opt.state_dict(), 'sched': sched.state_dict(), 'step': u + 1,
                              'log': log, 'ckpts': ckpts, 'row': row, 'plan_sha256': sha(BASE / 'plan.json'),
                              'torch_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state()})
        if (u + 1) % 500 == 0:
            print(row['id'], row['arm'], 'update', u + 1, round(float(total.detach()), 5), round(time.time() - started, 1), flush=True)
    num = den = 0.0
    for n, p in model.bb.state_dict().items():
        q = initial[n].to(dev).float(); num += float(((p.float() - q) ** 2).sum()); den += float((q ** 2).sum())
    Uf, Af, Tf, Rf = panel_features(src, model, P['fit_rows'], P['fit_off'])
    Ud, Ad, Td, Rd = panel_features(src, model, P['dev_rows'], P['dev_off'])
    probe_score = ridge_probe(Tf, Rf, Td, Rd)
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(BASE / 'plan.json'), 'updates': steps, 'log': log,
           'checkpoints': ckpts, 'final_checkpoint': ckpts[str(steps)]['path'], 'final_checkpoint_sha256': ckpts[str(steps)]['sha256'],
           'initial_state_sha256': init_digest, 'relative_backbone_change': math.sqrt(num) / (math.sqrt(den) + 1e-12),
           'selection_probe': probe_score, 'final_a': a.detach().cpu().tolist(), 'final_q_prior': torch.softmax(a.detach(), 0).cpu().tolist(),
           'bank_nbytes': src.nbytes, 'device': torch.cuda.get_device_name(0), 'job': job, 'seconds': time.time() - started,
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'objective_kind': kind,
           'wrong_pairing': 'cross-family bijection per support and query, shared by the three views' if row['arm'] == 'TCS_WRONG' else None}
    write(out / 'units' / f'{row["id"]}.json', rec)
    if resume.exists() and not probe:
        resume.unlink()
    print(row['id'], 'complete', row['arm'], row['lr'], 'probe', probe, round(rec['seconds'], 1), probe_score['mean'], flush=True)
    return rec


def B_atomic(path, value):
    import torch
    tmp = Path(str(path) + '.tmp'); torch.save(value, tmp); os.replace(tmp, path)


# ----------------------------------------------------------------------------------------------- readiness and selection
def readiness(plan):
    """Engineering checks on real data/model; no outcome threshold."""
    import torch
    from auditory_alignment_v2.foundation_adapter import Backbone, CBRAMOD_W
    from . import timebank as TB
    dev = torch.device('cuda'); out = {'resampler': TB.check_resampler()}
    assert max(r['max_abs_error'] for r in out['resampler']) < 1e-9
    sd = torch.load(CBRAMOD_W, map_location='cpu')
    out['stage1'] = {'weights_sha256': sha(CBRAMOD_W), 'expected_numel': int(sum(v.numel() for v in sd.values())), 'strict_load': True}
    probes = {}
    for key, n_ch, fs in (('private_bdf', 20, 250), ('fau', 31, 128), ('dtu', 64, 64)):
        torch.manual_seed(0)
        m = TB.TimeBankModel(key, n_ch, fs).to(dev).eval()
        loaded = int(sum(v.numel() for k, v in m.bb.net.state_dict().items() if k in sd))
        lay = TB.layout(fs); crops = [torch.randn(4, n_ch, b - a, device=dev) for a, b, _ in lay]
        proj, tok = m(crops)
        probes[key] = {'n_ch': n_ch, 'fs': fs, 'layout': lay, 'tokens': list(tok.shape), 'loaded_backbone_numel': loaded,
                       'finite': bool(torch.isfinite(tok).all())}
        assert tok.shape == (4, 3, n_ch, 200) and probes[key]['finite']
    out['channel_probes'] = probes
    man = open_manifest(); stream = load_arrays(STORE / 'stream.npz')
    check_stream(man, stream); out['stream_check'] = {'updates': int(len(stream['rows'])), 'status': 'pass'}
    model, a = build_model(dev); src = Source(man, stream['rows'][:2].reshape(-1), dev)
    model.eval()
    with torch.no_grad():
        p1, _ = model(src.crops(stream['rows'][0, 0, 0], stream['off'][0, 0, 0]))
    tmp = STORE / 'probes' / os.environ['SLURM_JOB_ID']; tmp.mkdir(parents=True, exist_ok=True, mode=0o700)
    torch.save({'model': model.state_dict()}, tmp / 'reload.pt')
    m2, _ = build_model(dev); m2.load_state_dict(torch.load(tmp / 'reload.pt', map_location=dev)['model'], strict=True); m2.eval()
    with torch.no_grad():
        p2, _ = m2(src.crops(stream['rows'][0, 0, 0], stream['off'][0, 0, 0]))
    out['save_reload_max_abs_diff'] = max(float((p1[v] - p2[v]).abs().max()) for v in p1)
    assert out['save_reload_max_abs_diff'] == 0.0
    (tmp / 'reload.pt').unlink()
    return out


def select():
    """Per objective: LR with the lower dev normalised MSE of the common probe (exact tie -> 1e-4); TCS_WRONG inherits TCS."""
    plan = read(BASE / 'plan.json'); choice = {}
    for obj in ('TCS', 'TNCE', 'GCS'):
        recs = {}
        for r in plan['rows']:
            if r['arm'] == obj:
                u = read(BASE / 'units' / f'{r["id"]}.json'); assert u['status'] == 'complete'
                recs[r['lr']] = u['selection_probe']
        best = min(CAL_LRS, key=lambda lr: (recs[lr]['mean'], lr))
        finite = all(math.isfinite(recs[lr]['mean']) for lr in CAL_LRS)
        choice[obj] = {'lr': best if finite else 1e-4, 'probe': {str(k): v for k, v in recs.items()},
                       'status': 'selected' if finite else 'uninformative_selection'}
    choice['TCS_WRONG'] = {'lr': choice['TCS']['lr'], 'status': 'inherits_TCS'}
    rows = []
    for arm in ARMS:
        body = {'stage': 'production', 'arm': arm, 'lr': choice[arm]['lr'], 'updates': PROD_STEPS, 'seed': SEED}
        rows.append({**body, 'id': 'ALN41P_' + digest(body, 16)})
    sel = {'version': 'ALN41_SOURCE_SELECTION_v1', 'plan_sha256': sha(BASE / 'plan.json'), 'choice': choice, 'production_rows': rows,
           'rule': 'common probe dev normalised MSE, equal-weight env/ss/sc; source fit/dev panels only; no target data',
           'created': datetime.now().astimezone().isoformat()}
    path = BASE / 'selection.json'
    if path.exists():
        old = read(path); assert old['choice'] == choice and old['production_rows'] == rows
        return old
    write(path, sel); path.chmod(0o444)
    return sel


def all_rows():
    plan = read(BASE / 'plan.json'); rows = list(plan['rows'])
    if (BASE / 'selection.json').exists():
        rows += read(BASE / 'selection.json')['production_rows']
    return plan, rows


def receipts():
    out = {'pass': [], 'other': []}
    if not (BASE / 'plan.json').exists():
        return out
    for path in sorted((BASE / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == sha(BASE / 'plan.json'):
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 10, 'slots': 1, 'initial': [], 'submit': []}
    if not (BASE / 'plan.json').exists():
        return st
    plan, rows = all_rows()
    calib = [r for r in rows if r['stage'] == 'calibration']
    calib_done = all((BASE / 'units' / f'{r["id"]}.json').exists() for r in calib)
    remaining = [r for r in rows if not (BASE / 'units' / f'{r["id"]}.json').exists()]
    pending_selection = calib_done and not (BASE / 'selection.json').exists()
    st['remaining'] = len(remaining) + (4 if not (BASE / 'selection.json').exists() else 0)
    if not remaining and (BASE / 'selection.json').exists():
        st['state'] = 'complete'; return st
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            st['state'] = 'engineering_probe_failed'; return st
        st.update(state='ready', ready=1, submit=[SBATCH, '--smoke']); return st
    available = [r for r in remaining if not (BASE / 'units' / f'{r["id"]}.FAILED.json').exists()]
    n_ready = len(available) + (4 if pending_selection else 0)
    st.update(state='ready' if n_ready else ('waiting_calibration' if not remaining else 'failed_unit_review'), ready=n_ready, slots=2,
              submit=[SBATCH, '--smoke-job', rec['pass'][-1].parent.name, '--max-units', '1'])
    return st


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'smoke', 'select'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit'); ap.add_argument('--smoke-job'); ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(BASE / 'plan.json'); verify(plan)
    if a.select:
        print(json.dumps(select()['choice'])); return
    _, rows = all_rows()
    if a.unit or a.probe_unit:
        run_unit(next(r for r in rows if r['id'] in (a.unit, a.probe_unit)), plan, probe=bool(a.probe_unit)); return
    if a.smoke:
        import torch
        job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(BASE / 'plan.json'), 'units': []}
        try:
            receipt['sigmas'] = fix_sigmas(plan, torch.device('cuda'))['sigmas']
            receipt['readiness'] = readiness(plan)
            for arm in ('TCS', 'TNCE', 'GCS'):
                row = next(r for r in rows if r['arm'] == arm)
                rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['id']]).returncode
                assert rc == 0, arm
                rec = read(BASE / 'probes' / job / 'units' / f'{row["id"]}.json')
                receipt['units'].append({'id': row['id'], 'arm': arm, 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'],
                                         'losses': [x['loss'] for x in rec['log']], 'probe': rec['selection_probe']})
            wrong = dict(next(r for r in rows if r['arm'] == 'TCS'), arm='TCS_WRONG', id='ALN41_SMOKE_WRONG')
            rec = run_unit(wrong, plan, probe=True)
            receipt['units'].append({'id': 'TCS_WRONG(smoke)', 'arm': 'TCS_WRONG', 'losses': [x['loss'] for x in rec['log']]})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            write(BASE / 'probes' / job / 'receipt.json', receipt)
        return
    rec = read(BASE / 'probes' / str(a.smoke_job) / 'receipt.json'); assert rec['status'] == 'pass' and rec['plan_sha256'] == sha(BASE / 'plan.json')
    calib = [r for r in rows if r['stage'] == 'calibration']
    if all((BASE / 'units' / f'{r["id"]}.json').exists() for r in calib) and not (BASE / 'selection.json').exists():
        lock = BASE / 'claims' / 'select.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            fcntl.flock(h, fcntl.LOCK_EX)
            print('selection', json.dumps(select()['choice']), flush=True)
        _, rows = all_rows()
    count = 0
    for row in rows:
        path = BASE / 'units' / f'{row["id"]}.json'
        if path.exists() or (BASE / 'units' / f'{row["id"]}.FAILED.json').exists():
            continue
        lock = BASE / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc or not path.exists():
                write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln41 source unit failed')
            count += 1
        if count >= a.max_units:
            break


if __name__ == '__main__':
    main()
