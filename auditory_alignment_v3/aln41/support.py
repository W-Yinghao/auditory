"""ALN4.1 R2 personal support (F_SUPPORT; package docs/04 §4.3), CPU only. Frozen before any support result exists.

Base: each core-3 private CE unit (B0 / TCS / TNCE x 5 outer folds x seeds 3401, 3407, 3413), its selected checkpoint and the
per-trial slot log-probabilities of its outer test children (written by private_ft at the selected checkpoint). theta and the
three slot heads stay frozen, so the adapted mixture needs only those slot outputs and the checkpoint's gate logits a_target
(read from best.pt; the stored q mixture must be reproduced to 1e-5).
Support contract: aln35.support_contract.private_split on every trial of the test child.
- Pool: the earliest ceil(0.3 x blocks) physical blocks, after the inherited support[:-1] / query[1:] boundary rule and the full
  epoch guard. Query: the remaining blocks, fixed once.
- U0: no support.
- U10: n10 = min(floor(0.1 x available trials), guarded pool size) trials, drawn with each of the fixed seeds 351410..351414
  (select_support; no label coverage).
- U30: the whole guarded pool.
Methods, each from U0 and on the same support:
- delta: the mixture logits a_target + delta, delta = 0 at start; support CE (mean nats) + 0.1/2 ||delta||^2; 5 plain gradient
  steps at lr 0.1, re-centred to zero mean after each step (as the package adapt_delta_fo).
- cal: pcal = sigmoid(exp(s) logit(p) + b), with p the U0 mixture probability clipped to [1e-6, 1 - 1e-6] for the logit only;
  s = b = 0 at start; support CE + 0.1/2 (s^2 + b^2); 5 plain gradient steps at lr 0.1.
- Fallback: a support with < 2 trials or one class gets no update (delta = s = b = 0); the reason is recorded.
Query endpoints per child: NLL bits/trial (primary), Brier and AUC (supplementary). The 5 U10 draws are averaged within the
child first. Seeds are averaged within the child before contrasts.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path

import numpy as np

from .. import core
from . import private_ft as PF, r2 as R2, source as SRC

OUT = SRC.OUT / 'support_v1'
RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/aln41/r2_support'
SEEDS = (3401, 3407, 3413)
STEPS, LR, L2 = 5, 0.1, 0.1
CLIP = 1e-6
METHODS = ('delta', 'cal')
FAMILY = {'unit': 'child (64); query NLL gain over U0 in bits/trial, positive = better; seeds averaged within child',
          'per_arm': ['delta_U10-U0', 'delta_U30-U0', 'cal_U10-U0', 'cal_U30-U0', 'delta_U10-cal_U10', 'delta_U30-cal_U30'],
          'arms': ['B0', 'TCS', 'TNCE'], 'arm_contrasts': ['delta_U30 gain: TCS-B0', 'delta_U30 gain: TCS-TNCE'],
          'inference': 'sci_r1 identity bootstrap-t B=4000, family max-|T*| over the 20 members; Brier/AUC descriptive families'}
read, write, sha, digest = SRC.read, SRC.write, SRC.sha, SRC.digest


def sources():
    files = [Path(__file__), Path(core.REPO) / 'auditory_alignment_v3/aln35/support_contract.py',
             Path(core.REPO) / 'auditory_alignment_v3/aln35/support_runtime.py', Path(core.REPO) / 'auditory_alignment/data.py']
    return {str(p.relative_to(core.REPO)): sha(p) for p in sorted(set(files))}


def make_plan():
    body = {'version': 'ALN41_SUPPORT_R2_v1', 'seeds': list(SEEDS), 'arms': list(PF.ARMS), 'folds': list(PF.FOLDS),
            'steps': STEPS, 'lr': LR, 'l2': L2, 'clip': CLIP, 'methods': list(METHODS), 'supports': ['U0', 'U10x5', 'U30'],
            'family_F_SUPPORT': FAMILY, 'sources': sources(), 'support_results_seen': False}
    plan = OUT / 'plan.json'
    if plan.exists():
        old = read(plan); assert all(old[k] == v for k, v in body.items()), 'immutable plan drift'
    else:
        OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
        write(plan, {**body, 'created': datetime.now().astimezone().isoformat()}); plan.chmod(0o444)
    print('ALN41 support plan', sha(plan), flush=True)


def ce_units():
    """[(seed, row, record path)] of every complete core-3 private CE unit."""
    out = []
    for seed in SEEDS:
        if seed == SRC.SEED:
            base = PF.BASE; rows = read(base / 'plan.json')['rows']
        else:
            with R2.seeded(seed):
                base = PF.BASE; rows = read(base / 'plan.json')['rows'] if (base / 'plan.json').exists() else []
        for r in rows:
            if (base / 'units' / f'{r["id"]}.json').exists():
                out.append((seed, r, base / 'units' / f'{r["id"]}.json'))
    return out


# ----------------------------------------------------------------------------------------------- the two support methods
def log_softmax(v):
    v = v - v.max(); return v - np.log(np.exp(v).sum())


def mixture_logp(a, lk):
    """lk [n, 3, 2] slot log-probs -> mixture log-probs [n, 2] with gate logits a."""
    z = log_softmax(a)[None, :, None] + lk
    m = z.max(1, keepdims=True)
    return (m + np.log(np.exp(z - m).sum(1, keepdims=True)))[:, 0]


def adapt_delta(a, lk, y):
    """Mean support CE (nats) + L2/2 ||delta||^2; gradient of the mixture CE w.r.t. the gate logits is analytic."""
    delta = np.zeros(3); hist = []
    for _ in range(STEPS):
        lq = log_softmax(a + delta); q = np.exp(lq)
        z = lq[None, :] + lk[np.arange(len(y)), :, y]                      # log q_k + log p_k(y)  [n, 3]
        r = np.exp(z - z.max(1, keepdims=True)); r /= r.sum(1, keepdims=True)  # posterior responsibility of each slot
        loss = float(-(z.max(1) + np.log(np.exp(z - z.max(1, keepdims=True)).sum(1))).mean() + .5 * L2 * (delta ** 2).sum())
        grad = -(r - q[None, :]).mean(0) + L2 * delta
        hist.append({'loss_nats': loss, 'q': q.tolist()})
        delta = delta - LR * grad; delta = delta - delta.mean()
    return delta, hist


def adapt_cal(p, y):
    lg = np.log(np.clip(p, CLIP, 1 - CLIP)) - np.log1p(-np.clip(p, CLIP, 1 - CLIP))
    s = b = 0.0; hist = []
    for _ in range(STEPS):
        t = math.exp(s) * lg + b; pc = 1 / (1 + np.exp(-t))
        loss = float(np.mean(np.logaddexp(0, -t) * y + np.logaddexp(0, t) * (1 - y)) + .5 * L2 * (s * s + b * b))
        e = pc - y
        gs, gb = float(np.mean(e * lg) * math.exp(s) + L2 * s), float(np.mean(e) + L2 * b)
        hist.append({'loss_nats': loss, 's': s, 'b': b})
        s, b = s - LR * gs, b - LR * gb
    return s, b, hist


def calibrated(p, s, b):
    lg = np.log(np.clip(p, CLIP, 1 - CLIP)) - np.log1p(-np.clip(p, CLIP, 1 - CLIP))
    return 1 / (1 + np.exp(-(math.exp(s) * lg + b)))


def query_metrics(p1, y):
    from sklearn.metrics import roc_auc_score
    pc = np.clip(p1, 1e-12, 1 - 1e-12)
    nll = -(y * np.log(pc) + (1 - y) * np.log(1 - pc)) / math.log(2)
    return {'nll_bits': float(nll.mean()), 'brier': float(np.mean((p1 - y) ** 2)),
            'auc': float(roc_auc_score(y, p1)) if len(np.unique(y)) == 2 else None}


# ----------------------------------------------------------------------------------------------- one CE unit
def run_unit(seed, row, rec_path, kids):
    import torch
    from ..aln35 import support_contract as SC
    rec = read(rec_path); assert rec['status'] == 'complete' and not rec['probe']
    ck = rec['checkpoints']['selected']; assert sha(ck) == rec['checkpoints']['selected_sha256']
    a = torch.load(ck, map_location='cpu', weights_only=True)['a'].double().numpy()
    dest = Path(ck).parent; by_id = {k['id']: k for k in kids}
    out = {'seed': seed, 'row': row, 'record_sha256': sha(rec_path), 'a_target': a.tolist(), 'children': {}}
    for cid in rec['test']['selected']:
        k = by_id[cid]
        with np.load(dest / f'test_{cid}.npz') as z:
            lk, lm, y = z['log_slots'].astype(np.float64), z['log_mixture'].astype(np.float64), z['y'].astype(np.int64)
        assert np.array_equal(y, k['y'])
        base = mixture_logp(a, lk); assert np.abs(base - lm).max() < 1e-4, 'stored mixture not reproduced from a_target'
        split = SC.private_split(k); q = split['query']; pool = split['pool']
        sel = SC.select_support(pool, split['n10'], cid, groups=k['block'][pool])   # U10/U30 ignore groups (C10 unused)
        p0 = np.exp(base[:, 1]); res = {'n_query': int(len(q)), 'n_pool': int(len(pool)), 'n10': int(split['n10']),
                                        'U0': query_metrics(p0[q], y[q]), 'fallbacks': []}
        for name, S in [(f'U10_{s}', sel[f'U10_{s}']) for s in SC.SAMPLING_SEEDS] + [('U30', sel['U30'])]:
            ys = y[S]
            if len(S) < 2 or len(np.unique(ys)) < 2:
                res['fallbacks'].append({'support': name, 'n': int(len(S)), 'classes': int(len(np.unique(ys)))})
                res[name] = {'delta': res['U0'], 'cal': res['U0'], 'fallback': True}
                continue
            d, dh = adapt_delta(a, lk[S], ys)
            s_, b_, ch = adapt_cal(p0[S], ys)
            res[name] = {'delta': query_metrics(np.exp(mixture_logp(a + d, lk[q])[:, 1]), y[q]),
                         'cal': query_metrics(calibrated(p0[q], s_, b_), y[q]), 'fallback': False,
                         'delta_value': d.tolist(), 'cal_value': [s_, b_], 'support_n': int(len(S)),
                         'support_class_counts': [int((ys == 0).sum()), int((ys == 1).sum())],
                         'delta_loss_first_last': [dh[0]['loss_nats'], dh[-1]['loss_nats']],
                         'cal_loss_first_last': [ch[0]['loss_nats'], ch[-1]['loss_nats']]}
        for m in METHODS:
            draws = [res[f'U10_{s}'][m] for s in SC.SAMPLING_SEEDS]
            res[f'U10_{m}_mean'] = {k_: (float(np.mean([d_[k_] for d_ in draws])) if all(d_[k_] is not None for d_ in draws) else None)
                                    for k_ in ('nll_bits', 'brier', 'auc')}
        out['children'][cid] = res
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--make-plan', action='store_true'); ap.add_argument('--run', action='store_true')
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.make_plan:
        make_plan(); return
    plan = read(OUT / 'plan.json'); assert plan['sources'] == sources(), 'frozen source drift'
    from ..aln35 import support_runtime as SR
    kids = SR.load_kids()
    for seed, row, path in ce_units():
        dest = OUT / 'units' / f'{row["id"]}.json'
        if dest.exists():
            continue
        write(dest, {**run_unit(seed, row, path, kids), 'plan_sha256': sha(OUT / 'plan.json')})
        print('support', seed, row['arm'], row['outer_fold'], flush=True)


if __name__ == '__main__':
    main()
