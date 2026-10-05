"""Lagged Gaussian-copula information engine for continuous speech (03 §3.2-3.6 as amended by
docs/auditory_c3/MEASUREMENT_AMENDMENT_001.md §1, §7).

A subject is a list of trials. Each trial has a response T (d_T x n, e.g. ROI principal components), a valid range
[a, b) of response samples (guards excluded; guards exceed the largest |lag|), and stimulus-side variables (d x n) on the
same time base (sample k = k/fs after stimulus onset). Every variable is copula-normalised once per subject (response
over valid samples, stimulus over all samples). Circular cross-correlations computed once per trial by FFT then give
every lagged covariance, for the observed alignment and for every circular-shift surrogate (stimulus delayed by s
within the trial, s >= 5 s, never across trials), by index lookup:
    sum_{t valid} T(t) X(t - tau - s)  =  c_TX[(tau + s) mod n].
Covariances among stimulus-side variables are invariant to the shift; they are taken from the full trial and rescaled
to the valid sample count (edge approximation, checked against direct estimation in tests/auditory_c3/test_engine.py).
Information values use the Gaussian entropy with Ince's bias correction (bits), exactly as gcmi_core.ent_g.
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtri, psi

LN2 = np.log(2.0)


def copnorm_rows(X, mask=None, return_ties=False):
    """Rank-to-normal transform of each row of X (d, n) over the samples selected by mask (others set to 0).
    Ties receive their average rank (C3 addendum item 2: never break ties by sample order, which would inject a
    sample-index signal). A constant row raises ValueError (its information is undefined, never silently 0).
    return_ties: also return the per-row fraction of samples that share their value with another sample."""
    from scipy.stats import rankdata
    X = np.atleast_2d(np.asarray(X, float))
    out = np.zeros_like(X)
    idx = np.arange(X.shape[1]) if mask is None else np.flatnonzero(mask)
    ties = []
    for i in range(X.shape[0]):
        x = X[i, idx]
        if np.all(x == x[0]):
            raise ValueError(f"CONSTANT_VARIABLE row {i}: copula transform undefined")
        r = rankdata(x, method="average")
        out[i, idx] = ndtri(r / (len(x) + 1.0))
        _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
        ties.append(float(np.mean(cnt[inv] > 1)))
    return (out, ties) if return_ties else out


def _bias(d, n):
    return d * (LN2 - np.log(n - 1)) / 2.0 + psi((n - np.arange(1, d + 1)) / 2.0).sum() / 2.0


def ent_from_cov(C, n):
    """Bias-corrected Gaussian entropy (bits) for batched covariance C (..., d, d) estimated from n samples.
    Matches gcmi_core.ent_g: C is the (n-1)-normalised covariance."""
    d = C.shape[-1]
    L = np.linalg.cholesky(C)
    h = np.sum(np.log(np.diagonal(L, axis1=-2, axis2=-1)), axis=-1) + 0.5 * d * np.log(2 * np.pi * np.e)
    return (h - _bias(d, n)) / LN2


class Subject:
    """Sufficient statistics for one subject (one response definition, one trial set)."""

    def __init__(self, trials, fs, lags, n_sur=200, min_shift_s=5.0, seed=0):
        """trials: list of dicts {"T": (dT, n), "valid": (a, b), "stim": {name: (d, n)}} (stim may lack names that are
        absent in a trial, e.g. the ignored stream of a single-speaker trial: then it is treated as zeros)."""
        self.fs, self.lags, self.n_sur = fs, np.asarray(lags), n_sur
        rng = np.random.default_rng(seed)
        self.names = sorted({k for t in trials for k in t["stim"]})
        self.dims = {k: next(t["stim"][k].shape[0] for t in trials if k in t["stim"]) for k in self.names}
        self.dT = trials[0]["T"].shape[0]
        # pooled copula normalisation
        Tcat = np.concatenate([t["T"] for t in trials], axis=1)
        mcat = np.concatenate([np.isin(np.arange(t["T"].shape[1]), np.arange(*t["valid"])) for t in trials])
        Tn, tT = copnorm_rows(Tcat, mcat, return_ties=True)
        self.tie_fraction = {"T": max(tT)}
        Sn = {}
        for k in self.names:
            Scat = np.concatenate([t["stim"].get(k, np.zeros((self.dims[k], t["T"].shape[1]))) for t in trials], axis=1)
            present = np.concatenate([np.full(t["T"].shape[1], k in t["stim"]) for t in trials])
            Sn[k], tk = copnorm_rows(Scat, present, return_ties=True)  # absent stream stays 0 (no information, no variance)
            self.tie_fraction[k] = max(tk)
        self.trials = []
        pos = 0
        for t in trials:
            n = t["T"].shape[1]; a, b = t["valid"]
            m = np.zeros(n); m[a:b] = 1.0
            T = Tn[:, pos:pos + n] * m
            S = {k: Sn[k][:, pos:pos + n] for k in self.names}
            shifts = rng.integers(int(min_shift_s * fs), n - int(min_shift_s * fs), size=n_sur)
            self.trials.append({"n": n, "nv": b - a, "m": m, "T": T, "S": S, "shifts": np.r_[0, shifts],
                                "FT": np.fft.rfft(T, axis=1), "FS": {k: np.fft.rfft(S[k], axis=1) for k in self.names}})
            pos += n
        self.N = sum(t["nv"] for t in self.trials)
        self._cache = {}

    # ---------------------------------------------------------------- pooled sums (n_sur+1, n_lags, ...)
    def _resp_stim(self, k):
        """sum_valid T(t) X(t - tau - s): array (n_sur+1, n_lags, dT, dX)."""
        key = ("TS", k)
        if key not in self._cache:
            acc = 0.0
            for tr in self.trials:
                c = np.fft.irfft(tr["FT"][:, None, :] * np.conj(tr["FS"][k][None, :, :]), n=tr["n"], axis=-1)
                idx = (self.lags[None, :] + tr["shifts"][:, None]) % tr["n"]
                acc = acc + np.moveaxis(c[:, :, idx], (0, 1), (2, 3))
            self._cache[key] = acc
        return self._cache[key]

    def _resp_resp(self):
        if "TT" not in self._cache:
            self._cache["TT"] = sum(tr["T"] @ tr["T"].T for tr in self.trials)
        return self._cache["TT"]

    def _stim_stim(self, k1, k2):
        """Exact same-lag stimulus covariance sum over the shifted valid window, mean-corrected:
        sum_{t valid} (X(t-tau-s) - mu_X)(Y(t-tau-s) - mu_Y)^T, via circular prefix sums; (n_sur+1, n_lags, d1, d2)."""
        key = ("SS", k1, k2)
        if key not in self._cache:
            nS, nL = self.n_sur + 1, len(self.lags)
            d1, d2 = self.dims[k1], self.dims[k2]
            Sxy = np.zeros((nS, nL, d1, d2)); Sx = np.zeros((nS, nL, d1)); Sy = np.zeros((nS, nL, d2))
            for tr in self.trials:
                n, nv = tr["n"], tr["nv"]
                X, Y = tr["S"][k1], tr["S"][k2]
                Pxy = np.concatenate([np.zeros((1, d1, d2)), np.cumsum(np.einsum("in,jn->nij", X, Y), axis=0)])
                Px = np.concatenate([np.zeros((1, d1)), np.cumsum(X.T, axis=0)])
                Py = np.concatenate([np.zeros((1, d2)), np.cumsum(Y.T, axis=0)])
                a = int(np.flatnonzero(tr["m"])[0])
                lo = (a - self.lags[None, :] - tr["shifts"][:, None]) % n
                hi = lo + nv
                wrap = hi > n
                hi_w = np.where(wrap, hi - n, hi)
                for P, acc in ((Pxy, Sxy), (Px, Sx), (Py, Sy)):
                    acc += np.where(wrap[..., *([None] * (P.ndim - 1))], (P[n] - P[lo]) + P[hi_w], P[hi_w] - P[lo])
            self._cache[key] = Sxy - Sx[..., :, None] * Sy[..., None, :] / self.N
        return self._cache[key]

    # ---------------------------------------------------------------- mediated variables (lag 0, response-aligned)
    def add_mediator(self, name, Y):
        """Register a response-aligned stimulus-derived variable (e.g. a cross-validated ridge prediction), list of
        (d, n) arrays per trial; it is copula-normalised over valid samples and shifted with the stimulus."""
        Ycat = np.concatenate(Y, axis=1)
        mcat = np.concatenate([tr["m"] > 0 for tr in self.trials])
        Yn, ty = copnorm_rows(Ycat, mcat, return_ties=True)
        self.tie_fraction[f"M:{name}"] = max(ty)
        pos = 0
        for tr in self.trials:
            n = tr["n"]
            tr.setdefault("M", {})[name] = Yn[:, pos:pos + n]
            tr.setdefault("FM", {})[name] = np.fft.rfft(Yn[:, pos:pos + n] * tr["m"], axis=1)
            tr.setdefault("FMraw", {})[name] = np.fft.rfft(Yn[:, pos:pos + n], axis=1)
            pos += n

    def _resp_med(self, mname):
        """sum_valid T(t) M(t - s): (n_sur+1, dT, dM)."""
        key = ("TM", mname)
        if key not in self._cache:
            acc = 0.0
            for tr in self.trials:
                c = np.fft.irfft(tr["FT"][:, None, :] * np.conj(tr["FMraw"][mname][None, :, :]), n=tr["n"], axis=-1)
                acc = acc + np.moveaxis(c[:, :, tr["shifts"] % tr["n"]], 2, 0)
            self._cache[key] = acc
        return self._cache[key]

    def _med_med(self, m1, m2):
        key = ("MM", m1, m2)
        if key not in self._cache:
            self._cache[key] = sum((tr["M"][m1] * tr["m"]) @ tr["M"][m2].T for tr in self.trials)
        return self._cache[key]

    def _med_stim(self, mname, k):
        """sum_valid M(t) X(t - tau) (shift-invariant): (n_lags, dM, dX)."""
        key = ("MS", mname, k)
        if key not in self._cache:
            acc = 0.0
            for tr in self.trials:
                c = np.fft.irfft(tr["FM"][mname][:, None, :] * np.conj(tr["FS"][k][None, :, :]), n=tr["n"], axis=-1)
                acc = acc + np.moveaxis(c[:, :, self.lags % tr["n"]], 2, 0)
            self._cache[key] = acc
        return self._cache[key]

    # ---------------------------------------------------------------- information quantities
    def _assemble(self, stims, meds):
        """Covariance (n_sur+1, n_lags, D, D) of [T, stims at lag tau, meds at lag 0]; (n-1)-normalised."""
        nS, nL = self.n_sur + 1, len(self.lags)
        blocks = [("T", self.dT)] + [("S:" + k, self.dims[k]) for k in stims] + [("M:" + m, self._mdim(m)) for m in meds]
        off = np.cumsum([0] + [d for _, d in blocks]); D = off[-1]
        C = np.zeros((nS, nL, D, D))
        C[..., :self.dT, :self.dT] = self._resp_resp()
        for i, (bi, di) in enumerate(blocks):
            for j, (bj, dj) in enumerate(blocks):
                if j < i:
                    continue
                si, sj = slice(off[i], off[i + 1]), slice(off[j], off[j + 1])
                if bi == "T" and bj == "T":
                    continue
                if bi == "T" and bj.startswith("S:"):
                    blk = self._resp_stim(bj[2:])
                elif bi == "T" and bj.startswith("M:"):
                    blk = self._resp_med(bj[2:])[:, None]
                elif bi.startswith("S:") and bj.startswith("S:"):
                    blk = self._stim_stim(bi[2:], bj[2:])
                elif bi.startswith("S:") and bj.startswith("M:"):
                    blk = np.swapaxes(self._med_stim(bj[2:], bi[2:]), -1, -2)[None]
                else:  # M, M
                    blk = self._med_med(bi[2:], bj[2:])
                C[..., si, sj] = blk
                if i != j:
                    C[..., sj, si] = np.swapaxes(np.broadcast_to(blk, C[..., si, sj].shape), -1, -2)
        return C / (self.N - 1), off, blocks

    def _mdim(self, m):
        return self.trials[0]["M"][m].shape[0]

    def _H(self, C, off, sel):
        idx = np.concatenate([np.arange(off[i], off[i + 1]) for i in sel])
        return ent_from_cov(C[..., idx[:, None], idx[None, :]], self.N)

    def mi(self, stim, meds=()):
        """I(T; stim_tau) [stim may be a tuple of names, taken jointly]; returns (n_sur+1, n_lags) in bits."""
        stims = (stim,) if isinstance(stim, str) else tuple(stim)
        C, off, blocks = self._assemble(stims, ())
        s = list(range(1, len(blocks)))
        return self._H(C, off, [0]) + self._H(C, off, s) - self._H(C, off, [0] + s)

    def cmi(self, stim, cond_meds=(), cond_stims=()):
        """I(T; stim_tau | cond_stims_tau, cond_meds_0); returns (n_sur+1, n_lags)."""
        stims = (stim,) + tuple(cond_stims)
        C, off, blocks = self._assemble(stims, tuple(cond_meds))
        x = [1]; z = list(range(2, len(blocks)))
        return (self._H(C, off, [0] + z) + self._H(C, off, x + z) - self._H(C, off, [0] + x + z) - self._H(C, off, z))

    def med_cov(self, meds):
        """Covariance (n_sur+1, D, D) of [meds..., T] without lags (for mediated PID / CMI)."""
        nS = self.n_sur + 1
        dims = [self._mdim(m) for m in meds] + [self.dT]
        off = np.cumsum([0] + dims); D = off[-1]
        C = np.zeros((nS, D, D))
        for i, mi_ in enumerate(meds):
            for j, mj in enumerate(meds):
                C[:, off[i]:off[i + 1], off[j]:off[j + 1]] = self._med_med(mi_, mj)
            tm = self._resp_med(mi_)  # (nS, dT, dM)
            C[:, off[-2]:, off[i]:off[i + 1]] = tm
            C[:, off[i]:off[i + 1], off[-2]:] = np.swapaxes(tm, -1, -2)
        C[:, off[-2]:, off[-2]:] = self._resp_resp()
        return C / (self.N - 1), off


def ridge_loto(Xs, Ys, lags, alphas):
    """Leave-one-trial-out ridge prediction of Ys[i] (dY, n) from lagged Xs[i] (dX, n) with lags (samples, stimulus
    leading positive). alpha chosen by LOTO mean correlation on all trials (it only shapes a conditioning variable),
    predictions for trial i always from weights fitted without trial i. Returns (predictions list, chosen alpha, r)."""
    def lagged(X):
        d, n = X.shape
        Z = np.zeros((n, d * len(lags)))
        for j, L in enumerate(lags):
            if L >= 0:
                Z[L:, j * d:(j + 1) * d] = X[:, :n - L].T
            else:
                Z[:L, j * d:(j + 1) * d] = X[:, -L:].T
        return Z
    # two passes keep only one lagged design matrix in memory at a time
    XtX, XtY = [], []
    for X, Y in zip(Xs, Ys):
        Z = lagged(X); XtX.append(Z.T @ Z); XtY.append(Z.T @ Y.T); del Z
    A, B = sum(XtX), sum(XtY)
    scale = np.trace(A) / A.shape[0]
    preds = {a: [] for a in alphas}
    for i in range(len(Xs)):
        w_, V = np.linalg.eigh(A - XtX[i])
        Bi = V.T @ (B - XtY[i])
        Zi = lagged(Xs[i])
        ZV = Zi @ V
        for a in alphas:
            preds[a].append((ZV @ (Bi / (w_ + a * scale)[:, None])).T)
        del Zi, ZV
    def score(P):
        return np.mean([np.mean([np.corrcoef(p[k], y[k])[0, 1] for k in range(y.shape[0])]) for p, y in zip(P, Ys)])
    scores = {a: score(preds[a]) for a in alphas}
    best = max(scores, key=scores.get)
    return preds[best], best, scores[best]
