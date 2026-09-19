"""Channel-budget curve on the classical spectral arm. Closed-form and fast."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from . import channels as channel_tools
from . import spectral
from . import train as train_tools
from .budget import identity_folds
from .data import RecordStore, record_scale

PENALTIES = (0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0)


def _fit_predict(x_train, y_train, x_eval, penalty):
    scaler = StandardScaler().fit(x_train)
    model = LogisticRegression(C=penalty, max_iter=4000)
    model.fit(scaler.transform(x_train), y_train)
    classes = model.classes_
    probabilities = model.predict_proba(scaler.transform(x_eval))
    return classes, probabilities


def _full_log_probabilities(classes, probabilities, n_classes):
    full = np.full((probabilities.shape[0], n_classes), 1e-12)
    full[:, classes] = np.maximum(probabilities, 1e-12)
    full = full / full.sum(axis=1, keepdims=True)
    return np.log(full)


def run_spectral_budget(args, root: Path, private: Path, results: Path) -> dict:
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
    qc = []
    for unit in units:
        store = RecordStore(root, args.run, unit["container_id"],
                            max_bad_fraction=args.max_bad_fraction, preload=False)
        qc.append({"container_id": unit["container_id"], "usable_windows": int(store.starts.size),
                   "usable_fraction": round(store.usable_fraction, 4)})
        if store.starts.size < args.min_windows:
            continue
        stores.append(store)
        scales.append(record_scale(store))
        kept.append(unit)
    if len(kept) < 20:
        return {"status": "D2_INSUFFICIENT_RECORDS", "records": len(kept), "qc": qc}

    ages = np.array([u["age_months"] for u in kept], dtype=float)
    identities = np.array([u["identity"] for u in kept])
    folds = identity_folds(identities, args.folds, args.seed)
    budgets = [int(b) for b in str(args.budgets).split(",") if b]
    rng = np.random.default_rng(args.seed)

    # One pass over the signal for the whole curve: features are per-channel.
    feature_build = time.time()
    matrices = np.stack([spectral.record_feature_matrix(store, scale,
                                                        max_windows=args.max_windows)
                         for store, scale in zip(stores, scales)])
    matrices = matrices[:, keep, :]
    feature_seconds = round(time.time() - feature_build, 1)

    rows = []
    for budget in budgets:
        subsets = channel_tools.subset_variants(geometry, min(budget, geometry.shape[0]),
                                                args.variants, seed=args.seed)
        for variant, subset in enumerate(subsets):
            design = spectral.subset_design(matrices, subset)
            for fold in folds:
                train_idx, test_idx = fold["train"], fold["test"]
                edges = train_tools.quantile_bins(ages[train_idx], args.bins)
                n_classes = edges.size + 1
                labels = train_tools.assign_bins(ages, edges)
                fit_labels = labels.copy()
                if args.shuffle_control:
                    fit_labels[train_idx] = labels[rng.permutation(train_idx)]
                inner = identity_folds(identities[train_idx], min(3, len(train_idx)),
                                       args.seed + 7)
                scores = []
                for penalty in PENALTIES:
                    total, n = 0.0, 0
                    for part in inner:
                        a, b = train_idx[part["train"]], train_idx[part["test"]]
                        if b.size == 0 or np.unique(fit_labels[a]).size < 2:
                            continue
                        classes, probabilities = _fit_predict(design[a], fit_labels[a],
                                                              design[b], penalty)
                        log_probabilities = _full_log_probabilities(classes, probabilities,
                                                                    n_classes)
                        total += -log_probabilities[np.arange(b.size), labels[b]].sum()
                        n += b.size
                    scores.append(total / n if n else np.inf)
                penalty = PENALTIES[int(np.argmin(scores))]
                classes, probabilities = _fit_predict(design[train_idx], fit_labels[train_idx],
                                                      design[test_idx], penalty)
                log_probabilities = _full_log_probabilities(classes, probabilities, n_classes)
                marginal = train_tools.marginal_log_probabilities(fit_labels[train_idx], n_classes)
                centres = np.array([ages[labels == k].mean() if (labels == k).any()
                                    else float(np.median(ages)) for k in range(n_classes)])
                truth = labels[test_idx]
                model_bits = train_tools.cross_entropy_bits(log_probabilities, truth)
                base_bits = train_tools.cross_entropy_bits(
                    np.repeat(marginal[None, :], truth.size, axis=0), truth)
                expected = np.exp(log_probabilities) @ centres
                rows.append({"budget": budget, "variant": variant, "fold": fold["fold"],
                             "status": "OK", "n_electrodes": int(subset.size),
                             "penalty": penalty, "n_features": int(design.shape[1]),
                             "record_cross_entropy_bits": model_bits,
                             "record_marginal_bits": base_bits,
                             "record_bits_recovered": base_bits - model_bits,
                             "record_top1_accuracy": float(
                                 (np.exp(log_probabilities).argmax(axis=1) == truth).mean()),
                             "record_expected_value_MAE": float(
                                 np.abs(expected - ages[test_idx]).mean()),
                             "n_records": int(test_idx.size)})

    curve = []
    for budget in budgets:
        good = [r for r in rows if r["budget"] == budget]
        def stat(key):
            values = np.array([r[key] for r in good], dtype=float)
            return {"mean": float(values.mean()),
                    "sd": float(values.std(ddof=1)) if values.size > 1 else 0.0}
        curve.append({"budget": budget, "n_runs": len(good),
                      "n_electrodes": int(good[0]["n_electrodes"]),
                      "n_features": int(good[0]["n_features"]),
                      "record_bits_recovered": stat("record_bits_recovered"),
                      "record_expected_value_MAE": stat("record_expected_value_MAE"),
                      "record_top1_accuracy": stat("record_top1_accuracy"),
                      "record_marginal_bits": stat("record_marginal_bits")})
    payload = {"run": args.run, "arm": "spectral", "status": "D2_SPECTRAL_BUDGET_COMPLETE",
               "job_id": os.environ.get("SLURM_JOB_ID"),
               "shuffle_control": bool(args.shuffle_control),
               "max_bad_fraction": args.max_bad_fraction, "min_windows": args.min_windows,
               "n_records": len(kept), "n_identities": int(len(set(identities.tolist()))),
               "bins": args.bins, "folds": args.folds, "variants": args.variants,
               "features_per_channel": spectral.FEATURES_PER_CHANNEL,
               "age_months_sd": float(ages.std(ddof=1)),
               "usable_windows_total": int(sum(s.starts.size for s in stores)),
               "elapsed_minutes": round((time.time() - started) / 60.0, 1),
               "feature_build_seconds": feature_seconds,
               "curve": curve}
    name = args.out or f"{args.run}_spectral_budget"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{name}_curve.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}_curve.json").chmod(0o644)
    (private / f"{name}_rows.json").write_text(json.dumps(rows, indent=2) + "\n")
    (private / f"{name}_rows.json").chmod(0o600)
    (private / f"{name}_qc.json").write_text(json.dumps(qc, indent=2) + "\n")
    (private / f"{name}_qc.json").chmod(0o600)
    return payload
