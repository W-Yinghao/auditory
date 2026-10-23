"""DEP12 Federici as a third public cohort, env only (Agent M; DECISIONS M20, revises M13; follow-up, descriptive).

Partition and people come from the existing loader `auditory_alignment.data.load_federici` (people, groups, identities, person
folds by identity, content roles fit / es / test from the content-group split, single content fold 0, 5 s segments); the 9
phantom recordings (test_only) are excluded. EEG per recording: the loader's z-score (`_stdz` over the recording's blocks, guard
20 samples at 100 Hz), then each 50 s block resampled 100 -> 128 Hz (5000 -> 6400) with foundation_adapter.resample_fft in
float64; the loader's per-block z-scored envelope is resampled the same way. From there everything is the DTU / FAU definition
(dep12/panels.py): native crop eeg[q-52:q+76] -> 200 points, 4 x 32-anchor panels at 0.5 s hop (2 candidate positions per block),
block-shift null banks, guard 32 samples at 128 Hz, env descriptor [q, q+16) -> pairwise means -> 8 points.
20 s decision (no competing talker): candidate A = the block's own envelope (match), candidate B = the envelope at the same
positions of a test-role block with a different content group (mismatch; same recording if possible, else another recording;
seeded). Queries = 4 consecutive loader segments (role test) of one block, start ceil(1.28 x st0_100) at 128 Hz.
Files (0444): private/.../dep12/public/defs_v1/federici/{scan.json, defs.json}; descriptors_v1/federici.npz (+ meta).
CLI (Slurm only): python -m auditory_alignment_v3.dep12.federici {freeze, descriptors, status}
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

import numpy as np

from .. import core
from . import panels as PN

DS = 'federici'
FS100, FS = 100, 128
N100, N128 = 5000, 6400
SEG100 = 500
GUARD = 32
DEFS = PN.DEFS / DS
DESC = PN.OUT / 'descriptors_v1'
sha, write, read, digest = PN.sha, PN.write, PN.read, PN.digest


def sources():
    repo = Path(core.REPO)
    files = [Path(__file__), Path(PN.__file__), repo / 'auditory_alignment/data.py', repo / 'auditory_alignment/federici_content.py',
             repo / 'auditory_alignment_v2/foundation_adapter.py', repo / 'auditory_alignment_v2/train.py']
    return {str(p.relative_to(repo)): sha(p) for p in files}


def to128(x):
    """foundation_adapter.resample_fft on the last axis, float64 (5000 -> 6400 for a 50 s block)."""
    import torch
    from auditory_alignment_v2.foundation_adapter import resample_fft
    t = torch.as_tensor(np.asarray(x, np.float64))
    n = t.shape[-1]; n_out = int(round(n * FS / FS100)); assert n * FS % FS100 == 0
    X = torch.fft.rfft(t, dim=-1); m = min(X.shape[-1], n_out // 2 + 1)
    Y = torch.zeros(*X.shape[:-1], n_out // 2 + 1, dtype=X.dtype); Y[..., :m] = X[..., :m]
    y = torch.fft.irfft(Y, n=n_out, dim=-1) * (n_out / n)
    ref = resample_fft(t.float(), n_out).double()                    # the established function (float32 internally) as a check
    assert float((y - ref).abs().max()) < 1e-4 * max(1.0, float(y.abs().max())), 'resampler differs from foundation_adapter.resample_fft'
    return y.numpy()


def recording_eeg(path):
    """Loader-equivalent z-scored blocks at 100 Hz (float32, as load_federici) -> list of [32, 5000]."""
    import h5py
    from auditory_alignment import data as D
    with h5py.File(path, 'r') as f:
        E = f['eeg'][()].astype(np.float64); env = f['env'][()].astype(np.float64)
    xs = D._stdz([seg for seg in E], 20)
    ez = [((e - e.mean()) / (e.std() + 1e-12)).astype(np.float32) for e in env]
    return xs, ez


# ------------------------------------------------------------------------------------------------ scan / defs
def scan():
    from auditory_alignment import data as D
    from auditory_alignment_v2.train import train_participants
    coh = D.load_federici()
    parts = coh.participants
    files = {}
    import glob
    for grp in ('HC', 'CI', 'HC-v', 'Artifact'):
        for p in sorted(glob.glob(os.path.join(D.FED_PRE, grp, '*.h5'))):
            files[f'{grp}:{os.path.basename(p)[:-3]}'] = p
    raw = {}
    for s in coh.segments:
        p = parts[s['p']]
        if p.get('test_only'):
            continue
        raw.setdefault(p['id'], {}).setdefault(s['block'], []).append(s)
    blocks, e0_block = {}, {}
    for pid, bl in raw.items():
        for b, segs in bl.items():
            segs = sorted(segs, key=lambda x: x['e0'])
            base = segs[0]['e0'] - 20                                # loader segments start at st = 20 in every block
            sts = [int(x['e0'] - base) for x in segs]
            item = int(segs[0]['s0'] - sts[0])                       # stimulus bank offset of the block's envelope item
            assert sts[0] == 20 and all(x['role'] == segs[0]['role'] and x['part'] == segs[0]['part'] for x in segs)
            assert all(x['s0'] - st == item for x, st in zip(segs, sts))
            blocks.setdefault(pid, {})[b] = {'block': int(b), 'role': segs[0]['role'], 'group_c': segs[0]['part'], 'item': item, 'sts': sts}
            e0_block[(pid, b)] = int(base)
    # equality of the loader-equivalent EEG with load_federici on two recordings (100 Hz, before resampling)
    checks = {}
    for pid in sorted(blocks)[:2]:
        xs, _ = recording_eeg(files[pid])
        md = max(float(np.abs(coh.eeg[:, e0_block[(pid, b)]:e0_block[(pid, b)] + N100] - xs[b]).max()) for b in blocks[pid])
        checks[pid] = md
    assert all(v == 0.0 for v in checks.values()), checks
    people = [{'id': p['id'], 'group': p['group'], 'fold': p['fold'], 'identity': p['identity'], 'test_only': bool(p.get('test_only'))}
              for p in parts]

    class _Shim:
        participants = parts
    train = {sf: sorted(parts[i]['id'] for i in train_participants(_Shim, {}, sf)) for sf in PN.SFS}
    test = {sf: sorted(p['id'] for p in parts if p['fold'] == sf and not p.get('test_only')) for sf in PN.SFS}
    body = {'version': 'DEP12_PUB_FED_SCAN_v1', 'dataset': DS, 'people': people, 'files': {k: v for k, v in files.items() if k in blocks},
            'blocks': {pid: [bl[b] for b in sorted(bl)] for pid, bl in blocks.items()}, 'train': train, 'test': test,
            'loader_equality_max_abs': checks, 'sources': sources()}
    write(DEFS / 'scan.json', body)
    print(DS, 'recordings', len(blocks), 'blocks', sum(len(v) for v in blocks.values()),
          {sf: (len(train[sf]), len(test[sf])) for sf in PN.SFS}, flush=True)
    return body


def block_starts():
    hi = N128 - GUARD - (PN.BLOCK_SPAN + PN.WIN[0])
    hi = min(hi, N128 - ((PN.BLOCK_N - 1) * PN.PANEL_HOP + PN.TGT))
    out, b = [], GUARD - PN.WIN[0]
    while b <= hi:
        out.append(int(b)); b += PN.BLOCK_SPAN + PN.BLOCK_GAP
    return out


def freeze():
    path = DEFS / 'defs.json'
    if path.exists():
        print('frozen', path, sha(path)); return read(path)
    sc = read(DEFS / 'scan.json'); acf = read(PN.DEFS / 'acf_check.json'); min_shift = acf['decision']['min_shift_s']
    folds = {p['id']: p['fold'] for p in sc['people'] if not p['test_only']}
    cand = block_starts()
    panels = {}
    for pid in sorted(sc['blocks']):
        bl = sc['blocks'][pid]
        for kind, role in (('test', 'test'), ('calib', 'fit')):
            elig = [b for b in bl if b['role'] == role]
            rng = np.random.default_rng(PN.seed_of(PN.SEED, DS, pid, 0, kind))
            order = [elig[i] for i in rng.permutation(len(elig))]
            blocks, m = [], 0
            while len(blocks) < PN.PANEL_BLOCKS and m < len(cand) and order:
                for b in order:
                    if len(blocks) < PN.PANEL_BLOCKS:
                        blocks.append({'trial': b['block'], 'stim': b['item'], 'b': cand[m]})
                m += 1
            pn = {'person': pid, 'cf': 0, 'kind': kind, 'blocks': blocks, 'n': len(blocks) * PN.BLOCK_N,
                  'coverage': 'full' if len(blocks) == PN.PANEL_BLOCKS else f'short_{len(blocks)}_blocks', 'n_eligible_trials': len(elig),
                  'id': f'{DS}:{pid}:cf0:{kind}'}
            if kind == 'test':
                others = sorted(p for p in sc['blocks'] if p != pid)
                prng = np.random.default_rng(PN.seed_of(PN.SEED, DS, pid, 0, 'partner'))
                porder = [others[i] for i in prng.permutation(len(others))]
                parts_ = []
                for blk in blocks:
                    pick = None
                    for q in porder:
                        hit = [b for b in sc['blocks'][q] if b['item'] == blk['stim']]
                        if hit:
                            pick = {'person': q, 'trial': hit[0]['block']}; break
                    parts_.append(pick)
                pn['partners'] = parts_; pn['noise_seed'] = PN.seed_of(PN.SEED, DS, pid, 0, 'noise')
            panels[pn['id']] = pn
    # queries: runs of 4 consecutive test-role loader segments of one block; mismatch envelope from another content group
    from ..run_attention import _windows
    tests = {sf: set(sc['test'][str(sf)] if str(sf) in sc['test'] else sc['test'][sf]) for sf in PN.SFS}
    pool = [(p, b) for p, bl in sc['blocks'].items() for b in bl if b['role'] == 'test']
    queries = []
    for sf in PN.SFS:
        for pid in sorted(tests[sf]):
            for b in sc['blocks'][pid]:
                if b['role'] != 'test':
                    continue
                run = [[{'st': st} for st in sorted(b['sts'])]]
                assert all(y['st'] - x['st'] == SEG100 for x, y in zip(run[0], run[0][1:]))
                for w in _windows(run, PN.QUERY_SEGS):
                    st0 = int(math.ceil(w[0]['st'] * FS / FS100))
                    q = st0 + PN.QUERY_FIRST + PN.QUERY_HOP * np.arange(PN.QUERY_N)
                    assert q[0] + PN.WIN[0] >= GUARD and q[-1] + PN.WIN[1] <= N128 - GUARD
                    own = [x for x in sc['blocks'][pid] if x['role'] == 'test' and x['group_c'] != b['group_c']]
                    cands = [(pid, x['block'], x['item']) for x in own] or \
                            [(p2, x['block'], x['item']) for p2, x in pool if p2 != pid and x['group_c'] != b['group_c']]
                    rng = np.random.default_rng(PN.seed_of(PN.SEED, DS, pid, b['block'], st0, 'mismatch'))
                    mm = cands[int(rng.integers(len(cands)))]
                    queries.append({'person': pid, 'cf': 0, 'sf': sf, 'trial': b['block'], 'st0': st0, 'st0_100': w[0]['st'],
                                    'code': b['group_c'], 'item': b['item'], 'mismatch': {'person': mm[0], 'trial': mm[1], 'item': mm[2]},
                                    'mismatch_source': 'same_recording' if own else 'other_recording', 'status': 'ok'})
    sh = PN.legal_shifts(PN.BLOCK_N, PN.PANEL_HOP / FS, min_shift)
    banks = {'n128': PN.draw_bank(4, sh, PN.N_NULL, PN.seed_of(PN.SEED, 'bank', 4)).tolist(),
             'n64': PN.draw_bank(2, sh, PN.N_NULL, PN.seed_of(PN.SEED, 'bank', 2)).tolist(),
             'n32': PN.draw_bank(1, sh, PN.N_NULL, PN.seed_of(PN.SEED, 'bank', 1)).tolist()}
    att_shifts = PN.legal_shifts(PN.QUERY_N, PN.QUERY_HOP / FS, min_shift)
    body = {'version': 'DEP12_PUB_DEFS_FED_v1', 'dataset': DS, 'scan_sha256': sha(DEFS / 'scan.json'), 'acf_sha256': sha(PN.DEFS / 'acf_check.json'),
            'min_shift_s': min_shift, 'geometry': {'fs': FS, 'fs_source': FS100, 'resampler': 'foundation_adapter.resample_fft per 50 s block (float64)',
                                                   'window': list(PN.WIN), 'window_ms': list(PN.SUPPORT_MS), 'target': PN.TGT, 'descriptor_points': PN.TGT // 2,
                                                   'guard': GUARD, 'block_n': PN.BLOCK_N, 'panel_blocks': PN.PANEL_BLOCKS, 'panel_hop': PN.PANEL_HOP,
                                                   'block_gap': PN.BLOCK_GAP, 'query_len': PN.QUERY_LEN, 'query_first': PN.QUERY_FIRST,
                                                   'query_hop': PN.QUERY_HOP, 'query_n': PN.QUERY_N},
            'folds': folds, 'panels': panels, 'block_shifts_legal': sh, 'null_banks': banks,
            'null_design': {'n128': f'blockwise_circular_shift_4x32_hop0.5s_min{min_shift:g}s_{len(banks["n128"])}draws',
                            'n64': f'blockwise_circular_shift_2x32_hop0.5s_min{min_shift:g}s_{len(banks["n64"])}draws',
                            'n32': f'blockwise_circular_shift_1x32_hop0.5s_min{min_shift:g}s_{len(banks["n32"])}draws',
                            'attention': f'query_circular_shift_152_hop0.125s_min{min_shift:g}s_{len(att_shifts)}shifts'},
            'attention_shifts': att_shifts, 'queries': queries,
            'decision': 'match (own block envelope) vs mismatch (different content group, same positions); not attention selection',
            'train': sc['train'], 'test': sc['test'], 'sources': sources()}
    body['panels_sha256'] = digest(panels); body['queries_sha256'] = digest(queries); body['banks_sha256'] = digest(banks)
    write(path, body); path.chmod(0o444)
    cov = {}
    for pn in panels.values():
        cov[(pn['kind'], pn['coverage'])] = cov.get((pn['kind'], pn['coverage']), 0) + 1
    print(DS, 'frozen', sha(path), {f'{k}/{c}': v for (k, c), v in cov.items()}, 'partners',
          sum(x is not None for pn in panels.values() if pn['kind'] == 'test' for x in pn['partners']), 'queries', len(queries),
          'mismatch other_recording', sum(q['mismatch_source'] == 'other_recording' for q in queries), flush=True)
    return body


def defs():
    path = DEFS / 'defs.json'
    assert path.exists() and not os.access(path, os.W_OK), f'{path} must be frozen (0444)'
    return read(path)


def unit_people(sf):
    d = defs()
    return sorted(d['train'][str(sf)]), sorted(d['test'][str(sf)])


# ------------------------------------------------------------------------------------------------ descriptors
def _take(e128, q):
    idx = np.asarray(q)[:, None] + np.arange(PN.TGT)[None]
    assert idx.min() >= 0 and idx.max() < e128.shape[-1]
    w = 0.5 * (e128[idx][..., 0::2] + e128[idx][..., 1::2])
    return w.reshape(len(q), -1)


def descriptors():
    path = DESC / f'{DS}.npz'
    if path.exists():
        return path
    d = defs(); sc = read(DEFS / 'scan.json'); cache = {}

    def env(pid):
        if pid not in cache:
            _, ez = recording_eeg(sc['files'][pid]); cache[pid] = [to128(e) for e in ez]
        return cache[pid]
    ids = sorted(d['panels']); E, A, B = [], [], []
    for pid in ids:
        pn = d['panels'][pid]
        e = np.full((128, PN.TGT // 2), np.nan)                       # short panels (< 4 blocks): rows beyond n stay NaN, never read
        e[:pn['n']] = np.concatenate([_take(env(pn['person'])[blk['trial']], PN.anchors_of(blk)) for blk in pn['blocks']])
        E.append(e)
    for qd in d['queries']:
        q = qd['st0'] + PN.QUERY_FIRST + PN.QUERY_HOP * np.arange(PN.QUERY_N)
        A.append(_take(env(qd['person'])[qd['trial']], q)); B.append(_take(env(qd['mismatch']['person'])[qd['mismatch']['trial']], q))
    arrays = {'panel_ids': np.array(ids), 'env': np.stack(E), 'q_att': np.stack(A), 'q_ign': np.stack(B)}
    for k in ('q_att', 'q_ign'):
        assert np.isfinite(arrays[k]).all(), k
    assert all(np.isfinite(arrays['env'][i, :d['panels'][pid]['n']]).all() for i, pid in enumerate(ids))
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez(path, **arrays); path.chmod(0o444)
    write(DESC / f'{DS}.meta.json', {'version': 'DEP12_PUB_DESC_FED_v1', 'dataset': DS, 'defs_sha256': sha(DEFS / 'defs.json'), 'sha256': sha(path),
                                      'shapes': {k: list(v.shape) for k, v in arrays.items()}, 'sources': sources(),
                                      'definition': ('loader per-block z-scored envelope resampled 100 -> 128 Hz (resample_fft); support [q, q+16) '
                                                     '-> pairwise means -> 8 points; q_att = own block (match), q_ign = mismatch block')})
    print(DS, 'descriptors', sha(path), {k: v.shape for k, v in arrays.items()}, flush=True)
    return path


# ------------------------------------------------------------------------------------------------ loader for the feature exporter
class FedCohort:
    """Same interface as public_features.Cohort: parts, channels, train / test per sf, load(pid) -> {block: x128 [32, 6400]}."""

    def __init__(self):
        from auditory_alignment_v2.foundation_adapter import ALIASES, CHANNELS
        sc = read(DEFS / 'scan.json'); self.sc = sc
        self.parts = {p['id']: p for p in sc['people'] if not p['test_only']}
        self.channels = [ALIASES.get(c, c) for c in CHANNELS[DS]]
        self.train = {sf: set(sc['train'][str(sf)]) for sf in PN.SFS}
        self.test = {sf: set(sc['test'][str(sf)]) for sf in PN.SFS}

    def load(self, pid):
        import h5py
        from auditory_alignment_v2.foundation_adapter import ALIASES
        path = self.sc['files'][pid]
        with h5py.File(path, 'r') as f:
            raw = f.attrs['channels']
        names = raw.strip('[]').replace("'", '').split() if isinstance(raw, str) else [c.decode() if isinstance(c, bytes) else str(c) for c in raw]
        ch = [ALIASES.get(c.strip(), c.strip()) for c in names]
        assert ch == self.channels, f'{pid}: channel order differs from the registered federici montage'
        xs, _ = recording_eeg(path)
        return {b: to128(x).astype(np.float32) for b, x in enumerate(xs)}

    def close(self):
        pass


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=('freeze', 'descriptors', 'status'))
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.step == 'freeze':
        if not (DEFS / 'scan.json').exists():
            scan()
        freeze()
    elif a.step == 'descriptors':
        descriptors()
    else:
        print((DEFS / 'defs.json').exists() and sha(DEFS / 'defs.json'))


if __name__ == '__main__':
    main()
