"""Pure contract tests for fit_accounting; execution is owned by a Slurm gate."""

import json

from auditory_next.fit_accounting import (
    MANDATORY_RECEIPT_FIELDS,
    account_c2s_ledger,
    account_fit_directory,
    discover_fit_units,
    receipt_field_coverage,
    status_class,
    summarize_fit_units,
)
from auditory_next.fit_accounting import _fit_category


def test_status_never_promotes_unknown_or_prepared_receipt():
    assert status_class({"status": "PASS"}) == "COMPLETED"
    assert status_class({"status": "OPTIMIZATION_UNRESOLVED"}) == "NUMERICAL_FAILURE"
    assert status_class({"status": "prepared"}) == "UNRESOLVED"


def test_family_is_authoritative_for_synthetic_and_a2_categories():
    assert _fit_category("synthetic_001", {"family": "mlp32"}) == "neural"
    assert _fit_category("synthetic_001", {"family": "ridge"}) == "ridge"


def test_fit_folder_counts_start_once_and_missing_completion_is_unresolved(tmp_path):
    folder = tmp_path / "fit0"
    folder.mkdir()
    (folder / "start.json").write_text(json.dumps({"fit_id": "fit0", "family": "logistic"}))
    unit = account_fit_directory("N3_core_001", folder)
    assert unit["attempted"] is True
    assert unit["completed"] is None
    assert unit["status"] == "UNRESOLVED"
    (folder / "completion.json").write_text(json.dumps({"status": "OPTIMIZATION_STABLE"}))
    unit = account_fit_directory("N3_core_001", folder)
    assert unit["completed"] is True


def test_c2s_started_pass_rows_are_one_fit(tmp_path):
    ledger = tmp_path / "fit_ledger.jsonl"
    rows = [
        {"outer_fold": 0, "inner_fold": 1, "view": "S0", "C": 1, "scope_hash": "s", "status": "STARTED"},
        {"outer_fold": 0, "inner_fold": 1, "view": "S0", "C": 1, "scope_hash": "s", "status": "PASS"},
    ]
    ledger.write_text("\n".join(json.dumps(row) for row in rows))
    units = account_c2s_ledger("C2S_core_001", ledger)
    assert len(units) == 1
    assert units[0]["completed"] is True


def test_prepare_dirs_are_not_fit_evidence(tmp_path):
    v2 = tmp_path / "private" / "auditory_next_v2"
    run = v2 / "C2R_inputs_001"
    run.mkdir(parents=True)
    (run / "start.json").write_text(json.dumps({"run": run.name, "source_hashes": {}}))
    case = run / "cases" / "x"
    case.mkdir(parents=True)
    (case / "case.json").write_text("{}")
    (case / "inner0" ).mkdir()
    (case / "inner0" / "receipt.json").write_text("{}")
    units, _ = discover_fit_units(v2)
    assert units == []


def test_summary_keeps_unknown_early_test_family_out_of_zero_completed():
    unit = {"attempted": True, "completed": True, "numerical_failure": False,
            "reused": False, "fit_category": "test", "status": "COMPLETED",
            "count": 13, "receipt_field_present": []}
    unknown = {"attempted": None, "completed": None, "numerical_failure": None,
               "reused": False, "fit_category": "test", "status": "UNKNOWN",
               "receipt_field_present": []}
    summary = summarize_fit_units([unit, unknown], source_run_count=1)
    assert summary["test_fit_count_lower_bound"] == 13
    assert summary["fit_attempts_lower_bound"] == 13
    assert summary["test_fit_count_unknown"] == 1
    assert summary["fit_completed"] == 0
    assert summary["test_fit_completion_unknown_count"] == 13


def test_coverage_is_explicit_and_does_not_fill_missing_fields():
    rows = [{"attempted": True, "receipt_field_present": ["fit_id"]}]
    coverage = {row["field"]: row for row in receipt_field_coverage(rows)}
    assert coverage["fit_id"]["present_count"] == 1
    assert coverage["model_hash"]["present_count"] == 0
    assert set(MANDATORY_RECEIPT_FIELDS) == set(coverage)


def test_scope_and_numerical_aliases_are_recorded_as_aliases():
    from auditory_next.fit_accounting import _unit
    row = _unit("C2S_core_001", "ledger", "f", {
        "scope_hash": "s", "feature_hash": "x", "feature_scope_id": "task",
        "label_hash": "labels", "numerical_status": "PASS"})
    assert "training_scope_hash" in row["receipt_field_present"]
    assert row["receipt_field_aliases"]["optimizer_status"] == "numerical_status"
    assert "feature_scope_hash" not in row["receipt_field_present"]
    assert "label_map_hash" not in row["receipt_field_present"]


def test_test_entries_never_become_successful_models(tmp_path):
    run=tmp_path/'tests_fixture'; run.mkdir()
    (run/'start.json').write_text('{}')
    (run/'completion.json').write_text('{"status":"PASS"}')
    (run/'test_fit_counts.json').write_text('{"logistic":2,"neural":0,"ridge":1}')
    units,_=discover_fit_units(tmp_path)
    assert all(row['completed'] is None for row in units)
    assert {row['status'] for row in units}=={'COUNT_RECORDED','NO_FIT'}
    summary=summarize_fit_units(units)
    assert summary['head_fit_attempts_total']==3
    assert summary['head_fit_completed_total']==0
    assert summary['test_fit_completion_unknown_count']==3
    assert summary['fit_unresolved']==0


def test_early_count_requires_actual_world_call_and_passed_target_cases(tmp_path):
    from auditory_next.fit_accounting import _derive_early_test_counts
    run=tmp_path/'tests_003'
    testdir=run/'source/tests/auditory_next'; testdir.mkdir(parents=True)
    module=run/'source/auditory_next'; module.mkdir()
    (testdir/'test_a2.py').write_text('''
def test_three_worlds_share_conditions_and_fit_never_sees_test_values():
    for mechanism in MECHANISMS:
        audit_residual_world(world)
        audit_residual_world(world)
def test_real_predictable_nuisance_and_signal_are_distinct_constructed_cases():
    fit_background(x,y,alpha=.1)
''')
    (module/'a2_residual_audit.py').write_text('''
MECHANISMS=('null','predictable_nuisance','individual_stimulus')
def audit_residual_world(world):
    return fit_background(x,y)
''')
    names=['test_three_worlds_share_conditions_and_fit_never_sees_test_values',
        'test_real_predictable_nuisance_and_signal_are_distinct_constructed_cases']
    xml='<testsuites><testsuite>'+''.join('<testcase name="'+name+'" />' for name in names)
    xml+='<testcase name="unrelated"><failure/></testcase></testsuite></testsuites>'
    (run/'tests.xml').write_text(xml)
    counts,evidence=_derive_early_test_counts(run)
    assert counts==dict(ridge=7,logistic=0,neural=0) and evidence['status']=='DERIVED_EXACT'
    (run/'tests.xml').write_text(xml.replace('name="'+names[0]+'" />','name="'+names[0]+'"><skipped/></testcase>'))
    assert _derive_early_test_counts(run)[0]=={}


def test_repair_without_final_receipt_has_unknown_inflight_count(tmp_path):
    from auditory_next.fit_accounting import repair_unstarted_unknown_count
    assert repair_unstarted_unknown_count('C2R_core_001',tmp_path)==1
    assert repair_unstarted_unknown_count('C2R_inputs_001',tmp_path)==0
    (tmp_path/'completion.json').write_text('{"status":"NUMERICAL_INCOMPLETE"}')
    assert repair_unstarted_unknown_count('C2R_core_001',tmp_path)==0
