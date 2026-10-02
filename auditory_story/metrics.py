"""P3 scoring and aggregation (03_METHOD_SPEC section 8; 02_SERVER_EXECUTION sections 6.4, 7.3).

Loss first, children second: every child's losses are averaged over the label repeats and outer seeds of one budget,
then children are averaged (no implicit ensembling of predictions). Bootstrap resamples children with all their
seed / mask predictions (fixed OOF predictions; not the uncertainty of the whole development path).
"""
from __future__ import annotations

import numpy as np

LEVELS = 5


def score_sir(P: np.ndarray, y: np.ndarray, *, floor: float = 1e-6) -> dict:
    P = np.asarray(P, np.float64)
    y = np.asarray(y).astype(int)
    if P.ndim != 2 or P.shape[1] != LEVELS or not np.isfinite(P).all() or (P < -1e-12).any() \
            or not np.allclose(P.sum(1), 1.0, atol=1e-8):
        raise ValueError("probabilities must be finite [n,5] rows summing to 1")
    if not np.isin(y, [1, 2, 3, 4, 5]).all():
        raise ValueError("SIR outside 1..5")
    Q = np.maximum(P, floor)
    Q /= Q.sum(1, keepdims=True)
    F = np.cumsum(P, 1)[:, :-1]
    truth = (y[:, None] <= np.arange(1, LEVELS)[None, :]).astype(float)
    onehot = np.eye(LEVELS)[y - 1]
    return {"rps": ((F - truth) ** 2).mean(1), "nll_bits": -np.log2(Q[np.arange(len(y)), y - 1]),
            "brier": ((P - onehot) ** 2).sum(1), "expected_mae": np.abs(P @ np.arange(1, LEVELS + 1) - y),
            "p_gt3": P[:, 3:].sum(1), "floored": (P < floor).sum(1)}


def auc(score: np.ndarray, label: np.ndarray) -> float:
    """Mann-Whitney AUC with average ranks for ties; NaN if one class is absent."""
    score, label = np.asarray(score, float), np.asarray(label).astype(bool)
    n1, n0 = int(label.sum()), int((~label).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty(len(score))
    s = score[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1
        i = j + 1
    return float((ranks[label].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def child_means(frame, value: str, keys: list[str]):
    """Per child (and keys) mean of `value` over repeats and seeds: returns a Series indexed by (keys..., child)."""
    return frame.groupby(keys + ["child"])[value].mean()


def bootstrap(diff_by_child: np.ndarray, B: int, seed: int) -> dict:
    """Child-level bootstrap of a per-child difference vector (positive = second model better by convention of the
    caller). Percentile 95% interval; two-sided bootstrap p = 2 min(P(d* <= 0), P(d* >= 0)) (descriptive)."""
    d = np.asarray(diff_by_child, float)
    if not np.isfinite(d).all() or d.size == 0:
        raise ValueError("bootstrap needs finite per-child differences")
    idx = np.random.default_rng(seed).integers(0, d.size, size=(B, d.size))
    boot = d[idx].mean(1)
    p = 2 * min((boot <= 0).mean(), (boot >= 0).mean())
    return {"estimate": float(d.mean()), "ci_low": float(np.quantile(boot, 0.025)), "ci_high": float(np.quantile(boot, 0.975)),
            "p_boot_two_sided": float(min(1.0, p)), "n_children": int(d.size)}


def holm(pvals: dict) -> dict:
    keys = sorted(pvals, key=lambda k: pvals[k])
    m, running, out = len(keys), 0.0, {}
    for i, k in enumerate(keys):
        running = max(running, min(1.0, (m - i) * pvals[k]))
        out[k] = running
    return out
