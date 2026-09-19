"""Closed-form parity checks and a bounded clinical-shrinkage quantification.

Review section 4.2 requires three closed forms to be compared on synthetic design
matrices that contain no personal data:

  (1) SSE + alpha * ||gamma||^2                 <- what ridge_solution implements
  (2) MSE + (alpha / n) * ||gamma||^2           <- (1) divided by n; must match (1)
  (3) MSE + alpha * ||gamma||^2                 <- what the network objective used;
                                                    must equal (1) with n*alpha, not (1)

Section 4.3 then quantifies, on the already-frozen folds and the already-selected M1
specification, how much the clinical block alone moves when alpha is replaced by
n*alpha. That is a shrinkage demonstration, not a causal attribution of the observed
M3/M4 degradation and not a new tuning search.
"""
from __future__ import annotations

import numpy as np

from auditory_fn1.models import TabularTransform, clip_to_bounds, ridge_solution

PENALTIES = (0.01, 0.1, 1.0)
FP64_TOLERANCE = 1e-10


def _closed_forms(design: np.ndarray, y: np.ndarray, alpha: float) -> dict:
    n = design.shape[0]
    centre = design.mean(axis=0, keepdims=True)
    centred = design - centre
    target = y - y.mean()
    eye = np.eye(design.shape[1])
    sse = np.linalg.solve(centred.T @ centred + alpha * eye, centred.T @ target)
    mse_over_n = np.linalg.solve(centred.T @ centred / n + (alpha / n) * eye, centred.T @ target / n)
    mse_plain = np.linalg.solve(centred.T @ centred / n + alpha * eye, centred.T @ target / n)
    sse_n_alpha = np.linalg.solve(centred.T @ centred + (n * alpha) * eye, centred.T @ target)
    implemented, _ = ridge_solution(design, y, np.full(design.shape[1], alpha))
    return {
        "n": int(n), "p": int(design.shape[1]), "alpha": float(alpha), "alpha_over_n": float(alpha / n),
        "implementation_matches_sse_form": float(np.max(np.abs(implemented - sse))),
        "sse_vs_mse_over_n": float(np.max(np.abs(sse - mse_over_n))),
        "sse_vs_mse_plain": float(np.max(np.abs(sse - mse_plain))),
        "mse_plain_vs_sse_n_alpha": float(np.max(np.abs(mse_plain - sse_n_alpha))),
        "coefficient_norm_sse": float(np.linalg.norm(sse)),
        "coefficient_norm_mse_plain": float(np.linalg.norm(mse_plain)),
        "shrinkage_ratio": float(np.linalg.norm(mse_plain) / np.linalg.norm(sse)) if np.linalg.norm(sse) else None,
    }


def synthetic_design(rng: np.random.Generator, n: int, p: int, *, constant_column: bool,
                     indicator_columns: int, target_scale: float, target_offset: float) -> tuple[np.ndarray, np.ndarray]:
    """A design with the structural features the real clinical block has.

    No participant data is involved: values are drawn from the supplied generator.
    """
    blocks = [rng.normal(size=(n, max(1, p - indicator_columns - int(constant_column))))]
    if constant_column:
        blocks.append(np.full((n, 1), 3.0))
    if indicator_columns:
        blocks.append((rng.random((n, indicator_columns)) < 0.2).astype(float))
    design = np.hstack(blocks)[:, :p]
    y = target_offset + target_scale * rng.normal(size=n)
    return design, y


def parity_suite(fit_sizes: list[int], *, seed: int = 20260919) -> dict:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for n in fit_sizes:
        for alpha in PENALTIES:
            for constant_column in (False, True):
                for indicators in (0, 4):
                    for offset, scale, unit in ((0.0, 1.0, "centred_unit"),
                                                (88.0, 16.0, "source_units_0_to_100"),
                                                (0.88, 0.16, "scaled_0_to_1")):
                        design, y = synthetic_design(rng, n, 9, constant_column=constant_column,
                                                     indicator_columns=indicators,
                                                     target_scale=scale, target_offset=offset)
                        record = _closed_forms(design, y, alpha)
                        record.update({"constant_column": constant_column, "indicator_columns": indicators,
                                       "target_unit": unit})
                        rows.append(record)
    equivalent = [r for r in rows if r["sse_vs_mse_over_n"] <= FP64_TOLERANCE]
    restated = [r for r in rows if r["mse_plain_vs_sse_n_alpha"] <= FP64_TOLERANCE]
    distinct = [r for r in rows if r["sse_vs_mse_plain"] > FP64_TOLERANCE]
    implementation_ok = [r for r in rows if r["implementation_matches_sse_form"] <= FP64_TOLERANCE]
    return {
        "cases": len(rows),
        "tolerance": FP64_TOLERANCE,
        "implementation_is_sse_form": len(implementation_ok) == len(rows),
        "sse_equals_mse_over_n": len(equivalent) == len(rows),
        "mse_plain_equals_sse_with_n_alpha": len(restated) == len(rows),
        "sse_differs_from_mse_plain": len(distinct) == len(rows),
        "max_sse_vs_mse_over_n": max(r["sse_vs_mse_over_n"] for r in rows),
        "max_mse_plain_vs_sse_n_alpha": max(r["mse_plain_vs_sse_n_alpha"] for r in rows),
        "min_sse_vs_mse_plain": min(r["sse_vs_mse_plain"] for r in rows),
        "shrinkage_ratio_range": [min(r["shrinkage_ratio"] for r in rows),
                                  max(r["shrinkage_ratio"] for r in rows)],
        "rows": rows,
    }


def clinical_shrinkage(design_matrix: np.ndarray, target: np.ndarray, folds: list[dict],
                       specs: dict, bounds: tuple[float, float]) -> dict:
    """Fixed-OOF error under alpha versus n*alpha, clinical + technical inputs only.

    This isolates what the scale defect does to the CLINICAL block by itself. It says
    nothing about how much of the observed M3/M4 degradation it explains.
    """
    n_total = target.size
    predictions = {"alpha": np.full(n_total, np.nan), "n_alpha": np.full(n_total, np.nan)}
    scope: list[dict] = []
    for fold in folds:
        train, test = fold["train_idx"], fold["test_idx"]
        spec = specs[fold["outer_fold"]]
        transform = TabularTransform(spec["family"]).fit(design_matrix[train])
        design_train = transform.transform(design_matrix[train])
        design_test = transform.transform(design_matrix[test])
        n = int(train.size)
        for label, penalty in (("alpha", float(spec["penalty"])), ("n_alpha", float(spec["penalty"]) * n)):
            coef, intercept = ridge_solution(design_train, target[train], np.full(design_train.shape[1], penalty))
            centre = design_train.mean(axis=0, keepdims=True)
            predictions[label][test] = clip_to_bounds(intercept + (design_test - centre) @ coef, bounds)
        scope.append({"outer_fold": fold["outer_fold"], "n_train": n, "n_test": int(test.size),
                      "family": spec["family"], "alpha": float(spec["penalty"]),
                      "alpha_over_n": float(spec["penalty"]) / n,
                      "effective_network_penalty_multiple": n,
                      "design_columns": int(design_train.shape[1])})
    errors = {k: np.abs(v - target) for k, v in predictions.items()}
    return {
        "fit_scopes": scope,
        "MAE_alpha": float(errors["alpha"].mean()),
        "MAE_n_alpha": float(errors["n_alpha"].mean()),
        "MAE_change_from_overpenalising_the_clinical_block": float(errors["n_alpha"].mean() - errors["alpha"].mean()),
        "identities": int(n_total),
        "interpretation": ("Fixed out-of-fold error of the CLINICAL block alone under the correct and the "
                           "over-strong penalty. It demonstrates the size of the clinical shrinkage; it does "
                           "not attribute the observed M3/M4 degradation to this cause."),
    }
