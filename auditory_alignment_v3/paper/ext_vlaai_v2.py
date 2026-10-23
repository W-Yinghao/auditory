"""Paper line, Table 2 row 'VLAAI' -- v2: dependency-scoped correction of the v1 swap-antisymmetry CHECK (paper/ext_vlaai.py).

What was wrong (v1, ext_vlaai.run_unit): swap_antisymmetric = np.allclose(rowcorr(P, ign[ids]) - rowcorr(P, att[ids]), -(ra - ri))
recomputed the two correlations with the float32 envelope arrays (numpy reduces float32 means in float32) while the saved
margins ra - ri use float64 copies, and allclose's default atol = 1e-8 is below that float32 round-off for margins near zero.
Unit PXVLA_b71adaac1426b919 (job 1056221) therefore ended 'check_failed' with every other check passing.  The check only gates the
unit status: training, prediction, saved margins (margins.npz) and the saved model are produced before it and are not changed.
v2: the swap check reuses the SAME float64 arrays (r_att, r_ign of the saved margins) and an explicit tolerance relative to the margin
scale (SWAP_ATOL_REL x max(1, max |margin|)); everything else is v1 code imported unchanged (same recipe, numerics, rows / ids,
storage).  v2 has its own plan / records (OUT = .../external_decoders/vlaai_v2) with the same row ids; v1 units are ADOPTED after
validation (sha of margins / model, finiteness, margin == r_att - r_ign, v2 swap check; v1 status complete, or check_failed with
swap_antisymmetric as the only failing check); v1 FAILED markers of such units are moved to vlaai/technical_failures/
swapcheck_20261022/ with a receipt.  Claims use the v1 claim locks, so a still-running v1 worker and a v2 worker never run the same
unit; a v2 worker adopts a unit that already has a v1 record instead of re-running it.
CLI (Slurm only): python -m auditory_alignment_v3.paper.ext_vlaai_v2 plan | adopt | smoke-inherit | worker [--max-units N] |
unit --id ID | score     (the sbatch passes '--system vlaai_v2', which is accepted and ignored)
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np

from . import ext_common as XC
from . import ext_fleet as XF
from . import ext_vlaai as V1

SYSTEM = 'vlaai_v2'
NAME, LANE, SBATCH = V1.NAME, V1.LANE, 'slurm/aln35_paper_ext_vlaai_v2.sbatch'
OUT = XC.OUT / 'vlaai_v2'
STORE = V1.STORE                       # unit artefacts stay at STORE/units/<id> (same ids, never run twice: shared v1 claims)
CLAIMS = V1.OUT / 'claims'
RELEASE = V1.OUT / 'technical_failures' / 'swapcheck_20261022'
SWAP_ATOL_REL = 1e-9
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def sources():
    here = Path(__file__).parent
    return {**V1.sources(), 'auditory_alignment_v3/paper/ext_vlaai_v2.py': sha(here / 'ext_vlaai_v2.py')}


def make_plan():
    v1 = read(V1.OUT / 'plan.json')
    body = {'version': 'PAPER_EXT_VLAAI_v2', 'rows': v1['rows'], 'sources': sources(), 'supersedes_plan_sha256': sha(V1.OUT / 'plan.json'),
            'correction': 'swap-antisymmetry check on the same float64 arrays with atol = 1e-9 x max(1, max|margin|); gates status only',
            **{k: v1[k] for k in ('input_index_sha256', 'released', 'recipe', 'context', 'smoke')}, 'swap_atol_rel': SWAP_ATOL_REL}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        return old
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    return read(plan)


def verify(plan):
    assert plan['sources'] == sources(), 'vlaai_v2 source drift'
    assert plan['supersedes_plan_sha256'] == sha(V1.OUT / 'plan.json')
    V1.verify(read(V1.OUT / 'plan.json'))


def swap_check(margin, r_att, r_ign, ids):
    m = margin[ids]; ra, ri = r_att[ids], r_ign[ids]
    swapped = ri - ra                                  # margin with the candidates exchanged, same float64 arrays
    atol = SWAP_ATOL_REL * max(1.0, float(np.abs(m).max()))
    d = float(np.abs(swapped + m).max()); dm = float(np.abs(m - (ra - ri)).max())
    return {'swap_max_abs': d, 'swap_atol': atol, 'margin_equals_r_att_minus_r_ign_max_abs': dm, 'swap_antisymmetric': bool(d <= atol and dm <= atol)}


# ------------------------------------------------------------------------------------------------ run (v1 code + corrected check)
def run_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    numerics = V1.fp32_numerics()
    ds, cf, sf = row['dataset'], row['content_fold'], row['person_fold']
    cache = XC.Cache(ds); channels = cache.index['channels']
    t0 = time.time(); X, att, ign = V1.load_all(cache, car=(ds == 'dtu')); t_load = time.time() - t0
    role = cache.role(cf); tr_ids, te_ids = cache.scored(cf, sf)
    fit_ids, val_ids = tr_ids[role[tr_ids] == 'fit'], tr_ids[role[tr_ids] == 'es']
    full = {'fit': int(len(fit_ids)), 'val': int(len(val_ids)), 'score': int(len(tr_ids) + len(te_ids))}
    score_tr, score_te = tr_ids, te_ids
    if probe:
        rng = np.random.default_rng(V1.SEED)
        fit_ids = np.sort(rng.choice(fit_ids, V1.SMOKE['train'], replace=False)); val_ids = val_ids[:V1.SMOKE['val']]
        score_tr, score_te = tr_ids[:V1.SMOKE['score']], te_ids[:0]
    torch.manual_seed(V1.SEED); np.random.seed(V1.SEED)
    net = V1.build_net(ds, channels, dev)
    init_val = float(XC.rowcorr(V1.predict(net, X, val_ids, dev), att[val_ids].astype(np.float64)).mean())
    t0 = time.time(); tr = V1.fit(net, X, att, fit_ids, val_ids, V1.SMOKE['epochs'] if probe else V1.MAX_EPOCHS, dev, row['id']); t_train = time.time() - t0
    t0 = time.time(); ids = np.concatenate([score_tr, score_te]).astype(int)
    att64, ign64 = att[ids].astype(np.float64), ign[ids].astype(np.float64)
    P = V1.predict(net, X, ids, dev); ra = XC.rowcorr(P, att64); ri = XC.rowcorr(P, ign64)
    t_score = time.time() - t0
    n = len(cache.arr['cs_person'])
    margin = np.full(n, np.nan); r_att = np.full(n, np.nan); r_ign = np.full(n, np.nan); scored = np.full(n, '', dtype='<U10')
    margin[ids], r_att[ids], r_ign[ids] = ra - ri, ra, ri
    scored[score_tr] = 'train_side'; scored[score_te] = 'test'
    checks = {'margins_finite': bool(np.isfinite(margin[ids]).all())}

    def margin_fn(idx):
        Q = V1.predict(net, X, idx, dev)
        return XC.rowcorr(Q, att[idx].astype(np.float64)) - XC.rowcorr(Q, ign[idx].astype(np.float64))
    checks.update(V1.margin_invariance(margin_fn, ids, ra - ri, ra - ri))
    k = ids[:V1.N_INVARIANCE]
    checks['prediction_alone_vs_batch_max_abs'] = float(np.abs(np.concatenate([V1.predict(net, X, k[j:j + 1], dev) for j in range(len(k))]) - P[:len(k)]).max())
    checks['prediction_sd'] = float(P.std())
    checks.update(swap_check(margin, r_att, r_ign, ids))
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'margins.npz', cs_person=cache.arr['cs_person'], cs_code=cache.arr['cs_code'], cs_e0=cache.arr['cs_e0'],
                        cs_role=role, margin=margin, r_att=r_att, r_ign=r_ign, scored=scored)
    if not probe:
        torch.save(net.state_dict(), dest / 'final_model.pt')
    rec = {'status': 'complete' if all(v for kk, v in checks.items() if kk.endswith(('_ok', 'finite', 'antisymmetric'))) else 'check_failed',
           'version': 'v2', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'dest': str(dest), 'npz_sha256': sha(dest / 'margins.npz'),
           'final_model_sha256': None if probe else sha(dest / 'final_model.pt'), 'init_val_mean_r': init_val, **tr,
           'adapter': getattr(net, 'adapter_info', None), 'n': {'fit': int(len(fit_ids)), 'val': int(len(val_ids)), 'scored_train_side': int(len(score_tr)),
                                                                 'scored_test': int(len(score_te))}, 'full_counts': full,
           'seconds': {'load': round(t_load, 1), 'train': round(t_train, 1), 'score': round(t_score, 1), 'total': round(time.time() - t_all, 1)},
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job, 'checks': checks,
           'numerics': numerics}
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], ds, cf, sf, rec['status'], rec['seconds'], flush=True)
    assert rec['status'] == 'complete', checks
    return rec


# ------------------------------------------------------------------------------------------------ adoption of v1 units
def adopt_one(row, plan):
    """Validate the v1 record of `row` under v2 and write the v2 record; returns the v2 record or None (no v1 record)."""
    v1p = V1.OUT / 'units' / f'{row["id"]}.json'
    if not v1p.exists():
        return None
    v1 = read(v1p); failed = {k for k, v in v1['checks'].items() if k.endswith(('_ok', 'finite', 'antisymmetric')) and not v}
    assert v1['status'] == 'complete' or (v1['status'] == 'check_failed' and failed == {'swap_antisymmetric'}), (row['id'], failed)
    assert not v1['probe'] and v1['row'] == row and v1['plan_sha256'] == plan['supersedes_plan_sha256']
    dest = Path(v1['dest']); assert sha(dest / 'margins.npz') == v1['npz_sha256'] and sha(dest / 'final_model.pt') == v1['final_model_sha256']
    with np.load(dest / 'margins.npz', allow_pickle=False) as z:
        Z = {k: z[k] for k in z.files}
    cache = XC.Cache(row['dataset'])
    for k in ('cs_person', 'cs_code', 'cs_e0'):
        assert np.array_equal(Z[k], cache.arr[k]), k
    assert np.array_equal(Z['cs_role'], cache.role(row['content_fold']))
    tr, te = cache.scored(row['content_fold'], row['person_fold']); ids = np.concatenate([tr, te]).astype(int)
    sc = np.full(len(Z['margin']), '', dtype='<U10'); sc[tr] = 'train_side'; sc[te] = 'test'
    assert np.array_equal(Z['scored'], sc) and np.isnan(Z['margin'][sc == '']).all()
    checks = {**{k: v for k, v in v1['checks'].items() if k != 'swap_antisymmetric'}, 'margins_finite': bool(np.isfinite(Z['margin'][ids]).all()),
              'v1_swap_antisymmetric': v1['checks'].get('swap_antisymmetric')}
    checks.update(swap_check(Z['margin'], Z['r_att'], Z['r_ign'], ids))
    status = 'complete' if all(v for k, v in checks.items() if k.endswith(('_ok', 'finite')) or k == 'swap_antisymmetric') else 'check_failed'
    rec = {**{k: v for k, v in v1.items() if k not in ('status', 'checks', 'plan_sha256')}, 'status': status, 'version': 'v2_adopted',
           'plan_sha256': sha(OUT / 'plan.json'), 'checks': checks, 'adopted_from': {'record': str(v1p), 'record_sha256': sha(v1p), 'v1_status': v1['status']},
           'adoption': {'job': os.environ.get('SLURM_JOB_ID'), 'time': datetime.now().astimezone().isoformat(),
                        'note': 'margins and model unchanged (sha256 verified); only the status-gating swap check re-evaluated under v2'}}
    write(OUT / 'units' / f'{row["id"]}.json', rec)
    assert status == 'complete', checks
    marker = V1.OUT / 'units' / f'{row["id"]}.FAILED.json'
    if marker.exists():
        release_marker(row['id'], marker, v1, rec)
    return rec


def release_marker(uid, marker, v1, v2rec):
    RELEASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    digest_ = sha(marker); body = read(marker); dst = RELEASE / f'{uid}.FAILED.released_20261022.json'
    shutil.move(str(marker), str(dst))
    receipt = {'unit': uid, 'time': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID'),
               'moved': str(marker), 'to': str(dst), 'marker_sha256': digest_, 'marker': body,
               'cause': 'v1 swap_antisymmetric check: float32 recomputation vs float64 margins with np.allclose default atol=1e-8 '
                        '(every other check passed); check gates status only',
               'v1_record_sha256': sha(V1.OUT / 'units' / f'{uid}.json'), 'v1_failed_checks': ['swap_antisymmetric'],
               'v2_record': str(OUT / 'units' / f'{uid}.json'), 'v2_checks': v2rec['checks'], 'driver_sha256': sha(Path(__file__))}
    write(RELEASE / f'release_{uid}_{os.environ.get("SLURM_JOB_ID")}.json', receipt)


def adopt_all():
    plan = make_plan(); verify(plan); out = {}
    for row in plan['rows']:
        if (OUT / 'units' / f'{row["id"]}.json').exists():
            continue
        lock = CLAIMS / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                out[row['id']] = 'running_elsewhere'; continue
            rec = adopt_one(row, plan)
            out[row['id']] = None if rec is None else rec['status']
    return out


def smoke_inherit():
    """v2 changes only the status-gating swap check: the v1 GPU smoke 1056215 (pass under the v1 plan) is inherited, with the v2
    check re-evaluated on that smoke's saved probe margins (CPU)."""
    plan = make_plan(); verify(plan)
    v1r = V1.OUT / 'probes' / '1056215' / 'receipt.json'; r1 = read(v1r)
    assert r1['status'] == 'pass' and r1['plan_sha256'] == plan['supersedes_plan_sha256']
    units = []
    for u in r1['units']:
        rec = read(V1.OUT / 'probes' / '1056215' / 'units' / f'{u["row"]["id"]}.json'); dest = Path(rec['dest'])
        assert sha(dest / 'margins.npz') == rec['npz_sha256']
        with np.load(dest / 'margins.npz', allow_pickle=False) as z:
            ids = np.flatnonzero(z['scored'] != ''); units.append({'row': u['row'], **swap_check(z['margin'], z['r_att'], z['r_ign'], ids),
                                                                  'v1_checks': u['checks']})
    ok = all(u['swap_antisymmetric'] for u in units)
    tag = f'inherit_{os.environ["SLURM_JOB_ID"]}'
    write(OUT / 'probes' / tag / 'receipt.json', {'status': 'pass' if ok else 'failed', 'plan_sha256': sha(OUT / 'plan.json'),
                                                   'inherited_from': {'receipt': str(v1r), 'sha256': sha(v1r), 'job': '1056215'},
                                                   'units': units, 'note': 'no GPU rerun: v2 changes only the status-gating swap check'})
    return ok


# ------------------------------------------------------------------------------------------------ fleet
def ready_fn(row):
    return True


def fleet_status():
    st = XF.fleet_status(sys.modules[__name__], slots=1, max_units=10)
    if st['state'] == 'ready' and st['submit'] and st['submit'][1] == 'smoke':
        st['submit'] = [SBATCH, 'smoke-inherit', '--system', SYSTEM]
    return st


def worker(max_units):
    assert XF.receipts(sys.modules[__name__])['pass'], 'no passing smoke'
    plan = read(OUT / 'plan.json'); verify(plan); count = 0
    for row, failed in XF.open_rows(sys.modules[__name__]):
        if failed:
            continue
        lock = CLAIMS / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if (OUT / 'units' / f'{row["id"]}.json').exists():
                continue
            if (V1.OUT / 'units' / f'{row["id"]}.json').exists():
                adopt_one(row, plan); continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, 'unit', '--id', row['id']]).returncode
            if rc < 0:
                raise SystemExit(rc)
            if rc or not (OUT / 'units' / f'{row["id"]}.json').exists():
                write(OUT / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ.get('SLURM_JOB_ID'), 'returncode': rc})
                raise RuntimeError(f'vlaai_v2 unit failed: {row["id"]}')
            count += 1
        if count >= max_units:
            break


def score():
    from . import external_decoders as ED
    ED.MODULES = {**ED.MODULES, SYSTEM: 'ext_vlaai_v2'}          # in-process only; external_decoders.py is not edited
    return ED.score(SYSTEM)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'adopt', 'smoke-inherit', 'worker', 'unit', 'score'))
    ap.add_argument('--system'); ap.add_argument('--id'); ap.add_argument('--probe', action='store_true'); ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.cmd == 'plan':
        print(sha(OUT / 'plan.json') if make_plan() else None)
    elif a.cmd == 'adopt':
        print(json.dumps(adopt_all(), indent=1))
    elif a.cmd == 'smoke-inherit':
        assert smoke_inherit()
    elif a.cmd == 'worker':
        adopt_all(); worker(a.max_units)
    elif a.cmd == 'unit':
        plan = read(OUT / 'plan.json'); verify(plan)
        run_unit(next(r for r in plan['rows'] if r['id'] == a.id), plan, a.probe)
    elif a.cmd == 'score':
        score()


if __name__ == '__main__':
    main()
