"""Paper line, Table 2 POST-HOC context-matched sensitivity, VLAAI row (GPU).  Protocol: results/.../context_matched/PROTOCOL.json.

The Table 2 VLAAI recipe (paper/ext_vlaai.py, status check as paper/ext_vlaai_v2.py) re-fitted per unit on the proposed system's EEG
span only: model input = cache EEG [:, :, 13:304] at 64 Hz (ext_context.SPAN64, 291 samples; VLAAI is fully convolutional and zero-
pads its window edges as natively), DTU common-average reference + per-listener per-channel z-score computed over span samples only
(load_ctx = ext_vlaai.load_all with the span slice), FAU Linear(31->64) adapter as Table 2.  Target / loss / validation r / margin
envelope = the same window [13, 304) (VLAAI's native convention: EEG window == envelope window).  Training (seed 3401, Adam 1e-4,
batch 64, <= 50 epochs, patience 5, best epoch by mean per-segment r on train people cs role=es, fp32 numerics) = ext_vlaai.fit /
build_net / predict unchanged.  Checks: finiteness, batch invariance (ext_vlaai.margin_invariance), swap check (ext_vlaai_v2).
Same 20 units (dataset x content fold x person fold), new ids, own plan / records / claims; nothing of the Table 2 row is touched.
Fleet: fleet_status() (shim aln35/paper_ext_ctx_vlaai_fleet.py), job name c3_s35pxvctx, lane s35_paper_ext_vlaai_ctx, slots 2.
CLI (Slurm only): python -m auditory_alignment_v3.paper.ext_context_vlaai plan | smoke | worker [--max-units N] |
unit --id ID [--probe] | score | status       ('--system vlaai_ctx' from the fleet submit line is accepted and ignored)
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from . import ext_common as XC
from . import ext_context as CX
from . import ext_fleet as XF
from . import ext_vlaai as V1
from . import ext_vlaai_v2 as V2

SYSTEM = 'vlaai_ctx'
NAME, LANE, SBATCH = 'c3_s35pxvctx', 's35_paper_ext_vlaai_ctx', 'slurm/aln35_paper_ext_ctx_vlaai.sbatch'
OUT = CX.OUT / 'vlaai'
STORE = CX.STORE / 'vlaai'
S0, S1 = CX.SPAN64
SLOTS, MAX_UNITS = 2, 10
MODULE_FILES = ('auditory_alignment_v3/paper/ext_context_vlaai.py', 'auditory_alignment_v3/paper/ext_context.py',
                'auditory_alignment_v3/paper/ext_vlaai.py', 'auditory_alignment_v3/paper/ext_vlaai_v2.py', 'auditory_alignment_v3/paper/vlaai_torch.py',
                'auditory_alignment_v3/paper/ext_fleet.py', 'auditory_alignment_v3/paper/ext_common.py', 'auditory_alignment_v3/aln42/external_eval.py')
read, write, sha, digest = XC.read, XC.write, XC.sha, XC.digest


def sources():
    return CX.file_shas(MODULE_FILES)


def rows():
    out = []
    for ds in XC.DATASETS:
        for cf in XC.CFS:
            for sf in XC.SFS:
                body = {'system': SYSTEM, 'dataset': ds, 'content_fold': cf, 'person_fold': sf, 'seed': V1.SEED, 'span_64hz': list(CX.SPAN64)}
                out.append({**body, 'id': 'PXVCTX_' + digest(body, 16)})
    return out


def make_plan():
    v1 = read(V1.OUT / 'plan.json')
    body = {'version': 'PAPER_EXT_VLAAI_CTX_v1', 'post_hoc': True, 'protocol_sha256': CX.protocol_sha(), 'rows': rows(), 'sources': sources(),
            'reference_plan_sha256': {'vlaai_v1': sha(V1.OUT / 'plan.json'), 'vlaai_v2': sha(V2.OUT / 'plan.json')},
            'input_index_sha256': {ds: sha(XC.INPUT / ds / 'index.json') for ds in XC.DATASETS}, 'released': v1['released'],
            'recipe': {**v1['recipe'], 'swap_check': 'ext_vlaai_v2.swap_check (atol 1e-9 x max(1, max|margin|))'},
            'span': {'eeg_64hz_half_open': [S0, S1], 'input_samples': S1 - S0, 'envelope_64hz_half_open': [S0, S1],
                     'dtu_input': 'CAR, then per-listener per-channel z-score over span samples only'},
            'smoke': V1.SMOKE, 'fleet': {'name': NAME, 'lane': LANE, 'sbatch': SBATCH, 'slots': SLOTS, 'max_units_per_job': MAX_UNITS}}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
        return old
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700); STORE.mkdir(parents=True, exist_ok=True, mode=0o700)
    write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    return read(plan)


def verify(plan):
    assert plan['sources'] == sources(), 'vlaai_ctx source drift'
    assert plan['protocol_sha256'] == CX.protocol_sha()
    for ds in XC.DATASETS:
        assert sha(XC.INPUT / ds / 'index.json') == plan['input_index_sha256'][ds]
    assert sha(V1.VERIFY) == plan['released']['verify_sha256'] and sha(V1.VT.H5) == plan['released']['h5_sha256']


# ------------------------------------------------------------------------------------------------ data (span only)
def load_ctx(cache, car):
    """ext_vlaai.load_all restricted to the span: EEG [n, C, 291] (cache order), attended / ignored envelopes [n, 291];
    DTU: CAR + per-listener z-score over span samples only.  No sample outside [13, 304) is read into X."""
    a = cache.arr; n = len(a['cs_person']); C = len(cache.index['channels']); L = S1 - S0
    X = np.zeros((n, C, L), np.float32); att = np.zeros((n, L), np.float32); ign = np.zeros_like(att)
    for pid in sorted(set(a['cs_person'].tolist())):
        rows_ = cache.person_rows(pid); E, at, ig = cache.load(pid, check=True); E = E[a['cs_row'][rows_], :, S0:S1]
        if car:
            E = E - E.mean(1, keepdims=True)
            mu = E.mean((0, 2), keepdims=True); sd = E.std((0, 2), keepdims=True); sd[sd == 0] = 1
            E = (E - mu) / sd
        X[rows_] = E; att[rows_] = at[a['cs_row'][rows_], S0:S1]; ign[rows_] = ig[a['cs_row'][rows_], S0:S1]
    assert X.shape[-1] == L and att.shape[-1] == L
    return X, att, ign


# ------------------------------------------------------------------------------------------------ run (= ext_vlaai_v2.run_unit on the span)
def run_unit(row, plan, probe=False):
    import torch
    t_all = time.time(); job = os.environ['SLURM_JOB_ID']; dev = torch.device('cuda'); torch.cuda.reset_peak_memory_stats()
    numerics = V1.fp32_numerics()
    ds, cf, sf = row['dataset'], row['content_fold'], row['person_fold']
    cache = XC.Cache(ds); channels = cache.index['channels']
    t0 = time.time(); X, att, ign = load_ctx(cache, car=(ds == 'dtu')); t_load = time.time() - t0
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
    P = V1.predict(net, X, ids, dev); ra = XC.rowcorr(P, att[ids].astype(np.float64)); ri = XC.rowcorr(P, ign[ids].astype(np.float64))
    t_score = time.time() - t0
    n = len(cache.arr['cs_person'])
    margin = np.full(n, np.nan); r_att = np.full(n, np.nan); r_ign = np.full(n, np.nan); scored = np.full(n, '', dtype='<U10')
    margin[ids], r_att[ids], r_ign[ids] = ra - ri, ra, ri
    scored[score_tr] = 'train_side'; scored[score_te] = 'test'
    checks = {'margins_finite': bool(np.isfinite(margin[ids]).all()), 'span_input_ok': bool(X.shape[-1] == S1 - S0 and P.shape[-1] == S1 - S0)}

    def margin_fn(idx):
        Q = V1.predict(net, X, idx, dev)
        return XC.rowcorr(Q, att[idx].astype(np.float64)) - XC.rowcorr(Q, ign[idx].astype(np.float64))
    checks.update(V1.margin_invariance(margin_fn, ids, ra - ri, ra - ri))
    k = ids[:V1.N_INVARIANCE]
    checks['prediction_alone_vs_batch_max_abs'] = float(np.abs(np.concatenate([V1.predict(net, X, k[j:j + 1], dev) for j in range(len(k))]) - P[:len(k)]).max())
    checks['prediction_sd'] = float(P.std())
    checks.update(V2.swap_check(margin, r_att, r_ign, ids))
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    np.savez_compressed(dest / 'margins.npz', cs_person=cache.arr['cs_person'], cs_code=cache.arr['cs_code'], cs_e0=cache.arr['cs_e0'],
                        cs_role=role, margin=margin, r_att=r_att, r_ign=r_ign, scored=scored)
    if not probe:
        torch.save(net.state_dict(), dest / 'final_model.pt')
    rec = {'status': 'complete' if all(v for kk, v in checks.items() if kk.endswith(('_ok', 'finite', 'antisymmetric'))) else 'check_failed',
           'version': 'ctx_v1', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'protocol_sha256': CX.protocol_sha(),
           'dest': str(dest), 'npz_sha256': sha(dest / 'margins.npz'), 'final_model_sha256': None if probe else sha(dest / 'final_model.pt'),
           'init_val_mean_r': init_val, **tr, 'adapter': getattr(net, 'adapter_info', None),
           'n': {'fit': int(len(fit_ids)), 'val': int(len(val_ids)), 'scored_train_side': int(len(score_tr)), 'scored_test': int(len(score_te))},
           'full_counts': full, 'span_64hz': [S0, S1],
           'seconds': {'load': round(t_load, 1), 'train': round(t_train, 1), 'score': round(t_score, 1), 'total': round(time.time() - t_all, 1)},
           'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20, 'device': torch.cuda.get_device_name(0), 'job': job, 'checks': checks,
           'numerics': numerics}
    if probe:
        per = t_train / max(1, tr['epochs_run']) / max(1, len(fit_ids))
        rec['projected_full_unit_hours_upper'] = (t_load + per * full['fit'] * V1.MAX_EPOCHS + t_score / max(1, len(ids)) * full['score']) / 3600
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], ds, cf, sf, rec['status'], rec['seconds'], flush=True)
    assert rec['status'] == 'complete', checks
    return rec


def _sub(*args):
    return subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, *map(str, args)]).returncode


def smoke():
    """Probe units (training-side segments only, 2 epochs, no test segment scored) for dtu / fau cf0 sf0."""
    job = os.environ['SLURM_JOB_ID']; plan = make_plan(); verify(plan)
    receipt = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'protocol_sha256': CX.protocol_sha(), 'units': []}
    try:
        for ds in XC.DATASETS:
            row = next(r for r in plan['rows'] if r['dataset'] == ds and r['content_fold'] == 0 and r['person_fold'] == 0)
            rc = _sub('unit', '--id', row['id'], '--probe'); assert rc == 0, (ds, rc)
            rec = read(OUT / 'probes' / job / 'units' / f'{row["id"]}.json')
            assert rec['status'] == 'complete' and rec['n']['scored_test'] == 0
            receipt['units'].append({k: rec[k] for k in ('row', 'seconds', 'gpu_peak_mb', 'device', 'checks', 'numerics', 'init_val_mean_r', 'history',
                                                         'adapter', 'n', 'full_counts', 'projected_full_unit_hours_upper', 'span_64hz')})
        receipt['status'] = 'pass'
    except BaseException:
        receipt.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', receipt)


# ------------------------------------------------------------------------------------------------ fleet
def fleet_status():
    return XF.fleet_status(sys.modules[__name__], slots=SLOTS, max_units=MAX_UNITS)


def worker(max_units):
    S = sys.modules[__name__]
    assert XF.receipts(S)['pass'], 'no passing smoke'
    plan = read(OUT / 'plan.json'); verify(plan); count = 0
    for row, failed in XF.open_rows(S):
        if failed:
            continue
        if XF.claim(S, row['id'], lambda: _sub('unit', '--id', row['id'])):
            count += 1
        if count >= max_units:
            break


def score():
    plan = read(OUT / 'plan.json'); verify(plan)
    recs = {r['id']: read(OUT / 'units' / f'{r["id"]}.json') for r in plan['rows'] if (OUT / 'units' / f'{r["id"]}.json').exists()}
    assert len(recs) == len(plan['rows']), f'{len(plan["rows"]) - len(recs)} units incomplete; scoring refused'
    by = CX.score_units(plan['rows'], lambda row: recs[row['id']])
    meta = {f"{r['dataset']}_cf{r['content_fold']}_sf{r['person_fold']}": {k: recs[r['id']][k] for k in ('best_epoch', 'epochs_run', 'best_val_mean_r', 'job', 'device')}
            for r in plan['rows']}
    return CX.table(SYSTEM, by, MODULE_FILES, extra={'plan_sha256': sha(OUT / 'plan.json'), 'units': meta,
                                                      'definition': read(CX.PROTOCOL)['analyses'][SYSTEM]})


def status():
    out = {'plan': (OUT / 'plan.json').exists()}
    if out['plan']:
        rows_ = read(OUT / 'plan.json')['rows']
        out['complete'] = sum((OUT / 'units' / f'{r["id"]}.json').exists() for r in rows_); out['total'] = len(rows_)
        out['failed'] = sum((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in rows_)
        out['smoke_pass'] = [str(p) for p in XF.receipts(sys.modules[__name__])['pass']]
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'smoke', 'worker', 'unit', 'score', 'status'))
    ap.add_argument('--system'); ap.add_argument('--id'); ap.add_argument('--probe', action='store_true')
    ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    assert a.system in (None, SYSTEM), a.system
    if a.cmd == 'plan':
        make_plan(); print(sha(OUT / 'plan.json'))
    elif a.cmd == 'smoke':
        smoke()
    elif a.cmd == 'worker':
        worker(a.max_units)
    elif a.cmd == 'unit':
        plan = read(OUT / 'plan.json'); verify(plan)
        run_unit(next(r for r in plan['rows'] if r['id'] == a.id), plan, a.probe)
    elif a.cmd == 'score':
        score()
    elif a.cmd == 'status':
        status()


if __name__ == '__main__':
    main()
