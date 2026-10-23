"""W7 §2.7 D, version 2 (APPENDUM_RAD_05): the RAD_02 primary (5 plain steps, lr 0.1) plus the secondary "converged" variant.

Everything of v1 (paper/w7_adapt.py, APPENDUM_RAD_02) is reused unchanged: base checkpoints, data, support / query split, input
filter x + dW x, criteria (D_CE mixture CE; D_CS q^2-mixed CS of the slot features Z with the class Y, sigma_Z fixed at dW = 0),
L2 0.1 / 2 ||dW||_F^2, cal step, query scoring, U0 gate. v1's child_run computes U0, cal, D_CE, D_CS (primary) per child.
Secondary (RAD_05): the same objective minimised by plain gradient descent at lr 0.1 from dW = 0 on the support loss until
r_t = |L_t - L_{t-1}| / max(|L_{t-1}|, 1e-12) < 1e-4 for 5 consecutive updates or 200 updates (cap); the final iterate, then the
same cal step and query scoring -> D_CE_conv, D_CS_conv (+cal). Steps used, converged flag and ||dW|| are recorded.
Families: W7_ADAPT:private (primary, frozen) and W7_ADAPT_CONV:private (appendum RAD_05, secondary), both in W7_ADAPT_FAMILIES.json.
CLI: --make-plan | --smoke | --worker | --unit ID | --summarize (CPU)
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from . import w7_adapt as V1

OUT = V1.W7 / 'adapt_v2'
STORE = V1.STORE.parent / 'adapt_v2'
RESULTS = V1.RESULTS
APPENDUM_05 = V1.W7 / 'APPENDUM_RAD_05.md'
V1_SMOKE = V1.OUT / 'probes' / '1057961' / 'units'
CONV_TOL, CONV_PATIENCE, CONV_CAP = 1e-4, 5, 200
PRIMARY = ('D_CE', 'D_CS')
CONV = ('D_CE_conv', 'D_CS_conv')
METHODS = ('U0', 'cal') + PRIMARY + tuple(f'{c}+cal' for c in PRIMARY) + CONV + tuple(f'{c}+cal' for c in CONV)
NAME, LANE, SBATCH = 'c3_s35pw7adapt2', 's35_paper_w7_adapt_v2', 'slurm/aln35_paper_w7_adapt_v2.sbatch'
sha, read, write, digest = V1.sha, V1.read, V1.write, V1.digest


def sources():
    return {**V1.sources(), 'auditory_alignment_v3/paper/w7_adapt_v2.py': sha(Path(__file__))}


def bindings():
    b = V1.bindings()
    assert APPENDUM_05.exists() and not os.access(APPENDUM_05, os.W_OK), 'APPENDUM_RAD_05 must exist and be read-only'
    return {**b, 'appendum_rad_05_sha256': sha(APPENDUM_05)}


def make_plan():
    rows = []
    for seed in V1.SEEDS:
        for arm in V1.ARMS:
            for fold in V1.FOLDS:
                rec_path, row, sup = V1.ce_unit(arm, seed, fold); rec = read(rec_path)
                assert rec['status'] == 'complete' and not rec['probe'] and sha(rec['checkpoints']['selected']) == rec['checkpoints']['selected_sha256']
                assert sup.exists(), sup
                body = {'arm': arm, 'seed': seed, 'outer_fold': fold, 'ce_unit': row['id'], 'version': 2}
                rows.append({**body, 'id': 'W7D2_' + digest(body), 'ce_record': str(rec_path), 'ce_record_sha256': sha(rec_path),
                             'checkpoint': rec['checkpoints']['selected'], 'checkpoint_sha256': rec['checkpoints']['selected_sha256'],
                             'ce_device': rec.get('device'), 'support_record': str(sup), 'support_record_sha256': sha(sup),
                             'test_children': list(rec['test']['selected'])})
    body = {'version': 'W7_ADAPT_v2', 'rows': rows, 'sources': sources(), 'bindings': bindings(),
            'settings': {'steps': V1.STEPS, 'lr': V1.LR, 'l2': V1.L2, 'criteria': list(V1.CRITERIA), 'conv_tol': CONV_TOL,
                         'conv_patience': CONV_PATIENCE, 'conv_cap': CONV_CAP, 'support': 'U30 pool (aln35.support_contract.private_split)',
                         'filter': 'x + dW x at the model input, dW [20, 20] = 0 at start', 'gate_tol': V1.GATE_TOL, 'sanity_tol': V1.SANITY_TOL}}
    path = OUT / 'plan.json'
    if path.exists():
        old = read(path); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        OUT.mkdir(parents=True, exist_ok=True, mode=0o700); write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('W7 adapt v2 plan', len(rows), sha(path), flush=True)


# ----------------------------------------------------------------------------------------------- converged variant
def loss_grad(model, x, yt, dW, criterion, sigma, chunk=V1.CHUNK):
    """Support loss (criterion + L2/2 ||dW||^2) at dW and its exact gradient (one graph over all support chunks)."""
    import torch
    d = dW.detach().clone().requires_grad_(True)
    with torch.enable_grad():
        Z = torch.cat([V1.forward(model, x[s:s + chunk], d)[2] for s in range(0, len(x), chunk)])
        if criterion == 'D_CE':
            crit = V1.head_loss_from_Z(model, Z, yt)
        else:
            score, _ = V1.cs_labels_score(Z.double(), yt, model.a, sigma); crit = -score
        g, = torch.autograd.grad(crit, d)
    loss = float(crit) + .5 * V1.L2 * float((dW.double() ** 2).sum())
    grad = g + V1.L2 * dW
    if not (math.isfinite(loss) and bool(torch.isfinite(grad).all())):
        raise FloatingPointError(f'nonfinite {criterion} loss / gradient')
    return loss, grad, float(crit)


def adapt_conv(model, x, y, criterion, sigma=None):
    import torch
    dW = torch.zeros(x.shape[1], x.shape[1], device=x.device); yt = torch.as_tensor(y, device=x.device)
    prev, small, steps, converged, trace = None, 0, 0, False, []
    while True:
        L, grad, crit = loss_grad(model, x, yt, dW, criterion, sigma)
        r = None
        if prev is not None:
            r = abs(L - prev) / max(abs(prev), 1e-12); small = small + 1 if r < CONV_TOL else 0
        trace.append((steps, L, crit, r, float(grad.norm()), float(dW.norm())))
        if small >= CONV_PATIENCE:
            converged = True; break
        if steps >= CONV_CAP:
            break
        prev = L; dW = (dW - V1.LR * grad).detach(); steps += 1
    keep = [t for t in trace if t[0] < 5 or t[0] % 10 == 0 or t[0] >= trace[-1][0] - 5]
    return dW, {'updates': steps, 'converged': converged, 'dW_fro': float(dW.norm()), 'dW_max_abs': float(dW.abs().max()),
                'loss_first': trace[0][1], 'loss_final': trace[-1][1], 'r_final': trace[-1][3],
                'trace': [{'step': t[0], 'loss_nats': t[1], 'criterion_nats': t[2], 'rel_change': t[3], 'grad_norm': t[4], 'dW_fro': t[5]} for t in keep]}


def child_run_v2(model, kid, stored, sup_child, dev, check_gate):
    import torch
    from ..aln35 import support_contract as SC
    from ..aln41 import support as SUP
    res, probs = V1.child_run(model, kid, stored, sup_child, dev, check_gate)      # U0, cal, primary D_CE / D_CS (v1 path)
    if probs is None:                                                               # fallback child: no update
        for m in CONV + tuple(f'{c}+cal' for c in CONV):
            res[m] = res['U0']
        return res, None
    x = torch.as_tensor(kid['x'], dtype=torch.float32, device=dev); y = np.asarray(kid['y'], np.int64)
    split = SC.private_split(kid); S, Q = split['pool'], split['query']; xs = x[S]
    for crit, name in zip(V1.CRITERIA, CONV):
        t0 = time.time()
        dW, info = adapt_conv(model, xs, y[S], crit, sigma=res['sigma_Z_U0'] if crit == 'D_CS' else None)
        lpS, _, ZS = V1.run_all(model, xs, dW); lpQ, _, _ = V1.run_all(model, x[Q], dW)
        pS, pQ = np.exp(lpS[:, 1].double().cpu().numpy()), np.exp(lpQ[:, 1].double().cpu().numpy())
        sc, bc, _ = SUP.adapt_cal(pS, y[S]); pQc = SUP.calibrated(pQ, sc, bc)
        res[name] = SUP.query_metrics(pQ, y[Q]); res[f'{name}+cal'] = SUP.query_metrics(pQc, y[Q])
        cs_after, _ = V1.cs_labels_score(ZS.double(), torch.as_tensor(y[S], device=dev), model.a, res['sigma_Z_U0'])
        info.update(support_ce_nats_after=float(V1.head_loss_from_Z(model, ZS, torch.as_tensor(y[S], device=dev))),
                    support_cs_nats_after=float(cs_after), cal_value=[sc, bc], seconds=time.time() - t0)
        res[f'{name}_detail'] = info
        probs[name] = pQ; probs[f'{name}+cal'] = pQc; probs[f'{name}_dW'] = dW.cpu().numpy()
    return res, probs


def run_unit(row, probe=False):
    import torch
    from ..aln35 import support_runtime as SR
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    assert sha(row['ce_record']) == row['ce_record_sha256'] and sha(row['support_record']) == row['support_record_sha256']
    sup = read(row['support_record'])
    kids = {k['id']: k for k in SR.load_kids()}; model = V1.load_model(row, dev); dest_ck = Path(row['checkpoint']).parent
    store = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; store.mkdir(parents=True, exist_ok=True, mode=0o700)
    children, gate = {}, None
    for j, cid in enumerate(row['test_children']):
        with np.load(dest_ck / f'test_{cid}.npz') as z:
            stored = {k: z[k] for k in ('log_mixture', 'y')}
        res, probs = child_run_v2(model, kids[cid], stored, sup['children'][cid], dev, check_gate=(probe and j == 0))
        if probe and j == 0:
            gate = {'child': cid, **res['u0_reproduction'], 'pass': res['u0_reproduction']['max_abs_p_query'] <= V1.GATE_TOL}
        if probs is not None:
            np.savez_compressed(store / f'{cid}.npz', **probs)
        children[cid] = res
        conv = {c: (res[f'{c}_detail']['updates'], res[f'{c}_detail']['converged'], round(res[f'{c}_detail']['dW_fro'], 4))
                for c in CONV if f'{c}_detail' in res}
        print(row['id'], cid, {m: round(res[m]['nll_bits'], 5) for m in METHODS}, conv, flush=True)
    out = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(OUT / 'plan.json'), 'children': children, 'gate': gate,
           'store': str(store), 'seconds': time.time() - t0, 'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20,
           'device': torch.cuda.get_device_name(0), 'ce_device': row['ce_device'], 'job': job,
           'torch': {'version': torch.__version__, 'matmul_tf32': torch.backends.cuda.matmul.allow_tf32, 'cudnn_tf32': torch.backends.cudnn.allow_tf32}}
    write((OUT / 'probes' / job if probe else OUT) / 'units' / f'{row["id"]}.json', out)
    print(row['id'], 'complete', round(out['seconds'], 1), 'peak MB', round(out['gpu_peak_mb']), flush=True)
    return out


# ----------------------------------------------------------------------------------------------- fleet
def receipts():
    out = {'pass': [], 'other': []}
    if (OUT / 'plan.json').exists():
        ps = sha(OUT / 'plan.json')
        for p in sorted((OUT / 'probes').glob('*/receipt.json')):
            r = read(p)
            if r.get('plan_sha256') == ps:
                out['pass' if r.get('status') == 'pass' else 'other'].append(p)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 30, 'slots': 1, 'initial': [], 'submit': []}
    if not (OUT / 'plan.json').exists():
        return st
    plan = read(OUT / 'plan.json'); left = [r for r in plan['rows'] if not (OUT / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{r["id"]}.FAILED.json').exists() for r in left):
        return {**st, 'state': 'failed_unit_review'}
    rec = receipts()
    if not rec['pass']:
        return {**st, 'state': 'engineering_probe_failed'} if rec['other'] else {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, '--smoke']}
    return {**st, 'state': 'ready', 'ready': len(left), 'slots': 2, 'submit': [SBATCH, '--worker']}


def worker(plan):
    assert receipts()['pass'], 'no passing smoke'
    for row in plan['rows']:
        path = OUT / 'units' / f'{row["id"]}.json'
        if path.exists() or (OUT / 'units' / f'{row["id"]}.FAILED.json').exists():
            continue
        lock = OUT / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc < 0:
                raise SystemExit(f'unit ended by signal {-rc}')
            if rc or not path.exists():
                write(OUT / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('W7 adapt v2 unit failed')


def smoke(plan):
    """Unit B0 / seed 3401 / outer fold 0: RAD_02 U0 gate on its first child; primary metrics vs the v1 smoke probe (recorded)."""
    job = os.environ['SLURM_JOB_ID']; rec = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        row = next(r for r in plan['rows'] if r['arm'] == 'B0' and r['seed'] == 3401 and r['outer_fold'] == 0)
        u = run_unit(row, probe=True)
        assert u['gate']['pass'], u['gate']
        assert all(math.isfinite(c[m]['nll_bits']) for c in u['children'].values() for m in METHODS), 'nonfinite query NLL'
        v1 = read(V1_SMOKE / f'{next(r["id"] for r in V1.read(V1.OUT / "plan.json")["rows"] if r["ce_unit"] == row["ce_unit"])}.json')
        diff = max(abs(u['children'][c][m][k] - v1['children'][c][m][k]) for c in u['children'] for m in ('U0', 'cal') + PRIMARY + tuple(f'{x}+cal' for x in PRIMARY)
                   for k in ('nll_bits', 'brier') if u['children'][c][m][k] is not None)
        conv = {c: {'updates': [ch[f'{c}_detail']['updates'] for ch in u['children'].values() if f'{c}_detail' in ch],
                    'converged': [ch[f'{c}_detail']['converged'] for ch in u['children'].values() if f'{c}_detail' in ch],
                    'dW_fro': [round(ch[f'{c}_detail']['dW_fro'], 5) for ch in u['children'].values() if f'{c}_detail' in ch],
                    'seconds': [round(ch[f'{c}_detail']['seconds'], 2) for ch in u['children'].values() if f'{c}_detail' in ch]} for c in CONV}
        rec['units'].append({k: u[k] for k in ('gate', 'seconds', 'gpu_peak_mb', 'device', 'ce_device', 'torch')}
                            | {'row': row['id'], 'children': len(u['children']), 'primary_vs_v1_smoke_max_abs_diff': diff,
                               'v1_smoke_device': v1['device'], 'converged_variant': conv})
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', rec)


# ----------------------------------------------------------------------------------------------- summary (CPU)
def summarize():
    from ..aln41 import analysis as AN
    from ..aln35 import support_runtime as SR
    plan = read(OUT / 'plan.json'); fams = {f['id']: f for f in read(V1.FAMILIES)['families']}
    per, conv_info = {}, {}
    for row in plan['rows']:
        u = read(OUT / 'units' / f'{row["id"]}.json'); assert u['status'] == 'complete' and not u['probe']
        for cid, r in u['children'].items():
            d = {m: r[m] for m in METHODS}
            d['stored_cal'] = r['stored_support_v1_U30']['cal']; d['stored_delta'] = r['stored_support_v1_U30']['delta']
            per.setdefault(row['arm'], {}).setdefault(cid, {})[row['seed']] = d
            for c in CONV:
                if f'{c}_detail' in r:
                    conv_info.setdefault(row['arm'], {}).setdefault(c, []).append((r[f'{c}_detail']['updates'], r[f'{c}_detail']['converged'],
                                                                                   r[f'{c}_detail']['dW_fro']))
    groups = {k['id']: k['group'] for k in SR.load_kids()}
    keys = METHODS + ('stored_cal', 'stored_delta')
    table = {arm: {cid: {m: {k: (float(np.mean([s[x][m][k] for x in V1.SEEDS])) if all(s[x][m][k] is not None for x in V1.SEEDS) else None)
                             for k in ('nll_bits', 'brier', 'auc')} for m in keys}
                   for cid, s in kids.items() if sorted(s) == list(V1.SEEDS)} for arm, kids in per.items()}
    children = sorted(set().union(*[set(v) for v in table.values()]), key=lambda c: (len(c), c))

    def members_for(names, conv):
        out = []
        for name in names:
            arm, contrast = name.split(':'); first, second = contrast.split('-')
            if conv:
                first, second = (x.replace('D_CE', 'D_CE_conv').replace('D_CS', 'D_CS_conv') for x in (first, second))
            A_, B_ = (first if first != 'cal' else 'stored_cal'), (second if second != 'cal' else 'stored_cal')
            label = f'{arm}:{first}-{second}' if conv else name
            out.append((label, {c: (table[arm][c][B_]['nll_bits'] - table[arm][c][A_]['nll_bits']) if c in table.get(arm, {}) else None
                                for c in children}))
        return out
    fz = fams['W7_ADAPT:private']; out_f = []
    for fid, conv, label in (('W7_ADAPT:private', False, 'primary (frozen family; RAD_02 5-step budget)'),
                             ('W7_ADAPT_CONV:private', True, 'appendum RAD_05, secondary (converged regularised optimum)')):
        mem = members_for(fz['members'], conv)
        f = AN.family(fid, 'query NLL bits/trial at U30, positive = first-named better', mem, children)
        f['method'] = 'aln41.analysis.family: child bootstrap-t B=4000, family max-|T*|; per child seeds 3401 / 3407 / 3413 averaged first'
        f['label'] = label; f['cal_reference'] = 'cal = stored aln41 support_v1 U30 cal of the same checkpoint and child'
        f['inputs'] = {n: v for n, v in mem}; out_f.append(f)
    desc = {arm: {m: {k: (float(np.mean([v[m][k] for v in t.values() if v[m][k] is not None])) if t else None) for k in ('nll_bits', 'brier', 'auc')}
                  for m in keys} for arm, t in table.items()}
    by_group = {arm: {g: {m: float(np.mean([v[m]['nll_bits'] for c, v in t.items() if groups.get(c) == g])) for m in METHODS + ('stored_cal',)}
                      for g in sorted({groups[c] for c in t})} for arm, t in table.items()}
    conv_summary = {arm: {c: {'n': len(v), 'converged_fraction': float(np.mean([x[1] for x in v])), 'updates_median': float(np.median([x[0] for x in v])),
                              'updates_max': int(max(x[0] for x in v)), 'dW_fro_median': float(np.median([x[2] for x in v]))} for c, v in d.items()}
                    for arm, d in conv_info.items()}
    out = {'version': 'W7_ADAPT_v2', 'bindings': plan['bindings'], 'plan_sha256': sha(OUT / 'plan.json'), 'definition': __doc__,
           'variants': {'primary': 'RAD_02 5 plain steps lr 0.1 (D_CE, D_CS)', 'converged': 'RAD_05 secondary (D_CE_conv, D_CS_conv)'},
           'per_child': table, 'groups': {c: groups[c] for c in children}, 'descriptive_means': desc, 'nll_by_group': by_group,
           'converged_variant_optimisation': conv_summary,
           'family_inputs': {f['family_id']: {'people': children, 'members': f.pop('inputs')} for f in out_f}}
    os.umask(0o022); RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'W7_ADAPT.json').write_text(json.dumps(out, indent=1, default=float) + '\n')
    (RESULTS / 'W7_ADAPT_FAMILIES.json').write_text(json.dumps({'version': 'W7_ADAPT_FAMILIES_v2', 'input_sha256': sha(RESULTS / 'W7_ADAPT.json'),
                                                                'families': out_f}, indent=1, default=float) + '\n')
    print(json.dumps(desc, indent=1)); print(json.dumps(conv_summary, indent=1))
    for f in out_f:
        print(f['family_id'], f['status'], [(m['name'], m.get('estimate'), m.get('simultaneous_95')) for m in f['members']])


def main():
    ap = argparse.ArgumentParser()
    for flag in ('make_plan', 'smoke', 'worker', 'summarize'):
        ap.add_argument('--' + flag.replace('_', '-'), action='store_true')
    ap.add_argument('--unit'); a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); assert plan['sources'] == sources(), 'frozen source drift'
    assert plan['bindings'] == bindings()
    if a.unit:
        run_unit(next(r for r in plan['rows'] if r['id'] == a.unit)); return
    if a.smoke:
        smoke(plan); return
    if a.summarize:
        summarize(); return
    assert a.worker
    worker(plan)


if __name__ == '__main__':
    main()
