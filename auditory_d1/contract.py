"""D1 continuous-decoding export contract v1. Frozen before any export runs.

This is a NEW export version for continuous EEG decoding. It does not alter, reuse
or reinterpret the auditory5 `P1_CAUSAL_NATIVE` epoch export, whose causal filter and
[-0.2, 0.5) epoch grid exist for event-locked work. D1 produces no epochs and reads no
event file: the object is the ongoing recording.

Decisions, with reasons:

* Zero-phase filtering. Causal filtering exists in this repository to keep a strict
  pre-stimulus boundary for event-locked analysis. D1 has no events, so the reason does
  not apply, and a zero-phase response avoids the frequency-dependent group delay that
  would otherwise distort cross-band timing relations.
* Band 0.5-45 Hz. The auditory5 family stops at 30 Hz. D1 keeps up to 45 Hz because
  maturational descriptors of the aperiodic spectrum need a usable fit range above the
  alpha/beta peaks, and 45 Hz stays clear of the 50 Hz mains.
* 250 Hz by integer stride only. This repository has no verified resampler. 1000 -> 4,
  500 -> 2, 250 -> 1. Any other original rate is refused, not approximated.
* Average reference over all retained physical channels, applied after filtering and
  before decimation, with declared reference channels (VREF and friends) excluded from
  both the average and the output.
* Each stored interval is filtered independently. Filtering never spans a storage gap.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

CONTRACT_VERSION = "auditory_d1_continuous_v1"
TARGET_RATE_HZ = 250.0
HIGHPASS_HZ = 0.5
HIGHPASS_ORDER = 4
LOWPASS_HZ = 45.0
LOWPASS_ORDER = 8
PAD_SECONDS = 20.0
BLOCK_SECONDS = 120.0
MIN_INTERVAL_SECONDS = 60.0
SUPPORTED_RATES_HZ = (250.0, 500.0, 1000.0)
QC_BLOCK_SECONDS = 4.0
QC_PEAK_TO_PEAK_UV = 150.0
QC_FLAT_UV = 0.5


def stride_for(original_fs: float) -> int:
    """Integer decimation stride to TARGET_RATE_HZ, or refuse."""
    if original_fs not in SUPPORTED_RATES_HZ:
        raise ValueError(f"D1_UNSUPPORTED_RATE:{original_fs}")
    ratio = original_fs / TARGET_RATE_HZ
    stride = int(round(ratio))
    if abs(ratio - stride) > 1e-12 or stride < 1:
        raise ValueError(f"D1_NON_INTEGER_STRIDE:{original_fs}")
    return stride


def sos_for(original_fs: float) -> np.ndarray:
    """Butterworth SOS cascade applied with sosfiltfilt (zero phase)."""
    nyquist = original_fs / 2.0
    if LOWPASS_HZ >= nyquist:
        raise ValueError(f"D1_LOWPASS_ABOVE_NYQUIST:{original_fs}")
    high = signal.butter(HIGHPASS_ORDER, HIGHPASS_HZ / nyquist, btype="highpass", output="sos")
    low = signal.butter(LOWPASS_ORDER, LOWPASS_HZ / nyquist, btype="lowpass", output="sos")
    return np.concatenate([high, low], axis=0)


def filter_whole(data: np.ndarray, original_fs: float) -> np.ndarray:
    """Reference implementation: zero-phase filter an entire interval at once."""
    return signal.sosfiltfilt(sos_for(original_fs), np.asarray(data, dtype=np.float64), axis=-1)


def filter_blocked(data: np.ndarray, original_fs: float) -> np.ndarray:
    """Overlap-save zero-phase filtering with PAD_SECONDS discarded on each side.

    Produces the same result as `filter_whole` to numerical tolerance while holding
    only one padded block in memory. `d1_filter_agreement` in this module is the check.
    """
    array = np.asarray(data, dtype=np.float64)
    n = array.shape[-1]
    pad = int(round(PAD_SECONDS * original_fs))
    block = int(round(BLOCK_SECONDS * original_fs))
    if n <= block + 2 * pad:
        return filter_whole(array, original_fs)
    sos = sos_for(original_fs)
    out = np.empty_like(array)
    start = 0
    while start < n:
        stop = min(start + block, n)
        left = max(0, start - pad)
        right = min(n, stop + pad)
        filtered = signal.sosfiltfilt(sos, array[..., left:right], axis=-1)
        out[..., start:stop] = filtered[..., start - left:start - left + (stop - start)]
        start = stop
    return out


def d1_filter_agreement(seed: int = 20260919, seconds: float = 900.0,
                        original_fs: float = 1000.0, channels: int = 4) -> dict:
    """Blocked filtering must reproduce whole-interval filtering."""
    rng = np.random.default_rng(seed)
    n = int(seconds * original_fs)
    time = np.arange(n) / original_fs
    base = (rng.standard_normal((channels, n))
            + 8.0 * np.sin(2 * np.pi * 10.0 * time)[None, :]
            + 3.0 * np.sin(2 * np.pi * 0.2 * time)[None, :])
    whole = filter_whole(base, original_fs)
    blocked = filter_blocked(base, original_fs)
    difference = float(np.max(np.abs(whole - blocked)))
    scale = float(np.max(np.abs(whole)))
    return {"max_abs_difference": difference, "signal_scale": scale,
            "relative": difference / scale if scale else float("nan"),
            "status": "AGREE" if difference / max(scale, 1e-12) < 1e-9 else "DISAGREE"}


def average_reference(data: np.ndarray) -> np.ndarray:
    return data - data.mean(axis=0, keepdims=True)


def decimate(data: np.ndarray, stride: int) -> np.ndarray:
    """Integer stride after the 45 Hz low-pass has already removed alias energy."""
    return np.ascontiguousarray(data[..., ::stride])


def qc_blocks(data_uv: np.ndarray, rate_hz: float) -> dict:
    """Per-block channel health. Recorded, never used to drop samples at export time."""
    width = int(round(QC_BLOCK_SECONDS * rate_hz))
    n_blocks = data_uv.shape[-1] // width
    if n_blocks == 0:
        return {"n_blocks": 0}
    trimmed = data_uv[..., :n_blocks * width].reshape(data_uv.shape[0], n_blocks, width)
    peak = trimmed.max(axis=-1) - trimmed.min(axis=-1)
    over = (peak > QC_PEAK_TO_PEAK_UV).sum(axis=0)
    flat = (peak < QC_FLAT_UV).sum(axis=0)
    return {"n_blocks": int(n_blocks), "block_seconds": QC_BLOCK_SECONDS,
            "channels_over_threshold": over.astype(np.int16),
            "channels_flat": flat.astype(np.int16),
            "block_median_peak_to_peak_uv": np.median(peak, axis=0).astype(np.float32)}
