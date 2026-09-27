"""Statistics for auditory_pf: rank AUC, permutation p, bootstrap, Cliff's delta, penalised models."""
from __future__ import annotations

import warnings

import numpy as np
from scipy import optimize
from scipy.special import expit
from scipy.stats import rankdata, spearmanr


def auc(y, score) -> float:
    """Mann-Whitney AUC with average ranks for ties; nan if one class is missing."""
    y = np.asarray(y).astype(bool)
    score = np.asarray(score, dtype=np.float64)
    m = np.isfinite(score)
    y, score = y[m], score[m]
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(score)
    return float((r[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def perm_p(obs: float, null) -> float:
    null = np.asarray(null, dtype=np.float64)
    null = null[np.isfinite(null)]
    return float((1 + np.sum(null >= obs - 1e-12)) / (1 + len(null)))


def cliff_delta(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    diff = a[:, None] - b[None, :]
    return float((np.sum(diff > 0) - np.sum(diff < 0)) / diff.size)


def spearman(a, b) -> dict:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 5:
        return {"n": int(m.sum()), "rho": None, "p": None}
    r, p = spearmanr(a[m], b[m])
    return {"n": int(m.sum()), "rho": float(r), "p": float(p)}


def query_block_test(y, score, direction: int, n_perm: int, rng: np.random.Generator) -> tuple[float, float]:
    """AUC on query trials and one-sided permutation p in the given direction (+1 / -1)."""
    a = auc(y, score)
    if not np.isfinite(a):
        return a, float("nan")
    stat = direction * (a - 0.5)
    null = np.empty(n_perm)
    yy = np.asarray(y).astype(bool)
    r = rankdata(np.asarray(score, float))
    n1, n0 = int(yy.sum()), int((~yy).sum())
    for i in range(n_perm):
        yp = rng.permutation(yy)
        null[i] = direction * ((r[yp].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0) - 0.5)
    return a, float((1 + np.sum(null >= stat - 1e-12)) / (1 + n_perm))


def two_sided_perm(y, score, n_perm: int, rng: np.random.Generator) -> tuple[float, float]:
    a = auc(y, score)
    if not np.isfinite(a):
        return a, float("nan")
    yy = np.asarray(y).astype(bool)
    r = rankdata(np.asarray(score, float))
    n1, n0 = int(yy.sum()), int((~yy).sum())
    null = np.empty(n_perm)
    for i in range(n_perm):
        yp = rng.permutation(yy)
        null[i] = abs((r[yp].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0) - 0.5)
    return a, float((1 + np.sum(null >= abs(a - 0.5) - 1e-12)) / (1 + n_perm))


# ----------------------------------------------------------------------------- penalised models

class Standardizer:
    def fit(self, X):
        X = np.asarray(X, float)
        self.mu = np.nanmean(X, 0)
        self.sd = np.nanstd(X, 0)
        self.sd[~np.isfinite(self.sd) | (self.sd < 1e-12)] = 1.0
        self.mu[~np.isfinite(self.mu)] = 0.0
        return self

    def transform(self, X):
        Z = (np.asarray(X, float) - self.mu) / self.sd
        return np.nan_to_num(Z, nan=0.0)


def logistic_fit(X, y, C: float, balanced: bool = True):
    from sklearn.linear_model import LogisticRegression
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = LogisticRegression(C=C, class_weight="balanced" if balanced else None, max_iter=5000, solver="lbfgs")
        m.fit(X, y)
    return m


def _inner_splits(y_strat, n_splits: int, seed: int):
    from sklearn.model_selection import StratifiedKFold
    y_strat = np.asarray(y_strat)
    counts = np.bincount(y_strat.astype(int)) if len(y_strat) else np.array([0])
    k = int(min(n_splits, counts[counts > 0].min())) if len(counts[counts > 0]) > 1 else 0
    if k < 2:
        return []
    return list(StratifiedKFold(k, shuffle=True, random_state=seed).split(np.zeros(len(y_strat)), y_strat))


def logistic_cv(X, y, grid, seed: int = 0, n_splits: int = 5):
    """Standardise in-fold, choose C by inner stratified CV AUC, refit on all training rows."""
    X, y = np.asarray(X, float), np.asarray(y).astype(int)
    splits = _inner_splits(y, n_splits, seed)
    best_c, best = grid[len(grid) // 2], -np.inf
    if splits:
        for C in grid:
            scores = []
            for tr, va in splits:
                st = Standardizer().fit(X[tr])
                m = logistic_fit(st.transform(X[tr]), y[tr], C)
                scores.append(auc(y[va], m.decision_function(st.transform(X[va]))))
            s = np.nanmean(scores)
            if s > best + 1e-12:
                best, best_c = s, C
    st = Standardizer().fit(X)
    m = logistic_fit(st.transform(X), y, best_c)
    return lambda Z: m.decision_function(st.transform(Z)), {"C": best_c, "inner_auc": best}


def ridge_cv(X, y, grid, seed: int = 0, n_splits: int = 5):
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import KFold
    X, y = np.asarray(X, float), np.asarray(y, float)
    best_a, best = grid[len(grid) // 2], np.inf
    splits = list(KFold(min(n_splits, len(y)), shuffle=True, random_state=seed).split(X))
    for a in grid:
        err = []
        for tr, va in splits:
            st = Standardizer().fit(X[tr])
            m = Ridge(alpha=a).fit(st.transform(X[tr]), y[tr])
            err.append(np.mean(np.abs(m.predict(st.transform(X[va])) - y[va])))
        if np.mean(err) < best - 1e-12:
            best, best_a = float(np.mean(err)), a
    st = Standardizer().fit(X)
    m = Ridge(alpha=best_a).fit(st.transform(X), y)
    return lambda Z: m.predict(st.transform(Z)), {"alpha": best_a, "inner_mae": best}


class OrdinalLogistic:
    """Proportional-odds cumulative logit: P(Y <= j) = sigmoid(theta_j - x.beta), L2 on beta only.

    Levels are the integers 1..L; thresholds are parametrised by a first value and positive gaps
    (softplus) so they stay ordered. Unobserved levels are handled by the ordering constraint.
    """

    def __init__(self, lam: float, levels: int = 5):
        self.lam, self.L = float(lam), int(levels)

    def _unpack(self, w, p):
        beta = w[:p]
        first = w[p]
        gaps = np.logaddexp(0.0, w[p + 1:]) + 1e-4
        theta = np.concatenate([[first], first + np.cumsum(gaps)])
        return beta, theta

    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y).astype(int) - 1                 # 0..L-1
        n, p = X.shape
        L = self.L

        def f(w):
            beta, theta = self._unpack(w, p)
            eta = X @ beta
            th = np.concatenate([[-np.inf], theta, [np.inf]])
            up = expit(th[y + 1] - eta)
            lo = expit(th[y] - eta)
            prob = np.clip(up - lo, 1e-12, None)
            nll = -np.log(prob).sum() + self.lam * beta @ beta
            # gradients
            dup = up * (1 - up)
            dlo = lo * (1 - lo)
            g_eta = (dup - dlo) / prob                     # d(-log prob)/d eta = (dup - dlo)/prob
            g_beta = X.T @ g_eta + 2 * self.lam * beta
            g_theta = np.zeros(L - 1)
            for j in range(L - 1):
                g_theta[j] = -np.sum(dup[y == j] / prob[y == j]) + np.sum(dlo[y == j + 1] / prob[y == j + 1])
            # chain rule to (first, raw gaps)
            g_first = g_theta.sum()
            raw = w[p + 1:]
            sig = expit(raw)
            g_raw = np.array([g_theta[j + 1:].sum() * sig[j] for j in range(L - 2)])
            return nll, np.concatenate([g_beta, [g_first], g_raw])

        counts = np.bincount(y, minlength=L).astype(float) + 0.5
        cum = np.cumsum(counts)[:-1] / counts.sum()
        th0 = np.log(cum / (1 - cum))
        w0 = np.concatenate([np.zeros(p), [th0[0]], np.log(np.expm1(np.maximum(np.diff(th0), 1e-3)))])
        res = optimize.minimize(f, w0, jac=True, method="L-BFGS-B", options={"maxiter": 2000})
        self.beta, self.theta = self._unpack(res.x, p)
        self.converged = bool(res.success)
        return self

    def latent(self, X):
        return np.asarray(X, float) @ self.beta

    def proba(self, X):
        eta = self.latent(X)
        th = np.concatenate([[-np.inf], self.theta, [np.inf]])
        cdf = expit(th[None, :] - eta[:, None])
        return np.diff(cdf, axis=1)

    def expected(self, X):
        return self.proba(X) @ np.arange(1, self.L + 1)


def ordinal_cv(X, y, grid, seed: int = 0, n_splits: int = 5, levels: int = 5):
    """Standardise in-fold, choose lambda by inner CV MAE of E[Y], refit; returns (latent_fn, expected_fn)."""
    from sklearn.model_selection import KFold
    X, y = np.asarray(X, float), np.asarray(y).astype(int)
    splits = list(KFold(min(n_splits, len(y)), shuffle=True, random_state=seed).split(X))
    best_l, best = grid[len(grid) // 2], np.inf
    if len(grid) > 1:
        for lam in grid:
            err = []
            for tr, va in splits:
                st = Standardizer().fit(X[tr])
                m = OrdinalLogistic(lam, levels).fit(st.transform(X[tr]), y[tr])
                err.append(np.mean(np.abs(m.expected(st.transform(X[va])) - y[va])))
            if np.mean(err) < best - 1e-12:
                best, best_l = float(np.mean(err)), lam
    st = Standardizer().fit(X)
    m = OrdinalLogistic(best_l, levels).fit(st.transform(X), y)
    return (lambda Z: m.latent(st.transform(Z))), (lambda Z: m.expected(st.transform(Z))), {"lambda": best_l, "inner_mae": best,
                                                                                          "converged": m.converged}


def spline_basis(train_values, n_knots: int = 5, degree: int = 3):
    """B-spline basis fitted on training values (3 interior knots at quantiles when n_knots=5)."""
    from sklearn.preprocessing import SplineTransformer
    st = SplineTransformer(n_knots=n_knots, degree=degree, knots="quantile", include_bias=False, extrapolation="linear")
    st.fit(np.asarray(train_values, float).reshape(-1, 1))
    return lambda v: st.transform(np.asarray(v, float).reshape(-1, 1))
