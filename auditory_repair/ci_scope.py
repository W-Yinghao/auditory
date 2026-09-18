#!/usr/bin/env python3
"""Descriptive CI/MFF scope summaries from frozen Phase 3 tables.

This run intentionally consumes record-level feature tables already produced by
the Phase 3 Slurm jobs.  It does not load EEG arrays, fit a clinical model, or
reinterpret source labels as diagnoses.  Public tables contain aggregate
counts and numeric summaries only; identifier-level provenance is private.
"""
import csv
import hashlib
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RUN = "ci_scope_001"
OUT = BASE / "results" / "auditory_repair" / RUN
PRIVATE = BASE / "private" / "results" / "auditory_repair" / RUN

INPUTS = {
    "clinical_rows": BASE / "private/phase3_ci_clinical_004/candidate_rows_index.csv",
    "labels": BASE / "results/phase3_ci_linkage_005/canonical_source_labels.csv",
    "links": BASE / "results/phase3_ci_linkage_005/clinical_source_links.csv",
    "source_manifest": BASE / "results/phase3_ci_sources_001/source_manifest.csv",
    "metadata_addendum": BASE / "results/phase3_metadata_addendum_001/source_metadata.csv",
    "features": BASE / "results/phase3_ci_measurements_001/features.csv",
    "half_scores": BASE / "results/phase3_ci_measurements_001/half_scores.csv",
    "decoder_scores": BASE / "results/phase3_ci_measurements_001/decoder_scores.csv",
    "measurement_summary": BASE / "results/phase3_ci_measurements_001/summary.json",
    "qualification_summary": BASE / "results/auditory_fseries/ci_qualification_001/summary.json",
}

ENDPOINT_FIELDS = {
    "IT_MAIS_or_MAIS": "raw_itmais",
    "MUSS": "raw_muss",
    "CAP": "raw_cap",
    "SIR": "raw_sir",
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


def finite_number(value):
    raw = str(value or "").strip().replace(",", "").replace("%", "")
    if not raw:
        return None
    try:
        number = float(raw)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def fnumber(value):
    return None if value is None else float(value)


def vals(values):
    numeric = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    return numeric


def stats(values):
    numeric = vals(values)
    if not numeric:
        return {"n": 0, "median": None, "q25": None, "q75": None, "min": None, "max": None}
    ordered = numeric
    # Linear interpolation matches numpy's default quantile definition while
    # avoiding an import solely for descriptive arithmetic.
    def quantile(q):
        if len(ordered) == 1:
            return ordered[0]
        pos = (len(ordered) - 1) * q
        lo = int(math.floor(pos)); hi = int(math.ceil(pos))
        if lo == hi:
            return ordered[lo]
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)
    return {"n": len(ordered), "median": quantile(0.5), "q25": quantile(0.25),
            "q75": quantile(0.75), "min": ordered[0], "max": ordered[-1]}


def source_scope(label, metadata):
    if label.get("source_cohort_evidence") in {"CI", "CIHA_label"}:
        return "expanded_CI_scope"
    if str(metadata.get("clinical_CI_history_same_day", "")).lower() == "true":
        return "expanded_CI_scope"
    return "all_canonical_MFF"


def group_label(label):
    value = label.get("source_cohort_evidence", "")
    return value if value else "unknown_or_unlabelled"


def summarize_values(rows, value_key="value"):
    summary = stats([row.get(value_key) for row in rows])
    return summary


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("CI scope summary must run under Slurm")
    os.umask(0o077)
    if OUT.exists() or PRIVATE.exists():
        raise FileExistsError(f"output already exists: {OUT} or {PRIVATE}")
    missing = [str(path) for path in INPUTS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing frozen inputs: " + ", ".join(missing))
    OUT.mkdir(parents=True)
    PRIVATE.mkdir(parents=True, mode=0o700)

    hashes = {name: sha256(path) for name, path in INPUTS.items()}
    (PRIVATE / "input_sha256.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    # The public snapshot is keyed by logical artifact names and contains no
    # private paths, names, dates, participant IDs, or source IDs.
    (OUT / "source_snapshot.json").write_text(json.dumps({
        "run": RUN, "job_id": os.environ["SLURM_JOB_ID"],
        "logical_inputs": hashes,
        "feature_source": "phase3_ci_measurements_001/features.csv and half_scores.csv",
        "scope_rule": "literal CI/CIHA source evidence OR explicit same-day clinical CI history; otherwise all canonical MFF",
    }, indent=2), encoding="utf-8")
    shutil.copy2(Path(__file__), PRIVATE / "ci_scope.py")
    (PRIVATE / "ci_scope.py").chmod(0o600)

    clinical_rows = [row for row in read_csv(INPUTS["clinical_rows"])
                     if row.get("row_status") == "candidate_row"]
    labels = {row["container_id"]: row for row in read_csv(INPUTS["labels"])}
    metadata = {row["container_id"]: row for row in read_csv(INPUTS["metadata_addendum"])}
    manifest = {row["container_id"]: row for row in read_csv(INPUTS["source_manifest"])}
    canonical = {
        cid for cid, row in manifest.items()
        if row.get("source_status") == "eligible"
        and (row.get("canonical_container_id") or cid) == cid
    }
    features = [row for row in read_csv(INPUTS["features"])
                if row.get("container_id") in canonical]
    halves = [row for row in read_csv(INPUTS["half_scores"])
              if row.get("container_id") in canonical]
    decoders = [row for row in read_csv(INPUTS["decoder_scores"])
                if row.get("container_id") in canonical]
    links = [row for row in read_csv(INPUTS["links"])
             if row.get("container_id") in canonical
             and row.get("link_status") == "exact_name_date"
             and row.get("source_candidate_ambiguity") == "unique_participant"]
    links_by_source = defaultdict(list)
    for link in links:
        links_by_source[link.get("container_id", "")].append(link)

    scope_by_source = {}
    label_by_source = {}
    for cid in canonical:
        label = labels.get(cid, {})
        label_by_source[cid] = group_label(label)
        scope_by_source[cid] = source_scope(label, metadata.get(cid, {}))

    # Keep linked source-level endpoint values private until aggregation.  A
    # source is unique only when every accepted linked row has one same value.
    clinical_by_ref = {}
    for row in clinical_rows:
        material = "|".join(row.get(key, "") for key in
                             ("participant_id", "source_sheet_index", "source_worksheet_row"))
        ref = "R" + hashlib.sha256(material.encode()).hexdigest()[:12]
        clinical_by_ref[ref] = row
    endpoint_by_source = {}
    private_endpoint = []
    for cid in sorted(canonical):
        endpoint_by_source[cid] = {}
        for endpoint, field in ENDPOINT_FIELDS.items():
            numbers = []
            refs = []
            for link in links_by_source.get(cid, []):
                row = clinical_by_ref.get(link.get("clinical_row_ref", ""), {})
                value = finite_number(row.get(field, ""))
                if value is not None:
                    numbers.append(value)
                    refs.append(link.get("clinical_row_ref", ""))
            unique = sorted(set(numbers))
            status = ("unique_literal_numeric" if len(unique) == 1 else
                      "conflicting_literal_numeric" if len(unique) > 1 else
                      "missing_literal_numeric")
            endpoint_by_source[cid][endpoint] = {
                "status": status, "value": unique[0] if len(unique) == 1 else None,
                "values": unique,
            }
            private_endpoint.append({
                "container_id": cid, "scope": scope_by_source[cid],
                "source_label": label_by_source[cid], "endpoint": endpoint,
                "status": status, "values": "|".join(str(v) for v in unique),
                "clinical_row_refs": "|".join(refs),
            })
    write_csv(PRIVATE / "endpoint_source_evidence.csv", private_endpoint)

    # Endpoint availability and exact literal-value distributions are source
    # aggregates.  Values are intentionally left in registered original units.
    endpoint_rows = []
    value_rows = []
    for scope in ("expanded_CI_scope", "all_canonical_MFF"):
        scoped = [cid for cid in canonical if scope_by_source[cid] == scope or scope == "all_canonical_MFF"]
        for endpoint in ENDPOINT_FIELDS:
            evidence = [endpoint_by_source[cid][endpoint] for cid in scoped]
            unique = [row["value"] for row in evidence if row["status"] == "unique_literal_numeric"]
            measured = sum(
                any(f.get("variant") == "primary" and f.get("event_code") == "stad"
                    and f.get("status") == "measured" and f.get("container_id") == cid
                    for f in features)
                for cid in scoped if endpoint_by_source[cid][endpoint]["status"] == "unique_literal_numeric"
            )
            counts = Counter(unique)
            endpoint_rows.append({
                "scope": scope, "endpoint": endpoint, "canonical_sources": len(scoped),
                "linked_sources": sum(bool(links_by_source.get(cid)) for cid in scoped),
                "unique_numeric_sources": len(unique),
                "conflicting_sources": sum(row["status"] == "conflicting_literal_numeric" for row in evidence),
                "unique_numeric_with_primary_stad_feature": measured,
                "literal_min": min(unique) if unique else None,
                "literal_max": max(unique) if unique else None,
                "unit_status": "percent_header_values_literal_0_to_40_unresolved" if endpoint in {"IT_MAIS_or_MAIS", "MUSS"} else "ordinal_or_named_unit_row_assignment_unresolved",
                "time_version_status": "functional_date_role_and_scale_version_unresolved",
            })
            for value, count in sorted(counts.items()):
                value_rows.append({"scope": scope, "endpoint": endpoint,
                                   "literal_value": value, "unique_numeric_sources": count})
    write_csv(OUT / "endpoint_scope_summary.csv", endpoint_rows)
    write_csv(OUT / "endpoint_literal_value_distribution.csv", value_rows)

    def rows_for_scope(rows, scope):
        return [row for row in rows if scope == "all_canonical_MFF"
                or scope_by_source.get(row.get("container_id", "")) == scope]

    feature_rows = []
    for scope in ("expanded_CI_scope", "all_canonical_MFF"):
        scoped = rows_for_scope(features, scope)
        by_group = defaultdict(list)
        for row in scoped:
            by_group[(label_by_source.get(row["container_id"], "unknown_or_unlabelled"),
                      row.get("variant", ""), row.get("event_code", ""))].append(row)
        for (source_label, variant, event_code), group in sorted(by_group.items()):
            measured_rows = [row for row in group if row.get("status") == "measured"]
            n_trials = stats([finite_number(row.get("n_trials")) for row in measured_rows])
            main = stats([finite_number(row.get("main_mean_uv")) for row in measured_rows])
            late = stats([finite_number(row.get("late_mean_uv")) for row in measured_rows])
            feature_rows.append({
                "scope": scope, "source_cohort_evidence": source_label,
                "variant": variant, "event_code": event_code,
                "records": len(group), "measured_records": len(measured_rows),
                "n_trials_median": n_trials["median"], "n_trials_q25": n_trials["q25"],
                "n_trials_q75": n_trials["q75"],
                "main_mean_uv_median": main["median"], "main_mean_uv_q25": main["q25"],
                "main_mean_uv_q75": main["q75"],
                "late_mean_uv_median": late["median"], "late_mean_uv_q25": late["q25"],
                "late_mean_uv_q75": late["q75"],
            })
    write_csv(OUT / "record_feature_summary.csv", feature_rows)

    reliability_rows = []
    for scope in ("expanded_CI_scope", "all_canonical_MFF"):
        scoped = rows_for_scope(halves, scope)
        groups = defaultdict(list)
        for row in scoped:
            groups[(label_by_source.get(row["container_id"], "unknown_or_unlabelled"),
                    row.get("variant", ""), row.get("event_code", ""), row.get("split", ""))].append(row)
        for (source_label, variant, event_code, split), group in sorted(groups.items()):
            measured_rows = [row for row in group if row.get("status") == "measured"]
            rel = stats([finite_number(row.get("waveform_r")) for row in measured_rows])
            rmse = stats([finite_number(row.get("waveform_rmse_uv")) for row in measured_rows])
            half_delta = stats([finite_number(row.get("half_b_mean_uv")) - finite_number(row.get("half_a_mean_uv"))
                                for row in measured_rows
                                if finite_number(row.get("half_b_mean_uv")) is not None
                                and finite_number(row.get("half_a_mean_uv")) is not None])
            reliability_rows.append({
                "scope": scope, "source_cohort_evidence": source_label,
                "variant": variant, "event_code": event_code, "split": split,
                "records": len(group), "measured_records": len(measured_rows),
                "waveform_r_median": rel["median"], "waveform_r_q25": rel["q25"],
                "waveform_r_q75": rel["q75"], "waveform_rmse_uv_median": rmse["median"],
                "waveform_rmse_uv_q25": rmse["q25"], "waveform_rmse_uv_q75": rmse["q75"],
                "half_b_minus_a_uv_median": half_delta["median"],
                "half_b_minus_a_uv_q25": half_delta["q25"],
                "half_b_minus_a_uv_q75": half_delta["q75"],
            })
    write_csv(OUT / "within_record_reliability_summary.csv", reliability_rows)

    # Paired event and variant contrasts use only records for which both sides
    # are measured.  They are descriptive record-level contrasts, not child-
    # level effects or inferential tests.
    by_feature = {}
    for row in features:
        if row.get("status") == "measured":
            by_feature[(row["container_id"], row.get("variant", ""), row.get("event_code", ""))] = row
    pair_rows = []
    for scope in ("expanded_CI_scope", "all_canonical_MFF"):
        scoped_ids = [cid for cid in canonical if scope == "all_canonical_MFF" or scope_by_source[cid] == scope]
        for variant in ("primary", "strict"):
            for field, label in (("main_mean_uv", "devt_minus_stad_main_uv"),
                                 ("late_mean_uv", "devt_minus_stad_late_uv")):
                pairs = []
                for cid in scoped_ids:
                    devt = by_feature.get((cid, variant, "devt"))
                    stad = by_feature.get((cid, variant, "stad"))
                    if devt and stad:
                        devt_value = finite_number(devt.get(field))
                        stad_value = finite_number(stad.get(field))
                        if devt_value is not None and stad_value is not None:
                            pairs.append(devt_value - stad_value)
                result = stats(pairs)
                pair_rows.append({"scope": scope, "contrast": label, "variant": variant,
                                  "n_pairs": result["n"], "median_uv": result["median"],
                                  "q25_uv": result["q25"], "q75_uv": result["q75"],
                                  "min_uv": result["min"], "max_uv": result["max"],
                                  "positive_pairs": sum(v > 0 for v in pairs),
                                  "negative_pairs": sum(v < 0 for v in pairs),
                                  "zero_pairs": sum(v == 0 for v in pairs)})
        for event_code in ("devt", "stad"):
            for field, label in (("main_mean_uv", "strict_minus_primary_main_uv"),
                                 ("late_mean_uv", "strict_minus_primary_late_uv")):
                pairs = []
                for cid in scoped_ids:
                    primary = by_feature.get((cid, "primary", event_code))
                    strict = by_feature.get((cid, "strict", event_code))
                    if primary and strict:
                        strict_value = finite_number(strict.get(field))
                        primary_value = finite_number(primary.get(field))
                        if strict_value is not None and primary_value is not None:
                            pairs.append(strict_value - primary_value)
                result = stats(pairs)
                pair_rows.append({"scope": scope, "contrast": label, "event_code": event_code,
                                  "variant": "primary_vs_strict", "n_pairs": result["n"],
                                  "median_uv": result["median"], "q25_uv": result["q25"],
                                  "q75_uv": result["q75"], "min_uv": result["min"],
                                  "max_uv": result["max"], "positive_pairs": sum(v > 0 for v in pairs),
                                  "negative_pairs": sum(v < 0 for v in pairs),
                                  "zero_pairs": sum(v == 0 for v in pairs)})
    write_csv(OUT / "paired_within_record_summary.csv", pair_rows)

    # Source-label composition and feasibility are aggregate only.  Numeric
    # availability is not treated as a valid clinical outcome definition.
    composition = []
    for scope in ("expanded_CI_scope", "all_canonical_MFF"):
        ids = [cid for cid in canonical if scope == "all_canonical_MFF" or scope_by_source[cid] == scope]
        counts = Counter(label_by_source[cid] for cid in ids)
        for source_label, count in sorted(counts.items()):
            composition.append({"scope": scope, "source_cohort_evidence": source_label,
                                "canonical_records": count})
    write_csv(OUT / "source_scope_composition.csv", composition)

    feasibility = {
        "scope": "all_canonical_MFF",
        "record_count": len(canonical),
        "numeric_endpoint_source_counts": {
            row["endpoint"]: row["unique_numeric_sources"]
            for row in endpoint_rows if row["scope"] == "all_canonical_MFF"
        },
        "measured_numeric_source_counts": {
            row["endpoint"]: row["unique_numeric_with_primary_stad_feature"]
            for row in endpoint_rows if row["scope"] == "all_canonical_MFF"
        },
        "technical_record_level_regression_possible": True,
        "scientific_regression_status": "EXPLORATORY_ONLY_NOT_CLINICALLY_QUALIFIED",
        "barriers": [
            "IT_MAIS_or_MAIS and MUSS carry percent headers but literal values are 0-40; no unit conversion is applied",
            "endpoint version, functional assessment date role, and row-to-source temporal alignment remain unresolved",
            "source labels are mixed (CI, CIHA, HA, NH, unknown, normal_literal); unknown remains unknown",
            "linked numeric support is source-record level and identity links are not adjudicated independent children",
        ],
        "permitted_next_use": "descriptive record-level summaries retaining original literal units and source-cohort strata",
        "disallowed_interpretation": "pooled CI clinical validity, confirmed device-state effect, or child-level generalization",
    }
    (OUT / "mixed_mff_regression_feasibility.json").write_text(json.dumps(feasibility, indent=2), encoding="utf-8")

    measurement_summary = json.loads(INPUTS["measurement_summary"].read_text(encoding="utf-8"))
    qualification_summary = json.loads(INPUTS["qualification_summary"].read_text(encoding="utf-8"))
    summary = {
        "status": "COMPLETED_DESCRIPTIVE_SCOPE_ONLY",
        "job_id": os.environ["SLURM_JOB_ID"],
        "canonical_records": len(canonical),
        "expanded_CI_scope_records": sum(scope_by_source[cid] == "expanded_CI_scope" for cid in canonical),
        "all_mixed_MFF_records": len(canonical),
        "existing_feature_rows": len(features),
        "existing_half_score_rows": len(halves),
        "existing_decoder_score_rows": len(decoders),
        "measurement_source_job_id": measurement_summary.get("job_id"),
        "qualification_source_job_id": qualification_summary.get("job_id"),
        "clinical_regression_fit": False,
        "new_raw_eeg_features": False,
        "new_eeg_array_reads": False,
        "scope_labels_are_diagnostic": False,
        "source_outputs": [
            "endpoint_scope_summary.csv",
            "endpoint_literal_value_distribution.csv",
            "record_feature_summary.csv",
            "within_record_reliability_summary.csv",
            "paired_within_record_summary.csv",
            "source_scope_composition.csv",
            "mixed_mff_regression_feasibility.json",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "completion.json").write_text(json.dumps({
        "status": "COMPLETED", "job_id": os.environ["SLURM_JOB_ID"], "run": RUN,
        "private_evidence": "private/results/auditory_repair/ci_scope_001",
    }, indent=2), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
