"""EEGNet-style decoders with optional per-child spatial filters and FiLM conditioning; SSL encoder."""
from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F


class EEGNet(nn.Module):
    """EEGNet-8,2 shape: temporal conv -> (per-child) depthwise spatial conv -> separable conv -> linear.

    n_children > 0 gives every child its own spatial filter bank (index n_children is the shared
    fallback used for unseen children); cond_dim > 0 adds FiLM (scale, shift) on the spatial maps
    from a conditioning vector such as z-scored age.
    """

    def __init__(self, n_channels: int, n_times: int, n_classes: int, *, F1: int = 16, D: int = 2,
                 F2: int = 32, k1: int = 25, k2: int = 15, dropout: float = 0.25,
                 n_children: int = 0, cond_dim: int = 0):
        super().__init__()
        self.C, self.T, self.F1, self.D = n_channels, n_times, F1, D
        self.n_children, self.cond_dim = n_children, cond_dim
        self.temporal = nn.Conv2d(1, F1, (1, k1), padding=(0, k1 // 2), bias=False)
        self.bn1 = nn.BatchNorm2d(F1)
        if n_children > 0:
            w = torch.empty(n_children + 1, F1 * D, n_channels)
            nn.init.normal_(w, std=1.0 / n_channels ** 0.5)
            self.child_spatial = nn.Parameter(w)
        else:
            self.spatial = nn.Conv2d(F1, F1 * D, (n_channels, 1), groups=F1, bias=False)
        self.bn2 = nn.BatchNorm2d(F1 * D)
        if cond_dim > 0:
            self.film = nn.Linear(cond_dim, 2 * F1 * D)
            nn.init.zeros_(self.film.weight)
            nn.init.zeros_(self.film.bias)
        self.pool1 = nn.AvgPool2d((1, 4))
        self.drop1 = nn.Dropout(dropout)
        self.sep_depth = nn.Conv2d(F1 * D, F1 * D, (1, k2), padding=(0, k2 // 2), groups=F1 * D, bias=False)
        self.sep_point = nn.Conv2d(F1 * D, F2, 1, bias=False)
        self.bn3 = nn.BatchNorm2d(F2)
        self.pool2 = nn.AvgPool2d((1, 8))
        self.drop2 = nn.Dropout(dropout)
        self.feature_dim = F2 * (n_times // 32)
        self.head = nn.Linear(self.feature_dim, n_classes)

    def _spatial(self, h: torch.Tensor, child: torch.Tensor | None) -> torch.Tensor:
        # h: [B, F1, C, T] -> [B, F1*D, 1, T]
        if self.n_children == 0:
            return self.spatial(h)
        if child is None:
            child = torch.full((h.shape[0],), self.n_children, dtype=torch.long, device=h.device)
        out = h.new_empty(h.shape[0], self.F1 * self.D, 1, h.shape[-1])
        for c in torch.unique(child):
            sel = torch.nonzero(child == c, as_tuple=False).squeeze(1)
            w = self.child_spatial[c].view(self.F1 * self.D, 1, self.C, 1)
            out[sel] = F.conv2d(h[sel], w, groups=self.F1)
        return out

    def embed(self, x: torch.Tensor, child: torch.Tensor | None = None, cond: torch.Tensor | None = None) -> torch.Tensor:
        h = self.bn1(self.temporal(x.unsqueeze(1)))               # [B, F1, C, T]
        h = self.bn2(self._spatial(h, child))                     # [B, F1*D, 1, T]
        if self.cond_dim > 0 and cond is not None:
            gamma, beta = self.film(cond).chunk(2, dim=-1)
            h = h * (1.0 + gamma)[:, :, None, None] + beta[:, :, None, None]
        h = self.drop1(self.pool1(F.elu(h)))
        h = self.bn3(self.sep_point(self.sep_depth(h)))
        h = self.drop2(self.pool2(F.elu(h)))
        return h.flatten(1)

    def forward(self, x, child=None, cond=None):
        return self.head(self.embed(x, child, cond))

    def share_child_filters_from_mean(self) -> None:
        """Set the fallback (unseen-child) spatial bank to the mean of the trained banks."""
        if self.n_children > 0:
            with torch.no_grad():
                self.child_spatial[self.n_children] = self.child_spatial[: self.n_children].mean(0)


class ConvEncoder(nn.Module):
    """Continuous-window encoder: 1x1 spatial mixing, three stride-2 temporal blocks (x8 downsampling)."""

    def __init__(self, n_channels: int, width: int = 64):
        super().__init__()
        self.spatial = nn.Sequential(nn.Conv1d(n_channels, width, 1), nn.BatchNorm1d(width), nn.GELU())
        blocks = []
        for _ in range(3):
            blocks += [nn.Conv1d(width, width, 9, stride=2, padding=4), nn.BatchNorm1d(width), nn.GELU(),
                       nn.Conv1d(width, width, 5, padding=2), nn.BatchNorm1d(width), nn.GELU()]
        self.blocks = nn.Sequential(*blocks)
        self.width = width
        self.embedding_dim = 2 * width

    def tokens(self, x: torch.Tensor) -> torch.Tensor:
        return self.blocks(self.spatial(x))                        # [B, width, L/8]

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        t = self.tokens(x)
        return torch.cat([t.mean(-1), t.std(-1)], dim=-1)


class MaskedReconstructor(nn.Module):
    """Masked time-patch reconstruction: zero masked patches at the input, reconstruct them."""

    def __init__(self, n_channels: int, width: int = 64):
        super().__init__()
        self.encoder = ConvEncoder(n_channels, width)
        dec = []
        for _ in range(3):
            dec += [nn.ConvTranspose1d(width, width, 4, stride=2, padding=1), nn.BatchNorm1d(width), nn.GELU()]
        dec += [nn.Conv1d(width, n_channels, 5, padding=2)]
        self.decoder = nn.Sequential(*dec)

    def forward(self, x_masked: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder.tokens(x_masked))


def patch_mask(batch: int, length: int, patch: int, fraction: float, gen: torch.Generator, device) -> torch.Tensor:
    """Boolean [B, L] mask, True where the signal is hidden, in contiguous patches."""
    n_patches = length // patch
    n_masked = max(1, int(round(fraction * n_patches)))
    scores = torch.rand(batch, n_patches, generator=gen, device=device)
    idx = scores.argsort(dim=1)[:, :n_masked]
    m = torch.zeros(batch, n_patches, dtype=torch.bool, device=device)
    m.scatter_(1, idx, True)
    m = m.repeat_interleave(patch, dim=1)
    if m.shape[1] < length:
        m = torch.cat([m, torch.zeros(batch, length - m.shape[1], dtype=torch.bool, device=device)], dim=1)
    return m
