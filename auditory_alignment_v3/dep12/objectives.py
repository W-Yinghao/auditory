"""Thin wrappers over the package reference objectives (training_objectives_torch.py is a byte copy of the package file).

One call = one listener episode and one view: u [n, 32] L2 rows (EEG projector output, with gradient), y [n, 32] L2 rows
(fixed audio head, no gradient). The sampler guarantees that every off-diagonal pair is a legal negative; no mask is applied.
  cs_pair        centered_cs(u, y, permutations=P)            -(D(K,L) - mean_b D(K, P_b L P_b^T)), null NOT detached
  raw_cs         raw_cs(u, y)                                 -D(K,L)
  info_nce       symmetric_info_nce(u, y, temperature=0.07)
  sigmoid        sigmoid_pair_loss(u, y, temperature=0.07)    bias = -log(n-1) (reference default)
  cs_pair_wrong  centered_cs(u, y[w], permutations=P)         EEG row i is paired with audio w[i]; the references pair it with
                                                              w[P_b[i]]; w and every w o P_b are fixed-point free and w != P_b
Views are weighted 1/3 and the two listeners 1/2 by the trainer.
"""
from __future__ import annotations

import numpy as np

from . import training_objectives_torch as T

OBJECTIVES = ('cs_pair', 'info_nce', 'sigmoid', 'raw_cs', 'cs_pair_wrong')
TEMPERATURE = 0.07
REFERENCE_SHA256 = 'd5116dec303aa6dba4a2f5493540ce2372d92cc0d7792a540fb62c1c96cf7f91'
USES_SIGMA = ('cs_pair', 'raw_cs', 'cs_pair_wrong')


def check_wrong(wrong, perms):
    w = np.asarray(wrong, np.int64); P = np.asarray(perms, np.int64); ar = np.arange(len(w))
    assert sorted(w.tolist()) == ar.tolist() and not np.any(w == ar), 'wrong map must be a derangement'
    assert not any(np.array_equal(w, p) for p in P), 'wrong map equals a reference mismatch'
    assert not any(np.any(w[p] == ar) for p in P), 'a reference mismatch restores a true pair under the wrong map'


def episode_loss(objective, u, y, *, sigma_u=None, sigma_y=None, perms=None, wrong=None):
    """(loss, detached stats) for one listener episode and one view."""
    import torch
    if objective == 'cs_pair':
        return T.centered_cs(u, y, sigma_u=sigma_u, sigma_y=sigma_y, permutations=perms)
    if objective == 'raw_cs':
        return T.raw_cs(u, y, sigma_u=sigma_u, sigma_y=sigma_y)
    if objective == 'info_nce':
        return T.symmetric_info_nce(u, y, temperature=TEMPERATURE)
    if objective == 'sigmoid':
        return T.sigmoid_pair_loss(u, y, temperature=TEMPERATURE)
    if objective == 'cs_pair_wrong':
        check_wrong(wrong, perms)
        idx = torch.as_tensor(np.asarray(wrong, np.int64), device=y.device)
        loss, st = T.centered_cs(u, y.index_select(0, idx), sigma_u=sigma_u, sigma_y=sigma_y, permutations=perms)
        st = dict(st, positive_pairing='independent_wrong_derangement', wrong_map_fixed_points=0)
        return loss, st
    raise ValueError(objective)


STAT_KEYS = ('loss', 'raw_cs_nats', 'training_null_mean_nats', 'centered_cs_nats', 'loss_eeg_to_audio', 'loss_audio_to_eeg',
             'n_unique_permutations', 'null_fixed_pair_fraction')


def compact(st):
    return {k: st[k] for k in STAT_KEYS if k in st}
