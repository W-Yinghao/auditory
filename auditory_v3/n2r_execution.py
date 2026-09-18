"""One N2R numerical path for the bounded capability and real-data matrices.

Four training contexts per outer fold (three inner, one full outer) are shared
by all lambda/view fits. Bag feature blocks are standardized once, before the
isometric HQQ duplicate is constructed. No view-level rescaling follows it.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from .bags_packet import (H_COLUMNS, VIEW_NAMES, FULL_VIEW_NAMES,
                          bag_history_array, quadratic_mean, validate_aligned_inputs)
from .linear import WeightedScaler, WeightedPCA, fit_logistic, require_slurm
from .statistics import hierarchical_weights, paired_contrasts, weighted_metrics


ALL_VIEWS = (*VIEW_NAMES, *FULL_VIEW_NAMES)
LAMBDAS = (.001, .01, .1)


def n2r_algorithm_hash():
    digest = hashlib.sha256()
    for name in ("linear.py", "statistics.py", "bags_packet.py", "n2r_execution.py"):
        digest.update(name.encode())
        digest.update(Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


@dataclass
class TransformContext:
    fit_groups: tuple
    evaluation_groups: tuple
    bag_indices: np.ndarray
    fit_bag_indices: np.ndarray
    evaluation_bag_indices: np.ndarray
    views: dict
    trial_scalers: dict
    pcas: dict
    block_scalers: dict
    blocks: dict


def _bind_splits(frame, splits, outer_folds):
    folds = {int(f["outer_fold"]): f for f in splits["folds"]}
    if len(folds) != 5 or len(splits["folds"]) != 5:
        raise ValueError("N2R requires the original five-fold mapping")
    selected = sorted(folds) if outer_folds is None else list(map(int, outer_folds))
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= set(folds):
        raise ValueError("Invalid requested N2R outer folds")
    population = set(frame.split_group_id.astype(str))
    mapping = {}
    for number, fold in folds.items():
        train, test = (set(map(str, fold[k])) for k in ("train_groups", "test_groups"))
        if train & test or train | test != population:
            raise ValueError("Frozen outer groups do not partition the population")
        if set(mapping) & test:
            raise ValueError("Duplicate outer test identity")
        mapping.update({group: number for group in test})
        if number not in selected:
            continue
        if len(train) < 20 or len(test) < 4:
            raise ValueError("N2R outer identity support is insufficient")
        inner = fold["inner_folds"]
        if len(inner) != 3 or len({int(f["inner_fold"]) for f in inner}) != 3:
            raise ValueError("N2R requires three frozen inner folds")
        validated = set()
        for item in inner:
            fit, validation = (set(map(str, item[k])) for k in ("fit_groups", "validation_groups"))
            if fit & validation or fit | validation != train or validated & validation:
                raise ValueError("Frozen inner groups are not disjoint complete partitions")
            if len(fit) < 12 or len(validation) < 4:
                raise ValueError("N2R inner identity support is insufficient")
            validated |= validation
        if validated != train:
            raise ValueError("Every outer-train identity needs one inner OOF prediction")
    if set(mapping) != population:
        raise ValueError("Frozen outer test mapping is incomplete")
    mapped = frame.split_group_id.astype(str).map(mapping)
    if "outer_fold" in frame and not np.array_equal(frame.outer_fold.to_numpy(), mapped.to_numpy()):
        raise ValueError("Member outer fold differs from frozen identity mapping")
    frame = frame.copy()
    frame["outer_fold"] = mapped
    if frame.groupby("split_group_id").A_half.nunique().ne(2).any():
        raise ValueError("Both frozen halves are required")
    return frame, [folds[number] for number in selected]


def _bag_index(frame):
    groups = frame.groupby("bag_id", sort=False).indices
    indices = np.stack(list(groups.values()))
    if indices.shape[1] != 8:
        raise ValueError("Frozen bag member count differs from eight")
    first = indices[:, 0]
    columns = [c for c in ("bag_id", "matched_pair_id", "candidate_id", "split_group_id",
                          "stimulus_local_id", "A_half", "previous_code", "previous_run_bin", "outer_fold")
               if c in frame]
    return frame.iloc[first][columns].reset_index(drop=True), indices


def _means_log_variances(values, local_bag_indices):
    bags = values[local_bag_indices]
    return bags.mean(axis=1), np.log1p(bags.var(axis=1, ddof=1))


def _make_views(blocks, view_names):
    """Assemble already standardized blocks; never standardize these views."""
    b = blocks
    builders = {
        "H": lambda: b["H"],
        "HM": lambda: np.column_stack([b["H"], b["MU"]]),
        "HMV": lambda: np.column_stack([b["H"], b["MU"], b["V"]]),
        "HQ": lambda: np.column_stack([b["H"], b["Q"]]),
        "HQV": lambda: np.column_stack([b["H"], b["Q"], b["V"]]),
        "HQQ": lambda: np.column_stack([b["H"], b["Q"] / np.sqrt(2), b["Q"] / np.sqrt(2)]),
        "HPRE": lambda: np.column_stack([b["H"], b["PRE_Q"], b["PRE_V"]]),
        "HPREQ": lambda: np.column_stack([b["H"], b["PRE_Q"], b["PRE_V"], b["Q"]]),
        "HPREQV": lambda: np.column_stack([b["H"], b["PRE_Q"], b["PRE_V"], b["Q"], b["V"]]),
        "FULL_MU": lambda: b["FULL_MU"],
        "FULL_MU_VAR": lambda: np.column_stack([b["FULL_MU"], b["FULL_V"]]),
    }
    return {name: builders[name]() for name in view_names}


def fit_transform_context(frame, bag_frame, bag_members, post, pre, h,
                          fit_groups, evaluation_groups, view_names=ALL_VIEWS):
    """Fit one context without reading held-out rows into fitted statistics.

    Private return values expose each block scaler and training-only PCA for
    leakage audits. ``bag_indices`` maps its local matrices back to global bags.
    """
    fit_groups = tuple(sorted(map(str, fit_groups)))
    evaluation_groups = tuple(sorted(map(str, evaluation_groups)))
    if set(fit_groups) & set(evaluation_groups):
        raise ValueError("Transform fit/evaluation scopes overlap")
    member_group = frame.split_group_id.astype(str)
    fit_rows = np.flatnonzero(member_group.isin(fit_groups).to_numpy())
    allowed_rows = np.flatnonzero(member_group.isin((*fit_groups, *evaluation_groups)).to_numpy())
    bag_group = bag_frame.split_group_id.astype(str)
    bag_indices = np.flatnonzero(bag_group.isin((*fit_groups, *evaluation_groups)).to_numpy())
    fit_bags = np.flatnonzero(bag_group.iloc[bag_indices].isin(fit_groups).to_numpy())
    eval_bags = np.flatnonzero(bag_group.iloc[bag_indices].isin(evaluation_groups).to_numpy())
    if not len(fit_rows) or not len(fit_bags) or not len(eval_bags):
        raise ValueError("Empty transform scope")
    row_lookup = np.full(len(frame), -1, dtype=int)
    row_lookup[allowed_rows] = np.arange(len(allowed_rows))
    local_bag_members = row_lookup[bag_members[bag_indices]]
    if (local_bag_members < 0).any():
        raise ValueError("Bag straddles transform identity scopes")
    weights = hierarchical_weights(frame.iloc[fit_rows])
    bag_weights = hierarchical_weights(bag_frame.iloc[bag_indices[fit_bags]])
    trial_scalers, pcas, raw_blocks = {}, {}, {}
    raw_blocks["H"] = h[bag_members[bag_indices, 0]]
    need_pc = any(view in VIEW_NAMES and view != "H" for view in view_names)
    need_pre = any(view in ("HPRE", "HPREQ", "HPREQV") for view in view_names)
    need_full = any(view in FULL_VIEW_NAMES for view in view_names)
    if need_pc or need_full:
        scaler = WeightedScaler().fit(post[fit_rows], weights)
        trial_scalers["post"] = scaler
        scaled_post = scaler.transform(post[allowed_rows])
        if need_pc:
            pca = WeightedPCA().fit(scaler.transform(post[fit_rows]), weights)
            if pca.rank_ < 8:
                raise ValueError("PCA8_POST_RANK_UNSUPPORTED")
            pcas["post"] = pca
            pc = pca.transform(scaled_post, n_components=8)
            mu, variance = _means_log_variances(pc, local_bag_members)
            raw_blocks.update(MU=mu, Q=quadratic_mean(mu), V=variance)
        if need_full:
            mu, variance = _means_log_variances(scaled_post, local_bag_members)
            raw_blocks.update(FULL_MU=mu, FULL_V=variance)
    if need_pre:
        scaler = WeightedScaler().fit(pre[fit_rows], weights)
        trial_scalers["pre"] = scaler
        pca = WeightedPCA().fit(scaler.transform(pre[fit_rows]), weights)
        if pca.rank_ < 8:
            raise ValueError("PCA8_PRE_RANK_UNSUPPORTED")
        pcas["pre"] = pca
        pc = pca.transform(scaler.transform(pre[allowed_rows]), n_components=8)
        mu, variance = _means_log_variances(pc, local_bag_members)
        raw_blocks.update(PRE_Q=quadratic_mean(mu), PRE_V=variance)
    block_scalers, blocks = {}, {}
    for name, values in raw_blocks.items():
        scaler = WeightedScaler().fit(values[fit_bags], bag_weights)
        block_scalers[name] = scaler
        blocks[name] = scaler.transform(values)
    views = _make_views(blocks, view_names)
    return TransformContext(fit_groups, evaluation_groups, bag_indices, fit_bags, eval_bags,
                            views, trial_scalers, pcas, block_scalers, blocks)


def _equivalence(reference, duplicate, reference_X, duplicate_X, **context):
    if not reference.success or not duplicate.success:
        return dict(context, status="NUMERICAL_FAIL", prediction_max_abs=None, objective_difference=None)
    difference = float(np.max(np.abs(reference.predict_proba(reference_X) - duplicate.predict_proba(duplicate_X))))
    objective_difference = float(abs(reference.diagnostics["final_objective"] - duplicate.diagnostics["final_objective"]))
    return dict(context, status="PASS" if difference <= 2e-5 and objective_difference <= 2e-8 else "FAIL",
                prediction_max_abs=difference, objective_difference=objective_difference)


def _contrasts(view_names):
    specified = {"HQ_minus_HQV": ("HQ", "HQV"), "H_minus_HQV": ("H", "HQV"),
        "HQQ_minus_HQV": ("HQQ", "HQV"), "HPREQ_minus_HPREQV": ("HPREQ", "HPREQV"),
        "HM_minus_HMV": ("HM", "HMV"), "FULL_MU_minus_FULL_MU_VAR": ("FULL_MU", "FULL_MU_VAR"),
        "HQQ_minus_HQ": ("HQQ", "HQ")}
    return {name: pair for name, pair in specified.items() if set(pair) <= set(view_names)}


def _research(summary, controls, view_names, n_folds):
    primary = summary["contrasts"].get("HQ_minus_HQV")
    if primary is None or primary["status"] != "PASS":
        return "NUMERICAL_FAIL" if primary is not None else "NOT_EVALUABLE"
    if n_folds != 5 or set(view_names) != set(ALL_VIEWS):
        return "CAPABILITY_SUBSET_EVALUATED"
    if primary["gain_bits"] < .005 or primary["ci_low"] <= 0:
        return "NO_CONTROLLED_GAIN_ESTABLISHED"
    required = [summary["contrasts"][name] for name in
                ("H_minus_HQV", "HQQ_minus_HQV", "HPREQ_minus_HPREQV")]
    controls_pass = bool(controls) and all(item["status"] == "PASS" for item in controls)
    if all(item["status"] == "PASS" and item["ci_low"] > 0 for item in required) and controls_pass:
        return "PROMISING_DISTRIBUTIONAL_EVIDENCE"
    return "UNRESOLVED_ALTERNATIVE_EXPLANATION"


def run_packet(members, post, pre, history, splits, *, view_names=ALL_VIEWS,
               outer_folds=None, ledger=None, context=None, bootstrap_repetitions=2000):
    """Run fixed N2R views on requested frozen outer folds, returning private OOF.

    Real use selects all eleven views/all five folds (550 planned heads).
    Capability selects HQ/HQV and one fold (20 planned heads). Both execute this
    exact transform, nested selection, optimization, and paired-statistics path.
    The calling worker checks support/capability receipts before invoking this
    function. No files or external data are loaded here.
    """
    require_slurm()
    view_names = tuple(view_names)
    if not view_names or len(set(view_names)) != len(view_names) or not set(view_names) <= set(ALL_VIEWS):
        raise ValueError("Unknown or duplicate N2R view")
    h = bag_history_array(members, history)
    frame, post, pre, h = validate_aligned_inputs(members, post, pre, h)
    frame, folds = _bind_splits(frame, splits, outer_folds)
    bag_frame, bag_members = _bag_index(frame)
    # Validate target support once. Trial and bag weights for every fit are
    # recomputed only from its own training identities below.
    hierarchical_weights(bag_frame)
    for rows in bag_members:
        if not np.array_equal(h[rows], np.broadcast_to(h[rows[0]], h[rows].shape)):
            raise ValueError("H_BAG differs between members of a frozen bag")
    predictions = bag_frame.copy()
    for view in view_names:
        predictions[view] = np.nan
    diagnostics, selections, controls, models, transforms = [], [], [], {}, {}
    group_values = bag_frame.split_group_id.astype(str)
    y = bag_frame.stimulus_local_id.to_numpy()
    for fold in folds:
        number = int(fold["outer_fold"])
        train_mask = group_values.isin(set(map(str, fold["train_groups"]))).to_numpy()
        train_global = np.flatnonzero(train_mask)
        inner_oof = {(view, lam): np.full(len(bag_frame), np.nan) for view in view_names for lam in LAMBDAS}
        for inner in sorted(fold["inner_folds"], key=lambda value: int(value["inner_fold"])):
            inner_number = int(inner["inner_fold"])
            transform = fit_transform_context(frame, bag_frame, bag_members, post, pre, h,
                        inner["fit_groups"], inner["validation_groups"], view_names)
            transforms[f"fold{number}__inner{inner_number}"] = transform
            fit_local, val_local = transform.fit_bag_indices, transform.evaluation_bag_indices
            fit_global = transform.bag_indices[fit_local]
            val_global = transform.bag_indices[val_local]
            weights = hierarchical_weights(bag_frame.iloc[fit_global])
            for lam in LAMBDAS:
                fitted = {}
                for view in view_names:
                    fit_context = dict(context or {}, packet="N2R", outer_fold=number,
                        stage="inner", inner_fold=inner_number, view=view, lambda_l2=lam)
                    X = transform.views[view]
                    model = fit_logistic(X[fit_local], y[fit_global], weights, lam,
                                         ledger=ledger, context=fit_context)
                    fitted[view] = model
                    inner_oof[(view, lam)][val_global] = model.predict_proba(X[val_local])
                    diagnostics.append(dict(fit_context, **model.diagnostics))
                    models[f"fold{number}__inner{inner_number}__{view}__lambda{lam:g}"] = model
                if "HQ" in fitted and "HQQ" in fitted:
                    controls.append(_equivalence(fitted["HQ"], fitted["HQQ"], transform.views["HQ"],
                        transform.views["HQQ"], outer_fold=number, stage="inner", inner_fold=inner_number, lambda_l2=lam))
        inner_weights = hierarchical_weights(bag_frame.iloc[train_global])
        choices = {}
        for view in view_names:
            risks = {lam: weighted_metrics(y[train_global], inner_oof[(view, lam)][train_global], inner_weights)["ce_bits"]
                     for lam in LAMBDAS}
            complete = all(value is not None and np.isfinite(value) for value in risks.values())
            chosen = float(min(LAMBDAS, key=lambda lam: (risks[lam], -lam))) if complete else None
            choices[view] = chosen
            selections.append({"outer_fold": number, "view": view, "selected_lambda": chosen,
                "status": "PASS" if complete else "INCOMPLETE_INNER_GRID",
                "inner_oof_ce_bits": {str(lam): risks[lam] for lam in LAMBDAS},
                "n_selection_groups": int(bag_frame.iloc[train_global].split_group_id.nunique()),
                "risk_rule": "hierarchical_weighted_all_inner_oof_identities"})
        transform = fit_transform_context(frame, bag_frame, bag_members, post, pre, h,
                    fold["train_groups"], fold["test_groups"], view_names)
        transforms[f"fold{number}__outer"] = transform
        fit_local, test_local = transform.fit_bag_indices, transform.evaluation_bag_indices
        fit_global, test_global = transform.bag_indices[fit_local], transform.bag_indices[test_local]
        weights = hierarchical_weights(bag_frame.iloc[fit_global])
        final_models = {}
        for view in view_names:
            lam = choices[view]
            fit_context = dict(context or {}, packet="N2R", outer_fold=number, stage="outer",
                               view=view, lambda_l2=lam)
            key = f"fold{number}__outer__{view}"
            if lam is None:
                models[key] = None
                diagnostics.append(dict(fit_context, success=False, status="INCOMPLETE_INNER_GRID", attempt_count=0))
                continue
            X = transform.views[view]
            model = fit_logistic(X[fit_local], y[fit_global], weights, lam, ledger=ledger, context=fit_context)
            final_models[view] = model
            models[key] = model
            predictions.loc[test_global, view] = model.predict_proba(X[test_local])
            diagnostics.append(dict(fit_context, **model.diagnostics))
        if "HQ" in view_names and "HQQ" in view_names:
            if choices["HQ"] != choices["HQQ"] or choices["HQ"] is None:
                controls.append({"outer_fold": number, "stage": "outer",
                                 "status": "LAMBDA_SELECTION_DISAGREEMENT_OR_FAILURE",
                                 "HQ_lambda": choices["HQ"], "HQQ_lambda": choices["HQQ"]})
            elif "HQ" in final_models and "HQQ" in final_models:
                controls.append(_equivalence(final_models["HQ"], final_models["HQQ"], transform.views["HQ"],
                    transform.views["HQQ"], outer_fold=number, stage="outer", lambda_l2=choices["HQ"]))
    expected = len(folds) * len(view_names) * 10
    if len(diagnostics) != expected or len(transforms) != 4 * len(folds):
        raise AssertionError("N2R fit catalog or transform-cache count changed")
    tested_folds = [int(fold["outer_fold"]) for fold in folds]
    predictions = predictions.loc[predictions.outer_fold.isin(tested_folds)].reset_index(drop=True)
    summary, identities = paired_contrasts(predictions, {v: v for v in view_names}, _contrasts(view_names),
                                           repetitions=bootstrap_repetitions)
    complete = all(item["success"] for item in diagnostics)
    primary = summary["contrasts"].get("HQ_minus_HQV")
    summary.update(packet="N2R", risk_unit="bits_per_bag", population="P_MATCH_bal",
        execution="COMPLETE" if complete else "NUMERICAL_FAIL", support="PASS",
        primary_status=("PASS" if primary["status"] == "PASS" else "NUMERICAL_FAIL") if primary is not None else "NOT_EVALUABLE",
        research=_research(summary, controls, view_names, len(folds)),
        primary_contrast="HQ_minus_HQV", outer_folds=tested_folds,
        planned_heads=expected, actual_heads=sum(d.get("attempt_count", 0) > 0 for d in diagnostics),
        optimizer_attempts=sum(d.get("attempt_count", 0) for d in diagnostics),
        transform_contexts=len(transforms), view_names=list(view_names),
        incomplete_models=[name for name, metric in summary["metrics"].items() if metric["status"] != "PASS"],
        equivalence_controls=controls, algorithm_hash=n2r_algorithm_hash(),
        bag_size=8, variance_ddof=1, variance_transform="log1p_sample_variance",
        bootstrap_scope="fixed_oof_not_pipeline_refit",
        inference_limitation="Beyond the prespecified quadratic-mean readout family; not exact conditional mutual information")
    return {"summary": summary, "predictions": predictions, "identity_risks": identities,
            "fit_diagnostics": pd.DataFrame(diagnostics), "selections": pd.DataFrame(selections),
            "models": models, "transforms": transforms, "equivalence_controls": controls}


run_bags = run_packet
