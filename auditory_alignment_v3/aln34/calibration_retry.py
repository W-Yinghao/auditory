"""Versioned numerical recovery for training-side positive-affine calibration.

Successful historical fits are returned verbatim. Only an explicit optimizer
failure triggers a longer line search for the identical convex objective.
"""
import hashlib
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from ..aln3_reference.calibration import AffineLogitCalibrator as Legacy

FIT_EVENTS = []


class AffineLogitCalibrator(Legacy):
    @classmethod
    def fit(cls, scores, labels, sample_weight=None, l2=1e-6):
        try:
            answer = Legacy.fit(scores, labels, sample_weight, l2)
        except RuntimeError as exc:
            if not str(exc).startswith('Calibration optimizer did not converge:'):
                raise
            original_error = str(exc)
        else:
            FIT_EVENTS.append({'solver': 'original', 'fallback': False})
            return answer
        # Legacy.fit has already validated every input and the two classes.
        x, y = np.asarray(scores, dtype=float), np.asarray(labels, dtype=float)
        w = np.ones_like(x) if sample_weight is None else np.asarray(sample_weight, dtype=float)
        w = w / w.sum()
        prior, mu = float(w@y), float(w@x)
        scale = float(np.sqrt(w@((x-mu)**2)))
        assert scale >= 1e-12
        z = (x-mu)/scale
        def obj(ab):
            a, b = ab
            logits = a*z+b
            value = w@(np.logaddexp(0, logits)-y*logits)+0.5*l2*(a*a+b*b)
            residual = expit(logits)-y
            grad = np.array([w@(residual*z)+l2*a, w@residual+l2*b])
            return float(value), grad
        res = minimize(obj, [1., np.log(prior/(1-prior))], jac=True, method='L-BFGS-B',
                       bounds=[(1e-8, None), (None, None)],
                       options={'maxiter': 3000, 'ftol': 1e-12, 'gtol': 1e-8, 'maxls': 100})
        value, grad = obj(res.x)
        projected = grad.copy()
        if res.x[0] <= 1.0001e-8:
            projected[0] = min(projected[0], 0.)
        residual = float(abs(projected).max())
        if (not res.success or not np.isfinite(res.x).all() or not np.isfinite(value)
                or res.x[0] < 1e-8 or residual > 1e-7):
            raise RuntimeError(f'Calibration recovery failed: {res.message}; projected gradient={residual}')
        FIT_EVENTS.append({'solver': 'same_objective_lbfgsb_maxls100', 'fallback': True,
                           'original_error': original_error, 'message': str(res.message),
                           'projected_gradient_inf': residual, 'objective': value, 'iterations': int(res.nit),
                           'n_training_rows': len(x), 'score_sha256': hashlib.sha256(x.tobytes()).hexdigest(),
                           'label_sha256': hashlib.sha256(y.tobytes()).hexdigest()})
        return cls(float(res.x[0]), float(res.x[1]), mu, scale)
