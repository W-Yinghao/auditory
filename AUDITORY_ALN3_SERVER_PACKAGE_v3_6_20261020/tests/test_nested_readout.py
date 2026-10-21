"""Seven targeted checks of the CPU reference, using synthetic data only."""
import inspect
import itertools
import json
from pathlib import Path
import sys
import unittest

import numpy as np
from scipy.special import expit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aln36_readout import build_time_basis, evaluate_readout, fit_nested_readout, risk_contrasts


def fit(family, x, y, a0, *, offset=None, history=None, source_x=None, penalty=1.0):
    history = np.ones((len(x), 1)) if history is None else history
    offset = np.zeros(len(x)) if offset is None else offset
    source_x = x if source_x is None else source_x
    source_history = history if source_x is x else np.ones((len(source_x), history.shape[1]))
    basis = build_time_basis(a0=a0, source_scores=source_x, source_history_design=source_history)
    return fit_nested_readout(family=family, support_offset=offset, support_history=history,
                             support_scores=x, support_y=y, a0=a0, time_basis=basis,
                             ridge_history=penalty, ridge_scale=penalty, ridge_time=penalty)


class NestedReadoutTests(unittest.TestCase):
    def test_zero_shared_signal_and_source_rank_degeneracy_are_explicit(self):
        rng = np.random.default_rng(13)
        x = rng.normal(size=(200, 3))
        model = fit("bernoulli", x, np.tile([0., 1.], 100), np.zeros(3))
        self.assertEqual(model.time_basis.status, "zero_shared_direction")
        predictions = model.predict(offset=np.zeros(200), history_design=np.ones((200, 1)), scores=x)
        for state in predictions:
            np.testing.assert_allclose(predictions[state], .5, atol=1e-9)
        self.assertEqual(model.states["ET"].receipt["identical_to"], "EC")
        one = rng.normal(size=100)
        reduced = build_time_basis(a0=[1., 0., 0.], source_scores=np.column_stack([one, 2*one, -one]))
        self.assertEqual(reduced.rank, 0)
        self.assertEqual(reduced.status, "no_independent_time_direction")

    def test_pure_base_rate_shift_is_not_a_temporal_rotation(self):
        grid = np.asarray(list(itertools.product((-1., 1.), repeat=3)))
        x = np.repeat(grid, 100, axis=0)
        y = np.tile(np.r_[np.ones(80), np.zeros(20)], len(grid))
        offset = np.full(len(x), np.log(.2/.8))
        model = fit("bernoulli", x, y, np.array([1., 0., 0.]), offset=offset)
        out = evaluate_readout(fit=model, query_offset=offset, query_history=np.ones((len(x), 1)),
                               query_scores=x, query_y=y)
        self.assertGreater(out["estimands"]["history_calibration_gain"], .5)
        self.assertLess(abs(out["estimands"]["time_increment"]), 1e-8)
        np.testing.assert_allclose(model.states["ET"].gamma, 0., atol=1e-7)

    def test_true_temporal_rotation_recovers_on_independent_queries_in_both_families(self):
        rng = np.random.default_rng(71)
        source = rng.normal(size=(1000, 5))
        x, query = rng.normal(size=(500, 5)), rng.normal(size=(1000, 5))
        y = .4 + .1*x[:, 0] + 1.2*x[:, 1] + rng.normal(scale=.05, size=len(x))
        truth = .4 + .1*query[:, 0] + 1.2*query[:, 1]
        model = fit("gaussian", x, y, np.array([1., 0., 0., 0., 0.]), source_x=source)
        self.assertEqual(model.time_basis.rank, 4)
        np.testing.assert_allclose(model.a0 @ model.time_basis.matrix, 0., atol=1e-12)
        out = evaluate_readout(fit=model, query_offset=np.zeros(len(query)),
                               query_history=np.ones((len(query), 1)), query_scores=query, query_y=truth)
        self.assertGreater(out["estimands"]["time_increment"], 1.)
        self.assertLess(out["risk"]["ET"], .01)
        source_binary = rng.normal(size=(1000, 3))
        binary_x, binary_q = rng.normal(size=(700, 3)), rng.normal(size=(3000, 3))
        binary_y = rng.binomial(1, expit(.3 + .1*binary_x[:, 0] + 1.8*binary_x[:, 1]))
        binary_q_y = rng.binomial(1, expit(.3 + .1*binary_q[:, 0] + 1.8*binary_q[:, 1]))
        binary_model = fit("bernoulli", binary_x, binary_y, np.array([1., 0., 0.]), source_x=source_binary)
        binary_out = evaluate_readout(fit=binary_model, query_offset=np.zeros(len(binary_q)),
                                     query_history=np.ones((len(binary_q), 1)),
                                     query_scores=binary_q, query_y=binary_q_y)
        self.assertEqual(binary_model.time_basis.rank, 2)
        self.assertGreater(binary_out["estimands"]["time_increment"], .12)

    def test_nested_models_positive_scale_bound_and_identity_initialization(self):
        grid = np.asarray(list(itertools.product((-1., 1.), repeat=3)))
        x = np.repeat(grid, 100, axis=0)
        y = np.concatenate([np.r_[np.ones(90 if row[0] < 0 else 10),
                                  np.zeros(10 if row[0] < 0 else 90)] for row in grid])
        model = fit("bernoulli", x, y, np.array([1., 0., 0.]))
        self.assertGreaterEqual(model.states["EC"].beta, 0.)
        self.assertGreaterEqual(model.states["ET"].beta, 0.)
        self.assertLess(model.states["EC"].beta, 1e-7)
        self.assertLessEqual(model.states["ET"].receipt["objective"], model.states["EC"].receipt["objective"] + 1e-7)
        self.assertEqual(model.states["HP"].receipt["identity_initialization"], [0.])
        self.assertEqual(model.states["EC"].receipt["identity_initialization"], [0., 1.])
        self.assertEqual(model.states["ET"].receipt["identity_initialization"], [0., 1., 0., 0.])
        predictions = model.predict_linear(offset=np.full(len(x), .3), history_design=np.ones((len(x), 1)), scores=x)
        np.testing.assert_allclose(predictions["H0"], .3)
        np.testing.assert_allclose(predictions["E0"], .3 + x[:, 0])

    def test_one_class_support_is_finite_and_query_evaluation_does_not_refit(self):
        rng = np.random.default_rng(91)
        x = rng.normal(size=(80, 3))
        model = fit("bernoulli", x, np.ones(len(x)), np.array([1., .2, -.1]))
        self.assertEqual(model.support_class_counts, {"0": 0, "1": 80})
        before = json.dumps(model.as_dict(), sort_keys=True)
        query = rng.normal(size=(100, 3))
        for labels in (np.zeros(100), np.ones(100)):
            out = evaluate_readout(fit=model, query_offset=np.zeros(100), query_history=np.ones((100, 1)),
                                   query_scores=query, query_y=labels)
            self.assertTrue(all(np.isfinite(v) for v in out["risk"].values()))
        self.assertEqual(before, json.dumps(model.as_dict(), sort_keys=True))

    def test_fit_has_no_query_label_api_and_contrasts_use_direct_paired_algebra(self):
        self.assertFalse(any("query" in k for k in inspect.signature(fit_nested_readout).parameters))
        with self.assertRaises(TypeError):
            fit_nested_readout(query_y=np.array([0, 1]))
        risk = {"H0": 1.0, "E0": .8, "HP": .85, "EC": .62, "ET": .58}
        out = risk_contrasts(risk)
        self.assertAlmostEqual(out["time_increment"], .04)
        self.assertAlmostEqual(out["double_difference"], (.8-.58)-(1.-.85))
        self.assertAlmostEqual(out["double_difference"], out["personal_EEG_gain"]-out["shared_EEG_gain"])
        self.assertAlmostEqual(out["time_increment"], out["double_difference"]-out["calibration_double_difference"])

    def test_near_collinear_time_score_cannot_cheaply_replace_global_gain(self):
        rng = np.random.default_rng(20261020)

        def orthogonal_bank(n):
            raw = rng.normal(size=(n, 5))
            q, _ = np.linalg.qr(raw - raw.mean(0), mode="reduced")
            q *= np.sqrt(n)
            x = q.copy()
            # The second score almost duplicates the shared direction. Its
            # tiny independent residual is real, but contains no target signal.
            x[:, 1] = (q[:, 0] + .01*q[:, 1]) / np.sqrt(1.0001)
            return x, q[:, 0]

        source, _ = orthogonal_bank(512)
        support, support_y = orthogonal_bank(256)
        query, query_y = orthogonal_bank(384)
        a0 = np.array([.01, 0., 0., 0., 0.])
        model = fit("gaussian", support, support_y, a0, source_x=source, penalty=1.)
        self.assertEqual(model.time_basis.rank, 4)
        z_source = model.time_basis.project(source, np.ones((len(source), 1)))
        nuisance = np.column_stack((np.ones(len(source)), source @ a0))
        np.testing.assert_allclose(nuisance.T @ z_source / len(source), 0., atol=1e-10)
        np.testing.assert_allclose(z_source.T @ z_source / len(source), np.eye(4), atol=1e-10)
        out = evaluate_readout(fit=model, query_offset=np.zeros(len(query)),
                               query_history=np.ones((len(query), 1)), query_scores=query, query_y=query_y)
        self.assertGreater(out["risk"]["EC"], .8)
        self.assertLess(abs(out["estimands"]["time_increment"]), 1e-10)
        # Without the actual residual transform, the raw near-duplicate score
        # with coefficient near 1 would bypass beta ~= 100's ridge cost.
        naive_raw_time_risk = np.mean((query[:, 1] - query_y) ** 2)
        self.assertLess(naive_raw_time_risk, .001)
        np.testing.assert_allclose(model.states["ET"].gamma, 0., atol=1e-9)


if __name__ == "__main__":
    unittest.main()
