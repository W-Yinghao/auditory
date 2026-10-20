"""Synthetic contract checks, not validation on actual EEG or server artifacts."""

import copy
import importlib.util
import io
import json
import math
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aln35_reference.contrasts import ReferenceError, analyze, parse_json, validate_rows
from aln35_reference.sampling import allocate_support_ids, audit_mask_coverage


def synthetic_rows():
    rows = []
    for group in ("HA", "NH"):
        for i in range(4):
            identity = f"SYN_{group}_{i + 1}"
            for seed in (3401, 3407):
                for fold_index, fold in enumerate(("content_0", "content_1")):
                    baseline = 20 + 10 * fold_index + 5 * (seed == 3407)
                    effect = (i + 1) * (1 if group == "HA" else .2) + .4 * fold_index + .2 * (seed == 3407)
                    for window in ("early", "late"):
                        benefit = effect + (.25 * (i + 1) if window == "late" else 0)
                        for arm in ("reference", "candidate"):
                            query = f"q:{identity}:{fold}"
                            rows.append({"dataset": "synthetic_demo", "identity": identity, "group": group,
                                         "stratum": "region_0" if i < 2 else "region_1",
                                         "fold": fold, "seed": seed, "arm": arm, "window": window,
                                         "metric": "true_query_nll", "unit": "bits/query",
                                         "value": round(baseline - (benefit if arm == "candidate" else 0), 10),
                                         "query_set_id": query, "analysis_role": "outer_test",
                                         "provenance": {"query_ids": [query], "support_ids": [f"support:{identity}:{fold}"],
                                                        "population_fit_identities": ["SYN_SOURCE_TRAIN"],
                                                        "selection_identities": ["SYN_INNER_DEV"],
                                                        "outer_fold": f"subject_partition_{i % 2}",
                                                        "source_record": "synthetic_only"}})
    return rows


def term(group, arm, window, weight):
    return {"group": group, "arm": arm, "window": window, "weight": weight}


def synthetic_spec():
    return {"family_id": "SYNTHETIC_ONLY_three_contrasts", "dataset": "synthetic_demo",
            "metric": "true_query_nll", "unit": "bits/query", "required_folds": ["content_0", "content_1"],
            "required_seeds": [3401, 3407], "minimum_n": 3, "require_full_provenance": True,
            "expected_identities": {g: [f"SYN_{g}_{i + 1}" for i in range(4)] for g in ("HA", "NH")},
            "bootstrap": {"B": 4000, "seed": 351001, "resampling": "independent", "alpha": .05},
            "contrasts": [
                {"id": "HA_benefit", "terms": [term("HA", "reference", "early", 1), term("HA", "candidate", "early", -1)]},
                {"id": "HA_minus_NH_benefit", "terms": [term("HA", "reference", "early", 1), term("HA", "candidate", "early", -1),
                                                         term("NH", "reference", "early", -1), term("NH", "candidate", "early", 1)]},
                {"id": "HA_early_minus_late_risk", "terms": [term("HA", "candidate", "early", 1), term("HA", "candidate", "late", -1)]},
            ]}


class PairedInferenceTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.spec = synthetic_rows(), synthetic_spec()

    def test_manual_paired_estimates_and_identity_n(self):
        result = analyze(self.rows, self.spec)
        self.assertEqual(result["status"], "regular")
        self.assertEqual(result["coverage"]["HA"]["common_complete_n"], 4)
        self.assertEqual(result["coverage"]["NH"]["expected_n"], 4)
        estimates = {x["id"]: x for x in result["contrasts"]}
        self.assertAlmostEqual(estimates["HA_benefit"]["estimate"], 2.8)
        self.assertAlmostEqual(estimates["HA_minus_NH_benefit"]["estimate"], 2.0)
        self.assertAlmostEqual(estimates["HA_early_minus_late_risk"]["estimate"], .625)
        # Hand calculation: independent group-mean variances 5/12 and 1/60.
        self.assertAlmostEqual(estimates["HA_minus_NH_benefit"]["original_se"], math.sqrt(5 / 12 + 1 / 60))
        self.assertEqual(result["bootstrap"]["B"], 4000)
        self.assertFalse(result["bootstrap"]["original_se_reestimated_per_draw"])

    def test_reproducible_and_invariant_to_input_row_order(self):
        first = analyze(self.rows, self.spec)
        self.assertEqual(first, analyze(list(reversed(self.rows)), self.spec))

    def test_missing_one_condition_excludes_person_from_entire_group_family(self):
        target = next(r for r in self.rows if r["identity"] == "SYN_HA_1" and r["seed"] == 3407 and
                      r["fold"] == "content_1" and r["arm"] == "candidate" and r["window"] == "late")
        self.rows.remove(target)
        result = analyze(self.rows, self.spec)
        self.assertEqual(result["coverage"]["HA"]["common_complete_n"], 3)
        self.assertEqual(len(result["coverage"]["HA"]["excluded_incomplete"]["SYN_HA_1"]["missing_cells"]), 1)
        for contrast in result["contrasts"]:
            self.assertEqual(contrast["groups"]["HA"]["n"], 3)

    def test_missing_required_seed_is_not_silently_averaged_over_observed_seeds(self):
        self.rows = [r for r in self.rows if not (r["identity"] == "SYN_HA_1" and r["seed"] == 3407)]
        result = analyze(self.rows, self.spec)
        self.assertNotIn("SYN_HA_1", result["coverage"]["HA"]["complete_identities"])
        self.assertTrue(result["coverage"]["HA"]["excluded_incomplete"]["SYN_HA_1"]["missing_cells"])

    def test_expected_roster_missing_people_and_no_roster_are_distinct(self):
        self.spec["expected_identities"]["HA"].append("SYN_HA_ABSENT")
        result = analyze(self.rows, self.spec)
        self.assertEqual(result["coverage"]["HA"]["expected_n"], 5)
        self.assertEqual(result["coverage"]["HA"]["missing_expected_identities"], ["SYN_HA_ABSENT"])
        del self.spec["expected_identities"]
        observed = analyze(self.rows, self.spec)["coverage"]["HA"]
        self.assertIsNone(observed["expected_n"])
        self.assertEqual(observed["expected_status"], "not_supplied")

    def test_per_identity_required_folds_do_not_weight_people_by_fold_count(self):
        self.rows = [r for r in self.rows if not (r["identity"] == "SYN_HA_1" and r["fold"] == "content_1")]
        self.spec["required_folds_by_identity"] = {"SYN_HA_1": ["content_0"]}
        result = analyze(self.rows, self.spec)
        self.assertEqual(result["coverage"]["HA"]["common_complete_n"], 4)
        self.assertAlmostEqual(result["identity_values"]["HA"]["SYN_HA_1"]["HA_benefit"], 1.1)
        self.assertAlmostEqual(result["contrasts"][0]["estimate"], 2.75)

    def test_group_pooling_is_explicit_and_overlap_is_rejected(self):
        self.spec["contrasts"] = [{"id": "pooled", "terms": [term("all", "reference", "early", 1), term("all", "candidate", "early", -1)]}]
        self.spec["group_sets"] = {"all": ["HA", "NH"]}
        del self.spec["expected_identities"]
        result = analyze(self.rows, self.spec)
        self.assertEqual(result["coverage"]["all"]["common_complete_n"], 8)
        self.assertAlmostEqual(result["contrasts"][0]["estimate"], 1.8)
        self.spec["contrasts"].append({"id": "overlap", "terms": [term("HA", "candidate", "early", 1)]})
        with self.assertRaisesRegex(ReferenceError, "overlap"):
            analyze(self.rows, self.spec)

    def test_stratified_resampling_uses_fixed_group_stratum_weights(self):
        self.spec["bootstrap"]["resampling"] = "stratified"
        result = analyze(self.rows, self.spec)
        difference = result["contrasts"][1]
        self.assertAlmostEqual(difference["estimate"], 2.0)
        # Two equally weighted strata per group: .125 + .005.
        self.assertAlmostEqual(difference["original_se"], math.sqrt(.13))
        self.assertEqual(difference["groups"]["HA"]["resampling_block_sizes"], [2, 2])
        del self.rows[0]["stratum"]
        with self.assertRaises(ReferenceError):
            analyze(self.rows, self.spec)

    def test_zero_variance_is_nonregular_without_confidence_interval(self):
        for row in self.rows:
            if row["window"] == "early":
                row["value"] = 20.0
        result = analyze(self.rows, self.spec)
        zero = result["contrasts"][0]
        self.assertEqual(zero["estimate"], 0.0)
        self.assertEqual(zero["status"], "nonregular")
        self.assertIsNone(zero["simultaneous_ci"])
        self.assertNotIn("HA_benefit", result["simultaneous_scope"])
        self.assertIn("No population equivalence", result["nonregular_warning"])

    def test_small_group_and_singleton_stratum_are_nonregular(self):
        self.spec["expected_identities"]["HA"] = ["SYN_HA_1", "SYN_HA_2"]
        result = analyze(self.rows, self.spec)
        self.assertTrue(all(x["status"] == "nonregular" and x["simultaneous_ci"] is None for x in result["contrasts"]))
        self.spec = synthetic_spec()
        self.spec["bootstrap"]["resampling"] = "stratified"
        for row in self.rows:
            if row["identity"] == "SYN_HA_1":
                row["stratum"] = "singleton"
        result = analyze(self.rows, self.spec)
        self.assertEqual(result["contrasts"][0]["status"], "nonregular")

    def test_sparse_discrete_sample_does_not_use_near_zero_resampled_se(self):
        rows = []
        for i in range(10):
            for arm in ("reference", "candidate"):
                row = copy.deepcopy(self.rows[0])
                row.update(identity=f"SPARSE_{i}", arm=arm, fold="evaluation", seed=3401,
                           window="full", group="all", value=float(i == 9 and arm == "reference"))
                rows.append(row)
        spec = {"family_id": "sparse", "dataset": "synthetic_demo", "metric": "true_query_nll", "unit": "bits/query",
                "required_seeds": [3401], "required_folds": ["evaluation"],
                "contrasts": [{"id": "benefit", "terms": [term("all", "reference", "full", 1), term("all", "candidate", "full", -1)]}]}
        result = analyze(rows, spec)
        self.assertEqual(result["status"], "regular")
        self.assertAlmostEqual(result["contrasts"][0]["original_se"], .1)
        self.assertLess(result["bootstrap"]["critical_value"], 5)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.spec = synthetic_rows(), synthetic_spec()

    def test_duplicate_row_and_duplicate_json_key_are_rejected(self):
        self.rows.append(copy.deepcopy(self.rows[0]))
        with self.assertRaisesRegex(ReferenceError, "duplicate normalized"):
            analyze(self.rows, self.spec)
        with self.assertRaisesRegex(ReferenceError, "duplicate JSON"):
            parse_json('{"value": 1, "value": 2}')

    def test_nonfinite_boolean_and_typo_are_rejected(self):
        for value in (float("nan"), float("inf"), True):
            self.rows[0]["value"] = value
            with self.assertRaises(ReferenceError):
                validate_rows(self.rows)
        with self.assertRaises(ReferenceError):
            parse_json('{"value": NaN}')
        self.rows[0]["value"] = 1
        self.rows[0]["vlaue"] = 1
        with self.assertRaises(ReferenceError):
            validate_rows(self.rows)

    def test_mismatched_query_sets_and_same_name_different_ids_are_rejected(self):
        self.rows[0]["query_set_id"] = "different_queries"
        with self.assertRaisesRegex(ReferenceError, "different query_set_id"):
            analyze(self.rows, self.spec)
        self.rows = synthetic_rows()
        self.rows[0]["provenance"]["query_ids"] = ["different_actual_query"]
        with self.assertRaisesRegex(ReferenceError, "different explicit query"):
            analyze(self.rows, self.spec)

    def test_support_overlap_and_outer_identity_leakage_are_rejected(self):
        for field, value in (("support_ids", self.rows[0]["provenance"]["query_ids"]),
                             ("population_fit_identities", [self.rows[0]["identity"]]),
                             ("selection_identities", [self.rows[0]["identity"]])):
            rows = synthetic_rows()
            rows[0]["provenance"][field] = value
            with self.assertRaisesRegex(ReferenceError, "leakage"):
                analyze(rows, self.spec)

    def test_inner_dev_may_be_used_for_selection_but_not_population_fit(self):
        for row in self.rows:
            row["analysis_role"] = "inner_dev"
            row["provenance"]["selection_identities"] = [row["identity"]]
        self.spec["analysis_role"] = "inner_dev"
        result = analyze(self.rows, self.spec)
        self.assertEqual(result["analysis_role"], "inner_dev")
        self.rows[0]["provenance"]["population_fit_identities"] = [self.rows[0]["identity"]]
        with self.assertRaisesRegex(ReferenceError, "leakage"):
            analyze(self.rows, self.spec)

    def test_outer_fold_mismatch_and_membership_changes_are_rejected(self):
        self.rows[0]["provenance"]["outer_fold"] = "wrong_partition"
        with self.assertRaisesRegex(ReferenceError, "outer_fold"):
            analyze(self.rows, self.spec)
        self.rows = synthetic_rows()
        self.rows[0]["group"] = "wrong_group"
        with self.assertRaisesRegex(ReferenceError, "group/stratum"):
            analyze(self.rows, self.spec)

    def test_hidden_seed_average_and_untraced_fold_average_are_rejected(self):
        self.rows[0]["provenance"]["source_seed_ids"] = [3401, 3407]
        with self.assertRaisesRegex(ReferenceError, "across seeds"):
            validate_rows(self.rows)
        self.rows = synthetic_rows()
        self.rows[0]["fold"] = "reported_identity_mean"
        with self.assertRaisesRegex(ReferenceError, "source fold/seed"):
            validate_rows(self.rows)

    def test_missing_required_folds_and_misdeclared_expected_group_are_rejected(self):
        del self.spec["required_folds"]
        with self.assertRaisesRegex(ReferenceError, "required_folds"):
            analyze(self.rows, self.spec)
        self.spec = synthetic_spec()
        self.spec["expected_identities"]["HA"] = ["SYN_NH_1"]
        self.spec["expected_identities"]["NH"] = []
        with self.assertRaisesRegex(ReferenceError, "conflicting observed group"):
            analyze(self.rows, self.spec)


class PhysicalReferenceTests(unittest.TestCase):
    def test_generic_partial_requested_window_coverage(self):
        result = audit_mask_coverage({"sample_rate_hz": 200, "mask_samples": [-200, 0],
                                      "contexts": [{"id": "local_pre", "input_samples": [0, 120], "expected_overlap_samples": 0},
                                                   {"id": "fm_pre", "input_samples": [-50, 550], "expected_overlap_samples": 50}]})
        self.assertTrue(result["all_declared_counts_match"])
        local, fm = result["contexts"]
        self.assertFalse(local["has_requested_data"])
        self.assertEqual(local["retained_samples"], 0)
        self.assertEqual(local["zeroed_samples"], 120)
        self.assertIs(local["all_zero_input_after_keep_mask"], True)
        self.assertEqual(fm["overlap_samples"], 50)
        self.assertEqual(fm["overlap_seconds"], .25)
        self.assertEqual(fm["requested_mask_fraction_present"], .25)

    def test_private_250hz_pre_geometry_and_keep_mask(self):
        # Production private access geometry at baseline 5ef4a60: pre [-200,0) ms,
        # local [0,600) ms, FM [-200,600) ms; 250 Hz. Values are not read here.
        result = audit_mask_coverage({"sample_rate_hz": 250, "mask_samples": [-50, 0],
                                      "contexts": [{"id": "local_pre", "input_samples": [0, 150], "expected_overlap_samples": 0},
                                                   {"id": "fm_pre", "input_samples": [-50, 150], "expected_overlap_samples": 50}]})
        local, fm = result["contexts"]
        self.assertTrue(result["all_declared_counts_match"])
        self.assertFalse(result["input_values_inspected"])
        self.assertEqual((local["retained_samples"], local["zeroed_samples"]), (0, 150))
        self.assertFalse(local["has_requested_data"])
        self.assertIs(local["all_zero_input_after_keep_mask"], True)
        self.assertEqual((fm["retained_samples"], fm["zeroed_samples"]), (50, 150))
        self.assertEqual(fm["retained_seconds"], .2)
        self.assertEqual(fm["requested_mask_fraction_present"], 1.0)
        self.assertTrue(fm["has_requested_data"])
        self.assertIsNone(fm["all_zero_input_after_keep_mask"])
        self.assertNotIn("perturbation_can_change_physical_input", local)

    def test_keep_mask_retains_positions_without_claiming_values_are_nonzero(self):
        result = audit_mask_coverage({"sample_rate_hz": 250, "mask_samples": [-50, 0],
                                      "contexts": [{"id": "pre_only_input", "input_samples": [-50, 0], "expected_overlap_samples": 50}]})
        context = result["contexts"][0]
        self.assertEqual(context["retained_samples"], 50)
        self.assertEqual(context["zeroed_samples"], 0)
        self.assertTrue(context["has_requested_data"])
        self.assertIsNone(context["all_zero_input_after_keep_mask"])

    def test_half_open_boundaries_and_failed_declared_coverage(self):
        result = audit_mask_coverage({"sample_rate_hz": 200, "mask_samples": [-50, 0],
                                      "contexts": [{"id": "exact", "input_samples": [-50, 0], "expected_overlap_samples": 49}]})
        self.assertEqual(result["contexts"][0]["overlap_samples"], 50)
        self.assertFalse(result["all_declared_counts_match"])
        with self.assertRaises(ReferenceError):
            audit_mask_coverage({"sample_rate_hz": 200, "mask_samples": [0, 0], "contexts": []})

    def test_same_region_nested_support_and_fixed_query(self):
        spec = {"segments": [{"id": f"segment_{i:03d}", "order": i} for i in range(100)], "seed": 351007}
        result = allocate_support_ids(spec)
        self.assertEqual((result["n_support_10"], result["n_support_30"], result["n_query"]), (10, 30, 70))
        self.assertLessEqual(set(result["support_10_ids"]), set(result["support_30_ids"]))
        self.assertFalse(set(result["support_30_ids"]) & set(result["query_ids"]))
        self.assertFalse(result["physical_context_leakage_checked"])
        self.assertEqual(result, allocate_support_ids(dict(spec, segments=list(reversed(spec["segments"])))))
        self.assertNotEqual(result["support_10_ids"], result["support_30_ids"][:10])

    def test_support_rounding_small_n_and_duplicate_ids(self):
        spec = {"segments": [{"id": str(i), "order": i} for i in range(11)], "seed": 1}
        result = allocate_support_ids(spec)
        self.assertEqual((result["n_support_10"], result["n_support_30"], result["n_query"]), (1, 3, 8))
        spec["segments"] = spec["segments"][:9]
        with self.assertRaisesRegex(ReferenceError, "insufficient"):
            allocate_support_ids(spec)
        spec["segments"].append(spec["segments"][0])
        with self.assertRaisesRegex(ReferenceError, "unique"):
            allocate_support_ids(spec)


class CommandLineBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        module_spec = importlib.util.spec_from_file_location("aln35_cli_for_test", cls.root / "scripts" / "paired_contrasts.py")
        cls.cli = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(cls.cli)

    def test_cli_reads_example_and_emits_the_declared_reference_method(self):
        rows_path = self.root / "examples" / "synthetic_rows.jsonl"
        before = rows_path.read_bytes()
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = self.cli.main(["contrast", "--rows", str(rows_path), "--spec-json", json.dumps(synthetic_spec())])
        result = json.loads(stream.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["coverage"]["HA"]["common_complete_n"], 4)
        self.assertTrue(result["not_legacy_bootstrap_t"])
        self.assertEqual(rows_path.read_bytes(), before)

    def test_existing_output_including_input_file_is_never_overwritten(self):
        rows_path = self.root / "examples" / "synthetic_rows.jsonl"
        before = rows_path.read_bytes()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            self.cli.main(["contrast", "--rows", str(rows_path), "--spec-json", json.dumps(synthetic_spec()),
                           "--output", str(rows_path)])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(rows_path.read_bytes(), before)

    def test_mask_declared_count_mismatch_has_machine_readable_report_and_nonzero_exit(self):
        spec = {"sample_rate_hz": 250, "mask_samples": [-50, 0],
                "contexts": [{"id": "fm_pre", "input_samples": [-50, 150], "expected_overlap_samples": 49}]}
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = self.cli.main(["mask", "--spec-json", json.dumps(spec)])
        self.assertEqual(code, 3)
        self.assertFalse(json.loads(stream.getvalue())["all_declared_counts_match"])


if __name__ == "__main__":
    unittest.main()
