"""ALN3.5 APwrong: complete-family identities and fixed-original-SE max-|z*|.

Pre-result correction of the sealed, zero-output v1 analysis. Training, v1 seal,
and v1 placeholders remain byte-identical. Uses the supplied reference unchanged.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ..prior33 import analysis as OLD
from . import ap_wrong as W, ap_wrong_queries as Q

BASE = W.OUT / "analysis_v2"
SEAL = BASE / "registration.json"
LEDGER = W.STORAGE / "analysis_v2/query_ledger.json"
RESULT = W.ROOT / "results/auditory_alignment_v3/aln35/ap_wrong/paired_v2.json"
NOTE = W.ROOT / "docs/auditory_alignment_v3/aln35/AP_WRONG_ANALYSIS_V2.md"
REFERENCE = W.ROOT / "AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018/src/aln35_reference/contrasts.py"
module_spec = importlib.util.spec_from_file_location("aln35_apwrong_reference_contrasts", REFERENCE)
REF = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(REF)
METRICS = {"dtu": (OLD.PRIMARY,), "fau": (OLD.PRIMARY,), "private_bdf": ("NLL", "AUC")}
CONTRASTS = {"AP-S": ("S", "AP"), "APwrong-S": ("S", "APwrong"), "AP-APwrong": ("APwrong", "AP")}


def code_hashes():
    from auditory_c3 import private_mi, private_mi2
    from auditory_c3.c3dl import hc
    from auditory_alignment import data, evaluate
    paths = [Path(__file__), Path(Q.__file__), Path(OLD.__file__), REFERENCE, NOTE,
             Path(private_mi.__file__), Path(private_mi2.__file__), Path(hc.__file__), Path(data.__file__), Path(evaluate.__file__),
             W.ROOT / "tests/auditory_alignment_v3/aln35/test_ap_wrong_analysis_v2.py"]
    return {str(path.relative_to(W.ROOT)): W.sha(path) for path in paths}


def make_specs(ledger):
    specs = []
    for di, dataset in enumerate(METRICS):
        expected = ledger["expected"][dataset]
        for mi, metric in enumerate(METRICS[dataset]):
            direction = 1 if OLD.DIRECTION[metric] == "lower" else -1
            terms = [{"id": name, "terms": [
                {"group": "all", "arm": reference, "window": "full", "weight": direction},
                {"group": "all", "arm": candidate, "window": "full", "weight": -direction}]}
                     for name, (reference, candidate) in CONTRASTS.items()]
            spec = {"family_id": f"S35_AP_WRONG_v2|{dataset}|{metric}", "dataset": dataset,
                    "metric": metric, "unit": "AUC" if metric == "AUC" else (
                        "bits/trial" if dataset == "private_bdf" else "bits/query"),
                    "required_seeds": [3401], "required_folds_by_identity": ledger["required_folds"][dataset],
                    "expected_identities": {"all": sorted(expected)}, "group_sets": {"all": sorted(set(expected.values()))},
                    "bootstrap": {"B": 4000, "seed": 351035 + 10 * di + mi, "alpha": .05, "resampling": "stratified"},
                    "minimum_n": 3, "analysis_role": "outer_test", "require_full_provenance": True,
                    "description": "Exploratory paired common-sampler h30; complete S/AP/APwrong and all declared content folds; hearing-group strata",
                    "contrasts": terms}
            REF.validate_spec(spec)
            specs.append(spec)
    return specs


def endpoint_values(record, dataset):
    context = {"notes": [], "mode": "T", "objective": "NCE", "slot": record.get("arm", "S")}
    view = (OLD._private_view if dataset == "private_bdf" else OLD._continuous_view)(record["eval"], context)
    return view["rows"]


def normalized_rows(record, arm, cell, path, source_sha):
    dataset = cell["dataset"]
    queried = Q.check_record(record, cell, dataset)
    metrics = endpoint_values(record, dataset)
    fit = cell["target_fit"] + ([] if arm == "S" else cell["donor_fit"])
    selection = cell["target_selection"] + ([] if arm == "S" else cell["donor_selection"])
    rows, missing = [], []
    for pid, person in queried.items():
        for metric in METRICS[dataset]:
            value = metrics[pid].get(metric)
            if value is None or not math.isfinite(value):
                missing.append({"identity": person["identity"], "metric": metric, "arm": arm,
                                "fold": cell["fold_name"], "reason": "missing_or_nonfinite_endpoint"})
                continue
            rows.append({"dataset": dataset, "identity": person["identity"], "group": person["group"],
                         "stratum": person["group"], "fold": cell["fold_name"], "seed": 3401,
                         "arm": arm, "window": "full", "metric": metric,
                         "unit": "AUC" if metric == "AUC" else ("bits/trial" if dataset == "private_bdf" else "bits/query"),
                         "value": float(value), "query_set_id": person["query_set_id"], "analysis_role": "outer_test",
                         "provenance": {"query_ids": person["query_ids"], "support_ids": [],
                                        "population_fit_identities": sorted(set(fit)), "selection_identities": sorted(set(selection)),
                                        "outer_fold": f"subject_partition_{cell['subject_fold']}",
                                        "source_record": str(path), "source_sha256": source_sha,
                                        "source_fold_ids": [cell["fold_name"]], "source_seed_ids": [3401],
                                        "aggregation_note": "one original evaluator cell; no seed or content averaging yet"},
                         "metadata": {"candidate_ids": cell["candidate_ids"],
                                      "candidate_order_sha256": cell["candidate_order_sha256"],
                                      "query_order_sha256": person["query_order_sha256"],
                                      "query_provenance": "frozen evaluator reconstruction; legacy records were not runtime-instrumented",
                                      "input_view_sha256": record["view"]["view_sha256"],
                                      "readout": "positive_affine_native" if dataset == "private_bdf" else "unified_mode_T"}})
    return rows, missing


def check_same_queries(rows):
    """The reference checks query sets; also verify actual candidate order here."""
    seen = {}
    for row in rows:
        key = (row["dataset"], row["identity"], row["fold"], row["seed"])
        current = (row["query_set_id"], row["metadata"]["candidate_order_sha256"],
                   tuple(row["metadata"]["candidate_ids"]), tuple(row["provenance"]["query_ids"]))
        if key in seen and seen[key] != current:
            raise ValueError("paired arms do not share actual ordered query/candidate IDs")
        seen[key] = current
    return True


def register():
    plan, plan_sha = W.open_plan()
    if SEAL.exists():
        raise FileExistsError("v2 analysis seal exists")
    if list((W.OUT / "units").glob("ALN35APT_*.json")):
        raise RuntimeError("new target results exist; this pre-result correction can no longer be registered")
    v1 = W.OUT / "analysis_registration.json"
    old_result = W.ROOT / "results/auditory_alignment_v3/aln35/ap_wrong/paired.json"
    if sum(json.loads(old_result.read_text())["complete_target_cells"].values()) != 0:
        raise ValueError("v1 was not an empty placeholder")
    ledger = Q.make_ledger(plan)
    # Validate every legacy S against explicit reconstructed IDs before sealing.
    rows, checked = [], set()
    for unit in plan["units"]:
        if unit["stage"] != "target" or unit["arm"] != "AP":
            continue
        ref = unit["scratch_reference"]
        if ref["path"] in checked:
            continue
        checked.add(ref["path"])
        record = json.loads(Path(ref["path"]).read_text())
        row = unit["adapter_row"]
        cell = ledger["cells"][f"{unit['dataset']}|{row['subject_fold']}|{row['content_fold']}"]
        normalized, _ = normalized_rows(record, "S", cell, ref["path"], ref["sha256"])
        rows.extend(normalized)
    REF.validate_rows(rows)
    check_same_queries(rows)
    W.write(LEDGER, ledger)
    LEDGER.chmod(0o400)
    specs = make_specs(ledger)
    body = {"version": "ALN35_APWRONG_ANALYSIS_v2", "created_utc": datetime.now(timezone.utc).isoformat(),
            "job": os.environ["SLURM_JOB_ID"], "training_plan_sha256": plan_sha,
            "code_hashes": code_hashes(), "new_target_results_at_correction": 0,
            "supersedes_analysis_only": {"v1_seal": str(v1), "v1_sha256": W.sha(v1),
                "v1_empty_result": str(old_result), "v1_empty_result_sha256": W.sha(old_result),
                "reason": "v1 incorrectly inherited old bootstrap-t and partial-cell per-contrast pairing; docs06§6.5 requires fixed-original-SE max-|z*| and complete family panel"},
            "query_ledger": {"path": str(LEDGER), "sha256": W.sha(LEDGER)}, "specs": specs,
            "exploratory": True, "training_changed": False,
            "historical_query_provenance_limit": ledger["historical_limit"],
            "legacy_S_records_validated": len(checked), "expected_n": {ds: len(v) for ds, v in ledger["expected"].items()}}
    W.write(SEAL, body)
    SEAL.with_suffix(".sha256").write_text(W.sha(SEAL) + "\n")
    SEAL.chmod(0o444); SEAL.with_suffix(".sha256").chmod(0o444)
    print(json.dumps({"status": "PASS", "analysis_v2_sha256": W.sha(SEAL), "expected_n": body["expected_n"]}), flush=True)


def verify():
    plan, plan_sha = W.open_plan()
    registration = json.loads(SEAL.read_text())
    if W.sha(SEAL) != SEAL.with_suffix(".sha256").read_text().strip():
        raise ValueError("v2 analysis seal mismatch")
    if registration["code_hashes"] != code_hashes() or registration["training_plan_sha256"] != plan_sha:
        raise ValueError("v2 analysis/training code drift")
    if W.sha(LEDGER) != registration["query_ledger"]["sha256"]:
        raise ValueError("explicit query/candidate ledger changed")
    ledger = json.loads(LEDGER.read_text())
    for path, expected in ledger["source_files"].items():
        if W.sha(path) != expected:
            raise ValueError("private staged input changed after query-ID registration")
    return plan, registration, ledger


def export_rows(plan, ledger):
    rows, missing, sources, done = [], [], {}, Counter()
    seen_scratch = set()
    for unit in plan["units"]:
        if unit["stage"] != "target":
            continue
        row = unit["adapter_row"]
        cell = ledger["cells"][f"{unit['dataset']}|{row['subject_fold']}|{row['content_fold']}"]
        ref = unit["scratch_reference"]
        scratch = json.loads(Path(ref["path"]).read_text())
        if ref["path"] not in seen_scratch:
            seen_scratch.add(ref["path"])
            normalized, issues = normalized_rows(scratch, "S", cell, ref["path"], ref["sha256"])
            rows.extend(normalized); missing.extend(issues); sources[ref["path"]] = ref["sha256"]
        path = W.OUT / "units" / f'{unit["unit_id"]}.json'
        if not path.exists():
            missing.append({"unit_id": unit["unit_id"], "dataset": unit["dataset"], "arm": unit["arm"],
                            "subject_fold": row["subject_fold"], "content_fold": row["content_fold"],
                            "reason": "technical_failure" if path.with_name(path.stem + ".FAILED.json").exists() else "not_complete"})
            continue
        record = json.loads(path.read_text())
        if (record["status"] != "complete" or record["plan_sha256"] != W.sha(W.PLAN)
                or record["arm"] != unit["arm"] or record["adapter_row"] != row
                or record["code_hashes"] != plan["code_hashes"]):
            raise ValueError("new target execution identity mismatch")
        if record["normalisation_access"] != scratch["normalisation_access"]:
            raise ValueError("target preprocessing access differs from S")
        normalized, issues = normalized_rows(record, unit["arm"], cell, path, W.sha(path))
        rows.extend(normalized); missing.extend(issues); sources[str(path)] = W.sha(path)
        done[unit["dataset"]] += 1
    REF.validate_rows(rows)
    check_same_queries(rows)
    return rows, missing, sources, done


def run():
    plan, registration, ledger = verify()
    rows, missing, sources, done = export_rows(plan, ledger)
    analyses = [REF.analyze(rows, spec) for spec in registration["specs"]]
    private = {"normalized_rows": rows, "families": analyses, "missing": missing}
    W.write(W.STORAGE / "analysis_v2/normalized_and_results.json", private)
    public = copy.deepcopy(analyses)
    for family in public:
        family.pop("identity_values")
    result = {"version": "ALN35_APWRONG_ANALYSIS_v2", "analysis_sha256": W.sha(SEAL),
              "training_plan_sha256": registration["training_plan_sha256"], "exploratory": True,
              "complete_target_cells": dict(done), "expected_target_cells": 50,
              "query_ledger_sha256": registration["query_ledger"]["sha256"],
              "query_provenance_limit": ledger["historical_limit"], "source_records": sources,
              "method": "identity bootstrap with fixed original SE, max absolute centered z-star",
              "complete_family_panel_required": True, "families": public, "missing": missing,
              "v1_preserved": registration["supersedes_analysis_only"]}
    W.write(RESULT, result)
    render(result)
    print(json.dumps({"status": "PASS", "complete_target_cells": dict(done), "analysis_sha256": W.sha(SEAL)}), flush=True)


def render(result):
    lines = ["# ALN3.5 APwrong results, corrected analysis v2", "",
             "Analysis-only correction before any new target result: v1 incorrectly inherited the previous round's bootstrap-t and partial-cell pairing. Its seal and empty report remain intact. v2 applies package §6.5 and does not alter training.", "",
             f"Completed target executions: {sum(result['complete_target_cells'].values())}/50; exploratory seed3401.", "",
             "| Dataset | Endpoint | Contrast | Common complete people / expected | Effect | Simultaneous 95% | Status |",
             "|---|---|---|---:|---:|---|---|"]
    for family in result["families"]:
        cover = family["coverage"]["all"]
        for contrast in family["contrasts"]:
            effect = "pending" if contrast["estimate"] is None else f"{contrast['estimate']:+.5g}"
            ci = contrast["simultaneous_ci"]
            ci = "unavailable" if ci is None else f"[{ci[0]:.5g}, {ci[1]:.5g}]"
            lines.append(f"| {family['dataset']} | {family['metric']} | {contrast['id']} | {cover['common_complete_n']}/{cover['expected_n']} | {effect} | {ci} | {contrast['status']} |")
    lines += ["", "Every family uses the same people complete for S/AP/APwrong, all required content folds, and seed3401. The roster is supplied from the frozen manifest: DTU44, FAU67, private64. Subject-fold is exclusion membership, not a repeated fold. Public content folds0/1 are both required; private has one evaluation cell.", "",
              "The package's unchanged reference analyzer performs 4,000 whole-person bootstrap draws within hearing-group strata, shares draws across all contrasts, and uses fixed original standard errors for max-|z*| intervals. Each metric is its own three-contrast family. Low n, zero stratum contrast variance and other nonregular cases retain point estimates and missing intervals, with reasons in JSON.", "",
              "Ordered query and candidate IDs are reconstructed from the exact frozen evaluator metadata, bound to input-view/code hashes, and stored privately. This exceeds count-only matching. Historical S records did not capture runtime query IDs; reconstruction is explicitly distinguished from historical runtime evidence. Private staged-source hashes are rechecked at every analysis.", "",
              "Positive risk effects mean reference minus candidate; positive AUC effects mean candidate minus reference. Intervals condition on these fitted models/content/seed. AP over wrong alone does not establish AP over S. All original public-prior endpoints remain available; no performance gate or sign-based stopping is introduced."]
    path = W.ROOT / "docs/auditory_alignment_v3/aln35/AP_WRONG_RESULTS_V2.md"
    path.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("register", "run"))
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Slurm only")
    (register if args.command == "register" else run)()


if __name__ == "__main__":
    main()
