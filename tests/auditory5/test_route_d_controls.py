"""Synthetic D control contracts. Execute through Slurm, not a login node."""

import copy
import pickle
import unittest

import numpy as np
import pandas as pd

from auditory5.routes.route_d import make_features, grouped_ridge_predict
from auditory5.routes.route_d_controls import (NUISANCE_COLUMNS, all_trial_means, count_qc_covariates,
    fit_null_probe, fp32_invariance, sensitivity_features, summarize_clinical, validate_projection)


class FixedHead:
    def __init__(self, width):
        self.weight = np.zeros((2, width))
        self.weight[1, 0] = 1.

    def effective_linear_head(self):
        return self.weight.copy(), np.zeros(2)


def synthetic_core():
    rng = np.random.default_rng(13)
    train, test = list("abcdef"), ["heldout_a", "heldout_b"]
    ids = train + test
    groups = np.repeat(ids, 80)
    labels = np.tile(np.repeat([0, 1], 40), len(ids))
    post = rng.normal(size=(len(groups), 8))
    post[:, 1] += 4 * (2 * labels - 1)
    payload = dict(post=post, pre=rng.normal(size=post.shape), y=labels, groups=groups,
                   trial_ids=np.array(["synthetic_trial_" + str(i) for i in range(len(groups))]))
    clinical = pd.DataFrame(dict(age_months=rng.uniform(30, 80, len(ids)),
        log1p_device_duration_months=rng.uniform(1, 4, len(ids)),
        better_ear_4freq_source_units=rng.uniform(20, 80, len(ids)),
        MUSS_source_percentage=np.linspace(10, 90, len(ids))), index=ids)
    head = FixedHead(8)
    split, artifact = make_features(payload, head, clinical, train, test)
    return payload, head, split, artifact, clinical.MUSS_source_percentage, train, test


class DControlSummaryTests(unittest.TestCase):
    def test_all_trials_equal_budget_when_exactly_40_per_class(self):
        payload, _, original, artifact, target, train, test = synthetic_core()
        result = sensitivity_features(payload, artifact, train, test, target, all_trials=True)
        for part in ("train", "test"):
            for name in original[part]:
                np.testing.assert_allclose(result[part][name], original[part][name], atol=1e-10, rtol=1e-10)
        means = all_trial_means(payload["post"], payload["y"], payload["groups"], train + test)
        self.assertEqual(means.shape, (8, 2, 8))

    def test_all_trial_mean_uses_every_trial_and_preserves_support_floor(self):
        x = np.arange(100 * 3).reshape(100, 3)
        y = np.repeat([0, 1], 50)
        actual = all_trial_means(x, y, np.repeat("a", 100), ["a"])
        np.testing.assert_allclose(actual[0, 0], x[:50].mean(axis=0))
        np.testing.assert_allclose(actual[0, 1], x[50:].mean(axis=0))
        with self.assertRaisesRegex(ValueError, "D_ALL_TRIAL_SUPPORT"):
            all_trial_means(x[:89], y[:89], np.repeat("a", 89), ["a"])

    def test_saved_train_bases_are_not_refit_by_test_eeg_or_test_targets(self):
        payload, _, _, artifact, targets, train, test = synthetic_core()
        before = pickle.dumps(artifact)
        a = sensitivity_features(payload, artifact, train, test, targets, all_trials=True)
        changed = {key: value.copy() for key, value in payload.items()}
        heldout = np.isin(payload["groups"], test)
        changed["post"][heldout] *= -1000
        changed["pre"][heldout] += 1e6
        b = sensitivity_features(changed, artifact, train, test, targets, all_trials=True)
        for name in a["train"]:
            np.testing.assert_array_equal(a["train"][name], b["train"][name])
        altered_targets = targets.copy()
        altered_targets.loc[test] = 100 - altered_targets.loc[test]
        c = sensitivity_features(payload, artifact, train, test, altered_targets, all_trials=True)
        penalties = {"C": 1., "V": 10., "N": 10.}
        pa = grouped_ridge_predict(a["train"], a["test"], a["y_train"], penalties)
        pc = grouped_ridge_predict(c["train"], c["test"], c["y_train"], penalties)
        np.testing.assert_array_equal(pa, pc)
        self.assertEqual(before, pickle.dumps(artifact))

    def test_original_budget_features_are_reused_and_qc_only_augments_C(self):
        payload, _, original, artifact, targets, train, test = synthetic_core()
        nuisance = pd.DataFrame(np.arange(16.).reshape(8, 2), index=train + test, columns=NUISANCE_COLUMNS)
        result = sensitivity_features(payload, artifact, train, test, targets, all_trials=False, nuisance=nuisance)
        self.assertEqual(result["train"]["C"].shape, (len(train), 5))
        np.testing.assert_array_equal(result["train"]["C"][:, :3], original["train"]["C"])
        for name in original["train"]:
            if name != "C":
                np.testing.assert_array_equal(result["train"][name], original["train"][name])
        bad = nuisance.copy()
        bad["new_feature"] = 1
        with self.assertRaisesRegex(ValueError, "D_NUISANCE_SCHEMA"):
            sensitivity_features(payload, artifact, train, test, targets, all_trials=False, nuisance=bad)

    def test_projection_scope_rejects_test_candidates_in_pca_fit(self):
        _, _, _, artifact, _, train, test = synthetic_core()
        validate_projection(artifact, train, test)
        changed = copy.deepcopy(artifact)
        changed["null_pca"].fit_groups_ = tuple(train + [test[0]])
        with self.assertRaisesRegex(ValueError, "D_PROJECTION_LEAKAGE"):
            validate_projection(changed, train, test)
        with self.assertRaisesRegex(ValueError, "D_PROJECTION_SCOPE"):
            validate_projection(artifact, train[::-1], test)

    def test_count_qc_denominator_includes_rejected_targets_not_nonsound_rows(self):
        entries = []
        for i in range(95):
            target = i < 90
            entries.append(dict(trial_id=f"trial_{i}", split_group_id="a", event_kind="target" if target else "non_sound",
                event_literal=str(i % 2 + 1) if target else "boundary", accepted=i < 80, stimulus_local_id=i % 2))
        result = count_qc_covariates(pd.DataFrame(entries), ["a"])
        self.assertEqual(tuple(result.columns), NUISANCE_COLUMNS)
        self.assertAlmostEqual(result.iloc[0, 0], np.log1p(40))
        self.assertAlmostEqual(result.iloc[0, 1], 10 / 90)
        changed = pd.DataFrame(entries)
        changed.loc[0, "accepted"] = False
        with self.assertRaisesRegex(ValueError, "D_QC_SUPPORT"):
            count_qc_covariates(changed, ["a"])

    def test_paired_clinical_summary_keeps_negative_gains_and_rejects_missing_candidates(self):
        original, sensitivity = [], []
        for group in ("a", "b", "c"):
            for model, error in (("D1_C", 1.), ("D2_CV", 2.), ("D3_CVN", 3.)):
                row = dict(mode="L0", split_group_id=group, model=model, absolute_error=error)
                original.append(row)
                sensitivity.append(dict(row, variant="budget40_count_qc"))
        frame, reference = pd.DataFrame(sensitivity), pd.DataFrame(original)
        result = summarize_clinical(frame, reference, seed=4)
        main = next(row for row in result if row["comparison"] == "D2_minus_D3")
        self.assertEqual(main["estimate"], -1.)
        self.assertEqual(main["n_bootstrap"], 2000)
        with self.assertRaisesRegex(ValueError, "D_CONTROL_PAIRED_SUPPORT"):
            summarize_clinical(frame[frame.split_group_id.ne("c")], reference)


class DHeadControlTests(unittest.TestCase):
    def test_fp32_checks_actual_operations_and_saved_projector(self):
        payload, head, _, artifact, _, _, _ = synthetic_core()
        result = fp32_invariance(payload, head, artifact)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["dtype"], "float32")
        self.assertEqual(result["real_trials"], len(payload["post"]))
        self.assertEqual(result["synthetic_trials"], 128)
        self.assertLessEqual(result["real_max_abs_probability_difference"], 1e-6)
        changed = copy.deepcopy(artifact)
        changed["visible_basis"] = np.eye(8)[:, 1:2]
        with self.assertRaisesRegex(ValueError, "D_REFIT_PROJECTOR_MISMATCH"):
            fp32_invariance(payload, head, changed)

    def test_new_null_probe_can_decode_signal_invisible_to_original_head(self):
        payload, head, _, artifact, _, train, test = synthetic_core()
        fitted, predictions = fit_null_probe(payload, artifact, train, test)
        self.assertEqual(set(fitted.fit_scopes["fit_groups"]), set(train))
        self.assertFalse(fitted.fit_scopes["upstream_inner_refitted"])
        for fold in fitted.fit_scopes["inner_folds"]:
            self.assertFalse(set(fold["fit_groups"]) & set(fold["validation_groups"]))
            self.assertFalse(set(fold["fit_groups"]) & set(test))
        self.assertEqual(set(predictions.split_group_id), set(test))
        raw = predictions[predictions.probability_mode.eq("raw")]
        correct_probability = np.where(raw.stimulus_local_id.to_numpy() == 1, raw.p1, raw.p0)
        self.assertGreater(float(np.mean(correct_probability)), .8)
        # This diagnostic cannot change or erase the original fixed head.
        np.testing.assert_array_equal(head.weight[1], np.eye(8)[0])
        self.assertEqual(artifact["rank"], 1)


if __name__ == "__main__":
    unittest.main()
