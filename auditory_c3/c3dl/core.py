"""C3-DL shared components (docs/auditory_c3/C3DL_PILOT_SPEC.md): EEG encoder, per-time-step heads, fixed-covariance
Gaussian scoring for P-L, offset-logistic scoring for H-Cur, and a training loop that logs model mode, losses,
gradient/parameter norms and non-finite values, restoring train() after every validation pass.
"""
from __future__ import annotations

import math
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

LN2 = math.log(2.0)


class ChannelLN(nn.Module):
    """LayerNorm over channels at each time point (keeps the temporal receptive field local)."""

    def __init__(self, c):
        super().__init__()
        self.ln = nn.LayerNorm(c)

    def forward(self, x):
        return self.ln(x.transpose(1, 2)).transpose(1, 2)


class Encoder(nn.Module):
    """[B, C, T + rf - 1] -> [B, d_z, T]; output t sees input samples t .. t + rf - 1 only."""

    def __init__(self, n_ch, d_sp=16, kernels=(27, 26, 26), widths=(32, 32, 64), d_z=32):
        super().__init__()
        self.sp = nn.Conv1d(n_ch, d_sp, 1)
        layers, c = [], d_sp
        for k, w in zip(kernels, widths):
            layers += [nn.Conv1d(c, w, k), ChannelLN(w), nn.GELU()]
            c = w
        self.tc = nn.Sequential(*layers)
        self.out = nn.Conv1d(c, d_z, 1)
        self.rf = 1 + sum(k - 1 for k in kernels)
        self.d_z = d_z

    def forward(self, x):
        return self.out(self.tc(self.sp(x)))


class Head(nn.Module):
    """Per-time-step MLP d_in -> 64 -> d_out; last layer zero-initialised (offset arms start exactly at q0)."""

    def __init__(self, d_in, d_out, hidden=64):
        super().__init__()
        self.l1 = nn.Conv1d(d_in, hidden, 1)
        self.l2 = nn.Conv1d(hidden, d_out, 1)
        nn.init.zeros_(self.l2.weight); nn.init.zeros_(self.l2.bias)

    def forward(self, h):
        return self.l2(F.gelu(self.l1(h)))


class Proj(nn.Module):
    """Training-only contrastive projection head (H-Cur supervised contrast)."""

    def __init__(self, d_in, d_out=32):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, 64), nn.GELU(), nn.Linear(64, d_out))

    def forward(self, z):
        return F.normalize(self.net(z), dim=-1)


def maha(r, W):
    """Squared Mahalanobis norm per time step. r [B, D, T]; W [D, D] = Sigma^{-1/2}. -> [B, T]"""
    return torch.einsum("ed,bdt->bet", W, r).pow(2).sum(1)


def gaussian_evidence_bits(L, m0, Lhat, W):
    """e = (||L - m0||^2 - ||L - Lhat||^2) / (2 ln 2) per time step, bits. -> [B, T]"""
    return (maha(L - m0, W) - maha(L - Lhat, W)) / (2 * LN2)


def candidate_scores(Lc, Lhat, W):
    """Lc [B, K+1, D, T] candidates (index 0 = positive); score = -mean_t ||Lc - Lhat||^2 / 2. -> [B, K+1]"""
    B, K1, D, T = Lc.shape
    r = Lc - Lhat[:, None]
    q = torch.einsum("ed,bkdt->bket", W, r).pow(2).sum(2)
    return -q.mean(-1) / 2


def supcon(p, y, valid, tau):
    """Supervised contrastive loss restricted to valid pairs. p [N, d] normalised; y [N]; valid [N, N] bool (i != j).
    Anchors without any valid positive are skipped."""
    sim = p @ p.t() / tau
    sim = sim.masked_fill(~valid, -1e9)
    logprob = sim - torch.logsumexp(sim, dim=1, keepdim=True)
    pos = valid & (y[:, None] == y[None, :])
    npos = pos.sum(1)
    ok = npos > 0
    if ok.sum() == 0:
        return p.sum() * 0.0, 0
    loss = -(logprob * pos).sum(1)[ok] / npos[ok]
    return loss.mean(), int(ok.sum())


def grad_param_norms(model):
    g = [p.grad.detach().norm() for p in model.parameters() if p.grad is not None]
    w = [p.detach().norm() for p in model.parameters()]
    return (float(torch.stack(g).norm()) if g else 0.0), float(torch.stack(w).norm())


def nonfinite(model):
    return int(sum((~torch.isfinite(p)).sum().item() for p in model.parameters()))


class Timer:
    def __init__(self):
        self.t0 = time.time()

    def s(self):
        return round(time.time() - self.t0, 2)


def set_seed(seed):
    np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")
