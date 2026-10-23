"""DEP12 public 20 s attention decision (Agent M; package v1.2 02 §6.1, 03 §4.3; DECISIONS M8).

Queries, anchors and null shifts: dep12/panels.py (frozen). Representation distances / PCA projections: dep12/public_features.py.
Calibration: the encoder's measure.py calibration of the same (cf, sf) (σ_u from the training people's single-talker calib panels;
env standardiser and σ_env from the same panels; access target_train_unlabelled). Nothing here reads an attention label except
the final scoring line, where 'att' is the attended stream of the query.
Both candidates (attended stream A, ignored stream I, both on the query clock, standardised by the same fixed affine map) get the
same K, the same 121 circular shifts and the same scoring code:
  (a) dependence: excess(U; A) - excess(U; I) with excess = raw CS - mean over the shifts (reference measure_from_grams);
  (b) readout: PCA-16 scores (standardised on the training rows) -> ridge W = argmin mean ||Y - ZW||^2 + 0.1 ||W||^2 fitted on the
      training people's calib panels (single-talker EEG / env pairs, no attention labels); r_X = mean over the 8 env points of the
      Pearson r between Z_query W and X across the 152 anchors; margin r_A - r_I.
Decision credit: 1 if margin > 0, 0.5 if margin == 0, 0 otherwise (symmetric in the candidates). Person accuracy = mean credit of
its test windows per content fold, then the mean over both content folds (both required).
Outputs: results/auditory_alignment_v3/dep12/predictions/attention_public/<ds>/<encoder>.{queries.csv.gz, people.json}
CLI (Slurm only): python -m auditory_alignment_v3.dep12.attention {run --encoder NAME [--dataset ds], run-all, status}
"""
from __future__ import annotations

import argparse
from datetime import datetime
import gzip
import json
import os
from pathlib import Path
import time

import numpy as np

from . import dependence_measure as DM
from . import measure as M
from . import panels as PN
from . import public_features as PF

PRED = M.RESULTS / 'predictions' / 'attention_public'
RIDGE = 0.1
FOREIGN_SEED = 20261023
sha, write, read = PN.sha, PN.write, PN.read


def sources():
    here = Path(__file__).parent
    return {**M.sources(), str((here / 'attention.py').relative_to(M.core.REPO)): sha(here / 'attention.py')}


def credit(m):
    return 1.0 if m > 0 else (0.5 if m == 0 else 0.0)


def colcorr(a, b):
    a = a - a.mean(0); b = b - b.mean(0)
    den = np.sqrt((a * a).sum(0) * (b * b).sum(0))
    return float(np.mean(np.where(den > 0, (a * b).sum(0) / np.where(den > 0, den, 1.0), 0.0)))


def ridge_fit(Z, Y, lam=RIDGE):
    n = len(Z)
    return np.linalg.solve(Z.T @ Z / n + lam * np.eye(Z.shape[1]), Z.T @ Y / n)


def run(name, ds, probe_dir=None, out_root=None):
    t0 = time.time(); M.check_reference()
    dest = Path(probe_dir) if probe_dir else PF.feature_dir(name, ds)[0]; info = read(dest / 'meta.json')
    for f, h in info['files_sha256'].items():
        assert sha(dest / f) == h, f
    calp = (Path(out_root) / 'measurement' if out_root else M.MEAS) / ds / name / 'calibration.json'
    cal = read(calp)
    assert cal['feature_meta']['files_sha256'] == info['files_sha256'], 'measurement calibration is not from this feature cache'
    defs = PN.defs(ds); desc = PF.load_descriptors(ds); didx = {p: i for i, p in enumerate(desc['panel_ids'].tolist())}
    with np.load(dest / 'queries.npz', allow_pickle=False) as z:
        qidx, d2c, proj = z['qidx'], z['d2c'], z['proj']
    with np.load(dest / 'pca.npz', allow_pickle=False) as z:
        pca = {k: z[k] for k in z.files}
    shifts = defs['attention_shifts']; base = np.arange(PN.QUERY_N)
    perms = np.stack([(base + k) % PN.QUERY_N for k in shifts]).astype(np.int64)
    design = defs['null_design']['attention']
    groups = {q['id']: q.get('group') for q in read(PN.DEFS / ds / 'scan.json')['people']}
    readout, rows, per = {}, [], {}
    qlist = qidx.tolist(); Q = len(qlist)
    cache_k = {}

    def fold(j):
        qd = defs['queries'][qlist[j]]; key = f"cf{qd['cf']}_sf{qd['sf']}"; c = cal['calibration'][key]
        return qd, key, c, (c['eeg']['1.0'] if '1.0' in c['eeg'] else c['eeg'][1.0])

    def kernel(j):
        if j not in cache_k:
            _, _, _, e = fold(j)
            if e['status'] == 'ok':
                K = M.gram_from_d2(M.full_d2(d2c[j]), e['overlap_sigma'])
            elif e['status'] == 'constant_representation':
                K = np.ones((PN.QUERY_N, PN.QUERY_N))
            else:
                K = None
            cache_k.clear(); cache_k[j] = K                    # keep memory flat: one cached kernel
        return cache_k[j]

    def predict(j):
        qd, key, c, _ = fold(j)
        if key not in readout:
            mu, sd = np.asarray(c['descriptors']['env']['mu']), np.asarray(c['descriptors']['env']['sd'])
            P = pca[f'calib_proj_{key}'].astype(np.float64); people = pca[f'calib_people_{key}'].tolist()
            Z = P.reshape(-1, P.shape[-1]); mz, sz = Z.mean(0), Z.std(0); sz = np.where(sz > 0, sz, 1.0)
            Y = np.concatenate([(desc['env'][didx[f"{ds}:{p}:cf{qd['cf']}:calib"]] - mu) / sd for p in people])
            W = ridge_fit((Z - mz) / sz, Y - Y.mean(0))
            readout[key] = (mz, sz, W, {'n_rows': int(len(Z)), 'people': len(people), 'train_fit_r': colcorr(Y, ((Z - mz) / sz) @ W)})
        mz, sz, W, _ = readout[key]
        return ((proj[j].astype(np.float64) - mz) / sz) @ W

    def score(K, pred, A, I, sy):
        out = {}
        if K is not None:
            ra = DM.measure_from_grams(K, DM.gaussian_gram(A, sy), perms, null_design=design)
            ri = DM.measure_from_grams(K, DM.gaussian_gram(I, sy), perms, null_design=design)
            out.update(raw_att=ra['raw_cs_nats'], raw_ign=ri['raw_cs_nats'], null_mean_att=ra['null_mean_nats'],
                       null_mean_ign=ri['null_mean_nats'], null_sd_att=ra['null_sd_nats'], null_sd_ign=ri['null_sd_nats'],
                       excess_att=ra['excess_cs_nats'], excess_ign=ri['excess_cs_nats'],
                       dep_margin=ra['excess_cs_nats'] - ri['excess_cs_nats'])
            out['dep_credit'] = credit(out['dep_margin'])
            if ra['z'] is not None and ri['z'] is not None:
                out['depz_margin'] = ra['z'] - ri['z']; out['depz_credit'] = credit(out['depz_margin'])
            else:
                out['depz_credit'] = None; out['depz_status'] = f"{ra['z_status']}|{ri['z_status']}"
            out['k_offdiag_median'] = ra['k_diagnostics']['offdiag_median']
        else:
            out.update(dep_credit=None, depz_credit=None, dep_status='calibration_degenerate')
        r_a, r_i = colcorr(pred, A), colcorr(pred, I)
        out.update(read_r_att=r_a, read_r_ign=r_i, read_margin=r_a - r_i, read_credit=credit(r_a - r_i))
        return out
    # foreign-EEG map (DECISIONS M14): first position in a seeded permutation with the same content fold and another person
    order = np.random.default_rng(FOREIGN_SEED).permutation(Q)
    qcf = [defs['queries'][i]['cf'] for i in qlist]; qper = [defs['queries'][i]['person'] for i in qlist]
    foreign = {}
    for j in range(Q):
        foreign[j] = next((int(k) for k in order if qcf[k] == qcf[j] and qper[k] != qper[j]), None)
    for j, i in enumerate(qlist):
        qd, key, c, e = fold(j); cf, sf = qd['cf'], qd['sf']
        mu, sd = np.asarray(c['descriptors']['env']['mu']), np.asarray(c['descriptors']['env']['sd'])
        sy = c['descriptors']['env']['cal']['overlap_sigma']
        A = (desc['q_att'][i] - mu) / sd; I = (desc['q_ign'][i] - mu) / sd
        row = {'query': i, 'participant_id': qd['person'], 'group': groups.get(qd['person']), 'content_fold': cf, 'person_fold': sf,
               'trial': qd['trial'], 'st0': qd['st0']}
        row.update(score(kernel(j), predict(j), A, I, sy))
        f = foreign[j]
        if f is not None:
            fs = score(kernel(f), predict(f), A, I, sy)
            row.update({'foreign_query': qlist[f], 'foreign_participant': qper[f]},
                       **{'foreign_' + k: v for k, v in fs.items() if k in ('dep_margin', 'dep_credit', 'depz_margin', 'depz_credit',
                                                                           'read_margin', 'read_credit', 'excess_att', 'excess_ign')})
        rows.append(row)
        for ep in ('dep_credit', 'depz_credit', 'read_credit', 'foreign_dep_credit', 'foreign_read_credit',
                   'dep_margin', 'read_margin', 'foreign_dep_margin', 'foreign_read_margin'):
            if row.get(ep) is not None:
                per.setdefault(qd['person'], {}).setdefault(ep, {}).setdefault(cf, []).append(row[ep])
    people = {}
    for p, d in per.items():
        v = {'group': groups.get(p), 'n_windows': {str(cf): len(d['read_credit'].get(cf, [])) for cf in PN.CFS}}
        for ep, name_ in (('dep_credit', 'attention20_acc_dependence'), ('depz_credit', 'attention20_acc_dependence_z'),
                          ('read_credit', 'attention20_acc_readout'), ('foreign_dep_credit', 'foreign_eeg_acc_dependence'),
                          ('foreign_read_credit', 'foreign_eeg_acc_readout'), ('dep_margin', 'mean_dep_margin'),
                          ('read_margin', 'mean_read_margin'), ('foreign_dep_margin', 'mean_foreign_dep_margin'),
                          ('foreign_read_margin', 'mean_foreign_read_margin')):
            by = d.get(ep, {})
            v[name_ + '_by_cf'] = {str(cf): float(np.mean(by[cf])) for cf in by}
            v[name_] = float(np.mean([np.mean(by[cf]) for cf in PN.CFS])) if all(cf in by for cf in PN.CFS) else None
        if 'depz_credit' in d or any(r.get('depz_status') for r in rows if r['participant_id'] == p):
            v['n_windows_z_unavailable'] = sum(1 for r in rows if r['participant_id'] == p and r.get('depz_credit') is None)
        people[p] = v
    margins = {}
    for cf in PN.CFS:
        rr = [r for r in rows if r['content_fold'] == cf]
        margins[str(cf)] = {k: (float(np.mean([r[k] for r in rr if r.get(k) is not None])) if any(r.get(k) is not None for r in rr) else None)
                            for k in ('dep_margin', 'depz_margin', 'read_margin', 'foreign_dep_margin', 'foreign_depz_margin',
                                      'foreign_read_margin')}
    out = (Path(out_root) / 'attention' if out_root else PRED) / ds; out.mkdir(parents=True, exist_ok=True)
    cols = sorted({k for r in rows for k in r})
    with gzip.open(out / f'{name}.queries.csv.gz', 'wt') as f:
        f.write(','.join(cols) + '\n')
        for r in rows:
            f.write(','.join('' if r.get(k) is None else (f'{r[k]:.10g}' if isinstance(r[k], float) else str(r[k])) for k in cols) + '\n')
    receipt = {'version': 'DEP12_PUB_ATTENTION_v1', 'encoder': name, 'dataset': ds, 'feature_files_sha256': info['files_sha256'],
               'calibration_sha256': sha(calp), 'n_queries': len(rows), 'people': people,
               'readout': {k: v[3] for k, v in readout.items()}, 'null_design': design, 'n_shifts': len(shifts),
               'mean_margins_by_content_fold': margins, 'foreign_map': {'seed': FOREIGN_SEED, 'rule': 'first query of a seeded permutation '
                                                                        'with the same content fold and another person (in-scope queries)',
                                                                        'sha256': PN.digest({str(k): v for k, v in foreign.items()})},
               'queries_sha256': sha(out / f'{name}.queries.csv.gz'), 'scope': info['scope'], 'registry': info['registry'],
               'support_id': info['support_id'], 'sources': sources(), 'seconds': time.time() - t0, 'job': os.environ.get('SLURM_JOB_ID'),
               'time': datetime.now().astimezone().isoformat(),
               'access': {'eeg_calibration': 'target_train_unlabelled (training people single-talker EEG)',
                          'readout_fit': 'target-cohort training people single-talker EEG + envelope pairs; no attention labels',
                          'query_inputs': 'query EEG (20 s) + both candidate envelopes (legal inputs)',
                          'attention_labels': 'final scoring only'}}
    write(out / f'{name}.people.json', receipt)
    acc = [v['attention20_acc_dependence'] for v in people.values() if v['attention20_acc_dependence'] is not None]
    acr = [v['attention20_acc_readout'] for v in people.values() if v['attention20_acc_readout'] is not None]
    print(name, ds, 'queries', len(rows), 'people', len(acc), 'dep acc', round(float(np.mean(acc)), 4) if acc else None,
          'readout acc', round(float(np.mean(acr)), 4) if acr else None, round(time.time() - t0, 1), 's', flush=True)
    return receipt


def done(name, ds):
    p = PRED / ds / f'{name}.people.json'
    if not p.exists() or not M.done(name, ds):
        return False
    dest, rec = PF.feature_dir(name, ds)
    return read(p)['feature_files_sha256'] == rec['files_sha256']


def run_all():
    plan = read(PF.FEAT / 'plan.json')
    for row in plan['rows']:
        if not (PF.FEAT / 'units' / f'{row["id"]}.json').exists():
            continue
        for name in row['encoders']:
            if M.done(name, row['dataset']) and not done(name, row['dataset']):
                run(name, row['dataset'])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=('run', 'run-all', 'status'))
    ap.add_argument('--encoder'); ap.add_argument('--dataset', choices=PN.DATASETS)
    ap.add_argument('--probe-dir'); ap.add_argument('--out-root')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    if a.step == 'run':
        for ds in ([a.dataset] if a.dataset else PN.DATASETS):
            run(a.encoder, ds, a.probe_dir, a.out_root)
    elif a.step == 'run-all':
        run_all()
    else:
        plan = read(PF.FEAT / 'plan.json')
        print({f'{r["dataset"]}:{n}': done(n, r['dataset']) for r in plan['rows'] for n in r['encoders']})


if __name__ == '__main__':
    main()
