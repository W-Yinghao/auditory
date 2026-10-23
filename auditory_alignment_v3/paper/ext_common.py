"""Paper line (manuscript v2, Table 2): the common two-candidate attention protocol shared by every external decoder.

Common partition = the ALN4.1 public units: dataset in {dtu, fau} x content fold cf in {0, 1} x pooled person fold sf in 0..4.
Query segments = exactly the competing-speaker ('cs') list of aln41/frozen.py public_unit (5 s, roles fit / es / test), whose
person / code / e0 / role arrays are asserted equal to the frozen B0 unit of (dataset, cf).  Train people of sf =
auditory_alignment_v2.train.train_participants (asserted == frozen meta pca[sf].train_people); test people = ss-anchor people
with fold == sf and not dev (as aln41.readout.public).  Decision integration = aln42.external_eval.integrate (= aln41.readout
.attention with a precomputed segment margin): mean evidence over 5 / 10 / 20 s runs, tau fitted by double-order log loss on
the train people's fit + es windows, both candidate orders, ties 0.5.  Hearing groups = cohort participant 'group'.

Input cache (CPU, built once per dataset; EEG-derived, private store 0700): a lean replica of auditory_alignment.data.load_dtu /
load_fau that keeps only the cs segments (the cohort loaders hold the full ss+cs bank, ~5 GB).  It imports the loaders' own
helpers (_stdz, _folds, _segments_of, fau_panel, FAU_CF, paths) and reproduces their loop; equality is asserted for every cs
segment against the frozen B0 units of both content folds (person, code, e0, role, and the 1-8 Hz envelope at the 16
frozen anchors of both streams), and EEG equality against the original loader on a two-person subset (verify_eeg).
Per segment: EEG block = cohort EEG [e0, e0 + 704) at 128 Hz (5 s + 0.5 s of later EEG of the same trial; every cs segment
ends >= 85 samples before its trial end) -> pairwise mean -> [C, 352] at 64 Hz; attended / ignored envelope = the common
target (kcs Local row 5: broadband envelope, 1-8 Hz, 128 Hz) over the 5 s segment -> pairwise mean -> [320] at 64 Hz.
"""
from __future__ import annotations

import glob
import json
import math
import os
from pathlib import Path

import numpy as np

from .. import core
from ..aln41 import source as SRC

OUT = Path(core.OUT) / 'paper' / 'external_decoders'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/external_decoders')
RESULTS = Path(core.REPO) / 'results' / 'auditory_alignment_v3' / 'paper' / 'external_decoders'
INPUT = STORE / 'input_v1'
DATASETS, CFS, SFS = ('dtu', 'fau'), (0, 1), (0, 1, 2, 3, 4)
FS_IN, FS = 128, 64
SEG128, LAG128 = 640, 64                    # 5 s segment, 0.5 s of later EEG (backward-model lags 0..500 ms)
BLOCK128 = SEG128 + LAG128
SEG64, BLOCK64 = SEG128 // 2, BLOCK128 // 2
GROUPS = {'dtu': ('nh', 'hi'), 'fau': ('th', 'ha', 'ci')}
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest


def pairmean(x):
    x = np.asarray(x)
    assert x.shape[-1] % 2 == 0
    return 0.5 * (x[..., 0::2] + x[..., 1::2])


def rowcorr(a, b):
    """Pearson r along the last axis (a, b broadcastable)."""
    a = a - a.mean(-1, keepdims=True); b = b - b.mean(-1, keepdims=True)
    return (a * b).sum(-1) / np.sqrt(np.maximum((a * a).sum(-1) * (b * b).sum(-1), 1e-24))


def sources():
    repo = Path(core.REPO)
    files = [Path(__file__), repo / 'auditory_alignment/data.py', repo / 'auditory_alignment_v2/train.py',
             repo / 'auditory_alignment_v3/aln41/frozen.py', repo / 'auditory_alignment_v3/aln41/readout.py',
             repo / 'auditory_alignment_v3/aln42/external_eval.py', repo / 'auditory_alignment_v3/run_attention.py',
             repo / 'auditory_alignment_v3/aln34/attention_order.py']
    return {str(p.relative_to(repo)): sha(p) for p in files}


# ------------------------------------------------------------------------------------------------ frozen reference
def frozen_b0(ds):
    from ..aln41 import frozen as FZ
    plan = read(FZ.BASE / 'plan.json'); out = {}
    for cf in CFS:
        row = next(r for r in plan['rows'] if r['arm'] == 'B0' and r['dataset'] == ds and r['content_fold'] == cf)
        rec = read(FZ.BASE / 'units' / f'{row["id"]}.json'); assert rec['status'] == 'complete'
        out[str(cf)] = {'unit': row['id'], 'dest': rec['dest'], 'array_sha256': rec['array_sha256'], 'meta_sha256': rec['meta_sha256']}
    return out


def frozen_arrays(ds, cf, keys=('cs_person', 'cs_code', 'cs_e0', 'cs_role', 'cs_env_att', 'cs_env_ign', 'cs_offsets', 'person')):
    ref = frozen_b0(ds)[str(cf)]; dest = Path(ref['dest'])
    with np.load(dest / 'arrays.npz', allow_pickle=False) as z:
        A = {k: z[k] for k in keys}
    return A, read(dest / 'meta.json')


# ------------------------------------------------------------------------------------------------ lean cohort replica
class _Shim:
    def __init__(self, parts):
        self.participants = parts


def _people(ds):
    from auditory_alignment import data as D
    if ds == 'fau':
        dev, panel = D.fau_panel()
        return [{'id': s, 'group': 'th', 'fold': -1, 'dev': True} for s in dev] + \
               [{'id': s, 'group': g, 'fold': f, 'dev': False} for s, (g, f) in sorted(panel.items())]
    import pandas as pd
    part = pd.read_csv(f'{D.PUB}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv', sep='\t')
    hs = dict(zip(part.participant_id, part.hearing_status)); age = dict(zip(part.participant_id, part.age))
    subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(D.REPO, 'private', 'auditory_c3', 'public', 'dtu_v2', '*.json')))
    folds = D._folds({g: [s for s in subs if hs[s] == g] for g in ('nh', 'hi')})
    return [{'id': s, 'group': hs[s], 'fold': folds[s], 'dev': False, 'age': float(age[s])} for s in subs]


def _dtu_person(p, tfs, inv, cg, kept):
    """Yield (trial rows) for one DTU person exactly as load_dtu (kinds ss + cs); EEG standardised with the loader's _stdz."""
    import h5py
    from auditory_alignment import data as D
    shaof = {(r['file'], r['trial'], r['kind']): (r.get('sha'), r['offset_s']) for r in inv}
    with h5py.File(os.path.join(D.DTU_PRE, f"{p['id']}.h5"), 'r') as f:
        ch = [str(c) for c in f.attrs['channels']][:64]
        rows = []
        for k in sorted(f.keys()):
            g = f[k]; two = str(g.attrs['talkers']) == 'twotalker'
            th, _ = shaof.get((p['id'], k, 'target'), (None, 0)); mh, moff = shaof.get((p['id'], k, 'masker'), (None, 0))
            if th is None or th not in cg or any(th not in tf for tf in tfs) or (two and (mh is None or any(mh not in tf for tf in tfs))):
                continue
            rows.append((k, two, th, mh, moff, g['eeg_1_20'][()][:64].astype(np.float64), float(g.attrs['masker_onset_rel_s']) if two else None))
    xs = D._stdz([r[5] for r in rows], 64)
    out = []
    for (k, two, th, mh, moff, _, mon), x in zip(rows, xs):
        n = x.shape[1]; c = cg[th]
        roles = tuple('test' if c['half'] == cf else ('es' if c['early_stop'] else 'fit') for cf in CFS)
        a0 = 64 if not two else max(64, int(np.ceil((mon + 1.7) * FS_IN)))
        sts = D._segments_of(a0, n, SEG128, int(D.MAX_WIN_S * FS_IN) + 1 + D.AUDIO_FRAMES)
        env = None
        if two and kept:
            env = []
            for h, lead in ((th, 0), (mh, int(round(moff * FS_IN)))):
                es_ = []
                for tf in tfs:
                    z = tf[f'{h}/Local'][5]; a = np.zeros(n, np.float32); m = min(len(z), n - lead); a[lead:lead + m] = z[:m]; es_.append(a)
                assert all(np.array_equal(es_[0], e) for e in es_[1:]), 'Local[5] differs between content folds'
                env.append(es_[0])
        out.append({'trial': k, 'kind': 'cs' if two else 'ss', 'n': n, 'x': x, 'sts': sts, 'roles': roles, 'code': th[:10],
                    'uid': lambda st, c=c: f"g{c['group']}@{st}", 'env': env, 'th': th, 'mh': mh, 'moff': moff if two else None})
    return ch, out


def _fau_person(p, tfs, kept):
    import h5py
    from auditory_alignment import data as D
    guard = 314
    with h5py.File(os.path.join(D.STAGEB, p['group'], f"{p['id']}.h5"), 'r') as f:
        ch = [str(c) for c in f.attrs['channels']]
        assert len(ch) == 31 and 'IO2' not in ch
        trials = [(str(f[t].attrs['stimulus']), t, f[t]['eeg_1_20_ica'][()].astype(np.float64)) for t in sorted(f.keys())]
    trials = [(c, t, x) for c, t, x in trials if c[0] in '12']
    xs = D._stdz([x for _, _, x in trials], guard)
    out = []
    for (code, tkey, _), x in zip(trials, xs):
        kind = 'ss' if code[0] == '1' else 'cs'
        roles = tuple(next(r for r, parts in D.FAU_CF[cf][kind].items() if code[2] in parts) for cf in CFS)
        lens = []
        for stream in (('attended', 'distractor') if kind == 'cs' else ('attended',)):
            ls = []
            for tf in tfs:
                ls.append(min(tf[f'{code}/{stream}/{t}'].shape[1] for t in ('Ac', 'Lz', 'Local')))
            assert len(set(ls)) == 1; lens.append(ls[0])
        n = min([x.shape[1]] + lens)
        sts = D._segments_of(guard, n - guard, SEG128, int(D.MAX_WIN_S * FS_IN) + 1 + D.AUDIO_FRAMES)
        env = None
        if kind == 'cs' and kept:
            env = []
            for stream, ln in zip(('attended', 'distractor'), lens):
                es_ = [tf[f'{code}/{stream}/Local'][5, :ln].astype(np.float32) for tf in tfs]
                assert all(np.array_equal(es_[0], e) for e in es_[1:]), 'Local[5] differs between content folds'
                env.append(es_[0])
        out.append({'trial': tkey, 'kind': kind, 'n': x.shape[1], 'x': x, 'sts': sts, 'roles': roles, 'code': code,
                    'uid': lambda st, code=code: f'{code}@{st}', 'env': env})
    return ch, out


def build_input(ds):
    """CPU: per-person cs cache + index for both content folds (asserted against the frozen B0 units)."""
    import h5py
    from auditory_alignment import data as D
    from auditory_alignment_v2.train import train_participants
    root = INPUT / ds; root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (root / 'index.json').exists():
        return read(root / 'index.json')
    parts = _people(ds)
    if ds == 'dtu':
        tfs = [h5py.File(os.path.join(D.DTU_KCS, f'dtu_cf{cf}.h5'), 'r') for cf in CFS]
        inv = json.load(open(f'{D.PUB}/derived/c3_features_v1/dtu/inventory.json'))
        cg = json.load(open(os.path.join(D.DTU_KCS, 'content_groups.json')))['content']
    else:
        tfs = [h5py.File(os.path.join(D.FAU_KCS, f'fau_cf{cf}.h5'), 'r') for cf in CFS]
    base = 0; idx = {k: [] for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role0', 'cs_role1', 'cs_trial', 'cs_st', 'cs_row')}
    ss_people, channels, files = set(), None, {}
    for p in parts:
        if p.get('test_only'):
            raise AssertionError('test_only participant not expected')
        ch, rows = (_dtu_person(p, tfs, inv, cg, True) if ds == 'dtu' else _fau_person(p, tfs, True))
        channels = channels or ch; assert ch == channels, f'channel order differs for {p["id"]}'
        E, ATT, IGN = [], [], []
        for r in rows:
            for st in r['sts']:
                if r['kind'] == 'ss':
                    if any(role in ('fit', 'es', 'test') for role in r['roles']):
                        ss_people.add(p['id'])
                    continue
                if r['env'] is None:
                    continue
                assert st + BLOCK128 <= r['n'], ('block beyond trial', p['id'], r['trial'], st)
                idx['cs_person'].append(p['id']); idx['cs_code'].append(str(r['code'])); idx['cs_e0'].append(base + st)
                idx['cs_role0'].append(r['roles'][0]); idx['cs_role1'].append(r['roles'][1]); idx['cs_trial'].append(r['trial'])
                idx['cs_st'].append(st); idx['cs_row'].append(len(E))
                E.append(pairmean(r['x'][:, st:st + BLOCK128]).astype(np.float32))
                ATT.append(r['env'][0][st:st + SEG128]); IGN.append(r['env'][1][st:st + SEG128])
            base += r['n']
        if E:
            path = root / f"{p['id']}.npz"
            np.savez(path, eeg64=np.stack(E), att128=np.stack(ATT), ign128=np.stack(IGN))
            files[p['id']] = sha(path)
        del rows, E, ATT, IGN
    for tf in tfs:
        tf.close()
    arrays = {k: np.array(v) for k, v in idx.items()}
    # ------------------------------------------------------------------ equality with the frozen B0 units, both content folds
    checks = {}
    for cf in CFS:
        A, meta = frozen_arrays(ds, cf)
        assert np.array_equal(arrays['cs_person'], A['cs_person']) and np.array_equal(arrays['cs_code'], A['cs_code'])
        assert np.array_equal(arrays['cs_e0'], A['cs_e0']) and np.array_equal(arrays[f'cs_role{cf}'], A['cs_role']), f'cs arrays cf{cf}'
        offs = A['cs_offsets']; att_ok = ign_ok = True
        for pid in sorted(set(arrays['cs_person'].tolist())):
            sel = np.flatnonzero(arrays['cs_person'] == pid)
            with np.load(root / f'{pid}.npz') as z:
                rows_ = arrays['cs_row'][sel]
                att_ok &= np.array_equal(z['att128'][rows_][:, offs].astype(np.float64), A['cs_env_att'][sel])
                ign_ok &= np.array_equal(z['ign128'][rows_][:, offs].astype(np.float64), A['cs_env_ign'][sel])
        assert att_ok and ign_ok, f'envelope anchors cf{cf}'
        shim = _Shim(parts)
        for sf in SFS:
            tp = sorted(parts[i]['id'] for i in train_participants(shim, {}, sf))
            assert tp == meta['pca'][str(sf)]['train_people'], f'train people cf{cf} sf{sf}'
        assert sorted(ss_people) == sorted(set(A['person'].tolist())), 'ss-anchor people'
        assert meta['groups'] == {p['id']: p['group'] for p in parts} and meta['folds'] == {p['id']: p['fold'] for p in parts}
        checks[f'cf{cf}'] = {'cs_arrays_equal': True, 'env_anchor_equal': True, 'train_people_equal': True, 'ss_people_equal': True}
    np.savez(root / 'index.npz', **arrays)
    shim = _Shim(parts)
    people = {}
    for sf in SFS:
        tp = sorted(parts[i]['id'] for i in train_participants(shim, {}, sf))
        te = sorted(p['id'] for p in parts if p['id'] in ss_people and p['fold'] == sf and not p.get('dev'))
        people[str(sf)] = {'train': tp, 'test': te}
    index = {'version': 'PAPER_EXT_INPUT_v1', 'dataset': ds, 'n_cs': int(len(arrays['cs_e0'])), 'channels': channels,
             'groups': {p['id']: p['group'] for p in parts}, 'folds': {p['id']: p['fold'] for p in parts},
             'dev_people': [p['id'] for p in parts if p.get('dev')], 'ss_people': sorted(ss_people), 'people': people,
             'files_sha256': files, 'index_sha256': sha(root / 'index.npz'), 'frozen_b0': frozen_b0(ds), 'checks': checks,
             'geometry': {'fs_in': FS_IN, 'fs': FS, 'segment_128': SEG128, 'block_128': BLOCK128, 'downsample': 'pairwise mean',
                          'eeg': 'cohort EEG (per-person z-score of the loaders), block [e0, e0 + 704) at 128 Hz',
                          'envelope': 'kcs Local row 5 (broadband envelope, 1-8 Hz, 128 Hz) of the attended / ignored stream over [s0, s0 + 640)'},
             'sources': sources()}
    write(root / 'index.json', index)
    return index


def verify_eeg(ds, n_people=2):
    """EEG blocks of the cache == the original loader's cohort EEG on a person subset (loader restricted by patching its
    participant enumeration only; per-person standardisation makes the subset exact)."""
    from auditory_alignment import data as D
    root = INPUT / ds; index = read(root / 'index.json')
    with np.load(root / 'index.npz') as z:
        arr = {k: z[k] for k in z.files}
    people = sorted(set(arr['cs_person'].tolist()))[:n_people]
    saved = {}
    try:
        if ds == 'dtu':
            real = D.glob.glob
            saved['glob'] = real

            class G:
                @staticmethod
                def glob(pat):
                    out = real(pat)
                    return [p for p in out if os.path.basename(p)[:-5] in people] if 'dtu_v2' in pat else out
            D.glob = G
            coh = D.load_dtu(0, kinds=('ss', 'cs'))
        else:
            real = D.fau_panel
            saved['fau_panel'] = real
            dev, panel = real()
            D.fau_panel = lambda: ([s for s in dev if s in people], {s: v for s, v in panel.items() if s in people})
            coh = D.load_fau(0, kinds=('ss', 'cs'))
    finally:
        if 'glob' in saved:
            D.glob = saved['glob']
        if 'fau_panel' in saved:
            D.fau_panel = saved['fau_panel']
    parts = coh.participants; maxdiff, n = 0.0, 0
    cs = [s for s in coh.segments if s['kind'] == 'cs' and s.get('s0_ign') is not None and s['role'] in ('fit', 'es', 'test')]
    for pid in people:
        sel = np.flatnonzero(arr['cs_person'] == pid)
        mine = [s for s in cs if parts[s['p']]['id'] == pid]
        assert len(mine) == len(sel), (pid, len(mine), len(sel))
        with np.load(root / f'{pid}.npz') as z:
            E = z['eeg64'][arr['cs_row'][sel]]
        for j, s in enumerate(mine):
            ref = pairmean(coh.eeg[:, s['e0']:s['e0'] + BLOCK128])
            maxdiff = max(maxdiff, float(np.abs(ref - E[j]).max())); n += 1
    rec = {'dataset': ds, 'people': people, 'segments_compared': n, 'max_abs_diff': maxdiff, 'pass': maxdiff == 0.0}
    write(root / 'verify_eeg.json', rec)
    assert rec['pass'], rec
    return rec


class Cache:
    """Read access to the per-person cs cache of one dataset."""

    def __init__(self, ds):
        self.ds = ds; self.root = INPUT / ds; self.index = read(self.root / 'index.json')
        with np.load(self.root / 'index.npz') as z:
            self.arr = {k: z[k] for k in z.files}
        assert sha(self.root / 'index.npz') == self.index['index_sha256']

    def role(self, cf):
        return self.arr[f'cs_role{cf}']

    def person_rows(self, pid):
        return np.flatnonzero(self.arr['cs_person'] == pid)

    def load(self, pid, check=False):
        path = self.root / f'{pid}.npz'
        if check:
            assert sha(path) == self.index['files_sha256'][pid]
        with np.load(path) as z:
            return z['eeg64'], pairmean(z['att128']), pairmean(z['ign128'])

    def unit_people(self, sf):
        p = self.index['people'][str(sf)]
        return p['train'], p['test']

    def scored(self, cf, sf):
        """(train-side ids = train people fit + es; test ids = test people test) in cache order."""
        train, test = map(set, self.unit_people(sf)); person, role = self.arr['cs_person'], self.role(cf)
        tr = np.flatnonzero(np.isin(person, list(train)) & np.isin(role, ('fit', 'es')))
        te = np.flatnonzero(np.isin(person, list(test)) & (role == 'test'))
        return tr, te


# ------------------------------------------------------------------------------------------------ scoring
def integrate_unit(cache, cf, sf, margin):
    """aln42.external_eval.integrate on one unit's segment margins (NaN outside the unit's scored segments)."""
    from ..aln42 import external_eval as XE
    train, test = cache.unit_people(sf)
    a = cache.arr
    return XE.integrate(margin, a['cs_person'], cache.role(cf), a['cs_code'], a['cs_e0'], SEG128, set(train), set(test))


def summarize(per_unit, groups, ds):
    """per_unit: {(cf, sf): integrate() output}.  Per person: content folds averaged, both required (as external_eval)."""
    per = {}
    for (cf, sf), res in per_unit.items():
        for sec, val in res.items():
            for p, v in val['people'].items():
                per.setdefault(sec, {}).setdefault(p, {})[cf] = v
    out = {}
    for sec, d in per.items():
        people = {p: {'accuracy': float(np.mean([v[c]['accuracy'] for c in CFS])), 'nll_bits': float(np.mean([v[c]['nll_bits'] for c in CFS])),
                      'n_windows': int(sum(v[c]['n_windows'] for c in CFS)), 'group': groups[p]}
                  for p, v in d.items() if sorted(v) == list(CFS)}
        g = {}
        for grp in GROUPS[ds] + ('all',):
            vals = [v for v in people.values() if grp == 'all' or v['group'] == grp]
            if vals:
                acc = np.array([v['accuracy'] for v in vals]); nll = np.array([v['nll_bits'] for v in vals])
                g[grp] = {'n_people': len(vals), 'accuracy_mean': float(acc.mean()), 'accuracy_sd': float(acc.std(ddof=1)) if len(acc) > 1 else None,
                          'nll_bits_mean': float(nll.mean()), 'nll_bits_sd': float(nll.std(ddof=1)) if len(nll) > 1 else None}
        out[sec] = {'groups': g, 'people': people}
    return out
