"""Exactly 15 P0 synthetic worlds / 30 heads, plus two identity-test heads."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .linear import WeightedScaler, WeightedPCA, fit_logistic, require_slurm
from .statistics import hierarchical_weights, weighted_metrics
from .pca_packet import p0_algorithm_hash, orthogonal_equivalence


WORLD_NAMES = ("LOW_VARIANCE_SIGNAL", "TOP_PCA_SIGNAL", "NULL")
EVALUATION_SEED_START = 51001


def _metadata(n_groups, offset=0):
    return pd.DataFrame([{"split_group_id": f"synthetic_{g+offset:03d}",
                          "A_half": half, "previous_code": "known",
                          "previous_run_bin": "one", "stimulus_local_id": label}
                         for g in range(n_groups) for half in (0, 1)
                         for label in (0, 1) for _ in range(20)])


def _world_features(metadata, rng, mechanism):
    y = metadata.stimulus_local_id.to_numpy()
    n = len(metadata)
    background = rng.normal(size=(n, 12))
    if mechanism == "TOP_PCA_SIGNAL":
        # The signal drives four correlated coordinate pairs. Thus its leading
        # standardized eigenvalue is near eight, above the remaining pairwise
        # backgrounds near two. A single pair would not ensure top-PC placement
        # after per-coordinate scaling in a finite sample.
        signal = 2.0 * (2 * y - 1) + .5 * rng.normal(size=n)
        background[:, :4] = signal[:, None] + .15 * rng.normal(size=(n, 4))
    left = background + .03 * rng.normal(size=(n, 12))
    right = background + .03 * rng.normal(size=(n, 12))
    if mechanism == "LOW_VARIANCE_SIGNAL":
        # Standardizing individual coordinates leaves this antisymmetric
        # direction low variance relative to 12 correlated background axes.
        signal = .35 * (2 * y - 1) + .06 * rng.normal(size=n)
        left[:, 0] += signal
        right[:, 0] -= signal
    X = np.empty((n, 24))
    X[:, ::2], X[:, 1::2] = left, right
    return X


def run_p0_capability(*, ledger=None, context=None, development_revision=0):
    require_slurm()
    if development_revision not in (0, 1):
        raise ValueError("At most one capability development revision is authorized")
    # A revision is an explicitly recorded new evaluation bank, never reuse.
    first_seed = EVALUATION_SEED_START + 1000 * development_revision
    train_frame, test_frame = _metadata(20), _metadata(10, 20)
    train_weights, test_weights = (hierarchical_weights(f) for f in (train_frame, test_frame))
    train_y, test_y = (f.stimulus_local_id.to_numpy() for f in (train_frame, test_frame))
    records, diagnostics, identities = [], [], []
    for mechanism_index, mechanism in enumerate(WORLD_NAMES):
        for repetition in range(5):
            seed = first_seed + mechanism_index * 5 + repetition
            rng = np.random.default_rng(seed)
            train_X = _world_features(train_frame, rng, mechanism)
            test_X = _world_features(test_frame, rng, mechanism)
            scaler = WeightedScaler().fit(train_X, train_weights)
            train_U, test_U = scaler.transform(train_X), scaler.transform(test_X)
            pca = WeightedPCA().fit(train_U, train_weights)
            train_views, test_views = pca.views(train_U), pca.views(test_U)
            models, scores = {}, {}
            for view in ("FULL", "PC8"):
                fit_context = dict(context or {}, packet="P0", fit_kind="capability", mechanism=mechanism,
                                   seed=seed, view=view, lambda_l2=.01)
                fit = fit_logistic(train_views[view], train_y, train_weights, .01,
                                   ledger=ledger, context=fit_context)
                models[view] = fit
                scores[view] = weighted_metrics(test_y, fit.predict_proba(test_views[view]), test_weights)
                diagnostics.append(dict(fit_context, **fit.diagnostics))
            complete = all(s["status"] == "PASS" for s in scores.values())
            row = {"mechanism": mechanism, "repetition": repetition, "seed": seed,
                   "status": "PASS" if complete else "NUMERICAL_FAIL", "rank": pca.rank_,
                   "gain_pc8_minus_full": scores["PC8"]["ce_bits"] - scores["FULL"]["ce_bits"] if complete else None,
                   "full_ce_bits": scores["FULL"]["ce_bits"], "pc8_ce_bits": scores["PC8"]["ce_bits"],
                   "full_bacc": scores["FULL"]["bacc"], "pc8_bacc": scores["PC8"]["bacc"]}
            records.append(row)
            if mechanism_index == 0 and repetition == 0:
                # Explicitly outside the 30-world-head denominator; both
                # optimizer invocations still pass through the global ledger.
                for control, source_view, train_control, test_control in (
                    ("FULL_ORTHOGONAL", "FULL", pca.transform(train_U), pca.transform(test_U)),
                    ("PC8_DUP", "PC8", train_views["PC8_DUP"], test_views["PC8_DUP"])):
                    fit_context = dict(context or {}, packet="P0", fit_kind="equivalence_test",
                                       control=control, seed=seed, lambda_l2=.01)
                    model = fit_logistic(train_control, train_y, train_weights, .01,
                                         ledger=ledger, context=fit_context)
                    diagnostics.append(dict(fit_context, **model.diagnostics))
                    maximum = float(np.max(np.abs(model.predict_proba(test_control)
                                     - models[source_view].predict_proba(test_views[source_view]))))
                    source_objective = models[source_view].diagnostics["final_objective"]
                    difference = (abs(model.diagnostics["final_objective"] - source_objective)
                                  if model.success and models[source_view].success else np.nan)
                    identities.append({"control": control, "prediction_max_abs": maximum if np.isfinite(maximum) else None,
                        "objective_abs_difference": float(difference) if np.isfinite(difference) else None,
                        "status": "PASS" if np.isfinite(maximum) and maximum <= 2e-5 and difference <= 2e-8 else "FAIL"})
                identities.append(dict(control="FULL_TRANSPORT", **orthogonal_equivalence(models["FULL"], test_U, pca)))
    low = [r for r in records if r["mechanism"] == "LOW_VARIANCE_SIGNAL"]
    top = [r for r in records if r["mechanism"] == "TOP_PCA_SIGNAL"]
    recovered = sum(r["status"] == "PASS" and r["gain_pc8_minus_full"] > 0 and r["full_bacc"] >= .75 for r in low)
    top_recovered = sum(r["status"] == "PASS" and r["pc8_bacc"] >= .75 for r in top)
    passed = (len(records) == 15 and all(r["status"] == "PASS" for r in records)
              and recovered >= 4 and top_recovered == 5 and all(r["status"] == "PASS" for r in identities))
    receipt = {"packet": "P0", "status": "PASS" if passed else "CAPABILITY_FAIL",
               "algorithm_hash": p0_algorithm_hash(), "development_revision": development_revision,
               "evaluation_seed_start": first_seed, "worlds": 15, "capability_heads": 30,
               "equivalence_test_heads": 2, "optimizer_attempts": sum(d["attempt_count"] for d in diagnostics),
               "low_variance_recovered": recovered, "low_variance_denominator": 5,
               "top_pca_recovered": top_recovered, "top_pca_denominator": 5,
               "null_requirement": "finite complete evaluation; no exact-zero or real-data power claim",
               "equivalence_controls": identities, "world_results": records}
    return {"receipt": receipt, "world_results": pd.DataFrame(records),
            "fit_diagnostics": pd.DataFrame(diagnostics)}
