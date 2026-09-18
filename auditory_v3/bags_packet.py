"""Frozen matched-bag construction and N2R feature views.

This module only handles the observation contract.  It does not redraw bags,
read clinical outcomes, or fit a model.  Numeric transforms are deliberately
provided as a separate train-only helper so the same path can be used by the
synthetic capability packet and the later real packet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


K = 8
H_COLUMNS = (
    "previous_code_1_proportion", "previous_code_2_proportion",
    "previous_code_unknown_proportion", "previous_run_run_1_proportion",
    "previous_run_run_2_proportion", "previous_run_run_3_5_proportion",
    "previous_run_run_6_plus_proportion", "previous_run_unknown_proportion",
    "gap_mean", "gap_present", "position_mean", "position_squared",
    "gap_std", "position_std", "block_count", "time_coverage_s",
)
REQUIRED_MEMBER_COLUMNS = (
    "bag_id", "matched_pair_id", "trial_id", "candidate_id", "split_group_id",
    "record_id", "segment_id", "stimulus_local_id", "A_half", "A_block_id",
    "physical_block_id", "previous_code", "previous_run_bin", "k",
)
IDENTIFIER_COLUMNS = {
    "bag_id", "matched_pair_id", "trial_id", "candidate_id", "split_group_id",
    "record_id", "segment_id", "A_half", "A_block_id", "physical_block_id",
    "previous_code", "previous_run_bin", "stimulus_local_id", "outer_fold", "inner_fold",
}
VIEW_NAMES = ("H", "HM", "HMV", "HQ", "HQV", "HQQ", "HPRE", "HPREQ", "HPREQV")
FULL_VIEW_NAMES = ("FULL_MU", "FULL_MU_VAR")


@dataclass(frozen=True)
class BagStatistics:
    """Bag-level arrays with a private row table retaining alignment metadata."""

    frame: pd.DataFrame
    h: np.ndarray
    post_mean: np.ndarray
    post_var: np.ndarray
    pre_mean: np.ndarray
    pre_var: np.ndarray

    @property
    def n_bags(self) -> int:
        return int(len(self.frame))


def _as_frame(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy()
    if isinstance(value, Mapping):
        return pd.DataFrame(value)
    raise TypeError("MEMBER_FRAME_REQUIRED")


def validate_member_schema(members: Any, *, k: int = K) -> pd.DataFrame:
    """Validate the frozen bag member schema without changing row order."""

    frame = _as_frame(members)
    missing = [column for column in REQUIRED_MEMBER_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("MISSING_MEMBER_COLUMNS:" + ",".join(missing))
    if frame.empty:
        raise ValueError("EMPTY_MATCHED_BAGS")
    if frame["trial_id"].isna().any():
        raise ValueError("MISSING_TRIAL_ID")
    if frame["trial_id"].duplicated().any():
        raise ValueError("DUPLICATE_TRIAL_ID")
    if frame["bag_id"].isna().any() or frame["split_group_id"].isna().any():
        raise ValueError("MISSING_BAG_OR_GROUP_ID")
    if not np.all(frame["k"].to_numpy() == int(k)):
        raise ValueError("BAG_K_MISMATCH")
    counts = frame.groupby("bag_id", sort=False, dropna=False).size()
    if not bool((counts == int(k)).all()):
        raise ValueError("BAG_MEMBER_COUNT_MISMATCH")
    for bag_id, part in frame.groupby("bag_id", sort=False, dropna=False):
        if part["stimulus_local_id"].nunique(dropna=False) != 1:
            raise ValueError("BAG_CLASS_MISMATCH")
        for column in ("matched_pair_id", "candidate_id", "split_group_id", "A_half",
                       "record_id", "segment_id", "previous_code", "previous_run_bin"):
            if part[column].nunique(dropna=False) != 1:
                raise ValueError(f"BAG_METADATA_NOT_CONSTANT:{column}")
        if part["physical_block_id"].nunique(dropna=False) < 2:
            raise ValueError("BAG_NEEDS_TWO_PHYSICAL_BLOCKS")
        if int(part["physical_block_id"].value_counts().max()) > 4:
            raise ValueError("BAG_BLOCK_MEMBER_CAP")
    return frame.reset_index(drop=True)


def _aligned_array(value: Any, n_rows: int, name: str, width: int | None = None) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[0] != n_rows:
        raise ValueError(f"{name}_ROW_ALIGNMENT")
    if width is not None and array.shape[1] != width:
        raise ValueError(f"{name}_WIDTH_MISMATCH")
    if not np.isfinite(array).all():
        raise ValueError(f"{name}_NONFINITE")
    return array


def _h_array(members: pd.DataFrame, h: Any = None) -> np.ndarray:
    source = members.loc[:, list(H_COLUMNS)] if h is None else h
    if isinstance(source, pd.DataFrame):
        missing = [column for column in H_COLUMNS if column not in source.columns]
        if missing:
            raise ValueError("H_BAG_COLUMNS_MISSING:" + ",".join(missing))
        array = source.loc[:, list(H_COLUMNS)].to_numpy(dtype=float)
    else:
        array = _aligned_array(source, len(members), "H_BAG", len(H_COLUMNS))
    if not np.isfinite(array).all():
        raise ValueError("H_BAG_NONFINITE")
    return array


def bag_history_array(members: Any, history: Any) -> np.ndarray:
    """Align the frozen 16-column bag history to member row order.

    ``history`` is a bag-level table.  Missing or duplicated bag coverage is
    rejected before any feature aggregation.
    """

    frame = validate_member_schema(members)
    if not isinstance(history, pd.DataFrame):
        raise TypeError("BAG_HISTORY_DATAFRAME_REQUIRED")
    missing = [column for column in ("bag_id", *H_COLUMNS) if column not in history.columns]
    if missing:
        raise ValueError("BAG_HISTORY_COLUMNS_MISSING:" + ",".join(missing))
    source = history.loc[:, ["bag_id", *H_COLUMNS]].copy()
    if source["bag_id"].duplicated().any():
        raise ValueError("DUPLICATE_BAG_HISTORY")
    expected = set(frame["bag_id"].astype(str))
    actual = set(source["bag_id"].astype(str))
    if expected != actual:
        raise ValueError("BAG_HISTORY_COVERAGE")
    lookup = source.assign(_bag_key=source["bag_id"].astype(str)).set_index("_bag_key")
    array = lookup.loc[frame["bag_id"].astype(str), list(H_COLUMNS)].to_numpy(dtype=float)
    if not np.isfinite(array).all():
        raise ValueError("BAG_HISTORY_NONFINITE")
    return array


def validate_aligned_inputs(members: Any, post: Any, pre: Any, h: Any = None,
                            *, k: int = K) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    frame = validate_member_schema(members, k=k)
    post_array = _aligned_array(post, len(frame), "L0_POST", 400)
    pre_array = _aligned_array(pre, len(frame), "L0_PRE", 200)
    h_array = _h_array(frame, h)
    return frame, post_array, pre_array, h_array


def aggregate_bag_statistics(members: Any, post: Any, pre: Any, h: Any = None,
                             *, k: int = K) -> BagStatistics:
    """Aggregate exactly the saved eight members of each bag.

    Variance is the sample variance (ddof=1), followed by the N2R log1p
    transform in :func:`make_n2r_views`.  No class or half is rebalanced here.
    """

    frame = validate_member_schema(members, k=k)
    post_array = _aligned_array(post, len(frame), 'BAG_POST')
    pre_array = _aligned_array(pre, len(frame), 'BAG_PRE')
    h_array = _h_array(frame, h)
    rows: list[dict[str, Any]] = []
    post_mean: list[np.ndarray] = []
    post_var: list[np.ndarray] = []
    pre_mean: list[np.ndarray] = []
    pre_var: list[np.ndarray] = []
    for bag_id, part in frame.groupby("bag_id", sort=False, dropna=False):
        indices = part.index.to_numpy(dtype=int)
        first = part.iloc[0]
        row = {column: first[column] for column in frame.columns if column in {
            "bag_id", "matched_pair_id", "candidate_id", "split_group_id", "stimulus_local_id",
            "A_half", "previous_code", "previous_run_bin", "outer_fold", "inner_fold",
        }}
        row["bag_id"] = bag_id
        rows.append(row)
        post_mean.append(post_array[indices].mean(axis=0))
        post_var.append(post_array[indices].var(axis=0, ddof=1))
        pre_mean.append(pre_array[indices].mean(axis=0))
        pre_var.append(pre_array[indices].var(axis=0, ddof=1))
        if not np.allclose(h_array[indices], h_array[indices[0]], rtol=0.0, atol=0.0):
            raise ValueError("H_BAG_NOT_CONSTANT_WITHIN_BAG")
    bag_frame = pd.DataFrame(rows)
    return BagStatistics(
        bag_frame,
        np.asarray([h_array[frame.index[frame["bag_id"] == bag_id][0]] for bag_id in bag_frame["bag_id"]]),
        np.asarray(post_mean), np.asarray(post_var), np.asarray(pre_mean), np.asarray(pre_var),
    )


def quadratic_mean(mean: Any) -> np.ndarray:
    """Return [x_i, x_i*x_j for i<=j], with the prescribed 44 columns for 8D."""

    values = np.asarray(mean, dtype=float)
    if values.ndim != 2:
        raise ValueError("MEAN_MATRIX_REQUIRED")
    products = [values[:, index] * values[:, other]
                for index in range(values.shape[1]) for other in range(index, values.shape[1])]
    return np.column_stack([values, *products])


def _log_variance(values: np.ndarray) -> np.ndarray:
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("NEGATIVE_OR_NONFINITE_VARIANCE")
    return np.log1p(values)


def make_n2r_views(stats: BagStatistics, *, include_full: bool = False, full_stats: BagStatistics | None = None) -> dict[str, np.ndarray]:
    """Build the fixed nine N2R views from already transformed trial features."""

    h = np.asarray(stats.h, dtype=float)
    post_mean, pre_mean = stats.post_mean, stats.pre_mean
    if post_mean.shape[1]!=8 or pre_mean.shape[1]!=8:raise ValueError('N2R_PC8_REQUIRED')
    post_var, pre_var = _log_variance(stats.post_var), _log_variance(stats.pre_var)
    post_quad, pre_quad = quadratic_mean(post_mean), quadratic_mean(pre_mean)
    views = {
        "H": h,
        "HM": np.column_stack([h, post_mean]),
        "HMV": np.column_stack([h, post_mean, post_var]),
        "HQ": np.column_stack([h, post_quad]),
        "HQV": np.column_stack([h, post_quad, post_var]),
        "HQQ": np.column_stack([h, post_quad / np.sqrt(2.0), post_quad / np.sqrt(2.0)]),
        "HPRE": np.column_stack([h, pre_quad, pre_var]),
        "HPREQ": np.column_stack([h, pre_quad, pre_var, post_quad]),
        "HPREQV": np.column_stack([h, pre_quad, pre_var, post_quad, post_var]),
    }
    if include_full:
        if full_stats is None or full_stats.post_mean.shape!=(len(post_mean),400):raise ValueError('SEPARATE_FULL400_STATISTICS_REQUIRED')
        views.update({
            # The FULL sensitivities are separate raw L0 controls, rather
            # than H-augmented N2R views.  For the real packet these become
            # 400 and 800 columns after train-only trial scaling.
            "FULL_MU": full_stats.post_mean,
            "FULL_MU_VAR": np.column_stack([full_stats.post_mean, _log_variance(full_stats.post_var)]),
        })
    if any(not np.isfinite(value).all() for value in views.values()):
        raise ValueError("N2R_VIEW_NONFINITE")
    return views


def n2r_views(stats: BagStatistics, *, include_full: bool = False, full_stats: BagStatistics | None = None) -> dict[str, np.ndarray]:
    return make_n2r_views(stats, include_full=include_full,full_stats=full_stats)


def forbidden_feature_columns(columns: Sequence[str]) -> list[str]:
    return sorted(set(map(str, columns)) & IDENTIFIER_COLUMNS)


def validate_feature_whitelist(columns: Sequence[str]) -> None:
    forbidden = forbidden_feature_columns(columns)
    if forbidden:
        raise ValueError("IDENTIFIER_FEATURE_COLUMNS:" + ",".join(forbidden))


def _linear_api():
    from .linear import WeightedPCA, WeightedScaler
    return WeightedScaler, WeightedPCA


@dataclass
class TrialTransforms:
    post_scaler: Any
    pre_scaler: Any
    post_pca: Any
    pre_pca: Any
    fit_groups: tuple[str, ...]


def fit_trial_transforms(members: Any, post: Any, pre: Any, fit_groups: Sequence[str],
                         weights: Any = None, *, pca_dim: int = 8) -> TrialTransforms:
    """Fit post/pre scaler and PCA using only the requested identity groups."""

    # H is a bag-level input and is not needed while fitting the trial
    # transforms.  Accept packets that carry H in the separate frozen array.
    frame, post_array, pre_array, _ = validate_aligned_inputs(
        members, post, pre, np.zeros((len(_as_frame(members)), len(H_COLUMNS)), dtype=float)
    )
    groups = {str(value) for value in fit_groups}
    mask = frame["split_group_id"].astype(str).isin(groups).to_numpy()
    if int(mask.sum()) < 1:
        raise ValueError("EMPTY_TRANSFORM_FIT_SCOPE")
    if weights is None:
        fit_weights = np.ones(int(mask.sum()), dtype=float)
    else:
        full_weights = np.asarray(weights, dtype=float)
        if full_weights.shape != (len(frame),):
            raise ValueError("TRANSFORM_WEIGHT_ALIGNMENT")
        fit_weights = full_weights[mask]
    WeightedScaler, WeightedPCA = _linear_api()
    post_scaler, pre_scaler = WeightedScaler(), WeightedScaler()
    post_scaled = post_scaler.fit(post_array[mask], fit_weights).transform(post_array[mask])
    pre_scaled = pre_scaler.fit(pre_array[mask], fit_weights).transform(pre_array[mask])
    post_pca, pre_pca = WeightedPCA(), WeightedPCA()
    post_pca.fit(post_scaled, fit_weights)
    pre_pca.fit(pre_scaled, fit_weights)
    return TrialTransforms(post_scaler, pre_scaler, post_pca, pre_pca,
                           tuple(sorted(groups)))


def transform_trials(post: Any, pre: Any, transforms: TrialTransforms,
                     *, pca_dim: int = 8) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    post_scaled = transforms.post_scaler.transform(np.asarray(post, dtype=float))
    pre_scaled = transforms.pre_scaler.transform(np.asarray(pre, dtype=float))
    post_pc = transforms.post_pca.transform(post_scaled, n_components=pca_dim)
    pre_pc = transforms.pre_pca.transform(pre_scaled, n_components=pca_dim)
    return post_scaled, pre_scaled, post_pc, pre_pc


# Small compatibility aliases used by the packet runner and pure tests.
validate_bag_members = validate_member_schema


def build_bag_features(members: Any, post: Any, pre: Any, history: Any = None, *, k: int = K) -> BagStatistics:
    """Aggregate bag features, accepting either aligned H rows or bag history."""

    h = bag_history_array(members, history) if isinstance(history, pd.DataFrame) else history
    return aggregate_bag_statistics(members, post, pre, h, k=k)


make_views = make_n2r_views


__all__ = [
    "K", "H_COLUMNS", "REQUIRED_MEMBER_COLUMNS", "VIEW_NAMES", "FULL_VIEW_NAMES",
    "BagStatistics", "TrialTransforms", "validate_member_schema", "validate_bag_members",
    "validate_aligned_inputs", "validate_feature_whitelist", "aggregate_bag_statistics",
    "bag_history_array",
    "build_bag_features", "quadratic_mean", "make_n2r_views", "make_views", "n2r_views",
    "fit_trial_transforms", "transform_trials",
]
