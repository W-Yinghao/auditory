"""Group-level statistics fixed in MEASUREMENT_AMENDMENT_001 §7: difference of group means with a within-group
participant bootstrap (10 000 resamples, 95% percentile interval), two-sided label-permutation p (10 000), BH-FDR within
a claim family, equivalence against +-15% of the reference-group median, one-sample intervals for within-group effects."""
from __future__ import annotations

import numpy as np

B = 10_000


def diff_ci(a, b, seed=0):
    """mean(a) - mean(b): estimate, 95% bootstrap interval (resampling within each group), permutation p."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    rng = np.random.default_rng(seed)
    est = a.mean() - b.mean()
    boots = rng.choice(a, (B, len(a))).mean(1) - rng.choice(b, (B, len(b))).mean(1)
    pool = np.r_[a, b]
    perm = np.empty(B)
    for i in range(B):
        p = rng.permutation(pool)
        perm[i] = p[:len(a)].mean() - p[len(a):].mean()
    pval = (np.sum(np.abs(perm) >= abs(est)) + 1) / (B + 1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"est": float(est), "ci_low": float(lo), "ci_high": float(hi), "p_perm": float(pval), "n_a": len(a), "n_b": len(b)}


def mean_ci(a, seed=0):
    """one-sample mean with 95% bootstrap interval and sign-flip permutation p (H0: mean 0)."""
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    rng = np.random.default_rng(seed)
    boots = rng.choice(a, (B, len(a))).mean(1)
    flips = (rng.choice([-1, 1], (B, len(a))) * a).mean(1)
    pval = (np.sum(np.abs(flips) >= abs(a.mean())) + 1) / (B + 1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"est": float(a.mean()), "ci_low": float(lo), "ci_high": float(hi), "p_signflip": float(pval), "n": len(a)}


def equivalence(diff, ref_values, frac=0.15):
    bound = frac * float(np.median(ref_values))
    return {"bound": bound, "equivalent": bool(-abs(bound) < diff["ci_low"] and diff["ci_high"] < abs(bound))}


def bh(pvals):
    p = np.asarray(pvals, float); n = len(p)
    order = np.argsort(p); q = np.empty(n)
    q[order] = np.minimum.accumulate((p[order] * n / np.arange(1, n + 1))[::-1])[::-1]
    return np.minimum(q, 1.0)
