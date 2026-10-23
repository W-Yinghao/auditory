"""DEP12 source sampler (package v1.2, 03 §1-§2): within-listener episodes on SparrKULee fit, the exact CBAUD window.

Pool: aln41.source.pool (prior33 core+rich manifests, hash-checked; fit = cb_auditory.eligible fit rows minus the
downstream-overlap presentations; dev = manifest pools.dev; fit/dev people AND content families disjoint, asserted there);
every segment must have all three rich views (env/ss/sc). Nothing is re-split from snapshot counts.

Anchor = (segment row, tick offset q) with q in prior33 TICK_OFFS, q >= 26. EEG = the exact CBAUD 64 Hz window
q+[-26:38] = before[..., :26] ++ after (two DonorBank 38-sample gathers, as aln34.cb_auditory.Stream.draw), 64 native samples,
then crop-only resampling to 200 points with aln41.timebank.resample (scipy-equivalent). Audio = env (8 samples, 125 ms),
ss (8 x 4 source-fit PCA), sc (8 frame-change norms) at [q, q+8) through the fixed prior33 heads (32-d, L2).

Full-window guard (per anchor, asserted): the whole 64-sample window lies in [g0, T_eeg - g1) of its piece (SparrKULee
guards 128/128 samples, which also contain the +-64-sample 1-20 Hz zero-phase filter support on both sides) and inside the
loaded segment span [s, s + 357); the target window lies inside the stream minus ENV_EDGE. This checks the full 1 s window,
not only the old 38-sample gather.

Legal pairs (checked before any objective sees a Gram): two anchors of one episode may not share a family when either side
has no usable family clock (unknown-clock family, or a known-clock family whose presentation offset is unknown), and anchors
of a known-clock family must be > SEP = 128 samples apart on the family clock (>= max(2 s, 64-sample window support);
matches the existing prior33 NEIGHBOR exclusion |ds| <= 128). Repeated presentations of the same content collide on the
family clock and are excluded by the same rule.

Stream (one per training seed, shared by every arm and mode of that seed): per update two distinct fit listeners
(uniform), per listener n legal anchors (n from the frozen coverage check), four derangements shared by the three views
(training mismatches, redrawn every update) and one independent "wrong" derangement w for cs_pair_wrong with w != P_b and
w o P_b fixed-point free for every b. Everything is pre-generated from numpy PCG64(seed + STREAM_OFFSET), saved and hashed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from . import encoders as ENC

WIN_LO, WIN_HI = -26, 38
N_NATIVE = WIN_HI - WIN_LO               # 64
SEP = 128                                # legal iff |dt| > 128 family-clock samples (2 s)
N_ANCHORS, FALLBACK = 64, 32
PEOPLE_PER_UPDATE, N_PERM = 2, 4
STREAM_OFFSET = 120000                   # stream RNG = PCG64(seed + 120000)
PANEL_SEEDS = {'fit': 3460, 'dev': 3461, 'diag': 3462, 'coverage': 3463}
DEV_PANEL_N = 128
DIAG_NULL = 16
STEPS = 10000
VIEWS = ('env', 'ss', 'sc')
OUT = ENC.SOURCE_OUT
STORE = ENC.SOURCE_STORE
COVERAGE = OUT / 'COVERAGE_64v32.json'
PANELS = STORE / 'panels.npz'
PANELS_RECEIPT = OUT / 'panels.json'


def stream_path(seed):
    return STORE / f'stream_s{seed}.npz'


def stream_receipt(seed):
    return OUT / f'stream_s{seed}.json'


sha, read = ENC.sha, ENC.read


def dumps(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)


def write(path, value, freeze=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() and freeze:
        raise FileExistsError(f'{path} is frozen')
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=1, sort_keys=True, allow_nan=False, default=str) + '\n')
    os.replace(tmp, path)
    if freeze:
        path.chmod(0o444)
    return path


def now():
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------------------------------- pool and anchor identity
class Pool:
    """Fit/dev segments per listener with everything needed for guards and legality (CPU, no EEG)."""

    def __init__(self):
        from ..aln41 import source as A41
        from ..prior33 import views as V, contract as PC, losses as L
        self.man = A41.open_manifest()
        self.split, self.info = A41.pool(self.man)
        self.idx = V.manifest_index(self.man)
        self.seg = self.idx.seg['sparrkulee']
        _, items = V.cohort_table(self.man, 'sparrkulee')
        self.T_eeg = np.array([int(it['T_eeg']) for it in items], dtype=np.int64)
        streams = V.cohort_streams(self.man, 'sparrkulee')
        self.stream_len = np.array([int(r['length']) for r in streams], dtype=np.int64)
        self.guards = tuple(int(g) for g in self.man['cohorts']['sparrkulee'].get('guards', PC.GUARDS['sparrkulee']))
        assert self.guards == PC.GUARDS['sparrkulee']
        self.offsets = PC.TICK_OFFS[(PC.TICK_OFFS >= -WIN_LO) & (PC.TICK_OFFS + WIN_HI <= PC.SPAN_EEG)].astype(np.int64)
        self.span = int(PC.SPAN_EEG); self.edge = int(PC.ENV_EDGE); self.n_tgt = int(PC.N_TGT)
        unknown = set(L.unknown_clock_families(self.man))
        fam = self.seg['family']; pres = self.seg['presentation']
        self.exclusive_seg = np.array([int(f) in unknown for f in fam], dtype=bool) | (self.idx.famoff[pres] < 0)
        self.people = {k: sorted(v) for k, v in self.split.items()}
        self.rows = {k: {p: np.array(sorted(r for f in fs.values() for r in f), dtype=np.int64) for p, fs in v.items()}
                     for k, v in self.split.items()}
        self.manifest_sha = A41.MANIFEST_SHA; self.rich_sha = A41.RICH_SHA

    # anchor identity ----------------------------------------------------------------------------------------------
    def clock(self, rows, off):
        """Family-clock sample of each anchor (int64; -1 where the family/presentation has no usable clock)."""
        rows = np.asarray(rows, np.int64); off = np.asarray(off, np.int64)
        pres = self.seg['presentation'][rows]
        t = self.idx.famoff[pres] + self.seg['s'][rows] + off
        return np.where(self.exclusive_seg[rows], -1, t)

    def legal_matrix(self, rows, off):
        """[n, n] bool: True where the off-diagonal pair is a legal negative."""
        rows = np.asarray(rows, np.int64)
        fam = self.seg['family'][rows]; t = self.clock(rows, off); ex = self.exclusive_seg[rows]
        same = fam[:, None] == fam[None, :]
        near = np.abs(t[:, None] - t[None, :]) <= SEP
        bad = same & (ex[:, None] | ex[None, :] | near)
        np.fill_diagonal(bad, False)
        return ~bad

    def guard(self, rows, off):
        """Full-window guard; returns the checked intervals (raises on any violation)."""
        rows = np.asarray(rows, np.int64); off = np.asarray(off, np.int64)
        s = self.seg['s'][rows]; piece = self.seg['piece'][rows]; pres = self.seg['presentation'][rows]
        a, b = s + off + WIN_LO, s + off + WIN_HI
        g0, g1 = self.guards
        assert np.all(off + WIN_LO >= 0) and np.all(off + WIN_HI <= self.span), 'window leaves the loaded segment span'
        assert np.all(a >= g0) and np.all(b <= self.T_eeg[piece] - g1), 'window leaves the piece guards'
        assert np.all(a - 64 >= 0) and np.all(b + 64 <= self.T_eeg[piece]), 'filter support leaves the piece'
        st = self.idx.stream[pres]
        assert np.all(st >= 0)
        assert np.all(s + off >= self.edge) and np.all(s + off + self.n_tgt <= self.stream_len[st] - self.edge), 'target edge'
        return {'n': int(len(rows)), 'eeg_window_64hz': [WIN_LO, WIN_HI], 'guards': list(self.guards),
                'min_margin_start': int((a - g0).min()) if len(a) else None,
                'min_margin_end': int((self.T_eeg[piece] - g1 - b).min()) if len(b) else None}

    # episode drawing -------------------------------------------------------------------------------------------------
    def draw_episode(self, rng, person, n, split='fit'):
        """n legal anchors of one listener: random segment order, uniform tick offset per segment, accept if legal."""
        segs = self.rows[split][person]
        order = rng.permutation(len(segs))
        R, O = np.empty(n, np.int64), np.empty(n, np.int64)
        fam_acc, t_acc, ex_acc = np.empty(n, np.int64), np.empty(n, np.int64), np.empty(n, bool)
        k = 0
        for i in order:
            r = int(segs[i]); o = int(self.offsets[rng.integers(len(self.offsets))])
            f = int(self.seg['family'][r]); ex = bool(self.exclusive_seg[r]); t = int(self.clock([r], [o])[0])
            if k:
                same = fam_acc[:k] == f
                if np.any(same & (ex | ex_acc[:k] | (np.abs(t_acc[:k] - t) <= SEP))):
                    continue
            R[k], O[k], fam_acc[k], t_acc[k], ex_acc[k] = r, o, f, t, ex
            k += 1
            if k == n:
                return R, O
        raise RuntimeError(f'listener {person}: only {k} legal anchors could be drawn (n={n})')

    def greedy_capacity(self, person, split='fit'):
        """Deterministic lower bound on the largest legal set: segments in row order, middle tick offset, greedy accept."""
        segs = self.rows[split][person]
        mid = int(self.offsets[len(self.offsets) // 2])
        fam = self.seg['family'][segs]; ex = self.exclusive_seg[segs]; t = self.clock(segs, np.full(len(segs), mid))
        used_ex, acc = set(), {}
        k = 0
        for f, e, tt in zip(fam.tolist(), ex.tolist(), t.tolist()):
            if f in used_ex:
                continue
            prev = acc.get(f)
            if e:
                if prev:
                    continue
                used_ex.add(f); acc.setdefault(f, []).append(tt); k += 1; continue
            if prev is not None and any(abs(tt - x) <= SEP for x in prev):
                continue
            acc.setdefault(f, []).append(tt); k += 1
        return k


def derangement(rng, n):
    while True:
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p


def wrong_map(rng, perms):
    """Independent derangement w with w != P_b and w o P_b (EEG i <-> audio w[P_b[i]]) fixed-point free for every b."""
    n = perms.shape[1]; ar = np.arange(n)
    for _ in range(10000):
        w = derangement(rng, n)
        if any(np.array_equal(w, p) for p in perms):
            continue
        if any(np.any(w[p] == ar) for p in perms):
            continue
        return w
    raise RuntimeError('no admissible wrong map')


# ----------------------------------------------------------------------------------------------- coverage (frozen first)
def coverage(pool=None, attempts=8):
    """64-vs-32 rule over ALL fit listeners, frozen 0444 before any dev result exists."""
    if COVERAGE.exists():
        return read(COVERAGE)
    runs = OUT / 'runs'
    dev_results = sorted(str(p) for p in runs.glob('*/devprobe_*.json')) if runs.exists() else []
    assert not dev_results, f'dev results already exist: {dev_results[:3]}'
    pool = pool or Pool()
    rng = np.random.default_rng(PANEL_SEEDS['coverage'])
    per = {}
    for p in pool.people['fit']:
        cap = pool.greedy_capacity(p)
        ok64 = ok32 = 0
        for _ in range(attempts):
            try:
                pool.draw_episode(rng, p, N_ANCHORS); ok64 += 1
            except RuntimeError:
                pass
            try:
                pool.draw_episode(rng, p, FALLBACK); ok32 += 1
            except RuntimeError:
                pass
        per[p] = {'segments': int(len(pool.rows['fit'][p])), 'families': len(pool.split['fit'][p]),
                  'greedy_legal_capacity': int(cap), 'random_draws_64_ok': ok64, 'random_draws_32_ok': ok32,
                  'attempts': attempts}
    below64 = sorted(p for p, v in per.items() if v['greedy_legal_capacity'] < N_ANCHORS)
    below32 = sorted(p for p, v in per.items() if v['greedy_legal_capacity'] < FALLBACK)
    n = N_ANCHORS if not below64 else FALLBACK
    body = {'version': 'DEP12_SOURCE_COVERAGE_v1', 'created_utc': now(), 'rule': ('03 §2.4: every fit listener can form '
            '64 legal rows -> n=64 for all arms, else n=32 for all arms; listeners below 32 are listed, never dropped silently'),
            'anchors_per_person': n, 'fit_listeners': len(per), 'listeners_below_64': below64, 'listeners_below_32': below32,
            'min_greedy_capacity': int(min(v['greedy_legal_capacity'] for v in per.values())),
            'per_listener': per, 'sep_family_clock_samples': SEP, 'eeg_window_64hz': [WIN_LO, WIN_HI],
            'pool_info': pool.info, 'manifest_sha256': pool.manifest_sha, 'rich_sha256': pool.rich_sha,
            'dev_results_existing_at_freeze': dev_results, 'source_sampler_sha256': sha(__file__),
            'note': 'capacity = deterministic greedy lower bound (row order, middle tick); random draws use the production sampler'}
    write(COVERAGE, body, freeze=True)
    return body


def anchors_per_person():
    c = read(COVERAGE)
    assert c['anchors_per_person'] in (N_ANCHORS, FALLBACK)
    return int(c['anchors_per_person'])


# ----------------------------------------------------------------------------------------------- panels and streams
def make_panels(pool=None):
    """Fixed source panels: fit (n legal anchors per fit listener; CS calibration + dev-probe fit), dev (128 per dev
    listener; dev-probe readout), diagnostic nulls (16 derangements per fit / dev episode)."""
    if PANELS.exists():
        rec = read(PANELS_RECEIPT); assert sha(PANELS) == rec['sha256']
        return rec
    pool = pool or Pool(); n = anchors_per_person()
    out, meta = {}, {}
    for split, per, seed in (('fit', n, PANEL_SEEDS['fit']), ('dev', DEV_PANEL_N, PANEL_SEEDS['dev'])):
        rng = np.random.default_rng(seed); R, O, W = [], [], []
        for i, p in enumerate(pool.people[split]):
            r, o = pool.draw_episode(rng, p, per, split)
            assert pool.legal_matrix(r, o)[~np.eye(per, dtype=bool)].all()
            pool.guard(r, o); R.append(r); O.append(o); W.append(np.full(per, i))
        out[f'{split}_rows'] = np.concatenate(R); out[f'{split}_off'] = np.concatenate(O); out[f'{split}_who'] = np.concatenate(W)
        meta[split] = {'people': pool.people[split], 'per_person': per, 'n': int(len(out[f'{split}_rows'])), 'seed': seed}
    rng = np.random.default_rng(PANEL_SEEDS['diag'])
    for split, per in (('fit', n), ('dev', min(n, DEV_PANEL_N))):
        k = len(pool.people[split])
        out[f'{split}_diag_null'] = np.stack([np.stack([derangement(rng, per) for _ in range(DIAG_NULL)]) for _ in range(k)]).astype(np.int16)
    STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = STORE / 'panels.tmp.npz'
    np.savez_compressed(tmp, **out); os.replace(tmp, PANELS)
    rec = {'version': 'DEP12_SOURCE_PANELS_v1', 'path': str(PANELS), 'sha256': sha(PANELS), 'created_utc': now(), 'meta': meta,
           'diag_null_per_episode': DIAG_NULL, 'diag_seed': PANEL_SEEDS['diag'], 'coverage_sha256': sha(COVERAGE),
           'dev_people_disjoint_from_fit': not (set(pool.people['fit']) & set(pool.people['dev'])),
           'source_sampler_sha256': sha(__file__)}
    write(PANELS_RECEIPT, rec, freeze=True)
    return rec


def make_stream(seed, pool=None, steps=STEPS):
    """Pre-generated schedule shared by every arm/mode of `seed`; hashed; RNG identity recorded."""
    path = stream_path(seed)
    if path.exists():
        rec = read(stream_receipt(seed)); assert sha(path) == rec['sha256']
        return rec
    pool = pool or Pool(); n = anchors_per_person(); people = pool.people['fit']
    rng = np.random.default_rng(seed + STREAM_OFFSET)
    who = np.zeros((steps, PEOPLE_PER_UPDATE), np.int16)
    rows = np.zeros((steps, PEOPLE_PER_UPDATE, n), np.int32); off = np.zeros((steps, PEOPLE_PER_UPDATE, n), np.int16)
    perm = np.zeros((steps, PEOPLE_PER_UPDATE, N_PERM, n), np.int16); wrong = np.zeros((steps, PEOPLE_PER_UPDATE, n), np.int16)
    dup = 0
    for u in range(steps):
        pair = rng.choice(len(people), size=PEOPLE_PER_UPDATE, replace=False); who[u] = pair
        for j, pi in enumerate(pair):
            r, o = pool.draw_episode(rng, people[pi], n)
            P = np.stack([derangement(rng, n) for _ in range(N_PERM)])
            dup += N_PERM - len(np.unique(P, axis=0))
            rows[u, j], off[u, j], perm[u, j] = r, o, P
            wrong[u, j] = wrong_map(rng, P)
    final_state = rng.bit_generator.state
    STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = STORE / f'stream_s{seed}.tmp.npz'
    np.savez_compressed(tmp, who=who, rows=rows, off=off, perm=perm, wrong=wrong, people=np.array(people))
    os.replace(tmp, path)
    check = check_stream(seed, pool)
    rec = {'version': 'DEP12_SOURCE_STREAM_v1', 'seed': seed, 'rng': {'bit_generator': 'PCG64', 'seed': seed + STREAM_OFFSET,
           'final_state_sha256': hashlib.sha256(dumps(final_state).encode()).hexdigest()}, 'steps': steps,
           'anchors_per_person': n, 'people_per_update': PEOPLE_PER_UPDATE, 'n_perm': N_PERM,
           'duplicate_training_mismatches': int(dup), 'path': str(path), 'sha256': sha(path),
           'component_sha256': {k: hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()
                                for k, v in (('rows', rows), ('off', off), ('perm', perm), ('wrong', wrong), ('who', who))},
           'check': check, 'coverage_sha256': sha(COVERAGE), 'source_sampler_sha256': sha(__file__), 'created_utc': now()}
    write(stream_receipt(seed), rec, freeze=True)
    return rec


def load_stream(seed):
    rec = read(stream_receipt(seed)); assert sha(stream_path(seed)) == rec['sha256'], 'stream hash drift'
    with np.load(stream_path(seed), allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def load_panels():
    rec = read(PANELS_RECEIPT); assert sha(PANELS) == rec['sha256'], 'panel hash drift'
    with np.load(PANELS, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}, rec


def check_stream(seed, pool=None, sample=None):
    """Within-listener, all off-diagonal pairs legal, guards, derangements, wrong-map admissibility, distinct listeners."""
    pool = pool or Pool()
    with np.load(stream_path(seed), allow_pickle=False) as z:
        S = {k: z[k] for k in z.files}
    people = [str(p) for p in S['people']]
    assert people == pool.people['fit']
    U, J, n = S['rows'].shape
    ar = np.arange(n); off_diag = ~np.eye(n, dtype=bool)
    idx = range(U) if sample is None else sample
    for u in idx:
        assert len(set(S['who'][u].tolist())) == J
        for j in range(J):
            r, o = S['rows'][u, j].astype(np.int64), S['off'][u, j].astype(np.int64)
            assert len(set(r.tolist())) == n
            assert set(str(x) for x in pool.seg['participant'][r]) == {people[S['who'][u, j]]}, 'episode mixes listeners'
            assert pool.legal_matrix(r, o)[off_diag].all(), f'illegal pair at update {u}'
            P = S['perm'][u, j].astype(np.int64); w = S['wrong'][u, j].astype(np.int64)
            assert np.all(np.sort(P, 1) == ar) and not np.any(P == ar), 'training mismatch not a derangement'
            assert sorted(w.tolist()) == ar.tolist() and not np.any(w == ar)
            assert not any(np.array_equal(w, p) for p in P) and not any(np.any(w[p] == ar) for p in P)
    allr = S['rows'].reshape(-1).astype(np.int64); allo = S['off'].reshape(-1).astype(np.int64)
    g = pool.guard(allr, allo) if sample is None else pool.guard(allr[:4096], allo[:4096])
    return {'status': 'pass', 'updates_checked': U if sample is None else len(list(sample)), 'guard': g,
            'unique_segments': int(len(np.unique(allr)))}


# ----------------------------------------------------------------------------------------------- data on the device
class SourceData:
    """DonorBank (segments mode) for the given rows; exact CBAUD crops -> 200 points; fixed audio heads (32-d, L2)."""

    def __init__(self, pool, segment_rows, device):
        from ..prior33 import views as V, model as M, contract as PC
        self.pool, self.seg, self.device = pool, pool.seg, device
        self.bank = V.DonorBank(pool.man, 'sparrkulee', ('fit', 'dev'), device=device, rich=True,
                                segments=np.unique(np.asarray(segment_rows, np.int64)))
        assert self.bank.layout == PC.BIOSEMI64
        self.heads = {k: h.to(device).requires_grad_(False).eval() for k, h in M.fixed_heads(pool.man, pool.man.root).items()}
        assert set(self.heads) == set(VIEWS)
        self.channel_names = list(PC.BIOSEMI64)

    def native(self, rows, off):
        """[n, 64 ch, 64] float32 native window q+[-26:38]."""
        import torch
        rows = np.asarray(rows, np.int64); off = np.asarray(off, np.int64)
        piece, start = self.seg['piece'][rows], self.seg['s'][rows]
        before = self.bank.gather(piece, start, off + WIN_LO)
        after = self.bank.gather(piece, start, off)
        x = torch.cat([before[..., :-WIN_LO], after], dim=-1).float()
        assert x.shape[-1] == N_NATIVE and bool(torch.isfinite(x).all())
        return x

    def eeg(self, rows, off):
        """[n, 64, 200] container (crop-only scipy-equivalent resampling; no padding)."""
        from ..aln41 import timebank as TB
        return TB.resample(self.native(rows, off), 200).float()

    def audio(self, rows, off):
        import torch
        rows = np.asarray(rows, np.int64); off = np.asarray(off, np.int64)
        pres, start = self.seg['presentation'][rows], self.seg['s'][rows]
        env = self.bank.targets(pres, start, off); ss, sc, ok = self.bank.rich_targets(pres, start, off)
        assert bool(ok.all()), 'a rich view is missing for a sampled anchor'
        raw = {'env': env, 'ss': ss, 'sc': sc}
        with torch.no_grad():
            return {k: self.heads[k](v).float() for k, v in raw.items()}, raw


# ----------------------------------------------------------------------------------------------- CLI (Slurm CPU)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['coverage', 'panels', 'streams', 'check', 'all'])
    ap.add_argument('--seeds', default='3401,3407,3413')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm only'
    os.umask(0o077)
    pool = Pool()
    if a.step in ('coverage', 'all'):
        c = coverage(pool)
        print('coverage n =', c['anchors_per_person'], 'fit listeners', c['fit_listeners'], 'min capacity', c['min_greedy_capacity'],
              'below64', c['listeners_below_64'], 'below32', c['listeners_below_32'], flush=True)
    if a.step in ('panels', 'all'):
        print('panels', json.dumps(make_panels(pool)['meta'], default=str)[:400], flush=True)
    if a.step in ('streams', 'all'):
        for s in [int(x) for x in a.seeds.split(',')]:
            r = make_stream(s, pool)
            print('stream', s, r['sha256'], r['check']['status'], r['check']['unique_segments'], flush=True)
    if a.step == 'check':
        for s in [int(x) for x in a.seeds.split(',')]:
            print('check', s, json.dumps(check_stream(s, pool))[:300], flush=True)


if __name__ == '__main__':
    main()
