#!/usr/bin/env python3
"""Bounded, evidence-preserving clinical-to-CI-source candidate linkage.

This script is deliberately a linkage audit, not an identity adjudicator.  A
clinical Han name is converted to one normalized full pinyin token and is
matched only to an identical normalized source token.  Initials and unmatched
source clues are retained as private diagnostic evidence and never become
confirmed children or diagnoses.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from statistics import median

BASE = Path(__file__).resolve().parents[1]
DEPS = BASE / ".deps_phase3"
if DEPS.exists():
    import sys
    sys.path.insert(0, str(DEPS))
from pypinyin import lazy_pinyin

CLINICAL = BASE / "private/phase3_ci_clinical_004/candidate_rows_index.csv"
SOURCE_MANIFEST = BASE / "results/phase3_ci_sources_001/source_manifest.csv"
SOURCE_PATHS = BASE / "private/phase3_ci_sources_001/source_paths_and_tokens.csv"
VENDOR = BASE / "private/linkage_001/vendor_identity_records.json"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as h:
        return list(csv.DictReader(h))


def write_table(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = sorted({k for r in rows for k in r}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text(value):
    return "" if value is None else str(value).strip()


def norm_text(value):
    return re.sub(r"[^a-z0-9]+", "", text(value).lower())


def name_key(value):
    raw = re.sub(r"\s+", "", text(value))
    m = re.match(r"^[\u4e00-\u9fff]+", raw)
    return m.group(0) if m else ""


def pinyin_parts(value):
    key = name_key(value)
    return key, [norm_text(p) for p in lazy_pinyin(key)] if key else []


def pinyin_token(value):
    key, parts = pinyin_parts(value)
    return "".join(parts), key, "".join(p[0] for p in parts if p)


def parse_date(value):
    raw = text(value).replace("Z", "+00:00")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d.%m.%Y", "%d.%m.%y", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    m = re.search(r"(?<!\d)(20\d{2})[-/.]?(\d{1,2})[-/.]?(\d{1,2})(?!\d)", raw)
    if m:
        try:
            return datetime(int(m[1]), int(m[2]), int(m[3])).date()
        except ValueError:
            return None
    return None


def source_tokens(row):
    """Return literal alphanumeric path/subject tokens, excluding task labels."""
    stop = {
        "ci", "ciha", "ha", "nh", "puretone", "pure", "tone", "bapa",
        "ba", "ba1ba4", "ba1", "ba2", "ba3", "ba4", "naked", "quiet",
        "noise", "front", "left", "right", "raw", "mff", "egi",
    }
    values = [row.get("identity_clue", ""), row.get("subject", "")]
    values += re.split(r"[/\\_\- .()\[\]]+", row.get("path", ""))
    out = set()
    for value in values:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9]*", text(value).lower()):
            token = norm_text(token)
            if (len(token) >= 2 and token not in stop and
                    not re.fullmatch(r"\d+", token) and
                    not re.fullmatch(r"20\d{2}\d{2}\d{2}", token)):
                out.add(token)
    return sorted(out)


def sheet_label(value):
    """Literal workbook label evidence only; this is not a diagnosis."""
    tokens = set(re.findall(r"[a-z0-9]+", text(value).lower()))
    if "ciha" in tokens:
        return "CIHA_label"
    hits = sorted(tokens.intersection({"ci", "nh", "ha"}))
    return hits[0].upper() if len(hits) == 1 else ("ambiguous" if hits else "unknown")


def source_cohort_label(path_rows):
    """Literal directory/subject label evidence, kept separate from diagnosis."""
    tokens = set()
    for row in path_rows:
        tokens.update(re.findall(r"[a-z0-9]+", (text(row.get("path")) + " " + text(row.get("subject"))).lower()))
    if "ciha" in tokens:
        return "CIHA_label"
    hits = sorted(tokens.intersection({"ci", "nh", "ha"}))
    return hits[0].upper() if len(hits) == 1 else ("ambiguous" if hits else "unknown")


def task_literal(protocol, source_row):
    value = (text(protocol) + " " + text(source_row.get("subject")) + " " +
             text(source_row.get("path"))).lower()
    if "puretone" in value:
        return "puretone"
    if "bapa" in value:
        return "bapa"
    if re.search(r"ba[1-4]ba[1-4]", value):
        return "tone"
    return "unknown"


def date_evidence(clinical_date, source_date):
    if clinical_date and source_date:
        return "same_calendar_day" if clinical_date == source_date else "calendar_day_mismatch"
    return "date_unavailable"


def numeric(value):
    raw = text(value).replace(",", "").replace("%", "")
    if not raw:
        return None
    try:
        n = float(raw)
        return n if math.isfinite(n) else None
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="phase3_ci_linkage_001")
    args = ap.parse_args()
    assert os.environ.get("SLURM_JOB_ID"), "linkage must run under Slurm"
    os.umask(0o077)
    out = BASE / "results" / args.run
    private = BASE / "private" / args.run
    out.mkdir(exist_ok=False)
    private.mkdir(mode=0o700, exist_ok=False)

    clinical_rows = [r for r in read_csv(CLINICAL) if r.get("row_status") == "candidate_row"]
    source_manifest = read_csv(SOURCE_MANIFEST)
    source_paths = read_csv(SOURCE_PATHS)
    manifest = {r["container_id"]: r for r in source_manifest}
    paths_by_id = defaultdict(list)
    for r in source_paths:
        paths_by_id[r["container_id"]].append(r)

    # Only canonical rows enter availability. Duplicate exports remain private
    # diagnostics and cannot inflate candidate or task-pair counts.
    canonical_sources = []
    for r in source_manifest:
        cid = r.get("container_id", "")
        canonical = r.get("canonical_container_id") or cid
        if cid == canonical:
            canonical_sources.append(r)

    source_private = []
    source_info = {}
    for source in canonical_sources:
        cid = source["container_id"]
        path_rows = paths_by_id.get(cid, [])
        # There should normally be one row; retain all private export rows.
        path_row = path_rows[0] if path_rows else {}
        tokens = sorted({t for p in path_rows for t in source_tokens(p)})
        source_date = parse_date(path_row.get("record_time", ""))
        info = dict(source=source, paths=path_rows, tokens=tokens,
                    source_date=source_date, protocol_task=task_literal(source.get("protocol_clue", ""), path_row),
                    source_cohort=source_cohort_label(path_rows))
        source_info[cid] = info
        for p in path_rows or [{}]:
            source_private.append(dict(
                container_id=cid, canonical_container_id=source.get("canonical_container_id") or cid,
                identity_clue=p.get("identity_clue", ""), subject=p.get("subject", ""),
                path=p.get("path", ""), record_time=p.get("record_time", ""),
                source_tokens="|".join(tokens), protocol_task=info["protocol_task"],
                source_cohort_evidence=info["source_cohort"],
                source_status=source.get("source_status", "")))
    write_table(private / "source_token_map.csv", source_private)

    # Clinical rows are deduplicated by opaque participant for coverage while
    # row-level alternatives and source-sheet evidence are retained privately.
    clinical_info = {}
    clinical_private = []
    for row in clinical_rows:
        pid = row.get("participant_id", "")
        if not pid:
            continue
        ptoken, han_key, initials = pinyin_token(row.get("raw_name", ""))
        info = clinical_info.setdefault(pid, dict(
            participant_id=pid, pinyin_token=ptoken, initials=initials,
            source_labels=set(), rows=[]))
        info["source_labels"].add(sheet_label(row.get("source_sheet_title", "")))
        info["rows"].append(row)
        clinical_private.append(dict(
            participant_id=pid, source_sheet_title=row.get("source_sheet_title", ""),
            source_worksheet_row=row.get("source_worksheet_row", ""), raw_name=row.get("raw_name", ""),
            raw_clinical_date=row.get("raw_clinical_date", ""), raw_dob=row.get("raw_dob", ""),
            pinyin_token=ptoken, pinyin_name_key=han_key, initials=initials,
            clinical_date_parseable=bool(parse_date(row.get("raw_clinical_date", ""))),
            clinical_row_ref="R" + hashlib.sha256((pid + "|" + row.get("source_sheet_index", "") + "|" + row.get("source_worksheet_row", "")).encode()).hexdigest()[:12],
            raw_muss=row.get("raw_muss", ""), raw_patient_no=row.get("raw_patient_no", "")))
    write_table(private / "clinical_link_inputs.csv", clinical_private)

    # Compare every candidate to source tokens. Exact full pinyin is the only
    # evidence eligible for a candidate link. Initials are diagnostic only.
    private_links = []
    public_links = []
    diagnostics = 0
    for pid, ci in clinical_info.items():
        ptoken = ci["pinyin_token"]
        initials = ci["initials"]
        for crow in ci["rows"]:
            clinical_date = parse_date(crow.get("raw_clinical_date", ""))
            row_ref = "R" + hashlib.sha256((pid + "|" + crow.get("source_sheet_index", "") + "|" + crow.get("source_worksheet_row", "")).encode()).hexdigest()[:12]
            cohort = sheet_label(crow.get("source_sheet_title", ""))
            for cid, si in source_info.items():
                sm = si["source"]
                matches = bool(ptoken and ptoken in si["tokens"])
                initial_match = bool(initials and len(initials) >= 2 and initials in si["tokens"])
                if matches:
                    de = date_evidence(clinical_date, si["source_date"])
                    if de == "same_calendar_day":
                        status = "exact_name_date"
                    elif de == "calendar_day_mismatch":
                        status = "exact_name_date_mismatch"
                    else:
                        status = "exact_name_only_date_unavailable"
                    accepted = status in {"exact_name_date", "exact_name_only_date_unavailable"}
                    rec = dict(participant_id=pid, clinical_row_ref=row_ref, container_id=cid,
                               canonical_container_id=sm.get("canonical_container_id") or cid,
                               source_status=sm.get("source_status", ""),
                               source_cohort_evidence=si["source_cohort"], protocol_task=si["protocol_task"],
                               clinical_cohort_evidence=cohort, cohort_evidence=cohort,
                               link_status=status, date_agreement=de,
                               accepted_name_link=str(bool(accepted)).lower(),
                               diagnostic_only="false")
                    public_links.append(rec)
                    private_links.append(dict(rec, clinical_name=crow.get("raw_name", ""),
                        clinical_date=crow.get("raw_clinical_date", ""),
                        source_subject=si["paths"][0].get("subject", "") if si["paths"] else "",
                        source_path=si["paths"][0].get("path", "") if si["paths"] else "",
                        source_record_time=si["paths"][0].get("record_time", "") if si["paths"] else "",
                        pinyin_token=ptoken, source_tokens="|".join(si["tokens"])))
                elif initial_match:
                    diagnostics += 1
                    private_links.append(dict(
                        participant_id=pid, clinical_row_ref=row_ref, container_id=cid,
                        canonical_container_id=sm.get("canonical_container_id") or cid,
                        source_status=sm.get("source_status", ""), source_cohort_evidence=si["source_cohort"],
                        protocol_task=si["protocol_task"], clinical_cohort_evidence=cohort,
                        cohort_evidence=cohort,
                        link_status="diagnostic_only_initials", date_agreement="not_used",
                        accepted_name_link="false", diagnostic_only="true",
                        clinical_name=crow.get("raw_name", ""), clinical_date=crow.get("raw_clinical_date", ""),
                        source_subject=si["paths"][0].get("subject", "") if si["paths"] else "",
                        source_path=si["paths"][0].get("path", "") if si["paths"] else "",
                        source_record_time=si["paths"][0].get("record_time", "") if si["paths"] else "",
                        pinyin_token=ptoken, source_tokens="|".join(si["tokens"])))
    # Preserve source clues which had no exact full-pinyin clinical match as a
    # diagnostic record, without manufacturing a participant assignment.
    matched_source_ids = {r["container_id"] for r in public_links}
    for cid, si in source_info.items():
        if cid not in matched_source_ids:
            sm = si["source"]
            private_links.append(dict(
                participant_id="", container_id=cid,
                canonical_container_id=sm.get("canonical_container_id") or cid,
                source_status=sm.get("source_status", ""), source_cohort_evidence=si["source_cohort"],
                protocol_task=si["protocol_task"], clinical_cohort_evidence="", cohort_evidence="",
                link_status="diagnostic_only_unmatched_source_token", date_agreement="not_used",
                accepted_name_link="false", diagnostic_only="true", clinical_name="",
                clinical_date="", source_subject=si["paths"][0].get("subject", "") if si["paths"] else "",
                source_path=si["paths"][0].get("path", "") if si["paths"] else "",
                source_record_time=si["paths"][0].get("record_time", "") if si["paths"] else "",
                pinyin_token="", source_tokens="|".join(si["tokens"])))
    write_table(private / "linkage_candidates.csv", private_links)
    source_pids = defaultdict(set)
    for row in public_links:
        source_pids[row["container_id"]].add(row["participant_id"])
    for row in public_links:
        n = len(source_pids[row["container_id"]])
        row["source_candidate_ambiguity"] = ("unique_participant" if n == 1
                                              else "ambiguous_multiple_participants")
    source_same_day_pids = defaultdict(set)
    for row in public_links:
        if row["link_status"] == "exact_name_date":
            source_same_day_pids[row["container_id"]].add(row["participant_id"])
    write_table(out / "clinical_source_links.csv", public_links,
                fields=["participant_id", "container_id", "canonical_container_id", "source_status",
                        "source_cohort_evidence", "protocol_task", "clinical_cohort_evidence",
                        "cohort_evidence", "clinical_row_ref", "link_status", "date_agreement", "accepted_name_link",
                        "source_candidate_ambiguity", "diagnostic_only"])

    # One public row per canonical source keeps duplicate exports from inflating
    # coverage. Dates are never written here; the day ID is opaque and only
    # emitted when there is exactly one same-day candidate.
    source_label_rows = []
    for cid, si in source_info.items():
        exact_pids = source_pids.get(cid, set())
        same_pids = source_same_day_pids.get(cid, set())
        if not exact_pids:
            ambiguity = "no_exact_name_candidate"
        elif len(exact_pids) == 1:
            ambiguity = "unique_participant"
        else:
            ambiguity = "ambiguous_multiple_participants"
        unique_same = next(iter(same_pids)) if len(same_pids) == 1 else ""
        day_id = ""
        if unique_same and si["source_date"]:
            day_id = "D" + hashlib.sha256((unique_same + "|" + si["source_date"].isoformat()).encode()).hexdigest()[:12]
        source_label_rows.append(dict(
            container_id=cid, protocol_task=si["protocol_task"],
            source_cohort_evidence=si["source_cohort"], configuration_literal=si["source_cohort"],
            source_candidate_ambiguity=ambiguity, n_exactname_candidates=len(exact_pids),
            n_same_day_candidates=len(same_pids), unique_same_day_pid=unique_same,
            candidate_acquisition_day_id=day_id))
    write_table(out / "canonical_source_labels.csv", source_label_rows,
                fields=["container_id", "protocol_task", "source_cohort_evidence",
                        "configuration_literal", "source_candidate_ambiguity",
                        "n_exactname_candidates", "n_same_day_candidates",
                        "unique_same_day_pid", "candidate_acquisition_day_id"])

    # Public availability uses one canonical source per container and only
    # exact-name evidence; source technical eligibility remains explicit.
    available = [r for r in public_links if r["accepted_name_link"] == "true" and r["source_status"] == "eligible"]
    # Pairability requires same acquisition calendar day and a known literal task;
    # unknown protocol rows are retained above but cannot form a task pair.
    pairable_before_ambiguity_gate = [r for r in available if r["link_status"] == "exact_name_date" and r["protocol_task"] in {"puretone", "bapa", "tone"}]
    pairable = [r for r in pairable_before_ambiguity_gate
                if r["source_candidate_ambiguity"] == "unique_participant"]
    participant_any = {r["participant_id"] for r in available}
    # Never pool two visits for one participant: task sets are keyed by the
    # opaque participant and parsed source acquisition calendar day.
    day_task = defaultdict(set)
    day_config = defaultdict(set)
    for r in pairable:
        source_date = source_info[r["container_id"]]["source_date"]
        if source_date is None:
            continue
        key = (r["participant_id"], source_date)
        day_task[key].add(r["protocol_task"])
        day_config[(key[0],key[1],r["protocol_task"])].add(r["source_cohort_evidence"])
    pair_counts = Counter()
    for tasks in day_task.values():
        for pair in combinations(sorted(tasks), 2):
            pair_counts["+".join(pair)] += 1
    pair_participants = {pid for pid, tasks_day in ((key[0], tasks) for key, tasks in day_task.items()) if len(tasks_day) >= 2}
    config_pairs = Counter()
    for key, labels in day_config.items():
        if {"CI", "CIHA_label"}.issubset(labels):
            config_pairs["CI+CIHA_label"] += 1
    muss_values = [numeric(r.get("raw_muss", "")) for r in clinical_rows]
    muss_values = [x for x in muss_values if x is not None]
    vendor_overlap_pids = {r["participant_id"] for r in clinical_rows if int(r.get("vendor_name_overlap_count") or 0) > 0}
    status_counts = Counter(r["link_status"] for r in public_links)
    summary = {
        "job_id": os.environ["SLURM_JOB_ID"],
        "clinical_candidate_rows": len(clinical_rows),
        "clinical_distinct_candidates": len(clinical_info),
        "source_manifest_rows": len(source_manifest),
        "canonical_source_rows": len(canonical_sources),
        "source_status_counts_canonical": dict(Counter(r.get("source_status", "") for r in canonical_sources)),
        "link_status_counts": dict(status_counts),
        "exact_name_date_links": status_counts.get("exact_name_date", 0),
        "exact_name_date_mismatch_links": status_counts.get("exact_name_date_mismatch", 0),
        "diagnostic_only_initial_links_private": diagnostics,
        "accepted_name_links": len([r for r in public_links if r["accepted_name_link"] == "true"]),
        "accepted_clinical_row_source_links": len([r for r in public_links if r["accepted_name_link"] == "true"]),
        "accepted_unique_participant_source_pairs": len({(r["participant_id"], r["container_id"]) for r in public_links if r["accepted_name_link"] == "true"}),
        "eligible_canonical_name_links": len(available),
        "participants_with_eligible_source": len(participant_any),
        "same_day_known_task_links_before_ambiguity_gate": len(pairable_before_ambiguity_gate),
        "same_day_known_task_links_after_ambiguity_gate": len(pairable),
        "participant_known_task_pair_availability": dict(sorted(pair_counts.items())),
        "participants_with_same_day_known_task_pair": len(pair_participants),
        "same_day_acquisition_groups_by_task_count": dict(Counter(len(v) for v in day_task.values())),
        "participants_with_any_same_day_known_task": len({key[0] for key in day_task}),
        "same_day_configuration_label_pairs_known_protocol": dict(config_pairs),
        "canonical_sources_with_exact_name_candidate": len(source_pids),
        "canonical_sources_unique_participant": sum(len(v) == 1 for v in source_pids.values()),
        "canonical_sources_ambiguous_multiple_participants": sum(len(v) > 1 for v in source_pids.values()),
        "participants_with_multiple_clinical_rows": sum(len(ci["rows"]) > 1 for ci in clinical_info.values()),
        "clinical_sheet_label_evidence_counts": dict(Counter(label for ci in clinical_info.values() for label in ci["source_labels"])),
        "source_cohort_literal_label_counts_canonical": dict(Counter(si["source_cohort"] for si in source_info.values())),
        "source_cohort_literal_label_counts_linked": dict(Counter(r["source_cohort_evidence"] for r in public_links)),
        "source_protocol_task_counts_canonical": dict(Counter(task_literal(r.get("protocol_clue", ""), (paths_by_id.get(r["container_id"]) or [{}])[0]) for r in canonical_sources)),
        "muss_numeric_n": len(muss_values),
        "muss_numeric_min": min(muss_values) if muss_values else None,
        "muss_numeric_median": median(muss_values) if muss_values else None,
        "muss_numeric_max": max(muss_values) if muss_values else None,
        "muss_units": "header_percent_but_observed_0_to_40_unresolved; no conversion applied",
        "ha_vendor_name_dob_overlap_candidate_count": len(vendor_overlap_pids),
        "identity_policy": "exact full pinyin token only; initials/unmatched clues diagnostic-only; no independent-child or diagnosis assertion",
        "date_policy": "same calendar day is linkage evidence only, not proof that scales were administered the same day",
        "device_state_policy": "not inferred; source device_state retained as supplied",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    config = BASE / "configs/phase3_science_v1.json"
    inputs = [CLINICAL, SOURCE_MANIFEST, SOURCE_PATHS] + ([config] if config.exists() else [])
    (out / "input_sha256.json").write_text(json.dumps({str(p.relative_to(BASE)): sha256(p) for p in inputs}, indent=2))
    shutil.copy2(Path(__file__), out / Path(__file__).name)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
