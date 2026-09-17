"""Synthetic paired C contracts; execute only in the parent Slurm test gate."""

import pickle
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPClassifier

from auditory5.contracts import FitScope
from auditory5.routes.route_c import (MODEL_SPECS, VIEWS, align_branch_payloads, compose_view,
    fit_paired_readouts, paired_bootstrap, replacement_indices, screen, synthetic_controls,
    _c_logits, _fit_c_head, _candidate_losses, _prediction_rows, summarize_losses)


def metadata(groups=("a", "b"), each=32):
    n = each * len(groups)
    return pd.DataFrame(dict(trial_id=[f"synthetic_trial_{i}" for i in range(n)],
        record_id=np.repeat(groups, each), candidate_id=np.repeat(groups, each),
        split_group_id=np.repeat(groups, each), stimulus_local_id=np.tile(np.arange(each) % 2, len(groups)),
        time_block_id=np.tile(np.arange(each) // 4, len(groups))))


class CPairingTests(unittest.TestCase):
    def test_pairing_reorders_explicitly_and_rejects_unmatched_or_changed_labels(self):
        rows = metadata()
        x = np.arange(len(rows) * 2).reshape(len(rows), 2)
        order = np.arange(len(rows))[::-1]
        left = dict(rows=rows, post=x)
        right = dict(rows=rows.iloc[order].reset_index(drop=True), post=(x + 1)[order])
        a, b, aligned = align_branch_payloads(left, right)
        np.testing.assert_array_equal(a, x)
        np.testing.assert_array_equal(b, x + 1)
        pd.testing.assert_frame_equal(rows, aligned)
        changed = dict(rows=right["rows"].copy(), post=right["post"])
        changed["rows"].loc[0, "stimulus_local_id"] = 1 - changed["rows"].loc[0, "stimulus_local_id"]
        with self.assertRaisesRegex(ValueError, "C_PAIR_MISMATCH"):
            align_branch_payloads(left, changed)
        with self.assertRaisesRegex(ValueError, "C_PAIR_MISMATCH"):
            align_branch_payloads(left, dict(rows=rows.iloc[:-1], post=x[:-1]))

    def test_donors_stay_same_candidate_other_block_and_are_order_invariant(self):
        rows = metadata()
        # Identity components may contain different candidate IDs: no donor crosses them.
        rows.split_group_id = "shared_component"
        for opposite in (False, True):
            donor = replacement_indices(rows, opposite=opposite)
            self.assertTrue(np.all(donor >= 0))
            chosen = rows.iloc[donor].reset_index(drop=True)
            np.testing.assert_array_equal(rows.candidate_id, chosen.candidate_id)
            self.assertTrue(np.all(rows.time_block_id.to_numpy() != chosen.time_block_id.to_numpy()))
            expected = 1 - rows.stimulus_local_id if opposite else rows.stimulus_local_id
            np.testing.assert_array_equal(expected, chosen.stimulus_local_id)
            shuffled = rows.iloc[::-1].reset_index(drop=True)
            second = replacement_indices(shuffled, opposite=opposite)
            original = dict(zip(rows.trial_id, chosen.trial_id))
            reordered = dict(zip(shuffled.trial_id, shuffled.iloc[second].trial_id))
            self.assertEqual(original, reordered)

    def test_missing_donor_is_explicit_never_falls_back_to_another_candidate(self):
        rows = metadata()
        rows.loc[rows.candidate_id.eq("a"), "time_block_id"] = 0
        donor = replacement_indices(rows)
        self.assertTrue(np.all(donor[rows.candidate_id.eq("a")] == -1))
        self.assertTrue(np.all(donor[rows.candidate_id.eq("b")] >= 0))


class CReadoutTests(unittest.TestCase):
    def test_mlp_uses_exact_candidate_class_weights_and_stable_raw_logits(self):
        groups = np.array(["a"] * 8 + ["b"] * 24)
        y = np.arange(len(groups)) % 2
        x = np.c_[2 * y - 1., np.arange(len(y)) / len(y)]
        original = MLPClassifier.fit
        captured = []

        def fit_with_capture(head, features, labels, sample_weight):
            captured.append(sample_weight.copy())
            return original(head, features, labels, sample_weight=sample_weight)

        with patch.object(MLPClassifier, "fit", new=fit_with_capture):
            head = _fit_c_head(x, y, groups, .01, 32, 20260917)
        for group in ("a", "b"):
            for label in (0, 1):
                self.assertAlmostEqual(captured[0][(groups == group) & (y == label)].sum(), .5)
        np.testing.assert_allclose(softmax(_c_logits(head, x), axis=1), head.predict_proba(x), atol=1e-12)
        self.assertEqual(head.max_iter, 5000)
        self.assertEqual(head.max_fun, 250000)

    def test_nonconvergence_is_failure_without_alternate_head(self):
        x, y, groups = np.arange(16.).reshape(8, 2), np.arange(8) % 2, np.repeat(["a", "b"], 4)
        with patch.object(MLPClassifier, "fit", side_effect=ConvergenceWarning("synthetic nonconvergence")):
            with self.assertRaisesRegex(ValueError, "C_HEAD_CONVERGENCE_FAILURE"):
                _fit_c_head(x, y, groups, .01, 32, 1)

    def test_missing_candidate_class_fails_before_any_fit(self):
        groups = np.repeat(["a", "b", "c"], 8)
        y = np.arange(len(groups)) % 2
        y[:8] = 0
        with self.assertRaisesRegex(ValueError, "CANDIDATE_CLASS_SUPPORT"):
            fit_paired_readouts(np.ones((24, 2)), np.ones((24, 2)), y, groups, FitScope(("a", "b", "c")))

    def test_whole_matrix_scopes_inference_isolation_and_fixed_head_controls(self):
        rows = metadata(("a", "b", "c", "d", "e", "f"), 16)
        y, groups = rows.stimulus_local_id.to_numpy(), rows.split_group_id.to_numpy()
        rng = np.random.default_rng(14)
        left = np.c_[2 * y - 1., rng.normal(size=len(y))]
        right = np.c_[rng.normal(size=len(y)), 2 * y - 1.]
        scope = FitScope(tuple(np.unique(groups)), test_groups=("heldout",))
        fitted = fit_paired_readouts(left, right, y, groups, scope)
        self.assertEqual(set(fitted), {(f, v) for f, v, _ in MODEL_SPECS})
        for head in fitted.values():
            self.assertEqual(set(head.evidence["fit_groups"]), set(groups))
            for fold in head.evidence["inner_folds"]:
                self.assertFalse(set(fold["fit_groups"]) & set(fold["validation_groups"]))
                self.assertNotIn("heldout", fold["fit_groups"])
            self.assertGreaterEqual(head.temperature, .25)
            self.assertLessEqual(head.temperature, 4)
        test_left, test_right = rng.normal(size=(8, 2)), rng.normal(size=(8, 2))
        single = fitted["linear", "C_L"]
        state = pickle.dumps(single)
        a = single.predict(test_left, test_right)
        b = single.predict(test_left, test_right + 1e6)
        np.testing.assert_array_equal(a["raw"], b["raw"])
        self.assertEqual(state, pickle.dumps(single))
        duplicate = fitted["mlp32", "C_LL"]
        before = pickle.dumps(duplicate)
        donor = np.roll(np.arange(8), 1)
        p = duplicate.predict(test_left, test_right, intervention="same_class_first", donor_indices=donor)
        scaled = duplicate.left_scaler.transform(test_left)
        expected = softmax(_c_logits(duplicate.head, np.c_[scaled[donor], scaled]), axis=1)
        np.testing.assert_allclose(p["raw"], expected, atol=1e-12)
        zero = duplicate.predict(test_left, test_right, intervention="zero_second")
        expected = softmax(_c_logits(duplicate.head, np.c_[scaled, np.zeros_like(scaled)]), axis=1)
        np.testing.assert_allclose(zero["raw"], expected, atol=1e-12)
        self.assertEqual(before, pickle.dumps(duplicate))

    def test_production_heads_cover_copy_left_only_and_xor_worlds(self):
        result = synthetic_controls()
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(set(result["worlds"]), {"copied", "left_only", "xor"})


class CStatisticsTests(unittest.TestCase):
    def test_bootstrap_reselects_best_mean_branch_and_capacity_each_draw(self):
        table = pd.DataFrame(dict(C_L=[0., 2.], C_R=[2., 0.], C_LR=[.4, .4],
                                  C_LL=[.1, 2.1], C_RR=[2.1, .1], C_L64=[.2, 2.2], C_R64=[2.2, .2]), index=["a", "b"])
        summary = {row["statistic"]: row for row in paired_bootstrap(table, seed=55)}
        self.assertAlmostEqual(summary["T_C"]["estimate"], .6)
        # Mean per-person minimum would give -.4 and is expressly forbidden.
        self.assertAlmostEqual(summary["T_C"]["ci_lower"], -.4)
        self.assertAlmostEqual(summary["T_C"]["ci_upper"], .6)
        self.assertAlmostEqual(summary["capacity_margin"]["estimate"], .7)
        rng = np.random.default_rng(55)
        draws = rng.integers(0, 2, (2000, 2))
        means = table.to_numpy()[draws].mean(axis=1)
        expected = np.minimum(means[:, 0], means[:, 1]) - means[:, 2]
        self.assertAlmostEqual(summary["T_C"]["ci_lower"], np.quantile(expected, .025))
        bad = table.copy()
        bad.loc["a", "C_RR"] = np.nan
        with self.assertRaisesRegex(ValueError, "C_PAIRED_SUPPORT"):
            paired_bootstrap(bad)

    def test_candidate_ce_class_balance_and_complete_family_aggregation(self):
        rows = metadata()
        parts = []
        for family, view, _ in MODEL_SPECS:
            probability = .8 if view == "C_LR" else .6
            p1 = np.where(rows.stimulus_local_id.to_numpy() == 1, probability, 1 - probability)
            parts.append(_prediction_rows(rows, {"raw": np.c_[1 - p1, p1], "calibrated": np.c_[1 - p1, p1]},
                mode="L0", fold=0, family=family, view=view, intervention="none"))
        frame = pd.DataFrame(_candidate_losses(pd.concat(parts, ignore_index=True)))
        gains, interventions = summarize_losses(frame)
        self.assertFalse(interventions)
        t = [v for v in gains if v["statistic"] == "T_C"]
        self.assertEqual(len(t), 4)
        for result in t:
            self.assertAlmostEqual(result["estimate"], np.log2(.8 / .6))
        self.assertEqual(screen(gains, ["pending learned modes"])["status"], "NEED_CONTROLS")

    def test_screen_requires_controls_primary_support_and_capacity_ci(self):
        gains = []
        for mode in ("R_SIM", "R_SUP"):
            for family in ("linear", "mlp32"):
                for calibration in ("raw", "calibrated"):
                    for statistic in ("T_C", "J_joint", "capacity_margin", "duplicate_margin"):
                        gains.append(dict(representation=mode, family=family, probability_mode=calibration,
                                          statistic=statistic, estimate=.1, ci_lower=.02, n_candidates=30))
        self.assertEqual(screen(gains, ["missing donor"])["status"], "NEED_CONTROLS")
        self.assertEqual(screen(gains, [])["status"], "POSITIVE_SCREEN")
        missing_raw = [r for r in gains if r["probability_mode"] != "raw"]
        self.assertEqual(screen(missing_raw, [])["status"], "NEED_CONTROLS")
        for row in gains:
            if row["statistic"] == "capacity_margin":
                row["ci_lower"] = -.01
        self.assertEqual(screen(gains, [])["status"], "MIXED_SCREEN: capacity_or_calibration")


if __name__ == "__main__":
    unittest.main()
