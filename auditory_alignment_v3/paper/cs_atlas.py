"""Paper line W1 (docs/auditory_alignment_v3/paper/PR_STORY_BLUEPRINT.md §2C): Cauchy–Schwarz dependence atlas on stored
representations. CPU, read-only on frozen arrays; exploratory, designed after ALN4.1 R1 and the ALN4.2 source diagnosis.

Estimator: Gaussian-kernel CS-QMI with the formula of aln41.cs_qmi_reference.cs_qmi (uniform weights, V-statistic, natural logs)
    CS(U;S) = log mean(K∘L) + log[mean(K)·mean(L)] − 2 log mean_i(k̄_i·l̄_i)  (≥ 0 by Cauchy–Schwarz),
    K_ij = exp(−‖u_i − u_j‖² / 2σ_u²), L likewise on the stimulus target.
Bandwidths: the reference calibrate_overlap_sigma rule (lower median of off-diagonal distances, multiplier 1) on at most
SIGMA_ROWS training-people rows (fixed RNG), separately for every representation space and every target of a cell.
Per test person: CS on that person's test-role anchors. Null: within-person segment roll — whole segments rotated by r, so each
EEG segment meets another segment's sound of the same person (marginals, within-segment structure and B unchanged).
Excess dependence D = CS_true − mean_r CS_roll(r); z = D / sd_r over R_ROLLS evenly spaced r (all r if fewer segments).
Control 'noise' (aln41 only): U replaced by Gaussian rows with the training rows' mean and covariance (zero-point check).
Sources:
  aln41  frozen CBraMod tokens, PCA64 per slot W0/W1/W2 (crops [−0.2,0.2), [0,0.4), [0.2,0.6) s around the anchor); arms B0,
         TCS, TNCE, GCS, TCS_WRONG; DTU / FAU; content folds 0/1; seeds 3401 and R2 3407 / 3413 (B0 is seed-free). Test people of
         person fold sf (source-dev people excluded) with that fold's train-people PCA. Targets: env (train-standardised) and
         env|history (env minus its train-fitted ridge prediction from its own 20/100/200/500 ms past, aln34 content_time.fitted).
  aln34  content/time cache: target-trained 32-d encoders (local / CBraMod pre / CBraMod random / REVE pre) at five 1-s access
         centres, plus the local units' raw-EEG 64-channel reference; targets = aln34 content_time.target_views (six attributes
         direct, each conditional on the preceding attributes, and env|history), train-scaled.
Usage: `python -m auditory_alignment_v3.paper.cs_atlas plan` then `run --source aln41|aln34` (Slurm), then `summarize`.
Outputs: private/auditory_alignment_v3/paper/cs_atlas_v1/plan.json; results/auditory_alignment_v3/paper/cs_atlas/
{cells_<source>.csv.gz, receipt_<source>.json, summary.json, ATLAS.md}.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import json
import os
from pathlib import Path
import time

import numpy as np

from .. import core
from ..aln34 import content_time as CT, learning_budget as B
from ..aln41 import frozen as FZ, r2 as R2, source as SRC

PLAN_DIR = Path(core.OUT) / 'paper' / 'cs_atlas_v1'
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/paper/cs_atlas'
R_ROLLS, SIGMA_ROWS, RNG_SEED = 20, 2000, 20261021
SEEDS = (3401, 3407, 3413)
COLUMNS = ('source', 'dataset', 'model', 'seed', 'content_fold', 'person_fold', 'person', 'group', 'rep', 'target', 'n', 'n_segments',
           'n_rolls', 'sigma_u', 'sigma_s', 'cs_true', 'null_mean', 'null_sd', 'excess', 'z')


# ----------------------------------------------------------------------------------------------- estimator
def sqdist(x):
    n = (x * x).sum(1); d = n[:, None] + n[None] - 2.0 * (x @ x.T)
    np.maximum(d, 0.0, out=d); np.fill_diagonal(d, 0.0); return d


def gram(x, sigma):
    return np.exp(-sqdist(np.asarray(x, np.float64)) / (2.0 * sigma * sigma))


def sigma_rule(rows, rng):
    """Reference calibrate_overlap_sigma on a fixed-RNG subsample of training rows."""
    import torch
    from ..aln41.cs_qmi_reference import calibrate_overlap_sigma
    rows = np.asarray(rows, np.float64)
    if len(rows) > SIGMA_ROWS:
        rows = rows[np.sort(rng.choice(len(rows), SIGMA_ROWS, replace=False))]
    return calibrate_overlap_sigma(torch.as_tensor(rows))[0]


def cs_value(K, L):
    kb, lb = K.mean(1), L.mean(1)
    return float(np.log((K * L).mean()) + np.log(kb.mean() * lb.mean()) - 2.0 * np.log((kb * lb).mean()))


def roll_values(K, L, nb, m, rolls):
    """CS for each segment roll r: stimulus block a+r paired with EEG block a (row order = segment-major, m anchors each)."""
    K4, L4 = K.reshape(nb, m, nb, m), L.reshape(nb, m, nb, m)
    kb, lb = K.mean(1).reshape(nb, m), L.mean(1).reshape(nb, m)
    logB = np.log(K.mean() * L.mean()); out = []
    for r in rolls:
        Lr = np.roll(np.roll(L4, -r, axis=0), -r, axis=2)
        A = (K4 * Lr).mean(); C = (kb * np.roll(lb, -r, axis=0)).mean()
        out.append(float(np.log(A) + logB - 2.0 * np.log(C)))
    return np.array(out)


def rolls_for(nb):
    return list(range(1, nb)) if nb - 1 <= R_ROLLS else sorted({int(round(x)) for x in np.linspace(1, nb - 1, R_ROLLS)})


def person_cells(reps, targets, seg, sig_u, sig_s):
    """reps / targets: {name: [n, d]} for one person's rows (segment-major); yields (rep, target, values)."""
    order = np.argsort(seg, kind='stable'); seg = seg[order]
    blocks, counts = np.unique(seg, return_counts=True); m = int(counts[0]); nb = len(blocks)
    assert (counts == m).all() and nb >= 3, 'equal anchors per segment and >= 3 segments required'
    rolls = rolls_for(nb)
    Ls = {t: gram(y[order], sig_s[t]) for t, y in targets.items()}
    for rname, u in reps.items():
        K = gram(u[order], sig_u[rname])
        for t, L in Ls.items():
            true = cs_value(K, L); null = roll_values(K, L, nb, m, rolls)
            yield rname, t, {'n': len(seg), 'n_segments': nb, 'n_rolls': len(rolls), 'sigma_u': sig_u[rname], 'sigma_s': sig_s[t],
                             'cs_true': true, 'null_mean': float(null.mean()), 'null_sd': float(null.std(ddof=1)),
                             'excess': true - float(null.mean()), 'z': (true - float(null.mean())) / max(float(null.std(ddof=1)), 1e-300)}


def reference_check(rng):
    """The numpy estimator equals aln41.cs_qmi_reference.cs_qmi on random data (true and one rolled pairing)."""
    import torch
    from ..aln41.cs_qmi_reference import cs_qmi
    u = rng.normal(size=(48, 7)); s = u[:, :2] + rng.normal(size=(48, 2)); su, ss = 2.5, 1.3
    ref = float(cs_qmi(torch.as_tensor(u), torch.as_tensor(s), sigma_u=su, sigma_v=ss)[0])
    mine = cs_value(gram(u, su), gram(s, ss))
    perm = np.roll(np.arange(48).reshape(6, 8), -2, axis=0).reshape(-1)
    ref_r = float(cs_qmi(torch.as_tensor(u), torch.as_tensor(s[perm]), sigma_u=su, sigma_v=ss)[0])
    mine_r = float(roll_values(gram(u, su), gram(s, ss), 6, 8, [2])[0])
    assert abs(ref - mine) < 1e-9 and abs(ref_r - mine_r) < 1e-9, (ref, mine, ref_r, mine_r)
    return {'true_ref': ref, 'true_numpy': mine, 'roll2_ref': ref_r, 'roll2_numpy': mine_r}


# ----------------------------------------------------------------------------------------------- unit lists
def aln41_units():
    out = []
    for seed in SEEDS:
        ctx = R2.seeded(seed) if seed != SRC.SEED else contextlib.nullcontext()
        with ctx:
            assert seed == SRC.SEED or f'seed{seed}' in str(FZ.BASE)
            for row in FZ.read(FZ.BASE / 'plan.json')['rows']:
                if row['dataset'] not in ('dtu', 'fau'):
                    continue
                rec = FZ.read(FZ.BASE / 'units' / f'{row["id"]}.json'); assert rec['status'] == 'complete' and not rec['probe']
                out.append({'source': 'aln41', 'id': row['id'], 'seed': seed, 'arm': row['arm'], 'dataset': row['dataset'],
                            'content_fold': row['content_fold'], 'dest': rec['dest'], 'array_sha256': rec['array_sha256'],
                            'meta_sha256': rec['meta_sha256']})
    return out


def aln34_units():
    out = []
    for d in sorted((CT.STORE / 'cache').glob('ALN34T_*')):
        meta = json.loads((d / 'meta.json').read_text()); src = meta['unit']['source']
        assert not meta['probe']
        out.append({'source': 'aln34', 'id': d.name, 'seed': src['seed'], 'arm': CT.label(src), 'dataset': src['dataset'],
                    'content_fold': src['content_fold'], 'person_fold': src['subject_fold'], 'dest': str(d),
                    'array_sha256': meta['array_sha256'], 'meta_sha256': B.sha(d / 'meta.json')})
    return out


def make_plan():
    PLAN_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = PLAN_DIR / 'plan.json'; assert not path.exists(), 'plan is frozen'
    plan = {'version': 'CS_ATLAS_v1', 'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'module_sha256': B.sha(Path(__file__)),
            'reference_sha256': B.sha(Path(core.REPO) / 'auditory_alignment_v3/aln41/cs_qmi_reference.py'),
            'settings': {'R_ROLLS': R_ROLLS, 'SIGMA_ROWS': SIGMA_ROWS, 'RNG_SEED': RNG_SEED, 'sigma_multiplier': 1.0},
            'units': aln41_units() + aln34_units()}
    path.write_text(json.dumps(plan, indent=1) + '\n'); os.chmod(path, 0o444)
    print(path, len(plan['units']), 'units')


def open_plan():
    plan = json.loads((PLAN_DIR / 'plan.json').read_text())
    assert plan['module_sha256'] == B.sha(Path(__file__)), 'cs_atlas changed after the plan was frozen; make a new version'
    return plan


# ----------------------------------------------------------------------------------------------- per source
def standardise(y, train):
    mu, sd = y[train].mean(0), y[train].std(0) + 1e-8
    return (y - mu) / sd


def run_aln41(u, rng, write):
    dest = Path(u['dest']); assert B.sha(dest / 'arrays.npz') == u['array_sha256'] and B.sha(dest / 'meta.json') == u['meta_sha256']
    meta = json.loads((dest / 'meta.json').read_text()); dev = set(meta['dev_people'])
    with np.load(dest / 'arrays.npz', allow_pickle=False) as z:
        person, role, seg = z['person'], z['role'], z['segment']; env, hist = z['env'][:, None], z['env_history']
        for sf in range(5):
            P = z[f'pca_sf{sf}'].astype(np.float64)
            train = np.isin(person, sorted(meta['pca'][str(sf)]['train_people'])) & np.isin(role, ('fit', 'es'))
            w, b, _ = CT.fitted(hist[train], env[train], role[train])
            targets = {'env': standardise(env, train), 'env|history': standardise(env - (hist @ w + b), train)}
            sig_s = {t: sigma_rule(y[train], rng) for t, y in targets.items()}
            reps = {f'W{k}': P[:, k] for k in range(3)}; sig_u = {r: sigma_rule(x[train], rng) for r, x in reps.items()}
            mu, cov = P[train, 1].mean(0), np.cov(P[train, 1], rowvar=False); chol = np.linalg.cholesky(cov + 1e-9 * np.eye(len(mu)))
            sig_u['noise'] = sig_u['W1']
            people = sorted(p for p, f in meta['folds'].items() if f == sf and p not in dev)
            for p in people:
                ix = np.flatnonzero((person == p) & (role == 'test'))
                if not len(ix):
                    continue
                pr = {r: x[ix] for r, x in reps.items()}; pr['noise'] = mu + rng.normal(size=(len(ix), len(mu))) @ chol.T
                for rname, t, v in person_cells(pr, {t: y[ix] for t, y in targets.items()}, seg[ix], sig_u, sig_s):
                    write({'source': 'aln41', 'dataset': u['dataset'], 'model': u['arm'], 'seed': u['seed'], 'content_fold': u['content_fold'],
                           'person_fold': sf, 'person': p, 'group': meta['groups'].get(p), 'rep': rname, 'target': t, **v})


def run_aln34(u, rng, write):
    dest = Path(u['dest']); assert B.sha(dest / 'arrays.npz') == u['array_sha256'] and B.sha(dest / 'meta.json') == u['meta_sha256']
    meta = json.loads((dest / 'meta.json').read_text())
    with np.load(dest / 'arrays.npz', allow_pickle=False) as z:
        A = {k: z[k] for k in z.files}
    targets, _ = CT.target_views(A); role, person, seg = A['role'], A['person'], A['segment']; train = role != 'test'
    sig_s = {t: sigma_rule(y[train], rng) for t, y in targets.items()}
    reps = {f'{kind}_{c}': A[f'{kind}_{c}'].astype(np.float64) for kind in ('model', 'raw') for c in CT.CENTERS if f'{kind}_{c}' in A}
    sig_u = {r: sigma_rule(x[train], rng) for r, x in reps.items()}
    for p in sorted(set(person[role == 'test'].tolist())):
        ix = np.flatnonzero((person == p) & (role == 'test'))
        for rname, t, v in person_cells({r: x[ix] for r, x in reps.items()}, {t: y[ix] for t, y in targets.items()}, seg[ix], sig_u, sig_s):
            write({'source': 'aln34', 'dataset': u['dataset'], 'model': u['arm'], 'seed': u['seed'], 'content_fold': u['content_fold'],
                   'person_fold': u['person_fold'], 'person': p, 'group': meta['groups'].get(p), 'rep': rname, 'target': t, **v})


def run(source):
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    plan = open_plan(); rng = np.random.default_rng(RNG_SEED)
    check = reference_check(np.random.default_rng(RNG_SEED + 1))
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f'cells_{source}.csv.gz'; assert not out.exists(), 'output exists'
    tmp = out.with_suffix('.tmp'); t0 = time.time(); n = 0; done = []
    with gzip.open(tmp, 'wt', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator='\n'); w.writeheader()

        def write(row):
            nonlocal n
            w.writerow({k: (f'{v:.10g}' if isinstance(v, float) else v) for k, v in row.items()}); n += 1
        for u in plan['units']:
            if u['source'] != source:
                continue
            (run_aln41 if source == 'aln41' else run_aln34)(u, rng, write)
            done.append(u['id']); print(f'{len(done)} {u["id"]} {u["arm"]} {u["dataset"]} s{u["seed"]} cells={n} {time.time() - t0:.0f}s', flush=True)
    os.replace(tmp, out)
    (RESULTS / f'receipt_{source}.json').write_text(json.dumps({
        'version': plan['version'], 'job': os.environ['SLURM_JOB_ID'], 'plan_sha256': B.sha(PLAN_DIR / 'plan.json'),
        'module_sha256': plan['module_sha256'], 'reference_check': check, 'units': done, 'cells': n,
        'cells_sha256': B.sha(out), 'seconds': time.time() - t0}, indent=1) + '\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=('plan', 'run', 'summarize'))
    ap.add_argument('--source', choices=('aln41', 'aln34')); a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID')
    if a.step == 'plan':
        make_plan()
    elif a.step == 'run':
        run(a.source)
    else:
        from . import cs_atlas_summary
        cs_atlas_summary.main()


if __name__ == '__main__':
    main()
