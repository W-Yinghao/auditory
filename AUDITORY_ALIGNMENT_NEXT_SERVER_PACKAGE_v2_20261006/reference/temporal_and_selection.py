"""Reference tensor interfaces only; no real EEG loader or foundation-model runner.

Temporal independence here refers to the tensor passed to crop_windows. Upstream
filtering/normalization may have wider raw-signal support and must be reported.
"""
from __future__ import annotations
import math
import torch
from torch import Tensor, nn
import torch.nn.functional as F


def crop_windows(x: Tensor, anchors: Tensor, start: int, stop: int) -> Tensor:
    """Extract [anchor+start, anchor+stop) for each item; reject missing support.

    x [B,C,T], anchors [B], integer sample offsets. No time stretching and no
    silently added outside EEG. Cropping is differentiable with respect to x.
    """
    if x.ndim != 3 or anchors.ndim != 1 or anchors.numel() != x.shape[0]:
        raise ValueError("Expected x [B,C,T] and anchors [B].")
    if anchors.dtype not in (torch.int32, torch.int64):
        raise ValueError("Anchors must be integer sample indices.")
    if stop <= start:
        raise ValueError("A window must have positive length.")
    a=anchors.to(device=x.device, dtype=torch.long)
    indices=a[:,None]+torch.arange(start,stop,device=x.device)[None,:]
    if torch.any(indices < 0) or torch.any(indices >= x.shape[-1]):
        raise ValueError("Requested support is outside the supplied tensor.")
    return torch.gather(x, 2, indices[:,None,:].expand(-1,x.shape[1],-1))


class TimeTokenEncoder(nn.Module):
    """Small reference: preserves one output token per supplied input sample.

    This is NOT a tuned model or the proposed full production architecture.
    Padding is within the already-cropped input. Normalization is channel-wise
    per time point, not over the full recording.
    """
    def __init__(self, channels: int, hidden: int=16, output: int=16) -> None:
        super().__init__()
        if min(channels,hidden,output) <= 0:
            raise ValueError("Dimensions must be positive.")
        self.spatial=nn.Conv1d(channels,hidden,1)
        self.temporal=nn.Conv1d(hidden,hidden,5,padding=2)
        self.norm=nn.LayerNorm(hidden)
        self.proj=nn.Linear(hidden,output)

    def forward(self, patch: Tensor) -> Tensor:
        if patch.ndim != 3:
            raise ValueError("Expected patch [B,C,L].")
        z=self.temporal(F.gelu(self.spatial(patch))).transpose(1,2)
        return self.proj(F.gelu(self.norm(z)))


def two_stream_selection_loss(scores: Tensor, attended: Tensor, temperature: float=1.0) -> Tensor:
    """Two simultaneous REAL streams; label is instructed attended candidate."""
    if scores.ndim != 2 or scores.shape[1] != 2 or scores.shape[0] == 0:
        raise ValueError("scores must have shape [N>0,2].")
    if attended.shape != (scores.shape[0],) or attended.dtype not in (torch.int32,torch.int64):
        raise ValueError("attended must be an integer label vector [N].")
    if torch.any((attended < 0) | (attended > 1)):
        raise ValueError("Two-candidate labels must be 0 or 1.")
    if not math.isfinite(temperature) or temperature <= 0 or not torch.isfinite(scores).all():
        raise ValueError("Scores and temperature must be finite; temperature must be positive.")
    return F.cross_entropy(scores/temperature, attended.to(device=scores.device,dtype=torch.long))


def query_nll_bits(scores: Tensor, labels: Tensor, temperature: float=1.0) -> Tensor:
    """Per-query log loss. Reports probabilities, not Shannon neural information."""
    if scores.ndim != 2 or scores.shape[0] == 0 or scores.shape[1] < 2:
        raise ValueError("Expected scores [N>0,K>=2].")
    if labels.shape != (scores.shape[0],):
        raise ValueError("labels must match the query rows.")
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be positive and finite.")
    return F.cross_entropy(scores/temperature, labels.to(device=scores.device,dtype=torch.long),reduction="none")/math.log(2)


def permuted_query_gain_identity(scores: Tensor, labels: Tensor, permutation: Tensor, temperature: float=1.0) -> tuple[Tensor,Tensor]:
    """Return mean mismatch-minus-true loss and its fixed-pool margin identity.

    Only valid when mismatch is a permutation of the exact same rows with the
    same candidate pool, weights and temperature. This is a mathematical test,
    not a claim that gain alone establishes clinical or biological validity.
    """
    n=scores.shape[0]
    perm=permutation.to(device=scores.device,dtype=torch.long)
    if perm.shape != (n,) or not torch.equal(torch.sort(perm).values,torch.arange(n,device=scores.device)):
        raise ValueError("permutation must contain every query row exactly once.")
    y=labels.to(device=scores.device,dtype=torch.long)
    gain=(query_nll_bits(scores[perm],y,temperature)-query_nll_bits(scores,y,temperature)).mean()
    i=torch.arange(n,device=scores.device)
    margin=(scores[i,y]-scores[perm,y]).mean()/(temperature*math.log(2))
    return gain,margin
