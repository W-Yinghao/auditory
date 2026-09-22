"""Record table for auditory_st: which recordings exist, with what task, identity and signal.

Pure metadata. No EEG is read here and no clinical outcome value is loaded; the age
cohort tables are consulted only for presence/values of age and device-use months.
Identity is never re-derived: the audited conservative identity graph is the only
source of the split group, and the record is the unit of the table.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from .runtime import ROOT, ProvenanceError, cfg, read_json, source_path

MFF_RECORD_NODE = "record:{cid}"


def _rows(path: Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def d1_meta_dir(config: dict, branch: str) -> Path:
    run = cfg(config, "sources.d1_mff_run" if branch == "MFF" else "sources.d1_bdf_run")
    return ROOT / "private/auditory_d1" / run / "arrays"


def _d1_meta(config: dict, branch: str, container_id: str) -> dict | None:
    path = d1_meta_dir(config, branch) / f"{container_id}.json"
    if not path.is_file():
        return None
    meta = read_json(path)
    if meta.get("contract") != cfg(config, "sources.d1_contract") or meta.get("status") != "D1_EXPORTED":
        raise ProvenanceError(f"D1_META_UNEXPECTED:{container_id}")
    return meta


def _d1_fields(meta: dict | None) -> dict:
    if meta is None:
        return {"d1_exported": False, "d1_rate_hz": np.nan, "d1_original_fs": np.nan, "d1_stride": -1,
                "d1_n_channels": -1, "d1_seconds": np.nan, "d1_n_intervals": 0,
                "d1_n_skipped_intervals": 0, "d1_layout_hash": "", "d1_sensor_net": ""}
    return {"d1_exported": True, "d1_rate_hz": float(meta["rate_hz"]),
            "d1_original_fs": float(meta["original_fs"]), "d1_stride": int(meta["stride"]),
            "d1_n_channels": int(meta["n_channels"]), "d1_seconds": float(meta["seconds"]),
            "d1_n_intervals": len(meta["intervals"]),
            "d1_n_skipped_intervals": len(meta.get("skipped_intervals", [])),
            "d1_layout_hash": str(meta.get("layout_hash") or ""),
            "d1_sensor_net": str(meta.get("sensor_net") or "")}


def lane_of(config: dict, branch: str, protocol_task: str, code_literals: set) -> str:
    """Lane = (branch, audited task label, literal code set). Codes never come from frequency."""
    for name, lane in cfg(config, "lanes").items():
        if lane["branch"] != branch or lane["protocol_task"] != protocol_task:
            continue
        if set(str(k) for k in lane["codes"]) <= set(code_literals):
            return name
    return ""


def _literal_set(text: str) -> set:
    try:
        payload = json.loads(text) if text else {}
    except json.JSONDecodeError:
        return set()
    return set(str(k) for k in payload) if isinstance(payload, dict) else set()


def mff_age_table(config: dict) -> dict[str, dict]:
    """Age at the selected record, from the audited ci_prepare cohort (one record per child)."""
    cohort_csv = source_path(config, "mff_age_cohort")
    rows = _rows(cohort_csv)
    with np.load(cohort_csv.parent / "data.npz", allow_pickle=False) as store:
        clinical = store["C"]
        recordings = [str(r) for r in store["recordings"]]
    if len(rows) != len(recordings):
        raise ProvenanceError("MFF_AGE_COHORT_LENGTH_MISMATCH")
    out = {}
    for index, row in enumerate(rows):
        if str(row["recording"]) != recordings[index]:
            raise ProvenanceError("MFF_AGE_COHORT_ORDER_MISMATCH")
        age = float(clinical[index, 0])
        out[recordings[index]] = {"age_months": age if np.isfinite(age) else np.nan,
                                  "age_source_status": row["age_source_status"],
                                  "age_cohort_scope": row["scope"]}
    return out


def mff_records(config: dict) -> list[dict]:
    labels = {r["container_id"]: r for r in _rows(source_path(config, "mff_canonical_labels"))}
    metadata = {r["container_id"]: r for r in _rows(source_path(config, "mff_source_metadata"))}
    manifest = {r["container_id"]: r for r in _rows(source_path(config, "mff_sources_manifest"))
                if r["container_id"] == r["canonical_container_id"]}
    paths = {r["container_id"]: r for r in _rows(source_path(config, "mff_source_paths"))}
    graph = read_json(source_path(config, "identity_graph"))["node_to_group"]
    ages = mff_age_table(config)
    if set(labels) != set(manifest):
        raise ProvenanceError("MFF_CANONICAL_SET_MISMATCH")
    records = []
    for cid in sorted(labels):
        lab, meta, man = labels[cid], metadata[cid], manifest[cid]
        node = MFF_RECORD_NODE.format(cid=cid)
        if node not in graph:
            raise ProvenanceError(f"IDENTITY_NODE_MISSING:{cid}")
        if cid not in paths:
            raise ProvenanceError(f"MFF_PATH_MISSING:{cid}")
        d1 = _d1_meta(config, "MFF", cid)
        age = ages.get(cid, {})
        literals = _literal_set(man.get("annotation_code_counts", ""))
        records.append({
            "record_id": cid, "branch": "MFF", "protocol_task": lab["protocol_task"],
            "lane": lane_of(config, "MFF", lab["protocol_task"], literals),
            "literal_code_set": json.dumps(sorted(literals)),
            "identity_group": graph[node], "identity_basis": "auditory5_manifest_001_identity_graph",
            "source_cohort_evidence": lab["source_cohort_evidence"],
            "source_label_expanded": meta.get("source_label_expanded", ""),
            "source_candidate_ambiguity": lab["source_candidate_ambiguity"],
            "candidate_day_id": lab["candidate_acquisition_day_id"],
            "same_day_pid": lab["unique_same_day_pid"],
            "wearing_evidence": meta.get("wearing_evidence", ""),
            "device_power_state": meta.get("device_power_state", ""),
            "metadata_caution_flags": meta.get("metadata_caution_flags", ""),
            "source_status": man["source_status"], "sensor_net": man["sensor_net"],
            "source_sfreq": float(man["sfreq"]), "source_n_channels": int(man["n_channels"]),
            "n_storage_intervals": int(man["n_storage_intervals"]),
            "storage_intervals_samples": man["storage_intervals_samples"],
            "source_token_id": man["candidate_token_id"],
            "age_months": float(age.get("age_months", np.nan)),
            "age_source_status": age.get("age_source_status", "not_in_age_cohort"),
            "device_duration_months": np.nan, "device_duration_status": "no_numeric_CI_duration_column",
            "source_gate": "eligible" if man["source_status"] == "eligible" else man["source_status"],
            "source_gate_reasons": "",
            # private-only columns (stripped from public tables)
            "_signal_path": paths[cid]["path"], "_record_time": paths[cid]["record_time"],
            **_d1_fields(d1),
        })
    return records


def ha_records(config: dict) -> list[dict]:
    manifest = _rows(source_path(config, "ha_source_manifest"))
    index = {r["recording_id"]: r for r in _rows(source_path(config, "ha_index_recordings"))}
    lookup = {r["file_id"]: r["absolute_path"] for r in _rows(source_path(config, "file_path_map"))}
    graph = read_json(source_path(config, "identity_graph"))["node_to_group"]
    cohort = {}
    for row in _rows(source_path(config, "ha_age_cohort")):
        def number(key):
            try:
                value = float(row[key])
            except (TypeError, ValueError):
                return np.nan
            return value if np.isfinite(value) else np.nan
        cohort[str(row["recording"])] = {"age_months": number("age"), "device_duration_months": number("duration"),
                                         "unaided_present": np.isfinite(number("unaided")),
                                         "aided_present": np.isfinite(number("aided"))}
    records = []
    for r in sorted(manifest, key=lambda x: x["recording_id"]):
        rid = r["recording_id"]
        pid = r["participant_id"]
        if pid not in graph:
            raise ProvenanceError(f"IDENTITY_NODE_MISSING:{rid}")
        d1 = _d1_meta(config, "HA_BDF", r["signal_file_id"])
        ix = index.get(rid, {})
        c = cohort.get(rid, {})
        clock = float(r["event_header_minus_signal_header_s"])
        literals = _literal_set(r.get("annotation_counts", ""))
        records.append({
            "record_id": rid, "branch": "HA_BDF", "protocol_task": "puretone_literal_1_2",
            "lane": lane_of(config, "HA_BDF", "puretone_literal_1_2", literals),
            "literal_code_set": json.dumps(sorted(literals)),
            "identity_group": graph[pid], "identity_basis": "auditory5_manifest_001_identity_graph",
            "source_cohort_evidence": r["cohort_label"], "source_label_expanded": r["cohort_label"],
            "source_candidate_ambiguity": r["participant_status"],
            "candidate_day_id": "", "same_day_pid": pid,
            "wearing_evidence": "", "device_power_state": r.get("device_state", "unknown"),
            "metadata_caution_flags": "identity_dob_conflict" if r["identity_dob_conflict"] == "True" else "",
            "source_status": r["source_gate"], "sensor_net": "clinical_22ch_bdf",
            "source_sfreq": float(r["sfreq_hz"]), "source_n_channels": int(r["n_channels"]),
            "n_storage_intervals": 1, "storage_intervals_samples": f"[[0, {int(r['n_samples'])}]]",
            "source_token_id": pid,
            "age_months": float(c.get("age_months", np.nan)),
            "age_source_status": "ha_prepare_001_cohort" if rid in cohort else "not_in_age_cohort",
            "device_duration_months": float(c.get("device_duration_months", np.nan)),
            "device_duration_status": "ha_prepare_001_cohort" if rid in cohort else "not_in_age_cohort",
            "source_gate": r["source_gate"], "source_gate_reasons": r["source_gate_reasons"],
            "ha_event_clock_offset_s": clock,
            "ha_index_recording_flag": ix.get("index_recording_flag", ""),
            "ha_index_hold_reason": ix.get("index_hold_reason", ""),
            "ha_target_interval_median_s": r["target_interval_median_s"],
            "_signal_path": lookup[r["signal_file_id"]], "_event_path": lookup[r["event_file_id"]],
            "_d1_container_id": r["signal_file_id"], "_record_time": "",
            **_d1_fields(d1),
        })
    return records


def build(config: dict) -> list[dict]:
    records = mff_records(config) + ha_records(config)
    ids = [r["record_id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ProvenanceError("RECORD_ID_COLLISION")
    return records


def public_view(records: list[dict]) -> list[dict]:
    """Strip private columns (paths, times) from a record table."""
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]


def write_records(records: list[dict], private: Path, public: Path) -> dict:
    import pandas as pd

    frame = pd.DataFrame(records)
    frame.to_parquet(private / "records.parquet", index=False)
    (private / "records.parquet").chmod(0o600)
    frame.to_csv(private / "records.csv", index=False)
    (private / "records.csv").chmod(0o600)
    counts = {}
    for branch in sorted(frame.branch.unique()):
        sub = frame[frame.branch == branch]
        counts[branch] = {
            "records": int(len(sub)),
            "identity_groups": int(sub.identity_group.nunique()),
            "d1_exported": int(sub.d1_exported.sum()),
            "by_task_records": {k: int(v) for k, v in sub.protocol_task.value_counts().items()},
            "by_task_groups": {k: int(v) for k, v in sub.groupby("protocol_task").identity_group.nunique().items()},
            "age_available_records": int(np.isfinite(sub.age_months.astype(float)).sum()),
            "device_duration_available_records": int(np.isfinite(sub.device_duration_months.astype(float)).sum()),
            "source_gate": {k: int(v) for k, v in sub.source_gate.value_counts().items()},
        }
    return counts
