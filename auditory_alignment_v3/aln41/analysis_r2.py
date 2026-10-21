"""ALN4.1 R2 analysis (CPU): per-seed frozen readouts and age for seeds 3407 / 3413 (R1 code, re-pointed), then the
three-seed person-level families, F_SUPPORT and F_CROSS_STIM. Written before any R2 result.

Steps: `python -m auditory_alignment_v3.aln41.analysis_r2 <readout|age|families>`.
- readout: R1 readout.main for each R2 seed. It reads that seed's frozen non-B0 units and writes r2/seed<S>/readout_v1.
- age: R1 age.main for each R2 seed, on TCS and TNCE.
- families: every endpoint is averaged per person over seeds 3401 / 3407 / 3413, with three exceptions:
  - B0 frozen endpoints and B0 age are seed-free and come from R1;
  - B0 CE AUC is seed-specific and is averaged;
  - the raw-EEG / train-mean age baselines come from R1.
  A person enters a member only when every required seed contributes; there are no partial-seed means.
  Families: R1 layout (F_CONTENT / F_TIME / F_UTILITY per cohort, plus F_ASSOC with the fourth person endpoint, the R2
  delta U30 gain); F_SUPPORT (support_v1 plan); F_CROSS_STIM (cross_stim_v1 plan and decision record).
  Per-seed values are also reported per member (seed-wise estimates). Seeds are not independent people.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np

from .. import core
from . import age as AGE, analysis as AN, cross_stim as XS, frozen as FZ, private_ft as PF, r2 as R2, readout as RO
from . import source as SRC, support as SU

SEEDS = (3401, 3407, 3413)
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/aln41/r2'
OTHERS = AN.OTHERS
read, write = SRC.read, SRC.write


@contextlib.contextmanager
def seed_ctx(seed):
    """R1 bases for 3401; R2 seeded bases (+ readout / age / age-result roots) otherwise."""
    if seed == SRC.SEED:
        yield; return
    root = R2.ROOT / f'seed{seed}'
    saved = [(RO, 'BASE', RO.BASE), (AGE, 'BASE', AGE.BASE), (AGE, 'ARMS', AGE.ARMS), (SRC, 'OUT', SRC.OUT)]
    with R2.seeded(seed):
        try:
            RO.BASE, AGE.BASE, AGE.ARMS, SRC.OUT = root / 'readout_v1', root / 'age_v1', ('TCS', 'TNCE'), root
            yield
        finally:
            for m, k, v in saved:
                setattr(m, k, v)


def run_readout_and_age(which):
    argv = sys.argv
    for seed in SEEDS[1:]:
        with seed_ctx(seed):
            if which == 'readout':
                sys.argv = ['readout', '--all-ready']; RO.main()
            elif not (AGE.BASE / 'age_results.json').exists():
                AGE.main()
    sys.argv = argv


# ----------------------------------------------------------------------------------------------- merge over seeds
SEED_FREE_B0 = ('content_r', 'content_direct_r', 'time_fixed_loss', 'time_refit_recovery', 'attention20_acc', 'content_hist_bits',
                'current_auc', 'twin_bits', 'age_abs_err', 'mean_abs_err')


def collect():
    pub, priv = {}, {}
    for seed in SEEDS:
        with seed_ctx(seed):
            pub[seed], priv[seed] = AN.public_values(), AN.private_values()
    return pub, priv


def merge(by_seed, arm_of):
    """{seed: {key: {person: {endpoint: v}}}} -> ({key: {person: {endpoint: mean}}}, {key: {person: {endpoint: [per-seed]}}})."""
    out, per = {}, {}
    keys = set().union(*[set(d) for d in by_seed.values()])
    for key in keys:
        arm = arm_of(key)
        people = set().union(*[set(by_seed[s].get(key, {})) for s in SEEDS])
        for p in people:
            eps = set().union(*[set(by_seed[s].get(key, {}).get(p, {})) for s in SEEDS])
            for ep in eps:
                if ep == 'group':
                    out.setdefault(key, {}).setdefault(p, {})['group'] = next(by_seed[s][key][p]['group'] for s in SEEDS
                                                                             if 'group' in by_seed[s].get(key, {}).get(p, {}))
                    continue
                seeds = (SRC.SEED,) if (arm in ('B0', 'RAW') and ep in SEED_FREE_B0) else SEEDS
                vals = [by_seed[s].get(key, {}).get(p, {}).get(ep) for s in seeds]
                ok = all(v is not None for v in vals)
                out.setdefault(key, {}).setdefault(p, {})[ep] = float(np.mean(vals)) if ok else None
                per.setdefault(key, {}).setdefault(p, {})[ep] = vals
    return out, per


# ----------------------------------------------------------------------------------------------- R2 endpoints
def support_values():
    """{arm: {child: {method_support: query NLL gain over U0 (bits), seed-averaged}}}; None unless all seeds exist."""
    vals = {}
    for p in sorted((SU.OUT / 'units').glob('*.json')):
        u = read(p); arm, seed = u['row']['arm'], u['seed']
        for cid, r in u['children'].items():
            base = r['U0']['nll_bits']
            g = {'delta_U10': base - r['U10_delta_mean']['nll_bits'], 'delta_U30': base - r['U30']['delta']['nll_bits'],
                 'cal_U10': base - r['U10_cal_mean']['nll_bits'], 'cal_U30': base - r['U30']['cal']['nll_bits'],
                 'brier_delta_U30': r['U0']['brier'] - r['U30']['delta']['brier'], 'brier_cal_U30': r['U0']['brier'] - r['U30']['cal']['brier'],
                 'auc_delta_U30': (r['U30']['delta']['auc'] - r['U0']['auc']) if None not in (r['U30']['delta']['auc'], r['U0']['auc']) else None,
                 'n_fallbacks': len(r['fallbacks'])}
            vals.setdefault(arm, {}).setdefault(cid, {})[seed] = g
    out = {}
    for arm, kids in vals.items():
        for cid, by_seed in kids.items():
            if sorted(by_seed) != list(SEEDS):
                out.setdefault(arm, {})[cid] = None; continue
            out.setdefault(arm, {})[cid] = {k: (float(np.mean([by_seed[s][k] for s in SEEDS])) if all(by_seed[s][k] is not None for s in SEEDS) else None)
                                            for k in by_seed[SEEDS[0]]}
    return out


def support_families(sv, kids):
    get = lambda arm, k: {c: (sv.get(arm, {}).get(c) or {}).get(k) for c in kids}
    sub = lambda a, b: {c: (a[c] - b[c]) if a.get(c) is not None and b.get(c) is not None else None for c in kids}
    members = []
    for arm in ('B0', 'TCS', 'TNCE'):
        dU10, dU30, cU10, cU30 = (get(arm, k) for k in ('delta_U10', 'delta_U30', 'cal_U10', 'cal_U30'))
        members += [(f'{arm}:delta_U10-U0', dU10), (f'{arm}:delta_U30-U0', dU30), (f'{arm}:cal_U10-U0', cU10), (f'{arm}:cal_U30-U0', cU30),
                    (f'{arm}:delta_U10-cal_U10', sub(dU10, cU10)), (f'{arm}:delta_U30-cal_U30', sub(dU30, cU30))]
    members += [('delta_U30 gain:TCS-B0', sub(get('TCS', 'delta_U30'), get('B0', 'delta_U30'))),
                ('delta_U30 gain:TCS-TNCE', sub(get('TCS', 'delta_U30'), get('TNCE', 'delta_U30')))]
    fam = AN.family('F_SUPPORT:PRIVATE', 'query NLL gain over U0, bits/trial (positive = better); seeds averaged', members, kids)
    desc = []
    for arm in ('B0', 'TCS', 'TNCE'):
        desc += [(f'{arm}:brier_delta_U30', get(arm, 'brier_delta_U30')), (f'{arm}:brier_cal_U30', get(arm, 'brier_cal_U30')),
                 (f'{arm}:auc_delta_U30', get(arm, 'auc_delta_U30'))]
    return fam, AN.family('F_SUPPORT_DESCRIPTIVE:PRIVATE', 'Brier gain / AUC change at U30 (descriptive)', desc, kids)


def cross_values():
    """{arm: {bapa id: {transfer, refit, transfer_hist, refit_hist}}} (TCS/TNCE seed-averaged), pure-tone within AUC."""
    plan = read(XS.OUT / 'plan.json'); per = {}
    for row in plan['rows']:
        p = XS.OUT / 'readout' / f'{row["id"]}.json'
        if not p.exists():
            continue
        r = read(p)['children']
        for kind in ('transfer', 'refit', 'within'):
            for i, v in r[kind].items():
                per.setdefault(row['arm'], {}).setdefault((kind, i), {})[row['seed']] = v
    out = {}
    for arm, items in per.items():
        need = [None] if arm == 'B0' else [3401, 3407, 3413]
        for (kind, i), by_seed in items.items():
            ok = sorted(by_seed, key=str) == sorted(need, key=str)
            d = out.setdefault(arm, {}).setdefault(i, {})
            d[kind] = float(np.mean([by_seed[s]['auc_q0'] for s in need])) if ok else None
            d[kind + '_hist'] = float(np.mean([by_seed[s]['history_increment_bits_q0'] for s in need])) if ok else None
    return out


def cross_families(cv):
    bapa = sorted({i for arm in cv.values() for i, d in arm.items() if 'transfer' in d or 'refit' in d})
    def fam(fid, key, unit):
        g = lambda arm, k: {i: (cv.get(arm, {}).get(i) or {}).get(k) for i in bapa}
        sub = lambda a, b: {i: (a[i] - b[i]) if a.get(i) is not None and b.get(i) is not None else None for i in bapa}
        chance = 0.5 if key == '' else 0.0
        members = []
        for arm in ('B0', 'TCS', 'TNCE'):
            t, r = g(arm, 'transfer' + key), g(arm, 'refit' + key)
            members += [(f'{arm}:transfer-{chance}', {i: (v - chance) if v is not None else None for i, v in t.items()}),
                        (f'{arm}:refit-{chance}', {i: (v - chance) if v is not None else None for i, v in r.items()}),
                        (f'{arm}:refit-transfer', sub(r, t))]
        for kind in ('transfer', 'refit'):
            members += [(f'{kind}:TCS-B0', sub(g('TCS', kind + key), g('B0', kind + key))),
                        (f'{kind}:TCS-TNCE', sub(g('TCS', kind + key), g('TNCE', kind + key)))]
        return AN.family(fid, unit, members, bapa)
    paired = sorted(i for i in bapa if any((cv.get(a, {}).get(i) or {}).get('within') is not None for a in cv))
    table = [{'child': f'pair{n + 1}', **{f'{arm}:{k}': (cv.get(arm, {}).get(i) or {}).get(k) for arm in ('B0', 'TCS', 'TNCE')
                                          for k in ('within', 'transfer', 'refit')}} for n, i in enumerate(paired)]
    return (fam('F_CROSS_STIM:BAPA', '', 'bapa child AUC (deviant vs standard), q0 mixture; seeds averaged'),
            fam('F_CROSS_STIM_SECONDARY:BAPA', '_hist', 'history-conditional increment, bits/trial (descriptive family)'), table)


# ----------------------------------------------------------------------------------------------- families
def families(pub, priv, sv):
    diff = AN.diff; fams = []
    for ds, label in (('dtu', 'DTU'), ('fau', 'FAU')):
        arms = {a: pub.get((ds, a), {}) for a in ('TCS',) + OTHERS}
        if not arms['TCS']:
            continue
        people = sorted(set().union(*[set(v) for v in arms.values()]))
        fams.append(AN.family(f'F_CONTENT:{label}', 'history-conditional envelope r', [(f'TCS-{o}', diff(arms['TCS'], arms[o], 'content_r')) for o in OTHERS], people))
        fams.append(AN.family(f'F_TIME:{label}', 'r', [(f'fixed_loss:{o}-TCS', diff(arms['TCS'], arms[o], 'time_fixed_loss', -1)) for o in OTHERS]
                              + [(f'refit_recovery:TCS-{o}', diff(arms['TCS'], arms[o], 'time_refit_recovery')) for o in OTHERS], people))
        fams.append(AN.family(f'F_UTILITY:{label}', 'attention accuracy (20 s)', [(f'TCS-{o}', diff(arms['TCS'], arms[o], 'attention20_acc')) for o in ('B0', 'TNCE')], people))
    T = priv.get('TCS', {}); kids = sorted(set().union(*[set(v) for v in priv.values()]))
    fams.append(AN.family('F_CONTENT:PRIVATE', 'bits/trial', [(f'TCS-{o}', diff(T, priv.get(o, {}), 'content_hist_bits')) for o in OTHERS], kids))
    fams.append(AN.family('F_TIME:PRIVATE', 'AUC', [(f'fixed_loss:{o}-TCS', diff(T, priv.get(o, {}), 'time_fixed_loss', -1)) for o in OTHERS]
                          + [(f'refit_recovery:TCS-{o}', diff(T, priv.get(o, {}), 'time_refit_recovery')) for o in OTHERS], kids))
    util = [(f'ft_auc:TCS-{o}', diff(T, priv.get(o, {}), 'ft_auc')) for o in ('B0', 'TNCE')]
    util += [(f'age_abs_err:{o}-TCS', diff(T, priv.get(o, {}), 'age_abs_err', -1)) for o in ('B0', 'TNCE')]
    for arm in ('B0', 'TCS', 'TNCE'):
        A = priv.get(arm, {})
        util.append((f'age_abs_err:RAW-{arm}', {p: (priv['RAW'][p]['age_abs_err'] - A[p]['age_abs_err'])
                                                if p in priv.get('RAW', {}) and A.get(p, {}).get('age_abs_err') is not None else None for p in kids}))
        util.append((f'age_abs_err:MEAN-{arm}', {p: (A[p]['mean_abs_err'] - A[p]['age_abs_err'])
                                                 if A.get(p, {}).get('age_abs_err') is not None else None for p in kids}))
    age_kids = [p for p in kids if priv.get('B0', {}).get(p, {}).get('age_abs_err') is not None] or kids
    fams.append(AN.family('F_UTILITY:PRIVATE', 'AUC / months', util, age_kids))
    for arm in ('B0', 'TCS', 'TNCE'):            # fourth F_ASSOC person endpoint: R2 U30 personal-delta gain
        for c in kids:
            if c in priv.get(arm, {}):
                priv[arm][c]['support_delta_U30_gain'] = (sv.get(arm, {}).get(c) or {}).get('delta_U30')
    saved = dict(AN.ASSOC_ENDPOINTS)
    AN.ASSOC_ENDPOINTS['private'] = saved['private'] + ('support_delta_U30_gain',)
    try:
        assoc = AN.assoc(pub, priv)
    finally:
        AN.ASSOC_ENDPOINTS.clear(); AN.ASSOC_ENDPOINTS.update(saved)
    return fams, assoc, kids


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=('readout', 'age', 'families'))
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.step in ('readout', 'age'):
        run_readout_and_age(a.step); return
    pub_s, priv_s = collect()
    pub, pub_per = merge(pub_s, lambda key: key[1])
    priv, priv_per = merge(priv_s, lambda key: key)
    sv = support_values()
    fams, assoc, kids = families(pub, priv, sv)
    sup, sup_desc = support_families(sv, kids)
    xs, xs2, pairs = cross_families(cross_values()) if (XS.OUT / 'readout').exists() else (None, None, [])
    for f in fams + [sup, sup_desc] + [x for x in (xs, xs2) if x]:
        f['method'] = 'sci_r1 identity bootstrap-t B=4000, family max-|T*|; person values averaged over seeds 3401/3407/3413'
    RESULTS.mkdir(parents=True, exist_ok=True)
    write(RESULTS / 'contrasts.json', {'version': 'ALN41_R2_ANALYSIS_v1', 'seeds': list(SEEDS), 'families': fams + [sup, sup_desc] + [x for x in (xs, xs2) if x],
                                       'F_ASSOC': assoc, 'cross_stim_same_day_pairs': pairs,
                                       'note': 'people are the unit; seeds averaged within person; B0 frozen endpoints are seed-free (R1)'})
    keys = sorted({k for d in list(pub.values()) + list(priv.values()) for v in d.values() for k in v})
    with open(RESULTS / 'person_results.csv', 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(['cohort', 'arm', 'person'] + keys + ['per_seed'])
        for (ds, arm), people in sorted(pub.items()):
            for p, v in sorted(people.items()):
                w.writerow([ds, arm, p] + [v.get(k) for k in keys] + [json.dumps(pub_per.get((ds, arm), {}).get(p, {}))])
        for arm, people in sorted(priv.items()):
            for p, v in sorted(people.items()):
                w.writerow(['private_bdf', arm, p] + [v.get(k) for k in keys] + [json.dumps(priv_per.get(arm, {}).get(p, {}))])
    print(json.dumps({f['family_id']: f['status'] for f in fams + [sup] + ([xs] if xs else [])}), flush=True)


if __name__ == '__main__':
    main()
