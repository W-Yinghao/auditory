"""ALN4.1 R1 per-person endpoints and cohort-bound families (CPU).

Units: independent people. Public values are averaged over the two content folds (each person is an outer test person
once per content fold); private values come from the child's outer fold. R1 has one seed (exploratory).
Families (package docs/06, bound per cohort):
  F_CONTENT:{DTU,FAU,PRIVATE}  history-conditional envelope readout r (q0 mixture) / private history increment (bits/trial)
                               for TCS-B0, TCS-TNCE, TCS-GCS, TCS-TCS_WRONG (positive = TCS better)
  F_TIME:{DTU,FAU,PRIVATE}     W0->W2 fixed-readout loss (positive = TCS loses less: other - TCS) and target-window refit
                               recovery (TCS - other), same four comparisons; public on the history-conditional envelope r,
                               private on current-class AUC
  F_UTILITY:PRIVATE            CE full-FT test AUC (selected checkpoint, q mixture) TCS-B0, TCS-TNCE; frozen age absolute
                               error (other - TCS) for B0 and TNCE, and each core arm vs the raw-EEG ridge and the train mean
  F_UTILITY:{DTU,FAU}          20 s attention accuracy (q0 mixture) TCS-B0, TCS-TNCE
Intervals: sci_r1.stats identity bootstrap-t, B = 4000, family max-|T*|; a family whose members do not all have every
expected person is marked incomplete (no simultaneous interval). F_ASSOC (metadata regressions) is reported separately.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from .. import core
from ..sci_r1 import stats as S
from . import frozen as FZ, private_ft as PF, readout as RO, source as SRC

RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/aln41/r1'
B_REP, SEED = 4000, 410021
OTHERS = ('B0', 'TNCE', 'GCS', 'TCS_WRONG')
read, write = SRC.read, SRC.write


def gseed(*parts):
    return SEED + int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:8], 16) % 100000


def public_values():
    """{(dataset, arm): {person: {endpoint: value}}} averaged over content folds (both required)."""
    plan = read(FZ.BASE / 'plan.json'); acc = {}
    for row in plan['rows']:
        if row['dataset'] == 'private_bdf':
            continue
        p = RO.BASE / 'units' / f'{row["id"]}.json'
        if not p.exists():
            continue
        for pid, r in read(p)['people'].items():
            PEOPLE_GROUP[(row['dataset'], pid)] = r.get('group')
            h = r.get('env/history_conditional'); d = r.get('env/direct'); att = r.get('attention', {}).get('q0', {}).get('20')
            vals = {'content_r': h and h['mixture_q0_r'], 'content_direct_r': d and d['mixture_q0_r'],
                    'time_fixed_loss': h and h['W0_to_W2_fixed_loss'], 'time_refit_recovery': h and h['W0_to_W2_refit_recovery'],
                    'attention20_acc': att and att['accuracy']}
            acc.setdefault((row['dataset'], row['arm']), {}).setdefault(pid, {}).setdefault(row['content_fold'], vals)
    out = {}
    for key, people in acc.items():
        for pid, by_cf in people.items():
            if sorted(by_cf) != [0, 1]:
                continue
            out.setdefault(key, {})[pid] = {e: (float(np.mean([by_cf[c][e] for c in (0, 1)])) if all(by_cf[c][e] is not None for c in (0, 1)) else None)
                                            for e in by_cf[0]}
    return out


def private_values():
    plan = read(FZ.BASE / 'plan.json'); out = {}
    for row in plan['rows']:
        if row['dataset'] != 'private_bdf':
            continue
        p = RO.BASE / 'units' / f'{row["id"]}.json'
        if not p.exists():
            continue
        for cid, r in read(p)['people'].items():
            out.setdefault(row['arm'], {})[cid] = {'content_hist_bits': r['history_increment_bits_q0'], 'time_fixed_loss': r['W0_to_W2_fixed_loss_auc'],
                                                    'time_refit_recovery': r['W0_to_W2_refit_recovery_auc'], 'current_auc': r['current_auc_mixture_q0'],
                                                    'twin_bits': r['strict_twin'].get('EEG_minus_twin_bits_q0'), 'group': r['group']}
    fplan = read(PF.BASE / 'plan.json')
    for row in fplan['rows']:
        p = PF.BASE / 'units' / f'{row["id"]}.json'
        if not p.exists():
            continue
        for cid, r in read(p)['test']['selected'].items():
            out.setdefault(row['arm'], {}).setdefault(cid, {})['ft_auc'] = r['mixture']['auc']
    age = SRC.OUT / 'age_v1/age_results.json'
    if age.exists():
        a = read(age)
        for arm, res in list(a['arms'].items()) + [('RAW', a['raw_eeg_logvar'])]:
            for c in res.get('children', []):
                out.setdefault(arm, {}).setdefault(c['id'], {}).update(age_abs_err=c['model_absolute_error_months'],
                                                                        mean_abs_err=c['train_mean_absolute_error_months'])
    return out


def family(fid, unit, members, people):
    """members: [(name, {person: value or None})]; one group of people resampled jointly."""
    complete = [p for p in people if all(v.get(p) is not None for _, v in members)]
    incomplete = len(complete) != len(people)
    idx = S.draws(len(complete), B_REP, gseed(fid)) if len(complete) >= 3 else None
    items, rows = {}, []
    for name, v in members:
        y = np.array([v[p] for p in complete], float)
        rec = {'name': name, 'n': len(y), 'n_available': sum(v.get(p) is not None for p in people)}
        if idx is not None:
            s = S.summary(y, idx=idx)
            rec.update(estimate=float(s['est']), se=float(s['se']), pointwise_95=[float(s['ci_low']), float(s['ci_high'])])
            if s['se'] > 1e-15:
                items[name] = (s['est'], s['se'], s['T'])
        rows.append(rec)
    fam = S.family_maxt(items) if items else None
    for r in rows:
        iv = fam['intervals'].get(r['name']) if fam else None
        r['simultaneous_95'] = [iv['sim_low'], iv['sim_high']] if iv and not incomplete else None
    return {'family_id': fid, 'unit': unit, 'status': 'incomplete_no_intervals' if incomplete else 'complete',
            'expected_n': len(people), 'complete_n': len(complete), 'critical': fam['crit'] if fam else None,
            'method': 'sci_r1 identity bootstrap-t B=4000, family max-|T*|; single seed 3401 (exploratory R1)', 'members': rows}


ASSOC_ENDPOINTS = {'private': ('content_hist_bits', 'time_fixed_loss', 'time_refit_recovery'),
                   'public': ('content_r', 'time_fixed_loss', 'time_refit_recovery')}


def assoc(pub, priv):
    """F_ASSOC: person-level method differences (TCS-B0, TCS-TNCE) on the predeclared endpoints.
    Private: OLS on age(years)+HA indicator (all children) and age+device duration (HA only), person bootstrap refits
    (sci_r1.stats.ols); public: direct group-difference contrasts (FAU HA-CI, HA-TH, CI-TH; DTU HI-NH). One family max-|T*|
    over all private coefficients of age/HA/duration; group contrasts reported with pointwise bootstrap-t intervals."""
    from auditory_alignment import data
    out = {'private': {}, 'public': {}}
    kids = {k['id']: k for k in data.load_private()}
    T = priv.get('TCS', {}); items = {}
    for other in ('B0', 'TNCE'):
        O = priv.get(other, {})
        for ep in ASSOC_ENDPOINTS['private']:
            d = {c: T[c][ep] - O[c][ep] for c in T if c in O and T[c].get(ep) is not None and O[c].get(ep) is not None}
            ids = sorted(d)
            for model, sel in (('age+HA', ids), ('age+duration (HA only)', [c for c in ids if kids[c]['group'] == 'HA'])):
                X = []
                for c in sel:
                    k = kids[c]; age = k.get('age_months')
                    if age is None:
                        continue
                    if model == 'age+HA':
                        X.append((c, [age / 12.0, 1.0 if k['group'] == 'HA' else 0.0]))
                    elif k.get('duration_months') is not None:
                        X.append((c, [age / 12.0, k['duration_months'] / 12.0]))
                names = ['age_years', 'HA'] if model == 'age+HA' else ['age_years', 'duration_years']
                if len(X) < 8:
                    out['private'][f'TCS-{other}/{ep}/{model}'] = {'status': 'too_few', 'n': len(X)}; continue
                res = S.ols(np.array([x for _, x in X]), np.array([d[c] for c, _ in X]), names, seed=gseed('assoc', other, ep, model))
                key = f'TCS-{other}/{ep}/{model}'
                out['private'][key] = {k: v for k, v in res.items() if k != 'T'}
                for nm in names:
                    items[f'{key}/{nm}'] = (res['coef'][nm]['est'], res['coef'][nm]['se'], res['T'][nm])
    fam = S.family_maxt(items) if items else None
    out['private_family'] = fam and {'critical': fam['crit'], 'n_members': fam['n_members'], 'intervals': fam['intervals']}
    pairs = {'fau': (('ha', 'ci'), ('ha', 'th'), ('ci', 'th')), 'dtu': (('hi', 'nh'),)}
    for ds, prs in pairs.items():
        groups = None
        for other in ('B0', 'TNCE'):
            A, O = pub.get((ds, 'TCS'), {}), pub.get((ds, other), {})
            for ep in ASSOC_ENDPOINTS['public']:
                d = {p: A[p][ep] - O[p][ep] for p in A if p in O and A[p].get(ep) is not None and O[p].get(ep) is not None}
                for ga, gb in prs:
                    ya = np.array([v for p, v in d.items() if PEOPLE_GROUP.get((ds, p)) == ga])
                    yb = np.array([v for p, v in d.items() if PEOPLE_GROUP.get((ds, p)) == gb])
                    r = S.contrast(ya, yb, seed=gseed('grp', ds, other, ep, ga, gb))
                    out['public'][f'{ds}/TCS-{other}/{ep}/{ga}-{gb}'] = {k: (float(v) if np.ndim(v) == 0 else None) for k, v in r.items()
                                                                       if k in ('est', 'se', 'ci_low', 'ci_high', 'n_a', 'n_b', 'note')}
    return out


PEOPLE_GROUP = {}


def diff(a, b, key, sign=1):
    return {p: (sign * (a[p][key] - b[p][key]) if p in b and a[p].get(key) is not None and b[p].get(key) is not None else None) for p in a}


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    pub, priv = public_values(), private_values()
    fams = []
    for ds, label in (('dtu', 'DTU'), ('fau', 'FAU')):
        arms = {a: pub.get((ds, a), {}) for a in ('TCS',) + OTHERS}
        people = sorted(set().union(*[set(v) for v in arms.values()])) if any(arms.values()) else []
        if not arms['TCS']:
            continue
        fams.append(family(f'F_CONTENT:{label}', 'history-conditional envelope r', [(f'TCS-{o}', diff(arms['TCS'], arms[o], 'content_r')) for o in OTHERS], people))
        fams.append(family(f'F_TIME:{label}', 'r', [(f'fixed_loss:{o}-TCS', diff(arms['TCS'], arms[o], 'time_fixed_loss', -1)) for o in OTHERS]
                           + [(f'refit_recovery:TCS-{o}', diff(arms['TCS'], arms[o], 'time_refit_recovery')) for o in OTHERS], people))
        fams.append(family(f'F_UTILITY:{label}', 'attention accuracy (20 s)', [(f'TCS-{o}', diff(arms['TCS'], arms[o], 'attention20_acc')) for o in ('B0', 'TNCE')], people))
    if priv.get('TCS'):
        kids = sorted(set().union(*[set(v) for v in priv.values()]))
        T = priv['TCS']
        fams.append(family('F_CONTENT:PRIVATE', 'bits/trial', [(f'TCS-{o}', diff(T, priv.get(o, {}), 'content_hist_bits')) for o in OTHERS], kids))
        fams.append(family('F_TIME:PRIVATE', 'AUC', [(f'fixed_loss:{o}-TCS', diff(T, priv.get(o, {}), 'time_fixed_loss', -1)) for o in OTHERS]
                           + [(f'refit_recovery:TCS-{o}', diff(T, priv.get(o, {}), 'time_refit_recovery')) for o in OTHERS], kids))
        util = [(f'ft_auc:TCS-{o}', diff(T, priv.get(o, {}), 'ft_auc')) for o in ('B0', 'TNCE')]
        util += [(f'age_abs_err:{o}-TCS', diff(T, priv.get(o, {}), 'age_abs_err', -1)) for o in ('B0', 'TNCE')]
        for arm in ('B0', 'TCS', 'TNCE'):
            A = priv.get(arm, {})
            util.append((f'age_abs_err:RAW-{arm}', {p: (priv['RAW'][p]['age_abs_err'] - A[p]['age_abs_err']) if p in priv.get('RAW', {}) and A.get(p, {}).get('age_abs_err') is not None else None for p in kids}))
            util.append((f'age_abs_err:MEAN-{arm}', {p: (A[p]['mean_abs_err'] - A[p]['age_abs_err']) if A.get(p, {}).get('age_abs_err') is not None else None for p in kids}))
        age_kids = [p for p in kids if priv.get('B0', {}).get(p, {}).get('age_abs_err') is not None] or kids
        fams.append(family('F_UTILITY:PRIVATE', 'AUC / months', util, age_kids))
    RESULTS.mkdir(parents=True, exist_ok=True)
    write(RESULTS / 'contrasts.json', {'version': 'ALN41_R1_ANALYSIS_v1', 'families': fams, 'seed': SRC.SEED, 'F_ASSOC': assoc(pub, priv),
                                       'note': 'exploratory single-seed R1; people are the unit; content folds averaged within person'})
    keys = sorted({k for d in list(pub.values()) + list(priv.values()) for v in d.values() for k in v})
    with open(RESULTS / 'person_results.csv', 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(['cohort', 'arm', 'person'] + keys)
        for (ds, arm), people in sorted(pub.items()):
            for p, v in sorted(people.items()):
                w.writerow([ds, arm, p] + [v.get(k) for k in keys])
        for arm, people in sorted(priv.items()):
            for p, v in sorted(people.items()):
                w.writerow(['private_bdf', arm, p] + [v.get(k) for k in keys])
    print(json.dumps({f['family_id']: f['status'] for f in fams}), flush=True)


if __name__ == '__main__':
    main()
