"""Candidate-balanced CPU readouts for already frozen feature coordinates.

Only caller-declared training data enter fit_probe. Its inner folds isolate
tabular transforms and heads, NOT an upstream encoder that produced X. Strict
inner validation of the whole encoder/readout pipeline needs the caller to
refit that encoder without each inner validation candidate (especially D).
Classifier weights are 1/(K*n_candidate_class), each candidate total one;
scaler/PCA weights are 1/n_candidate, also each candidate total one.
All fitting and tests must run through Slurm; this module performs no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import warnings

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp, softmax
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from auditory5.contracts import FitScope


C_GRID = (0.01, 0.1, 1.0, 10.0)
TEMPERATURE_BOUNDS = (0.25, 4.0)


def bin_20ms(X, *, processed_fs: float = 250.0) -> np.ndarray:
    """[trial,channel,time] -> channel-major 20 ms means at exactly 250 Hz.

    Five original processed samples form each nonoverlapping bin. Windows
    must contain a positive multiple of five samples: no silent truncation,
    event realignment, padding, baseline subtraction, or normalization.
    """
    x = np.asarray(X, dtype=np.float64)
    if processed_fs != 250.0:
        raise ValueError("L0_REQUIRES_250HZ: native-rate inputs need a separate definition")
    if (x.ndim != 3 or min(x.shape) < 1 or x.shape[-1] < 5
            or x.shape[-1] % 5 or not np.isfinite(x).all()):
        raise ValueError("L0_SHAPE: finite nonempty trials/channels and time multiple of 5 required")
    return x.reshape(x.shape[0], x.shape[1], x.shape[2] // 5, 5).mean(axis=-1).reshape(len(x), -1)


def _tabular(X) -> np.ndarray:
    x = np.asarray(X, dtype=np.float64)
    if x.ndim == 3:
        return bin_20ms(x)
    if x.ndim != 2 or min(x.shape) < 1 or not np.isfinite(x).all():
        raise ValueError("FEATURE_SUPPORT: finite nonempty tabular features required")
    return x


def _groups(groups, n_samples: int) -> np.ndarray:
    group = np.asarray(groups)
    if group.ndim != 1 or len(group) != n_samples or n_samples == 0:
        raise ValueError("GROUP_SUPPORT: groups must match nonempty observations")
    if any(value is None or (isinstance(value, (float, np.floating)) and not np.isfinite(value))
           for value in group):
        raise ValueError("GROUP_SUPPORT: group identifiers cannot be missing")
    return group


def _labels(y, n_samples: int) -> np.ndarray:
    values = np.asarray(y)
    try:
        encoded = values.astype(np.int64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("CLASS_SUPPORT: labels must be integer class indices") from exc
    if values.ndim != 1 or len(values) != n_samples or not np.array_equal(values, encoded):
        raise ValueError("CLASS_SUPPORT: labels must be aligned integer class indices")
    classes = np.unique(encoded)
    if len(classes) < 2 or not np.array_equal(classes, np.arange(len(classes))):
        raise ValueError("CLASS_SUPPORT: need every class in contiguous indices 0..K-1")
    return encoded


def candidate_weights(groups) -> np.ndarray:
    """Each candidate sums to one, independently of trial count or label."""
    group = _groups(groups, len(groups))
    unique, inverse, counts = np.unique(group, return_inverse=True, return_counts=True)
    del unique
    return 1.0 / counts[inverse]


def candidate_class_weights(y, groups) -> np.ndarray:
    """Each candidate sums to 1 and each of its K classes to 1/K.

    All candidates must contain every class. The total weight equals the
    number of candidates (not trials), fixing the meaning of sklearn's C as
    record duration changes. Evaluation normalizes by the total weight.
    """
    group = _groups(groups, len(y))
    labels = _labels(y, len(group))
    classes = np.unique(labels)
    weights = np.empty(len(labels), dtype=np.float64)
    for candidate in np.unique(group):
        own = group == candidate
        if not np.array_equal(np.unique(labels[own]), classes):
            raise ValueError("CANDIDATE_CLASS_SUPPORT: each candidate needs every class")
        for label in classes:
            mask = own & (labels == label)
            weights[mask] = 1.0 / (len(classes) * mask.sum())
    return weights


class CandidateTabularScaler:
    """Population mean/variance with equal candidate mass, train data only."""

    def fit(self, X, groups, scope: FitScope):
        x = _tabular(X)
        group = _groups(groups, len(x))
        scope.assert_fit_groups(group)
        weight = candidate_weights(group)
        weight /= weight.sum()
        self.mean_ = np.sum(x * weight[:, None], axis=0)
        constant = np.ptp(x, axis=0) == 0
        self.mean_[constant] = x[0, constant]
        variance = np.sum((x - self.mean_) ** 2 * weight[:, None], axis=0)
        if not np.isfinite(self.mean_).all() or not np.isfinite(variance).all():
            raise ValueError("SCALER_NUMERICAL_FAILURE: nonfinite training moments")
        self.scale_ = np.sqrt(variance)
        self.scale_[constant | (self.scale_ <= np.finfo(np.float64).eps)] = 1.0
        self.n_features_in_ = x.shape[1]
        self.fit_groups_ = tuple(np.unique(group).tolist())
        self.scope_hash_ = scope.hash
        return self

    def transform(self, X):
        x = _tabular(X)
        if x.shape[1] != self.n_features_in_:
            raise ValueError("FEATURE_DIMENSION: feature width differs from training")
        return (x - self.mean_) / self.scale_


class CandidateWeightedPCA:
    """SVD of sqrt(normalized candidate weights) times centered features.

    Keep min(max_components<=32, n_features, n_train_samples-1). Variance is the
    weighted population covariance eigenvalue; no whitening is applied.
    """

    def __init__(self, max_components=32):
        if (isinstance(max_components, bool) or int(max_components) != max_components
                or not 1 <= max_components <= 32):
            raise ValueError("PCA_DIMENSION: max_components must be an integer in [1,32]")
        self.max_components = int(max_components)

    def fit(self, X, groups, scope: FitScope):
        x = _tabular(X)
        group = _groups(groups, len(x))
        scope.assert_fit_groups(group)
        if len(x) < 2:
            raise ValueError("PCA_SUPPORT: at least two training observations required")
        weight = candidate_weights(group)
        weight /= weight.sum()
        self.mean_ = np.sum(x * weight[:, None], axis=0)
        constant = np.ptp(x, axis=0) == 0
        self.mean_[constant] = x[0, constant]
        weighted = (x - self.mean_) * np.sqrt(weight[:, None])
        _, singular, vt = np.linalg.svd(weighted, full_matrices=False)
        self.n_components_ = min(self.max_components, x.shape[1], len(x) - 1)
        components = vt[:self.n_components_].copy()
        # Deterministic sign convention for auditing and persistence.
        pivot = np.argmax(np.abs(components), axis=1)
        sign = np.sign(components[np.arange(len(components)), pivot])
        sign[sign == 0] = 1
        self.components_ = components * sign[:, None]
        self.singular_values_ = singular[:self.n_components_]
        self.explained_variance_ = self.singular_values_ ** 2
        self.n_features_in_ = x.shape[1]
        threshold = max(weighted.shape) * np.finfo(float).eps * singular[0]
        self.rank_ = int(np.sum(singular > threshold))
        self.fit_groups_ = tuple(np.unique(group).tolist())
        self.scope_hash_ = scope.hash
        return self

    def transform(self, X):
        x = _tabular(X)
        if x.shape[1] != self.n_features_in_:
            raise ValueError("FEATURE_DIMENSION: PCA input width differs from training")
        return (x - self.mean_) @ self.components_.T


def weighted_log_loss_nats(logits, y, weights) -> float:
    scores = np.asarray(logits, dtype=np.float64)
    labels = _labels(y, len(scores))
    weight = np.asarray(weights, dtype=np.float64)
    if (scores.ndim != 2 or scores.shape[1] != len(np.unique(labels))
            or not np.isfinite(scores).all() or weight.shape != labels.shape
            or not np.isfinite(weight).all() or np.any(weight <= 0)):
        raise ValueError("LOSS_SUPPORT: finite class logits and positive aligned weights required")
    loss = logsumexp(scores, axis=1) - scores[np.arange(len(labels)), labels]
    return float(np.dot(weight, loss) / weight.sum())


def fit_temperature(logits, y, groups, scope: FitScope) -> dict:
    """Fit bounded scalar T on training-only inner OOF logits in natural logs."""
    scores = np.asarray(logits, dtype=np.float64)
    group = _groups(groups, len(scores))
    scope.assert_fit_groups(group)
    weight = candidate_class_weights(y, group)

    def objective(log_temperature):
        return weighted_log_loss_nats(scores / math.exp(log_temperature), y, weight)

    baseline = objective(0.0)  # Also validates logits before the optimizer.
    if np.max(np.ptp(scores, axis=1)) <= np.finfo(float).eps:
        temperature, loss = 1.0, baseline
    else:
        optimized = minimize_scalar(objective, bounds=tuple(map(math.log, TEMPERATURE_BOUNDS)),
                                    method="bounded", options={"xatol": 1e-8})
        if not optimized.success or not math.isfinite(optimized.fun):
            raise ValueError("CALIBRATION_FAILURE: bounded temperature optimization failed")
        candidates = [(1.0, baseline),
                      (TEMPERATURE_BOUNDS[0], objective(math.log(TEMPERATURE_BOUNDS[0]))),
                      (TEMPERATURE_BOUNDS[1], objective(math.log(TEMPERATURE_BOUNDS[1]))),
                      (math.exp(optimized.x), float(optimized.fun))]
        temperature, loss = min(candidates, key=lambda item: (item[1], abs(math.log(item[0]))))
    return dict(temperature=float(temperature), fit_groups=tuple(np.unique(group).tolist()),
                scope_hash=scope.hash, objective_unit="nats", inner_oof_ce_bits=loss / math.log(2),
                raw_inner_oof_ce_bits=baseline / math.log(2), bounds=TEMPERATURE_BOUNDS)


def _head_logits(head, features) -> np.ndarray:
    logits = np.asarray(head.decision_function(features), dtype=np.float64)
    return np.column_stack((-logits / 2, logits / 2)) if logits.ndim == 1 else logits


def _fit_head(features, y, groups, C, seed):
    head = LogisticRegression(C=C, solver="lbfgs", max_iter=2000, tol=1e-8, random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        try:
            head.fit(features, y, sample_weight=candidate_class_weights(y, groups))
        except ConvergenceWarning as exc:
            raise ValueError("HEAD_CONVERGENCE_FAILURE: logistic solver did not converge") from exc
    return head


@dataclass
class FittedProbe:
    scaler: CandidateTabularScaler
    pca: CandidateWeightedPCA | None
    head: LogisticRegression
    selected_C: float
    temperature: float
    calibration: dict
    fit_scopes: dict
    inner_scores: list[dict]
    input_shape: tuple
    classes: np.ndarray
    seed: int

    @property
    def effective_feature_space(self):
        return "channel-major 20ms binned features" if len(self.input_shape) == 2 else "raw tabular input features"

    def effective_linear_head(self, *, calibrated=False) -> tuple[np.ndarray, np.ndarray]:
        """Compose head/PCA/scaler into K x p original feature coordinates.

        For 2D encoder input p is its full original width (including all 64
        coordinates when applicable). For 3D input p is the flattened binned
        feature width, NOT raw EEG samples. Binary class logits are [0, d].
        Setting calibrated=True additionally divides W and b by scalar T.
        """
        weight = self.head.coef_.copy()
        bias = self.head.intercept_.copy()
        if self.pca is not None:
            weight = weight @ self.pca.components_
            bias = bias - weight @ self.pca.mean_
        weight = weight / self.scaler.scale_[None, :]
        bias = bias - weight @ self.scaler.mean_
        if len(self.classes) == 2:
            weight = np.vstack((np.zeros_like(weight), weight))
            bias = np.r_[0.0, bias]
        if calibrated:
            weight, bias = weight / self.temperature, bias / self.temperature
        return weight, bias

    def predict(self, X_test) -> dict[str, np.ndarray]:
        """Prediction has no label argument and never updates fitted state."""
        if np.asarray(X_test).shape[1:] != self.input_shape:
            raise ValueError("FEATURE_SHAPE: inference shape differs from fitted feature definition")
        feature = self.scaler.transform(_tabular(X_test))
        if self.pca is not None:
            feature = self.pca.transform(feature)
        logits = _head_logits(self.head, feature)
        return {"raw": softmax(logits, axis=1),
                "calibrated": softmax(logits / self.temperature, axis=1)}


def fit_probe(X_train, y_train, groups_train, scope: FitScope, seed=20260917, inner_folds=3,
              pca_max_dim=32):
    """Select C by group OOF CE, calibrate its OOF logits, then refit all train.

    Tuning/calibration scores are training diagnostics, not held-out scientific
    results. GroupKFold is deterministic without shuffling; seed is recorded
    and passed to the solver. Scaler/PCA are freshly fitted inside every fold.
    pca_max_dim=None disables PCA; otherwise it is a fixed integer in [1,32].
    This function never receives held-out EEG or held-out labels.
    """
    input_shape = np.asarray(X_train).shape[1:]
    x = _tabular(X_train)
    y = _labels(y_train, len(x))
    group = _groups(groups_train, len(x))
    scope.assert_fit_groups(group)
    if pca_max_dim is not None:
        CandidateWeightedPCA(pca_max_dim)  # Validate before any fitting.
    if isinstance(inner_folds, bool) or int(inner_folds) != inner_folds or inner_folds < 2:
        raise ValueError("INNER_SUPPORT: at least two integer group folds required")
    if len(np.unique(group)) < inner_folds:
        raise ValueError("INNER_SUPPORT: fewer training candidate groups than folds")
    classes = np.unique(y)
    splits = list(GroupKFold(n_splits=int(inner_folds)).split(x, y, group))
    for train, validation in splits:
        if set(group[train]) & set(group[validation]):
            raise ValueError("INNER_GROUP_LEAKAGE")
        if any(not np.array_equal(np.unique(y[index]), classes) for index in (train, validation)):
            raise ValueError("INNER_CLASS_SUPPORT: every fit and validation fold needs every class")
    weights = candidate_class_weights(y, group)
    oof = {C: np.full((len(x), len(classes)), np.nan) for C in C_GRID}
    inner_scopes = []
    for fold, (train, validation) in enumerate(splits):
        inner_scope = FitScope(tuple(np.unique(group[train]).tolist()),
                               tuple(np.unique(group[validation]).tolist()),
                               tuple(scope.validation_groups) + tuple(scope.test_groups))
        scaler = CandidateTabularScaler().fit(x[train], group[train], inner_scope)
        z_train, z_valid = scaler.transform(x[train]), scaler.transform(x[validation])
        if pca_max_dim is not None:
            pca = CandidateWeightedPCA(pca_max_dim).fit(z_train, group[train], inner_scope)
            z_train, z_valid = pca.transform(z_train), pca.transform(z_valid)
        for C in C_GRID:
            head = _fit_head(z_train, y[train], group[train], C, seed)
            oof[C][validation] = _head_logits(head, z_valid)
        inner_scopes.append(dict(fold=fold, fit_groups=scaler.fit_groups_,
                                 validation_groups=tuple(np.unique(group[validation]).tolist()),
                                 scope_hash=inner_scope.hash,
                                 stages=("tabular_scaler", "weighted_pca", "logistic_head")
                                 if pca_max_dim is not None else ("tabular_scaler", "logistic_head")))
    scores = [dict(C=C, ce_bits=weighted_log_loss_nats(oof[C], y, weights) / math.log(2))
              for C in C_GRID]
    selected = min(scores, key=lambda item: (item["ce_bits"], item["C"]))["C"]
    calibration = fit_temperature(oof[selected], y, group, scope)
    scaler = CandidateTabularScaler().fit(x, group, scope)
    final_features = scaler.transform(x)
    pca = None
    if pca_max_dim is not None:
        pca = CandidateWeightedPCA(pca_max_dim).fit(final_features, group, scope)
        final_features = pca.transform(final_features)
    head = _fit_head(final_features, y, group, selected, seed)
    fit_scopes = dict(
        scope_hash=scope.hash, fit_groups=tuple(np.unique(group).tolist()), inner_folds=inner_scopes,
        final_transform_and_head_fit_groups=scaler.fit_groups_,
        calibration_fit_groups=calibration["fit_groups"],
        calibration_source="selected-C pooled inner OOF logits; training diagnostic",
        encoder_scope="not established by this frozen-feature readout module",
        classifier_weight_definition="1/(K*n_candidate_class); candidate total 1",
        transform_weight_definition="1/n_candidate; candidate total 1",
        pca_max_dim=pca_max_dim,
        loss_unit="bits per candidate-and-class-balanced trial",
    )
    return FittedProbe(scaler, pca, head, selected, calibration["temperature"], calibration,
                       fit_scopes, scores, input_shape, classes, int(seed))
