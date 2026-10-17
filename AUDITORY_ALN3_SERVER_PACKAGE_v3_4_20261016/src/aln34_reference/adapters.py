"""Small identity-initialized spatial adapters; no backbone/training runner."""
from __future__ import annotations
import torch
from torch import nn

class SpatialAdapter(nn.Module):
    """Accepts EEG (batch, channels, time); applies A on the channel axis.

    Low-rank A=I+UV^T starts exactly at identity but not at a dead U=V=0 point.
    """
    def __init__(self, channels: int, kind: str = "lowrank", rank: int = 4):
        super().__init__()
        if not isinstance(channels, int) or channels < 1:
            raise ValueError("channels must be a positive integer")
        if kind not in {"diagonal", "lowrank", "full"}:
            raise ValueError("kind must be diagonal, lowrank, or full")
        self.channels, self.kind = channels, kind
        self.register_buffer("identity", torch.eye(channels))
        if kind == "diagonal":
            self.delta = nn.Parameter(torch.zeros(channels))
        elif kind == "full":
            self.delta = nn.Parameter(torch.zeros(channels, channels))
        else:
            if not isinstance(rank, int) or rank < 1 or rank > channels:
                raise ValueError("rank must lie in [1, channels]")
            self.U = nn.Parameter(0.01 * torch.randn(channels, rank))
            self.V = nn.Parameter(torch.zeros(channels, rank))

    def matrix(self) -> torch.Tensor:
        if self.kind == "diagonal":
            change = torch.diag(self.delta)
        elif self.kind == "full":
            change = self.delta
        else:
            change = self.U @ self.V.T
        return self.identity + change

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3 or x.shape[1] != self.channels:
            raise ValueError("x must have shape (batch, declared_channels, time)")
        return torch.einsum("dc,bct->bdt", self.matrix(), x)

    def trainable_parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
