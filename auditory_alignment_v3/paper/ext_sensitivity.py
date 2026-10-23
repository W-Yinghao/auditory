"""Paper line, Table 2 POST-HOC training-data sensitivity analyses (CPU), requested by the coordinator on 2026-10-22 after the
mTRF Table 2 numbers (cs-trained) had been seen.  Protocol frozen before computing: results/.../sensitivity/PROTOCOL.json
(post_hoc: true).  Nothing here replaces a primary Table 2 cell.

(a) mtrf_ss: the ext_mtrf backward decoder (64 Hz, lags 0..500 ms, aln34.content_time ridge, alpha grid logspace(-3, 4, 8),
    alpha by mean per-segment r, refit fit + es) trained on the unit's train people's SINGLE-SPEAKER (ss) role=fit segments
    (target = the presented envelope, kcs Local row 5), alpha selected on their ss role=es segments, then applied to the same
    competing-speaker (cs) segments with the same margin and aln42.external_eval.integrate rule as Table 2.  The ss inputs come
    from a lean replica of the cohort loaders (ext_common helpers), asserted against the frozen B0 ss anchors (person, role, e0,
    envelope at the 8 anchors) for both content folds.
(b) readout_cs: the aln41 frozen PCA64 features of B0 (seed-free R1), TCS and TNCE (seeds 3401 / 3407 / 3413; R2 seeds via
    aln41.r2.seeded) with the readout.public ridge (content_time.fitted per slot, alpha by ES r, refit fit + es; target
    standardised on the training rows) fitted on the train people's cs ANCHORS (16 per 5 s segment, cs_pca_sf<sf>) with the
    ATTENDED envelope as target (role fit; alpha on role es), q0 mixture over the 3 slots, scored with readout.attention
    (attention margin + mean evidence + tau on training-side windows).  Per person: content folds averaged, then seeds (all
    three required for TCS / TNCE).  Pipeline check: the original ss-trained readout recomputed here must reproduce the stored
    aln41 readout records (q0 attention, every window and person) exactly.
CLI: python -m auditory_alignment_v3.paper.ext_sensitivity protocol | ss-input | mtrf-ss | readout-cs
"""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

from .. import core
from . import ext_common as XC
from . import ext_mtrf as MT

RES = XC.RESULTS / 'sensitivity'
OUT = XC.OUT / 'sensitivity'
STORE = XC.STORE / 'sensitivity'
SS_INPUT = XC.STORE / 'input_ss_v1'
PROTOCOL = RES / 'PROTOCOL.json'
ARMS = {'B0': (3401,), 'TCS': (3401, 3407, 3413), 'TNCE': (3401, 3407, 3413)}
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def freeze_protocol():
    body = {'post_hoc': True, 'requested': '2026-10-22 by the coordinator, after the cs-trained mTRF Table 2 numbers were seen',
            'reason': 'training-data mismatch: mTRF trains on cs attended segments, the proposed readout (aln41 readout.attention) on ss data',
            'analyses': {
                'a_mtrf_ss': {'output': 'TABLE2_MTRF_SS.json', 'decoder': 'ext_mtrf (same lags, alpha grid, selection rule)',
                              'train': 'train people ss role=fit (presented envelope)', 'alpha': 'mean per-segment r on train people ss role=es',
                              'refit': 'ss fit + es', 'scored': 'Table 2 cs segments, margin r(att) - r(ign), aln42.external_eval.integrate'},
                'b_readout_cs': {'output': 'TABLE2_READOUT_CS_<ARM>.json', 'arms_seeds': {k: list(v) for k, v in ARMS.items()},
                                 'features': 'aln41 frozen cs_pca_sf<sf> (16 anchors x 3 slots x 64)',
                                 'ridge': 'aln34.content_time.fitted per slot (alpha by ES r, refit fit + es), target standardised on training rows',
                                 'train': 'train people cs anchors role=fit, ATTENDED envelope', 'alpha': 'train people cs anchors role=es',
                                 'mixture': 'q0 = softmax(source a) (B0 uniform)', 'scored': 'aln41 readout.attention (q0), 5/10/20 s',
                                 'aggregation': 'content folds averaged, then seeds (all required)',
                                 'pipeline_check': 'ss-trained readout recomputed == stored aln41 readout records'}},
            'partition': 'ext_common / ALN4.1 public units (2 content folds x 5 person folds)',
            'module_sha256_at_freeze': sha(Path(__file__)), 'mtrf_plan_sha256': sha(MT.OUT / 'plan.json')}
    if PROTOCOL.exists():
        old = read(PROTOCOL); assert all(old[k] == v for k, v in body.items() if k != 'module_sha256_at_freeze'), 'protocol drift'
        return old
    os.umask(0o022); RES.mkdir(parents=True, exist_ok=True)
    PROTOCOL.write_text(json.dumps({**body, 'frozen_at': datetime.now().astimezone().isoformat()}, indent=1) + '\n'); PROTOCOL.chmod(0o444)
    os.umask(0o077)
    return read(PROTOCOL)


# ------------------------------------------------------------------------------------------------ (a) ss inputs
def build_ss_input(ds):
    import h5py
    from auditory_alignment import data as D
    from ..aln34 import content_time as CT
    root = SS_INPUT / ds; root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (root / 'index.json').exists():
        return read(root / 'index.json')
    parts = XC._people(ds)
    if ds == 'dtu':
        tfs = [h5py.File(os.path.join(D.DTU_KCS, f'dtu_cf{cf}.h5'), 'r') for cf in XC.CFS]
        inv = json.load(open(f'{D.PUB}/derived/c3_features_v1/dtu/inventory.json'))
        cg = json.load(open(os.path.join(D.DTU_KCS, 'content_groups.json')))['content']
    else:
        tfs = [h5py.File(os.path.join(D.FAU_KCS, f'fau_cf{cf}.h5'), 'r') for cf in XC.CFS]
    base = 0; idx = {k: [] for k in ('ss_person', 'ss_e0', 'ss_role0', 'ss_role1', 'ss_row')}
    files = {}
    for p in parts:
        ch, rows = (XC._dtu_person(p, tfs, inv, cg, False) if ds == 'dtu' else XC._fau_person(p, tfs, False))
        E, ENV = [], []
        for r in rows:
            if r['kind'] == 'ss' and r['sts']:
                if ds == 'dtu':
                    es_ = []
                    for tf in tfs:
                        z = tf[f"{r['th']}/Local"][5]; a = np.zeros(r['n'], np.float32); m = min(len(z), r['n']); a[:m] = z[:m]; es_.append(a)
                else:
                    ln = min(tfs[0][f"{r['code']}/attended/{t}"].shape[1] for t in ('Ac', 'Lz', 'Local'))
                    es_ = [tf[f"{r['code']}/attended/Local"][5, :ln].astype(np.float32) for tf in tfs]
                assert all(np.array_equal(es_[0], e) for e in es_[1:]), 'ss Local[5] differs between content folds'
                env = es_[0]
                for st in r['sts']:
                    assert st + XC.BLOCK128 <= r['n'] and st + XC.SEG128 <= len(env)
                    idx['ss_person'].append(p['id']); idx['ss_e0'].append(base + st); idx['ss_role0'].append(r['roles'][0])
                    idx['ss_role1'].append(r['roles'][1]); idx['ss_row'].append(len(E))
                    E.append(XC.pairmean(r['x'][:, st:st + XC.BLOCK128]).astype(np.float32)); ENV.append(env[st:st + XC.SEG128])
            base += r['n']
        if E:
            np.savez(root / f"{p['id']}.npz", eeg64=np.stack(E), env128=np.stack(ENV)); files[p['id']] = sha(root / f"{p['id']}.npz")
        del rows, E, ENV
    for tf in tfs:
        tf.close()
    arr = {k: np.array(v) for k, v in idx.items()}
    offs = CT.valid_offsets(XC.FS_IN, XC.SEG128)
    for cf in XC.CFS:
        ref = XC.frozen_b0(ds)[str(cf)]
        with np.load(Path(ref['dest']) / 'arrays.npz', allow_pickle=False) as z:
            seg, person, role, e0, env = z['segment'], z['person'], z['role'], z['e0'], z['env']
        first = np.unique(seg, return_index=True)[1]
        assert np.array_equal(person[first], arr['ss_person']) and np.array_equal(e0[first], arr['ss_e0'])
        assert np.array_equal(role[first], arr[f'ss_role{cf}']), f'ss roles cf{cf}'
        envs = env.reshape(len(first), len(offs)); ok = True
        for pid in sorted(set(arr['ss_person'].tolist())):
            sel = np.flatnonzero(arr['ss_person'] == pid)
            with np.load(root / f'{pid}.npz') as zz:
                ok &= np.array_equal(zz['env128'][arr['ss_row'][sel]][:, offs].astype(np.float64), envs[sel])
        assert ok, f'ss envelope anchors cf{cf}'
    np.savez(root / 'index.npz', **arr)
    index = {'version': 'PAPER_EXT_SS_INPUT_v1', 'dataset': ds, 'n_ss': int(len(arr['ss_e0'])), 'files_sha256': files,
             'index_sha256': sha(root / 'index.npz'), 'checks': 'person / e0 / role (both cf) and envelope at the 8 frozen anchors equal to frozen B0',
             'module_sha256': sha(Path(__file__))}
    write(root / 'index.json', index)
    return index


class SSCache:
    def __init__(self, ds):
        self.root = SS_INPUT / ds; self.index = read(self.root / 'index.json')
        with np.load(self.root / 'index.npz') as z:
            self.arr = {k: z[k] for k in z.files}
        assert sha(self.root / 'index.npz') == self.index['index_sha256']

    def load(self, pid):
        path = self.root / f'{pid}.npz'; assert sha(path) == self.index['files_sha256'][pid]
        with np.load(path) as z:
            return z['eeg64'], XC.pairmean(z['env128'])


# ------------------------------------------------------------------------------------------------ (a) mTRF-ss
def mtrf_ss_group(ds, cf):
    t0 = time.time()
    cs, ss = XC.Cache(ds), SSCache(ds)
    srole, sperson = ss.arr[f'ss_role{cf}'], ss.arr['ss_person']
    D = len(cs.index['channels']) * MT.NLAG
    stats = {}
    for pid in sorted(set(sperson.tolist())):                                        # pass 1: ss fit / es statistics
        rows_ = np.flatnonzero(sperson == pid); E, env = ss.load(pid); loc = ss.arr['ss_row'][rows_]; k = MT.fold_key(cs.index, pid)
        for r in ('fit', 'es'):
            sel = loc[srole[rows_] == r]; st = stats.setdefault((k, r), MT.Stats(D))
            for s in range(0, len(sel), MT.CHUNK):
                b = sel[s:s + MT.CHUNK]; st.add(MT.design(E[b]), env[b].reshape(-1).astype(np.float64))
        del E
    units = {}
    for sf in XC.SFS:
        train, test = cs.unit_people(sf); keys = sorted({MT.fold_key(cs.index, p) for p in train}); assert str(sf) not in keys
        fit = sum((stats[(k, 'fit')] for k in keys[1:]), stats[(keys[0], 'fit')]); es = sum((stats[(k, 'es')] for k in keys[1:]), stats[(keys[0], 'es')])
        Wa, ba = MT.solve(fit, MT.ALPHAS)
        units[sf] = {'train': set(train), 'test': set(test), 'Wa': Wa, 'ba': ba, 'es_r': [[] for _ in MT.ALPHAS], 'all': fit + es,
                     'fit_rows': fit.n, 'es_rows': es.n}
    for pid in sorted(set(sperson.tolist())):                                        # pass 2: ss es selection
        need = [sf for sf in XC.SFS if pid in units[sf]['train']]
        if not need:
            continue
        rows_ = np.flatnonzero(sperson == pid); E, env = ss.load(pid); sel = ss.arr['ss_row'][rows_][srole[rows_] == 'es']
        for s in range(0, len(sel), MT.CHUNK):
            b = sel[s:s + MT.CHUNK]; X = MT.design(E[b])
            for sf in need:
                P = (X @ units[sf]['Wa'] + units[sf]['ba']).reshape(len(b), XC.SEG64, len(MT.ALPHAS))
                r = XC.rowcorr(np.moveaxis(P, 2, 1), env[b][:, None, :].astype(np.float64))
                for a in range(len(MT.ALPHAS)):
                    units[sf]['es_r'][a].extend(r[:, a].tolist())
        del E
    for sf, u in units.items():
        u['curve'] = [float(np.mean(v)) for v in u['es_r']]; u['alpha'] = float(MT.ALPHAS[int(np.argmax(u['curve']))])
        W, b = MT.solve(u['all'], [u['alpha']]); u['w'], u['b'] = W[:, 0], float(b[0]); u['n_es'] = len(u['es_r'][0])
        del u['all'], u['Wa'], u['ba'], u['es_r']
    role, person = cs.role(cf), cs.arr['cs_person']; n = len(person)                # pass 3: cs margins
    for u in units.values():
        u['margin'] = np.full(n, np.nan)
    for pid in sorted(set(person.tolist())):
        rows_ = cs.person_rows(pid); E, att, ign = cs.load(pid); loc = cs.arr['cs_row'][rows_]; rl = role[rows_]
        for sf, u in units.items():
            m = np.isin(rl, ('fit', 'es')) if pid in u['train'] else (rl == 'test') if pid in u['test'] else None
            if m is None:
                continue
            for s in range(0, int(m.sum()), MT.CHUNK):
                gi = rows_[m][s:s + MT.CHUNK]; b = loc[m][s:s + MT.CHUNK]
                P = (MT.design(E[b]) @ u['w'] + u['b']).reshape(len(b), XC.SEG64)
                u['margin'][gi] = XC.rowcorr(P, att[b].astype(np.float64)) - XC.rowcorr(P, ign[b].astype(np.float64))
        del E
    res = {}
    for sf, u in units.items():
        body = {'analysis': 'mtrf_ss', 'dataset': ds, 'content_fold': cf, 'person_fold': sf}; uid = 'PXSENS_A_' + digest(body, 16)
        dest = STORE / 'mtrf_ss' / uid; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
        np.savez_compressed(dest / 'margins.npz', margin=u['margin'], cs_person=person, cs_role=role)
        res[(cf, sf)] = XC.integrate_unit(cs, cf, sf, u['margin'])
        write(OUT / 'mtrf_ss' / 'units' / f'{uid}.json', {**body, 'id': uid, 'alpha_relative': u['alpha'], 'es_mean_r_curve': u['curve'],
                                                          'n_ss_es_segments': u['n_es'], 'ss_fit_rows': int(u['fit_rows']), 'ss_es_rows': int(u['es_rows']),
                                                          'margins_sha256': sha(dest / 'margins.npz'), 'protocol_sha256': sha(PROTOCOL),
                                                          'module_sha256': sha(Path(__file__)), 'seconds_group': round(time.time() - t0, 1)})
        print('mtrf_ss', ds, cf, sf, 'alpha', u['alpha'], flush=True)
    return res


def table(system, per_unit_by_ds, extra=None):
    out = {'system': system, 'post_hoc': True, 'protocol_sha256': sha(PROTOCOL), 'module_sha256': sha(Path(__file__)), **(extra or {}), 'datasets': {}}
    for ds, (summ, taus) in per_unit_by_ds.items():
        out['datasets'][ds] = {'summary_by_window_s': {sec: v['groups'] for sec, v in summ.items()},
                               'per_person_by_window_s': {sec: v['people'] for sec, v in summ.items()}, 'tau': taus}
    os.umask(0o022); RES.mkdir(parents=True, exist_ok=True)
    path = RES / f'TABLE2_{system.upper()}.json'; path.write_text(json.dumps(out, indent=1, default=float) + '\n'); os.umask(0o077)
    cells = {ds: {g: (round(v['accuracy_mean'], 4), round(v['nll_bits_mean'], 4), v['n_people'])
                  for g, v in out['datasets'][ds]['summary_by_window_s']['20'].items()} for ds in out['datasets']}
    print(system, json.dumps(cells), flush=True)
    return out


def run_mtrf_ss():
    assert PROTOCOL.exists()
    by = {}
    for ds in XC.DATASETS:
        per_unit = {}
        for cf in XC.CFS:
            per_unit.update(mtrf_ss_group(ds, cf))
        cache = XC.Cache(ds)
        by[ds] = (XC.summarize(per_unit, cache.index['groups'], ds),
                  {f'cf{cf}_sf{sf}': {sec: v['tau'] for sec, v in r.items()} for (cf, sf), r in per_unit.items()})
    return table('mtrf_ss', by)


# ------------------------------------------------------------------------------------------------ (b) cs-trained frozen readout
def frozen_unit(arm, ds, cf, seed):
    from ..aln41 import frozen as FZ, r2 as R2
    import contextlib
    ctx = R2.seeded(seed) if seed != 3401 else contextlib.nullcontext()
    with ctx:
        plan = read(FZ.BASE / 'plan.json')
        row = next(r for r in plan['rows'] if r['arm'] == arm and r['dataset'] == ds and r['content_fold'] == cf)
        unit = read(FZ.BASE / 'units' / f'{row["id"]}.json')
        ro = (FZ.BASE.parent / 'readout_v1' / 'units' / f'{row["id"]}.json')
    dest = Path(unit['dest'])
    assert sha(dest / 'meta.json') == unit['meta_sha256'] and sha(dest / 'arrays.npz') == unit['array_sha256']
    return row, dest, read(dest / 'meta.json'), (read(ro) if ro.exists() else None)


def readout_unit(arm, ds, cf, seed):
    """{sf: {'cs': attention(cs-trained fits), 'ss': attention(ss-trained fits, readout.public replica)}} + check vs stored."""
    from ..aln34 import content_time as CT
    from ..aln41 import readout as RO
    row, dest, meta, stored = frozen_unit(arm, ds, cf, seed)
    q0 = np.asarray(meta['q0']); folds, dev = meta['folds'], set(meta['dev_people'])
    z = np.load(dest / 'arrays.npz', allow_pickle=False)
    base = {k: z[k] for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role', 'cs_env_att', 'cs_env_ign', 'person', 'role', 'env')}
    cp, crole = base['cs_person'], base['cs_role']; person, role = base['person'], base['role']
    out, maxdiff = {}, 0.0
    for sf in XC.SFS:
        train_people = set(meta['pca'][str(sf)]['train_people'])
        test_people = sorted(p for p in set(person.tolist()) if folds.get(p) == sf and p not in dev)
        A = {**{k: base[k] for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role', 'cs_env_att', 'cs_env_ign')}, f'cs_pca_sf{sf}': z[f'cs_pca_sf{sf}']}
        F = A[f'cs_pca_sf{sf}'].astype(np.float64); nseg, nanc = F.shape[:2]
        trn = np.isin(cp, list(train_people)); fit = np.repeat(trn & (crole == 'fit'), nanc); es = np.repeat(trn & (crole == 'es'), nanc)
        r2 = np.where(fit, 'fit', np.where(es, 'es', 'other'))
        y = base['cs_env_att'].reshape(-1); m, s = y[fit | es].mean(), y[fit | es].std() + 1e-12; t = (y - m) / s
        fits_cs = [CT.fitted(F[:, :, k].reshape(nseg * nanc, -1), t[:, None], r2) for k in range(3)]
        res_cs = RO.attention(A, meta, sf, fits_cs, q0, train_people, set(test_people))
        # pipeline check: readout.public's ss-trained fits, then the same attention call
        X = z[f'pca_sf{sf}'].astype(np.float64)
        strn = np.isin(person, list(train_people)); sfit = strn & (role == 'fit'); ses = strn & (role == 'es')
        sr2 = np.where(sfit, 'fit', np.where(ses, 'es', 'other'))
        ye = base['env']; m2, s2 = ye[sfit | ses].mean(), ye[sfit | ses].std() + 1e-12
        fits_ss = [CT.fitted(X[:, k], ((ye - m2) / s2)[:, None], sr2) for k in range(3)]
        res_ss = RO.attention(A, meta, sf, fits_ss, q0, train_people, set(test_people))
        if stored is not None:
            for sec, val in res_ss.items():
                for p, v in val['people'].items():
                    sv = stored['people'][p]['attention']['q0'][sec]
                    maxdiff = max(maxdiff, abs(v['accuracy'] - sv['accuracy']), abs(v['nll_bits'] - sv['nll_bits']), abs(val['tau'] - sv['tau']))
        out[sf] = {'cs': res_cs, 'ss': res_ss, 'alphas_cs': [f[2]['alpha_relative'] for f in fits_cs]}
        del F, X
    z.close()
    return out, {'unit': row['id'], 'seed': seed, 'stored_readout_present': stored is not None, 'ss_reproduction_max_abs_diff': maxdiff}, meta['groups']


def aggregate(per_seed, groups, ds, seeds):
    """per_seed[seed][(cf, sf)] = attention output -> people: cf mean (both required) then seed mean (all required)."""
    per = {}
    for seed, units in per_seed.items():
        for (cf, sf), res in units.items():
            for sec, val in res.items():
                for p, v in val['people'].items():
                    per.setdefault(sec, {}).setdefault(p, {}).setdefault(seed, {})[cf] = v
    out = {}
    for sec, d in per.items():
        people = {}
        for p, s in d.items():
            if all(x in s and sorted(s[x]) == list(XC.CFS) for x in seeds):
                acc = np.mean([np.mean([s[x][c]['accuracy'] for c in XC.CFS]) for x in seeds])
                nll = np.mean([np.mean([s[x][c]['nll_bits'] for c in XC.CFS]) for x in seeds])
                people[p] = {'accuracy': float(acc), 'nll_bits': float(nll), 'n_windows': int(sum(s[x][c]['n_windows'] for x in seeds for c in XC.CFS)),
                             'group': groups[p]}
        g = {}
        for grp in XC.GROUPS[ds] + ('all',):
            vals = [v for v in people.values() if grp == 'all' or v['group'] == grp]
            if vals:
                a = np.array([v['accuracy'] for v in vals]); nl = np.array([v['nll_bits'] for v in vals])
                g[grp] = {'n_people': len(vals), 'accuracy_mean': float(a.mean()), 'accuracy_sd': float(a.std(ddof=1)) if len(a) > 1 else None,
                          'nll_bits_mean': float(nl.mean()), 'nll_bits_sd': float(nl.std(ddof=1)) if len(nl) > 1 else None}
        out[sec] = {'groups': g, 'people': people}
    return out


def run_readout_cs():
    assert PROTOCOL.exists()
    for arm, seeds in ARMS.items():
        by, by_ss, checks, alphas = {}, {}, [], {}
        for ds in XC.DATASETS:
            per_cs, per_ss, groups = {}, {}, None
            for seed in seeds:
                for cf in XC.CFS:
                    res, chk, groups = readout_unit(arm, ds, cf, seed); checks.append({**chk, 'dataset': ds, 'content_fold': cf})
                    for sf, r in res.items():
                        per_cs.setdefault(seed, {})[(cf, sf)] = r['cs']; per_ss.setdefault(seed, {})[(cf, sf)] = r['ss']
                        alphas[f'{ds}_s{seed}_cf{cf}_sf{sf}'] = r['alphas_cs']
                    print(arm, ds, seed, cf, chk, flush=True)
            taus = {f's{seed}_cf{cf}_sf{sf}': {sec: v['tau'] for sec, v in r.items()} for seed, u in per_cs.items() for (cf, sf), r in u.items()}
            by[ds] = (aggregate(per_cs, groups, ds, seeds), taus)
            by_ss[ds] = {sec: v['groups'] for sec, v in aggregate(per_ss, groups, ds, seeds).items()}
        assert all(c['stored_readout_present'] for c in checks)
        worst = max(c['ss_reproduction_max_abs_diff'] for c in checks)
        table(f'readout_cs_{arm}', by, extra={'arm': arm, 'seeds': list(seeds), 'pipeline_check': {'ss_readout_reproduces_stored_max_abs_diff': worst,
              'pass': worst < 1e-9, 'units': checks}, 'reference_ss_trained_summary_by_window_s': by_ss, 'cs_alphas_relative': alphas})


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    cmd = sys.argv[1]
    if cmd == 'protocol':
        print(json.dumps(freeze_protocol(), indent=1))
    elif cmd == 'ss-input':
        for ds in XC.DATASETS:
            print(ds, build_ss_input(ds)['n_ss'], flush=True)
    elif cmd == 'mtrf-ss':
        run_mtrf_ss()
    elif cmd == 'readout-cs':
        run_readout_cs()


if __name__ == '__main__':
    main()
