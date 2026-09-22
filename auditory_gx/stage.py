"""One-time staging: event-locked float16 epoch tensors per record from the D1 arrays.

Reads the ST1 scope run (records + per-record event tables on the D1 axis), cuts every
target event with full support at [-pre, +post], stores ALL of them with QC flags, and
attaches child/age/device/condition metadata. Output: private/auditory_gx/<run>/epochs/<rid>.npz
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from auditory_st import features as ft
from auditory_st.runtime import ROOT, read_json

from .runtime import cfg


def _rows(path: Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def condition_map(config: dict) -> dict[str, str]:
    """Canonical record -> directory condition clue (ci/ciha x quiet/noise x direction), when any."""
    clues = {r["container_id"]: r["condition_clue"] for r in _rows(ROOT / cfg(config, "sources.condition_clues"))}
    lineage = _rows(ROOT / cfg(config, "sources.mff_lineage"))
    out: dict[str, set] = {}
    for r in lineage:
        cid = r["container_id"]
        if cid not in clues:
            continue
        for s in r["source_candidate_ids"].replace("[", "").replace("]", "").replace('"', "").replace("'", "").split(","):
            s = s.strip()
            if s:
                out.setdefault(s, set()).add(clues[cid])
    return {k: "|".join(sorted(v)) for k, v in out.items()}


def lane_codes(config_st: dict, lane: str) -> dict:
    return {str(k): int(v) for k, v in config_st["lanes"][lane]["codes"].items()}


def _bandpass_record(data: np.ndarray, meta: dict, lo: float, hi: float, *, noise: bool = False, seed: int = 0) -> np.ndarray:
    """Zero-phase Butterworth band-pass applied per stored interval of the whole record (edges far from epochs)."""
    from scipy import signal
    rate = float(meta["rate_hz"])
    sos = signal.butter(4, [lo, hi], btype="bandpass", fs=rate, output="sos")
    out = np.empty_like(data, dtype=np.float32)
    rng = np.random.default_rng(seed)
    for iv in meta["intervals"]:
        a, b = int(iv["start"]), int(iv["stop"])
        block = np.asarray(data[:, a:b], dtype=np.float64)
        if noise:
            block = rng.standard_normal(block.shape) * block.std(axis=1, keepdims=True)
        out[:, a:b] = signal.sosfiltfilt(sos, block, axis=-1).astype(np.float32)
    return out


def stage_record(rec: dict, scope_private: Path, config: dict, config_st: dict, cond: dict[str, str],
                 variant: str = "") -> dict:
    lane = rec["lane"]
    codes = lane_codes(config_st, lane)
    branch = rec["branch"]
    d1_run = cfg(config, "sources.d1_mff_run" if branch == "MFF" else "sources.d1_bdf_run")
    container = rec["record_id"] if branch == "MFF" else rec["_d1_container_id"]
    meta = read_json(ROOT / "private/auditory_d1" / d1_run / "arrays" / f"{container}.json")
    array_path = ROOT / "private/auditory_d1" / d1_run / "arrays" / f"{container}.npy"
    events = pd.read_parquet(scope_private / "events" / f"{rec['record_id']}.parquet")
    rate = float(meta["rate_hz"])
    pre = int(round(cfg(config, "epoch.pre_seconds") * rate))
    post = int(round(cfg(config, "epoch.post_seconds") * rate))
    guard = int(round(cfg(config, "epoch.interval_edge_guard_seconds") * rate))
    intervals = {int(r["interval_index"]): r for r in meta["intervals"]}
    targets = events[(events.event_kind == "target") & (events.exported_index >= 0)].copy()
    keep = []
    for row in targets.itertuples():
        iv = intervals[int(row.exported_interval_index)]
        lo, hi = int(row.exported_index) - pre, int(row.exported_index) + post
        keep.append(lo >= int(iv["start"]) + guard and hi <= int(iv["stop"]) - guard)
    targets = targets[np.asarray(keep, dtype=bool)]
    data = np.load(array_path, mmap_mode="r")
    onsets = targets.exported_index.to_numpy(dtype=np.int64).copy()
    if variant.startswith("band:") or variant.startswith("noise_band:"):
        lo, hi = (float(v) for v in variant.split(":")[1].split("-"))
        data = _bandpass_record(data, meta, lo, hi, noise=variant.startswith("noise"), seed=abs(hash(rec["record_id"])) % (2 ** 31))
    elif variant == "jitter":
        # destroy time-locking: uniform shift within +-0.35 s per trial, seeded per record
        rng = np.random.default_rng(abs(hash(rec["record_id"])) % (2 ** 31))
        shift = rng.integers(-int(0.35 * rate), int(0.35 * rate) + 1, size=len(onsets))
        onsets = onsets + shift
        keep2 = []
        for e, ii in zip(onsets, targets.exported_interval_index.to_numpy(dtype=int)):
            iv = intervals[ii]
            keep2.append(e - pre >= int(iv["start"]) + guard and e + post <= int(iv["stop"]) - guard)
        keep2 = np.asarray(keep2, dtype=bool)
        targets, onsets = targets[keep2], onsets[keep2]
    elif variant:
        raise ValueError(f"unknown staging variant {variant}")
    n, C, T = len(targets), data.shape[0], pre + post
    epochs = np.empty((n, C, T), dtype=np.float32)
    for i, e in enumerate(onsets):
        epochs[i] = data[:, e - pre:e + post]
    qc = cfg(config, "qc")
    accepted = np.zeros(n, dtype=bool)
    over = np.zeros(n, dtype=np.float32)
    for i in range(n):
        ok, _reason, o, _f = ft.epoch_qc(epochs[i], ptp_max=float(qc["ptp_max_uv"]),
                                        ptp_fraction_max=float(qc["ptp_channel_fraction_max"]),
                                        flat_ptp=float(qc["flat_ptp_uv"]),
                                        flat_fraction_max=float(qc["flat_channel_fraction_max"]))
        accepted[i], over[i] = ok, o
    scale = float(np.median(np.abs(epochs[accepted]))) if accepted.any() else 1.0
    if not np.isfinite(scale) or scale <= 1e-6:
        scale = 1.0
    x16 = np.clip(epochs / scale, -60.0, 60.0).astype(np.float16)
    prev_code = ft.literal_to_class(targets.previous_code.to_numpy(dtype=object), codes)
    prev_run = np.array([(-1 if v is None or (isinstance(v, float) and np.isnan(v)) else int(v))
                         for v in targets.previous_run_length.to_numpy(dtype=object)], dtype=np.int64)
    payload = dict(
        x=x16, y=targets.stimulus_local_id.to_numpy(dtype=np.int64), accepted=accepted, qc_over_fraction=over,
        onset_seconds=targets.onset_seconds.to_numpy(dtype=np.float64),
        block_id=targets.block_id.to_numpy(dtype=np.int64), trial_id=targets.trial_id.to_numpy(dtype=str),
        previous_code=prev_code, previous_gap_s=np.nan_to_num(targets.previous_gap_s.to_numpy(dtype=np.float64), nan=-1.0),
        previous_run_length=prev_run, history_status=targets.history_status.to_numpy(dtype=str),
        record_scale=np.float64(scale), rate_hz=np.float64(rate), pre_samples=np.int64(pre), post_samples=np.int64(post),
        record_id=str(rec["record_id"]), lane=str(lane), branch=str(branch), identity_group=str(rec["identity_group"]),
        n_channels=np.int64(C), layout_hash=str(rec.get("d1_layout_hash", "")),
        age_months=np.float64(rec.get("age_months", np.nan)), device_duration_months=np.float64(rec.get("device_duration_months", np.nan)),
        source_cohort_evidence=str(rec.get("source_cohort_evidence", "")), candidate_day_id=str(rec.get("candidate_day_id", "")),
        condition_clue=str(cond.get(rec["record_id"], "")), original_fs=np.float64(meta["original_fs"]),
        d1_seconds=np.float64(meta["seconds"]), variant=str(variant),
    )
    return payload


def summary_of(payload: dict) -> dict:
    y, acc = payload["y"], payload["accepted"]
    return {"record_id": payload["record_id"], "lane": payload["lane"], "branch": payload["branch"],
            "identity_group": payload["identity_group"], "n_channels": int(payload["n_channels"]),
            "n_epochs": int(len(y)), "n_accepted": int(acc.sum()),
            "accepted_per_class": {int(k): int(np.sum(acc & (y == k))) for k in np.unique(y)},
            "blocks": int(len(np.unique(payload["block_id"]))), "record_scale": float(payload["record_scale"]),
            "condition_clue": payload["condition_clue"], "source_cohort_evidence": payload["source_cohort_evidence"],
            "age_months": float(payload["age_months"]), "device_duration_months": float(payload["device_duration_months"]),
            "d1_seconds": float(payload["d1_seconds"])}
