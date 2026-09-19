"""Archive cohort assembly and the FN1-A analysis lock.

Plan sections 3, 4 and 13.2. The governing rule of this module:

    Plain metadata unknowns (scale version, questionnaire date, EEG-questionnaire
    relation, device state, PTA unit) are ACCEPTED and recorded as limitations.
    Only a real identity conflict, a real target conflict/absence, or absent signal
    support blocks the corresponding record.

There is no clinician gate here and no code path that waits for an external reply.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from auditory_fn1.clinical import detect_sequential_key_misalignment, parse_clinical_row_id

from .runtime import ROOT, ProvenanceError, digest, require_config_value, resolve_source

# Status vocabularies. UNKNOWN is a real state, never rewritten to a confirmed value.
INSTRUMENT_STATUS = ("DOCUMENTED", "UNKNOWN_MIXED_HEADER", "CONFLICT")
UNIT_STATUS = ("HA_SOURCE_COLUMN", "DOCUMENTED", "CONFLICT")
DATE_ROLE = ("QUESTIONNAIRE", "EEG_ONLY", "UNKNOWN")
RELATION = ("DOCUMENTED_SAME_VISIT", "KNOWN_INTERVAL", "UNKNOWN")

ANALYSIS_ROW_COLUMNS: tuple[str, ...] = (
    "split_group_id", "index_record_id", "source_workbook_sha256", "source_sheet",
    "source_row_number", "clinical_link_key", "link_evidence_level", "identity_conflict",
    "A_literal_header", "A_raw_value", "A_instrument_status", "A_score_unit_status",
    "MUSS_raw_value", "MUSS_instrument_status", "assessment_date", "assessment_date_role",
    "eeg_acquisition_time", "eeg_questionnaire_relation", "age_recorded_months",
    "age_at_eeg_if_derivable", "HA_duration_months", "better_unaided_pta_corrected",
    "better_aided_pta_corrected", "pta_unit_status", "pta_date_relation", "device_state_status",
    "target_A_available", "target_V_given_A_available", "source_refs", "exclusion_reason",
)

# Operational columns the analysis table must also carry. They are not part of the
# plan's schema listing but are required to locate the signal; omitting them from the
# written file silently produced "no_signal_source" for every record on the first run.
OPERATIONAL_COLUMNS: tuple[str, ...] = ("source_duration_s", "sfreq_hz", "signal_file_id")
ANALYSIS_TABLE_COLUMNS: tuple[str, ...] = ANALYSIS_ROW_COLUMNS + OPERATIONAL_COLUMNS

# Reasons that DO block a record. Metadata unknowns are deliberately absent from this set.
BLOCKING_REASONS = frozenset({
    "identity_conflict", "target_absent", "target_nonnumeric", "target_conflict",
    "target_out_of_source_range", "no_signal_source", "signal_support_insufficient",
})


def _rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _number(value: Any) -> float | None:
    text = str(value).strip()
    if text in ("", "None", "nan", "NaN"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def build_cohort(config: dict) -> dict:
    """Assemble the archive analysis list from existing, already-audited material."""
    if require_config_value(config, "archive.historical_pta_table_allowed"):
        raise ProvenanceError("HISTORICAL_PTA_TABLE_MUST_REMAIN_FORBIDDEN")

    clinical_path = resolve_source(config, "clinical_rows")
    pta_path = resolve_source(config, "corrected_pta")
    index_path = resolve_source(config, "frozen_index_cohort")
    signal_path = resolve_source(config, "signal_manifest")

    clinical = _rows(clinical_path)
    pta = _rows(pta_path)
    index = _rows(index_path)
    signal = {row["recording_id"]: row for row in _rows(signal_path)}

    # Mandated row-key guard on the corrected table this round inherits.
    pta_guard = detect_sequential_key_misalignment(pta)
    if not pta_guard["aligned"]:
        raise ProvenanceError(f"CORRECTED_PTA_ROW_KEY_MISALIGNED:{pta_guard['offset_distribution']}")
    pta_by_key = {row["clinical_row_id"]: row for row in pta}
    clinical_by_row = {int(row["source_row"]): row for row in clinical}

    primary_column = require_config_value(config, "archive.primary_source_column")
    secondary_column = require_config_value(config, "archive.secondary_source_column")
    lo, hi = require_config_value(config, "archive.target_bounds_source_units")
    workbook_sha = digest(clinical_path)

    rows: list[dict] = []
    for entry in index:
        link_key = entry["clinical_row_id"]
        worksheet_row = int(entry["worksheet_source_row"])
        # The key must resolve to its own worksheet row; this is the corrected convention.
        if parse_clinical_row_id(link_key) != worksheet_row:
            raise ProvenanceError(f"INDEX_ROW_KEY_MISMATCH:{link_key}!={worksheet_row}")
        clinical_row = clinical_by_row.get(worksheet_row)
        pta_row = pta_by_key.get(link_key)
        signal_row = signal.get(entry["recording_id"])

        a_value = _number(clinical_row.get(primary_column)) if clinical_row else None
        v_value = _number(clinical_row.get(secondary_column)) if clinical_row else None
        reasons: list[str] = []
        if clinical_row is None:
            reasons.append("target_absent")
        else:
            if a_value is None:
                reasons.append("target_absent")
            elif not (lo <= a_value <= hi):
                reasons.append("target_out_of_source_range")
        identity_conflict = str(entry.get("identity_dob_conflict", "")).strip().lower() in ("true", "1", "yes")
        if identity_conflict:
            reasons.append("identity_conflict")
        if signal_row is None:
            reasons.append("no_signal_source")

        row = {
            "split_group_id": entry["participant_id"],
            "index_record_id": entry["recording_id"],
            "source_workbook_sha256": workbook_sha,
            "source_sheet": "Sheet1",
            "source_row_number": worksheet_row,
            "clinical_link_key": link_key,
            "link_evidence_level": entry.get("source_gate", "") or "unknown",
            "identity_conflict": identity_conflict,
            "A_literal_header": require_config_value(config, "archive.primary_source_header"),
            "A_raw_value": a_value,
            # The header merges two instruments and the per-row assignment is not
            # established by any supplied document. That is recorded, not resolved.
            "A_instrument_status": "UNKNOWN_MIXED_HEADER",
            "A_score_unit_status": "HA_SOURCE_COLUMN",
            "MUSS_raw_value": v_value,
            "MUSS_instrument_status": "DOCUMENTED",
            "assessment_date": "",
            "assessment_date_role": "UNKNOWN",
            "eeg_acquisition_time": entry.get("vendor_exam_time", ""),
            "eeg_questionnaire_relation": "UNKNOWN",
            "age_recorded_months": _number(clinical_row.get("age_months")) if clinical_row else None,
            "age_at_eeg_if_derivable": _number(pta_row.get("age_months_from_dob_at_vendor_start")) if pta_row else None,
            "HA_duration_months": _number(clinical_row.get("duration_months")) if clinical_row else None,
            "better_unaided_pta_corrected": _number(pta_row.get("better_unaided_pta")) if pta_row else None,
            "better_aided_pta_corrected": _number(pta_row.get("better_aided_pta")) if pta_row else None,
            "pta_unit_status": "UNKNOWN_ROW_LEVEL_DOCUMENTARY_DBHL_CONTEXT",
            "pta_date_relation": "UNKNOWN",
            "device_state_status": "UNKNOWN",
            "target_A_available": a_value is not None and not reasons,
            "target_V_given_A_available": (a_value is not None and v_value is not None and not reasons),
            "source_refs": json.dumps({
                "clinical_rows": str(clinical_path.relative_to(ROOT)),
                "corrected_pta": str(pta_path.relative_to(ROOT)),
                "frozen_index_cohort": str(index_path.relative_to(ROOT)),
                "signal_manifest": str(signal_path.relative_to(ROOT)),
            }, ensure_ascii=False),
            "exclusion_reason": ";".join(sorted(set(reasons))),
            "source_duration_s": _number(entry.get("source_duration_s")),
            "sfreq_hz": _number(signal_row.get("sfreq_hz")) if signal_row else None,
            "signal_file_id": (signal_row or {}).get("signal_file_id", ""),
        }
        rows.append(row)

    blocked = [r for r in rows if set(r["exclusion_reason"].split(";")) & BLOCKING_REASONS if r["exclusion_reason"]]
    eligible = [r for r in rows if not r["exclusion_reason"]]
    if len({r["split_group_id"] for r in eligible}) != len(eligible):
        raise ProvenanceError("DUPLICATE_IDENTITY_IN_ARCHIVE_COHORT")
    return {
        "rows": rows,
        "eligible": eligible,
        "blocked": blocked,
        "pta_row_key_guard": pta_guard,
        "flow": {
            "index_records_considered": len(index),
            "eligible_for_A": sum(1 for r in rows if r["target_A_available"]),
            "eligible_for_V_given_A": sum(1 for r in rows if r["target_V_given_A_available"]),
            "blocked_records": len(blocked),
            "identity_groups_eligible": len({r["split_group_id"] for r in eligible}),
        },
        "limitations": limitation_table(rows),
        "source_hashes": {
            "clinical_rows": digest(clinical_path),
            "corrected_pta": digest(pta_path),
            "frozen_index_cohort": digest(index_path),
            "signal_manifest": digest(signal_path),
        },
    }


def limitation_table(rows: list[dict]) -> list[dict]:
    """Counts of the metadata unknowns that are accepted rather than blocking."""
    def count(field: str, value: str) -> int:
        return sum(1 for r in rows if str(r.get(field)) == value)

    total = len(rows)
    return [
        {"limitation": "auditory instrument version per row", "status": "UNKNOWN_MIXED_HEADER",
         "records": count("A_instrument_status", "UNKNOWN_MIXED_HEADER"), "of": total,
         "blocking": False,
         "consequence": "the modelled quantity is the recorded value of one merged source column, not a confirmed IT-MAIS score"},
        {"limitation": "questionnaire assessment date", "status": "UNKNOWN",
         "records": count("assessment_date_role", "UNKNOWN"), "of": total, "blocking": False,
         "consequence": "no contemporaneous, follow-up or temporal-direction reading is permitted; no zero interval is assumed"},
        {"limitation": "EEG-questionnaire relation", "status": "UNKNOWN",
         "records": count("eeg_questionnaire_relation", "UNKNOWN"), "of": total, "blocking": False,
         "consequence": "association only; not same-visit and not prediction of a later assessment"},
        {"limitation": "PTA unit and test condition at row level", "status": "UNKNOWN",
         "records": count("pta_unit_status", "UNKNOWN_ROW_LEVEL_DOCUMENTARY_DBHL_CONTEXT"), "of": total,
         "blocking": False,
         "consequence": "results may say 'beyond the recorded hearing variables', never 'beyond a complete contemporaneous audibility assessment'"},
        {"limitation": "device worn/powered during acquisition", "status": "UNKNOWN",
         "records": count("device_state_status", "UNKNOWN"), "of": total, "blocking": False,
         "consequence": "no device-benefit or conditional-causal statement; unknown is not an exclusion"},
    ]


def analysis_lock(config: dict, cohort: dict, *, cohort_manifest: str, identity_registry: str) -> dict:
    """The FN1-A lock. It fixes THIS round's object and rules.

    It is explicitly not a claim that any clinical material was confirmed by a clinician,
    and it carries no field that waits on an external person.
    """
    pta_relative = require_config_value(config, "sources.corrected_pta")
    return {
        "analysis_lock": {
            "status": "LOCKED_FROM_EXISTING_ARCHIVE",
            "estimand": "HA_source_score_prediction_not_contemporaneous_clinical_validation",
            "external_confirmation_required": False,
            "primary_target": require_config_value(config, "archive.primary_target"),
            "secondary_target": require_config_value(config, "archive.secondary_target"),
            "target_source": "HA_registered_workbook_same_source_column",
            "unknown_instrument_version_allowed": True,
            "unknown_questionnaire_time_allowed": True,
            "unknown_device_state_allowed": True,
            "assumptions": [
                "predict_recorded_values_without_claiming_psychometric_equivalence",
                "no_imputed_questionnaire_dates_or_scale_versions",
                "association_not_temporal_or_causal_prediction",
            ],
            "cohort_manifest": cohort_manifest,
            "corrected_pta_source": {"path": pta_relative, "sha256": cohort["source_hashes"]["corrected_pta"]},
            "identity_registry": identity_registry,
            "locked_before_new_outcome_modeling": True,
            "row_key_rule": "actual_worksheet_row",
            "row_key_guard": cohort["pta_row_key_guard"]["status"],
        },
        "note": ("LOCKED_FROM_EXISTING_ARCHIVE means this round's object and rules are fixed. "
                 "It is not a statement that a clinician confirmed the clinical material."),
    }
