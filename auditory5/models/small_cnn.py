"""The fixed SmallEEGCNN_v1 baseline from the auditory5 specification."""

from __future__ import annotations

import torch
from torch import Tensor, nn


class SmallEEGCNN_v1(nn.Module):
    """Small EEG CNN with a 64-dimensional representation and no BatchNorm.

    Input is ``[batch, channels, time]``.  The classifier is optional at
    construction time and is kept separate from the representation output.
    """

    def __init__(self, channels: int, n_classes: int | None = None) -> None:
        super().__init__()
        if not isinstance(channels, int) or channels <= 0:
            raise ValueError("channels must be a positive integer")
        if n_classes is not None and (not isinstance(n_classes, int) or n_classes <= 0):
            raise ValueError("n_classes must be a positive integer or None")
        self.channels = channels
        self.n_classes = n_classes
        self.features = nn.Sequential(
            nn.Conv1d(channels, 32, kernel_size=15, padding=7),
            nn.GroupNorm(4, 32),
            nn.GELU(),
            nn.Conv1d(32, 64, kernel_size=9, padding=4, stride=2),
            nn.GroupNorm(8, 64),
            nn.GELU(),
            nn.Conv1d(64, 64, kernel_size=7, padding=3, stride=2),
            nn.GroupNorm(8, 64),
            nn.GELU(),
            nn.AdaptiveAvgPool1d(4),
        )
        self.to_representation = nn.Linear(256, 64)
        self.head = nn.Linear(64, n_classes) if n_classes is not None else None

    def forward(self, x: Tensor, *, return_logits: bool = False) -> Tensor | tuple[Tensor, Tensor]:
        if not isinstance(x, Tensor) or x.ndim != 3:
            raise ValueError("x must have shape [batch, channels, time]")
        if x.shape[0] == 0 or x.shape[2] == 0:
            raise ValueError("empty batch or time dimension")
        if x.shape[1] != self.channels:
            raise ValueError(f"expected {self.channels} channels, got {x.shape[1]}")
        if not torch.isfinite(x).all():
            raise ValueError("x contains NaN or infinite values")
        z = self.to_representation(self.features(x).flatten(1))
        if return_logits:
            if self.head is None:
                raise ValueError("return_logits=True requires n_classes")
            return z, self.head(z)
        return z
