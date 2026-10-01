"""Input representations for the age readouts (execution spec sections 4.3, 4.5, 5).

Paired views share ONE per-dimension centre/scale estimated on the training children of the current fit (children and
classes weighted equally), then rotate: c = (z0 + z1)/sqrt2, d = (z1 - z0)/sqrt2. pair = [z0, z1] and joint = [c, d]
differ by an orthogonal rotation, so an isotropic ridge gives identical predictions (T3). *_bs views re-standardise
c and d separately (approved sensitivity, plan section 3a) and therefore change the penalty geometry on purpose.
"""
from __future__ import annotations

import numpy as np

SQRT2 = float(np.sqrt(2.0))
PAIRED_VIEWS = ("std", "dev", "common", "contrast", "joint", "pair", "contrast_bs", "joint_bs")
STANDARD_VIEWS = ("spectral_ridge", "spectral_rbf", "technical", "technical_noscale")


def paired_scale_fit(mu0: np.ndarray, mu1: np.ndarray, floor: float) -> tuple[np.ndarray, np.ndarray, int]:
    stacked = np.concatenate([np.asarray(mu0, float), np.asarray(mu1, float)], axis=0)
    m = stacked.mean(0)
    s = stacked.std(0)
    small = s < floor
    return m, np.where(small, 1.0, s), int(small.sum())


def _zscore_fit(X: np.ndarray, floor: float) -> tuple[np.ndarray, np.ndarray, int]:
    m = X.mean(0)
    s = X.std(0)
    small = s < floor
    return m, np.where(small, 1.0, s), int(small.sum())


def paired_design(view: str, mu0: np.ndarray, mu1: np.ndarray, train: np.ndarray, test: np.ndarray, *,
                  floor: float = 1e-8) -> tuple[np.ndarray, np.ndarray, dict]:
    """Rows `train` / `test` of the view matrix; every scale is estimated on `train` only."""
    mu0, mu1 = np.asarray(mu0, float), np.asarray(mu1, float)
    m, s, n_floor = paired_scale_fit(mu0[train], mu1[train], floor)
    z0, z1 = (mu0 - m) / s, (mu1 - m) / s
    c, d = (z0 + z1) / SQRT2, (z1 - z0) / SQRT2
    info = {"n_scale_floor": n_floor}
    if view == "std":
        X = z0
    elif view == "dev":
        X = z1
    elif view == "common":
        X = c
    elif view == "contrast":
        X = d
    elif view == "joint":
        X = np.concatenate([c, d], 1)
    elif view == "pair":
        X = np.concatenate([z0, z1], 1)
    elif view in ("contrast_bs", "joint_bs"):
        dm, ds, nd = _zscore_fit(d[train], floor)
        blocks = [(d - dm) / ds]
        info["n_block_floor_d"] = nd
        if view == "joint_bs":
            cm, cs, nc = _zscore_fit(c[train], floor)
            blocks = [(c - cm) / cs] + blocks
            info["n_block_floor_c"] = nc
        X = np.concatenate(blocks, 1)
    else:
        raise ValueError(view)
    return X[train], X[test], info


def standard_design(X: np.ndarray, train: np.ndarray, test: np.ndarray, *, floor: float = 1e-8,
                    missing_flags: bool = False) -> tuple[np.ndarray, np.ndarray, dict]:
    """Per-feature z-score on `train`; optional training-median imputation with missingness flags."""
    X = np.asarray(X, float).copy()
    info = {}
    if missing_flags:
        miss = ~np.isfinite(X)
        med = np.array([np.median(col[np.isfinite(col)]) if np.isfinite(col).any() else 0.0 for col in X[train].T])
        X = np.where(miss, med[None, :], X)
        X = np.concatenate([X, miss.astype(float)], 1)
        info["n_missing"] = int(miss.sum())
    elif not np.isfinite(X).all():
        raise ValueError("NONFINITE_STANDARD_INPUT")
    m, s, n_floor = _zscore_fit(X[train], floor)
    Z = (X - m) / s
    info["n_scale_floor"] = n_floor
    return Z[train], Z[test], info


# ---------------------------------------------------------------------- fixed raw features and staging transform

def raw_bins(x: np.ndarray, bin_samples: int) -> np.ndarray:
    """[n, C, T] epochs -> [n, C * (T // bin)] non-overlapping bin means (trailing remainder dropped and reported)."""
    x = np.asarray(x, dtype=np.float64)
    n, C, T = x.shape
    nb = T // bin_samples
    return x[:, :, :nb * bin_samples].reshape(n, C, nb, bin_samples).mean(-1).reshape(n, C * nb)


def stage_transform(epochs_uv: np.ndarray, record_scale: float) -> np.ndarray:
    """GX staging normalisation, bit-for-bit: float32 epochs / Python-float scale, clip +-60, float16. No baseline."""
    e = np.asarray(epochs_uv, dtype=np.float32)
    return np.clip(e / float(record_scale), -60.0, 60.0).astype(np.float16)


# ---------------------------------------------------------------------- non-aligned windows (spec 5.4)

def block_of_anchor(anchor: int, interval: dict, *, stride: int, original_fs: float, block_seconds: float) -> int:
    original = int(interval["original_start_sample"]) + (int(anchor) - int(interval["start"])) * int(stride)
    return int((original / float(original_fs)) // float(block_seconds))


def candidate_anchors(interval: dict, events: np.ndarray, *, pre: int, post: int, guard: int, exclusion: int) -> np.ndarray:
    """Anchors whose [a - pre, a + post) window stays inside the stored interval with the source guard, and that lie
    MORE than `exclusion` samples from every recorded event of the interval. No wrap-around, no concatenation."""
    lo = int(interval["start"]) + guard + pre
    hi = int(interval["stop"]) - guard - post
    if hi < lo:
        return np.zeros(0, dtype=np.int64)
    a = np.arange(lo, hi + 1, dtype=np.int64)
    ev = np.sort(np.asarray(events, dtype=np.int64))
    if ev.size:
        j = np.searchsorted(ev, a)
        left = np.abs(a - ev[np.clip(j - 1, 0, ev.size - 1)])
        right = np.abs(ev[np.clip(j, 0, ev.size - 1)] - a)
        a = a[np.minimum(left, right) > exclusion]
    return a


def nearest_event_distance(anchors: np.ndarray, events: np.ndarray) -> np.ndarray:
    ev = np.sort(np.asarray(events, dtype=np.int64))
    if ev.size == 0:
        return np.full(len(anchors), np.iinfo(np.int64).max)
    j = np.searchsorted(ev, anchors)
    left = np.abs(anchors - ev[np.clip(j - 1, 0, ev.size - 1)])
    right = np.abs(ev[np.clip(j, 0, ev.size - 1)] - anchors)
    return np.minimum(left, right)


def select_block_windows(candidates: np.ndarray, quota: int, rng: np.random.Generator, qc_ok) -> tuple[list[int], int]:
    """Seeded permutation of the block's candidates; keep the first `quota` that pass QC. Returns (anchors, n_tested)."""
    keep, tested = [], 0
    for a in rng.permutation(candidates):
        if len(keep) >= quota:
            break
        tested += 1
        if qc_ok(int(a)):
            keep.append(int(a))
    return sorted(keep), tested
