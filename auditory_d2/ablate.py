"""Where does the developmental information live? Feature-family ablation.

Each family is run alone and left out, at one fixed electrode budget, on the same folds
and with the same nested selection as the main curve, so the numbers sit on the same
scale as everything else in the study.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from auditory_fn1.statistics import paired_identity_bootstrap, shared_draws

from . import channels as channel_tools
from . import spectral
from .budget import identity_folds
from .clinical import _oof_ridge
from .data import RecordStore, record_scale

FAMILIES = tuple(spectral.BAND_NAMES) + ("log_variance", "log_mobility", "log_complexity")
REPETITIONS = 2000


def run_ablate(args, root: Path, private: Path, results: Path) -> dict:
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
    matrices = np.stack([spectral.record_feature_matrix(s, sc, max_windows=args.max_windows)
                         for s, sc in zip(stores, scales)])[:, keep, :]
    ages = np.array([u["age_months"] for u in kept], dtype=float)
    identities = np.array([u["identity"] for u in kept])
    folds = identity_folds(identities, args.folds, args.seed)
    budget = min(args.select_budget, geometry.shape[0])
    subset = channel_tools.farthest_point_subset(geometry, budget, 0)
    block = matrices[:, subset, :]

    def design_for(columns):
        return block[:, :, np.asarray(columns, dtype=int)].reshape(block.shape[0], -1)

    full = _oof_ridge(design_for(range(len(FAMILIES))), ages, identities, folds, args.seed)
    naive = np.full(ages.shape, np.nan)
    for fold in folds:
        naive[fold["test"]] = ages[fold["train"]].mean()
    draws = shared_draws(ages.size, repetitions=REPETITIONS, seed=args.seed)

    rows = []
    for index, family in enumerate(FAMILIES):
        alone = _oof_ridge(design_for([index]), ages, identities, folds, args.seed)
        without = _oof_ridge(design_for([i for i in range(len(FAMILIES)) if i != index]),
                             ages, identities, folds, args.seed)
        alone_gain = paired_identity_bootstrap(np.abs(naive - ages), np.abs(alone - ages),
                                               repetitions=REPETITIONS, seed=args.seed,
                                               draws=draws)
        drop = paired_identity_bootstrap(np.abs(without - ages), np.abs(full - ages),
                                         repetitions=REPETITIONS, seed=args.seed, draws=draws)
        rows.append({"family": family,
                     "alone_MAE": float(np.abs(alone - ages).mean()),
                     "alone_gain_over_naive": alone_gain["gain_MAE"],
                     "alone_gain_ci": [alone_gain["ci_low"], alone_gain["ci_high"]],
                     "without_MAE": float(np.abs(without - ages).mean()),
                     "unique_contribution": drop["gain_MAE"],
                     "unique_contribution_ci": [drop["ci_low"], drop["ci_high"]]})

    payload = {"run": args.run, "arm": "ablate", "status": "D2_ABLATE_COMPLETE",
               "job_id": os.environ.get("SLURM_JOB_ID"), "electrodes": int(budget),
               "n_records": len(kept), "families": list(FAMILIES),
               "naive_mean_MAE": float(np.abs(naive - ages).mean()),
               "full_model_MAE": float(np.abs(full - ages).mean()),
               "repetitions": REPETITIONS, "interval": "percentile",
               "rows": rows, "elapsed_minutes": round((time.time() - started) / 60.0, 1)}
    name = args.out or f"{args.run}_ablate_{budget}"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{name}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}.json").chmod(0o644)
    return payload
