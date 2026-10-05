"""Two-source Gaussian PID with Ince's I_ccs redundancy (Ince 2017, Entropy 19:318), ported from
robince/partial-info-decomp Iccs_mvn_P2.m / calc_pi_mvn.m (commit 32207164741b9e3ba86cec225c09b4b617681e93).

The upstream Python port (pid_mvn.py) indexes covariance blocks with numpy fancy indexing (Cfull[idx, idx]), which
returns diagonal elements instead of blocks whenever a variable has more than one dimension; this port uses np.ix_
throughout. Redundancy is the Monte Carlo mean of the local co-information over samples of the full Gaussian, keeping
only samples where the local co-information and the three local changes in surprisal share one sign (pairwise-marginal
maximum-entropy, "P2", which for Gaussians is the full joint). Units: bits.

C3 use (03 §3.5): the covariance is that of the copula-normalised (A, B, T) — the same Gaussian model GCMI uses.
The estimate carries Monte Carlo error; pass a fixed rng.
"""
from __future__ import annotations

import numpy as np

LN2 = np.log(2.0)


def _logmvnpdf_centred(xc, C):
    """log N(xc; 0, C) for rows of xc (n, d)."""
    L = np.linalg.cholesky(C)
    z = np.linalg.solve(L, xc.T)
    d = C.shape[0]
    return -0.5 * np.sum(z**2, axis=0) - np.sum(np.log(np.diag(L))) - 0.5 * d * np.log(2 * np.pi)


def _gauss_mi_bits(C, ia, ib):
    def ld(idx):
        return np.linalg.slogdet(C[np.ix_(idx, idx)])[1]
    return 0.5 * (ld(ia) + ld(ib) - ld(np.r_[ia, ib])) / LN2


def iccs_redundancy(C, n1, n2, ns, n_mc=100_000, rng=None, return_samples=False, samples=None):
    """I_ccs({1}{2}) for Gaussian (X1 [n1], X2 [n2], S [ns]) with joint covariance C (order X1, X2, S).
    `samples` (n, n1+n2+ns) overrides the Monte Carlo draw (used to compare implementations on identical samples)."""
    C = np.asarray(C, float)
    assert C.shape == (n1 + n2 + ns,) * 2
    i1, i2, is_ = np.arange(n1), np.arange(n1, n1 + n2), np.arange(n1 + n2, n1 + n2 + ns)
    i12 = np.r_[i1, i2]
    Cs = C[np.ix_(is_, is_)]
    Csi = np.linalg.pinv(Cs)

    def cond(ix):
        Cx = C[np.ix_(ix, ix)]
        M = C[np.ix_(ix, is_)] @ Csi
        return Cx, M, Cx - M @ C[np.ix_(is_, ix)]

    if samples is None:
        rng = np.random.default_rng(rng)
        x = rng.multivariate_normal(np.zeros(C.shape[0]), C, size=n_mc, method="cholesky")
    else:
        x = np.asarray(samples, float)
    s = x[:, is_]
    out = {}
    for name, ix in (("1", i1), ("2", i2), ("12", i12)):
        Cx, M, Cc = cond(ix)
        out[name] = _logmvnpdf_centred(x[:, ix] - s @ M.T, Cc) - _logmvnpdf_centred(x[:, ix], Cx)
    dh1, dh2, dh12 = out["1"], out["2"], out["12"]
    lnii = dh1 + dh2 - dh12
    sg = np.sign(dh1)
    keep = (sg == np.sign(lnii)) & (sg == np.sign(dh2)) & (sg == np.sign(dh12))
    lnii = np.where(keep, lnii, 0.0)
    r = float(np.nanmean(lnii) / LN2)
    return (r, lnii / LN2) if return_samples else r


def pid_ccs(C, n1, n2, ns, n_mc=100_000, rng=None):
    """Full two-source lattice (R, U1, U2, S) under I_ccs, plus the Gaussian MIs used (bits)."""
    i1, i2, is_ = np.arange(n1), np.arange(n1, n1 + n2), np.arange(n1 + n2, n1 + n2 + ns)
    i_s1 = _gauss_mi_bits(C, i1, is_); i_s2 = _gauss_mi_bits(C, i2, is_); i_s12 = _gauss_mi_bits(C, np.r_[i1, i2], is_)
    r = iccs_redundancy(C, n1, n2, ns, n_mc=n_mc, rng=rng)
    u1, u2 = i_s1 - r, i_s2 - r
    return {"R": r, "U1": u1, "U2": u2, "S": i_s12 - u1 - u2 - r, "I_S_X1": i_s1, "I_S_X2": i_s2, "I_S_X1X2": i_s12}


def pid_mmi(C, n1, n2, ns):
    """Barrett (2015) Gaussian MMI decomposition on the same covariance (bits)."""
    i1, i2, is_ = np.arange(n1), np.arange(n1, n1 + n2), np.arange(n1 + n2, n1 + n2 + ns)
    a, b, ab = _gauss_mi_bits(C, i1, is_), _gauss_mi_bits(C, i2, is_), _gauss_mi_bits(C, np.r_[i1, i2], is_)
    r = min(a, b)
    return {"R": r, "U1": a - r, "U2": b - r, "S": ab - a - b + r, "I_S_X1": a, "I_S_X2": b, "I_S_X1X2": ab}
