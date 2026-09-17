"""Learned B ingestion/scope tests; run through the parent Slurm gate only."""

import copy
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from auditory5.contracts import FitScope
from auditory5.routes.route_b_learned import (CORE_MODELS, build_history_features, fit_outer_history,
    summarize_mode, validate_encoder_scope, validate_feature_ledger, validate_original_history)


def feature_ledger(groups=("a", "b", "c", "heldout"), each=120):
    rng = np.random.default_rng(41)
    records = []
    for group in groups:
        for i in range(each + 1):
            records.append(dict(trial_id=f"{group}_trial_{i}", record_id=group, candidate_id=group,
                split_group_id=group, segment_id=f"segment_{group}", onset_sample=700 * i,
                stimulus_local_id=0, accepted=True, event_literal="1", previous_code="1" if i else None,
                previous_event_id=f"{group}_trial_{i - 1}" if i else None,
                previous_gap_s=float(rng.choice([.6, .7, .8])) if i else np.nan,
                history_target=i % 2 if i else np.nan,
                segment_position_fraction=float(rng.choice([1 / 6, .5, 5 / 6])), time_block_id=i // 4))
    rows = pd.DataFrame(records)
    post = np.arange(len(rows) * 64, dtype=np.float32).reshape(len(rows), 64)
    payload = dict(pre=post + .25, post=post, trial_ids=rows.trial_id.to_numpy(str),
                   groups=rows.split_group_id.to_numpy(str), y=rows.stimulus_local_id.to_numpy(int))
    return payload, rows


class LearnedBLedgerTests(unittest.TestCase):
    def test_feature_history_must_equal_original_ledger_before_qc_filtering(self):
        _, rows = feature_ledger()
        validate_original_history(rows, rows.iloc[::-1])
        changed = rows.copy()
        changed.loc[5, "history_target"] = 1 - changed.loc[5, "history_target"]
        with self.assertRaisesRegex(ValueError, "B_ORIGINAL_EVENT_MISMATCH"):
            validate_original_history(changed, rows)

    def test_alignment_width_and_clinical_schema_are_hard_failures(self):
        payload, rows = feature_ledger()
        pd.testing.assert_frame_equal(validate_feature_ledger(payload, rows), rows)
        changed = dict(payload, trial_ids=payload["trial_ids"][::-1])
        with self.assertRaisesRegex(ValueError, "B_FEATURE_ALIGNMENT"):
            validate_feature_ledger(changed, rows)
        with self.assertRaisesRegex(ValueError, "B_FEATURE_DIMENSION"):
            validate_feature_ledger(dict(payload, post=payload["post"][:, :32]), rows)
        changed_rows = rows.copy()
        changed_rows["MUSS_source_percentage"] = 0
        with self.assertRaisesRegex(ValueError, "B_CLINICAL_FIELDS_FORBIDDEN"):
            validate_feature_ledger(payload, changed_rows)

    def test_full_ledger_coverage_and_identity_assignments_match_frozen_support(self):
        payload, rows = feature_ledger(("a", "b"))
        support = pd.DataFrame([dict(record_id=g, candidate_id=g, split_group_id=g, accepted_P1=121,
                                     general=True, A=False, B=True, D=False) for g in ("a", "b")])
        validate_feature_ledger(payload, rows, support)
        support.loc[0, "accepted_P1"] -= 1
        with self.assertRaisesRegex(ValueError, "B_FEATURE_COVERAGE"):
            validate_feature_ledger(payload, rows, support)
        support.loc[0, "accepted_P1"] += 1
        support.loc[0, "split_group_id"] = "another_group"
        with self.assertRaisesRegex(ValueError, "B_FEATURE_COVERAGE"):
            validate_feature_ledger(payload, rows, support)

    def test_previous_uses_complete_accepted_ledger_and_never_rebuilds_history(self):
        payload, rows = feature_ledger(("a",))
        original = build_history_features(payload, rows, {"a"})
        # The accepted predecessor itself need not be in the H0/H1 target set.
        self.assertTrue(np.isnan(rows.loc[0, "history_target"]))
        np.testing.assert_array_equal(original.previous_post[0], payload["post"][0])
        current_id = "a_trial_11"
        target_before = original.rows.loc[original.rows.trial_id.eq(current_id), "history_target"].iloc[0]
        keep = ~rows.trial_id.eq("a_trial_10").to_numpy()
        rejected = {key: value[keep] for key, value in payload.items()}
        after = build_history_features(rejected, rows.loc[keep].reset_index(drop=True), {"a"})
        index = np.flatnonzero(after.rows.trial_id.eq(current_id))[0]
        self.assertEqual(after.rows.iloc[index].history_target, target_before)
        self.assertEqual(after.previous_indices[index], -1)
        self.assertTrue(np.isnan(after.previous_post[index]).all())
        self.assertEqual(after.rows.iloc[index].previous_event_id, "a_trial_10")

    def test_previous_cannot_cross_record_segment_identity_or_time(self):
        payload, rows = feature_ledger(("a", "b"))
        changed = rows.copy()
        changed.loc[1, "previous_event_id"] = "b_trial_0"
        with self.assertRaisesRegex(ValueError, "B_PREVIOUS_RECORD_MISMATCH"):
            build_history_features(payload, changed, {"a"})
        for column, value in (("segment_id", "different_segment"), ("candidate_id", "different_candidate"),
                              ("onset_sample", 999999)):
            changed = rows.copy()
            changed.loc[0, column] = value
            with self.assertRaisesRegex(ValueError, "B_PREVIOUS_HISTORY_MISMATCH"):
                build_history_features(payload, changed, {"a"})

    def test_checkpoint_metadata_and_scaler_must_share_outer_training_scope(self):
        scope = FitScope(("train",), test_groups=("heldout",))
        task = dict(mode="R_SIM", seed=11)
        checkpoint = dict(version="auditory5_training_v2", mode="R_SIM", seed=11,
            scope=dict(train_groups=scope.train_groups, validation_groups=(), test_groups=scope.test_groups),
            scope_hash=scope.hash, scaler=dict(scope_hash=scope.hash, fit_groups=["train"]),
            metadata=dict(scope_hash=scope.hash, train_groups=["train"], config_hash="frozen_config",
                          input_channels=20, input_time_samples=100))
        evidence = validate_encoder_scope(checkpoint, task, scope, "frozen_config")
        self.assertEqual(evidence["train_groups"], ["train"])
        changed = copy.deepcopy(checkpoint)
        changed["scaler"]["fit_groups"] = ["heldout"]
        with self.assertRaisesRegex(ValueError, "B_ENCODER_SCOPE_MISMATCH"):
            validate_encoder_scope(changed, task, scope, "frozen_config")
        changed = copy.deepcopy(checkpoint)
        changed["metadata"]["input_channels"] = 8
        with self.assertRaisesRegex(ValueError, "B_ENCODER_SCOPE_MISMATCH"):
            validate_encoder_scope(changed, task, scope, "frozen_config")


class _FrozenFakeReadout:
    def __init__(self):
        self.fit_scope = {}
        self.selected_C = 1.
        self.temperature = 1.

    def predict(self, rows, features):
        if features is not None and not np.isfinite(features).all():
            raise ValueError("missing previous feature entered a head")
        probabilities = np.full((len(rows), 2), .5)
        return dict(raw=probabilities, calibrated=probabilities.copy())


class LearnedBFoldTests(unittest.TestCase):
    def test_wrapper_fits_only_training_groups_and_reruns_all_baselines_on_previous_subset(self):
        payload, rows = feature_ledger()
        features = build_history_features(payload, rows, set(rows.record_id))
        scope = FitScope(("a", "b", "c"), test_groups=("heldout",))
        captures = []

        def fake_fit(train, values, declared_scope, **kwargs):
            self.assertEqual(declared_scope, scope)
            self.assertTrue(set(train.split_group_id) <= set(scope.train_groups))
            self.assertNotIn("heldout", set(train.split_group_id))
            self.assertEqual(kwargs["inner_folds"], 3)
            captures.append((train.copy(), {key: None if value is None else value.copy() for key, value in values.items()}))
            return {name: _FrozenFakeReadout() for name in values}

        with patch("auditory5.routes.route_b_learned.fit_history_readouts", side_effect=fake_fit):
            output, flows = fit_outer_history(features, scope, seed=20260917)
        self.assertEqual(len(captures), 2)
        self.assertEqual(set(captures[0][1]), set(CORE_MODELS))
        self.assertEqual(set(captures[1][1]), set(CORE_MODELS) | {"B4_previous", "B5_previous_post"})
        self.assertTrue(all(row["status"] == "COMPLETE_FOLD" for row in flows))
        for result in output.values():
            frame = result["predictions"]
            reference = set(frame.trial_id)
            for _, model_rows in frame.groupby(["model", "probability_mode"]):
                self.assertEqual(set(model_rows.trial_id), reference)
            self.assertEqual(set(frame.split_group_id), {"heldout"})
            for model in result["models"].values():
                self.assertFalse(model.fit_scope["inner_encoder_refitted"])
                self.assertNotIn("L0", model.fit_scope["encoder_scope"])
        # Changing outer-test EEG/labels cannot change a training fit argument.
        before = captures.copy()
        changed = copy.deepcopy(features)
        mask = changed.rows.split_group_id.eq("heldout").to_numpy()
        changed.pre[mask] *= -100
        changed.post[mask] += 1e9
        changed.previous_post[mask] -= 1e9
        changed.rows.loc[mask, "history_target"] = 1 - changed.rows.loc[mask, "history_target"]
        captures.clear()
        with patch("auditory5.routes.route_b_learned.fit_history_readouts", side_effect=fake_fit):
            fit_outer_history(changed, scope, seed=20260917)
        for first, second in zip(before, captures):
            pd.testing.assert_frame_equal(first[0], second[0])
            for name in first[1]:
                if first[1][name] is not None:
                    np.testing.assert_array_equal(first[1][name], second[1][name])

    def test_summary_cannot_claim_complete_core_below_20_candidates(self):
        rows = []
        for analysis_set in ("all", "previous_response_available"):
            models = CORE_MODELS if analysis_set == "all" else (*CORE_MODELS, "B4_previous", "B5_previous_post")
            for model in models:
                for group in ("a", "b"):
                    for h in (0, 1):
                        rows.append(dict(analysis_set=analysis_set, model=model, probability_mode="raw",
                            split_group_id=group, trial_id=f"{group}_{h}", history_target=h, p0=.5, p1=.5))
        losses, summary = summarize_mode(pd.DataFrame(rows), [dict(status="COMPLETE_FOLD")] * 2, 1, seed=1)
        self.assertEqual(summary["status"], "INSUFFICIENT")
        self.assertFalse(summary["full_B_complete"])
        self.assertTrue(all(row["estimate"] == 0 for row in summary["comparisons"]))
        self.assertEqual(set(losses.split_group_id), {"a", "b"})


if __name__ == "__main__":
    unittest.main()
