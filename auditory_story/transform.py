"""Training-pool transforms (03_METHOD_SPEC sections 1-3): child x class-equal standardisation + PCA-32 of the frozen
192-d trial embeddings, history scaling, and the frozen population response model q0.

Every fit receives only outer-training (auxiliary pool) rows; callers assert that no outer-test child is present.
All solves are FP64. Nothing here reads files or clinical values.
"""
from __future__ import annotations

import numpy as np

from .runtime import stable_int


def cell_weights(child: np.ndarray, cls: np.ndarray) -> np.ndarray:
    """Row weights giving every (child, class) cell the same total weight; weights sum to 1."""
    child, cls = np.asarray(child), np.asarray(cls)
    keys = child.astype(np.int64) * 16 + cls.astype(np.int64)
    uniq, inv, counts = np.unique(keys, return_inverse=True, return_counts=True)
    return (1.0 / (len(uniq) * counts))[inv]


def pca_sample(child: np.ndarray, cls: np.ndarray, per_cell: int, seed: int) -> np.ndarray:
    """Row indices: at most `per_cell` rows per (child, class), fixed-seed sampling without replacement, sorted."""
    child, cls = np.asarray(child), np.asarray(cls)
    out = []
    for c in np.unique(child):
        for k in np.unique(cls[child == c]):
            rows = np.flatnonzero((child == c) & (cls == k))
            if rows.size > per_cell:
                rng = np.random.default_rng(stable_int(seed, int(c), int(k)) % (2 ** 63))
                rows = np.sort(rng.choice(rows, per_cell, replace=False))
            out.append(rows)
    return np.sort(np.concatenate(out))


def fit_projection(x: np.ndarray, child: np.ndarray, cls: np.ndarray, max_dim: int, *, whiten: bool = True) -> dict:
    """Weighted standardisation + PCA. Returns mean, sd, components [D, r], scale [r] (sqrt eigenvalues), rank.

    Rank: eigenvalues above 1e-10 x the largest; r = min(max_dim, rank) and never padded with random directions.
    Signs: the largest-magnitude loading of every component is positive (deterministic)."""
    x = np.asarray(x, np.float64)
    w = cell_weights(child, cls)
    mean = w @ x
    var = w @ (x - mean) ** 2
    sd = np.sqrt(var)
    constant = sd < 1e-12
    sd = np.where(constant, 1.0, sd)
    z = (x - mean) / sd
    cov = (z * w[:, None]).T @ z
    evals, evecs = np.linalg.eigh(cov)
    order = np.argsort(evals)[::-1]
    evals, evecs = evals[order], evecs[:, order]
    rank = int((evals > 1e-10 * max(evals[0], 1e-300)).sum())
    r = min(int(max_dim), rank)
    comp = evecs[:, :r].copy()
    flip = np.sign(comp[np.argmax(np.abs(comp), axis=0), np.arange(r)])
    comp *= np.where(flip == 0, 1.0, flip)
    scale = np.sqrt(evals[:r]) if whiten else np.ones(r)
    return {"mean": mean, "sd": sd, "components": comp, "scale": scale, "rank": rank, "dim": r,
            "constant_features": int(constant.sum()), "explained": float(evals[:r].sum() / evals[evals > 0].sum())}


def apply_projection(T: dict, x: np.ndarray) -> np.ndarray:
    z = (np.asarray(x, np.float64) - T["mean"]) / T["sd"]
    return ((z @ T["components"]) / T["scale"]).astype(np.float32)


def fit_history(h_raw: np.ndarray, child: np.ndarray, cls: np.ndarray) -> dict:
    """Training-pool medians for missing history values, then child x class-equal mean / sd of the imputed values."""
    h = np.asarray(h_raw, np.float64)
    med = np.nanmedian(h, axis=0)
    if not np.isfinite(med).all():
        raise ValueError("a history field has no observed training value")
    hi = np.where(np.isfinite(h), h, med[None, :])
    w = cell_weights(child, cls)
    mean = w @ hi
    sd = np.sqrt(w @ (hi - mean) ** 2)
    sd = np.where(sd < 1e-12, 1.0, sd)
    return {"median": med, "mean": mean, "sd": sd, "missing_counts": np.isnan(h).sum(0).astype(int)}


def apply_history(Hs: dict, h_raw: np.ndarray) -> np.ndarray:
    h = np.asarray(h_raw, np.float64)
    hi = np.where(np.isfinite(h), h, Hs["median"][None, :])
    return ((hi - Hs["mean"]) / Hs["sd"]).astype(np.float32)


def fit_population(e: np.ndarray, h: np.ndarray, cls: np.ndarray, child: np.ndarray, *, n_conditions: int = 2,
                   alpha: float = 0.1, logvar_bounds=(-4.0, 3.0)) -> dict:
    """Per condition s: weighted ridge m0(s,h) = [1,h] A_s with every child's rows in s carrying equal total weight
    (weights sum to 1), alpha on the non-intercept rows only; v0(s) = weighted per-dimension residual variance,
    log-variance clipped. Returns coefficients [K, H+1, D] and logvar [K, D] (FP64)."""
    e, h = np.asarray(e, np.float64), np.asarray(h, np.float64)
    cls, child = np.asarray(cls), np.asarray(child)
    K, D, H = int(n_conditions), e.shape[1], h.shape[1]
    coef = np.zeros((K, H + 1, D))
    logvar = np.zeros((K, D))
    info = []
    for s in range(K):
        m = cls == s
        if not m.any():
            raise ValueError(f"no training rows for condition {s}")
        kids, inv, counts = np.unique(child[m], return_inverse=True, return_counts=True)
        w = (1.0 / (len(kids) * counts))[inv]
        X = np.concatenate([np.ones((int(m.sum()), 1)), h[m]], 1)
        P = np.eye(H + 1) * float(alpha)
        P[0, 0] = 0.0
        A = np.linalg.solve((X * w[:, None]).T @ X + P, (X * w[:, None]).T @ e[m])
        resid = e[m] - X @ A
        var = w @ resid ** 2
        coef[s] = A
        logvar[s] = np.clip(np.log(np.maximum(var, 1e-300)), *logvar_bounds)
        info.append({"condition": s, "children": int(len(kids)), "rows": int(m.sum()), "weight_sum": float(w.sum()),
                     "logvar_clipped": int(((np.log(np.maximum(var, 1e-300)) < logvar_bounds[0]) |
                                            (np.log(np.maximum(var, 1e-300)) > logvar_bounds[1])).sum())})
    return {"coefficients": coef, "logvar": logvar, "info": info}
