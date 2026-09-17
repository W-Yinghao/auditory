#!/usr/bin/env python3
"""Schema-first, metadata-only audit of the CI clinical workbook.

The workbook is read only from a Slurm job.  Raw names, dates and cell values
are kept under private/; public outputs contain opaque IDs, schema and counts.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median

import openpyxl


BASE = Path(__file__).resolve().parents[1]
WORKBOOK_ID = "file_225d0f1d5180f1dc47fb96cedbde60d7"
RUN = "phase3_ci_clinical_001"
WORKBOOK_MAP = BASE / "private/inventory_001/file_path_map.csv"


def text(value):
    return "" if value is None else str(value).strip()


def norm(value):
    return re.sub(r"\s+", " ", text(value)).strip().lower()


def name_key(value):
    raw = re.sub(r"\s+", "", text(value))
    leading = re.match(r"^[\u4e00-\u9fff]+", raw)
    return leading.group(0) if leading else norm(value)


def pid_for(value):
    key = name_key(value)
    return "P" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12] if key else ""


def parse_number(value):
    raw = norm(value).replace(",", "").replace("%", "")
    if not raw:
        return None
    try:
        number = float(raw)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    raw = text(value).replace("Z", "+00:00")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def table(path, rows):
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


ALIASES = {
    "name": ("姓名", "患者姓名", "受试者姓名", "name", "patient name", "subject"),
    "dob": ("出生日期", "出生年月", "dob", "birth date", "birthdate"),
    "gender": ("性别", "gender", "sex"),
    "clinical_date": ("量表日期", "评估日期", "评估时间", "测试日期", "临床日期", "检查日期", "assessment date", "date of assessment"),
    "eeg_date": ("脑电日期", "eeg日期", "采集日期", "采集时间", "acquisition date", "recording date"),
    "implant_date": ("植入日期", "植入时间", "ci植入", "implant date"),
    "activation_date": ("开机日期", "开机时间", "ci开机", "activation date"),
    "device_state": ("设备状态", "装置状态", "device state", "ci state"),
    "cooperation_status": ("配合状态", "cooperation status"),
    "patient_no": ("patient no", "patient number", "病历号", "患者编号"),
    "cap": ("cap得分", "cap", "categories of auditory performance"),
    "sir": ("sir得分", "sir", "speech intelligibility rating"),
    "itmais": ("it-mais", "itmais", "mais得分", "it-mais/mais", "it mais"),
    "muss": ("muss", "muss得分"),
    "pta": ("pta", "纯音听阈", "hearing threshold"),
    "pure_tone": ("pure tone", "audiology", "听力", "听力学", "audiometric"),
    "age_months": ("实际月龄", "月龄", "年龄（月）", "age months", "age (months)"),
}


def find_workbook():
    with WORKBOOK_MAP.open(newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if row and row[0] == WORKBOOK_ID:
                if len(row) < 4:
                    raise ValueError("malformed workbook map row")
                return Path(row[3])
    raise FileNotFoundError(WORKBOOK_ID)


def merged_lookup(ws):
    values = {}
    for merged in ws.merged_cells.ranges:
        value = ws.cell(merged.min_row, merged.min_col).value
        for row in range(merged.min_row, merged.max_row + 1):
            for col in range(merged.min_col, merged.max_col + 1):
                values[(row, col)] = value
    return values


def cell_value(ws, merged, row, col):
    return merged.get((row, col), ws.cell(row, col).value)


def alias_hit(header, aliases):
    value = norm(header)
    return any(norm(alias) in value for alias in aliases)


def sheet_schema(ws):
    merged = merged_lookup(ws)
    header_candidates = []
    for row_number in range(1, min(ws.max_row, 30) + 1):
        values = [cell_value(ws, merged, row_number, col) for col in range(1, ws.max_column + 1)]
        hits = sum(any(alias_hit(value, aliases) for aliases in ALIASES.values()) for value in values)
        if hits:
            # Header text is safe to expose in the Slurm probe; data values are
            # never printed or written to the public schema summary.
            fields = [text(value) for value in values if any(alias_hit(value, aliases) for aliases in ALIASES.values())]
            all_fields = [text(value) for value in values if text(value)]
            header_candidates.append({"row": row_number, "alias_hits": hits,
                                      "field_names": fields, "all_nonempty_fields": all_fields})
    return {
        "sheet_index": ws._parent.worksheets.index(ws) + 1,
        "sheet_title_sha256": hashlib.sha256(text(ws.title).encode()).hexdigest()[:16],
        "rows": ws.max_row,
        "columns": ws.max_column,
        "merged_range_count": len(ws.merged_cells.ranges),
        "header_candidates": header_candidates,
    }


def schema_probe(path, destination):
    wb = openpyxl.load_workbook(path, read_only=False, data_only=True)
    schemas = [sheet_schema(ws) for ws in wb.worksheets]
    result = {"workbook_file_id": WORKBOOK_ID, "sha256": sha256(path), "sheets": schemas}
    destination.parent.mkdir(mode=0o700, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    # Emit only sheet dimensions and header labels, never cell data or titles.
    print(json.dumps({"workbook_file_id": WORKBOOK_ID, "sheets": schemas}, ensure_ascii=False), flush=True)


def header_map(ws, header_row, merged):
    columns = {}
    for col in range(1, ws.max_column + 1):
        pieces = []
        for row in range(max(1, header_row - 3), header_row + 1):
            value = text(cell_value(ws, merged, row, col))
            if value and value not in pieces:
                pieces.append(value)
        columns[col] = " / ".join(pieces)
    candidates = {}
    mapping = {}
    for field, aliases in ALIASES.items():
        matches = [col for col, header in columns.items() if alias_hit(header, aliases)]
        if matches:
            candidates[field] = matches
        if len(matches) == 1:
            mapping[field] = matches[0]
    return columns, mapping, candidates


def choose_header(ws, merged):
    best = None
    for row in range(1, min(ws.max_row, 30) + 1):
        values = [cell_value(ws, merged, row, col) for col in range(1, ws.max_column + 1)]
        hits = sum(any(alias_hit(value, aliases) for aliases in ALIASES.values()) for value in values)
        if best is None or hits > best[0]:
            best = (hits, row)
    if best is None or best[0] == 0:
        return None, {}, {}
    columns, mapping, candidates = header_map(ws, best[1], merged)
    return best[1], columns, mapping, candidates


def serial(value):
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    return value


def extracted_value(values, mapping, candidates, field):
    """Return a scalar only for a unique column; retain all ambiguous columns."""
    if field in mapping:
        return serial(values[mapping[field] - 1])
    if field in candidates:
        return json.dumps([serial(values[col - 1]) for col in candidates[field]],
                          ensure_ascii=False, default=str)
    return ""


def clean_workbook(path, private_dir):
    wb = openpyxl.load_workbook(path, read_only=False, data_only=True)
    rows = []
    schema = []
    for sheet_index, ws in enumerate(wb.worksheets, 1):
        merged = merged_lookup(ws)
        header_row, columns, mapping, candidates = choose_header(ws, merged)
        schema.append({
            "sheet_index": sheet_index,
            "sheet_title_sha256": hashlib.sha256(text(ws.title).encode()).hexdigest()[:16],
            "rows": ws.max_row,
            "columns": ws.max_column,
            "merged_range_count": len(ws.merged_cells.ranges),
            "header_row": header_row,
            "recognized_fields": sorted(mapping),
            "ambiguous_fields": sorted(field for field, cols in candidates.items() if len(cols) > 1),
            "field_column_candidates": {field: cols for field, cols in candidates.items()},
            "field_column_mapping": mapping,
            "recognized_column_headers": {str(col): columns[col] for col in mapping.values()},
        })
        if header_row is None or "name" not in mapping:
            continue
        for row_number in range(header_row + 1, ws.max_row + 1):
            values = [serial(cell_value(ws, merged, row_number, col)) for col in range(1, ws.max_column + 1)]
            if not any(text(value) for value in values):
                continue
            raw_name = values[mapping["name"] - 1] if mapping["name"] <= len(values) else ""
            # Repeated header rows and group labels are retained privately but
            # do not become candidate identities.
            parsed_name = text(raw_name)
            key = name_key(parsed_name)
            if not parsed_name:
                row_status = "missing_name_non_identity_row"
            elif norm(parsed_name) in {"name", "姓名", "patient name", "受试者姓名"}:
                row_status = "repeated_header"
            elif any(token in norm(parsed_name) for token in ("合计", "总计", "统计", "平均", "均值", "组别", "group")):
                row_status = "summary_or_group_row"
            else:
                row_status = "candidate_row"
            row = {
                "source_workbook_file_id": WORKBOOK_ID,
                "source_sheet_index": sheet_index,
                "source_sheet_title": ws.title,
                "source_worksheet_row": row_number,
                "participant_id": pid_for(parsed_name),
                "row_status": row_status,
                "name_parse_status": "parsed_han_leading" if re.match(r"^[\u4e00-\u9fff]+", re.sub(r"\s+", "", parsed_name)) else ("parsed_non_han" if key else "missing_name"),
                "raw_name": parsed_name,
                "raw_dob": extracted_value(values, mapping, candidates, "dob"),
                "raw_gender": extracted_value(values, mapping, candidates, "gender"),
                "raw_clinical_date": extracted_value(values, mapping, candidates, "clinical_date"),
                "raw_eeg_date": extracted_value(values, mapping, candidates, "eeg_date"),
                "raw_implant_date": extracted_value(values, mapping, candidates, "implant_date"),
                "raw_activation_date": extracted_value(values, mapping, candidates, "activation_date"),
                "raw_device_state": extracted_value(values, mapping, candidates, "device_state"),
                "raw_cooperation_status": extracted_value(values, mapping, candidates, "cooperation_status"),
                "raw_patient_no": extracted_value(values, mapping, candidates, "patient_no"),
                "raw_cap": extracted_value(values, mapping, candidates, "cap"),
                "raw_sir": extracted_value(values, mapping, candidates, "sir"),
                "raw_itmais": extracted_value(values, mapping, candidates, "itmais"),
                "raw_muss": extracted_value(values, mapping, candidates, "muss"),
                "raw_pta": extracted_value(values, mapping, candidates, "pta"),
                "raw_pure_tone": extracted_value(values, mapping, candidates, "pure_tone"),
                "raw_age_months": extracted_value(values, mapping, candidates, "age_months"),
                "raw_cells_json": json.dumps(values, ensure_ascii=False, default=str),
                "recognized_fields_json": json.dumps(sorted(mapping), ensure_ascii=False),
            }
            rows.append(row)
    table(private_dir / "clinical_rows_clean.csv", rows)
    (private_dir / "schema_private.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    return rows, schema


def vendor_overlap(rows):
    vendor_path = BASE / "private/linkage_001/vendor_identity_records.json"
    vendors = json.loads(vendor_path.read_text(encoding="utf-8"))
    by_key = defaultdict(list)
    for vendor in vendors:
        by_key[name_key(vendor.get("namekey") or vendor.get("PatientName", ""))].append(vendor)
    for row in rows:
        matches = by_key.get(name_key(row["raw_name"]), []) if row["row_status"] == "candidate_row" else []
        row["vendor_name_overlap_count"] = len(matches)
        row["vendor_overlap_recording_ids"] = "|".join(sorted(text(v.get("candidate_acquisition_id")) for v in matches))
        ci_dob = parse_date(row["raw_dob"])
        vendor_dobs = {parse_date(v.get("BirthDate")) for v in matches if parse_date(v.get("BirthDate")) is not None}
        row["vendor_dob_overlap"] = bool(ci_dob is not None and ci_dob in vendor_dobs)
        row["vendor_dob_conflict"] = bool(ci_dob is not None and vendor_dobs and ci_dob not in vendor_dobs)


def public_outputs(rows, schema, path, out, private_dir):
    vendor_overlap(rows)
    candidates = defaultdict(list)
    for row in rows:
        if row["row_status"] == "candidate_row" and row["participant_id"]:
            candidates[row["participant_id"]].append(row)
    candidate_rows = []
    for pid, group in sorted(candidates.items()):
        candidate_rows.append({
            "participant_id": pid,
            "n_source_rows": len(group),
            "n_sheets": len({row["source_sheet_index"] for row in group}),
            "name_parse_status": "non_han_name_key" if any(row["name_parse_status"] == "parsed_non_han" for row in group) else "han_leading_or_mixed",
            "dob_values_present": sum(bool(row["raw_dob"]) for row in group),
            "dob_parseable_rows": sum(parse_date(row["raw_dob"]) is not None for row in group),
            "clinical_date_parseable_rows": sum(parse_date(row["raw_clinical_date"]) is not None for row in group),
            "gender_values_present": sum(bool(row["raw_gender"]) for row in group),
            "eeg_date_values_present": sum(bool(row["raw_eeg_date"]) for row in group),
            "implant_date_values_present": sum(bool(row["raw_implant_date"]) for row in group),
            "activation_date_values_present": sum(bool(row["raw_activation_date"]) for row in group),
            "cooperation_status_values_present": sum(bool(row["raw_cooperation_status"]) for row in group),
            "patient_no_values_present": sum(bool(row["raw_patient_no"]) for row in group),
            "cap_values_present": sum(parse_number(row["raw_cap"]) is not None for row in group),
            "sir_values_present": sum(parse_number(row["raw_sir"]) is not None for row in group),
            "itmais_values_present": sum(parse_number(row["raw_itmais"]) is not None for row in group),
            "muss_values_present": sum(parse_number(row["raw_muss"]) is not None for row in group),
            "pta_values_present": sum(bool(row["raw_pta"]) for row in group),
            "pure_tone_audiology_values_present": sum(bool(row["raw_pure_tone"]) for row in group),
            "vendor_name_overlap": any(row["vendor_name_overlap_count"] for row in group),
            "vendor_dob_overlap": any(row["vendor_dob_overlap"] for row in group),
            "vendor_dob_conflict": any(row["vendor_dob_conflict"] for row in group),
        })
    table(out / "candidate_summary.csv", candidate_rows)
    canonical_fields = {
        "dob": "raw_dob", "gender": "raw_gender", "clinical_date": "raw_clinical_date",
        "eeg_date": "raw_eeg_date", "implant_date": "raw_implant_date",
        "activation_date": "raw_activation_date", "device_state": "raw_device_state",
        "cooperation_status": "raw_cooperation_status", "patient_no": "raw_patient_no",
        "CAP": "raw_cap", "SIR": "raw_sir", "IT_MAIS_MAIS": "raw_itmais",
        "MUSS": "raw_muss", "PTA_or_audiology": "raw_pta", "age_months": "raw_age_months",
        "pure_tone_audiology": "raw_pure_tone",
    }
    field_availability = {}
    for label, field in canonical_fields.items():
        present_rows = [row for row in rows if row["row_status"] == "candidate_row" and text(row[field])]
        candidate_present = sum(any(text(row[field]) for row in group) for group in candidates.values())
        field_availability[label] = {
            "candidate_count": candidate_present,
            "row_count": len(present_rows),
            "numeric_row_count": sum(parse_number(row[field]) is not None for row in present_rows),
            "date_parseable_row_count": sum(parse_date(row[field]) is not None for row in present_rows),
        }
    muss_values = [parse_number(row["raw_muss"]) for row in rows
                   if row["row_status"] == "candidate_row"]
    muss_values = [value for value in muss_values if value is not None]
    numeric_profiles = {}
    for label, field in (("CAP", "raw_cap"), ("SIR", "raw_sir"),
                         ("IT_MAIS_MAIS", "raw_itmais"), ("MUSS", "raw_muss")):
        values = [parse_number(row[field]) for row in rows
                  if row["row_status"] == "candidate_row"]
        values = [value for value in values if value is not None]
        numeric_profiles[label] = {
            "n": len(values),
            "min": min(values) if values else None,
            "median": median(values) if values else None,
            "max": max(values) if values else None,
            "value_frequency": dict(sorted(Counter(values).items())),
        }
    schema_public = []
    for item in schema:
        schema_public.append({key: value for key, value in item.items() if key != "recognized_column_headers"})
    (out / "schema_summary.json").write_text(json.dumps({"workbook_file_id": WORKBOOK_ID, "sha256": sha256(path), "sheets": schema_public}, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "input_sha256.json").write_text(json.dumps({
        "workbook": sha256(path),
        "vendor_identity_records": sha256(BASE / "private/linkage_001/vendor_identity_records.json"),
        "file_path_map": sha256(WORKBOOK_MAP),
    }, indent=2), encoding="utf-8")
    (out / "code_snapshot.py").write_bytes(Path(__file__).read_bytes())
    private_rows = []
    for row in rows:
        private_rows.append(row)
    table(private_dir / "candidate_rows_index.csv", private_rows)

    group_counts = Counter(row["name_parse_status"] for row in rows)
    row_status_counts = Counter(row["row_status"] for row in rows)
    summary = {
        "job_id": os.environ["SLURM_JOB_ID"],
        "workbook_file_id": WORKBOOK_ID,
        "workbook_sha256": sha256(path),
        "source_rows_with_values": len(rows),
        "row_status_counts": dict(row_status_counts),
        "non_identity_rows_excluded_from_candidate_counts": sum(row["row_status"] != "candidate_row" for row in rows),
        "candidate_participants": len(candidate_rows),
        "rows_by_name_parse_status": dict(group_counts),
        "recognized_fields_union": sorted({field for item in schema for field in
                                           (item["recognized_fields"] + item.get("ambiguous_fields", []))}),
        "ambiguous_fields_union": sorted({field for item in schema for field in item.get("ambiguous_fields", [])}),
        "field_availability": field_availability,
        "numeric_profiles": numeric_profiles,
        "muss_exact_100_row_count": sum(value == 100 for value in muss_values),
        "muss_scale_policy": "retain observed values and source header; no 0-100 conversion or ceiling assumption",
        "ci_vendor_name_overlap_candidates": sum(row["vendor_name_overlap"] for row in candidate_rows),
        "ci_vendor_dob_overlap_candidates": sum(row["vendor_dob_overlap"] for row in candidate_rows),
        "ci_vendor_dob_conflict_candidates": sum(row["vendor_dob_conflict"] for row in candidate_rows),
        "sheets_with_recognized_name_field": sum("name" in item["recognized_fields"] for item in schema),
        "clinical_date_status": "unknown_until_row_level_concurrent_date_check",
        "cohort_evidence": "CI extension workbook designated by the task/file_id; sheet names are not used as diagnostic labels",
        "device_status_policy": "extract_only; no filename or sheet-name diagnosis inference",
        "identity_policy": "one PID per normalized name key; repeated sheets/rows are retained and not counted as independent children",
        "eeg_clinical_link_model_fitted": False,
        "eeg_amplitudes_read": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-only", action="store_true")
    parser.add_argument("--private-run", default=RUN)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Slurm required for workbook parsing")
    os.umask(0o077)
    path = find_workbook()
    if args.schema_only:
        schema_probe(path, BASE / "private/phase3_ci_clinical_schema_001/schema.json")
        return
    out = BASE / "results" / args.private_run
    private_dir = BASE / "private" / args.private_run
    if out.exists() or private_dir.exists():
        raise FileExistsError("Phase 3 output directory already exists")
    out.mkdir()
    private_dir.mkdir(mode=0o700)
    rows, schema = clean_workbook(path, private_dir)
    if not rows:
        raise ValueError("no nonempty worksheet rows with a recognized name column")
    public_outputs(rows, schema, path, out, private_dir)


if __name__ == "__main__":
    main()
