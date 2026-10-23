"""DEP12 manipulation check (coordinator DECISIONS 2026-10-23 12:20; Agent M M21): how far did each trained arm move the representation
away from B0 on the common panels?  Descriptive.

U is not stored (M5), so the check uses the cached exact squared distances of every encoder on the SAME test panels (same anchors):
  Gaussian CKA  = centred kernel alignment of K_arm = exp(-D²_arm / 2σ_arm²) and K_B0 = exp(-D²_B0 / 2σ_B0²), each σ = that encoder's
                  frozen measurement σ_u of the panel's fold (measure calibration)            -> change_g = 1 - CKA
  linear CKA    = the same alignment of the double-centred -D²/2 matrices (= Gram matrices of the centred U; σ-free) -> change_l = 1 - CKA
per test panel (n anchors), averaged per person over both content folds (Federici: recordings of one identity averaged), then the
cohort mean with a descriptive person-bootstrap interval (B = 10,000).  Per seed and merged (person mean over 3401 / 3407 / 3413).
Ratios of cohort means: change(ssl_continue) / change(cs_pair_noise) and / change(cs_pair); 12:20 rule: < 0.25 => an
"ssl_continue ≈ B0" outcome is an inconclusive control.  Output: results/auditory_alignment_v3/dep12/MANIPULATION_CHECK.{json,md}.
CLI (Slurm only): python -m auditory_alignment_v3.dep12.manipulation
"""
from __future__ import annotations

from datetime import datetime
import os

import numpy as np

from . import measure_v5 as M
from . import panels as PN
from . import public_features_v5 as PF

ARMS = ('ssl_continue', 'cs_pair_noise', 'cs_pair', 'info_nce', 'sigmoid', 'raw_cs', 'cs_pair_wrong')
SEEDS = (3401, 3407, 3413)
RULE = 0.25
OUT = M.RESULTS
sha, write, read = PN.sha, PN.write, PN.read


def centred(A):
    return A - A.mean(0, keepdims=True) - A.mean(1, keepdims=True) + A.mean()


def cka(A, B):
    a, b = centred(A), centred(B)
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else float('nan')


def load(name, ds):
    dest, _ = PF.feature_dir(name, ds)
    calp = M.MEAS / ds / name / 'calibration.json'
    if dest is None or not calp.exists():
        return None
    with np.load(dest / 'panels.npz', allow_pickle=False) as z:
        D = z['d2']; ids = z['ids'].tolist()
    return {'d2': {p: D[i] for i, p in enumerate(ids)}, 'cal': read(calp)['calibration']}


def sigma(enc, cf, sf):
    e = enc['cal'].get(f'cf{cf}_sf{sf}', {}).get('eeg', {}).get('1.0', {})
    return e.get('overlap_sigma') if e.get('status') == 'ok' else None


def person_changes(ds, name, b0, defs):
    enc = load(name, ds)
    if enc is None:
        return None
    by = {}
    for pid, pn in defs['panels'].items():
        if pn['kind'] != 'test' or pid not in enc['d2'] or pid not in b0['d2']:
            continue
        p, cf = pn['person'], pn['cf']; sf = defs['folds'][p]; n = pn['n']
        sa, sb = sigma(enc, cf, sf), sigma(b0, cf, sf)
        Da = enc['d2'][pid][:n, :n].astype(np.float64); Db = b0['d2'][pid][:n, :n].astype(np.float64)
        rec = {'linear': 1.0 - cka(-0.5 * Da, -0.5 * Db)}
        if sa and sb:
            rec['gaussian'] = 1.0 - cka(M.gram_from_d2(Da, sa), M.gram_from_d2(Db, sb))
        by.setdefault(p, {})[cf] = rec
    cfs = (0,) if ds == 'federici' else PN.CFS
    out = {}
    for p, v in by.items():
        if all(cf in v for cf in cfs):
            out[p] = {k: float(np.mean([v[cf][k] for cf in cfs])) for k in ('linear', 'gaussian') if all(k in v[cf] for cf in cfs)}
    if ds == 'federici':
        ident = {q['id']: q['identity'] for q in read(PN.DEFS / ds / 'scan.json')['people']}
        grp = {}
        for p, v in out.items():
            grp.setdefault(ident[p], []).append(v)
        out = {i: {k: float(np.mean([x[k] for x in vs if k in x])) for k in ('linear', 'gaussian') if all(k in x for x in vs)} for i, vs in grp.items()}
    return out


def main():
    from . import public_report as RP
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    res = {'version': 'DEP12_MANIPULATION_CHECK_v1', 'time': datetime.now().astimezone().isoformat(), 'rule': RULE,
           'definition': __doc__.split('\n\n')[1] if __doc__ else '', 'cohorts': {}}
    for ds in PF.DATASETS:
        try:
            defs = PN.defs(ds)
        except AssertionError:
            continue
        b0 = load('B0', ds)
        if b0 is None:
            continue
        coh = {'per_seed': {}, 'merged': {}, 'ratios': {}}
        per = {}
        for arm in ARMS:
            for s in SEEDS:
                v = person_changes(ds, f'{arm}@{s}', b0, defs)
                if v:
                    per[(arm, s)] = v
                    coh['per_seed'][f'{arm}@{s}'] = {k: RP.describe([x[k] for x in v.values() if k in x]) for k in ('gaussian', 'linear')}
            if all((arm, s) in per for s in SEEDS):
                people = set.intersection(*[set(per[(arm, s)]) for s in SEEDS])
                m = {p: {k: float(np.mean([per[(arm, s)][p][k] for s in SEEDS])) for k in ('gaussian', 'linear')
                         if all(k in per[(arm, s)][p] for s in SEEDS)} for p in people}
                coh['merged'][arm] = {k: RP.describe([x[k] for x in m.values() if k in x]) for k in ('gaussian', 'linear')}
        for tag in [f'seed{s}' for s in SEEDS] + ['merged']:
            def mean(arm, k):
                e = coh['merged'].get(arm) if tag == 'merged' else coh['per_seed'].get(f'{arm}@{tag[4:]}')
                return (e or {}).get(k, {}).get('mean')
            r = {}
            for k in ('gaussian', 'linear'):
                ssl, noise, cs = mean('ssl_continue', k), mean('cs_pair_noise', k), mean('cs_pair', k)
                r[k] = {'ssl_over_noise': (ssl / noise) if ssl is not None and noise else None,
                        'ssl_over_cs_pair': (ssl / cs) if ssl is not None and cs else None}
            r['rule_inconclusive_if_ssl_over_noise_below'] = RULE
            g = r['gaussian']['ssl_over_noise']
            r['ssl_continue_control'] = None if g is None else ('inconclusive (ssl_continue moved < 25 % of cs_pair_noise)' if g < RULE
                                                                else 'informative (11:55 interpretation applies)')
            coh['ratios'][tag] = r
        res['cohorts'][ds] = coh
    write(OUT / 'MANIPULATION_CHECK.json', res)
    (OUT / 'MANIPULATION_CHECK.md').write_text(markdown(res))
    print('manipulation check', {ds: c['ratios'].get('merged') for ds, c in res['cohorts'].items()}, flush=True)
    return res


def markdown(res):
    L = ['# DEP12 manipulation check (ext3)', '', f'Generated {res["time"]}. Descriptive; coordinator DECISIONS 2026-10-23 12:20, Agent M M21.', '',
         'Representation change relative to B0 on the common test panels (same anchors): **1 − CKA**, Gaussian kernels with each encoder\'s '
         'own frozen σ (primary) and σ-free linear CKA (double-centred −D²/2). Person = unit (content folds averaged; Federici identities '
         'averaged); cohort means with descriptive person-bootstrap 95 % intervals. Rule (12:20): if change(ssl_continue) / '
         'change(cs_pair_noise) < 0.25 (Gaussian, DTU primary), an "ssl_continue ≈ B0" result is an inconclusive control.', '']
    for ds, c in res['cohorts'].items():
        L += [f'## {ds.upper()}', '', '| encoder | 1 − CKA (Gaussian) | 1 − CKA (linear) | n |', '|---|---|---|---|']
        for name, e in list(c['per_seed'].items()) + [(f'{a} (3-seed merged)', v) for a, v in c['merged'].items()]:
            g, l = e.get('gaussian', {}), e.get('linear', {})
            f = lambda v: '—' if not v or v.get('mean') is None else (f'{v["mean"]:.4f}' + (f' [{v["pointwise_95"][0]:.4f}, {v["pointwise_95"][1]:.4f}]' if v.get('pointwise_95') else ''))
            L.append(f'| {name} | {f(g)} | {f(l)} | {g.get("n", "—")} |')
        L += ['', '| seed | ssl / noise (Gaussian) | ssl / cs_pair (Gaussian) | ssl / noise (linear) | control |', '|---|---|---|---|---|']
        for tag, r in c['ratios'].items():
            fm = lambda x: '—' if x is None else f'{x:.3f}'
            L.append(f'| {tag} | {fm(r["gaussian"]["ssl_over_noise"])} | {fm(r["gaussian"]["ssl_over_cs_pair"])} | {fm(r["linear"]["ssl_over_noise"])} | '
                     f'{r["ssl_continue_control"] or "—"} |')
        L.append('')
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    main()
