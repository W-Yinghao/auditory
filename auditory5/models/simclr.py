"""Auditable two-view SimCLR helpers for auditory5 v1."""

from __future__ import annotations

import torch
import math
from torch import Tensor, nn
from torch.nn import functional as F


class ProjectionHead(nn.Module):
    """The specified 64 -> 128 -> 64 GELU projector.

    Only the projector output is L2-normalized; encoder representations are
    returned unchanged by the CNN.
    """

    def __init__(self, in_dim: int = 64) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_dim, 128), nn.GELU(), nn.Linear(128, 64))

    def forward(self, z: Tensor) -> Tensor:
        if z.ndim != 2 or z.shape[0] == 0 or z.shape[1] != 64:
            raise ValueError("projector input must have shape [nonempty batch, 64]")
        if not torch.isfinite(z).all():
            raise ValueError("projector input contains NaN or infinite values")
        return F.normalize(self.net(z), p=2, dim=1)


def add_independent_gaussian_noise(x: Tensor, scale: Tensor | float, *, generator=None) -> Tensor:
    """Add independent Gaussian noise; ``scale`` is the training-fold scale."""
    if not isinstance(x, Tensor) or x.numel() == 0 or not torch.isfinite(x).all():
        raise ValueError("x must be a nonempty finite tensor")
    s = torch.as_tensor(scale, dtype=x.dtype, device=x.device)
    if s.ndim == 1 and x.ndim == 3:
        if s.numel() != x.shape[1]:
            raise ValueError('channel scale length must match the channel axis')
        s = s[None, :, None]
    if not torch.isfinite(s).all() or (s < 0).any():
        raise ValueError("scale must be finite and nonnegative")
    return x + torch.randn(x.shape, dtype=x.dtype, device=x.device, generator=generator) * s


def make_noise_views(x: Tensor, channel_scale: Tensor | float, *, noise_fraction: float = 0.02,
                     generator=None) -> tuple[Tensor, Tensor]:
    """Return two independently seeded noise views of the same trials."""
    if noise_fraction < 0 or not torch.isfinite(torch.tensor(noise_fraction)):
        raise ValueError("noise_fraction must be finite and nonnegative")
    scale = torch.as_tensor(channel_scale, dtype=x.dtype, device=x.device) * noise_fraction
    return (add_independent_gaussian_noise(x, scale, generator=generator),
            add_independent_gaussian_noise(x, scale, generator=generator))


def nt_xent_loss(z1: Tensor, z2: Tensor, temperature: float = 0.2) -> Tensor:
    """Symmetric NT-Xent, with same-trial positives and self-pairs excluded."""
    if z1.ndim != 2 or z2.ndim != 2 or z1.shape != z2.shape or z1.shape[0] < 2:
        raise ValueError("z1 and z2 must be matching [batch>=2, dim] tensors")
    if not torch.isfinite(z1).all() or not torch.isfinite(z2).all():
        raise ValueError("representations contain NaN or infinite values")
    if not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be positive")
    n = z1.shape[0]
    reps = F.normalize(torch.cat((z1, z2), dim=0), p=2, dim=1)
    logits = reps @ reps.T / temperature
    eye = torch.eye(2 * n, dtype=torch.bool, device=logits.device)
    logits = logits.masked_fill(eye, float("-inf"))
    positive = torch.arange(2 * n, device=logits.device)
    positive = (positive + n) % (2 * n)
    return F.cross_entropy(logits, positive)
