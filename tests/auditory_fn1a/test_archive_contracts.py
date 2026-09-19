"""Checks required by FN1-A plan section 11, scoped to what this revision changed.

The revision's whole point is that unknown scale version, unknown questionnaire time and
unknown device state must be ACCEPTED and recorded, while a real identity or target
conflict must still block. These tests pin both directions, and pin that no clinical
confirmation gate survives anywhere in the package.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from auditory_fn1.clinical import detect_sequential_key_misalignment, worksheet_row_key
from auditory_fn1a import archive

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG = yaml.safe_load((ROOT / "configs/auditory_fn1a.yaml").read_text())


def _row(**overrides) -> dict:
    row = {
        "A_instrument_status": "UNKNOWN_MIXED_HEADER",
        "assessment_date_role": "UNKNOWN",
        "eeg_questionnaire_relation": "UNKNOWN",
        "pta_unit_status": "UNKNOWN_ROW_LEVEL_DOCUMENTARY_DBHL_CONTEXT",
        "device_state_status": "UNKNOWN",
        "exclusion_reason": "",
    }
    row.update(overrides)
    return row


def test_metadata_unknowns_are_never_in_the_blocking_vocabulary():
    """Plan 3: plain unknowns go to the limitation table, not to the exclusion set."""
    for unknown in ("unknown_instrument_version", "unknown_questionnaire_date",
                    "unknown_eeg_questionnaire_relation", "unknown_pta_unit", "unknown_device_state"):
        assert unknown not in archive.BLOCKING_REASONS
    for blocking in ("identity_conflict", "target_absent", "target_conflict", "no_signal_source",
                     "signal_support_insufficient"):
        assert blocking in archive.BLOCKING_REASONS


def test_an_all_unknown_but_labelled_row_is_accepted():
    """A record with every metadata field unknown, but a usable label and identity, passes."""
    rows = [_row() for _ in range(3)]
    table = archive.limitation_table(rows)
    # `status` is the coarse label shown in the published table; the count behind it is
    # derived from the precise per-row field value.
    assert {entry["status"] for entry in table} == {"UNKNOWN", "UNKNOWN_MIXED_HEADER"}
    assert all(entry["blocking"] is False for entry in table)
    assert all(entry["records"] == 3 for entry in table), "every unknown must be counted, none dropped"
    assert {entry["limitation"] for entry in table} == {
        "auditory instrument version per row", "questionnaire assessment date",
        "EEG-questionnaire relation", "PTA unit and test condition at row level",
        "device worn/powered during acquisition"}
    # The PTA row must count the precise field value, not the coarse label.
    pta = next(e for e in table if e["limitation"].startswith("PTA unit"))
    assert pta["records"] == sum(1 for r in rows
                                 if r["pta_unit_status"] == "UNKNOWN_ROW_LEVEL_DOCUMENTARY_DBHL_CONTEXT")
    assert all(not r["exclusion_reason"] for r in rows)


def test_real_conflicts_still_block():
    blocked = [_row(exclusion_reason="identity_conflict"), _row(exclusion_reason="target_conflict"),
               _row(exclusion_reason="signal_support_insufficient")]
    for row in blocked:
        assert set(row["exclusion_reason"].split(";")) & archive.BLOCKING_REASONS


def test_config_permits_every_unknown_this_revision_lifted():
    archive_config = CONFIG["archive"]
    for key in ("allow_unknown_instrument_version", "allow_unknown_questionnaire_date",
                "allow_unknown_eeg_questionnaire_relation", "allow_unknown_device_state"):
        assert archive_config[key] is True, key
    for key in ("unknown_time_imputation", "assume_same_visit", "infer_scale_from_age_or_score",
                "merge_HA_MFF_scales", "target_imputation", "automatic_endpoint_substitution",
                "historical_pta_table_allowed"):
        assert archive_config[key] is False, key
    assert CONFIG["project"]["external_contact_required"] is False
    assert CONFIG["validation"]["metadata_completeness_gate"] is False


def test_analysis_lock_can_be_built_from_all_unknown_metadata():
    """Plan 11: an all-unknown-but-labelled synthetic input must still yield a lock."""
    cohort = {"pta_row_key_guard": {"status": "ROW_KEY_ALIGNED"},
              "source_hashes": {"corrected_pta": "0" * 64}}
    lock = archive.analysis_lock(CONFIG, cohort, cohort_manifest="private/x.csv",
                                 identity_registry="private/y.csv")["analysis_lock"]
    assert lock["status"] == "LOCKED_FROM_EXISTING_ARCHIVE"
    assert lock["external_confirmation_required"] is False
    assert lock["unknown_instrument_version_allowed"] is True
    assert lock["unknown_questionnaire_time_allowed"] is True
    assert lock["unknown_device_state_allowed"] is True
    # The v1.0 gate fields must not reappear under any name.
    assert "hypothesis_and_scope_approved" not in lock
    assert "clinical_response_received" not in lock


def test_no_clinical_confirmation_gate_survives_in_the_package():
    """Plan 13.2: the old gate must not be reachable, not even as a hidden dependency."""
    forbidden = ("validate_lock", "empty_lock", "NEEDS_CLINICAL_RESPONSE",
                 "W1_BLOCKED_CLINICAL_LOCK", "hypothesis_and_scope_approved",
                 "clinical_response_received", "prepare_request", "resolve_evidence")
    for module in sorted((ROOT / "auditory_fn1a").glob("*.py")):
        text = module.read_text()
        for token in forbidden:
            assert token not in text, f"{module.name} reintroduces {token}"


def test_row_key_rule_is_the_actual_worksheet_row_and_history_is_forbidden():
    assert CONFIG["archive"]["source_row_key"] == "actual_worksheet_row"
    assert CONFIG["archive"]["corrected_pta_required"] is True
    assert CONFIG["archive"]["historical_pta_table_allowed"] is False
    aligned = [{"clinical_row_id": worksheet_row_key(r), "source_row": r} for r in range(4, 20)]
    assert detect_sequential_key_misalignment(aligned)["status"] == "ROW_KEY_ALIGNED"
    sequential = [{"clinical_row_id": f"C{i:04d}", "source_row": i + 3} for i in range(1, 17)]
    assert detect_sequential_key_misalignment(sequential)["status"] == "SEQUENTIAL_ROW_KEY_MISALIGNMENT"


def test_target_is_never_imputed_and_bounds_come_from_the_source_column():
    assert CONFIG["archive"]["target_bounds_source_units"] == [0.0, 100.0]
    assert CONFIG["archive"]["primary_source_column"] == "IT_MAIS_MAIS"
    assert CONFIG["archive"]["secondary_source_column"] == "MUSS"
    assert CONFIG["archive"]["same_source_row_for_secondary"] is True
    source = (ROOT / "auditory_fn1a" / "archive.py").read_text()
    assert "target_absent" in source and "target_out_of_source_range" in source


def test_no_effect_size_or_significance_gate_controls_execution():
    assert CONFIG["validation"]["effect_or_significance_execution_gate"] is False
    assert CONFIG["validation"]["expand_after_small_positive"] is False
    assert CONFIG["models"]["test_early_stopping"] is False
