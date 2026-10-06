"""Runner for the registered extension units (make_ext_plan.py). The main protocol code is used unchanged; this module only
adds (i) summed objectives CS_SINGLE+NCE / FMCA+NCE and (ii) class-balanced private training batches, by wrapping
train.Objective and train.PrivateBatcher. Unit code hash = main unit code + this file.

Usage: python -m auditory_alignment.run_ext --manifest planned_jobs_ext.jsonl --job-index <i> [--epochs N] [--out DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import os

import numpy as np
import torch

from . import evaluate, run, train
from .losses import cs_qmi, deduplicated_infonce, fmca_logdet_loss

_BaseObjective, _BasePrivate = train.Objective, train.PrivateBatcher
_base_code_hash, _base_eval_cont = run.code_hash, evaluate.evaluate_continuous


def eval_cont(objective, *a, **k):
    """Summed objectives contain an NCE term that aligns u and v directly: their native readout is the NCE one (cosine)."""
    return _base_eval_cont("NCE" if objective.endswith("+NCE") else objective, *a, **k)


class ComboObjective(_BaseObjective):
    def __init__(self, job, u0, v0, labels0=None):
        super().__init__(job, u0, v0, labels0)
        self.parts = job["objective"].split("+") if "+" in job["objective"] else None

    def __call__(self, u, v=None, keys=None, labels=None, prototypes=None):
        if not self.parts:
            return super().__call__(u, v, keys=keys, labels=labels, prototypes=prototypes)
        loss, st = 0.0, {}
        for p in self.parts:  # summed at native scales (registered, not tuned)
            if p == "NCE":
                loss = loss + deduplicated_infonce(u, v, keys, self.temperature)
            elif p == "FMCA":
                loss = loss + fmca_logdet_loss(u, v, ridge_u=self.ridge_u, ridge_v=self.ridge_v)
            elif p == "CS_SINGLE":
                val, s = cs_qmi(u, v, sigma_u=self.sigma_u, sigma_v=self.sigma_v); loss = loss - val; st.update(s)
            else:
                raise ValueError(p)
        return loss, st


class BalancedPrivateBatcher(_BasePrivate):
    """Training batches: per child, half of the trials drawn from each class (when both exist). Early-stopping / selection
    batches keep the natural distribution (es=True path of the base class)."""

    def __init__(self, kids, job, dev):
        super().__init__(kids, job, dev)
        self.balanced = bool(job["config"].get("class_balanced_training"))
        yt = self.yall.cpu().numpy()
        self.fit_by_class = {i: [v[yt[v] == c] for c in (0, 1)] for i, v in self.fit_idx.items()}

    def batch(self, rng, es=False, n_kids=32, per=8, true_labels=False):
        if es or not self.balanced:
            return super().batch(rng, es=es, n_kids=n_kids, per=per, true_labels=true_labels)
        pool = [i for i in self.train if len(self.fit_idx[i])]
        ks = rng.choice(pool, size=min(n_kids, len(pool)), replace=False)
        g = []
        for i in ks:
            a, b = self.fit_by_class[i]
            if len(a) and len(b):
                g.append(np.r_[a[rng.integers(0, len(a), per - per // 2)], b[rng.integers(0, len(b), per // 2)]])
            else:
                g.append(self.fit_idx[i][rng.integers(0, len(self.fit_idx[i]), per)])
        gt = torch.tensor(np.concatenate(g), device=self.dev)
        x = self.Xall[gt].float()
        y = self.ytrue[gt] if true_labels else self.yall[gt]
        return [x[:, :, a:b] for a, b in self.W], y


def code_hash():
    h = hashlib.sha256(_base_code_hash().encode())
    h.update(open(os.path.abspath(__file__), "rb").read())
    return h.hexdigest()[:16]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--manifest", required=True); a.add_argument("--job-index", type=int); a.add_argument("--experiment-id")
    a.add_argument("--epochs", type=int); a.add_argument("--out", default=run.OUT)
    args = a.parse_args()
    train.Objective, train.PrivateBatcher = ComboObjective, BalancedPrivateBatcher
    evaluate.evaluate_continuous = eval_cont
    run.code_hash = code_hash
    run.run_job(run.load_job(args.manifest, args.job_index, args.experiment_id), args.out, args.epochs)


if __name__ == "__main__":
    main()
