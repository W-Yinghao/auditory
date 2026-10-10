"""ALN2 module A: time-preserving EEG encoders for anchor-level sound-EEG alignment (package docs/03).

Architectures (all take the restricted EEG window(s) cropped by the batcher; nothing outside [start, stop) is read):
  legacy_pool4      : the previous round's EEGEncoder (spatial 1x1 -> 3 dilated conv blocks -> AdaptiveAvgPool1d(4)),
                      kept with the legacy window rule (right end + 1 sample) so results connect to the last round.
  density_tokens    : same conv body, then average-pooling to a fixed token step (~20 ms; 3 samples at 128 Hz, 2 at
                      100 Hz, 5 at 250 Hz), a learned token-position embedding, and a token-flatten projection to d.
                      Longer windows therefore keep more tokens instead of being compressed to four cells.
  lag_local_tokens  : a local encoder f_local over w = 40 ms sub-windows at lag offsets tau (step ~20 ms), parameters
                      shared across tau, plus an explicit lag-position embedding; tokens are flattened and projected.
Joint (early + late) models concatenate the token sequences of the two restricted branches before the projection
(legacy_pool4: the previous two-branch fuse). New architectures use half-open windows [start_ms, stop_ms).
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from auditory_alignment.model import WINDOWS_MS, EEGEncoder as LegacyEncoder, window_samples as legacy_window_samples

TOKEN_STEP_MS = 20.0
LOCAL_PATCH_MS = 40.0
TOKEN_DIM = 32


def window_samples_v2(dataset, window, fs, pre=0):
    """Half-open sample range [start, stop) of a window relative to the anchor (new ALN2 rule)."""
    a, b = WINDOWS_MS[dataset][window]
    return pre + int(round(a * fs / 1000)), pre + int(round(b * fs / 1000))


def windows_of(window):
    return ["early", "late"] if window == "joint" else [window]


def window_ranges(architecture, dataset, window, fs, pre=0):
    rule = legacy_window_samples if architecture == "legacy_pool4" else window_samples_v2
    return [rule(dataset, w, fs, pre=pre) for w in windows_of(window)]


def token_step(fs):
    return max(1, int(round(TOKEN_STEP_MS * fs / 1000)))


class ChannelLN(nn.Module):
    def __init__(self, c):
        super().__init__(); self.ln = nn.LayerNorm(c)

    def forward(self, x):
        return self.ln(x.transpose(1, 2)).transpose(1, 2)


def conv_body(n_ch, width=32, d_sp=16):
    layers, c = [nn.Conv1d(n_ch, d_sp, 1)], d_sp
    for dil in (1, 2, 4):
        layers += [nn.Conv1d(c, width, 5, padding=2 * dil, dilation=dil), ChannelLN(width), nn.GELU()]; c = width
    return nn.Sequential(*layers)


class DensityBranch(nn.Module):
    """[B, C, L] -> tokens [B, K, TOKEN_DIM], K = L // step (time order kept)."""

    def __init__(self, n_ch, L, step):
        super().__init__()
        self.body = conv_body(n_ch)
        self.step, self.K = step, max(1, L // step)
        self.tok = nn.Linear(32, TOKEN_DIM)
        self.pos = nn.Parameter(torch.zeros(self.K, TOKEN_DIM))

    def forward(self, x):
        h = self.body(x)[:, :, : self.K * self.step]
        h = F.avg_pool1d(h, self.step, self.step).transpose(1, 2)  # [B, K, 32]
        return self.tok(h) + self.pos


class LagLocalBranch(nn.Module):
    """Shared local encoder over w-sample sub-windows at lag offsets; [B, C, L] -> tokens [B, n_tau, TOKEN_DIM]."""

    def __init__(self, n_ch, L, step, w):
        super().__init__()
        w = min(w, L)
        offs = sorted(set(range(0, L - w + 1, step)) | {L - w})
        self.register_buffer("offs", torch.tensor(offs), persistent=False)
        self.w = w
        self.local = nn.Sequential(nn.Conv1d(n_ch, 16, 1), nn.Conv1d(16, 32, min(3, w), padding=min(3, w) // 2), ChannelLN(32), nn.GELU())
        self.tok = nn.Linear(32, TOKEN_DIM)
        self.pos = nn.Parameter(torch.zeros(len(offs), TOKEN_DIM))

    @property
    def K(self):
        return len(self.offs)

    def forward(self, x):
        B, C, L = x.shape
        idx = self.offs[:, None] + torch.arange(self.w, device=x.device)[None]  # [n_tau, w]
        p = x[:, :, idx].permute(0, 2, 1, 3).reshape(B * len(self.offs), C, self.w)
        h = self.local(p).mean(-1).reshape(B, len(self.offs), 32)
        return self.tok(h) + self.pos


class TokenEncoder(nn.Module):
    """density_tokens / lag_local_tokens: branch tokens (one branch per restricted window) -> flatten -> d, L2-normalised.
    forward_tokens() exposes the time-ordered token sequence for single-token analyses."""

    def __init__(self, kind, n_ch, d, windows, fs):
        super().__init__()
        step = token_step(fs)
        w = max(2, int(round(LOCAL_PATCH_MS * fs / 1000)))
        self.windows, self.kind = windows, kind
        mk = (lambda L: DensityBranch(n_ch, L, step)) if kind == "density_tokens" else (lambda L: LagLocalBranch(n_ch, L, step, w))
        self.branches = nn.ModuleList([mk(b - a) for a, b in windows])
        self.n_tokens = sum(br.K for br in self.branches)
        self.proj = nn.Sequential(nn.LayerNorm(self.n_tokens * TOKEN_DIM), nn.Linear(self.n_tokens * TOKEN_DIM, d))

    def forward_tokens(self, patches):
        return torch.cat([br(p) for br, p in zip(self.branches, patches)], 1)

    def forward(self, patches):
        z = self.forward_tokens(patches)
        return F.normalize(self.proj(z.flatten(1)), dim=1)


def build_encoder(architecture, n_ch, d, windows, fs):
    if architecture == "legacy_pool4":
        return LegacyEncoder(n_ch, d, windows)
    if architecture in ("density_tokens", "lag_local_tokens"):
        return TokenEncoder(architecture, n_ch, d, windows, fs)
    raise ValueError(architecture)


def describe(enc):
    n = sum(p.numel() for p in enc.parameters())
    out = {"n_params": int(n)}
    if isinstance(enc, TokenEncoder):
        out.update({"n_tokens": int(enc.n_tokens), "tokens_per_branch": [int(b.K) for b in enc.branches]})
    return out
