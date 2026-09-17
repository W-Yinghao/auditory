"""Frozen metadata-only N2 v2.1 design and ablation plan.

The design uses the complete saved event history and constructs a new,
deterministic, without-replacement bag set.  It does not open EEG arrays or
fit an EEG head.  The separate diagnostic fits only the pre-registered
metadata views.  Every candidate/half is assessed against the full
intersection of its exact ``previous_code x previous_run_bin`` cells; cells
are never chosen after inspecting an effect.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .runtime import digest, require_slurm
from .estimator import Transform, fit_head, predict_head
from .fit_ledger import FitLedger


K = 8
MIN_BAGS = 2
MIN_SOURCE_BLOCKS = 3
MIN_TRIALS_PER_CELL = 16
MAX_PER_BLOCK = 4
KNOWN_CODES = ("1", "2")
H_BAG_COLUMNS = (
    "previous_code_1_proportion", "previous_code_2_proportion",
    "previous_code_unknown_proportion", "previous_run_run_1_proportion",
    "previous_run_run_2_proportion", "previous_run_run_3_5_proportion",
    "previous_run_run_6_plus_proportion", "previous_run_unknown_proportion",
    "gap_mean", "gap_present", "position_mean", "position_squared",
    "gap_std", "position_std", "block_count", "time_coverage_s",
)
ABLATION_VIEWS = {
    "all_metadata": H_BAG_COLUMNS,
    "history": H_BAG_COLUMNS[:8],
    "gap": ("gap_mean", "gap_present", "gap_std"),
    "position": ("position_mean", "position_squared", "position_std"),
    "block_span": ("block_count", "time_coverage_s"),
}

REQUIRED = {
    "trial_id", "candidate_id", "record_id", "segment_id", "split_group_id",
    "stimulus_local_id", "accepted", "A_half", "A_block_id", "onset_sample",
    "previous_event_id", "previous_code", "previous_run_bin",
}


def _missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        out = pd.isna(value)
        return bool(out) if np.ndim(out) == 0 else False
    except (TypeError, ValueError):
        return False


def _text(value: Any, missing: str = "__MISSING__") -> str:
    return missing if _missing(value) else str(value)


def exact_history_cell(row: pd.Series | dict[str, Any]) -> tuple[str, str]:
    """Frozen conservative ``previous_code x previous_run_bin`` cell."""
    return (_text(row.get("previous_code")), _text(row.get("previous_run_bin"), "unknown"))


def physical_block(row: pd.Series | dict[str, Any]) -> tuple[str, str, str]:
    return (_text(row["record_id"]), _text(row["segment_id"]), _text(row["A_block_id"]))


def _rank(seed: int, *parts: Any) -> str:
    return hashlib.sha256("|".join([str(seed), *(str(p) for p in parts)]).encode()).hexdigest()


def _prepare_history(history: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(history, pd.DataFrame):
        raise ValueError("N2_DESIGN_HISTORY_TYPE")
    missing = sorted(REQUIRED - set(history.columns))
    if missing:
        raise ValueError("N2_DESIGN_HISTORY_SCHEMA:" + ",".join(missing))
    frame = history.copy()
    if frame.trial_id.isna().any() or frame.trial_id.astype(str).duplicated().any():
        raise ValueError("N2_DESIGN_DUPLICATE_TRIAL")
    halves = pd.to_numeric(frame.A_half, errors="coerce")
    if halves.notna().any() and not halves.dropna().isin([0, 1]).all():
        raise ValueError("N2_DESIGN_HALF")
    frame["_trial_key"] = frame.trial_id.astype(str)
    frame["_cell"] = list(frame.apply(exact_history_cell, axis=1))
    frame["_physical_block"] = list(frame.apply(physical_block, axis=1))
    if "v2_context_boundary_eligible" in frame:
        eligible = frame.v2_context_boundary_eligible.fillna(False).astype(bool)
        frame["_eligible_source"] = eligible
    elif "A_boundary_eligible" in frame:
        frame["_eligible_source"] = frame.A_boundary_eligible.fillna(False).astype(bool)
    else:
        frame["_eligible_source"] = True
    frame["_eligible_source"] &= frame.accepted.astype(bool)
    frame["_eligible_source"] &= frame.stimulus_local_id.isin([0, 1])
    frame["_eligible_source"] &= frame.A_half.notna()
    frame["A_half"] = halves
    return frame


def _choose_without_replacement(part: pd.DataFrame, *, n: int, seed: int,
                                 candidate: str, half: int, cls: int,
                                 cell: tuple[str, str]) -> list[list[dict[str, Any]]]:
    """Create deterministic k=8 bags with frozen physical block limits."""
    if len(part) < K:
        return []
    available = [row for row in part.to_dict("records")]
    bags: list[list[dict[str, Any]]] = []
    for ordinal in range(int(n)):
        ordered = sorted(
            available,
            key=lambda row: _rank(seed, candidate, half, cls, cell[0], cell[1], row["trial_id"]),
        )
        selected: list[dict[str, Any]] = []
        selected_ids: set[str] = set()
        counts: dict[tuple[str, str, str], int] = {}
        # Every k>=4 bag must span at least two physical blocks.  Remaining
        # members are filled in deterministic order, with ceil(k/2) cap.
        for row in ordered:
            block = row["_physical_block"]
            if block not in counts:
                selected.append(row)
                selected_ids.add(str(row["trial_id"]))
                counts[block] = 1
                if len(counts) >= 2:
                    break
        if len(selected) < 2:
            break
        for row in ordered:
            if str(row["trial_id"]) in selected_ids:
                continue
            block = row["_physical_block"]
            if counts.get(block, 0) >= MAX_PER_BLOCK:
                continue
            selected.append(row)
            selected_ids.add(str(row["trial_id"]))
            counts[block] = counts.get(block, 0) + 1
            if len(selected) == K:
                break
        if len(selected) != K:
            break
        bags.append(selected)
        available = [row for row in available if str(row["trial_id"]) not in selected_ids]
    return bags


def _bag_rows(selected: list[dict[str, Any]], *, bag_id: str, pair_id: str,
              candidate: str, half: int, cls: int, cell: tuple[str, str],
              ordinal: int) -> list[dict[str, Any]]:
    return [{
        "bag_id": bag_id, "matched_pair_id": pair_id, "trial_id": str(row["trial_id"]),
        "candidate_id": candidate, "record_id": str(row["record_id"]),
        "segment_id": str(row["segment_id"]), "split_group_id": str(row["split_group_id"]),
        "stimulus_local_id": int(cls), "A_half": int(half),
        "A_block_id": row["A_block_id"], "physical_block_id": json.dumps(list(row["_physical_block"]), separators=(",", ":")),
        "previous_code": cell[0], "previous_run_bin": cell[1], "k": K,
        "bag_ordinal": int(ordinal), "bag_block_count": int(len({row["_physical_block"] for row in selected})),
    } for row in selected]


def construct_matched_bags(
    history: pd.DataFrame, *, seed: int = 21201, k: int = K,
    min_bags: int = MIN_BAGS, min_source_blocks: int = MIN_SOURCE_BLOCKS,
    min_trials_per_cell: int = MIN_TRIALS_PER_CELL,
    candidate_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Construct the frozen common-cell bag design from metadata only.

    For each candidate×half, *all* exact cells shared by both classes are
    assessed.  A candidate×half is retained only when every shared cell has
    at least one paired bag and the total reaches the fixed two-pair minimum.
    Sparse common cells are assessed and then excluded only by the fixed
    predeclared support threshold; no cell is dropped after seeing a result.
    The source pools are separate by class and no trial is reused; physical
    block identity remains part of every member and constraint check.
    """
    if int(k) != K:
        raise ValueError("N2_DESIGN_FIXED_K8")
    if int(min_bags) < 1 or int(min_source_blocks) < 1 or int(min_trials_per_cell) < K:
        raise ValueError("N2_DESIGN_QUOTA")
    frame = _prepare_history(history)
    source = frame.loc[frame._eligible_source].copy()
    candidates = sorted(frame.candidate_id.dropna().astype(str).unique())
    if candidate_ids is not None:
        candidates = sorted(set(candidates) & {str(value) for value in candidate_ids})
    bag_records: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        for half in (0, 1):
            pools = {
                cls: source.loc[(source.candidate_id.astype(str) == candidate)
                                & (source.A_half.astype(int) == half)
                                & (source.stimulus_local_id.astype(int) == cls)]
                for cls in (0, 1)
            }
            common = sorted(set(pools[0]["_cell"]) & set(pools[1]["_cell"])
                            if not pools[0].empty and not pools[1].empty else set())
            common = [cell for cell in common if isinstance(cell, tuple) and len(cell) == 2]
            plans = []
            cell_summary: dict[tuple[str, str], dict[str, Any]] = {}
            for cell in common:
                by_source = {}
                for source_key, source_part in pools[0].loc[pools[0]["_cell"] == cell].groupby(["record_id", "segment_id"], sort=True):
                    by_source.setdefault(tuple(map(str, source_key)), {})[0] = source_part
                for source_key, source_part in pools[1].loc[pools[1]["_cell"] == cell].groupby(["record_id", "segment_id"], sort=True):
                    by_source.setdefault(tuple(map(str, source_key)), {})[1] = source_part
                cell_summary[cell] = {"n_source_groups": len(by_source), "n_supported_source_groups": 0,
                                      "paired_bags": 0, "class0_trials": 0, "class1_trials": 0,
                                      "class0_blocks": 0, "class1_blocks": 0}
                for source_key, grouped in sorted(by_source.items()):
                    if 0 not in grouped or 1 not in grouped:
                        continue
                    cell_pools = grouped
                    source_blocks = {cls: int(cell_pools[cls]["_physical_block"].nunique()) for cls in (0, 1)}
                    threshold_ok = all(
                        len(cell_pools[cls]) >= int(min_trials_per_cell)
                        and source_blocks[cls] >= int(min_source_blocks)
                        for cls in (0, 1)
                    )
                    if not threshold_ok:
                        continue
                    generated = {
                        cls: _choose_without_replacement(cell_pools[cls], n=10_000, seed=int(seed),
                                                         candidate=candidate, half=half, cls=cls, cell=cell)
                        for cls in (0, 1)
                    }
                    pair_count = min(len(generated[0]), len(generated[1]))
                    plans.append((cell, source_key, source_blocks, generated, pair_count))
                    cell_summary[cell]["n_supported_source_groups"] += 1
                    cell_summary[cell]["paired_bags"] += pair_count
                    cell_summary[cell]["class0_trials"] += len(cell_pools[0])
                    cell_summary[cell]["class1_trials"] += len(cell_pools[1])
                    cell_summary[cell]["class0_blocks"] = max(cell_summary[cell]["class0_blocks"], source_blocks[0])
                    cell_summary[cell]["class1_blocks"] = max(cell_summary[cell]["class1_blocks"], source_blocks[1])
                cell_meta = cell_summary[cell]
                cell_rows.append({
                    "candidate_id": candidate, "A_half": half,
                    "previous_code": cell[0], "previous_run_bin": cell[1],
                    "class0_n_trials": int(cell_meta["class0_trials"]), "class1_n_trials": int(cell_meta["class1_trials"]),
                    "class0_source_blocks": int(cell_meta["class0_blocks"]), "class1_source_blocks": int(cell_meta["class1_blocks"]),
                    "n_source_groups": int(cell_meta["n_source_groups"]),
                    "n_supported_source_groups": int(cell_meta["n_supported_source_groups"]),
                    "paired_bag_count": int(cell_meta["paired_bags"]),
                    "source_threshold_ok": bool(cell_meta["n_supported_source_groups"] > 0),
                    "fixed_support_status": (
                        "ELIGIBLE"
                        if cell_meta["n_supported_source_groups"] > 0
                        else "BELOW_PREDECLARED_TRIAL_OR_BLOCK_THRESHOLD"
                    ),
                })
            eligible_common = [cell for cell in common if cell_summary[cell]["n_supported_source_groups"] > 0]
            all_cells_feasible = bool(eligible_common) and all(
                cell_summary[cell]["paired_bags"] > 0 for cell in eligible_common
            )
            total_pairs = int(sum(pair_count for _, _, _, _, pair_count in plans))
            eligible = bool(all_cells_feasible and total_pairs >= int(min_bags))
            if eligible:
                ordinal = 0
                for cell, source_key, _, generated, pair_count in plans:
                    for pair_index in range(pair_count):
                        pair_id = "pair_" + _rank(seed, candidate, half, cell, ordinal)[:20]
                        bag_records.extend(_bag_rows(
                            generated[0][pair_index], bag_id=pair_id + "_c0", pair_id=pair_id,
                            candidate=candidate, half=half, cls=0, cell=cell, ordinal=ordinal))
                        bag_records.extend(_bag_rows(
                            generated[1][pair_index], bag_id=pair_id + "_c1", pair_id=pair_id,
                            candidate=candidate, half=half, cls=1, cell=cell, ordinal=ordinal))
                        ordinal += 1
            candidate_rows.append({
                "candidate_id": candidate, "A_half": half,
                "class0_n_source_trials": int(len(pools[0])), "class1_n_source_trials": int(len(pools[1])),
                "class0_source_blocks": int(pools[0]["_physical_block"].nunique()),
                "class1_source_blocks": int(pools[1]["_physical_block"].nunique()),
                "common_cell_count": int(len(common)), "common_cells_all_paired": bool(all_cells_feasible),
                "eligible_common_cell_count": int(len(eligible_common)),
                "sparse_common_cell_excluded_count": int(len(common) - len(eligible_common)),
                "planned_pair_bags": total_pairs, "matched_pair_bags": total_pairs if eligible else 0,
                "matched_bags_per_class": total_pairs if eligible else 0,
                "min_bags_ok": bool(total_pairs >= int(min_bags)), "eligible": eligible,
            })
    matched = pd.DataFrame(bag_records)
    candidates_detail = pd.DataFrame(candidate_rows)
    cells_detail = pd.DataFrame(cell_rows)
    if matched.empty:
        matched = pd.DataFrame(columns=[
            "bag_id", "matched_pair_id", "trial_id", "candidate_id", "record_id", "segment_id",
            "split_group_id", "stimulus_local_id", "A_half", "A_block_id", "physical_block_id",
            "previous_code", "previous_run_bin", "k", "bag_ordinal", "bag_block_count",
        ])
    coverage = []
    for half in (0, 1):
        for cls in (0, 1):
            original = source.loc[(source.A_half.astype(int) == half) & (source.stimulus_local_id.astype(int) == cls)]
            selected = matched.loc[(matched.A_half.astype(int) == half) & (matched.stimulus_local_id.astype(int) == cls)] if not matched.empty else matched
            coverage.append({
                "A_half": half, "stimulus_local_id": cls,
                "source_candidate_denominator": int(original.candidate_id.astype(str).nunique()),
                "source_trial_denominator": int(len(original)),
                "matched_candidate_numerator": int(selected.candidate_id.astype(str).nunique()) if not selected.empty else 0,
                "matched_bag_numerator": int(selected.bag_id.astype(str).nunique()) if not selected.empty else 0,
                "matched_trial_numerator": int(len(selected)),
            })
    coverage = pd.DataFrame(coverage)
    eligible_count = int(candidates_detail["eligible"].sum()) if "eligible" in candidates_detail else 0
    both_half = candidates_detail.groupby("candidate_id")["eligible"].agg(list) if not candidates_detail.empty else pd.Series(dtype=object)
    both_half_count = int(sum(len(values) == 2 and all(values) for values in both_half))
    aggregate = {
        "candidate_denominator": int(len(candidates)),
        "candidate_half_denominator": int(len(candidates) * 2),
        "candidate_half_eligible_numerator": eligible_count,
        "candidate_both_halves_eligible_numerator": both_half_count,
        "real_scope_candidate_denominator": int(len(candidates)),
        "candidate_half_common_cell_denominator": int(candidates_detail["common_cell_count"].gt(0).sum()) if "common_cell_count" in candidates_detail else 0,
        "candidate_half_sparse_common_cell_exclusion_count": int(candidates_detail["sparse_common_cell_excluded_count"].sum()) if "sparse_common_cell_excluded_count" in candidates_detail else 0,
        "candidate_half_common_cells_all_paired_numerator": int(candidates_detail["common_cells_all_paired"].sum()) if "common_cells_all_paired" in candidates_detail else 0,
        "matched_pair_bag_denominator": int(matched.matched_pair_id.astype(str).nunique()) if not matched.empty else 0,
        "matched_member_row_denominator": int(len(matched)),
        "k": K, "min_bags_per_class_half": int(min_bags), "min_source_blocks": int(min_source_blocks),
        "without_replacement": True, "half_separated": True,
        "all_common_cells_assessed": True, "posthoc_cell_selection": False,
        "old_imbalance_does_not_rule_out_new_balanced_design": True,
        "support_status": "DESIGN_SUPPORT_PRESENT" if both_half_count > 0 else "OBSERVATIONAL_SUPPORT_LIMITED",
    }
    return {"matched_bags": matched, "candidate_detail": candidates_detail,
            "cell_detail": cells_detail, "coverage": coverage, "aggregate": aggregate}


def build_h_bag_metadata(bags: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    """Materialize old H_BAG metadata columns for private ablation planning."""
    if not isinstance(bags, pd.DataFrame) or bags.empty:
        return pd.DataFrame(columns=["bag_id", "candidate_id", "A_half", "stimulus_local_id", *H_BAG_COLUMNS])
    frame = _prepare_history(history)
    lookup = {str(row["trial_id"]): row for row in frame.to_dict("records")}
    out = []
    for bag_id, part in bags.groupby(bags.bag_id.astype(str), sort=True):
        members = [lookup[str(t)] for t in part.trial_id.astype(str)]
        previous_codes = [row.get("previous_code") for row in members]
        previous_runs = [_text(row.get("previous_run_bin"), "unknown") for row in members]
        gaps = pd.to_numeric(pd.Series([row.get("previous_gap_s") for row in members]), errors="coerce").to_numpy(float)
        positions = pd.to_numeric(pd.Series([row.get("position_fraction", row.get("segment_position_fraction")) for row in members]), errors="coerce").to_numpy(float)
        if not np.isfinite(positions).all() or not ((positions >= 0).all() and (positions <= 1).all()):
            raise ValueError("N2_DESIGN_POSITION_SCHEMA")
        values = {}
        for code in KNOWN_CODES:
            values[f"previous_code_{code}_proportion"] = float(np.mean([_text(value) == code for value in previous_codes]))
        values["previous_code_unknown_proportion"] = float(np.mean([_text(value) not in KNOWN_CODES for value in previous_codes]))
        for run_bin in ("run_1", "run_2", "run_3_5", "run_6_plus", "unknown"):
            values[f"previous_run_{run_bin}_proportion"] = float(np.mean([value == run_bin for value in previous_runs]))
        values.update({
            "gap_mean": float(np.nan_to_num(gaps, nan=0.0).mean()), "gap_present": float(np.isfinite(gaps).mean()),
            "position_mean": float(positions.mean()), "position_squared": float((positions ** 2).mean()),
            "gap_std": float(np.nanstd(gaps)), "position_std": float(np.std(positions, ddof=1)),
            "block_count": int(len({physical_block(row) for row in members})),
        })
        if "onset_seconds" in frame:
            times = pd.to_numeric(pd.Series([row.get("onset_seconds") for row in members]), errors="coerce").to_numpy(float)
        else:
            samples = pd.to_numeric(pd.Series([row.get("onset_sample") for row in members]), errors="coerce").to_numpy(float)
            fs = pd.to_numeric(pd.Series([row.get("original_fs") for row in members]), errors="coerce").to_numpy(float)
            if not np.isfinite(samples).all() or not np.isfinite(fs).all() or (fs <= 0).any():
                raise ValueError("N2_DESIGN_TIME_SCHEMA")
            times = samples / fs
        if not np.isfinite(times).all():
            raise ValueError("N2_DESIGN_TIME_SCHEMA")
        values["time_coverage_s"] = float(np.nanmax(times) - np.nanmin(times))
        first = part.iloc[0]
        out.append({"bag_id": str(bag_id), "candidate_id": str(first.candidate_id),
                    "record_id": str(first.record_id), "segment_id": str(first.segment_id),
                    "split_group_id": str(first.split_group_id), "A_half": int(first.A_half),
                    "stimulus_local_id": int(first.stimulus_local_id), **values})
    return pd.DataFrame(out)


def metadata_ablation_plan(folds: Iterable[dict[str, Any]], *, lam: float = .01, maxiter: int = 200) -> dict[str, Any]:
    """Freeze the 5-view × 5-fold low-complexity diagnostic catalog."""
    if float(lam) != .01 or int(maxiter) != 200:
        raise ValueError("N2_METADATA_FIXED_ALGORITHM")
    folds = list(folds)
    if len(folds) != 5:
        raise ValueError("N2_DESIGN_FIVE_FOLDS_REQUIRED")
    rows = []
    for fold in folds:
        number = int(fold.get("outer_fold", fold.get("fold", -1)))
        if number < 0:
            raise ValueError("N2_DESIGN_FOLD_SCHEMA")
        for view, columns in ABLATION_VIEWS.items():
            rows.append({"outer_fold": number, "view": view, "columns": list(columns),
                         "lambda_l2": float(lam), "maxiter": int(maxiter),
                         "model": "logistic_regression", "selection": "none",
                         "fit_status": "PLAN_ONLY", "prediction_status": "NOT_RUN"})
    plan = pd.DataFrame(rows).sort_values(["outer_fold", "view"]).reset_index(drop=True)
    return {"plan": plan, "aggregate": {
        "n_folds": 5, "n_views": len(ABLATION_VIEWS), "head_count": int(len(plan)),
        "lambda_l2": float(lam), "maxiter": int(maxiter), "fits_executed": 0,
        "h_bag_column_count": len(H_BAG_COLUMNS), "mu_dimension_required": 8,
        "var_dimension_required": 8, "fit_status": "PLAN_ONLY",
    }}


def _raw_candidate_scores(frame: pd.DataFrame, logits: np.ndarray) -> pd.DataFrame:
    """Return one raw CE/bAcc row per candidate, preserving OOF groups."""
    if len(frame) != len(logits) or not np.isfinite(logits).all():
        raise ValueError("N2_METADATA_PREDICTION_ALIGNMENT")
    required = {"candidate_id", "split_group_id", "stimulus_local_id"}
    if not required.issubset(frame.columns):
        raise ValueError("N2_METADATA_SCORE_SCHEMA")
    work = frame[["candidate_id", "split_group_id", "stimulus_local_id"]].copy()
    work["logit"] = np.asarray(logits, dtype=float)
    rows = []
    for identity, part in work.groupby(work.split_group_id.astype(str), sort=True):
        candidates = part.candidate_id.astype(str).unique()
        if len(candidates) != 1:
            raise ValueError("N2_METADATA_IDENTITY_MAPPING")
        y = part.stimulus_local_id.to_numpy(int)
        z = part.logit.to_numpy(float)
        ce = np.mean(np.logaddexp(0.0, z) - y * z) / np.log(2.0)
        pred = z >= 0
        if np.any(y == 0) and np.any(y == 1):
            bacc = float(.5 * np.mean(~pred[y == 0]) + .5 * np.mean(pred[y == 1]))
        else:
            raise ValueError("N2_METADATA_INCOMPLETE_IDENTITY_CLASSES")
        rows.append({"candidate_id": str(candidates[0]), "split_group_id": str(identity),
                     "ce_bits": float(ce), "bacc": bacc, "n_bags": int(len(part))})
    return pd.DataFrame(rows)


def _cluster_bootstrap(values: pd.Series, *, seed: int, replicates: int) -> tuple[float, float, float, int]:
    values = pd.to_numeric(values, errors="coerce").to_numpy(float)
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("N2_METADATA_NONFINITE_SCORE")
    if len(values) < 2:
        return (float(values.mean()), float("nan"), float("nan"), int(len(values)))
    rng = np.random.default_rng(int(seed))
    sample = rng.integers(0, len(values), size=(int(replicates), len(values)))
    boot = values[sample].mean(axis=1)
    return float(values.mean()), float(np.quantile(boot, .025)), float(np.quantile(boot, .975)), int(len(values))


def run_metadata_diagnostic(
    original_h_bag: pd.DataFrame, folds: Iterable[dict[str, Any]], private: Path,
    public: Path, *, lam: float = .01, maxiter: int = 200,
    bootstrap_seed: int = 21201, bootstrap_replicates: int = 2000,
) -> dict[str, Any]:
    """Fit the frozen 25-head raw metadata diagnostic and save private OOF rows."""
    if float(lam) != .01 or int(maxiter) != 200:
        raise ValueError("N2_METADATA_FIXED_ALGORITHM")
    required = {"candidate_id", "split_group_id", "stimulus_local_id", *H_BAG_COLUMNS}
    if not required.issubset(original_h_bag.columns):
        raise ValueError("N2_METADATA_DIAGNOSTIC_SCHEMA")
    folds = list(folds)
    if len(folds) != 5:
        raise ValueError("N2_DESIGN_FIVE_FOLDS_REQUIRED")
    identity_frame = original_h_bag[["candidate_id", "split_group_id"]].copy()
    identity_frame["candidate_id"] = identity_frame.candidate_id.astype(str)
    identity_frame["split_group_id"] = identity_frame.split_group_id.astype(str)
    if (identity_frame.groupby("candidate_id").split_group_id.nunique().gt(1).any()
            or identity_frame.groupby("split_group_id").candidate_id.nunique().gt(1).any()):
        raise ValueError("N2_METADATA_IDENTITY_MAPPING")
    private.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)
    ledger = FitLedger(private / "metadata_fit_ledger.jsonl",
                       {"head": 25, "transform": 25, "calibration": 0})
    ledger.begin_world(0, {"head": 25, "transform": 25, "calibration": 0})

    def tracked(kind: str, name: str, operation):
        ledger("start", kind, name, {})
        try:
            result = operation()
        except Exception as exc:
            ledger("failed", kind, name, {"exception_type": type(exc).__name__})
            raise
        details = result[1] if kind == "head" else {}
        ledger("completed", kind, name, details)
        return result

    predictions: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    candidate_scores: list[pd.DataFrame] = []
    for fold in folds:
        number = int(fold.get("outer_fold", fold.get("fold", -1)))
        train_groups = {str(x) for x in fold.get("train_groups", [])}
        test_groups = {str(x) for x in fold.get("test_groups", [])}
        if not train_groups or not test_groups or train_groups & test_groups:
            raise ValueError("N2_METADATA_FOLD_SCOPE")
        train = original_h_bag.loc[original_h_bag.split_group_id.astype(str).isin(train_groups)].copy()
        test = original_h_bag.loc[original_h_bag.split_group_id.astype(str).isin(test_groups)].copy()
        for view, columns in ABLATION_VIEWS.items():
            if train.empty or test.empty or train.stimulus_local_id.nunique() < 2:
                raise ValueError("N2_METADATA_DIAGNOSTIC_SUPPORT")
            transform = tracked(
                "transform", f"N2_metadata_transform_{view}_f{number}",
                lambda: Transform.fit(train[list(columns)].to_numpy(float),
                                       train.split_group_id.astype(str).to_numpy()))
            x_train = transform.apply(train[list(columns)].to_numpy(float))
            x_test = transform.apply(test[list(columns)].to_numpy(float))
            head_id = f"N2_metadata_{view}_f{number}"
            theta, receipt = tracked(
                "head", head_id,
                lambda: fit_head(
                    x_train, train.stimulus_local_id.to_numpy(int),
                    train.split_group_id.astype(str).to_numpy(),
                    lam=float(lam), maxiter=int(maxiter),
                ),
            )
            logits = predict_head(theta, x_test)
            event = {"head_id": head_id, "outer_fold": number, "view": view,
                     "lambda_l2": float(lam), "maxiter": int(maxiter),
                     "train_bags": int(len(train)), "test_bags": int(len(test)),
                     "train_candidates": int(train.candidate_id.astype(str).nunique()),
                     "test_candidates": int(test.candidate_id.astype(str).nunique()),
                     "fit_status": str(receipt.get("status", "FINITE_BUDGET_ESTIMATOR")),
                     "selection": "none", "calibration": "none",
                     "transform_fit_scope": "outer_train_candidate_equal",
                     "iterations": int(receipt.get("iterations", 0)),
                     "optimizer_success": bool(receipt.get("optimizer_success", False)),
                     "fit_rows": int(receipt.get("fit_rows", len(train)))}
            events.append(event)
            scores = _raw_candidate_scores(test, logits)
            scores["outer_fold"] = number; scores["view"] = view
            candidate_scores.append(scores)
            for row, logit in zip(test.itertuples(index=False), logits):
                predictions.append({"head_id": head_id, "outer_fold": number, "view": view,
                                    "candidate_id": str(row.candidate_id), "split_group_id": str(row.split_group_id),
                                    "bag_id": str(row.bag_id), "stimulus_local_id": int(row.stimulus_local_id),
                                    "logit_raw": float(logit)})
    prediction_frame = pd.DataFrame(predictions)
    event_frame = pd.DataFrame(events)
    score_frame = pd.concat(candidate_scores, ignore_index=True)
    metric_rows = []
    for view, part in score_frame.groupby("view", sort=True):
        for metric in ("ce_bits", "bacc"):
            estimate, lower, upper, n_candidates = _cluster_bootstrap(
                part[metric], seed=int(bootstrap_seed) + list(ABLATION_VIEWS).index(view),
                replicates=int(bootstrap_replicates),
            )
            metric_rows.append({"view": view, "metric": metric, "estimate": estimate,
                                "ci_lower": lower, "ci_upper": upper,
                                "n_candidates": n_candidates, "n_bags": int(part.n_bags.sum()),
                                "unit": "bits_per_bag" if metric == "ce_bits" else "balanced_accuracy",
                                "bootstrap_scope": "candidate_cluster_fixed_oof_no_refit",
                                "calibration": "none", "selection": "none"})
    ledger.complete_world()
    ledger.path.chmod(0o600)
    _private_frame(private / "metadata_original_h_bag.parquet", original_h_bag)
    _private_frame(private / "metadata_predictions.parquet", prediction_frame)
    _private_frame(private / "metadata_fit_events.parquet", event_frame)
    event_frame.to_json(private / "metadata_fit_events.jsonl", orient="records", lines=True)
    (private / "metadata_fit_events.jsonl").chmod(0o600)
    _private_frame(private / "metadata_candidate_scores.parquet", score_frame)
    metric_frame = pd.DataFrame(metric_rows)
    metric_frame.to_csv(public / "N2_METADATA_ABLATION_METRICS.csv", index=False)
    public.joinpath("N2_METADATA_ABLATION_METRICS.csv").chmod(0o600)
    return {"head_count": int(len(event_frame)), "expected_head_count": 25,
            "fits_executed": int(len(event_frame)), "transform_fits": 25,
            "calibration_fits": 0, "fit_ledger": ledger.summary(),
            "prediction_rows": int(len(prediction_frame)),
            "candidate_score_rows": int(len(score_frame)), "metrics": metric_frame.to_dict("records"),
            "lambda_l2": float(lam), "maxiter": int(maxiter),
            "fit_status": "COMPLETE", "calibration": "none", "selection": "none",
            "raw_oof_candidate_cluster_bootstrap": True}


def _resolve_paths(root: Path, config: dict[str, Any]) -> tuple[Path, Path, Path]:
    stage = config.get("stage0", config)
    design = config.get("n2_design", stage.get("n2_design", {}))
    design = design if isinstance(design, dict) else {}
    source = design.get("support_source", stage.get("support_source", "S1_support_004"))
    support_run = design.get("support_run", stage.get("support_run"))
    support = root / "private" / "auditory_next_v2" / str(support_run or source)
    history = Path(design.get("history_path", stage.get("history_path", support / "full_event_history.parquet")))
    if not history.is_absolute():
        history = root / history
    split = Path(design.get("splits_path", stage.get("splits_path", root / "private/auditory5_v1/splits/splits_001/folds.json")))
    if not split.is_absolute():
        split = root / split
    bags = Path(design.get("original_bags_path", stage.get("original_bags_path", support / "N2_k8_bags.parquet")))
    if not bags.is_absolute():
        bags = root / bags
    return history, split, bags


def _design_config(config: dict[str, Any]) -> dict[str, Any]:
    stage = config.get("stage0", config)
    value = config.get("n2_design", stage.get("n2_design", {}))
    return value if isinstance(value, dict) else {}


def _private_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    path.chmod(0o600)


def _private_frame(path: Path, frame: pd.DataFrame) -> None:
    frame.to_parquet(path, index=False)
    path.chmod(0o600)


def run(root: Path, private: Path, public: Path, report: Path, config: dict) -> dict[str, Any]:
    """Run metadata construction and ablation planning under Slurm."""
    require_slurm()
    root, private, public, report = map(Path, (root, private, public, report))
    stage = config.get("stage0", config)
    design_config = _design_config(config)
    if int(stage.get("N2_k", K)) != K:
        raise ValueError("N2_DESIGN_FIXED_K8")
    history_path, split_path, original_bags_path = _resolve_paths(root, config)
    if not history_path.is_file() or not split_path.is_file() or not original_bags_path.is_file():
        raise FileNotFoundError("N2_DESIGN_INPUT_MISSING")
    private.mkdir(parents=True, exist_ok=True, mode=0o700); public.mkdir(parents=True, exist_ok=True, mode=0o700); report.mkdir(parents=True, exist_ok=True, mode=0o700)
    private.chmod(0o700)
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    input_hashes = {"full_event_history.parquet": digest(history_path), "folds.json": digest(split_path), "original_N2_k8_bags.parquet": digest(original_bags_path), "stage0_config": config_hash}
    _private_json(private / "input_hashes.json", {str(history_path): input_hashes["full_event_history.parquet"], str(split_path): input_hashes["folds.json"], str(original_bags_path): input_hashes["original_N2_k8_bags.parquet"], "stage0_config": config_hash})
    history = pd.read_parquet(history_path)
    original_bags = pd.read_parquet(original_bags_path)
    original_candidates = original_bags.candidate_id.astype(str).unique()
    design = construct_matched_bags(history, seed=int(design_config.get("seed", stage.get("N2_design_seed", 21201))), k=K,
                                     min_bags=int(design_config.get("min_bags_per_class_half", stage.get("N2_min_bags_per_class_half", MIN_BAGS))),
                                     min_source_blocks=int(design_config.get("min_source_blocks", stage.get("N2_min_source_blocks", MIN_SOURCE_BLOCKS))),
                                     min_trials_per_cell=int(design_config.get("min_trials_per_cell", stage.get("N2_min_trials_per_cell", MIN_TRIALS_PER_CELL))),
                                     candidate_ids=original_candidates)
    design["aggregate"]["original_saved_bag_candidate_denominator"] = int(len(set(original_candidates)))
    design["aggregate"]["new_cohort_source"] = "immutable_old_saved_N2_k8_bag_candidates"
    folds_payload = json.loads(split_path.read_text())
    folds = folds_payload.get("folds", folds_payload if isinstance(folds_payload, list) else [])
    plan = metadata_ablation_plan(folds)
    original_h = build_h_bag_metadata(original_bags, history)
    matched_h = build_h_bag_metadata(design["matched_bags"], history)
    metadata_diag = run_metadata_diagnostic(
        original_h, folds, private, public,
        lam=float(design_config.get("lambda_l2", .01)),
        maxiter=int(design_config.get("maxiter", 200)),
        bootstrap_seed=int(design_config.get("bootstrap_seed", 21201)),
        bootstrap_replicates=int(design_config.get("bootstrap_replicates", 2000)),
    )
    _private_frame(private / "matched_bags.parquet", design["matched_bags"])
    _private_frame(private / "matched_h_bag_metadata.parquet", matched_h)
    _private_frame(private / "candidate_half_support.parquet", design["candidate_detail"])
    _private_frame(private / "common_cell_support.parquet", design["cell_detail"])
    _private_frame(private / "original_h_bag_metadata.parquet", original_h)
    _private_frame(private / "metadata_ablation_plan.parquet", plan["plan"])
    _private_json(private / "design_manifest.json", {
        "k": K, "without_replacement": True, "half_separated": True,
        "seed": int(design_config.get("seed", stage.get("N2_design_seed", 21201))),
        "primary_cells": ["previous_code", "previous_run_bin"],
        "min_bags_per_class_half": int(design_config.get("min_bags_per_class_half", stage.get("N2_min_bags_per_class_half", MIN_BAGS))),
        "min_source_blocks": int(design_config.get("min_source_blocks", stage.get("N2_min_source_blocks", MIN_SOURCE_BLOCKS))),
        "min_trials_per_common_cell_per_class": int(design_config.get("min_trials_per_cell", stage.get("N2_min_trials_per_cell", MIN_TRIALS_PER_CELL))),
        "max_members_per_physical_block": MAX_PER_BLOCK,
        "h_bag_columns": list(H_BAG_COLUMNS), "h_bag_column_count": len(H_BAG_COLUMNS),
        "mu_dimension_required": 8, "var_dimension_required": 8,
        "group_bag_counts_private": "candidate_half_support.parquet",
        "matched_h_bag_metadata_private": "matched_h_bag_metadata.parquet",
        "metadata_ablation_plan_private": "metadata_ablation_plan.parquet",
        "fits_executed": int(metadata_diag["fits_executed"]),
    })
    _private_json(private / "support_manifest.json", {
        "support_status": design["aggregate"]["support_status"],
        "real_scope_requires_both_halves": True,
        "groups": design["candidate_detail"].to_dict("records"),
        "h_bag_column_count": len(H_BAG_COLUMNS), "h_bag_columns": list(H_BAG_COLUMNS),
        "mu_dimension_required": 8, "var_dimension_required": 8,
        "quota": {"k": K, "min_bags_per_class_half": int(design_config.get("min_bags_per_class_half", stage.get("N2_min_bags_per_class_half", MIN_BAGS))),
                   "min_source_blocks": int(design_config.get("min_source_blocks", stage.get("N2_min_source_blocks", MIN_SOURCE_BLOCKS))),
                   "min_trials_per_common_cell_per_class": int(design_config.get("min_trials_per_cell", stage.get("N2_min_trials_per_cell", MIN_TRIALS_PER_CELL))),
                   "max_members_per_physical_block": MAX_PER_BLOCK},
        "matched_bags_per_class_field": "matched_bags_per_class",
    })
    summary = {"status": "N2_METADATA_DESIGN_COMPLETE", "scientific_effects_viewed": False,
               "metadata_effects_viewed": True, "new_head_fits": int(metadata_diag["fits_executed"]), "new_encoder_fits": 0, "input_hashes_recorded": True,
               "design": design["aggregate"], "class_coverage": design["coverage"].to_dict("records"),
               "metadata_ablation": dict(plan["aggregate"], **metadata_diag),
               "input_hashes_logical": input_hashes,
               "support_stop": design["aggregate"]["support_status"] == "OBSERVATIONAL_SUPPORT_LIMITED",
               "old_imbalance_does_not_rule_out_new_balanced_design": True}
    _private_json(private / "n2_design_summary.json", summary)
    public_summary = {key: value for key, value in summary.items() if key != "class_coverage"}
    public_summary["class_coverage"] = summary["class_coverage"]
    _private_json(public / "N2_DESIGN_SUMMARY.json", public_summary)
    design["coverage"].to_csv(public / "N2_CLASS_COVERAGE.csv", index=False)
    (public / "N2_CLASS_COVERAGE.csv").chmod(0o600)
    report_path = report / "N2_DESIGN_LOCK.md"
    report_path.write_text(
        "# N2 v2.1 design lock\n\n"
        "This run constructs metadata-only matched bags from the immutable complete event history. It uses k=8, exact previous_code×previous_run_bin common cells, half-separated pools, equal class bag budgets, no replacement, at least two physical blocks per bag with at most four members per block, at least two bags per class/half, and at least three source blocks. All common cells are assessed before any effect is available.\n\n"
        f"Candidate denominator: {design['aggregate']['candidate_denominator']}; candidate×half denominator: {design['aggregate']['candidate_half_denominator']}; eligible candidate×half numerator: {design['aggregate']['candidate_half_eligible_numerator']}; matched pair-bag denominator: {design['aggregate']['matched_pair_bag_denominator']}. Support status: {design['aggregate']['support_status']}.\n\n"
        "The original saved imbalance is recorded as a necessary-support limitation only. It does not establish that a newly constructed balanced design is impossible. If support is limited, no EEG contrast is authorized by this run.\n\n"
        f"The separate metadata diagnostic executed {metadata_diag['fits_executed']} heads (five folds × all metadata plus history, gap, position, and block-span views), lambda={metadata_diag['lambda_l2']}, maxiter={metadata_diag['maxiter']}, with raw fixed-OOF candidate-cluster CE/bAcc and no calibration or selection. H_BAG has {len(H_BAG_COLUMNS)} columns; required MU/VAR dimensions are 8/8.\n"
    )
    report_path.chmod(0o600)
    return summary


__all__ = [
    "K", "H_BAG_COLUMNS", "ABLATION_VIEWS", "exact_history_cell",
    "construct_matched_bags", "build_h_bag_metadata", "metadata_ablation_plan", "run",
]
