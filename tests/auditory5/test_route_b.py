"""Synthetic B schema, support, scope and paired-readout tests; Slurm only."""

import pickle
import unittest

import numpy as np
import pandas as pd

from auditory5.contracts import FitScope, validate_history_context
from auditory5.routes.route_b import (CONTEXT_COLUMNS, CommonSupport, ContextFeatures,
    candidate_support_mask, context_frame, fit_history_readouts, history_eligible,
    select_common_support, _summaries)


def rows_for_groups(groups, each=120):
    rng = np.random.default_rng(41)
    n = len(groups) * each
    return pd.DataFrame(dict(
        split_group_id=np.repeat(groups, each), candidate_id=np.repeat(groups, each),
        trial_id=[f"synthetic_trial_{i}" for i in range(n)], record_id=np.repeat(groups, each),
        previous_gap_s=rng.choice([.6, .7, .8], size=n),
        segment_position_fraction=rng.choice([1 / 6, .5, 5 / 6], size=n),
        history_target=np.tile(np.arange(each) % 2, len(groups)),
        previous_run_length=np.tile(np.where(np.arange(each) % 2, 3, 1), len(groups)),
        time_block_id=np.tile(np.arange(each) % 12, len(groups)),
        event_literal="1", previous_code="1", accepted=True,
    ))


class BSupportTests(unittest.TestCase):
    def test_context_schema_excludes_history_ids_and_quality(self):
        rows = rows_for_groups(["a"])
        first = context_frame(rows)
        changed = rows.copy()
        changed["history_target"] = 1 - changed.history_target
        changed["previous_run_length"] = 999
        changed["split_group_id"] = "different_identity"
        changed["all_ptp_uv"] = 1e9
        pd.testing.assert_frame_equal(first, context_frame(changed))
        self.assertEqual(tuple(first.columns), CONTEXT_COLUMNS)
        with self.assertRaises(ValueError):
            validate_history_context([*CONTEXT_COLUMNS, "history_target"])

    def test_test_context_and_history_changes_cannot_change_training_support(self):
        train, test = rows_for_groups(["a", "b", "c"]), rows_for_groups(["heldout"])
        scope = FitScope(("a", "b", "c"), test_groups=("heldout",))
        a, _, gate = select_common_support(train, test, scope)
        changed = test.copy()
        changed.previous_gap_s *= 100
        changed.history_target = 1 - changed.history_target
        b, test_mask, second = select_common_support(train, changed, scope)
        np.testing.assert_array_equal(a, b)
        self.assertEqual(gate.to_dict(), second.to_dict())
        self.assertFalse(test_mask.any())
        with self.assertRaisesRegex(ValueError, "LEAKAGE"):
            CommonSupport.fit(test, scope)

    def test_single_history_stratum_is_never_extrapolated(self):
        train = rows_for_groups(["a", "b", "c"])
        train.loc[train.segment_position_fraction < 1 / 3, "history_target"] = 0
        gate = CommonSupport.fit(train, FitScope(("a", "b", "c")))
        test = rows_for_groups(["heldout"])
        test.segment_position_fraction = 1 / 6
        self.assertFalse(gate.mask(test).any())
        self.assertTrue(any(not entry["supported"] for entry in gate.support_counts))

    def test_candidate_requires_both_counts_and_original_block_support(self):
        rows = rows_for_groups(["a"], each=40)
        rows.time_block_id = 0
        self.assertFalse(candidate_support_mask(rows).any())
        rows.time_block_id = np.arange(40) // 10
        self.assertTrue(candidate_support_mask(rows).all())
        rows.loc[0, "history_target"] = 1
        self.assertFalse(candidate_support_mask(rows).any())

    def test_history_target_remains_usable_when_previous_eeg_was_rejected(self):
        rows = rows_for_groups(["a"])
        rows["previous_eeg_accepted"] = False
        before = rows.history_target.copy()
        self.assertTrue(history_eligible(rows).all())
        pd.testing.assert_series_equal(before, rows.history_target)
        rows.loc[0, "previous_code"] = "2"
        self.assertFalse(history_eligible(rows)[0])

    def test_previous_subset_keeps_main_gap_boundaries_and_prunes_training_only(self):
        train, test = rows_for_groups(["a", "b", "c"]), rows_for_groups(["heldout"])
        scope = FitScope(("a", "b", "c"), test_groups=("heldout",))
        _, _, gate = select_common_support(train, test, scope)
        subset = train[train.segment_position_fraction > 1 / 3]
        _, _, filtered = select_common_support(subset, test, scope, frozen_gate=gate)
        np.testing.assert_array_equal(gate.gap_edges, filtered.gap_edges)
        self.assertTrue(set(filtered.strata) <= set(gate.strata))


class BReadoutTests(unittest.TestCase):
    def test_spline_is_training_only_with_constant_feature_handling(self):
        train = rows_for_groups(["a", "b", "c"])
        train.previous_gap_s = .7
        context = ContextFeatures().fit(train, FitScope(("a", "b", "c"), test_groups=("heldout",)))
        self.assertFalse(context.active_[0])
        snapshot = pickle.dumps(context)
        test = rows_for_groups(["heldout"])
        test.previous_gap_s = 20
        values = context.transform(test)
        self.assertTrue(np.isfinite(values).all())
        self.assertEqual(snapshot, pickle.dumps(context))

    def test_inner_models_preserve_context_outside_eeg_pca_and_exclude_test_labels(self):
        train = rows_for_groups(["a", "b", "c", "d", "e", "f"])
        scope = FitScope(tuple(train.split_group_id.unique()), test_groups=("heldout",))
        eeg = np.random.default_rng(4).normal(size=(len(train), 8))
        models = fit_history_readouts(train, {"B0_context_spline": None, "B2_post": eeg}, scope)
        post = models["B2_post"]
        self.assertEqual(post.eeg_pca.n_features_in_, 8)
        self.assertGreater(post.fit_scope["context_dimension"], 4)
        self.assertFalse(post.fit_scope["context_reduced_by_PCA"])
        self.assertEqual(post.head.coef_.shape[1], post.fit_scope["context_dimension"] + post.eeg_pca.n_components_)
        for fold in post.fit_scope["inner_folds"]:
            self.assertFalse(set(fold["fit_groups"]) & set(fold["validation_groups"]))
            self.assertNotIn("heldout", fold["fit_groups"])
        test = rows_for_groups(["heldout"])
        test_eeg = np.random.default_rng(9).normal(size=(len(test), 8))
        first = post.predict(test, test_eeg)
        state = pickle.dumps(post)
        test.history_target = 1 - test.history_target
        second = post.predict(test, test_eeg)
        for mode in ("raw", "calibrated"):
            np.testing.assert_array_equal(first[mode], second[mode])
        self.assertEqual(state, pickle.dumps(post))

    def test_paired_summary_compares_only_same_analysis_set(self):
        rows = []
        for analysis_set, accuracy in (("all", .8), ("previous_response_available", .7)):
            for group in ("a", "b"):
                for label in (0, 1):
                    for model in ("B0_context_spline", "B2_post", "B1_pre", "B3_pre_post"):
                        p = .5 if model in ("B0_context_spline", "B1_pre") else accuracy
                        rows.append(dict(analysis_set=analysis_set, probability_mode="raw", model=model,
                                         split_group_id=group, trial_id=f"{group}_{label}", history_target=label,
                                         p0=p if label == 0 else 1 - p, p1=p if label == 1 else 1 - p))
        _, comparisons = _summaries(pd.DataFrame(rows), 31)
        self.assertEqual(len(comparisons), 4)
        for row in comparisons:
            p = .8 if row["analysis_set"] == "all" else .7
            self.assertAlmostEqual(row["estimate"], 1 + np.log2(p))
            self.assertEqual(row["n_candidates"], 2)
            self.assertEqual(row["n_bootstrap"], 2000)


if __name__ == "__main__":
    unittest.main()
