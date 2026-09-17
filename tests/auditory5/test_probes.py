"""Synthetic frozen-feature readout contracts; run only through Slurm."""

import hashlib
import math
import pickle
import unittest
from unittest.mock import patch

import numpy as np
from scipy.special import softmax

from auditory5.contracts import FitScope
from auditory5.probes import (
    C_GRID, CandidateTabularScaler, CandidateWeightedPCA, bin_20ms,
    candidate_class_weights, candidate_weights, fit_probe, fit_temperature,
    weighted_log_loss_nats,
)


def synthetic_features(n_features=6, n_classes=2):
    rng = np.random.default_rng(130)
    groups = np.repeat([f"g{i}" for i in range(6)], n_classes * 6)
    y = np.tile(np.repeat(np.arange(n_classes), 6), 6)
    x = rng.normal(size=(len(y), n_features))
    x[:, 0] += y * .7
    scope = FitScope(tuple(np.unique(groups)), test_groups=("heldout",))
    return x, y, groups, scope


class ProbeWeightTests(unittest.TestCase):
    def test_candidate_and_class_total_weights_are_exact(self):
        group = np.array(["a"] * 4 + ["b"] * 12)
        y = np.array([0, 0, 0, 1] + [0] * 4 + [1] * 8)
        weight = candidate_class_weights(y, group)
        for candidate in ("a", "b"):
            self.assertAlmostEqual(weight[group == candidate].sum(), 1.0)
            for label in (0, 1):
                self.assertAlmostEqual(weight[(group == candidate) & (y == label)].sum(), .5)
        self.assertAlmostEqual(weight.sum(), 2.0)
        self.assertAlmostEqual(candidate_weights(group)[group == "a"].sum(), 1.0)

    def test_candidate_scaler_is_not_trial_or_class_weighted(self):
        x = np.r_[np.zeros(2), np.full(10, 10.0)][:, None]
        groups = np.array(["a"] * 2 + ["b"] * 10)
        scaler = CandidateTabularScaler().fit(x, groups, FitScope(("a", "b")))
        np.testing.assert_allclose(scaler.mean_, [5.0], atol=1e-14)
        np.testing.assert_allclose(scaler.scale_, [5.0], atol=1e-14)
        replicated = np.r_[np.zeros(2), np.full(100, 10.0)][:, None]
        other = CandidateTabularScaler().fit(replicated, ["a"] * 2 + ["b"] * 100,
                                             FitScope(("a", "b")))
        np.testing.assert_allclose(scaler.mean_, other.mean_, atol=1e-14)
        np.testing.assert_allclose(scaler.scale_, other.scale_, atol=1e-14)

    def test_weighted_pca_matches_independent_population_covariance(self):
        x = np.array([[0., 1., 4.], [1., 4., 2.], [3., 5., 8.],
                      [2., 0., 1.], [2., 3., 2.], [1., 8., 0.]])
        groups = np.array(["a", "a", "b", "b", "b", "b"])
        fitted = CandidateWeightedPCA().fit(x, groups, FitScope(("a", "b")))
        center = (x[:2].mean(axis=0) + x[2:].mean(axis=0)) / 2
        covariance = ((x[:2] - center).T @ (x[:2] - center) / 2
                      + (x[2:] - center).T @ (x[2:] - center) / 4) / 2
        reconstructed = fitted.components_.T @ np.diag(fitted.explained_variance_) @ fitted.components_
        np.testing.assert_allclose(fitted.mean_, center, atol=1e-14)
        np.testing.assert_allclose(reconstructed, covariance, atol=1e-12)
        self.assertEqual(fitted.n_components_, 3)

    def test_scaler_and_pca_reject_heldout_fit_groups(self):
        x = np.ones((4, 2))
        group = ["a", "a", "heldout", "heldout"]
        scope = FitScope(("a",), test_groups=("heldout",))
        for transform in (CandidateTabularScaler(), CandidateWeightedPCA()):
            with self.assertRaisesRegex(ValueError, "LEAKAGE"):
                transform.fit(x, group, scope)

    def test_l0_bins_preserve_channel_order_and_reject_implicit_cropping(self):
        x = np.arange(20.).reshape(1, 2, 10)
        np.testing.assert_array_equal(bin_20ms(x), [[2., 7., 12., 17.]])
        with self.assertRaisesRegex(ValueError, "L0_SHAPE"):
            bin_20ms(np.zeros((1, 2, 11)))
        with self.assertRaisesRegex(ValueError, "250HZ"):
            bin_20ms(x, processed_fs=500)


class ProbeFitTests(unittest.TestCase):
    def test_test_eeg_and_label_mutation_cannot_change_fit_or_calibration(self):
        x, y, groups, scope = synthetic_features()
        first = fit_probe(x, y, groups, scope)
        before = hashlib.sha256(pickle.dumps(first)).hexdigest()
        heldout_x = np.ones((8, x.shape[1]))
        heldout_y = np.arange(8) % 2
        original = first.predict(heldout_x)
        heldout_x *= 1e4
        heldout_y[:] = 1 - heldout_y
        mutated = first.predict(heldout_x)
        self.assertEqual(before, hashlib.sha256(pickle.dumps(first)).hexdigest())
        second = fit_probe(x.copy(), y.copy(), groups.copy(), scope)
        self.assertEqual(first.selected_C, second.selected_C)
        self.assertEqual(first.temperature, second.temperature)
        np.testing.assert_array_equal(first.head.coef_, second.head.coef_)
        self.assertFalse(np.array_equal(original["raw"], mutated["raw"]))
        with self.assertRaises(TypeError):
            first.predict(heldout_x, y_test=heldout_y)

    def test_actual_inner_transform_fits_are_candidate_disjoint(self):
        x, y, groups, scope = synthetic_features()
        fits = []
        original_fit = CandidateTabularScaler.fit

        def tracked_fit(instance, values, fit_groups, fit_scope):
            self.assertFalse(set(fit_groups) & set(fit_scope.validation_groups))
            self.assertFalse(set(fit_groups) & set(fit_scope.test_groups))
            fits.append(tuple(np.unique(fit_groups)))
            return original_fit(instance, values, fit_groups, fit_scope)

        with patch.object(CandidateTabularScaler, "fit", tracked_fit):
            fitted = fit_probe(x, y, groups, scope)
        self.assertEqual(len(fits), 4)
        for item, actual in zip(fitted.fit_scopes["inner_folds"], fits[:-1]):
            self.assertEqual(item["fit_groups"], actual)
            self.assertFalse(set(actual) & set(item["validation_groups"]))
            self.assertNotIn("heldout", actual)
        self.assertEqual(fitted.calibration["fit_groups"], tuple(np.unique(groups)))
        self.assertIn("not established", fitted.fit_scopes["encoder_scope"])

    def test_binary_effective_head_composes_scaler_and_non_square_pca(self):
        x, y, groups, scope = synthetic_features(n_features=64)
        for dimension in (None, 7, 32):
            fitted = fit_probe(x, y, groups, scope, pca_max_dim=dimension)
            test = np.random.default_rng(9).normal(size=(11, 64)) * 3 + 5
            W, b = fitted.effective_linear_head()
            self.assertEqual(W.shape, (2, 64))
            self.assertEqual(b.shape, (2,))
            predicted = fitted.predict(test)
            np.testing.assert_allclose(softmax(test @ W.T + b, axis=1), predicted["raw"], atol=1e-10)
            Wc, bc = fitted.effective_linear_head(calibrated=True)
            np.testing.assert_allclose(softmax(test @ Wc.T + bc, axis=1),
                                       predicted["calibrated"], atol=1e-10)
            np.testing.assert_allclose(Wc, W / fitted.temperature, atol=1e-14)
            self.assertEqual(fitted.pca is None, dimension is None)

    def test_multiclass_effective_head_and_probability_columns(self):
        x, y, groups, scope = synthetic_features(n_features=12, n_classes=3)
        fitted = fit_probe(x, y, groups, scope, pca_max_dim=5)
        W, b = fitted.effective_linear_head()
        self.assertEqual(W.shape, (3, 12))
        np.testing.assert_allclose(softmax(x @ W.T + b, axis=1), fitted.predict(x)["raw"], atol=1e-10)
        np.testing.assert_array_equal(fitted.classes, [0, 1, 2])

    def test_binned_effective_head_declares_its_feature_coordinates(self):
        x, y, groups, scope = synthetic_features(n_features=20)
        raw_epochs = x.reshape(len(x), 2, 10)
        fitted = fit_probe(raw_epochs, y, groups, scope, pca_max_dim=None)
        W, b = fitted.effective_linear_head()
        self.assertEqual(W.shape, (2, 4))
        self.assertIn("binned", fitted.effective_feature_space)
        np.testing.assert_allclose(softmax(bin_20ms(raw_epochs) @ W.T + b, axis=1),
                                   fitted.predict(raw_epochs)["raw"], atol=1e-10)

    def test_empty_missing_class_and_inner_missing_class_fail_explicitly(self):
        x, y, groups, scope = synthetic_features()
        with self.assertRaisesRegex(ValueError, "FEATURE_SUPPORT"):
            fit_probe(x[:0], y[:0], groups[:0], scope)
        with self.assertRaisesRegex(ValueError, "CLASS_SUPPORT"):
            fit_probe(x, np.zeros_like(y), groups, scope)
        with self.assertRaisesRegex(ValueError, "CANDIDATE_CLASS_SUPPORT"):
            candidate_class_weights([0, 0, 1, 1], ["a", "a", "b", "b"])
        sparse_x = np.arange(16.).reshape(8, 2)
        sparse_y = np.repeat([0, 0, 1, 1], 2)
        sparse_groups = np.repeat(["a", "b", "c", "d"], 2)
        with self.assertRaisesRegex(ValueError, "INNER_CLASS_SUPPORT"):
            fit_probe(sparse_x, sparse_y, sparse_groups, FitScope(("a", "b", "c", "d")))

    def test_constant_features_return_uniform_not_high_information(self):
        x, y, groups, scope = synthetic_features()
        fitted = fit_probe(np.ones_like(x), y, groups, scope)
        probabilities = fitted.predict(np.ones((4, x.shape[1])))
        np.testing.assert_allclose(probabilities["raw"], .5, atol=1e-10)
        self.assertEqual(fitted.temperature, 1.0)
        self.assertEqual(fitted.pca.rank_, 0)
        self.assertEqual(fitted.selected_C, C_GRID[0])


class TemperatureTests(unittest.TestCase):
    def test_natural_log_fit_reports_bits_and_keeps_bounds(self):
        y = np.array([0, 1, 0, 1])
        groups = np.array(["a", "a", "b", "b"])
        scope = FitScope(("a", "b"), test_groups=("heldout",))
        scores = np.zeros((4, 2))
        weights = candidate_class_weights(y, groups)
        self.assertAlmostEqual(weighted_log_loss_nats(scores, y, weights), math.log(2))
        calibration = fit_temperature(scores, y, groups, scope)
        self.assertEqual(calibration["temperature"], 1.0)
        self.assertEqual(calibration["objective_unit"], "nats")
        self.assertAlmostEqual(calibration["inner_oof_ce_bits"], 1.0)
        contradictory = np.tile([10., -10.], (4, 1))
        fitted = fit_temperature(contradictory, y, groups, scope)
        self.assertEqual(fitted["temperature"], 4.0)
        self.assertLessEqual(fitted["inner_oof_ce_bits"], fitted["raw_inner_oof_ce_bits"])

    def test_temperature_rejects_heldout_candidate_logits(self):
        with self.assertRaisesRegex(ValueError, "LEAKAGE"):
            fit_temperature(np.zeros((4, 2)), [0, 1, 0, 1], ["a", "a", "heldout", "heldout"],
                            FitScope(("a",), test_groups=("heldout",)))


if __name__ == "__main__":
    unittest.main()
