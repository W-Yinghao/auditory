"""ALN2 C_ADAPT: shared model + personal support adaptation (package docs/05 §5.2 G2, study.json personal_support).

Base model (same outer fold / content fold / seed / objective; checkpoint of a completed unit):
  density_tokens : A_TIME density_tokens full-window fixed_features unit (FAU / DTU); D_TASK_LOCAL density_tokens full (private)
  cbramod        : B_FM cbramod pretrained_peft unit (FAU / DTU); D_FM_GENERIC cbramod pretrained_peft unit (private)
Per test participant, data in recording order: support = first 10% or 30%, query = the last 70% (identical query for every
support fraction and adapter kind). Adapters (base frozen): none; spatial_adapter (input C x C map, identity init);
personal_low_rank (rank-4 residual on the output embedding, zero init). Updates use the unit's own objective on the
support pairs (known sounds / known stimulus classes); the number of steps is chosen on TRAINING participants only
(their early-stopping content split the same way) from {20, 50, 100}. This is individual adaptation, not zero-shot.
Query evaluation: continuous - true vs within-query mismatched EEG over the full test candidate pool with the readouts
fitted on training participants with the base model (unified ridge and native); private - task-native head metrics.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

STEP_CANDIDATES = (20, 50, 100)
FRACTIONS = (0.1, 0.3)
QUERY_FROM = 0.3


class SpatialAdapter(nn.Module):
    def __init__(self, C):
        super().__init__(); self.M = nn.Parameter(torch.eye(C))

    def forward(self, x):  # [B, C, L]
        return torch.einsum("dc,bcl->bdl", self.M, x)


class LowRank(nn.Module):
    def __init__(self, d=16, r=4):
        super().__init__(); self.A = nn.Parameter(torch.randn(r, d) * 0.1); self.B = nn.Parameter(torch.zeros(d, r))

    def forward(self, u):
        return F.normalize(u + u @ self.A.T @ self.B.T, dim=-1)


class Adapted(nn.Module):
    """Wraps a frozen base encoder; enc_kind 'patches' (anchor-level: list of window crops) or 'segment' (foundation)."""

    def __init__(self, base, kind, C, enc_kind):
        super().__init__()
        self.base, self.kind, self.enc_kind = base, kind, enc_kind
        for p in self.base.parameters():
            p.requires_grad_(False)
        self.sp = SpatialAdapter(C) if kind == "spatial_adapter" else None
        self.lr_ = LowRank() if kind == "personal_low_rank" else None

    def forward(self, x):
        if self.sp is not None:
            x = [self.sp(p) for p in x] if isinstance(x, list) else self.sp(x)
        u = self.base(x)
        return self.lr_(u) if self.lr_ is not None else u


def split_support_query(items, frac):
    n = len(items); q0 = int(round(QUERY_FROM * n)); s1 = max(1, int(round(frac * n)))
    return items[:s1], items[q0:]


def adapt_steps(adapted, loss_fn, support, steps, lr=1e-3, seed=0):
    params = [p for p in adapted.parameters() if p.requires_grad]
    if not params or steps == 0:
        return adapted
    opt = torch.optim.Adam(params, lr=lr); g = np.random.default_rng(seed)
    for _ in range(steps):
        loss = loss_fn(adapted, support, g)
        opt.zero_grad(); loss.backward(); opt.step()
    return adapted
