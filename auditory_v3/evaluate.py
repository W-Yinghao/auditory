"""R3's fixed full-representation probes with an identity holdout.

Selection uses only requested inner-fit/validation rows from selection-stage
encoders. Final probes use independently refitted final-stage encoders. There
is no PCA, calibration, offset family, or outer-test model selection.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import htrial
from .linear import WeightedScaler, fit_logistic, require_slurm
from .statistics import hierarchical_weights, paired_contrasts, weighted_metrics


OBJECTIVES = ("SUP", "SIM", "MATCH")
PROBE_VIEWS = ("Zpost", "Htrial_Zpost", "Htrial_Zpre")
LAMBDAS = (.001, .01, .1)
COMMON_MODELS = ("Htrial", "L0_post", "RAND_post")
MODEL_NAMES = tuple(f"{objective}__{view}" for objective in OBJECTIVES for view in PROBE_VIEWS) + COMMON_MODELS


def r3_probe_algorithm_hash():
    digest = hashlib.sha256()
    for filename in ("linear.py", "statistics.py", "data.py", "evaluate.py"):
        digest.update(filename.encode())
        digest.update(Path(__file__).with_name(filename).read_bytes())
    return digest.hexdigest()


def _json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _prepare(members, splits):
    required = ("trial_id", "split_group_id", "A_half", "previous_code", "previous_run_bin",
                "stimulus_local_id", "outer_fold", "previous_gap_s", "position_fraction")
    if any(name not in members for name in required):
        raise ValueError("R3 probe member metadata are incomplete")
    if not np.array_equal(members.index, np.arange(len(members))):
        raise ValueError("Global member indices must be canonical before feature loading")
    if members.trial_id.duplicated().any() or members.trial_id.isna().any():
        raise ValueError("Frozen member trial IDs must be unique and present")
    if not members.stimulus_local_id.isin([0, 1]).all():
        raise ValueError("R3 labels must remain the frozen binary stimulus codes")
    if members.groupby("split_group_id").A_half.nunique().ne(2).any():
        raise ValueError("R3 requires both frozen halves of every identity")
    all_groups = set(members.split_group_id.astype(str))
    folds = sorted(splits["folds"], key=lambda f: int(f["outer_fold"]))
    if len(folds) != 5 or len({int(f["outer_fold"]) for f in folds}) != 5:
        raise ValueError("R3 probes require all five frozen outer folds")
    tested = set()
    for fold in folds:
        train, test, fit, validation = (set(map(str, fold[key])) for key in
            ("train_groups", "test_groups", "R3_fit_groups", "R3_validation_groups"))
        if train & test or train | test != all_groups:
            raise ValueError("Invalid frozen outer identity split")
        if fit & validation or fit | validation != train:
            raise ValueError("R3 selection roles are not a partition of outer training identities")
        if len(train) < 21 or len(test) < 4 or len(fit) < 16 or len(validation) < 5:
            raise ValueError("R3 probe identity support is below the frozen minimum")
        if tested & test:
            raise ValueError("An identity is tested in multiple outer folds")
        tested |= test
        actual = set(members.loc[members.outer_fold == fold["outer_fold"], "split_group_id"].astype(str))
        if actual != test:
            raise ValueError("Member outer-fold labels disagree with the frozen split")
    if tested != all_groups:
        raise ValueError("Some identities have no frozen outer test fold")
    return folds


def _indices(members, groups):
    return np.flatnonzero(members.split_group_id.astype(str).isin(set(map(str, groups))).to_numpy())


def _load(feature_loader, objective, fold, stage, window, indices, dimension):
    values = np.asarray(feature_loader(objective, int(fold), stage, window, indices.copy()), dtype=np.float64)
    if values.shape != (len(indices), dimension) or not np.all(np.isfinite(values)):
        raise ValueError("R3 requested feature rows are misaligned, nonfinite, or the wrong dimension")
    return values


def _view_matrices(members, feature_loader, fold, stage, indices):
    """Materialize requested rows only; the caller selects train/val or train/test."""
    H = np.asarray(htrial(members.iloc[indices]), dtype=np.float64)
    if H.shape != (len(indices), 13) or not np.all(np.isfinite(H)):
        raise ValueError("Explicit Htrial whitelist did not produce 13 finite coordinates")
    matrices = {"Htrial": H}
    for objective in OBJECTIVES:
        post = _load(feature_loader, objective, fold, stage, "post", indices, 64)
        pre = _load(feature_loader, objective, fold, stage, "pre", indices, 64)
        matrices[f"{objective}__Zpost"] = post
        matrices[f"{objective}__Htrial_Zpost"] = np.column_stack([H, post])
        matrices[f"{objective}__Htrial_Zpre"] = np.column_stack([H, pre])
    matrices["L0_post"] = _load(feature_loader, "L0", fold, stage, "post", indices, 400)
    matrices["RAND_post"] = _load(feature_loader, "RAND", fold, stage, "post", indices, 64)
    return matrices


def _choose_lambda(scores):
    """Require the complete three-lambda grid; exact ties prefer larger lambda."""
    if set(scores) != set(LAMBDAS) or any(v is None or not np.isfinite(v) for v in scores.values()):
        return None
    return float(min(LAMBDAS, key=lambda lam: (scores[lam], -lam)))


def select_probes(members, feature_loader, splits, *, ledger=None, context=None):
    """Fit 180 selection probes and return all 60 fixed choices, privately.

    Loader signature: ``(objective, outer_fold, stage, window, indices)``.
    It returns only those global member rows in the requested order. Stages are
    ``selection`` and ``final``. SUP/SIM/MATCH/RAND yield 64 encoder coordinates;
    L0 post yields 400 coordinates. The root loader verifies checkpoint hashes
    and exact encoder/scaler training scope before inference. Htrial is built
    here from its fixed metadata whitelist.
    """
    require_slurm()
    folds = _prepare(members, splits)
    selections, diagnostics, models = [], [], {}
    for fold in folds:
        fold_number = int(fold["outer_fold"])
        fit_indices = _indices(members, fold["R3_fit_groups"])
        validation_indices = _indices(members, fold["R3_validation_groups"])
        train_matrices = _view_matrices(members, feature_loader, fold_number, "selection", fit_indices)
        validation_matrices = _view_matrices(members, feature_loader, fold_number, "selection", validation_indices)
        fit_rows, validation_rows = members.iloc[fit_indices], members.iloc[validation_indices]
        fit_weights = hierarchical_weights(fit_rows)
        validation_weights = hierarchical_weights(validation_rows)
        fit_y = fit_rows.stimulus_local_id.to_numpy()
        validation_y = validation_rows.stimulus_local_id.to_numpy()
        for name in MODEL_NAMES:
            scaler = WeightedScaler().fit(train_matrices[name], fit_weights)
            train = scaler.transform(train_matrices[name])
            validation = scaler.transform(validation_matrices[name])
            scores = {}
            for lam in LAMBDAS:
                fit_context = dict(context or {}, packet="R3", stage="selection", probe=name,
                                   outer_fold=fold_number, lambda_l2=lam, fit_kind="real_probe")
                model = fit_logistic(train, fit_y, fit_weights, lam, ledger=ledger, context=fit_context)
                metric = weighted_metrics(validation_y, model.predict_proba(validation), validation_weights)
                scores[lam] = metric["ce_bits"]
                diagnostics.append(dict(fit_context, validation_ce_bits=metric["ce_bits"], **model.diagnostics))
                models[f"fold{fold_number}__{name}__lambda{lam:g}"] = {
                    "scaler": scaler, "model": model, "fit_groups": list(fold["R3_fit_groups"]),
                    "validation_groups": list(fold["R3_validation_groups"]),
                    "feature_dimension": train.shape[1]}
            selected = _choose_lambda(scores)
            selections.append({"outer_fold": fold_number, "probe": name, "selected_lambda": selected,
                "status": "PASS" if selected is not None else "NUMERICAL_FAIL",
                "validation_ce_bits": {str(lam): scores[lam] for lam in LAMBDAS},
                "fit_groups_sha256": _json_hash(sorted(map(str, fold["R3_fit_groups"]))),
                "validation_groups_sha256": _json_hash(sorted(map(str, fold["R3_validation_groups"]))),
                "feature_dimension": train.shape[1]})
    if len(diagnostics) != 180 or len(selections) != 60:
        raise AssertionError("R3 selection matrix differs from the fixed 180-head / 60-choice catalog")
    receipt = {"packet": "R3", "stage": "probe_selection",
        "status": "PASS" if all(s["status"] == "PASS" for s in selections) else "COMPLETED_WITH_NUMERICAL_FAILURES",
        "selection_complete": True,
        "algorithm_hash": r3_probe_algorithm_hash(), "splits_sha256": _json_hash(splits),
        "trial_order_sha256": _json_hash(members.trial_id.astype(str).tolist()),
        "expected_choices": 60, "selection_heads": 180,
        "objective_selection_heads": 135, "common_selection_heads": 45,
        "optimizer_attempts": sum(d["attempt_count"] for d in diagnostics),
        "selections": selections, "lambda_grid": list(LAMBDAS),
        "tie_break": "stronger_regularization", "outer_test_scored": False}
    return {"selection_receipt": receipt, "fit_diagnostics": pd.DataFrame(diagnostics), "models": models}


def _validate_selection(members, splits, receipt):
    if (receipt.get("status") not in ("PASS", "COMPLETED_WITH_NUMERICAL_FAILURES")
            or not receipt.get("selection_complete") or receipt.get("stage") != "probe_selection"
            or receipt.get("algorithm_hash") != r3_probe_algorithm_hash()
            or receipt.get("splits_sha256") != _json_hash(splits)
            or receipt.get("trial_order_sha256") != _json_hash(members.trial_id.astype(str).tolist())):
        raise RuntimeError("Final R3 probes require complete source- and split-bound selection choices")
    selected = {}
    for item in receipt.get("selections", []):
        key = (int(item["outer_fold"]), item["probe"])
        valid = item.get("status") == "PASS" and item.get("selected_lambda") in LAMBDAS
        failed = item.get("status") == "NUMERICAL_FAIL" and item.get("selected_lambda") is None
        if key in selected or not (valid or failed):
            raise RuntimeError("Invalid or repeated R3 probe choice")
        selected[key] = item["selected_lambda"]
    wanted = {(int(fold["outer_fold"]), name) for fold in splits["folds"] for name in MODEL_NAMES}
    if set(selected) != wanted or len(selected) != 60 or receipt.get("selection_heads") != 180:
        raise RuntimeError("The complete R3 selection matrix must precede all final probes")
    return selected


def r3_contrasts():
    contrasts = {}
    for view in PROBE_VIEWS:
        contrasts[f"SUP_minus_MATCH__{view}"] = (f"SUP__{view}", f"MATCH__{view}")
        contrasts[f"SIM_minus_MATCH__{view}"] = (f"SIM__{view}", f"MATCH__{view}")
        contrasts[f"SUP_minus_SIM__{view}"] = (f"SUP__{view}", f"SIM__{view}")
    for objective in OBJECTIVES:
        for view in PROBE_VIEWS:
            for baseline in COMMON_MODELS:
                contrasts[f"{baseline}_minus_{objective}__{view}"] = (baseline, f"{objective}__{view}")
        contrasts[f"{objective}__pre_minus_post"] = (
            f"{objective}__Htrial_Zpre", f"{objective}__Htrial_Zpost")
    return contrasts


def _research_status(summary):
    contrast = summary["contrasts"]
    primary = contrast["SUP_minus_MATCH__Htrial_Zpost"]
    metadata = contrast["Htrial_minus_MATCH__Htrial_Zpost"]
    matches_l0 = contrast["L0_post_minus_MATCH__Htrial_Zpost"]
    matches_rand = contrast["RAND_post_minus_MATCH__Htrial_Zpost"]
    if primary["status"] != "PASS":
        return "NUMERICAL_FAIL"
    primary_pass = primary["gain_bits"] >= .005 and primary["ci_low"] > 0
    if not primary_pass:
        return "NO_ADDED_VALUE_OVER_SUPERVISION"
    if any(item["status"] != "PASS" for item in (metadata, matches_l0, matches_rand)):
        return "UNRESOLVED_ALTERNATIVE_EXPLANATION"
    metadata_pass = metadata["ci_low"] > 0
    if matches_l0["gain_bits"] <= 0 and matches_rand["gain_bits"] <= 0:
        return "NO_LEARNING_ADVANTAGE_ESTABLISHED"
    if not metadata_pass:
        return "UNRESOLVED_METADATA_EXPLANATION"
    # The protocol does not define a numerical pre veto or a threshold for a
    # post-versus-pre difference. Do not invent one after seeing the outcomes.
    return "UNRESOLVED_ALTERNATIVE_EXPLANATION"


def evaluate_representations(members, feature_loader, splits, selection_receipt, *,
                             ledger=None, context=None):
    """Refit 60 probes on all outer-train identities and score every OOF row.

    The caller must gate completion of all 15 selection encoders/choices before
    starting the 15 final encoder fits, and verify final encoder receipts before
    constructing this loader. Models/scalers and identity rows returned here
    are private artifacts, never public summary fields.
    """
    require_slurm()
    folds = _prepare(members, splits)
    selected = _validate_selection(members, splits, selection_receipt)
    metadata_columns = ["trial_id", "split_group_id", "A_half", "previous_code",
                        "previous_run_bin", "stimulus_local_id", "outer_fold"]
    predictions = members[metadata_columns].copy()
    for name in MODEL_NAMES:
        predictions[name] = np.nan
    diagnostics, models, rank_diagnostics = [], {}, []
    for fold in folds:
        fold_number = int(fold["outer_fold"])
        train_indices = _indices(members, fold["train_groups"])
        test_indices = _indices(members, fold["test_groups"])
        train_matrices = _view_matrices(members, feature_loader, fold_number, "final", train_indices)
        test_matrices = _view_matrices(members, feature_loader, fold_number, "final", test_indices)
        train_rows = members.iloc[train_indices]
        weights = hierarchical_weights(train_rows)
        train_y = train_rows.stimulus_local_id.to_numpy()
        for name in MODEL_NAMES:
            lam = selected[(fold_number, name)]
            fit_context = dict(context or {}, packet="R3", stage="final", probe=name,
                               outer_fold=fold_number, lambda_l2=lam, fit_kind="real_probe")
            if lam is None:
                diagnostics.append(dict(fit_context, status="SELECTION_NUMERICAL_FAIL",
                                        success=False, attempt_count=0))
                models[f"fold{fold_number}__{name}"] = {"model": None,
                    "status": "SELECTION_NUMERICAL_FAIL", "selected_lambda": None}
                continue
            scaler = WeightedScaler().fit(train_matrices[name], weights)
            train = scaler.transform(train_matrices[name])
            test = scaler.transform(test_matrices[name])
            model = fit_logistic(train, train_y, weights, lam, ledger=ledger, context=fit_context)
            predictions.loc[test_indices, name] = model.predict_proba(test)
            diagnostics.append(dict(fit_context, **model.diagnostics))
            models[f"fold{fold_number}__{name}"] = {"scaler": scaler, "model": model,
                "fit_groups": list(fold["train_groups"]), "test_groups": list(fold["test_groups"]),
                "feature_dimension": train.shape[1], "selected_lambda": lam}
            if name.endswith("__Zpost") or name == "RAND_post":
                # A collapsed representation is retained and its intercept
                # model is still evaluated; rank is diagnostic only.
                constant=scaler.constant_ | (np.ptp(train_matrices[name],axis=0)==0)
                rank_input=train-train[:1];rank_input[:,constant]=0.
                rank_diagnostics.append({"outer_fold": fold_number, "probe": name,
                    "numerical_rank": int(np.linalg.matrix_rank(rank_input)),
                    "constant_coordinates": int(np.sum(constant)), "dimension": train.shape[1]})
    if len(diagnostics) != 60:
        raise AssertionError("R3 final matrix differs from the frozen 60-head catalog")
    summary, identities = paired_contrasts(predictions, {n: n for n in MODEL_NAMES}, r3_contrasts())
    complete = all(d["success"] for d in diagnostics) and all(m["status"] == "PASS" for m in summary["metrics"].values())
    summary.update(packet="R3", risk_unit="bits_per_trial", primary_contrast="SUP_minus_MATCH__Htrial_Zpost",
        execution="COMPLETE" if complete else "NUMERICAL_FAIL", support="PASS",
        research=_research_status(summary),
        primary_status="PASS" if summary["contrasts"]["SUP_minus_MATCH__Htrial_Zpost"]["status"] == "PASS" else "NUMERICAL_FAIL",
        incomplete_models=[name for name, metric in summary["metrics"].items() if metric["status"] != "PASS"],
        selection_heads=180, final_heads=sum(d["attempt_count"] > 0 for d in diagnostics),
        planned_final_heads=60, total_planned_probe_heads=240,
        final_optimizer_attempts=sum(d["attempt_count"] for d in diagnostics),
        rank_diagnostics=rank_diagnostics, algorithm_hash=r3_probe_algorithm_hash(),
        pre_limitation="pre200ms versus post400ms; encoder trained on post; diagnostic only",
        attribution="whole prespecified objective and sampling strategy; no isolated positive-edge claim",
        population="P_MATCH_bal", scope="exploratory_existing_cohort_fixed_oof")
    if summary["research"] == "UNRESOLVED_ALTERNATIVE_EXPLANATION":
        required_controls = ["Htrial", "L0_post", "RAND_post", "MATCH__Htrial_Zpre"]
        summary["research_reason"] = ("INCOMPLETE_REQUIRED_CONTROLS" if any(
            summary["metrics"][name]["status"] != "PASS" for name in required_controls)
            else "PRE_DIAGNOSTIC_REVIEW_REQUIRED")
    return {"summary": summary, "predictions": predictions, "identity_risks": identities,
            "fit_diagnostics": pd.DataFrame(diagnostics), "models": models}
