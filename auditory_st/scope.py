"""Aggregate, outcome-blind scope tables: who/what/when is actually analysable.

Public outputs contain counts, quantiles and opaque record ids only. Identity groups,
paths and record times stay private.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .runtime import cfg

PUBLIC_RECORD_COLUMNS = ["record_id", "branch", "protocol_task", "lane", "source_cohort_evidence",
                         "source_gate", "source_gate_reasons", "d1_exported", "d1_rate_hz", "d1_original_fs",
                         "d1_n_channels", "d1_seconds", "d1_n_intervals", "d1_n_skipped_intervals",
                         "n_storage_intervals", "sensor_net"]


def _q(values, q):
    arr = np.asarray([v for v in values if v is not None and np.isfinite(v)], dtype=float)
    return float(np.quantile(arr, q)) if arr.size else float("nan")


def data_scope_table(records: pd.DataFrame, event_summaries: dict[str, dict], config: dict) -> pd.DataFrame:
    rows = []
    minimum = int(cfg(config, "qc.record_min_trials_per_class"))
    for (branch, task), sub in records.groupby(["branch", "protocol_task"], sort=True):
        lane = sub.lane.iloc[0]
        ev = [event_summaries[r] for r in sub.record_id if r in event_summaries]
        eligible = sub[(sub.source_gate == "eligible") | (sub.source_gate == "eligible_technical_measurement")]
        ok_records = [r for r in sub.record_id if r in event_summaries
                      and all(v >= minimum for v in event_summaries[r]["supported_by_class"].values())
                      and len(event_summaries[r]["supported_by_class"]) == 2]
        ok_groups = sub[sub.record_id.isin(ok_records)].identity_group.nunique()
        day_groups = sub[sub.candidate_day_id.astype(str) != ""].groupby("candidate_day_id").record_id.nunique()
        rows.append({
            "branch": branch, "protocol_task": task, "lane": lane,
            "records": int(len(sub)), "identity_groups": int(sub.identity_group.nunique()),
            "source_gate_eligible_records": int(len(eligible)),
            "d1_exported_records": int(sub.d1_exported.sum()),
            "events_read_records": len(ev),
            "records_with_two_classes_ge_min": len(ok_records),
            "identity_groups_with_two_classes_ge_min": int(ok_groups),
            "age_available_records": int(np.isfinite(sub.age_months.astype(float)).sum()),
            "age_available_groups": int(sub[np.isfinite(sub.age_months.astype(float))].identity_group.nunique()),
            "device_duration_available_records": int(np.isfinite(sub.device_duration_months.astype(float)).sum()),
            "cohort_evidence_counts": json.dumps({k: int(v) for k, v in sub.source_cohort_evidence.value_counts().items()}),
            "same_day_multirecord_days": int((day_groups > 1).sum()) if len(day_groups) else 0,
            "supported_trials_class0_median": _q([e["supported_by_class"].get("0", np.nan) for e in ev], 0.5),
            "supported_trials_class1_median": _q([e["supported_by_class"].get("1", np.nan) for e in ev], 0.5),
            "supported_trials_class1_min": _q([e["supported_by_class"].get("1", np.nan) for e in ev], 0.0),
            "d1_seconds_median": _q(sub.d1_seconds.astype(float), 0.5),
            "age_months_p25": _q(sub.age_months.astype(float), 0.25),
            "age_months_median": _q(sub.age_months.astype(float), 0.5),
            "age_months_p75": _q(sub.age_months.astype(float), 0.75),
        })
    return pd.DataFrame(rows)


def task_event_table(records: pd.DataFrame, event_summaries: dict[str, dict], config: dict) -> pd.DataFrame:
    rows = []
    lanes = cfg(config, "lanes")
    for lane_name, lane in lanes.items():
        sub = records[records.lane == lane_name]
        ev = [event_summaries[r] for r in sub.record_id if r in event_summaries]
        if not ev:
            continue
        literal_counts: dict[str, int] = {}
        reasons: dict[str, int] = {}
        for e in ev:
            for k, v in e.get("literal_counts", {}).items():
                literal_counts[k] = literal_counts.get(k, 0) + int(v)
            for k, v in e.get("unsupported_reasons", {}).items():
                reasons[k] = reasons.get(k, 0) + int(v)
        soa_p05 = [e["soa_quantiles_s"].get("p05") for e in ev if e["soa_quantiles_s"]]
        soa_p50 = [e["soa_quantiles_s"].get("p50") for e in ev if e["soa_quantiles_s"]]
        soa_p00 = [e["soa_quantiles_s"].get("p00") for e in ev if e["soa_quantiles_s"]]
        rows.append({
            "lane": lane_name, "branch": lane["branch"], "protocol_task": lane["protocol_task"],
            "role": lane["role"], "codes": json.dumps(lane["codes"]),
            "sound_identity_status": lane.get("note", "literal source task label; acoustics not re-validated"),
            "onset_coordinate": ("original MFF sample from MNE annotations; no acoustic latency correction"
                                 if lane["branch"] == "MFF" else
                                 "BDF event-companion annotation seconds x 1000 Hz; header clocks equal (else held)"),
            "export_coordinate": "D1 interval.start + (onset - interval.original_start_sample) // stride @250 Hz",
            "records": int(len(sub)), "records_with_events": len(ev),
            "n_target_events": int(sum(e["n_target_events"] for e in ev)),
            "n_supported_epochs": int(sum(e["n_supported"] for e in ev)),
            "literal_counts": json.dumps(dict(sorted(literal_counts.items()))),
            "unsupported_reasons": json.dumps(dict(sorted(reasons.items()))),
            "target_sample_collisions": int(sum(e.get("target_sample_collisions", 0) for e in ev)),
            "unknown_sound_events": int(sum(e["n_unknown_sound"] for e in ev)),
            "soa_min_over_records_s": _q(soa_p00, 0.0),
            "soa_p05_median_over_records_s": _q(soa_p05, 0.5),
            "soa_p05_min_over_records_s": _q(soa_p05, 0.0),
            "soa_median_over_records_s": _q(soa_p50, 0.5),
            "max_alignment_residual_ms": _q([e["max_alignment_residual_ms"] for e in ev], 1.0),
            "history_complete_fraction": (float(sum(e["history_complete"] for e in ev)) /
                                          max(1, sum(e["n_supported"] for e in ev))),
        })
    return pd.DataFrame(rows)


def record_support_table(records: pd.DataFrame, event_summaries: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for r in records.itertuples():
        e = event_summaries.get(r.record_id)
        rows.append({**{c: getattr(r, c) for c in PUBLIC_RECORD_COLUMNS},
                     "events_read": e is not None,
                     "n_target_events": e["n_target_events"] if e else 0,
                     "n_supported": e["n_supported"] if e else 0,
                     "supported_class0": e["supported_by_class"].get("0", 0) if e else 0,
                     "supported_class1": e["supported_by_class"].get("1", 0) if e else 0,
                     "blocks_class0": e["blocks_by_class"].get("0", 0) if e else 0,
                     "blocks_class1": e["blocks_by_class"].get("1", 0) if e else 0,
                     "soa_median_s": e["soa_quantiles_s"].get("p50", np.nan) if e and e["soa_quantiles_s"] else np.nan,
                     "unsupported_reasons": json.dumps(e["unsupported_reasons"]) if e else "",
                     "unknown_sound_events": e["n_unknown_sound"] if e else 0})
    return pd.DataFrame(rows)


def write_public_tables(public: Path, tables: dict[str, pd.DataFrame]) -> dict[str, str]:
    from .runtime import digest

    hashes = {}
    for name, frame in tables.items():
        path = public / f"{name}.csv"
        frame.to_csv(path, index=False)
        path.chmod(0o644)
        hashes[path.name] = digest(path)
    return hashes
