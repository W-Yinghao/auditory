"""Pure numerical helpers for the fixed Phase 1 measurement protocol."""
import numpy as np


def epoch_grid(sfreq, tmin, tmax, decimation=1):
    first, last = int(round(tmin*sfreq)), int(round(tmax*sfreq))
    offsets = np.arange(first, last+1, dtype=np.int64)
    # Decimation is anchored at event time zero, even if tmin changes.
    selected = offsets % decimation == 0
    return offsets, selected, offsets[selected] / sfreq


def reference(data, scalp_indices, ear_indices):
    scalp = data[scalp_indices]
    return scalp - scalp.mean(axis=0, keepdims=True), scalp - data[ear_indices].mean(axis=0, keepdims=True)


def baseline(data, times, interval):
    mask = (times >= interval[0]-1e-10) & (times < interval[1]-1e-10)
    if not mask.any(): raise ValueError('empty_baseline')
    return data - data[..., mask].mean(axis=-1, keepdims=True)


def block_bootstrap_scores(scores, codes, blocks, repetitions, rng):
    """Joint block bootstrap: resample occupied blocks, retain all trials in block.

    Columns are condition 1, condition 2, condition 2 minus condition 1.
    Empty condition draws remain NaN and must be counted by the caller.
    """
    unique = np.unique(blocks)
    sums = np.zeros((len(unique), 2, scores.shape[1]))
    counts = np.zeros((len(unique), 2))
    for i, block in enumerate(unique):
        for j, code in enumerate((1, 2)):
            chosen = (blocks == block) & (codes == code)
            counts[i, j] = chosen.sum()
            sums[i, j] = scores[chosen].sum(axis=0)
    draws = rng.integers(0, len(unique), size=(repetitions, len(unique)))
    numerator = sums[draws].sum(axis=1)
    denominator = counts[draws].sum(axis=1)
    means = np.divide(numerator, denominator[..., None],
                      out=np.full_like(numerator, np.nan), where=denominator[..., None] > 0)
    return np.concatenate([means, (means[:, 1]-means[:, 0])[:, None]], axis=1)


def waveform_comparison(a, b):
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        corr = np.nan
    else:
        corr = float(np.corrcoef(a, b)[0, 1])
    return corr, float(np.sqrt(np.mean((a-b)**2)))


def ear_reference_valid(accepted, saturation, persistent_flat):
    accepted = np.asarray(accepted,dtype=bool)
    saturation = np.asarray(saturation,dtype=bool)
    if accepted.shape != saturation.shape: raise ValueError('ear_QC_epoch_alignment')
    return not persistent_flat and not np.any(accepted & saturation)
