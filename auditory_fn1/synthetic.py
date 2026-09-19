"""Limited implementation check (plan section 11).

Exactly three mechanisms x four fixed seeds, with M3 and M4 fitted once each = 24
small-model trainings. This is a structural and learnability check. It is NOT a
false-positive-rate certificate, NOT a power analysis, and NOT evidence that any real
clinical effect is detectable.

Acceptance criteria are defined here, before any result is generated:

* The strong-injection criterion is measured against a CLINICAL-ONLY ridge baseline
  fitted on the same training rows, not against the training mean. A mean baseline is
  too weak here: every world carries a clinical signal, so both orders beat a constant
  predictor without using the EEG path at all, and the check would certify nothing
  about the pathway it is meant to exercise. Reduction against the training mean is
  retained as a diagnostic column.
* `segment_mean_drives_target` is a strong injection for BOTH orders: each of M3 and M4
  must reduce test MSE by at least `min_mse_reduction` relative to the clinical-only
  baseline, in at least `min_seeds` of the four seeds.
* `distribution_shape_drives_target` is a strong injection for M4 ONLY, by construction:
  the per-record segment mean is held (near) constant across records, so a mean-then-map
  model cannot see the signal. M4 must meet the same bar; M3's result is recorded
  without a requirement. Passing this does NOT show M4 is better on real data.
* `clinical_sufficient_eeg_independent` sets no "must be negative" guarantee. It checks
  that a no-signal world yields finite output in range. Chance-level small gains are
  recorded, not suppressed.
"""
from __future__ import annotations

import numpy as np

from .models import SetNetwork, TabularTransform, ridge_solution, train_set_network, clip_to_bounds
from .statistics import error_metrics

MECHANISMS = ("clinical_sufficient_eeg_independent", "segment_mean_drives_target", "distribution_shape_drives_target")
STRONG_INJECTION_MECHANISMS = {"segment_mean_drives_target": ("M3", "M4"),
                               "distribution_shape_drives_target": ("M4",)}


def _clinical(rng: np.random.Generator, n: int) -> np.ndarray:
    return np.column_stack([rng.normal(size=n), rng.normal(size=n), rng.uniform(0.0, 1.0, size=n)])


def generate(mechanism: str, seed: int, *, n_identities: int, windows: int, feature_dim: int) -> dict:
    """Build one synthetic world. Targets live on a 0-100 scale like the real ones."""
    rng = np.random.default_rng(int(seed))
    clinical = _clinical(rng, n_identities)
    segments = rng.normal(size=(n_identities, windows, feature_dim))
    clinical_part = 8.0 * clinical[:, 0] - 5.0 * clinical[:, 1]
    if mechanism == "clinical_sufficient_eeg_independent":
        latent = np.zeros(n_identities)
    elif mechanism == "segment_mean_drives_target":
        # A record-level shift of a small feature block; visible to both orders.
        strength = rng.normal(size=n_identities)
        segments[:, :, :8] += strength[:, None, None] * 1.5
        latent = 20.0 * strength
    elif mechanism == "distribution_shape_drives_target":
        # Per-window amplitude regime: each window is drawn high- or low-amplitude with a
        # record-dependent probability, coherently across ALL feature dimensions. The
        # realised per-record mean is then removed exactly, so a mean-then-map model sees
        # an all-zero EEG input for every record while the DISTRIBUTION over windows still
        # differs. A map-then-mean model can see it because a saturating non-linearity
        # responds differently to high- and low-amplitude windows.
        #
        # SYNTHETIC-SCALE CORRECTION (plan section 11 permits one such pass; no real
        # result had been viewed). The first construction placed the asymmetry in 8 of 140
        # dimensions; summing 140 dimensions in the first layer washed it out by the
        # central limit effect and M4 could not learn it either, so the world was not a
        # valid positive control for the order under test. The mechanism is now coherent
        # across dimensions. Neither the models, the optimiser, nor the acceptance
        # criterion were changed.
        shape = rng.uniform(0.0, 1.0, size=n_identities)
        p = 0.15 + 0.70 * shape
        high_amplitude, low_amplitude = 6.0, 0.25
        for i in range(n_identities):
            regime = rng.random(windows) < p[i]
            scale = np.where(regime, high_amplitude, low_amplitude)[:, None]
            segments[i] = scale * rng.normal(size=(windows, feature_dim))
            # Remove the realised mean so the record-level mean is exactly zero.
            segments[i] -= segments[i].mean(axis=0, keepdims=True)
        latent = 20.0 * shape
    else:
        raise ValueError(f"UNKNOWN_SYNTHETIC_MECHANISM:{mechanism}")
    noise = rng.normal(scale=3.0, size=n_identities)
    target = 50.0 + clinical_part + latent + noise
    target = np.clip(target, 0.0, 100.0)
    holdout = rng.permutation(n_identities)
    split = int(round(0.7 * n_identities))
    return {"mechanism": mechanism, "seed": int(seed), "clinical": clinical, "segments": segments,
            "target": target, "train": np.sort(holdout[:split]), "test": np.sort(holdout[split:]),
            "bounds": (0.0, 100.0)}


def run_world(world: dict, order: str, *, steps: int, learning_rate: float, neural_penalty: float,
              clinical_penalty: float) -> dict:
    """Fit one order on one world. Every transform is fitted on training rows only."""
    train, test = world["train"], world["test"]
    lo, hi = world["bounds"]
    scale = hi - lo
    transform = TabularTransform("linear").fit(world["clinical"][train])
    c_train = transform.transform(world["clinical"][train])
    c_test = transform.transform(world["clinical"][test])
    segment_center = world["segments"][train].reshape(-1, world["segments"].shape[2]).mean(axis=0)
    segment_spread = world["segments"][train].reshape(-1, world["segments"].shape[2]).std(axis=0)
    segment_spread = np.where(segment_spread <= 0, 1.0, segment_spread)
    s_train = (world["segments"][train] - segment_center) / segment_spread
    s_test = (world["segments"][test] - segment_center) / segment_spread
    y_train = (world["target"][train] - lo) / scale
    network = SetNetwork(order="mean_then_map" if order == "M3" else "map_then_mean",
                         clinical_dim=c_train.shape[1], seed=int(world["seed"]))
    diagnostics = train_set_network(network, s_train, c_train, y_train, steps=steps,
                                    learning_rate=learning_rate, neural_penalty=neural_penalty,
                                    clinical_penalty=clinical_penalty)
    prediction_scaled, _ = network.forward(s_test, c_test)
    prediction = clip_to_bounds(prediction_scaled * scale + lo, world["bounds"])
    y_test = world["target"][test]
    mean_baseline = np.full(test.size, float(world["target"][train].mean()))
    # Clinical-only reference: the same clinical design, no EEG path. This is what the
    # EEG orders must beat, so the criterion measures the pathway under test.
    coef, intercept = ridge_solution(c_train, world["target"][train], np.full(c_train.shape[1], 0.1))
    clinical_baseline = clip_to_bounds(intercept + (c_test - c_train.mean(axis=0, keepdims=True)) @ coef,
                                       world["bounds"])
    model_mse = float(np.mean((prediction - y_test) ** 2))
    mean_mse = float(np.mean((mean_baseline - y_test) ** 2))
    clinical_mse = float(np.mean((clinical_baseline - y_test) ** 2))
    reduction = 1.0 - model_mse / clinical_mse if clinical_mse > 0 else 0.0
    reduction_vs_mean = 1.0 - model_mse / mean_mse if mean_mse > 0 else 0.0
    return {
        "mechanism": world["mechanism"], "seed": int(world["seed"]), "model": order,
        "parameter_count": network.eeg_parameter_count,
        "test_mse": model_mse, "train_mean_baseline_mse": mean_mse,
        "clinical_only_baseline_mse": clinical_mse,
        "mse_reduction_vs_clinical_baseline": float(reduction),
        "mse_reduction_vs_train_mean": float(reduction_vs_mean),
        "linear_solver_calls": 1,
        "prediction_min": float(prediction.min()), "prediction_max": float(prediction.max()),
        "prediction_finite": bool(np.all(np.isfinite(prediction))),
        **{f"metric_{k}": v for k, v in error_metrics(y_test, prediction).items()},
        **{f"optimizer_{k}": v for k, v in diagnostics.items()},
    }


def run_suite(config_synthetic: dict, model_config: dict, feature_dim: int) -> dict:
    rows: list[dict] = []
    for mechanism in config_synthetic["mechanisms"]:
        for seed in config_synthetic["seeds"]:
            world = generate(mechanism, seed, n_identities=int(config_synthetic["n_identities"]),
                             windows=int(config_synthetic["windows_per_identity"]), feature_dim=feature_dim)
            for order in ("M3", "M4"):
                rows.append(run_world(world, order, steps=int(model_config["optimization_steps"]),
                                      learning_rate=float(model_config["learning_rate"]),
                                      neural_penalty=float(model_config["neural_penalties"][0]),
                                      clinical_penalty=float(model_config["clinical_penalties"][0])))
    threshold = float(config_synthetic["strong_injection_min_mse_reduction"])
    min_seeds = int(config_synthetic["strong_injection_min_seeds"])
    checks = []
    for mechanism, required in STRONG_INJECTION_MECHANISMS.items():
        for order in ("M3", "M4"):
            subset = [r for r in rows if r["mechanism"] == mechanism and r["model"] == order]
            meeting = sum(1 for r in subset if r["mse_reduction_vs_clinical_baseline"] >= threshold)
            checks.append({"mechanism": mechanism, "model": order, "required": order in required,
                           "seeds_meeting_threshold": meeting, "seeds_total": len(subset),
                           "threshold": threshold, "min_seeds": min_seeds,
                           "criterion": "test MSE reduction against a clinical-only ridge baseline",
                           "passed": (meeting >= min_seeds) if order in required else None})
    finite = all(r["prediction_finite"] for r in rows)
    nonfinite_optimizer = [r for r in rows if r.get("optimizer_nonfinite")]
    required_ok = all(c["passed"] for c in checks if c["required"])
    parameter_counts = sorted({r["parameter_count"] for r in rows})
    status = "IMPLEMENTATION_CAPABILITY_ESTABLISHED" if (required_ok and finite and not nonfinite_optimizer) else "IMPLEMENTATION_UNRESOLVED"
    return {
        "status": status,
        "rows": rows,
        "checks": checks,
        "total_neural_fits": len(rows),
        "total_linear_solver_calls": sum(int(r.get("linear_solver_calls", 0)) for r in rows),
        "all_predictions_finite": finite,
        "nonfinite_optimizer_runs": len(nonfinite_optimizer),
        "parameter_counts_observed": parameter_counts,
        "interpretation": ("Structural and learnability check of the fixed implementation. "
                           "Not a false-positive-rate certificate, not a power analysis, and not "
                           "evidence that a real clinical effect is detectable."),
    }
