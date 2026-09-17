"""Fixed-classifier visible/null geometry for auditory5 Idea D."""

from __future__ import annotations

from dataclasses import dataclass
import torch
from torch import Tensor
from torch.nn import functional as F


@dataclass(frozen=True)
class HeadGeometry:
    weight: Tensor
    bias: Tensor
    center: Tensor
    visible_basis: Tensor
    null_basis: Tensor
    rank: int
    threshold: float

    @property
    def p_visible(self) -> Tensor:
        return self.visible_basis @ self.visible_basis.T

    @property
    def p_null(self) -> Tensor:
        return self.null_basis @ self.null_basis.T


def decompose_head(weight: Tensor, bias: Tensor, center: Tensor | None = None) -> HeadGeometry:
    """SVD-decompose the centered class row space in float64.

    A rank-zero head is valid and returns an empty visible basis plus the full
    null basis, with ``rank == 0`` as an explicit diagnostic.
    """
    if weight.ndim != 2 or weight.shape[0] < 1 or weight.shape[1] < 1:
        raise ValueError("weight must have shape [classes>=1, features>=1]")
    if bias.ndim != 1 or bias.shape[0] != weight.shape[0]:
        raise ValueError("bias must match the class dimension")
    if not torch.isfinite(weight).all() or not torch.isfinite(bias).all():
        raise ValueError("head contains NaN or infinite values")
    p = weight.shape[1]
    mu = torch.zeros(p, dtype=torch.float64, device=weight.device) if center is None else torch.as_tensor(center, dtype=torch.float64, device=weight.device)
    if mu.shape != (p,) or not torch.isfinite(mu).all():
        raise ValueError("center must be a finite vector matching feature dimension")
    w64, b64 = weight.to(torch.float64), bias.to(torch.float64)
    centered_w = w64 - w64.mean(dim=0, keepdim=True)
    u, s, vh = torch.linalg.svd(centered_w, full_matrices=True)
    smax = float(s.max().item()) if s.numel() else 0.0
    threshold = max(weight.shape[0], p) * torch.finfo(torch.float64).eps * smax
    rank = int((s > threshold).sum().item())
    # V columns are the right singular vectors; vh is V^T.
    v = vh.T
    visible = v[:, :rank]
    null = v[:, rank:]
    return HeadGeometry(w64, b64, mu, visible, null, rank, threshold)


def split_features(z: Tensor, geometry: HeadGeometry) -> tuple[Tensor, Tensor]:
    """Return centered visible and null components in the shared feature space."""
    if z.ndim != 2 or z.shape[1] != geometry.weight.shape[1] or not torch.isfinite(z).all():
        raise ValueError("z has invalid shape or non-finite values")
    zc = z.to(torch.float64) - geometry.center
    return zc @ geometry.p_visible, zc @ geometry.p_null


def max_softmax_difference(z: Tensor, geometry: HeadGeometry) -> Tensor:
    """Maximum float64 probability difference after removing null components."""
    visible, _ = split_features(z, geometry)
    original = F.softmax(z.to(torch.float64) @ geometry.weight.T + geometry.bias, dim=1)
    reconstructed = geometry.center + visible
    reduced = F.softmax(reconstructed @ geometry.weight.T + geometry.bias, dim=1)
    return (original - reduced).abs().max()
