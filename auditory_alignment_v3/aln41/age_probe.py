#!/usr/bin/env python3
"""Nested child-level frozen-feature age probe; NumPy only.

Input NPZ (allow_pickle=False): X[N,D], age[N] in months, ids[N] strings,
folds[N] fixed outer test folds, optional feature_names[D]. One child per row.
Features must come from one shared frozen public-source encoder per arm, not
from concatenating outputs of independently fine-tuned target-fold encoders.
This array-only CLI cannot verify that upstream provenance.

Example: python age_probe.py --input features.npz --out age_results.json
"""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np


ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)
INNER_SEED = 3431


def _strings(values, name, n):
    values = np.asarray(values)
    if values.shape != (n,):
        raise ValueError(f"{name} must have shape ({n},)")
    if values.dtype.kind not in "USiu":
        raise ValueError(f"{name} must contain strings or integers, not objects/floats")
    result = values.astype(str)
    if any(not value.strip() for value in result):
        raise ValueError(f"{name} contains an empty value")
    return result


@dataclass
class RidgeFit:
    x_mean: np.ndarray
    x_scale: np.ndarray
    z_train: np.ndarray
    dual: np.ndarray
    y_mean: float
    alpha: float
    trace_scale: float
    penalty: float
    zero_scale_fallback: bool
    constant_features: int

    def predict(self, x):
        x = np.asarray(x, dtype=np.float64)
        if x.ndim != 2 or x.shape[1] != self.x_mean.size or not np.isfinite(x).all():
            raise ValueError("prediction X has wrong shape or nonfinite entries")
        z = (x - self.x_mean) / self.x_scale
        return self.y_mean + (z @ self.z_train.T) @ self.dual


def fit_ridge(x, y, alpha):
    """Train-only ddof=0 standardization and centered dual ridge.

    lambda = alpha * trace(Z Z.T) / n_train. When that trace scale is exactly
    zero, use 1.0 as the explicit scale fallback; centered features/predictions
    then vanish and the result is exactly the training-age mean.
    """
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if x.ndim != 2 or min(x.shape) < 1 or y.shape != (x.shape[0],):
        raise ValueError("ridge requires X[n,d] and y[n], with n,d >= 1")
    if not np.isfinite(x).all() or not np.isfinite(y).all() or not (np.isfinite(alpha) and alpha > 0):
        raise ValueError("ridge inputs must be finite and alpha positive")
    mean, std = x.mean(axis=0), x.std(axis=0, ddof=0)
    constant = std == 0.0
    scale = np.where(constant, 1.0, std)
    z = (x - mean) / scale
    gram = z @ z.T
    trace_scale = float(np.trace(gram) / x.shape[0])
    if not np.isfinite(trace_scale) or not np.isfinite(z).all():
        raise ValueError("numeric overflow in training feature standardization")
    zero_scale = trace_scale == 0.0
    penalty = float(alpha * (1.0 if zero_scale else trace_scale))
    gram.flat[:: gram.shape[0] + 1] += penalty
    y_mean = float(y.mean())
    dual = np.linalg.solve(gram, y - y_mean)
    return RidgeFit(mean, scale, z, dual, y_mean, float(alpha), trace_scale,
                    penalty, bool(zero_scale), int(constant.sum()))


def average_ranks(values):
    """One-based midranks, including exact ties; no SciPy dependency."""
    values = np.asarray(values, dtype=np.float64)
    order = np.argsort(values, kind="stable")
    ranks = np.empty(values.size, dtype=np.float64)
    start = 0
    while start < values.size:
        stop = start + 1
        while stop < values.size and values[order[stop]] == values[order[start]]:
            stop += 1
        ranks[order[start:stop]] = (start + 1 + stop) / 2.0
        start = stop
    return ranks


def metrics(y, pred):
    residual = pred - y
    sst = float(np.sum((y - y.mean()) ** 2))
    yr, pr = average_ranks(y), average_ranks(pred)
    yr, pr = yr - yr.mean(), pr - pr.mean()
    denominator = float(np.linalg.norm(yr) * np.linalg.norm(pr))
    return {
        "mae_months": float(np.mean(np.abs(residual))),
        "rmse_months": float(np.sqrt(np.mean(residual ** 2))),
        "r2": None if sst == 0.0 else float(1.0 - np.sum(residual ** 2) / sst),
        "spearman": None if denominator == 0.0 else float(np.dot(yr, pr) / denominator),
    }


def _array_hash(x):
    return hashlib.sha256(np.asarray(x, dtype="<f8").tobytes()).hexdigest()


def run_probe(x, age, ids, folds, feature_names=None):
    x, age = np.asarray(x, dtype=np.float64), np.asarray(age, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] < 1 or age.shape != (x.shape[0],):
        raise ValueError("expected X[N,D] and age[N], with D >= 1")
    n_input = x.shape[0]
    ids, folds = _strings(ids, "ids", n_input), _strings(folds, "folds", n_input)
    if np.unique(ids).size != n_input:
        raise ValueError("duplicate child ids: exactly one row per child is required")
    names = None if feature_names is None else _strings(feature_names, "feature_names", x.shape[1]).tolist()
    keep = np.isfinite(age)
    excluded = [{"id": str(ids[i]), "input_row": int(i), "fold": str(folds[i]),
                 "reason": "nonfinite_age", "age_representation": str(age[i])}
                for i in np.flatnonzero(~keep)]
    retained_rows = np.flatnonzero(keep)
    x, age, ids, folds = x[keep], age[keep], ids[keep], folds[keep]
    if not np.isfinite(x).all():
        raise ValueError("retained X contains nonfinite features; no implicit imputation")
    unique_folds = np.unique(folds)
    if unique_folds.size < 2:
        raise ValueError("need at least two nonempty fixed outer folds after age filtering")

    def sorted_indices(mask):
        idx = np.flatnonzero(mask)
        return idx[np.argsort(ids[idx], kind="stable")]

    predictions = np.full(age.size, np.nan)
    train_means = np.full(age.size, np.nan)
    chosen_alphas = np.full(age.size, np.nan)
    fold_results = []
    for fold in unique_folds:
        train, test = sorted_indices(folds != fold), sorted_indices(folds == fold)
        if train.size < 2:
            raise ValueError(f"outer fold {fold}: need at least 2 training children for inner CV")
        # Stable child order makes assignments independent of input row order.
        shuffled = np.random.default_rng(INNER_SEED).permutation(train)
        inner_tests = np.array_split(shuffled, min(4, train.size))
        alpha_scores = []
        for alpha in ALPHAS:
            errors = []
            for inner_test in inner_tests:
                inner_train = train[~np.isin(train, inner_test)]
                fitted = fit_ridge(x[inner_train], age[inner_train], alpha)
                errors.extend(np.abs(fitted.predict(x[inner_test]) - age[inner_test]).tolist())
            # Child-weighted pooled OOF MAE, rather than weighting unequal folds equally.
            alpha_scores.append(float(np.mean(errors)))
        # ALPHAS is increasing; argmin therefore breaks exact ties at the smallest alpha.
        selected = ALPHAS[int(np.argmin(alpha_scores))]
        fitted = fit_ridge(x[train], age[train], selected)
        predictions[test] = fitted.predict(x[test])
        train_means[test] = fitted.y_mean
        chosen_alphas[test] = selected
        fold_results.append({
            "fold": str(fold), "n_train": int(train.size), "n_test": int(test.size),
            "train_ids": ids[train].tolist(), "test_ids": ids[test].tolist(),
            "inner_seed": INNER_SEED, "n_inner_folds": len(inner_tests),
            "inner_validation_ids": [ids[a].tolist() for a in inner_tests],
            "inner_mae_by_alpha": [{"alpha": a, "mae_months": m} for a, m in zip(ALPHAS, alpha_scores)],
            "selected_alpha": selected, "ridge_trace_scale": fitted.trace_scale,
            "ridge_penalty": fitted.penalty, "zero_scale_fallback": fitted.zero_scale_fallback,
            "constant_features": fitted.constant_features, "train_mean_age_months": fitted.y_mean,
            "train_feature_mean_sha256": _array_hash(fitted.x_mean),
            "train_feature_scale_sha256": _array_hash(fitted.x_scale),
        })
    if not np.isfinite(predictions).all():
        raise ValueError("not all heldout predictions are finite")
    model_error, mean_error = np.abs(predictions - age), np.abs(train_means - age)
    return {
        "schema": "aln4.child_age_probe.v1", "age_unit": "months",
        "encoder_contract": "one shared public-source frozen encoder per arm; array CLI cannot verify upstream provenance",
        "input_rows": n_input, "retained_children": int(age.size), "n_features": int(x.shape[1]),
        "feature_names": names, "excluded_rows": excluded,
        "retained_ids": ids.tolist(), "retained_input_rows": retained_rows.tolist(),
        "fixed_outer_fold_count": int(unique_folds.size),
        "ridge_definition": "lambda=alpha*trace(Z_train Z_train.T)/n_train; exact-zero scale uses 1.0",
        "inner_selection": "child-pooled OOF MAE; exact ties choose smallest alpha",
        "preprocessing": "train-only per inner/outer fit: mean, ddof=0 std, constant std -> 1; no PCA",
        "undefined_metrics": "R2=null for constant ages; Spearman=null for either constant rank vector",
        "model_metrics": metrics(age, predictions), "train_mean_metrics": metrics(age, train_means),
        "mean_paired_absolute_error_difference_months": float(np.mean(model_error - mean_error)),
        "paired_difference_direction": "model absolute error minus train-mean absolute error; negative favors model",
        "fold_results": fold_results,
        "children": [{
            "id": str(ids[i]), "fold": str(folds[i]), "input_row": int(retained_rows[i]),
            "age_months": float(age[i]), "prediction_months": float(predictions[i]),
            "train_mean_prediction_months": float(train_means[i]), "selected_alpha": float(chosen_alphas[i]),
            "model_absolute_error_months": float(model_error[i]),
            "train_mean_absolute_error_months": float(mean_error[i]),
            "paired_absolute_error_difference_months": float(model_error[i] - mean_error[i]),
        } for i in range(age.size)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="JSON output path")
    args = parser.parse_args()
    try:
        with np.load(args.input, allow_pickle=False) as arrays:
            missing = {"X", "age", "ids", "folds"} - set(arrays.files)
            if missing:
                raise ValueError(f"missing NPZ keys: {sorted(missing)}")
            result = run_probe(arrays["X"], arrays["age"], arrays["ids"], arrays["folds"],
                               arrays["feature_names"] if "feature_names" in arrays.files else None)
        result["input_npz_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (ValueError, OSError, np.linalg.LinAlgError) as exc:
        parser.exit(2, f"age_probe: {exc}\n")
    print(json.dumps({"out": str(args.out), "retained_children": result["retained_children"],
                      "model_metrics": result["model_metrics"]}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
