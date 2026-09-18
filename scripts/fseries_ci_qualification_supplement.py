#!/usr/bin/env python3
"""Aggregate-only supplement for the completed F-series qualification.

Reads the existing private qualification evidence and writes only safe counts;
it does not alter ci_qualification_001 or read EEG arrays.
"""
import csv
import json
import os
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PRIVATE = BASE / "private/auditory_fseries/ci_qualification_001"
OUT = BASE / "results/auditory_fseries/ci_qualification_001"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_number(value):
    raw = str(value or "").strip().replace(",", "").replace("%", "")
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("supplement must run under Slurm")
    f4 = read_csv(PRIVATE / "f4_followup_evidence.csv")
    clinical = {"R" + __import__("hashlib").sha256((r.get("participant_id", "") + "|" + r.get("source_sheet_index", "") + "|" + r.get("source_worksheet_row", "")).encode()).hexdigest()[:12]: r for r in read_csv(BASE / "private/phase3_ci_clinical_004/candidate_rows_index.csv") if r.get("row_status") == "candidate_row"}
    fields = {"IT_MAIS_or_MAIS": "raw_itmais", "MUSS": "raw_muss", "CAP": "raw_cap", "SIR": "raw_sir"}
    states = []
    for row in f4:
        refs = [ref for ref in row.get("assessment_row_refs", "").split("|") if ref]
        values_by_date = defaultdict(set)
        field = fields[row["endpoint"]]
        for ref in refs:
            source = clinical.get(ref)
            if not source:
                continue
            value = as_number(source.get(field, ""))
            if value is not None:
                values_by_date[source.get("raw_clinical_date", "")].add(value)
        ordered = [values_by_date[d] for d in sorted(values_by_date)]
        if len(ordered) < 2:
            state = "insufficient_unique_values"
        elif any(len(values) > 1 for values in ordered):
            state = "within_date_conflict"
        elif len({next(iter(values)) for values in ordered}) == 1:
            state = "same_literal_value_across_dates"
        else:
            state = "changed_literal_value_across_dates"
        states.append((row.get("participant_id", ""), state))
    by_pid = defaultdict(set)
    for pid, state in states:
        by_pid[pid].add(state)
    result = {
        "status": "COMPLETED",
        "job_id": os.environ["SLURM_JOB_ID"],
        "source_run": "ci_qualification_001",
        "f4_identity_endpoint_series": len(states),
        "f4_unique_candidate_identity_groups": len(by_pid),
        "f4_series_state_counts": {state: sum(item == state for _, item in states) for state in sorted({item for _, item in states})},
        "f4_identity_groups_with_state_counts": {state: sum(state in values for values in by_pid.values()) for state in sorted({item for _, item in states})},
        "interpretation": "Literal score equality/change is descriptive only; endpoint version, unit, functional-assessment date role and clinical comparability remain unresolved.",
    }
    (OUT / "f4_aggregate_supplement.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    definitions = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))["endpoint_definitions"]
    supplement = []
    for item in definitions:
        supplement.append({
            "endpoint": item["endpoint"],
            "registered_rows_at_literal_value_40_or_document_max": item["registered_rows_at_declared_source_max"],
            "interpretation": "descriptive literal-value count; not a confirmed ceiling or normalized score",
        })
    (OUT / "endpoint_literal_max_supplement.json").write_text(json.dumps(supplement, indent=2), encoding="utf-8")
    print(json.dumps({"status": "COMPLETED", "job_id": os.environ["SLURM_JOB_ID"], "f4_series": len(states), "f4_identity_groups": len(by_pid)}, sort_keys=True))


if __name__ == "__main__":
    main()
