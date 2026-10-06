"""Time-limited EEG patch encoders and the audio projection head (IMPLEMENTATION_NOTES §2)."""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

WINDOWS_MS = {
    "fau": {"full": (0, 600), "early": (0, 80), "late": (90, 300), "late_equalwidth": (90, 170)},
    "dtu": {"full": (0, 600), "early": (0, 80), "late": (90, 300), "late_equalwidth": (90, 170)},
    "federici": {"full": (0, 600), "early": (0, 150), "late": (150, 600), "late_equalwidth": (150, 300)},
    "private_bdf": {"full": (0, 600), "early": (120, 200), "late": (240, 320), "late_equalwidth": (240, 320)},
}


def window_samples(dataset, window, fs, pre=0):
    """[start, stop) sample offsets of a window relative to the anchor (plus the epoch pre-stimulus offset)."""
    a, b = WINDOWS_MS[dataset][window]
    return pre + int(round(a * fs / 1000)), pre + int(round(b * fs / 1000)) + 1


class ChannelLN(nn.Module):
    def __init__(self, c):
        super().__init__(); self.ln = nn.LayerNorm(c)

    def forward(self, x):
        return self.ln(x.transpose(1, 2)).transpose(1, 2)


class PatchEncoder(nn.Module):
    """[B, C, L] patch (only samples inside W) -> d. Zero padding is applied inside the patch, so no EEG outside W is read."""

    def __init__(self, n_ch, d, width=32, d_sp=16, pool=4):
        super().__init__()
        self.sp = nn.Conv1d(n_ch, d_sp, 1)
        blocks, c = [], d_sp
        for dil in (1, 2, 4):
            blocks += [nn.Conv1d(c, width, 5, padding=2 * dil, dilation=dil), ChannelLN(width), nn.GELU()]; c = width
        self.tc = nn.Sequential(*blocks)
        self.pool = nn.AdaptiveAvgPool1d(pool)
        self.out = nn.Linear(width * pool, d)

    def forward(self, x):
        return self.out(self.pool(self.tc(self.sp(x))).flatten(1))


class EEGEncoder(nn.Module):
    """Single window, or the early+late joint model (two restricted branches, concatenated, linearly fused)."""

    def __init__(self, n_ch, d, windows):
        super().__init__()
        self.windows = windows  # list of (start, stop)
        self.branches = nn.ModuleList([PatchEncoder(n_ch, d) for _ in windows])
        self.fuse = nn.Linear(d * len(windows), d) if len(windows) > 1 else None

    def forward(self, patches):
        z = [b(p) for b, p in zip(self.branches, patches)]
        z = self.fuse(torch.cat(z, 1)) if self.fuse is not None else z[0]
        return F.normalize(z, dim=1)


class AudioProjection(nn.Module):
    def __init__(self, in_dim, d, frozen=False):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_dim, 32), nn.GELU(), nn.Linear(32, d))
        if frozen:
            for p in self.net.parameters():
                p.requires_grad_(False)

    def forward(self, a):
        return F.normalize(self.net(a), dim=1)


def n_params(m):
    return int(sum(p.numel() for p in m.parameters()))
