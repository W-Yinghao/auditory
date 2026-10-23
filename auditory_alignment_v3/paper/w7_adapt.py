"""W7 §2.7 D: dependence-driven personal adaptation on the children (Table 5 protocol), GPU.

Frozen design docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md §2.7 / §7.3 (sha256 DESIGN_SHA), family
W7_ADAPT:private of results/auditory_alignment_v3/paper/w7/W7_FAMILIES_v1.json; F5 and the open implementation points are frozen
in private/auditory_alignment_v3/paper/w7_v1/APPENDUM_RAD_02.md before any D output.

Base models: the selected (minimum source-ES NLL) checkpoints of the core private CE fits, arms B0 and TCS x seeds 3401 / 3407 /
3413 x outer folds 0..4 (aln41.private_ft / private_ft_resume; R2 seeds via aln41.r2.seeded); theta, the three slot heads
(SpatialPatchHead + linear classifier) and the gate logits a_target stay frozen. Per outer test child (data via
aln35.support_runtime.load_kids, i.e. auditory_alignment.data.load_private + event geometry):
  support S = the U30 pool and query Q of aln35.support_contract.private_split (the Table 5 / aln41.support contract);
  input-level per-child spatial filter W_c = I + dW (20 x 20 channels, dW = 0 at start) applied to the model input x [n, 20, 200]
  (x + dW x, so dW = 0 reproduces the stored forward), then the unchanged crops -> CBraMod -> slot heads -> q mixture;
  D_CE: mean support CE (nats) of the mixture prediction + 0.1 / 2 ||dW||_F^2;
  D_CS: - TCS-style q^2-mixed kernel CS-QMI between the slot head features Z_k (the 32-d SpatialPatchHead outputs that feed the
        slot classifiers) and the stimulus class Y (counting-measure / delta kernel), q = softmax(a_target), one Gaussian bandwidth
        over the three slots (lower median of within-slot distinct-pair distances, aln41.source.calibrate_sigmas rule) fixed at
        dW = 0 on the child's support trials, + 0.1 / 2 ||dW||_F^2;
  5 plain gradient steps at lr 0.1 (no re-centring), eval mode; gradients by the exact two-pass chain rule (dL/dZ on the whole
  support, then Z-chunk backward); afterwards the unchanged Table 5 cal step (aln41.support.adapt_cal on the adapted support
  probabilities, applied to the adapted query probabilities). Fallback as aln41.support: < 2 support trials or one class -> no update.
Query endpoints per child: NLL bits/trial (primary), Brier, AUC (aln41.support.query_metrics) for U0, cal, D_CE, D_CE+cal, D_CS,
D_CS+cal; the stored aln41 support_v1 U30 results (delta, cal) of the same checkpoint and child are carried for the comparison.
Gate (smoke, before production): with dW = 0 the recomputed U0 query mixture probabilities of the first test child equal the
stored selected-checkpoint probabilities within 1e-5.
CLI: --make-plan | --smoke | --worker | --unit ID | --summarize (CPU)
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core

ROOT = Path(core.REPO)
W7 = Path(core.OUT) / 'paper' / 'w7_v1'
OUT = W7 / 'adapt'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/paper/w7_v1/adapt')
RESULTS = ROOT / 'results/auditory_alignment_v3/paper/w7'
DESIGN = ROOT / 'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md'
DESIGN_SHA = 'c4b461b0a6754af0ba04720320b0acc3f8c907a37f90369a4a250a612a92746c'
FAMILIES = RESULTS / 'W7_FAMILIES_v1.json'
FAMILIES_SHA = 'a95aa35f0f47733f9b1ad57427bd1cc477056459c6555c94cb980fb730982421'
APPENDUM = W7 / 'APPENDUM_RAD_02.md'
ARMS, SEEDS, FOLDS = ('B0', 'TCS'), (3401, 3407, 3413), (0, 1, 2, 3, 4)
STEPS, LR, L2 = 5, 0.1, 0.1
CRITERIA = ('D_CE', 'D_CS')
GATE_TOL, SANITY_TOL = 1e-5, 1e-3
CHUNK = 128
NAME, LANE, SBATCH = 'c3_s35pw7adapt', 's35_paper_w7_adapt', 'slurm/aln35_paper_w7_adapt.sbatch'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def write(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + '.tmp'); tmp.write_text(json.dumps(obj, indent=1, default=float) + '\n'); os.replace(tmp, path)


def digest(v, n=16):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:n]


def sources():
    a = ROOT / 'auditory_alignment_v3'
    files = [Path(__file__), a / 'aln41/private_ft.py', a / 'aln41/private_ft_resume.py', a / 'aln41/support.py', a / 'aln41/timebank.py',
             a / 'aln41/time_access.py', a / 'aln41/cs_qmi_reference.py', a / 'aln41/temporal_objectives_torch.py', a / 'aln35/support_contract.py',
             a / 'aln35/support_runtime.py', ROOT / 'auditory_alignment/data.py', ROOT / 'auditory_alignment_v2/fm_readout.py',
             ROOT / 'auditory_alignment_v2/foundation_adapter.py']
    return {str(p.relative_to(ROOT)): sha(p) for p in files}


def bindings():
    assert sha(DESIGN) == DESIGN_SHA and sha(FAMILIES) == FAMILIES_SHA, 'frozen W7 design / families drift'
    assert APPENDUM.exists() and not os.access(APPENDUM, os.W_OK), 'APPENDUM_RAD_02 must exist and be read-only'
    return {'design_sha256': DESIGN_SHA, 'families_sha256': FAMILIES_SHA, 'appendum_rad_02_sha256': sha(APPENDUM)}


# ----------------------------------------------------------------------------------------------- plan
def ce_unit(arm, seed, fold):
    """(CE unit record path, row, support_v1 record path) of one core private CE fit."""
    from ..aln41 import private_ft as PF, r2 as R2, support as SUP
    ctx = R2.seeded(seed) if seed != 3401 else contextlib.nullcontext()
    with ctx:
        base = PF.BASE; rows = read(base / 'plan.json')['rows']
    row = next(r for r in rows if r['arm'] == arm and r['outer_fold'] == fold)
    return base / 'units' / f'{row["id"]}.json', row, SUP.OUT / 'units' / f'{row["id"]}.json'


def make_plan():
    rows = []
    for seed in SEEDS:
        for arm in ARMS:
            for fold in FOLDS:
                rec_path, row, sup = ce_unit(arm, seed, fold); rec = read(rec_path)
                assert rec['status'] == 'complete' and not rec['probe'] and sha(rec['checkpoints']['selected']) == rec['checkpoints']['selected_sha256']
                assert sup.exists(), sup
                body = {'arm': arm, 'seed': seed, 'outer_fold': fold, 'ce_unit': row['id']}
                rows.append({**body, 'id': 'W7D_' + digest(body), 'ce_record': str(rec_path), 'ce_record_sha256': sha(rec_path),
                             'checkpoint': rec['checkpoints']['selected'], 'checkpoint_sha256': rec['checkpoints']['selected_sha256'],
                             'ce_device': rec.get('device'), 'support_record': str(sup), 'support_record_sha256': sha(sup),
                             'test_children': list(rec['test']['selected'])})
    body = {'version': 'W7_ADAPT_v1', 'rows': rows, 'sources': sources(), 'bindings': bindings(),
            'settings': {'steps': STEPS, 'lr': LR, 'l2': L2, 'criteria': list(CRITERIA), 'support': 'U30 pool (aln35.support_contract.private_split)',
                         'filter': 'x + dW x at the model input, dW [20, 20] = 0 at start', 'gate_tol': GATE_TOL, 'sanity_tol': SANITY_TOL,
                         'chunk': CHUNK}}
    path = OUT / 'plan.json'
    if path.exists():
        old = read(path); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        OUT.mkdir(parents=True, exist_ok=True, mode=0o700); write(path, {**body, 'created': datetime.now().astimezone().isoformat()}); path.chmod(0o444)
    print('W7 adapt plan', len(rows), sha(path), flush=True)


# ----------------------------------------------------------------------------------------------- model pieces
def load_model(row, dev):
    import torch
    from ..aln41 import private_ft as PF
    assert sha(row['checkpoint']) == row['checkpoint_sha256']
    model = PF.build(None, torch.zeros(3), 0, dev)
    model.load_state_dict(torch.load(row['checkpoint'], map_location=dev), strict=True)
    model.eval(); model.requires_grad_(False)
    return model


def forward(model, x, dW):
    """x [B, 20, 200] -> (mixture log-probs [B, 2], slot log-probs [B, 3, 2], slot features Z [B, 3, 32]); input x + dW x."""
    import torch
    from ..aln41 import private_ft as PF, timebank as TB
    xw = x if dW is None else x + torch.einsum('cd,bdt->bct', dW, x)
    B = x.shape[0]; lay = TB.layout(250)
    crops = [xw[..., PF.ONSET + a:PF.ONSET + b] for a, b, _ in lay]
    h = model.bb(TB.crop_inputs(crops, 250)); h = h.reshape(3, B, *h.shape[1:])
    Z = torch.stack([model.slots[k](h[k])[:, 0] for k in range(3)], 1)
    lk = torch.log_softmax(torch.stack([model.cls[k](Z[:, k]) for k in range(3)], 1), -1)
    lq = torch.log_softmax(model.a, 0)
    return torch.logsumexp(lq[None, :, None] + lk, 1), lk, Z


def run_all(model, x, dW, chunk=512):
    import torch
    lp, lk, Z = [], [], []
    with torch.no_grad():
        for s in range(0, len(x), chunk):
            a, b, c = forward(model, x[s:s + chunk], dW); lp.append(a); lk.append(b); Z.append(c)
    return torch.cat(lp), torch.cat(lk), torch.cat(Z)


def head_loss_from_Z(model, Z, y):
    """Mixture CE (mean nats) from slot features through the frozen classifiers and gate."""
    import torch
    lk = torch.log_softmax(torch.stack([model.cls[k](Z[:, k]) for k in range(3)], 1), -1)
    lp = torch.logsumexp(torch.log_softmax(model.a, 0)[None, :, None] + lk, 1)
    return -lp[torch.arange(len(y), device=Z.device), y].mean()


def cs_labels_score(Z, y, a, sigma):
    """TCS-style time-tagged kernel CS-QMI between Z [n, 3, d] and categorical y (counting measure), q^2 mixture over slots."""
    import torch
    from ..aln41.cs_qmi_reference import gaussian_log_gram
    from ..aln41.temporal_objectives_torch import tcs_from_log_potentials
    n = len(Z); nlog = math.log(n)
    same = y[:, None] == y[None, :]
    log_l = torch.full(same.shape, -torch.inf, dtype=torch.float64, device=Z.device).masked_fill(same, 0.0)
    l_square = torch.logsumexp(log_l, dim=(0, 1)) - 2 * nlog; l_rows = torch.logsumexp(log_l, dim=1)
    la, lb, lc = [], [], []
    for k in range(Z.shape[1]):
        log_k = gaussian_log_gram(Z[:, k], sigma)
        la.append(torch.logsumexp(log_k + log_l, dim=(0, 1)) - 2 * nlog)
        lb.append(torch.logsumexp(log_k, dim=(0, 1)) - 2 * nlog + l_square)
        lc.append(torch.logsumexp(torch.logsumexp(log_k, dim=1) + l_rows, dim=0) - 3 * nlog)
    return tcs_from_log_potentials((torch.stack(la), torch.stack(lb), torch.stack(lc)), a.detach().to(torch.float64))


def sigma_Z(Z):
    """Lower median of within-slot distinct-pair distances pooled over the 3 slots (aln41.source.calibrate_sigmas)."""
    import torch
    n = len(Z); off = ~torch.eye(n, dtype=torch.bool, device=Z.device)
    d = torch.cat([torch.cdist(Z[:, k].double(), Z[:, k].double())[off] for k in range(Z.shape[1])]).cpu().numpy()
    d = np.sort(d); s = float(d[(len(d) - 1) // 2]); assert math.isfinite(s) and s > 0
    return s


def adapt(model, x, y, criterion, sigma=None):
    """5 plain gradient steps on dW (exact two-pass chain rule). Returns (dW, history)."""
    import torch
    dev = x.device; dW = torch.zeros(x.shape[1], x.shape[1], device=dev); hist = []
    yt = torch.as_tensor(y, device=dev)
    for step in range(STEPS):
        _, _, Z = run_all(model, x, dW, chunk=CHUNK)
        Zg = Z.detach().clone().requires_grad_(True)
        with torch.enable_grad():
            if criterion == 'D_CE':
                crit = head_loss_from_Z(model, Zg, yt); extra = {}
            else:
                score, st = cs_labels_score(Zg.double(), yt, model.a, sigma); crit = -score; extra = {'cs_nats': float(score)}
            gZ, = torch.autograd.grad(crit, Zg)
        grad = torch.zeros_like(dW)
        for s in range(0, len(x), CHUNK):
            d = dW.detach().clone().requires_grad_(True)
            with torch.enable_grad():
                _, _, Zc = forward(model, x[s:s + CHUNK], d)
                g, = torch.autograd.grad(Zc, d, grad_outputs=gZ[s:s + CHUNK].to(Zc.dtype))
            grad += g
        loss = float(crit) + .5 * L2 * float((dW.double() ** 2).sum())
        grad = grad + L2 * dW
        if not (math.isfinite(loss) and bool(torch.isfinite(grad).all())):
            raise FloatingPointError(f'nonfinite {criterion} loss / gradient')
        hist.append({'step': step, 'loss_nats': loss, 'criterion_nats': float(crit), 'grad_norm': float(grad.norm()),
                     'dW_fro': float(dW.norm()), **extra})
        dW = (dW - LR * grad).detach()
    return dW, hist


def child_run(model, kid, stored, sup_child, dev, check_gate):
    import torch
    from ..aln35 import support_contract as SC
    from ..aln41 import support as SUP
    x = torch.as_tensor(kid['x'], dtype=torch.float32, device=dev); y = np.asarray(kid['y'], np.int64)
    assert np.array_equal(y, stored['y'])
    split = SC.private_split(kid); S, Q = split['pool'], split['query']
    lp0, lk0, Z0 = run_all(model, x, None)
    p0 = np.exp(lp0[:, 1].double().cpu().numpy()); p_st = np.exp(stored['log_mixture'][:, 1].astype(np.float64))
    diff_q = float(np.abs(p0[Q] - p_st[Q]).max()); diff_all = float(np.abs(p0 - p_st).max())
    if check_gate:
        assert diff_q <= GATE_TOL, f'U0 query probabilities not reproduced: {diff_q}'
    assert diff_all <= SANITY_TOL, f'stored U0 forward far from recomputed ({diff_all}); wrong checkpoint or data'
    res = {'n_trials': int(len(y)), 'n_support': int(len(S)), 'n_query': int(len(Q)),
           'support_class_counts': [int((y[S] == 0).sum()), int((y[S] == 1).sum())],
           'u0_reproduction': {'max_abs_p_query': diff_q, 'max_abs_p_all': diff_all, 'tol_gate': GATE_TOL},
           'U0': SUP.query_metrics(p0[Q], y[Q]), 'stored_support_v1_U30': {k: sup_child['U30'][k] for k in ('delta', 'cal', 'fallback')}}
    if len(S) < 2 or len(np.unique(y[S])) < 2:
        res['fallback'] = {'n': int(len(S)), 'classes': int(len(np.unique(y[S])))}
        for m in ('cal',) + CRITERIA + tuple(f'{c}+cal' for c in CRITERIA):
            res[m] = res['U0']
        return res, None
    s_, b_, _ = SUP.adapt_cal(p0[S], y[S]); res['cal'] = SUP.query_metrics(SUP.calibrated(p0[Q], s_, b_), y[Q])
    sig = sigma_Z(Z0[S]); res['sigma_Z_U0'] = sig
    xs = x[S]; probs = {'U0': p0[Q]}
    for crit in CRITERIA:
        t0 = time.time()
        dW, hist = adapt(model, xs, y[S], crit, sigma=sig if crit == 'D_CS' else None)
        lpS, _, ZS = run_all(model, xs, dW); lpQ, _, _ = run_all(model, x[Q], dW)
        pS, pQ = np.exp(lpS[:, 1].double().cpu().numpy()), np.exp(lpQ[:, 1].double().cpu().numpy())
        sc, bc, chist = SUP.adapt_cal(pS, y[S]); pQc = SUP.calibrated(pQ, sc, bc)
        res[crit] = SUP.query_metrics(pQ, y[Q]); res[f'{crit}+cal'] = SUP.query_metrics(pQc, y[Q])
        cs_after, _ = cs_labels_score(ZS.double(), torch.as_tensor(y[S], device=dev), model.a, sig)
        ce_after = float(head_loss_from_Z(model, ZS, torch.as_tensor(y[S], device=dev)))
        res[f'{crit}_detail'] = {'history': hist, 'dW_fro': float(dW.norm()), 'dW_max_abs': float(dW.abs().max()),
                                 'support_ce_nats_after': ce_after, 'support_cs_nats_after': float(cs_after), 'cal_value': [sc, bc],
                                 'seconds': time.time() - t0}
        probs[crit] = pQ; probs[f'{crit}+cal'] = pQc; probs[f'{crit}_dW'] = dW.cpu().numpy()
    return res, probs


def run_unit(row, probe=False):
    import torch
    from ..aln35 import support_runtime as SR
    t0 = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    assert sha(row['ce_record']) == row['ce_record_sha256'] and sha(row['support_record']) == row['support_record_sha256']
    rec = read(row['ce_record']); sup = read(row['support_record'])
    kids = {k['id']: k for k in SR.load_kids()}; model = load_model(row, dev); dest_ck = Path(row['checkpoint']).parent
    store = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; store.mkdir(parents=True, exist_ok=True, mode=0o700)
    children, gate = {}, None
    for j, cid in enumerate(row['test_children']):
        with np.load(dest_ck / f'test_{cid}.npz') as z:
            stored = {k: z[k] for k in ('log_mixture', 'y')}
        res, probs = child_run(model, kids[cid], stored, sup['children'][cid], dev, check_gate=(probe and j == 0))
        if probe and j == 0:
            gate = {'child': cid, **res['u0_reproduction'], 'pass': res['u0_reproduction']['max_abs_p_query'] <= GATE_TOL}
            if probs is not None:     # replay of the first child's D_CE adaptation (determinism, recorded)
                x = torch.as_tensor(kids[cid]['x'], dtype=torch.float32, device=dev)
                from ..aln35 import support_contract as SC
                S = SC.private_split(kids[cid])['pool']
                dW2, _ = adapt(model, x[S], np.asarray(kids[cid]['y'], np.int64)[S], 'D_CE')
                gate['replay_D_CE_dW_max_abs_diff'] = float(np.abs(dW2.cpu().numpy() - probs['D_CE_dW']).max())
        if probs is not None:
            np.savez_compressed(store / f'{cid}.npz', **probs)
        children[cid] = res
        print(row['id'], cid, {m: round(res[m]['nll_bits'], 5) for m in ('U0', 'cal') + CRITERIA + tuple(f'{c}+cal' for c in CRITERIA)}, flush=True)
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
                raise RuntimeError('W7 adapt unit failed')


def smoke(plan):
    """One unit (B0, seed 3401, outer fold 0) as a probe; gate on its first test child (U0 reproduction <= 1e-5)."""
    job = os.environ['SLURM_JOB_ID']; rec = {'status': 'running', 'plan_sha256': sha(OUT / 'plan.json'), 'units': []}
    try:
        row = next(r for r in plan['rows'] if r['arm'] == 'B0' and r['seed'] == 3401 and r['outer_fold'] == 0)
        u = run_unit(row, probe=True)
        assert u['gate']['pass'], u['gate']
        fin = all(math.isfinite(c[m]['nll_bits']) for c in u['children'].values() for m in ('U0', 'cal') + CRITERIA + tuple(f'{x}+cal' for x in CRITERIA))
        assert fin, 'nonfinite query NLL'
        rec['units'].append({k: u[k] for k in ('gate', 'seconds', 'gpu_peak_mb', 'device', 'ce_device', 'torch')} | {'row': row['id'], 'children': len(u['children'])})
        rec['status'] = 'pass'
    except BaseException:
        rec.update(status='failed', traceback=traceback.format_exc()); raise
    finally:
        write(OUT / 'probes' / job / 'receipt.json', rec)


# ----------------------------------------------------------------------------------------------- summary (CPU)
METHODS = ('U0', 'cal', 'D_CE', 'D_CE+cal', 'D_CS', 'D_CS+cal')


def summarize():
    from ..aln41 import analysis as AN
    plan = read(OUT / 'plan.json'); fz = next(f for f in read(FAMILIES)['families'] if f['id'] == 'W7_ADAPT:private')
    per = {}                                                   # arm -> child -> seed -> {method: metrics}
    groups = {}
    for row in plan['rows']:
        u = read(OUT / 'units' / f'{row["id"]}.json'); assert u['status'] == 'complete' and not u['probe']
        for cid, r in u['children'].items():
            d = {m: r[m] for m in METHODS}
            d['stored_cal'] = r['stored_support_v1_U30']['cal']; d['stored_delta'] = r['stored_support_v1_U30']['delta']
            per.setdefault(row['arm'], {}).setdefault(cid, {})[row['seed']] = d
    from ..aln35 import support_runtime as SR
    groups = {k['id']: k['group'] for k in SR.load_kids()}
    table = {}
    for arm, kids in per.items():
        table[arm] = {}
        for cid, s in kids.items():
            if sorted(s) != list(SEEDS):
                continue
            table[arm][cid] = {m: {k: (float(np.mean([s[x][m][k] for x in SEEDS])) if all(s[x][m][k] is not None for x in SEEDS) else None)
                                   for k in ('nll_bits', 'brier', 'auc')} for m in METHODS + ('stored_cal', 'stored_delta')}
    children = sorted(set().union(*[set(v) for v in table.values()]), key=lambda c: (len(c), c))
    members = []
    for name in fz['members']:
        arm, contrast = name.split(':'); first, second = contrast.split('-')
        A, Bm = (first if first != 'cal' else 'stored_cal'), (second if second != 'cal' else 'stored_cal')
        members.append((name, {c: (table[arm][c][Bm]['nll_bits'] - table[arm][c][A]['nll_bits']) if c in table.get(arm, {}) else None for c in children}))
    fam = AN.family(fz['id'], 'query NLL bits/trial at U30, positive = first-named better', members, children)
    fam['method'] = 'aln41.analysis.family: child bootstrap-t B=4000, family max-|T*|; per child seeds 3401 / 3407 / 3413 averaged first'
    fam['cal_reference'] = 'cal = stored aln41 support_v1 U30 cal of the same checkpoint and child'
    desc = {arm: {m: {k: (float(np.mean([v[m][k] for v in t.values() if v[m][k] is not None])) if t else None) for k in ('nll_bits', 'brier', 'auc')}
                  for m in METHODS + ('stored_cal', 'stored_delta')} for arm, t in table.items()}
    by_group = {arm: {g: {m: float(np.mean([v[m]['nll_bits'] for c, v in t.items() if groups.get(c) == g])) for m in METHODS + ('stored_cal',)}
                      for g in sorted({groups[c] for c in t})} for arm, t in table.items()}
    out = {'version': 'W7_ADAPT_v1', 'bindings': plan['bindings'], 'plan_sha256': sha(OUT / 'plan.json'), 'definition': __doc__,
           'per_child': table, 'groups': {c: groups[c] for c in children}, 'descriptive_means': desc, 'nll_by_group': by_group,
           'family_inputs': {fz['id']: {'people': children, 'members': {n: v for n, v in members}}}}
    os.umask(0o022); RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'W7_ADAPT.json').write_text(json.dumps(out, indent=1, default=float) + '\n')
    (RESULTS / 'W7_ADAPT_FAMILIES.json').write_text(json.dumps({'version': 'W7_ADAPT_FAMILIES_v1', 'input_sha256': sha(RESULTS / 'W7_ADAPT.json'),
                                                                'families': [fam]}, indent=1, default=float) + '\n')
    print(json.dumps(desc, indent=1)); print(fam['status'], [(m['name'], m.get('estimate'), m.get('simultaneous_95')) for m in fam['members']])


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
