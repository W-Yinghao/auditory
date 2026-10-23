"""DEP12 common dependence measurement v2 (Agent M; = measure.py v1 reading public_features_v2 incl. plan_ext1; package v1.2 03 §4.1-4.3, §4.5; 02 §5.2; 05 §2).

Estimator, kernels, null summaries and diagnostics come from dep12/dependence_measure.py, a byte copy of the package reference
(sha256 asserted). Only two thin adapters are added because U is stored as exact squared distances (DECISIONS M5):
  gram_from_d2(d2, sigma)             = reference gaussian_gram's formula exp(-0.5 * (d2 / s) / s) on precomputed d2
  calibrate_grouped_from_d2(...)      = reference calibrate_grouped_overlap_sigma (pooled within-person upper-triangle
                                        distances, lower median, reference _lower_median_bandwidth) from per-person d2
Both are checked against the reference functions on random rows (check_adapters) before any measurement.
Descriptors are rows, so the reference gaussian_gram / calibrate_grouped_overlap_sigma are used on them directly.

Per encoder x cohort x content fold cf x person fold sf (encoder scope):
  calibration (access target_train_unlabelled): σ_u = grouped lower median over the training people's calib panels (n = 128 each);
  per descriptor: column mean / SD and σ_y from the same panels' descriptor rows (shared by every encoder). States
  constant_representation (all calib distances 0: K = 1, raw / null / excess 0, z unavailable) and calibration_degenerate
  (median 0 otherwise: kernel measurement not estimable) are recorded, never patched with an epsilon.
  measurement for each test person of sf (test panel of cf): raw CS, A/B/C, 199-draw block-shift null (mean, SD, all draws),
  signed excess, z / status, kernel diagnostics, n, σ_u, σ_y; conditions
    main      own EEG,                                 n128, σ x 1   (the F_MEASURE endpoint)
    partner   same-stimulus other listener's EEG,      blocks with a partner (own_on_partner_blocks alongside)
    noise     i.i.d. N(0,1) native windows,            n128, σ x 1
    sens      DTU env, seed-3401 / seedless encoders: n32 (block 1), n64 (blocks 1-2) at σ x 1; n128 at σ x 0.5 and x 2
              (multiplier applied to both calibrated kernels; nested panels; σ of the n128 calibration)
Person value = mean of the two content folds (both required; missing stays missing).
Outputs: results/auditory_alignment_v3/dep12/measurement/public/<ds>/<encoder>/{cells.jsonl.gz, nulls.npz, calibration.json}
CLI (Slurm only): python -m auditory_alignment_v3.dep12.measure {check, run --encoder NAME [--dataset ds], run-all, status}
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

from .. import core
from . import dependence_measure as DM
from . import panels as PN
from . import public_features_v2 as PF

REFERENCE_SHA256 = '22cf63e144b76c97c4dd69b78dac507580d7a5187e2add87cd5916f83fb31005'
PACKAGE_REFERENCE = Path(core.REPO) / 'private/auditory_alignment_v3/dep12/package/reference/dependence_measure.py'
RESULTS = Path(core.REPO) / 'results' / 'auditory_alignment_v3' / 'dep12'
MEAS = RESULTS / 'measurement' / 'public'
DESCRIPTORS = ('env', 'spec', 'Lz')
SCOPE = 'target_train_unlabelled'
SENS_MULTS = (0.5, 2.0)
sha, write, read, digest = PN.sha, PN.write, PN.read, PN.digest


def check_reference():
    assert sha(Path(DM.__file__)) == REFERENCE_SHA256 == sha(PACKAGE_REFERENCE), 'dependence_measure.py is not the package byte copy'
    return REFERENCE_SHA256


def sources():
    here = Path(__file__).parent
    return {str(p.relative_to(core.REPO)): sha(p) for p in (here / 'measure_v2.py', here / 'dependence_measure.py', here / 'panels.py',
                                                             here / 'public_features_v2.py')}


# ------------------------------------------------------------------------------------------------ adapters (checked)
def gram_from_d2(d2, sigma):
    s = DM._sigma(sigma, 'sigma')
    d2 = np.asarray(d2, np.float64)
    with np.errstate(over='ignore', under='ignore', invalid='raise'):
        k = np.exp(-0.5 * ((d2 / s) / s))
    if not np.isfinite(k).all():
        raise ValueError('Nonfinite Gaussian kernel')
    return k


def calibrate_grouped_from_d2(d2_by_person, *, calibration_scope, panel_id, multiplier=1.0):
    DM._validate_calibration_provenance(calibration_scope, panel_id)
    ids, dist, shape = [], [], None
    for pid, d2 in d2_by_person.items():
        d2 = np.asarray(d2, np.float64)
        assert d2.ndim == 2 and d2.shape[0] == d2.shape[1] >= 2 and np.isfinite(d2).all()
        if shape is None:
            shape = d2.shape
        elif d2.shape != shape:
            raise ValueError('Every person must have the same fixed anchor count')
        ids.append(pid); dist.append(np.sqrt(np.maximum(d2[np.triu_indices(len(d2), 1)], 0.0)))
    distances = np.concatenate(dist)
    return {**DM._lower_median_bandwidth(distances, multiplier),
            'rule': 'pooled_within_person_offdiagonal_lower_median_including_zeros', 'n_people': len(ids), 'person_ids': ids,
            'n_rows_per_person': int(shape[0]), 'n_pairs_per_person': int(shape[0] * (shape[0] - 1) // 2),
            'cross_person_pairs_included': False, 'equal_person_pair_weight': True, 'calibration_scope': calibration_scope,
            'panel_id': panel_id, 'adapter': 'calibrate_grouped_from_d2 (reference rule on precomputed squared distances)'}


def check_adapters(seed=0):
    rng = np.random.default_rng(seed); out = {}
    rows = {f'p{i}': rng.normal(size=(40, 300)) * (1 + i) for i in range(5)}
    ref = DM.calibrate_grouped_overlap_sigma(rows, calibration_scope=SCOPE, panel_id='check')
    d2 = {k: DM._pairwise_squared_distances(v) for k, v in rows.items()}
    mine = calibrate_grouped_from_d2(d2, calibration_scope=SCOPE, panel_id='check')
    out['calibration_rel_diff'] = abs(mine['overlap_sigma'] - ref['overlap_sigma']) / ref['overlap_sigma']
    x = rows['p1']; s = ref['overlap_sigma']
    g_ref = DM.gaussian_gram(x, s); g = gram_from_d2(DM._pairwise_squared_distances(x).astype(np.float32), s)
    out['gram_max_abs_diff_float32_d2'] = float(np.abs(g - g_ref).max())
    perms = np.stack([np.roll(np.arange(40), k) for k in (5, 11, 17)])
    y = rng.normal(size=(40, 3)); L = DM.gaussian_gram(y, 1.3)
    a = DM.measure_from_grams(g_ref, L, perms, null_design='check'); b = DM.measure_from_grams(g, L, perms, null_design='check')
    out['excess_abs_diff'] = abs(a['excess_cs_nats'] - b['excess_cs_nats'])
    assert out['calibration_rel_diff'] < 1e-12 and out['gram_max_abs_diff_float32_d2'] < 1e-5 and out['excess_abs_diff'] < 1e-5, out
    # block-shift permutations: rows stay in their block, each a derangement for legal shifts
    P = PN.perms_from_shifts(np.array([[4, 28, 16, 5]]), 4)[0]
    assert sorted(P.tolist()) == list(range(128)) and all(set(P[b * 32:(b + 1) * 32]) == set(range(b * 32, (b + 1) * 32)) for b in range(4))
    assert not np.any(P == np.arange(128))
    out['block_perm_ok'] = True
    return out


# ------------------------------------------------------------------------------------------------ helpers
def full_d2(cond, n=PN.QUERY_N):
    D = np.zeros((n, n), np.float64); iu = np.triu_indices(n, 1)
    D[iu] = cond; D[(iu[1], iu[0])] = cond
    return D


def standardizer(rows):
    mu = rows.mean(0); sd = rows.std(0)
    sd = np.where(sd > 0, sd, 1.0)
    return mu, sd


def cell_record(res, keep_nulls):
    out = {k: res[k] for k in ('raw_cs_nats', 'joint_square', 'marginal_product_square', 'cross_overlap', 'null_mean_nats', 'null_sd_nats',
                               'excess_cs_nats', 'z', 'z_status', 'n_rows', 'n_null_draws', 'n_unique_permutations',
                               'n_identity_permutations', 'null_design', 'null_sd_threshold')}
    out['k_diagnostics'] = res['k_diagnostics']; out['l_diagnostics'] = res['l_diagnostics']
    keep_nulls.append(np.asarray(res['null_scores_nats'], np.float64))
    return out


def bank(defs, key, blocks):
    """Null permutations of the panel rows restricted to `blocks` (in order), from the frozen tuples; duplicates removed."""
    tuples = np.asarray(defs['null_banks'][key], np.int64)
    if tuples.shape[1] > len(blocks):
        tuples = tuples[:, :len(blocks)]
    tuples = np.unique(tuples, axis=0) if len(blocks) < np.asarray(defs['null_banks'][key]).shape[1] else tuples
    return PN.perms_from_shifts(tuples, len(blocks))


def descriptor_calibration(ds, defs, desc, cf, sf, people):
    """Per descriptor: column standardiser and σ_y from the training people's calib panels (encoder independent)."""
    idx = {p: i for i, p in enumerate(desc['panel_ids'].tolist())}
    out = {}
    for name in DESCRIPTORS:
        rows = {p: desc[name][idx[f'{ds}:{p}:cf{cf}:calib']].astype(np.float64) for p in people}
        mu, sd = standardizer(np.concatenate(list(rows.values())))
        z = {p: (v - mu) / sd for p, v in rows.items()}
        cal = DM.calibrate_grouped_overlap_sigma(z, calibration_scope=SCOPE, panel_id=f'{ds}:cf{cf}:sf{sf}:calib:{name}')
        out[name] = {'mu': mu, 'sd': sd, 'cal': {k: v for k, v in cal.items() if k != 'person_ids'},
                     'people_sha': digest(sorted(people), 16)}
    return out


def eeg_calibration(d2_calib, people, ds, cf, sf, name, mult=1.0):
    pid = f'{ds}:cf{cf}:sf{sf}:calib:{name}'
    d2 = {p: d2_calib[p] for p in people}
    try:
        cal = calibrate_grouped_from_d2(d2, calibration_scope=SCOPE, panel_id=pid, multiplier=mult)
        return {'status': 'ok', **{k: v for k, v in cal.items() if k != 'person_ids'}}
    except ValueError as exc:
        allzero = all(float(np.max(v)) == 0.0 for v in d2.values())
        return {'status': 'constant_representation' if allzero else 'calibration_degenerate', 'error': str(exc)[:200],
                'max_distance': float(max(np.sqrt(np.max(v)) for v in d2.values())), 'panel_id': pid, 'multiplier': mult}


# ------------------------------------------------------------------------------------------------ one encoder x cohort
def run(name, ds, probe_dir=None, out_root=None):
    """probe_dir / out_root: engineering checks on a probe feature directory, written outside results/."""
    t0 = time.time(); check_reference()
    if probe_dir is None:
        dest, rec = PF.feature_dir(name, ds)
        assert dest is not None, f'{name} {ds}: no completed feature unit'
    else:
        dest = Path(probe_dir); rec = {'files_sha256': read(dest / 'meta.json')['files_sha256']}
    info = read(dest / 'meta.json'); assert info['files_sha256'] == rec['files_sha256']
    for f, h in info['files_sha256'].items():
        assert sha(dest / f) == h, f
    defs = PN.defs(ds); assert info['defs_sha256'] == PF.defs_hash(ds)
    desc = PF.load_descriptors(ds)
    didx = {p: i for i, p in enumerate(desc['panel_ids'].tolist())}
    with np.load(dest / 'panels.npz', allow_pickle=False) as z:
        P = {k: z[k] for k in z.files}
    pidx = {p: i for i, p in enumerate(P['ids'].tolist())}; tidx = {p: i for i, p in enumerate(P['test_ids'].tolist())}
    coh_train, coh_test = {}, {}
    from ..paper import ext_common as X
    c = X.Cache(ds)
    for sf in PN.SFS:
        coh_train[sf], coh_test[sf] = c.unit_people(sf)
    groups = {q['id']: q.get('group') for q in read(PN.DEFS / ds / 'scan.json')['people']}
    out_dir = (Path(out_root) if out_root else MEAS) / ds / name; out_dir.mkdir(parents=True, exist_ok=True)
    cells, nulls, calib = [], [], {}
    seedless_or_3401 = info['registry'].get('seed') in (None, 3401)
    for cf, sf in [tuple(s) for s in info['scope']]:
        people = sorted(p for p in coh_train[sf] if f'{ds}:{p}:cf{cf}:calib' in pidx)
        if not people:
            continue
        d2c = {p: P['d2'][pidx[f'{ds}:{p}:cf{cf}:calib']] for p in people}
        dcal = descriptor_calibration(ds, defs, desc, cf, sf, people)
        ecal = {m: eeg_calibration(d2c, people, ds, cf, sf, name, m) for m in (1.0,) + SENS_MULTS}
        calib[f'cf{cf}_sf{sf}'] = {'eeg': ecal, 'descriptors': {k: {'cal': v['cal'], 'mu': v['mu'].tolist(), 'sd': v['sd'].tolist(),
                                                                       'people_sha': v['people_sha']} for k, v in dcal.items()},
                                   'people': people}
        for p in sorted(coh_test[sf]):
            panel = f'{ds}:{p}:cf{cf}:test'
            if panel not in tidx:
                continue
            pn = defs['panels'][panel]; nb = len(pn['blocks'])
            Y = {k: (desc[k][didx[panel]].astype(np.float64) - dcal[k]['mu']) / dcal[k]['sd'] for k in DESCRIPTORS}
            base = {'cohort': ds, 'encoder': name, 'content_fold': cf, 'person_fold': sf, 'participant_id': p, 'panel_id': panel,
                    'group': groups.get(p)}

            def emit(cond, desc_name, d2, rows, blocks, key, mult, extra=None):
                st = ecal[mult]['status']
                rec = {**base, 'condition': cond, 'descriptor': desc_name, 'n_anchors': len(rows), 'sigma_multiplier': mult,
                       'blocks': list(blocks), 'null_bank': key}
                if st == 'calibration_degenerate':
                    cells.append({**rec, 'status': 'calibration_degenerate', 'missing_reason': ecal[mult]['error']}); return
                sy = dcal[desc_name]['cal']['overlap_sigma'] * mult
                L = DM.gaussian_gram(Y[desc_name][rows], sy)
                if st == 'constant_representation':
                    K = np.ones((len(rows), len(rows))); su = None
                else:
                    su = ecal[mult]['overlap_sigma']; K = gram_from_d2(d2[np.ix_(rows, rows)], su)
                perms = bank(defs, key, blocks)
                res = DM.measure_from_grams(K, L, perms, null_design=defs['null_design'][key] + f':blocks{"".join(map(str, blocks))}')
                r = cell_record(res, nulls)
                cells.append({**rec, 'status': 'completed' if st == 'ok' else 'completed_constant_representation', 'sigma_u': su,
                              'sigma_y': sy, 'null_index': len(nulls) - 1, **r, **(extra or {})})
            own = P['d2'][pidx[panel]]
            allrows = np.arange(nb * PN.BLOCK_N)
            for dn in DESCRIPTORS:
                emit('main', dn, own, allrows, range(nb), 'n128', 1.0)
                emit('noise', dn, P['noise_d2'][tidx[panel]].astype(np.float64), allrows, range(nb), 'n128', 1.0)
                mask = P['partner_mask'][tidx[panel]]
                pb = [j for j in range(nb) if mask[j]]
                if pb:
                    rows = np.concatenate([np.arange(j * 32, (j + 1) * 32) for j in pb])
                    key = {4: 'n128', 3: 'n128', 2: 'n64', 1: 'n32'}[len(pb)]
                    pd2 = P['partner_d2'][tidx[panel]].astype(np.float64)
                    sub_d2 = np.zeros((nb * 32, nb * 32)); sub_d2[np.ix_(rows, rows)] = pd2[np.ix_(rows, rows)]
                    emit('partner', dn, sub_d2, rows, pb, key, 1.0, {'partner_blocks': len(pb),
                                                                     'partners': [pn['partners'][j]['person'] for j in pb]})
                    if len(pb) < nb:
                        emit('own_on_partner_blocks', dn, own, rows, pb, key, 1.0)
                else:
                    cells.append({**base, 'condition': 'partner', 'descriptor': dn, 'status': 'missing',
                                  'missing_reason': 'no other listener with the same stimulus covering any block'})
            if ds == 'dtu' and seedless_or_3401:
                emit('sens_n32', 'env', own, np.arange(32), [0], 'n32', 1.0)
                emit('sens_n64', 'env', own, np.arange(64), [0, 1], 'n64', 1.0)
                for m in SENS_MULTS:
                    emit(f'sens_sigma_x{m:g}', 'env', own, allrows, range(nb), 'n128', m)
    with gzip.open(out_dir / 'cells.jsonl.gz', 'wt') as f:
        for cell in cells:
            f.write(json.dumps(cell, allow_nan=False, default=float) + '\n')
    lens = np.array([len(x) for x in nulls], np.int64)
    np.savez(out_dir / 'nulls.npz', flat=np.concatenate(nulls) if nulls else np.zeros(0), offsets=np.r_[0, np.cumsum(lens)].astype(np.int64))
    receipt = {'version': 'DEP12_PUB_MEASURE_v1', 'encoder': name, 'dataset': ds, 'feature_dir': str(dest), 'feature_meta': info,
               'calibration': calib, 'n_cells': len(cells), 'cells_sha256': sha(out_dir / 'cells.jsonl.gz'), 'nulls_sha256': sha(out_dir / 'nulls.npz'),
               'reference_sha256': REFERENCE_SHA256, 'adapter_check': check_adapters(), 'sources': sources(),
               'seconds': time.time() - t0, 'job': os.environ.get('SLURM_JOB_ID'), 'time': datetime.now().astimezone().isoformat()}
    write(out_dir / 'calibration.json', receipt)
    print(name, ds, 'cells', len(cells), round(time.time() - t0, 1), 's', flush=True)
    return receipt


def done(name, ds):
    p = MEAS / ds / name / 'calibration.json'
    if not p.exists():
        return False
    dest, rec = PF.feature_dir(name, ds)
    return dest is not None and read(p)['feature_meta']['files_sha256'] == rec['files_sha256']


def run_all():
    for row in PF.plan_rows():
        if not (PF.FEAT / 'units' / f'{row["id"]}.json').exists():
            continue
        for name in row['encoders']:
            if not done(name, row['dataset']):
                run(name, row['dataset'])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=('check', 'run', 'run-all', 'status'))
    ap.add_argument('--encoder'); ap.add_argument('--dataset', choices=PN.DATASETS)
    ap.add_argument('--probe-dir'); ap.add_argument('--out-root')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    if a.step == 'check':
        print(json.dumps({'reference': check_reference(), **check_adapters()}))
    elif a.step == 'run':
        for ds in ([a.dataset] if a.dataset else PN.DATASETS):
            run(a.encoder, ds, a.probe_dir, a.out_root)
    elif a.step == 'run-all':
        run_all()
    else:
        print({f'{r["dataset"]}:{n}': done(n, r['dataset']) for r in PF.plan_rows() for n in r['encoders']
               if (PF.FEAT / 'units' / f'{r["id"]}.json').exists()})


if __name__ == '__main__':
    main()
