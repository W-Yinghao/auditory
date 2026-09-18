"""Exact adaptive-average bins using deterministic mean/slice operations.

PyTorch's native CUDA adaptive pooling backward does not implement its strict
deterministic mode for the lengths used by the frozen CNN. This parameter-free
replacement preserves the same four overlapping bins and all state-dict keys.
"""
from __future__ import annotations

import torch
from torch import nn

from auditory5.models.small_cnn import SmallEEGCNN_v1


class DeterministicAdaptiveAvgPool1d(nn.Module):
    """AdaptiveAvgPool1d(4): bin i is [floor(i L/4), ceil((i+1)L/4))."""

    def __init__(self, output_size=4):
        super().__init__()
        if output_size != 4:
            raise ValueError("The frozen EEG pooling contract has exactly four outputs")
        self.output_size = 4

    def forward(self, x):
        if x.ndim not in (2, 3) or x.shape[-1] < 1:
            raise ValueError("Adaptive one-dimensional pooling requires a nonempty time axis")
        length = x.shape[-1]
        return torch.stack([
            x[..., (i * length) // 4: ((i + 1) * length + 3) // 4].mean(dim=-1)
            for i in range(4)
        ], dim=-1)

    def extra_repr(self):
        return "output_size=4, implementation=deterministic_mean_slices"


def configure_pool(model):
    """Replace only the frozen SmallEEGCNN's parameter-free pooling module.

    This is idempotent, consumes no random numbers, and leaves initialization,
    parameter objects and checkpoint state keys unchanged. The caller must also
    configure this equivalent implementation when restoring a checkpoint.
    """
    if not isinstance(model, SmallEEGCNN_v1):
        raise TypeError("Only the frozen SmallEEGCNN_v1 pooling implementation may be replaced")
    matches = [(name, child) for name, child in model.features.named_children()
               if isinstance(child, (nn.AdaptiveAvgPool1d, DeterministicAdaptiveAvgPool1d))]
    if len(matches) != 1:
        raise ValueError("Expected exactly one adaptive pooling layer in the frozen CNN")
    name, pool = matches[0]
    if pool.output_size != 4:
        raise ValueError("Frozen CNN pooling output size changed")
    if not isinstance(pool, DeterministicAdaptiveAvgPool1d):
        replacement = DeterministicAdaptiveAvgPool1d(4)
        replacement.train(pool.training)
        model.features._modules[name] = replacement
    return model
