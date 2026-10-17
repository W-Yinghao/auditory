"""Functional diagnostics, not estimators of neural information."""
from __future__ import annotations
from typing import Any
import numpy as np

def _matrix(x: Any, name: str) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64)
    if a.ndim != 2 or min(a.shape) == 0 or not np.isfinite(a).all():
        raise ValueError(f"{name} must be a finite, nonempty (rows, features) array")
    return a

def normalize_rows(x: Any, eps: float = 1e-12) -> np.ndarray:
    a = _matrix(x, "x")
    if eps <= 0:
        raise ValueError("eps must be positive")
    return a / np.maximum(np.linalg.norm(a, axis=1, keepdims=True), eps)

def residual_diagnostics(base: Any, residual: Any, eps: float = 1e-12) -> dict[str, float | int]:
    """Rows may be queries/tokens, not independent people. Zero-base rows are reported.

    eps is numerical protection, not a scientific admission threshold.
    """
    u, r = _matrix(base, "base"), _matrix(residual, "residual")
    if u.shape != r.shape:
        raise ValueError("base and residual shapes must match")
    if eps <= 0:
        raise ValueError("eps must be positive")
    nu, nr = np.linalg.norm(u, axis=1), np.linalg.norm(r, axis=1)
    valid = nu > eps
    coef = np.sum(u * r, axis=1) / np.maximum(nu ** 2, eps ** 2)
    parallel = coef[:, None] * u
    orthogonal = r - parallel
    before = normalize_rows(u, eps)
    after = normalize_rows(u + r, eps)
    def mean_valid(a: np.ndarray) -> float:
        return float(np.mean(a[valid])) if np.any(valid) else float("nan")
    return {
        "n_rows": int(len(u)), "n_nonzero_base_rows": int(valid.sum()),
        "n_zero_or_tiny_base_rows": int((~valid).sum()),
        "relative_residual_norm_mean": mean_valid(nr / np.maximum(nu, eps)),
        "relative_parallel_norm_mean": mean_valid(np.linalg.norm(parallel, axis=1) / np.maximum(nu, eps)),
        "relative_orthogonal_norm_mean": mean_valid(np.linalg.norm(orthogonal, axis=1) / np.maximum(nu, eps)),
        "normalized_change_mean": mean_valid(np.linalg.norm(after - before, axis=1)),
        "pre_normalization_change_mean": float(np.mean(nr)),
    }

def ridge_fit_predict(x: Any, y: Any, x_test: Any, alpha: float = 1.0) -> np.ndarray:
    """Centered isotropic ridge. No featurewise standardization. Synthetic reference only.

    This definition makes the orthogonal-coordinate invariance explicit.
    """
    x, y, xt = _matrix(x, "x"), _matrix(y, "y"), _matrix(x_test, "x_test")
    if len(x) != len(y) or xt.shape[1] != x.shape[1]:
        raise ValueError("ridge sample/feature dimensions do not match")
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be finite and positive")
    xm, ym = x.mean(0), y.mean(0)
    xc, yc = x - xm, y - ym
    if x.shape[1] <= x.shape[0]:
        w = np.linalg.solve(xc.T @ xc + alpha * np.eye(x.shape[1]), xc.T @ yc)
    else:
        w = xc.T @ np.linalg.solve(xc @ xc.T + alpha * np.eye(len(x)), yc)
    return (xt - xm) @ w + ym
