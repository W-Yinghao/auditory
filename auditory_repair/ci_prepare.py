#!/usr/bin/env python3
"""Prepare a conservative linked MFF archival regression cohort.

Only already-derived Phase 3 record summaries are used.  The selected source
is the earliest timestamped canonical EEG record for each unambiguous linked
candidate, chosen before endpoint availability is inspected.  Literal score
values remain in their registered archive units; this module performs no unit
normalization and no clinical model fitting.
"""
import csv
import hashlib
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[1]
RUN = "ci_prepare_004"
OUT = BASE / "results" / "auditory_repair" / RUN
PRIVATE = BASE / "private" / "results" / "auditory_repair" / RUN

INPUTS = {
    "clinical_rows": BASE / "private/phase3_ci_clinical_004/candidate_rows_index.csv",
    "clinical_schema": BASE / "private/phase3_ci_clinical_004/schema_private.json",
    "labels": BASE / "results/phase3_ci_linkage_005/canonical_source_labels.csv",
    "links": BASE / "results/phase3_ci_linkage_005/clinical_source_links.csv",
    "source_manifest": BASE / "results/phase3_ci_sources_001/source_manifest.csv",
    "source_paths": BASE / "private/phase3_ci_sources_001/source_paths_and_tokens.csv",
    "metadata_addendum": BASE / "results/phase3_metadata_addendum_001/source_metadata.csv",
    "features": BASE / "results/phase3_ci_measurements_001/features.csv",
    "half_scores": BASE / "results/phase3_ci_measurements_001/half_scores.csv",
}

ENDPOINT_FIELDS = {
    "A": "raw_itmais",
    "V": "raw_muss",
    "CAP": "raw_cap",
    "SIR": "raw_sir",
}

Z_NAMES = [
    "stad_primary_main_mean_uv",
    "stad_primary_late_mean_uv",
    "stad_primary_late_minus_main_uv",
]
Q_NAMES = [
    "log1p_stad_primary_trials",
    "stad_primary_retention_fraction",
    "stad_primary_reliability_r_alternating",
    "stad_primary_reliability_rmse_alternating_uv",
    "stad_primary_reliability_r_early_late",
    "stad_primary_reliability_rmse_early_late_uv",
    "n_channels",
    "roi_distance_max_m",
    "sfreq_hz",
    "stad_feature_available",
    "stad_reliability_available",
]
C_NAMES = ["age_months", "ci_duration_months", "ha_duration_months"]


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def number(value):
    raw = str(value or "").strip().replace(",", "").replace("%", "")
    if not raw:
        return None
    try:
        parsed = float(raw)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def json_list_numbers(value):
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = []
    return [float(v) for v in parsed if isinstance(v, (int, float)) and math.isfinite(float(v))]


def parse_iso(value):
    raw = str(value or "").strip().replace("Z", "+00:00")
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=None)
    return parsed.astimezone().replace(tzinfo=None)


def parse_date(value):
    parsed = parse_iso(value)
    if parsed is not None:
        return parsed.date()
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def row_ref(row):
    material = "|".join(row.get(key, "") for key in
                         ("participant_id", "source_sheet_index", "source_worksheet_row"))
    return "R" + hashlib.sha256(material.encode()).hexdigest()[:12]


def unique_numeric(values):
    clean = sorted(set(v for v in values if v is not None and math.isfinite(float(v))))
    return clean


def literal_endpoint(rows, field):
    return unique_numeric([number(row.get(field, "")) for row in rows])


def safe_float(value):
    value = number(value)
    return np.nan if value is None else value


def source_scope(label, metadata):
    if label.get("source_cohort_evidence") in {"CI", "CIHA_label"}:
        return "expanded_CI_scope"
    if str(metadata.get("clinical_CI_history_same_day", "")).lower() == "true":
        return "expanded_CI_scope"
    return "all_canonical_MFF"


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("CI cohort preparation must run under Slurm")
    os.umask(0o077)
    if OUT.exists() or PRIVATE.exists():
        raise FileExistsError(f"output already exists: {OUT} or {PRIVATE}")
    missing = [str(path) for path in INPUTS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing registered inputs: " + ", ".join(missing))
    OUT.mkdir(parents=True)
    PRIVATE.mkdir(parents=True, mode=0o700)

    hashes = {name: sha256(path) for name, path in INPUTS.items()}
    (PRIVATE / "input_sha256.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    shutil.copy2(Path(__file__), PRIVATE / "ci_prepare.py")
    (PRIVATE / "ci_prepare.py").chmod(0o600)
    (OUT / "source_snapshot.json").write_text(json.dumps({
        "run": RUN,
        "job_id": os.environ["SLURM_JOB_ID"],
        "logical_inputs": hashes,
        "selection_rule": "earliest timestamped canonical EEG source per unambiguous exact-name/date candidate link before endpoint filtering",
        "outcome_rule": "literal archive values retained; no unit normalization",
    }, indent=2), encoding="utf-8")

    clinical_rows = [row for row in read_csv(INPUTS["clinical_rows"])
                     if row.get("row_status") == "candidate_row"]
    clinical_by_ref = {row_ref(row): row for row in clinical_rows}
    labels = {row["container_id"]: row for row in read_csv(INPUTS["labels"])}
    metadata = {row["container_id"]: row for row in read_csv(INPUTS["metadata_addendum"])}
    manifest = {row["container_id"]: row for row in read_csv(INPUTS["source_manifest"])}
    paths = {row["container_id"]: row for row in read_csv(INPUTS["source_paths"])}
    canonical = {
        cid for cid, row in manifest.items()
        if row.get("source_status") == "eligible"
        and (row.get("canonical_container_id") or cid) == cid
        and cid in paths and parse_iso(paths[cid].get("record_time")) is not None
    }
    features = read_csv(INPUTS["features"])
    halves = read_csv(INPUTS["half_scores"])
    primary_stad = {
        row["container_id"]: row for row in features
        if row.get("container_id") in canonical
        and row.get("variant") == "primary"
        and row.get("event_code") == "stad"
    }
    reliability = {}
    for row in halves:
        key = (row.get("container_id"), row.get("variant"), row.get("event_code"), row.get("split"))
        if row.get("container_id") in canonical and row.get("variant") == "primary" and row.get("event_code") == "stad":
            reliability[key] = row

    links = [row for row in read_csv(INPUTS["links"])
             if row.get("container_id") in canonical
             and row.get("canonical_container_id") == row.get("container_id")
             and row.get("source_status") == "eligible"
             and row.get("link_status") == "exact_name_date"
             and row.get("date_agreement") == "same_calendar_day"
             and row.get("accepted_name_link") == "true"
             and row.get("source_candidate_ambiguity") == "unique_participant"
             and row.get("diagnostic_only") == "false"]
    links_by_group = defaultdict(list)
    links_by_source = defaultdict(list)
    for link in links:
        links_by_group[link.get("participant_id", "")].append(link)
        links_by_source[link.get("container_id", "")].append(link)

    # Audit all clinical rows linked to each candidate identity before source
    # selection.  A conflicting DOB, a vendor-marked DOB contradiction, a
    # vendor name-overlap flag, or an unparsed linked name is an identity hold
    # for the whole candidate group.  It is never repaired by selecting a
    # later EEG source.
    group_audit = {}
    for group, group_links in sorted(links_by_group.items()):
        linked_rows = [clinical_by_ref.get(link.get("clinical_row_ref"), {}) for link in group_links]
        linked_rows = [row for row in linked_rows if row]
        dob_dates = sorted({parse_date(row.get("raw_dob", "")) for row in linked_rows
                            if parse_date(row.get("raw_dob", "")) is not None})
        name_statuses = sorted({row.get("name_parse_status", "") for row in linked_rows if row.get("name_parse_status", "")})
        vendor_dob_conflict = any(str(row.get("vendor_dob_conflict", "")).lower() == "true" for row in linked_rows)
        vendor_name_overlap = any(number(row.get("vendor_name_overlap_count")) not in (None, 0) for row in linked_rows)
        reasons = []
        if vendor_dob_conflict:
            reasons.append("vendor_dob_conflict")
        if len(dob_dates) > 1:
            reasons.append("multiple_parsed_dob_values")
        if vendor_name_overlap:
            reasons.append("vendor_name_overlap")
        if any(not status.startswith("parsed_") for status in name_statuses):
            reasons.append("name_parse_status_not_parsed")
        group_audit[group] = {
            "dob_dates": dob_dates,
            "name_statuses": name_statuses,
            "vendor_dob_conflict": vendor_dob_conflict,
            "vendor_name_overlap": vendor_name_overlap,
            "identity_hold": bool(reasons),
            "identity_hold_reasons": reasons,
        }

    # Identity contradictions are rejected before endpoint or feature
    # availability is considered.  This preserves low support rather than
    # replacing an early poor-quality source with a later source.
    exclusion_counts = Counter()
    candidate_sources = {}
    selection_rows = []
    for group, group_links in sorted(links_by_group.items()):
        audit = group_audit[group]
        if audit["identity_hold"]:
            for reason in audit["identity_hold_reasons"]:
                exclusion_counts[reason] += 1
            continue
        source_ids = sorted({link["container_id"] for link in group_links})
        candidates = []
        for cid in source_ids:
            if cid not in canonical:
                exclusion_counts["noncanonical_or_un-timestamped_source"] += 1
                continue
            label = labels.get(cid, {})
            if label.get("source_candidate_ambiguity") != "unique_participant":
                exclusion_counts["source_identity_ambiguity"] += 1
                continue
            timestamp = parse_iso(paths[cid].get("record_time"))
            if timestamp is None:
                exclusion_counts["missing_record_timestamp"] += 1
                continue
            candidates.append((timestamp, cid))
        if not candidates:
            exclusion_counts["no_timestamped_unambiguous_source"] += 1
            continue
        candidates.sort()
        earliest_time = candidates[0][0]
        earliest = [cid for timestamp, cid in candidates if timestamp == earliest_time]
        if len(earliest) != 1:
            exclusion_counts["earliest_timestamp_tie"] += 1
            continue
        selected = earliest[0]
        candidate_sources[group] = selected
        for rank, (timestamp, cid) in enumerate(candidates, start=1):
            selection_rows.append({
                "candidate_group": group, "container_id": cid,
                "record_time": paths[cid].get("record_time", ""),
                "rank_before_outcome_filter": rank,
                "selected_earliest": str(cid == selected).lower(),
                "source_path": paths[cid].get("path", ""),
                "source_subject": paths[cid].get("subject", ""),
                "source_label": labels.get(cid, {}).get("source_cohort_evidence", "unknown"),
                "identity_status": "unique_participant_exact_name_same_day",
            })
    if not candidate_sources:
        raise RuntimeError("no unambiguous timestamped candidate sources")
    write_csv(PRIVATE / "selection_evidence.csv", selection_rows)

    selected_rows = []
    arrays = {name: [] for name in ("C", "Q", "Z", "A", "V", "CAP", "SIR")}
    groups = []
    recordings = []
    endpoint_valid = {name: [] for name in ENDPOINT_FIELDS}
    source_labels = []
    scopes = []
    protocol_tasks = []
    configurations = []
    identity_statuses = []
    record_times = []
    age_statuses = []

    for group, cid in sorted(candidate_sources.items(), key=lambda item: (parse_iso(paths[item[1]].get("record_time")), item[0])):
        label = labels.get(cid, {})
        meta = metadata.get(cid, {})
        linked_rows = [clinical_by_ref.get(link.get("clinical_row_ref"), {})
                       for link in links_by_source.get(cid, [])]
        linked_rows = [row for row in linked_rows if row]
        endpoint_values = {name: literal_endpoint(linked_rows, field)
                           for name, field in ENDPOINT_FIELDS.items()}
        primary = primary_stad.get(cid, {})
        feature_available = primary.get("status") == "measured"
        main = safe_float(primary.get("main_mean_uv")) if feature_available else np.nan
        late = safe_float(primary.get("late_mean_uv")) if feature_available else np.nan
        z = np.array([main, late, late - main if np.isfinite(main) and np.isfinite(late) else np.nan], dtype=float)

        # Numeric clinical covariates are accepted only from explicit source
        # fields.  No duration is derived from dates in this preparation.
        # Age is derived only from one unique parsed DOB and the selected EEG
        # record timestamp.  The clinical assessment date is never used as a
        # proxy for EEG time.  No numeric source-verified duration field exists
        # in the registered schema, so both duration covariates remain NaN.
        selected_dob = group_audit[group]["dob_dates"]
        record_dt = parse_iso(paths[cid].get("record_time"))
        if len(selected_dob) == 1 and record_dt is not None:
            age_days = (record_dt.date() - selected_dob[0]).days
            age = age_days / 30.4375 if age_days >= 0 else np.nan
            age_status = "derived_unique_dob_plus_eeg_record_time"
        elif not selected_dob:
            age = np.nan
            age_status = "dob_absent_or_unparsed"
        else:
            age = np.nan
            age_status = "dob_or_eeg_time_unusable"
        c = np.array([age, np.nan, np.nan], dtype=float)

        quality = json.loads(manifest[cid].get("annotation_code_counts", "{}"))
        stad_target = number(quality.get("stad"))
        trials = number(primary.get("n_trials")) if feature_available else np.nan
        retention = trials / stad_target if np.isfinite(trials) and stad_target and stad_target > 0 else np.nan
        alt = reliability.get((cid, "primary", "stad", "alternating_30s_blocks"), {})
        early = reliability.get((cid, "primary", "stad", "early_late_time"), {})
        rel_values = [
            np.log1p(trials) if np.isfinite(trials) and trials >= 0 else np.nan,
            retention,
            safe_float(alt.get("waveform_r")) if alt.get("status") == "measured" else np.nan,
            safe_float(alt.get("waveform_rmse_uv")) if alt.get("status") == "measured" else np.nan,
            safe_float(early.get("waveform_r")) if early.get("status") == "measured" else np.nan,
            safe_float(early.get("waveform_rmse_uv")) if early.get("status") == "measured" else np.nan,
            safe_float(manifest[cid].get("n_channels")),
            max(json_list_numbers(manifest[cid].get("roi_distance_m"))) if json_list_numbers(manifest[cid].get("roi_distance_m")) else np.nan,
            safe_float(manifest[cid].get("sfreq")),
            float(np.isfinite(z).all()),
            float(alt.get("status") == "measured" and early.get("status") == "measured"),
        ]
        q = np.array(rel_values, dtype=float)
        for name, values in (("C", c), ("Q", q), ("Z", z)):
            arrays[name].append(values)
        for name in ENDPOINT_FIELDS:
            arrays[name].append(endpoint_values[name][0] if len(endpoint_values[name]) == 1 else np.nan)
            endpoint_valid[name].append(len(endpoint_values[name]) == 1)
        groups.append(group)
        recordings.append(cid)
        source_label = label.get("source_cohort_evidence", "unknown") or "unknown"
        source_labels.append(source_label)
        scopes.append(source_scope(label, meta))
        protocol_tasks.append(label.get("protocol_task", "unknown") or "unknown")
        configurations.append(label.get("configuration_literal", "unknown") or "unknown")
        identity_statuses.append("unique_participant_exact_name_same_day")
        record_times.append(paths[cid].get("record_time", ""))
        age_statuses.append(age_status)
        selected_rows.append({
            "candidate_group": group, "recording": cid,
            "record_time": paths[cid].get("record_time", ""),
            "source_path": paths[cid].get("path", ""),
            "source_label": source_label, "scope": scopes[-1],
            "protocol_task": protocol_tasks[-1],
            "configuration_literal": configurations[-1],
            "identity_status": identity_statuses[-1],
            "age_source_status": age_status,
            "dob_value_count": len(selected_dob),
            "A_valid": str(endpoint_valid["A"][-1]).lower(),
            "V_valid": str(endpoint_valid["V"][-1]).lower(),
            "CAP_valid": str(endpoint_valid["CAP"][-1]).lower(),
            "SIR_valid": str(endpoint_valid["SIR"][-1]).lower(),
            "stad_feature_available": str(bool(q[9])).lower(),
            "stad_reliability_available": str(bool(q[10])).lower(),
        })
    write_csv(PRIVATE / "cohort.csv", selected_rows)

    np.savez(
        PRIVATE / "data.npz",
        C=np.asarray(arrays["C"], dtype=float),
        Q=np.asarray(arrays["Q"], dtype=float),
        Z=np.asarray(arrays["Z"], dtype=float),
        A=np.asarray(arrays["A"], dtype=float),
        V=np.asarray(arrays["V"], dtype=float),
        CAP=np.asarray(arrays["CAP"], dtype=float),
        SIR=np.asarray(arrays["SIR"], dtype=float),
        A_valid=np.asarray(endpoint_valid["A"], dtype=bool),
        V_valid=np.asarray(endpoint_valid["V"], dtype=bool),
        CAP_valid=np.asarray(endpoint_valid["CAP"], dtype=bool),
        SIR_valid=np.asarray(endpoint_valid["SIR"], dtype=bool),
        groups=np.asarray(groups, dtype="U64"),
        recordings=np.asarray(recordings, dtype="U32"),
    )

    feature_schema = {
        "C": C_NAMES,
        "Q": Q_NAMES,
        "Z": Z_NAMES,
        "targets": {"A": "raw_itmais_literal_0_to_40", "V": "raw_muss_literal_0_to_40", "CAP": "raw_cap_literal_observed_0_to_7_theoretical_0_to_9", "SIR": "raw_sir_literal_1_to_5"},
        "categorical_columns": ["source_label", "scope", "protocol_task", "configuration_literal", "identity_status"],
        "missingness": "NaN retained for train-fold imputation; no endpoint or feature availability selection after earliest source selection",
        "slope_latency": "not available in frozen record feature table; no picked-peak substitute added",
        "age_derivation": "derived only from one unique parsed DOB plus selected EEG record_time; clinical assessment dates are not used",
        "duration": "ci_duration_months and ha_duration_months remain NaN because schema_private.json has no recognized numeric activation, implant, or HA duration field",
    }
    (OUT / "feature_schema.json").write_text(json.dumps(feature_schema, indent=2), encoding="utf-8")

    def counts(values):
        return dict(sorted(Counter(values).items()))

    support_rows = []
    for name in ("A", "V", "CAP", "SIR"):
        valid = np.asarray(endpoint_valid[name], dtype=bool)
        support_rows.append({"target": name, "selected_records": len(groups), "valid_unique_literal_values": int(valid.sum()), "missing_or_conflicting": int((~valid).sum())})
    write_csv(OUT / "target_support.csv", support_rows)
    write_csv(OUT / "source_category_support.csv", [
        {"category": "source_label", "value": key, "records": value}
        for key, value in counts(source_labels).items()
    ] + [
        {"category": "scope", "value": key, "records": value}
        for key, value in counts(scopes).items()
    ] + [
        {"category": "protocol_task", "value": key, "records": value}
        for key, value in counts(protocol_tasks).items()
    ])
    summary = {
        "status": "COMPLETED_COHORT_PREPARATION",
        "job_id": os.environ["SLURM_JOB_ID"],
        "selected_records": len(groups),
        "selected_candidate_identity_groups": len(set(groups)),
        "canonical_timestamped_sources": len(canonical),
        "link_rows_used": len(links),
        "scope_counts": counts(scopes),
        "source_label_counts": counts(source_labels),
        "target_valid_counts": {name: int(np.asarray(endpoint_valid[name], dtype=bool).sum()) for name in ENDPOINT_FIELDS},
        "feature_availability": {
            "stad_primary_main_late": int(np.isfinite(np.asarray(arrays["Z"], dtype=float)[:, :2]).all(axis=1).sum()),
            "stad_reliability_both_splits": int(np.asarray(arrays["Q"], dtype=float)[:, 10].sum()),
            "age_months_unique_dob_eeg_time_derived": int(np.isfinite(np.asarray(arrays["C"], dtype=float)[:, 0]).sum()),
            "ci_duration_months_explicit_numeric": 0,
            "ha_duration_months_explicit_numeric": 0,
        },
        "age_source_status_counts": counts(age_statuses),
        "identity_exclusions": dict(exclusion_counts),
        "models_fit": False,
        "raw_eeg_read": False,
        "new_signal_features": False,
        "unit_normalization": False,
        "earliest_source_selected_before_endpoint_filtering": True,
        "output_private": f"private/results/auditory_repair/{RUN}/cohort.csv and data.npz",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "completion.json").write_text(json.dumps({"status": "COMPLETED", "job_id": os.environ["SLURM_JOB_ID"], "run": RUN}, indent=2), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
