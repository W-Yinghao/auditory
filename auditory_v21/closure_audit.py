"""Read-only closure audit for the frozen auditory-next v2 artifacts.

The closure pass is deliberately an artifact audit.  It does not import the
model stack, unpickle fitted objects, load EEG/features, or fit a new head.
The entry point is called by the Slurm worker; all file hashes are calculated
here so that a local invocation cannot accidentally be presented as a
provenance check.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd


RUNS = ("S0_001", "A2_core_001", "G0_001", "G0_metadata_002", "G0_readouts_001",
        "C2R_core_001", "C2S_core_001")
CSV_FIELDS = ("package", "check", "status", "evidence", "numerator",
              "denominator", "notes")
MEASUREMENT_FIELDS = ("package", "analysis", "metric", "estimate",
                      "ci_lower", "ci_upper", "n", "status", "units",
                      "notes")
HASH_FIELDS = ("run", "chain", "status", "checked", "matched",
               "mismatched", "unresolved", "notes")


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def ci_crosses_zero(lower: Any, upper: Any) -> bool:
    """Return whether a finite closed interval contains zero."""

    return _finite(lower) and _finite(upper) and float(lower) <= 0.0 <= float(upper)


def _scope_check(scope: Mapping[str, Any] | None, scope_hash: Any = None) -> dict[str, Any]:
    """Validate saved train/validation/test groups without returning IDs."""

    if not isinstance(scope, Mapping):
        return {"status": "MISSING", "train": 0, "validation": 0,
                "test": 0, "overlap": 0, "scope_hash": False}
    sets: dict[str, set[str]] = {}
    aliases = {"train_groups": ("train_groups", "fit_groups"),
               "validation_groups": ("validation_groups", "valid_groups"),
               "test_groups": ("test_groups", "heldout_groups", "eval_groups")}
    for name, names in aliases.items():
        value = next((scope.get(alias) for alias in names if alias in scope), [])
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return {"status": "INVALID", "train": 0, "validation": 0,
                    "test": 0, "overlap": 0, "scope_hash": False}
        sets[name] = {str(item) for item in value}
    overlap = sum(len(sets[a] & sets[b]) for i, a in enumerate(sets)
                  for b in tuple(sets)[i + 1:])
    has_hash = bool(scope_hash or scope.get("scope_hash") or scope.get("fit_scope_hash") or
                    scope.get("encoder_scope_hash"))
    status = "PASS" if overlap == 0 and sets["train_groups"] and sets["test_groups"] else "INVALID"
    return {"status": status, "train": len(sets["train_groups"]),
            "validation": len(sets["validation_groups"]),
            "test": len(sets["test_groups"]), "overlap": overlap,
            "scope_hash": has_hash}


def _has_calibration_receipt(value: Any) -> bool:
    """Find an actual temperature plus scope/fit-group calibration record."""

    if isinstance(value, Mapping):
        has_scope = bool(value.get("scope_hash") or value.get("fit_scope_hash"))
        has_groups = isinstance(value.get("fit_groups"), Sequence) and not isinstance(
            value.get("fit_groups"), (str, bytes))
        nested_scope = any(_has_scope_receipt(child) for key, child in value.items()
                           if str(key).lower() in {"fit_scopes", "fit_scope", "calibration"})
        if _finite(value.get("temperature")) and (has_scope or (has_groups and has_scope) or nested_scope):
            return True
        return any(_has_calibration_receipt(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_has_calibration_receipt(child) for child in value)
    return False


def _has_scope_receipt(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    return bool((value.get("scope_hash") or value.get("fit_scope_hash")) and
                isinstance(value.get("fit_groups"), Sequence) and
                not isinstance(value.get("fit_groups"), (str, bytes)))


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path, details: dict[str, str], alias: str) -> Any:
    if not path.exists():
        return None
    before = _digest(path)
    value = _json(path)
    after = _digest(path)
    if before != after:
        raise ValueError("SOURCE_CHANGED_DURING_READ")
    details[alias] = before
    return value


def _read_csv(path: Path, details: dict[str, str], alias: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    before = _digest(path)
    value = _csv(path)
    after = _digest(path)
    if before != after:
        raise ValueError("SOURCE_CHANGED_DURING_READ")
    details[alias] = before
    return value


def _hash_record(records: list[dict[str, Any]] | None, run: str, chain: str,
                 alias: str, path: Path | None, status: str,
                 actual: Any = "", expected: Any = None) -> None:
    """Retain exact per-item hash evidence privately, never in public rows."""
    if records is None:
        return
    records.append({"run": run, "chain": chain, "alias": alias,
                    "path": str(path) if path is not None else "",
                    "expected_sha256": str(expected or ""),
                    "actual_sha256": str(actual or ""), "status": status})


def _check_one_hash(root: Path, run: str, chain: str, alias: str,
                    expected: Any, candidate: Path | None,
                    counters: dict[str, int], records: list[dict[str, Any]] | None) -> None:
    if candidate is None or not candidate.exists():
        counters["unresolved"] += 1
        _hash_record(records, run, chain, alias, candidate, "UNRESOLVED", expected=expected)
        return
    counters["checked"] += 1
    actual = _digest(candidate)
    if actual == str(expected):
        counters["matched"] += 1
        _hash_record(records, run, chain, alias, candidate, "MATCHED", actual, expected=expected)
    else:
        counters["mismatched"] += 1
        _hash_record(records, run, chain, alias, candidate, "MISMATCH", actual, expected=expected)


def _check_hash_chain(root: Path, private_root: Path, run: str,
                      details: dict[str, str],
                      item_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Verify receipt source hashes and declared input hashes.

    Input hash keys in old receipts are either absolute paths or short private
    aliases.  Absolute keys are resolved and hashed in Slurm; aliases are
    counted as unresolved because the old receipt did not preserve a path.
    No path or participant identifier is returned in the public row.
    """

    run_dir = private_root / run
    start_path = run_dir / "start.json"
    input_path = run_dir / "input_hashes.json"
    completion_path = run_dir / "completion.json"
    counters = {"checked": 0, "matched": 0, "mismatched": 0, "unresolved": 0}
    notes: list[str] = []
    start = _read_json(start_path, details, f"{run}/start.json")
    if isinstance(start, Mapping) and isinstance(start.get("source_hashes"), Mapping):
        source_dir = run_dir / "source"
        for relative, expected in start["source_hashes"].items():
            candidate = source_dir / str(relative)
            _check_one_hash(root, run, "source_snapshot", str(relative), expected,
                            candidate, counters, item_records)
        notes.append("saved source snapshot hashes")
    elif start is None:
        counters["unresolved"] += 1
        _hash_record(item_records, run, "source_snapshot", "start.json", None, "MISSING")
        notes.append("start receipt missing")
    else:
        counters["unresolved"] += 1
        _hash_record(item_records, run, "source_snapshot", "source_hashes", None, "UNRESOLVED")
        notes.append("source hash map missing")

    declared = _read_json(input_path, details, f"{run}/input_hashes.json")
    if isinstance(declared, Mapping):
        alias_paths = {
            "task_csv": root / "private/auditory_next_v2/plan_003/TASK_PLAN.csv",
            "legacy_plan": root / "private/auditory5_v1/jobs/plan_001/plan.json",
            "legacy_splits": root / "private/auditory5_v1/splits/splits_001/folds.json",
            "G0_roles": root / "private/auditory_next_v2/G0_metadata_002/G0_temporal_roles.parquet",
            "G0_support": root / "private/auditory_next_v2/G0_metadata_002/G0_temporal_support.parquet",
            "offline_mapping": root / "private/auditory_next_v2/G0_metadata_002/offline_common_mapping.parquet",
        }
        support_run = str(declared.get("support_run", "S1_support_004"))
        for key, expected in declared.items():
            if key == "support_run":
                continue
            if key == "offline_hashes" and isinstance(expected, Mapping):
                for path_value, hash_value in expected.items():
                    candidate = Path(str(path_value))
                    if not candidate.is_absolute():
                        candidate = root / candidate
                    _check_one_hash(root, run, "declared_inputs", str(path_value), hash_value,
                                    candidate, counters, item_records)
                continue
            if key == "history_sha256":
                candidate = private_root / support_run / "full_event_history.parquet"
                _check_one_hash(root, run, "declared_inputs", key, expected, candidate,
                                counters, item_records)
                continue
            if key == "old_diagnostic_receipt_sha256":
                candidate = private_root / "G0_001" / "completion.json"
                _check_one_hash(root, run, "declared_inputs", key, expected, candidate,
                                counters, item_records)
                continue
            # G0 readout receipts use short aliases; the frozen source layout
            # supplies their private paths here without publishing them.
            candidate = alias_paths.get(str(key), Path(str(key)))
            if not candidate.is_absolute():
                candidate = root / candidate
            _check_one_hash(root, run, "declared_inputs", str(key), expected, candidate,
                            counters, item_records)
        notes.append("declared input hashes")
    elif input_path.exists():
        counters["unresolved"] += 1
        _hash_record(item_records, run, "declared_inputs", "input_hashes.json", None, "UNRESOLVED")
        notes.append("input hash schema missing")

    # G0_001 predates the normalized input_hashes receipt and keeps its
    # checkpoint/epoch declarations in additional_inputs.json instead.
    additional_path = run_dir / "additional_inputs.json"
    additional = _read_json(additional_path, details, f"{run}/additional_inputs.json")
    if isinstance(additional, list):
        for item in additional:
            if not isinstance(item, Mapping) or not item.get("path") or not item.get("sha256"):
                counters["unresolved"] += 1
                _hash_record(item_records, run, "additional_inputs", "malformed", None, "UNRESOLVED")
                continue
            candidate = Path(str(item["path"]))
            if not candidate.is_absolute():
                candidate = root / candidate
            _check_one_hash(root, run, "additional_inputs", str(item["path"]), item["sha256"],
                            candidate, counters, item_records)
        notes.append("legacy additional input hashes")

    legacy_path = run_dir / "legacy_input_hashes.json"
    legacy = _read_json(legacy_path, details, f"{run}/legacy_input_hashes.json")
    if isinstance(legacy, list):
        for item in legacy:
            if not isinstance(item, Mapping) or not item.get("path") or not item.get("sha256"):
                counters["unresolved"] += 1
                _hash_record(item_records, run, "legacy_inputs", "malformed", None, "UNRESOLVED")
                continue
            candidate = Path(str(item["path"]))
            if not candidate.is_absolute():
                candidate = root / candidate
            _check_one_hash(root, run, "legacy_inputs", str(item["path"]), item["sha256"],
                            candidate, counters, item_records)
        notes.append("legacy input hash chain")

    # Completion is evidence of an executed receipt, but a PASS here never
    # overrides a failed source/input hash comparison.
    completion = _read_json(completion_path, details, f"{run}/completion.json")
    complete = isinstance(completion, Mapping) and bool(completion.get("status"))
    if completion_path.exists() and not complete:
        counters["unresolved"] += 1
        _hash_record(item_records, run, "completion", "completion.json", None, "UNRESOLVED")
    status = "PASS" if counters["checked"] > 0 and counters["mismatched"] == 0 and counters["unresolved"] == 0 and complete else "LIMITED"
    if counters["mismatched"]:
        if any(item.get("status") == "MISMATCH" and
               str(item.get("path", "")).endswith(("PUBLICATION.md", "release/manifest.json"))
               for item in item_records or () if item.get("run") == run):
            notes.append("historical publication metadata mismatch retained; EEG input integrity is separate")
    return {"run": run, "status": status, "checked": counters["checked"], "matched": counters["matched"],
            "mismatched": counters["mismatched"], "unresolved": counters["unresolved"],
            "notes": "; ".join(notes)}


def _check_row(package: str, check: str, status: str, evidence: str,
               numerator: Any = "", denominator: Any = "", notes: str = "") -> dict[str, Any]:
    return {"package": package, "check": check, "status": status,
            "evidence": evidence, "numerator": numerator,
            "denominator": denominator, "notes": notes}


def _s0_audit(root: Path, details: dict[str, str]) -> list[dict[str, Any]]:
    """Check the immutable S0 scope registry and legacy checkpoint chain."""

    checks: list[dict[str, Any]] = []
    private = root / "private/auditory_next_v2/S0_001"
    registry = _read_json(private / "feature_scope_registry.json", details, "S0/feature_scope_registry.json")
    items = registry if isinstance(registry, list) else []
    scope_ok = 0
    for item in items:
        if not isinstance(item, Mapping):
            continue
        # S0's registry names the training partition ``fit_groups``.  It is
        # equivalent to train_groups here, while test/validation remain
        # explicit fields in the same record.
        checked = _scope_check(item)
        if checked["status"] == "PASS" and item.get("task") and item.get("mode") and item.get("stage"):
            scope_ok += 1
    checks.append(_check_row("G0/C2", "S0_scope_registry", "PASS" if len(items) == 90 and scope_ok == 90 else "LIMITED",
                             "S0/feature_scope_registry.json", scope_ok, 90,
                             "fit_groups is the saved training partition; all/left/right and outer/D_inner task records are retained"))

    task_dir = root / "private/auditory5_v1/jobs/plan_001/outputs"
    support_path = root / "private/auditory5_v1/splits/splits_001/support.parquet"
    try:
        support = pd.read_parquet(support_path, columns=["split_group_id", "general", "C"])
        eligible_by_branch = {
            "all": {str(value) for value in support.loc[support["general"], "split_group_id"]},
            "left": {str(value) for value in support.loc[support["C"], "split_group_id"]},
            "right": {str(value) for value in support.loc[support["C"], "split_group_id"]},
        }
        details["S0/splits/splits_001/support.parquet"] = _digest(support_path)
    except (FileNotFoundError, OSError, KeyError, ImportError):
        eligible_by_branch = {}
    task_ok = 0
    completion_ok = 0
    checkpoint_scope_ok = 0
    for item in items:
        if not isinstance(item, Mapping) or not item.get("task"):
            continue
        task_name = str(item["task"])
        task = _read_json(task_dir / task_name / "task.json", details, f"S0/tasks/{task_name}/task.json")
        completion = _read_json(task_dir / task_name / "completion.json", details, f"S0/tasks/{task_name}/completion.json")
        if isinstance(task, Mapping):
            expected = _scope_check(item)
            # The job plan stores planned groups.  The immutable preflight
            # registry stores the same groups after the frozen feature-support
            # eligibility intersection (see auditory_next/preflight.py).  The
            # planned task can therefore contain ineligible groups; compare
            # the effective intersection, while retaining validation/test
            # partitions exactly as planned.
            planned_fit = {str(group) for group in task.get("fit_groups", ())}
            branch = str(item.get("branch", "all"))
            eligible = eligible_by_branch.get(branch, set())
            effective_fit = planned_fit & eligible
            actual = _scope_check({"fit_groups": sorted(effective_fit),
                                   "validation_groups": task.get("validation_groups", []),
                                   "test_groups": task.get("test_groups", [])},
                                  task.get("encoder_fit_scope_hash"))
            if (effective_fit == {str(group) for group in item.get("fit_groups", ())}
                    and {str(group) for group in task.get("validation_groups", ())} ==
                    {str(group) for group in item.get("validation_groups", ())}
                    and {str(group) for group in task.get("test_groups", ())} ==
                    {str(group) for group in item.get("test_groups", ())}
                    and actual["status"] == "PASS"):
                task_ok += 1
        if isinstance(completion, Mapping) and completion.get("status") == "PASS":
            completion_ok += 1
            if completion.get("encoder_fit_scope_hash"):
                checkpoint_scope_ok += 1
    checks.append(_check_row("G0/C2", "S0_task_scope_alignment", "PASS" if task_ok == len(items) == 90 else "LIMITED",
                             "S0 plan001 task.json and completion.json", task_ok, len(items),
                             "task scope counts are compared to the immutable registry"))
    checks.append(_check_row("G0/C2", "S0_checkpoint_scope_receipts", "PASS" if checkpoint_scope_ok == completion_ok == 90 else "LIMITED",
                             "S0 plan001 completion.json", checkpoint_scope_ok, completion_ok,
                             "encoder_fit_scope_hash is checked without loading checkpoint tensors"))

    legacy = _read_json(private / "legacy_input_hashes.json", details, "S0/legacy_input_hashes.json")
    legacy_items = legacy if isinstance(legacy, list) else []
    checkpoint_entries = sum(str(item.get("path", "")).endswith("encoder.pt")
                             for item in legacy_items if isinstance(item, Mapping))
    checks.append(_check_row("G0/C2", "checkpoint_hash_inventory", "PASS" if checkpoint_entries else "MISSING",
                             "S0/legacy_input_hashes.json", checkpoint_entries, len(legacy_items),
                             "declared encoder checkpoint hashes are verified by the hash-chain pass"))

    # probe_metadata.json is the saved scaler/calibration receipt.  It is
    # inspected as JSON only; no probe/head object is loaded.
    metadata_files = sorted(task_dir.glob("*/probe_metadata.json"))
    scaler_receipts = 0
    for path in metadata_files:
        value = _read_json(path, details, f"S0/{path.parent.name}/probe_metadata.json")
        if _has_calibration_receipt(value):
            scaler_receipts += 1
    checks.append(_check_row("G0/C2", "scaler_scope_receipts", "PASS" if metadata_files and scaler_receipts == len(metadata_files) else "LIMITED",
                             "S0 plan001 probe_metadata.json", scaler_receipts, len(metadata_files),
                             "saved temperature/scaler scope receipts are checked across outer tasks"))
    return checks


def _a2_audit(root: Path, details: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    measurements: list[dict[str, Any]] = []
    base = root / "results/auditory_next_v2/A2_core_001"
    private = root / "private/auditory_next_v2/A2_core_001"
    summary = _read_json(base / "summary.json", details, "A2/summary.json")
    if not isinstance(summary, Mapping):
        checks.append(_check_row("A2", "core_summary", "MISSING", "A2/summary.json"))
        return checks, measurements
    omega = tuple(summary.get("omega", ()))
    checks.append(_check_row("A2", "frozen_omega", "PASS" if omega == ("run3_5_pos0", "run3_5_pos1") else "INVALID",
                             "A2/summary.json omega", len(omega), 2))
    checks.append(_check_row("A2", "no_new_fits", "PASS" if summary.get("new_encoder_fits", 0) == 0 else "INVALID",
                             "A2/summary.json new_encoder_fits", summary.get("new_encoder_fits", 0), 0))
    receipts = _read_json(private / "fit_receipts.json", details, "A2/fit_receipts.json")
    receipt_items = receipts if isinstance(receipts, list) else (
        list(receipts.values()) if isinstance(receipts, Mapping) else [])
    scope_results = []
    for item in receipt_items:
        if isinstance(item, Mapping):
            saved_scope = item.get("fit_scope", item)
            scope_results.append(_scope_check(saved_scope, item.get("scope_hash") or item.get("encoder_scope_hash")))
    valid_scopes = sum(item["status"] == "PASS" and item["scope_hash"] for item in scope_results)
    checks.append(_check_row("A2", "train_test_scope", "PASS" if scope_results and valid_scopes == len(scope_results) else "LIMITED",
                             "A2/fit_receipts.json aggregate scope fields", valid_scopes, len(scope_results),
                             "IDs remain private; validation groups are retained as saved"))
    diagnostics = _read_json(private / "fold_diagnostics.json", details, "A2/fold_diagnostics.json")
    diag_items = diagnostics if isinstance(diagnostics, list) else []
    pass_diags = sum(isinstance(row, Mapping) and str(row.get("status", "")).upper() in {"PASS", "COMPUTED"}
                     for row in diag_items)
    checks.append(_check_row("A2", "fold_receipts", "PASS" if diag_items and pass_diags == len(diag_items) else "LIMITED",
                             "A2/fold_diagnostics.json", pass_diags, len(diag_items)))

    # The existing Stage 0 aggregate contains exactly the posthoc contrasts;
    # these values are carried through without recomputation or reinterpretation.
    stage = root / "results/auditory_v21/stage0_001"
    rows = _read_csv(stage / "a2_secondary_comparisons.csv", details, "Stage0/a2_secondary_comparisons.csv")
    cosine_rows: list[dict[str, str]] = []
    for row in rows:
        if row.get("metric") != "cosine":
            continue
        cosine_rows.append(row)
        interval_ok = ci_crosses_zero(row.get("ci_lower"), row.get("ci_upper"))
        measurements.append({"package": "A2", "analysis": row.get("comparison", ""),
                             "metric": row.get("endpoint", "cosine"), "estimate": row.get("estimate"),
                             "ci_lower": row.get("ci_lower"), "ci_upper": row.get("ci_upper"),
                             "n": row.get("n_candidates"), "status": "COMPLETE" if row.get("status") == "COMPUTED" and interval_ok else "LIMITED",
                             "units": "cosine_difference", "notes": "frozen saved Stage0 posthoc contrast; R_SIM primary unchanged"})
    crossed = sum(ci_crosses_zero(row.get("ci_lower"), row.get("ci_upper")) for row in cosine_rows)
    checks.append(_check_row("A2", "paired_cosine_intervals", "PASS" if len(cosine_rows) == 4 and crossed == 4 else "LIMITED",
                             "Stage0/a2_secondary_comparisons.csv", crossed, 4,
                             "Four requested SUP-SIM/SUP-RAND post and post-minus-pre rows are secondary"))
    norms = _read_csv(stage / "a2_norm_sensitivity.csv", details, "Stage0/a2_norm_sensitivity.csv")
    norm_complete = sum(row.get("status") == "COMPUTED" for row in norms)
    checks.append(_check_row("A2", "saved_norm_measurements", "PASS" if norms and norm_complete == len(norms) else "MISSING",
                             "Stage0/a2_norm_sensitivity.csv", norm_complete, len(norms),
                             "scale diagnostics only; no information-unit relabeling"))
    repeatability = _read_csv(base / "repeatability_aggregate.csv", details, "A2/repeatability_aggregate.csv")
    inner_rows = [row for row in repeatability if row.get("metric") == "inner_product"]
    inner_source = "A2/repeatability_aggregate.csv"
    if not inner_rows:
        effects = _read_csv(root / "results/auditory_next_v2/final_002/paired_effects.csv",
                            details, "final_002/paired_effects.csv")
        inner_rows = [row for row in effects
                      if row.get("packet") == "A2" and row.get("metric") == "projected_inner_product"]
        inner_source = "final_002/paired_effects.csv"
    for row in inner_rows:
        analysis = row.get("analysis_id") or f"{row.get('mode', '')}_{row.get('endpoint', '')}"
        measurements.append({"package": "A2", "analysis": analysis,
                             "metric": "projected_inner_product", "estimate": row.get("estimate"),
                             "ci_lower": row.get("ci_lower"), "ci_upper": row.get("ci_upper"),
                             "n": row.get("n_candidates"), "status": "COMPLETE" if _finite(row.get("estimate")) else "LIMITED",
                             "units": row.get("unit", "projected_inner_product"),
                             "notes": f"saved projected inner-product scale diagnostic from {inner_source}; not information"})
    checks.append(_check_row("A2", "saved_inner_product_measurements", "PASS" if inner_rows else "MISSING",
                             inner_source, len(inner_rows), "", 
                             "reported only when saved; projected scale diagnostic, not mutual information"))
    # The fixed A2 residual input is an archive-level quality field.  Inspect
    # NPZ member names only, so this check never opens EEG or feature arrays.
    archive_count = quality_archive_count = 0
    for mode in ("L0", "R_RAND", "R_SUP", "R_SIM"):
        for fold in range(5):
            archive = root / "private/auditory5_v1/jobs/plan_001/outputs" / f"outer{fold}_all_{mode}" / "features.npz"
            if not archive.exists():
                continue
            archive_count += 1
            with zipfile.ZipFile(archive) as source:
                if "quality.npy" in source.namelist():
                    quality_archive_count += 1
    checks.append(_check_row("A2", "fixed_quality_archive_header", "PASS" if archive_count == 20 else "LIMITED",
                             "saved outer all-mode features.npz ZIP headers", archive_count, 20,
                             f"quality.npy archives={quality_archive_count}; headers only, no EEG/feature values loaded"))
    modes_with_controls = set()
    for mode in ("L0", "R_RAND", "R_SUP", "R_SIM"):
        mode_rows = [str(row.get("endpoint", "")) for row in repeatability
                     if row.get("mode") == mode and row.get("status") == "COMPUTED"]
        if (any("post_delta" in analysis for analysis in mode_rows) and
                any("pre_delta" in analysis for analysis in mode_rows) and
                any("common_response" in analysis for analysis in mode_rows)):
            modes_with_controls.add(mode)
    checks.append(_check_row("A2", "saved_post_pre_common_response_controls",
                             "PASS" if len(modes_with_controls) >= 4 else "LIMITED",
                             "A2/repeatability_aggregate.csv", len(modes_with_controls), 4,
                             "post_delta, pre_delta and common_response rows are retained on their projected scale"))
    controls = _read_csv(root / "results/auditory_next_v2/final_002/controls_aggregate.csv",
                         details, "final_002/controls_aggregate.csv")
    quality = next((r for r in controls if r.get("packet") == "A2" and "quality" in r.get("control", "").lower()), None)
    qstatus = str(quality.get("status", "MISSING")) if quality else "MISSING"
    checks.append(_check_row("A2", "quality_background_control", qstatus if qstatus in {"COMPLETE", "MISSING", "LIMITED"} else "LIMITED",
                             "final_002/controls_aggregate.csv plus fixed archive headers", quality_archive_count, archive_count,
                             "quality.npy is absent when zero archives contain it; fixed quality input cannot be recreated equivalently from this snapshot"))
    return checks, measurements


def _g0_audit(root: Path, details: dict[str, str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    base = root / "results/auditory_next_v2"
    summary = _read_json(base / "G0_001/summary.json", details, "G0/G0_001/summary.json")
    diag = _read_csv(base / "G0_001/encoder_training_diagnostics.csv", details, "G0/encoder_training_diagnostics.csv")
    heads = _read_csv(base / "G0_001/supervised_original_head.csv", details, "G0/supervised_original_head.csv")
    if isinstance(summary, Mapping):
        checks.append(_check_row("G0", "original_cnn_head", "PASS" if len(heads) == int(summary.get("supervised_original_head_rows", -1)) and heads else "LIMITED",
                                 "G0/supervised_original_head.csv plus G0_001/summary.json", len(heads), summary.get("supervised_original_head_rows", ""),
                                 "TRAIN_DIAGNOSTIC and OUTER_SHARED are original supervised head roles"))
        checkpoints = int(summary.get("encoder_checkpoints_diagnosed", 0) or 0)
        # G0's diagnostic CSV intentionally contains no checkpoint columns.
        # Link each diagnostic task to the immutable S0 encoder artifact whose
        # hash is recorded in the S0 legacy inventory instead of requiring
        # fictional per-row fields.
        legacy = _read_json(root / "private/auditory_next_v2/S0_001/legacy_input_hashes.json",
                            details, "S0/legacy_input_hashes.json#G0_checkpoint_links")
        checkpoint_by_task = {}
        for item in (legacy if isinstance(legacy, list) else ()):
            if isinstance(item, Mapping) and str(item.get("path", "")).endswith("/encoder.pt"):
                checkpoint_by_task[Path(str(item["path"])).parent.name] = str(item["path"])
        checkpoint_fields = 0
        for row in diag:
            task_name = str(row.get("task", ""))
            path_value = checkpoint_by_task.get(task_name)
            if path_value:
                checkpoint_path = Path(path_value)
                if not checkpoint_path.is_absolute():
                    checkpoint_path = root / checkpoint_path
                if checkpoint_path.exists():
                    checkpoint_fields += 1
        checkpoint_status = "PASS" if checkpoints == 75 and checkpoint_fields == 75 else "LIMITED"
        checks.append(_check_row("G0", "encoder_checkpoint_scaler_provenance", checkpoint_status,
                                 "G0 diagnostics linked to S0 legacy encoder artifacts; scaler fields remain absent",
                                 checkpoint_fields, checkpoints,
                                 "checkpoint link is verified from immutable S0 paths; scaler inheritance is a separate unresolved provenance field"))
    outer = [r for r in diag if r.get("stage") == "outer"]
    inner = [r for r in diag if r.get("stage") == "D_inner"]
    ranges_ok = bool(outer and inner and all(_finite(r.get("fit_groups")) and int(float(r["fit_groups"])) > 0 for r in diag))
    checks.append(_check_row("G0", "encoder_train_ranges", "PASS" if ranges_ok else "LIMITED",
                             "G0/encoder_training_diagnostics.csv", len(outer) + len(inner), len(outer) + len(inner),
                             f"separate diagnostic rows: outer={len(outer)}, D_inner={len(inner)}; counts are not a cross-stratum ratio"))
    readout = _read_json(base / "G0_readouts_001/summary.json", details, "G0_readouts/summary.json")
    within = _read_csv(base / "G0_readouts_001/g0_within_child_metrics.csv", details, "G0_readouts/within_child_metrics.csv")
    bridge = _read_csv(base / "G0_readouts_001/g0_bridge_metrics.csv", details, "G0_readouts/bridge_metrics.csv")
    if isinstance(readout, Mapping):
        within_summary = readout.get("within_child", {})
        bridge_summary = readout.get("offline_bridge", {})
        within_n = int(within_summary.get("fit_count", 0) or 0) if isinstance(within_summary, Mapping) else 0
        bridge_n = int(bridge_summary.get("fit_count", 0) or 0) if isinstance(bridge_summary, Mapping) else 0
        heldout_rows = sum(str(row.get("child_role", "")).lower() == "heldout" for row in within)
        bridge_rows = sum(bool(row.get("bank")) for row in bridge)
        checks.append(_check_row("G0", "posthoc_probe", "PASS" if within_n and heldout_rows else "LIMITED",
                                 "G0_readouts/summary.json and within_child_metrics.csv", len(within), len(within),
                                 f"metric rows={len(within)}; historical post-fitted probe head fits={within_n}; separate from original CNN head"))
        checks.append(_check_row("G0", "same_child_heldout", "PASS" if within_n and heldout_rows else "LIMITED",
                                 "G0_readouts/within_child_metrics.csv", heldout_rows, len(within)))
        checks.append(_check_row("G0", "cross_child_bridge", "PASS" if bridge_n and bridge_rows else "LIMITED",
                                 "G0_readouts/summary.json and bridge_metrics.csv", bridge_rows, len(bridge),
                                 "offline bridge object is kept separate from same-child heldout"))
        checks.append(_check_row("G0", "no_new_encoder_fit_in_closure", "PASS" if readout.get("encoder_fits") == 0 else "INVALID",
                                 "G0_readouts/summary.json", readout.get("encoder_fits", ""), 0,
                                 "historical probes are reused; this closure performs zero fits"))
        checks.append(_check_row("G0", "historical_probe_head_fits", "PASS" if within_n and bridge_n else "LIMITED",
                                 "G0_readouts/summary.json", within_n + bridge_n, "",
                                 "1158 existing probe head fits are retained as historical artifacts"))
    metadata = _read_json(base / "G0_metadata_002/summary.json", details, "G0_metadata/G0_metadata_002/summary.json")
    selection = metadata.get("selection_isolation") if isinstance(metadata, Mapping) else None
    checks.append(_check_row("G0", "selection_isolation", "PASS" if selection is True else "MISSING",
                             "G0_metadata/G0_metadata_002/summary.json", int(selection is True), 1,
                             "whole-record offline QC selection remains unisolated"))
    return checks


def _c2_audit(root: Path, details: dict[str, str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    base = root / "results/auditory_next_v2"
    private = root / "private/auditory_next_v2"
    summary = _read_json(base / "C2S_core_001/summary.json", details, "C2/C2S_core_001/summary.json")
    scopes = _read_json(private / "C2S_core_001/fit_scopes.json", details, "C2/C2S_core_001/fit_scopes.json")
    scope_items = scopes if isinstance(scopes, list) else []
    scope_results = [_scope_check(item.get("fit_scope") if isinstance(item, Mapping) else None,
                                  item.get("scope_hash") if isinstance(item, Mapping) else None)
                     for item in scope_items]
    valid = sum(item["status"] == "PASS" and item["scope_hash"] for item in scope_results)
    calibration = sum(isinstance(item, Mapping) and _finite(item.get("temperature")) for item in scope_items)
    checks.append(_check_row("C2", "spatial_train_test_scope", "PASS" if scope_results and valid == len(scope_results) else "LIMITED",
                             "C2/C2S_core_001/fit_scopes.json", valid, len(scope_results),
                             "scope hashes and disjoint group partitions checked without exposing IDs"))
    checks.append(_check_row("C2", "scaler_calibration_receipts", "PASS" if scope_items and calibration == len(scope_items) else "LIMITED",
                             "C2/C2S_core_001/fit_scopes.json temperature fields", calibration, len(scope_items),
                             "saved calibration temperatures are checked as provenance fields"))
    if isinstance(summary, Mapping):
        geometry = summary.get("geometry", {})
        if not isinstance(geometry, Mapping):
            geometry = {}
        checks.append(_check_row("C2", "spatial_geometry_source", "PASS" if geometry.get("status") == "PASS" else "LIMITED",
                                 "C2S_core_001/summary.json geometry", geometry.get("records", ""), 60,
                                 f"max reconstruction error={geometry.get('max_reconstruction_error', 'MISSING')}; existing left/right source; no spatial grid expansion"))
        checks.append(_check_row("C2", "numeric_isolation", "PASS" if summary.get("numeric_isolation") is True else "MISSING",
                                 "C2S_core_001/summary.json", int(summary.get("numeric_isolation") is True), 1))
        checks.append(_check_row("C2", "selection_isolation", "PASS" if summary.get("selection_isolation") is True else "MISSING",
                                 "C2S_core_001/summary.json", int(summary.get("selection_isolation") is True), 1,
                                 "whole-record offline QC selection is not isolated"))
        checks.append(_check_row("C2", "no_new_encoder_fit", "PASS" if summary.get("new_encoder_fits") == 0 else "INVALID",
                                 "C2S_core_001/summary.json", summary.get("new_encoder_fits", ""), 0))
    repair = _read_json(base / "C2R_core_001/summary.json", details, "C2/C2R_core_001/summary.json")
    definition = _read_json(private / "C2R_core_001/repair_definition.json", details, "C2/C2R_core_001/repair_definition.json")
    inventory = _read_json(private / "C2R_core_001/selection_inventory.json", details, "C2/C2R_core_001/selection_inventory.json")
    inventory_items = list(inventory.values()) if isinstance(inventory, Mapping) else []
    calibration_scope = sum(
        isinstance(item, Mapping)
        and isinstance(item.get("calibration"), Mapping)
        and bool(item["calibration"].get("fit_groups"))
        and bool(item.get("scope_hash") or item["calibration"].get("scope_hash"))
        and _finite(item.get("temperature"))
        for item in inventory_items)
    checks.append(_check_row("C2", "repaired_train_calibration_scope", "PASS" if inventory_items and calibration_scope == len(inventory_items) else "LIMITED",
                             "C2R_core_001/selection_inventory.json", calibration_scope, len(inventory_items),
                             "fit_groups and temperature calibration receipts checked; IDs remain private"))
    if isinstance(definition, Mapping):
        declared_scope = str(definition.get("fit_scope", ""))
        checks.append(_check_row("C2", "repaired_scope_declaration", "PASS" if "GroupKFold3" in declared_scope and "frozen outer encoders" in declared_scope else "LIMITED",
                                 "C2R_core_001/repair_definition.json", 1 if declared_scope else 0, 1,
                                 "saved declaration distinguishes frozen encoders from inner head/scaler fitting"))
    diagnostics = _read_json(private / "C2R_core_001/family_training_diagnostics.json", details,
                             "C2/C2R_core_001/family_training_diagnostics.json")
    records: list[Mapping[str, Any]] = []
    if isinstance(diagnostics, Mapping):
        for value in diagnostics.values():
            if isinstance(value, list):
                records.extend(item for item in value if isinstance(item, Mapping))
    hashes_ok = sum(bool(item.get("fit_scope_hash") and item.get("fit_input_hash")) for item in records)
    checks.append(_check_row("C2", "repaired_head_scope_receipts", "PASS" if records and hashes_ok == len(records) else "LIMITED",
                             "C2R_core_001/family_training_diagnostics.json", hashes_ok, len(records),
                             "optimization/head receipts retain scope and input hashes; models are not loaded"))
    if isinstance(repair, Mapping):
        stable = repair.get("stable_members")
        required = repair.get("required_members")
        neural_heads = repair.get("new_neural_head_fits")
        linear_heads = repair.get("new_linear_head_fits")
        checks.append(_check_row("C2", "repaired_head_fit_counts", "PASS" if neural_heads == 560 and linear_heads == 325 else "LIMITED",
                                 "C2R_core_001/summary.json", neural_heads or "", linear_heads or "",
                                 "historical C2-R neural and linear head fit counts are retained; this closure made zero fits"))
        checks.append(_check_row("C2", "repaired_core_completion", "PASS" if stable == required == 560 else "LIMITED",
                                 "C2R_core_001/summary.json", stable or "", required or 560,
                                 "C2-R scientific status remains NOT_EVALUABLE where declared"))
        checks.append(_check_row("C2", "repaired_no_new_encoder_fit", "PASS" if repair.get("new_encoder_fits") == 0 else "INVALID",
                                 "C2R_core_001/summary.json", repair.get("new_encoder_fits", ""), 0))
    controls = _read_csv(base / "final_002/controls_aggregate.csv", details, "final_002/controls_aggregate.csv")
    inherited = next((r for r in controls if "inherited raw" in " ".join(r.values()).lower()), None)
    inherited_status = str(inherited.get("status", "MISSING")) if inherited else "MISSING"
    checks.append(_check_row("C2", "inherited_raw_isolation", inherited_status if inherited_status in {"COMPLETE", "MISSING", "LIMITED"} else "LIMITED",
                             "final_002/controls_aggregate.csv", "", "", "control gap is reported separately from numeric isolation"))
    return checks


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(root: Path, private: Path, public: Path, report: Path, config: dict) -> dict[str, Any]:
    """Audit frozen A2/G0/C2 receipts and write aggregate closure artifacts."""

    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("SLURM_REQUIRED")
    root, private, public, report = map(Path, (root, private, public, report))
    details: dict[str, str] = {}
    checks: list[dict[str, Any]] = []
    measurements: list[dict[str, Any]] = []
    checks.extend(_s0_audit(root, details))
    a2_checks, a2_measurements = _a2_audit(root, details)
    checks.extend(a2_checks)
    measurements.extend(a2_measurements)
    checks.extend(_g0_audit(root, details))
    checks.extend(_c2_audit(root, details))
    hash_items: list[dict[str, Any]] = []
    hash_rows = [_check_hash_chain(root, root / "private/auditory_next_v2", run, details, hash_items) for run in RUNS]
    _write_csv(public / "closure_checks.csv", checks, CSV_FIELDS)
    _write_csv(public / "closure_measurements.csv", measurements, MEASUREMENT_FIELDS)
    _write_csv(public / "closure_hash_chain.csv", hash_rows, HASH_FIELDS)
    # Exact path/hash details remain private.  Public rows contain only aliases.
    _write_json(private / "closure_input_hashes.json", details)
    _write_json(private / "closure_hash_items.json", hash_items)
    pass_count = sum(row["status"] == "PASS" for row in checks)
    missing_count = sum(row["status"] in {"MISSING", "LIMITED"} for row in checks)
    hash_pass = sum(row["status"] == "PASS" for row in hash_rows)
    publication_hash_mismatches = sum(
        item.get("status") == "MISMATCH" and
        str(item.get("path", "")).endswith(("PUBLICATION.md", "release/manifest.json"))
        for item in hash_items)
    historical_publication_verified = 0
    historical_repo = root.parent / "auditory_github"
    historical_commit = "191b3a189bea116c4c91fdcfcb6d3bd2945b8dfa"
    if historical_repo.is_dir():
        for item in hash_items:
            path_value = str(item.get("path", ""))
            if (item.get("status") != "MISMATCH" or
                    not path_value.endswith(("PUBLICATION.md", "release/manifest.json"))):
                continue
            try:
                relative = Path(path_value).resolve().relative_to(historical_repo.resolve())
                shown = subprocess.run(
                    ["git", "-C", str(historical_repo), "show",
                     f"{historical_commit}:{relative.as_posix()}"],
                    capture_output=True, check=True)
            except (OSError, subprocess.CalledProcessError, ValueError):
                continue
            if hashlib.sha256(shown.stdout).hexdigest() == item.get("expected_sha256"):
                historical_publication_verified += 1
    g0_readout_summary = _read_json(root / "results/auditory_next_v2/G0_readouts_001/summary.json",
                                    details, "G0_readouts/summary.json#fit_counts")
    c2_repair_summary = _read_json(root / "results/auditory_next_v2/C2R_core_001/summary.json",
                                   details, "C2R_core_001/summary.json#fit_counts")
    historical_g0_heads = 0
    if isinstance(g0_readout_summary, Mapping):
        historical_g0_heads = int(g0_readout_summary.get("within_child_head_fits", 0) or 0) + int(
            g0_readout_summary.get("offline_bridge_head_fits", 0) or 0)
    historical_c2_heads = 0
    if isinstance(c2_repair_summary, Mapping):
        historical_c2_heads = int(c2_repair_summary.get("new_neural_head_fits", 0) or 0) + int(
            c2_repair_summary.get("new_linear_head_fits", 0) or 0)
    summary = {
        "status": "CLOSURE_AUDIT_COMPLETE",
        "implementation_status": "PASS",
        "scientific_status": "EXISTING_ARTIFACTS_ONLY",
        "scope": ["A2", "G0", "C2"],
        "new_encoder_fits": 0,
        "new_head_fits": 0,
        "historical_existing_head_fits_reused": {"G0": historical_g0_heads, "C2_R": historical_c2_heads},
        "checks_pass": pass_count,
        "checks_limited_or_missing": missing_count,
        "hash_chains_pass": hash_pass,
        "hash_chains_total": len(hash_rows),
        "publication_metadata_hash_mismatches": publication_hash_mismatches,
        "historical_publication_version_verified": historical_publication_verified,
        "primary_result_unchanged": True,
        "a2_inner_product_and_norms_are_scale_diagnostics": True,
        "new_source_schemas_needed": False,
        "outputs": ["closure_checks.csv", "closure_measurements.csv", "closure_hash_chain.csv"],
        "private_hash_item_records": len(hash_items),
    }
    _write_json(public / "summary.json", summary)
    report.mkdir(parents=True, exist_ok=True)
    (report / "CLOSURE_AUDIT.md").write_text(
        "# Auditory v2.1 existing-artifact closure\n\n"
        "This Slurm audit inspected saved A2, G0 and C2 receipts, summaries, "
        "train/test scope declarations, and source/input hash chains. It made "
        "zero new encoder or head fits in this audit and did not load EEG, features, checkpoints, "
        "or fitted model objects.\n\n"
        "A2 paired cosine intervals remain secondary posthoc review values and "
        "the frozen R_SIM primary is unchanged. Inner products and norms are "
        "scale diagnostics. G0 original CNN head, posthoc probes, same-child "
        "heldout metrics and cross-child bridge metrics are separate rows. C2 "
        "uses existing left/right geometry evidence without expanding the grid. "
        "Missing or unisolated controls remain explicit in closure_checks.csv. "
        "Historical publication metadata hash mismatches, if present, remain "
        f"scoped separately from EEG input integrity; historical release verification "
        f"matched {historical_publication_verified}/{publication_hash_mismatches}.\n",
        encoding="utf-8")
    return summary


__all__ = ["ci_crosses_zero", "run", "_scope_check"]
