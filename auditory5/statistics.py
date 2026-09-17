"""Candidate-level paired bootstrap statistics for auditory5."""

from __future__ import annotations

import numpy as np


def _summary(values, n_boot, seed):
    v = np.asarray(values, float)
    if v.ndim != 1 or len(v) == 0 or not np.isfinite(v).all():
        raise ValueError("values must be a nonempty finite vector")
    rng = np.random.default_rng(seed)
    boots = np.array([np.mean(v[rng.integers(0, len(v), len(v))]) for _ in range(n_boot)])
    return {"estimate": float(np.mean(v)), "ci_lower": float(np.quantile(boots, .025)),
            "ci_upper": float(np.quantile(boots, .975)), "n_candidates": int(len(v)),
            "n_bootstrap": int(n_boot), "seed": int(seed)}


def paired_cluster_bootstrap(baseline, augmented, candidate_ids, n_boot=2000, seed=20260917):
    """Bootstrap paired candidate losses; repeated rows are first averaged per ID."""
    a, b, ids = map(np.asarray, (baseline, augmented, candidate_ids))
    if a.ndim != 1 or b.shape != a.shape or ids.shape != a.shape or len(a) == 0:
        raise ValueError("paired vectors must be nonempty and same shaped")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or n_boot <= 0:
        raise ValueError("losses finite and n_boot positive required")
    diffs = np.array([np.mean(a[ids == i] - b[ids == i]) for i in np.unique(ids)])
    result = _summary(diffs, n_boot, seed)
    result.update({"effect": "baseline_minus_augmented", "gain_definition": "baseline - augmented", "valid": True})
    return result


def _a_stat(x, y, ids):
    if len(np.unique(ids)) < 2:
        return None
    norms_x, norms_y = np.linalg.norm(x, axis=1), np.linalg.norm(y, axis=1)
    denominator = norms_x[:, None] * norms_y[None, :]
    cos = np.divide(x @ y.T, denominator, out=np.full(denominator.shape,np.nan), where=denominator>0)
    same = ids[:, None] == ids[None, :]
    diagonal = np.diag(cos)[np.isfinite(np.diag(cos))]
    finite = np.isfinite(cos)
    off = cos[(~same) & finite]
    ranks = []
    for i in range(len(ids)):
        if np.isfinite(cos[i, i]):
            competitors = cos[i, :][(ids != ids[i]) & np.isfinite(cos[i, :])]
            if len(competitors):
                ranks.append(1 + int(np.sum(competitors > cos[i, i])))
    return {"cosine": float(np.mean(diagonal) - np.mean(off)) if len(diagonal) and len(off) else np.nan,
            "inner_product": float(np.mean(np.diag(x @ y.T)) - np.mean((x @ y.T)[(~same) & np.isfinite(x @ y.T)])),
            "rank": float(np.mean(ranks)) if ranks else np.nan,
            "zero_vector_count": int(np.sum((norms_x == 0) | (norms_y == 0))),
            "undefined_zero_vector": bool(np.any((norms_x == 0) | (norms_y == 0)))}


def a_matching_statistic(x_a, x_b, candidate_ids, fold_ids=None):
    """A diagonal-minus-distinct-ID off-diagonal statistic, fold averaged."""
    x, y, ids = map(np.asarray, (x_a, x_b, candidate_ids))
    if x.ndim != 2 or y.shape != x.shape or ids.shape != (len(x),):
        raise ValueError("A arrays must be [n,d], matching, and have IDs")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("A representations must be finite")
    folds = np.zeros(len(x), int) if fold_ids is None else np.asarray(fold_ids)
    if folds.shape != ids.shape:
        raise ValueError("fold_ids must match candidate_ids")
    vals = [(int(len(np.unique(ids[folds == f]))),
             _a_stat(x[folds == f], y[folds == f], ids[folds == f]))
            for f in np.unique(folds)]
    if any(v[1] is None for v in vals):
        raise ValueError("each fold requires at least two distinct candidates")
    if not vals:
        raise ValueError("fewer than two distinct candidates")
    total = sum(n for n, _ in vals)
    return {"cosine": float(sum(n * v["cosine"] for n, v in vals) / total),
            "inner_product": float(sum(n * v["inner_product"] for n, v in vals) / total),
            "rank": float(sum(n * v["rank"] for n, v in vals) / total),
            "zero_vector_count": int(sum(v["zero_vector_count"] for _, v in vals)),
            "undefined_zero_vector": bool(any(v["undefined_zero_vector"] for _, v in vals))}


def a_candidate_bootstrap(x_a, x_b, candidate_ids, fold_ids=None, n_boot=2000, seed=20260917):
    """Candidate-weighted A bootstrap; duplicate draws never become non-matches."""
    x, y, ids = map(np.asarray, (x_a, x_b, candidate_ids))
    folds = np.zeros(len(x), int) if fold_ids is None else np.asarray(fold_ids)
    if x.ndim != 2 or y.shape != x.shape or ids.shape != (len(x),) or folds.shape != ids.shape:
        raise ValueError("invalid A bootstrap shapes")
    rng = np.random.default_rng(seed)
    out, invalid = [], 0
    for _ in range(n_boot):
        stats = []
        for f in np.unique(folds):
            ix = np.flatnonzero(folds == f); unique = np.unique(ids[ix])
            if len(unique) < 2: stats = []; break
            draw = rng.choice(unique, len(unique), replace=True)
            # one representative row per sampled ID; identity remains attached to draw
            xa = np.stack([x[ix[np.flatnonzero(ids[ix] == d)[0]]] for d in draw])
            xb = np.stack([y[ix[np.flatnonzero(ids[ix] == d)[0]]] for d in draw])
            s = _a_stat(xa, xb, draw)
            if s is None: stats = []; break
            stats.append(s)
        if not stats: invalid += 1
        else:
            fold_sizes = [len(np.unique(ids[folds == f])) for f in np.unique(folds)]
            out.append(float(np.average([s["cosine"] for s in stats], weights=fold_sizes)))
    if not out: raise ValueError("all A bootstrap replicates invalid")
    original = a_matching_statistic(x, y, ids, folds)
    boot = np.asarray(out)
    result = {"estimate": float(original["cosine"]), "ci_lower": float(np.quantile(boot, .025)),
              "ci_upper": float(np.quantile(boot, .975)), "n_candidates": int(len(np.unique(ids))),
              "n_bootstrap": int(len(out)), "seed": int(seed)}
    result.update({"requested_bootstrap": int(n_boot), "invalid_replicates": int(invalid), "valid": True})
    return result
