"""Training-only transforms and metadata-safe N2 bag summaries.

The module accepts trial feature arrays already produced by a caller.  It
never reads EEG, labels, clinical fields, or source paths, and fitted scale,
PCA, and RFF parameters are reusable without refitting on test regroupings.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _as_features(x):
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or not len(x) or not np.isfinite(x).all():
        raise ValueError("N2_FEATURE_SCHEMA")
    return x


def _candidate_weights(candidate_ids, n):
    raw = np.asarray(candidate_ids)
    if raw.ndim != 1 or len(raw) != n or pd.isna(raw).any():
        raise ValueError("N2_CANDIDATE_ALIGNMENT")
    ids = raw.astype(str)
    if ids.ndim != 1 or len(ids) != n:
        raise ValueError("N2_CANDIDATE_ALIGNMENT")
    counts = pd.Series(ids).value_counts(sort=False)
    return np.asarray([1.0 / counts[x] for x in ids], dtype=float)


def fit_weighted_scale(x, candidate_ids):
    """Fit candidate-equal weighted center/scale using training trials only."""
    x = _as_features(x)
    weights = _candidate_weights(candidate_ids, len(x))
    weights /= weights.sum()
    center = np.sum(x * weights[:, None], axis=0)
    variance = np.sum((x - center) ** 2 * weights[:, None], axis=0)
    scale = np.sqrt(np.maximum(variance, 1e-12))
    return {"center": center, "scale": scale,
            "fit_candidate_ids": sorted(set(np.asarray(candidate_ids).astype(str))),
            "weighting": "equal_candidate_total_weight"}


def transform_scale(x, scaler):
    x = _as_features(x)
    center, scale = np.asarray(scaler["center"], float), np.asarray(scaler["scale"], float)
    if (x.shape[1] != len(center) or len(scale) != len(center) or
            not np.isfinite(center).all() or not np.isfinite(scale).all() or
            (scale <= 0).any()):
        raise ValueError("N2_SCALE_SCHEMA")
    return (x - center[None, :]) / scale[None, :]


def fit_weighted_pca8(x, candidate_ids, *, scaler=None, max_components: int = 8):
    """Fit a candidate-weighted PCA (at most eight components) on training data."""
    x = _as_features(x)
    if max_components < 1 or max_components > 8:
        raise ValueError("N2_PCA_COMPONENTS")
    scaler = fit_weighted_scale(x, candidate_ids) if scaler is None else scaler
    z = transform_scale(x, scaler)
    weights = _candidate_weights(candidate_ids, len(x))
    weights /= weights.sum()
    mean = np.sum(z * weights[:, None], axis=0)
    centered = z - mean[None, :]
    covariance = (centered * weights[:, None]).T @ centered
    eigenvalues, vectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    rank = int(np.sum(eigenvalues > max(float(eigenvalues.max()), 1e-12) * 1e-10))
    n_components = min(int(max_components), x.shape[1], max(0, len(x) - 1), rank)
    if n_components < 1:
        raise ValueError("N2_PCA_DEGENERATE")
    components = vectors[:, order[:n_components]].T
    # Deterministic sign convention, independent of LAPACK eigenvector signs.
    for row in components:
        pivot = int(np.argmax(np.abs(row)))
        if row[pivot] < 0:
            row *= -1
    return {"scaler": scaler, "center": mean, "components": components,
            "eigenvalues": eigenvalues[order[:n_components]],
            "n_components": int(n_components),
            "fit_candidate_ids": sorted(set(np.asarray(candidate_ids).astype(str))),
            "weighting": "equal_candidate_total_weight"}


def transform_pca8(x, fit):
    z = transform_scale(x, fit["scaler"])
    center, components = np.asarray(fit["center"], float), np.asarray(fit["components"], float)
    if z.shape[1] != components.shape[1] or len(center) != z.shape[1]:
        raise ValueError("N2_PCA_SCHEMA")
    return (z - center[None, :]) @ components.T


def fit_rff16(x_train, *, seed: int = 11, pair_budget: int = 4096):
    """Fit fixed RFF parameters; bandwidth uses unlabeled training distances only."""
    x = _as_features(x_train)
    if len(x) < 2 or pair_budget < 1:
        raise ValueError("N2_RFF_SUPPORT")
    rng = np.random.default_rng(seed)
    pair_count = min(int(pair_budget), len(x) * (len(x) - 1) // 2)
    pair_set = set()
    while len(pair_set) < pair_count:
        left = int(rng.integers(0, len(x)))
        right = int(rng.integers(0, len(x) - 1))
        if right >= left:
            right += 1
        pair_set.add((min(left, right), max(left, right)))
    pairs = sorted(pair_set)
    distances = np.asarray([np.linalg.norm(x[a] - x[b]) for a, b in pairs])
    positive = distances[distances > 0]
    bandwidth = float(np.median(positive)) if len(positive) else 1.0
    if not np.isfinite(bandwidth) or bandwidth <= 0:
        bandwidth = 1.0
    frequencies = rng.normal(size=(x.shape[1], 16)) / bandwidth
    phase = rng.uniform(0, 2 * np.pi, size=16)
    return {"frequencies": frequencies, "phase": phase, "bandwidth": bandwidth,
            "seed": int(seed), "pair_budget": int(pair_budget),
            "fit_n_trials": int(len(x)), "fit_scope": "training_only"}


def transform_rff16(x, fit):
    x = _as_features(x)
    frequencies, phase = np.asarray(fit["frequencies"], float), np.asarray(fit["phase"], float)
    if (frequencies.shape != (x.shape[1], 16) or phase.shape != (16,) or
            not np.isfinite(frequencies).all() or not np.isfinite(phase).all()):
        raise ValueError("N2_RFF_SCHEMA")
    return np.sqrt(2.0 / 16.0) * np.cos(x @ frequencies + phase[None, :])


def _history_matrix(rows: pd.DataFrame, trial_order, known_codes=None):
    if rows is None:
        return np.empty((len(trial_order), 0), dtype=float), []
    required = {"trial_id", "previous_code", "previous_run_bin", "previous_gap_s",
                "position_fraction", "A_block_id", "onset_sample"}
    if not required.issubset(rows.columns) or rows.trial_id.isna().any():
        raise ValueError("N2_H_BAG_SCHEMA")
    keyed = rows.copy()
    keyed["_trial_key"] = keyed.trial_id.astype(str)
    if keyed["_trial_key"].duplicated().any():
        raise ValueError("N2_H_BAG_SCHEMA")
    keys = [str(value) for value in trial_order]
    lookup = keyed.set_index("_trial_key")
    if not set(keys).issubset(lookup.index):
        raise ValueError("N2_H_BAG_ALIGNMENT")
    ordered = lookup.loc[keys]
    codes = tuple(str(x) for x in (known_codes if known_codes is not None else
                                    sorted(ordered.previous_code.dropna().astype(str).unique())))
    bins = ("run_1", "run_2", "run_3_5", "run_6_plus", "unknown")
    output, names = [], []
    for code in codes:
        output.append(ordered.previous_code.astype(object).eq(code).astype(float).to_numpy())
        names.append(f"previous_code_{code}_proportion")
    known_mask = ordered.previous_code.astype(object).isin(codes)
    output.append((~known_mask).astype(float).to_numpy())
    names.append("previous_code_unknown_proportion")
    for run_bin in bins:
        output.append(ordered.previous_run_bin.astype(object).eq(run_bin).astype(float).to_numpy())
        names.append(f"previous_run_{run_bin}_proportion")
    gaps = pd.to_numeric(ordered.previous_gap_s, errors="coerce").to_numpy(float)
    positions = pd.to_numeric(ordered.position_fraction, errors="coerce").to_numpy(float)
    if not np.isfinite(positions).all() or not ((0 <= positions).all() and (positions <= 1).all()):
        raise ValueError("N2_H_BAG_POSITION")
    output.extend([np.nan_to_num(gaps, nan=0.0), np.isfinite(gaps).astype(float), positions,
                   positions ** 2])
    names.extend(["gap_mean", "gap_present", "position_mean", "position_squared"])
    return np.column_stack(output), names


def build_bag_features(x, trial_rows: pd.DataFrame, bags: pd.DataFrame, *,
                       h_rows: pd.DataFrame | None = None,
                       known_codes=None, rff_fit=None,
                       original_fs: float | None = None):
    """Aggregate fixed bags into MU/VAR/MU_VAR/MU_DUP/RFF/H_BAG arrays."""
    x = _as_features(x)
    if not {"trial_id"}.issubset(trial_rows.columns) or len(trial_rows) != len(x):
        raise ValueError("N2_TRIAL_FEATURE_ALIGNMENT")
    if (trial_rows.trial_id.isna().any() or trial_rows.trial_id.duplicated().any() or
            not {"bag_id", "trial_id"}.issubset(bags.columns) or bags.trial_id.isna().any() or
            bags.bag_id.isna().any()):
        raise ValueError("N2_BAG_FEATURE_SCHEMA")
    if bags.trial_id.duplicated().any():
        raise ValueError("N2_BAG_OVERLAP")
    trial_index = {str(t): i for i, t in enumerate(trial_rows.trial_id.astype(str))}
    bag_ids = sorted(bags.bag_id.astype(str).unique())
    mu, var, rff, h_values, bag_sizes, trial_lists = [], [], [], [], [], []
    gap_stds, position_stds, block_counts, time_coverages = [], [], [], []
    h_names = None
    if h_rows is not None:
        history_ids=sorted(set(bags.trial_id.astype(str)))
        full_h,h_names=_history_matrix(h_rows,history_ids,known_codes=known_codes)
        h_index={tid:i for i,tid in enumerate(history_ids)}
        hcols=['trial_id','previous_gap_s','position_fraction','A_block_id','onset_sample']
        hcols += [c for c in ('onset_seconds','original_fs') if c in h_rows]
        keyed_h=h_rows[hcols].copy()
        keyed_h['_trial_key']=keyed_h.trial_id.astype(str)
        keyed_h=keyed_h.set_index('_trial_key')
    grouped_bags=bags.assign(_bag_key=bags.bag_id.astype(str)).groupby('_bag_key',sort=True)
    for bag_id,part in grouped_bags:
        ids = part.trial_id.astype(str).tolist()
        if not ids or not set(ids).issubset(trial_index):
            raise ValueError("N2_BAG_TRIAL_ALIGNMENT")
        if "k" in part:
            ks = pd.to_numeric(part["k"], errors="coerce").dropna().unique()
            if len(ks) != 1 or int(ks[0]) != len(ids):
                raise ValueError("N2_BAG_K_ALIGNMENT")
        values = x[[trial_index[t] for t in ids]]
        mu.append(values.mean(axis=0))
        if len(values) < 2:
            var.append(np.full(x.shape[1], np.nan))
        else:
            var.append(np.log(np.var(values, axis=0, ddof=1) + 1e-6))
        if rff_fit is not None:
            rff_values = transform_rff16(values, rff_fit)
            rff.append(rff_values.mean(axis=0))
        if h_rows is not None:
            h=full_h[[h_index[tid] for tid in ids]]
            h_values.append(np.nanmean(h, axis=0))
            ordered_h = keyed_h.loc[ids]
            gaps = pd.to_numeric(ordered_h.previous_gap_s, errors="coerce").to_numpy(float)
            positions = pd.to_numeric(ordered_h.position_fraction, errors="coerce").to_numpy(float)
            gap_stds.append(float(np.nanstd(gaps)) if np.isfinite(gaps).any() else np.nan)
            position_stds.append(float(np.std(positions, ddof=1)) if len(positions) > 1 else np.nan)
            block_counts.append(int(ordered_h.A_block_id.nunique()))
            if "onset_seconds" in ordered_h:
                times = pd.to_numeric(ordered_h.onset_seconds, errors="coerce").to_numpy(float)
            else:
                samples = pd.to_numeric(ordered_h.onset_sample, errors="coerce").to_numpy(float)
                if original_fs is None and "original_fs" not in ordered_h:
                    raise ValueError("N2_H_BAG_FS_REQUIRED")
                if original_fs is None:
                    fs = pd.to_numeric(ordered_h["original_fs"], errors="coerce").to_numpy(float)
                else:
                    if not np.isfinite(float(original_fs)) or float(original_fs) <= 0:
                        raise ValueError("N2_H_BAG_FS")
                    fs = np.full(len(samples), float(original_fs))
                if not np.isfinite(fs).all() or (fs <= 0).any():
                    raise ValueError("N2_H_BAG_FS")
                times = samples / fs
            time_coverages.append(float(np.nanmax(times) - np.nanmin(times)) if np.isfinite(times).all() else np.nan)
        bag_sizes.append(len(values))
        trial_lists.append(ids)
    mu, var = np.asarray(mu), np.asarray(var)
    result = {"bag_ids": np.asarray(bag_ids, dtype=str), "MU": mu, "VAR": var,
              "MU_VAR": np.concatenate([mu, var], axis=1),
              "MU_DUP": np.concatenate([mu, mu], axis=1),
              "bag_sizes": np.asarray(bag_sizes, dtype=int),
              "variance_defined": np.asarray(bag_sizes, dtype=int) >= 2,
              "trial_ids": trial_lists}
    if rff_fit is not None:
        result["RFF_MEAN"] = np.asarray(rff)
    if h_rows is not None:
        h_array = np.asarray(h_values)
        extra = np.column_stack([gap_stds, position_stds, block_counts, time_coverages])
        result["H_BAG"] = np.column_stack([h_array, extra])
        result["H_BAG_columns"] = h_names + ["gap_std", "position_std", "block_count", "time_coverage_s"]
    return result
