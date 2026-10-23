"""DEP12 Agent P: mechanism-control report for the private cohorts (DECISIONS P23; supplementary, separate from the registered
F_PRIVATE / F_SELECTION families and from the MFF extension families).

Contrasts (positive = cs_pair higher): cs_pair@s - raw_cs@s (pairing reference vs raw CS) and cs_pair@s - cs_pair_wrong@s
(correct vs wrong positive pairs), for each training seed s in 3401 / 3407 / 3413 that has both arms, and merged = each
child's mean over the three seeds (a child enters only when all three seeds of both arms exist; never zero-filled).
Endpoints:
  BDF (64 children; outer-test children, private_use outputs): U0 all-trials G (bits/trial) and n128 x1 δ excess (U kernel,
      nats) are the reported families; PCA64-kernel δ and the EEG-part AUC are descriptive families.
  MFF (DECISIONS P21): within-pure-tone G and transfer (pure tone -> bapa) EEG-part AUC are the reported families; δ excess of
      pure-tone children (within fits) and bapa children (refit fits) descriptive.
Statistics: aln41.analysis.family with B = 10,000 (private_analysis.family), one family per cohort x endpoint x seed / merged.
Outputs: results/auditory_alignment_v3/dep12/private_mechanism_controls.{json,md}; marker REC/mechanism_v1/inputs.json.
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
from . import private_fleet_v2 as FL2

SEEDS = (3401, 3407, 3413)
CONTROLS = ('raw_cs', 'cs_pair_wrong')
OUT_JSON = PF.RESULTS / 'private_mechanism_controls.json'
OUT_MD = PF.RESULTS / 'private_mechanism_controls.md'
MARK = PF.REC / 'mechanism_v1'
read, write, sha = PF.read, PF.write, PF.sha


def bdf_values():
    out = {}
    for o in ('cs_pair',) + CONTROLS:
        for s in SEEDS:
            n = f'{o}@{s}'
            folds = PA.use_rows(n)
            if folds is None:
                continue
            out[n] = {'G': PA.u0_map(folds), 'delta': PA.profile_map(folds), 'delta_pca64': PA.profile_map(folds, 'pca64_n128_x1'),
                      'auc_EEG_part': PA.u0_map(folds, key='auc_EEG_part')}
    return out


def mff_values():
    from . import private_mff_v2 as M
    out = {}
    for o in ('cs_pair',) + CONTROLS:
        for s in SEEDS:
            n = f'{o}@{s}'
            p = M.BASE / 'use' / (n.replace('@', '_at_') + '.json')
            if not p.exists():
                continue
            r = read(p)
            out[n] = {'within_G': M.child_values(r, ('within',), 'G_bits'), 'transfer_AUC': M.child_values(r, ('transfer',), 'auc_EEG_part'),
                      'delta_pure': M.child_values(r, ('within',), 'profile'), 'delta_bapa_refit': M.child_values(r, ('refit',), 'profile')}
    return out


def families(V, endpoints, people, cohort):
    fams = []
    for ep, role in endpoints:
        for s in SEEDS:
            mem = [(f'cs_pair-{c}', PA.diff(V[f'cs_pair@{s}'][ep], V[f'{c}@{s}'][ep])) for c in CONTROLS
                   if f'cs_pair@{s}' in V and f'{c}@{s}' in V]
            if mem:
                f = PA.family(f'MECH:{cohort}:{ep}[{s}]', f'{ep} ({role})', mem, people[ep])
                f['seed'] = s; fams.append(f)
        mem = []
        for c in CONTROLS:
            if all(f'cs_pair@{s}' in V and f'{c}@{s}' in V for s in SEEDS):
                mem.append((f'cs_pair-{c}', PA.mean_over([PA.diff(V[f'cs_pair@{s}'][ep], V[f'{c}@{s}'][ep]) for s in SEEDS])))
        if mem:
            f = PA.family(f'MECH:{cohort}:{ep}[merged]', f'{ep} ({role}); child mean over seeds 3401/3407/3413', mem, people[ep])
            f['seed'] = 'merged'; fams.append(f)
    return fams


def levels(V):
    return {n: {ep: PA.describe(m) for ep, m in d.items()} for n, d in sorted(V.items())}


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    MARK.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(MARK / 'run.lock', 'a+') as h:
        fcntl.flock(h, fcntl.LOCK_EX)
        digest_now = FL2.mechanism_inputs()
        bind = PF.Binding()
        B = bdf_values()
        kids = bind.ids
        fams = families(B, [('G', 'reported'), ('delta', 'reported'), ('delta_pca64', 'descriptive'), ('auc_EEG_part', 'descriptive')],
                        {ep: kids for ep in ('G', 'delta', 'delta_pca64', 'auc_EEG_part')}, 'BDF')
        Mv = mff_values()
        mff_fams = []
        if Mv:
            from . import private_mff_v2 as M
            mb = M.Binding()
            pure = [k['id'] for k in mb.kids if k['lane'] == 'mff_puretone']; bapa = [k['id'] for k in mb.kids if k['lane'] == 'mff_bapa']
            mff_fams = families(Mv, [('within_G', 'reported'), ('transfer_AUC', 'reported'), ('delta_pure', 'descriptive'),
                                     ('delta_bapa_refit', 'descriptive')],
                                {'within_G': pure, 'transfer_AUC': bapa, 'delta_pure': pure, 'delta_bapa_refit': bapa}, 'MFF')
        have = {'BDF': sorted(B), 'MFF': sorted(Mv)}
        expected = [f'{o}@{s}' for o in ('cs_pair',) + CONTROLS for s in SEEDS]
        body = {'version': 'DEP12_PRIVATE_MECHANISM_v1', 'time': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID'),
                'inputs_digest': digest_now, 'encoders_with_results': have,
                'missing': {k: [n for n in expected if n not in v] for k, v in have.items()},
                'families': fams + mff_fams, 'levels': {'BDF': levels(B), 'MFF': levels(Mv)},
                'notes': ['supplementary mechanism controls (raw_cs, cs_pair_wrong); separate from the registered families',
                          'raw_cs / cs_pair_wrong at 3407 / 3413 are the coordinator extension beyond the package budget (DECISIONS 07:30, P23)',
                          'single-seed rows are labelled single-seed; merged rows use children with all three seeds'],
                'code': {str(Path(p).relative_to(PF.ROOT)): sha(p) for p in (Path(__file__), Path(PA.__file__), Path(FL2.__file__))}}
        write(OUT_JSON, body)
        write_md(body)
        write(MARK / 'inputs.json', {'digest': digest_now, 'job': os.environ.get('SLURM_JOB_ID'), 'time': body['time']})
        print(json.dumps({'families': [f['family_id'] for f in body['families']], 'missing': body['missing']}), flush=True)


def write_md(body):
    f_ = PA.fmt
    L = ['# DEP12 private mechanism controls (supplementary; DECISIONS P23)', '',
         f"Generated {body['time']}. Contrasts are cs_pair − control (positive = cs_pair higher). Person bootstrap-t, B = 10,000; "
         'simultaneous intervals within each family (one family per cohort × endpoint × seed / merged). Single-seed rows are single-seed '
         'evidence; merged rows average each child over seeds 3401/3407/3413.', '',
         f"Missing encoders: {body['missing']}", '',
         '| family | member | n | estimate | pointwise 95% | simultaneous 95% |', '|---|---|---:|---:|---|---|']
    for fam in body['families']:
        for m in fam['members']:
            pw, sm = m.get('pointwise_95'), m.get('simultaneous_95')
            L.append(f"| {fam['family_id']} | {m['name']} | {m['n']} | {f_(m.get('estimate'), 6)} | "
                     f"{('[' + f_(pw[0], 6) + ', ' + f_(pw[1], 6) + ']') if pw else 'NA'} | {('[' + f_(sm[0], 6) + ', ' + f_(sm[1], 6) + ']') if sm else 'NA'} |")
    for cohort, lv in body['levels'].items():
        if not lv:
            continue
        eps = list(next(iter(lv.values())))
        L += ['', f'## {cohort} levels (child means)', '', '| encoder | ' + ' | '.join(eps) + ' |', '|---|' + '---:|' * len(eps)]
        for n, d in lv.items():
            L.append(f'| {n} | ' + ' | '.join(f_(d[e]['mean'], 6) for e in eps) + ' |')
    OUT_MD.write_text('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
