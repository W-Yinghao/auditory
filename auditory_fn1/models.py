"""M0-M4 estimators for the FN1 record-level comparison.

Plan section 8. The only scientific contrast is the ORDER of non-linearity and
aggregation over the same 32 segments, same local features, same clinical target and
approximately the same parameter count:

    M3 (aggregate then learn) : yhat = b + c(C,Q) . gamma + w . phi(mean_k u_k)
    M4 (learn then aggregate) : yhat = b + c(C,Q) . gamma + w . (mean_k phi(u_k))

phi is 140 -> 8 -> 8 with tanh on the first layer and a linear second layer; the EEG
readout is 8 -> 1. Local map plus EEG head plus the global bias is 1209 parameters,
identical for M3 and M4 by construction (asserted in tests).

Implementation notes:
* Forward and backward are written explicitly in float64 numpy with a deterministic
  Adam. There is no CUDA path, so no non-deterministic kernel can enter, and the
  gradient is pinned against finite differences in tests/auditory_fn1/test_models.py.
* Every transform (imputation, standardisation, basis expansion) is fitted on the
  caller-declared training rows only and applied to evaluation rows.
* Clinical and neural penalties are separate; no bias term is ever penalised.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

LOCAL_DIMS = (140, 8, 8)
PARAMETER_COUNT = LOCAL_DIMS[0] * LOCAL_DIMS[1] + LOCAL_DIMS[1] + LOCAL_DIMS[1] * LOCAL_DIMS[2] + LOCAL_DIMS[2] + LOCAL_DIMS[2] + 1


# --------------------------------------------------------------------------- clinical


@dataclass
class TabularTransform:
    """Train-only median imputation, missingness indicators, basis expansion, scaling."""

    family: str
    medians: np.ndarray = field(default_factory=lambda: np.zeros(0))
    center: np.ndarray = field(default_factory=lambda: np.zeros(0))
    scale: np.ndarray = field(default_factory=lambda: np.ones(0))
    constant_columns: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=bool))

    def fit(self, x: np.ndarray) -> "TabularTransform":
        x = np.asarray(x, dtype=float)
        if x.ndim != 2:
            raise ValueError("CLINICAL_MATRIX_MUST_BE_2D")
        with np.errstate(all="raise"):
            medians = np.empty(x.shape[1])
            for j in range(x.shape[1]):
                column = x[:, j]
                finite = column[np.isfinite(column)]
                # A column with no finite training value becomes a constant zero plus
                # its indicator; it must never be filled from evaluation rows.
                medians[j] = float(np.median(finite)) if finite.size else 0.0
        self.medians = medians
        expanded = self._expand(self._impute(x))
        self.center = expanded.mean(axis=0)
        spread = expanded.std(axis=0)
        self.constant_columns = spread <= 0
        self.scale = np.where(self.constant_columns, 1.0, spread)
        return self

    def _impute(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        missing = ~np.isfinite(x)
        filled = np.where(missing, self.medians[None, :], x)
        return np.hstack([filled, missing.astype(float)])

    def _expand(self, filled: np.ndarray) -> np.ndarray:
        if self.family == "linear":
            return filled
        if self.family == "additive_quadratic":
            half = filled.shape[1] // 2
            continuous = filled[:, :half]
            # Additive squares only. No cross terms, by plan section 7.1.
            return np.hstack([filled, continuous ** 2])
        raise ValueError(f"UNKNOWN_CLINICAL_FAMILY:{self.family}")

    def transform(self, x: np.ndarray) -> np.ndarray:
        expanded = self._expand(self._impute(x))
        return (expanded - self.center[None, :]) / self.scale[None, :]


def ridge_solution(design: np.ndarray, y: np.ndarray, penalties: np.ndarray) -> tuple[np.ndarray, float]:
    """Ridge with a per-column penalty and an unpenalised intercept.

    Columns are centred here so the intercept is exactly the training mean of y.
    """
    design = np.asarray(design, dtype=float)
    y = np.asarray(y, dtype=float)
    if design.shape[0] != y.shape[0]:
        raise ValueError("RIDGE_SHAPE_MISMATCH")
    intercept = float(y.mean())
    centred = design - design.mean(axis=0, keepdims=True)
    gram = centred.T @ centred + np.diag(np.asarray(penalties, dtype=float))
    coef = np.linalg.solve(gram, centred.T @ (y - intercept))
    return coef, intercept


# --------------------------------------------------------------------------- set network


@dataclass
class SetNetwork:
    """phi: 140 -> tanh(8) -> linear(8); readout 8 -> 1; plus a global bias.

    `order` is the only difference between M3 and M4:
      "mean_then_map"  aggregates the 32 segments first, then applies phi (M3)
      "map_then_mean"  applies phi per segment, then aggregates (M4)
    """

    order: str
    clinical_dim: int
    seed: int
    params: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.order not in ("mean_then_map", "map_then_mean"):
            raise ValueError(f"UNKNOWN_SET_ORDER:{self.order}")
        rng = np.random.default_rng(self.seed)
        d0, d1, d2 = LOCAL_DIMS
        # Identical initialisation rule for both orders; the draw depends only on the
        # seed and the shapes, never on the order, so M3 and M4 start from the same
        # numbers for a given seed.
        self.params = {
            "W1": rng.normal(0.0, np.sqrt(1.0 / d0), (d0, d1)),
            "b1": np.zeros(d1),
            "W2": rng.normal(0.0, np.sqrt(1.0 / d1), (d1, d2)),
            "b2": np.zeros(d2),
            "w": np.zeros(d2),
            "b": np.zeros(()),
            "gamma": np.zeros(self.clinical_dim),
        }

    # -- parameter bookkeeping -------------------------------------------------
    @property
    def eeg_parameter_count(self) -> int:
        """Local map + EEG readout + global bias. Excludes the clinical branch."""
        return sum(int(np.size(self.params[k])) for k in ("W1", "b1", "W2", "b2", "w", "b"))

    def penalised_keys(self) -> tuple[str, ...]:
        return ("W1", "W2", "w")

    # -- forward ---------------------------------------------------------------
    def _phi(self, u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        pre = u @ self.params["W1"] + self.params["b1"]
        hidden = np.tanh(pre)
        out = hidden @ self.params["W2"] + self.params["b2"]
        return hidden, out

    def forward(self, segments: np.ndarray, clinical: np.ndarray) -> tuple[np.ndarray, dict]:
        """segments: (N, K, 140); clinical: (N, clinical_dim)."""
        segments = np.asarray(segments, dtype=float)
        clinical = np.asarray(clinical, dtype=float)
        if segments.ndim != 3 or segments.shape[2] != LOCAL_DIMS[0]:
            raise ValueError("SEGMENT_TENSOR_SHAPE")
        if clinical.shape[0] != segments.shape[0]:
            raise ValueError("CLINICAL_RECORD_COUNT_MISMATCH")
        n, k, _ = segments.shape
        if self.order == "mean_then_map":
            pooled = segments.mean(axis=1)
            hidden, mapped = self._phi(pooled)
            z = mapped
            cache = {"mode": "mean_then_map", "pooled": pooled, "hidden": hidden}
        else:
            flat = segments.reshape(n * k, LOCAL_DIMS[0])
            hidden, mapped = self._phi(flat)
            z = mapped.reshape(n, k, LOCAL_DIMS[2]).mean(axis=1)
            cache = {"mode": "map_then_mean", "flat": flat, "hidden": hidden, "k": k, "n": n}
        prediction = self.params["b"] + clinical @ self.params["gamma"] + z @ self.params["w"]
        cache.update({"z": z, "clinical": clinical, "segments": segments})
        return prediction, cache

    # -- backward --------------------------------------------------------------
    def gradients(self, cache: dict, residual: np.ndarray) -> dict:
        """d(mean squared error)/d(params) for residual = (prediction - target)."""
        n = residual.shape[0]
        scale = 2.0 / n
        g_pred = scale * residual
        grads = {
            "b": np.array(g_pred.sum()),
            "gamma": cache["clinical"].T @ g_pred,
            "w": cache["z"].T @ g_pred,
        }
        g_z = np.outer(g_pred, self.params["w"])
        if cache["mode"] == "mean_then_map":
            hidden = cache["hidden"]
            grads["W2"] = hidden.T @ g_z
            grads["b2"] = g_z.sum(axis=0)
            g_hidden = g_z @ self.params["W2"].T
            g_pre = g_hidden * (1.0 - hidden ** 2)
            grads["W1"] = cache["pooled"].T @ g_pre
            grads["b1"] = g_pre.sum(axis=0)
        else:
            k = cache["k"]
            g_mapped = np.repeat(g_z / k, k, axis=0)
            hidden = cache["hidden"]
            grads["W2"] = hidden.T @ g_mapped
            grads["b2"] = g_mapped.sum(axis=0)
            g_hidden = g_mapped @ self.params["W2"].T
            g_pre = g_hidden * (1.0 - hidden ** 2)
            grads["W1"] = cache["flat"].T @ g_pre
            grads["b1"] = g_pre.sum(axis=0)
        return grads

    def loss(self, segments: np.ndarray, clinical: np.ndarray, y: np.ndarray,
             neural_penalty: float, clinical_penalty: float) -> float:
        prediction, _ = self.forward(segments, clinical)
        residual = prediction - y
        penalty = neural_penalty * sum(float(np.sum(self.params[k] ** 2)) for k in self.penalised_keys())
        penalty += clinical_penalty * float(np.sum(self.params["gamma"] ** 2))
        return float(np.mean(residual ** 2) + penalty)


def train_set_network(network: SetNetwork, segments: np.ndarray, clinical: np.ndarray, y: np.ndarray,
                      *, steps: int, learning_rate: float, neural_penalty: float,
                      clinical_penalty: float) -> dict:
    """Full-batch Adam. Fixed step count; no early stopping of any kind."""
    m = {k: np.zeros_like(v, dtype=float) for k, v in network.params.items()}
    v = {k: np.zeros_like(val, dtype=float) for k, val in network.params.items()}
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    history: list[float] = []
    nonfinite = False
    for step in range(1, int(steps) + 1):
        prediction, cache = network.forward(segments, clinical)
        residual = prediction - y
        grads = network.gradients(cache, residual)
        for key in network.penalised_keys():
            grads[key] = grads[key] + 2.0 * neural_penalty * network.params[key]
        grads["gamma"] = grads["gamma"] + 2.0 * clinical_penalty * network.params["gamma"]
        objective = float(np.mean(residual ** 2))
        objective += neural_penalty * sum(float(np.sum(network.params[k] ** 2)) for k in network.penalised_keys())
        objective += clinical_penalty * float(np.sum(network.params["gamma"] ** 2))
        history.append(objective)
        if not np.isfinite(objective) or any(not np.all(np.isfinite(g)) for g in grads.values()):
            nonfinite = True
            break
        for key, grad in grads.items():
            m[key] = beta1 * m[key] + (1 - beta1) * grad
            v[key] = beta2 * v[key] + (1 - beta2) * grad ** 2
            mhat = m[key] / (1 - beta1 ** step)
            vhat = v[key] / (1 - beta2 ** step)
            network.params[key] = network.params[key] - learning_rate * mhat / (np.sqrt(vhat) + eps)
    return {
        "steps_run": len(history),
        "initial_objective": history[0] if history else None,
        "final_objective": history[-1] if history else None,
        "nonfinite": bool(nonfinite),
        "parameter_norm": float(np.sqrt(sum(float(np.sum(p ** 2)) for p in network.params.values()))),
        "status": "OPTIMIZATION_NONFINITE" if nonfinite else "OPTIMIZATION_BUDGET_COMPLETE",
    }


def clip_to_bounds(prediction: np.ndarray, bounds: Sequence[float] | None) -> np.ndarray:
    if bounds is None:
        return np.asarray(prediction, dtype=float)
    lo, hi = float(bounds[0]), float(bounds[1])
    if not lo < hi:
        raise ValueError("TARGET_BOUNDS_NOT_ORDERED")
    return np.clip(np.asarray(prediction, dtype=float), lo, hi)
