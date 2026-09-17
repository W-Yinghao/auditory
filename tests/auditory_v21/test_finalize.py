"""Pure receipt-fixture tests for the zero-fit final aggregator."""

import json
from pathlib import Path

import pytest

from auditory_v21.finalize import (
    _classify_receipt,
    _count_fit_events,
    _normalise_expected_runs,
    _normalize_test_fit_counts,
    _route,
    run,
)


def test_expected_run_records_and_routes_are_normalized():
    config = {"finalize": {"expected_runs": [
        "evaluation_N1_R_SIM_001",
        {"run": "real_N3_L0_001", "primary": True, "allow_conditional_stop": True},
        {"name": "closure_001", "kind": "closure", "required": False},
    ]}}
    rows = _normalise_expected_runs(config)
    assert [(row["kind"], row["packet"], row["mode"]) for row in rows] == [
        ("evaluation", "N1", "R_SIM"),
        ("real", "N3", "L0"),
        ("closure", "", ""),
    ]
    assert rows[1]["primary"] is True
    assert rows[2]["required"] is False
    assert _route("real_N3_L0_001", "real") == ("N3", "L0")


def test_fit_events_count_attempts_and_failures_without_dropping_failed_events(tmp_path: Path):
    path = tmp_path / "fit_events.jsonl"
    path.write_text(
        '{"event":"start","kind":"head","name":"private"}\n'
        '{"event":"failed","kind":"head","name":"private"}\n'
        '{"event":"start","kind":"transform"}\n'
        '{"event":"completed","kind":"transform"}\n'
        'not-json\n', encoding="utf-8")
    result = _count_fit_events(path)
    assert result["attempts"] == 2
    assert result["completed"] == 1
    assert result["failed"] == 1
    assert result["malformed_lines"] == 1
    assert result["by_kind"]["head"]["failed"] == 1


def test_test_fit_count_formats_keep_named_and_aggregate_counts():
    flat = _normalize_test_fit_counts({
        "head_attempts": 39, "head_completed": 38,
        "temperature_calls": 12, "transform_calls": 42,
    })
    assert flat["head_attempts"] == 39
    assert flat["head_completed"] == 38
    assert flat["temperature_attempts"] == 12
    assert flat["transform_attempts"] == 42
    assert flat["attempts"] == 93
    nested = _normalize_test_fit_counts({"head": {"attempts": 2, "failed": 1},
                                         "calibration": {"attempts": 3, "completed": 3}})
    assert nested["head_attempts"] == 2
    assert nested["head_failed"] == 1
    assert nested["calibration_completed"] == 3
    assert nested["attempts"] == 5


def test_conditional_real_stop_is_not_a_scientific_negative():
    receipt = {"status": "CONDITIONALLY_STOPPED", "reason": "CAPABILITY_NOT_PASS",
               "scientific_effect_status": "NOT_EVALUATED"}
    result = _classify_receipt(receipt, kind="real", allow_conditional_stop=True)
    assert result["status"] == "CONDITIONAL_STOP"
    assert result["scientific_status"] == "CONDITIONALLY_STOPPED_NOT_NEGATIVE"
    assert result["acceptable"] is True


def test_capability_failure_and_missing_receipt_are_incomplete():
    failed = _classify_receipt({"capability_status": "FAIL", "status": "FAIL"})
    missing = _classify_receipt(None, file_status="MISSING")
    assert failed["status"] == "FAILED"
    assert failed["acceptable"] is False
    assert missing["status"] == "MISSING"
    assert missing["scientific_status"] == "NOT_EVALUATED"


def test_run_retains_optional_failure_and_accepts_gated_real_stop(tmp_path: Path, monkeypatch):
    root = tmp_path / "root"
    store = root / "private" / "auditory_v21"
    results = root / "results" / "auditory_v21"

    def private_receipt(name, value):
        path = store / name
        path.mkdir(parents=True)
        (path / "completion.json").write_text(json.dumps(value), encoding="utf-8")

    private_receipt("old_failed", {"status": "FAILED"})
    (store / "old_failed" / "failure.json").write_text(json.dumps({"type":"ValueError","message":"fixture failure"}))
    private_receipt("n2_inputs_001", {"status": "N2_INPUTS_BLOCKED", "support": "BLOCKED"})
    private_receipt("evaluation_N1_R_SIM_001", {
        "status": "CAPABILITY_COMPLETE", "capability_status": "FAIL",
        "finite_prediction_status": "PASS", "budget_execution_status": "COMPLETE",
        "worlds_planned": 2, "worlds_evaluated": 2, "unevaluable": 0,
    })
    route = results / "real_N1_R_SIM_001"
    route.mkdir(parents=True)
    (route / "route_decision.json").write_text(json.dumps({
        "status": "CONDITIONALLY_STOPPED", "reason": "CAPABILITY_NOT_PASS",
        "support_status": "BLOCKED",
    }), encoding="utf-8")

    monkeypatch.setenv("SLURM_JOB_ID", "fixture")
    summary = run(
        root, root / "private" / "auditory_v21" / "finalize_001",
        root / "final_results", root / "reports", {
            "finalize": {"expected_runs": [
                {"run": "old_failed", "required": False},
                "n2_inputs_001", "evaluation_N1_R_SIM_001",
                {"run": "real_N1_R_SIM_001", "primary": True},
            ]}
        })
    assert summary["status"] == "FINAL_AGGREGATE_COMPLETE"
    assert summary["required_failed_runs"] == []
    assert summary["conditional_stopped_real_runs"] == ["real_N1_R_SIM_001"]
    assert summary["n2_support_status"] == "BLOCKED"
    assert summary["n2_independent_capability_pending"] is False
    assert (root / "final_results" / "four_axis_routes.csv").exists()
