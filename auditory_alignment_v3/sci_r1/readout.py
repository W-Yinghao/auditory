"""Numerical core shared by the continuous and private analyses (SCI_R1_PREREG §4, §6, §7).

RelRidge  ridge with an unpenalised intercept and a scale-free penalty alpha = lam * tr(Xc'Xc) / p computed on the rows being
          fitted; lam chosen fit -> es by mean per-dimension Pearson r (the ALN unified-readout criterion) on logspace(-4, 4, 17),
          extended by decades while the optimum sits on a grid edge (down to 1e-8 / up to 1e8), then refitted on fit + es with
          the chosen lam. Same rule for every lag and feature set.
Unified scores, temperature and metrics follow auditory_alignment.evaluate (Readouts.scores 'unified', Readouts.calibrate,
_metrics); the score is computed as one matrix product over (anchor x target-dimension) z-scores, the rank counts strictly
better candidates (ties, of probability zero for continuous scores, favour the own candidate).
Haufe activation patterns for linear maps: A = Sigma_X W (W' Sigma_X W)^+ on the rows the map was fitted on.
"""
from __future__ import annotations

import numpy as np

from auditory_alignment.evaluate import _zt

LN2 = np.log(2.0)
LAM_GRID = np.logspace(-4, 4, 17)
LAM_LIMITS = (1e-8, 1e8)


def _solver(X, Y):
    mx, my = X.mean(0), Y.mean(0)
    Xc = X - mx
    G = Xc.T @ Xc
    s, V = np.linalg.eigh(G)
    VtXY = V.T @ (Xc.T @ (Y - my))
    scale = float(np.trace(G)) / X.shape[1]

    def solve(lam):
        Bm = V @ (VtXY / (np.clip(s, 0, None) + lam * scale)[:, None])
        return np.vstack([Bm, (my - mx @ Bm)[None]])
    return solve, scale


def _corr_err(P, Y):
    Pc, Yc = P - P.mean(0), Y - Y.mean(0)
    return -float(((Pc * Yc).sum(0) / (np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12)).mean())


def apply(B, X):
    return X @ B[:-1] + B[-1]


class RelRidge:
    def __init__(self, X, Y, fit, es, grid=LAM_GRID):
        X = np.asarray(X, np.float64); Y = np.asarray(Y, np.float64)
        if not es.any() or not fit.any():
            raise ValueError("RelRidge needs fit and es rows")
        solve, _ = _solver(X[fit], Y[fit])
        Xe, Ye = X[es], Y[es]
        curve = {}

        def err(lam):
            if lam not in curve:
                curve[lam] = _corr_err(apply(solve(lam), Xe), Ye)
            return curve[lam]
        lams = list(grid)
        for lam in lams:
            err(lam)
        while True:  # extend by decades while the optimum is on an edge of the searched range
            best = min(curve, key=curve.get); lo, hi = min(curve), max(curve)
            if best == lo and lo / 10 >= LAM_LIMITS[0] * (1 - 1e-9):
                err(lo / 10); continue
            if best == hi and hi * 10 <= LAM_LIMITS[1] * (1 + 1e-9):
                err(hi * 10); continue
            break
        self.lam = float(best)
        self.on_edge = bool(best in (min(curve), max(curve)))
        self.curve = {f"{k:.0e}": -v for k, v in sorted(curve.items())}  # mean es r per lam
        both = fit | es
        solve_all, scale = _solver(X[both], Y[both])
        self.B = solve_all(self.lam); self.alpha = self.lam * scale

    def predict(self, X):
        return apply(self.B, np.asarray(X, np.float64))


def cand_matrix(Ac, a_mu, a_sd):
    """Candidate targets [nc, T, D] -> z-scored over anchors, flattened [nc, T * D] (Readouts.scores 'unified')."""
    return _zt((np.asarray(Ac, np.float64) - a_mu) / a_sd).reshape(len(Ac), -1)


def unified_scores(P, Zc):
    """Predicted targets P [nq, T, D] against candidate matrix Zc [nc, T * D] -> [nq, nc] reconstruction correlation."""
    Zp = _zt(np.asarray(P, np.float64)).reshape(len(P), -1)
    return Zp @ Zc.T / Zp.shape[1]


def calibrate_tau(S, own):
    """Readouts.calibrate: scalar temperature on logspace(-3, 2, 41) * std(S) minimising the own-column cross-entropy."""
    best = None
    sd = S.std() + 1e-12
    for tau in np.logspace(-3, 2, 41) * sd:
        z = S / tau; z = z - z.max(1, keepdims=True)
        ce = float((np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), own]).mean())
        if best is None or ce < best[0]:
            best = (ce, tau)
    return float(best[1])


def metrics(s, own, tau):
    so = s[np.arange(len(s)), own]
    rank = (s > so[:, None]).sum(1)
    z = s / tau; z = z - z.max(1, keepdims=True)
    ll = (np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), own]) / LN2
    n = s.shape[1]
    return {"top1": float((rank == 0).mean()), "top5": float((rank < 5).mean()), "mrr": float((1 / (rank + 1)).mean()),
            "rank_pct": float((rank / max(1, n - 1)).mean()), "logloss_bits": float(ll.mean()), "n_candidates": int(n), "n_queries": int(len(s))}


def participant_metrics(S, own, hard, tau, K=8):
    """One participant's queries (physical order): regular, mismatched EEG (previous segment: np.roll of the score rows,
    identical to scoring np.roll(Uq, 1)), hard pool; derived gain_bits, rank_gain, hard_gain_bits (aggregate.unit_rows)."""
    reg = metrics(S, own, tau); mm = metrics(np.roll(S, 1, axis=0), own, tau)
    Sh = np.stack([S[i, [own[i]] + hard[own[i]]] for i in range(len(S))])
    hd = metrics(Sh, np.zeros(len(S), int), tau)
    return {"gain_bits": mm["logloss_bits"] - reg["logloss_bits"], "rank_gain": mm["rank_pct"] - reg["rank_pct"],
            "hard_gain_bits": float(np.log2(1 + K)) - hd["logloss_bits"], "regular_logloss_bits": reg["logloss_bits"],
            "mismatched_logloss_bits": mm["logloss_bits"], "top1": reg["top1"], "rank_pct": reg["rank_pct"], "top5": reg["top5"], "mrr": reg["mrr"],
            "n_queries": reg["n_queries"]}


def cov(X):
    X = np.asarray(X, np.float64)
    Xc = X - X.mean(0)
    return Xc.T @ Xc / max(1, len(X) - 1)


def haufe(Sx, W):
    """Activation patterns of the linear map W [p, D] (or [p]) for inputs with covariance Sx [p, p]."""
    W = np.asarray(W, np.float64)
    if W.ndim == 1:
        return Sx @ W / float(W @ Sx @ W)
    return Sx @ W @ np.linalg.pinv(W.T @ Sx @ W)


def channel_summary(A, C):
    """[C * w (, D)] pattern (feature order channel-major, as patches.flatten(1)) -> per-channel RMS over samples and outputs,
    unit L2 norm across channels."""
    a = np.asarray(A, np.float64).reshape(C, -1)
    r = np.sqrt((a ** 2).mean(1))
    return r / (np.linalg.norm(r) + 1e-30)


def filter_energy(W1, Sch):
    """First-layer linear spatial filter bank W1 [F, C], input channel covariance Sch [C, C]. Returns the activation patterns
    A [C, F] and, per channel, the fraction of its variance explained by the F filter outputs,
    diag(Sch W1' (W1 Sch W1')^+ W1 Sch) / diag(Sch), which is invariant to any invertible remixing of the filters (the next
    layer is linear, so the bank is identified only up to such remixing; methods review S10)."""
    W1 = np.asarray(W1, np.float64)
    A = haufe(Sch, W1.T)
    E = Sch @ W1.T @ np.linalg.pinv(W1 @ Sch @ W1.T) @ W1 @ Sch
    return A, np.diag(E) / np.maximum(np.diag(Sch), 1e-30)
