"""Frozen v3 normalized weighted linear readout and training-only transforms.

No sklearn ``C`` convention is used.  All optimizer attempts, including a
continuation, are exposed to the caller's fit ledger before optimization.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Callable, Mapping

import numpy as np
from scipy.linalg import svd
from scipy.optimize import minimize
from scipy.special import expit

_DEFAULT_LEDGER = None


def set_fit_ledger(ledger):
    """Install a process-local ledger, including for contract-test fits."""
    global _DEFAULT_LEDGER
    _DEFAULT_LEDGER = ledger


def require_slurm() -> None:
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Numerical execution requires a Slurm allocation")


def normalized_weights(weights, n: int) -> np.ndarray:
    a = np.asarray(weights, dtype=np.float64)
    if a.shape != (n,) or not np.all(np.isfinite(a)) or np.any(a < 0):
        raise ValueError("Weights must be finite, nonnegative and observation-aligned")
    # Dividing by the maximum first avoids overflow from an arbitrary common
    # weight multiplier, which has no role in the normalized objective.
    maximum = a.max(initial=0.0)
    if maximum <= 0:
        raise ValueError("Weights have zero mass")
    a = a / maximum
    return a / a.sum()


def _matrix(X) -> np.ndarray:
    a = np.asarray(X, dtype=np.float64)
    if a.ndim != 2 or len(a) == 0 or not np.all(np.isfinite(a)):
        raise ValueError("Features must be a nonempty finite two-dimensional matrix")
    return a


def logistic_objective_gradient(theta, X, y, weights, lambda_l2):
    """Return exact mean weighted BCE + lambda/2 ||w||² and its gradient."""
    X = _matrix(X)
    y = np.asarray(y, dtype=np.float64)
    theta = np.asarray(theta, dtype=np.float64)
    if y.shape != (len(X),) or not np.all(np.isin(y, [0.0, 1.0])):
        raise ValueError("Binary outcomes must be observation-aligned")
    if theta.shape != (X.shape[1] + 1,) or not np.all(np.isfinite(theta)):
        raise ValueError("Coefficient vector is nonfinite or has the wrong shape")
    if not np.isfinite(lambda_l2) or lambda_l2 < 0:
        raise ValueError("lambda_l2 must be finite and nonnegative")
    weights = normalized_weights(weights, len(X))
    return _objective_gradient(theta, X, y, weights, float(lambda_l2))


def _objective_gradient(theta, X, y, weights, lambda_l2):
    coef, intercept = theta[:-1], theta[-1]
    logits = X @ coef + intercept
    # logaddexp(0, +/-logit), selected by class, avoids cancellation at
    # correctly classified large logits without probability clipping.
    loss = np.logaddexp(0.0, (1.0 - 2.0 * y) * logits)
    value = float(weights @ loss + 0.5 * lambda_l2 * (coef @ coef))
    residual = weights * (expit(logits) - y)
    gradient = np.r_[X.T @ residual + lambda_l2 * coef, residual.sum()]
    return value, gradient


@dataclass
class LogisticFit:
    coef_: np.ndarray
    intercept_: float
    diagnostics: dict

    @property
    def success(self):
        return bool(self.diagnostics["success"])

    def decision_function(self, X):
        X = _matrix(X)
        if X.shape[1] != len(self.coef_):
            raise ValueError("Prediction feature dimension changed")
        if not self.success:
            return np.full(len(X), np.nan)
        return X @ self.coef_ + self.intercept_

    def predict_proba(self, X):
        """One-dimensional native P(y=1); failed fits remain NaN."""
        return expit(self.decision_function(X))


def fit_logistic(X, y, weights, lambda_l2, *, ledger: Callable | None = None,
                 context: Mapping | None = None, initial=None) -> LogisticFit:
    require_slurm()
    if ledger is None:
        ledger = _DEFAULT_LEDGER
    X = _matrix(X)
    y = np.asarray(y, dtype=np.float64)
    weights = normalized_weights(weights, len(X))
    if y.shape != (len(X),) or not np.all(np.isin(y, [0.0, 1.0])):
        raise ValueError("Binary outcomes must be observation-aligned")
    if len(np.unique(y[weights > 0])) != 2:
        raise ValueError("Both outcome classes need positive training weight")
    if not np.isfinite(lambda_l2) or lambda_l2 < 0:
        raise ValueError("lambda_l2 must be finite and nonnegative")
    theta = np.zeros(X.shape[1] + 1) if initial is None else np.asarray(initial, dtype=np.float64).copy()
    initial_objective, _ = logistic_objective_gradient(theta, X, y, weights, lambda_l2)
    context = dict(context or {})
    attempts, total_iterations = [], 0
    accepted = False
    for attempt in range(2):
        maxiter = 1000 if attempt == 0 else 2000 - total_iterations
        event = dict(context)
        event.update(event="logistic_fit_attempt", attempt=attempt + 1,
                     recovery=bool(attempt), n_observations=len(X),
                     n_features=X.shape[1], lambda_l2=float(lambda_l2),
                     max_iterations=maxiter, same_state_continuation=bool(attempt))
        if ledger is not None:
            ledger(event)
        try:
            result = minimize(_objective_gradient, theta, args=(X, y, weights, float(lambda_l2)),
                              jac=True, method="L-BFGS-B",
                              options={"maxiter": maxiter, "gtol": 1e-7,
                                       "ftol": 1e-15, "maxls": 50, "maxcor": 20})
            theta = np.asarray(result.x, dtype=np.float64)
            objective, gradient = _objective_gradient(theta, X, y, weights, float(lambda_l2))
            finite = bool(np.all(np.isfinite(theta)) and np.isfinite(objective)
                          and np.all(np.isfinite(gradient))
                          and np.all(np.isfinite(expit(X @ theta[:-1] + theta[-1]))))
            gradient_inf = float(np.max(np.abs(gradient)))
            accepted = bool(finite and objective <= initial_objective + 1e-10
                            and (gradient_inf <= 1e-5 or
                                 (result.success and gradient_inf <= 1e-4)))
            total_iterations += int(result.nit)
            attempts.append({"attempt": attempt + 1, "objective": float(objective),
                             "gradient_inf": gradient_inf, "finite": finite,
                             "solver_success": bool(result.success),
                             "solver_message": str(result.message),
                             "iterations": int(result.nit), "accepted": accepted})
            if accepted or not finite:
                break
        except (FloatingPointError, ValueError, np.linalg.LinAlgError) as error:
            attempts.append({"attempt": attempt + 1, "objective": None,
                             "gradient_inf": None, "finite": False,
                             "solver_success": False, "solver_message": str(error),
                             "iterations": 0, "accepted": False})
            break
    diagnostics = {"success": accepted, "status": "PASS" if accepted else "NUMERICAL_FAIL",
                   "initial_objective": initial_objective,
                   "final_objective": attempts[-1]["objective"],
                   "gradient_inf": attempts[-1]["gradient_inf"],
                   "finite": attempts[-1]["finite"],
                   "solver_message": attempts[-1]["solver_message"],
                   "lambda_l2": float(lambda_l2), "total_iterations": total_iterations,
                   "attempt_count": len(attempts), "attempts": attempts}
    return LogisticFit(theta[:-1].copy(), float(theta[-1]), diagnostics)


class WeightedScaler:
    """Weighted population center/scale, fitted exclusively on supplied rows."""
    def fit(self, X, weights):
        X = _matrix(X)
        weights = normalized_weights(weights, len(X))
        self.mean_ = weights @ X
        variance = weights @ ((X - self.mean_) ** 2)
        self.scale_ = np.sqrt(np.maximum(variance, 0.0))
        self.constant_ = self.scale_ <= np.finfo(np.float64).eps
        self.scale_[self.constant_] = 1.0
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        X = _matrix(X)
        if X.shape[1] != self.n_features_in_:
            raise ValueError("Scaler feature dimension changed")
        return (X - self.mean_) / self.scale_

    def fit_transform(self, X, weights):
        return self.fit(X, weights).transform(X)


class WeightedPCA:
    """Weighted SVD directions up to numerical rank, never whitened."""
    def fit(self, X, weights):
        X = _matrix(X)
        weights = normalized_weights(weights, len(X))
        self.mean_ = weights @ X
        weighted_centered = (X - self.mean_) * np.sqrt(weights[:, None])
        _, singular, vt = svd(weighted_centered, full_matrices=False, check_finite=False)
        self.rank_tolerance_ = float(max(X.shape) * np.finfo(np.float64).eps * singular.max(initial=0))
        self.rank_ = int(np.count_nonzero(singular > self.rank_tolerance_))
        self.components_ = vt[:self.rank_].copy()
        self.singular_values_ = singular[:self.rank_].copy()
        self.explained_variance_ = self.singular_values_ ** 2
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X, n_components=None):
        X = _matrix(X)
        if X.shape[1] != self.n_features_in_:
            raise ValueError("PCA feature dimension changed")
        k = self.rank_ if n_components is None else min(int(n_components), self.rank_)
        if k < 0:
            raise ValueError("Negative PCA dimension")
        return (X - self.mean_) @ self.components_[:k].T

    def views(self, X, k=8):
        X = _matrix(X)
        projected = self.transform(X)
        pc = projected[:, :min(k, self.rank_)]
        return {"FULL": X, "PC8": pc,
                "REST": projected[:, min(k, self.rank_):],
                "PC8_DUP": np.concatenate([pc, pc], axis=1) / np.sqrt(2.0)}
