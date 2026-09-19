"""Clinical object resolution: row keys, the confirmation template, and the W1 lock.

Plan sections 3.4, 5.1 and 13.

The row-key rule is the load-bearing part. A historical defect keyed the clinical
lookup by a SEQUENTIAL counter over non-empty worksheet rows while the rest of the
project keyed it by the ACTUAL worksheet row number. Because the sheet's data began at
worksheet row 4, `C{k}` resolved to worksheet row `k+3`, and every candidate received
another child's audiometry. Plan section 13 requires a dedicated test for exactly this
misalignment; `detect_sequential_key_misalignment` is that guard, and it is called on
every table this module reads.
"""
from __future__ import annotations

import re
from typing import Iterable, Sequence

CLINICAL_ROW_ID = re.compile(r"^C(\d{4})$")

# Plan section 3.4. Private confirmation table; unknown is a value, empty string is not.
RESOLUTION_COLUMNS: tuple[str, ...] = (
    "candidate_key",
    "source_workbook_sha256",
    "source_sheet",
    "source_row_number",
    "clinical_link_key",
    "visit_key",
    "identity_status",
    "outcome_role",
    "instrument_literal",
    "instrument_resolved",
    "score_unit_resolved",
    "version_evidence_ref",
    "age_applicability_note",
    "assessment_date_or_interval",
    "assessment_time_role",
    "eeg_visit_relation",
    "time_evidence_ref",
    "cohort_rule_id",
    "clinical_interval_event_flag",
    "pta_unit_and_condition_status",
    "recording_device_state",
    "resolver_role",
    "confirmation_evidence_ref",
    "resolution_status",
)

PRIVATE_ONLY_COLUMNS = frozenset({"candidate_key", "clinical_link_key", "visit_key",
                                  "assessment_date_or_interval", "source_row_number"})

ENUMERATED_VALUES = {
    "identity_status": ("confirmed", "supported_candidate", "conflict", "unknown"),
    "outcome_role": ("auditory", "speech", "unknown"),
    "instrument_resolved": ("IT_MAIS", "MAIS", "MUSS", "UNKNOWN"),
    "assessment_time_role": ("questionnaire", "EEG_only", "UNKNOWN"),
    "eeg_visit_relation": ("same_visit", "dated_interval", "UNKNOWN"),
    "recording_device_state": ("ON", "OFF", "WORN_POWER_UNKNOWN", "UNKNOWN"),
    "resolution_status": ("resolved", "unresolved", "conflict", "unknown"),
}

# Plan section 5.1. Every value is null until a real, traceable clinical confirmation
# supplies it. No code path in this package may set these from defaults.
CLINICAL_LOCK_FIELDS: tuple[str, ...] = (
    "status",
    "resolver_evidence_file",
    "target_id",
    "instrument",
    "unit",
    "applicable_age_scope",
    "time_relation_rule",
    "cohort_manifest",
    "corrected_pta_source",
    "identity_registry",
    "hypothesis_and_scope_approved",
    "locked_before_new_eeg_outcome_analysis",
)

REQUIRED_FOR_W1: tuple[str, ...] = (
    "resolver_evidence_file", "target_id", "instrument", "unit", "time_relation_rule",
    "cohort_manifest", "corrected_pta_source", "identity_registry",
)


class ClinicalLockError(RuntimeError):
    """Raised when W1 is requested without a real, complete clinical lock."""


def parse_clinical_row_id(clinical_row_id: str) -> int:
    match = CLINICAL_ROW_ID.match(str(clinical_row_id).strip())
    if not match:
        raise ValueError(f"CLINICAL_ROW_ID_MALFORMED:{clinical_row_id}")
    return int(match.group(1))


def worksheet_row_key(source_row_number: int) -> str:
    """The project-wide key: C + the ACTUAL worksheet row, zero padded to four digits."""
    row = int(source_row_number)
    if row < 1:
        raise ValueError("WORKSHEET_ROW_MUST_BE_POSITIVE")
    return f"C{row:04d}"


ROW_FIELD_ALIASES: tuple[str, ...] = ("source_row_number", "source_row", "worksheet_source_row", "rn")


def resolve_row_field(sample: dict, row_field: str | None = None) -> str:
    """Find the actual worksheet-row column, or raise naming what was available.

    A guard that cannot find its input must fail loudly. Returning "every key is
    unresolved" would turn a schema mismatch into a false misalignment alarm, which is
    precisely the failure mode this guard exists to catch.
    """
    if row_field is not None:
        if row_field not in sample:
            raise ValueError(f"ROW_FIELD_ABSENT:{row_field}:available={sorted(sample)}")
        return row_field
    for alias in ROW_FIELD_ALIASES:
        if alias in sample:
            return alias
    raise ValueError(f"ROW_FIELD_ABSENT:none_of={ROW_FIELD_ALIASES}:available={sorted(sample)}")


def detect_sequential_key_misalignment(records: Iterable[dict], *, id_field: str = "clinical_row_id",
                                       row_field: str | None = None) -> dict:
    """Guard for plan section 13's mandated check.

    Returns the offset distribution between the numeric part of the key and the actual
    worksheet row. A correct table has every offset equal to zero. A table built with a
    sequential counter over non-empty rows shows a constant non-zero offset equal to the
    number of blank rows above the first data row, and keys beyond the counter's range
    fail to resolve at all.
    """
    records = list(records)
    if not records:
        raise ValueError("ROW_KEY_GUARD_EMPTY_INPUT")
    resolved_row_field = resolve_row_field(records[0], row_field)
    if id_field not in records[0]:
        raise ValueError(f"ID_FIELD_ABSENT:{id_field}:available={sorted(records[0])}")
    offsets: dict[int, int] = {}
    unresolved: list[str] = []
    total = 0
    for record in records:
        total += 1
        identifier = str(record.get(id_field, "")).strip()
        raw_row = record.get(resolved_row_field, "")
        if not identifier:
            unresolved.append("<missing_id>")
            continue
        if raw_row in (None, ""):
            unresolved.append(identifier)
            continue
        offset = int(raw_row) - parse_clinical_row_id(identifier)
        offsets[offset] = offsets.get(offset, 0) + 1
    aligned = set(offsets) <= {0} and not unresolved
    return {
        "n_records": total,
        "offset_distribution": {str(k): v for k, v in sorted(offsets.items())},
        "n_unresolved_keys": len(unresolved),
        "aligned": bool(aligned),
        "status": "ROW_KEY_ALIGNED" if aligned else "SEQUENTIAL_ROW_KEY_MISALIGNMENT",
        "rule": "clinical_row_id numeric part must equal the actual worksheet row number",
        "row_field": resolved_row_field,
    }


def require_row_key_alignment(records: Sequence[dict]) -> dict:
    report = detect_sequential_key_misalignment(records)
    if not report["aligned"]:
        raise ValueError(f"SEQUENTIAL_ROW_KEY_MISALIGNMENT:{report['offset_distribution']}")
    return report


def empty_lock() -> dict:
    lock = {field: None for field in CLINICAL_LOCK_FIELDS}
    lock["status"] = "PENDING"
    lock["hypothesis_and_scope_approved"] = False
    lock["locked_before_new_eeg_outcome_analysis"] = False
    return {"clinical_lock": lock}


def validate_lock(document: dict | None) -> dict:
    """Decide whether W1 may start. Never mutates the lock; never supplies a default.

    A missing file, a PENDING status, an unapproved scope, or any null required field
    keeps W1 blocked. This function is the only authority the CLI consults.
    """
    if document is None:
        return {"w1_allowed": False, "status": "W1_BLOCKED_CLINICAL_LOCK",
                "reason": "no clinical lock file supplied", "missing_fields": list(REQUIRED_FOR_W1)}
    lock = document.get("clinical_lock")
    if not isinstance(lock, dict):
        return {"w1_allowed": False, "status": "W1_BLOCKED_CLINICAL_LOCK",
                "reason": "clinical_lock section absent or malformed", "missing_fields": list(REQUIRED_FOR_W1)}
    unknown = sorted(set(lock) - set(CLINICAL_LOCK_FIELDS))
    missing = [field for field in REQUIRED_FOR_W1 if lock.get(field) in (None, "", [])]
    reasons: list[str] = []
    if unknown:
        reasons.append(f"unexpected lock fields: {unknown}")
    if missing:
        reasons.append(f"null required fields: {missing}")
    if lock.get("status") != "LOCKED":
        reasons.append(f"status is {lock.get('status')!r}, not LOCKED")
    if lock.get("hypothesis_and_scope_approved") is not True:
        reasons.append("hypothesis_and_scope_approved is not true")
    if lock.get("locked_before_new_eeg_outcome_analysis") is not True:
        reasons.append("locked_before_new_eeg_outcome_analysis is not true")
    allowed = not reasons
    return {
        "w1_allowed": allowed,
        "status": "CLINICAL_LOCK_VALID" if allowed else "W1_BLOCKED_CLINICAL_LOCK",
        "reason": "; ".join(reasons) if reasons else "all required lock fields present and approved",
        "missing_fields": missing,
        "note": ("A lock is evidence of a real clinical confirmation. An execution agent may not "
                 "author or edit one to obtain permission to run."),
    }


def template_rows() -> list[dict]:
    """One all-unknown example row, so the template's value vocabulary is unambiguous."""
    row = {column: "" for column in RESOLUTION_COLUMNS}
    for column, values in ENUMERATED_VALUES.items():
        row[column] = values[-1] if values[-1].lower().startswith("unknown") else "unknown"
    row["source_row_number"] = "<actual worksheet row number, not a sequential index>"
    row["clinical_link_key"] = "<C + zero-padded actual worksheet row>"
    return [row]
