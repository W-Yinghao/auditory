"""ALN4.1 R1 private CE full fine-tuning: core arms B0 / TCS / TNCE x 5 outer child folds (15 fits).

Children: auditory_alignment.data.load_private() (64; 20 channels x 200 samples at 250 Hz, epoch [-200, 600) ms, per-child
z-score of the inherited loader). Three native crops [0:100], [50:150], [100:200] (W0, W1, W2) -> crop-only resampling to
80 points -> pad 200 -> one shared CBraMod backbone. Per slot an independent channel-aware signed spatial readout
(fm_readout.SpatialPatchHead, K 8, e 32, d 32) and a 2-class linear classifier; p = sum_k softmax(a)_k p_k, loss
-log p_y via logsumexp. Initialisation: B0 = generic CBraMod (a = 0); TCS/TNCE = the ALN4.1 production source backbone
and its learned a at update 10000. All of theta, heads and a train from the first step; outer test children use delta = 0.
AdamW lr 1e-4 (weight decay 1e-4; biases, norms and a 0), batch 64, 100 epochs, cosine, clip 5; updates per epoch =
ceil(N_fit/64), each draw = uniform training child then a uniform fit trial of that child (natural class mix).
Selection: minimum equal-child source-ES true-label NLL over epochs 0..100 (tie -> earlier); the last state is kept.
Test children never enter training or selection.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from .. import core
from . import source as SRC

BASE = SRC.OUT / 'private_ft_v1'
STORE = SRC.STORE.parent / 'private_ft_v1'
ARMS = ('B0', 'TCS', 'TNCE')
FOLDS = (0, 1, 2, 3, 4)
EPOCHS, BATCH, LR = 100, 64, 1e-4
ONSET = 50
NAME, LANE, SBATCH = 'c3_s35a41prv', 's35_aln41_private', 'slurm/aln35_aln41_private.sbatch'
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest


def sources():
    here = Path(__file__).parent
    files = [here / 'private_ft.py', here / 'timebank.py', here / 'time_access.py', Path(core.REPO) / 'auditory_alignment/data.py',
             Path(core.REPO) / 'auditory_c3/c3dl/hc.py', Path(core.REPO) / 'auditory_alignment_v2/fm_readout.py',
             Path(core.REPO) / 'auditory_alignment_v2/foundation_adapter.py']
    return {str(p.relative_to(core.REPO)): sha(p) for p in sorted(set(files))}


def make_plan():
    rows = []
    for arm in ARMS:
        for f in FOLDS:
            body = {'arm': arm, 'outer_fold': f, 'seed': SRC.SEED, 'epochs': EPOCHS, 'batch': BATCH, 'lr': LR}
            rows.append({**body, 'id': 'ALN41F_' + digest(body, 16)})
    body = {'version': 'ALN41_PRIVATE_FT_v1', 'rows': rows, 'sources': sources(), 'store': str(STORE),
            'source_plan_sha256': sha(SRC.BASE / 'plan.json'), 'stage1': read(SRC.BASE / 'plan.json')['stage1']}
    plan = BASE / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        STORE.mkdir(parents=True, exist_ok=True, mode=0o700); write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    print('ALN41 private FT plan', len(rows), sha(plan), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'frozen source drift'


def source_init(arm):
    """(backbone net state or None, a) for an arm; TCS/TNCE need the completed production source unit."""
    import torch
    if arm == 'B0':
        return None, torch.zeros(3), {'kind': 'generic_cbramod'}
    sel = read(SRC.BASE / 'selection.json'); row = next(r for r in sel['production_rows'] if r['arm'] == arm)
    rec = read(SRC.BASE / 'units' / f'{row["id"]}.json'); assert rec['status'] == 'complete' and rec['updates'] == SRC.PROD_STEPS
    ck = rec['checkpoints'][str(SRC.PROD_STEPS)]; assert sha(ck['path']) == ck['sha256']
    st = torch.load(ck['path'], map_location='cpu', weights_only=False)
    net = {k[len('net.'):]: v for k, v in st['backbone'].items() if k.startswith('net.')}
    return net, st['a'].float(), {'kind': 'aln41_source', 'unit': row['id'], 'checkpoint': ck}


def ready(row):
    if row['arm'] == 'B0':
        return True
    if not (SRC.BASE / 'selection.json').exists():
        return False
    sel = read(SRC.BASE / 'selection.json'); r = next(x for x in sel['production_rows'] if x['arm'] == row['arm'])
    return (SRC.BASE / 'units' / f'{r["id"]}.json').exists()



def build(net_state, a0, seed, dev):
    import torch
    import torch.nn as nn
    from auditory_alignment_v2.foundation_adapter import Backbone
    from auditory_alignment_v2.fm_readout import SpatialPatchHead

    class Model(nn.Module):
        def __init__(self):
            super().__init__()
            self.bb = Backbone('cbramod', 'private_bdf', 'pretrained_full', 200, init_state=net_state)
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(seed)
                self.slots = nn.ModuleList([SpatialPatchHead(200, 20, d=32, K=8, e=32) for _ in range(3)])
                self.cls = nn.ModuleList([nn.Linear(32, 2) for _ in range(3)])
            self.a = nn.Parameter(a0.clone().float())

        def slot_logits(self, x):
            from . import timebank as TB
            B = x.shape[0]
            lay = TB.layout(250)
            crops = [x[..., ONSET + a:ONSET + b] for a, b, _ in lay]
            h = self.bb(TB.crop_inputs(crops, 250))                       # [3B, C, 1, E]
            h = h.reshape(3, B, *h.shape[1:])
            return torch.stack([self.cls[k](self.slots[k](h[k])[:, 0]) for k in range(3)], 1)   # [B, 3, 2]

        def log_probs(self, x, uniform=False):
            lk = torch.log_softmax(self.slot_logits(x), -1)
            lq = torch.log_softmax(torch.zeros_like(self.a) if uniform else self.a, 0)
            return torch.logsumexp(lq[None, :, None] + lk, 1), lk          # mixture [B, 2], slots [B, 3, 2]
    return Model().to(dev)


def param_groups(model):
    decay, no = [], []
    for n, p in model.named_parameters():
        (no if (p.ndim <= 1 or n.endswith('.bias') or n == 'a') else decay).append(p)
    return [{'params': decay, 'weight_decay': 1e-4}, {'params': no, 'weight_decay': 0.0}]


def nll_bits(lp, y):
    return -lp[np.arange(len(y)), y] / math.log(2)


def evaluate(model, X, kids, idx, dev):
    import torch
    out = {}
    model.eval()
    with torch.no_grad():
        for i in idx:
            x = X[i]; lp, lk, lu = [], [], []
            for s in range(0, len(x), 512):
                m, k = model.log_probs(x[s:s + 512]); u, _ = model.log_probs(x[s:s + 512], uniform=True)
                lp.append(m.cpu().numpy()); lk.append(k.cpu().numpy()); lu.append(u.cpu().numpy())
            out[i] = (np.concatenate(lp), np.concatenate(lk), np.concatenate(lu))
    return out


def metrics(lp, y):
    from sklearn.metrics import roc_auc_score
    p = np.exp(lp[:, 1]); pred = (p >= .5).astype(int)
    tpr = float(((pred == 1) & (y == 1)).sum() / max(1, (y == 1).sum())); tnr = float(((pred == 0) & (y == 0)).sum() / max(1, (y == 0).sum()))
    return {'auc': float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None, 'nll_bits': float(nll_bits(lp, y).mean()),
            'brier': float(np.mean((p - y) ** 2)), 'ba_at_0p5': (tpr + tnr) / 2, 'n_trials': int(len(y)),
            'class_counts': {'0': int((y == 0).sum()), '1': int((y == 1).sum())}}


def run_unit(row, plan, probe=False):
    import torch
    from auditory_alignment import data
    started = time.time(); dev = torch.device('cuda'); job = os.environ['SLURM_JOB_ID']
    kids = data.load_private(); f = row['outer_fold']
    train = [i for i, k in enumerate(kids) if k['fold'] != f]; test = [i for i, k in enumerate(kids) if k['fold'] == f]
    assert len(kids) == 64 and len(test) in (12, 13)
    X = [torch.as_tensor(k['x'], dtype=torch.float32, device=dev) for k in kids]
    Y = [np.asarray(k['y'], np.int64) for k in kids]
    fit = {i: np.flatnonzero(~kids[i]['es_mask']) for i in train}; es = {i: np.flatnonzero(kids[i]['es_mask']) for i in train}
    assert all(len(fit[i]) for i in train) and sum(len(v) for v in es.values())
    net, a0, init = source_init(row['arm'])
    model = build(net, a0, SRC.SEED + 1000 * f, dev)
    opt = torch.optim.AdamW(param_groups(model), lr=LR)
    n_fit = sum(len(v) for v in fit.values()); per_epoch = math.ceil(n_fit / BATCH)
    epochs = 1 if probe else EPOCHS
    if probe:
        per_epoch = 3
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs * per_epoch)
    rng = np.random.default_rng(SRC.SEED + 1000 * f + 7)
    dest = (STORE / 'probes' / job if probe else STORE / 'units') / row['id']; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    es_children = sorted(es)

    def es_nll():
        ev = evaluate(model, X, kids, es_children, dev)
        return float(np.mean([nll_bits(ev[i][0][es[i]], Y[i][es[i]]).mean() for i in es_children]))

    curve = [{'epoch': 0, 'es_nll_bits': es_nll()}]
    best = (curve[0]['es_nll_bits'], 0); torch.save(model.state_dict(), dest / 'best.pt')
    params = [p for g in opt.param_groups for p in g['params']]
    for ep in range(1, epochs + 1):
        model.train(); losses = []
        for _ in range(per_epoch):
            ch = rng.choice(train, size=BATCH, replace=True)
            tr = np.array([fit[c][rng.integers(len(fit[c]))] for c in ch])
            xb = torch.stack([X[c][t] for c, t in zip(ch, tr)]); yb = torch.as_tensor([Y[c][t] for c, t in zip(ch, tr)], device=dev)
            lp, _ = model.log_probs(xb)
            loss = -lp[torch.arange(len(yb), device=dev), yb].mean()
            opt.zero_grad(set_to_none=True); loss.backward()
            gn = torch.nn.utils.clip_grad_norm_(params, 5.0)
            if not torch.isfinite(loss) or not torch.isfinite(gn):
                raise FloatingPointError('nonfinite private CE loss/gradient')
            opt.step(); sched.step(); losses.append(float(loss))
        cur = es_nll(); curve.append({'epoch': ep, 'es_nll_bits': cur, 'train_ce_nats': float(np.mean(losses)), 'a': model.a.detach().cpu().tolist()})
        if cur < best[0]:
            best = (cur, ep); torch.save(model.state_dict(), dest / 'best.pt')
        if ep % 10 == 0:
            print(row['id'], row['arm'], 'fold', f, 'epoch', ep, round(cur, 5), round(time.time() - started, 1), flush=True)
    torch.save(model.state_dict(), dest / 'last.pt')
    results = {}
    for label, path in (('selected', dest / 'best.pt'), ('last', dest / 'last.pt')):
        model.load_state_dict(torch.load(path, map_location=dev))
        ev = evaluate(model, X, kids, test, dev); per = {}
        for i in test:
            lp, lk, lu = ev[i]; y = Y[i]
            per[kids[i]['id']] = {'group': kids[i]['group'], 'mixture': metrics(lp, y), 'uniform_q': metrics(lu, y),
                                  'slots': [metrics(lk[:, k], y) for k in range(3)]}
            if label == 'selected':
                np.savez_compressed(dest / f'test_{kids[i]["id"]}.npz', log_mixture=lp, log_slots=lk, log_uniform=lu, y=y)
        results[label] = per
    rec = {'status': 'complete', 'row': row, 'probe': probe, 'plan_sha256': sha(BASE / 'plan.json'), 'init': init,
           'initial_a': a0.tolist(), 'final_a': model.a.detach().cpu().tolist(), 'curve': curve, 'selected_epoch': best[1],
           'selected_es_nll_bits': best[0], 'checkpoints': {'selected': str(dest / 'best.pt'), 'selected_sha256': sha(dest / 'best.pt'),
                                                            'last': str(dest / 'last.pt'), 'last_sha256': sha(dest / 'last.pt')},
           'label_access': {'fit_trials': n_fit, 'es_trials': int(sum(len(v) for v in es.values())), 'train_children': len(train),
                            'test_children': len(test), 'test_labels_used_for_training_or_selection': False},
           'updates_per_epoch': per_epoch, 'epochs': epochs, 'test': results, 'device': torch.cuda.get_device_name(0), 'job': job,
           'seconds': time.time() - started, 'gpu_peak_mb': torch.cuda.max_memory_allocated() / 2 ** 20}
    out = BASE / 'probes' / job if probe else BASE
    write(out / 'units' / f'{row["id"]}.json', rec)
    print(row['id'], 'complete', row['arm'], f, 'selected epoch', best[1], round(rec['seconds'], 1), flush=True)
    return rec


def receipts():
    out = {'pass': [], 'other': []}
    if not (BASE / 'plan.json').exists():
        return out
    for path in sorted((BASE / 'probes').glob('*/receipt.json')):
        rec = read(path)
        if rec.get('plan_sha256') == sha(BASE / 'plan.json'):
            out['pass' if rec.get('status') == 'pass' else 'other'].append(path)
    return out


def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 15, 'slots': 1, 'initial': [], 'submit': []}
    if not (BASE / 'plan.json').exists():
        return st
    plan = read(BASE / 'plan.json')
    remaining = [r for r in plan['rows'] if not (BASE / 'units' / f'{r["id"]}.json').exists()]
    st['remaining'] = len(remaining)
    if not remaining:
        st['state'] = 'complete'; return st
    rec = receipts()
    if not rec['pass']:
        if rec['other']:
            st['state'] = 'engineering_probe_failed'; return st
        st.update(state='ready', ready=1, submit=[SBATCH, '--smoke']); return st
    available = [r for r in remaining if ready(r) and not (BASE / 'units' / f'{r["id"]}.FAILED.json').exists()]
    st.update(state='ready' if available else 'waiting_for_sources', ready=len(available), slots=2,
              submit=[SBATCH, '--smoke-job', rec['pass'][-1].parent.name, '--max-units', '1'])
    return st


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--make-plan', action='store_true'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--probe-unit'); ap.add_argument('--smoke-job'); ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(BASE / 'plan.json'); verify(plan)
    if a.unit or a.probe_unit:
        run_unit(next(r for r in plan['rows'] if r['id'] in (a.unit, a.probe_unit)), plan, probe=bool(a.probe_unit)); return
    if a.smoke:
        job = os.environ['SLURM_JOB_ID']; receipt = {'status': 'running', 'plan_sha256': sha(BASE / 'plan.json'), 'units': []}
        try:
            row = next(r for r in plan['rows'] if r['arm'] == 'B0' and r['outer_fold'] == 0)
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--probe-unit', row['id']]).returncode
            assert rc == 0
            rec = read(BASE / 'probes' / job / 'units' / f'{row["id"]}.json')
            assert rec['label_access']['test_children'] in (12, 13) and len(rec['curve']) == 2
            receipt['units'].append({'id': row['id'], 'seconds': rec['seconds'], 'peak_mb': rec['gpu_peak_mb'], 'curve': rec['curve']})
            receipt['status'] = 'pass'
        except BaseException:
            receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally:
            write(BASE / 'probes' / job / 'receipt.json', receipt)
        return
    rec = read(BASE / 'probes' / str(a.smoke_job) / 'receipt.json'); assert rec['status'] == 'pass' and rec['plan_sha256'] == sha(BASE / 'plan.json')
    count = 0
    for row in plan['rows']:
        path = BASE / 'units' / f'{row["id"]}.json'
        if path.exists() or (BASE / 'units' / f'{row["id"]}.FAILED.json').exists() or not ready(row):
            continue
        lock = BASE / 'claims' / f'{row["id"]}.lock'; lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if path.exists():
                continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', row['id']]).returncode
            if rc or not path.exists():
                write(BASE / 'units' / f'{row["id"]}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'returncode': rc})
                raise RuntimeError('aln41 private FT unit failed')
            count += 1
        if count >= a.max_units:
            break


if __name__ == '__main__':
    main()
