"""
gcmi_core.py — reference implementation for synthetic checks (C3 package).

Scope: Gaussian-copula mutual information (GCMI), conditional MI, continuous–discrete MI,
Gaussian MMI partial information decomposition, and surrogate-based bias correction.

This file exists so that the server can verify its production estimator (Ince's gcmi
toolbox) against an independent implementation on synthetic data. It never reads
real EEG. I_ccs (the primary PID measure) is NOT implemented here; see 03_MEASUREMENT_SPEC §3.5.

Units: bits.
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtri, psi

LN2 = np.log(2.0)


def _as2d(x):
    x = np.asarray(x, dtype=float)
    return x[:, None] if x.ndim == 1 else x


def copnorm(x):
    """Rank-based Gaussian copula transform, column-wise. x: (n, d) -> (n, d)."""
    x = _as2d(x)
    n = x.shape[0]
    ranks = np.argsort(np.argsort(x, axis=0, kind="stable"), axis=0) + 1
    return ndtri(ranks / (n + 1.0))


def ent_g(x, biascorrect=True):
    """Entropy (bits) of a Gaussian fitted to x (n, d), with Ince-style bias correction."""
    x = _as2d(x)
    n, d = x.shape
    xc = x - x.mean(axis=0, keepdims=True)
    cov = xc.T @ xc / (n - 1)
    chol = np.linalg.cholesky(cov)
    h = np.sum(np.log(np.diag(chol))) + 0.5 * d * np.log(2 * np.pi * np.e)
    if biascorrect:
        psiterms = psi((n - np.arange(1, d + 1)) / 2.0) / 2.0
        dterm = (LN2 - np.log(n - 1)) / 2.0
        h = h - d * dterm - psiterms.sum()
    return h / LN2


def mi_gg(x, y, biascorrect=True):
    """MI (bits) between Gaussian-assumed x (n, dx) and y (n, dy)."""
    x, y = _as2d(x), _as2d(y)
    return ent_g(x, biascorrect) + ent_g(y, biascorrect) - ent_g(np.hstack([x, y]), biascorrect)


def gcmi_cc(x, y, biascorrect=True):
    """Gaussian-copula MI between continuous x and continuous y."""
    return mi_gg(copnorm(x), copnorm(y), biascorrect)


def cmi_ggg(x, y, z, biascorrect=True):
    """Conditional MI I(x; y | z) for Gaussian-assumed variables."""
    x, y, z = _as2d(x), _as2d(y), _as2d(z)
    hxz = ent_g(np.hstack([x, z]), biascorrect)
    hyz = ent_g(np.hstack([y, z]), biascorrect)
    hxyz = ent_g(np.hstack([x, y, z]), biascorrect)
    hz = ent_g(z, biascorrect)
    return hxz + hyz - hxyz - hz


def gcmi_ccc(x, y, z, biascorrect=True):
    """Gaussian-copula conditional MI I(x; y | z), all continuous."""
    return cmi_ggg(copnorm(x), copnorm(y), copnorm(z), biascorrect)


def collapse_rare(y, min_count=20):
    """Merge discrete categories with fewer than min_count samples into the nearest (by value) frequent category.
    Required because a class-conditional Gaussian needs enough samples per class."""
    y = np.asarray(y).copy()
    vals, counts = np.unique(y, return_counts=True)
    frequent = vals[counts >= min_count]
    if frequent.size == 0:
        return np.zeros_like(y)
    for v, c in zip(vals, counts):
        if c < min_count:
            y[y == v] = frequent[np.argmin(np.abs(frequent - v))]
    return y


def mi_model_gd(x, y, biascorrect=True, min_count=20):
    """MI between continuous x (n, d) and discrete labels y (n,) via class-conditional Gaussians."""
    x = _as2d(x)
    y = collapse_rare(y, min_count)
    classes, counts = np.unique(y, return_counts=True)
    if classes.size < 2:
        return 0.0
    hcond = 0.0
    for c, k in zip(classes, counts):
        hcond += (k / len(y)) * ent_g(x[y == c], biascorrect)
    return ent_g(x, biascorrect) - hcond


def gcmi_model_cd(x, y, biascorrect=True):
    """Gaussian-copula MI between continuous x and discrete y."""
    return mi_model_gd(copnorm(x), y, biascorrect)


def cmi_model_gdd(x, y, z, biascorrect=True):
    """I(x; y | z) with x continuous (Gaussian-assumed), y and z discrete: sum_z p(z) I(x; y | z=z)."""
    x = _as2d(x)
    y, z = np.asarray(y), np.asarray(z)
    out = 0.0
    for zz in np.unique(z):
        m = z == zz
        if m.sum() < 40:
            continue
        out += (m.sum() / len(z)) * mi_model_gd(x[m], y[m], biascorrect)
    return out


def pid_mmi(i_ta, i_tb, i_tab):
    """Two-source PID with the Gaussian/MMI redundancy (Barrett 2015).
    Structural limitation: at most one unique term is non-zero."""
    r = min(i_ta, i_tb)
    return {"U_A": i_ta - r, "U_B": i_tb - r, "R": r, "S": i_tab - i_ta - i_tb + r}


def circular_shift_surrogates(stat_fn, x, y, n_sur=200, min_shift=None, rng=None):
    """Bias-correct stat_fn(x, y) by circularly shifting y relative to x.
    Returns (observed, corrected, surrogate_values)."""
    rng = np.random.default_rng(rng)
    x, y = _as2d(x), _as2d(y)
    n = x.shape[0]
    min_shift = int(min_shift or max(1, n // 10))
    obs = stat_fn(x, y)
    sur = np.empty(n_sur)
    for i in range(n_sur):
        s = rng.integers(min_shift, n - min_shift)
        sur[i] = stat_fn(x, np.roll(y, s, axis=0))
    return obs, obs - sur.mean(), sur


def label_permutation_surrogates(stat_fn, x, labels, n_sur=200, rng=None):
    """Bias-correct stat_fn(x, labels) by permuting labels (class ratio preserved)."""
    rng = np.random.default_rng(rng)
    obs = stat_fn(x, labels)
    sur = np.empty(n_sur)
    for i in range(n_sur):
        sur[i] = stat_fn(x, rng.permutation(labels))
    return obs, obs - sur.mean(), sur


def tmif(stim, eeg, lags, biascorrect=True):
    """Temporal MI function: I(eeg_t; stim_{t-lag}) for each lag (samples; positive = stim leads)."""
    stim, eeg = _as2d(stim), _as2d(eeg)
    n = stim.shape[0]
    out = np.empty(len(lags))
    for i, lag in enumerate(lags):
        if lag >= 0:
            s, e = stim[: n - lag], eeg[lag:]
        else:
            s, e = stim[-lag:], eeg[: n + lag]
        out[i] = gcmi_cc(s, e, biascorrect)
    return out
