"""Which electrodes? Nested greedy forward selection, chosen inside training folds only.

Reporting "the best 16 electrodes" after looking at every child would be selection on
the test set. Here the montage is re-selected from scratch inside each outer training
fold using inner-fold error alone, and the number reported is the out-of-fold error of
that whole procedure. The consensus montage across folds is reported separately, as a
recommendation with its selection frequency, never as the source of the error estimate.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from . import channels as channel_tools
from . import spectral
from . import train as train_tools
from .budget import identity_folds
from .data import RecordStore, record_scale
from .ridge_budget import GAMMAS, PENALTIES, _bin_probabilities, _kernel_ridge, _ridge


def _inner_error(design, target, identities, train_idx, inner, nonlinear):
    settings = ([(p, g) for p in PENALTIES for g in GAMMAS] if nonlinear
                else [(p, None) for p in PENALTIES])
    best = (np.inf, None)
    for penalty, gamma in settings:
        errors = []
        for part in inner:
            a, b = train_idx[part["train"]], train_idx[part["test"]]
            if b.size == 0:
                continue
            fit = (_kernel_ridge(design[a], target[a], design[b], penalty, gamma) if nonlinear
                   else _ridge(design[a], target[a], design[b], penalty))
            errors.append(fit - target[b])
        if errors:
            score = float(np.mean(np.concatenate(errors) ** 2))
            if score < best[0]:
                best = (score, (penalty, gamma))
    return best


def greedy_forward(matrices, target, identities, train_idx, inner, budget, nonlinear):
    """Add the electrode that most reduces inner-fold squared error, one at a time."""
    n_electrodes = matrices.shape[1]
    chosen: list[int] = []
    trace = []
    while len(chosen) < budget:
        best = (np.inf, None, None)
        for candidate in range(n_electrodes):
            if candidate in chosen:
                continue
            columns = chosen + [candidate]
            design = spectral.subset_design(matrices, np.array(columns, dtype=int))
            score, setting = _inner_error(design, target, identities, train_idx, inner, nonlinear)
            if score < best[0]:
                best = (score, candidate, setting)
        if best[1] is None:
            break
        chosen.append(best[1])
        trace.append({"step": len(chosen), "electrode": int(best[1]),
                      "inner_mse": best[0], "setting": list(best[2]) if best[2] else None})
    return chosen, trace


def run_select(args, root: Path, private: Path, results: Path) -> dict:
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
    names = [layout["channels"][i] for i in keep]

    stores, scales, kept = [], [], []
    for unit in units:
        store = RecordStore(root, args.run, unit["container_id"],
                            max_bad_fraction=args.max_bad_fraction, preload=False)
        if store.starts.size < args.min_windows:
            continue
        stores.append(store)
        scales.append(record_scale(store))
        kept.append(unit)
    matrices = np.stack([spectral.record_feature_matrix(s, sc, max_windows=args.max_windows)
                         for s, sc in zip(stores, scales)])[:, keep, :]
    ages = np.array([u["age_months"] for u in kept], dtype=float)
    identities = np.array([u["identity"] for u in kept])
    folds = identity_folds(identities, args.folds, args.seed)
    nonlinear = args.readout == "rbf"
    budget = args.select_budget

    predicted = np.full(ages.shape, np.nan)
    spread_predicted = np.full(ages.shape, np.nan)
    per_fold = []
    counter: dict[int, int] = {}
    for fold in folds:
        train_idx, test_idx = fold["train"], fold["test"]
        inner = identity_folds(identities[train_idx],
                               min(3, max(2, len(train_idx) // 8)), args.seed + 7)
        chosen, trace = greedy_forward(matrices, ages, identities, train_idx, inner,
                                       budget, nonlinear)
        for electrode in chosen:
            counter[electrode] = counter.get(electrode, 0) + 1
        design = spectral.subset_design(matrices, np.array(chosen, dtype=int))
        score, setting = _inner_error(design, ages, identities, train_idx, inner, nonlinear)
        penalty, gamma = setting
        predicted[test_idx] = (_kernel_ridge(design[train_idx], ages[train_idx],
                                             design[test_idx], penalty, gamma) if nonlinear
                               else _ridge(design[train_idx], ages[train_idx],
                                           design[test_idx], penalty))
        # Matched spatial baseline: the same number of electrodes, spread not selected.
        spread_subset = channel_tools.farthest_point_subset(geometry, budget, 0)
        spread_design = spectral.subset_design(matrices, spread_subset)
        spread_score, spread_setting = _inner_error(spread_design, ages, identities,
                                                    train_idx, inner, nonlinear)
        sp, sg = spread_setting
        spread_predicted[test_idx] = (
            _kernel_ridge(spread_design[train_idx], ages[train_idx], spread_design[test_idx],
                          sp, sg) if nonlinear else
            _ridge(spread_design[train_idx], ages[train_idx], spread_design[test_idx], sp))
        edges = train_tools.quantile_bins(ages[train_idx], args.bins)
        n_classes = edges.size + 1
        labels = train_tools.assign_bins(ages, edges)
        marginal = train_tools.marginal_log_probabilities(labels[train_idx], n_classes)
        log_probabilities = _bin_probabilities(predicted[test_idx], float(np.sqrt(score)),
                                               edges, n_classes)
        truth = labels[test_idx]
        per_fold.append({
            "fold": fold["fold"], "selected_indices": [int(c) for c in chosen],
            "selected_channels": [names[c] for c in chosen],
            "inner_mse": score, "penalty": penalty, "gamma": gamma,
            "MAE": float(np.abs(predicted[test_idx] - ages[test_idx]).mean()),
            "spread_MAE": float(np.abs(spread_predicted[test_idx] - ages[test_idx]).mean()),
            "bits_recovered": train_tools.cross_entropy_bits(
                np.repeat(marginal[None, :], truth.size, axis=0), truth)
            - train_tools.cross_entropy_bits(log_probabilities, truth),
            "trace": trace})

    order = sorted(counter, key=lambda k: (-counter[k], k))
    consensus = [{"channel": names[e], "index": int(e), "folds_selected": counter[e],
                  "xyz_m": [float(v) for v in geometry[e]]} for e in order[:budget]]
    payload = {
        "run": args.run, "arm": f"select_{args.readout}", "status": "D2_SELECT_COMPLETE",
        "job_id": os.environ.get("SLURM_JOB_ID"), "select_budget": budget,
        "readout": args.readout, "n_records": len(kept),
        "n_identities": int(len(set(identities.tolist()))),
        "electrodes_available": int(keep.size),
        "naive_mean_MAE": float(np.abs(ages - ages.mean()).mean()),
        "nested_selection_MAE": float(np.abs(predicted - ages).mean()),
        "matched_spread_MAE": float(np.abs(spread_predicted - ages).mean()),
        "mean_bits_recovered": float(np.mean([f["bits_recovered"] for f in per_fold])),
        "selection_overlap_between_folds": float(np.mean([
            len(set(a["selected_indices"]) & set(b["selected_indices"])) / budget
            for i, a in enumerate(per_fold) for b in per_fold[i + 1:]])),
        "consensus_montage": consensus,
        "folds": [{k: v for k, v in f.items() if k != "trace"} for f in per_fold],
        "elapsed_minutes": round((time.time() - started) / 60.0, 1),
    }
    name = args.out or f"{args.run}_select_{args.readout}_{budget}"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{name}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}.json").chmod(0o644)
    (private / f"{name}_predictions.json").write_text(json.dumps(
        {"identities": identities.tolist(), "ages": ages.tolist(),
         "predictions": {f"b{budget}_v0": predicted.tolist(),
                         f"spread_b{budget}_v0": spread_predicted.tolist()},
         "folds": [{"fold": f["fold"], "test": []} for f in per_fold],
         "per_fold": per_fold}, indent=2) + "\n")
    (private / f"{name}_predictions.json").chmod(0o600)
    return payload
