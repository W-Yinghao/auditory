"""P2 clinical heads (03_METHOD_SPEC section 7; 02_SERVER_EXECUTION section 6).

SIR: regularised five-level proportional-odds model P(Y <= k | x) = sigmoid(t_k - x'w), k = 1..4, t_1 free and
t_{k+1} = t_k + softplus(r_k) + 1e-4, objective  mean NLL + (lam/2)||w||^2 + (0.001/2) sum_k (t_k - logit(k/5))^2,
FP64 stable log-differences, analytic gradient, L-BFGS-B (max 400 iterations, gtol 1e-6).
MUSS: ridge on the standardised design with the centred / scaled target, (X'X + n lam I) w = X'y, original units,
clipped to the scale range for every arm (unclipped kept as sensitivity).
Design: quadratic B-splines (3 quantile knots, no bias) of age and log1p(device months) plus the arm's EEG view; knots,
imputation medians and standardisation are fitted on the labelled fitting rows only. Inner 3-fold selection of
lam in [0.01, 0.1, 1] by mean RPS (SIR) or MAE (MUSS); ties go to the larger lam; final refit on all labels.
"""
from __future__ import annotations

import numpy as np
from scipy import optimize
from scipy.special import expit, log_expit

LEVELS = 5
PRIOR_T = np.log(np.arange(1, LEVELS) / LEVELS / (1 - np.arange(1, LEVELS) / LEVELS))     # logit(k/5), k=1..4


# ---------------------------------------------------------------------- design

class Design:
    """Clinical splines + EEG view, fitted on the labelled fitting rows only."""

    def __init__(self, spline: dict):
        self.spline = spline

    def fit(self, clin: np.ndarray, view: np.ndarray | None):
        from sklearn.preprocessing import SplineTransformer
        self.parts = []
        for j in range(clin.shape[1]):
            x = clin[:, j:j + 1]
            knots = np.percentile(x[:, 0], np.linspace(0, 100, int(self.spline["n_knots"])))
            if np.unique(x).size >= int(self.spline["min_unique_for_spline"]) and np.all(np.diff(knots) > 0):
                st = SplineTransformer(n_knots=int(self.spline["n_knots"]), degree=int(self.spline["degree"]),
                                       knots="quantile", include_bias=bool(self.spline["include_bias"]),
                                       extrapolation=str(self.spline["extrapolation"])).fit(x)
                self.parts.append(("spline", st))
            else:
                self.parts.append(("linear", None))
        raw = self._raw(clin, view, fit_median=True)
        self.mean = raw.mean(0)
        sd = raw.std(0)
        self.sd = np.where(sd < 1e-12, 1.0, sd)
        self.n_linear_fallback = sum(1 for k, _ in self.parts if k == "linear")
        return self

    def _raw(self, clin, view, fit_median=False):
        cols = []
        for j, (kind, st) in enumerate(self.parts):
            x = clin[:, j:j + 1]
            cols.append(st.transform(x) if kind == "spline" else x)
        if view is not None:
            v = np.asarray(view, np.float64)
            if fit_median:
                med = np.nanmedian(v, 0)
                self.median = np.where(np.isfinite(med), med, 0.0)
                self.n_imputed_fit = int((~np.isfinite(v)).sum())
            v = np.where(np.isfinite(v), v, self.median[None, :])
            cols.append(v)
        return np.concatenate(cols, 1) if cols else np.zeros((clin.shape[0], 0))

    def transform(self, clin, view):
        return (self._raw(clin, view) - self.mean) / self.sd


def clinical_matrix(age: np.ndarray, device_months: np.ndarray) -> np.ndarray:
    return np.column_stack([np.asarray(age, float), np.log1p(np.asarray(device_months, float))])


# ---------------------------------------------------------------------- proportional odds

def _unpack(theta: np.ndarray, p: int):
    w, t1, r = theta[:p], theta[p], theta[p + 1:]
    t = t1 + np.concatenate([[0.0], np.cumsum(np.logaddexp(0.0, r) + 1e-4)])
    return w, t, r


def _log1mexp(x):
    """log(1 - exp(x)) for x < 0, stable."""
    x = np.asarray(x, float)
    return np.where(x > -0.6931471805599453, np.log(-np.expm1(x)), np.log1p(-np.exp(x)))


def level_logprob(t: np.ndarray, eta: np.ndarray) -> np.ndarray:
    """log P(Y = k | eta) for k = 1..5, [n, 5], via logsig(b) + logsig(-a) + log(1 - exp(a - b))."""
    c = t[None, :] - eta[:, None]                                          # [n, 4]
    out = np.empty((eta.shape[0], LEVELS))
    out[:, 0] = log_expit(c[:, 0])
    out[:, -1] = log_expit(-c[:, -1])
    for k in range(1, LEVELS - 1):
        a, b = c[:, k - 1], c[:, k]
        out[:, k] = log_expit(b) + log_expit(-a) + _log1mexp(a - b)
    return out


def objective(theta: np.ndarray, X: np.ndarray, y: np.ndarray, lam: float, prior_w: float):
    """Mean NLL + lam/2 ||w||^2 + prior_w/2 ||t - a||^2 and its analytic gradient. y in 1..5."""
    n, p = X.shape
    w, t, r = _unpack(theta, p)
    eta = X @ w
    lp = level_logprob(t, eta)
    yi = y.astype(int) - 1
    nll = -lp[np.arange(n), yi].mean()
    c = t[None, :] - eta[:, None]
    # d(-log P)/dc_k for the observed level
    G = np.zeros((n, LEVELS - 1))
    logp = lp[np.arange(n), yi]
    for k in range(LEVELS - 1):
        ratio = np.exp(log_expit(c[:, k]) + log_expit(-c[:, k]) - logp)   # sigmoid'(c_k) / P(observed level)
        upper = yi == k                                                    # c_k is the upper cut of level k+1
        lower = yi == k + 1                                                # c_k is the lower cut of level k+2
        G[upper, k] -= ratio[upper]
        G[lower, k] += ratio[lower]
    g_eta = -G.sum(1)
    g_w = X.T @ g_eta / n + lam * w
    g_t = G.sum(0) / n + prior_w * (t - PRIOR_T)
    g_t1 = g_t.sum()
    g_r = np.array([expit(r[j]) * g_t[j + 1:].sum() for j in range(LEVELS - 2)])
    f = nll + 0.5 * lam * w @ w + 0.5 * prior_w * np.sum((t - PRIOR_T) ** 2)
    return f, np.concatenate([g_w, [g_t1], g_r])


def fit_ordinal(X: np.ndarray, y: np.ndarray, lam: float, *, prior_w: float = 0.001, maxiter: int = 400,
                gtol: float = 1e-6) -> dict:
    X = np.asarray(X, np.float64)
    y = np.asarray(y)
    p = X.shape[1]
    r0 = np.log(np.expm1(np.diff(PRIOR_T) - 1e-4))
    theta0 = np.concatenate([np.zeros(p), [PRIOR_T[0]], r0])
    f0, _ = objective(theta0, X, y, lam, prior_w)
    res = optimize.minimize(objective, theta0, args=(X, y, lam, prior_w), jac=True, method="L-BFGS-B",
                            options={"maxiter": int(maxiter), "gtol": float(gtol)})
    w, t, _ = _unpack(res.x, p)
    _, g = objective(res.x, X, y, lam, prior_w)
    return {"w": w, "t": t, "converged": bool(res.success), "nit": int(res.nit), "message": str(res.message),
            "initial_objective": float(f0), "final_objective": float(res.fun), "grad_norm": float(np.abs(g).max())}


def predict_ordinal(model: dict, X: np.ndarray) -> np.ndarray:
    P = np.exp(level_logprob(model["t"], np.asarray(X, np.float64) @ model["w"]))
    return P / P.sum(1, keepdims=True)


def prior_probabilities(y_train: np.ndarray, pseudo: float = 0.5) -> np.ndarray:
    counts = np.bincount(np.asarray(y_train, int) - 1, minlength=LEVELS).astype(float) + pseudo
    return counts / counts.sum()


def rps(P: np.ndarray, y: np.ndarray) -> np.ndarray:
    F = np.cumsum(P, 1)[:, :-1]
    truth = (np.asarray(y, int)[:, None] <= np.arange(1, LEVELS)[None, :]).astype(float)
    return ((F - truth) ** 2).mean(1)


# ---------------------------------------------------------------------- MUSS ridge

def fit_ridge(X: np.ndarray, y: np.ndarray, lam: float) -> dict:
    X, y = np.asarray(X, np.float64), np.asarray(y, np.float64)
    n, p = X.shape
    mu, sd = y.mean(), y.std()
    sd = sd if sd > 1e-12 else 1.0
    w = np.linalg.solve(X.T @ X + n * lam * np.eye(p), X.T @ ((y - mu) / sd))
    return {"w": w, "mu": mu, "sd": sd}


def predict_ridge(model: dict, X: np.ndarray) -> np.ndarray:
    return model["mu"] + model["sd"] * (np.asarray(X, np.float64) @ model["w"])


# ---------------------------------------------------------------------- one labelled set: inner selection + final fit

def fit_head(kind: str, clin_L, view_L, y_L, fold_of_L, clin_test, view_test, config: dict, extra_tests: dict | None = None) -> dict:
    """kind in {'sir', 'muss'}. Returns test predictions, the selected lambda, inner scores and a ledger of every
    optimiser call (10 = 3 lambdas x 3 inner folds + 1 final). extra_tests {name: (clin, view)} are scored by the same
    final fitted head (E5 split-half inputs; no additional fit)."""
    c = config["clinical"]
    lambdas = [float(v) for v in c["lambda_mean_loss"]]
    folds = np.asarray(fold_of_L)
    calls, scores = [], {}
    lo, hi = (float(v) for v in config["targets"]["muss_range"])
    for lam in lambdas:
        errs = []
        for f in sorted(set(folds.tolist())):
            tr, te = folds != f, folds == f
            D = Design(c["clinical_spline"]).fit(clin_L[tr], None if view_L is None else view_L[tr])
            Xtr = D.transform(clin_L[tr], None if view_L is None else view_L[tr])
            Xte = D.transform(clin_L[te], None if view_L is None else view_L[te])
            if kind == "sir":
                m = fit_ordinal(Xtr, y_L[tr], lam, prior_w=float(c["threshold_prior_weight"]),
                                maxiter=int(c["max_optimizer_iterations"]), gtol=float(c["optimizer_tolerance"]))
                errs.append(rps(predict_ordinal(m, Xte), y_L[te]))
                calls.append({"stage": "inner", "lambda": lam, "fold": int(f), **_fit_info(m)})
            else:
                m = fit_ridge(Xtr, y_L[tr], lam)
                pred = np.clip(predict_ridge(m, Xte), lo, hi)
                errs.append(np.abs(pred - y_L[te]))
                calls.append({"stage": "inner", "lambda": lam, "fold": int(f), "converged": True, "closed_form": True})
        scores[lam] = float(np.concatenate(errs).mean())
    best = min(scores.values())
    lam_star = max(l for l, v in scores.items() if v <= best + 1e-12)                # ties -> larger lambda
    D = Design(c["clinical_spline"]).fit(clin_L, view_L)
    XL, Xt = D.transform(clin_L, view_L), D.transform(clin_test, view_test)
    out = {"lambda": lam_star, "inner_scores": scores, "n_features": int(XL.shape[1]),
           "linear_fallbacks": int(D.n_linear_fallback), "imputed_fit_values": int(getattr(D, "n_imputed_fit", 0))}
    if kind == "sir":
        m = fit_ordinal(XL, y_L, lam_star, prior_w=float(c["threshold_prior_weight"]),
                        maxiter=int(c["max_optimizer_iterations"]), gtol=float(c["optimizer_tolerance"]))
        P = predict_ordinal(m, Xt)
        out.update(proba=P, thresholds=m["t"].tolist(), train_level_counts=np.bincount(np.asarray(y_L, int) - 1, minlength=LEVELS).tolist())
        out["extra"] = {name: predict_ordinal(m, D.transform(cx, vx)) for name, (cx, vx) in (extra_tests or {}).items()}
        calls.append({"stage": "final", "lambda": lam_star, "fold": -1, **_fit_info(m)})
    else:
        m = fit_ridge(XL, y_L, lam_star)
        raw = predict_ridge(m, Xt)
        out.update(pred_raw=raw, pred=np.clip(raw, lo, hi))
        out["extra"] = {name: np.clip(predict_ridge(m, D.transform(cx, vx)), lo, hi) for name, (cx, vx) in (extra_tests or {}).items()}
        calls.append({"stage": "final", "lambda": lam_star, "fold": -1, "converged": True, "closed_form": True})
    out["calls"] = calls
    return out


def _fit_info(m: dict) -> dict:
    return {"converged": m["converged"], "nit": m["nit"], "message": m["message"][:80],
            "initial_objective": m["initial_objective"], "final_objective": m["final_objective"],
            "grad_norm": m["grad_norm"]}
