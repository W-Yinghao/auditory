"""DEP12 Agent P: private mechanism-control report, version 2 (DECISIONS P24). Block EXT1 is the P23 report, computed by the
unchanged private_mechanism functions (cs_pair - raw_cs, cs_pair - cs_pair_wrong). Block EXT2 is the coordinator's
follow-up ext2 (DECISIONS 2026-10-23 10:55): arm cs_pair_noise (cs_pair recipe with i.i.d. Gaussian targets).

EXT2 members per seed s and merged (child mean over 3401 / 3407 / 3413; a child needs all three seeds):
  cs_pair_noise@s - B0 and cs_pair@s - cs_pair_noise@s (B0 is seed-free).
Primary (fixed at 10:55): BDF U0 all-trials G (bits/trial). Descriptive: BDF n128 δ excess (U kernel), PCA64-kernel δ,
EEG-part AUC; MFF within-pure-tone G and transfer (pure tone -> bapa) EEG-part AUC. One family per cohort x endpoint x seed /
merged; B = 10,000; family max-|T*| simultaneous intervals (aln41.analysis.family via private_analysis.family).
Outputs: results/.../dep12/private_mechanism_controls.{json,md} (EXT1 unchanged + block EXT2, labelled follow-up) and
results/.../dep12/EXT2_PRIVATE.md; marker REC/mechanism_v2/inputs.json.
"""
from __future__ import annotations

from datetime import datetime
import fcntl
import json
import os
from pathlib import Path

from . import private_features as PF
from . import private_analysis as PA
from . import private_mechanism as M1
from . import private_fleet_v3 as FL3

SEEDS = (3401, 3407, 3413)
MARK = PF.REC / 'mechanism_v2'
EXT2_MD = PF.RESULTS / 'EXT2_PRIVATE.md'
read, write, sha = PF.read, PF.write, PF.sha
BDF_EPS = [('G', 'primary'), ('delta', 'descriptive'), ('delta_pca64', 'descriptive'), ('auc_EEG_part', 'descriptive')]
MFF_EPS = [('within_G', 'descriptive'), ('transfer_AUC', 'descriptive')]


def bdf_values(names):
    out = {}
    for n in names:
        folds = PA.use_rows(n)
        if folds is None:
            continue
        out[n] = {'G': PA.u0_map(folds), 'delta': PA.profile_map(folds), 'delta_pca64': PA.profile_map(folds, 'pca64_n128_x1'),
                  'auc_EEG_part': PA.u0_map(folds, key='auc_EEG_part')}
    return out


def mff_values(names):
    from . import private_mff_v3 as M
    out = {}
    for n in names:
        p = M.BASE / 'use' / (n.replace('@', '_at_') + '.json')
        if p.exists():
            r = read(p)
            out[n] = {'within_G': M.child_values(r, ('within',), 'G_bits'), 'transfer_AUC': M.child_values(r, ('transfer',), 'auc_EEG_part')}
    return out


def ext2_families(V, endpoints, people, cohort):
    fams = []
    for ep, role in endpoints:
        for s in SEEDS:
            noise, cs = f'cs_pair_noise@{s}', f'cs_pair@{s}'
            mem = []
            if noise in V and 'B0' in V:
                mem.append(('cs_pair_noise-B0', PA.diff(V[noise][ep], V['B0'][ep])))
            if cs in V and noise in V:
                mem.append(('cs_pair-cs_pair_noise', PA.diff(V[cs][ep], V[noise][ep])))
            if mem:
                f = PA.family(f'EXT2:{cohort}:{ep}[{s}]', f'{ep} ({role}; follow-up ext2)', mem, people[ep])
                f.update(seed=s, role=role, block='EXT2'); fams.append(f)
        if 'B0' in V and all(f'cs_pair_noise@{s}' in V and f'cs_pair@{s}' in V for s in SEEDS):
            mem = [('cs_pair_noise-B0', PA.mean_over([PA.diff(V[f'cs_pair_noise@{s}'][ep], V['B0'][ep]) for s in SEEDS])),
                   ('cs_pair-cs_pair_noise', PA.mean_over([PA.diff(V[f'cs_pair@{s}'][ep], V[f'cs_pair_noise@{s}'][ep]) for s in SEEDS]))]
            f = PA.family(f'EXT2:{cohort}:{ep}[merged]', f'{ep} ({role}; follow-up ext2); child mean over seeds 3401/3407/3413', mem, people[ep])
            f.update(seed='merged', role=role, block='EXT2'); fams.append(f)
    return fams


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    MARK.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(MARK / 'run.lock', 'a+') as h:
        fcntl.flock(h, fcntl.LOCK_EX)
        digest_now = FL3.mechanism_inputs()
        bind = PF.Binding(); kids = bind.ids
        # ---- block EXT1: the unchanged P23 report
        B1 = M1.bdf_values(); Mv1 = M1.mff_values()        # private_mff_v2 / v3 share the MFF use directory
        fams1 = M1.families(B1, [('G', 'reported'), ('delta', 'reported'), ('delta_pca64', 'descriptive'), ('auc_EEG_part', 'descriptive')],
                            {ep: kids for ep in ('G', 'delta', 'delta_pca64', 'auc_EEG_part')}, 'BDF')
        from . import private_mff_v3 as M
        mb = M.Binding()
        pure = [k['id'] for k in mb.kids if k['lane'] == 'mff_puretone']; bapa = [k['id'] for k in mb.kids if k['lane'] == 'mff_bapa']
        if Mv1:
            fams1 += M1.families(Mv1, [('within_G', 'reported'), ('transfer_AUC', 'reported'), ('delta_pure', 'descriptive'),
                                       ('delta_bapa_refit', 'descriptive')],
                                 {'within_G': pure, 'transfer_AUC': bapa, 'delta_pure': pure, 'delta_bapa_refit': bapa}, 'MFF')
        for f in fams1:
            f['block'] = 'EXT1'
        # ---- block EXT2
        names2 = ['B0'] + [f'{o}@{s}' for o in ('cs_pair', 'cs_pair_noise') for s in SEEDS]
        B2, Mv2 = bdf_values(names2), mff_values(names2)
        fams2 = ext2_families(B2, BDF_EPS, {ep: kids for ep, _ in BDF_EPS}, 'BDF')
        fams2 += ext2_families(Mv2, MFF_EPS, {'within_G': pure, 'transfer_AUC': bapa}, 'MFF')
        exp1 = [f'{o}@{s}' for o in ('cs_pair', 'raw_cs', 'cs_pair_wrong') for s in SEEDS]
        body = {'version': 'DEP12_PRIVATE_MECHANISM_v2', 'time': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID'),
                'inputs_digest': digest_now,
                'encoders_with_results': {'BDF': sorted(set(B1) | set(B2)), 'MFF': sorted(set(Mv1) | set(Mv2))},
                'missing': {'EXT1': {'BDF': [n for n in exp1 if n not in B1], 'MFF': [n for n in exp1 if n not in Mv1]},
                            'EXT2': {'BDF': [n for n in names2 if n not in B2], 'MFF': [n for n in names2 if n not in Mv2]}},
                'families': fams1, 'levels': {'BDF': M1.levels(B1), 'MFF': M1.levels(Mv1)},
                'EXT2': {'label': 'follow-up ext2 (DECISIONS 2026-10-23 10:55, P24); designed after the round results; beyond the package budget',
                         'primary': 'BDF U0 all-trials G: cs_pair_noise - B0 and cs_pair - cs_pair_noise, per seed and merged',
                         'families': fams2, 'levels': {'BDF': M1.levels(B2), 'MFF': M1.levels(Mv2)}},
                'notes': ['EXT1 = P23 mechanism controls, unchanged definitions; EXT2 = follow-up block',
                          'single-seed rows are single-seed evidence; merged rows use children with all three seeds; never zero-filled',
                          'interpretation rule for EXT2 is the coordinator entry of 10:55; values only here'],
                'code': {str(Path(p).relative_to(PF.ROOT)): sha(p) for p in (Path(__file__), Path(M1.__file__), Path(PA.__file__), Path(FL3.__file__))}}
        write(M1.OUT_JSON, body)
        M1.write_md({**body, 'missing': body['missing']['EXT1']})
        append_ext2_md(body)
        write_ext2_md(body)
        write(MARK / 'inputs.json', {'digest': digest_now, 'job': os.environ.get('SLURM_JOB_ID'), 'time': body['time']})
        print(json.dumps({'EXT1': [f['family_id'] for f in fams1], 'EXT2': [f['family_id'] for f in fams2], 'missing': body['missing']}), flush=True)


def ext2_table(fams):
    f_ = PA.fmt
    L = ['| family | role | member | n | estimate | pointwise 95% | simultaneous 95% |', '|---|---|---|---:|---:|---|---|']
    for fam in fams:
        for m in fam['members']:
            pw, sm = m.get('pointwise_95'), m.get('simultaneous_95')
            L.append(f"| {fam['family_id']} | {fam['role']} | {m['name']} | {m['n']} | {f_(m.get('estimate'), 6)} | "
                     f"{('[' + f_(pw[0], 6) + ', ' + f_(pw[1], 6) + ']') if pw else 'NA'} | {('[' + f_(sm[0], 6) + ', ' + f_(sm[1], 6) + ']') if sm else 'NA'} |")
    return L


def levels_table(lv):
    f_ = PA.fmt; L = []
    for cohort, d in lv.items():
        if not d:
            continue
        eps = list(next(iter(d.values())))
        L += ['', f'### {cohort} levels (child means)', '', '| encoder | ' + ' | '.join(eps) + ' |', '|---|' + '---:|' * len(eps)]
        for n, v in d.items():
            L.append(f'| {n} | ' + ' | '.join(f_(v[e]['mean'], 6) for e in eps) + ' |')
    return L


def append_ext2_md(body):
    e = body['EXT2']
    L = ['', '## Block EXT2 — follow-up (cs_pair_noise; DECISIONS 2026-10-23 10:55, P24)', '', e['label'] + '.', '',
         'Primary: ' + e['primary'] + '. Everything else descriptive. Missing: ' + json.dumps(body['missing']['EXT2']), '']
    L += ext2_table(e['families']) + levels_table(e['levels'])
    with open(M1.OUT_MD, 'a') as fh:
        fh.write('\n'.join(L) + '\n')


def write_ext2_md(body):
    e = body['EXT2']
    L = ['# EXT2 private read-outs (follow-up; cs_pair_noise)', '',
         f"Generated {body['time']} (job {body['job']}). {e['label']}.", '',
         'Arm cs_pair_noise = the cs_pair LoRA recipe with i.i.d. unit-Gaussian 32-d targets per view (S20-S22). Contrasts: '
         'cs_pair_noise − B0 and cs_pair − cs_pair_noise (positive = first-named higher). Person bootstrap-t, B = 10,000; simultaneous '
         '95% intervals within each family (one family per cohort × endpoint × seed / merged). Single-seed rows are single-seed evidence; '
         'merged rows average each child over seeds 3401/3407/3413.', '',
         '**Primary:** ' + e['primary'] + '.', '', 'Missing encoders: ' + json.dumps(body['missing']['EXT2']), '']
    prim = [f for f in e['families'] if f['role'] == 'primary']; desc = [f for f in e['families'] if f['role'] != 'primary']
    L += ['## Primary: BDF U0 G (bits/trial)', ''] + ext2_table(prim) + ['', '## Descriptive', ''] + ext2_table(desc)
    L += levels_table(e['levels'])
    L += ['', 'Interpretation rule (coordinator, fixed at 10:55): cs_pair_noise ≈ cs_pair (> B0) → sound-independent training effect; '
          'cs_pair_noise ≈ B0 < cs_pair → the sound kernel structure contributes; otherwise partial. This file reports values only.']
    EXT2_MD.write_text('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
