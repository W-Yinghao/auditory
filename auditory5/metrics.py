"""Outcome-blind, candidate-balanced metrics for auditory5."""

from __future__ import annotations

import numpy as np


def _validate(y, probabilities, candidate_ids=None, trial_ids=None):
    y = np.asarray(y)
    p = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or p.ndim != 2 or len(y) != len(p) or len(y) == 0:
        raise ValueError("y/probabilities must be nonempty with matching first dimension")
    if not np.isfinite(p).all() or np.any(p < 0) or np.any(y != y.astype(int)):
        raise ValueError("labels and probabilities must be finite")
    if not np.allclose(p.sum(axis=1), 1.0, atol=1e-6, rtol=1e-6):
        raise ValueError("probability rows must sum to one")
    y = y.astype(int)
    k = p.shape[1]
    if k < 2 or np.any(y < 0) or np.any(y >= k):
        raise ValueError("labels must be integer class indices in probability columns")
    if candidate_ids is None:
        candidate_ids = np.zeros(len(y), dtype=int)
    candidate_ids = np.asarray(candidate_ids)
    if candidate_ids.shape != y.shape:
        raise ValueError("candidate_ids must match y")
    if trial_ids is not None:
        trial_ids = np.asarray(trial_ids)
        if trial_ids.shape != y.shape or len(np.unique(trial_ids)) != len(trial_ids):
            raise ValueError("trial_ids must be unique and match y")
    return y, p, candidate_ids


def candidate_balanced_ce_bits(y, probabilities, candidate_ids=None, trial_ids=None, eps=1e-7):
    """CE in bits: equal class weight within candidate, then equal candidates."""
    y, p, ids = _validate(y, probabilities, candidate_ids, trial_ids)
    if not np.isfinite(eps) or eps <= 0:
        raise ValueError("eps must be positive and finite")
    losses = -np.log2(np.clip(p[np.arange(len(y)), y], eps, 1.0))
    values = []
    for cid in np.unique(ids):
        m = ids == cid
        if len(np.unique(y[m])) != p.shape[1]:
            raise ValueError("each candidate must contain every class")
        values.extend(np.mean(losses[m & (y == c)]) for c in range(p.shape[1]))
    # values are class means in candidate order; candidate and class weighted equally
    return float(np.mean(values))


def candidate_log_losses_bits(y, probabilities, candidate_ids=None, trial_ids=None, eps=1e-7):
    """Return private-friendly candidate CE values (caller controls persistence)."""
    y, p, ids = _validate(y, probabilities, candidate_ids, trial_ids)
    if not np.isfinite(eps) or eps <= 0:
        raise ValueError("eps must be positive and finite")
    losses = -np.log2(np.clip(p[np.arange(len(y)), y], eps, 1.0))
    out = {}
    for cid in np.unique(ids):
        m = ids == cid
        if len(np.unique(y[m])) != p.shape[1]:
            raise ValueError("each candidate must contain every class")
        out[str(cid)] = float(np.mean([np.mean(losses[m & (y == c)]) for c in range(p.shape[1])]))
    return out


def classification_metrics(y, probabilities, candidate_ids=None, trial_ids=None, eps=1e-7):
    """Candidate-balanced CE, balanced accuracy, AUROC and Brier score."""
    y, p, ids = _validate(y, probabilities, candidate_ids, trial_ids)
    pred = np.argmax(p, axis=1)
    baccs, briers, candidate_auroc = [], [], []
    for cid in np.unique(ids):
        m = ids == cid
        if len(np.unique(y[m])) != p.shape[1]:
            raise ValueError("each candidate must contain every class")
        baccs.append(np.mean([np.mean(pred[m & (y == c)] == c) for c in range(p.shape[1])]))
        onehot_c = np.eye(p.shape[1])[y[m]]
        briers.append(np.mean([np.mean(np.sum((p[m & (y == c)] - onehot_c[y[m] == c]) ** 2, axis=1))
                               for c in range(p.shape[1])]))
    try:
        from sklearn.metrics import roc_auc_score
        for cid in np.unique(ids):
            m = ids == cid
            candidate_auroc.append(float(roc_auc_score(y[m], p[m, 1])) if p.shape[1] == 2
                                   else float(roc_auc_score(y[m], p[m], multi_class="ovr", average="macro")))
        auroc = float(np.mean(candidate_auroc))
    except (ImportError, ValueError) as exc:
        raise ValueError("AUROC requires every class and sklearn support") from exc
    return {"ce_bits": candidate_balanced_ce_bits(y, p, ids, eps=eps),
            "J_bits": float(np.log2(p.shape[1]) - candidate_balanced_ce_bits(y, p, ids, eps=eps)),
            "bacc": float(np.mean(baccs)), "auroc": auroc,
            "brier": float(np.mean(briers)), "auroc_definition": "candidate-macro; multiclass one-vs-rest macro"}
