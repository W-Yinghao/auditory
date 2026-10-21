"""Small convex CPU reference, with target labels restricted to support fitting.

H0 = offset; E0 = offset + scores @ a0.
HP = offset + H @ delta.
EC = offset + H @ delta + beta * (scores @ a0).
ET = EC + source_residualized_time_features @ gamma, beta >= 0.
Raw B satisfies a0 @ B = 0; source nuisance projection and residual whitening
are frozen and actually applied to support and query, not just used to check rank.

Source fitting, preprocessing, trial/block identities, and source/target exclusions
are the responsibility of the adapter. See docs/03_READOUT_CONTRACT.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


STATES = ("H0", "E0", "HP", "EC", "ET")
DIMENSIONS = {"bernoulli": 3, "gaussian": 5}


class FitFailure(RuntimeError):
    """A numerical fit failed; the adapter must not publish it as a valid zero."""


def _array(value: Any, ndim: int, name: str) -> np.ndarray:
    out = np.asarray(value, dtype=np.float64)
    if out.ndim != ndim or not np.isfinite(out).all():
        raise ValueError(f"{name} must be a finite {ndim}-dimensional array")
    return out


def _family(family: str) -> int:
    if family not in DIMENSIONS:
        raise ValueError("family must be 'bernoulli' (K=3) or 'gaussian' (K=5)")
    return DIMENSIONS[family]


@dataclass(frozen=True)
class TemporalBasis:
    a0: np.ndarray
    matrix: np.ndarray
    nuisance_coefficients: np.ndarray
    residual_scale: np.ndarray
    history_dimension: int
    nuisance_column_scale: np.ndarray
    status: str
    nominal_rank: int
    source_conditional_singular_values: tuple[float, ...]
    source_n: int
    rank_rtol: float
    zero_direction_atol: float

    @property
    def rank(self) -> int:
        return self.matrix.shape[1]

    def project(self, scores: Any, history: Any) -> np.ndarray:
        """Apply a source-frozen residualization/whitening, with no target fit.

        Z = (X B - [1,H,X a0] C) / scale. Raw coefficient orthogonality
        alone would allow near-collinear time scores to duplicate H/shared m.
        """
        x = _array(scores, 2, "scores")
        h = _array(history, 2, "history")
        if x.shape[1] != len(self.a0) or h.shape != (len(x), self.history_dimension):
            raise ValueError("time projection requires the exact source score/history column contract")
        if self.nuisance_coefficients.shape != (self.history_dimension + 2, self.rank):
            raise ValueError("invalid source nuisance projection shape")
        if self.residual_scale.shape != (self.rank,) or not np.isfinite(self.residual_scale).all() or np.any(self.residual_scale <= 0):
            raise ValueError("invalid source residual scales")
        nuisance = np.column_stack((np.ones(len(x)), h, x @ self.a0))
        projected = (x @ self.matrix - nuisance @ self.nuisance_coefficients) / self.residual_scale
        if not np.isfinite(projected).all():
            raise ValueError("nonfinite source-frozen time features")
        return projected

    def as_dict(self) -> dict[str, Any]:
        return {"a0": self.a0.tolist(), "matrix": self.matrix.tolist(),
                "transform_version": "source_nuisance_residual_whiten_v1",
                "nuisance_coefficients": self.nuisance_coefficients.tolist(),
                "residual_scale": self.residual_scale.tolist(),
                "history_dimension": self.history_dimension,
                "nuisance_column_scale": self.nuisance_column_scale.tolist(),
                "status": self.status, "rank": self.rank, "nominal_rank": self.nominal_rank,
                "source_conditional_singular_values": list(self.source_conditional_singular_values),
                "source_n": self.source_n, "rank_rtol": self.rank_rtol,
                "zero_direction_atol": self.zero_direction_atol}


def build_time_basis(*, a0: Any, source_scores: Any,
                     source_history_design: Any | None = None,
                     rank_rtol: float = 1e-8,
                     zero_direction_atol: float = 1e-12) -> TemporalBasis:
    """Construct source-only conditional time features; accepts no y.

    Nominally K-1 coefficient directions orthogonal to a0, followed by a frozen
    projection off [1, history, shared m] and whitening of source residuals.
    Source rank and scales never use target support/query. Omitting source
    history means P=0, not permission to later pass a different history basis.
    """
    weights = _array(a0, 1, "a0")
    x = _array(source_scores, 2, "source_scores")
    if len(weights) not in (3, 5) or x.shape[1] != len(weights) or len(x) < 2:
        raise ValueError("source_scores must have >=2 rows and K=3 or K=5 matching a0")
    if not np.isfinite(rank_rtol) or not 0 < rank_rtol < 1:
        raise ValueError("rank_rtol must be in (0,1)")
    if not np.isfinite(zero_direction_atol) or zero_direction_atol < 0:
        raise ValueError("zero_direction_atol must be finite and nonnegative")
    history = np.empty((len(x), 0)) if source_history_design is None else _array(source_history_design, 2, "source_history_design")
    if len(history) != len(x):
        raise ValueError("source history and scores must have the same rows")
    k = len(weights)
    nuisance = np.column_stack((np.ones(len(x)), history, x @ weights))
    nuisance_scale = np.sqrt(np.mean(nuisance ** 2, axis=0))
    nuisance_scale[nuisance_scale == 0] = 1.0
    if np.linalg.norm(weights) <= zero_direction_atol:
        return TemporalBasis(weights.copy(), np.empty((k, 0)), np.empty((history.shape[1] + 2, 0)),
                             np.empty(0), history.shape[1], nuisance_scale.copy(),
                             "zero_shared_direction", k - 1, (), len(x), rank_rtol, zero_direction_atol)
    _, _, vh = np.linalg.svd(weights.reshape(1, -1), full_matrices=True)
    null_basis = vh[1:].T
    contrast = x @ null_basis
    # Normalize nuisance columns for the solve: a small but nonzero a0 must not
    # make its shared direction disappear from the nuisance rank decision.
    scaled_coefficients = np.linalg.lstsq(nuisance / nuisance_scale, contrast, rcond=rank_rtol)[0]
    nuisance_coefficients = scaled_coefficients / nuisance_scale[:, None]
    residual = contrast - nuisance @ nuisance_coefficients
    _, singular, vh_residual = np.linalg.svd(residual, full_matrices=False)
    scale = max(float(np.linalg.norm(x - x.mean(0), ord=2)), 1.0)
    keep = singular > rank_rtol * scale
    rotation = vh_residual[keep].T
    basis = null_basis @ rotation
    coefficients = nuisance_coefficients @ rotation
    residual_scale = singular[keep] / np.sqrt(len(x))
    # Remove arbitrary SVD sign flips from serialized coefficients.
    for col in range(basis.shape[1]):
        pivot = int(np.argmax(np.abs(basis[:, col])))
        if basis[pivot, col] < 0:
            basis[:, col] *= -1
            coefficients[:, col] *= -1
    rank = basis.shape[1]
    status = "full_rank" if rank == k - 1 else "no_independent_time_direction" if rank == 0 else "reduced_rank"
    return TemporalBasis(weights.copy(), basis.copy(), coefficients.copy(), residual_scale.copy(),
                         history.shape[1], nuisance_scale.copy(), status, k - 1,
                         tuple(map(float, singular)), len(x), rank_rtol, zero_direction_atol)


@dataclass(frozen=True)
class StateFit:
    history_delta: np.ndarray
    beta: float
    gamma: np.ndarray
    receipt: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"history_delta": self.history_delta.tolist(), "beta": self.beta,
                "gamma": self.gamma.tolist(), "receipt": self.receipt}


@dataclass(frozen=True)
class NestedReadoutFit:
    family: str
    a0: np.ndarray
    time_basis: TemporalBasis
    history_dimension: int
    states: dict[str, StateFit]
    penalties: dict[str, float]
    support_n: int
    support_class_counts: dict[str, int] | None

    def predict_linear(self, *, offset: Any, history_design: Any, scores: Any) -> dict[str, np.ndarray]:
        off, history, x = _inputs(offset, history_design, scores, self.a0, self.history_dimension)
        shared, temporal = x @ self.a0, self.time_basis.project(x, history)
        return {name: off + history @ state.history_delta + state.beta * shared + temporal @ state.gamma
                for name, state in self.states.items()}

    def predict(self, *, offset: Any, history_design: Any, scores: Any) -> dict[str, np.ndarray]:
        values = self.predict_linear(offset=offset, history_design=history_design, scores=scores)
        return {k: expit(v) for k, v in values.items()} if self.family == "bernoulli" else values

    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": "aln36.nested-readout.reference.v1", "reference_only": True,
                "family": self.family, "a0": self.a0.tolist(), "time_basis": self.time_basis.as_dict(),
                "history_dimension": self.history_dimension, "penalties": self.penalties,
                "support_n": self.support_n, "support_class_counts": self.support_class_counts,
                "states": {k: v.as_dict() for k, v in self.states.items()}}


def _inputs(offset: Any, history_design: Any, scores: Any, a0: np.ndarray,
            history_dimension: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    off, history, x = _array(offset, 1, "offset"), _array(history_design, 2, "history_design"), _array(scores, 2, "scores")
    if not len(off) or history.shape[0] != len(off) or x.shape != (len(off), len(a0)):
        raise ValueError("nonempty offset/history/scores must describe exactly the same rows")
    if history_dimension is not None and history.shape[1] != history_dimension:
        raise ValueError("history basis dimension differs from the fitted source contract")
    return off, history, x


def _optimize(*, family: str, offset: np.ndarray, design: np.ndarray, y: np.ndarray,
              center: np.ndarray, ridge: np.ndarray, beta_index: int | None,
              max_iter: int, gradient_tol: float) -> tuple[np.ndarray, dict[str, Any]]:
    def objective(theta: np.ndarray) -> tuple[float, np.ndarray]:
        eta = offset + design @ theta
        if family == "bernoulli":
            loss, residual = np.logaddexp(0, eta) - y * eta, expit(eta) - y
        else:
            residual = eta - y
            loss = 0.5 * residual ** 2
        difference = theta - center
        return (float(loss.sum() + 0.5 * np.sum(ridge * difference ** 2)),
                design.T @ residual + ridge * difference)

    initial_objective = objective(center)[0]
    if not len(center):
        theta, success, message, nit = center.copy(), True, "no free parameters", 0
    elif family == "gaussian":
        gram = design.T @ design + np.diag(ridge)
        rhs = design.T @ (y - offset) + ridge * center
        theta = np.linalg.solve(gram, rhs)
        if beta_index is not None and theta[beta_index] < 0:
            free = np.arange(len(theta)) != beta_index
            theta[beta_index] = 0.0
            theta[free] = np.linalg.solve(gram[np.ix_(free, free)], rhs[free])
        success, message, nit = True, "positive-ridge quadratic solve with one bound", 0
    else:
        bounds = [(0.0, None) if j == beta_index else (None, None) for j in range(len(center))]
        result = minimize(objective, center.copy(), jac=True, method="L-BFGS-B", bounds=bounds,
                          options={"maxiter": max_iter, "ftol": 1e-14, "gtol": gradient_tol * len(y) * 0.1,
                                   "maxls": 50})
        theta, success, message, nit = result.x, bool(result.success), str(result.message), int(result.nit)
    value, grad = objective(theta)
    projected = grad.copy()
    if beta_index is not None and theta[beta_index] <= 1e-10 and projected[beta_index] > 0:
        projected[beta_index] = 0.0
    scaled_gradient = float(np.max(np.abs(projected), initial=0.0) / max(1, len(y)))
    valid = success and np.isfinite(theta).all() and np.isfinite(value) and scaled_gradient <= gradient_tol
    receipt = {"success": bool(valid), "optimizer_success": success, "message": message,
               "iterations": nit, "objective": value, "initial_objective": initial_objective,
               "projected_gradient_max_per_support_row": scaled_gradient,
               "gradient_tolerance": gradient_tol, "identity_initialization": center.tolist(),
               "objective_definition": "sum Bernoulli NLL in nats or half sum squared error + half ridge distance to source identity"}
    if not valid:
        raise FitFailure(str(receipt))
    return theta, receipt


def fit_nested_readout(*, family: str, support_offset: Any, support_history: Any,
                       support_scores: Any, support_y: Any, a0: Any, time_basis: TemporalBasis,
                       ridge_history: float, ridge_scale: float, ridge_time: float,
                       max_iter: int = 2000, gradient_tol: float = 1e-7) -> NestedReadoutFit:
    """Fit HP/EC/ET on support only. No query data or query labels are accepted.

All three ridge strengths must be positive, finite, and fixed by the external
source-only contract. H0/E0 are retained exactly. Personal fits use equal rows;
no class weighting, resampling, or outer-query model selection occurs here.
"""
    k = _family(family)
    weights = _array(a0, 1, "a0")
    if len(weights) != k or not isinstance(time_basis, TemporalBasis):
        raise ValueError("a0/basis do not match the family")
    basis = _array(time_basis.matrix, 2, "time_basis.matrix")
    if basis.shape[0] != k or basis.shape[1] > k - 1 or not np.array_equal(weights, time_basis.a0):
        raise ValueError("time_basis must be bound to exactly this source a0")
    if not np.allclose(weights @ basis, 0, atol=1e-9 * max(1., np.linalg.norm(weights)), rtol=0):
        raise ValueError("time directions must be coefficient-orthogonal to source a0")
    penalties = {"history": float(ridge_history), "scale": float(ridge_scale), "time": float(ridge_time)}
    if any(not np.isfinite(v) or v <= 0 for v in penalties.values()):
        raise ValueError("all ridge strengths must be finite and strictly positive")
    if max_iter < 1 or not np.isfinite(gradient_tol) or gradient_tol <= 0:
        raise ValueError("invalid convergence settings")
    off, history, scores = _inputs(support_offset, support_history, support_scores, weights)
    if history.shape[1] != time_basis.history_dimension:
        raise ValueError("support history columns differ from the source time-projection contract")
    y = _array(support_y, 1, "support_y")
    if y.shape != off.shape or (family == "bernoulli" and not np.isin(y, [0., 1.]).all()):
        raise ValueError("support_y must match rows; Bernoulli labels must be 0 or 1")
    p, r = history.shape[1], basis.shape[1]
    states = {name: StateFit(np.zeros(p), beta, np.zeros(r), {"success": True, "fitted": False})
              for name, beta in (("H0", 0.0), ("E0", 1.0))}
    shared, temporal = scores @ weights, time_basis.project(scores, history)
    for name in ("HP", "EC", "ET"):
        if name == "ET" and r == 0:
            old = states["EC"]
            states[name] = StateFit(old.history_delta.copy(), old.beta, old.gamma.copy(),
                                   {**old.receipt, "identical_to": "EC", "temporal_test_available": False})
            continue
        use_scale = name != "HP"
        use_time = name == "ET"
        design = np.column_stack((history, shared)) if use_scale else history.copy()
        center = np.r_[np.zeros(p), 1.0] if use_scale else np.zeros(p)
        ridge = np.r_[np.full(p, ridge_history), ridge_scale] if use_scale else np.full(p, ridge_history)
        if use_time:
            design = np.column_stack((design, temporal))
            center = np.r_[center, np.zeros(r)]
            ridge = np.r_[ridge, np.full(r, ridge_time)]
        theta, receipt = _optimize(family=family, offset=off, design=design, y=y, center=center,
                                   ridge=ridge, beta_index=p if use_scale else None,
                                   max_iter=max_iter, gradient_tol=gradient_tol)
        receipt.update(fitted=True, temporal_test_available=bool(r), n_free_parameters=len(theta))
        states[name] = StateFit(theta[:p].copy(), float(theta[p]) if use_scale else 0.0,
                               theta[p+1:].copy() if use_time else np.zeros(r), receipt)
    if states["ET"].receipt["objective"] > states["EC"].receipt["objective"] + 1e-6 * max(1, len(y)):
        raise FitFailure("ET failed the nested support-objective check against EC with gamma=0")
    counts = {str(v): int((y == v).sum()) for v in (0, 1)} if family == "bernoulli" else None
    return NestedReadoutFit(family, weights.copy(), time_basis, p, states, penalties, len(y), counts)


def risk_contrasts(risks: dict[str, float]) -> dict[str, float]:
    """Direct paired algebra; call on each independent person's common query first."""
    if set(risks) != set(STATES) or not all(np.isfinite(v) for v in risks.values()):
        raise ValueError("finite H0/E0/HP/EC/ET risks are all required")
    h0, e0, hp, ec, et = (float(risks[s]) for s in STATES)
    return {"RsharedEEG": e0, "RpersonalEEG": et,
            "shared_EEG_gain": h0 - e0, "personal_calibrated_EEG_gain": hp - ec,
            "personal_EEG_gain": hp - et, "history_calibration_gain": h0 - hp,
            "time_increment": ec - et,
            "double_difference": (e0 - et) - (h0 - hp),
            "calibration_double_difference": (e0 - ec) - (h0 - hp),
            "total_EEG_risk_improvement": e0 - et}


def evaluate_readout(*, fit: NestedReadoutFit, query_offset: Any, query_history: Any,
                     query_scores: Any, query_y: Any) -> dict[str, Any]:
    """Evaluate once on a common query set. This function never refits/selects."""
    predictors = fit.predict_linear(offset=query_offset, history_design=query_history, scores=query_scores)
    y = _array(query_y, 1, "query_y")
    if y.shape != next(iter(predictors.values())).shape:
        raise ValueError("query labels and predictions have different rows")
    if fit.family == "bernoulli" and not np.isin(y, [0., 1.]).all():
        raise ValueError("Bernoulli query labels must be 0 or 1")
    if fit.family == "bernoulli":
        risks = {name: float(np.mean(np.logaddexp(0, eta) - y * eta) / np.log(2.))
                 for name, eta in predictors.items()}
        unit = "bits/trial"
    else:
        risks = {name: float(np.mean((eta - y) ** 2)) for name, eta in predictors.items()}
        unit = "source_target_scaled_MSE"
    return {"schema_version": "aln36.nested-readout.evaluation.v1", "reference_only": True,
            "family": fit.family, "n_query": len(y), "unit": unit,
            "risk": risks, "estimands": risk_contrasts(risks),
            "temporal_test_available": bool(fit.time_basis.rank),
            "inference": "per-person arithmetic only; no bootstrap, population n, or significance inferred"}
