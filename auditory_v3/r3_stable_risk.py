"""Stable, uncalibrated R3 logit risks for already fitted native logistic heads.

Finite logits can map to exactly zero or one in floating-point ``expit``.
Cross-entropy is therefore evaluated from logits directly, without clipping,
refitting, changing regularization, or altering the prediction distribution.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import roc_auc_score

from .linear import normalized_weights
from .statistics import hierarchical_weights, stratified_identity_bootstrap


def scoring_hash():
    """Provenance for this scoring correction, separate from frozen fit hashes."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def per_row_logit_loss(y, logits):
    y = np.asarray(y, dtype=np.float64)
    logits = np.asarray(logits, dtype=np.float64)
    if y.ndim != 1 or y.shape != logits.shape or not np.all(np.isin(y, [0., 1.])):
        raise ValueError("Binary outcomes and one-dimensional logits must align")
    # A nonfinite logit is an invalid observation, even when its infinite sign
    # agrees with the outcome. Do not silently score +inf as perfect evidence.
    loss = np.full(len(y), np.nan, dtype=np.float64)
    finite = np.isfinite(logits)
    loss[finite] = np.logaddexp(0., (1. - 2. * y[finite]) * logits[finite]) / np.log(2.)
    return loss


def stable_metrics(y, logits, weights):
    """Match weighted_metrics' schema while evaluating exact native-logit BCE."""
    y, logits = np.asarray(y), np.asarray(logits, dtype=np.float64)
    weights = normalized_weights(weights, len(y))
    losses = per_row_logit_loss(y, logits)
    if not np.all(np.isfinite(logits)) or not np.all(np.isfinite(losses)):
        return {"status": "INCOMPLETE_OR_NONFINITE", "ce_bits": None,
                "J_bits": None, "bacc": None, "auc": None, "brier": None}
    ce = float(weights @ losses)
    probability = expit(logits)
    recalls = [float(np.average((logits[y == label] >= 0.) == label,
                                weights=weights[y == label]))
               for label in (0, 1) if np.any(y == label) and weights[y == label].sum() > 0]
    return {"status": "PASS", "ce_bits": ce, "J_bits": 1. - ce,
            "bacc": float(np.mean(recalls)) if len(recalls) == 2 else None,
            "auc": float(roc_auc_score(y, logits, sample_weight=weights)) if len(recalls) == 2 else None,
            "brier": float(weights @ ((probability - y) ** 2))}


def paired_logit_contrasts(frame, logit_columns, contrasts, *, seed=63017,
                           repetitions=2000, group_col="split_group_id",
                           class_col="stimulus_local_id", fold_col="outer_fold"):
    """Return (aggregate, identity table), with the original complete denominator.

    ``logit_columns`` maps model names to columns containing decision-function
    values. A model with any absent/nonfinite OOF logit is invalid as a whole;
    successful folds are never used to replace its complete-OOF estimate.
    Contrast gains remain CE(reference) minus CE(candidate), in bits/trial.
    The caller supplies every frozen OOF observation, including failed rows.
    """
    frame = frame.reset_index(drop=True).copy()
    weights = hierarchical_weights(frame, group_col=group_col, class_col=class_col)
    if frame[[group_col, fold_col]].isna().any().any():
        raise ValueError("Every frozen OOF identity must retain its original outer fold")
    if frame.groupby(group_col)[fold_col].nunique().ne(1).any():
        raise ValueError("Identity occurs in more than one outer fold")
    for reference, candidate in contrasts.values():
        if reference not in logit_columns or candidate not in logit_columns:
            raise ValueError("A contrast references an undeclared logit model")
    y = frame[class_col].to_numpy()
    metrics = {name: stable_metrics(y, frame[column].to_numpy(), weights)
               for name, column in logit_columns.items()}
    identity_rows = []
    for group, part in frame.groupby(group_col, sort=True):
        indices = part.index.to_numpy()
        group_weights = normalized_weights(weights[indices], len(indices))
        row = {group_col: group, fold_col: part[fold_col].iloc[0], "n_observations": len(indices)}
        for name, column in logit_columns.items():
            loss = per_row_logit_loss(y[indices], frame.loc[indices, column].to_numpy())
            row[name] = float(group_weights @ loss) if np.all(np.isfinite(loss)) else np.nan
        for name, (reference, candidate) in contrasts.items():
            row[name] = row[reference] - row[candidate]
        identity_rows.append(row)
    identities = pd.DataFrame(identity_rows)
    contrast_result = stratified_identity_bootstrap(identities, list(contrasts), repetitions=repetitions,
                    seed=seed, group_col=group_col, fold_col=fold_col)
    fold_metrics, half_metrics = {}, {}
    for split_col, target in ((fold_col, fold_metrics), ("A_half", half_metrics)):
        for value, part in frame.groupby(split_col, sort=True):
            indices = part.index.to_numpy()
            subweights = hierarchical_weights(part, group_col=group_col, class_col=class_col)
            target[str(value)] = {name: stable_metrics(y[indices], frame.loc[indices, column].to_numpy(), subweights)
                                 for name, column in logit_columns.items()}
    return {"metrics": metrics, "contrasts": contrast_result,
            "fold_metrics": fold_metrics, "half_metrics": half_metrics,
            "n_groups": len(identities), "n_observations": len(frame)}, identities
