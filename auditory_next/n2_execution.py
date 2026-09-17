"""Frozen N2 bag-level execution.

This runner consumes the metadata support freeze and the already audited
feature tasks.  It fits no encoder and never chooses bags or transforms using
test outcomes.  The only fitted coordinates are the trial scaler/PCA/RFF and
the declared readout head, each scoped to the current outer/inner training
groups.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import roc_auc_score

from .features import LegacyFeatureRegistry, audit_inner_scope
from .fitting import fit_cases, predict_logits
from .n2_features import (
    build_bag_features,
    fit_rff16,
    fit_weighted_pca8,
    fit_weighted_scale,
    transform_pca8,
    transform_scale,
)
from .n2_bags import make_n2_bags
from .provenance import ROOT, digest, finish, require_slurm, write_json
from .readouts import calibrate, ce_bits, population_weights


MODES = ("R_SIM", "L0")
WINDOWS = ("post", "pre")
VIEWS = ("H", "HMU", "HMUVAR", "HMUMU", "HVAR", "HRFF")
FAMILIES = {"R_SIM": ("logistic", "mlp32"), "L0": ("logistic",)}
K_MAIN = 8
BOOTSTRAPS = 2000


def _as_groups(values):
    return {str(value) for value in values}


def calibrated_logits(logits, calibration):
    """Apply the frozen temperature and optional prior-mixture calibration."""
    logits = np.asarray(logits, dtype=float)
    temperature = float(calibration.get("temperature", 1.0))
    if temperature <= 0 or not np.isfinite(temperature) or not np.isfinite(logits).all():
        raise ValueError("N2_CALIBRATION_SCHEMA")
    z = logits / temperature
    eta = float(calibration.get("eta", 0.0))
    if not np.isfinite(eta) or eta < 0 or eta > 1:
        raise ValueError("N2_CALIBRATION_SCHEMA")
    if eta == 0:
        return z
    prior = float(calibration.get("training_prior", np.nan))
    if not 0 < prior < 1 or eta > 1:
        raise ValueError("N2_CALIBRATION_SCHEMA")
    l0 = -np.logaddexp(0.0, z)
    l1 = -np.logaddexp(0.0, -z)
    log_false = np.logaddexp(l0 + (np.log1p(-eta) if eta < 1 else -np.inf),
                             np.log(eta * (1 - prior)))
    log_true = np.logaddexp(l1 + (np.log1p(-eta) if eta < 1 else -np.inf),
                            np.log(eta * prior))
    return log_true - log_false


def evaluation_scores(logits, calibration):
    """Keep raw, primary temperature and prior-mixture diagnostic separate."""
    raw = np.asarray(logits, dtype=float)
    return {"raw": raw, "temperature": calibrated_logits(raw, {**calibration, "eta": 0.}),
            "mixture_diagnostic": calibrated_logits(raw, calibration)}


def inner_validation_groups(fold, inner, support_groups):
    """Return only explicitly recorded D-inner groups.

    Missing mappings remain missing; this helper never creates a validation
    fold from an outer split or from the feature rows.
    """
    if inner is None:
        return set()
    mapping = fold.get("D_inner_fold_by_group", {})
    return {str(group) for group, number in mapping.items()
            if int(number) == int(inner) and str(group) in _as_groups(support_groups)}


def expected_case_count(task_catalog: pd.DataFrame, *, smoke=False):
    """Count the frozen N2 head cases without inspecting any model output."""
    required = {"packet", "mode", "family", "view", "window", "fit_stage"}
    if not required.issubset(task_catalog.columns):
        raise ValueError("N2_TASK_CATALOG_SCHEMA")
    selected = task_catalog.loc[
        task_catalog["packet"].eq("N2") & task_catalog["mode"].isin(MODES) &
        task_catalog["family"].isin(tuple(sorted({f for fs in FAMILIES.values() for f in fs}))) &
        task_catalog["view"].isin(VIEWS) & task_catalog["window"].isin(WINDOWS) &
        task_catalog["fit_stage"].isin(("inner", "final"))
    ]
    if smoke:
        return 0
    return int(len(selected))


def _loss_by_candidate(rows, logits, population):
    rows = rows.reset_index(drop=True)
    logits = np.asarray(logits, dtype=float)
    if len(rows) != len(logits) or not np.isfinite(logits).all():
        raise ValueError("N2_PREDICTION_ALIGNMENT")
    pieces = []
    for candidate, part in rows.assign(logit=logits).groupby("candidate_id", sort=True):
        y = part.stimulus_local_id.to_numpy(int)
        groups = np.full(len(part), str(candidate), dtype=str)
        weights = population_weights(y, groups, population)
        z=part.logit.to_numpy(float);prob=expit(z);prediction=z>=0
        pieces.append({"candidate_id": str(candidate),
                       "loss_bits_per_bag": ce_bits(z, y, weights),
                       "bacc":float(.5*np.mean(~prediction[y==0])+.5*np.mean(prediction[y==1])),
                       "auroc":float(roc_auc_score(y,z)),
                       "brier_two_class_sum":float(np.average(2*(prob-y)**2,weights=weights)),
                       "n_bags": int(len(part))})
    return pd.DataFrame(pieces)


def paired_bootstrap_gain(losses: pd.DataFrame, first: str, second: str,
                          *, n_boot=BOOTSTRAPS, seed=20260917):
    """Cluster-bootstrap a paired loss difference across candidates.

    ``losses`` is one row per candidate and contains loss columns.  Missing
    candidates are dropped only from this explicitly paired contrast and are
    reported through ``n_candidates``; no favorable replicate regeneration is
    performed.
    """
    if int(n_boot) < 1:
        raise ValueError("N2_BOOTSTRAP_COUNT")
    if not {"candidate_id", first, second}.issubset(losses.columns):
        return None
    table = losses[["candidate_id", first, second]].copy()
    table[first] = pd.to_numeric(table[first], errors="coerce")
    table[second] = pd.to_numeric(table[second], errors="coerce")
    table = table.dropna()
    if table.candidate_id.duplicated().any() or len(table) < 2:
        return None
    difference = (table[first] - table[second]).to_numpy(float)
    if not np.isfinite(difference).all():
        return None
    rng = np.random.default_rng(int(seed))
    indices = rng.integers(0, len(difference), size=(int(n_boot), len(difference)))
    boot = difference[indices].mean(axis=1)
    return {
        "first": first,
        "second": second,
        "estimate": float(difference.mean()),
        "ci_lower": float(np.quantile(boot, .025)),
        "ci_upper": float(np.quantile(boot, .975)),
        "n_candidates": int(len(difference)),
        "n_bootstrap": int(n_boot),
        "units": "bits_per_bag",
        "bootstrap_scope": "candidate_cluster_fixed_oof_no_refit",
    }


def paired_window_gain(post: pd.DataFrame, pre: pd.DataFrame, *, seed=20260917):
    """Compare a post/pre gain on the shared candidate support."""
    if post.empty or pre.empty:
        return None
    required = {"candidate_id", "HMU", "HMUVAR"}
    if not required.issubset(post.columns) or not required.issubset(pre.columns):
        return None
    joined = post[["candidate_id", "HMU", "HMUVAR"]].merge(
        pre[["candidate_id", "HMU", "HMUVAR"]], on="candidate_id", suffixes=("_post", "_pre"))
    if joined.empty or joined.candidate_id.duplicated().any():
        return None
    post_gain = joined.HMU_post.to_numpy(float) - joined.HMUVAR_post.to_numpy(float)
    pre_gain = joined.HMU_pre.to_numpy(float) - joined.HMUVAR_pre.to_numpy(float)
    difference = post_gain - pre_gain
    if len(difference) < 2 or not np.isfinite(difference).all():
        return None
    rng = np.random.default_rng(int(seed))
    indices = rng.integers(0, len(difference), size=(BOOTSTRAPS, len(difference)))
    boot = difference[indices].mean(axis=1)
    return {"first": "post_gain", "second": "pre_gain",
            "estimate": float(difference.mean()),
            "ci_lower": float(np.quantile(boot, .025)),
            "ci_upper": float(np.quantile(boot, .975)),
            "n_candidates": int(len(difference)), "n_bootstrap": BOOTSTRAPS,
            "units": "bits_per_bag",
            "bootstrap_scope": "shared_candidate_fixed_oof_no_refit"}


def frozen_test_partition_seeds(*, n=10, seed=20260917):
    """Freeze sensitivity partition identities without scheduling refits."""
    if int(n) < 1:
        raise ValueError("N2_PARTITION_COUNT")
    return [int(seed) + i for i in range(int(n))]


def common_sensitivity_candidates(partitions, required=None):
    """Return the fixed candidate intersection used by every sensitivity seed."""
    sets = [set(str(value) for value in values) for values in partitions]
    if not sets:
        return set()
    common = set.intersection(*sets)
    if required is not None:
        common &= {str(value) for value in required}
    return common


def _view_matrix(bag_features, view):
    """Construct a view from the same bag IDs and no current label fields."""
    if view not in VIEWS:
        raise ValueError("N2_VIEW")
    h = np.asarray(bag_features["H_BAG"], dtype=float)
    if view == "H":
        result = h
    elif view == "HMU":
        result = np.c_[h, bag_features["MU"]]
    elif view == "HMUVAR":
        result = np.c_[h, bag_features["MU_VAR"]]
    elif view == "HMUMU":
        result = np.c_[h, bag_features["MU_DUP"]]
    elif view == "HVAR":
        result = np.c_[h, bag_features["VAR"]]
    else:
        result = np.c_[h, bag_features["RFF_MEAN"]]
    if result.ndim != 2 or not np.isfinite(result).all():
        raise ValueError("N2_VIEW_NONFINITE")
    return result


def _resolve_feature_task(features, *, mode, fold, inner):
    # L0 has no fitted encoder and deliberately reuses the explicit outer-bin
    # feature task for inner heads. R_SIM uses the recorded D-inner encoder.
    stage = "outer" if mode == "L0" or inner is None else "D_inner"
    task = features.resolve_task(stage=stage, mode=mode, branch="all",
                                 outer_fold=int(fold["outer_fold"]), inner_fold=None if mode=='L0' else inner)
    scope = features.scope_for(task)
    if scope.get("status") != "PASS":
        raise ValueError("N2_FEATURE_SCOPE_NOT_PASS")
    if scope.get("stage") != stage or scope.get("mode") != mode:
        raise ValueError("N2_FEATURE_SCOPE_MISMATCH")
    return task, scope


def _load_features(features, task, planpath, inventory):
    folder = planpath.parent / "outputs" / task["name"]
    for filename in ("features.npz", "feature_rows.parquet"):
        path = folder / filename
        expected = inventory.get(str(path))
        if expected is None:
            raise ValueError("N2_FEATURE_HASH_MISSING")
        if digest(path) != expected:
            raise ValueError("N2_FEATURE_INPUT_MUTATION")
    data = features.load_features(task, planpath.parent / "outputs")
    rows = pd.DataFrame(data["rows"])
    if not rows.trial_id.is_unique:
        raise ValueError("N2_FEATURE_DUPLICATE_TRIAL")
    return data, rows


def _prepare_history(frame):
    required = {"trial_id", "previous_code", "previous_run_bin", "previous_gap_s",
                "segment_position_fraction", "A_block_id", "onset_sample", "original_fs"}
    if not required.issubset(frame.columns):
        raise ValueError("N2_HISTORY_SUPPORT_SCHEMA")
    history = frame.copy()
    history["position_fraction"] = pd.to_numeric(history.segment_position_fraction, errors="coerce")
    if history.trial_id.duplicated().any() or history.trial_id.isna().any():
        raise ValueError("N2_HISTORY_DUPLICATE_TRIAL")
    return history


def _prepare_bags(bags, history, k=K_MAIN):
    required = {"bag_id", "trial_id", "candidate_id", "split_group_id", "stimulus_local_id", "k"}
    if not required.issubset(bags.columns) or bags.empty:
        raise ValueError("N2_BAG_SUPPORT_SCHEMA")
    bags = bags.copy()
    if bags.k.nunique() != 1 or int(bags.k.iloc[0]) != int(k):
        raise ValueError("N2_MAIN_K_MISMATCH")
    if bags.trial_id.duplicated().any() or bags.bag_id.isna().any():
        raise ValueError("N2_BAG_OVERLAP")
    grouped = bags.groupby("bag_id", sort=True)
    meta = grouped.agg(candidate_id=("candidate_id", "first"),
                        split_group_id=("split_group_id", "first"),
                        stimulus_local_id=("stimulus_local_id", "first"),
                        n_trials=("trial_id", "size"),
                        n_candidates=("candidate_id", "nunique"),
                        n_labels=("stimulus_local_id", "nunique"))
    if (meta.n_trials != int(k)).any() or (meta.n_candidates != 1).any() or (meta.n_labels != 1).any():
        raise ValueError("N2_BAG_METADATA_MISMATCH")
    if not set(bags.trial_id.astype(str)).issubset(set(history.trial_id.astype(str))):
        raise ValueError("N2_BAG_HISTORY_ALIGNMENT")
    return bags, meta.reset_index()


def _trial_projection(x, feature_rows, bags, fit_groups):
    rows = feature_rows.copy()
    rows["_trial_key"] = rows.trial_id.astype(str)
    if rows["_trial_key"].duplicated().any():
        raise ValueError("N2_FEATURE_DUPLICATE_TRIAL")
    bag_trials = set(bags.trial_id.astype(str))
    if not bag_trials.issubset(set(rows["_trial_key"])):
        raise ValueError("N2_BAG_FEATURE_ALIGNMENT")
    fit_mask = rows["split_group_id"].astype(str).isin(_as_groups(fit_groups)).to_numpy()
    if not fit_mask.any():
        raise ValueError("N2_EMPTY_TRIAL_FIT")
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or len(x) != len(rows) or not np.isfinite(x).all():
        raise ValueError("N2_FEATURE_ARRAY_ALIGNMENT")
    scaler = fit_weighted_scale(x[fit_mask], rows.loc[fit_mask, "candidate_id"].astype(str))
    pca = fit_weighted_pca8(x[fit_mask], rows.loc[fit_mask, "candidate_id"].astype(str), scaler=scaler)
    projected = transform_pca8(x, pca)
    rff = fit_rff16(projected[fit_mask], seed=11, pair_budget=4096)
    return projected, rff, {"scaler": scaler, "pca": pca, "rff": rff,
                            "fit_groups": sorted(_as_groups(fit_groups)),
                            "fit_n_trials": int(fit_mask.sum())}


def _make_case(case_id, matrix, meta, fit_groups, val_groups, test_groups,
               feature_scope_id, family, view, mode, fold, inner, window):
    fit_mask = meta.split_group_id.astype(str).isin(_as_groups(fit_groups)).to_numpy()
    eval_groups = val_groups if inner is not None else test_groups
    eval_mask = meta.split_group_id.astype(str).isin(_as_groups(eval_groups)).to_numpy()
    if not fit_mask.any() or not eval_mask.any():
        raise ValueError("N2_EMPTY_BAG_SCOPE")
    y = meta.stimulus_local_id.to_numpy(int)
    candidate = meta.candidate_id.astype(str).to_numpy()
    weights = population_weights(y[fit_mask], candidate[fit_mask], "P_bal")
    scope = {"fit_groups": sorted(_as_groups(fit_groups)),
             "validation_groups": sorted(_as_groups(val_groups)),
             "test_groups": sorted(_as_groups(test_groups))}
    return {
        "id": case_id, "family": family, "view": view, "mode": mode,
        "outer_fold": int(fold), "inner_fold": inner, "window": window,
        "x": matrix[fit_mask], "y": y[fit_mask], "weights": weights,
        "scope": scope, "feature_scope_id": str(feature_scope_id),
        "width": 32, "C": 1.0, "lam": 0.001,
    }, {
        "x": matrix[eval_mask], "rows": meta.loc[eval_mask].reset_index(drop=True),
        "scope": scope, "mode": mode, "population": "P_bal", "family": family,
        "view": view, "outer_fold": int(fold), "inner_fold": inner, "window": window,
    }


def _sensitivity_source_rows(history, test_groups):
    required = {"trial_id", "candidate_id", "record_id", "segment_id", "split_group_id",
                "stimulus_local_id", "A_half", "A_block_id", "accepted"}
    if not required.issubset(history.columns):
        raise ValueError("N2_SENSITIVITY_HISTORY_SCHEMA")
    boundary = "v2_context_boundary_eligible"
    if boundary not in history:
        raise ValueError("N2_SENSITIVITY_BOUNDARY_SCHEMA")
    source = history.loc[
        history.accepted.astype(bool) & history.stimulus_local_id.isin([0, 1]) &
        history.A_half.notna() & history.split_group_id.astype(str).isin(_as_groups(test_groups)),
        ["trial_id", "candidate_id", "record_id", "segment_id", "split_group_id",
         "stimulus_local_id", "A_half", "A_block_id", boundary]
    ].copy()
    source["A_half"] = source["A_half"].astype(int)
    source["A_block_id"] = source["A_block_id"].astype(int)
    source["A_boundary_eligible"] = source[boundary].fillna(False).astype(bool)
    return source.drop(columns=[boundary])


def _final_case_index(cases):
    return {case["id"]: case for case in cases if case["inner_fold"] is None}


def _calibration_index(rows):
    return {(row["mode"], int(row["outer_fold"]), row["window"], row["family"], row["view"]): row
            for row in rows}


def _run_test_sensitivities(*, features, planpath, inventory, folds, history, original_bags,
                            original_meta, transforms, cases, models, receipts, calibrations,
                            support_run, config, dest, public):
    """Evaluate ten test-only partitions with frozen transforms and heads."""
    seeds = frozen_test_partition_seeds(
        n=int(config.get("N2", {}).get("sensitivity_test_partitions", 10)))
    final_cases = _final_case_index(cases)
    receipt_index = {row["fit_id"]: row for row in receipts}
    calibration_index = _calibration_index(calibrations)
    complete_family = {}
    for mode in MODES:
        for family in FAMILIES[mode]:
            ids = [case["id"] for case in cases if case["mode"] == mode and case["family"] == family]
            complete_family[(mode, family)] = bool(ids) and all(
                receipt_index[case_id]["numerical_status"] == "OPTIMIZATION_STABLE" for case_id in ids)
    detailed, summaries, support_receipts = [], [], []
    for fold in folds:
        number = int(fold["outer_fold"])
        test_groups = _as_groups(fold["test_groups"]) & set(original_meta.split_group_id.astype(str))
        original_candidates = set(original_meta.loc[
            original_meta.split_group_id.astype(str).isin(test_groups), "candidate_id"].astype(str))
        source = _sensitivity_source_rows(history, test_groups)
        partitions, partition_meta = [], []
        for seed in seeds:
            rebuilt, unused = make_n2_bags(source, k=K_MAIN, seed=seed)
            if rebuilt.empty:
                partitions.append(set())
                partition_meta.append((seed, rebuilt, unused))
                continue
            rebuilt, meta = _prepare_bags(rebuilt, history)
            complete = meta.groupby("candidate_id", sort=False).stimulus_local_id.nunique()
            partitions.append(set(complete.index[complete.eq(2)].astype(str)))
            partition_meta.append((seed, rebuilt, unused))
        common = common_sensitivity_candidates(partitions, required=original_candidates)
        for (seed, rebuilt, unused), candidates in zip(partition_meta, partitions):
            support_receipts.append(dict(outer_fold=number, seed=int(seed),
                                         n_bags=int(rebuilt.bag_id.nunique()) if not rebuilt.empty else 0,
                                         n_trials=int(len(rebuilt)), n_unused=int(len(unused)),
                                         n_candidates_with_both_classes=int(len(candidates)),
                                         n_common_candidates=int(len(common)),
                                         original_test_candidates=int(len(original_candidates))))
        if len(common) < 2:
            continue
        for seed, sensitivity_bags, unused in partition_meta:
            if sensitivity_bags.empty:
                continue
            sensitivity_bags = sensitivity_bags.loc[
                sensitivity_bags.candidate_id.astype(str).isin(common)].reset_index(drop=True)
            if sensitivity_bags.empty:
                continue
            sensitivity_meta = sensitivity_bags.groupby("bag_id", sort=True).agg(
                candidate_id=("candidate_id", "first"), split_group_id=("split_group_id", "first"),
                stimulus_local_id=("stimulus_local_id", "first"), n_trials=("trial_id", "size"),
                n_candidates=("candidate_id", "nunique"), n_labels=("stimulus_local_id", "nunique")).reset_index()
            for mode in MODES:
                for window in WINDOWS:
                    task, scope = _resolve_feature_task(features, mode=mode, fold=fold, inner=None)
                    data, feature_rows = _load_features(features, task, planpath, inventory)
                    transform = transforms[f"{mode}_f{number}_iNone_{window}"]
                    projected = transform_pca8(data["z" + window], transform["pca"])
                    bag_features = build_bag_features(projected, feature_rows, sensitivity_bags,
                                                       h_rows=history, known_codes=("1", "2"),
                                                       rff_fit=transform["rff"])
                    by_id = {str(row.bag_id): row for row in sensitivity_meta.itertuples()}
                    ordered_meta = pd.DataFrame([by_id[str(b)] for b in bag_features["bag_ids"]])
                    for family in FAMILIES[mode]:
                        if not complete_family.get((mode, family), False):
                            continue
                        for view in VIEWS:
                            final_id = f"N2_{mode}_f{number}_iNone_{window}_{view}_{family}"
                            model = models.get(final_id)
                            if model is None:
                                continue
                            case = final_cases[final_id]
                            head_scaler = case.get("head_scaler")
                            if head_scaler is None:
                                raise ValueError("N2_SENSITIVITY_HEAD_SCALER_MISSING")
                            raw = _view_matrix(bag_features, view)
                            matrix = transform_scale(raw, head_scaler)
                            calibration = calibration_index.get((mode, number, window, family, view))
                            if calibration is None:
                                raise ValueError("N2_SENSITIVITY_CALIBRATION_MISSING")
                            logits = calibrated_logits(predict_logits(model, matrix), {**calibration,'eta':0.})
                            rows = ordered_meta.copy()
                            rows["logit"] = logits
                            candidate_loss = _loss_by_candidate(rows, logits, "P_bal")
                            candidate_loss["mode"] = mode; candidate_loss["outer_fold"] = number
                            candidate_loss["window"] = window; candidate_loss["family"] = family
                            candidate_loss["view"] = view; candidate_loss["seed"] = int(seed)
                            detailed.append(candidate_loss)
        # Candidate support is fixed before any seed's effect is inspected.
        # The loop above records all views; effects are calculated below.
    if not detailed:
        write_json(dest / "test_sensitivity_support.json", support_receipts)
        return dict(status="SENSITIVITY_SUPPORT_INSUFFICIENT", seeds=seeds,
                    n_rows=0, n_common_fold_supports=0)
    detail = pd.concat(detailed, ignore_index=True)
    write_json(dest / "test_sensitivity_support.json", support_receipts)
    detail.to_parquet(dest / "test_sensitivity_candidate_losses.parquet", index=False)
    averaged=detail.groupby(['mode','window','family','view','candidate_id'],sort=True).loss_bits_per_bag.mean().reset_index()
    global_sensitivity=[]
    for (mode,window,family),part in averaged.groupby(['mode','window','family']):
        wide=part.pivot(index='candidate_id',columns='view',values='loss_bits_per_bag').reset_index()
        for first,second,name in (('HMU','HMUVAR','gain_mu_var'),('HMUMU','HMUVAR','mv_vs_dup')):
            effect=paired_bootstrap_gain(wide,first,second)
            if effect:global_sensitivity.append(dict(mode=mode,window=window,family=family,effect=name,calibration='temperature',**effect))
    pd.DataFrame(global_sensitivity).to_csv(public/'test_sensitivity_averaged_effects.csv',index=False)
    for keys, part in detail.groupby(["mode", "outer_fold", "window", "family", "seed"], sort=True):
        wide = part.pivot(index="candidate_id", columns="view", values="loss_bits_per_bag").reset_index()
        for first, second, name in (("HMU", "HMUVAR", "gain_mu_var"),
                                    ("HMUMU", "HMUVAR", "mv_vs_dup")):
            effect = paired_bootstrap_gain(wide, first, second)
            if effect:
                summaries.append(dict(mode=keys[0], outer_fold=int(keys[1]), window=keys[2],
                                      family=keys[3], seed=int(keys[4]), effect=name, **effect,
                                      partition_scope="test_only_common_candidate_intersection",
                                      head_refit=False))
    sensitivity = pd.DataFrame(summaries)
    sensitivity.to_csv(public / "test_sensitivity_gains.csv", index=False)
    if not sensitivity.empty:
        aggregate = sensitivity.groupby(["mode", "outer_fold", "window", "family", "effect"], sort=True).agg(
            seeds=("seed", "nunique"), mean_estimate=("estimate", "mean"), sd_estimate=("estimate", "std"),
            min_estimate=("estimate", "min"), max_estimate=("estimate", "max"),
            min_n_candidates=("n_candidates", "min")).reset_index()
        aggregate["selection_of_seed"] = False
        aggregate["head_refits"] = 0
        aggregate.to_csv(public / "test_sensitivity_summary.csv", index=False)
    return dict(status="SENSITIVITY_RECORDED", seeds=seeds, n_rows=int(len(detail)),
                n_effect_rows=int(len(sensitivity)), n_common_fold_supports=int(detail[["outer_fold"]].drop_duplicates().shape[0]),
                head_refits=0, selected_seed=None)


def run(config, registry, site, dest, public, report, task_plan, *, smoke=False):
    """Run the frozen N2 core; smoke stops after first-fold transforms."""
    require_slurm()
    dest, public, report = map(Path, (dest, public, report))
    if not dest.resolve().is_relative_to(ROOT / "private/auditory_next_v2"):
        raise ValueError("N2_PRIVATE_OUTPUT_REQUIRED")
    if not public.resolve().is_relative_to(ROOT / "results/auditory_next_v2"):
        raise ValueError("N2_PUBLIC_OUTPUT_REQUIRED")
    if any(path.exists() for path in (dest / "completion.json", public / "summary.json")):
        raise FileExistsError("N2_RUN_ALREADY_STARTED")

    support_run = str(task_plan.get("support_run", ""))
    if not support_run or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in support_run):
        raise ValueError("N2_SUPPORT_RUN")
    support = ROOT / "private/auditory_next_v2" / support_run
    completion_path = support / "completion.json"
    completion = json.loads(completion_path.read_text())
    if completion.get("status") != "PASS":
        raise ValueError("N2_SUPPORT_GATE")
    definition = json.loads((support / "support_definition.json").read_text())
    if definition.get("frozen_before_features") is not True:
        raise ValueError("N2_SUPPORT_NOT_FROZEN")
    history = _prepare_history(pd.read_parquet(support / "full_event_history.parquet"))
    bags, bag_meta = _prepare_bags(pd.read_parquet(support / "N2_k8_bags.parquet"), history)
    n2_groups = json.loads((support / "N2_groups.json").read_text()).get("by_k", {}).get("8", [])
    if not set(bag_meta.split_group_id.astype(str)).issubset(_as_groups(n2_groups)):
        raise ValueError("N2_BAG_GROUP_GATE")

    planpath = ROOT / registry["legacy_plan"]
    splitpath = ROOT / registry["legacy_splits"]
    if digest(planpath) != registry["legacy_plan_sha256"] or digest(splitpath) != registry["legacy_split_sha256"]:
        raise ValueError("N2_LEGACY_SOURCE_HASH")
    folds = json.loads(splitpath.read_text())["folds"]
    gate = ROOT / "private/auditory_next_v2" / str(task_plan["preflight_run"])
    inventory_rows = json.loads((gate / "legacy_input_hashes.json").read_text())
    inventory = {str(row["path"]): row["sha256"] for row in inventory_rows}
    scope_path = gate / "feature_scope_registry.json"
    features = LegacyFeatureRegistry.from_files(planpath, scope_path)
    catalog = pd.read_csv(task_plan["task_csv"])
    expected = expected_case_count(catalog, smoke=smoke)
    hashes = {str(path): digest(path) for path in
              (completion_path, support / "support_definition.json", support / "N2_groups.json",
               support / "N2_k8_bags.parquet", support / "full_event_history.parquet", planpath, splitpath,
               scope_path)}
    write_json(dest / "input_hashes.json", hashes)
    write_json(dest / "support_definition.json", definition)

    cases, evaluations, transforms, case_receipts = [], {}, {}, []
    first_fold_done = False
    for mode in MODES:
        for fold in folds:
            fold_number = int(fold["outer_fold"])
            support_groups = set(bag_meta.split_group_id.astype(str))
            outer_train = _as_groups(fold["train_groups"]) & support_groups
            outer_test = _as_groups(fold["test_groups"]) & support_groups
            if len(outer_train) < 2 or len(outer_test) < 1:
                raise ValueError("N2_OUTER_SUPPORT")
            inner_values = (0,) if smoke else (0, 1, 2, None)
            for inner in inner_values:
                val = inner_validation_groups(fold, inner, support_groups)
                if inner is not None and not val:
                    continue
                train = outer_train - val
                task, scope = _resolve_feature_task(features, mode=mode, fold=fold, inner=inner)
                data, feature_rows = _load_features(features, task, planpath, inventory)
                actual_fit_groups = data.get("actual_fit_groups", scope.get("fit_groups", []))
                if mode == "R_SIM" and inner is not None:
                    audit_inner_scope(scope, val, actual_fit_groups, fold["train_groups"])
                if _as_groups(actual_fit_groups) & outer_test:
                    raise ValueError("N2_ENCODER_OUTER_TEST_LEAKAGE")
                if mode=='R_SIM' and inner is not None and not val.issubset(_as_groups(scope.get("validation_groups", []))):
                    raise ValueError("N2_UNRECORDED_VALIDATION")
                for window in WINDOWS:
                    if data.get("z" + window) is None:
                        raise ValueError("N2_FEATURE_WINDOW_MISSING")
                    projected, rff, transform = _trial_projection(data["z" + window], feature_rows, bags, train)
                    bag_features = build_bag_features(
                        projected, feature_rows, bags, h_rows=history,
                        known_codes=("1", "2"), rff_fit=rff)
                    transforms[f"{mode}_f{fold_number}_i{inner}_{window}"] = transform
                    if set(bag_features["bag_ids"]) != set(bag_meta.bag_id.astype(str)):
                        raise ValueError("N2_BAG_ID_MATRIX_MISMATCH")
                    by_id = {str(row.bag_id): row for row in bag_meta.itertuples()}
                    ordered_meta = pd.DataFrame([by_id[str(b)] for b in bag_features["bag_ids"]])
                    if not np.array_equal(ordered_meta.bag_id.astype(str), bag_features["bag_ids"]):
                        raise ValueError("N2_BAG_ORDER_MISMATCH")
                    for view in VIEWS:
                        raw_matrix = _view_matrix(bag_features, view)
                        head_scaler = fit_weighted_scale(raw_matrix[
                            ordered_meta.split_group_id.astype(str).isin(train).to_numpy()],
                            ordered_meta.loc[ordered_meta.split_group_id.astype(str).isin(train), "candidate_id"].astype(str))
                        matrix = transform_scale(raw_matrix, head_scaler)
                        for family in FAMILIES[mode]:
                            case_id = f"N2_{mode}_f{fold_number}_i{inner}_{window}_{view}_{family}"
                            case, evaluation = _make_case(case_id, matrix, ordered_meta, train, val, outer_test,
                                                           scope.get("feature_scope_id", task["name"]), family, view,
                                                           mode, fold_number, inner, window)
                            case["head_scaler"] = head_scaler
                            cases.append(case)
                            evaluations[case_id] = evaluation
                    first_fold_done = True
                if smoke and first_fold_done:
                    break
            if smoke and first_fold_done:
                break
        if smoke and first_fold_done:
            break

    if smoke:
        write_json(dest / "case_manifest.json", [])
        with (dest / "transforms.pkl").open("xb") as stream:
            pickle.dump(transforms, stream)
        (report / "N2_REPORT.md").write_text(
            "# N2 metadata and transform smoke\n\n"
            "The first explicit outer/inner support scope was aligned to frozen k=8 bags. "
            "No readout or test evaluation was fitted in smoke mode; complete matrix status remains pending.\n",
            encoding="utf-8")
        return finish(dest, public, dict(status="PASS", support_run=support_run,
                                         prepared_cases=len(cases), encoder_fits=0, readout_fits=0,
                                         scientific_status="NOT_EVALUABLE"))

    if len(cases) != expected:
        raise ValueError("N2_TASK_PLAN_CASE_COUNT")
    write_json(dest / "case_manifest.json", [
        {key: case[key] for key in ("id", "family", "view", "mode", "outer_fold", "inner_fold", "window",
                                     "scope", "feature_scope_id")}
        for case in cases])
    with (dest / "transforms.pkl").open("xb") as stream:
        pickle.dump(transforms, stream)
    fit_input = [{key: case[key] for key in ("id", "family", "x", "y", "weights", "scope", "feature_scope_id", "width", "C", "lam")}
                 for case in cases]
    models, receipts = fit_cases(fit_input, dest / "fits", device="cuda", expected_fits=expected)
    receipt_by_id = {row["fit_id"]: row for row in receipts}
    complete_family = {}
    for mode in MODES:
        for family in FAMILIES[mode]:
            family_ids = [case["id"] for case in cases
                          if case["mode"] == mode and case["family"] == family]
            complete_family[(mode, family)] = bool(family_ids) and all(
                receipt_by_id[case_id]["numerical_status"] == "OPTIMIZATION_STABLE"
                for case_id in family_ids)
    prediction_rows, loss_rows, calibration_rows = [], [], []
    for mode in MODES:
        for fold in folds:
            number = int(fold["outer_fold"])
            for window in WINDOWS:
                for family in FAMILIES[mode]:
                    for view in VIEWS:
                        final_id = f"N2_{mode}_f{number}_iNone_{window}_{view}_{family}"
                        if not complete_family.get((mode, family), False) or final_id not in models:
                            continue
                        inner_ids = [case_id for case_id, evaluation in evaluations.items()
                                     if evaluation["mode"] == mode and evaluation["outer_fold"] == number and
                                     evaluation["window"] == window and evaluation["view"] == view and
                                     evaluation["family"] == family and evaluation["inner_fold"] is not None and
                                     case_id in models]
                        calibration = None
                        if inner_ids:
                            oof = []
                            for case_id in sorted(inner_ids):
                                evaluation = evaluations[case_id]
                                if not receipt_by_id[case_id]["numerical_status"] == "OPTIMIZATION_STABLE":
                                    continue
                                oof.append((evaluation, predict_logits(models[case_id], evaluation["x"])))
                            if oof:
                                rows = pd.concat([entry[0]["rows"] for entry in oof], ignore_index=True)
                                if rows.bag_id.duplicated().any():
                                    raise ValueError("N2_INNER_OOF_DUPLICATE")
                                logits = np.concatenate([entry[1] for entry in oof])
                                weights = population_weights(rows.stimulus_local_id.to_numpy(int),
                                                              rows.candidate_id.astype(str).to_numpy(), "P_bal")
                                final_case_for_prior = next(case for case in cases if case["id"] == final_id)
                                training_prior = float(np.average(final_case_for_prior["y"],
                                                                  weights=final_case_for_prior["weights"]))
                                calibration = calibrate(logits, rows.stimulus_local_id.to_numpy(int), weights,
                                                        training_prior=training_prior)
                                calibration.update(mode=mode, outer_fold=number, window=window,
                                                   family=family, view=view,
                                                   inner_groups=sorted({str(g) for entry in oof for g in
                                                                        entry[0]["rows"].split_group_id}),
                                                   status="PARTIAL_COVERAGE_ENCODER_ISOLATED_INNER_OOF")
                        if calibration is None:
                            case = next(case for case in cases if case["id"] == final_id)
                            calibration = dict(temperature=1.0, eta=0.0,
                                               training_prior=float(np.average(case["y"], weights=case["weights"])),
                                               mode=mode, outer_fold=number, window=window,
                                               family=family, view=view, inner_groups=[],
                                               status="UNCALIBRATED_FIXED_NO_COMPLETE_INNER_OOF")
                        calibration_rows.append(calibration)
                        evaluation = evaluations[final_id]
                        logits = predict_logits(models[final_id], evaluation["x"])
                        for kind, scores in evaluation_scores(logits, calibration).items():
                            rows = evaluation["rows"].copy()
                            rows['logit']=scores
                            rows['mode']=mode;rows['outer_fold']=number;rows['window']=window
                            rows['family']=family;rows['view']=view;rows['calibration']=kind
                            prediction_rows.append(rows)
                            candidate_loss=_loss_by_candidate(rows,rows.logit.to_numpy(float),'P_bal')
                            candidate_loss=candidate_loss.assign(mode=mode,outer_fold=number,window=window,family=family,view=view,calibration=kind)
                            loss_rows.append(candidate_loss)
    if not loss_rows:
        raise ValueError("N2_NO_COMPLETED_FINAL_HEADS")
    losses = pd.concat(loss_rows, ignore_index=True)
    predictions = pd.concat(prediction_rows, ignore_index=True)
    predictions.to_parquet(dest / "oof_predictions.parquet", index=False)
    losses.to_parquet(dest / "candidate_losses.parquet", index=False)
    write_json(dest / "calibration.json", calibration_rows)
    metrics = []
    for keys, part in losses.groupby(["mode", "outer_fold", "window", "family", "calibration"], sort=True):
        wide = part.pivot(index="candidate_id", columns="view", values="loss_bits_per_bag").reset_index()
        for first, second, name in (("HMU", "HMUVAR", "gain_mu_var"),
                                    ("HMUMU", "HMUVAR", "mv_vs_dup")):
            effect = paired_bootstrap_gain(wide, first, second)
            if effect:
                metrics.append(dict(mode=keys[0], outer_fold=int(keys[1]), window=keys[2],
                                    family=keys[3], calibration=keys[4], effect=name, **effect))
    for keys, part in losses.groupby(["mode", "outer_fold", "family", "calibration"], sort=True):
        post = part.loc[part.window.eq("post")].pivot(index="candidate_id", columns="view",
                                                       values="loss_bits_per_bag").reset_index()
        pre = part.loc[part.window.eq("pre")].pivot(index="candidate_id", columns="view",
                                                      values="loss_bits_per_bag").reset_index()
        effect = paired_window_gain(post, pre)
        if effect:
            metrics.append(dict(mode=keys[0], outer_fold=int(keys[1]), window="post_minus_pre",
                                family=keys[2], calibration=keys[3], effect="gain_mu_var_post_minus_pre",
                                **effect))
    for (mode,window,family,kind),part in losses.groupby(['mode','window','family','calibration']):
        wide=part.pivot(index='candidate_id',columns='view',values='loss_bits_per_bag').reset_index()
        if len(wide)!=bag_meta.candidate_id.nunique() or wide.isna().any().any():raise ValueError('N2_INCOMPLETE_MAIN_CANDIDATE_MATRIX')
        for first,second,name in (('HMU','HMUVAR','gain_mu_var'),('HMUMU','HMUVAR','mv_vs_dup')):
            effect=paired_bootstrap_gain(wide,first,second)
            if effect:metrics.append(dict(mode=mode,outer_fold='ALL',window=window,family=family,calibration=kind,effect=name,**effect))
    for (mode,family,kind),part in losses.groupby(['mode','family','calibration']):
        post=part[part.window.eq('post')].pivot(index='candidate_id',columns='view',values='loss_bits_per_bag').reset_index()
        pre=part[part.window.eq('pre')].pivot(index='candidate_id',columns='view',values='loss_bits_per_bag').reset_index()
        effect=paired_window_gain(post,pre)
        if effect:metrics.append(dict(mode=mode,outer_fold='ALL',window='post_minus_pre',family=family,calibration=kind,effect='gain_mu_var_post_minus_pre',**effect))
    pd.DataFrame(metrics).to_csv(public / "paired_gains.csv", index=False)
    losses.groupby(['mode','window','family','view','calibration'])[['loss_bits_per_bag','bacc','auroc','brier_two_class_sum']].mean().reset_index().to_csv(public/'readout_metrics.csv',index=False)
    coverage = losses.groupby(["mode", "outer_fold", "window", "family", "calibration"], sort=True).candidate_id.nunique().reset_index(name="n_candidates")
    coverage.to_csv(public / "coverage.csv", index=False)
    sensitivity_status = _run_test_sensitivities(
        features=features, planpath=planpath, inventory=inventory, folds=folds,
        history=history, original_bags=bags, original_meta=bag_meta,
        transforms=transforms, cases=cases, models=models, receipts=receipts,
        calibrations=calibration_rows, support_run=support_run, config=config,
        dest=dest, public=public)
    sensitivity_manifest = {
        "seeds": frozen_test_partition_seeds(
            n=int(config.get("N2", {}).get("sensitivity_test_partitions", 10))),
        "refit_each_partition": False,
    }
    sensitivity_manifest.update(sensitivity_status)
    write_json(dest / "sensitivity_partitions.json", sensitivity_manifest)
    (report / "N2_REPORT.md").write_text(
        "# N2 core matrix\n\n"
        "The fixed k=8 bag matrix uses candidate-scoped training transforms and explicit outer/inner feature scopes. "
        "R_SIM inner transforms use recorded D-inner encoder scopes; L0 inner heads reuse outer-bin features. "
        "Calibration uses only available declared inner OOF groups. Ten test-only no-refit regroupings are recorded "
        "as a conditional algorithmic sensitivity; synthetic controls remain pending before any supported scientific claim.\n",
        encoding="utf-8")
    return finish(dest, public, dict(status="CORE_MATRIX_RECORDED", support_run=support_run,
                                     k=K_MAIN, cases=len(cases), readout_fits=len(receipts),
                                     completed_fits=sum(r["numerical_status"] == "OPTIMIZATION_STABLE" for r in receipts),
                                     scientific_status="NOT_SUPPORTED_CONTROLS_PENDING",
                                     pending_controls=["synthetic N2 controls"],
                                     test_sensitivity=sensitivity_status,
                                     bootstrap_repetitions=BOOTSTRAPS, clinical_inputs=False))
