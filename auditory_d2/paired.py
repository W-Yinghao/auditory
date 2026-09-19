"""Paired analysis of the channel-budget curve.

Every budget is evaluated on the SAME children in the SAME folds, so comparing budgets
by their independent means throws away the pairing and buries the effect in
between-child variance. This module compares them as paired per-child absolute errors,
with the identity-level bootstrap already verified in `auditory_fn1.statistics`, and one
shared resampling index set so all contrasts on the curve are mutually comparable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from auditory_fn1.statistics import (leave_one_identity_range, paired_identity_bootstrap,
                                     shared_draws)

REPETITIONS = 2000


def load(private: Path, name: str) -> dict:
    return json.loads((private / f"{name}_predictions.json").read_text())


def variant_mean_absolute_error(payload: dict, budget: int) -> np.ndarray:
    """Per-child absolute error, averaged over the electrode-subset variants."""
    ages = np.asarray(payload["ages"], dtype=float)
    keys = [k for k in payload["predictions"] if k.startswith(f"b{budget}_v")]
    if not keys:
        raise KeyError(f"D2_NO_PREDICTIONS_FOR_BUDGET:{budget}")
    errors = np.stack([np.abs(np.asarray(payload["predictions"][k], dtype=float) - ages)
                       for k in keys])
    return errors.mean(axis=0)


def run_paired(args, root: Path, private: Path, results: Path) -> dict:
    payload = load(private, args.out or f"{args.run}_ridge_budget")
    ages = np.asarray(payload["ages"], dtype=float)
    budgets = sorted({int(k.split("_")[0][1:]) for k in payload["predictions"]})
    absolute = {b: variant_mean_absolute_error(payload, b) for b in budgets}
    finite = np.all([np.isfinite(v) for v in absolute.values()], axis=0)
    n = int(finite.sum())
    draws = shared_draws(n, repetitions=REPETITIONS, seed=args.seed)

    naive = float(np.abs(ages[finite] - ages[finite].mean()).mean())
    reference = min(budgets)
    top = max(budgets)
    contrasts = []
    for budget in budgets:
        if budget == reference:
            continue
        result = paired_identity_bootstrap(absolute[reference][finite], absolute[budget][finite],
                                           repetitions=REPETITIONS, seed=args.seed, draws=draws)
        influence = leave_one_identity_range(absolute[reference][finite], absolute[budget][finite])
        contrasts.append({"comparison": f"{reference}_to_{budget}_electrodes",
                          "reference_electrodes": reference, "candidate_electrodes": budget,
                          "meaning": "months of mean absolute age error removed by the extra electrodes",
                          **result, "loo_min": influence["min"], "loo_max": influence["max"]})
    steps = []
    for lower, upper in zip(budgets[:-1], budgets[1:]):
        result = paired_identity_bootstrap(absolute[lower][finite], absolute[upper][finite],
                                           repetitions=REPETITIONS, seed=args.seed, draws=draws)
        steps.append({"comparison": f"{lower}_to_{upper}_electrodes", "from": lower, "to": upper,
                      "gain_MAE": result["gain_MAE"], "ci_low": result["ci_low"],
                      "ci_high": result["ci_high"], "status": result["status"]})
    saturation = [s for s in steps if s["ci_low"] is not None and s["ci_low"] <= 0.0 <= s["ci_high"]]
    first_flat = saturation[0]["from"] if saturation else None

    summary = {
        "run": args.run, "source": args.out or f"{args.run}_ridge_budget",
        "job_id": os.environ.get("SLURM_JOB_ID"), "status": "D2_PAIRED_COMPLETE",
        "n_identity_groups": n, "repetitions": REPETITIONS, "interval": "percentile",
        "scope": "fixed_oof_identity_paired_not_pipeline_refit",
        "naive_mean_MAE_months": naive,
        "per_budget_MAE_months": {str(b): float(absolute[b][finite].mean()) for b in budgets},
        "contrasts_against_smallest_budget": contrasts,
        "adjacent_steps": steps,
        "first_step_whose_interval_includes_zero": first_flat,
        "largest_budget": top,
    }
    name = (args.out or f"{args.run}_ridge_budget") + "_paired"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{name}.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}.json").chmod(0o644)
    return summary


def run_compare(args, root: Path, private: Path, results: Path) -> dict:
    """Paired comparison of two readouts evaluated on the same children and folds.

    The question is not which readout wins overall but WHERE it wins: if a nonlinear
    readout only shortens the climb and leaves the plateau where it was, the plateau is
    a property of the signal rather than of the estimator.
    """
    left = load(private, args.out)
    right = load(private, args.compare)
    if left["ages"] != right["ages"] or left["identities"] != right["identities"]:
        raise ValueError("D2_COMPARE_COHORT_MISMATCH")
    budgets = sorted({int(k.split("_")[0][1:]) for k in left["predictions"]}
                     & {int(k.split("_")[0][1:]) for k in right["predictions"]})
    contrasts = []
    for budget in budgets:
        a = variant_mean_absolute_error(left, budget)
        b = variant_mean_absolute_error(right, budget)
        finite = np.isfinite(a) & np.isfinite(b)
        draws = shared_draws(int(finite.sum()), repetitions=REPETITIONS, seed=args.seed)
        result = paired_identity_bootstrap(a[finite], b[finite], repetitions=REPETITIONS,
                                           seed=args.seed, draws=draws)
        contrasts.append({"budget": budget, "n_electrodes": budget,
                          "reference_MAE": float(a[finite].mean()),
                          "candidate_MAE": float(b[finite].mean()),
                          "gain_MAE": result["gain_MAE"], "ci_low": result["ci_low"],
                          "ci_high": result["ci_high"],
                          "interval_includes_zero": bool(result["ci_low"] <= 0 <= result["ci_high"])})
    summary = {"run": args.run, "reference": args.out, "candidate": args.compare,
               "job_id": os.environ.get("SLURM_JOB_ID"), "status": "D2_COMPARE_COMPLETE",
               "meaning": "positive gain = candidate readout has the smaller error",
               "repetitions": REPETITIONS, "interval": "percentile",
               "n_identity_groups": int(len(left["ages"])), "contrasts": contrasts}
    results.mkdir(parents=True, exist_ok=True)
    name = f"{args.out}_vs_{args.compare}"
    (results / f"{name}.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}.json").chmod(0o644)
    return summary
