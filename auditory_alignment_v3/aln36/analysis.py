"""ALN3.6 R1 per-person contrasts and the predeclared statistical families (CPU).

Per person: each state's risk is on that person's own query rows; differences are formed per person and source model;
content folds are averaged within person (both required), then the single R1 seed. People are the unit; source models,
content folds, person-fold slices, anchors and trials never add n.
Intervals: auditory_alignment_v3.sci_r1.stats identity bootstrap-t (per-replicate studentisation), B = 4000; within a
family every member of one group shares that group's replicate indices; groups are resampled independently; the family
critical value is the 95th percentile of the max over members of |T*| (simultaneous 95%). The package's fixed-SE
max-|z*| reference (scripts/paired_summary.py) is computed as a secondary column. A family with any expected person missing
for any member is marked incomplete and gets no simultaneous interval; its point values and coverage are still reported.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

import numpy as np

from ..sci_r1 import stats as S
from . import common as C
from . import fau_group as G
from . import private_features as PF
from . import private_readout as PR
from . import public_features as F
from . import public_readout as R

BASE = C.OUT / 'analysis_r1'
RESULTS = C.REPO / 'results/auditory_alignment_v3/aln36/r1'
B_REPLICATES = 4000
SEED = 361020
EST = {'G0': 'shared_EEG_gain', 'DT': 'time_increment', 'GC': 'personal_calibrated_EEG_gain', 'GT': 'personal_EEG_gain',
       'J': 'double_difference', 'GH': 'history_calibration_gain'}
SHARED_TIME, MECHANISM = ('G0', 'DT'), ('GC', 'GT', 'J', 'GH')


def group_seed(*parts):
    return SEED + int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:8], 16) % 100000


def person_value(record, key):
    if record.get('status') != 'complete':
        return None
    return float(record['evaluation']['estimands'][key])


def public_tables():
    """{(panel, tool, group): {person: {estimand: [values per content fold]}}} plus coverage of evaluation cells."""
    plan = C.read(F.PLAN); out, cells, statuses = {}, {}, {}
    for row in plan['rows']:
        path = R.BASE / 'units' / f'{row["id"]}.json'
        if not path.exists():
            continue
        rec = C.read(path)
        if row['kind'] == 'whole_group':
            panel, tool = 'fau_group', row['tool']
        else:
            panel, tool = f'{row["dataset"]}_pooled', row['tool']
        for pid, pr in rec['people'].items():
            group = row['excluded_group'] if panel == 'fau_group' else (pr['group'] if panel == 'fau_pooled' else 'all')
            slot = out.setdefault((panel, tool, group), {}).setdefault(pid, {})
            statuses.setdefault((panel, tool, group), []).append(pr['status'])
            for name, key in EST.items():
                slot.setdefault(name, []).append(person_value(pr, key))
            m0 = pr['M0'].get('M0_minus_E0')
            slot.setdefault('M0', []).append(m0)
            slot.setdefault('_cf', []).append(row['content_fold'])
            if panel == 'fau_group':
                cell = (tool, row['excluded_group'], row['content_fold'], pr['person_fold'])
                cells.setdefault(cell, set()).add(pid)
    return out, cells, statuses


def private_tables():
    plan = C.read(PF.PLAN); out = {}
    for row in plan['rows'] + plan['optional_S']:
        path = PR.BASE / 'units' / f'{row["id"]}.json'
        if not path.exists():
            continue
        rec = C.read(path)
        for cid, pr in rec['people'].items():
            slot = out.setdefault(row['arm'], {}).setdefault(cid, {'group': pr['group']})
            for name, key in EST.items():
                slot[name] = person_value(pr, key)
            tw = pr.get('twin', {}); ctl = tw.get('controls', {})
            slot['twin_E0'] = tw['E0_twin'] - tw['E0_real'] if 'E0_twin' in tw else None
            ok = all('risk' in ctl.get(k, {}) for k in ('real_control', 'twin_control'))
            slot['twin_ET'] = ctl['twin_control']['risk']['ET'] - ctl['real_control']['risk']['ET'] if ok else None
            slot['status'] = pr['status']
    return out


def mean_cf(values, need=2):
    v = [x for x in values if x is not None]
    return float(np.mean(v)) if len(v) == need and len(values) == need else None


def family(fid, unit, members, expected):
    """members: [{name, group, values: {person: value or None}}]; expected: {group: [people]}."""
    rows, incomplete = [], False
    coverage = {}
    for g, people in expected.items():
        names = [m for m in members if m['group'] == g]
        complete = [p for p in people if all(m['values'].get(p) is not None for m in names)]
        coverage[g] = {'expected_n': len(people), 'complete_n': len(complete), 'missing': [p for p in people if p not in complete]}
        incomplete |= len(complete) != len(people)
    idx = {g: S.draws(coverage[g]['complete_n'], B_REPLICATES, group_seed(fid, g)) if coverage[g]['complete_n'] else None
           for g in expected}
    items, pkg_rows = {}, []
    for m in members:
        g = m['group']; people = [p for p in expected[g] if p not in coverage[g]['missing']]
        y = np.array([m['values'][p] for p in people])
        rec = {'name': m['name'], 'group': g, 'n': len(y), 'identity_values': dict(zip(people, map(float, y)))}
        if len(y) >= 3:
            s = S.summary(y, idx=idx[g])
            rec.update(estimate=float(s['est']), se=float(s['se']), pointwise_95=[float(s['ci_low']), float(s['ci_high'])],
                       percentile_95=[float(s['pct_low']), float(s['pct_high'])])
            if s['se'] > 1e-15:
                items[m['name']] = (s['est'], s['se'], s['T'])
            else:
                rec['status'] = 'nonregular_zero_variance'
        else:
            rec['status'] = 'fewer_than_3_people'
        rows.append(rec)
        for p in people:
            pkg_rows.append({'person_id': p, 'group': g, 'seed': C.SEED, 'repeat': '0', 'contrast': m['name'], 'value': float(m['values'][p])})
    fam = S.family_maxt(items)
    for rec in rows:
        if fam and rec['name'] in fam['intervals'] and not incomplete:
            iv = fam['intervals'][rec['name']]; rec['simultaneous_95'] = [iv['sim_low'], iv['sim_high']]
        else:
            rec['simultaneous_95'] = None
    reference = None
    try:
        spec = importlib.util.spec_from_file_location('paired_summary', C.PACKAGE / 'scripts/paired_summary.py')
        ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
        reference = ps.summarize_family({'family_id': fid, 'unit': unit, 'expected_people': {g: [p for p in expected[g] if p not in coverage[g]['missing']] for g in expected},
                                         'required_seeds': [C.SEED], 'required_repeats': ['0'],
                                         'contrasts': [{'name': m['name'], 'group': m['group']} for m in members], 'rows': pkg_rows},
                                        B=B_REPLICATES, seed=SEED)
        reference = {'method': reference['method'], 'critical': reference['critical'], 'status': reference['status'],
                     'intervals': {c['name']: c['simultaneous_95'] for c in reference['contrasts']}}
    except Exception as exc:  # the secondary reference never blocks the primary family
        reference = {'error': repr(exc)}
    return {'family_id': fid, 'unit': unit, 'status': 'incomplete_no_intervals' if incomplete else 'complete',
            'method': 'sci_r1 identity bootstrap-t, family max-|T*| simultaneous 95%', 'B': B_REPLICATES, 'seed': SEED,
            'critical': fam['crit'] if fam else None, 'coverage': coverage, 'members': rows,
            'secondary_reference_fixed_se_max_z': reference, 'conditional_on_fitted_models': True}


def build():
    pub, cells, statuses = public_tables(); priv = private_tables()
    families, per_person = [], []
    fau_expected = {g: C.read(G.BINDINGS / f'{g}_cf0.json')['target_ids'] for g in C.GROUPS}
    for g in C.GROUPS:
        assert fau_expected[g] == C.read(G.BINDINGS / f'{g}_cf1.json')['target_ids']

    def values(panel, tool, group, name):
        table = pub.get((panel, tool, group), {})
        return {p: mean_cf(v[name]) for p, v in table.items()}

    for fid, names, unit in (('F_FAU_GROUP_SHARED_TIME', SHARED_TIME, 'source-scaled envelope MSE'),
                             ('F_FAU_MECHANISM', MECHANISM, 'source-scaled envelope MSE'),
                             ('F_FAU_ALIGNMENT', ('M0',), 'source-scaled envelope MSE')):
        members = [{'name': f'{tool}/{g}/{n}', 'group': g, 'values': values('fau_group', tool, g, n)}
                   for tool in C.TOOLS for g in C.GROUPS for n in names]
        families.append(family(fid, unit, members, fau_expected))
    dtu_people = sorted({p for tool in C.TOOLS for p in pub.get(('dtu_pooled', tool, 'all'), {})})
    for fid, names in (('F_DTU_SHARED_TIME', SHARED_TIME), ('F_DTU_MECHANISM', MECHANISM), ('F_DTU_ALIGNMENT', ('M0',))):
        members = [{'name': f'{tool}/{n}', 'group': 'all', 'values': values('dtu_pooled', tool, 'all', n)} for tool in C.TOOLS for n in names]
        families.append(family(fid, 'source-scaled envelope MSE', members, {'all': dtu_people}))
    pooled = {}
    for g in C.GROUPS:
        for tool in C.TOOLS:
            for n in SHARED_TIME + ('M0',):
                v = {p: x for p, x in values('fau_pooled', tool, g, n).items() if x is not None}
                if len(v) >= 3:
                    s = S.summary(np.array(list(v.values())), seed=group_seed('fau_pooled', tool, g, n))
                    pooled[f'{tool}/{g}/{n}'] = {'n': len(v), 'estimate': float(s['est']), 'pointwise_95': [float(s['ci_low']), float(s['ci_high'])]}
    children = sorted({c for arm in ('AP', 'APwrong') for c in priv.get(arm, {})})
    ap, apw = priv.get('AP', {}), priv.get('APwrong', {})
    shared = [{'name': f'{arm}/{n}', 'group': 'all', 'values': {c: priv.get(arm, {}).get(c, {}).get(n) for c in children}}
              for arm in ('AP', 'APwrong') for n in SHARED_TIME]
    for n in SHARED_TIME:
        shared.append({'name': f'AP-APwrong/{n}', 'group': 'all',
                       'values': {c: (ap[c][n] - apw[c][n]) if c in ap and c in apw and ap[c].get(n) is not None and apw[c].get(n) is not None else None
                                  for c in children}})
    families.append(family('F_PRIVATE_SHARED_TIME', 'bits/trial', shared, {'all': children}))
    families.append(family('F_PRIVATE_MECHANISM', 'bits/trial',
                           [{'name': f'{arm}/{n}', 'group': 'all', 'values': {c: priv.get(arm, {}).get(c, {}).get(n) for c in children}}
                            for arm in ('AP', 'APwrong') for n in MECHANISM], {'all': children}))
    families.append(family('F_PRIVATE_CURRENT_CORRESPONDENCE', 'bits/trial',
                           [{'name': f'{arm}/{n}', 'group': 'all', 'values': {c: priv.get(arm, {}).get(c, {}).get(n) for c in children}}
                            for arm in ('AP', 'APwrong') for n in ('twin_E0', 'twin_ET')], {'all': children}))
    s_ref = {}
    for n in SHARED_TIME + MECHANISM:
        v = {c: x[n] for c, x in priv.get('S', {}).items() if x.get(n) is not None}
        if len(v) >= 3:
            s = S.summary(np.array(list(v.values())), seed=group_seed('S', n))
            s_ref[n] = {'n': len(v), 'estimate': float(s['est']), 'pointwise_95': [float(s['ci_low']), float(s['ci_high'])]}
    for (panel, tool, group), table in pub.items():
        for p, v in table.items():
            per_person.append({'panel': panel, 'tool': tool, 'group': group, 'person': p,
                               **{n: mean_cf(v[n]) for n in tuple(EST) + ('M0',)}})
    for arm, table in priv.items():
        for c, v in table.items():
            per_person.append({'panel': 'private', 'tool': arm, 'group': v['group'], 'person': c,
                               **{n: v.get(n) for n in tuple(EST) + ('twin_E0', 'twin_ET')}})
    cell_cov = {f'{t}/{g}/cf{cf}/pf{pf}': len(v) for (t, g, cf, pf), v in sorted(cells.items())}
    status_counts = {f'{k[0]}/{k[1]}/{k[2]}': {s: v.count(s) for s in set(v)} for k, v in statuses.items()}
    return {'version': 'ALN36_R1_ANALYSIS_v1', 'analysis_origin': C.ORIGIN, 'families': families, 'fau_pooled_descriptive': pooled,
            'private_S_reference_descriptive': s_ref, 'fau_group_evaluation_cells': cell_cov, 'n_fau_group_cells': len(cell_cov),
            'readout_status_counts': status_counts, 'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'job': os.environ.get('SLURM_JOB_ID')}, per_person


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--tag', default='latest')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    summary, per_person = build()
    out = RESULTS / a.tag; out.mkdir(parents=True, exist_ok=True)
    C.write(out / 'summary.json', summary)
    keys = ['panel', 'tool', 'group', 'person'] + list(EST) + ['M0', 'twin_E0', 'twin_ET']
    with open(out / 'per_person.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator='\n'); w.writeheader()
        for r in per_person:
            w.writerow({k: r.get(k) for k in keys})
    print(json.dumps({'families': {f['family_id']: f['status'] for f in summary['families']}, 'cells': summary['n_fau_group_cells']}), flush=True)


if __name__ == '__main__':
    main()
