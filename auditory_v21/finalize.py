"""Zero-fit aggregation of the frozen auditory v2.1 run receipts.

The final pass is deliberately a receipt audit.  It reads JSON/JSONL and CSV
metadata from earlier runs, counts historical fit events, and writes a
provenance manifest.  It does not import a model implementation, load EEG,
fit a head, or turn a stopped capability lane into a scientific result.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_RUNS = (
    "stage0_001", "development_001", "launch_review_001",
    "input_preflight_003", "n2_design_001", "n2_inputs_001", "closure_001",
    "evaluation_N1_R_SIM_001", "evaluation_N1_L0_001",
    "evaluation_N3_R_SIM_001", "evaluation_N3_L0_001",
    "real_N1_R_SIM_001", "real_N1_L0_001",
    "real_N3_R_SIM_001", "real_N3_L0_001",
)

_EVALUATION = {"evaluation", "capability", "eval"}
_REAL = {"real", "real_comparison"}


def _json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                sort_keys=True, allow_nan=False) + "\n",
                     encoding="utf-8")


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _run_kind(name: str, explicit: Any = None) -> str:
    value = str(explicit or "").strip().lower()
    if value in _REAL:
        return "real"
    if value in _EVALUATION:
        return "evaluation"
    lowered = name.lower()
    if lowered.startswith("real_"):
        return "real"
    if lowered.startswith("evaluation_") or lowered.startswith("capability_"):
        return "evaluation"
    if lowered.startswith("stage0"):
        return "stage0"
    if lowered.startswith("development"):
        return "development"
    if lowered.startswith("launch_review"):
        return "launch_review"
    if lowered.startswith("input_preflight"):
        return "input_preflight"
    if lowered.startswith("n2_design"):
        return "n2_design"
    if lowered.startswith("n2_inputs"):
        return "n2_inputs"
    if lowered.startswith("closure"):
        return "closure"
    return value or "other"


def _route(name: str, kind: str) -> tuple[str, str]:
    """Return packet and mode while retaining only public route labels."""
    if kind in {"evaluation", "real"}:
        parts = name.split("_")
        # evaluation_N1_R_SIM_001 and real_N3_L0_001
        if len(parts) >= 4:
            packet = parts[1]
            mode = "_".join(parts[2:-1])
            return packet, mode
    return "", ""


def _normalise_expected_runs(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Normalize both the compact and record-shaped finalizer config forms."""
    section = config.get("finalize")
    if not isinstance(section, Mapping):
        section = config
    configured = section.get("expected_runs", section.get("runs", section.get("required_runs")))
    if configured is None:
        configured = DEFAULT_RUNS
    if isinstance(configured, Mapping):
        configured = [dict((({"run": key} | dict(value)) if isinstance(value, Mapping)
                           else {"run": key})) for key, value in configured.items()]
    records: list[dict[str, Any]] = []
    for item in configured:
        if isinstance(item, str):
            record = {"run": item}
        elif isinstance(item, Mapping):
            record = dict(item)
            record["run"] = record.get("run", record.get("name"))
        else:
            continue
        name = str(record.get("run") or "").strip()
        if not name:
            continue
        kind = _run_kind(name, record.get("kind", record.get("axis")))
        packet, mode = _route(name, kind)
        records.append({
            "run": name,
            "kind": kind,
            "packet": str(record.get("packet", packet) or ""),
            "mode": str(record.get("mode", mode) or ""),
            "required": bool(record.get("required", True)),
            "allow_conditional_stop": bool(record.get(
                "allow_conditional_stop", kind == "real")),
            "primary": bool(record.get("primary", False)),
        })
    return records


def _read_receipt(path: Path) -> tuple[Any, str]:
    if not path.exists() or not path.is_file():
        return None, "MISSING"
    try:
        return _json(path), "PRESENT"
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None, "MALFORMED"


def _status_text(value: Any) -> str:
    pieces: list[str] = []
    keys = {"status", "capability_status", "scientific_effect_status", "reason",
            "gate_status", "support_status", "design_support_status",
            "input_status", "independent_capability_status", "support"}
    def visit(obj: Any) -> None:
        if isinstance(obj, Mapping):
            for key, child in obj.items():
                if str(key).lower() in keys:
                    if isinstance(child, (str, int, float, bool)):
                        pieces.append(str(child))
                elif isinstance(child, (Mapping, list, tuple)):
                    visit(child)
        elif isinstance(obj, (list, tuple)):
            for child in obj:
                visit(child)
    visit(value)
    if not pieces and not isinstance(value, (Mapping, list, tuple)):
        pieces.append(str(value or ""))
    return " ".join(pieces).upper()


def _classify_receipt(receipt: Any, *, kind: str = "other",
                      file_status: str = "PRESENT",
                      allow_conditional_stop: bool = False) -> dict[str, Any]:
    """Classify a receipt conservatively; stopped real work is not negative."""
    text = _status_text(receipt)
    if file_status == "MISSING":
        return {"status": "MISSING", "scientific_status": "NOT_EVALUATED",
                "acceptable": False, "conditional": False, "reason": "receipt missing"}
    if file_status == "MALFORMED":
        return {"status": "FAILED", "scientific_status": "NOT_EVALUATED",
                "acceptable": False, "conditional": False, "reason": "receipt malformed"}
    stopped = "CONDITIONALLY_STOPPED" in text or "CONDITIONAL_STOP" in text
    if kind == "real" and stopped:
        conditional = allow_conditional_stop
        return {"status": "CONDITIONAL_STOP", "scientific_status":
                "CONDITIONALLY_STOPPED_NOT_NEGATIVE", "acceptable": conditional,
                "conditional": True, "reason": "capability/support gate stopped real lane"}
    if kind == "evaluation" and isinstance(receipt, Mapping):
        finite = str(receipt.get("finite_prediction_status", "")).upper()
        budget = str(receipt.get("budget_execution_status", "")).upper()
        planned = _number(receipt.get("worlds_planned"))
        evaluated = _number(receipt.get("worlds_evaluated"))
        unevaluable = _number(receipt.get("unevaluable"))
        if (finite == "PASS" and budget == "COMPLETE" and planned is not None and
                evaluated == planned and unevaluable == 0):
            capability = str(receipt.get("capability_status", "PASS")).upper()
            return {"status": "COMPLETE", "scientific_status": capability,
                    "acceptable": True, "conditional": False,
                    "reason": "all finite capability worlds completed"}
    failure_tokens = {"FAIL", "FAILED", "FAILURE", "ERROR", "WITH_FAILURES", "INCOMPLETE"}
    if (any(token in failure_tokens for token in text.split()) or
            "CAPABILITY_STATUS_FAIL" in text or
            any(token in text for token in ("_FAILED", "_FAILURE", "_INCOMPLETE"))):
        return {"status": "FAILED", "scientific_status": "NOT_EVALUATED",
                "acceptable": False, "conditional": False, "reason": "receipt reports failure"}
    if stopped:
        return {"status": "CONDITIONAL_STOP", "scientific_status": "NOT_EVALUATED",
                "acceptable": False, "conditional": True, "reason": "conditional stop"}
    if not isinstance(receipt, Mapping):
        return {"status": "FAILED", "scientific_status": "NOT_EVALUATED",
                "acceptable": False, "conditional": False, "reason": "receipt is not an object"}
    status = str(receipt.get("status", "")).upper()
    if status in {"", "UNKNOWN", "NOT_EVALUATED", "NOT_EVALUATED_INDEPENDENTLY"}:
        # A present infrastructure receipt is complete as an audit input, even
        # when it explicitly says that an independent scientific capability
        # was not run.
        return {"status": "PRESENT", "scientific_status": status or "NOT_EVALUATED",
                "acceptable": True, "conditional": False, "reason": "receipt present"}
    return {"status": "COMPLETE", "scientific_status":
            str(receipt.get("scientific_effect_status", status)),
            "acceptable": True, "conditional": False, "reason": "receipt present"}


def _event_kind(value: Any) -> str:
    return str(value or "unknown").strip().lower()


def _count_fit_events(path: Path | None) -> dict[str, Any]:
    """Count all start/completed/failed JSONL event shapes without identities."""
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"attempts": 0, "completed": 0, "failed": 0})
    lines = malformed = 0
    if path is None or not path.exists():
        return {"event_lines": 0, "malformed_lines": 0, "by_kind": {},
                "attempts": 0, "completed": 0, "failed": 0}
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            lines += 1
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, UnicodeError):
                malformed += 1
                continue
            if not isinstance(event, Mapping):
                malformed += 1
                continue
            kind = _event_kind(event.get("kind", event.get("fit_kind")))
            event_name = str(event.get("event", event.get("status", ""))).lower()
            bucket = counts[kind]
            if event_name in {"start", "started", "attempt", "attempted"}:
                bucket["attempts"] += 1
            elif event_name in {"completed", "complete", "success", "succeeded", "pass"}:
                bucket["completed"] += 1
            elif event_name in {"failed", "failure", "error"}:
                bucket["failed"] += 1
    return {
        "event_lines": lines,
        "malformed_lines": malformed,
        "by_kind": {key: dict(value) for key, value in sorted(counts.items())},
        "attempts": sum(v["attempts"] for v in counts.values()),
        "completed": sum(v["completed"] for v in counts.values()),
        "failed": sum(v["failed"] for v in counts.values()),
    }


def _merge_count(target: dict[str, int], key: str, value: Any) -> None:
    number = _number(value)
    if number is not None:
        target[key] = target.get(key, 0) + number


def _normalize_test_fit_counts(value: Any) -> dict[str, int]:
    """Normalize flat, nested, and event-list test ledger formats."""
    result: dict[str, int] = {}
    aliases = {"attempts": "attempts", "attempt": "attempts", "calls": "attempts",
               "completed": "completed", "success": "completed", "failed": "failed",
               "failure": "failed"}
    def visit(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, Mapping):
            event = str(obj.get("event", obj.get("status", ""))).lower()
            event_kind = _event_kind(obj.get("kind", obj.get("fit_kind")))
            if event in {"start", "started", "attempt", "attempted",
                         "completed", "complete", "success", "succeeded", "pass",
                         "failed", "failure", "error"} and event_kind != "unknown":
                phase = ("attempts" if event in {"start", "started", "attempt", "attempted"}
                         else "completed" if event in {"completed", "complete", "success", "succeeded", "pass"}
                         else "failed")
                _merge_count(result, f"{event_kind}_{phase}", 1)
                _merge_count(result, phase, 1)
            for key, child in obj.items():
                lower = str(key).lower()
                if lower in {"head_attempts", "head_completed", "head_failed",
                                "temperature_calls", "transform_calls", "fit_attempts",
                                "fit_completed", "fit_failed"}:
                    label = lower.replace("_calls", "_attempts")
                    _merge_count(result, label, child)
                    if lower.endswith("_calls"):
                        _merge_count(result, "attempts", child)
                    elif lower.endswith("_attempts"):
                        _merge_count(result, "attempts", child)
                    elif lower.endswith("_completed"):
                        _merge_count(result, "completed", child)
                    elif lower.endswith("_failed"):
                        _merge_count(result, "failed", child)
                elif lower in aliases and _number(child) is not None:
                    label = f"{prefix}_{aliases[lower]}" if prefix else aliases[lower]
                    _merge_count(result, label, child)
                    _merge_count(result, aliases[lower], child)
                else:
                    visit(child, lower)
        elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
            for child in obj:
                visit(child, prefix)
    visit(value)
    return result


def _candidate_receipt_paths(base: Path, run: str) -> list[Path]:
    private_dir = base / "private" / "auditory_v21" / run
    results_dir = base / "results" / "auditory_v21" / run
    return [private_dir / "completion.json", results_dir / "summary.json",
            results_dir / "capability_receipt.json", results_dir / "route_decision.json",
            private_dir / "completion.json"]


def _find_receipt(root: Path, run: str) -> tuple[Any, Path | None, str]:
    seen: set[Path] = set()
    for path in _candidate_receipt_paths(root, run):
        if path in seen:
            continue
        seen.add(path)
        receipt, status = _read_receipt(path)
        if status != "MISSING":
            return receipt, path, status
    return None, None, "MISSING"


def _n2_support_status(receipts: Mapping[str, Any], config: Mapping[str, Any]) -> str:
    # A config may describe the intended branch, but cannot override a saved
    # N2 receipt.  Search the nested ``support`` object and its aggregate keys.
    for name in ("n2_inputs_001", "n2_design_001", "stage0_001"):
        receipt = receipts.get(name)
        if isinstance(receipt, Mapping) and isinstance(receipt.get("support"), Mapping):
            support_text = _status_text(receipt["support"])
        else:
            support_text = _status_text(receipt)
        if any(token in support_text for token in ("BLOCK", "LIMITED", "INSUFFICIENT", "NECESSARY_SUPPORT_ONLY")):
            return "BLOCKED"
        if any(token in support_text for token in ("PASS", "SUFFICIENT", "DESIGN_SUPPORT_PRESENT",
                                                   "COMMON_HISTORY_SUPPORT_WITH_FIXED_QUOTAS")):
            return "PASS"
    return "UNKNOWN"


def _real_stop_allowed(item: Mapping[str, Any], n2_status: str) -> bool:
    if bool(item.get("allow_conditional_stop")):
        return True
    return n2_status in {"BLOCKED", "SUPPORT_BLOCKED", "NOT_SUPPORTED"}


def _conditional_real_valid(root: Path, run: str, receipt: Any) -> bool:
    """Require evidence for a stopped route's capability/support gate."""
    reason = _status_text(receipt)
    if any(token in reason for token in ("SOURCE_CHANGED", "SCOPE_MISMATCH",
                                         "INPUT_MANIFEST_CHANGED", "HASH_MISMATCH")):
        return False
    cap_name = run.replace("real_", "evaluation_", 1)
    cap, _, cap_status = _find_receipt(root, cap_name)
    cap_text = _status_text(cap)
    cap_failed = (cap_status == "PRESENT" and
                  ("NOT_EVALUATED" in cap_text or "BLOCKED" in cap_text or
                   any(token in cap_text.split() for token in ("FAIL", "FAILED", "INCOMPLETE"))))
    genuine_input_block = "SOURCE_OR_SUPPORT_BLOCKED" in reason or "INPUT_BLOCKED" in reason
    return cap_failed or genuine_input_block


def _fit_event_path(root: Path, run: str) -> Path:
    run_dir = root / "private" / "auditory_v21" / run
    metadata_ledger = run_dir / "metadata_fit_ledger.jsonl"
    if metadata_ledger.exists():
        return metadata_ledger
    return run_dir / "fit_events.jsonl"


def run(root: Path, private: Path, public: Path, report: Path,
        config: dict) -> dict[str, Any]:
    """Aggregate frozen receipts.  Must be invoked by a Slurm worker."""
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("SLURM_REQUIRED")
    root, private, public, report = map(Path, (root, private, public, report))
    private.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    expected = _normalise_expected_runs(config)
    receipt_values: dict[str, Any] = {}
    inventory: list[dict[str, Any]] = []
    fit_rows: list[dict[str, Any]] = []
    historical_test_counts: dict[str, int] = {}
    historical_event_kinds: dict[str, dict[str, int]] = defaultdict(
        lambda: {"attempts": 0, "completed": 0, "failed": 0})
    manifest: dict[str, Any] = {"zero_fit": True, "artifacts": {}}
    missing: list[str] = []
    failed: list[str] = []
    for item in expected:
        name, kind = item["run"], item["kind"]
        receipt, receipt_path, file_status = _find_receipt(root, name)
        receipt_values[name] = receipt
        # A failure receipt has priority over a stale completion/summary.
        failure_path = root / "private" / "auditory_v21" / name / "failure.json"
        if failure_path.exists():
            failure_receipt, failure_status = _read_receipt(failure_path)
            if isinstance(failure_receipt, Mapping):
                failure_receipt = dict(failure_receipt, status="FAILED")
            receipt = dict(failure_receipt, status='FAILED') if isinstance(failure_receipt, Mapping) else {'status':'FAILED'}
            receipt_path, file_status = failure_path, failure_status
            receipt_values[name] = receipt
        allowed_stop = _real_stop_allowed(item, "UNKNOWN")
        classification = _classify_receipt(receipt, kind=kind, file_status=file_status,
                                            allow_conditional_stop=allowed_stop)
        events_path = _fit_event_path(root, name)
        event_counts = _count_fit_events(events_path)
        test_path = root / "private" / "auditory_v21" / name / "test_fit_counts.json"
        test_counts: dict[str, int] = {}
        if test_path.exists():
            try:
                test_counts = _normalize_test_fit_counts(_json(test_path))
            except (OSError, json.JSONDecodeError, UnicodeError):
                test_counts = {"malformed": 1}
        for key, value in test_counts.items():
            _merge_count(historical_test_counts, key, value)
        for key, value in event_counts["by_kind"].items():
            for phase in ("attempts", "completed", "failed"):
                historical_event_kinds[key][phase] += int(value.get(phase, 0))
        fit_rows.append({"run": name, "kind": kind,
                         "event_attempts": event_counts["attempts"],
                         "event_completed": event_counts["completed"],
                         "event_failed": event_counts["failed"],
                         "event_lines": event_counts["event_lines"],
                         "test_counts": json.dumps(test_counts, sort_keys=True),
                         "zero_fit_finalizer": True})
        route_axis = "capability" if kind == "evaluation" else kind
        packet, mode = item["packet"], item["mode"]
        scientific = classification["scientific_status"]
        inventory.append({"run": name, "kind": kind, "route_axis": route_axis,
                          "packet": packet, "mode": mode,
                          "status": classification["status"],
                          "receipt_status": file_status,
                          "scientific_status": scientific,
                          "primary": item["primary"],
                          "capability_status": _status_text(receipt)[:160],
                          "support_status": "BLOCKED" if "BLOCK" in _status_text(receipt) else "",
                          "fit_attempts": event_counts["attempts"],
                          "fit_failures": event_counts["failed"],
                          "notes": classification["reason"]})
        if classification["status"] == "MISSING" and item["required"]:
            missing.append(name)
        elif (classification["status"] == "FAILED" and item["required"]):
            failed.append(name)
        if receipt_path is not None:
            manifest["artifacts"][f"{name}/receipt"] = {"sha256": _digest(receipt_path),
                                                           "status": file_status}
        for artifact, path in (("fit_events", events_path), ("test_fit_counts", test_path)):
            if path.exists():
                manifest["artifacts"][f"{name}/{artifact}"] = {"sha256": _digest(path),
                                                                  "status": "PRESENT"}

    # Conditional stop acceptability depends on the N2 support receipt.  Re-
    # classify only real rows after reading all N2 receipts.
    n2_status = _n2_support_status(receipt_values, config)
    for item, row in zip(expected, inventory):
        if item["kind"] == "real" and row["status"] == "CONDITIONAL_STOP":
            accepted = (_real_stop_allowed(item, n2_status) and
                        _conditional_real_valid(root, item["run"], receipt_values[item["run"]]))
            row["status"] = "CONDITIONAL_STOP" if accepted else "FAILED"
            row["notes"] = ("capability/support stop; not a scientific negative" if row["status"] == "CONDITIONAL_STOP"
                            else "conditional stop not authorized by config/support receipt")
            if row["status"] == "FAILED" and item["required"]:
                failed.append(item["run"])
    conditional = [row["run"] for row in inventory if row["status"] == "CONDITIONAL_STOP"]
    required_missing = sorted(set(missing))
    required_failed = sorted(set(failed))
    n2_expected = {item["run"] for item in expected
                   if item["kind"] in {"evaluation", "real"} and
                   item["packet"].upper() == "N2"}
    n2_independent_pending = n2_status == "PASS" and not n2_expected
    complete = not required_missing and not required_failed and not n2_independent_pending
    fields = ("route_axis", "packet", "mode", "run", "status", "receipt_status",
              "scientific_status", "primary", "capability_status", "support_status",
              "fit_attempts", "fit_failures", "notes")
    _write_csv(public / "four_axis_routes.csv", inventory, fields)
    _write_csv(public / "receipt_inventory.csv", inventory,
               ("run", "kind", "status", "receipt_status", "scientific_status", "notes"))
    _write_csv(public / "fit_event_counts.csv", fit_rows,
               ("run", "kind", "event_attempts", "event_completed", "event_failed",
                "event_lines", "test_counts", "zero_fit_finalizer"))
    _write_json(private / "zero_fit_hash_manifest.json", manifest)
    public_manifest = [{"artifact": key, "status": value["status"], "sha256": value["sha256"]}
                       for key, value in sorted(manifest["artifacts"].items())]
    _write_csv(public / "zero_fit_hash_manifest.csv", public_manifest,
               ("artifact", "status", "sha256"))

    section = config.get("finalize") if isinstance(config.get("finalize"), Mapping) else config
    budget = section.get("budget", section.get("job_allocation_budget", {})) if isinstance(section, Mapping) else {}
    total_fit_attempts = sum(row["event_attempts"] for row in fit_rows)
    total_fit_failures = sum(row["event_failed"] for row in fit_rows)
    summary = {
        "status": "FINAL_AGGREGATE_COMPLETE" if complete else "FINAL_AGGREGATE_INCOMPLETE",
        "implementation_status": "PASS",
        "scientific_status": "AGGREGATE_ONLY",
        "expected_runs": [item["run"] for item in expected],
        "required_missing_runs": required_missing,
        "required_failed_runs": required_failed,
        "conditional_stopped_real_runs": conditional,
        "conditional_stops_are_not_scientific_negative": True,
        "n2_support_status": n2_status,
        "n2_independent_capability_pending_when_supported": n2_independent_pending,
        "n2_independent_capability_pending": n2_independent_pending,
        "new_head_fits": 0,
        "new_encoder_fits": 0,
        "finalizer_fit_events": 0,
        "historical_fit_event_attempts": total_fit_attempts,
        "historical_fit_event_failures": total_fit_failures,
        "historical_fit_events_by_kind": {key: dict(value) for key, value in sorted(historical_event_kinds.items())},
        "historical_test_fit_counts": historical_test_counts,
        "old_primaries_preserved": True,
        "no_zero_mi_inference": True,
        "new_estimator_is_not_old_solver_repair": True,
        "job_allocation_budget": budget,
        "outputs": ["four_axis_routes.csv", "receipt_inventory.csv",
                     "fit_event_counts.csv", "zero_fit_hash_manifest.csv"],
    }
    _write_json(private / "finalize_summary.json", summary)
    report_text = _report(summary, inventory)
    (report / "FINAL_REPORT_CN.md").write_text(report_text, encoding="utf-8")
    (report / "FINAL_REPORT.md").write_text(report_text, encoding="utf-8")
    return summary


def _report(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> str:
    lines = ["# auditory v2.1 最终聚合审计", "",
             f"状态：**{summary['status']}**。本次聚合为零拟合；finalizer 新增 head/encoder fits 均为 0。",
             "所有 fit event 计数来自既有回执，仅表示历史尝试，不能替代独立能力结论。", "",
             "## 四轴路线", "", "|轴|packet|mode|run|状态|科学状态|", "|---|---|---|---|---|---|"]
    for row in rows:
        lines.append(f"|{row['route_axis']}|{row['packet']}|{row['mode']}|{row['run']}|{row['status']}|{row['scientific_status']}|")
    lines += ["", "缺失必需回执：" + ("、".join(summary["required_missing_runs"]) or "无") + "。",
              "失败必需回执：" + ("、".join(summary["required_failed_runs"]) or "无") + "。",
              f"N2 support 状态为 `{summary['n2_support_status']}`。支持阻断时，real 条件停止可关闭条件分支；条件停止保持为未评估，不能写成 EEG 科学负结果。",
              "原始 primary 结果保留；不作零 MI 推断。若使用新 estimator，其含义不等于修复旧 solver。", "",
              "历史 fit attempts：" + str(summary["historical_fit_event_attempts"]) +
              "；历史失败事件：" + str(summary["historical_fit_event_failures"]) + "。"]
    if summary.get("n2_independent_capability_pending_when_supported"):
        lines.append("N2 support 已通过时，N2 独立 capability/real 分支仍待其专门回执（除非配置另行列出并完成）。")
    return "\n".join(lines) + "\n"


__all__ = ["run", "_classify_receipt", "_count_fit_events",
           "_normalize_test_fit_counts", "_normalise_expected_runs"]
