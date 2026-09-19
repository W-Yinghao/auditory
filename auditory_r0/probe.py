"""R0 diagnostics. Closed form only; no neural fit, no raw EEG read, no M-matrix refit."""
from __future__ import annotations

import numpy as np

PENALTIES = np.logspace(-2, 4, 13)


def naive_oof(target: np.ndarray, folds, keep: np.ndarray | None = None) -> dict:
    """Training-mean and training-median predictors on the frozen outer folds.

    `keep` restricts the probe to records with an observed value; every kept record
    must still receive exactly one out-of-fold prediction.
    """
    if keep is None:
        keep = np.ones(target.shape, dtype=bool)
    mean_pred = np.full(target.shape, np.nan)
    median_pred = np.full(target.shape, np.nan)
    for fold in folds:
        train = np.array([i for i in fold["train_idx"] if keep[i]], dtype=int)
        test = np.array([i for i in fold["test_idx"] if keep[i]], dtype=int)
        if train.size == 0 or test.size == 0:
            continue
        mean_pred[test] = float(target[train].mean())
        median_pred[test] = float(np.median(target[train]))
    assert np.isfinite(mean_pred[keep]).all() and np.isfinite(median_pred[keep]).all()
    return {"mean": mean_pred, "median": median_pred}


def errors(pred: np.ndarray, target: np.ndarray) -> dict:
    residual = pred - target
    return {"MAE": float(np.abs(residual).mean()), "RMSE": float(np.sqrt((residual ** 2).mean())),
            "n": int(target.size)}


def skill(pred: np.ndarray, baseline: np.ndarray, target: np.ndarray) -> float:
    """1 - SSE(model)/SSE(out-of-fold training-mean baseline). Zero means no better than guessing."""
    denominator = float(((baseline - target) ** 2).sum())
    if denominator <= 0:
        return float("nan")
    return float(1.0 - ((pred - target) ** 2).sum() / denominator)


def _standardise(train_x: np.ndarray):
    centre = train_x.mean(axis=0)
    spread = train_x.std(axis=0)
    spread = np.where(spread <= 1e-12, 1.0, spread)
    return centre, spread


def ridge_fit(x: np.ndarray, y: np.ndarray, penalty: float):
    centre, spread = _standardise(x)
    z = (x - centre) / spread
    intercept = float(y.mean())
    gram = z.T @ z + penalty * np.eye(z.shape[1])
    coef = np.linalg.solve(gram, z.T @ (y - intercept))
    return {"centre": centre, "spread": spread, "coef": coef, "intercept": intercept}


def ridge_apply(model: dict, x: np.ndarray) -> np.ndarray:
    return model["intercept"] + ((x - model["centre"]) / model["spread"]) @ model["coef"]


def ridge_oof(x: np.ndarray, y: np.ndarray, folds, keep: np.ndarray) -> tuple[np.ndarray, list]:
    """Nested OOF ridge: penalty chosen by inner-fold MSE, refit on the outer training set.

    `keep` is a boolean mask of records with an observed target; folds are subset to it.
    """
    prediction = np.full(y.shape, np.nan)
    chosen = []
    for fold in folds:
        train = np.array([i for i in fold["train_idx"] if keep[i]], dtype=int)
        test = np.array([i for i in fold["test_idx"] if keep[i]], dtype=int)
        if train.size < 5 or test.size == 0:
            continue
        scores = []
        for penalty in PENALTIES:
            total, count = 0.0, 0
            for inner in fold["inner"]:
                itrain = np.array([i for i in inner["train_idx"] if keep[i]], dtype=int)
                ivalid = np.array([i for i in inner["validation_idx"] if keep[i]], dtype=int)
                if itrain.size < 5 or ivalid.size == 0:
                    continue
                model = ridge_fit(x[itrain], y[itrain], penalty)
                total += float(((ridge_apply(model, x[ivalid]) - y[ivalid]) ** 2).sum())
                count += ivalid.size
            scores.append(total / count if count else np.inf)
        penalty = float(PENALTIES[int(np.argmin(scores))])
        model = ridge_fit(x[train], y[train], penalty)
        prediction[test] = ridge_apply(model, x[test])
        chosen.append({"outer_fold": int(fold["outer_fold"]), "penalty": penalty,
                       "n_train": int(train.size), "n_test": int(test.size)})
    return prediction, chosen


def summarise_windows(segments: np.ndarray) -> np.ndarray:
    """(n, 32, 140) -> (n, 280): per-record window mean and window standard deviation."""
    return np.concatenate([segments.mean(axis=1), segments.std(axis=1)], axis=1)


def split_half_reliability(segments: np.ndarray) -> np.ndarray:
    """Per-feature correlation across records between odd-window and even-window means."""
    first = segments[:, 0::2, :].mean(axis=1)
    second = segments[:, 1::2, :].mean(axis=1)
    out = np.full(segments.shape[2], np.nan)
    for j in range(segments.shape[2]):
        a, b = first[:, j], second[:, j]
        if a.std() <= 1e-12 or b.std() <= 1e-12:
            continue
        out[j] = float(np.corrcoef(a, b)[0, 1])
    return out


def quantiles(values: np.ndarray) -> dict:
    ordered = np.sort(np.asarray(values, dtype=float))
    def q(p):
        return float(np.quantile(ordered, p))
    return {"n": int(ordered.size), "min": float(ordered[0]), "p25": q(0.25), "median": q(0.5),
            "p75": q(0.75), "max": float(ordered[-1]), "mean": float(ordered.mean()),
            "sd": float(ordered.std(ddof=1)) if ordered.size > 1 else float("nan")}


def granularity(values: np.ndarray) -> dict:
    """Aggregate description of the measurement grid; reports no individual value."""
    distinct = np.unique(np.asarray(values, dtype=float))
    gaps = np.diff(distinct)
    scaled = np.round(gaps * 1000).astype(np.int64)
    step = 0
    for value in scaled:
        step = int(np.gcd(step, int(value)))
    return {"n_distinct_values": int(distinct.size),
            "implied_step": step / 1000.0 if step else None,
            "smallest_observed_gap": float(gaps.min()) if gaps.size else None}
