"""Private accounting of v2 fitting attempts.

This module only audits receipts already written by a route.  It deliberately
does not open EEG arrays, reconstruct a prepared case, or regard a plan as an
executed fit.  The ``.tmp`` suffix is intentional while the parent agent
reviews the contract.
"""

from __future__ import annotations

import csv
import ast
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable, Mapping

from .provenance import finish as provenance_finish


MANDATORY_RECEIPT_FIELDS = (
    "fit_id", "packet", "mode", "view", "objective_id", "optimizer_id",
    "outer_fold", "inner_fold", "seed", "training_scope_hash",
    "input_hash", "feature_scope_hash", "label_map_hash", "weight_distribution",
    "hyperparameter_source", "calibration_scope_hash", "n_train_candidates",
    "n_train_trials_or_bags", "n_eval_candidates", "n_eval_trials_or_bags",
    "step_count", "final_train_loss", "gradient_diagnostic",
    "finite_parameters", "optimizer_status", "resource_usage", "code_hash",
    "config_hash", "model_hash", "prediction_hash", "exception_class",
    "failure_stage",
)

_PASS = {
    "PASS", "OK", "COMPLETE", "COMPLETED", "OPTIMIZATION_STABLE",
    "STABLE", "WITHIN_CHILD_COMPLETE", "BRIDGE_COMPLETE", "SYNTHETIC_COMPLETE",
    "MODULE_PASS", "COMPLETE_REPAIRED_CORE",
}
_FAIL = {
    "FAIL", "FAILED", "ERROR", "NUMERICAL_FAILURE", "NUMERICAL_FAIL",
    "OPTIMIZATION_UNRESOLVED", "UNRESOLVED", "BUG", "CANCELLED", "ABORTED",
}
_MISSING = {"", "UNKNOWN", "UNAVAILABLE", "NONE", "NULL", "N/A", "NA", "-"}
DERIVED_TEST_RUNS = {"tests_001", "tests_002", "tests_003", "tests_005", "tests_007"}


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _load_list(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError, TypeError):
        return []
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _test_suite_pass(run_dir: Path) -> bool:
    completion = _load(run_dir / "completion.json")
    if str(completion.get("status", "")).upper() in _PASS:
        return True
    try:
        xml = (run_dir / "tests.xml").read_text()
    except OSError:
        return False
    return bool(re.search(r"<testsuite[^>]*errors=\"0\"[^>]*failures=\"0\"", xml))


def _derive_early_test_counts(run_dir: Path) -> tuple[dict[str, int], dict[str, Any]]:
    """Validate the frozen source/XML evidence before deriving the old ridge count."""
    run = run_dir.name
    if run not in DERIVED_TEST_RUNS:
        return {}, {"status": "NOT_APPLICABLE"}
    source_path = run_dir / "source" / "tests" / "auditory_next" / "test_a2.py"
    audit_path = run_dir / "source" / "auditory_next" / "a2_residual_audit.py"
    xml_path = run_dir / "tests.xml"
    evidence: dict[str, Any] = {"status": "UNKNOWN", "source_test_path": str(source_path),
                                "audit_module_path": str(audit_path), "tests_xml_path": str(xml_path)}
    try:
        source = source_path.read_text()
        audit_source = audit_path.read_text()
        xml = xml_path.read_text()
    except OSError as exc:
        evidence["reason"] = type(exc).__name__
        return {}, evidence
    evidence.update({"source_test_a2_sha256": hash_file(source_path),
                     "audit_module_sha256": hash_file(audit_path), "tests_xml_sha256": hash_file(xml_path)})
    try:
        tree = ast.parse(source, filename=str(source_path))
        audit_tree = ast.parse(audit_source, filename=str(audit_path))
    except SyntaxError:
        evidence["reason"] = "SOURCE_AST_INVALID"
        return {}, evidence
    mechanisms = next((node for node in audit_tree.body if isinstance(node, ast.Assign) and
                       any(isinstance(target, ast.Name) and target.id == "MECHANISMS" for target in node.targets)), None)
    values = mechanisms.value.elts if mechanisms is not None and isinstance(mechanisms.value, (ast.Tuple, ast.List)) else []
    if [getattr(value, "value", None) for value in values] != ["null", "predictable_nuisance", "individual_stimulus"]:
        evidence["reason"] = "MECHANISM_TUPLE_MISMATCH"
        return {}, evidence
    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    worlds = functions.get("test_three_worlds_share_conditions_and_fit_never_sees_test_values")
    nuisance = functions.get("test_real_predictable_nuisance_and_signal_are_distinct_constructed_cases")
    world_loop = any(isinstance(node, ast.For) and isinstance(node.iter, ast.Name) and
                     node.iter.id == "MECHANISMS" for node in ast.walk(worlds)) if worlds else False
    world_calls = [node for node in ast.walk(worlds) if isinstance(node, ast.Call) and
                   isinstance(node.func, ast.Name) and node.func.id == "audit_residual_world"] if worlds else []
    ridge_calls = [node for node in ast.walk(nuisance) if isinstance(node, ast.Call) and
                   isinstance(node.func, ast.Name) and node.func.id == "fit_background"] if nuisance else []
    rejected = [node for node in ridge_calls if any(keyword.arg == "alpha" and
               isinstance(keyword.value, ast.Constant) and keyword.value.value == .1
               for keyword in node.keywords)]
    if not (world_loop and len(world_calls) == 2 and len(rejected) == 1 and len(ridge_calls) == 1):
        evidence["reason"] = "FIT_CALL_STRUCTURE_MISMATCH"
        return {}, evidence
    audit_function = next((n for n in audit_tree.body if isinstance(n, ast.FunctionDef) and
        n.name == 'audit_residual_world'), None)
    if audit_function is None or sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and
        n.func.id == 'fit_background' for n in ast.walk(audit_function)) != 1:
        evidence['reason'] = 'AUDIT_WORLD_RIDGE_CALL_STRUCTURE_MISMATCH'
        return {}, evidence
    names = ("test_three_worlds_share_conditions_and_fit_never_sees_test_values",
             "test_real_predictable_nuisance_and_signal_are_distinct_constructed_cases")
    try:
        cases = ET.fromstring(xml).findall('.//testcase')
    except ET.ParseError:
        evidence['reason'] = 'TEST_XML_INVALID'
        return {}, evidence
    for name in names:
        matches = [case for case in cases if case.get('name') == name]
        if len(matches) != 1 or any(matches[0].find(tag) is not None for tag in ('failure','error','skipped')):
            evidence["reason"] = "TARGET_TEST_FAILURE_OR_MISSING"
            return {}, evidence
    evidence.update({"status": "DERIVED_EXACT", "ast_validated": True, "mechanism_count": 3,
                     "audit_calls": 6, "expected_rejected_fit_calls": 1,
                     "derived_ridge_entries": 7})
    derived = {'ridge': 7}
    if run in {'tests_001','tests_002','tests_003'}:
        # These three frozen suites predate fitting.py. Their imported helper
        # implementations were text-reviewed; record the direct call scan and
        # all source hashes rather than silently filling an absent ledger.
        scanned = {}
        forbidden = False
        for path in sorted(source_path.parent.glob('*.py')):
            scanned[path.name] = hash_file(path)
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call):
                    forbidden |= (isinstance(node.func, ast.Attribute) and node.func.attr in {'fit','step'})
                    forbidden |= (isinstance(node.func, ast.Name) and node.func.id in {'advance_fit','fit_cases'})
        evidence['early_test_source_hashes'] = scanned
        if not forbidden:
            derived.update(logistic=0, neural=0)
            evidence['zero_logistic_neural_basis'] = 'reviewed frozen helper code and direct fit/optimizer-call scan; start_fit alone initializes only'
    return derived, evidence


def hash_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str | None:
    """Hash one generated receipt/model/prediction file, without loading it."""
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _stable_json_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def status_class(receipt: Mapping[str, Any] | None) -> str:
    """Map a receipt status to the accounting vocabulary; unknown stays unknown."""
    receipt = receipt or {}
    values = [receipt.get("numerical_status"), receipt.get("optimizer_status"), receipt.get("status")]
    for value in values:
        token = str(value or "").upper().strip()
        if token in _PASS or token.endswith("_COMPLETE"):
            return "COMPLETED"
        if token in _FAIL or any(word in token for word in ("FAIL", "ERROR", "UNRESOLVED", "ABORT")):
            return "NUMERICAL_FAILURE"
    return "UNRESOLVED"


def _fit_category(run: str, payload: Mapping[str, Any] | None = None) -> str:
    value = str((payload or {}).get("family", "")).lower()
    # Receipt family is authoritative; the run name is only a fallback.
    if "ridge" in value:
        return "ridge"
    if "neural" in value or "mlp" in value:
        return "neural"
    if run.startswith("synthetic") and "logistic" not in value:
        return "readout"
    return "readout"


_RECEIPT_ALIASES = {
    # These aliases are fields written by the current fitting implementation,
    # not guesses from a related output file.
    "training_scope_hash": ("scope_hash",),
    "input_hash": ("feature_hash",),
    "objective_id": ("objective",),
    "step_count": ("iterations",),
    "optimizer_status": ("numerical_status",),
}


def _receipt_fields(receipt: Mapping[str, Any]) -> tuple[list[str], dict[str, str]]:
    present, aliases = [], {}
    for field in MANDATORY_RECEIPT_FIELDS:
        if field in receipt and receipt[field] not in (None, ""):
            present.append(field)
            continue
        for alias in _RECEIPT_ALIASES.get(field, ()):
            if alias in receipt and receipt[alias] not in (None, ""):
                present.append(field)
                aliases[field] = alias
                break
    return present, aliases


def _unit(run: str, kind: str, fit_id: str, receipt: Mapping[str, Any] | None,
          *, receipt_files: Iterable[Path] = (), completed_receipt: Mapping[str, Any] | None = None,
          attempted: bool = True, completed: bool | None = None, reused: bool = False,
          category: str | None = None, evidence: str = "") -> dict[str, Any]:
    receipt = dict(receipt or {})
    completed_receipt = dict(completed_receipt or {})
    merged = dict(receipt)
    merged.update(completed_receipt)
    status = status_class(merged) if attempted else ("REUSED" if reused else "UNKNOWN")
    if completed is None:
        completed = status == "COMPLETED" if attempted else None
    failure = status == "NUMERICAL_FAILURE" if attempted else None
    fields, aliases = _receipt_fields(merged)
    return {
        "run": run, "fit_id": fit_id, "source_kind": kind,
        "fit_category": category or _fit_category(run, merged), "attempted": bool(attempted),
        "completed": completed, "numerical_failure": failure, "reused": bool(reused),
        "status": status, "evidence": evidence,
        "receipt_files": [str(path) for path in receipt_files],
        "receipt_field_present": fields,
        "receipt_field_aliases": aliases,
        "missing_required_fields": [key for key in MANDATORY_RECEIPT_FIELDS if key not in fields],
        "field_present_count": len(fields),
    }


def _fit_files(folder: Path) -> tuple[list[Path], list[Path]]:
    models, predictions = [], []
    try:
        files = list(folder.iterdir())
    except OSError:
        return models, predictions
    for path in files:
        if not path.is_file():
            continue
        name = path.name.lower()
        if name in {"model.pkl", "adam_state.pt", "adam_1000.pt", "adam_2000.pt", "failed_state.pt"}:
            models.append(path)
        elif "predict" in name:
            predictions.append(path)
    return models, predictions


def account_fit_directory(run: str, folder: str | Path, *, kind: str = "fit_directory") -> dict[str, Any] | None:
    """Account one route fit folder; both start and legacy initial receipts are supported."""
    folder = Path(folder)
    start_path, initial_path, completion_path = folder / "start.json", folder / "initial_receipt.json", folder / "completion.json"
    if not start_path.exists() and not initial_path.exists():
        return None
    start = _load(start_path) if start_path.exists() else _load(initial_path)
    completion = _load(completion_path) if completion_path.exists() else {}
    receipts = [path for path in (start_path, initial_path, completion_path) if path.exists()]
    unit = _unit(run, kind, str(folder.name), start, receipt_files=receipts,
                 completed_receipt=completion, evidence="fit_folder_start_or_initial_receipt")
    if not completion_path.exists():
        unit["completed"] = None
        unit["numerical_failure"] = None
        unit["status"] = "UNRESOLVED"
    model_files, prediction_files = _fit_files(folder)
    unit["model_files"] = model_files
    unit["prediction_files"] = prediction_files
    return unit


def account_c2s_ledger(run: str, path: str | Path) -> list[dict[str, Any]]:
    """Deduplicate append-only STARTED/PASS rows into one unit per fit."""
    path = Path(path)
    latest: dict[tuple[Any, ...], tuple[int, dict[str, Any]]] = {}
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return []
    for index, line in enumerate(lines):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        key = (row.get("outer_fold"), row.get("inner_fold"), row.get("view"),
               row.get("C"), row.get("scope_hash"), row.get("fit_id"))
        latest[key] = (index, row)
    units = []
    for ordinal, row in sorted(latest.values(), key=lambda item: item[0]):
        fit_id = str(row.get("fit_id") or f"ledger_{ordinal:05d}")
        units.append(_unit(run, "c2s_fit_ledger", fit_id, row,
                           receipt_files=[path], category="readout", evidence="deduplicated_ledger_fit"))
        if str(row.get("status", "")).upper() not in _PASS:
            units[-1]["completed"] = None
            units[-1]["numerical_failure"] = None
            units[-1]["status"] = "UNRESOLVED"
    return units


def account_repair_states(run: str, root: str | Path) -> list[dict[str, Any]]:
    """Count one repair fit per member; 2000-step continuation is not another fit."""
    root = Path(root)
    members: dict[str, dict[str, Any]] = {}
    for directory in (root / "states", root / "fit_states", root / "members"):
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or not re.search(r"_(?:1000|2000)\.json$", path.name):
                continue
            key = str(path.relative_to(root))
            key = re.sub(r"_(?:1000|2000)\.json$", "", key)
            item = members.setdefault(key, {"paths": [], "has_2000": False})
            item["paths"].append(path)
            item["has_2000"] |= path.name.endswith("_2000.json")
    units = []
    for key, item in sorted(members.items()):
        # The terminal budget is authoritative.  A stable 1000-step receipt
        # must not win over a later 2000-step unresolved/failure receipt.
        terminal = max(item["paths"], key=lambda path: 2000 if path.name.endswith("_2000.json") else 1000)
        terminal_receipt = _load(terminal)
        terminal_budget = 2000 if terminal.name.endswith("_2000.json") else 1000
        prefix = terminal.name[:-len(f"_{terminal_budget}.json")]
        model = terminal.with_name(f"{prefix}_{terminal_budget}.pkl")
        prediction = terminal.with_name(f"{prefix}_{terminal_budget}_training_logits.npy")
        unit = _unit(run, "repair_member", key, terminal_receipt, receipt_files=item["paths"],
                     category="neural", evidence="repair_member_terminal_step_marker")
        unit["terminal_budget_steps"] = terminal_budget
        unit["model_files"] = [model] if model.exists() else []
        unit["prediction_files"] = [prediction] if prediction.exists() else []
        unit["extension_2000_steps"] = terminal_budget == 2000
        if status_class(terminal_receipt) != "COMPLETED":
            unit["completed"] = None
            unit["numerical_failure"] = status_class(terminal_receipt) == "NUMERICAL_FAILURE"
            unit["status"] = "NUMERICAL_FAILURE" if unit["numerical_failure"] else "UNRESOLVED"
        units.append(unit)
    return units


def account_linear_models(run: str, root: str | Path) -> list[dict[str, Any]]:
    """Account the actual 13-per-case linear models saved by ``_fit_linear``."""
    model_root = Path(root) / "linear_models"
    if not model_root.exists():
        return []
    units = []
    for path in sorted(model_root.rglob("*.pkl")):
        unit = _unit(run, "repair_linear_model", path.stem, {}, category="readout",
                     completed=True, evidence="repair_linear_model_file")
        unit["model_files"] = [path]
        units.append(unit)
    return units


def repair_inflight_unknown_count(root: str | Path) -> int:
    """Count state artifacts without a terminal JSON marker as unresolved evidence.

    This is a limitation count only: no fit unit is invented for an interrupted
    job that never wrote its starting/diagnostic receipt.
    """
    root = Path(root)
    count = 0
    for directory in (root / "states", root / "fit_states", root / "members"):
        if not directory.exists():
            continue
        for path in directory.rglob("*.pkl"):
            if re.search(r"_(?:1000|2000)\.pkl$", path.name):
                budget = re.search(r"_(1000|2000)\.pkl$", path.name).group(1)
                if not path.with_name(path.name[:-len(f"_{budget}.pkl")] + f"_{budget}.json").exists():
                    count += 1
    return count


def repair_unstarted_unknown_count(run: str, root: str | Path) -> int:
    """Reserve at most one run-level unknown for an interrupted repair barrier."""
    if not ((run.startswith("C2R") or run.startswith("E0R")) and "core" in run):
        return 0
    completion = _load(Path(root) / "completion.json")
    if completion:
        return 0
    return 1


def _attach_file_hashes(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for unit in units:
        model_files = [Path(path) for path in unit.pop("model_files", [])]
        prediction_files = [Path(path) for path in unit.pop("prediction_files", [])]
        model_records = [{"path": str(path), "sha256": digest} for path in model_files if (digest := hash_file(path))]
        prediction_records = [{"path": str(path), "sha256": digest} for path in prediction_files if (digest := hash_file(path))]
        unit["model_hashes"] = [row["sha256"] for row in model_records]
        unit["prediction_hashes"] = [row["sha256"] for row in prediction_records]
        unit["model_file_digests"] = model_records
        unit["prediction_file_digests"] = prediction_records
        unit["model_file_count"] = len(model_files)
        unit["prediction_file_count"] = len(prediction_files)
    return units


def _run_artifacts(run_dir: Path) -> dict[str, Any]:
    """Collect hashes for route-level model/prediction summaries.

    C2S/G0 write heads and prediction tables beside their per-fit receipts;
    those files are evidence of the fit output but are not additional fits.
    ``source`` and prepared input trees are intentionally excluded.
    """
    model_names = {"model.pkl", "within_child_heads.pkl", "bridge_heads.pkl", "heads.pkl"}
    model_paths: list[Path] = []
    prediction_paths: list[Path] = []
    for path in run_dir.rglob("*"):
        if not path.is_file() or "source" in path.parts:
            continue
        relative = path.relative_to(run_dir)
        name = path.name.lower()
        # Per-fit model files are already attached to their fit unit.  Keep
        # this pass for route-level summaries only, avoiding double counting.
        if "fits" in relative.parts[:-1] or ("heads" in relative.parts[:-1] and name == "model.pkl"):
            continue
        if relative.parts[:1] == ("heads",) and len(relative.parts) == 2 and path.suffix.lower() == ".pkl":
            model_paths.append(path)
            continue
        if relative.parts and relative.parts[0] in {"cases", "worlds", "prepared", "inputs"}:
            # Synthetic worlds have their own explicit prediction files below;
            # arbitrary prepared arrays are not model/prediction summaries.
            if not any(token in path.name.lower() for token in ("predict", "logit", "candidate_loss")):
                continue
        if path.name in model_names and not name.endswith("_predictor.pkl"):
            model_paths.append(path)
        elif any(token in name for token in ("prediction", "logit", "candidate_loss")) and path.suffix.lower() in {".parquet", ".npy", ".npz", ".json"}:
            prediction_paths.append(path)
    def records(paths: Iterable[Path]) -> list[dict[str, str]]:
        output = []
        for path in sorted(set(paths)):
            digest = hash_file(path)
            if digest:
                output.append({"relative_path": str(path.relative_to(run_dir)), "sha256": digest})
        return output
    models, predictions = records(model_paths), records(prediction_paths)
    return {
        "model_artifacts": models, "prediction_artifacts": predictions,
        "model_artifact_count": len(models), "prediction_artifact_count": len(predictions),
        "model_summary_hash": _stable_json_hash(models),
        "prediction_summary_hash": _stable_json_hash(predictions),
    }


def discover_fit_units(v2_root: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Discover only executed fit evidence below ``private/auditory_next_v2``."""
    v2_root = Path(v2_root)
    units: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for run_dir in sorted(path for path in v2_root.iterdir() if path.is_dir()):
        run = run_dir.name
        if run in {"source", "controller_jobs.json"}:
            continue
        start_path = run_dir / "start.json"
        if not start_path.exists():
            continue
        start = _load(start_path)
        source_row = {"run": run, "config_hash": start.get("config_hash"),
                        "source_snapshot_hash": _stable_json_hash(start.get("source_hashes", {})),
                        "source_hash_count": len(start.get("source_hashes", {})) if isinstance(start.get("source_hashes"), dict) else None}

        seen_folders: set[Path] = set()
        # Route fit folders are the only accepted nested start/initial receipts.
        for receipt in sorted(run_dir.rglob("start.json")) + sorted(run_dir.rglob("initial_receipt.json")):
            if receipt == start_path or "source" in receipt.parts:
                continue
            folder = receipt.parent
            if folder in seen_folders:
                continue
            kind = "g0_fit_directory" if run.startswith("G0_readouts") else "route_fit_directory"
            unit = account_fit_directory(run, folder, kind=kind)
            if unit is not None:
                units.append(unit)
                seen_folders.add(folder)

        ledger = run_dir / "fit_ledger.jsonl"
        if ledger.exists():
            units.extend(account_c2s_ledger(run, ledger))

        # Synthetic A2 writes one ridge fit receipt per world directory.
        for ridge_start in sorted(run_dir.rglob("ridge_start.json")):
            ridge = _load(ridge_start)
            completion_path = ridge_start.with_name("ridge_completion.json")
            completion = _load(completion_path) if completion_path.exists() else {}
            unit = _unit(run, "synthetic_ridge", ridge_start.parent.name, ridge,
                         receipt_files=[ridge_start] + ([completion_path] if completion_path.exists() else []),
                         completed_receipt=completion, category="ridge", evidence="ridge_start_receipt")
            if not completion_path.exists():
                unit["completed"] = None
                unit["numerical_failure"] = None
                unit["status"] = "UNRESOLVED"
            units.append(unit)

        # A2 residual predictors are real saved readout predictors; recovery is reuse.
        if run.startswith("A2_residual"):
            for predictor in sorted(run_dir.glob("*.pkl")):
                if "predictor" not in predictor.name:
                    continue
                units.append(_unit(run, "a2_saved_predictor", predictor.stem, {},
                                   receipt_files=(), category="ridge", evidence="saved_predictor_file",
                                   completed=True, attempted=True))
                units[-1]["model_files"] = [predictor]
            reused = _load_list(run_dir / "reused_fit_receipts.json")
            for index, row in enumerate(reused):
                units.append(_unit(run, "a2_reused_receipt", f"reused_{index:04d}", row,
                                   receipt_files=[run_dir / "reused_fit_receipts.json"],
                                   attempted=False, completed=None, reused=True,
                                   category="ridge", evidence="recovery_reuse_receipt"))

        # A2 core summary axes are transform fits, separate from readout fits.
        if run.startswith("A2_core"):
            receipt_path = run_dir / "fit_receipts.json"
            for index, row in enumerate(_load_list(receipt_path)):
                units.append(_unit(run, "a2_summary_axis", f"axis_{index:04d}", row,
                                   receipt_files=[receipt_path], category="transform",
                                   evidence="summary_axis_receipt"))

        # Repair diagnostics are fit evidence only in the explicitly named state roots.
        units.extend(account_repair_states(run, run_dir))
        units.extend(account_linear_models(run, run_dir))
        marker_unknown = repair_inflight_unknown_count(run_dir)
        source_row["repair_inflight_unknown_count"] = marker_unknown or repair_unstarted_unknown_count(run, run_dir)
        source_row["repair_inflight_unknown_reason"] = (
            "state_artifact_without_marker" if marker_unknown else
            "unfinished_repair_without_first_state_marker" if source_row["repair_inflight_unknown_count"] else None)

        # Contract test ledgers are lower-bound evidence, not route fits.
        test_ledger = run_dir / "test_fit_counts.json"
        counts = _load(test_ledger) if test_ledger.exists() else {}
        derived, derivation_evidence = _derive_early_test_counts(run_dir)
        source_row["test_derivation_evidence"] = derivation_evidence
        for family, derived_count in derived.items():
            if family not in counts:
                counts[family] = derived_count
        if counts or run in DERIVED_TEST_RUNS:
            suite_pass = _test_suite_pass(run_dir)
            for family, count in sorted(counts.items()):
                if not isinstance(count, int) or count < 0:
                    continue
                unit = _unit(run, "test_ledger", f"{run}:{family}",
                             {"fit_id": f"{run}:{family}", "family": family,
                              "n_attempts": count}, attempted=count > 0,
                             completed=None,
                             category="test", evidence=("static_source_and_test_xml_exact"
                                                          if derivation_evidence.get("status") == "DERIVED_EXACT" and family not in _load(test_ledger)
                                                          else "test_fit_counts_ledger"))
                unit["count"] = count
                if count == 0:
                    unit["status"] = "NO_FIT"
                else:
                    unit["status"] = "COUNT_RECORDED"
                unit["counter_scope"] = "fit_function_entries_including_expected_rejections"
                unit["count_source"] = ("static_source_and_test_xml_exact"
                                         if derivation_evidence.get("status") == "DERIVED_EXACT" and family not in _load(test_ledger)
                                         else "test_fit_counts_ledger")
                unit["completion_count"] = None
                unit["completed"] = None
                unit["numerical_failure"] = None
                unit["suite_pass_evidence"] = suite_pass
                unit["missing_required_fields"] = list(MANDATORY_RECEIPT_FIELDS)
                unit["field_present_count"] = 0
                units.append(unit)
            # Absence of a family in an early ledger is unknown, never zero.
            for family in ("logistic", "neural", "ridge"):
                if family not in counts and family not in derived:
                    units.append({"run": run, "fit_id": f"{run}:{family}:unknown",
                                  "source_kind": "test_ledger", "fit_category": "test",
                                  "attempted": None, "completed": None, "numerical_failure": None,
                                  "reused": False, "status": "UNKNOWN",
                                  "evidence": "family_absent_from_early_test_ledger",
                                  "count_lower_bound": 0, "count_upper_bound": None,
                                  "unknown_reason": "category_absent; do_not_infer_zero",
                                  "receipt_files": [str(test_ledger)],
                                  "receipt_field_present": [],
                                  "missing_required_fields": list(MANDATORY_RECEIPT_FIELDS),
                                  "field_present_count": 0})

        source_row.update(_run_artifacts(run_dir))
        sources.append(source_row)

    # Exact same physical receipt can be found by start and initial globs; the
    # folder guard above prevents that. Hashing is delayed until discovery ends.
    source_by_run = {row["run"]: row for row in sources}
    for unit in units:
        source = source_by_run.get(unit.get("run"), {})
        inherited = []
        if source.get("config_hash"):
            inherited.append("config_hash")
        if source.get("source_snapshot_hash"):
            inherited.append("code_hash")
        unit["inherited_fields"] = inherited
    return _attach_file_hashes(units), {"runs": sources}


def summarize_fit_units(units: Iterable[Mapping[str, Any]], *, source_run_count: int | None = None) -> dict[str, Any]:
    units = list(units)
    attempted = [row for row in units if row.get("attempted") is True]
    route_attempted = [row for row in attempted if row.get("fit_category") != "test"]
    route_completed = [row for row in route_attempted if row.get("completed") is True]
    route_unresolved = [row for row in route_attempted if row.get("completed") is not True]
    failures = [row for row in route_attempted if row.get("numerical_failure") is True]
    reused = [row for row in units if row.get("reused") is True]
    def n(category: str, *, only_attempted: bool = True) -> int:
        rows = attempted if only_attempted else units
        return sum(row.get("fit_category") == category for row in rows)
    test_unknown = sum(row.get("fit_category") == "test" and row.get("status") == "UNKNOWN" for row in units)
    unknown_categories = sorted(row.get("fit_id") for row in units
                                if row.get("fit_category") == "test" and row.get("status") == "UNKNOWN")
    test_lower = sum(int(row.get("count", 0)) for row in units if row.get("fit_category") == "test")
    route_attempts = len(route_attempted)
    route_completed_count = len(route_completed)
    # The counter is an entry count and includes intentionally rejected fits;
    # a passing pytest suite therefore cannot be converted into fit completion.
    test_completion_unknown = sum(int(row.get("count", 0)) for row in units
                                  if row.get("fit_category") == "test" and row.get("attempted") is True)
    actual_attempts = route_attempts + test_lower
    actual_completed = route_completed_count
    return {
        "fit_attempts": actual_attempts, "fit_completed": actual_completed,
        "fit_unresolved": len(route_unresolved),
        "fit_numerical_failures": len(failures),
        "fit_attempt_records": len(attempted),
        "fit_attempts_lower_bound": route_attempts + test_lower,
        "fit_completed_lower_bound": route_completed_count,
        "fit_reused": len(reused), "readout_fit_attempts": n("readout"),
        "transform_fit_attempts": n("transform"), "neural_fit_attempts": n("neural"),
        "ridge_fit_attempts": n("ridge"), "test_fit_count_lower_bound": test_lower,
        "head_fit_attempts_total": n("readout") + n("neural") + n("ridge") + test_lower,
        "head_fit_completed_total": sum(row.get('fit_category') in ('readout','neural','ridge') for row in route_completed),
        "head_fit_attempts_lower_bound": n("readout") + n("neural") + n("ridge") + test_lower,
        "head_fit_completed_lower_bound": sum(row.get('fit_category') in ('readout','neural','ridge') for row in route_completed),
        "test_fit_count_unknown": test_unknown, "model_file_count": sum(int(row.get("model_file_count", 0)) for row in units),
        "prediction_file_count": sum(int(row.get("prediction_file_count", 0)) for row in units),
        "source_run_count": source_run_count, "plan_runs_excluded": True,
        "unknown_fit_units": sum(row.get("status") == "UNKNOWN" for row in units),
        "inflight_fit_unknown": 0,
        "unknown_test_categories": unknown_categories,
        "unknown_test_fit_count_lower_bound": 0 if unknown_categories else None,
        "unknown_test_fit_count_upper_bound": None if unknown_categories else 0,
        "test_fit_completion_count": None,
        "test_fit_completion_unknown_count": test_completion_unknown,
    }


def receipt_field_coverage(units: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    units = list(units)
    rows = [row for row in units if row.get("attempted") is True]
    denominator = len(rows)
    output = []
    for field in MANDATORY_RECEIPT_FIELDS:
        explicit = sum(field in row.get("receipt_field_present", []) and
                       field not in row.get("receipt_field_aliases", {}) for row in rows)
        aliased = sum(field in row.get("receipt_field_aliases", {}) for row in rows)
        inherited = sum(field in row.get("inherited_fields", []) for row in rows)
        present = explicit + aliased + inherited
        output.append({"field": field, "attempted_units": denominator,
                       "explicit_count": explicit, "alias_count": aliased,
                       "inherited_count": inherited, "present_count": present,
                       "missing_count": denominator - present,
                       "coverage_fraction": (present / denominator if denominator else None)})
    return output


def _write_rows(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    rows = [dict(row) for row in rows]
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, sort_keys=True, default=str) if isinstance(value, (dict, list, tuple)) else value
                             for key, value in row.items()})


def run(config, registry, site, dest, public, report):
    """Emit private per-fit evidence and public aggregate accounting."""
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("SLURM_REQUIRED_FIT_ACCOUNTING")
    dest, public, report = Path(dest), Path(public), Path(report)
    root = Path(site.get("root")) if isinstance(site, Mapping) and site.get("root") else dest.resolve().parents[2]
    units, sources = discover_fit_units(root / "private" / "auditory_next_v2")
    summary = summarize_fit_units(units, source_run_count=len(sources.get("runs", [])))
    summary["inflight_fit_unknown"] = sum(int(source.get("repair_inflight_unknown_count", 0))
                                           for source in sources.get("runs", []))
    # Include both per-fit files and route-level summaries.  Paths are private;
    # the public digest is only an aggregate integrity marker.
    model_hash_records = [{"run": unit["run"], "fit_id": unit["fit_id"], "sha256": digest}
                          for unit in units for digest in unit.get("model_hashes", [])]
    prediction_hash_records = [{"run": unit["run"], "fit_id": unit["fit_id"], "sha256": digest}
                               for unit in units for digest in unit.get("prediction_hashes", [])]
    model_hash_records.extend({"run": source["run"], **row} for source in sources.get("runs", [])
                               for row in source.get("model_artifacts", []))
    prediction_hash_records.extend({"run": source["run"], **row} for source in sources.get("runs", [])
                                   for row in source.get("prediction_artifacts", []))
    summary.update({"model_artifact_count": len(model_hash_records),
                    "prediction_artifact_count": len(prediction_hash_records),
                    "model_summary_hash": _stable_json_hash(model_hash_records),
                    "prediction_summary_hash": _stable_json_hash(prediction_hash_records)})
    unknown = (summary["fit_unresolved"] > 0 or summary["test_fit_count_unknown"] > 0 or
               summary["unknown_fit_units"] > 0 or summary["inflight_fit_unknown"] > 0 or
               summary["test_fit_completion_unknown_count"] > 0)
    summary.update({"status": "FIT_ACCOUNTING_PARTIAL" if unknown else "FIT_ACCOUNTING_COMPLETE",
                    "scientific_status": "NOT_EVALUATED", "receipt_schema_version": "15.2",
                    "config_hash": _stable_json_hash(config), "registry_hash": _stable_json_hash(registry),
                    "mandatory_receipt_fields": list(MANDATORY_RECEIPT_FIELDS)})
    dest.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    (dest / "fit_units.json").write_text(json.dumps(units, indent=2, sort_keys=True, default=str))
    _write_rows(dest / "fit_units.csv", units)
    file_rows = []
    for unit in units:
        for row in unit.get("model_file_digests", []):
            file_rows.append({"run": unit["run"], "fit_id": unit["fit_id"], "file_kind": "model",
                              "file_path": row["path"], "sha256": row["sha256"]})
        for row in unit.get("prediction_file_digests", []):
            file_rows.append({"run": unit["run"], "fit_id": unit["fit_id"], "file_kind": "prediction",
                              "file_path": row["path"], "sha256": row["sha256"]})
    for source in sources.get("runs", []):
        for row in source.get("model_artifacts", []):
            file_rows.append({"run": source["run"], "fit_id": "__run_summary__", "file_kind": "model_summary",
                              "relative_path": row["relative_path"], "sha256": row["sha256"]})
        for row in source.get("prediction_artifacts", []):
            file_rows.append({"run": source["run"], "fit_id": "__run_summary__", "file_kind": "prediction_summary",
                              "relative_path": row["relative_path"], "sha256": row["sha256"]})
    _write_rows(dest / "fit_file_digests.csv", file_rows)
    (dest / "input_sources.json").write_text(json.dumps(sources, indent=2, sort_keys=True))
    from .receipt_enrichment import enrich_unit
    source_by_run = {row['run']: row for row in sources['runs']}
    enriched = [dict(run=unit['run'], fit_category=unit['fit_category'],
        attempted=unit['attempted'], completed=unit['completed'],
        receipt_files=unit['receipt_files'],
        **enrich_unit(unit, source_by_run.get(unit['run'], {})))
        for unit in units if unit.get('attempted') is True and unit.get('fit_category') != 'test']
    (dest/'enriched_fit_receipts.json').write_text(json.dumps(enriched,indent=2,sort_keys=True,default=str))
    receipt_digests = {path: hash_file(path) for path in sorted({path for row in enriched for path in row['receipt_files']})}
    (dest/'enriched_receipt_source_hashes.json').write_text(json.dumps(receipt_digests,indent=2,sort_keys=True))
    enriched_coverage = []
    for field in MANDATORY_RECEIPT_FIELDS:
        origins = [row['field_origin'][field] for row in enriched]
        categories = ['unknown' if value == 'unknown' else 'native' if value == 'native' else
            'alias' if value.startswith('alias:') else 'inherited' if value.startswith('inherited:') else 'derived'
            for value in origins]
        enriched_coverage.append(dict(field=field, attempted_units=len(enriched),
            **{kind+'_count':categories.count(kind) for kind in ('native','alias','derived','inherited','unknown')}))
    _write_rows(public/'receipt_enrichment_coverage.csv', enriched_coverage)
    public_counts = dict(summary)
    (public / "fit_counts.json").write_text(json.dumps(public_counts, indent=2, sort_keys=True, default=str))
    _write_rows(public / "fit_counts.csv", [public_counts])
    coverage = receipt_field_coverage(units)
    _write_rows(public / "receipt_field_coverage.csv", coverage)
    (public / "receipt_field_coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True))
    (report / "fit_accounting.md").write_text(
        "# v2 fit accounting\n\n" + f"Status: `{summary['status']}`.\n\n" +
        "Only explicit fit starts or legacy fit receipts are counted. Prepared cases, plans, recovery reuse, and absent early test-ledger families remain separately marked.\n")
    return provenance_finish(dest, public, summary)
