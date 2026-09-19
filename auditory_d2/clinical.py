"""The clinical layer: does the decoded developmental axis carry device-related signal?

Two questions are kept apart on purpose.

1. Can EEG predict a clinical variable at all, out of fold?
2. Does it predict it BEYOND chronological age? A model of hearing history that merely
   rediscovers age is not a finding, and the published criticism of brain-age gaps is
   precisely that a clinical difference need not be an age-like difference. The
   increment over an age-only model is therefore reported next to every raw result.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from auditory_fn1.statistics import paired_identity_bootstrap, shared_draws

from . import spectral
from . import train as train_tools
from .budget import identity_folds
from .data import RecordStore, record_scale
from .ridge_budget import PENALTIES, _ridge

REPETITIONS = 2000


def _oof_ridge(design, target, identities, folds, seed):
    predicted = np.full(target.shape, np.nan)
    for fold in folds:
        train_idx, test_idx = fold["train"], fold["test"]
        inner = identity_folds(identities[train_idx],
                               min(3, max(2, len(train_idx) // 8)), seed + 7)
        scored = {}
        for penalty in PENALTIES:
            errors = []
            for part in inner:
                a, b = train_idx[part["train"]], train_idx[part["test"]]
                if b.size == 0:
                    continue
                errors.append(_ridge(design[a], target[a], design[b], penalty) - target[b])
            if errors:
                scored[penalty] = float(np.mean(np.concatenate(errors) ** 2))
        penalty = min(scored, key=scored.get)
        predicted[test_idx] = _ridge(design[train_idx], target[train_idx],
                                     design[test_idx], penalty)
    return predicted


def run_clinical(args, root: Path, private: Path, results: Path) -> dict:
    started = time.time()
    cohort = json.loads((private / f"{args.run}_cohort.json").read_text())
    layouts = json.loads((private / f"{args.run}_geometry.json").read_text())
    layout_hash = str(cohort["units"][0]["layout_hash"])
    layout = layouts[layout_hash]
    keep = np.array([i for i, p in enumerate(layout["xyz_m"]) if p is not None], dtype=int)

    stores, scales, kept = [], [], []
    for unit in cohort["units"]:
        store = RecordStore(root, args.run, unit["container_id"],
                            max_bad_fraction=args.max_bad_fraction, preload=False)
        if store.starts.size < args.min_windows:
            continue
        stores.append(store)
        scales.append(record_scale(store))
        kept.append(unit)
    matrices = np.stack([spectral.record_feature_matrix(s, sc, max_windows=args.max_windows)
                         for s, sc in zip(stores, scales)])[:, keep, :]
    design = matrices.reshape(matrices.shape[0], -1)
    ages = np.array([u["age_months"] for u in kept], dtype=float)
    identities = np.array([u["identity"] for u in kept])
    folds = identity_folds(identities, args.folds, args.seed)

    predicted_age = _oof_ridge(design, ages, identities, folds, args.seed)
    gap = predicted_age - ages

    # Age-bias correction. An imperfect decoder regresses towards the cohort mean, so the
    # raw gap is negatively correlated with age by construction and any variable that
    # grows with age will correlate with it spuriously. The correction slope is fitted on
    # the training fold only and applied to the held-out children.
    corrected_gap = np.full(gap.shape, np.nan)
    slopes = []
    for fold in folds:
        train_idx, test_idx = fold["train"], fold["test"]
        design_age = np.column_stack([np.ones(train_idx.size), ages[train_idx]])
        coefficients, *_ = np.linalg.lstsq(design_age, gap[train_idx], rcond=None)
        slopes.append({"fold": int(fold["fold"]), "intercept": float(coefficients[0]),
                       "slope_per_month": float(coefficients[1])})
        corrected_gap[test_idx] = gap[test_idx] - (coefficients[0]
                                                   + coefficients[1] * ages[test_idx])

    targets = [name for name in ("duration", "unaided", "aided", "A", "V", "CAP", "SIR")
               if any(name in u for u in kept)]
    findings = []
    for name in targets:
        values = np.array([float(u.get(name, np.nan)) for u in kept], dtype=float)
        mask = np.isfinite(values)
        if mask.sum() < 25:
            findings.append({"target": name, "status": "INSUFFICIENT_OBSERVED",
                             "n": int(mask.sum())})
            continue
        sub_identities = identities[mask]
        sub_folds = identity_folds(sub_identities, args.folds, args.seed)
        y = values[mask]
        eeg = _oof_ridge(design[mask], y, sub_identities, sub_folds, args.seed)
        age_only = _oof_ridge(ages[mask][:, None], y, sub_identities, sub_folds, args.seed)
        joint = _oof_ridge(np.column_stack([design[mask], ages[mask]]), y,
                           sub_identities, sub_folds, args.seed)
        naive = np.full(y.shape, np.nan)
        for fold in sub_folds:
            naive[fold["test"]] = y[fold["train"]].mean()
        draws = shared_draws(int(mask.sum()), repetitions=REPETITIONS, seed=args.seed)
        against_naive = paired_identity_bootstrap(np.abs(naive - y), np.abs(eeg - y),
                                                  repetitions=REPETITIONS, seed=args.seed,
                                                  draws=draws)
        beyond_age = paired_identity_bootstrap(np.abs(age_only - y), np.abs(joint - y),
                                               repetitions=REPETITIONS, seed=args.seed,
                                               draws=draws)
        correlation = float(np.corrcoef(gap[mask], y)[0, 1])
        corrected = corrected_gap[mask]
        usable = np.isfinite(corrected)
        corrected_correlation = (float(np.corrcoef(corrected[usable], y[usable])[0, 1])
                                 if usable.sum() > 3 else None)
        if corrected_correlation is not None:
            difference = corrected[usable] - corrected[usable].mean()
            centred_y = y[usable] - y[usable].mean()
            draws_correlation = shared_draws(int(usable.sum()), repetitions=REPETITIONS,
                                             seed=args.seed + 3)
            replicates = np.array([
                float(np.corrcoef(difference[index], centred_y[index])[0, 1])
                for index in draws_correlation[:400]])
            replicates = replicates[np.isfinite(replicates)]
            correlation_ci = [float(np.quantile(replicates, 0.025)),
                              float(np.quantile(replicates, 0.975))] if replicates.size else None
        else:
            correlation_ci = None
        findings.append({
            "target": name, "status": "EVALUATED", "n": int(mask.sum()),
            "naive_MAE": float(np.abs(naive - y).mean()),
            "age_only_MAE": float(np.abs(age_only - y).mean()),
            "eeg_only_MAE": float(np.abs(eeg - y).mean()),
            "eeg_plus_age_MAE": float(np.abs(joint - y).mean()),
            "eeg_gain_over_naive": against_naive["gain_MAE"],
            "eeg_gain_over_naive_ci": [against_naive["ci_low"], against_naive["ci_high"]],
            "increment_over_age_only": beyond_age["gain_MAE"],
            "increment_over_age_only_ci": [beyond_age["ci_low"], beyond_age["ci_high"]],
            "age_gap_correlation_raw": correlation,
            "age_gap_correlation_bias_corrected": corrected_correlation,
            "age_gap_correlation_bias_corrected_ci": correlation_ci,
        })

    payload = {
        "run": args.run, "arm": "clinical", "status": "D2_CLINICAL_COMPLETE",
        "job_id": os.environ.get("SLURM_JOB_ID"), "n_records": len(kept),
        "n_identities": int(len(set(identities.tolist()))),
        "electrodes": int(keep.size), "n_features": int(design.shape[1]),
        "age_decoder": {
            "MAE_months": float(np.abs(gap).mean()),
            "naive_MAE_months": float(np.abs(ages - ages.mean()).mean()),
            "gap_mean_months": float(gap.mean()), "gap_sd_months": float(gap.std(ddof=1)),
            "gap_vs_age_correlation": float(np.corrcoef(gap, ages)[0, 1]),
            "corrected_gap_vs_age_correlation": float(np.corrcoef(
                corrected_gap[np.isfinite(corrected_gap)],
                ages[np.isfinite(corrected_gap)])[0, 1]),
            "bias_correction_slopes": slopes,
        },
        "repetitions": REPETITIONS, "interval": "percentile",
        "scope": "fixed_oof_identity_paired_not_pipeline_refit",
        "findings": findings,
        "elapsed_minutes": round((time.time() - started) / 60.0, 1),
    }
    name = args.out or f"{args.run}_clinical"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{name}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}.json").chmod(0o644)
    (private / f"{name}_gap.json").write_text(json.dumps(
        {"identities": identities.tolist(), "ages": ages.tolist(),
         "predicted_age": predicted_age.tolist(),
         "corrected_gap": corrected_gap.tolist()}, indent=2) + "\n")
    (private / f"{name}_gap.json").chmod(0o600)
    return payload
