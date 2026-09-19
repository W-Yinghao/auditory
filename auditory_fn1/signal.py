"""Continuous 4-second window selection and the fixed 140-dimensional local features.

Plan sections 6.2-6.4. This module is explicit about what it INHERITS and what is NEW,
because the plan permits reuse of already-tested definitions but forbids presenting new
code as inherited verification.

INHERITED (imported, not re-derived) from auditory5.preprocessing / auditory5.adapters.ha:
  * HA_CHANNELS            canonical 20-channel order; no interpolation, no dynamic selection
  * fixed_sos              causal Butterworth SOS, HP order 4 @ 0.5 Hz then LP order 8 @ 30 Hz
  * CausalPreprocessor     select 20 -> average reference -> causal sosfilt with carried
                           state -> integer-stride decimation on a fixed grid
  * effective_impulse_support  measured filter support and the max(20 s, support) guard
  * vendor rail rule       saturation = within one digital LSB of either physical rail,
                           read from the BDF signal header (never a guessed microvolt)

NEW IN THIS MODULE (no prior implementation existed anywhere in the repository):
  * fixed-grid, event-independent 4-second window selection
  * Welch band power (2 s Hann, 50 % overlap) and the 80 band-power dimensions
  * Hjorth at a caller-supplied sampling rate. The existing implementation in
    auditory_fseries/data.py hard-codes 250.0 in the mobility conversion, so it is
    correct only at 250 Hz; here the rate is a parameter and is recorded.

KNOWN GAP, deliberately surfaced rather than silently assumed:
  The repository has NO acquisition-gap / discontinuity detection for HA BDF. Every
  executed HA run has treated the record as one continuous interval [0, n_samples).
  `select_windows` therefore REQUIRES the caller to pass the intervals explicitly and
  records `interval_source`, so a receipt can never imply a verification that does not
  exist. Passing a single whole-record interval is allowed but is labelled
  `assumed_single_interval_unverified`.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy.signal import welch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from auditory5.preprocessing import HA_CHANNELS, effective_impulse_support, fixed_sos  # noqa: E402

CANONICAL_CHANNELS = tuple(HA_CHANNELS)
N_CHANNELS = len(CANONICAL_CHANNELS)
INHERITED_SOURCES = {
    "channels": "auditory5.preprocessing.HA_CHANNELS",
    "filter": "auditory5.preprocessing.fixed_sos (Butterworth SOS, HP4@0.5 Hz, LP8@30 Hz, causal sosfilt)",
    "support_and_guard": "auditory5.preprocessing.effective_impulse_support",
    "reference_and_decimation": "auditory5.preprocessing.CausalPreprocessor",
    "saturation": "auditory5.adapters.ha vendor digital-rail rule",
}
NEW_IMPLEMENTATIONS = ("fixed_grid_4s_window_selection", "welch_band_power", "hjorth_at_parameterised_rate")


# --------------------------------------------------------------------- window selection


def select_windows(intervals: Sequence[Sequence[int]], *, processed_fs: float, guard_seconds: float,
                   window_seconds: float, count: int, interval_source: str) -> dict:
    """Chronological, uniform, non-overlapping window selection without replacement.

    `intervals` are half-open [start, stop) sample indices on the PROCESSED grid. Guards
    are removed from both ends of EVERY interval, and no window may straddle a boundary.
    """
    if interval_source not in ("verified_storage_intervals", "assumed_single_interval_unverified"):
        raise ValueError("INTERVAL_SOURCE_MUST_BE_DECLARED")
    window_samples = int(round(window_seconds * processed_fs))
    guard_samples = int(np.ceil(guard_seconds * processed_fs))
    if window_samples <= 0:
        raise ValueError("WINDOW_LENGTH_INVALID")
    candidates: list[tuple[int, int]] = []
    for start, stop in intervals:
        start, stop = int(start), int(stop)
        if stop <= start:
            raise ValueError("INTERVAL_NOT_HALF_OPEN")
        lo, hi = start + guard_samples, stop - guard_samples
        position = lo
        while position + window_samples <= hi:
            candidates.append((position, position + window_samples))
            position += window_samples
    candidates.sort()
    selected: list[tuple[int, int]] = []
    if len(candidates) >= count and count > 0:
        # Uniform indices over the chronological candidate list; no randomness, no
        # replacement, and no dependence on any signal or target value.
        picks = np.unique(np.linspace(0, len(candidates) - 1, num=count).round().astype(int))
        while picks.size < count:
            missing = [i for i in range(len(candidates)) if i not in set(picks.tolist())]
            picks = np.sort(np.concatenate([picks, np.array(missing[: count - picks.size], dtype=int)]))
        selected = [candidates[i] for i in picks[:count]]
    return {
        "window_samples": window_samples,
        "guard_samples": guard_samples,
        "n_candidate_windows": len(candidates),
        "n_selected": len(selected),
        "selected": selected,
        "sufficient": len(candidates) >= count,
        "interval_source": interval_source,
        "selection_rule": "chronological_uniform_without_replacement",
    }


# --------------------------------------------------------------------- local features


def band_power(window: np.ndarray, *, fs: float, bands: Sequence[Sequence[float]],
               welch_seconds: float, overlap_fraction: float, floor: float) -> tuple[np.ndarray, int]:
    """Absolute band power per channel via Welch, integrated as PSD x frequency spacing.

    Bins are left-closed / right-open; the last band additionally includes its upper
    edge, so no bin is counted twice and 30 Hz is not dropped.
    """
    window = np.asarray(window, dtype=float)
    if window.ndim != 2 or window.shape[0] != N_CHANNELS:
        raise ValueError("WINDOW_MUST_BE_20_CHANNELS_BY_SAMPLES")
    nperseg = int(round(welch_seconds * fs))
    noverlap = int(round(nperseg * overlap_fraction))
    if nperseg > window.shape[1]:
        raise ValueError("WELCH_SEGMENT_LONGER_THAN_WINDOW")
    freqs, psd = welch(window, fs=fs, window="hann", nperseg=nperseg, noverlap=noverlap,
                       detrend="constant", scaling="density", axis=-1)
    spacing = float(freqs[1] - freqs[0])
    powers = np.empty((N_CHANNELS, len(bands)), dtype=float)
    for index, (low, high) in enumerate(bands):
        if index == len(bands) - 1:
            mask = (freqs >= low) & (freqs <= high)
        else:
            mask = (freqs >= low) & (freqs < high)
        powers[:, index] = psd[:, mask].sum(axis=-1) * spacing
    truncated = int(np.count_nonzero(powers < floor))
    return np.log(np.maximum(powers, floor)), truncated


def hjorth(window: np.ndarray, *, fs: float, floor: float) -> tuple[np.ndarray, int]:
    """log activity, log mobility, log complexity per channel, at the given rate.

    The sampling-rate factor is explicit here; the historical implementation in
    auditory_fseries/data.py hard-codes 250.0 and is therefore rate-specific.
    """
    window = np.asarray(window, dtype=float)
    if window.ndim != 2 or window.shape[0] != N_CHANNELS:
        raise ValueError("WINDOW_MUST_BE_20_CHANNELS_BY_SAMPLES")
    centred = window - window.mean(axis=-1, keepdims=True)
    d1 = np.diff(centred, axis=-1)
    d2 = np.diff(d1, axis=-1)
    var0 = centred.var(axis=-1)
    var1 = d1.var(axis=-1)
    var2 = d2.var(axis=-1)
    safe0 = np.maximum(var0, floor)
    safe1 = np.maximum(var1, floor)
    mobility = np.sqrt(safe1 / safe0) * float(fs)
    complexity = np.sqrt(np.maximum(var2, floor) / safe1) * float(fs) / np.maximum(mobility, floor)
    stacked = np.column_stack([np.maximum(var0, floor), np.maximum(mobility, floor), np.maximum(complexity, floor)])
    truncated = int(np.count_nonzero(var0 < floor) + np.count_nonzero(var1 < floor) + np.count_nonzero(var2 < floor))
    return np.log(stacked), truncated


def window_features(window: np.ndarray, *, fs: float, feature_config: dict) -> tuple[np.ndarray, dict]:
    """The frozen 140-dimensional vector: 80 log band powers then 60 log Hjorth terms."""
    floor = float(feature_config["log_floor"])
    powers, truncated_power = band_power(window, fs=fs, bands=feature_config["bands_hz"],
                                         welch_seconds=float(feature_config["welch_window_seconds"]),
                                         overlap_fraction=float(feature_config["welch_overlap_fraction"]),
                                         floor=floor)
    hj, truncated_hjorth = hjorth(window, fs=fs, floor=floor)
    vector = np.concatenate([powers.reshape(-1), hj.reshape(-1)])
    if vector.size != 140:
        raise ValueError(f"FEATURE_DIM_CONTRACT:{vector.size}")
    if not np.all(np.isfinite(vector)):
        raise ValueError("NONFINITE_FEATURE_VECTOR")
    return vector, {"floor_truncated_band_power": truncated_power, "floor_truncated_hjorth": truncated_hjorth}


# --------------------------------------------------------------------- window quality


def window_quality(raw_window: np.ndarray, processed_window: np.ndarray, *, rails: Sequence[Sequence[float]] | None,
                   flat_ptp_uv: float, peak_to_peak_uv: float, maximum_channels_above_ptp: int) -> dict:
    """Frozen 4-second window QC (plan section 6.3). New rule; not equivalent to the old epoch QC."""
    reasons: list[str] = []
    raw_window = np.asarray(raw_window, dtype=float)
    processed_window = np.asarray(processed_window, dtype=float)
    if not np.all(np.isfinite(raw_window)) or not np.all(np.isfinite(processed_window)):
        reasons.append("nonfinite")
    if np.any(np.ptp(raw_window, axis=-1) < flat_ptp_uv):
        reasons.append("raw_flat")
    if rails is not None:
        for channel, (physical_min, physical_max, delta) in enumerate(rails):
            x = raw_window[channel]
            if np.any((x <= physical_min + delta) | (x >= physical_max - delta)):
                reasons.append("raw_saturation")
                break
    above = int(np.count_nonzero(np.ptp(processed_window, axis=-1) > peak_to_peak_uv))
    if above > int(maximum_channels_above_ptp):
        reasons.append("processed_ptp_channels")
    return {"accepted": not reasons, "reasons": sorted(set(reasons)), "channels_above_ptp": above}


def inherited_support(original_fs: float, minimum_guard_seconds: float) -> dict:
    """Report the inherited measured filter support and guard for the receipt."""
    support = effective_impulse_support(original_fs, minimum_guard_seconds=minimum_guard_seconds)
    sos = fixed_sos(original_fs)
    return {
        "original_fs": float(original_fs),
        "sos_sections": int(sos.shape[0]),
        "support_samples": int(support.support_samples),
        "support_seconds": float(support.support_seconds),
        "guard_samples": int(support.guard_samples),
        "guard_seconds": float(support.guard_seconds),
        "inherited_from": INHERITED_SOURCES["filter"],
    }
