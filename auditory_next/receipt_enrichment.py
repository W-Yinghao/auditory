"""Receipt-only enrichment for v2 fit accounting.

This sidecar reads the paths already recorded by fit accounting.  It never
opens a model, EEG array, label table, or scheduler receipt.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .fit_accounting import MANDATORY_RECEIPT_FIELDS


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _curve_last(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError, TypeError):
        return {}
    if isinstance(value, list):
        value = value[-1] if value else {}
    return value if isinstance(value, dict) else {}


def _model_digest(unit: Mapping[str, Any]) -> tuple[str | None, str | None]:
    values = [row.get("sha256") for row in unit.get("model_file_digests", [])
              if isinstance(row, Mapping) and row.get("sha256")]
    hashes = unit.get("model_hashes", [])
    hashes = [hashes] if isinstance(hashes, str) else hashes
    values.extend(value for value in hashes if value)
    values = sorted(set(str(value) for value in values))
    if not values:
        return None, None
    if len(values) == 1:
        return values[0], "single_available_artifact"
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest(), "checkpoint_collection"


def enrich_unit(unit: Mapping[str, Any], source_metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return all §15.2 fields plus an origin for each field.

    Receipt files are merged in the supplied order, so completion values win
    over initial/start values.  ``source_metadata`` contains only run-level
    inherited hashes such as ``config_hash`` and ``code_hash``.
    """
    merged: dict[str, Any] = {}
    optimization: dict[str, Any] = {}
    curve: dict[str, Any] = {}
    curve_paths_seen: set[Path] = set()
    receipt_paths = [Path(value) for value in unit.get("receipt_files", [])]
    for path in receipt_paths:
        receipt = _json(path)
        merged.update(receipt)
        if isinstance(receipt.get("optimization"), Mapping):
            optimization.update(receipt["optimization"])
        curve_path = path.with_name("training_curve.json")
        if curve_path.exists() and curve_path not in curve_paths_seen:
            curve.update(_curve_last(curve_path))
            curve_paths_seen.add(curve_path)
    source_metadata = source_metadata or {}
    result: dict[str, Any] = {field: None for field in MANDATORY_RECEIPT_FIELDS}
    result.update({"model_hash_kind": None, "last_observed_objective": None,
                   "last_observed_objective_origin": None})
    origins: dict[str, str] = {field: "unknown" for field in MANDATORY_RECEIPT_FIELDS}

    def native(field: str, *aliases: str) -> None:
        if merged.get(field) not in (None, ""):
            result[field], origins[field] = merged[field], "native"
            return
        for alias in aliases:
            if merged.get(alias) not in (None, ""):
                result[field], origins[field] = merged[alias], f"alias:{alias}"
                return

    for field in MANDATORY_RECEIPT_FIELDS:
        native(field)
    native("training_scope_hash", "scope_hash")
    native("input_hash", "feature_hash")
    native("optimizer_status", "numerical_status")
    native("objective_id", "objective")
    if isinstance(merged.get("scope"), Mapping):
        groups = merged["scope"].get("fit_groups")
        if isinstance(groups, (list, tuple, set)):
            result["n_train_candidates"] = len(set(str(value) for value in groups))
            origins["n_train_candidates"] = "derived:scope.fit_groups_unique"
    if unit.get("source_kind") == "g0_fit_directory" and merged.get("n") not in (None, ""):
        result["n_train_trials_or_bags"] = merged["n"]
        origins["n_train_trials_or_bags"] = "alias:n (G0 training observation count)"
    if merged.get("n_training_observations") not in (None, "") and result["n_train_trials_or_bags"] is None:
        result["n_train_trials_or_bags"] = merged["n_training_observations"]
        origins["n_train_trials_or_bags"] = "alias:n_training_observations"
    if optimization.get("steps") is not None:
        result["step_count"] = optimization["steps"]
        origins["step_count"] = "derived:optimization.steps"
    elif merged.get("steps") is not None:
        result["step_count"] = merged["steps"]
        origins["step_count"] = "alias:steps"
    elif merged.get("iterations") is not None:
        result["step_count"] = merged["iterations"]
        origins["step_count"] = "alias:iterations"
    if curve.get("gradient_norm_unclipped") is not None:
        result["gradient_diagnostic"] = {
            "gradient_norm_unclipped": curve["gradient_norm_unclipped"],
            "timing": "before_update",
        }
        origins["gradient_diagnostic"] = "derived:training_curve_last_before_update"
    if optimization.get("final_objective") is not None:
        result["final_train_loss"] = optimization["final_objective"]
        origins["final_train_loss"] = "derived:optimization.final_objective"
    elif merged.get("final_objective") is not None and result["final_train_loss"] is None:
        result["final_train_loss"] = merged["final_objective"]
        origins["final_train_loss"] = "native:final_objective"
    curve_loss = curve.get("objective", curve.get("loss"))
    if curve_loss is not None:
        result["last_observed_objective"] = curve_loss
        result["last_observed_objective_origin"] = "derived:training_curve_last_before_update"
    digest, digest_kind = _model_digest(unit)
    if digest is not None and result["model_hash"] is None:
        result["model_hash"], origins["model_hash"] = digest, "derived:model_file_digest"
        result["model_hash_kind"] = digest_kind
    elif result["model_hash"] is not None:
        result["model_hash_kind"] = "native_receipt"
    if result["config_hash"] is None and source_metadata.get("config_hash"):
        result["config_hash"], origins["config_hash"] = source_metadata["config_hash"], "inherited:run_config"
    source_code_hash = source_metadata.get("code_hash") or source_metadata.get("source_snapshot_hash")
    if result["code_hash"] is None and source_code_hash:
        result["code_hash"], origins["code_hash"] = source_code_hash, "inherited:source_snapshot"
    result["objective_kind"] = "penalized_objective" if result["objective_id"] is not None else None
    result["objective_timing"] = "after_update" if result["final_train_loss"] is not None else None
    if result["fit_id"] is None and unit.get("fit_id") is not None:
        result["fit_id"], origins["fit_id"] = unit["fit_id"], "unit_metadata"
    result["field_origin"] = origins
    return result
