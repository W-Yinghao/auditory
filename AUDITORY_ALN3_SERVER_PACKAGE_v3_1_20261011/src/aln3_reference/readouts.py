"""Channel-aware dense queries and zero-initialized complementary predictions.

These are reference heads, not integrated CBraMod/REVE models. Dense outputs
remain full-context outputs if the backbone has read full-context EEG. Query
coordinates must be relative physical times, never stimulus identities/audio.
"""
from __future__ import annotations
import math
import torch
from torch import nn


def _times(t: torch.Tensor, batch: int, count: int, name: str) -> torch.Tensor:
    if t.ndim == 1 and t.numel() == count:
        t = t[None].expand(batch, -1)
    if t.shape != (batch, count) or not torch.isfinite(t).all():
        raise ValueError(f"{name} must be finite [{count}] or [{batch},{count}]")
    return t


class TimeFeatures(nn.Module):
    def __init__(self, frequencies: int = 4):
        super().__init__()
        if frequencies < 1:
            raise ValueError("frequencies must be positive")
        self.register_buffer("freq", 2.0 ** torch.arange(frequencies, dtype=torch.float32))
        self.out_dim = 1 + 2 * frequencies

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        x = 2 * math.pi * t[..., None] * self.freq
        return torch.cat((t[..., None], x.sin(), x.cos()), dim=-1)


class ChannelSpatialProjection(nn.Module):
    """[B,C,P,D] -> [B,P,H], retaining learned signed channel contrasts."""
    def __init__(self, channels: int, feature_dim: int, hidden: int = 128,
                 spatial_filters: int = 8, projected_dim: int = 32):
        super().__init__()
        if min(channels, feature_dim, hidden, spatial_filters, projected_dim) < 1:
            raise ValueError("All dimensions must be positive")
        self.channels, self.feature_dim = channels, feature_dim
        self.feature = nn.Linear(feature_dim, projected_dim)
        self.spatial = nn.Parameter(torch.randn(spatial_filters, channels) / math.sqrt(channels))
        self.output = nn.Sequential(nn.LayerNorm(spatial_filters * projected_dim),
                                    nn.Linear(spatial_filters * projected_dim, hidden))

    def forward(self, h: torch.Tensor, valid_channels: torch.Tensor | None = None) -> torch.Tensor:
        if h.ndim != 4 or h.shape[1] != self.channels or h.shape[3] != self.feature_dim:
            raise ValueError("Expected backbone tokens [B,C,P,D] with declared channel order")
        if not torch.isfinite(h).all():
            raise ValueError("Non-finite backbone tokens")
        x = self.feature(h)
        if valid_channels is not None:
            if valid_channels.shape != h.shape[:2] or valid_channels.dtype != torch.bool:
                raise ValueError("valid_channels must be bool [B,C]")
            if not valid_channels.any(1).all():
                raise ValueError("An example has no valid EEG channels")
            x = x * valid_channels[:, :, None, None]
        x = torch.einsum("kc,bcpe->bpke", self.spatial, x).flatten(2)
        return self.output(x)


class DenseQueryReadout(nn.Module):
    """Predict a common audio target grid from EEG tokens and relative times only.

    No audio input, channel averaging, or automatic claim of temporal isolation.
    The caller supplies actual patch centers after the native model's patching.
    """
    def __init__(self, channels: int, feature_dim: int, output_dim: int,
                 hidden: int = 128, heads: int = 4, spatial_filters: int = 8,
                 projected_dim: int = 32):
        super().__init__()
        if output_dim < 1 or hidden % heads:
            raise ValueError("output_dim must be positive and hidden divisible by heads")
        self.project = ChannelSpatialProjection(channels, feature_dim, hidden, spatial_filters, projected_dim)
        self.time = TimeFeatures()
        self.patch_pos = nn.Linear(self.time.out_dim, hidden)
        self.query_pos = nn.Sequential(nn.Linear(self.time.out_dim, hidden), nn.GELU(), nn.Linear(hidden, hidden))
        self.attention = nn.MultiheadAttention(hidden, heads, batch_first=True, dropout=0.0)
        self.output = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, output_dim))

    def forward(self, h: torch.Tensor, patch_times: torch.Tensor, query_times: torch.Tensor,
                valid_patches: torch.Tensor | None = None,
                valid_channels: torch.Tensor | None = None) -> torch.Tensor:
        if h.ndim != 4:
            raise ValueError("h must be [B,C,P,D]")
        b, _, p, _ = h.shape
        if query_times.ndim not in (1, 2):
            raise ValueError("query_times must have one or two axes")
        q = query_times.shape[-1]
        if q < 1 or p < 1:
            raise ValueError("At least one query and patch are required")
        pt = _times(patch_times.to(h.device, h.dtype), b, p, "patch_times")
        qt = _times(query_times.to(h.device, h.dtype), b, q, "query_times")
        mask = None
        if valid_patches is not None:
            if valid_patches.shape != (b, p) or valid_patches.dtype != torch.bool:
                raise ValueError("valid_patches must be bool [B,P]")
            if not valid_patches.any(1).all():
                raise ValueError("An example has no valid patches")
            mask = ~valid_patches
        memory = self.project(h, valid_channels) + self.patch_pos(self.time(pt))
        queries = self.query_pos(self.time(qt))
        read, _ = self.attention(queries, memory, memory, key_padding_mask=mask, need_weights=False)
        return self.output(read + queries)


class ZeroResidualPrediction(nn.Module):
    """Add a learned residual in one declared prediction space.

    For continuous tasks the base and residual are audio predictions in the same
    fixed coordinate system; for private tasks they are logits, not probabilities.
    Zero initialization preserves base predictions exactly, not future test risk.
    """
    def __init__(self, local_dim: int, context_dim: int, output_dim: int, hidden: int = 64):
        super().__init__()
        self.local_dim, self.context_dim, self.output_dim = local_dim, context_dim, output_dim
        self.residual = nn.Sequential(nn.Linear(local_dim + context_dim, hidden), nn.GELU(), nn.Linear(hidden, output_dim))
        nn.init.zeros_(self.residual[-1].weight)
        nn.init.zeros_(self.residual[-1].bias)

    def forward(self, base: torch.Tensor, local: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        if base.shape[:-1] != local.shape[:-1] or base.shape[:-1] != context.shape[:-1]:
            raise ValueError("Base, local and context must have aligned batch/query axes")
        if (base.shape[-1], local.shape[-1], context.shape[-1]) != (self.output_dim, self.local_dim, self.context_dim):
            raise ValueError("Wrong feature dimensions")
        return base + self.residual(torch.cat((local, context), -1))


class ChannelPhaseLinearReadout(nn.Module):
    """Phase-basis decoder linear in EEG tokens, with fixed time-local patch weights.

    Every channel is retained; for fixed query coordinates the mapping from
    tokens to predictions is affine. Train it with the declared task objective,
    or use a separate ridge implementation on the explicit basis features.
    """
    def __init__(self, channels: int, feature_dim: int, output_dim: int,
                 time_frequencies: int = 4, bandwidth_seconds: float = 0.75):
        super().__init__()
        if min(channels, feature_dim, output_dim) < 1 or bandwidth_seconds <= 0:
            raise ValueError("Invalid dimensions or temporal weighting bandwidth")
        self.channels, self.feature_dim, self.output_dim = channels, feature_dim, output_dim
        self.time = TimeFeatures(time_frequencies)
        self.bandwidth = bandwidth_seconds
        self.coefficients = nn.Linear(channels * feature_dim, self.time.out_dim * output_dim)

    def forward(self, h: torch.Tensor, patch_times: torch.Tensor, query_times: torch.Tensor,
                valid_patches: torch.Tensor | None = None) -> torch.Tensor:
        if h.ndim != 4 or h.shape[1] != self.channels or h.shape[-1] != self.feature_dim or not torch.isfinite(h).all():
            raise ValueError("Expected finite channel-preserved tokens [B,C,P,D]")
        b, _, p, _ = h.shape
        if query_times.ndim not in (1, 2):
            raise ValueError("Invalid query times")
        q = query_times.shape[-1]
        pt = _times(patch_times.to(h.device, h.dtype), b, p, "patch_times")
        qt = _times(query_times.to(h.device, h.dtype), b, q, "query_times")
        rel = qt[:, :, None] - pt[:, None, :]
        basis = self.time(rel)  # B,Q,P,F
        coeff = self.coefficients(h.permute(0, 2, 1, 3).flatten(2))
        coeff = coeff.reshape(b, p, self.time.out_dim, self.output_dim)
        logits = -0.5 * (rel / self.bandwidth).square()
        if valid_patches is not None:
            if valid_patches.shape != (b, p) or valid_patches.dtype != torch.bool or not valid_patches.any(1).all():
                raise ValueError("Invalid patch mask")
            logits = logits.masked_fill(~valid_patches[:, None, :], -torch.inf)
        weight = logits.softmax(-1)
        return torch.einsum("bqp,bqpf,bpfa->bqa", weight, basis, coeff)
