#!/usr/bin/env python3
"""Descriptive, zero-fit summaries for the bounded F3/F4 pair evidence.

This module deliberately reads only registered aggregate tables.  It never opens
EEG arrays and contains no model fitting or clinical scale conversion.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parents[1]
RUN = os.environ.get("PAIR_RUN_ID", "pairs_001")
PUBLIC = BASE / "results" / "auditory_repair" / RUN
PRIVATE = BASE / "private" / "auditory_repair" / RUN

F3_PAIRS = BASE / "private/auditory_fseries/ci_qualification_001/f3_pair_evidence.csv"
F3_FEATURES = BASE / "results/phase3_ci_measurements_001/features.csv"
F3_QUAL = BASE / "results/auditory_fseries/ci_qualification_001/summary.json"
HA_PAIRS = BASE / "private/phase3_ha_covariates_004/repeat_audit.csv"
HA_FEATURES = BASE / "results/phase2_measurements_001/features.csv"
MFF_QUAL = BASE / "results/auditory_fseries/ci_qualification_001/f4_aggregate_supplement.json"


def _assert_slurm() -> str:
    job = os.environ.get("SLURM_JOB_ID")
    if not job:
        raise RuntimeError("pair description requires a Slurm allocation")
    return job


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _stats(values: Iterable[float]) -> dict:
    a = np.asarray(list(values), dtype=float)
    a = a[np.isfinite(a)]
    if not len(a):
        return {"n": 0, "min": None, "q25": None, "median": None, "q75": None, "max": None, "mean": None}
    q = np.quantile(a, [0.25, 0.5, 0.75])
    return {"n": int(len(a)), "min": float(np.min(a)), "q25": float(q[0]),
            "median": float(q[1]), "q75": float(q[2]), "max": float(np.max(a)),
            "mean": float(np.mean(a))}


def _pearson(x: pd.Series, y: pd.Series) -> dict:
    z = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    n = len(z)
    if n < 3:
        return {"n": int(n), "status": "INSUFFICIENT_FOR_CORRELATION", "pearson_r": None}
    if z.x.nunique() < 2 or z.y.nunique() < 2:
        return {"n": int(n), "status": "CONSTANT_INPUT", "pearson_r": None}
    return {"n": int(n), "status": "DESCRIPTIVE_ONLY", "pearson_r": float(np.corrcoef(z.x, z.y)[0, 1])}


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("\n")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _f3() -> tuple[dict, list[dict]]:
    pairs = pd.read_csv(F3_PAIRS, dtype=str).fillna("")
    # Retain all rows in the registered nine-pair candidate table.  The
    # qualification's literal clinical-target subset is smaller (two rows),
    # but the task asks for descriptive EEG values for every listed pair.
    if pairs.duplicated(["participant_id", "puretone_container_id", "bapa_container_id"]).any():
        raise ValueError("F3 pair table contains duplicate task pairs")
    features = pd.read_csv(F3_FEATURES)
    features = features[(features["variant"] == "primary") & (features["event_code"] == "stad")].copy()
    features = features[features["status"] == "measured"]
    keep = ["container_id", "late_mean_uv", "main_mean_uv", "n_trials"]
    a = features[keep].rename(columns={c: f"puretone_{c}" for c in keep if c != "container_id"})
    b = features[keep].rename(columns={c: f"bapa_{c}" for c in keep if c != "container_id"})
    if a["container_id"].duplicated().any() or b["container_id"].duplicated().any():
        raise ValueError("F3 frozen stad table is not unique per container")
    joined = pairs.merge(a, left_on="puretone_container_id", right_on="container_id", how="left", validate="many_to_one")
    joined = joined.merge(b, left_on="bapa_container_id", right_on="container_id", how="left", suffixes=("", "_b"), validate="many_to_one")
    evidence = []
    for _, r in joined.iterrows():
        row = {"participant_id": r["participant_id"], "acquisition_day_id": r["acquisition_day_id"],
               "puretone_container_id": r["puretone_container_id"], "bapa_container_id": r["bapa_container_id"],
               "same_day_clinical_target_endpoints": r.get("same_day_clinical_target_endpoints", ""),
               "pair_unique_per_task": r.get("pair_unique_per_task", ""),
               "eligible_raw_pair": r.get("eligible_raw_pair", "")}
        for w in ("main", "late"):
            pv, bv = r.get(f"puretone_{w}_mean_uv", np.nan), r.get(f"bapa_{w}_mean_uv", np.nan)
            row[f"puretone_{w}_uv"] = pv
            row[f"bapa_{w}_uv"] = bv
            row[f"{w}_delta_bapa_minus_puretone_uv"] = float(bv - pv) if pd.notna(pv) and pd.notna(bv) else np.nan
        evidence.append(row)
    qual = json.loads(F3_QUAL.read_text())
    metrics = {}
    for w in ("main", "late"):
        pcol, bcol, dcol = f"puretone_{w}_mean_uv", f"bapa_{w}_mean_uv", f"{w}_delta_bapa_minus_puretone_uv"
        metrics[w] = {"difference_bapa_minus_puretone_uv": _stats(joined[bcol] - joined[pcol]),
                      "task_value_correlation": _pearson(joined[pcol], joined[bcol]),
                      "pairs_with_both_task_values": int(pd.to_numeric(joined[pcol], errors="coerce").notna().astype(int).mul(pd.to_numeric(joined[bcol], errors="coerce").notna().astype(int)).sum())}
    summary = {"scope": "F3 puretone/bapa candidate same-day pairs; primary stad only",
               "candidate_pairs": int(len(pairs)), "pairs_with_both_stad_primary": int(sum(pd.notna(r["main_delta_bapa_minus_puretone_uv"]) and pd.notna(r["late_delta_bapa_minus_puretone_uv"]) for r in evidence)),
               "qualification_literal_target_pairs": int(qual["f3"]["unique_task_day_pairs_with_literal_target"]),
               "qualification_confirmed_comparable_pairs": int(qual["f3"]["pairs_with_confirmed_comparable_target"]),
               "metrics": metrics,
               "interpretation": "Descriptive EEG task differences only; puretone and bapa are not treated as the same clinical construct, and no clinical increment or association is inferred.",
               "comparability_caveat": "Clinical endpoint version/unit/timing comparability remains unresolved in the qualification source."}
    return summary, evidence


def _f4_ha() -> tuple[dict, list[dict]]:
    pairs = pd.read_csv(HA_PAIRS, dtype=str).fillna("")
    f = pd.read_csv(HA_FEATURES)
    f = f[(f["variant"] == "hp01_avg20") & (f["condition"] == "code1") & (f["measurement_status"] == "measured")]
    vals = f[["recording_id", "mean_uv"]].copy()
    if vals["recording_id"].duplicated().any():
        raise ValueError("frozen hp01_avg20 table is not unique per recording")
    vals = vals.rename(columns={"mean_uv": "hp01_avg20_code1_uv"})
    a = vals.rename(columns={"recording_id": "recording_a", "hp01_avg20_code1_uv": "a_uv"})
    b = vals.rename(columns={"recording_id": "recording_b", "hp01_avg20_code1_uv": "b_uv"})
    if pairs.duplicated(["participant_id", "recording_a", "recording_b"]).any():
        raise ValueError("HA repeat table contains duplicate pairs")
    j = pairs.merge(a, on="recording_a", how="left", validate="many_to_one").merge(b, on="recording_b", how="left", validate="many_to_one")
    evidence = []
    deltas, intervals = [], []
    for _, r in j.iterrows():
        av, bv = pd.to_numeric(pd.Series([r.get("a_uv")]), errors="coerce").iloc[0], pd.to_numeric(pd.Series([r.get("b_uv")]), errors="coerce").iloc[0]
        interval = pd.to_numeric(pd.Series([r.get("elapsed_vendor_exam_months")]), errors="coerce").iloc[0]
        delta = float(bv - av) if pd.notna(av) and pd.notna(bv) else np.nan
        if pd.notna(delta): deltas.append(delta)
        if pd.notna(interval): intervals.append(float(interval))
        evidence.append({"participant_id": r["participant_id"], "recording_a": r["recording_a"], "recording_b": r["recording_b"],
                         "exam_time_a": r["exam_time_a"], "exam_time_b": r["exam_time_b"], "a_hp01_avg20_code1_uv": av,
                         "b_hp01_avg20_code1_uv": bv, "delta_b_minus_a_uv": delta, "elapsed_vendor_exam_months": interval})
    summary = {"scope": "HA repeated acquisition pairs; frozen hp01_avg20 code1",
               "candidate_pairs": int(len(pairs)), "candidate_identity_groups": int(pairs["participant_id"].nunique()),
               "pairs_with_both_measurements": int(len(deltas)), "pairs_with_vendor_exam_interval": int(len(intervals)),
               "delta_b_minus_a_uv": _stats(deltas), "elapsed_vendor_exam_months": _stats(intervals),
               "independence": "Repeated pairs are descriptive and are not counted as independent people.",
               "measurement_definition": "Existing phase2_measurements_001 features; no feature extraction or EEG reread."}
    return summary, evidence


def _f4_mff() -> dict:
    x = json.loads(MFF_QUAL.read_text())
    return {"scope": "F4 MFF identity-endpoint literal repeated values", "identity_endpoint_series": int(x["f4_identity_endpoint_series"]),
            "identity_groups": int(x["f4_unique_candidate_identity_groups"]),
            "series_state_counts": x["f4_series_state_counts"], "identity_group_state_counts": x["f4_identity_groups_with_state_counts"],
            "interpretation": x["interpretation"]}


def _self_test() -> None:
    assert _stats([1, 2, 3])["median"] == 2.0
    assert _pearson(pd.Series([1, 2]), pd.Series([1, 2]))["status"] == "INSUFFICIENT_FOR_CORRELATION"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    job = _assert_slurm()
    if args.self_test:
        _self_test()
        print(json.dumps({"status": "SELF_TEST_PASS", "job_id": job, "fit_calls": 0}))
        return
    if PUBLIC.exists() or PRIVATE.exists():
        raise FileExistsError("refusing to overwrite pair description run")
    # Freeze source inventory before importing/reading any measurement rows.
    inputs = [F3_PAIRS, F3_FEATURES, F3_QUAL, HA_PAIRS, HA_FEATURES, MFF_QUAL, Path(__file__)]
    source_manifest = [{"path": str(p.relative_to(BASE)), "sha256": _sha256(p), "bytes": p.stat().st_size} for p in inputs]
    PRIVATE.mkdir(parents=True, mode=0o700)
    os.chmod(PRIVATE, 0o700)
    (PRIVATE / "start_receipt.json").write_text(json.dumps({"status": "STARTED", "job_id": job, "fit_calls": 0, "source_manifest": source_manifest}, indent=2))
    shutil.copy2(Path(__file__), PRIVATE / Path(__file__).name)
    try:
        f3, f3_rows = _f3()
        ha, ha_rows = _f4_ha()
        mff = _f4_mff()
        PUBLIC.mkdir(parents=True, mode=0o755)
        _write_csv(PRIVATE / "f3_pair_measurements.csv", f3_rows)
        _write_csv(PRIVATE / "f4_ha_pair_measurements.csv", ha_rows)
        (PRIVATE / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2))
        (PUBLIC / "f3_summary.json").write_text(json.dumps(f3, indent=2))
        (PUBLIC / "f4_ha_summary.json").write_text(json.dumps(ha, indent=2))
        (PUBLIC / "f4_mff_summary.json").write_text(json.dumps(mff, indent=2))
        out = {"status": "COMPLETED", "job_id": job, "fit_calls": 0, "f3": f3, "f4_ha": ha, "f4_mff": mff}
        (PUBLIC / "summary.json").write_text(json.dumps(out, indent=2))
        (PUBLIC / "run_receipt.json").write_text(json.dumps({"status": "COMPLETED", "job_id": job, "fit_calls": 0, "source_count": len(source_manifest)}, indent=2))
        (PRIVATE / "completion.json").write_text(json.dumps({"status": "COMPLETED", "job_id": job, "fit_calls": 0}, indent=2))
        print(json.dumps({"status": "COMPLETED", "job_id": job, "fit_calls": 0, "f3_pairs": f3["candidate_pairs"], "ha_pairs": ha["candidate_pairs"], "mff_series": mff["identity_endpoint_series"]}))
    except Exception as exc:
        (PRIVATE / "failure_receipt.json").write_text(json.dumps({"status": "FAILED", "job_id": job, "error_type": type(exc).__name__, "error": str(exc)}, indent=2))
        raise


if __name__ == "__main__":
    main()
