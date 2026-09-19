"""W0 `prepare_request`: assemble the one-off clinical check package.

Plan section 3. This command consumes ALREADY-EXISTING source material and support
receipts. It computes no new EEG-to-target association, opens no raw signal, fits
nothing, and contacts nobody.

Every count it publishes is read from a named artifact and carries that artifact's
path and sha256, so the resulting document states denominators without a reader having
to trust a literal typed into a report.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .clinical import RESOLUTION_COLUMNS, detect_sequential_key_misalignment, empty_lock, template_rows
from .runtime import ROOT, digest


def _read_json(relative: str) -> tuple[dict | None, dict]:
    path = ROOT / relative
    if not path.is_file():
        return None, {"path": relative, "present": False}
    return json.loads(path.read_text()), {"path": relative, "present": True, "sha256": digest(path)}


def _read_csv(relative: str) -> tuple[list[dict], dict]:
    path = ROOT / relative
    if not path.is_file():
        return [], {"path": relative, "present": False}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return rows, {"path": relative, "present": True, "sha256": digest(path), "n_rows": len(rows)}


def _pick(document: dict | None, *keys: str) -> Any:
    if not isinstance(document, dict):
        return None
    node: Any = document
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def collect_evidence() -> dict:
    """Read the receipts the plan's section 18 references, plus the corrected PTA table."""
    sources: list[dict] = []
    evidence: dict[str, Any] = {}

    corrected_rows, meta = _read_csv("private/auditory_repair/pta_007/candidate_covariates.csv")
    sources.append({"role": "corrected_pta", **meta})
    if corrected_rows:
        # The mandated row-key guard, run on the table W1 would actually inherit.
        alignment = detect_sequential_key_misalignment(corrected_rows)  # column auto-resolved, raises if absent
        evidence["corrected_pta_row_key"] = alignment
        evidence["corrected_pta_candidates"] = len(corrected_rows)
        evidence["corrected_pta_with_unaided"] = sum(
            1 for row in corrected_rows if str(row.get("better_unaided_pta", "")).strip() not in ("", "None"))
        evidence["corrected_pta_with_aided"] = sum(
            1 for row in corrected_rows if str(row.get("better_aided_pta", "")).strip() not in ("", "None"))
    else:
        evidence["corrected_pta_row_key"] = {"status": "CORRECTED_PTA_TABLE_ABSENT", "aligned": False}

    legacy_rows, meta = _read_csv("private/phase3_ha_covariates_004/candidate_covariates.csv")
    sources.append({"role": "legacy_pta_superseded", **meta})
    if legacy_rows:
        evidence["legacy_pta_row_key"] = detect_sequential_key_misalignment(legacy_rows)

    for role, relative, path_keys in (
        ("fseries_prepare", "results/auditory_fseries_archival/prepare_001/summary.json", ()),
        ("fseries_ci_qualification", "results/auditory_fseries/ci_qualification_001/summary.json", ()),
        ("fseries_ha_qualification", "results/auditory_fseries/ha_qualification_002/qualification_summary.json", ()),
        ("retrain_summary", "results/auditory_retrain_v1/verification_001/summary.json", ()),
        ("repair_summary", "results/auditory_repair/verification_001/summary.json", ()),
    ):
        document, meta = _read_json(relative)
        sources.append({"role": role, **meta})
        if document is not None:
            evidence[role] = {k: v for k, v in document.items() if isinstance(v, (int, float, str, bool))}

    return {"sources": sources, "evidence": evidence}


def question_register(evidence: dict) -> list[dict]:
    """The four question classes of plan section 3.2, with their machine-visible status.

    Only classes whose answer would change the study object appear. Each carries the
    reason it cannot be settled from the repository alone.
    """
    return [
        {
            "question_class": "target_identity",
            "question": "Which clinical rows use IT-MAIS and which use MAIS, under which version, and with what age applicability?",
            "already_established": "Scoring rules for IT-MAIS, CAP-II, MUSS and SIR are present in the source documentation; the numeric columns exist.",
            "still_required": "Per-row or per-batch instrument identity and version, from the clinical team or a traceable original.",
            "model_substitutable": False,
            "fallback_if_unanswered": "instrument_resolved=UNKNOWN; primary target cannot be a single confirmed instrument.",
            "blocks": ["W1_primary_target"],
        },
        {
            "question_class": "time_relation",
            "question": "Is the questionnaire the same clinical assessment as the EEG visit, and what does the table's date column denote?",
            "already_established": "EEG acquisition times exist; the clinical table carries a label date.",
            "still_required": "Same-visit confirmation, or a dated interval plus an explicit applicability rule confirmed before any new EEG outcome analysis.",
            "model_substitutable": False,
            "fallback_if_unanswered": "eeg_visit_relation=UNKNOWN; no time tolerance is invented and no zero interval is assumed.",
            "blocks": ["W1_primary_target", "W1_secondary_target"],
        },
        {
            "question_class": "identity_and_source",
            "question": "Are there known wrong-person, duplicate-export or visit-confusion cases among the currently unresolved records?",
            "already_established": "Candidate identity and worksheet-row linkage are audited; the corrected row key is in place.",
            "still_required": "Adjudication of the remaining conflicts only; resolved records are not re-asked.",
            "model_substitutable": False,
            "fallback_if_unanswered": "identity_status stays conflict or supported_candidate; such records stay out of the primary cohort.",
            "blocks": ["W1_cohort_membership"],
        },
        {
            "question_class": "threshold_and_device_context",
            "question": "What units and test conditions do the audiometric columns use, and was the device worn or powered during acquisition?",
            "already_established": "Unaided and aided four-frequency data exist; the PTA row key is corrected.",
            "still_required": "Unit and condition confirmation; any recorded mid-session device change.",
            "model_substitutable": False,
            "fallback_if_unanswered": ("device state stays UNKNOWN, which limits the wording of any conclusion but is NOT by "
                                       "itself a general exclusion; unknown PTA units restrict which clinical context a claim may cite."),
            "blocks": ["W1_conclusion_wording"],
        },
    ]


def write_package(public: Path, private: Path, evidence: dict, questions: list[dict],
                  lock_state: dict) -> dict:
    """Emit the machine-readable half of the W0 package."""
    from .runtime import write_json

    template_path = private / "PRIVATE_RESOLUTION_TEMPLATE.csv"
    with template_path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(RESOLUTION_COLUMNS))
        writer.writeheader()
        for row in template_rows():
            writer.writerow(row)
    template_path.chmod(0o600)

    public_template = public / "PRIVATE_RESOLUTION_TEMPLATE_columns.json"
    write_json(public_template, {
        "columns": list(RESOLUTION_COLUMNS),
        "note": ("Column list only. The filled table stays private: it carries candidate keys, "
                 "worksheet rows and assessment dates."),
    }, private=False)

    write_json(private / "clinical_lock_template.json", empty_lock(), private=True)
    write_json(public / "question_register.json", {"questions": questions}, private=False)
    write_json(public / "clinical_object_status.json", {
        "row_key_guard": evidence["evidence"].get("corrected_pta_row_key"),
        "legacy_row_key_guard": evidence["evidence"].get("legacy_pta_row_key"),
        "clinical_lock": lock_state,
        "counts_from_receipts": {k: v for k, v in evidence["evidence"].items()
                                 if k not in ("corrected_pta_row_key", "legacy_pta_row_key")},
    }, private=False)
    write_json(public / "source_inventory.json", {"sources": evidence["sources"]}, private=False)
    return {
        "template_columns": len(RESOLUTION_COLUMNS),
        "questions": len(questions),
        "sources_present": sum(1 for s in evidence["sources"] if s.get("present")),
        "sources_absent": sum(1 for s in evidence["sources"] if not s.get("present")),
    }
