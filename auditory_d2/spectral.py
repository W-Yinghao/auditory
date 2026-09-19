"""Classical spectral arm: the anchor the learned arm has to beat.

Features are per-channel log band power plus log Hjorth descriptors, averaged over a
recording's usable windows. No events, no trial averaging, no peak picking.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

BANDS = ((0.5, 4.0), (4.0, 8.0), (8.0, 13.0), (13.0, 20.0), (20.0, 30.0), (30.0, 45.0))
BAND_NAMES = ("delta", "theta", "alpha", "low_beta", "high_beta", "gamma")


def window_features(window: np.ndarray, rate: float) -> np.ndarray:
    """[channels, samples] -> [channels, len(BANDS) + 3] log features."""
    nperseg = int(round(2.0 * rate))
    frequencies, psd = signal.welch(window, fs=rate, nperseg=nperseg,
                                    noverlap=nperseg // 2, window="hann", axis=-1)
    resolution = float(frequencies[1] - frequencies[0])
    powers = []
    for low, high in BANDS:
        mask = (frequencies >= low) & (frequencies < high)
        if high == BANDS[-1][1]:
            mask |= np.isclose(frequencies, high)
        powers.append(psd[..., mask].sum(axis=-1) * resolution)
    band = np.log(np.maximum(np.stack(powers, axis=-1), 1e-20))
    first = np.diff(window, axis=-1)
    second = np.diff(first, axis=-1)
    variance = np.maximum(window.var(axis=-1), 1e-20)
    mobility = np.sqrt(np.maximum(first.var(axis=-1), 1e-20) / variance)
    complexity = np.sqrt(np.maximum(second.var(axis=-1), 1e-20)
                         / np.maximum(first.var(axis=-1), 1e-20)) / mobility
    extra = np.log(np.stack([variance, mobility, np.maximum(complexity, 1e-20)], axis=-1))
    return np.concatenate([band, extra], axis=-1)


FEATURES_PER_CHANNEL = len(BANDS) + 3


def record_feature_matrix(store, scale: float, *, max_windows: int = 400,
                          minutes: float | None = None) -> np.ndarray:
    """[channels, FEATURES_PER_CHANNEL] averaged over a recording's usable windows.

    Every feature is a function of one channel alone, so the full-array matrix is
    computed once and any electrode subset is a row slice of it. Recomputing per subset
    would repeat identical work for every budget on the curve.
    """
    starts = store.starts
    if starts.size == 0:
        raise ValueError("D2_NO_USABLE_WINDOW")
    if minutes is not None:
        # Recording time is the binding constraint with young children, so the duration
        # axis keeps the EARLIEST usable windows rather than a spread sample: that is
        # what a shortened session would actually have produced.
        limit = int(round(minutes * 60.0 * store.rate))
        starts = starts[starts + store.window <= limit]
        if starts.size == 0:
            raise ValueError("D2_NO_WINDOW_WITHIN_MINUTES")
    if starts.size > max_windows:
        starts = starts[np.linspace(0, starts.size - 1, max_windows).astype(int)]
    total = None
    for start in starts:
        window = np.asarray(store.read(int(start)), dtype=np.float64) / float(scale)
        features = window_features(window, store.rate)
        total = features if total is None else total + features
    return total / starts.size


def subset_design(matrices: np.ndarray, channels: np.ndarray) -> np.ndarray:
    """[records, channels, features] -> [records, len(channels) * features]."""
    return matrices[:, np.asarray(channels, dtype=int), :].reshape(matrices.shape[0], -1)
