"""Fixed-query risk comparisons, separate from mismatch sensitivity."""
from __future__ import annotations
import numpy as np
from scipy.special import logsumexp


def binary_logloss_bits_from_logits(logits, labels):
    z, y = np.asarray(logits, float), np.asarray(labels, float)
    if z.shape != y.shape or not np.isfinite(z).all() or not np.isin(y, [0, 1]).all():
        raise ValueError("Invalid binary prediction arrays")
    return (np.logaddexp(0, z) - y * z) / np.log(2)


def retrieval_logloss_bits(scores, correct_index, temperature: float = 1.0):
    s = np.asarray(scores, float)
    idx = np.asarray(correct_index)
    if s.ndim != 2 or idx.shape != (s.shape[0],) or not np.issubdtype(idx.dtype, np.integer):
        raise ValueError("Expected scores [query,candidate] and integer correct indices")
    if not np.isfinite(s).all() or not np.isfinite(temperature) or temperature <= 0:
        raise ValueError("Invalid scores or temperature")
    if np.any(idx < 0) or np.any(idx >= s.shape[1]):
        raise ValueError("Correct index out of candidate range")
    s = s / temperature
    return (logsumexp(s, axis=1) - s[np.arange(len(idx)), idx]) / np.log(2)


def paired_risk_gain(base_loss, improved_loss, base_query_ids, improved_query_ids):
    """R(base)-R(improved) on exactly the same queries in the same order.

    Candidate/target contracts must additionally be checked by the caller.
    """
    a, b = np.asarray(base_loss, float), np.asarray(improved_loss, float)
    qa, qb = list(base_query_ids), list(improved_query_ids)
    if a.ndim != 1 or a.shape != b.shape or len(a) != len(qa) or qa != qb or len(set(qa)) != len(qa):
        raise ValueError("Losses require unique, exactly aligned query identifiers")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or len(a) == 0:
        raise ValueError("Invalid losses")
    return a - b
