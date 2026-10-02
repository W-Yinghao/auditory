"""Probability scoring and child-level aggregation. No fitting and no data access."""
from __future__ import annotations
import numpy as np


def check_probabilities(p: np.ndarray, y: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    p=np.asarray(p,dtype=np.float64); y=np.asarray(y)
    if p.ndim != 2 or p.shape[1] != 5 or y.shape != (p.shape[0],):
        raise ValueError("Expected probabilities [N,5] and labels [N].")
    if not np.all(np.isfinite(p)) or (p < 0).any() or not np.allclose(p.sum(1),1,atol=1e-8):
        raise ValueError("Probabilities must be finite, nonnegative and sum to 1.")
    if not np.all(np.isin(y,[1,2,3,4,5])):
        raise ValueError("SIR labels must remain in 1..5.")
    return p,y.astype(int)


def score_sir(p: np.ndarray, y: np.ndarray, *, floor: float=1e-6) -> dict[str,np.ndarray]:
    p,y=check_probabilities(p,y)
    if not (0 < floor < 0.2):
        raise ValueError("Invalid common probability floor.")
    protected=np.maximum(p,floor); protected/=protected.sum(1,keepdims=True)
    cdf=np.cumsum(p,axis=1)[:,:-1]
    truth=(y[:,None] <= np.arange(1,5)[None,:]).astype(float)
    onehot=np.eye(5)[y-1]
    return {
        "rps":np.mean((cdf-truth)**2,axis=1),
        "nll_bits":-np.log2(protected[np.arange(len(y)),y-1]),
        "brier":np.sum((p-onehot)**2,axis=1),
        "expected_score_mae":np.abs(p@np.arange(1,6)-y),
        "probability_sir_gt3":p[:,3:].sum(1),
    }


def equal_child_mean(losses: np.ndarray, child_ids: np.ndarray) -> float:
    losses=np.asarray(losses,dtype=float); child_ids=np.asarray(child_ids)
    if losses.ndim != 1 or losses.shape != child_ids.shape or len(losses)==0 or not np.isfinite(losses).all():
        raise ValueError("Finite loss and child vectors of equal nonzero length are required.")
    return float(np.mean([losses[child_ids==c].mean() for c in np.unique(child_ids)]))


def low_label_risk(risk12: float, risk24: float) -> float:
    if not np.isfinite([risk12,risk24]).all():
        raise ValueError("Both predeclared budgets must have complete results.")
    return 0.5*(risk12+risk24)
