"""Channel-budget decoder. One model per electrode budget; no weight sharing across budgets."""
from __future__ import annotations

import torch
from torch import nn


class TemporalBlock(nn.Module):
    def __init__(self, width: int, dilation: int, dropout: float):
        super().__init__()
        self.conv = nn.Conv1d(width, width, kernel_size=5, padding=2 * dilation,
                              dilation=dilation)
        self.norm = nn.BatchNorm1d(width)
        self.act = nn.GELU()
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        return x + self.drop(self.act(self.norm(self.conv(x))))


class ChannelBudgetNet(nn.Module):
    """Spatial mixing, then dilated temporal blocks, then mean/std pooling.

    The spatial stage is a 1x1 convolution: with `in_channels` electrodes it learns a
    linear montage into `width` virtual channels, so a budget of 1 electrode and a
    budget of 128 differ only in what the first layer can see, never in depth.
    """

    def __init__(self, in_channels: int, n_classes: int, *, width: int = 96,
                 blocks: int = 6, dropout: float = 0.2, pool: int = 4):
        super().__init__()
        self.spatial = nn.Sequential(
            nn.Conv1d(in_channels, width, kernel_size=1), nn.BatchNorm1d(width), nn.GELU())
        self.stem = nn.Sequential(
            nn.Conv1d(width, width, kernel_size=25, stride=2, padding=12),
            nn.BatchNorm1d(width), nn.GELU(), nn.AvgPool1d(pool))
        self.blocks = nn.Sequential(*[TemporalBlock(width, 2 ** (i % 4), dropout)
                                      for i in range(blocks)])
        self.head = nn.Sequential(nn.Linear(2 * width, 2 * width), nn.GELU(),
                                  nn.Dropout(dropout), nn.Linear(2 * width, n_classes))
        self.embedding_dim = 2 * width

    def embed(self, x):
        h = self.blocks(self.stem(self.spatial(x)))
        return torch.cat([h.mean(dim=-1), h.std(dim=-1)], dim=-1)

    def forward(self, x):
        return self.head(self.embed(x))


def parameter_count(model: nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))
