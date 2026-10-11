"""Positive-slope affine logit calibration on training-side calibration data."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


@dataclass(frozen=True)
class AffineLogitCalibrator:
    slope: float
    intercept: float
    mean: float
    scale: float

    @classmethod
    def fit(cls, scores, labels, sample_weight=None, l2: float = 1e-6):
        x = np.asarray(scores, dtype=float)
        y = np.asarray(labels, dtype=float)
        if x.ndim != 1 or x.shape != y.shape or len(x) < 2 or not np.isfinite(x).all():
            raise ValueError("scores and labels must be aligned finite 1-D arrays")
        if not np.isin(y, [0, 1]).all() or len(np.unique(y)) != 2:
            raise ValueError("Both binary classes are required in calibration data")
        w = np.ones_like(x) if sample_weight is None else np.asarray(sample_weight, dtype=float)
        if w.shape != x.shape or not np.isfinite(w).all() or np.any(w < 0) or w.sum() <= 0 or l2 < 0:
            raise ValueError("Invalid sample weights or regularization")
        w = w / w.sum()
        prior = float(w @ y)
        if not 0 < prior < 1:
            raise ValueError("Both classes must have positive calibration weight")
        mu = float(w @ x)
        scale = float(np.sqrt(w @ ((x - mu) ** 2)))
        if scale < 1e-12:
            return cls(1.0, float(np.log(prior / (1 - prior))), mu, 1.0)
        z = (x - mu) / scale
        def obj(ab):
            a, b = ab
            logits = a * z + b
            value = w @ (np.logaddexp(0, logits) - y * logits) + 0.5 * l2 * (a*a + b*b)
            residual = expit(logits) - y
            grad = np.array([w @ (residual*z) + l2*a, w @ residual + l2*b])
            return float(value), grad
        init = [1.0, np.log(prior / (1 - prior))]
        res = minimize(obj, init, jac=True, method="L-BFGS-B", bounds=[(1e-8, None), (None, None)],
                       options={"maxiter": 3000, "ftol": 1e-12, "gtol": 1e-8})
        if not res.success:
            raise RuntimeError(f"Calibration optimizer did not converge: {res.message}")
        return cls(float(res.x[0]), float(res.x[1]), mu, scale)

    def logits(self, scores):
        x = np.asarray(scores, dtype=float)
        if not np.isfinite(x).all():
            raise ValueError("Non-finite prediction scores")
        return self.slope * ((x - self.mean) / self.scale) + self.intercept

    def predict(self, scores):
        return expit(self.logits(scores))

    def to_dict(self):
        return asdict(self)
