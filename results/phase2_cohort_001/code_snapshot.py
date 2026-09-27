#!/usr/bin/env python3
"""Build a candidate-level, outcome-blinded Phase 2 cohort index.

This stage reads metadata only.  It deliberately does not read EEG samples and
does not make a clinical label or visit claim from a name match.
"""
import csv
import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, time
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
EXPECTED_RECORDS = 93
ELIGIBLE_GATE = "eligible_technical_measurement"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_table(path, rows):
    fields = sorted({key for row in rows for key in row})
    if not fields:
        fields = ["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text(value):
    return "" if value is None else str(value).strip()


def parse_date(value):
    raw = text(value).replace("Z", "+00:00")
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
        return parsed.date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(value):
    raw = text(value).replace("Z", "+00:00")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=None)
    except ValueError:
        pass
    formats = (
        "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S", "%d.%m.%Y %H:%M:%S",
        "%d.%m.%y %H.%M.%S", "%d.%m.%y %H:%M:%S",
    )
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_vendor_start(raw_start, raw_exam):
    """Return (datetime, status), retaining StartRecordTime as the authority.

    The vendor export commonly stores StartRecordTime as HH:MM and ExamTime as
    the dated timestamp.  Combining those fields preserves the real vendor
    start time without using filesystem dates or EEG quality.
    """
    full = parse_datetime(raw_start)
    if full is not None:
        return full, "parsed"
    raw = text(raw_start)
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", raw)
    exam_date = parse_date(raw_exam)
    if match is None or exam_date is None:
        return None, "parse_failed"
    hour, minute, second = (int(match.group(1)), int(match.group(2)),
                            int(match.group(3) or 0))
    try:
        return datetime.combine(exam_date, time(hour, minute, second)), "parsed"
    except ValueError:
        return None, "parse_failed"


def number(value):
    raw = text(value).replace(",", "")
    if not raw:
        return None
    try:
        parsed = float(raw.rstrip("%"))
        return parsed if math.isfinite(parsed) else None
    except ValueError:
        return None


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Slurm required for Phase 2 cohort processing")
    os.umask(0o077)

    out = BASE / "results/phase2_cohort_001"
    private = BASE / "private/phase2_cohort_001"
    if out.exists() or private.exists():
        raise FileExistsError("Phase 2 output directory already exists")
    out.mkdir()
    private.mkdir(mode=0o700)

    source_path = BASE / "results/phase1_sources_001/source_manifest.csv"
    vendor_path = BASE / "private/linkage_001/vendor_identity_records.json"
    link_path = BASE / "manifests/clinical_link.csv"
    participant_path = BASE / "manifests/participant_index.csv"
    clinical_path = BASE / "private/clinical_003/clinical_rows_clean.csv"
    config_path = BASE / "configs/phase2_v1.json"
    inputs = {
        "source_manifest": source_path,
        "vendor_identity_records": vendor_path,
        "clinical_link": link_path,
        "participant_index": participant_path,
        "clinical_rows_clean": clinical_path,
        "phase2_config": config_path,
    }
    for path in inputs.values():
        if not path.exists():
            raise FileNotFoundError(path)

    source_rows = read_csv(source_path)
    if len(source_rows) != EXPECTED_RECORDS:
        raise ValueError(f"expected {EXPECTED_RECORDS} source rows, found {len(source_rows)}")
    recording_ids = [row["recording_id"] for row in source_rows]
    if len(set(recording_ids)) != len(recording_ids):
        raise ValueError("duplicate recording_id in source manifest")

    vendors = json.loads(vendor_path.read_text(encoding="utf-8"))
    if not isinstance(vendors, list):
        raise ValueError("vendor identity records must be a list")
    vendor_by_recording = {text(row.get("candidate_acquisition_id")): row for row in vendors}
    if len(vendor_by_recording) != len(vendors):
        raise ValueError("duplicate vendor candidate acquisition id")
    missing_vendor = sorted(set(recording_ids) - set(vendor_by_recording))
    extra_vendor = sorted(set(vendor_by_recording) - set(recording_ids))
    if missing_vendor or extra_vendor:
        raise ValueError("vendor/source manifest coverage mismatch")

    participants = {row["participant_id"]: row for row in read_csv(participant_path)}
    source_by_recording = {row["recording_id"]: row for row in source_rows}
    if any(row["participant_id"] not in participants for row in source_rows):
        raise ValueError("source participant missing from participant_index")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("version") != "phase2_v1":
        raise ValueError("unexpected Phase 2 config version")
    config_hash = sha256(config_path)

    clinical_rows = {}
    for clinical in read_csv(clinical_path):
        raw_source_row = text(clinical.get("source_row"))
        try:
            clinical_id = f"C{int(raw_source_row):04d}"
        except ValueError as exc:
            raise ValueError(f"invalid clinical source_row: {raw_source_row!r}") from exc
        if clinical_id in clinical_rows:
            raise ValueError(f"duplicate normalized clinical row: {clinical_id}")
        clinical_rows[clinical_id] = clinical
    links_by_recording = defaultdict(list)
    for link in read_csv(link_path):
        rid = text(link.get("candidate_acquisition_id"))
        if not rid:
            continue
        if rid not in source_by_recording:
            raise ValueError(f"clinical link recording absent from source manifest: {rid}")
        if text(link.get("participant_id")) != source_by_recording[rid]["participant_id"]:
            raise ValueError(f"clinical link participant mismatch for {rid}")
        clinical_id = text(link.get("clinical_row_id"))
        if clinical_id and clinical_id not in clinical_rows:
            raise ValueError(f"clinical link row absent from clinical table: {clinical_id}")
        links_by_recording[rid].append(link)

    # Parse all vendor start timestamps before choosing an index.  A failed
    # timestamp prevents an identity index for the whole candidate group: a
    # later parseable record must never silently replace an uncertain earliest
    # record.
    by_pid = defaultdict(list)
    for source in source_rows:
        rid = source["recording_id"]
        pid = source["participant_id"]
        vendor = vendor_by_recording[rid]
        start_dt, start_status = parse_vendor_start(
            vendor.get("StartRecordTime"), vendor.get("ExamTime"))
        dob = parse_date(vendor.get("BirthDate"))
        dob_conflict = text(participants[pid].get("n_birthdate_strings")) not in ("", "0", "1")
        link_rows = links_by_recording.get(rid, [])
        linked_ids = sorted({text(link.get("clinical_row_id")) for link in link_rows if text(link.get("clinical_row_id"))})
        evidences = sorted({text(link.get("evidence")) for link in link_rows if text(link.get("evidence"))})
        strong = (len(linked_ids) == 1 and len(link_rows) > 0 and
                  all(text(link.get("evidence")) == "name_and_label_date" for link in link_rows))
        row = {
            "recording_id": rid,
            "participant_id": pid,
            "cohort_label": source.get("cohort_label", "unknown"),
            "source_gate": source.get("source_gate", ""),
            "identity_dob_conflict": dob_conflict,
            "source_hold": source.get("source_gate") != ELIGIBLE_GATE,
            "start_dt": start_dt,
            "start_status": start_status,
            "dob": dob,
            "link_ids": linked_ids,
            "link_evidences": evidences,
            "strong_unique_link": strong,
            "vendor": vendor,
            "source": source,
        }
        by_pid[pid].append(row)

    public_rows = []
    private_rows = []
    index_status_counts = Counter()
    for pid, group in sorted(by_pid.items()):
        date_complete = all(row["start_dt"] is not None for row in group)
        ordered = sorted(group, key=lambda row: (
            row["start_dt"] is None,
            row["start_dt"] or datetime.max,
            row["recording_id"],
        ))
        for ordinal, row in enumerate(ordered, 1):
            is_index = ordinal == 1
            no_conflict = not row["identity_dob_conflict"]
            source_eligible = row["source_gate"] == ELIGIBLE_GATE
            eligible_index = bool(is_index and date_complete and no_conflict and
                                  row["start_dt"] is not None and source_eligible)
            reasons = []
            if not is_index:
                reasons.append("not_earliest_vendor_start")
            if not date_complete:
                reasons.append("candidate_start_date_parse_failure")
            if row["start_dt"] is None:
                reasons.append("record_start_date_parse_failure")
            if row["identity_dob_conflict"]:
                reasons.append("dob_conflict")
            if row["source_gate"] != ELIGIBLE_GATE:
                reasons.append("source_hold")
            if not reasons:
                reasons.append("none")
            index_status_counts[reasons[0]] += 1
            public_rows.append({
                "recording_id": row["recording_id"],
                "participant_id": pid,
                "cohort": row["cohort_label"],
                "index_recording_flag": is_index,
                "ordinal": ordinal,
                "identity_dob_conflict": row["identity_dob_conflict"],
                "source_gate": row["source_gate"],
                "source_hold": row["source_gate"] != ELIGIBLE_GATE,
                "acquisition_date_parseable": row["start_dt"] is not None,
                "index_hold_reason": "|".join(reasons),
                "clinical_link_count": len(row["link_ids"]),
                "clinical_link_evidence": "|".join(row["link_evidences"]),
                "eligible_measurement_identity_index": eligible_index,
                "strong_unique_link": row["strong_unique_link"],
            })

            clinical_id = row["link_ids"][0] if len(row["link_ids"]) == 1 else ""
            clinical = clinical_rows.get(clinical_id, {}) if clinical_id else {}
            archival = bool(eligible_index and row["strong_unique_link"])
            clinical_age = number(clinical.get("age_months"))
            duration = number(clinical.get("duration_months"))
            muss = number(clinical.get("MUSS"))
            age_from_dob = None
            age_difference = None
            if row["dob"] is not None and row["start_dt"] is not None:
                age_from_dob = (row["start_dt"].date() - row["dob"]).days / 30.4375
                if clinical_age is not None:
                    age_difference = clinical_age - age_from_dob
            private_rows.append({
                "recording_id": row["recording_id"],
                "participant_id": pid,
                "cohort": row["cohort_label"],
                "index_recording_flag": is_index,
                "ordinal": ordinal,
                "identity_dob_conflict": row["identity_dob_conflict"],
                "source_gate": row["source_gate"],
                "eligible_measurement_identity_index": eligible_index,
                "vendor_start_record_time": row["vendor"].get("StartRecordTime", ""),
                "vendor_exam_time": row["vendor"].get("ExamTime", ""),
                "vendor_birth_date": row["vendor"].get("BirthDate", ""),
                "start_date_parse_status": row["start_status"],
                "clinical_row_id": clinical_id,
                "clinical_link_count": len(row["link_ids"]),
                "clinical_link_evidence": "|".join(row["link_evidences"]),
                "strong_unique_link": row["strong_unique_link"],
                "archival_association_candidate": archival,
                "clinical_date_status": "unknown_not_supplied",
                "clinical_age_months": clinical_age,
                "duration_months": duration,
                "MUSS": muss,
                "age_months_from_dob_at_vendor_start": age_from_dob,
                "clinical_age_minus_dob_age_months": age_difference,
            })

    # A compact public flow table contains no scale values, names, or dates.
    flow = []
    for cohort in sorted({row["cohort"] for row in public_rows}):
        subset = [row for row in public_rows if row["cohort"] == cohort]
        flow.append({
            "cohort": cohort,
            "records": len(subset),
            "candidate_participants": len({row["participant_id"] for row in subset}),
            "index_recordings": sum(row["index_recording_flag"] for row in subset),
            "source_hold_records": sum(row["source_hold"] for row in subset),
            "eligible_measurement_identity_indices": sum(row["eligible_measurement_identity_index"] for row in subset),
            "strong_unique_links": sum(row["strong_unique_link"] for row in subset),
        })
    flow.append({
        "cohort": "ALL",
        "records": len(public_rows),
        "candidate_participants": len({row["participant_id"] for row in public_rows}),
        "index_recordings": sum(row["index_recording_flag"] for row in public_rows),
        "source_hold_records": sum(row["source_hold"] for row in public_rows),
        "eligible_measurement_identity_indices": sum(row["eligible_measurement_identity_index"] for row in public_rows),
        "strong_unique_links": sum(row["strong_unique_link"] for row in public_rows),
    })

    # Clinical availability is reported only as counts.  Values themselves
    # remain in private/linked_index.csv.  Archival association candidates are
    # restricted to the eligible identity index plus one dated clinical link;
    # repeated or source-held records remain available for audit only.
    identity_index_rows = [row for row in private_rows if row["eligible_measurement_identity_index"]]
    archival_rows = [row for row in identity_index_rows if row["archival_association_candidate"]]
    def available(field):
        return [row[field] for row in archival_rows if row[field] is not None]
    muss_values = available("MUSS")
    by_cohort_audit = {}
    for cohort in sorted({row["cohort"] for row in public_rows}):
        cohort_rows = [row for row in archival_rows if row["cohort"] == cohort]
        complete = [row for row in cohort_rows if all(row[field] is not None for field in
                                                     ("clinical_age_months", "duration_months", "MUSS"))]
        differences = [abs(row["clinical_age_minus_dob_age_months"])
                       for row in cohort_rows if row["clinical_age_minus_dob_age_months"] is not None]
        by_cohort_audit[cohort] = {
            "identity_archival_candidates": len(cohort_rows),
            "complete_age_duration_muss": len(complete),
            "age_difference_gt_3_months": sum(value > 3 for value in differences),
            "age_difference_gt_12_months": sum(value > 12 for value in differences),
            "duration_greater_than_age": sum(
                row["duration_months"] > row["clinical_age_months"] for row in cohort_rows
                if row["duration_months"] is not None and row["clinical_age_months"] is not None),
            "duration_negative": sum(
                row["duration_months"] < 0 for row in cohort_rows
                if row["duration_months"] is not None),
            "muss_out_of_range_0_100": sum(
                row["MUSS"] < 0 or row["MUSS"] > 100 for row in cohort_rows
                if row["MUSS"] is not None),
            "muss_available": sum(row["MUSS"] is not None for row in cohort_rows),
        }
    clinical_audit = {
        "identity_index_records": len(identity_index_rows),
        "candidate_linked_rows": sum(bool(row["clinical_row_id"]) for row in private_rows),
        "archival_association_candidate_records": len(archival_rows),
        "archival_muss_available": len(muss_values),
        "archival_age_months_available": len(available("clinical_age_months")),
        "archival_duration_months_available": len(available("duration_months")),
        "archival_muss_ceiling_count": sum(value == 100.0 for value in muss_values),
        "archival_muss_ceiling_fraction": (sum(value == 100.0 for value in muss_values) / len(muss_values)
                                            if muss_values else None),
        "vendor_start_date_parseable_records": sum(row["start_date_parse_status"] == "parsed" for row in private_rows),
        "vendor_birth_date_parseable_records": sum(bool(row["vendor_birth_date"]) and
                                                    parse_date(row["vendor_birth_date"]) is not None
                                                    for row in private_rows),
        "age_difference_available_records": sum(row["clinical_age_minus_dob_age_months"] is not None
                                                for row in identity_index_rows),
        "by_cohort": by_cohort_audit,
        "clinical_date_status": "unknown_not_supplied",
    }

    write_table(out / "index_recordings.csv", public_rows)
    write_table(out / "cohort_flow.csv", flow)
    (out / "input_sha256.json").write_text(json.dumps({name: sha256(path) for name, path in inputs.items()}, indent=2), encoding="utf-8")
    (out / "code_snapshot.py").write_bytes(Path(__file__).read_bytes())
    (out / "phase2_v1.json").write_bytes(config_path.read_bytes())

    private_rows.sort(key=lambda row: (row["participant_id"], row["ordinal"], row["recording_id"]))
    write_table(private / "linked_index.csv", private_rows)
    (private / "errors.json").write_text("[]\n", encoding="utf-8")

    source_gate_counts = Counter(row["source_gate"] for row in public_rows)
    source_hold_reasons = Counter()
    for row in source_rows:
        if row.get("source_gate") == ELIGIBLE_GATE:
            continue
        try:
            reasons = json.loads(row.get("source_gate_reasons", "[]"))
        except json.JSONDecodeError:
            reasons = ["unparseable_source_gate_reasons"]
        source_hold_reasons.update(text(reason) for reason in reasons if text(reason))
    dob_conflicts = sum(row["identity_dob_conflict"] for row in public_rows if row["index_recording_flag"])
    summary = {
        "job_id": os.environ["SLURM_JOB_ID"],
        "records": len(public_rows),
        "candidate_participants": len({row["participant_id"] for row in public_rows}),
        "source_gate_counts": dict(source_gate_counts),
        "source_hold_records": sum(row["source_hold"] for row in public_rows),
        "source_hold_reasons": dict(source_hold_reasons),
        "index_recordings": sum(row["index_recording_flag"] for row in public_rows),
        "index_records_with_dob_conflict": dob_conflicts,
        "index_date_parse_failures": sum(row["index_recording_flag"] and not row["acquisition_date_parseable"] for row in public_rows),
        "candidate_groups_with_date_parse_failure": sum(
            any(row["start_dt"] is None for row in group) for group in by_pid.values()),
        "eligible_measurement_identity_indices": sum(row["eligible_measurement_identity_index"] for row in public_rows),
        "strong_unique_links": sum(row["strong_unique_link"] for row in public_rows),
        "index_status_counts": dict(index_status_counts),
        "clinical_availability": clinical_audit,
        "input_sha256": {name: sha256(path) for name, path in inputs.items()},
        "config_sha256": config_hash,
        "clinical_outcomes_used_for_selection": False,
        "eeg_amplitudes_read": False,
        "date_policy": "vendor StartRecordTime, dated by vendor ExamTime only when StartRecordTime is time-only; parse failures remain held",
        "identity_policy": "earliest vendor start per candidate participant, recording_id tie-break; no EEG, scale, or link-based replacement",
        "archival_policy": "only earliest source-eligible, no-DOB-conflict index records with one name_and_label_date link are archival association candidates; not confirmed concurrent visits",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
