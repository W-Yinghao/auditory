"""DEP12 optional public support selector (Agent M; package v1.2 02 §7.2; rule frozen in DECISIONS M16 before any output).

For each test person p and content fold cf, the support is p's own single-talker 'calib' panel of cf (content-disjoint from the
test-half 20 s queries; stimulus pairing only). Four policies choose one representation among the candidates; the utility is
p's 20 s attention accuracy of the chosen candidate (rule (a) and rule (b) of attention.py), averaged over both content folds.
  dependence   largest support env excess (fold σ_u / σ_env, n128 block-shift bank; reference measure_from_grams)
  readout_cv   largest 4-fold leave-one-block-out Gaussian kernel ridge r (fold σ_u, λ = 0.1) on the support
  fixed        largest mean support env excess over the fold's training people's calib panels (independent of p)
  uniform      rule (a): sign of the summed z-margins of all candidates; rule (b): sign of the summed readout margins
Ties: candidate order as given (B0 first). Inputs: feature caches, measure calibration, attention query records.
Outputs: results/auditory_alignment_v3/dep12/selection/public/<ds>/<tag>.json
CLI (Slurm only): python -m auditory_alignment_v3.dep12.public_selector --tag TAG --candidates B0 cs_pair@3401 ... [--dataset ds]
"""
from __future__ import annotations

import argparse
from datetime import datetime
import gzip
import os
from pathlib import Path
import time

import numpy as np

from . import attention as AT
from . import dependence_measure as DM
from . import measure_v5 as M
from . import panels as PN
from . import public_features_v5 as PF

OUT = M.RESULTS / 'selection' / 'public'
LAMBDA = 0.1
sha, write, read = PN.sha, PN.write, PN.read


def query_table(ds, name):
    p = AT.PRED / ds / f'{name}.queries.csv.gz'
    with gzip.open(p, 'rt') as f:
        head = f.readline().strip().split(',')
        rows = [dict(zip(head, line.rstrip('\n').split(','))) for line in f]
    return {int(r['query']): r for r in rows}


def num(x):
    return None if x in ('', None) else float(x)


def krr_cv(K, Y, blocks, lam=LAMBDA):
    rs = []
    for b in np.unique(blocks):
        te, tr = blocks == b, blocks != b
        mu = Y[tr].mean(0); n = int(tr.sum())
        alpha = np.linalg.solve(K[np.ix_(tr, tr)] + n * lam * np.eye(n), Y[tr] - mu)
        rs.append(AT.colcorr(K[np.ix_(te, tr)] @ alpha + mu, Y[te]))
    return float(np.mean(rs))


def run(ds, tag, cands):
    t0 = time.time(); M.check_reference()
    defs = PN.defs(ds); desc = PF.load_descriptors(ds); didx = {p: i for i, p in enumerate(desc['panel_ids'].tolist())}
    from ..paper import ext_common as X
    c = X.Cache(ds)
    feats, cals, qt = {}, {}, {}
    for n in cands:
        dest, _ = PF.feature_dir(n, ds); assert dest is not None, n
        with np.load(dest / 'panels.npz', allow_pickle=False) as z:
            D2 = z['d2']                                  # load once (indexing z['d2'] per panel re-reads the whole array)
            feats[n] = {pid: D2[i] for i, pid in enumerate(z['ids'].tolist())}
        cals[n] = read(M.MEAS / ds / n / 'calibration.json')['calibration']
        qt[n] = query_table(ds, n)
    bank = M.bank(defs, 'n128', range(4)); blocks = np.repeat(np.arange(4), PN.BLOCK_N)

    def support_excess(n, panel, cf, sf):
        cal = cals[n][f'cf{cf}_sf{sf}']; e = cal['eeg']['1.0']; dcal = cal['descriptors']['env']
        if e['status'] != 'ok':
            return None
        Y = (desc['env'][didx[panel]] - np.asarray(dcal['mu'])) / np.asarray(dcal['sd'])
        r = DM.measure_from_grams(M.gram_from_d2(feats[n][panel], e['overlap_sigma']), DM.gaussian_gram(Y, dcal['cal']['overlap_sigma']), bank,
                                  null_design=defs['null_design']['n128'])
        return r['excess_cs_nats']

    def support_cv(n, panel, cf, sf):
        cal = cals[n][f'cf{cf}_sf{sf}']; e = cal['eeg']['1.0']; dcal = cal['descriptors']['env']
        if e['status'] != 'ok':
            return None
        Y = (desc['env'][didx[panel]] - np.asarray(dcal['mu'])) / np.asarray(dcal['sd'])
        return krr_cv(M.gram_from_d2(feats[n][panel], e['overlap_sigma']), Y, blocks)
    fixed = {}
    people, records = {}, []
    for cf in PN.CFS:
        for sf in PN.SFS:
            train, test = c.unit_people(sf)
            pop = {n: [v for v in (support_excess(n, f'{ds}:{p}:cf{cf}:calib', cf, sf) for p in train
                                   if f'{ds}:{p}:cf{cf}:calib' in feats[n]) if v is not None] for n in cands}
            means = {n: (float(np.mean(v)) if v else -np.inf) for n, v in pop.items()}
            fixed[f'cf{cf}_sf{sf}'] = {'choice': max(cands, key=lambda n: (means[n], -cands.index(n))), 'means': means}
            for p in sorted(test):
                panel = f'{ds}:{p}:cf{cf}:calib'
                if not all(panel in feats[n] for n in cands):
                    continue
                dep = {n: support_excess(n, panel, cf, sf) for n in cands}
                cv = {n: support_cv(n, panel, cf, sf) for n in cands}
                pick = {'dependence': max(cands, key=lambda n: (-np.inf if dep[n] is None else dep[n], -cands.index(n))),
                        'readout_cv': max(cands, key=lambda n: (-np.inf if cv[n] is None else cv[n], -cands.index(n))),
                        'fixed': fixed[f'cf{cf}_sf{sf}']['choice']}
                qs = [i for i, q in enumerate(defs['queries']) if q['person'] == p and q['cf'] == cf and q['status'] == 'ok']
                util = {}
                for rule, cred, marg in (('a', 'dep_credit', 'depz_margin'), ('b', 'read_credit', 'read_margin')):
                    for pol, n in pick.items():
                        v = [num(qt[n][i][cred]) for i in qs if i in qt[n]]
                        util[f'{pol}:{rule}'] = float(np.mean([x for x in v if x is not None])) if any(x is not None for x in v) else None
                    s = []
                    for i in qs:
                        m = [num(qt[n][i].get(marg)) for n in cands if i in qt[n]]
                        if len(m) == len(cands) and all(x is not None for x in m):
                            s.append(AT.credit(float(np.sum(m))))
                    util[f'uniform:{rule}'] = float(np.mean(s)) if s else None
                records.append({'participant_id': p, 'content_fold': cf, 'person_fold': sf, 'support_panel': panel,
                                'support_excess': dep, 'support_cv_r': cv, 'pick': pick, 'utility': util, 'n_queries': len(qs)})
                people.setdefault(p, {})[cf] = util
    per = {p: {k: (float(np.mean([v[cf][k] for cf in PN.CFS])) if all(v[cf].get(k) is not None for cf in PN.CFS) else None)
               for k in v[PN.CFS[0]]} for p, v in people.items() if sorted(v) == list(PN.CFS)}
    from . import public_report as RP
    comps = {}
    for rule in ('a', 'b'):
        for other in ('readout_cv', 'fixed', 'uniform'):
            d = [per[p][f'dependence:{rule}'] - per[p][f'{other}:{rule}'] for p in per
                 if per[p].get(f'dependence:{rule}') is not None and per[p].get(f'{other}:{rule}') is not None]
            comps[f'rule_{rule}:dependence-{other}'] = RP.describe(d)
        for pol in ('dependence', 'readout_cv', 'fixed', 'uniform'):
            comps[f'rule_{rule}:{pol}:accuracy'] = RP.describe([per[p][f'{pol}:{rule}'] for p in per])
    freq = {pol: {n: sum(r['pick'][pol] == n for r in records) for n in cands} for pol in ('dependence', 'readout_cv', 'fixed')}
    out = OUT / ds; out.mkdir(parents=True, exist_ok=True)
    write(out / f'{tag}.json', {'version': 'DEP12_PUB_SELECTOR_v1', 'dataset': ds, 'tag': tag, 'candidates': cands, 'records': records,
                                'people': per, 'comparisons': comps, 'selection_frequency': freq, 'fixed_choices': fixed,
                                'rule': 'DECISIONS M16', 'seconds': time.time() - t0, 'job': os.environ.get('SLURM_JOB_ID'),
                                'time': datetime.now().astimezone().isoformat()})
    print(ds, tag, 'people', len(per), {k: v.get('mean') for k, v in comps.items()}, flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--tag', required=True); ap.add_argument('--candidates', nargs='+', required=True)
    ap.add_argument('--dataset', choices=PN.DATASETS)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    for ds in ([a.dataset] if a.dataset else PN.DATASETS):
        run(ds, a.tag, a.candidates)


if __name__ == '__main__':
    main()
