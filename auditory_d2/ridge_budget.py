"""Channel-budget curve, ridge arm.

Two changes from the logistic arm, both of which matter for what the curve can say:

1. Age is continuous, so the model is a ridge regression and the information readout is
   derived from it: the inner folds give an honest residual scale, the predictive
   Gaussian is integrated over the same quantile bins, and the cross-entropy against the
   train-fold marginal gives bits. Calibration therefore comes from held-out residuals
   rather than from a classifier's own confidence.
2. Every per-recording prediction is kept, so budgets can be compared PAIRED on the same
   children instead of as independent means, which is what the earlier run could not do.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from scipy.stats import norm

from . import channels as channel_tools
from . import spectral
from . import train as train_tools
from .budget import identity_folds
from .data import RecordStore, record_scale

PENALTIES = tuple(float(x) for x in np.logspace(-1, 5, 13))


GAMMAS = (0.03, 0.1, 0.3, 1.0, 3.0)


def _kernel_ridge(design_train, y_train, design_eval, penalty, gamma):
    """RBF kernel ridge: the same estimator with a nonlinear readout.

    This is the apples-to-apples nonlinear counterpart of the linear arm - identical
    nested selection, identical folds, identical readout - so a difference in the
    saturation point can be attributed to the readout rather than to the protocol.
    """
    centre = design_train.mean(axis=0, keepdims=True)
    spread = design_train.std(axis=0, keepdims=True)
    spread = np.where(spread <= 1e-12, 1.0, spread)
    z_train = (design_train - centre) / spread
    z_eval = (design_eval - centre) / spread
    scale = gamma / max(z_train.shape[1], 1)
    square_train = (z_train ** 2).sum(axis=1)
    gram = np.exp(-scale * (square_train[:, None] + square_train[None, :]
                            - 2.0 * z_train @ z_train.T))
    square_eval = (z_eval ** 2).sum(axis=1)
    cross = np.exp(-scale * (square_eval[:, None] + square_train[None, :]
                             - 2.0 * z_eval @ z_train.T))
    intercept = float(y_train.mean())
    dual = np.linalg.solve(gram + penalty * np.eye(gram.shape[0]), y_train - intercept)
    return intercept + cross @ dual


def _ridge(design_train, y_train, design_eval, penalty):
    centre = design_train.mean(axis=0, keepdims=True)
    spread = design_train.std(axis=0, keepdims=True)
    spread = np.where(spread <= 1e-12, 1.0, spread)
    z_train = (design_train - centre) / spread
    intercept = float(y_train.mean())
    gram = z_train.T @ z_train + penalty * np.eye(z_train.shape[1])
    coefficients = np.linalg.solve(gram, z_train.T @ (y_train - intercept))
    return intercept + ((design_eval - centre) / spread) @ coefficients


def _bin_probabilities(prediction, scale, edges, n_classes):
    """Integrate N(prediction, scale^2) over the quantile bins."""
    bounds = np.concatenate([[-np.inf], edges, [np.inf]])
    cdf = norm.cdf((bounds[None, :] - prediction[:, None]) / max(scale, 1e-6))
    probabilities = np.diff(cdf, axis=1)
    probabilities = np.maximum(probabilities, 1e-12)
    return np.log(probabilities / probabilities.sum(axis=1, keepdims=True))


def run_ridge_budget(args, root: Path, private: Path, results: Path) -> dict:
    started = time.time()
    cohort = json.loads((private / f"{args.run}_cohort.json").read_text())
    layouts = json.loads((private / f"{args.run}_geometry.json").read_text())
    counts: dict[str, int] = {}
    for unit in cohort["units"]:
        counts[str(unit["layout_hash"])] = counts.get(str(unit["layout_hash"]), 0) + 1
    layout_hash = max(counts, key=counts.get)
    layout = layouts[layout_hash]
    units = [u for u in cohort["units"] if str(u["layout_hash"]) == layout_hash]
    keep = np.array([i for i, p in enumerate(layout["xyz_m"]) if p is not None], dtype=int)
    geometry = np.asarray([layout["xyz_m"][i] for i in keep], dtype=float)

    stores, scales, kept = [], [], []
    for unit in units:
        store = RecordStore(root, args.run, unit["container_id"],
                            max_bad_fraction=args.max_bad_fraction, preload=False)
        if store.starts.size < args.min_windows:
            continue
        stores.append(store)
        scales.append(record_scale(store))
        kept.append(unit)
    if len(kept) < 20:
        return {"status": "D2_INSUFFICIENT_RECORDS", "records": len(kept)}

    ages = np.array([u["age_months"] for u in kept], dtype=float)
    identities = np.array([u["identity"] for u in kept])
    feature_build = time.time()
    minutes = getattr(args, "minutes", None)
    usable, retained_index = [], []
    for index, (store, scale) in enumerate(zip(stores, scales)):
        try:
            usable.append(spectral.record_feature_matrix(store, scale,
                                                         max_windows=args.max_windows,
                                                         minutes=minutes))
            retained_index.append(index)
        except ValueError:
            continue
    if len(usable) < 20:
        return {"status": "D2_INSUFFICIENT_RECORDS_AT_DURATION", "records": len(usable),
                "minutes": minutes}
    matrices = np.stack(usable)[:, keep, :]
    retained = np.array(retained_index, dtype=int)
    ages = ages[retained]
    identities = identities[retained]
    kept = [kept[i] for i in retained]
    folds = identity_folds(identities, args.folds, args.seed)
    feature_seconds = round(time.time() - feature_build, 1)

    budgets = [int(b) for b in str(args.budgets).split(",") if b]
    rng = np.random.default_rng(args.seed)
    predictions: dict[str, np.ndarray] = {}
    rows = []

    for budget in budgets:
        subsets = channel_tools.subset_variants(geometry, min(budget, geometry.shape[0]),
                                                args.variants, seed=args.seed)
        for variant, subset in enumerate(subsets):
            design = spectral.subset_design(matrices, subset)
            predicted = np.full(ages.shape, np.nan)
            log_probabilities = np.full((ages.size, args.bins), np.nan)
            for fold in folds:
                train_idx, test_idx = fold["train"], fold["test"]
                target = ages.copy()
                if args.shuffle_control:
                    target[train_idx] = ages[rng.permutation(train_idx)]
                inner = identity_folds(identities[train_idx],
                                       min(3, max(2, len(train_idx) // 8)), args.seed + 7)
                nonlinear = getattr(args, "readout", "linear") == "rbf"
                settings = ([(p, g) for p in PENALTIES for g in GAMMAS] if nonlinear
                            else [(p, None) for p in PENALTIES])
                errors = {key: [] for key in settings}
                for part in inner:
                    a, b = train_idx[part["train"]], train_idx[part["test"]]
                    if b.size == 0:
                        continue
                    for key in settings:
                        penalty, gamma = key
                        fit = (_kernel_ridge(design[a], target[a], design[b], penalty, gamma)
                               if nonlinear else
                               _ridge(design[a], target[a], design[b], penalty))
                        errors[key].append(fit - target[b])
                scored = {k: float(np.mean(np.concatenate(v) ** 2))
                          for k, v in errors.items() if v}
                best = min(scored, key=scored.get)
                penalty, gamma = best
                residual_scale = float(np.sqrt(scored[best]))
                predicted[test_idx] = (
                    _kernel_ridge(design[train_idx], target[train_idx], design[test_idx],
                                  penalty, gamma) if nonlinear else
                    _ridge(design[train_idx], target[train_idx], design[test_idx], penalty))
                edges = train_tools.quantile_bins(ages[train_idx], args.bins)
                n_classes = edges.size + 1
                log_probabilities[test_idx, :n_classes] = _bin_probabilities(
                    predicted[test_idx], residual_scale, edges, n_classes)
                labels = train_tools.assign_bins(ages, edges)
                marginal = train_tools.marginal_log_probabilities(labels[train_idx], n_classes)
                truth = labels[test_idx]
                model_bits = train_tools.cross_entropy_bits(
                    log_probabilities[test_idx, :n_classes], truth)
                base_bits = train_tools.cross_entropy_bits(
                    np.repeat(marginal[None, :], truth.size, axis=0), truth)
                rows.append({"budget": budget, "variant": variant, "fold": fold["fold"],
                             "n_electrodes": int(subset.size), "penalty": penalty,
                             "gamma": gamma, "readout": "rbf" if nonlinear else "linear",
                             "residual_scale_months": residual_scale,
                             "n_features": int(design.shape[1]), "n_records": int(test_idx.size),
                             "record_cross_entropy_bits": model_bits,
                             "record_marginal_bits": base_bits,
                             "record_bits_recovered": base_bits - model_bits,
                             "record_MAE": float(np.abs(predicted[test_idx]
                                                        - ages[test_idx]).mean())})
            predictions[f"b{budget}_v{variant}"] = predicted

    stacked = {k: v.tolist() for k, v in predictions.items()}
    name = args.out or f"{args.run}_ridge_budget"
    payload = {"run": args.run, "arm": getattr(args, "readout", "linear") + "_ridge", "status": "D2_RIDGE_BUDGET_COMPLETE",
               "job_id": os.environ.get("SLURM_JOB_ID"),
               "shuffle_control": bool(args.shuffle_control),
               "n_records": len(kept), "n_identities": int(len(set(identities.tolist()))),
               "age_months": {"sd": float(ages.std(ddof=1)), "mean": float(ages.mean()),
                              "min": float(ages.min()), "max": float(ages.max())},
               "naive_mean_MAE": float(np.abs(ages - ages.mean()).mean()),
               "max_bad_fraction": args.max_bad_fraction,
               "minutes": minutes,
               "bins": args.bins, "folds": args.folds, "variants": args.variants,
               "feature_build_seconds": feature_seconds,
               "elapsed_minutes": round((time.time() - started) / 60.0, 1),
               "curve": curve_from(rows, budgets)}
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{name}_curve.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}_curve.json").chmod(0o644)
    (private / f"{name}_predictions.json").write_text(json.dumps(
        {"identities": identities.tolist(), "ages": ages.tolist(),
         "folds": [{"fold": f["fold"], "test": f["test"].tolist()} for f in folds],
         "predictions": stacked, "rows": rows}, indent=2) + "\n")
    (private / f"{name}_predictions.json").chmod(0o600)
    return payload


def curve_from(rows: list[dict], budgets: list[int]) -> list[dict]:
    out = []
    for budget in budgets:
        good = [r for r in rows if r["budget"] == budget]
        def stat(key):
            values = np.array([r[key] for r in good], dtype=float)
            return {"mean": float(values.mean()),
                    "sd": float(values.std(ddof=1)) if values.size > 1 else 0.0}
        out.append({"budget": budget, "n_runs": len(good),
                    "n_electrodes": int(good[0]["n_electrodes"]),
                    "n_features": int(good[0]["n_features"]),
                    "record_bits_recovered": stat("record_bits_recovered"),
                    "record_MAE": stat("record_MAE"),
                    "residual_scale_months": stat("residual_scale_months")})
    return out
