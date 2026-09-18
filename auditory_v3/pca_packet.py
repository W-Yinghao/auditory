"""P0's complete, fixed 260-head matrix over frozen outer-fold features."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

from .linear import WeightedScaler, WeightedPCA, fit_logistic, require_slurm
from .statistics import hierarchical_weights, paired_contrasts


P0_MODES = ("R_SIM", "L0", "R_SUP", "R_RAND")
P0_LAMBDAS = (0.01, 0.001, 0.1)
P0_VIEWS = ("FULL", "PC8", "REST", "PC8_DUP")


def p0_algorithm_hash():
    digest = hashlib.sha256()
    for name in ("linear.py", "statistics.py", "pca_packet.py", "p0_capability.py"):
        digest.update(name.encode())
        digest.update(Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


def view_key(mode, window, lambda_l2, view):
    return f"{mode}__{window}__lambda{lambda_l2:g}__{view}"


def orthogonal_equivalence(model, U, pca):
    """Check the full head's orthogonal coordinate transport without a new fit.

    If training rank is deficient, omitted directions have zero optimum ridge
    coefficient. Report the coefficient residual instead of inventing axes.
    """
    if not model.success:
        return {"status": "NUMERICAL_FAIL", "prediction_max_abs": None}
    rotated_coef = pca.components_ @ model.coef_
    rotated_bias = model.intercept_ + pca.mean_ @ model.coef_
    rotated_p = expit(pca.transform(U) @ rotated_coef + rotated_bias)
    difference = float(np.max(np.abs(model.predict_proba(U) - rotated_p)))
    residual = float(np.linalg.norm(model.coef_ - pca.components_.T @ rotated_coef))
    penalty_difference = float(abs(model.coef_ @ model.coef_ - rotated_coef @ rotated_coef))
    return {"status": "PASS" if difference <= 2e-5 and penalty_difference <= 2e-8 else "FAIL",
            "prediction_max_abs": difference, "coefficient_offspan_norm": residual,
            "squared_norm_difference": penalty_difference,
            "method": "exact_coordinate_transport_no_new_fit"}


def run_pca(members, feature_loader, *, capability_receipt, ledger=None, context=None):
    """Run P0 and return public summaries plus private tables/transforms.

    ``feature_loader(mode, outer_fold, window)`` must return a finite matrix in
    exactly ``members`` row order. The caller verifies trial joins, the old
    encoder's actual training scope and frozen registry/split hashes. The gate
    is checked before any feature loading or fitting here.
    """
    require_slurm()
    if (capability_receipt.get("status") != "PASS" or
            capability_receipt.get("algorithm_hash") != p0_algorithm_hash()):
        raise RuntimeError("P0 requires a passing capability receipt for these exact sources")
    frame = members.reset_index(drop=True).copy()
    required = ["trial_id", "split_group_id", "A_half", "previous_code",
                "previous_run_bin", "stimulus_local_id", "outer_fold"]
    if any(c not in frame for c in required):
        raise ValueError("P0 member metadata are incomplete")
    if frame.trial_id.duplicated().any():
        raise ValueError("P0 frozen member trials must not repeat")
    if frame.groupby("split_group_id").outer_fold.nunique().ne(1).any():
        raise ValueError("Identity split across outer folds")
    if frame.groupby("split_group_id").A_half.nunique().ne(2).any():
        raise ValueError("P0 requires both frozen halves for every identity")
    folds = sorted(frame.outer_fold.unique())
    if len(folds) != 5:
        raise ValueError("P0 requires all five outer folds")
    y = frame.stimulus_local_id.to_numpy(dtype=np.float64)
    predictions = frame[required].copy()
    fits, transform_records, numerical_controls, contrasts = [], [], [], {}
    models = {}
    probability_columns = {}
    fit_failures = []
    planned_heads = 0
    all_context = dict(context or {})
    for mode in P0_MODES:
        for window in (("post", "pre") if mode in ("R_SIM", "L0") else ("post",)):
            lambdas = P0_LAMBDAS if window == "post" else (0.01,)
            views = P0_VIEWS if window == "post" else ("FULL", "PC8")
            for lam in lambdas:
                for view in views:
                    key = view_key(mode, window, lam, view)
                    predictions[key] = np.nan
                    probability_columns[key] = key
                full, pc = (view_key(mode, window, lam, v) for v in ("FULL", "PC8"))
                contrasts[f"{mode}__{window}__lambda{lam:g}__PC8_minus_FULL"] = (pc, full)
                if window == "post":
                    duplicate = view_key(mode, window, lam, "PC8_DUP")
                    rest = view_key(mode, window, lam, "REST")
                    contrasts[f"{mode}__{window}__lambda{lam:g}__DUP_minus_PC8"] = (duplicate, pc)
                    contrasts[f"{mode}__{window}__lambda{lam:g}__REST_minus_FULL"] = (rest, full)
            for fold in folds:
                train = frame.outer_fold.to_numpy() != fold
                test = ~train
                if (frame.loc[train, "split_group_id"].nunique() < 20 or
                        frame.loc[test, "split_group_id"].nunique() < 4):
                    raise ValueError("P0 outer-fold group support is below the frozen minimum")
                weights = hierarchical_weights(frame.loc[train])
                X = np.asarray(feature_loader(mode, int(fold), window), dtype=np.float64)
                expected_dim = (400 if window == "post" else 200) if mode == "L0" else 64
                if X.shape != (len(frame), expected_dim) or not np.all(np.isfinite(X)):
                    raise ValueError("Frozen feature matrix has unexpected shape or nonfinite values")
                scaler = WeightedScaler().fit(X[train], weights)
                U = scaler.transform(X)
                pca = WeightedPCA().fit(U[train], weights)
                view_arrays = pca.views(U)
                transform_records.append({"mode": mode, "window": window, "outer_fold": int(fold),
                                          "mean": scaler.mean_, "scale": scaler.scale_,
                                          "pca_mean": pca.mean_, "components": pca.components_,
                                          "explained_variance": pca.explained_variance_,
                                          "rank": pca.rank_, "rank_tolerance": pca.rank_tolerance_})
                for lam in lambdas:
                    fitted = {}
                    for view in views:
                        planned_heads += 1
                        key = view_key(mode, window, lam, view)
                        fit_context = dict(all_context, packet="P0", representation=mode,
                                           window=window, outer_fold=int(fold), view=view,
                                           lambda_l2=lam, fit_kind="real")
                        data = view_arrays[view]
                        if view == "REST" and data.shape[1] == 0:
                            fits.append(dict(fit_context, status="NOT_APPLICABLE_ZERO_RANK_REST",
                                             success=False, n_features=0))
                            continue
                        model = fit_logistic(data[train], y[train], weights, lam,
                                             ledger=ledger, context=fit_context)
                        fitted[view] = model
                        models[f"fold{fold}__{key}"] = {"model": model, "scaler": scaler,
                                                       "pca": pca, "view": view}
                        predictions.loc[test, key] = model.predict_proba(data[test])
                        fits.append(dict(fit_context, **model.diagnostics))
                        if not model.success:
                            fit_failures.append(key)
                    if "FULL" in fitted:
                        numerical_controls.append(dict(mode=mode, window=window, outer_fold=int(fold),
                            lambda_l2=lam, control="FULL_ORTHOGONAL", **orthogonal_equivalence(fitted["FULL"], U, pca)))
                    if "PC8_DUP" in fitted:
                        pc, duplicate = fitted["PC8"], fitted["PC8_DUP"]
                        maximum = float(np.max(np.abs(pc.predict_proba(view_arrays["PC8"])
                                                - duplicate.predict_proba(view_arrays["PC8_DUP"]))))
                        numerical_controls.append({"mode": mode, "window": window, "outer_fold": int(fold),
                            "lambda_l2": lam, "control": "PC8_DUP", "prediction_max_abs": maximum if np.isfinite(maximum) else None,
                            "status": "PASS" if np.isfinite(maximum) and maximum <= 2e-5 else "FAIL"})
    if planned_heads != 260:
        raise AssertionError("P0 matrix differs from the frozen 260 planned heads")
    summary, identity = paired_contrasts(predictions, probability_columns, contrasts)
    primary_name = "R_SIM__post__lambda0.01__PC8_minus_FULL"
    primary = summary["contrasts"][primary_name]
    full_metric = summary["metrics"][view_key("R_SIM", "post", .01, "FULL")]
    controls_pass = all(c["status"] == "PASS" for c in numerical_controls)
    primary_keys = {view_key("R_SIM", "post", .01, v) for v in ("FULL", "PC8", "PC8_DUP")}
    primary_controls_pass = all(c["status"] == "PASS" for c in numerical_controls
        if c["mode"] == "R_SIM" and c["window"] == "post" and c["lambda_l2"] == .01)
    primary_complete = not (set(fit_failures) & primary_keys) and primary_controls_pass
    if not primary_complete:
        research = "NUMERICAL_FAIL"
    elif (primary["status"] == "PASS" and primary["gain_bits"] > .002
          and primary["ci_low"] > 0 and full_metric["J_bits"] > 0):
        research = "COMPRESSION_LIMITATION_SIGNAL"
    else:
        research = "NO_DETECTABLE_COMPRESSION_PENALTY"
    summary.update(packet="P0", risk_unit="bits_per_trial", research=research,
                   execution="COMPLETE" if not fit_failures and controls_pass else "PARTIAL_NUMERICAL_FAIL",
                   primary_status="PASS" if primary_complete else "NUMERICAL_FAIL",
                   incomplete_model_keys=sorted(set(fit_failures)),
                   support="PASS", capability="PASS", planned_heads=planned_heads,
                   actual_heads=len([f for f in fits if "attempt_count" in f]),
                   optimizer_attempts=sum(f.get("attempt_count", 0) for f in fits),
                   algorithm_hash=p0_algorithm_hash(), primary_contrast=primary_name,
                   numerical_controls=numerical_controls,
                   pca_diagnostics=[{"representation": t["mode"], "window": t["window"],
                       "outer_fold": t["outer_fold"], "rank": t["rank"],
                       "selected_variances": t["explained_variance"][:8].tolist(),
                       "remaining_variance_sum": float(t["explained_variance"][8:].sum())}
                       for t in transform_records],
                   pre_limitation="pre200ms versus post400ms; diagnostic, not an equal-length neural null")
    return {"summary": summary, "predictions": predictions, "identity_risks": identity,
            "fit_diagnostics": pd.DataFrame(fits), "transforms": transform_records, "models": models}
