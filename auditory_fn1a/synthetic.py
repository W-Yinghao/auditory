"""Limited implementation check for FN1-A (plan section 11).

Three mechanisms x four seeds, M3 and M4 fitted once each = 24 small-network trainings.
The generators are reused from auditory_fn1.synthetic, including the corrected
distribution-shape world.

Acceptance criterion, transcribed from the plan: "强均值机制要求两模型各至少3/4个seed
相对均值预测降低MSE至少50%；分布机制要求M4满足对应可学习性". The reference is therefore
the TRAINING-MEAN prediction, and that is what decides pass or fail here.

DISCLOSED CAVEAT, reported in every row rather than silently corrected: every synthetic
world also carries a clinical signal, so a model can clear a mean-relative bar using the
clinical branch alone without the EEG path contributing anything. The mean-relative
number is therefore not, on its own, evidence about the pathway under test. The
reduction against a clinical-only ridge baseline is computed and reported alongside as
a diagnostic. The plan's criterion is not substituted; both numbers are published.
"""
from __future__ import annotations

import numpy as np

from auditory_fn1.synthetic import generate, run_world

MECHANISMS = ("clinical_sufficient_eeg_independent", "segment_mean_drives_target",
              "distribution_shape_drives_target")
REQUIRED = {"segment_mean_drives_target": ("M3", "M4"),
            "distribution_shape_drives_target": ("M4",)}


def run_suite(config_synthetic: dict, model_config: dict, feature_dim: int) -> dict:
    reference = str(config_synthetic.get("reference_for_criterion", "train_mean_prediction"))
    if reference != "train_mean_prediction":
        raise ValueError(f"UNEXPECTED_CRITERION_REFERENCE:{reference}")
    rows: list[dict] = []
    for mechanism in config_synthetic["mechanisms"]:
        for seed in config_synthetic["seeds"]:
            world = generate(mechanism, seed, n_identities=int(config_synthetic["n_identities"]),
                             windows=int(config_synthetic["windows_per_identity"]), feature_dim=feature_dim)
            for order in ("M3", "M4"):
                row = run_world(world, order, steps=int(model_config["optimization_steps"]),
                                learning_rate=float(model_config["learning_rate"]),
                                neural_penalty=float(model_config["neural_penalties"][0]),
                                clinical_penalty=float(model_config["clinical_penalties"][0]))
                row["criterion_reference"] = reference
                row["criterion_value"] = row["mse_reduction_vs_train_mean"]
                rows.append(row)

    threshold = float(config_synthetic["strong_injection_min_mse_reduction"])
    min_seeds = int(config_synthetic["strong_injection_min_seeds"])
    checks = []
    for mechanism, required in REQUIRED.items():
        for order in ("M3", "M4"):
            subset = [r for r in rows if r["mechanism"] == mechanism and r["model"] == order]
            meeting = sum(1 for r in subset if r["criterion_value"] >= threshold)
            diagnostic = sum(1 for r in subset if r["mse_reduction_vs_clinical_baseline"] >= threshold)
            checks.append({
                "mechanism": mechanism, "model": order, "required": order in required,
                "criterion_reference": reference, "threshold": threshold, "min_seeds": min_seeds,
                "seeds_meeting_threshold": meeting, "seeds_total": len(subset),
                "passed": (meeting >= min_seeds) if order in required else None,
                "diagnostic_seeds_meeting_against_clinical_baseline": diagnostic,
            })
    finite = all(r["prediction_finite"] for r in rows)
    nonfinite = [r for r in rows if r.get("optimizer_nonfinite")]
    required_ok = all(c["passed"] for c in checks if c["required"])
    status = ("IMPLEMENTATION_CAPABILITY_ESTABLISHED"
              if (required_ok and finite and not nonfinite) else "IMPLEMENTATION_UNRESOLVED")
    return {
        "status": status,
        "rows": rows,
        "checks": checks,
        "total_neural_fits": len(rows),
        "total_linear_solver_calls": sum(int(r.get("linear_solver_calls", 0)) for r in rows),
        "all_predictions_finite": finite,
        "nonfinite_optimizer_runs": len(nonfinite),
        "parameter_counts_observed": sorted({r["parameter_count"] for r in rows}),
        "criterion": {
            "reference": reference,
            "plan_clause": "section 11: at least 3 of 4 seeds must reduce MSE by 50% against the mean prediction",
            "disclosed_caveat": ("Every synthetic world carries a clinical signal, so a model can clear a "
                                 "mean-relative bar through the clinical branch alone. The mean-relative "
                                 "number is not by itself evidence about the EEG pathway. The reduction "
                                 "against a clinical-only ridge baseline is reported per row and per check "
                                 "as a diagnostic; the plan's criterion was implemented as written and not "
                                 "substituted."),
        },
        "interpretation": ("Implementation learnability and numerical check. Not a false-positive-rate "
                           "certificate, not a power analysis, and not evidence that any archival effect "
                           "is detectable."),
    }
