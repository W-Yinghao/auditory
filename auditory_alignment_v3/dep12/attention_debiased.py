"""DEP12 POST-HOC debiased 20 s attention score (coordinator DECISIONS 2026-10-23 07:55; Agent M engineering note M18).

For every scored query i and both rules of attention.py (same calibration, shifts, readout, candidate standardisation):
  debiased margin = own margin(U_i; A_i, I_i) - mean_{j in F(i)} margin(U_j; A_i, I_i)
with F(i) = the first 8 queries of one seeded permutation (seed 20261023) of the in-scope queries with the same content fold and
another person (F(i)[0] is attention.py's single foreign query); U_j enters through its kernel with σ_u of j's own fold (rule a)
or its readout prediction with j's fold readout (rule b). Credit = sign (ties 0.5). No τ / NLL (M18). Person accuracy = mean
over its test windows per content fold, then over both content folds (both required). Labelled post hoc / secondary.
Outputs: results/auditory_alignment_v3/dep12/predictions/attention_public/<ds>/<encoder>.debiased.{queries.csv.gz, people.json}
CLI (Slurm only): python -m auditory_alignment_v3.dep12.attention_debiased {run --encoder NAME --dataset ds, run-all, check}
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
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

K_FOREIGN, FOREIGN_SEED = 8, 20261023
LOCKS = PN.OUT / 'stage_locks'
sha, write, read = PN.sha, PN.write, PN.read


def sources():
    here = Path(__file__).parent
    return {**AT.sources(), str((here / 'attention_debiased.py').relative_to(M.core.REPO)): sha(here / 'attention_debiased.py')}


def shift_excess(Ks, L, perms):
    """Reference Parzen CS (self-pairs, natural log) for kernels Ks [m, n, n] with one target Gram L under row permutations
    perms [S, n] (L[p][:, p]); returns (raw [m], null [S, m], excess [m])."""
    m, n, _ = Ks.shape; S = len(perms)
    kbar = Ks.mean(2); lbar = L.mean(1)
    A = (Ks * L[None]).mean((1, 2)); B = Ks.mean((1, 2)) * L.mean(); C = (kbar * lbar[None]).mean(1)
    raw = np.log(A) + np.log(B) - 2.0 * np.log(C)
    Lp = L[perms[:, :, None], perms[:, None, :]].reshape(S, -1)
    An = Lp @ Ks.reshape(m, -1).T / (n * n); Cn = lbar[perms] @ kbar.T / n
    null = np.log(An) + np.log(B)[None] - 2.0 * np.log(Cn)
    return raw, null, raw - null.mean(0)


def foreign_sets(defs, qlist):
    order = np.random.default_rng(FOREIGN_SEED).permutation(len(qlist))
    cf = [defs['queries'][i]['cf'] for i in qlist]; per = [defs['queries'][i]['person'] for i in qlist]
    out = {}
    for j in range(len(qlist)):
        got = []
        for k in order:
            if cf[k] == cf[j] and per[k] != per[j]:
                got.append(int(k))
                if len(got) == K_FOREIGN:
                    break
        out[j] = got
    return out


def run(name, ds):
    t0 = time.time(); M.check_reference()
    dest = PF.feature_dir(name, ds)[0]; info = read(dest / 'meta.json')
    for f, h in info['files_sha256'].items():
        assert sha(dest / f) == h, f
    cal = read(M.MEAS / ds / name / 'calibration.json')['calibration']
    defs = PN.defs(ds); desc = PF.load_descriptors(ds); didx = {p: i for i, p in enumerate(desc['panel_ids'].tolist())}
    prim = {}
    with gzip.open(AT.PRED / ds / f'{name}.queries.csv.gz', 'rt') as f:
        head = f.readline().strip().split(',')
        for line in f:
            r = dict(zip(head, line.rstrip('\n').split(','))); prim[int(r['query'])] = r
    with np.load(dest / 'queries.npz', allow_pickle=False) as z:
        qidx, d2c, proj = z['qidx'], z['d2c'], z['proj']
    with np.load(dest / 'pca.npz', allow_pickle=False) as z:
        pca = {k: z[k] for k in z.files}
    qlist = qidx.tolist(); Q = len(qlist); n = PN.QUERY_N
    perms = np.stack([(np.arange(n) + k) % n for k in defs['attention_shifts']]).astype(np.int64)
    fold = []
    for i in qlist:
        qd = defs['queries'][i]; c = cal[f"cf{qd['cf']}_sf{qd['sf']}"]; fold.append((qd, c, c['eeg']['1.0']))
    # kernels and readout predictions of every in-scope query (own fold calibration / readout)
    Kall = np.empty((Q, n, n), np.float64); ok = np.ones(Q, bool)
    for j in range(Q):
        e = fold[j][2]
        if e['status'] == 'ok':
            Kall[j] = M.gram_from_d2(M.full_d2(d2c[j]), e['overlap_sigma'])
        elif e['status'] == 'constant_representation':
            Kall[j] = 1.0
        else:
            ok[j] = False
    readout, pred = {}, np.empty((Q, n, 8))
    for j in range(Q):
        qd, c, _ = fold[j]; key = f"cf{qd['cf']}_sf{qd['sf']}"
        mu, sd = np.asarray(c['descriptors']['env']['mu']), np.asarray(c['descriptors']['env']['sd'])
        if key not in readout:
            P = pca[f'calib_proj_{key}'].astype(np.float64); people = pca[f'calib_people_{key}'].tolist()
            Z = P.reshape(-1, P.shape[-1]); mz, sz = Z.mean(0), Z.std(0); sz = np.where(sz > 0, sz, 1.0)
            Y = np.concatenate([(desc['env'][didx[f"{ds}:{p}:cf{qd['cf']}:calib"]] - mu) / sd for p in people])
            readout[key] = (mz, sz, AT.ridge_fit((Z - mz) / sz, Y - Y.mean(0)))
        mz, sz, W = readout[key]
        pred[j] = ((proj[j].astype(np.float64) - mz) / sz) @ W
    F = foreign_sets(defs, qlist)
    groups = {q['id']: q.get('group') for q in read(PN.DEFS / ds / 'scan.json')['people']}
    rows, per, checks = [], {}, {'reference_max_abs': 0.0, 'primary_max_abs': 0.0, 'n_checked': 0}
    for j, i in enumerate(qlist):
        qd, c, e = fold[j]; cf = qd['cf']
        mu, sd = np.asarray(c['descriptors']['env']['mu']), np.asarray(c['descriptors']['env']['sd'])
        sy = c['descriptors']['env']['cal']['overlap_sigma']
        A = (desc['q_att'][i] - mu) / sd; I = (desc['q_ign'][i] - mu) / sd
        LA, LI = DM.gaussian_gram(A, sy), DM.gaussian_gram(I, sy)
        fj = [k for k in F[j] if ok[k]]
        row = {'query': i, 'participant_id': qd['person'], 'group': groups.get(qd['person']), 'content_fold': cf, 'person_fold': qd['sf'],
               'n_foreign': len(fj)}
        if ok[j] and fj:
            idx = [j] + fj
            _, _, xa = shift_excess(Kall[idx], LA, perms); _, _, xi = shift_excess(Kall[idx], LI, perms)
            mg = xa - xi
            row.update(dep_margin=float(mg[0]), foreign_dep_margin_mean=float(mg[1:].mean()), dep_margin_debiased=float(mg[0] - mg[1:].mean()))
            row['dep_credit_debiased'] = AT.credit(row['dep_margin_debiased'])
            if checks['n_checked'] < 5:
                ref = DM.measure_from_grams(Kall[j], LA, perms, null_design='check')
                checks['reference_max_abs'] = max(checks['reference_max_abs'], abs(ref['excess_cs_nats'] - xa[0]))
                p = prim[i]
                checks['primary_max_abs'] = max(checks['primary_max_abs'], abs(float(p['dep_margin']) - mg[0]),
                                                abs(float(p['foreign_dep_margin']) - mg[1]) if p.get('foreign_dep_margin') else 0.0)
                checks['n_checked'] += 1
        else:
            row['dep_credit_debiased'] = None
        if F[j]:
            rm = np.array([AT.colcorr(pred[k], A) - AT.colcorr(pred[k], I) for k in [j] + F[j]])
            row.update(read_margin=float(rm[0]), foreign_read_margin_mean=float(rm[1:].mean()),
                       read_margin_debiased=float(rm[0] - rm[1:].mean()))
            row['read_credit_debiased'] = AT.credit(row['read_margin_debiased'])
        else:
            row['read_credit_debiased'] = None
        rows.append(row)
        for ep in ('dep_credit_debiased', 'read_credit_debiased'):
            if row.get(ep) is not None:
                per.setdefault(qd['person'], {}).setdefault(ep, {}).setdefault(cf, []).append(row[ep])
    assert checks['reference_max_abs'] < 1e-10 and checks['primary_max_abs'] < 1e-9, checks
    people = {}
    for p, d in per.items():
        v = {'group': groups.get(p)}
        for ep, nm in (('dep_credit_debiased', 'attention20_acc_dependence_debiased'), ('read_credit_debiased', 'attention20_acc_readout_debiased')):
            by = d.get(ep, {})
            v[nm + '_by_cf'] = {str(cf): float(np.mean(by[cf])) for cf in by}
            v[nm] = float(np.mean([np.mean(by[cf]) for cf in PN.CFS])) if all(cf in by for cf in PN.CFS) else None
        people[p] = v
    out = AT.PRED / ds
    cols = sorted({k for r in rows for k in r})
    with gzip.open(out / f'{name}.debiased.queries.csv.gz', 'wt') as f:
        f.write(','.join(cols) + '\n')
        for r in rows:
            f.write(','.join('' if r.get(k) is None else (f'{r[k]:.10g}' if isinstance(r[k], float) else str(r[k])) for k in cols) + '\n')
    write(out / f'{name}.debiased.people.json', {
        'version': 'DEP12_PUB_ATTENTION_DEBIASED_v1', 'post_hoc': True, 'label': 'POST HOC / secondary (DECISIONS 2026-10-23 07:55, M18)',
        'encoder': name, 'dataset': ds, 'feature_files_sha256': info['files_sha256'], 'k_foreign': K_FOREIGN, 'foreign_seed': FOREIGN_SEED,
        'foreign_sets_sha256': PN.digest({str(k): v for k, v in F.items()}), 'checks': checks, 'people': people, 'n_queries': len(rows),
        'queries_sha256': sha(out / f'{name}.debiased.queries.csv.gz'), 'sources': sources(), 'seconds': time.time() - t0,
        'job': os.environ.get('SLURM_JOB_ID'), 'time': datetime.now().astimezone().isoformat()})
    a = [v['attention20_acc_dependence_debiased'] for v in people.values() if v['attention20_acc_dependence_debiased'] is not None]
    b = [v['attention20_acc_readout_debiased'] for v in people.values() if v['attention20_acc_readout_debiased'] is not None]
    print(name, ds, 'debiased', 'a', round(float(np.mean(a)), 4) if a else None, 'b', round(float(np.mean(b)), 4) if b else None,
          'checks', checks, round(time.time() - t0, 1), 's', flush=True)


def done(name, ds):
    p = AT.PRED / ds / f'{name}.debiased.people.json'
    if not p.exists() or not AT.done(name, ds):
        return False
    return read(p)['feature_files_sha256'] == PF.feature_dir(name, ds)[1]['files_sha256']


def run_all(first=None):
    """Every encoder whose primary attention is done; per-item fcntl lock; `first` = names to process first."""
    LOCKS.mkdir(parents=True, exist_ok=True, mode=0o700)
    items = [(r['dataset'], n) for r in PF.plan_rows() if (PF.FEAT / 'units' / f'{r["id"]}.json').exists() for n in r['encoders']]
    if first:
        items = sorted(items, key=lambda x: (x[1] not in first, x))
    for ds, n in items:
        if not AT.done(n, ds) or done(n, ds):
            continue
        with (LOCKS / f'deb__{ds}__{n}.lock').open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if not done(n, ds):
                run(n, ds)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=('run', 'run-all'))
    ap.add_argument('--encoder'); ap.add_argument('--dataset', choices=PN.DATASETS); ap.add_argument('--first', nargs='*')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    if a.step == 'run':
        run(a.encoder, a.dataset)
    else:
        run_all(set(a.first or []))


if __name__ == '__main__':
    main()
