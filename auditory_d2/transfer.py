"""Cross-cohort transfer between the high-density net and the clinical 10-20 montage.

The two branches were recorded on different amplifiers with different electrode arrays,
so this is the honest deployability test: fit on one and predict the other, with no
target-cohort labels used for anything, including hyperparameter choice.

High-density sensors are matched to the twenty 10-20 targets by a one-to-one assignment
under the same 40 mm limit the repository already froze for cross-layout work, and a
match is refused rather than approximated if any target is out of range.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from auditory5.adapters.mff import standard_1020_head_positions
from auditory5.preprocessing import HA_CHANNELS

from . import spectral
from . import train as train_tools
from .budget import identity_folds
from .data import RecordStore, record_scale
from .ridge_budget import GAMMAS, PENALTIES, _bin_probabilities, _kernel_ridge, _ridge

MAXIMUM_DISTANCE_M = 0.04


def match_to_1020(geometry: np.ndarray) -> tuple[np.ndarray, dict]:
    targets = standard_1020_head_positions(HA_CHANNELS)
    cost = np.linalg.norm(geometry[None, :, :] - targets[:, None, :], axis=-1)
    rows, columns = linear_sum_assignment(cost)
    distances = cost[rows, columns]
    diagnosis = {"max_distance_m": float(distances.max()),
                 "mean_distance_m": float(distances.mean()),
                 "limit_m": MAXIMUM_DISTANCE_M,
                 "eligible": bool(distances.max() <= MAXIMUM_DISTANCE_M)}
    assignment = np.empty(len(HA_CHANNELS), dtype=int)
    assignment[rows] = columns
    return assignment, diagnosis


def _load_branch(root: Path, private: Path, run: str, args) -> dict:
    cohort = json.loads((private / f"{run}_cohort.json").read_text())
    layouts = json.loads((private / f"{run}_geometry.json").read_text())
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
        store = RecordStore(root, run, unit["container_id"],
                            max_bad_fraction=args.max_bad_fraction, preload=False)
        if store.starts.size < args.min_windows:
            continue
        stores.append(store)
        scales.append(record_scale(store))
        kept.append(unit)
    matrices = np.stack([spectral.record_feature_matrix(s, sc, max_windows=args.max_windows)
                         for s, sc in zip(stores, scales)])[:, keep, :]
    channels = [layout["channels"][i] for i in keep]
    if len(channels) == len(HA_CHANNELS) and list(channels) == list(HA_CHANNELS):
        order = np.arange(len(HA_CHANNELS))
        diagnosis = {"exact_1020_montage": True}
    else:
        order, diagnosis = match_to_1020(geometry)
    return {"matrices": matrices[:, order, :],
            "ages": np.array([u["age_months"] for u in kept], dtype=float),
            "identities": np.array([u["identity"] for u in kept]),
            "n": len(kept), "match": diagnosis,
            "channels": [channels[i] for i in order]}


def _fit_transfer(source, target, args):
    """Choose hyperparameters on the SOURCE cohort only, then predict the target."""
    nonlinear = args.readout == "rbf"
    design_source = source["matrices"].reshape(source["matrices"].shape[0], -1)
    design_target = target["matrices"].reshape(target["matrices"].shape[0], -1)
    inner = identity_folds(source["identities"], args.folds, args.seed)
    settings = ([(p, g) for p in PENALTIES for g in GAMMAS] if nonlinear
                else [(p, None) for p in PENALTIES])
    best = (np.inf, None)
    for penalty, gamma in settings:
        errors = []
        for fold in inner:
            a, b = fold["train"], fold["test"]
            fit = (_kernel_ridge(design_source[a], source["ages"][a], design_source[b],
                                 penalty, gamma) if nonlinear else
                   _ridge(design_source[a], source["ages"][a], design_source[b], penalty))
            errors.append(fit - source["ages"][b])
        score = float(np.mean(np.concatenate(errors) ** 2))
        if score < best[0]:
            best = (score, (penalty, gamma))
    penalty, gamma = best[1]
    prediction = (_kernel_ridge(design_source, source["ages"], design_target, penalty, gamma)
                  if nonlinear else
                  _ridge(design_source, source["ages"], design_target, penalty))
    return prediction, penalty, gamma, float(np.sqrt(best[0]))


def run_transfer(args, root: Path, private: Path, results: Path) -> dict:
    started = time.time()
    left = _load_branch(root, private, args.run, args)
    right = _load_branch(root, private, args.compare, args)
    directions = []
    for source_name, source, target_name, target in (
            (args.run, left, args.compare, right), (args.compare, right, args.run, left)):
        prediction, penalty, gamma, residual = _fit_transfer(source, target, args)
        truth = target["ages"]
        # Baselines the target cohort could have without any EEG at all.
        source_mean = float(source["ages"].mean())
        edges = train_tools.quantile_bins(source["ages"], args.bins)
        n_classes = edges.size + 1
        labels = train_tools.assign_bins(truth, edges)
        marginal = train_tools.marginal_log_probabilities(
            train_tools.assign_bins(source["ages"], edges), n_classes)
        log_probabilities = _bin_probabilities(prediction, residual, edges, n_classes)
        overlap = (truth >= source["ages"].min()) & (truth <= source["ages"].max())
        directions.append({
            "source": source_name, "target": target_name,
            "n_source": source["n"], "n_target": target["n"],
            "penalty": penalty, "gamma": gamma, "source_residual_months": residual,
            "target_MAE": float(np.abs(prediction - truth).mean()),
            "source_mean_baseline_MAE": float(np.abs(source_mean - truth).mean()),
            "target_own_mean_MAE": float(np.abs(truth - truth.mean()).mean()),
            "bits_recovered_vs_source_marginal": train_tools.cross_entropy_bits(
                np.repeat(marginal[None, :], labels.size, axis=0), labels)
            - train_tools.cross_entropy_bits(log_probabilities, labels),
            "correlation_with_truth": float(np.corrcoef(prediction, truth)[0, 1]),
            "n_in_source_age_range": int(overlap.sum()),
            "target_MAE_within_source_age_range": float(
                np.abs(prediction[overlap] - truth[overlap]).mean()) if overlap.any() else None,
            "source_age_range": [float(source["ages"].min()), float(source["ages"].max())],
            "target_age_range": [float(truth.min()), float(truth.max())],
            "match": target["match"],
        })
    payload = {"status": "D2_TRANSFER_COMPLETE", "job_id": os.environ.get("SLURM_JOB_ID"),
               "readout": args.readout, "electrodes": len(HA_CHANNELS),
               "montage": list(HA_CHANNELS),
               "left_match": left["match"], "right_match": right["match"],
               "directions": directions,
               "elapsed_minutes": round((time.time() - started) / 60.0, 1)}
    name = args.out or f"transfer_{args.run}_{args.compare}"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{name}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}.json").chmod(0o644)
    return payload
