"""Per-record event tables in ORIGINAL sample coordinates, mapped onto the D1 export axis.

Event roles come from frozen literal maps (MFF: stad/devt; HA: '1'/'2'); nothing is
inferred from class frequency. Stimulus history is computed on the complete pre-QC
chain with `auditory5.events.build_event_history`. The D1 mapping is
    exported_index = interval.start + (onset_sample - interval.original_start_sample) // stride
and is valid only when the onset lies inside a stored interval that D1 exported.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from auditory5.events import build_event_history

from .runtime import ProvenanceError, cfg

MFF_NON_SOUND = frozenset({"SESS", "CELL", "bgin", "TRSP", "ITI+", "stm+", "net", "BAD_ACQ_SKIP"})


def d1_interval_table(meta: dict) -> list[dict]:
    """Exported intervals with their original-sample span (exclusive stop)."""
    stride = int(meta["stride"])
    rows = []
    for row in meta["intervals"]:
        n_exported = int(row["stop"]) - int(row["start"])
        rows.append({"interval_index": int(row["interval_index"]), "start": int(row["start"]),
                     "stop": int(row["stop"]), "original_start_sample": int(row["original_start_sample"]),
                     "original_stop_sample_exclusive": int(row["original_start_sample"]) + n_exported * stride,
                     "stride": stride})
    return rows


def map_original_to_exported(onset_sample: int, intervals: list[dict]) -> tuple[int, int, float]:
    """Return (exported_index, interval_index, residual_samples) or (-1, -1, nan)."""
    for row in intervals:
        if row["original_start_sample"] <= onset_sample < row["original_stop_sample_exclusive"]:
            offset = onset_sample - row["original_start_sample"]
            exported = row["start"] + offset // row["stride"]
            return int(exported), int(row["interval_index"]), float(offset % row["stride"])
    return -1, -1, float("nan")


def epoch_support(exported: int, interval_index: int, intervals: list[dict], *,
                  pre_samples: int, post_samples: int, guard_samples: int) -> tuple[bool, str]:
    if exported < 0:
        return False, "onset_not_in_exported_interval"
    row = next(r for r in intervals if r["interval_index"] == interval_index)
    lo, hi = exported - pre_samples, exported + post_samples
    if lo < row["start"] + guard_samples:
        return False, "epoch_before_interval_guard"
    if hi > row["stop"] - guard_samples:
        return False, "epoch_after_interval_guard"
    return True, ""


def _finish_rows(rows: list[dict], fs: float, codes: dict, meta: dict, config: dict) -> list[dict]:
    """History, D1 mapping and support flags for a complete ordered chain."""
    history = build_event_history(rows, fs, target_codes=set(codes))
    intervals = d1_interval_table(meta)
    rate = float(meta["rate_hz"])
    pre = int(round(cfg(config, "epoch.pre_seconds") * rate))
    post = int(round(cfg(config, "epoch.post_seconds") * rate))
    guard = int(round(cfg(config, "epoch.interval_edge_guard_seconds") * rate))
    block = float(cfg(config, "qc.block_seconds"))
    out = []
    for row in history:
        onset = int(row["onset_sample"])
        exported, interval_index, residual = map_original_to_exported(onset, intervals)
        supported, reason = (False, "not_target") if row["event_kind"] != "target" else epoch_support(
            exported, interval_index, intervals, pre_samples=pre, post_samples=post, guard_samples=guard)
        onset_s = onset / fs
        row.update(
            stimulus_local_id=codes.get(row["event_literal"], -1),
            onset_seconds=onset_s,
            exported_index=exported,
            exported_interval_index=interval_index,
            alignment_residual_ms=(residual / fs * 1000.0) if math.isfinite(residual) else float("nan"),
            epoch_supported=bool(supported),
            epoch_support_reason=reason,
            block_id=int(onset_s // block),
        )
        out.append(row)
    return out


def mff_events(record: dict, meta: dict, config: dict, lane_codes: dict) -> tuple[list[dict], dict]:
    """Read annotations from the MFF source (headers only) and map onto the D1 axis."""
    from auditory5.adapters import mff

    source = mff.inspect_source(record["_signal_path"])
    fs = float(source["sfreq"])
    if fs != float(meta["original_fs"]):
        raise ProvenanceError(f"MFF_FS_MISMATCH:{record['record_id']}")
    # D1 interval bookkeeping must agree with the reader's stored intervals.
    reader_intervals = {int(r["interval_index"]): r for r in source["intervals"]}
    for row in meta["intervals"]:
        r = reader_intervals.get(int(row["interval_index"]))
        if r is None or int(r["start_sample"]) != int(row["original_start_sample"]):
            raise ProvenanceError(f"D1_INTERVAL_DISAGREES_WITH_READER:{record['record_id']}")
    rid = record["record_id"]
    rows = []
    collisions: dict[int, int] = {}
    for a in source["annotations"]:
        if str(a["event_literal"]) in lane_codes and a["annotation_origin"] != "reader_annotation":
            collisions[int(a["onset_sample"])] = collisions.get(int(a["onset_sample"]), 0) + 1
    n_collisions = 0
    for a in source["annotations"]:
        literal = str(a["event_literal"])
        if a["annotation_origin"] == "reader_annotation" or literal in MFF_NON_SOUND:
            kind = "non_sound"
        elif literal in lane_codes and collisions.get(int(a["onset_sample"]), 0) == 1:
            kind = "target"
        elif literal in lane_codes:
            kind = "unknown_sound"  # two sound literals at one sample: conservative history break
            n_collisions += 1
        else:
            kind = "unknown_sound"
        rows.append({
            "record_id": rid, "segment_id": a["segment_id"] or f"unstored_{a['annotation_index']}",
            "trial_id": f"{rid}:a{int(a['annotation_index']):05d}", "onset_sample": int(a["onset_sample"]),
            "event_literal": literal, "event_kind": kind,
            "in_stored_interval": bool(a["in_stored_interval"]),
            "source_alignment_residual": float(a["sample_alignment_residual"]),
        })
    # Reader order is chronological within the file; enforce per-segment ordering as build_event_history requires.
    rows.sort(key=lambda r: (r["segment_id"], r["onset_sample"], r["trial_id"]))
    literals = {}
    for r in rows:
        literals[r["event_literal"]] = literals.get(r["event_literal"], 0) + 1
    return _finish_rows(rows, fs, lane_codes, meta, config), {"literal_counts": literals,
                                                               "target_sample_collisions": n_collisions,
                                                               "reader": source["reader"],
                                                               "reader_version": source["reader_version"],
                                                               "layout_hash": source["layout_hash"]}


def ha_events(record: dict, meta: dict, config: dict, lane_codes: dict) -> tuple[list[dict], dict]:
    """Read the BDF event companion annotations; the signal is one stored interval from 0."""
    import pyedflib

    fs = float(meta["original_fs"])
    n_original = int(meta["n_samples"]) * int(meta["stride"])
    with pyedflib.EdfReader(record["_event_path"]) as reader:
        times, durations, codes = reader.readAnnotations()
    rid = record["record_id"]
    rows, literals = [], {}
    for ordinal, (time, _duration, code) in enumerate(zip(times, durations, codes), 1):
        literal = str(code).strip()
        sample = int(np.rint(float(time) * fs))
        if sample < 0 or sample >= n_original + int(meta["stride"]):
            raise ProvenanceError(f"HA_EVENT_OUTSIDE_SIGNAL:{rid}")
        literals[literal] = literals.get(literal, 0) + 1
        rows.append({"record_id": rid, "segment_id": f"{rid}:s0", "trial_id": f"{rid}:e{ordinal:05d}",
                     "onset_sample": sample, "event_literal": literal,
                     "event_kind": "target" if literal in lane_codes else "unknown_sound",
                     "in_stored_interval": True, "source_alignment_residual": float(time) * fs - sample})
    return _finish_rows(rows, fs, lane_codes, meta, config), {"literal_counts": literals,
                                                               "reader": "pyedflib.EdfReader.readAnnotations"}


def record_event_summary(rows: list[dict], codes: dict) -> dict:
    targets = [r for r in rows if r["event_kind"] == "target"]
    supported = [r for r in targets if r["epoch_supported"]]
    gaps = [r["previous_gap_s"] for r in targets if r.get("previous_gap_s") is not None]
    by_class = {str(v): sum(1 for r in supported if r["stimulus_local_id"] == v) for v in sorted(set(codes.values()))}
    blocks_by_class = {str(v): len({r["block_id"] for r in supported if r["stimulus_local_id"] == v})
                       for v in sorted(set(codes.values()))}
    reasons = {}
    for r in targets:
        if not r["epoch_supported"]:
            reasons[r["epoch_support_reason"]] = reasons.get(r["epoch_support_reason"], 0) + 1
    quantiles = {}
    if gaps:
        arr = np.asarray(gaps, dtype=float)
        quantiles = {f"p{int(q*100):02d}": float(np.quantile(arr, q)) for q in (0.0, 0.05, 0.5, 0.95, 1.0)}
    return {"n_annotations": len(rows), "n_target_events": len(targets), "n_supported": len(supported),
            "supported_by_class": by_class, "blocks_by_class": blocks_by_class,
            "unsupported_reasons": reasons, "soa_quantiles_s": quantiles,
            "n_unknown_sound": sum(1 for r in rows if r["event_kind"] == "unknown_sound"),
            "history_complete": sum(1 for r in supported if r["history_status"] == "complete"),
            "first_target_s": float(targets[0]["onset_seconds"]) if targets else float("nan"),
            "last_target_s": float(targets[-1]["onset_seconds"]) if targets else float("nan"),
            "max_alignment_residual_ms": float(max((r["alignment_residual_ms"] for r in supported), default=0.0))}


def write_events(rows: list[dict], path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame(rows)
    frame.to_parquet(path, index=False)
    path.chmod(0o600)
