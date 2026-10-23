"""DEP12 Agent P: private mechanism-control report, version 3 (DECISIONS P25).

Block EXT1 (P23) and block EXT2 (P24) are recomputed by their unchanged functions (private_mechanism, private_mechanism_v2).
Block EXT3 is the coordinator's follow-up ext3 (DECISIONS 2026-10-23 11:55): arm ssl_continue (audio-free masked-patch
reconstruction continued pre-training, cs_pair LoRA recipe otherwise). Members per seed s and merged: ssl_continue@s - B0 and
cs_pair@s - ssl_continue@s. Primary: BDF U0 all-trials G; descriptive: BDF δ (U kernel), PCA64 δ, EEG-part AUC, MFF
within-pure-tone G and transfer AUC. B = 10,000; family max-|T*| simultaneous intervals.

Manipulation check (descriptive; coordinator 12:20 rule): per cohort, arm and seed, the representation change versus B0 on
the same trials = the stored full-U panel rows (BDF: every child's 128 panel rows from its own outer-fold features; MFF: every
lane-child's panel rows). Quantities: 1 - linear CKA (centred Gram form, pooled rows) and mean ||U_arm - U_B0|| over rows.
Ratios ssl_continue / cs_pair_noise and ssl_continue / cs_pair per seed and of seed means; flag ratio < 0.25 ("ssl_continue ≈
B0" then inconclusive). Outputs: private_mechanism_controls.{json,md} (EXT1 + EXT2 + EXT3 + manipulation), EXT2_PRIVATE.md
(unchanged writer), EXT3_PRIVATE.md, private_manipulation_check.json; marker REC/mechanism_v3/inputs.json.
"""
from __future__ import annotations

from datetime import datetime
import fcntl
import json
import os
from pathlib import Path

import numpy as np

from . import private_features as PF
from . import private_analysis as PA
from . import private_mechanism as M1
from . import private_mechanism_v2 as M2
from . import private_fleet_v4 as FL4

SEEDS = (3401, 3407, 3413)
MARK = PF.REC / 'mechanism_v3'
EXT3_MD = PF.RESULTS / 'EXT3_PRIVATE.md'
MANIP_JSON = PF.RESULTS / 'private_manipulation_check.json'
ARMS = ('cs_pair', 'info_nce', 'sigmoid', 'raw_cs', 'cs_pair_wrong', 'cs_pair_noise', 'ssl_continue')
RULE = 0.25
read, write, sha = PF.read, PF.write, PF.sha


# ----------------------------------------------------------------------------------------------- EXT3 families
def ext_families(V, endpoints, people, cohort, arm, block):
    fams = []
    for ep, role in endpoints:
        for s in SEEDS:
            a, cs = f'{arm}@{s}', f'cs_pair@{s}'
            mem = []
            if a in V and 'B0' in V:
                mem.append((f'{arm}-B0', PA.diff(V[a][ep], V['B0'][ep])))
            if cs in V and a in V:
                mem.append((f'cs_pair-{arm}', PA.diff(V[cs][ep], V[a][ep])))
            if mem:
                f = PA.family(f'{block}:{cohort}:{ep}[{s}]', f'{ep} ({role}; follow-up {block.lower()})', mem, people[ep])
                f.update(seed=s, role=role, block=block); fams.append(f)
        if 'B0' in V and all(f'{arm}@{s}' in V and f'cs_pair@{s}' in V for s in SEEDS):
            mem = [(f'{arm}-B0', PA.mean_over([PA.diff(V[f'{arm}@{s}'][ep], V['B0'][ep]) for s in SEEDS])),
                   (f'cs_pair-{arm}', PA.mean_over([PA.diff(V[f'cs_pair@{s}'][ep], V[f'{arm}@{s}'][ep]) for s in SEEDS]))]
            f = PA.family(f'{block}:{cohort}:{ep}[merged]', f'{ep} ({role}; follow-up {block.lower()}); child mean over seeds 3401/3407/3413',
                          mem, people[ep])
            f.update(seed='merged', role=role, block=block); fams.append(f)
    return fams


# ----------------------------------------------------------------------------------------------- manipulation check
def bdf_panel_U(name, bind):
    """[8192, D] panel rows of every child from its own outer-fold features, in binding child order."""
    sp = next((s for s in FL4.specs() if s['encoder'] == name), None)
    if sp is None or not (FL4.BASE / 'units' / f'{sp["id"]}.json').exists():
        return None, None
    rec = read(FL4.BASE / 'units' / f'{sp["id"]}.json'); off, _ = bind.offsets()
    blocks, keys = {}, {}
    for f in PF.FOLDS:
        p = Path(sp['store']) / f'fold{f}.npz'
        assert sha(p) == rec['arrays_sha256'][str(f)], f'feature drift {name} fold {f}'
        with np.load(p, allow_pickle=False) as z:
            kpos = {int(g): i for i, g in enumerate(z['kernel_index'])}
            for c in bind.test_ids(f):
                rows = [off[c] + int(r) for r in bind.arr(c, 'panel_rows')]
                blocks[c] = z['U_kernel'][[kpos[g] for g in rows]]; keys[c] = rows
    order = [c for c in bind.ids if c in blocks]
    return np.concatenate([blocks[c] for c in order]).astype(np.float32), [k for c in order for k in keys[c]]


def mff_panel_U(name):
    from . import private_mff_v4 as M
    sp = next((s for s in M.specs() if s['encoder'] == name), None)
    if sp is None or not (M.BASE / 'units' / f'{sp["id"]}.json').exists():
        return None, None
    rec = read(M.BASE / 'units' / f'{sp["id"]}.json'); p = Path(sp['store']) / 'features.npz'
    assert sha(p) == rec['array_sha256'], f'feature drift {name}'
    with np.load(p, allow_pickle=False) as z:
        return z['U_kernel'].astype(np.float32), z['kernel_index'].tolist()


def centred_gram(X):
    Xc = X - X.mean(0, keepdims=True)
    return Xc @ Xc.T


def change(U, U0, K0, K0n):
    K = centred_gram(U)
    cka = float(np.sum(K.astype(np.float64) * K0) / (np.linalg.norm(K.astype(np.float64)) * K0n))
    return {'one_minus_cka': 1.0 - cka, 'linear_cka': cka, 'mean_delta_norm': float(np.linalg.norm(U - U0, axis=1).mean()), 'n_rows': int(len(U))}


def manipulation(bind):
    out = {}
    for cohort, loader in (('BDF', lambda n: bdf_panel_U(n, bind)), ('MFF', mff_panel_U)):
        U0, k0 = loader('B0')
        if U0 is None:
            continue
        K0 = centred_gram(U0).astype(np.float64); K0n = float(np.linalg.norm(K0))
        res = {}
        for a in ARMS:
            for s in SEEDS:
                U, k = loader(f'{a}@{s}')
                if U is None:
                    continue
                assert k == k0, f'row mismatch {cohort} {a}@{s}'
                res[f'{a}@{s}'] = change(U, U0, K0, K0n)
        seedmean = {a: {q: float(np.mean([res[f'{a}@{s}'][q] for s in SEEDS])) for q in ('one_minus_cka', 'mean_delta_norm')}
                    for a in ARMS if all(f'{a}@{s}' in res for s in SEEDS)}
        ratios = {}
        for ref in ('cs_pair_noise', 'cs_pair'):
            for s in SEEDS:
                if f'ssl_continue@{s}' in res and f'{ref}@{s}' in res:
                    ratios[f'ssl_continue/{ref}[{s}]'] = {q: res[f'ssl_continue@{s}'][q] / res[f'{ref}@{s}'][q] for q in ('one_minus_cka', 'mean_delta_norm')}
            if 'ssl_continue' in seedmean and ref in seedmean:
                ratios[f'ssl_continue/{ref}[seed_mean]'] = {q: seedmean['ssl_continue'][q] / seedmean[ref][q] for q in ('one_minus_cka', 'mean_delta_norm')}
        flags = {k: {q: v[q] < RULE for q in v} for k, v in ratios.items() if 'cs_pair_noise' in k}
        out[cohort] = {'per_arm_seed': res, 'seed_mean': seedmean, 'ratios': ratios, 'below_0.25_vs_cs_pair_noise': flags,
                       'rows': 'BDF: 64 children x 128 panel rows, own outer-fold features' if cohort == 'BDF' else 'MFF: lane-children panel rows'}
    return {'rule': '12:20: ssl_continue / cs_pair_noise < 0.25 -> an "ssl_continue ≈ B0" outcome is inconclusive (control did not move U)',
            'metrics': {'one_minus_cka': 'requested (coordinator message, ext3)', 'mean_delta_norm': '12:20 entry definition'},
            'cohorts': out}


# ----------------------------------------------------------------------------------------------- main
def main():
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    MARK.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(MARK / 'run.lock', 'a+') as h:
        fcntl.flock(h, fcntl.LOCK_EX)
        digest_now = FL4.mechanism_inputs()
        bind = PF.Binding(); kids = bind.ids
        from . import private_mff_v4 as M
        mb = M.Binding()
        pure = [k['id'] for k in mb.kids if k['lane'] == 'mff_puretone']; bapa = [k['id'] for k in mb.kids if k['lane'] == 'mff_bapa']
        # EXT1 (unchanged P23 functions)
        B1, Mv1 = M1.bdf_values(), M1.mff_values()
        fams1 = M1.families(B1, [('G', 'reported'), ('delta', 'reported'), ('delta_pca64', 'descriptive'), ('auc_EEG_part', 'descriptive')],
                            {ep: kids for ep in ('G', 'delta', 'delta_pca64', 'auc_EEG_part')}, 'BDF')
        if Mv1:
            fams1 += M1.families(Mv1, [('within_G', 'reported'), ('transfer_AUC', 'reported'), ('delta_pure', 'descriptive'),
                                       ('delta_bapa_refit', 'descriptive')],
                                 {'within_G': pure, 'transfer_AUC': bapa, 'delta_pure': pure, 'delta_bapa_refit': bapa}, 'MFF')
        for f in fams1:
            f['block'] = 'EXT1'
        # EXT2 (unchanged P24 functions)
        names2 = ['B0'] + [f'{o}@{s}' for o in ('cs_pair', 'cs_pair_noise') for s in SEEDS]
        B2, Mv2 = M2.bdf_values(names2), M2.mff_values(names2)
        fams2 = M2.ext2_families(B2, M2.BDF_EPS, {ep: kids for ep, _ in M2.BDF_EPS}, 'BDF')
        fams2 += M2.ext2_families(Mv2, M2.MFF_EPS, {'within_G': pure, 'transfer_AUC': bapa}, 'MFF')
        # EXT3
        names3 = ['B0'] + [f'{o}@{s}' for o in ('cs_pair', 'ssl_continue') for s in SEEDS]
        B3, Mv3 = M2.bdf_values(names3), M2.mff_values(names3)
        fams3 = ext_families(B3, M2.BDF_EPS, {ep: kids for ep, _ in M2.BDF_EPS}, 'BDF', 'ssl_continue', 'EXT3')
        fams3 += ext_families(Mv3, M2.MFF_EPS, {'within_G': pure, 'transfer_AUC': bapa}, 'MFF', 'ssl_continue', 'EXT3')
        manip = manipulation(bind)
        exp1 = [f'{o}@{s}' for o in ('cs_pair', 'raw_cs', 'cs_pair_wrong') for s in SEEDS]
        body = {'version': 'DEP12_PRIVATE_MECHANISM_v3', 'time': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID'),
                'inputs_digest': digest_now,
                'encoders_with_results': {'BDF': sorted(set(B1) | set(B2) | set(B3)), 'MFF': sorted(set(Mv1) | set(Mv2) | set(Mv3))},
                'missing': {'EXT1': {'BDF': [n for n in exp1 if n not in B1], 'MFF': [n for n in exp1 if n not in Mv1]},
                            'EXT2': {'BDF': [n for n in names2 if n not in B2], 'MFF': [n for n in names2 if n not in Mv2]},
                            'EXT3': {'BDF': [n for n in names3 if n not in B3], 'MFF': [n for n in names3 if n not in Mv3]}},
                'families': fams1, 'levels': {'BDF': M1.levels(B1), 'MFF': M1.levels(Mv1)},
                'EXT2': {'label': 'follow-up ext2 (DECISIONS 2026-10-23 10:55, P24); designed after the round results; beyond the package budget',
                         'primary': 'BDF U0 all-trials G: cs_pair_noise - B0 and cs_pair - cs_pair_noise, per seed and merged',
                         'families': fams2, 'levels': {'BDF': M1.levels(B2), 'MFF': M1.levels(Mv2)}},
                'EXT3': {'label': 'follow-up ext3 (DECISIONS 2026-10-23 11:55 / 12:20, P25); designed after the round results; beyond the package budget',
                         'primary': 'BDF U0 all-trials G: ssl_continue - B0 and cs_pair - ssl_continue, per seed and merged',
                         'families': fams3, 'levels': {'BDF': M1.levels(B3), 'MFF': M1.levels(Mv3)}},
                'manipulation_check': manip,
                'notes': ['EXT1 = P23 controls; EXT2 / EXT3 = follow-up blocks; single-seed rows are single-seed evidence; never zero-filled',
                          'interpretation rules are the coordinator entries (10:55, 11:55, 12:20); values and the 0.25 flag only here'],
                'code': {str(Path(p).relative_to(PF.ROOT)): sha(p) for p in (Path(__file__), Path(M1.__file__), Path(M2.__file__), Path(PA.__file__),
                                                                              Path(FL4.__file__))}}
        write(M1.OUT_JSON, body)
        write(MANIP_JSON, {'time': body['time'], 'job': body['job'], **manip})
        M1.write_md({**body, 'missing': body['missing']['EXT1']})
        M2.append_ext2_md({**body, 'missing': {'EXT2': body['missing']['EXT2']}})
        M2.write_ext2_md({**body, 'missing': {'EXT2': body['missing']['EXT2']}})
        append_ext3_md(body)
        write_ext3_md(body)
        write(MARK / 'inputs.json', {'digest': digest_now, 'job': os.environ.get('SLURM_JOB_ID'), 'time': body['time']})
        print(json.dumps({'EXT3': [f['family_id'] for f in fams3], 'missing': body['missing'],
                          'manip_cohorts': list(manip['cohorts'])}), flush=True)


def manip_lines(manip):
    f_ = PA.fmt; L = ['', '### Manipulation check: representation change vs B0 on the same panel rows (descriptive)', '',
                      manip['rule'] + '.', '', '| cohort | arm@seed | 1 − linear CKA | mean ‖U − U_B0‖ | rows |', '|---|---|---:|---:|---:|']
    for cohort, d in manip['cohorts'].items():
        for n, v in d['per_arm_seed'].items():
            L.append(f"| {cohort} | {n} | {f_(v['one_minus_cka'], 5)} | {f_(v['mean_delta_norm'], 5)} | {v['n_rows']} |")
    L += ['', '| cohort | ratio | 1 − CKA ratio | ‖ΔU‖ ratio | < 0.25 (1 − CKA / ‖ΔU‖) |', '|---|---|---:|---:|---|']
    for cohort, d in manip['cohorts'].items():
        for k, v in d['ratios'].items():
            fl = d['below_0.25_vs_cs_pair_noise'].get(k)
            L.append(f"| {cohort} | {k} | {f_(v['one_minus_cka'], 3)} | {f_(v['mean_delta_norm'], 3)} | "
                     f"{'NA' if fl is None else str(fl['one_minus_cka']) + ' / ' + str(fl['mean_delta_norm'])} |")
    return L


def append_ext3_md(body):
    e = body['EXT3']
    L = ['', '## Block EXT3 — follow-up (ssl_continue; DECISIONS 2026-10-23 11:55 / 12:20, P25)', '', e['label'] + '.', '',
         'Primary: ' + e['primary'] + '. Everything else descriptive. Missing: ' + json.dumps(body['missing']['EXT3']), '']
    L += M2.ext2_table(e['families']) + M2.levels_table(e['levels']) + manip_lines(body['manipulation_check'])
    with open(M1.OUT_MD, 'a') as fh:
        fh.write('\n'.join(L) + '\n')


def write_ext3_md(body):
    e = body['EXT3']
    prim = [f for f in e['families'] if f['role'] == 'primary']; desc = [f for f in e['families'] if f['role'] != 'primary']
    L = ['# EXT3 private read-outs (follow-up; ssl_continue)', '', f"Generated {body['time']} (job {body['job']}). {e['label']}.", '',
         'Arm ssl_continue = audio-free masked-patch reconstruction continued pre-training (CBraMod style) with the cs_pair LoRA recipe '
         '(S23–S26). Contrasts: ssl_continue − B0 and cs_pair − ssl_continue (positive = first-named higher). Person bootstrap-t, '
         'B = 10,000; simultaneous 95% intervals within each family (cohort × endpoint × seed / merged). Single-seed rows are single-seed '
         'evidence; merged rows average each child over seeds 3401/3407/3413.', '', '**Primary:** ' + e['primary'] + '.', '',
         'Missing encoders: ' + json.dumps(body['missing']['EXT3']), '', '## Primary: BDF U0 G (bits/trial)', '']
    L += M2.ext2_table(prim) + ['', '## Descriptive', ''] + M2.ext2_table(desc) + M2.levels_table(e['levels'])
    L += manip_lines(body['manipulation_check'])
    L += ['', 'Interpretation rules (coordinator 11:55, revised 12:20): ssl_continue ≈ cs_pair (> B0) → domain adaptation suffices; '
          'ssl_continue ≈ B0 → the alignment objective matters beyond source-EEG exposure, unless ssl_continue moved U by less than 25% '
          'of cs_pair_noise, in which case that outcome is an inconclusive control. This file reports values and the flag only.']
    EXT3_MD.write_text('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
