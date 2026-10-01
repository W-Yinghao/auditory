"""Age readouts with an explicit objective (execution spec 4.4-4.5).

Linear ridge:  min_{b,w} sum_i (A_i - b - x_i.w)^2 + alpha * ||w||^2   (SSE form, intercept unpenalised), FP64,
solved with np.linalg.solve (primal p x p when p <= n, dual n x n otherwise; never an explicit inverse).
RBF kernel ridge: gamma = 1 / median(nonzero squared training distances) (fallback fixed), training-centred kernel,
(K_c + alpha I) a = y_c. Inner CV: child folds, mean validation MAE, exact ties -> larger alpha. Every fit appends
diagnostics to the caller's ledger; failures are recorded, never replaced by constant predictions.
"""
from __future__ import annotations

import numpy as np
from sklearn.model_selection import KFold


class FitFailure(RuntimeError):
    pass


# ---------------------------------------------------------------------- linear ridge (SSE objective)

def ridge_fit(X: np.ndarray, y: np.ndarray, alpha: float) -> dict:
    X, y = np.asarray(X, np.float64), np.asarray(y, np.float64)
    if not (np.isfinite(X).all() and np.isfinite(y).all()):
        raise FitFailure("NONFINITE_INPUT")
    n, p = X.shape
    xm, ym = X.mean(0), float(y.mean())
    Xc, yc = X - xm, y - ym
    if p <= n:
        A = Xc.T @ Xc + alpha * np.eye(p)
        rhs = Xc.T @ yc
        w = np.linalg.solve(A, rhs)
        resid = float(np.linalg.norm(A @ w - rhs) / max(np.linalg.norm(rhs), 1e-300))
        cond = float(np.linalg.cond(A))
        form = "primal"
    else:
        G = Xc @ Xc.T + alpha * np.eye(n)
        beta = np.linalg.solve(G, yc)
        w = Xc.T @ beta
        resid = float(np.linalg.norm(G @ beta - yc) / max(np.linalg.norm(yc), 1e-300))
        cond = float(np.linalg.cond(G))
        form = "dual"
    if not np.isfinite(w).all():
        raise FitFailure("NONFINITE_COEFFICIENTS")
    fitted = ym + Xc @ w
    sse = float(np.sum((y - fitted) ** 2))
    return {"kind": "ridge", "xm": xm, "ym": ym, "w": w, "alpha": float(alpha), "form": form,
            "diag": {"n": int(n), "p": int(p), "rank": int(np.linalg.matrix_rank(Xc)), "cond": cond,
                     "solve_residual": resid, "w_norm": float(np.linalg.norm(w)),
                     "train_mae": float(np.mean(np.abs(y - fitted))), "objective_sse_l2": sse + alpha * float(w @ w)}}


def ridge_predict(model: dict, X: np.ndarray) -> np.ndarray:
    return model["ym"] + (np.asarray(X, np.float64) - model["xm"]) @ model["w"]


def ridge_fit_mse(X: np.ndarray, y: np.ndarray, alpha_mse: float) -> dict:
    """MSE + alpha_mse * ||w||^2 equals SSE + (n * alpha_mse) * ||w||^2 (the K0 scale lesson; T4)."""
    return ridge_fit(X, y, alpha_mse * len(y))


# ---------------------------------------------------------------------- RBF kernel ridge

def _sqdist(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    d = (A * A).sum(1)[:, None] + (B * B).sum(1)[None, :] - 2.0 * A @ B.T
    return np.maximum(d, 0.0)


def kernel_fit(X: np.ndarray, y: np.ndarray, alpha: float, *, gamma_fallback: float = 1.0) -> dict:
    X, y = np.asarray(X, np.float64), np.asarray(y, np.float64)
    if not (np.isfinite(X).all() and np.isfinite(y).all()):
        raise FitFailure("NONFINITE_INPUT")
    n = len(y)
    D = _sqdist(X, X)
    off = D[~np.eye(n, dtype=bool)]
    pos = off[off > 1e-12]
    fallback = pos.size == 0
    gamma = float(gamma_fallback) if fallback else 1.0 / float(np.median(pos))
    K = np.exp(-gamma * D)
    col = K.mean(0)
    allm = float(K.mean())
    Kc = K - col[None, :] - col[:, None] + allm
    ym = float(y.mean())
    G = Kc + alpha * np.eye(n)
    a = np.linalg.solve(G, y - ym)
    if not np.isfinite(a).all():
        raise FitFailure("NONFINITE_COEFFICIENTS")
    fitted = ym + Kc @ a
    return {"kind": "rbf", "Xtr": X, "gamma": gamma, "col": col, "allm": allm, "a": a, "ym": ym, "alpha": float(alpha),
            "diag": {"n": int(n), "p": int(X.shape[1]), "gamma": gamma, "gamma_fallback": bool(fallback),
                     "cond": float(np.linalg.cond(G)),
                     "solve_residual": float(np.linalg.norm(G @ a - (y - ym)) / max(np.linalg.norm(y - ym), 1e-300)),
                     "a_norm": float(np.linalg.norm(a)), "train_mae": float(np.mean(np.abs(y - fitted)))}}


def kernel_predict(model: dict, X: np.ndarray) -> np.ndarray:
    Kt = np.exp(-model["gamma"] * _sqdist(np.asarray(X, np.float64), model["Xtr"]))
    Kt_c = Kt - model["col"][None, :] - Kt.mean(1)[:, None] + model["allm"]
    return model["ym"] + Kt_c @ model["a"]


# ---------------------------------------------------------------------- selection by inner child folds

def fit_any(kind: str, X, y, alpha, gamma_fallback=1.0) -> dict:
    return kernel_fit(X, y, alpha, gamma_fallback=gamma_fallback) if kind == "rbf" else ridge_fit(X, y, alpha)


def predict_any(model: dict, X) -> np.ndarray:
    return kernel_predict(model, X) if model["kind"] == "rbf" else ridge_predict(model, X)


def choose_alpha(maes: dict[float, float], tol: float) -> float:
    """Smallest mean validation MAE; exact ties (within tol) go to the LARGER alpha."""
    finite = {a: m for a, m in maes.items() if np.isfinite(m)}
    if not finite:
        raise FitFailure("ALL_ALPHAS_FAILED")
    best = min(finite.values())
    return max(a for a, m in finite.items() if m <= best + tol)


def select_and_fit(design, y: np.ndarray, n_train: int, test_rows, *, kind: str, alphas, inner_folds: int,
                   inner_seed: int, tie_tol: float, ledger: list, key: dict, gamma_fallback: float = 1.0) -> dict:
    """`design(train_idx, eval_idx) -> (Xtr, Xev, info)` rebuilds every scale on the given training rows.

    Rows 0..n_train-1 are the outer-training children; `test_rows` index the outer-test children in the same
    row space. Returns test predictions, the chosen alpha and inner MAEs.
    """
    y = np.asarray(y, np.float64)
    tr_all = np.arange(n_train)
    splits = list(KFold(inner_folds, shuffle=True, random_state=inner_seed).split(tr_all))
    maes = {}
    for alpha in alphas:
        errs = []
        for f, (itr, iva) in enumerate(splits):
            rec = {**key, "stage": "inner", "inner_fold": f, "alpha": float(alpha), "n_train": int(len(itr)),
                   "n_eval": int(len(iva))}
            try:
                Xtr, Xva, info = design(tr_all[itr], tr_all[iva])
                model = fit_any(kind, Xtr, y[itr], alpha, gamma_fallback)
                pred = predict_any(model, Xva)
                if not np.isfinite(pred).all():
                    raise FitFailure("NONFINITE_PREDICTION")
                err = float(np.mean(np.abs(pred - y[iva])))
                rec.update(status="ok", val_mae=err, diag=model["diag"], design=info)
                errs.append(err)
            except (FitFailure, np.linalg.LinAlgError, ValueError) as exc:
                rec.update(status="failed", reason=str(exc))
                errs.append(np.nan)
            ledger.append(rec)
        maes[float(alpha)] = float(np.mean(errs)) if np.isfinite(errs).all() else float("nan")
    alpha = choose_alpha(maes, tie_tol)
    Xtr, Xte, info = design(tr_all, np.asarray(test_rows))
    rec = {**key, "stage": "outer", "alpha": alpha, "inner_mae": maes, "n_train": int(n_train), "n_eval": int(len(test_rows))}
    try:
        model = fit_any(kind, Xtr, y[:n_train], alpha, gamma_fallback)
        pred = predict_any(model, Xte)
        if not np.isfinite(pred).all():
            raise FitFailure("NONFINITE_PREDICTION")
    except (FitFailure, np.linalg.LinAlgError, ValueError) as exc:
        rec.update(status="failed", reason=str(exc))
        ledger.append(rec)
        raise FitFailure(f"OUTER_FIT_FAILED:{exc}") from exc
    const = bool(np.ptp(pred) < 1e-9 * max(1.0, float(np.abs(pred).max())))
    rec.update(status="ok", diag=model["diag"], design=info, constant_prediction=const)
    ledger.append(rec)
    return {"pred": pred, "alpha": alpha, "inner_mae": maes, "model": model, "constant_prediction": const,
            "n_fits": len(alphas) * len(splits) + 1}
