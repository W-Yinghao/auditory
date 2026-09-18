"""P_MATCH_bal risks and fixed-OOF identity bootstrap (no pipeline refits)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import xlogy
from sklearn.metrics import roc_auc_score

from .linear import normalized_weights


def hierarchical_weights(frame, group_col="split_group_id", half_col="A_half",
                         cell_cols=("previous_code", "previous_run_bin"),
                         class_col="stimulus_local_id"):
    """Equal mass at identity / half / history cell / class / observation.

    Missing history values are explicit cells. Incomplete class support raises
    rather than silently changing the target distribution. The original row
    order is retained even if the dataframe index is not unique.
    """
    columns = [group_col, half_col, *cell_cols, class_col]
    f = frame.loc[:, columns].reset_index(drop=True).copy()
    if len(f) == 0 or f[[group_col, half_col, class_col]].isna().any().any():
        raise ValueError("Empty population or missing identity/half/class")
    class_counts = f.groupby(columns[:-1], dropna=False)[class_col].nunique()
    if not (class_counts == 2).all():
        raise ValueError("Every fixed history cell must retain both classes")
    weight = np.ones(len(f), dtype=np.float64) / f[group_col].nunique()
    prefix = [group_col]
    levels = [[half_col], list(cell_cols), [class_col]]
    for level in levels:
        # Count distinct child tuples within each parent, without encoding
        # history cells in potentially colliding string concatenations.
        child = f[prefix + level].drop_duplicates()
        count = child.groupby(prefix, dropna=False).size().rename("_children")
        row_counts = f[prefix].merge(count.reset_index(), how="left", on=prefix,
                                     sort=False)["_children"].to_numpy()
        weight /= row_counts
        prefix += level
    observations = f.groupby(prefix, dropna=False)[group_col].transform("size").to_numpy()
    weight /= observations
    return normalized_weights(weight, len(f))


def per_row_log_loss(y, probability):
    y, p = np.asarray(y, dtype=np.float64), np.asarray(probability, dtype=np.float64)
    if y.shape != p.shape or not np.all(np.isin(y, [0.0, 1.0])):
        raise ValueError("Outcomes and probabilities must align")
    if np.any(np.isfinite(p) & ((p < 0) | (p > 1))):
        raise ValueError("Probability outside [0,1]")
    # Exact 0/1 predictions with the wrong label remain +inf; NaN is not zero.
    return -(xlogy(y, p) + xlogy(1 - y, 1 - p)) / np.log(2.0)


def weighted_metrics(y, probability, weights):
    y, p = np.asarray(y), np.asarray(probability, dtype=np.float64)
    w = normalized_weights(weights, len(y))
    loss = per_row_log_loss(y, p)
    if not np.all(np.isfinite(loss)) or not np.all(np.isfinite(p)):
        return {"status": "INCOMPLETE_OR_NONFINITE", "ce_bits": None,
                "J_bits": None, "bacc": None, "auc": None, "brier": None}
    ce = float(w @ loss)
    recalls = [float(np.average((p[y == c] >= 0.5) == c, weights=w[y == c]))
               for c in (0, 1) if np.any(y == c) and w[y == c].sum() > 0]
    return {"status": "PASS", "ce_bits": ce, "J_bits": 1 - ce,
            "bacc": float(np.mean(recalls)) if len(recalls) == 2 else None,
            "auc": float(roc_auc_score(y, p, sample_weight=w)) if len(recalls) == 2 else None,
            "brier": float(w @ ((p - y) ** 2))}


def stratified_identity_bootstrap(identity_frame, value_columns, *, repetitions=2000,
                                  seed=63017, group_col="split_group_id",
                                  fold_col="outer_fold"):
    """One shared resampling array for all contrasts, within original folds."""
    f = identity_frame.sort_values([fold_col, group_col]).reset_index(drop=True)
    if f[group_col].duplicated().any() or f[[group_col, fold_col]].isna().any().any():
        raise ValueError("Bootstrap requires exactly one row per identity and an outer fold")
    if not len(f):
        raise ValueError("Cannot bootstrap empty identities")
    values = f[list(value_columns)].to_numpy(dtype=np.float64)
    rng = np.random.default_rng(seed)
    totals = np.zeros((repetitions, len(value_columns)), dtype=np.float64)
    for _, part in f.groupby(fold_col, sort=True):
        positions = part.index.to_numpy()
        draws = rng.choice(positions, size=(repetitions, len(positions)), replace=True)
        totals += values[draws].sum(axis=1)
    bootstrap = totals / len(f)
    out = {}
    for j, column in enumerate(value_columns):
        v = values[:, j]
        if not np.all(np.isfinite(v)):
            out[column] = {"status": "INCOMPLETE_OR_NONFINITE", "gain_bits": None,
                           "ci_low": None, "ci_high": None, "positive_group_fraction": None,
                           "n_groups": len(f)}
            continue
        lo, hi = np.quantile(bootstrap[:, j], [.025, .975])
        out[column] = {"status": "PASS", "gain_bits": float(v.mean()),
                       "ci_low": float(lo), "ci_high": float(hi),
                       "positive_group_fraction": float(np.mean(v > 0)), "n_groups": len(f),
                       "identical_group_differences": bool(np.all(v == 0)),
                       "fold_gains": {str(k): float(part[column].mean())
                                      for k, part in f.groupby(fold_col, sort=True)},
                       "bootstrap_repetitions": repetitions, "bootstrap_seed": seed,
                       "scope": "fixed_oof_not_pipeline_refit"}
    return out


def paired_contrasts(frame, probability_columns, contrasts, *, seed=63017,
                     repetitions=2000, group_col="split_group_id",
                     class_col="stimulus_local_id", fold_col="outer_fold"):
    """Score complete models and return (public aggregate, private identity rows).

    probability_columns maps model names to dataframe column names. contrasts
    maps contrast names to (reference_model, candidate_model); gain is CEref-CEcand.
    No model's incomplete predictions can be averaged over its successful rows.
    """
    f = frame.reset_index(drop=True).copy()
    weights = hierarchical_weights(f, group_col=group_col, class_col=class_col)
    if f.groupby(group_col)[fold_col].nunique().ne(1).any():
        raise ValueError("Identity occurs in more than one outer fold")
    y = f[class_col].to_numpy()
    identity_rows = []
    metrics = {name: weighted_metrics(y, f[col].to_numpy(), weights)
               for name, col in probability_columns.items()}
    for group, part in f.groupby(group_col, sort=True):
        ix = part.index.to_numpy()
        wg = normalized_weights(weights[ix], len(ix))
        row = {group_col: group, fold_col: part[fold_col].iloc[0], "n_observations": len(ix)}
        for name, col in probability_columns.items():
            loss = per_row_log_loss(y[ix], f.loc[ix, col].to_numpy())
            row[name] = float(wg @ loss) if np.all(np.isfinite(loss)) else np.nan
        for name, (reference, candidate) in contrasts.items():
            row[name] = row[reference] - row[candidate]
        identity_rows.append(row)
    identities = pd.DataFrame(identity_rows)
    contrast_result = stratified_identity_bootstrap(identities, list(contrasts),
            repetitions=repetitions, seed=seed, group_col=group_col, fold_col=fold_col)
    fold_metrics, half_metrics = {}, {}
    for split_col, target in ((fold_col, fold_metrics), ("A_half", half_metrics)):
        for value, part in f.groupby(split_col, sort=True):
            ix = part.index.to_numpy()
            # Reweight the chosen half/fold's fixed identities equally.
            subweights = hierarchical_weights(part, group_col=group_col, class_col=class_col)
            target[str(value)] = {name: weighted_metrics(y[ix], f.loc[ix, col].to_numpy(), subweights)
                                  for name, col in probability_columns.items()}
    return {"metrics": metrics, "contrasts": contrast_result,
            "fold_metrics": fold_metrics, "half_metrics": half_metrics,
            "n_groups": len(identities), "n_observations": len(f)}, identities
