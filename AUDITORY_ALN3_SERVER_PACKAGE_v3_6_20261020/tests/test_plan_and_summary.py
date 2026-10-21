"""Meaningful safeguards: deduplication, identity inference and missing data."""
import importlib.util
from pathlib import Path
import copy
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class PlanAndSummary(unittest.TestCase):
    def test_person_slices_reuse_group_training(self):
        plan = module("materialize_plan").expand(json.loads((ROOT / "plans/round1.json").read_text()))
        self.assertEqual(plan["unique_train_count"], 12)
        self.assertEqual(plan["evaluation_bundle_count"], 110)
        for train in plan["source_training"]:
            matched = [e for e in plan["evaluations"] if e.get("source_draft_id") == train["draft_id"]]
            self.assertEqual({e["person_fold"] for e in matched}, {0, 1, 2, 3, 4})
            self.assertNotIn("person_fold", train)

    def test_repeats_do_not_inflate_n_and_missing_not_zero(self):
        family = {"family_id": "synthetic", "unit": "MSE", "expected_people": {"all": ["a", "b", "c"]},
                  "required_seeds": [1, 2], "required_repeats": ["0", "1"],
                  "contrasts": [{"name": "gain", "group": "all"}], "rows": []}
        for p, value in zip(["a", "b", "c"], [1., 2., 3.]):
            for s in [1, 2]:
                for t in ["0", "1"]:
                    family["rows"].append(dict(person_id=p, group="all", seed=s, repeat=t, contrast="gain", value=value))
        summary = module("paired_summary").summarize_family(family, B=200)
        self.assertEqual(summary["contrasts"][0]["n"], 3)
        self.assertEqual(summary["contrasts"][0]["estimate"], 2.)
        incomplete = copy.deepcopy(family)
        incomplete["rows"].pop()
        result = module("paired_summary").summarize_family(incomplete, B=200)
        self.assertEqual(result["status"], "incomplete_no_intervals")
        self.assertEqual(result["coverage"]["all"]["missing_people"], ["c"])
        self.assertIsNone(result["contrasts"][0]["simultaneous_95"])
        duplicated = copy.deepcopy(family)
        duplicated["rows"].append(duplicated["rows"][0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            module("paired_summary").summarize_family(duplicated, B=200)


if __name__ == "__main__":
    unittest.main()
