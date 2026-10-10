"""ALN2 audio reference heads (package docs/04 §4.6). Input A[t] = 8 target frames x D dims, flattened (8D).

fixed_features  : training-side standardised target features, then a fixed semi-orthogonal projection to d (seeded per
                  cohort, identical for every unit of that cohort), L2-normalised. EEG learns to read a fixed object.
frozen_random   : the previous round's MLP head at random initialisation, frozen (replicates the E5 intervention).
trainable_head  : the previous round's free MLP projection (reference).
anchored_head   : trainable MLP plus a linear decoder that reconstructs the standardised features (MSE weight lambda,
                  chosen on the training side); the decoder loss is returned by aux_loss().
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

COHORT_SEED = {"fau": 20261006, "dtu": 20261007, "federici": 20261008, "private_bdf": 20261009}


def semi_orthogonal(d, n, seed):
    """[d, n] matrix with orthonormal rows (n >= d) or orthonormal columns (n < d)."""
    g = np.random.default_rng(seed).standard_normal((max(d, n), min(d, n)))
    q, _ = np.linalg.qr(g)  # [max, min] orthonormal columns
    return torch.tensor(q.T if n >= d else q, dtype=torch.float32)  # n>=d: [d, n] rows orthonormal; else [d, n] cols


class Standardiser(nn.Module):
    def __init__(self, mu, sd):
        super().__init__()
        self.register_buffer("mu", torch.as_tensor(mu, dtype=torch.float32))
        self.register_buffer("sd", torch.as_tensor(sd, dtype=torch.float32))

    def forward(self, a):
        return (a - self.mu) / self.sd


class FixedFeatureHead(nn.Module):
    def __init__(self, in_dim, d, mu, sd, cohort):
        super().__init__()
        self.std = Standardiser(mu, sd)
        self.register_buffer("P", semi_orthogonal(d, in_dim, COHORT_SEED[cohort]))

    def forward(self, a):
        return F.normalize(self.std(a) @ self.P.T, dim=1)


class MLPHead(nn.Module):
    def __init__(self, in_dim, d, frozen=False, anchored=False, mu=None, sd=None):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_dim, 32), nn.GELU(), nn.Linear(32, d))
        self.anchored = anchored
        if anchored:
            self.std = Standardiser(mu, sd)
            self.dec = nn.Linear(d, in_dim)
        if frozen:
            for p in self.net.parameters():
                p.requires_grad_(False)
        self._last = None

    def forward(self, a):
        z = self.net(a)
        if self.anchored and self.training:
            self._last = (z, a)
        return F.normalize(z, dim=1)

    def aux_loss(self):
        """Reconstruction of the standardised target from the (un-normalised) head output of the last forward."""
        if not self.anchored or self._last is None:
            return None
        z, a = self._last
        self._last = None
        return F.mse_loss(self.dec(z), self.std(a))


def target_stats(bt, rng, n_seg=400):
    """Training-side mean / sd of the flattened 8-frame target over fit anchors of training participants."""
    segs = [bt.fit[i] for i in rng.choice(len(bt.fit), size=min(n_seg, len(bt.fit)), replace=False)]
    s0 = np.array([bt.coh_segments[i]["s0"] for i in segs])
    offs = np.arange(0, bt.seg_len, 8)
    idx = torch.tensor((s0[:, None] + offs[None]).reshape(-1), device=bt.dev)
    with torch.no_grad():
        A = bt.audio(idx)
    return A.mean(0).cpu().numpy(), (A.std(0) + 1e-6).cpu().numpy()


def build_head(kind, in_dim, d, cohort, stats=None):
    mu, sd = stats if stats is not None else (None, None)
    if kind == "fixed_features":
        return FixedFeatureHead(in_dim, d, mu, sd, cohort)
    if kind == "frozen_random":
        return MLPHead(in_dim, d, frozen=True)
    if kind == "trainable_head":
        return MLPHead(in_dim, d)
    if kind == "anchored_head":
        return MLPHead(in_dim, d, anchored=True, mu=mu, sd=sd)
    raise ValueError(kind)
