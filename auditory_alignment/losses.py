"""Objectives for the kernel-CS round. The kernel CS, category kernel, FMCA-logdet and single-positive InfoNCE are the
package reference implementation, imported unchanged from losses_reference.py (verbatim copy of
AUDITORY_KERNEL_CS_FULL_EXPERIMENTS_SERVER_v1_20261005/reference/losses.py). Added here: the class-prototype
(multi-positive) NCE for the private category task, as the reference file requires.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F

from .losses_reference import cs_qmi, fmca_logdet_loss, multiscale_cs_loss, symmetric_infonce  # noqa: F401


def prototype_nce(u, labels, prototypes, temperature):
    """Class-prototype NCE: each row is classified against the L2-normalised class prototypes, so other trials of the
    same class are never treated as instance negatives. Equivalent to a cosine-softmax classifier."""
    logits = F.normalize(u, dim=1) @ F.normalize(prototypes, dim=1).T / temperature
    return F.cross_entropy(logits, labels.long())


def deduplicated_infonce(u, v, keys, temperature):
    """Symmetric InfoNCE where rows sharing the same stimulus key are positives of each other (multi-positive);
    with unique keys this equals the reference single-positive loss."""
    u, v = F.normalize(u.double(), dim=1), F.normalize(v.double(), dim=1)
    logits = u @ v.T / temperature
    pos = (keys[:, None] == keys[None, :]).double()
    lp1 = logits - torch.logsumexp(logits, dim=1, keepdim=True)
    lp2 = logits.T - torch.logsumexp(logits.T, dim=1, keepdim=True)
    return -((lp1 * pos).sum(1) / pos.sum(1)).mean() / 2 - ((lp2 * pos).sum(1) / pos.sum(1)).mean() / 2
