"""Fixed out-of-fold identity-level paired bootstrap (plan section 9.3).

Scope is stated in every result: this resamples identities over FROZEN out-of-fold
predictions. It does not include re-training or re-splitting variance, and it is not a
prospective or external validation.

Two reporting choices are deliberate, both prompted by defects found when auditing
earlier rounds of this project:

* The interval convention is named explicitly (`percentile`) in the emitted record,
  rather than left for a reader to infer.
* `n_nonzero_paired_differences` is reported next to `n_identity_groups`. When two
  arms select the same candidate the paired difference is an exact structural zero;
  an interval computed over mostly-zero differences is narrow for a reason that has
  nothing to do with precision, and the reader must be able to see that.
"""
from __future__ import annotations

import numpy as np


def paired_identity_bootstrap(errors_reference: np.ndarray, errors_candidate: np.ndarray,
                              *, repetitions: int, seed: int, draws: np.ndarray | None = None) -> dict:
    """Gain = mean(|e_reference|) - mean(|e_candidate|); positive favours the candidate.

    `draws` lets all primary comparisons share one identity resampling index set, so
    contrasts are comparable; pass None to generate it from `seed`.
    """
    a = np.asarray(errors_reference, dtype=float)
    b = np.asarray(errors_candidate, dtype=float)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("PAIRED_BOOTSTRAP_SHAPE_MISMATCH")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return {"status": "INCOMPLETE_OR_NONFINITE", "gain_MAE": None, "ci_low": None, "ci_high": None,
                "n_identity_groups": int(a.size), "n_nonzero_paired_differences": None,
                "interval": "percentile", "scope": "fixed_oof_group_paired_not_pipeline_refit"}
    difference = a - b
    n = difference.size
    if draws is None:
        draws = np.random.default_rng(int(seed)).integers(0, n, size=(int(repetitions), n))
    replicates = difference[draws].mean(axis=1)
    low, high = np.quantile(replicates, [0.025, 0.975])
    return {
        "status": "PASS",
        "gain_MAE": float(difference.mean()),
        "ci_low": float(low),
        "ci_high": float(high),
        "n_identity_groups": int(n),
        "n_nonzero_paired_differences": int(np.count_nonzero(difference)),
        "repetitions": int(repetitions),
        "seed": int(seed),
        "interval": "percentile",
        "scope": "fixed_oof_group_paired_not_pipeline_refit",
    }


def shared_draws(n: int, *, repetitions: int, seed: int) -> np.ndarray:
    return np.random.default_rng(int(seed)).integers(0, int(n), size=(int(repetitions), int(n)))


def leave_one_identity_range(errors_reference: np.ndarray, errors_candidate: np.ndarray) -> dict:
    """Fixed-error influence diagnostic: the gain with each single identity removed."""
    a = np.asarray(errors_reference, dtype=float)
    b = np.asarray(errors_candidate, dtype=float)
    difference = a - b
    n = difference.size
    if n < 2:
        return {"min": None, "max": None}
    total = difference.sum()
    values = (total - difference) / (n - 1)
    return {"min": float(values.min()), "max": float(values.max())}


def error_metrics(y_true: np.ndarray, prediction: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    residual = prediction - y_true
    return {"MAE": float(np.abs(residual).mean()), "RMSE": float(np.sqrt(np.mean(residual ** 2))),
            "n": int(y_true.size)}
