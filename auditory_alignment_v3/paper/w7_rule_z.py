"""W7 R_z (POST HOC, exploratory; CPU): decision rule R with each candidate's within-segment CS-QMI z-scored against its own
anchor-row permutation null. Defined in private/auditory_alignment_v3/paper/w7_v1/APPENDUM_RAD_06.md (frozen after the R results
were seen, before any R_z output); everything else is R (w7_rule.py, APPENDUM_RAD_01).

Per segment, slot s and candidate c: z = (CS(X^s; a_c) - mean_pi CS(X^s; a_c[pi])) / sd_pi (ddof 1) over one fixed set of 200
permutations pi of the 16 anchor rows (np.random.default_rng(20261024)); margin = sum_s q0_s (z_att - z_ign); sd = 0 -> z = 0
(counted). Bandwidths, integration (aln42.external_eval.integrate), tau, people, aggregation and the ridge reference as R.
CLI (Slurm CPU): python -m auditory_alignment_v3.paper.w7_rule_z gates | run | aggregate
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time

import numpy as np

from . import w7_rule as R

OUT = R.W7 / 'rule_z'
APPENDUM = R.W7 / 'APPENDUM_RAD_06.md'
N_PERM, PERM_SEED = 200, 20261024
ANCHORS = 16


def perms():
    rng = np.random.default_rng(PERM_SEED)
    return np.stack([rng.permutation(ANCHORS) for _ in range(N_PERM)])


def bindings():
    b = R.bindings()
    assert APPENDUM.exists() and not os.access(APPENDUM, os.W_OK), 'APPENDUM_RAD_06 must exist and be read-only'
    return {**b, 'appendum_rad_06_sha256': R.sha(APPENDUM), 'module_rule_z_sha256': R.sha(__file__), 'post_hoc': True}


def zscores(F, att, ign, sx, sa, P, chunk=256):
    """z [n, 3 slots, 2 candidates] and the true CS [n, 3, 2]; NaN rows of F are skipped (NaN out)."""
    n = len(F); Z = np.full((n, F.shape[2], 2), np.nan); T = np.full_like(Z, np.nan); zero_sd = 0
    for s0 in range(0, n, chunk):
        sl = slice(s0, min(n, s0 + chunk)); m = sl.stop - sl.start
        Ls, Lps, lbps = [], [], []
        for a in (att[sl], ign[sl]):
            L = np.exp(-(a[:, :, None] - a[:, None, :]) ** 2 / (2 * sa * sa))
            Ls.append(L); Lps.append(L[:, P[:, :, None], P[:, None, :]].reshape(m, N_PERM, ANCHORS * ANCHORS))
            lbps.append(L.mean(2)[:, P])                                           # [m, P, 16]
        for k in range(F.shape[2]):
            K = R.gram_batch(F[sl, :, k], sx); kb = K.mean(2); mK = K.mean((1, 2)); Kf = K.reshape(m, -1, 1)
            for c in range(2):
                L = Ls[c]; true = R.cs_batch(K, L)
                A = np.matmul(Lps[c], Kf)[..., 0] / (ANCHORS * ANCHORS)
                C = np.einsum('mi,mpi->mp', kb, lbps[c]) / ANCHORS
                null = np.log(A) + np.log(mK * L.mean((1, 2)))[:, None] - 2.0 * np.log(C)
                mu, sd = null.mean(1), null.std(1, ddof=1)
                ok = sd > 0; zero_sd += int((~ok).sum())
                Z[sl, k, c] = np.where(ok, (true - mu) / np.where(ok, sd, 1.0), 0.0); T[sl, k, c] = true
    return Z, T, zero_sd


def unit_id(arm, ds, cf, seed):
    return f'W7RZ_{arm}_{ds}_cf{cf}_s{seed}'


def run_unit(arm, ds, cf, seed, bind, P):
    from ..aln42 import external_eval as XE
    t0 = time.time(); row, dest, meta, ro = R.frozen_unit(arm, ds, cf, seed)
    q = np.asarray(meta['q0'], np.float64)
    z = np.load(dest / 'arrays.npz', allow_pickle=False)
    A = {k: z[k] for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role', 'cs_env_att', 'cs_env_ign', 'person')}
    att, ign = A['cs_env_att'].astype(np.float64), A['cs_env_ign'].astype(np.float64)
    folds = {}
    for sf in R.SFS:
        train, test = R.people_sets(meta, A['person'], sf)
        tr_seg = np.flatnonzero(np.isin(A['cs_person'], sorted(train)) & np.isin(A['cs_role'], ('fit', 'es')))
        te_mask = np.isin(A['cs_person'], sorted(test)) & (A['cs_role'] == 'test')
        need = np.zeros(len(att), bool); need[tr_seg] = True; need |= te_mask
        Ffull = z[f'cs_pca_sf{sf}'].astype(np.float64)
        sx, sa, sinfo = R.sigmas(Ffull, att, ign, tr_seg, f'{arm}|{seed}|{ds}|{cf}|{sf}')  # identical to R's sigmas
        ix = np.flatnonzero(need)
        F = Ffull[ix]; del Ffull
        Zs, _, zero_sd = zscores(F, att[ix], ign[ix], sx, sa, P)
        m = np.full(len(att), np.nan); m[ix] = np.einsum('k,nk->n', q, Zs[:, :, 0] - Zs[:, :, 1])
        res = XE.integrate(m, A['cs_person'], A['cs_role'], A['cs_code'], A['cs_e0'], meta['cs']['seg_len'], train, test)
        folds[str(sf)] = {'sigma': sinfo, 'tau': {sec: v['tau'] for sec, v in res.items()}, 'people': {sec: v['people'] for sec, v in res.items()},
                          'zero_sd_cells': zero_sd, 'scored_segments': int(len(ix)), 'test_segments': int(te_mask.sum()),
                          'margin_test_mean': float(np.nanmean(m[te_mask])) if te_mask.any() else None,
                          'z_att_test_mean_by_slot': np.nanmean(Zs[te_mask[ix], :, 0], 0).tolist() if te_mask.any() else None,
                          'z_ign_test_mean_by_slot': np.nanmean(Zs[te_mask[ix], :, 1], 0).tolist() if te_mask.any() else None}
        del F
    z.close()
    rec = {'status': 'complete', 'id': unit_id(arm, ds, cf, seed), 'arm': arm, 'dataset': ds, 'content_fold': cf, 'seed': seed,
           'frozen_unit': row['id'], 'q0': q.tolist(), 'stored_readout': str(ro), 'stored_readout_sha256': R.sha(ro), 'folds': folds,
           'groups': meta['groups'], 'bindings': bind, 'post_hoc': True, 'seconds': time.time() - t0, 'job': os.environ.get('SLURM_JOB_ID')}
    R.write(OUT / 'units' / f'{rec["id"]}.json', rec)
    print(rec['id'], 'complete', round(rec['seconds'], 1), flush=True)


def gates():
    import torch
    from ..aln41.cs_qmi_reference import cs_qmi
    P = perms(); row, dest, meta, ro = R.frozen_unit('TCS', 'fau', 0, 3401)
    z = np.load(dest / 'arrays.npz', allow_pickle=False)
    att, ign, F = z['cs_env_att'].astype(np.float64), z['cs_env_ign'].astype(np.float64), z['cs_pca_sf0'].astype(np.float64)
    pick = np.arange(0, len(att), max(1, len(att) // 5))[:5]; sx, sa = 90.0, 0.9
    Zs, T, _ = zscores(F[pick], att[pick], ign[pick], sx, sa, P)
    worst = 0.0
    for j, i in enumerate(pick):
        for k in range(3):
            for c, a in enumerate((att, ign)):
                vals = [float(cs_qmi(torch.as_tensor(F[i, :, k]), torch.as_tensor(a[i][p][:, None]), sigma_u=sx, sigma_v=sa)[0]) for p in P]
                tru = float(cs_qmi(torch.as_tensor(F[i, :, k]), torch.as_tensor(a[i][:, None]), sigma_u=sx, sigma_v=sa)[0])
                zref = (tru - np.mean(vals)) / np.std(vals, ddof=1)
                worst = max(worst, abs(tru - T[j, k, c]), abs(zref - Zs[j, k, c]) * np.std(vals, ddof=1))
    z.close()
    rec = {'z_estimator_max_abs_diff_vs_cs_qmi_reference': worst, 'status': 'pass' if worst < 1e-9 else 'failed', 'bindings': bindings(),
           'perms_sha256': __import__('hashlib').sha256(P.astype(np.int64).tobytes()).hexdigest(), 'job': os.environ.get('SLURM_JOB_ID')}
    R.write(OUT / 'GATES.json', rec); print(json.dumps(rec, indent=1, default=float), flush=True)
    assert rec['status'] == 'pass'


def run():
    bind = bindings(); g = json.loads((OUT / 'GATES.json').read_text()); assert g['status'] == 'pass' and g['bindings'] == bind
    P = perms()
    for arm, seeds in R.ARMS.items():
        for ds in R.DATASETS:
            for seed in seeds:
                for cf in R.CFS:
                    if not (OUT / 'units' / f'{unit_id(arm, ds, cf, seed)}.json').exists():
                        run_unit(arm, ds, cf, seed, bind, P)


def aggregate():
    from ..aln41 import analysis as AN
    bind = bindings(); base = json.loads((R.RESULTS / 'W7_RULE.json').read_text())
    table, fam_inputs, families, by_cf = {}, {}, [], {}
    for ds in R.DATASETS:
        table[ds] = {}
        for arm, seeds in R.ARMS.items():
            Rz, groups, cfacc, cfm = {}, None, {cf: {} for cf in R.CFS}, {cf: [] for cf in R.CFS}
            for seed in seeds:
                for cf in R.CFS:
                    rec = json.loads((OUT / 'units' / f'{unit_id(arm, ds, cf, seed)}.json').read_text()); assert rec['status'] == 'complete'
                    groups = rec['groups']; Rz[(seed, cf)] = {sec: {} for sec in R.WINDOWS}
                    for f in rec['folds'].values():
                        for sec in R.WINDOWS:
                            Rz[(seed, cf)][sec].update(f['people'][sec])
                        if f['margin_test_mean'] is not None:
                            cfm[cf].append(f['margin_test_mean'])
                    for p, v in Rz[(seed, cf)]['20'].items():
                        cfacc[cf].setdefault(p, []).append(v['accuracy'])
            pz = R.per_person(Rz, lambda v, k: v[k])
            table[ds][arm] = {'seeds': list(seeds),
                              'R_z': {sec: {'groups': R.summary(pz[sec], groups, ds), 'people': pz[sec]} for sec in R.WINDOWS},
                              'R_reference': {sec: base['table'][ds][arm]['R'][sec]['groups'] for sec in R.WINDOWS},
                              'ridge_reference': {sec: base['table'][ds][arm]['ridge'][sec]['groups'] for sec in R.WINDOWS}}
            by_cf.setdefault(ds, {})[arm] = {f'cf{cf}': {'R_z_20s_accuracy_mean': float(np.mean([np.mean(v) for v in cfacc[cf].values()])),
                                                         'mean_test_margin': float(np.mean(cfm[cf]))} for cf in R.CFS}
        fid = f'W7_RULE_Z:{ds}'
        people = sorted(set().union(*[set(table[ds][a]['R_z']['20']['people']) | set(base['table'][ds][a]['ridge']['20']['people']) for a in R.ARMS]))
        members = []
        for arm in R.ARMS:
            rz, g = table[ds][arm]['R_z']['20']['people'], base['table'][ds][arm]['ridge']['20']['people']
            members.append((f'{arm}:R_z-ridge', {p: (rz[p]['accuracy'] - g[p]['accuracy']) if p in rz and p in g else None for p in people}))
        fam_inputs[fid] = {'people': people, 'members': {n: v for n, v in members}}
        f = AN.family(fid, '20-s two-candidate accuracy, R_z - ridge (POST HOC, exploratory, descriptive)', members, people)
        f['method'] = 'aln41.analysis.family (bootstrap-t B=4000, max-|T*|); post hoc / exploratory per APPENDUM_RAD_06; descriptive only'
        f['post_hoc'] = True; families.append(f)
    out = {'version': 'W7_RULE_Z_v1', 'post_hoc': True, 'label': 'POST HOC / exploratory (APPENDUM_RAD_06); does not replace W7_RULE',
           'bindings': bind, 'gates': json.loads((OUT / 'GATES.json').read_text()), 'definition': __doc__, 'table': table,
           'by_content_fold': by_cf, 'family_inputs': fam_inputs, 'families': families}
    os.umask(0o022)
    (R.RESULTS / 'W7_RULE_Z.json').write_text(json.dumps(out, indent=1, default=float) + '\n')
    (R.RESULTS / 'W7_RULE_Z_FAMILIES.json').write_text(json.dumps({'version': 'W7_RULE_Z_FAMILIES_v1', 'post_hoc': True, 'bindings': bind,
                                                                    'input_sha256': R.sha(R.RESULTS / 'W7_RULE_Z.json'), 'families': families},
                                                                   indent=1, default=float) + '\n')
    for ds in R.DATASETS:
        for arm in R.ARMS:
            for sec in R.WINDOWS:
                a = table[ds][arm]['R_z'][sec]['groups']
                print(ds, arm, sec, 'R_z', {g: (round(v['accuracy_mean'], 4), round(v['nll_bits_mean'], 4), v['n_people']) for g, v in a.items()})
            print(ds, arm, 'by cf', by_cf[ds][arm])
    for f in families:
        print(f['family_id'], f['status'], f['complete_n'], [(m['name'], round(m.get('estimate', float('nan')), 4), m.get('simultaneous_95')) for m in f['members']])


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    {'gates': gates, 'run': run, 'aggregate': aggregate}[sys.argv[1]]()


if __name__ == '__main__':
    main()
