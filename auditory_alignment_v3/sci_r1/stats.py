"""Identity-level inference (SCI_R1_PREREG §8). Rows are independent identities; whole curves / matrices are resampled jointly;
groups are resampled separately (independent-group contrasts); intervals condition on the fitted models.

Bootstrap-t with per-replicate studentisation (methods review B1: a fixed-SE max-t under-covers at n = 9-22):
  se_hat = sd(Y) / sqrt(n); per replicate se* = sd(Y*) / sqrt(n) (floor 1e-3 se_hat); T* = |m* - m_hat| / se*
  pointwise / scalar interval  m_hat +- q95(T*) se_hat            (symmetric bootstrap-t)
  curve / matrix band          m_hat +- q95(max over cells of T*) se_hat
  independent groups           se = sqrt(se_a^2 + se_b^2), replicates resample each group separately
  OLS                          per replicate classical coefficient SE
  family                       max over members of T*_b (members share replicate b of each group) -> simultaneous intervals
Percentile intervals are kept as a secondary column. Non-finite inputs raise (missing identities are listed upstream).
"""
from __future__ import annotations

import numpy as np

NB = 4000
SEED = 20261011


def _check(Y):
    Y = np.asarray(Y, np.float64)
    if not np.isfinite(Y).all():
        raise ValueError("non-finite values reached the bootstrap; list and exclude them upstream with a reason")
    return Y


def draws(n, B=NB, seed=SEED):
    return np.random.default_rng(seed).integers(0, n, (B, n))


def group_seed(*parts):
    """deterministic per-group seed (same group -> same replicate indices across a family)."""
    return SEED + sum((i + 1) * ord(c) for i, c in enumerate("|".join(map(str, parts)))) % 100000


def boot_mean_se(Y, idx, chunk=100):
    n = Y.shape[0]
    M = np.empty((len(idx),) + Y.shape[1:]); SE = np.empty_like(M)
    for a in range(0, len(idx), chunk):
        Yb = Y[idx[a:a + chunk]]
        M[a:a + chunk] = Yb.mean(1); SE[a:a + chunk] = Yb.std(1, ddof=1) / np.sqrt(n)
    return M, SE


def _bt(est, se, M, SE, multi):
    floor = 1e-3 * np.where(se > 0, se, 1.0)
    T = np.abs(M - est) / np.maximum(SE, floor)
    cp = np.nanpercentile(T, 95, axis=0)
    out = {"est": est, "se": se, "ci_low": est - cp * se, "ci_high": est + cp * se,
           "pct_low": np.nanpercentile(M, 2.5, axis=0), "pct_high": np.nanpercentile(M, 97.5, axis=0), "T": T}
    if multi:
        c = float(np.nanpercentile(np.nanmax(T.reshape(len(M), -1), 1), 95))
        out.update({"band_low": est - c * se, "band_high": est + c * se, "crit": c})
    return out


def summary(Y, B=NB, seed=SEED, idx=None):
    Y = _check(Y)
    n = len(Y)
    if n < 3:
        return {"n": n, "note": "fewer than 3 identities"}
    idx = draws(n, B, seed) if idx is None else idx
    M, SE = boot_mean_se(Y, idx)
    out = _bt(Y.mean(0), Y.std(0, ddof=1) / np.sqrt(n), M, SE, Y.ndim >= 2)
    out["n"] = int(n)
    return out


def contrast(Ya, Yb, B=NB, seed=SEED, idx_a=None, idx_b=None):
    Ya, Yb = _check(Ya), _check(Yb)
    na, nb = len(Ya), len(Yb)
    if na < 3 or nb < 3:
        return {"n_a": na, "n_b": nb, "note": "fewer than 3 identities in a group"}
    ia = draws(na, B, seed) if idx_a is None else idx_a
    ib = draws(nb, B, seed + 1) if idx_b is None else idx_b
    Ma, SEa = boot_mean_se(Ya, ia); Mb, SEb = boot_mean_se(Yb, ib)
    se = np.sqrt(Ya.var(0, ddof=1) / na + Yb.var(0, ddof=1) / nb)
    out = _bt(Ya.mean(0) - Yb.mean(0), se, Ma - Mb, np.sqrt(SEa ** 2 + SEb ** 2), Ya.ndim >= 2)
    out["n_a"], out["n_b"] = int(na), int(nb)
    return out


def _ols_fit(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta; dof = len(y) - X.shape[1]
    if dof <= 0:
        return beta, np.full(X.shape[1], np.nan)
    s2 = float(r @ r) / dof
    cov = s2 * np.linalg.pinv(X.T @ X)
    return beta, np.sqrt(np.clip(np.diag(cov), 0, None))


def ols(X, y, names, B=NB, seed=SEED):
    X = _check(np.c_[np.ones(len(X)), np.asarray(X, np.float64).reshape(len(X), -1)]); y = _check(y)
    if len(y) < X.shape[1] + 3:
        return {"n": int(len(y)), "note": "too few identities for this model"}
    est, se = _ols_fit(X, y)
    idx = draws(len(y), B, seed)
    bs = np.full((B, X.shape[1]), np.nan); ses = np.full_like(bs, np.nan)
    for b, i in enumerate(idx):
        if np.linalg.matrix_rank(X[i]) == X.shape[1]:
            bs[b], ses[b] = _ols_fit(X[i], y[i])
    r = _bt(est, se, bs, ses, False)
    nm = ["intercept"] + list(names)
    return {"n": int(len(y)), "df_resid": int(len(y) - X.shape[1]), "n_valid_replicates": int(np.isfinite(bs[:, 0]).sum()),
            "coef": {k: {"est": float(r["est"][j]), "se": float(r["se"][j]), "ci_low": float(r["ci_low"][j]), "ci_high": float(r["ci_high"][j]),
                         "pct_low": float(r["pct_low"][j]), "pct_high": float(r["pct_high"][j])} for j, k in enumerate(nm)},
            "T": {k: r["T"][:, j] for j, k in enumerate(nm)}}


def family_maxt(items):
    """items: {name: (est, se, T_b [B])} whose replicate b shares the group resamples -> simultaneous 95% intervals."""
    names = list(items)
    if not names:
        return None
    T = np.stack([np.asarray(items[k][2], float) for k in names], 1)
    c = float(np.nanpercentile(np.nanmax(T, 1), 95))
    return {"crit": c, "n_members": len(names),
            "intervals": {k: {"est": float(items[k][0]), "sim_low": float(items[k][0] - c * items[k][1]), "sim_high": float(items[k][0] + c * items[k][1])}
                          for k in names}}
