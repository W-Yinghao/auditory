"""Profiled objective: the clinical block is solved exactly at every theta.

On the normalised target y' and a training-scope-centred clinical design C_c:

    L(theta, gamma, b) = (1/n)||y' - b*1 - C_c gamma - f_theta(U)||^2
                       + (alpha/n)||gamma||^2
                       + (lambda/2) sum_W ||W||_F^2

For fixed theta, with r = y' - f_theta(U):

    b*(theta)     = mean(r)
    gamma*(theta) = (C_c^T C_c + alpha I)^{-1} C_c^T (r - mean(r))

Both are exact, so the clinical block no longer competes for the network's optimisation
budget and no longer carries the n-times-too-strong penalty that K0 confirmed.

The theta gradient of the profiled objective uses the envelope theorem: at the exact
(gamma*, b*) the partial derivatives through gamma and b vanish, so theta may be
differentiated with gamma*, b* held constant. That is an assumption about the
implementation being correct, so `profiled_gradient_check` verifies it against finite
differences of the PROFILED objective, with the clinical block re-solved inside every
perturbed evaluation.

(C_c^T C_c + alpha I) does not depend on theta, so it is Cholesky-factorised once per
fit and re-used; each theta update then costs one triangular solve. That is
numerically the same solution, not an approximation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from auditory_fn1.models import LOCAL_DIMS, PARAMETER_COUNT, SetNetwork

EEG_PARAMETER_KEYS = ("W1", "b1", "W2", "b2", "w")
PENALISED_KEYS = ("W1", "W2", "w")


@dataclass
class ClinicalBlock:
    """Training-scope centre and the cached factorisation of the normal-equation matrix."""

    centre: np.ndarray
    factor: tuple
    design_train: np.ndarray
    alpha: float
    n: int
    solves: int = field(default=0)

    @classmethod
    def fit(cls, design_train: np.ndarray, alpha: float) -> "ClinicalBlock":
        design_train = np.asarray(design_train, dtype=float)
        centre = design_train.mean(axis=0, keepdims=True)
        centred = design_train - centre
        gram = centred.T @ centred + float(alpha) * np.eye(centred.shape[1])
        return cls(centre=centre, factor=cho_factor(gram, lower=True), design_train=centred,
                   alpha=float(alpha), n=int(design_train.shape[0]))

    def solve(self, residual: np.ndarray) -> tuple[np.ndarray, float]:
        """gamma*, b* for the current residual r = y' - f_theta(U)."""
        self.solves += 1
        intercept = float(np.mean(residual))
        gamma = cho_solve(self.factor, self.design_train.T @ (residual - intercept))
        return gamma, intercept


def eeg_forward(network: SetNetwork, segments: np.ndarray) -> tuple[np.ndarray, dict]:
    """f_theta(U) only: no clinical term, no global bias."""
    zeros = np.zeros((segments.shape[0], 0))
    prediction, cache = network.forward(segments, zeros)
    return prediction, cache


def profiled_objective(network: SetNetwork, block: ClinicalBlock, segments: np.ndarray,
                       design: np.ndarray, y: np.ndarray, *, neural_penalty: float) -> dict:
    """Evaluate L at the exact clinical solution for the current theta."""
    f, cache = eeg_forward(network, segments)
    residual_target = y - f
    gamma, intercept = block.solve(residual_target)
    centred = design - block.centre
    error = f + intercept + centred @ gamma - y
    mse = float(np.mean(error ** 2))
    ridge_term = float(block.alpha / block.n * np.sum(gamma ** 2))
    neural_term = float(neural_penalty / 2.0 * sum(np.sum(network.params[k] ** 2) for k in PENALISED_KEYS))
    return {"objective": mse + ridge_term + neural_term, "mse": mse, "ridge_term": ridge_term,
            "neural_term": neural_term, "gamma": gamma, "intercept": intercept,
            "error": error, "cache": cache, "eeg_output": f}


def profiled_gradient(network: SetNetwork, state: dict, *, neural_penalty: float) -> dict:
    """Envelope-theorem gradient: differentiate theta with gamma*, b* held constant."""
    grads = network.gradients(state["cache"], state["error"])
    out = {key: grads[key] for key in EEG_PARAMETER_KEYS}
    for key in PENALISED_KEYS:
        out[key] = out[key] + neural_penalty * network.params[key]
    return out


def train_profiled(network: SetNetwork, block: ClinicalBlock, segments: np.ndarray, design: np.ndarray,
                   y: np.ndarray, *, steps: int, learning_rate: float, neural_penalty: float) -> dict:
    """Full-batch Adam on theta only; the clinical block is re-solved every step."""
    moment = {k: np.zeros_like(network.params[k], dtype=float) for k in EEG_PARAMETER_KEYS}
    velocity = {k: np.zeros_like(network.params[k], dtype=float) for k in EEG_PARAMETER_KEYS}
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    history: list[float] = []
    gradient_norms: list[float] = []
    nonfinite = False
    state = profiled_objective(network, block, segments, design, y, neural_penalty=neural_penalty)
    for step in range(1, int(steps) + 1):
        grads = profiled_gradient(network, state, neural_penalty=neural_penalty)
        history.append(state["objective"])
        gradient_norms.append(float(np.sqrt(sum(np.sum(g ** 2) for g in grads.values()))))
        if not np.isfinite(state["objective"]) or any(not np.all(np.isfinite(g)) for g in grads.values()):
            nonfinite = True
            break
        for key in EEG_PARAMETER_KEYS:
            moment[key] = beta1 * moment[key] + (1 - beta1) * grads[key]
            velocity[key] = beta2 * velocity[key] + (1 - beta2) * grads[key] ** 2
            mhat = moment[key] / (1 - beta1 ** step)
            vhat = velocity[key] / (1 - beta2 ** step)
            network.params[key] = network.params[key] - learning_rate * mhat / (np.sqrt(vhat) + eps)
        # Re-solve the clinical block after the theta update and record the full objective.
        state = profiled_objective(network, block, segments, design, y, neural_penalty=neural_penalty)
    return {
        "steps_run": len(history),
        "initial_objective": history[0] if history else None,
        "final_objective": float(state["objective"]),
        "final_mse": float(state["mse"]),
        "final_ridge_term": float(state["ridge_term"]),
        "final_neural_term": float(state["neural_term"]),
        "final_gradient_norm": gradient_norms[-1] if gradient_norms else None,
        "eeg_output_abs_max": float(np.max(np.abs(state["eeg_output"]))) if state["eeg_output"].size else 0.0,
        "clinical_coefficient_norm": float(np.linalg.norm(state["gamma"])),
        "clinical_intercept": float(state["intercept"]),
        "clinical_solves": int(block.solves),
        "nonfinite": bool(nonfinite),
        "status": "OPTIMIZATION_NONFINITE" if nonfinite else "OPTIMIZATION_BUDGET_COMPLETE",
        "gamma": state["gamma"], "intercept": state["intercept"],
    }


def predict(network: SetNetwork, block: ClinicalBlock, gamma: np.ndarray, intercept: float,
            segments: np.ndarray, design: np.ndarray) -> np.ndarray:
    """Evaluation uses the TRAINING centre, never a centre recomputed on held-out rows."""
    f, _ = eeg_forward(network, segments)
    return intercept + (design - block.centre) @ gamma + f


def profiled_gradient_check(seed: int = 7, n: int = 12, k: int = 5, p: int = 4,
                            alpha: float = 0.3, neural_penalty: float = 0.1,
                            probes: int = 6, step: float = 1e-6,
                            noise_floor: float = 1e-8, relative_tolerance: float = 1e-4) -> dict:
    """Finite-difference the PROFILED objective, re-solving the clinical block each time.

    A pure relative-error criterion is not usable here. Some components are exactly zero
    by construction: for `mean_then_map`, b2 shifts f by the same constant for every
    record, and that shift is absorbed exactly by b* = mean(r), so the profiled objective
    does not depend on it. Central differences of an order-one objective at h=1e-6 have a
    floor of about eps*|L|/h ~ 2e-10, so a zero gradient can only be confirmed in
    ABSOLUTE terms. The criterion is therefore mixed: components above `noise_floor` must
    agree relatively; components below it must agree absolutely.
    """
    rng = np.random.default_rng(seed)
    segments = rng.normal(size=(n, k, LOCAL_DIMS[0]))
    design = rng.normal(size=(n, p))
    y = rng.normal(size=n)
    per_key: dict[str, dict] = {}
    failures: list[dict] = []
    envelope_residual_sums: list[float] = []
    for order in ("mean_then_map", "map_then_mean"):
        network = SetNetwork(order=order, clinical_dim=0, seed=11)
        # A zero EEG readout makes every gradient trivially zero; perturb it first.
        network.params["w"] = rng.normal(scale=0.4, size=LOCAL_DIMS[2])
        block = ClinicalBlock.fit(design, alpha)
        state = profiled_objective(network, block, segments, design, y, neural_penalty=neural_penalty)
        envelope_residual_sums.append(float(np.abs(state["error"].sum())))
        grads = profiled_gradient(network, state, neural_penalty=neural_penalty)
        for key in EEG_PARAMETER_KEYS:
            flat = np.atleast_1d(network.params[key]).reshape(-1)
            analytic = np.atleast_1d(grads[key]).reshape(-1)
            shape = np.shape(network.params[key])
            worst_abs, worst_rel, compared, active = 0.0, 0.0, 0, 0
            for index in rng.choice(flat.size, size=min(probes, flat.size), replace=False):
                original = flat[index]
                flat[index] = original + step
                network.params[key] = flat.reshape(shape)
                plus = profiled_objective(network, block, segments, design, y,
                                          neural_penalty=neural_penalty)["objective"]
                flat[index] = original - step
                network.params[key] = flat.reshape(shape)
                minus = profiled_objective(network, block, segments, design, y,
                                           neural_penalty=neural_penalty)["objective"]
                flat[index] = original
                network.params[key] = flat.reshape(shape)
                numeric = (plus - minus) / (2 * step)
                magnitude = max(abs(numeric), abs(analytic[index]))
                absolute = abs(numeric - analytic[index])
                compared += 1
                worst_abs = max(worst_abs, absolute)
                if magnitude > noise_floor:
                    active += 1
                    relative = absolute / magnitude
                    worst_rel = max(worst_rel, relative)
                    if relative > relative_tolerance:
                        failures.append({"order": order, "key": key, "index": int(index),
                                         "analytic": float(analytic[index]), "numeric": float(numeric),
                                         "relative": float(relative)})
                elif absolute > noise_floor:
                    failures.append({"order": order, "key": key, "index": int(index),
                                     "analytic": float(analytic[index]), "numeric": float(numeric),
                                     "absolute": float(absolute)})
            per_key[f"{order}:{key}"] = {"compared": compared, "above_noise_floor": active,
                                         "max_absolute_error": worst_abs,
                                         "max_relative_error_where_active": worst_rel}
    return {
        "status": "GRADIENT_VERIFIED" if not failures else "GRADIENT_MISMATCH",
        "failures": failures,
        "per_key": per_key,
        "noise_floor": noise_floor,
        "relative_tolerance": relative_tolerance,
        "max_envelope_residual_sum": max(envelope_residual_sums),
        "parameter_count": PARAMETER_COUNT,
        "note": ("Finite differences of the profiled objective, with the clinical block re-solved "
                 "inside every perturbed evaluation. Components that are exactly zero by construction "
                 "(a constant shift in f absorbed by b*) are checked absolutely against the "
                 "finite-difference noise floor, not relatively."),
    }
