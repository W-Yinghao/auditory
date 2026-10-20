"""Bounded APwrong paired-identity analysis, isolated from frozen training code."""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ..prior33 import analysis as A
from ..sci_r1 import stats as S
from . import ap_wrong as W

SEAL = W.OUT / "analysis_registration.json"
RESULT = W.ROOT / "results/auditory_alignment_v3/aln35/ap_wrong/paired.json"
NOTE = W.ROOT / "docs/auditory_alignment_v3/aln35/AP_WRONG_ANALYSIS.md"
CONTRASTS = {"AP-S": ("S", "AP"), "APwrong-S": ("S", "APwrong"), "AP-APwrong": ("APwrong", "AP")}
METRICS = {"dtu": (A.PRIMARY,), "fau": (A.PRIMARY,), "private_bdf": ("NLL", "AUC")}


def code_hashes():
    paths = [Path(__file__), Path(A.__file__), Path(S.__file__), Path(A.AGG.__file__), NOTE,
             W.ROOT / "tests/auditory_alignment_v3/aln35/test_ap_wrong_analysis.py"]
    return {str(path.relative_to(W.ROOT)): W.sha(path) for path in paths}


def register():
    _, plan_sha = W.open_plan()
    if SEAL.exists():
        raise FileExistsError("analysis registration already frozen")
    # This assertion prevents silently presenting a later numerical choice as
    # prospective. The new training plan itself already declares exploration.
    target_outputs = [path.name for path in (W.OUT / "units").glob("ALN35APT_*.json")]
    if target_outputs:
        raise RuntimeError("target outputs already exist; a new explicitly post-result registration is required")
    body = {"version": "ALN35_APWRONG_ANALYSIS_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "job": os.environ["SLURM_JOB_ID"], "training_plan_sha256": plan_sha,
            "code_hashes": code_hashes(), "exploratory": True, "new_target_outputs_at_freeze": 0,
            "metrics": METRICS, "contrasts": CONTRASTS,
            "bootstrap": {"method": "identity bootstrap-t and simultaneous max-t", "replicates": S.NB,
                          "scope": A.BOOTSTRAP_SCOPE, "metric_families_separate": True},
            "cell_rule": "pair each contrast on its own complete matching cells, then average within identity",
            "missing": "list incomplete cells and nonfinite endpoint values; no imputation or score gates"}
    W.write(SEAL, body)
    SEAL.with_suffix(".sha256").write_text(W.sha(SEAL) + "\n")
    SEAL.chmod(0o444); SEAL.with_suffix(".sha256").chmod(0o444)
    print(json.dumps({"status": "PASS", "analysis_sha256": W.sha(SEAL)}), flush=True)


def endpoint_view(record, dataset):
    context = {"notes": [], "mode": "T", "objective": "NCE", "slot": record.get("arm", "S")}
    view = (A._private_view if dataset == "private_bdf" else A._continuous_view)(record["eval"], context)
    return view, context["notes"]


def assert_common_query(reference, candidate, dataset):
    """Check the actual fixed target view and evaluator coverage before pairing."""
    if reference["cell"] != candidate["cell"]:
        raise ValueError("target cell or split differs")
    if reference["view"] != candidate["view"]:
        raise ValueError("input/target view provenance differs")
    if reference["normalisation_access"] != candidate["normalisation_access"]:
        raise ValueError("normalisation access differs")
    ref, rn = endpoint_view(reference, dataset)
    cand, cn = endpoint_view(candidate, dataset)
    if ref["groups"] != cand["groups"] or ref["counts"] != cand["counts"]:
        raise ValueError("evaluated identities/groups/query counts differ")
    if ref["n_test_candidates"] != cand["n_test_candidates"]:
        raise ValueError("test candidate count differs")
    if dataset == "fau" and A.FAU_ALWAYS_TRAIN_TH.intersection(ref["rows"]):
        raise ValueError("always-train FAU people incorrectly entered evaluation")
    return ref, cand, rn + cn


def paired_differences(cells, dataset):
    """All contrasts retain their own available matched cells, with identity n."""
    values = {metric: {contrast: defaultdict(list) for contrast in CONTRASTS} for metric in METRICS[dataset]}
    missing, excluded, notes, matched = [], [], [], Counter()
    for cell, records in sorted(cells.items()):
        for contrast, (reference, candidate) in CONTRASTS.items():
            absent = [arm for arm in (reference, candidate) if arm not in records]
            if absent:
                missing.append({"cell": list(cell), "contrast": contrast, "missing_arms": absent})
                continue
            try:
                rv, cv, issues = assert_common_query(records[reference], records[candidate], dataset)
            except (KeyError, ValueError) as exc:
                excluded.append({"cell": list(cell), "contrast": contrast, "reason": str(exc)})
                continue
            notes.extend(issues)
            matched[contrast] += 1
            for pid in sorted(rv["rows"]):
                for metric in METRICS[dataset]:
                    r, c = rv["rows"][pid].get(metric), cv["rows"][pid].get(metric)
                    if r is None or c is None or not math.isfinite(r) or not math.isfinite(c):
                        excluded.append({"cell": list(cell), "contrast": contrast, "identity": pid,
                                         "metric": metric, "reason": "missing or nonfinite endpoint"})
                        continue
                    delta = r - c if A.DIRECTION[metric] == "lower" else c - r
                    values[metric][contrast][pid].append(float(delta))
    collapsed = {metric: {contrast: {pid: float(np.mean(v)) for pid, v in people.items()}
                         for contrast, people in contrasts.items()} for metric, contrasts in values.items()}
    counts = {metric: {contrast: {pid: len(v) for pid, v in people.items()}
                      for contrast, people in contrasts.items()} for metric, contrasts in values.items()}
    return collapsed, {"matched_cells": dict(matched), "missing": missing, "excluded": excluded,
                       "notes": sorted(set(notes)), "identity_cell_counts": counts}


def run():
    plan, plan_sha = W.open_plan()
    registration = json.loads(SEAL.read_text())
    if W.sha(SEAL) != SEAL.with_suffix(".sha256").read_text().strip():
        raise ValueError("analysis seal mismatch")
    if registration["training_plan_sha256"] != plan_sha or registration["code_hashes"] != code_hashes():
        raise ValueError("analysis/training source drift")
    by_dataset = {dataset: defaultdict(dict) for dataset in METRICS}
    sources, complete, failed = {}, Counter(), []
    for unit in plan["units"]:
        if unit["stage"] != "target":
            continue
        row, dataset = unit["adapter_row"], unit["dataset"]
        cell = (row["subject_fold"], row["content_fold"])
        records = by_dataset[dataset][cell]
        scratch = unit["scratch_reference"]
        if "S" not in records:
            assert W.sha(scratch["path"]) == scratch["sha256"]
            records["S"] = json.loads(Path(scratch["path"]).read_text())
            sources[scratch["path"]] = scratch["sha256"]
        path = W.OUT / "units" / f'{unit["unit_id"]}.json'
        if not path.exists():
            failure = path.with_name(path.stem + ".FAILED.json")
            if failure.exists():
                failed.append({"unit_id": unit["unit_id"], "failure": json.loads(failure.read_text())})
            continue
        record = json.loads(path.read_text())
        if (record["status"] != "complete" or record["plan_sha256"] != plan_sha or record["arm"] != unit["arm"]
                or record["adapter_row"] != row or record["code_hashes"] != plan["code_hashes"]):
            raise ValueError(f"invalid target record: {unit['unit_id']}")
        records[unit["arm"]] = record
        sources[str(path)] = W.sha(path)
        complete[dataset] += 1
    result = {"format": "ALN35_APWRONG_ANALYSIS_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
              "training_plan_sha256": plan_sha, "analysis_sha256": W.sha(SEAL), "code_hashes": code_hashes(),
              "exploratory": True, "complete_target_cells": dict(complete), "expected_target_cells": 50,
              "bootstrap_scope": A.BOOTSTRAP_SCOPE, "source_records": sources, "datasets": {}}
    private = {"datasets": {}, "technical_failures": failed}
    for dataset, cells in by_dataset.items():
        values, coverage = paired_differences(cells, dataset)
        private["datasets"][dataset] = {"paired_identity_differences": values, "coverage": coverage}
        result["datasets"][dataset] = {
            "complete_target_cells": complete[dataset], "matched_cells": coverage["matched_cells"],
            "missing_cells": coverage["missing"], "excluded_count": len(coverage["excluded"]),
            "metrics": {metric: {**A.family_stats("S35_AP_WRONG|" + dataset, metric, contrasts,
                                                  simultaneous=True, declared=CONTRASTS),
                                 "direction": A.DIR_TEXT[A.DIRECTION[metric]]}
                        for metric, contrasts in values.items()}}
    W.write(RESULT, result)
    W.write(W.OUT / "analysis/per_identity.json", private)
    render(result)
    print(json.dumps({"status": "PASS", "complete_target_cells": dict(complete), "results": str(RESULT)}), flush=True)


def render(result):
    lines = ["# ALN3.5 matched AP wrong-audio results", "", "Exploratory common-sampler, fixed-h30 comparison; seed3401 only.", "",
             f"Completed target executions: {sum(result['complete_target_cells'].values())}/50.", "",
             "| Dataset | Endpoint | Contrast | Paired people | Effect | Pointwise 95% | Family simultaneous 95% |",
             "|---|---|---|---:|---:|---|---|"]
    for dataset, value in result["datasets"].items():
        for metric, stats in value["metrics"].items():
            for name, member in stats["members"].items():
                point = f"[{member['ci_low']:.5g}, {member['ci_high']:.5g}]" if "ci_low" in member else "pending"
                family = member.get("family_set", {})
                joint = f"[{family['sim_low']:.5g}, {family['sim_high']:.5g}]" if family else "pending"
                effect = f"{member['est']:+.5g}" if "est" in member else "pending"
                lines.append(f"| {dataset} | {metric} | {name} | {member['n_paired']} | {effect} | {point} | {joint} |")
    lines += ["", "Positive effects favour the named candidate: risk is reference minus candidate; AUC is candidate minus reference. Each endpoint is a separate three-contrast family. Cell differences are averaged within people before inference; content folds and this single seed never increase n. Max-t uses the identities common to available contrasts; its n and membership are recorded in JSON.", "",
              "Intervals use 4,000 identity bootstrap replicates, conditional on these fitted donors and targets. Missing and technically invalid pairs are listed; nothing is zero-filled. Original AP/S/XP/J*/XM and their historical full-trajectory results remain unchanged and are not silently substituted for the new equal-budget AP comparator.", "",
              "Beating wrong-audio alone is insufficient evidence of benefit over scratch; read AP−S, APwrong−S and AP−APwrong jointly. Weak or reversed results remain valid within this configuration and do not close the shared sound–EEG research question."]
    path = W.ROOT / "docs/auditory_alignment_v3/aln35/AP_WRONG_RESULTS.md"
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
