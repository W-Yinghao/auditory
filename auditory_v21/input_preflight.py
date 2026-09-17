"""Metadata-only preflight for the frozen v2.1 real-input boundary.

This module never opens an EEG feature array.  It reads parquet row metadata,
JSON scope receipts, and NumPy ZIP headers.  ``run`` is deliberately Slurm
only; the returned PASS is an input-contract receipt, not a scientific result.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Iterable


SEED = 21101
PACKETS = ("N1", "N3")
MODES = ("R_SIM", "L0")
MIN_ROLE_GROUPS = {"A": 12, "B": 3, "C": 4, "D": 4, "E": 3}
RAW_H_COLUMNS = [
    "previous_run_log1p", "previous_run_missing",
    "current_gap_s_squared", "current_gap_s_missing",
    "previous_run_run_1", "previous_run_run_2",
    "previous_run_run_3_5", "previous_run_run_6_plus",
    "previous_code_1_1", "previous_code_1_2",
    "previous_code_1_unknown", "previous_gap_1_missing",
    "previous_gap_1_log", "previous_code_2_1",
    "previous_code_2_2", "previous_code_2_unknown",
    "previous_gap_2_missing", "previous_gap_2_log",
    "previous_code_3_1", "previous_code_3_2",
    "previous_code_3_unknown", "previous_gap_3_missing",
    "previous_gap_3_log", "position_fraction",
    "position_fraction_squared",
]


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _object_hash(value: Any) -> str:
    """Hash a canonical JSON object for provenance joins."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _safe_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _groups(values: Iterable[Any]) -> list[str]:
    return sorted({str(v) for v in values})


def split_role_groups(outer_train: Iterable[Any], validation: Iterable[Any],
                      test: Iterable[Any], seed: int = SEED) -> dict[str, list[str]]:
    """Return the contract's deterministic group assignment without arrays."""
    train, val, heldout_test = map(lambda x: set(map(str, x)),
                                   (outer_train, validation, test))
    if not val <= train or train & heldout_test:
        raise ValueError("ROLE_SCOPE_OVERLAP")
    ordered = sorted(val, key=lambda g: hashlib.sha256(f"{seed}|{g}".encode()).hexdigest())
    nb = max(3, int(len(ordered) * .25))
    nc = (len(ordered) - nb) // 2
    roles = {"A": sorted(train - val), "B": ordered[:nb],
             "C": ordered[nb:nb + nc], "D": ordered[nb + nc:],
             "E": sorted(heldout_test)}
    for role, minimum in MIN_ROLE_GROUPS.items():
        if len(roles[role]) < minimum:
            raise ValueError("ROLE_SUPPORT_LIMITED")
    if set().union(*map(set, roles.values())) != train | heldout_test:
        raise ValueError("ROLE_GROUP_COVERAGE")
    if sum(map(len, roles.values())) != len(set().union(*map(set, roles.values()))):
        raise ValueError("ROLE_GROUP_OVERLAP")
    return roles


# Keep the name parallel to auditory_v21.estimator.split_roles for adapters.
split_roles = split_role_groups


def _quantiles(values: list[int]) -> dict[str, int | None]:
    if not values:
        return {key: None for key in ("min", "q25", "median", "q75", "max")}
    ordered = sorted(values)
    def q(p: float) -> int:
        if len(ordered) == 1:
            return ordered[0]
        index = (len(ordered) - 1) * p
        low, high = int(index), min(int(index) + 1, len(ordered) - 1)
        return int(round(ordered[low] + (ordered[high] - ordered[low]) * (index - low)))
    return {"min": ordered[0], "q25": q(.25), "median": q(.5),
            "q75": q(.75), "max": ordered[-1]}


def _npz_headers(path: Path) -> dict[str, list[int]]:
    """Read only .npy headers inside an npz; no array payload is decompressed."""
    result: dict[str, list[int]] = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith(".npy"):
                continue
            raw = archive.open(name).read(16)
            if raw[:6] != b"\x93NUMPY":
                raise ValueError("NPZ_HEADER_SCHEMA")
            major, minor = raw[6], raw[7]
            header_len = int.from_bytes(raw[8:10], "little") if major == 1 else int.from_bytes(raw[8:12], "little")
            prefix = 10 if major == 1 else 12
            header = archive.open(name).read(prefix + header_len)[prefix:]
            record = ast.literal_eval(header.decode("latin1").strip())
            shape = record.get("shape")
            if not isinstance(shape, tuple) or not all(isinstance(x, int) for x in shape):
                raise ValueError("NPZ_HEADER_SHAPE")
            result[Path(name).stem] = list(shape)
    return result


def _hash_entries(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    entries = _json(path)
    return {str(row["path"]): str(row["sha256"]) for row in entries
            if isinstance(row, dict) and "path" in row and "sha256" in row}


def _path_hash(path: Path, hashes: dict[str, str]) -> dict[str, Any]:
    expected = hashes.get(str(path)) or hashes.get(str(path.resolve()))
    item = {"path": str(path), "exists": path.is_file(), "expected_sha256": expected}
    if path.is_file():
        item["sha256"] = _sha256(path)
        item["hash_match"] = expected is not None and item["sha256"] == expected
    else:
        item["sha256"] = None
        item["hash_match"] = False
    return item


def _read_rows(path: Path) -> list[dict[str, Any]]:
    """Read metadata rows in Slurm; supports parquet and small test fixtures."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        value = _json(path)
        return value if isinstance(value, list) else value.get("rows", [])
    if suffix == ".csv":
        import csv
        with path.open(newline="") as stream:
            return list(csv.DictReader(stream))
    if suffix in (".parquet", ".pq"):
        import pandas as pd
        return pd.read_parquet(path).to_dict(orient="records")
    raise ValueError("METADATA_FORMAT")


def _history_schema(root: Path, packet: str, rows: list[dict[str, Any]]) -> tuple[list[str], bool, str | None, str | None]:
    """Use the frozen selector on real metadata columns, retaining its hash."""
    source = root / "private/auditory_next_v2" / f"{packet}_inputs_001/source/auditory_next/history.py"
    if not source.is_file():
        return [], False, None, "MISSING_HISTORY_SELECTOR"
    try:
        import pandas as pd
        spec = importlib.util.spec_from_file_location(f"auditory_v21_{packet}_history", source)
        if spec is None or spec.loader is None:
            return [], False, _sha256(source), "HISTORY_SELECTOR_IMPORT"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        frame = pd.DataFrame(rows)
        columns = _selected_history_columns(module, frame)
        numeric = all(pd.api.types.is_numeric_dtype(frame[column]) for column in columns)
        return columns, numeric, _sha256(source), None
    except Exception as exc:
        return [], False, _sha256(source), type(exc).__name__


def _selected_history_columns(selector: Any, frame: Any) -> list[str]:
    """Mirror context_inputs.history_matrix's explicit layout_id exclusion."""
    return [column for column in selector.history_feature_columns(frame)
            if column != "layout_id"]


def _truth(value: Any) -> bool:
    return value is True or str(value).lower() in {"true", "1", "yes"}


def _jsonable(value: Any) -> Any:
    """Keep private selected-row receipts serializable without importing NumPy."""
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if value == value and abs(value) != float("inf") else None
    if hasattr(value, "item"):
        try:
            return _jsonable(value.item())
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)


def _valid_rows(rows: list[dict[str, Any]], packet: str, n3_cells: set[str], groups: set[str]) -> list[dict[str, Any]]:
    output = []
    for source_index, row in enumerate(rows):
        if not _truth(row.get("accepted")) or not _truth(row.get("history_chain_complete")):
            continue
        try:
            label = int(row.get("stimulus_local_id"))
        except (TypeError, ValueError):
            continue
        group = str(row.get("split_group_id"))
        if label not in (0, 1) or group not in groups:
            continue
        if packet == "N3" and f"{row.get('previous_code')}|{row.get('previous_run_bin')}" not in n3_cells:
            continue
        selected = {str(key): _jsonable(value) for key, value in row.items()}
        selected["_source_row_index"] = source_index
        output.append(selected)
    return output


def _role_profile(rows: list[dict[str, Any]], roles: dict[str, list[str]]) -> dict[str, Any]:
    by_group: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_group.setdefault(str(row.get("split_group_id")), []).append(row)
    profile: dict[str, Any] = {}
    for role, role_groups in roles.items():
        group_rows = {g: by_group.get(g, []) for g in role_groups}
        counts = [len(group_rows[g]) for g in role_groups]
        class_counts = {g: {str(label): sum(int(r.get("stimulus_local_id")) == label for r in group_rows[g])
                             for label in (0, 1)} for g in role_groups}
        profile[role] = {"groups": role_groups, "trial_count": _quantiles(counts),
                         "trials_by_group": {g: len(group_rows[g]) for g in role_groups},
                         "class_counts_by_group": class_counts,
                         "rows": sum(counts),
                         "class_counts": {str(label): sum(v[str(label)] for v in class_counts.values())
                                          for label in (0, 1)},
                         "both_classes": all(profile_class > 0 for profile_class in
                                              (sum(v["0"] for v in class_counts.values()),
                                               sum(v["1"] for v in class_counts.values()))),
                         "all_groups_both_classes": all(set(v) == {"0", "1"} and
                                                         all(v[k] > 0 for k in v)
                                                         for v in class_counts.values())}
    return profile


def _find_registry_task(registry: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    return next((row for row in registry if row.get("task") == name), None)


def _resolve_plan_task(plan_tasks: list[dict[str, Any]], *, mode: str, outer_fold: int,
                       stage: str, inner_fold: int | None) -> dict[str, Any]:
    matches = [task for task in plan_tasks
               if task.get("stage") == stage and task.get("mode") == mode
               and task.get("branch") == "all" and task.get("outer_fold") == outer_fold
               and task.get("inner_fold") == inner_fold]
    if len(matches) != 1:
        raise ValueError("EXPLICIT_TASK_NOT_UNIQUE")
    return dict(matches[0])


def _task_artifacts(feature_root: Path, task_name: str, hashes: dict[str, str]) -> dict[str, Any]:
    folder = feature_root / task_name
    names = ("task.json", "completion.json", "features.npz", "feature_rows.parquet", "encoder.pt", "probe_metadata.json")
    return {name: _path_hash(folder / name, hashes) for name in names}


def _l0_source_receipt(root: Path, plan: dict[str, Any], plan_hash: str,
                       artifacts: dict[str, Any], hashes: dict[str, str],
                       scope: dict[str, Any]) -> dict[str, Any]:
    """Verify the frozen L0 implementation and describe its probe scope.

    L0 has no learned encoder or feature scaler.  The old job still fits a
    stimulus probe after producing features; those probe fit groups are kept
    as an audit field and are never reported as encoder/scaler fit groups.
    """
    required = {
        "auditory5/execution.py": (
            "encoder=None",
            "z=bin_20ms(view.X) if encoder is None else encoder.transform(view.X)",
            "if encoder is not None:encoder.save",
        ),
        "auditory5/probes.py": (
            "def bin_20ms",
            "processed_fs != 250.0",
            "reshape(x.shape[0], x.shape[1], x.shape[2] // 5, 5)",
            ".mean(axis=-1)",
        ),
        "auditory5/datasets.py": (
            "def load_dataset",
            "np.load(dest/(branch+'.npy'",
        ),
    }
    snapshot_value = plan.get("source_snapshot")
    snapshot = _safe_path(root, snapshot_value) if snapshot_value else Path("")
    code_hashes = plan.get("code_hashes", {})
    source_files: dict[str, Any] = {}
    semantic_checks: dict[str, bool] = {}
    for relative, markers in required.items():
        path = snapshot / relative
        plan_expected = code_hashes.get(relative)
        # legacy_input_hashes records the original repository source path;
        # it is an independent S0 anchor from the plan snapshot hash.
        s0_item = _path_hash(root / relative, hashes)
        item = _path_hash(path, {})
        actual = item.get("sha256")
        item.update({"plan_expected_sha256": plan_expected,
                     "plan_hash_match": actual is not None and actual == plan_expected,
                     "s0_expected_sha256": s0_item.get("expected_sha256"),
                     "s0_hash_match": s0_item.get("hash_match", False)})
        source_files[relative] = item
        try:
            text = path.read_text()
            semantic_checks[relative] = all(marker in text for marker in markers)
        except (OSError, UnicodeError):
            semantic_checks[relative] = False
    source_hash_object = {relative: code_hashes.get(relative)
                          for relative in sorted(required)}
    source_scope_hash = _object_hash(source_hash_object)
    source_hashes_verified = bool(snapshot_value) and all(
        item["exists"] and item["plan_hash_match"] and item["s0_hash_match"]
        for item in source_files.values())
    stateless_source_verified = source_hashes_verified and all(semantic_checks.values())

    encoder_artifact = artifacts.get("encoder.pt", {})
    no_encoder_artifact = not encoder_artifact.get("exists", False)
    completion_proof_no_encoder = (
        scope.get("completion_status") == "PASS"
        and scope.get("plan_hash_match", False)
        and no_encoder_artifact
    )
    feature_names = ("features.npz", "feature_rows.parquet")
    feature_hashes_verified = all(
        artifacts.get(name, {}).get("exists", False)
        and artifacts.get(name, {}).get("hash_match", False)
        for name in feature_names
    )
    feature_binding = {
        "plan_hash": plan_hash,
        "source_scope_hash": source_scope_hash,
        "feature_sha256": {name: artifacts.get(name, {}).get("sha256")
                           for name in feature_names},
        "s0_feature_expected_sha256": {
            name: artifacts.get(name, {}).get("expected_sha256") for name in feature_names
        },
    }
    return {
        "status": "PASS" if stateless_source_verified and completion_proof_no_encoder
                  and feature_hashes_verified else "BLOCKED_L0_SOURCE",
        "feature_generation_kind": "STATELESS_FIXED_BINNING",
        "stateless_source_verified": stateless_source_verified,
        "source_snapshot": str(snapshot),
        "source_files": source_files,
        "source_semantic_checks": semantic_checks,
        "source_hash_object": source_hash_object,
        "source_scope_hash": source_scope_hash,
        "source_hashes_verified": source_hashes_verified,
        "completion_proof_no_encoder": completion_proof_no_encoder,
        "encoder_artifact_absent": no_encoder_artifact,
        "feature_hash_binding": feature_binding,
        "feature_hash_binding_hash": _object_hash(feature_binding),
        "feature_hashes_verified": feature_hashes_verified,
        "actual_encoder_fit_groups": [],
        "actual_scaler_fit_groups": [],
        "old_probe_fit_groups": scope.get("task_fit_groups", []),
        "old_probe_validation_groups": scope.get("task_validation_groups", []),
        "old_probe_test_groups": scope.get("task_test_groups", []),
        "old_probe_fit_scope_hash": scope.get("completion_scope_hash"),
        "raw_offline_qc_independence_verified": False,
    }


def _scope_receipt(feature_root: Path, task_name: str, mode: str, artifacts: dict[str, Any],
                   registry_row: dict[str, Any], plan_hash: str,
                   expected_task: dict[str, Any] | None = None) -> dict[str, Any]:
    folder = feature_root / task_name
    receipt: dict[str, Any] = {"status": "UNKNOWN", "actual_train_groups": [],
                               "scaler_train_groups": [], "scope_hash": None,
                               "scaler_scope_hash": None}
    task = _json(folder / "task.json") if (folder / "task.json").is_file() else {}
    completion = _json(folder / "completion.json") if (folder / "completion.json").is_file() else {}
    receipt.update({"task_fit_groups": _groups(task.get("fit_groups", [])),
                   "task_validation_groups": _groups(task.get("validation_groups", [])),
                   "task_test_groups": _groups(task.get("test_groups", [])),
                   "plan_hash": task.get("plan_hash"),
                   "completion_status": completion.get("status"),
                   "completion_plan_hash": completion.get("plan_hash"),
                   "completion_scope_hash": completion.get("encoder_fit_scope_hash")})
    identity_fields = ("name", "stage", "mode", "branch", "outer_fold", "inner_fold")
    receipt["task_identity_match"] = expected_task is not None and all(
        task.get(field) == expected_task.get(field) for field in identity_fields)
    if mode == "L0":
        # L0's task fit groups belong to the downstream stimulus probe.  The
        # feature path itself performs fixed binning and has no fitted state.
        receipt.update(status="LEGACY_NO_ENCODER", actual_train_groups=[],
                       scaler_train_groups=[],
                       old_probe_fit_groups=receipt["task_fit_groups"],
                       old_probe_validation_groups=receipt["task_validation_groups"],
                       old_probe_test_groups=receipt["task_test_groups"],
                       plan_hash_match=receipt["plan_hash"] == plan_hash == receipt["completion_plan_hash"])
        return receipt
    if not (folder / "encoder.pt").is_file():
        return receipt
    try:
        import torch
        checkpoint = torch.load(folder / "encoder.pt", map_location="cpu", weights_only=False)
        scope = checkpoint.get("scope", {})
        scaler = checkpoint.get("scaler", {})
        actual = _groups(scope.get("train_groups", []))
        scaled = _groups(scaler.get("fit_groups", []))
        scope_hash = checkpoint.get("scope_hash") or scope.get("scope_hash")
        receipt.update(status="PASS", actual_train_groups=actual, scaler_train_groups=scaled,
                       scope_hash=scope_hash, scaler_scope_hash=scaler.get("scope_hash"),
                       checkpoint_validation_groups=_groups(scope.get("validation_groups", [])),
                       checkpoint_test_groups=_groups(scope.get("test_groups", [])))
    except Exception as exc:  # the detailed exception belongs only in private output
        receipt.update(status="UNKNOWN_CHECKPOINT", error_type=type(exc).__name__)
    receipt["plan_hash_match"] = receipt["plan_hash"] == plan_hash == receipt["completion_plan_hash"]
    receipt["scope_hash_match"] = receipt["scope_hash"] is not None and receipt["scope_hash"] == receipt["completion_scope_hash"]
    receipt["scaler_scope_hash_match"] = receipt["scaler_scope_hash"] is not None and receipt["scaler_scope_hash"] == receipt["scope_hash"]
    if registry_row:
        receipt["registry_actual_train_groups"] = _groups(registry_row.get("fit_groups", []))
        receipt["registry_scope_match"] = receipt["actual_train_groups"] == receipt["registry_actual_train_groups"]
    return receipt


def _feature_row_alignment(path: Path, selected: list[dict[str, Any]],
                           header: dict[str, list[int]]) -> dict[str, Any]:
    """Compare metadata IDs/groups/labels without opening feature payloads."""
    required = ["trial_id", "split_group_id", "stimulus_local_id"]
    if not path.is_file():
        return {"status": "UNKNOWN_MISSING_FEATURE_ROWS", "rows": None}
    try:
        import pandas as pd
        frame = pd.read_parquet(path, columns=required)
        if frame["trial_id"].astype(str).duplicated().any():
            return {"status": "BLOCKED_DUPLICATE_FEATURE_TRIAL", "rows": len(frame)}
        labels = frame["stimulus_local_id"].astype(int)
        if not labels.isin([0, 1]).all():
            return {"status": "BLOCKED_NONBINARY_FEATURE_LABEL", "rows": len(frame)}
        lookup = {str(row.trial_id): (str(row.split_group_id), int(row.stimulus_local_id))
                  for row in frame.itertuples(index=False)}
        missing = []
        mismatches = []
        for row in selected:
            trial = str(row.get("trial_id"))
            expected = (str(row.get("split_group_id")), int(row.get("stimulus_local_id")))
            if trial not in lookup:
                missing.append(trial)
            elif lookup[trial] != expected:
                mismatches.append(trial)
        header_rows = {shape[0] for key, shape in header.items()
                       if key in ("post", "pre", "trial_ids", "groups", "y") and shape}
        row_shape_ok = not header_rows or header_rows == {len(frame)}
        return {"status": "PASS" if not missing and not mismatches and row_shape_ok else "BLOCKED_FEATURE_ALIGNMENT",
                "rows": len(frame), "selected_rows": len(selected),
                "missing_count": len(missing), "mismatch_count": len(mismatches),
                "header_row_counts": sorted(header_rows), "header_row_count_match": row_shape_ok}
    except Exception as exc:
        return {"status": "UNKNOWN_FEATURE_ALIGNMENT", "rows": None,
                "error_type": type(exc).__name__}


def _write_selected_rows(path: Path, rows: list[dict[str, Any]], h_columns: list[str]) -> None:
    """Persist the adapter's metadata table without duplicating the full ledger."""
    import pandas as pd
    keep = ["trial_id", "split_group_id", "stimulus_local_id", "record_id", "candidate_id"]
    columns = [column for column in keep + list(h_columns) if any(column in row for row in rows)]
    frame = pd.DataFrame([{column: row.get(column) for column in columns} for row in rows], columns=columns)
    # Missing H columns remain numeric even when every selected value is missing.
    for column in h_columns:
        if column not in frame:
            frame[column] = float("nan")
    frame.to_parquet(path, index=False)


def _case(root: Path, metadata: list[dict[str, Any]], support: Path, packet: str,
          mode: str, fold: dict[str, Any], plan: dict[str, Any],
          plan_tasks: list[dict[str, Any]],
          registry: list[dict[str, Any]], hashes: dict[str, str],
          feature_root: Path, plan_hash: str, history_columns: list[str], history_numeric: bool,
          history_selector_hash: str | None, history_error: str | None) -> dict[str, Any]:
    outer = int(fold["outer_fold"])
    train = _groups(fold.get("train_groups", []))
    test = _groups(fold.get("test_groups", []))
    inner = fold.get("D_inner_fold_by_group", {})
    source_groups = set(train) | set(test)
    cells: set[str] = set()
    if packet == "N3":
        n3 = _json(support / "N3_outer_support.json")[outer]
        cells = {str(x) for x in n3.get("omega_H", [])}
        source_groups = set(map(str, n3.get("train_groups", []) + n3.get("test_groups", [])))
    else:
        source_groups &= set(_json(support / "N1_groups.json"))
    train = sorted(set(train) & source_groups)
    test = sorted(set(test) & source_groups)
    validation = sorted(g for g, value in inner.items() if int(value) == 0 and g in train)
    role_groups = split_role_groups(train, validation, test)
    selected = _valid_rows(metadata, packet, cells, source_groups)
    selected.sort(key=lambda row: str(row.get("trial_id")))
    # Resolve the immutable task by all frozen identity fields, never by a guessed name.
    task = _resolve_plan_task(plan_tasks, mode=mode, outer_fold=outer,
                              stage="D_inner" if mode == "R_SIM" else "outer",
                              inner_fold=0 if mode == "R_SIM" else None)
    task_name = str(task["name"])
    registry_row = _find_registry_task(registry, task_name)
    artifacts = _task_artifacts(feature_root, task_name, hashes)
    expected = {"R_SIM": {"post": 64, "pre": 64}, "L0": {"post": 400, "pre": 200}}[mode]
    header = {}
    header_error = None
    feature_path = feature_root / task_name / "features.npz"
    if feature_path.is_file():
        try:
            header = _npz_headers(feature_path)
        except Exception as exc:
            header_error = type(exc).__name__
    dimensions = {"H": len(RAW_H_COLUMNS), "P": expected["post"], "B": expected["pre"]}
    dimensions.update({"P_header": (header.get("post") or [None, None])[-1],
                       "B_header": (header.get("pre") or [None, None])[-1]})
    scope = _scope_receipt(feature_root, task_name, mode, artifacts, registry_row or {}, plan_hash, task)
    if mode == "L0":
        scope.update(_l0_source_receipt(root, plan, plan_hash, artifacts, hashes, scope))
    feature_alignment = _feature_row_alignment(
        feature_root / task_name / "feature_rows.parquet",
        selected, header)
    h_source = root / "private/auditory_next_v2" / f"{packet}_inputs_001/source/auditory_next/history.py"
    leakage = sorted(set(scope.get("actual_train_groups", [])) &
                     set().union(*(set(role_groups[r]) for r in ("B", "C", "D", "E"))))
    checks = {
        "h_schema": h_source.is_file() and history_columns == RAW_H_COLUMNS and
                    history_numeric and history_selector_hash is not None and history_error is None,
        "dimensions": not header_error and dimensions.get("P_header") == expected["post"] and
                      dimensions.get("B_header") == expected["pre"] and registry_row is not None and
                      {"post", "pre", "trial_ids", "groups", "y"} <= set(header) and
                      registry_row.get("feature_shapes", {}).get("post", [None, None])[-1] == expected["post"] and
                      registry_row.get("feature_shapes", {}).get("pre", [None, None])[-1] == expected["pre"],
        "registry_present": registry_row is not None and registry_row.get("status") == "PASS",
        "artifact_hashes": all(v["exists"] and v["hash_match"] for v in artifacts.values()
                                if v["path"].endswith(("task.json", "completion.json", "features.npz", "feature_rows.parquet"))),
        "encoder_scope": scope.get("task_identity_match") and scope.get("completion_status") == "PASS" and
                         scope.get("plan_hash_match") and
                         (mode == "L0" and scope.get("stateless_source_verified") and
                          scope.get("completion_proof_no_encoder") and
                          scope.get("feature_hashes_verified") or
                          mode != "L0" and (scope.get("status") == "PASS" and
                                           scope.get("scope_hash_match") and
                                           scope.get("scaler_scope_hash_match") and
                                           scope.get("registry_scope_match") and
                                           scope.get("actual_train_groups") == scope.get("scaler_train_groups"))),
        "encoder_artifact_hash": (mode == "L0" and scope.get("encoder_artifact_absent")) or
                                 (artifacts["encoder.pt"]["exists"] and artifacts["encoder.pt"]["hash_match"]),
        "feature_rows_alignment": feature_alignment["status"] == "PASS",
        "role_encoder_exclusion": (scope.get("stateless_source_verified") if mode == "L0" else not leakage),
        "roles": all(len(role_groups[r]) >= MIN_ROLE_GROUPS[r] for r in MIN_ROLE_GROUPS),
    }
    profile = _role_profile(selected, role_groups)
    checks["class_support"] = all(profile[r]["both_classes"] for r in ("A", "B", "C", "D", "E"))
    status = "PASS" if all(checks.values()) else "BLOCKED"
    encoder_receipt = dict(scope)
    encoder_receipt.update({"verified_artifact_hashes": artifacts,
                            "source_scope_hash": scope.get("source_scope_hash", scope.get("scope_hash")),
                            "encoder_fit_groups": scope.get("actual_train_groups", []),
                            "scaler_fit_groups": scope.get("scaler_train_groups", []),
                            "encoder_validation_groups": scope.get("checkpoint_validation_groups",
                                                                    scope.get("task_validation_groups", [])),
                            "inner_fold": 0 if mode == "R_SIM" else None})
    role_sample_sizes = {r: [profile[r]["trials_by_group"][g] for g in role_groups[r]]
                         for r in role_groups}
    return {"case": f"{packet}_{mode}_outer{outer}", "packet": packet, "mode": mode,
            "outer_fold": outer, "status": status, "checks": checks,
            "dimensions": dimensions, "h_columns": history_columns,
            "task": task_name,
            "task_metadata": task,
            "feature_folder": str(feature_root / task_name),
            "metadata": {"path": str(support / "full_event_history.parquet"),
                         "filter": "accepted & history_chain_complete & stimulus_local_id in {0,1}" +
                                   (" & history_cell in omega_H" if packet == "N3" else ""),
                         "rows": len(selected),},
            "h_schema_source": str(h_source),
            "h_schema_source_sha256": history_selector_hash,
            "h_schema_error": history_error,
            "roles": role_groups, "role_groups": role_groups,
            "role_profile": profile, "role_sample_sizes": role_sample_sizes,
            "encoder_receipt": encoder_receipt,
            "scope": scope, "artifacts": artifacts,
            "feature_file_hashes": {k: v for k, v in artifacts.items()
                                    if k in ("features.npz", "feature_rows.parquet")},
            "feature_header": header, "feature_header_error": header_error,
            "feature_rows_alignment": feature_alignment,
            "old_transforms_reused": False}


def run(root: Path, private: Path, public: Path, report: Path, config: dict) -> dict[str, Any]:
    """Run all ten packet/mode/fold metadata cases and save private/public receipts."""
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("SLURM_REQUIRED")
    os.umask(0o077)
    root, private, public, report = map(Path, (root, private, public, report))
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    public.mkdir(parents=True, exist_ok=True, mode=0o700)
    report.mkdir(parents=True, exist_ok=True, mode=0o700)
    private.chmod(0o700)
    stage = config.get("input_preflight", config)
    legacy = root / "private/auditory5_v1"
    plan_path = _safe_path(root, stage.get("legacy_plan", legacy / "jobs/plan_001/plan.json"))
    split_path = _safe_path(root, stage.get("legacy_split", legacy / "splits/splits_001/folds.json"))
    s0 = root / "private/auditory_next_v2" / str(stage.get("preflight_run", "S0_001"))
    support = root / "private/auditory_next_v2" / str(stage.get("support_run", "S1_support_004"))
    registry_path = s0 / "feature_scope_registry.json"
    hashes_path = s0 / "legacy_input_hashes.json"
    metadata_path = support / "full_event_history.parquet"
    required = [plan_path, split_path, registry_path, hashes_path, metadata_path,
                support / "N1_groups.json", support / "N3_outer_support.json"]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("INPUT_PREFLIGHT_MISSING:" + ",".join(missing))
    plan = _json(plan_path)
    plan_tasks = list(plan.get("tasks", []))
    folds = _json(split_path).get("folds", [])
    if len(folds) != 5:
        raise ValueError("FIVE_OUTER_FOLDS_REQUIRED")
    registry = _json(registry_path)
    hashes = _hash_entries(hashes_path)
    metadata = _read_rows(metadata_path)
    plan_hash = _sha256(plan_path)
    feature_root = plan_path.parent / "outputs"
    cases = []
    for packet in PACKETS:
        history_columns, history_numeric, history_selector_hash, history_error = _history_schema(root, packet, metadata)
        for mode in MODES:
            for fold in folds:
                cases.append(_case(root, metadata, support, packet, mode, fold, plan, plan_tasks, registry, hashes,
                                   feature_root, plan_hash,
                                   history_columns, history_numeric, history_selector_hash, history_error))
    for index, case in enumerate(cases):
        selected_path = private / f"case_{index:02d}_{case['case']}_selected_rows.parquet"
        cells = set(_json(support / "N3_outer_support.json")[case["outer_fold"]].get("omega_H", [])) if case["packet"] == "N3" else set()
        selected = _valid_rows(metadata, case["packet"], cells,
                               set(case["roles"]["A"]) | set(case["roles"]["B"]) |
                               set(case["roles"]["C"]) | set(case["roles"]["D"]) | set(case["roles"]["E"]))
        selected.sort(key=lambda row: str(row.get("trial_id")))
        _write_selected_rows(selected_path, selected, case["h_columns"])
        trial_order = [str(r.get("trial_id")) for r in selected]
        row_indices = [r.get("_source_row_index") for r in selected]
        case.update({"selected_rows_path": str(selected_path),
                     "selected_rows_sha256": _sha256(selected_path)})
        case["metadata"].update({"trial_order_sha256": hashlib.sha256(
                                      "\n".join(trial_order).encode()).hexdigest(),
                                  "row_indices_sha256": hashlib.sha256(
                                      json.dumps(row_indices, separators=(",", ":")).encode()).hexdigest(),
                                  "selected_rows": len(selected)})
        (private / f"case_{index:02d}_{case['case']}.json").write_text(
            json.dumps(case, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    aggregate = [{"case": c["case"], "packet": c["packet"], "mode": c["mode"],
                  "outer_fold": c["outer_fold"], "status": c["status"],
                  "checks_passed": sum(c["checks"].values()), "checks_total": len(c["checks"]),
                  "role_groups": {r: len(c["roles"][r]) for r in c["roles"]},
                  "role_sample_sizes": {r: c["role_profile"][r]["trial_count"] for r in c["roles"]},
                  "dimensions": c["dimensions"]} for c in cases]
    summary = {"status": "PASS" if all(c["status"] == "PASS" for c in cases) else "BLOCKED",
               "scope": "metadata-only v2.1 input preflight; no EEG arrays or fits",
               "cases": len(cases), "case_status_counts": {
                   key: sum(c["status"] == key for c in cases) for key in ("PASS", "BLOCKED")},
               "h_columns": RAW_H_COLUMNS, "seed": SEED, "aggregate": aggregate}
    (private / "input_hashes.json").write_text(json.dumps(
        {str(path): _sha256(path) for path in required}, ensure_ascii=False, indent=2) + "\n")
    (private / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    (public / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (public / "case_aggregate.json").write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n")
    (report / "INPUT_PREFLIGHT.md").write_text(
        "# v2.1 input preflight\n\n"
        "Metadata-only receipt over N1/N3, R_SIM/L0 and five frozen outer folds. "
        "No EEG matrix payloads, predictions, or fits were used. BLOCKED cases require "
        "resolution before a real adapter or comparison.\n")
    return summary
