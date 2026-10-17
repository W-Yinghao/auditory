"""Candidate-swap consistent scoring of the SAME observations."""
from __future__ import annotations
from typing import Callable
import numpy as np

def _differences(d: np.ndarray) -> np.ndarray:
    a = np.asarray(d, dtype=np.float64)
    if a.ndim != 2 or min(a.shape) == 0 or not np.isfinite(a).all():
        raise ValueError("d must be finite shape (windows, segments)")
    return a

def summaries(d: np.ndarray) -> np.ndarray:
    a = _differences(d)
    return np.column_stack([a.mean(1), a.std(1), a.min(1), a.max(1), a[:, -1] - a[:, 0]])

def _score(h: Callable[[np.ndarray], np.ndarray], d: np.ndarray) -> np.ndarray:
    s = np.asarray(h(d), dtype=np.float64)
    if s.shape != (len(d),) or not np.isfinite(s).all():
        raise ValueError("score function must return one finite logit per window")
    return s

def antisymmetric_logit(h: Callable[[np.ndarray], np.ndarray], d: np.ndarray) -> np.ndarray:
    a = _differences(d)
    return 0.5 * (_score(h, a) - _score(h, -a))

def sigmoid(logit: np.ndarray) -> np.ndarray:
    a = np.asarray(logit, dtype=np.float64)
    if not np.isfinite(a).all():
        raise ValueError("logits must be finite")
    out = np.empty_like(a)
    pos = a >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-a[pos]))
    ea = np.exp(a[~pos]); out[~pos] = ea / (1.0 + ea)
    return out

def paired_order_metrics(h: Callable[[np.ndarray], np.ndarray], d: np.ndarray) -> dict[str, float | int]:
    """Input d is attended-minus-ignored for evaluation only.

    Evaluate label=1 on d and label=0 on -d. Each physical window receives one
    averaged contribution; swapped copies do not double the independent n.
    Train/test splitting and fitting h remain the caller's responsibility.
    """
    a = _differences(d)
    lp, lm = _score(h, a), _score(h, -a)
    correct_plus = (lp > 0).astype(float) + 0.5 * (lp == 0)
    correct_minus = (lm < 0).astype(float) + 0.5 * (lm == 0)
    acc = 0.5 * (correct_plus + correct_minus)
    loss = 0.5 * (np.logaddexp(0.0, -lp) + np.logaddexp(0.0, lm)) / np.log(2.0)
    return {"n_physical_windows": len(a), "accuracy": float(acc.mean()),
            "logloss_bits": float(loss.mean()),
            "swap_logit_error_max": float(np.max(np.abs(lp + lm)))}
