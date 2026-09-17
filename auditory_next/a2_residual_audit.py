"""A2 residual audit in one fold's coordinate system; no clinical inputs.

Three independent mechanisms each receive 100 draws in the planned experiment.
Zero/fixed/train-fitted W are shared-draw conditions, not extra worlds/children.
This module generates one world at a time and never launches that experiment.
"""
from dataclasses import dataclass
import numpy as np

MECHANISMS = ("null", "predictable_nuisance", "individual_stimulus")


def _repeated(x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 2:
        x = x[None]
    if x.ndim != 3 or min(x.shape) < 1 or not np.isfinite(x).all():
        raise ValueError("A2_AUDIT_SHAPE_FINITE")
    return x


def identity_contrast(matrix, candidate_ids):
    """Diagonal minus different-identity pairs; bootstrap duplicates are not peers."""
    matrix, ids = np.asarray(matrix, float), np.asarray(candidate_ids, str)
    if matrix.shape != (len(ids), len(ids)) or not np.isfinite(matrix).all():
        raise ValueError("A2_MATCH_MATRIX")
    different = ids[:, None] != ids[None, :]
    if not different.any():
        raise ValueError("A2_MATCH_REQUIRES_TWO_IDENTITIES")
    same, other = float(np.diag(matrix).mean()), float(matrix[different].mean())
    return dict(matched=same, mismatched=other, gain=same - other)


def matching_statistics(first, second, candidate_ids):
    """Delta/P/R cosine and inner-product statistics, with explicit zero norms."""
    a, b = _repeated(first), _repeated(second)
    if a.shape != b.shape or a.shape[1] != len(candidate_ids):
        raise ValueError("A2_MATCH_ALIGNMENT")
    dots = np.einsum("rnf,rmf->rnm", a, b)
    na, nb = np.linalg.norm(a, axis=-1), np.linalg.norm(b, axis=-1)
    zero = int(np.sum(na == 0) + np.sum(nb == 0))
    cosine = None if zero else identity_contrast((dots / (na[:, :, None] * nb[:, None, :])).mean(axis=0), candidate_ids)
    return dict(inner_product=identity_contrast(dots.mean(axis=0), candidate_ids), cosine=cosine,
                cosine_status="UNDEFINED_ZERO_NORM" if zero else "DEFINED", zero_norm_vectors=zero,
                first_mean_norm=float(na.mean()), second_mean_norm=float(nb.mean()))


def inner_product_decomposition(delta1, delta2, prediction1, prediction2, candidate_ids):
    """Exact four-term decomposition for every pair, then matching differences.

    All inputs are [repeat,candidate,feature] or [candidate,feature] in ONE
    feature space. Repeat averaging precedes the identity statistic. No cosine
    expansion is asserted. Pair matrices/IDs are restricted outputs in real use.
    """
    a, b, p, q = map(_repeated, (delta1, delta2, prediction1, prediction2))
    if not (a.shape == b.shape == p.shape == q.shape) or a.shape[1] != len(candidate_ids):
        raise ValueError("A2_DECOMPOSITION_ALIGNMENT")
    dot = lambda x, y: np.einsum("rnf,rmf->nm", x, y) / len(x)
    terms = dict(delta_delta=dot(a, b), minus_delta_prediction=-dot(a, q),
                 minus_prediction_delta=-dot(p, b), prediction_prediction=dot(p, q))
    residual = dot(a - p, b - q)
    reconstructed = sum(terms.values())
    error = float(np.max(np.abs(residual - reconstructed)))
    tolerance = 1e-11 * max(1., float(np.max(np.abs(residual))),
                            *(float(np.max(np.abs(term))) for term in terms.values()))
    if error > tolerance:
        raise ValueError("A2_FOUR_TERM_IDENTITY")
    summaries = {name: identity_contrast(value, candidate_ids) for name, value in terms.items()}
    summaries["residual"] = identity_contrast(residual, candidate_ids)
    gain_error = abs(summaries["residual"]["gain"] - sum(summaries[name]["gain"] for name in terms))
    if gain_error > tolerance:
        raise ValueError("A2_FOUR_TERM_MATCH_CONTRAST")
    return dict(matrices={**terms, "residual": residual}, summaries=summaries,
                max_pair_error=error, matching_gain_error=float(gain_error), tolerance=tolerance)


@dataclass(frozen=True)
class BackgroundPredictor:
    center: np.ndarray
    target_center: np.ndarray
    coefficient: np.ndarray
    alpha: float
    n_training_candidates: int

    def predict(self, background):
        x = np.asarray(background, float)
        if x.shape[-1] != len(self.center) or not np.isfinite(x).all():
            raise ValueError("A2_BACKGROUND_PREDICTION_SHAPE")
        return (x - self.center) @ self.coefficient + self.target_center


def fit_background(background_train, delta_train, *, alpha=10.):
    """Candidate-equal ridge on training half means; never accepts evaluation data.

    Fixed alpha=10 retains the existing audit's finite-sample regression scale;
    it is not a tuned scientific endpoint. Features must already share a single
    training-fitted coordinate system. Intercept is unpenalized.
    """
    b, d = np.asarray(background_train, float), np.asarray(delta_train, float)
    if (b.ndim != 3 or d.ndim != 3 or b.shape[:2] != d.shape[:2] or b.shape[1] != 2 or
            len(b) < 2 or min(b.shape + d.shape) < 1 or not np.isfinite(b).all() or not np.isfinite(d).all()):
        raise ValueError("A2_BACKGROUND_TRAINING_SHAPE")
    if alpha != 10.:
        raise ValueError("A2_FIXED_AUDIT_RIDGE")
    x, y = b.mean(axis=1), d.mean(axis=1)
    center, target = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - center, y - target
    coefficient = np.linalg.solve(xc.T @ xc + alpha * np.eye(x.shape[1]), xc.T @ yc)
    for value in (center, target, coefficient):
        value.setflags(write=False)
    return BackgroundPredictor(center, target, coefficient, float(alpha), len(x))


def make_residual_world(mechanism, *, n_train=40, n_test=20, n_features=8, n_background=8,
                        noise_scale_train=None, noise_scale_test=None, seed=20260917):
    """One synthetic draw, with explicit aggregate-count-derived noise scales.

    Optional positive [candidate,half] noise SDs represent a caller-frozen
    support/missingness pattern AFTER eligibility. Missing values are rejected;
    do not use masking to delete difficult synthetic candidates after a result.
    Inputs contain no real EEG, clinical values or participant identities.
    """
    if mechanism not in MECHANISMS or min(n_train, n_test, n_features, n_background) < 2:
        raise ValueError("A2_SYNTHETIC_SPEC")
    rng = np.random.default_rng(seed)
    w_true = rng.normal(size=(n_background, n_features)) / np.sqrt(n_background)
    output = dict(mechanism=mechanism, seed=int(seed), world_draws=1, true_weight=w_true)
    for role, count, scale in (("train", n_train, noise_scale_train), ("test", n_test, noise_scale_test)):
        scale = np.ones((count, 2)) if scale is None else np.asarray(scale, float)
        if scale.shape != (count, 2) or not np.isfinite(scale).all() or np.any(scale <= 0):
            raise ValueError("A2_SYNTHETIC_NOISE_SCALE")
        stable_background = rng.normal(size=(count, n_background))
        background = np.repeat(stable_background[:, None, :], 2, axis=1)
        epsilon = rng.normal(size=(count, 2, n_features)) * scale[:, :, None]
        signal = np.zeros_like(epsilon)
        nuisance = np.zeros_like(epsilon)
        if mechanism == "predictable_nuisance":
            nuisance = 2 * (background @ w_true)
        elif mechanism == "individual_stimulus":
            signal = np.repeat((2 * rng.normal(size=(count, n_features)))[:, None, :], 2, axis=1)
        output[role] = dict(background=background, delta=signal + nuisance + epsilon,
                            stimulus=signal, nuisance=nuisance, epsilon=epsilon,
                            candidate_ids=tuple(f"synthetic_{role}_{i}" for i in range(count)))
    return output


def audit_residual_world(world):
    """Shared draw W=0, fixed nonzero W and train-fitted W; evaluation never fits."""
    train, test = world["train"], world["test"]
    fitted = fit_background(train["background"], train["delta"])
    fixed = 2 * np.asarray(world["true_weight"])
    delta, background = np.asarray(test["delta"]), np.asarray(test["background"])
    predictions = dict(zero=np.zeros_like(delta), fixed=background @ fixed, fitted=fitted.predict(background))
    output = {}
    for condition, prediction in predictions.items():
        audit = inner_product_decomposition(delta[:, 0], delta[:, 1], prediction[:, 0], prediction[:, 1], test["candidate_ids"])
        output[condition] = dict(audit["summaries"], max_pair_error=audit["max_pair_error"],
            matching_gain_error=audit["matching_gain_error"], world_draws=1, shared_draw_seed=world["seed"],
            matching={name: matching_statistics(value[:, 0], value[:, 1], test["candidate_ids"])
                      for name, value in (("delta", delta), ("prediction", prediction), ("residual", delta - prediction))})
    return dict(mechanism=world["mechanism"], world_draws=1, conditions=output, fitted_predictor=fitted)
