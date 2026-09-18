#!/usr/bin/env python3
"""Stage 1 HA/BDF clinical and visit qualification for the F-series plan.

This is a metadata-only qualification audit.  It intentionally does not read
EEG signal arrays, fit models, or inspect EEG--clinical associations.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import sys
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_NAME = "ha_qualification_002"
PUBLIC = ROOT / "results" / "auditory_fseries" / RUN_NAME
PRIVATE = ROOT / "private" / "auditory_fseries" / RUN_NAME
MAP = ROOT / "private" / "inventory_001" / "file_path_map.csv"
HA_FID = "file_e254c9a75c971ac7d4e76bf6df2b4030"
CONFIG = ROOT / "configs" / "auditory_fseries_qualification_v1.json"
PLAN = ROOT / "AUDITORY_FUNCTIONAL_DECODING_F1_F4_RESEARCH_PLAN_v1.md"
STAGE_PROTOCOL = ROOT / "docs" / "auditory_fseries" / "STAGE1_PROTOCOL.md"
DOCUMENT_EVIDENCE = ROOT / "private" / "auditory_fseries" / "document_evidence_002" / "document_evidence.json"
DOCUMENT_SUMMARY = ROOT / "results" / "auditory_fseries" / "document_evidence_002" / "summary.json"


def text(value):
    return "" if value is None else str(value).strip()


def norm(value):
    return re.sub(r"\s+", " ", text(value)).strip().lower()


def number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = norm(value).replace(",", "").replace("%", "")
    try:
        out = float(raw)
    except ValueError:
        return None
    return out if out == out and abs(out) != float("inf") else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows):
    rows = list(rows)
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def source_path(file_id: str) -> Path:
    with MAP.open(newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if row and row[0] == file_id:
                return Path(row[3])
    raise FileNotFoundError(file_id)


def iso(value):
    return value.isoformat(sep=" ") if isinstance(value, datetime) else value


def reset_dirs():
    if PUBLIC.exists() or PRIVATE.exists():
        raise FileExistsError(f"refusing to overwrite existing run: {PUBLIC} or {PRIVATE}")
    PUBLIC.mkdir(parents=True, exist_ok=False)
    PRIVATE.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.chmod(PRIVATE, 0o700)


def table_rows(path: Path):
    return read_csv(path)


def scale_profile(values, group_n):
    parsed = [number(v) for v in values]
    present = [v for v in parsed if v is not None]
    counts = Counter(str(v) for v in present)
    return {
        "rows": group_n,
        "nonmissing": len(present),
        "missing": group_n - len(present),
        "observed_min": min(present) if present else None,
        "observed_max": max(present) if present else None,
        "unique_values": len(counts),
        "value_frequency": dict(sorted(counts.items(), key=lambda x: float(x[0]))),
        "ceiling_100_n": sum(v == 100 for v in present),
        "ceiling_9_n": sum(v == 9 for v in present),
        "ceiling_5_n": sum(v == 5 for v in present),
        "literal_87_n": sum(v == 87 for v in present),
    }


def threshold_profile(rows, columns, group_key):
    out = {}
    for panel, colspec in columns.items():
        group_rows = [r for r in rows if r["group"] == group_key]
        panel_out = {}
        for side, freq_cols in colspec.items():
            vals = []
            for row in group_rows:
                for freq, col in freq_cols.items():
                    vals.append(number(row["raw"][col]))
            present = [v for v in vals if v is not None]
            panel_out[side] = {
                "cells": len(vals),
                "numeric_cells": len(present),
                "missing_or_non_numeric_cells": len(vals) - len(present),
                "observed_min": min(present) if present else None,
                "observed_max": max(present) if present else None,
            }
        out[panel] = panel_out
    return out


def threshold_profile_rows(group_rows, colspec):
    out = {}
    for side, freq_cols in colspec.items():
        vals = [number(row["raw"][col]) for row in group_rows for col in freq_cols.values()]
        present = [v for v in vals if v is not None]
        out[side] = {
            "cells": len(vals),
            "numeric_cells": len(present),
            "missing_or_non_numeric_cells": len(vals) - len(present),
            "observed_min": min(present) if present else None,
            "observed_max": max(present) if present else None,
        }
    return out


def header_info(workbook_path: Path):
    import openpyxl

    workbook = openpyxl.load_workbook(workbook_path, read_only=False, data_only=False)
    result = []
    note_hits = []
    token_re = re.compile(r"(?i)(IT[- ]?MAIS|MAIS|MUSS|CAP|SIR|裸耳|助听|dB|Hz|频率|评估|测试|量表|佩戴|耳蜗)")
    for sheet_idx, ws in enumerate(workbook.worksheets, 1):
        cells = []
        comments = []
        for row in ws.iter_rows():
            for cell in row:
                val = cell.value
                if val is None:
                    continue
                if cell.comment is not None:
                    comments.append({"cell": cell.coordinate, "text": text(cell.comment.text), "author": text(cell.comment.author)})
                if cell.row <= min(ws.max_row, 12) or (isinstance(val, str) and token_re.search(val)):
                    cells.append({"cell": cell.coordinate, "row": cell.row, "column": cell.column, "value": iso(val)})
                if isinstance(val, str) and token_re.search(val):
                    note_hits.append({"sheet": sheet_idx, "cell": cell.coordinate, "value": val})
        result.append({
            "sheet_index": sheet_idx,
            "sheet_title": ws.title,
            "rows": ws.max_row,
            "columns": ws.max_column,
            "merged_ranges": [str(x) for x in ws.merged_cells.ranges],
            "cells_for_review": cells,
            "comments": comments,
        })
    return result, note_hits


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("all computation must run under Slurm")
    os.umask(0o077)
    reset_dirs()

    # Source/config receipt is written before opening any clinical source.
    source_files = {
        "registered_ha_workbook": source_path(HA_FID),
        "clinical_003_rows": ROOT / "private/clinical_003/clinical_rows_clean.csv",
        "ha_covariates_004": ROOT / "private/phase3_ha_covariates_004/candidate_covariates.csv",
        "ha_repeat_audit_004": ROOT / "private/phase3_ha_covariates_004/repeat_audit.csv",
        "ha_schema_evidence_004": ROOT / "private/phase3_ha_covariates_004/schema_evidence.json",
        "bdf_recording_index_001": ROOT / "results/linkage_001/recording_index.csv",
        "bdf_vendor_metadata_001": ROOT / "results/linkage_001/vendor_acquisition_metadata.csv",
        "bdf_clinical_link_001": ROOT / "results/linkage_001/clinical_link.csv",
        "bdf_files_to_recordings_001": ROOT / "results/linkage_001/files_to_recordings.csv",
        "bdf_participant_index_001": ROOT / "results/linkage_001/participant_index.csv",
        "bdf_visit_index_001": ROOT / "manifests/visit_index.csv",
        "registered_HA_document_evidence": DOCUMENT_EVIDENCE,
        "reviewed_HA_document_summary": DOCUMENT_SUMMARY,
        "config": CONFIG,
        "plan": PLAN,
        "stage_protocol": STAGE_PROTOCOL,
    }
    source_receipt = {
        "job_id": os.environ["SLURM_JOB_ID"],
        "run": RUN_NAME,
        "phase": "sources_hashed_before_analysis",
        "script_sha256": sha256(Path(__file__)),
        "sources": {key: {"sha256": sha256(path), "size_bytes": path.stat().st_size} for key, path in source_files.items()},
        "source_paths_private_only": True,
    }
    (PRIVATE / "source_manifest.json").write_text(json.dumps({key: {**value, "path": str(source_files[key])} for key, value in source_receipt["sources"].items()}, ensure_ascii=False, indent=2), encoding="utf-8")
    (PRIVATE / "config_snapshot.json").write_bytes(CONFIG.read_bytes())
    (PRIVATE / "plan_snapshot.md").write_bytes(PLAN.read_bytes())
    (PRIVATE / "stage_protocol_snapshot.md").write_bytes(STAGE_PROTOCOL.read_bytes())
    (PUBLIC / "start_receipt.json").write_text(json.dumps(source_receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    documentary_receipt = json.loads(DOCUMENT_EVIDENCE.read_text(encoding="utf-8"))
    documentary_summary = json.loads(DOCUMENT_SUMMARY.read_text(encoding="utf-8"))
    documentary_roles = [row.get("document_role") for row in documentary_summary.get("documents", [])]

    # Private workbook schema/notes review across all registered workbooks.
    all_workbooks = {}
    for fid, label in [("file_8a9c2767bddf88cb1bc2531e0dd4ea00", "caep_archive"), (HA_FID, "ha_group_workbook"), ("file_d4bd0c2924e725928f61c2756853cb38", "caep_full"), ("file_225d0f1d5180f1dc47fb96cedbde60d7", "caep_128")]:
        path = source_path(fid)
        schema, notes = header_info(path)
        all_workbooks[label] = {"file_id": fid, "sha256": sha256(path), "path": str(path), "sheets": schema, "note_hits": notes}
    (PRIVATE / "registered_workbook_schema_and_notes.json").write_text(json.dumps(all_workbooks, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    import openpyxl
    workbook_path = source_files["registered_ha_workbook"]
    workbook = openpyxl.load_workbook(workbook_path, read_only=False, data_only=True)
    ws = workbook["Sheet1"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    header = [text(v) for v in rows[0]]
    header_norm = [norm(v) for v in header]
    def col(label):
        target = norm(label)
        if target not in header_norm:
            raise KeyError(label)
        return header_norm.index(target)
    group_col = 0
    merged_group_values = {}
    for merged in ws.merged_cells.ranges:
        if merged.min_col <= group_col + 1 <= merged.max_col:
            value = ws.cell(merged.min_row, merged.min_col).value
            for rr in range(merged.min_row, merged.max_row + 1):
                merged_group_values[rr] = value
    name_col = col("姓名")
    age_col = col("实际月龄")
    duration_col = col("HA使用时长（月）")
    muss_col = col("MUSS得分（%）")
    itmais_col = col("IT-MAIS/MAIS得分（%）")
    sir_col = col("SIR得分")
    cap_col = col("CAP得分")
    wear_col = col("每日佩戴时长")

    scale_cols = {"MUSS": muss_col, "IT-MAIS/MAIS": itmais_col, "SIR": sir_col, "CAP": cap_col}
    threshold_cols = {"unaided": {"right": {}, "left": {}}, "aided": {"right": {}, "left": {}}}
    for i, h in enumerate(header):
        m = re.search(r"(右|左)耳\s*(500|1000|2000|4000)Hz\s*\((裸耳|助听)\)", h)
        if m:
            side = "right" if m.group(1) == "右" else "left"
            panel = "unaided" if m.group(3) == "裸耳" else "aided"
            threshold_cols[panel][side][m.group(2)] = i
    clinical_rows = []
    private_rows = []
    for source_row, values in enumerate(rows[1:], 2):
        if not any(text(v) for v in values):
            continue
        group = text(merged_group_values.get(source_row, values[group_col]))
        raw_name = text(values[name_col])
        parsed = {"source_row": source_row, "raw_name": raw_name, "group": group, "raw": [iso(v) for v in values]}
        clinical_rows.append(parsed)
        private_rows.append({"source_row": source_row, "raw_name": raw_name, "group": group, "age_months": iso(values[age_col]), "duration_months": iso(values[duration_col]), "daily_wear_raw": iso(values[wear_col]), **{name: iso(values[idx]) for name, idx in scale_cols.items()}})
    write_csv(PRIVATE / "ha_clinical_rows_evidence.csv", private_rows)
    ha_rows = [r for r in clinical_rows if norm(r["group"]) != "nh"]
    registered_identity_rows = {int(r["source_row"]): r.get("candidate_key", "") for r in read_csv(source_files["clinical_003_rows"]) if r.get("source_row", "").isdigit()}
    ha_candidate_keys = {registered_identity_rows.get(r["source_row"], "") for r in ha_rows} - {""}
    group_counts = Counter("NH" if norm(r["group"]) == "nh" else "HA" for r in clinical_rows)
    scale_public = {}
    literal_headers = {name: header[idx] for name, idx in scale_cols.items()}
    for name, idx in scale_cols.items():
        scale_public[name] = {"literal_header": header[idx], "version_status": "unresolved_from_registered_header", "scoring_unit_status": "literal_header_only", "HA": scale_profile([r["raw"][idx] for r in ha_rows], len(ha_rows)), "NH": scale_profile([r["raw"][idx] for r in clinical_rows if norm(r["group"]) == "nh"], group_counts["NH"])}

    age_vals = [number(r["raw"][age_col]) for r in ha_rows]
    duration_vals = [number(r["raw"][duration_col]) for r in ha_rows]
    wear_vals = [number(r["raw"][wear_col]) for r in ha_rows]
    age_device = {
        "age_months": {"rows": len(ha_rows), "numeric": sum(v is not None for v in age_vals), "min": min(v for v in age_vals if v is not None), "max": max(v for v in age_vals if v is not None)},
        "ha_duration_months": {"rows": len(ha_rows), "numeric": sum(v is not None for v in duration_vals), "min": min(v for v in duration_vals if v is not None), "max": max(v for v in duration_vals if v is not None)},
        "daily_wear": {"rows": len(ha_rows), "numeric": sum(v is not None for v in wear_vals), "missing_or_non_numeric": sum(v is None for v in wear_vals), "unit_status": "unresolved_from_registered_header"},
        "interpretation": "Use duration as archive field evidence, not actual daily exposure; device power/state and wear units are not established.",
    }
    threshold_public = {}
    for panel, sides in threshold_cols.items():
        threshold_public[panel] = {"header_columns": {side: {freq: header[idx] for freq, idx in freq_cols.items()} for side, freq_cols in sides.items()}, "unit_status": "not_explicit_in_Sheet1_headers; documentary dBHL context retained separately", "date_status": "no_threshold_date_column_in_registered_Sheet1", "profiles_HA": threshold_profile_rows(ha_rows, sides)}

    # Existing registered audit tables provide BDF/clinical linkage without a
    # full EEG directory scan.  Candidate IDs and exact dates stay private.
    cov = table_rows(source_files["ha_covariates_004"])
    repeats = table_rows(source_files["ha_repeat_audit_004"])
    recs = table_rows(source_files["bdf_recording_index_001"])
    vendor = table_rows(source_files["bdf_vendor_metadata_001"])
    links = table_rows(source_files["bdf_clinical_link_001"])
    files_to_rec = table_rows(source_files["bdf_files_to_recordings_001"])
    write_csv(PRIVATE / "bdf_clinical_temporal_linkage_evidence.csv", links)
    write_csv(PRIVATE / "ha_repeat_evidence.csv", repeats)
    write_csv(PRIVATE / "ha_covariates_evidence.csv", cov)
    vendor_by_id = {r.get("candidate_acquisition_id"): r for r in vendor}
    rec_by_id = {r.get("recording_id"): r for r in recs}
    map_rows = {r.get("recording_id"): r for r in cov}
    private_bdf = []
    for row in cov:
        rid = row.get("recording_id")
        b = rec_by_id.get(rid, {})
        v = vendor_by_id.get(rid, {})
        private_bdf.append({"recording_id": rid, "participant_id": row.get("participant_id"), "clinical_row_id": row.get("clinical_row_id"), "vendor_exam_time": row.get("vendor_exam_time"), "vendor_start_record_time": row.get("vendor_start_record_time"), "recording_status": b.get("recording_status"), "device_state": b.get("device_state"), "vendor_metadata_file_id": v.get("file_id")})
    write_csv(PRIVATE / "ha_bdf_recording_evidence.csv", private_bdf)
    file_map = {row[0]: row[3] for row in csv.reader(MAP.open(newline="", encoding="utf-8")) if row and len(row) >= 4}
    path_rows = []
    for row in files_to_rec:
        fid = row.get("file_id")
        if fid in file_map:
            path_rows.append({"recording_id": row.get("recording_id"), "file_role": row.get("file_role"), "file_id": fid, "original_path": file_map[fid], "sha256": "not_rehashed_stage1_existing_registered_file_id_only"})
    write_csv(PRIVATE / "ha_bdf_source_paths_and_hashes.csv", path_rows)

    link_status = Counter(r.get("concurrent_scale_date_status", "") or "missing" for r in links)
    link_evidence = Counter(r.get("evidence", "") for r in links)
    vendor_exam_present = sum(bool(r.get("exam_time_present", "").lower() == "true") for r in vendor)
    vendor_start_present = sum(bool(r.get("start_record_time_present", "").lower() == "true") for r in vendor)
    temporal = {
        "BDF_recordings_registered": len(recs),
        "BDF_vendor_metadata_rows": len(vendor),
        "BDF_vendor_exam_time_present": vendor_exam_present,
        "BDF_vendor_start_record_time_present": vendor_start_present,
        "clinical_link_rows": len(links),
        "clinical_link_date_status_counts": dict(link_status),
        "clinical_link_evidence_counts": dict(link_evidence),
        "nonmissing_EEG_clinical_gap_days": sum(bool(text(r.get("eeg_clinical_gap_days"))) for r in links),
        "interpretation": "EEG acquisition times are present in registered vendor metadata; assessment dates and an explicit same-visit relation are unavailable in this HA source table, so same-time functional endpoints are not established.",
    }
    repeats_public = {
        "candidate_repeat_pairs": len(repeats),
        "candidate_repeat_participants": len({r.get("participant_id") for r in repeats if r.get("participant_id")}),
        "pairs_with_both_vendor_exam_times": sum(bool(r.get("exam_time_a")) and bool(r.get("exam_time_b")) for r in repeats),
        "pairs_with_explicit_clinical_assessment_dates": 0,
        "ordered_clinical_followup_status": "unsupported_assessment_dates_missing",
        "interpretation": "Repeated vendor EEG acquisition times support candidate acquisition order only; they do not establish ordered repeated functional assessments.",
    }

    # Qualification flow keeps raw availability and strict interpretability
    # separate, and never uses EEG outcomes to choose an endpoint.
    score_complete = {name: scale_public[name]["HA"]["nonmissing"] for name in scale_public}
    joint_f2 = sum(number(r["raw"][muss_col]) is not None and number(r["raw"][sir_col]) is not None for r in ha_rows)
    raw_index = {
        "archival_HA_candidate_rows": len(cov),
        "archival_HA_candidate_identity_index_rows": sum(str(r.get("eligible_measurement_identity_index", "")).lower() == "true" for r in cov),
        "archival_HA_index_recording_rows": sum(str(r.get("index_recording_flag", "")).lower() == "true" for r in cov),
        "source_gate_counts": dict(Counter(r.get("source_gate", "") for r in cov)),
        "registered_recording_status_counts": dict(Counter(r.get("recording_status", "") for r in recs)),
        "registered_qc_status_counts": dict(Counter(r.get("qc_status", "") for r in recs)),
        "interpretation": "Historical index/technical availability is reported as provenance support; no new amplitude or signal-derived clinical gate was applied.",
    }
    documentary_definitions = {"declared_scales": documentary_summary.get("declared_scale_definitions", []), "hearing_units_evidence": documentary_summary.get("hearing_units_evidence"), "assessment_time_evidence": documentary_summary.get("assessment_time_evidence"), "source_review": "document_evidence_002 supersedes document_evidence_001 interpretation"}
    flow = [
        {"route": "F1", "stage": "HA clinical rows", "denominator": len(ha_rows), "count": len(ha_rows), "status": "candidate_raw_archive_values"},
        {"route": "F1", "stage": "HA candidate identity groups", "denominator": len(ha_rows), "count": len(ha_candidate_keys), "status": "candidate_groups_not_confirmed_children"},
        {"route": "F1", "stage": "auditory endpoint version and timing interpretable", "denominator": len(ha_rows), "count": 0, "status": "SUPPORT_INSUFFICIENT"},
        {"route": "F2", "stage": "MUSS/SIR raw numeric HA rows", "denominator": len(ha_rows), "count": joint_f2, "status": "candidate_raw_archive_values"},
        {"route": "F2", "stage": "speech endpoint version and timing interpretable", "denominator": len(ha_rows), "count": 0, "status": "SUPPORT_INSUFFICIENT"},
        {"route": "F3", "stage": "confirmed same-candidate two-task clinical pairs", "denominator": len(recs), "count": 0, "status": "SUPPORT_INSUFFICIENT"},
        {"route": "F4", "stage": "candidate repeated vendor acquisition pairs", "denominator": len(repeats), "count": len(repeats), "status": "candidate_order_only"},
        {"route": "F4", "stage": "ordered baseline/followup clinical assessments", "denominator": len(repeats), "count": 0, "status": "SUPPORT_INSUFFICIENT"},
    ]
    public = {
        "job_id": os.environ["SLURM_JOB_ID"],
        "run": RUN_NAME,
        "stage": "stage1_targeted_clinical_visit_qualification",
        "source_config": "auditory_fseries_qualification_v1",
        "scope": "HA/BDF clinical and visit qualification only; no EEG signal arrays, EEG--clinical associations, or models",
        "clinical_group_counts": dict(group_counts),
        "scale_definitions": scale_public,
        "documentary_scale_definitions": documentary_definitions,
        "documentary_evidence_receipt": {"roles_checked": documentary_roles, "source_text_kept_private": True, "assessment_timing_clause_status": "not established", "reviewed_version": "document_evidence_002"},
        "historical_index_and_EEG_availability": raw_index,
        "threshold_evidence": threshold_public,
        "age_and_device_month_evidence": age_device,
        "EEG_clinical_temporal_linkage": temporal,
        "F4_repeat_visit_evidence": repeats_public,
        "qualification_flow": flow,
        "primary_endpoint": {"status": "not_frozen", "reason": "IT-MAIS/MAIS combined literal header has unresolved version; clinical assessment timing unavailable"},
        "decision": {"F1": "SUPPORT_INSUFFICIENT", "F2": "SUPPORT_INSUFFICIENT", "F3": "SUPPORT_INSUFFICIENT", "F4": "SUPPORT_INSUFFICIENT"},
        "limitations": [
            "IT-MAIS and MAIS are not split by the registered header; values are retained as raw archive values.",
            "Literal percent headers do not establish validated scoring comparability; no conversion was applied.",
            "MUSS/IT-MAIS/CAP/SIR assessment dates and an explicit same-visit relation are not present in the HA Sheet1 source.",
            "Threshold units, threshold dates, device power and actual wearing exposure remain unresolved.",
            "Candidate identity groups and repeated vendor acquisitions are not counted as confirmed independent children or longitudinal assessments.",
        ],
    }
    (PUBLIC / "qualification_summary.json").write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8")
    (PUBLIC / "qualification_flow.csv").write_text("route,stage,denominator,count,status\n" + "\n".join(",".join(str(row[k]) for k in ("route", "stage", "denominator", "count", "status")) for row in flow) + "\n", encoding="utf-8")
    (PUBLIC / "source_hashes.json").write_text(json.dumps({"sources": {key: value["sha256"] for key, value in source_receipt["sources"].items()}, "private_paths": True}, indent=2), encoding="utf-8")
    done = dict(source_receipt, phase="complete", public_outputs=["qualification_summary.json", "qualification_flow.csv", "source_hashes.json"], private_evidence="private/auditory_fseries/ha_qualification_001")
    (PUBLIC / "run_receipt.json").write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(Path(__file__), PRIVATE / "fseries_ha_qualification.py")
    print(json.dumps({"job_id": os.environ["SLURM_JOB_ID"], "run": RUN_NAME, "status": "complete", "decision": public["decision"]}, ensure_ascii=False))


def run_with_failure_receipt():
    try:
        main()
    except Exception as exc:
        # Keep diagnostics private and expose only a generic failed run marker.
        if PRIVATE.exists():
            (PRIVATE / "failure_receipt.json").write_text(json.dumps({"job_id": os.environ.get("SLURM_JOB_ID", "unknown"), "status": "failed", "error_type": type(exc).__name__, "error": repr(exc), "traceback": traceback.format_exc()}, ensure_ascii=False, indent=2), encoding="utf-8")
        if PUBLIC.exists():
            (PUBLIC / "run_receipt.json").write_text(json.dumps({"job_id": os.environ.get("SLURM_JOB_ID", "unknown"), "run": RUN_NAME, "status": "failed", "details_private": True}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise


if __name__ == "__main__":
    run_with_failure_receipt()
