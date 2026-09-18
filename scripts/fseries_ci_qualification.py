#!/usr/bin/env python3
"""Stage 1 CI/MFF clinical qualification for the F-series plan.

This is a metadata and registered-row audit only.  It does not load EEG
arrays, fit a clinical model, compute an EEG--outcome association, or infer a
diagnosis.  Raw row values, dates, source paths, and identity evidence are
written only below private/auditory_fseries/ci_qualification_001.
"""
import csv
import hashlib
import json
import math
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RUN = "ci_qualification_001"
OUT = BASE / "results" / "auditory_fseries" / RUN
PRIVATE = BASE / "private" / "auditory_fseries" / RUN

INPUTS = {
    "config": BASE / "configs/auditory_fseries_qualification_v1.json",
    "protocol": BASE / "docs/auditory_fseries/STAGE1_PROTOCOL.md",
    "plan": BASE / "AUDITORY_FUNCTIONAL_DECODING_F1_F4_RESEARCH_PLAN_v1.md",
    "clinical_rows": BASE / "private/phase3_ci_clinical_004/candidate_rows_index.csv",
    "clinical_schema": BASE / "private/phase3_ci_clinical_004/schema_private.json",
    "clinical_hashes": BASE / "results/phase3_ci_clinical_004/input_sha256.json",
    "links": BASE / "results/phase3_ci_linkage_005/clinical_source_links.csv",
    "labels": BASE / "results/phase3_ci_linkage_005/canonical_source_labels.csv",
    "source_manifest": BASE / "results/phase3_ci_sources_001/source_manifest.csv",
    "source_paths": BASE / "private/phase3_ci_sources_001/source_paths_and_tokens.csv",
    "features": BASE / "results/phase3_ci_measurements_001/features.csv",
    "addendum": BASE / "results/phase3_metadata_addendum_001/source_metadata.csv",
    "notes": BASE / "results/phase3_metadata_addendum_001/clinical_note_annotations.csv",
    "document_scale_evidence": BASE / "results/auditory_fseries/document_evidence_002/summary.json",
}


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


def text(value):
    return "" if value is None else str(value).strip()


def parse_jsonish(value):
    raw = text(value)
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else [parsed]
        except (TypeError, ValueError, json.JSONDecodeError):
            return [raw]
    return [value]


def parse_date(value):
    raw = text(value).replace("Z", "+00:00")
    if not raw:
        return None
    try:
        if isinstance(value, datetime):
            return value.date()
        return datetime.fromisoformat(raw).date()
    except (ValueError, TypeError):
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d.%m.%Y", "%d.%m.%y", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    match = re.search(r"(?<!\d)(20\d{2})[-/.]?(\d{1,2})[-/.]?(\d{1,2})(?!\d)", raw)
    if match:
        try:
            return date(int(match[1]), int(match[2]), int(match[3]))
        except ValueError:
            return None
    return None


def unique_date(value):
    dates = {d for item in parse_jsonish(value) if (d := parse_date(item)) is not None}
    return next(iter(dates)) if len(dates) == 1 else None


def number(value):
    values = []
    for item in parse_jsonish(value):
        raw = text(item).replace(",", "").replace("%", "")
        if not raw:
            continue
        try:
            n = float(raw)
        except ValueError:
            continue
        if math.isfinite(n):
            values.append(n)
    unique = sorted(set(values))
    return unique[0] if len(unique) == 1 else None


def row_ref(row):
    material = "|".join((row.get(k, "") for k in ("participant_id", "source_sheet_index", "source_worksheet_row")))
    return "R" + hashlib.sha256(material.encode()).hexdigest()[:12]


def source_record_date(rows):
    dates = {unique_date(row.get("record_time", "")) for row in rows if unique_date(row.get("record_time", ""))}
    return next(iter(dates)) if len(dates) == 1 else None


def endpoint_definition(endpoint):
    # These are deliberately conservative: a named source column establishes
    # literal availability, not a confirmed version/scoring/unit definition.
    definitions = {
        "IT_MAIS_or_MAIS": {
            "header_class": "IT-MAIS/MAIS_combined_percent_header",
            "source_scale_definition": "registered_HA_document_defines_IT-MAIS_total_0_to_40_and_percent_score_divide_by_40",
            "version_status": "row_version_unresolved_IT-MAIS_vs_MAIS",
            "scoring_status": "source_definition_known_row_assignment_unresolved",
            "unit_status": "percent_header_row_unit_assignment_unresolved",
            "comparability_status": "not_confirmed_for_this_CI_row_set",
        },
        "MUSS": {
            "header_class": "MUSS_percent_header",
            "source_scale_definition": "registered_HA_document_defines_MUSS_total_0_to_40_and_percent_score_divide_by_40",
            "version_status": "source_version_unresolved",
            "scoring_status": "source_definition_known_observed_0_to_40_row_attribution_unresolved",
            "unit_status": "percent_header_with_0_to_40_values_row_unit_unresolved",
            "comparability_status": "not_confirmed_for_this_CI_row_set",
        },
        "CAP": {
            "header_class": "CAP_named_header",
            "source_scale_definition": "registered_HA_document_defines_CAP_II_ordinal_0_to_9",
            "version_status": "row_version_unresolved_CAP_vs_CAP_II",
            "scoring_status": "source_definition_known_row_assignment_unresolved",
            "unit_status": "ordinal_unitless_row_assignment_unresolved",
            "comparability_status": "not_confirmed_for_this_CI_row_set",
        },
        "SIR": {
            "header_class": "SIR_named_header",
            "source_scale_definition": "registered_HA_document_defines_SIR_ordinal_1_to_5",
            "version_status": "source_version_unresolved",
            "scoring_status": "source_definition_known_row_assignment_unresolved",
            "unit_status": "ordinal_unitless_row_assignment_unresolved",
            "comparability_status": "not_confirmed_for_this_CI_row_set",
        },
    }
    return definitions[endpoint]


def classify_scope(label, metadata):
    literal = label.get("source_cohort_evidence", "") in {"CI", "CIHA_label"}
    explicit_history = metadata.get("clinical_CI_history_same_day", "").lower() == "true"
    if literal or explicit_history:
        return "expanded_CI_scope"
    return "all_linked_scope"


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("F-series qualification must run under Slurm")
    os.umask(0o077)
    if OUT.exists() or PRIVATE.exists():
        raise FileExistsError("qualification output already exists")
    OUT.mkdir(parents=True)
    PRIVATE.mkdir(parents=True, mode=0o700)

    missing = [str(p) for p in INPUTS.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("missing registered inputs: " + ", ".join(missing))
    hashes = {name: sha256(path) for name, path in INPUTS.items()}
    (PRIVATE / "input_sha256.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    (PRIVATE / "source_manifest.json").write_text(json.dumps({"run": RUN, "job_id": os.environ["SLURM_JOB_ID"], "inputs": hashes}, indent=2), encoding="utf-8")
    for source_path in (Path(__file__), INPUTS["config"], INPUTS["protocol"]):
        copied = PRIVATE / source_path.name
        shutil.copy2(source_path, copied)
        copied.chmod(0o600)

    clinical_rows = [r for r in read_csv(INPUTS["clinical_rows"]) if r.get("row_status") == "candidate_row"]
    clinical = {row_ref(r): r for r in clinical_rows}
    # Deduplicate exact repeated workbook rows by candidate, assessment date,
    # endpoint payload, and DOB.  Row references remain in private provenance.
    dedup = {}
    dedup_refs = defaultdict(list)
    for ref, row in clinical.items():
        cdate = unique_date(row.get("raw_clinical_date", ""))
        payload = tuple(row.get("raw_" + ep, "") for ep in ("itmais", "muss", "cap", "sir"))
        key = (row.get("participant_id", ""), cdate.isoformat() if cdate else "date_unavailable", payload, row.get("raw_dob", ""))
        dedup.setdefault(key, dict(row, clinical_row_ref=ref, clinical_date=cdate.isoformat() if cdate else ""))
        dedup_refs[key].append(ref)
    assessments = list(dedup.values())
    write_csv(PRIVATE / "clinical_row_provenance.csv", [
        {"dedup_key_sha256": hashlib.sha256(repr(key).encode()).hexdigest(), "clinical_row_refs": "|".join(refs), "participant_id": dedup[key].get("participant_id", ""), "clinical_date": dedup[key].get("clinical_date", ""), "n_rows_collapsed": len(refs)}
        for key, refs in dedup_refs.items()
    ])

    # Establish the clinical-only denominator before any EEG linkage.  These
    # counts are deliberately separate from source-level visit support.
    endpoint_fields = {"IT_MAIS_or_MAIS": "raw_itmais", "MUSS": "raw_muss", "CAP": "raw_cap", "SIR": "raw_sir"}
    declared_max = {"IT_MAIS_or_MAIS": 40.0, "MUSS": 40.0, "CAP": 9.0, "SIR": 5.0}
    clinical_endpoint_profile = []
    for endpoint, field in endpoint_fields.items():
        row_values = [number(row.get(field, "")) for row in clinical_rows]
        row_values = [value for value in row_values if value is not None]
        by_pid = defaultdict(list)
        for row in clinical_rows:
            value = number(row.get(field, ""))
            if value is not None:
                by_pid[row.get("participant_id", "")].append(value)
        unique_groups = {pid: sorted(set(values)) for pid, values in by_pid.items()}
        clinical_endpoint_profile.append({
            "endpoint": endpoint,
            "registered_candidate_rows": len(clinical_rows),
            "rows_with_unique_literal_numeric_value": len(row_values),
            "candidate_identity_groups_with_literal_numeric_value": len(unique_groups),
            "candidate_identity_groups_with_conflicting_numeric_values": sum(len(values) > 1 for values in unique_groups.values()),
            "rows_missing_or_non_numeric": len(clinical_rows) - len(row_values),
            "observed_min": min(row_values) if row_values else None,
            "observed_max": max(row_values) if row_values else None,
            "rows_at_declared_source_max": sum(value == declared_max[endpoint] for value in row_values),
            "declared_source_max": declared_max[endpoint],
            "ceiling_interpretation": "descriptive_only_until_row_scale_version_and_unit_are assigned",
        })
    write_csv(OUT / "clinical_endpoint_profile.csv", clinical_endpoint_profile)

    labels = {r["container_id"]: r for r in read_csv(INPUTS["labels"])}
    manifest = {r["container_id"]: r for r in read_csv(INPUTS["source_manifest"])}
    path_rows = defaultdict(list)
    for row in read_csv(INPUTS["source_paths"]):
        path_rows[row.get("container_id", "")].append(row)
    metadata = {r["container_id"]: r for r in read_csv(INPUTS["addendum"])}
    measured = {r["container_id"] for r in read_csv(INPUTS["features"]) if r.get("variant") == "primary" and r.get("event_code") == "stad" and r.get("status") == "measured"}
    notes = {r.get("clinical_row_ref", ""): r for r in read_csv(INPUTS["notes"])}

    # Only canonical and eligible sources contribute to support denominators.
    canonical = {cid for cid, row in manifest.items() if (row.get("canonical_container_id") or cid) == cid and row.get("source_status") == "eligible"}
    source_date = {cid: source_record_date(path_rows.get(cid, [])) for cid in canonical}
    links = read_csv(INPUTS["links"])
    eligible_links = [r for r in links if r.get("container_id") in canonical and r.get("link_status") == "exact_name_date" and r.get("source_candidate_ambiguity") == "unique_participant"]
    links_by_source = defaultdict(list)
    links_by_pid_date = defaultdict(list)
    for link in eligible_links:
        links_by_source[link["container_id"]].append(link)
        # Keep all row alternatives private; dedup later at endpoint level.
        row = clinical.get(link.get("clinical_row_ref", ""))
        cdate = unique_date(row.get("raw_clinical_date", "")) if row else None
        if row and cdate:
            links_by_pid_date[(link["participant_id"], cdate)].append((link, row))

    private_identity = []
    for cid in sorted(canonical):
        label = labels.get(cid, {})
        meta = metadata.get(cid, {})
        for link in links_by_source.get(cid, []):
            row = clinical.get(link.get("clinical_row_ref", ""), {})
            private_identity.append({
                "container_id": cid,
                "participant_id": link.get("participant_id", ""),
                "clinical_row_ref": link.get("clinical_row_ref", ""),
                "identity_evidence": "full_pinyin_exact_name+same_calendar_day+unique_participant",
                "link_status": link.get("link_status", ""),
                "date_agreement": link.get("date_agreement", ""),
                "clinical_date": row.get("raw_clinical_date", ""),
                "source_record_time": ";".join(sorted({text(p.get("record_time")) for p in path_rows.get(cid, [])})),
                "source_task": label.get("protocol_task", ""),
                "source_label": label.get("source_cohort_evidence", ""),
                "source_label_expanded": meta.get("source_label_expanded", ""),
                "clinical_CI_history_same_day": meta.get("clinical_CI_history_same_day", ""),
                "note_row_refs": meta.get("note_row_refs", ""),
                "measured_stad": str(cid in measured).lower(),
            })
    write_csv(PRIVATE / "identity_evidence.csv", private_identity)

    endpoint_defs = {ep: endpoint_definition(ep) for ep in endpoint_fields}
    # Source-level endpoint evidence.  A value is unique only if all linked,
    # same-day candidate rows agree; disagreements remain a conflict.
    source_endpoint = {}
    private_endpoint = []
    for cid in sorted(canonical):
        label = labels.get(cid, {})
        meta = metadata.get(cid, {})
        scope = classify_scope(label, meta)
        by_ep = {}
        for endpoint, field in endpoint_fields.items():
            values = []
            refs = []
            for link in links_by_source.get(cid, []):
                row = clinical.get(link.get("clinical_row_ref", ""), {})
                val = number(row.get(field, ""))
                if val is not None:
                    values.append(val)
                    refs.append(link.get("clinical_row_ref", ""))
            unique_values = sorted(set(values))
            status = "unique_literal_numeric" if len(unique_values) == 1 else ("conflicting_literal_numeric" if len(unique_values) > 1 else "missing_literal_numeric")
            by_ep[endpoint] = {"status": status, "value": unique_values[0] if len(unique_values) == 1 else None, "refs": refs}
            private_endpoint.append({"container_id": cid, "participant_id": label.get("unique_same_day_pid", ""), "scope": scope, "endpoint": endpoint, "status": status, "values": "|".join(str(v) for v in unique_values), "clinical_row_refs": "|".join(refs), "version_status": endpoint_defs[endpoint]["version_status"], "unit_status": endpoint_defs[endpoint]["unit_status"], "scoring_status": endpoint_defs[endpoint]["scoring_status"]})
        source_endpoint[cid] = by_ep
    write_csv(PRIVATE / "endpoint_evidence.csv", private_endpoint)

    def source_scope(cid, scope):
        label = labels.get(cid, {})
        meta = metadata.get(cid, {})
        if scope == "all_canonical":
            return True
        if scope == "all_linked_scope":
            return bool(links_by_source.get(cid))
        return label.get("source_cohort_evidence") in {"CI", "CIHA_label"} or meta.get("clinical_CI_history_same_day", "").lower() == "true"

    support_rows = []
    for scope in ("all_canonical", "all_linked_scope", "expanded_CI_scope"):
        scoped = [cid for cid in canonical if source_scope(cid, scope)]
        identity = [cid for cid in scoped if cid in links_by_source]
        timeline = [cid for cid in identity if source_date.get(cid) is not None]
        for endpoint in endpoint_fields:
            numeric_sources = [cid for cid in timeline if source_endpoint[cid][endpoint]["status"] == "unique_literal_numeric"]
            comparable_sources = []  # all four endpoints retain an unresolved registry/version gate
            eeg_sources = [cid for cid in numeric_sources if cid in measured]
            support_rows.append({
                "scope": scope,
                "route": "F1" if endpoint in {"IT_MAIS_or_MAIS", "CAP"} else "F2",
                "endpoint": endpoint,
                "raw_canonical_sources": len(scoped),
                "identity_interpretable_sources": len(identity),
                "registered_clinical_date_and_EEG_date_parseable_sources": len(timeline),
                "literal_numeric_endpoint_sources": len(numeric_sources),
                "confirmed_comparable_endpoint_sources": len(comparable_sources),
                "valid_EEG_sources": len(eeg_sources),
                "literal_numeric_and_valid_EEG_final_intersection": len(eeg_sources),
                "confirmed_comparable_and_valid_EEG_final_intersection": len([cid for cid in comparable_sources if cid in measured]),
                "status": "SUPPORT_INSUFFICIENT" if not comparable_sources else "SUPPORTED_FOR_NEXT_STAGE",
                "gate_caveat": "registered headers/rows establish numeric availability; functional-assessment date role, version, scoring, source units and cross-cohort attribution remain unresolved",
            })
    write_csv(OUT / "support_breakdown.csv", support_rows)

    definitions = []
    for endpoint, definition in endpoint_defs.items():
        counts = [r for r in private_endpoint if r["endpoint"] == endpoint]
        nums = [float(v) for r in counts for v in r["values"].split("|") if v]
        profile = next(item for item in clinical_endpoint_profile if item["endpoint"] == endpoint)
        definitions.append(dict(endpoint=endpoint, **definition, registered_rows_with_unique_literal_numeric_value=profile["rows_with_unique_literal_numeric_value"], registered_identity_groups_with_literal_numeric_value=profile["candidate_identity_groups_with_literal_numeric_value"], registered_identity_groups_with_conflicting_numeric_values=profile["candidate_identity_groups_with_conflicting_numeric_values"], registered_rows_at_declared_source_max=profile["rows_at_declared_source_max"], literal_numeric_source_count=sum(r["status"] == "unique_literal_numeric" for r in counts), literal_numeric_min=min(nums) if nums else None, literal_numeric_max=max(nums) if nums else None, literal_numeric_rows=len(nums), rule="no version split, unit conversion, or cross-instrument merge"))
    write_csv(OUT / "endpoint_definitions.csv", definitions)

    # F3: exactly one puretone and one bapa canonical source on the same
    # identity/day, with a same-day clinical target and measured EEG on both.
    task_by_key = defaultdict(lambda: defaultdict(list))
    for cid in canonical:
        label = labels.get(cid, {})
        pid = label.get("unique_same_day_pid", "")
        day = label.get("candidate_acquisition_day_id", "")
        task = label.get("protocol_task", "")
        if pid and day and task in {"puretone", "bapa"} and cid in links_by_source:
            task_by_key[(pid, day)][task].append(cid)
    f3_rows = []
    for (pid, day), tasks in task_by_key.items():
        if set(tasks) != {"puretone", "bapa"}:
            continue
        pair_unique = len(tasks["puretone"]) == 1 and len(tasks["bapa"]) == 1
        a, b = tasks["puretone"][0], tasks["bapa"][0]
        target_ep = []
        for ep in endpoint_fields:
            pair_values = []
            for source_id in (a, b):
                evidence = source_endpoint[source_id][ep]
                if evidence["status"] == "conflicting_literal_numeric":
                    pair_values = ["conflict"]
                    break
                if evidence["status"] == "unique_literal_numeric":
                    pair_values.append(evidence["value"])
            if pair_values and pair_values != ["conflict"] and len(set(pair_values)) == 1:
                target_ep.append(ep)
        target_comparable = []
        f3_rows.append({"participant_id": pid, "acquisition_day_id": day, "puretone_container_id": a, "bapa_container_id": b, "pair_unique_per_task": str(pair_unique).lower(), "same_day_clinical_target_endpoints": "|".join(sorted(target_ep)), "confirmed_comparable_target_endpoints": "|".join(target_comparable), "puretone_valid_EEG": str(a in measured).lower(), "bapa_valid_EEG": str(b in measured).lower(), "timeline_evidence": "same_calendar_day_source_and_assessment_date" if target_ep else "same_calendar_day_EEG_only_no_target", "eligible_raw_pair": str(pair_unique and bool(target_ep)).lower(), "eligible_comparable_pair": "false"})
    write_csv(PRIVATE / "f3_pair_evidence.csv", f3_rows)
    f3_agg = {"candidate_task_day_pairs": len(f3_rows), "unique_task_day_pairs_with_literal_target": sum(bool(r["same_day_clinical_target_endpoints"]) and r["pair_unique_per_task"] == "true" for r in f3_rows), "pairs_with_confirmed_comparable_target": 0, "pairs_with_valid_EEG_both": sum(r["puretone_valid_EEG"] == "true" and r["bapa_valid_EEG"] == "true" for r in f3_rows), "final_comparable_pair_intersection": 0, "gate": "SUPPORT_INSUFFICIENT"}

    # F4: deduplicated clinical rows with two distinct explicit assessment
    # dates, then separately require exact same-day linked EEG at both dates.
    by_pid = defaultdict(list)
    for assessment in assessments:
        if assessment.get("clinical_date"):
            by_pid[assessment.get("participant_id", "")].append(assessment)
    f4_rows = []
    for pid, rows in by_pid.items():
        by_date = defaultdict(list)
        for row in rows:
            by_date[row["clinical_date"]].append(row)
        dates = sorted(by_date)
        if len(dates) < 2:
            continue
        for endpoint, field in endpoint_fields.items():
            dated_values = {d: sorted({number(r.get(field, "")) for r in by_date[d] if number(r.get(field, "")) is not None}) for d in dates}
            usable = [d for d in dates if len(dated_values[d]) == 1]
            if len(usable) < 2:
                continue
            eeg_dates = []
            for d in usable:
                sources = {link["container_id"] for link, row in links_by_pid_date.get((pid, date.fromisoformat(d)), []) if link.get("container_id") in measured}
                if sources:
                    eeg_dates.append((d, sorted(sources)))
            baseline_eeg = bool(eeg_dates and eeg_dates[0][0] == usable[0])
            later_clinical_target = len(usable) >= 2 and any(d > usable[0] for d in usable[1:])
            baseline_to_later_target = baseline_eeg and later_clinical_target
            private_row = {"participant_id": pid, "endpoint": endpoint, "assessment_dates": "|".join(usable), "baseline_date": usable[0], "followup_date": usable[-1], "n_distinct_assessment_dates": len(usable), "dates_with_valid_EEG": "|".join(d for d, _ in eeg_dates), "baseline_followup_valid_EEG": str(len(eeg_dates) >= 2).lower(), "confirmed_comparable_endpoint": "false", "assessment_row_refs": "|".join(r.get("clinical_row_ref", "") for d in usable for r in by_date[d]), "timeline_evidence": "explicit_clinical_assessment_dates;same_day_EEG_links_only_where_listed"}
            private_row.update({"baseline_EEG_with_later_clinical_target": str(baseline_to_later_target).lower(), "followup_EEG_is_optional_sensitivity": str(len(eeg_dates) >= 2).lower(), "timeline_evidence": "registered_clinical_date_field;functional_assessment_date_role_unresolved;same_day_EEG_links_only_where_listed"})
            f4_rows.append(private_row)
    write_csv(PRIVATE / "f4_followup_evidence.csv", f4_rows)
    f4_agg = {"candidate_id_endpoint_repeat_assessment_series": len(f4_rows), "series_with_baseline_EEG_and_later_clinical_target": sum(r["baseline_EEG_with_later_clinical_target"] == "true" for r in f4_rows), "series_with_two_valid_EEG_visits_sensitivity": sum(r["baseline_followup_valid_EEG"] == "true" for r in f4_rows), "series_with_confirmed_comparable_endpoint": 0, "final_comparable_followup_intersection": 0, "gate": "SUPPORT_INSUFFICIENT", "date_rule": "registered clinical_date field used as a date signal; functional-assessment role is unresolved; EEG filename suffix or file mtime not used"}

    # Public aggregates are intentionally free of participant/container/date
    # identifiers.  Detailed ID evidence remains private above.
    summary = {
        "job_id": os.environ["SLURM_JOB_ID"],
        "status": "COMPLETED",
        "canonical_eligible_sources": len(canonical),
        "registered_clinical_rows": len(clinical_rows),
        "deduplicated_clinical_assessments": len(assessments),
        "candidate_identity_groups": len({r.get("participant_id", "") for r in clinical_rows}),
        "valid_EEG_source_count_primary_stad": len(measured & canonical),
        "identity_evidence_counts": {"exact_name_same_day_unique_links": len(eligible_links), "sources_with_unique_identity_link": len(links_by_source)},
        "endpoint_definitions": definitions,
        "f3": f3_agg,
        "f4": f4_agg,
        "route_gates": {"F1": "SUPPORT_INSUFFICIENT", "F2": "SUPPORT_INSUFFICIENT", "F3": f3_agg["gate"], "F4": f4_agg["gate"]},
        "source_scope_caveats": [
            "literal CI/CIHA source labels and explicit same-day clinical CI history are separate evidence classes; expanded_CI_scope is a sensitivity scope, not a diagnosis",
            "unknown and normal_literal source labels remain unresolved; no global relabeling was performed",
            "candidate identity groups are exact full-pinyin plus same-calendar-day linkage evidence, not clinically adjudicated independent children",
            "numeric score availability is reported separately from confirmed scale comparability",
            "no EEG array values, EEG-outcome associations, clinical prediction fits, or new signal features were computed",
        ],
        "config_sha256": hashes["config"],
        "protocol_sha256": hashes["protocol"],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "completion.json").write_text(json.dumps({"status": "COMPLETED", "job_id": os.environ["SLURM_JOB_ID"], "run": RUN, "private_evidence": str(PRIVATE.relative_to(BASE))}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "COMPLETED", "job_id": os.environ["SLURM_JOB_ID"], "canonical_sources": len(canonical), "clinical_rows": len(clinical_rows), "f3_pairs": f3_agg["candidate_task_day_pairs"], "f4_series": f4_agg["candidate_id_endpoint_repeat_assessment_series"], "gates": summary["route_gates"]}, sort_keys=True))


if __name__ == "__main__":
    main()
