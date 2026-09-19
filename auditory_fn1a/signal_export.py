"""Real continuous HA BDF -> causal 0.5-30 Hz -> 250 Hz -> fixed 4 s windows -> 140 dims.

Plan section 6. Inherited, not re-derived: the canonical 20-channel order, the causal
Butterworth SOS (HP order 4 @ 0.5 Hz, LP order 8 @ 30 Hz) applied with carried state,
the average reference taken over exactly those 20 channels before filtering, the
integer-stride decimation on a fixed grid, and the vendor digital-rail saturation rule
read from the BDF signal header. New here: the fixed-grid event-independent 4 s window
selection, the Welch band power, and the Hjorth terms at a supplied rate.

Two honesty requirements the plan imposes and this module enforces:

* The raw root is owner-writable, so "read-only" cannot be delegated to the filesystem.
  Every record is stat-ed before and after and a change raises.
* This repository has no acquisition-gap detection for HA BDF. The single continuous
  interval is therefore recorded as an ASSUMPTION with its header-level evidence
  (byte/record agreement, zero annotations in the signal file), never as a verified
  storage-interval decomposition.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

from auditory_fn1.signal import band_power, hjorth, select_windows, window_features, window_quality
from auditory5.preprocessing import HA_CHANNELS, CausalPreprocessor, effective_impulse_support

from .runtime import ROOT, ProvenanceError, digest, require_config_value, resolve_source

CHUNK_SECONDS = 60.0


def _path_map(config: dict) -> dict[str, str]:
    path = resolve_source(config, "file_path_map")
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["file_id"]: row["absolute_path"] for row in csv.DictReader(handle)}


def _stat(path: Path) -> tuple[int, int]:
    info = path.stat()
    return info.st_size, info.st_mtime_ns


def stream_record(signal_path: Path, *, expected_fs: float | None, guard_seconds: float) -> dict:
    """Read one BDF, apply the inherited causal chain, return the processed 20xN array."""
    import pyedflib

    before = _stat(signal_path)
    with pyedflib.EdfReader(str(signal_path)) as reader:
        labels = list(reader.getSignalLabels())
        if len(set(labels)) != len(labels) or not set(HA_CHANNELS) <= set(labels):
            raise ProvenanceError("HA_CHANNEL_CONTRACT")
        rates = reader.getSampleFrequencies()
        if not np.all(rates == rates[0]):
            raise ProvenanceError("HA_MIXED_SAMPLE_RATES")
        original_fs = float(rates[0])
        if expected_fs is not None and abs(original_fs - expected_fs) > 1e-9:
            raise ProvenanceError(f"HA_SOURCE_RATE_CHANGED:{original_fs}!={expected_fs}")
        n_samples = int(reader.getNSamples()[0])
        headers = reader.getSignalHeaders()
        canonical = [labels.index(name) for name in HA_CHANNELS]
        for index in canonical:
            if headers[index]["dimension"] != "uV":
                raise ProvenanceError("HA_SOURCE_UNIT_CHANGED")
        rails = [(float(headers[i]["physical_min"]), float(headers[i]["physical_max"]),
                  (float(headers[i]["physical_max"]) - float(headers[i]["physical_min"]))
                  / (float(headers[i]["digital_max"]) - float(headers[i]["digital_min"])))
                 for i in canonical]

        support = effective_impulse_support(original_fs, minimum_guard_seconds=guard_seconds)
        processor = CausalPreprocessor(original_fs, labels, bank="P1_CAUSAL20", support=support)
        raw20 = np.empty((len(HA_CHANNELS), n_samples), dtype=np.float64)
        processed_parts: list[np.ndarray] = []
        source_parts: list[np.ndarray] = []
        chunk = int(CHUNK_SECONDS * original_fs)
        for start in range(0, n_samples, chunk):
            stop = min(n_samples, start + chunk)
            block = np.stack([reader.readSignal(k, start=start, n=stop - start) for k in range(len(labels))])
            if not np.isfinite(block).all():
                raise ProvenanceError("NONFINITE_SOURCE_NO_IMPLICIT_REPAIR")
            raw20[:, start:stop] = block[canonical]
            out = processor.process(block, start_sample=start)
            processed_parts.append(out.data["all"])
            source_parts.append(out.source_samples)
    after = _stat(signal_path)
    if before != after:
        raise ProvenanceError("SOURCE_CHANGED_DURING_EXPORT")

    processed = np.concatenate(processed_parts, axis=1)
    source_samples = np.concatenate(source_parts)
    if processed.shape[0] != len(HA_CHANNELS) or processed.shape[1] != source_samples.size:
        raise ProvenanceError("PROCESSED_SHAPE_MISMATCH")
    return {
        "processed": processed,
        "raw20": raw20,
        "source_samples": source_samples,
        "original_fs": original_fs,
        "processed_fs": float(processor.processed_fs),
        "decimation_factor": int(processor.decimation_factor),
        "n_samples_original": n_samples,
        "rails": rails,
        "support_seconds": float(support.support_seconds),
        "guard_seconds": float(support.guard_seconds),
        "channels": list(HA_CHANNELS),
        "source_sha256": digest(signal_path),
        "source_bytes": before[0],
    }


def qualify_and_select(stream: dict, config: dict) -> dict:
    """QC every candidate 4 s window, then take 32 uniformly from the qualified ones."""
    signal_config = require_config_value(config, "signal")
    processed_fs = stream["processed_fs"]
    window_samples = int(round(float(signal_config["window_seconds"]) * processed_fs))
    guard = float(signal_config["guard_seconds_min"])
    total = stream["processed"].shape[1]

    # Header-level evidence supports one continuous interval; the repository has no HA
    # gap detection, so the provenance of that interval is declared as an assumption.
    candidates = select_windows([[0, total]], processed_fs=processed_fs, guard_seconds=guard,
                                window_seconds=float(signal_config["window_seconds"]),
                                count=10 ** 9, interval_source="assumed_single_interval_unverified")
    grid = candidates["selected"] or []
    if not grid:
        # select_windows returns [] when it cannot satisfy `count`; rebuild the full grid.
        guard_samples = int(np.ceil(guard * processed_fs))
        grid = [(p, p + window_samples) for p in range(guard_samples, total - guard_samples - window_samples + 1, window_samples)]

    decimation = stream["decimation_factor"]
    qualified: list[tuple[int, int]] = []
    reasons: dict[str, int] = {}
    for start, stop in grid:
        raw_lo = int(stream["source_samples"][start])
        raw_hi = raw_lo + window_samples * decimation
        if raw_hi > stream["raw20"].shape[1]:
            reasons["raw_window_out_of_range"] = reasons.get("raw_window_out_of_range", 0) + 1
            continue
        verdict = window_quality(stream["raw20"][:, raw_lo:raw_hi], stream["processed"][:, start:stop],
                                 rails=stream["rails"],
                                 flat_ptp_uv=float(signal_config["flat_ptp_uv"]),
                                 peak_to_peak_uv=float(signal_config["peak_to_peak_uv"]),
                                 maximum_channels_above_ptp=int(signal_config["maximum_channels_above_ptp"]))
        if verdict["accepted"]:
            qualified.append((start, stop))
        else:
            for reason in verdict["reasons"]:
                reasons[reason] = reasons.get(reason, 0) + 1

    wanted = int(signal_config["windows_per_record"])
    selected: list[tuple[int, int]] = []
    if len(qualified) >= wanted:
        picks = np.unique(np.linspace(0, len(qualified) - 1, num=wanted).round().astype(int))
        cursor = 0
        while picks.size < wanted:
            if cursor not in picks:
                picks = np.sort(np.append(picks, cursor))
            cursor += 1
        selected = [qualified[i] for i in picks[:wanted]]
    return {
        "n_candidate_windows": len(grid),
        "n_qualified_windows": len(qualified),
        "n_selected": len(selected),
        "selected": selected,
        "reject_reason_counts": reasons,
        "sufficient": len(qualified) >= wanted,
        "window_samples": window_samples,
        "interval_source": "assumed_single_interval_unverified",
        "interval_evidence": ("BDF header: integer data records at 1 s, file bytes equal the declared "
                              "record concatenation, zero annotations in the signal file; the repository "
                              "has no HA acquisition-gap detector, so this is an assumption, not a "
                              "verified storage-interval decomposition."),
    }


def features_for(stream: dict, selection: dict, config: dict) -> tuple[np.ndarray, dict]:
    feature_config = require_config_value(config, "features")
    vectors = []
    truncated = {"floor_truncated_band_power": 0, "floor_truncated_hjorth": 0}
    for start, stop in selection["selected"]:
        vector, diagnostics = window_features(stream["processed"][:, start:stop],
                                              fs=stream["processed_fs"], feature_config=feature_config)
        vectors.append(vector)
        for key in truncated:
            truncated[key] += int(diagnostics[key])
    matrix = np.asarray(vectors, dtype=np.float64)
    if matrix.shape != (int(require_config_value(config, "signal.windows_per_record")),
                        int(require_config_value(config, "signal.feature_dim"))):
        raise ProvenanceError(f"FEATURE_MATRIX_SHAPE:{matrix.shape}")
    return matrix, truncated


def technical_summary(stream: dict, selection: dict) -> dict:
    """Q: acquisition-process summary only. No model output, no subject id, no target mask."""
    selected = selection["selected"]
    amplitude = float(np.median([np.median(np.ptp(stream["processed"][:, a:b], axis=-1)) for a, b in selected])) if selected else float("nan")
    duration = stream["n_samples_original"] / stream["original_fs"]
    return {
        "log1p_source_duration_s": float(np.log1p(duration)),
        "log1p_candidate_windows": float(np.log1p(selection["n_candidate_windows"])),
        "qualified_window_fraction": (selection["n_qualified_windows"] / selection["n_candidate_windows"]
                                      if selection["n_candidate_windows"] else 0.0),
        "log_saturation_rejects": float(np.log1p(selection["reject_reason_counts"].get("raw_saturation", 0))),
        "log_flat_rejects": float(np.log1p(selection["reject_reason_counts"].get("raw_flat", 0))),
        "log_ptp_rejects": float(np.log1p(selection["reject_reason_counts"].get("processed_ptp_channels", 0))),
        # Amplitude sensitivity variable, kept OUT of the main technical block.
        "amplitude_log_median_scalp_ptp": float(np.log(max(amplitude, 1e-12))),
    }


TECHNICAL_COLUMNS = ("log1p_source_duration_s", "log1p_candidate_windows", "qualified_window_fraction",
                     "log_saturation_rejects", "log_flat_rejects", "log_ptp_rejects")
AMPLITUDE_COLUMN = "amplitude_log_median_scalp_ptp"
