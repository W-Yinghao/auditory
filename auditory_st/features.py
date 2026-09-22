"""Event-locked windows from the D1 continuous arrays: QC, record scaling, window means.

The D1 export is zero-phase filtered (0.5-45 Hz), average referenced, 250 Hz. Epochs
are cut on the exported axis at the mapped onset index. No baseline subtraction: the
pre-stimulus windows stay in the curve as their own control. The per-record scalar
scale (median |x| over accepted epochs) removes recording gain only.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .runtime import ProvenanceError, cfg


def window_starts(rate: float, pre_s: float, post_s: float, length_s: float, step_s: float) -> tuple[np.ndarray, int]:
    """Start sample offsets (relative to epoch start) and window length in samples."""
    length = int(round(length_s * rate))
    step = int(round(step_s * rate))
    total = int(round((pre_s + post_s) * rate))
    starts = np.arange(0, total - length + 1, step, dtype=np.int64)
    return starts, length


def window_centres_s(starts: np.ndarray, length: int, rate: float, pre_s: float) -> np.ndarray:
    return (starts + length / 2.0) / rate - pre_s


def window_means(epochs: np.ndarray, starts: np.ndarray, length: int) -> np.ndarray:
    """epochs [n, C, T] -> [n, W, C] window means via cumulative sums."""
    cs = np.cumsum(np.concatenate([np.zeros(epochs.shape[:2] + (1,), dtype=np.float64),
                                   epochs.astype(np.float64)], axis=2), axis=2)
    means = (cs[:, :, starts + length] - cs[:, :, starts]) / float(length)  # [n, C, W]
    return np.ascontiguousarray(np.transpose(means, (0, 2, 1)).astype(np.float32))


def epoch_qc(epoch: np.ndarray, *, ptp_max: float, ptp_fraction_max: float,
             flat_ptp: float, flat_fraction_max: float) -> tuple[bool, str, float, float]:
    ptp = np.ptp(epoch, axis=1)
    over = float(np.mean(ptp > ptp_max))
    flat = float(np.mean(ptp < flat_ptp))
    reasons = []
    if not np.isfinite(epoch).all():
        reasons.append("nonfinite")
    if over > ptp_fraction_max:
        reasons.append("too_many_channels_over_ptp")
    if flat > flat_fraction_max:
        reasons.append("too_many_flat_channels")
    return (not reasons), "|".join(reasons), over, flat


def literal_to_class(values, codes: dict) -> np.ndarray:
    """Previous-sound literal -> class id from the frozen lane map; None/unknown -> -1."""
    out = np.full(len(values), -1, dtype=np.int64)
    for i, v in enumerate(values):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            continue
        out[i] = int(codes.get(str(v), -1))
    return out


def extract_record(array_path: Path, meta: dict, events, config: dict, *, post_seconds: float,
                   codes: dict) -> dict:
    """Cut supported target epochs, QC them, scale the record and compute window means.

    `events` is a pandas DataFrame from events.py (all annotations). Returns arrays for
    every supported target event, with `accepted` marking the QC outcome, so nothing
    is silently dropped. `codes` is the frozen literal->class map of the lane.
    """
    rate = float(meta["rate_hz"])
    if rate != float(cfg(config, "epoch.rate_hz")):
        raise ProvenanceError("D1_RATE_UNEXPECTED")
    pre_s = float(cfg(config, "epoch.pre_seconds"))
    pre = int(round(pre_s * rate))
    post = int(round(post_seconds * rate))
    guard = int(round(cfg(config, "epoch.interval_edge_guard_seconds") * rate))
    intervals = {int(r["interval_index"]): r for r in meta["intervals"]}
    targets = events[(events.event_kind == "target") & (events.exported_index >= 0)].copy()
    ok = []
    for row in targets.itertuples():
        iv = intervals[int(row.exported_interval_index)]
        lo, hi = int(row.exported_index) - pre, int(row.exported_index) + post
        ok.append(lo >= int(iv["start"]) + guard and hi <= int(iv["stop"]) - guard)
    targets = targets[np.asarray(ok, dtype=bool)]
    n = len(targets)
    data = np.load(array_path, mmap_mode="r")
    if data.shape[0] != int(meta["n_channels"]) or data.shape[1] != int(meta["n_samples"]):
        raise ProvenanceError("D1_ARRAY_SHAPE_MISMATCH")
    length = pre + post
    epochs = np.empty((n, data.shape[0], length), dtype=np.float32)
    for i, e in enumerate(targets.exported_index.to_numpy(dtype=np.int64)):
        epochs[i] = data[:, e - pre:e + post]
    qc = cfg(config, "qc")
    accepted = np.zeros(n, dtype=bool)
    reasons, over_frac, flat_frac = [], np.zeros(n), np.zeros(n)
    for i in range(n):
        acc, reason, over, flat = epoch_qc(epochs[i], ptp_max=float(qc["ptp_max_uv"]),
                                           ptp_fraction_max=float(qc["ptp_channel_fraction_max"]),
                                           flat_ptp=float(qc["flat_ptp_uv"]),
                                           flat_fraction_max=float(qc["flat_channel_fraction_max"]))
        accepted[i], over_frac[i], flat_frac[i] = acc, over, flat
        reasons.append(reason)
    if accepted.any():
        scale = float(np.median(np.abs(epochs[accepted])))
        if not np.isfinite(scale) or scale <= 1e-6:
            scale = 1.0
    else:
        scale = 1.0
    starts, wlen = window_starts(rate, pre_s, post_seconds, float(cfg(config, "window.length_seconds")),
                                 float(cfg(config, "window.step_seconds")))
    features = window_means(epochs / np.float32(scale), starts, wlen)  # [n, W, C]
    return {
        "features": features, "accepted": accepted, "qc_reason": np.asarray(reasons, dtype=object),
        "qc_over_fraction": over_frac.astype(np.float32), "qc_flat_fraction": flat_frac.astype(np.float32),
        "record_scale": scale, "window_starts": starts, "window_length": wlen,
        "window_centres_s": window_centres_s(starts, wlen, rate, pre_s),
        "trial_id": targets.trial_id.to_numpy(dtype=object),
        "y": targets.stimulus_local_id.to_numpy(dtype=np.int64),
        "onset_seconds": targets.onset_seconds.to_numpy(dtype=np.float64),
        "block_id": targets.block_id.to_numpy(dtype=np.int64),
        "previous_code": literal_to_class(targets.previous_code.to_numpy(dtype=object), codes),
        "previous_gap_s": targets.previous_gap_s.to_numpy(dtype=np.float64),
        "previous_run_length": targets.previous_run_length.to_numpy(dtype=object),
        "history_status": targets.history_status.to_numpy(dtype=object),
        "n_channels": int(data.shape[0]), "post_seconds": float(post_seconds),
    }


def save_features(out: dict, path: Path, *, record_id: str, lane: str, identity_group: str) -> None:
    prev_code = np.asarray(out["previous_code"], dtype=np.int64)
    prev_run = np.array([(-1 if v is None or (isinstance(v, float) and np.isnan(v)) else int(v))
                         for v in out["previous_run_length"]], dtype=np.int64)
    np.savez_compressed(
        path, features=out["features"], accepted=out["accepted"],
        qc_reason=out["qc_reason"].astype(str), qc_over_fraction=out["qc_over_fraction"],
        qc_flat_fraction=out["qc_flat_fraction"], record_scale=np.float64(out["record_scale"]),
        window_starts=out["window_starts"], window_length=np.int64(out["window_length"]),
        window_centres_s=out["window_centres_s"], trial_id=out["trial_id"].astype(str), y=out["y"],
        onset_seconds=out["onset_seconds"], block_id=out["block_id"], previous_code=prev_code,
        previous_gap_s=np.nan_to_num(out["previous_gap_s"], nan=-1.0), previous_run_length=prev_run,
        history_status=out["history_status"].astype(str), n_channels=np.int64(out["n_channels"]),
        post_seconds=np.float64(out["post_seconds"]), record_id=str(record_id), lane=str(lane),
        identity_group=str(identity_group))
    path.chmod(0o600)


def record_support(out: dict, config: dict) -> dict:
    """Outcome-blind support: accepted trials and 60-s blocks per class."""
    y, acc, blocks = out["y"], out["accepted"], out["block_id"]
    minimum = int(cfg(config, "qc.record_min_trials_per_class"))
    min_blocks = int(cfg(config, "qc.record_min_blocks_per_class"))
    per_class = {int(k): int(np.sum(acc & (y == k))) for k in np.unique(y)}
    blocks_per_class = {int(k): int(len(np.unique(blocks[acc & (y == k)]))) for k in np.unique(y)}
    classes = sorted(per_class)
    supported = (len(classes) == 2 and all(per_class[k] >= minimum for k in classes)
                 and all(blocks_per_class[k] >= min_blocks for k in classes))
    return {"accepted_per_class": per_class, "blocks_per_class": blocks_per_class,
            "n_supported_epochs": int(len(y)), "n_accepted": int(acc.sum()),
            "record_supported": bool(supported)}
