"""Query-aligned window reference with explicit segment and record boundaries.

This does not load EEG. It does not assume adjacent files belong to one record.
"""
from __future__ import annotations
import numpy as np


def support_counts(fs: float, pre_s: float = .4, post_s: float = .6) -> dict:
    if not np.isfinite(fs) or fs <= 0 or min(pre_s, post_s) < 0:
        raise ValueError('Invalid sample rate or time support')
    pre, post = int(round(fs * pre_s)), int(round(fs * post_s))
    if pre + post < 1:
        raise ValueError('Empty support')
    return {'pre_samples': pre, 'post_samples': post,
            'n_samples': pre + post,
            'nominal_seconds': [-pre_s, post_s],
            'actual_half_open_ms': [-1000 * pre / fs, 1000 * post / fs]}


def aligned_windows(eeg: np.ndarray, segment_starts: np.ndarray,
                    query_offsets: np.ndarray, pre: int, post: int,
                    record_bounds: np.ndarray, right_policy: str = 'error',
                    post_only: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """eeg[C,N], starts[B], offsets[B,Q], bounds[B,2] -> W[B,Q,C,L], mask[B,Q,L].

    Negative offsets relative to segment start are zero, matching ADDENDUM_06.
    Actual record bounds are mandatory. Out-of-record right access either raises
    or is explicitly zero-padded; it never reads a neighboring record's data.
    """
    x = np.asarray(eeg)
    starts = np.asarray(segment_starts)
    q = np.asarray(query_offsets)
    bounds = np.asarray(record_bounds)
    if x.ndim != 2 or starts.ndim != 1 or q.ndim != 2 or q.shape[0] != len(starts):
        raise ValueError('Expected [C,N], [B], [B,Q]')
    if not np.isfinite(x).all():
        raise ValueError('Non-finite EEG')
    if bounds.shape != (len(starts), 2) or pre < 0 or post < 1:
        raise ValueError('Bounds or window invalid')
    for z in (starts, q, bounds):
        if not np.issubdtype(z.dtype, np.integer):
            raise ValueError('Use integer physical sample coordinates')
    if (q < 0).any() or (bounds[:,0] < 0).any() or (bounds[:,1] > x.shape[1]).any():
        raise ValueError('Invalid query or record bounds')
    if (bounds[:,0] >= bounds[:,1]).any() or (starts < bounds[:,0]).any() or (starts >= bounds[:,1]).any():
        raise ValueError('Segment starts must lie in their records')
    if right_policy not in ('error', 'zero'):
        raise ValueError('Unknown right policy')
    rel = q[:,:,None] - pre + np.arange(pre + post)[None,None,:]
    absolute = starts[:,None,None] + rel
    bad_right = absolute >= bounds[:,1,None,None]
    if right_policy == 'error' and bad_right.any():
        raise ValueError('Requested EEG extends beyond true record')
    valid = (rel >= 0) & (absolute >= bounds[:,0,None,None]) & ~bad_right
    if post_only:
        valid &= np.arange(pre + post)[None,None,:] >= pre
    safe_idx = np.clip(absolute, 0, x.shape[1]-1)
    out = x[:, safe_idx].transpose(1,2,0,3).copy()
    out *= valid[:,:,None,:]
    return out, valid


def require_equal_access(mask_a: np.ndarray, indices_a: np.ndarray,
                         mask_b: np.ndarray, indices_b: np.ndarray) -> None:
    """Per-query equality of real sample sets, not merely equal nominal ms labels."""
    ma, mb = np.asarray(mask_a, bool), np.asarray(mask_b, bool)
    ia, ib = np.asarray(indices_a), np.asarray(indices_b)
    if ma.shape != ia.shape or mb.shape != ib.shape or ma.shape[:-1] != mb.shape[:-1]:
        raise ValueError('Masks/indices need matching query axes')
    for a, am, b, bm in zip(ia.reshape(-1, ia.shape[-1]), ma.reshape(-1, ma.shape[-1]),
                           ib.reshape(-1, ib.shape[-1]), mb.reshape(-1, mb.shape[-1])):
        if not np.array_equal(np.unique(a[am]), np.unique(b[bm])):
            raise ValueError('Real EEG access differs')
