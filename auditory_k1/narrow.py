"""The five narrow checks the route review requires before the real K1 matrix.

Review section 5.3. These are pathway-capability checks on a fixed implementation, not
a false-positive rate, not clinical power, and not a statistical gate on hundreds of
worlds.
"""
from __future__ import annotations

import numpy as np

from auditory_fn1.models import LOCAL_DIMS, SetNetwork, TabularTransform, clip_to_bounds, ridge_solution
from auditory_fn1.synthetic import generate

from .profiled import ClinicalBlock, predict, profiled_gradient_check, profiled_objective, train_profiled


def check_zero_eeg_reproduces_m1(seed: int = 3, n: int = 41, p: int = 6, alpha: float = 1.0,
                                 bounds: tuple[float, float] = (0.0, 100.0)) -> dict:
    """Check 1: with f_theta == 0 the profiled solution IS the M1 ridge solution.

    K1 works on y' = (y - lo)/span with penalty alpha/n on a mean objective; M1 works on
    y with penalty alpha on a sum objective. Dividing the ridge objective by n*span^2
    shows the two are the same problem, so the predictions must agree exactly after
    rescaling.
    """
    rng = np.random.default_rng(seed)
    design = rng.normal(size=(n, p))
    y = bounds[0] + (bounds[1] - bounds[0]) * rng.random(n)
    span = bounds[1] - bounds[0]
    # M1 reference in source units.
    coef, intercept = ridge_solution(design, y, np.full(p, alpha))
    centre = design.mean(axis=0, keepdims=True)
    m1 = intercept + (design - centre) @ coef
    # K1 with the EEG readout left at its zero initialisation.
    network = SetNetwork(order="map_then_mean", clinical_dim=0, seed=11)
    assert np.allclose(network.params["w"], 0.0), "the EEG readout must initialise to zero"
    segments = rng.normal(size=(n, 4, LOCAL_DIMS[0]))
    block = ClinicalBlock.fit(design, alpha)
    state = profiled_objective(network, block, segments, design, (y - bounds[0]) / span, neural_penalty=0.1)
    k1 = predict(network, block, state["gamma"], state["intercept"], segments, design) * span + bounds[0]
    difference = float(np.max(np.abs(k1 - m1)))
    return {"check": "zero_eeg_reproduces_M1", "max_abs_difference_source_units": difference,
            "passed": difference <= 1e-9, "n": n, "alpha": alpha,
            "eeg_output_abs_max": float(np.max(np.abs(state["eeg_output"])))}


def check_constant_eeg_moves_only_the_intercept(seed: int = 4, n: int = 41, p: int = 6,
                                                alpha: float = 1.0, constant: float = 0.37) -> dict:
    """Check 2: a constant f shifts b* and nothing else; no new clinical direction appears."""
    rng = np.random.default_rng(seed)
    design = rng.normal(size=(n, p))
    y = rng.random(n)
    segments = rng.normal(size=(n, 4, LOCAL_DIMS[0]))
    block = ClinicalBlock.fit(design, alpha)
    base = SetNetwork(order="map_then_mean", clinical_dim=0, seed=11)
    zero_state = profiled_objective(base, block, segments, design, y, neural_penalty=0.0)
    shifted = SetNetwork(order="map_then_mean", clinical_dim=0, seed=11)
    # W1 = 0 and W2 = 0 make phi constant at b2; w picks it up as a constant output.
    shifted.params["W1"] = np.zeros_like(shifted.params["W1"])
    shifted.params["W2"] = np.zeros_like(shifted.params["W2"])
    shifted.params["b2"] = np.full(LOCAL_DIMS[2], constant / LOCAL_DIMS[2])
    shifted.params["w"] = np.ones(LOCAL_DIMS[2])
    shift_state = profiled_objective(shifted, block, segments, design, y, neural_penalty=0.0)
    gamma_difference = float(np.max(np.abs(shift_state["gamma"] - zero_state["gamma"])))
    intercept_difference = float(shift_state["intercept"] - zero_state["intercept"])
    prediction_zero = predict(base, block, zero_state["gamma"], zero_state["intercept"], segments, design)
    prediction_shift = predict(shifted, block, shift_state["gamma"], shift_state["intercept"], segments, design)
    prediction_difference = float(np.max(np.abs(prediction_shift - prediction_zero)))
    observed_constant = float(np.mean(shift_state["eeg_output"]))
    return {"check": "constant_eeg_moves_only_the_intercept",
            "constant_applied": observed_constant,
            "max_abs_gamma_change": gamma_difference,
            "intercept_change": intercept_difference,
            "expected_intercept_change": -observed_constant,
            "max_abs_prediction_change": prediction_difference,
            "passed": (gamma_difference <= 1e-10 and prediction_difference <= 1e-10
                       and abs(intercept_difference + observed_constant) <= 1e-10)}


def _world_run(mechanism: str, seed: int, order: str, *, steps: int, learning_rate: float,
               neural_penalty: float, alpha: float, n_identities: int, windows: int) -> dict:
    world = generate(mechanism, seed, n_identities=n_identities, windows=windows,
                     feature_dim=LOCAL_DIMS[0])
    train, test = world["train"], world["test"]
    lo, hi = world["bounds"]
    span = hi - lo
    transform = TabularTransform("linear").fit(world["clinical"][train])
    design_train = transform.transform(world["clinical"][train])
    design_test = transform.transform(world["clinical"][test])
    centre = world["segments"][train].reshape(-1, LOCAL_DIMS[0]).mean(axis=0)
    spread = world["segments"][train].reshape(-1, LOCAL_DIMS[0]).std(axis=0)
    spread = np.where(spread <= 0, 1.0, spread)
    segments_train = (world["segments"][train] - centre) / spread
    segments_test = (world["segments"][test] - centre) / spread
    y_train = (world["target"][train] - lo) / span
    y_test = world["target"][test]

    block = ClinicalBlock.fit(design_train, alpha)
    network = SetNetwork(order="mean_then_map" if order == "M3" else "map_then_mean",
                         clinical_dim=0, seed=int(seed))
    diagnostics = train_profiled(network, block, segments_train, design_train, y_train,
                                 steps=steps, learning_rate=learning_rate, neural_penalty=neural_penalty)
    prediction = clip_to_bounds(
        predict(network, block, diagnostics["gamma"], diagnostics["intercept"], segments_test, design_test)
        * span + lo, world["bounds"])
    # Clinical-only reference under the SAME profiled objective, EEG held at zero.
    frozen = SetNetwork(order="map_then_mean", clinical_dim=0, seed=int(seed))
    clinical_block = ClinicalBlock.fit(design_train, alpha)
    clinical_state = profiled_objective(frozen, clinical_block, segments_train, design_train, y_train,
                                        neural_penalty=neural_penalty)
    clinical_prediction = clip_to_bounds(
        predict(frozen, clinical_block, clinical_state["gamma"], clinical_state["intercept"],
                segments_test, design_test) * span + lo, world["bounds"])
    mean_prediction = np.full(test.size, float(world["target"][train].mean()))
    model_mse = float(np.mean((prediction - y_test) ** 2))
    clinical_mse = float(np.mean((clinical_prediction - y_test) ** 2))
    mean_mse = float(np.mean((mean_prediction - y_test) ** 2))
    return {
        "mechanism": mechanism, "seed": int(seed), "model": order,
        "test_MAE": float(np.mean(np.abs(prediction - y_test))),
        "clinical_only_test_MAE": float(np.mean(np.abs(clinical_prediction - y_test))),
        "test_mse": model_mse, "clinical_only_mse": clinical_mse, "train_mean_mse": mean_mse,
        "mse_reduction_vs_clinical_baseline": float(1.0 - model_mse / clinical_mse) if clinical_mse else 0.0,
        "mse_reduction_vs_train_mean": float(1.0 - model_mse / mean_mse) if mean_mse else 0.0,
        "prediction_finite": bool(np.all(np.isfinite(prediction))),
        **{f"optimizer_{k}": v for k, v in diagnostics.items() if k not in ("gamma", "intercept")},
    }


def pathway_worlds(model_config: dict, *, alpha: float = 1.0, seeds=(101, 102, 103, 104),
                   n_identities: int = 40, windows: int = 32) -> dict:
    """Checks 4 and 5: measure against the CLINICAL baseline, not only the mean."""
    rows = []
    for mechanism in ("clinical_sufficient_eeg_independent", "segment_mean_drives_target",
                      "distribution_shape_drives_target"):
        for seed in seeds:
            for order in ("M3", "M4"):
                rows.append(_world_run(mechanism, seed, order,
                                       steps=int(model_config["optimization_steps"]),
                                       learning_rate=float(model_config["learning_rate"]),
                                       neural_penalty=float(model_config["neural_penalties"][0]),
                                       alpha=alpha, n_identities=n_identities, windows=windows))
    summary = []
    for mechanism in ("clinical_sufficient_eeg_independent", "segment_mean_drives_target",
                      "distribution_shape_drives_target"):
        for order in ("M3", "M4"):
            subset = [r for r in rows if r["mechanism"] == mechanism and r["model"] == order]
            values = [r["mse_reduction_vs_clinical_baseline"] for r in subset]
            summary.append({"mechanism": mechanism, "model": order, "seeds": len(subset),
                            "median_reduction_vs_clinical_baseline": float(np.median(values)),
                            "seeds_with_any_gain_over_clinical": int(sum(v > 0 for v in values))})
    return {"rows": rows, "summary": summary,
            "criterion": ("Reported against the clinical-only baseline under the same profiled "
                          "objective, which is what isolates the EEG pathway. A mean-relative number "
                          "cannot do that because every world carries a clinical signal."),
            "interpretation": ("Pathway capability of a fixed implementation. Not a false-positive rate, "
                               "not clinical power, and not evidence about the archive.")}


def run_all(model_config: dict) -> dict:
    checks = [check_zero_eeg_reproduces_m1(), check_constant_eeg_moves_only_the_intercept()]
    gradient = profiled_gradient_check()
    worlds = pathway_worlds(model_config)
    passed = all(c["passed"] for c in checks) and gradient["status"] == "GRADIENT_VERIFIED" \
        and all(r["prediction_finite"] for r in worlds["rows"])
    return {"status": "NARROW_CHECKS_PASSED" if passed else "NARROW_CHECKS_FAILED",
            "exactness_checks": checks, "gradient_check": gradient, "worlds": worlds,
            "world_fits": len(worlds["rows"])}
