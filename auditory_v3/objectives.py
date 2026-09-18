"""R3 training objectives.

The functions here deliberately operate on tensors already assembled by the
training runner.  They do not know about participant identifiers or data
paths.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def supervised_ce(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    """Cross entropy averaged over the two views of each original trial."""
    if logits.ndim == 3:
        if logits.shape[1] != 2:
            raise ValueError("logits must have two views")
        logits = logits.reshape(-1, logits.shape[-1])
        labels = labels.reshape(-1).repeat_interleave(2)
    elif logits.ndim == 2:
        labels = labels.reshape(-1)
        if logits.shape[0] != labels.shape[0]:
            raise ValueError("one label is required per logit row")
    else:
        raise ValueError("logits must have shape [trials, views, classes] or [rows, classes]")
    return F.cross_entropy(logits, labels)


def nt_xent_loss(views: torch.Tensor, temperature: float = 0.2) -> torch.Tensor:
    """SimCLR NT-Xent for ``[trials, 2, dimensions]`` views."""
    if views.ndim != 3 or views.shape[1] != 2:
        raise ValueError("views must have shape [trials, 2, dimensions]")
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    n = views.shape[0]
    if n < 2:
        raise ValueError("NT-Xent needs at least two original trials")
    z = F.normalize(views.reshape(2 * n, -1), dim=-1)
    logits = z @ z.T / temperature
    eye = torch.eye(2 * n, dtype=torch.bool, device=views.device)
    logits = logits.masked_fill(eye, float("-inf"))
    positive = torch.arange(2 * n, device=views.device)
    positive = positive ^ 1
    return F.cross_entropy(logits, positive)


def quartet_supcon_loss(embeddings: torch.Tensor, labels: torch.Tensor,
                        quartet_ids: torch.Tensor, temperature: float = 0.2) -> torch.Tensor:
    """Within-quartet SupCon, with two positives and six denominator terms.

    ``embeddings`` is ``[trials, 2, dim]`` and every quartet has two trials of
    each class.  The two views of the anchor's own trial are excluded from the
    denominator; positives are the two views of the other same-class trial.
    """
    if embeddings.ndim != 3 or embeddings.shape[1] != 2:
        raise ValueError("embeddings must have shape [trials, 2, dimensions]")
    labels = labels.reshape(-1)
    quartet_ids = quartet_ids.reshape(-1)
    n = embeddings.shape[0]
    if labels.numel() != n or quartet_ids.numel() != n:
        raise ValueError("labels and quartet_ids must have one value per trial")
    unique, counts = torch.unique(quartet_ids, sorted=True, return_counts=True)
    if unique.numel() == 0 or not torch.all(counts == 4):
        raise ValueError("each quartet must contain exactly four trials")
    order = torch.argsort(quartet_ids, stable=True)
    z = F.normalize(embeddings[order], dim=-1).reshape(-1, 4, 2, embeddings.shape[-1])
    y = labels[order].reshape(-1, 4)
    if not torch.all((y == y[:, :1]).sum(dim=1) == 2):
        raise ValueError("each quartet must contain two trials per class")
    # Flatten the two views, then construct masks at the original-trial level.
    sims = torch.einsum("gvd,gwd->gvw", z.reshape(-1, 8, z.shape[-1]),
                        z.reshape(-1, 8, z.shape[-1])) / temperature
    trial = torch.arange(4, device=embeddings.device).repeat_interleave(2)
    same_trial = trial[None, :, None] == trial[None, None, :]
    label_view = y.repeat_interleave(2, dim=1)
    positives = (label_view[:, :, None] == label_view[:, None, :]) & ~same_trial
    denominator = ~same_trial
    if not torch.all(positives.sum(dim=-1) == 2) or not torch.all(denominator.sum(dim=-1) == 6):
        raise ValueError("quartet masks must have two positives and six denominator terms")
    den = torch.logsumexp(sims.masked_fill(~denominator, float("-inf")), dim=-1)
    positive_logprob = sims.masked_fill(~positives, float("-inf")) - den.unsqueeze(-1)
    loss = -positive_logprob.masked_fill(~positives, 0.0).sum(dim=-1) / 2.0
    if loss.numel() == 0:
        raise ValueError("no quartets")
    return loss.mean()


def match_objective(logits: torch.Tensor, labels: torch.Tensor,
                    embeddings: torch.Tensor, quartet_ids: torch.Tensor,
                    temperature: float = 0.2) -> torch.Tensor:
    """The frozen MATCH objective: CE + 0.1 * quartet SupCon."""
    return supervised_ce(logits, labels) + 0.1 * quartet_supcon_loss(
        embeddings, labels, quartet_ids, temperature
    )


# Friendly aliases used by runners and tests.
sup_ce_loss = supervised_ce
sim_nt_xent_loss = nt_xent_loss
match_loss = match_objective
sup_loss = supervised_ce
sim_loss = nt_xent_loss
