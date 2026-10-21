#!/usr/bin/env python3
"""Synthetic correctness checks for paired_risk_summary; no real observations."""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
MODULE_PATH = Path(__file__).with_name("paired_risk_summary.py")
SPEC = importlib.util.spec_from_file_location("paired_risk_summary", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PairedRiskChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aln4_paired_risk_synthetic_")
        self.folder = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def records(self, seeds=(3401, 3407), tools=("local",)):
        rows = []
        for i in range(4):
            for tool in tools:
                for seed in seeds:
                    h0 = (1.0, 1.1, .9, 1.2)[i]
                    e0 = h0 - (.20, .24, .19, .22)[i]
                    hp = h0 + (.30, .28, .34, .27)[i]
                    ec = hp - (.10, .12, .13, .09)[i]
                    et = ec + (.02, -.01, .03, .015)[i]
                    row = dict(cohort="synthetic", person_id=f"P{i}", tool=tool, seed=seed, unit="mse")
                    row.update({f"risk_{s}": v for s, v in zip(MODULE.STATES, (h0, e0, hp, ec, et))})
                    digest = hashlib.sha256(f"synthetic_query_P{i}".encode()).hexdigest()
                    row.update({key: digest for key in MODULE.RISK_FINGERPRINTS})
                    rows.append(row)
        return rows

    def write_csv(self, records, name="input.csv"):
        path = self.folder / name
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        return path

    def report(self, records, seeds=(3401, 3407), **kwargs):
        return MODULE.build_report(self.write_csv(records), list(seeds), bootstrap=1000, **kwargs)

    def test_gc_positive_does_not_imply_improvement_over_e0(self):
        cohort = self.report(self.records())["cohorts"][0]
        gains = cohort["descriptive_by_tool"][0]["mean_effects"]
        self.assertGreater(gains["GC"], 0)
        self.assertLess(gains["NET_C"], 0)
        self.assertLess(gains["NET_T"], 0)
        self.assertAlmostEqual(gains["NET_C"], gains["GH"] + gains["GC"] - gains["G0"])
        self.assertLess(cohort["max_algebra_reconstruction_error"], 1e-14)
        self.assertEqual(cohort["net_family"]["bootstrap_used"], 1000)

    def test_duplicate_seeds_do_not_double_the_participant_sample(self):
        # Identical predictions at two DIFFERENT registered seeds change neither person SE nor CI.
        one = self.report(self.records(seeds=(3401,)), seeds=(3401,))["cohorts"][0]
        two = self.report(self.records())["cohorts"][0]
        self.assertEqual(two["n_participants"], 4)
        self.assertEqual(len(two["per_person"]), 4)
        for a, b in zip(one["net_family"]["estimands"], two["net_family"]["estimands"]):
            self.assertEqual(a, b)
        # A varying seed pair is averaged WITHIN person before inferential resampling.
        records = self.records()
        for row in records:
            if row["seed"] == 3407:
                row["risk_EC"] += .2
        varied = self.report(records)["cohorts"][0]
        self.assertAlmostEqual(varied["per_person"][0]["effects"]["NET_C"],
                               two["per_person"][0]["effects"]["NET_C"] - .1)

    def test_same_query_required_within_states_and_across_tools_and_seeds(self):
        for mode in ("state", "seed", "tool"):
            with self.subTest(mode=mode):
                rows = self.records(tools=("local", "cb"))
                replacement = "f" * 64
                if mode == "state":
                    rows[0]["risk_HP_query_fingerprint"] = replacement
                else:
                    target = 1 if mode == "seed" else 2
                    for key in MODULE.RISK_FINGERPRINTS:
                        rows[target][key] = replacement
                with self.assertRaises(MODULE.ValidationError):
                    self.report(rows)

    def test_incomplete_duplicate_missing_seed_and_wholly_missing_roster_rejected(self):
        original = self.records(tools=("local", "cb"))
        for mode in ("missing_seed", "missing_tool", "duplicate", "empty_seed"):
            rows = copy.deepcopy(original)
            if mode == "missing_seed":
                rows.pop()
            elif mode == "missing_tool":
                rows = [r for r in rows if not (r["person_id"] == "P0" and r["tool"] == "cb")]
            elif mode == "duplicate":
                rows.append(copy.deepcopy(rows[0]))
            else:
                rows[0]["seed"] = ""
            with self.subTest(mode=mode), self.assertRaises(MODULE.ValidationError):
                self.report(rows)
        panel = self.folder / "panel.json"
        panel.write_text(json.dumps({"synthetic": {"person_ids": ["P0", "P1", "P2", "P3", "P4"],
                                                  "tools": ["local", "cb"], "unit": "mse"}}))
        with self.assertRaises(MODULE.ValidationError):
            self.report(original, expected_panel_path=panel)

    def test_nonfinite_negative_and_mixed_units_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf"), -1e-16):
            rows = self.records()
            rows[0]["risk_H0"] = value
            with self.subTest(value=value), self.assertRaises(MODULE.ValidationError):
                self.report(rows)
        rows = self.records()
        rows[0]["unit"] = "bits_per_trial"
        with self.assertRaises(MODULE.ValidationError):
            self.report(rows)

    def test_single_fingerprint_requires_explicit_adapter_declaration(self):
        rows = self.records()
        for row in rows:
            row["query_fingerprint"] = row[MODULE.RISK_FINGERPRINTS[0]]
            for key in MODULE.RISK_FINGERPRINTS:
                del row[key]
        with self.assertRaises(MODULE.ValidationError):
            self.report(rows)
        report = self.report(rows, shared_query_declaration=True)
        self.assertEqual(report["input"]["query_binding"], "adapter_declared_shared_Q")

    def test_degenerate_family_has_null_intervals_and_no_invalid_json(self):
        rows = self.records()
        for row in rows:
            for state, value in zip(MODULE.STATES, (1., .75, 1.5, 1.25, 1.375)):
                row[f"risk_{state}"] = value
        family = self.report(rows)["cohorts"][0]["net_family"]
        self.assertEqual(family["status"], "nonregular_zero_original_SE_family_null_CI")
        self.assertTrue(all(x["simultaneous_ci95"] is None for x in family["estimands"]))
        json.dumps(family, allow_nan=False)
        rounded_constant = MODULE._net_family(np.full((67, 1), .1),
                                              [{"tool": "synthetic", "effect": "NET_C"}],
                                              "synthetic_rounding", 1000, 1)
        self.assertEqual(rounded_constant["status"], "nonregular_zero_original_SE_family_null_CI")
        regular = self.report(self.records())["cohorts"][0]["net_family"]
        # Repeated draws of the same person yield a zero RESAMPLE SE; fixed ORIGINAL SE stays valid.
        self.assertGreater(regular["bootstrap_zero_resample_se_total"], 0)
        self.assertEqual(regular["bootstrap_used"], regular["bootstrap_requested"])

    def test_cli_writes_only_new_output_and_does_not_overwrite(self):
        source = self.write_csv(self.records())
        destination = self.folder / "result.json"
        command = [sys.executable, "-B", str(MODULE_PATH), "--input", str(source),
                   "--output", str(destination), "--expected-seeds", "3401", "3407", "--bootstrap", "1000"]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = destination.read_bytes()
        self.assertEqual(json.loads(before)["analysis_scope"]["label"], "post_R1_diagnostic_net_contrasts")
        second = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(second.returncode, 2)
        self.assertEqual(destination.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
