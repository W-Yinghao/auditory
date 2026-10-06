"""Numerical reference for traditional kernel CS-QMI and comparison objectives.

This file contains no dataset loader, no neural critic, and no variational CS method.
Gaussian sigmas are the pairwise-kernel bandwidths. The CS computation retains all
self-pairs and uses a single, consistent (optionally weighted) empirical measure.

Inputs to all losses are low-dimensional paired rows, not flattened long sequences.
Representation normalization and pair sampling belong to the calling experiment.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import torch
import torch.nn.functional as F
from torch import Tensor


def _rows(x: Tensor, name: str) -> Tensor:
    if x.ndim != 2 or x.shape[0] < 2 or x.shape[1] < 1:
        raise ValueError(f"{name} must have shape [n>=2, d>=1]; got {tuple(x.shape)}")
    if not torch.isfinite(x).all():
        raise ValueError(f"{name} contains NaN or Inf")
    # .to() preserves the graph; kernel algebra is deliberately outside fp16.
    return x.to(dtype=torch.float64)


def gaussian_log_gram(x: Tensor, sigma: float) -> Tensor:
    """Log of the unnormalized Gaussian overlap Gram matrix; diagonal is retained."""
    x = _rows(x, "x")
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("sigma must be finite and strictly positive")
    xx = x.square().sum(dim=1, keepdim=True)
    distances2 = (xx + xx.T - 2 * (x @ x.T)).clamp_min(0)
    return -distances2 / (2 * sigma**2)


def label_log_gram(labels: Tensor) -> Tensor:
    """Counting-measure category kernel: log(1[y_i=y_j]); no category merging."""
    y = labels.reshape(-1)
    if y.numel() < 2:
        raise ValueError("at least two label observations are needed")
    same = y[:, None] == y[None, :]
    out = torch.full(same.shape, -torch.inf, dtype=torch.float64, device=y.device)
    return out.masked_fill(same, 0.0)


def cs_qmi_from_log_grams(
    log_k: Tensor, log_l: Tensor, weights: Tensor | None = None
) -> tuple[Tensor, dict[str, float]]:
    """Return CS-QMI and three log information potentials, in natural-log units.

    The loss to minimize is -value. This is a KDE/information-potential objective,
    not a Shannon-MI bound. No clipping of the returned objective is performed.
    """
    if log_k.ndim != 2 or log_k.shape[0] != log_k.shape[1]:
        raise ValueError("log_k must be square")
    if log_l.shape != log_k.shape or log_k.shape[0] < 2:
        raise ValueError("equal square Gram shapes with n>=2 are required")
    if log_k.device != log_l.device:
        raise ValueError("both kernels must be on the same device")
    k, l = log_k.double(), log_l.double()
    n = k.shape[0]
    for name, m in (("log_k", k), ("log_l", l)):
        if torch.isnan(m).any() or torch.isposinf(m).any():
            raise ValueError(f"{name} has invalid entries")
    if weights is None:
        lw = torch.full((n,), -math.log(n), dtype=torch.float64, device=k.device)
    else:
        w = weights.to(device=k.device, dtype=torch.float64).reshape(-1)
        if w.shape != (n,) or not torch.isfinite(w).all() or (w < 0).any():
            raise ValueError("weights must be finite, nonnegative, and length n")
        if w.sum() <= 0:
            raise ValueError("weights must have positive total mass")
        lw = (w / w.sum()).log()
    pair_lw = lw[:, None] + lw[None, :]
    log_a = torch.logsumexp(k + l + pair_lw, dim=(0, 1))
    log_mu = torch.logsumexp(k + pair_lw, dim=(0, 1))
    log_mv = torch.logsumexp(l + pair_lw, dim=(0, 1))
    log_ku = torch.logsumexp(k + lw[None, :], dim=1)
    log_lv = torch.logsumexp(l + lw[None, :], dim=1)
    log_c = torch.logsumexp(lw + log_ku + log_lv, dim=0)
    value = log_a + log_mu + log_mv - 2 * log_c
    stats = {
        "cs_qmi_nats": float(value.detach()),
        "log_joint_square": float(log_a.detach()),
        "log_marginal_product_square": float((log_mu + log_mv).detach()),
        "log_cross_overlap": float(log_c.detach()),
        "n_rows": n,
    }
    return value, stats


def cs_qmi(
    u: Tensor,
    v: Tensor | None = None,
    *,
    sigma_u: float,
    sigma_v: float | None = None,
    labels: Tensor | None = None,
    weights: Tensor | None = None,
) -> tuple[Tensor, dict[str, float]]:
    """Continuous-continuous or continuous-categorical traditional CS-QMI."""
    if (v is None) == (labels is None):
        raise ValueError("provide exactly one of v and labels")
    u = _rows(u, "u")
    log_k = gaussian_log_gram(u, sigma_u)
    if v is not None:
        v = _rows(v, "v")
        if len(v) != len(u) or v.device != u.device or sigma_v is None:
            raise ValueError("v must match rows/device; sigma_v is required")
        log_l = gaussian_log_gram(v, sigma_v)
    else:
        assert labels is not None
        if labels.numel() != len(u):
            raise ValueError("labels must have one value per paired row")
        log_l = label_log_gram(labels.to(u.device))
    return cs_qmi_from_log_grams(log_k, log_l, weights)


def multiscale_cs_loss(
    u: Tensor,
    v: Tensor | None = None,
    *,
    sigma_u: float,
    sigma_v: float | None = None,
    scales: Sequence[float] = (0.5, 1.0, 2.0),
    labels: Tensor | None = None,
    weights: Tensor | None = None,
) -> tuple[Tensor, dict[str, Any]]:
    """Negative average of single-scale CS objectives, not CS of a merged kernel."""
    if not scales:
        raise ValueError("scales must be nonempty")
    scores, details = [], []
    for scale in scales:
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("all scale multipliers must be positive")
        value, stats = cs_qmi(
            u, v, sigma_u=sigma_u * scale,
            sigma_v=None if sigma_v is None else sigma_v * scale,
            labels=labels, weights=weights,
        )
        scores.append(value)
        details.append({"scale": float(scale), **stats})
    score = torch.stack(scores).mean()
    return -score, {"mean_cs_nats": float(score.detach()), "scales": details}


def fmca_logdet_loss(
    u: Tensor, v: Tensor, *, ridge_u: float = 1e-3, ridge_v: float = 1e-3
) -> Tensor:
    """Centered FMCA logdet; ridges here are absolute, pre-calibrated constants.

    Experiment configs use relative ridge. Convert using training calibration
    covariance scales outside this function, save the resulting absolute ridges,
    and keep them fixed for that fit. No eigentruncation or clipping is used here.
    """
    u, v = _rows(u, "u"), _rows(v, "v")
    if len(u) != len(v) or u.device != v.device:
        raise ValueError("paired rows/devices do not match")
    if not all(math.isfinite(e) and e > 0 for e in (ridge_u, ridge_v)):
        raise ValueError("positive finite ridges are required")
    u, v = u - u.mean(0), v - v.mean(0)
    n = len(u)
    ru = u.T @ u / n + ridge_u * torch.eye(u.shape[1], device=u.device, dtype=u.dtype)
    rv = v.T @ v / n + ridge_v * torch.eye(v.shape[1], device=v.device, dtype=v.dtype)
    p = u.T @ v / n
    joint = torch.cat((torch.cat((ru, p), 1), torch.cat((p.T, rv), 1)), 0)

    def logdet_pd(x: Tensor) -> Tensor:
        return 2 * torch.linalg.cholesky((x + x.T) / 2).diagonal().log().sum()

    return logdet_pd(joint) - logdet_pd(ru) - logdet_pd(rv)


def symmetric_infonce(u: Tensor, v: Tensor, temperature: float = 0.1) -> Tensor:
    """Single-positive baseline. Caller must handle duplicate stimulus anchors.

    This is NOT the private categorical loss: use prototypes or a validated
    multi-positive implementation when multiple rows have the same class.
    """
    u, v = _rows(u, "u"), _rows(v, "v")
    if u.shape != v.shape or u.device != v.device:
        raise ValueError("InfoNCE requires matched [n,d] arrays on one device")
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be positive and finite")
    logits = F.normalize(u, dim=1) @ F.normalize(v, dim=1).T / temperature
    y = torch.arange(len(u), device=u.device)
    return (F.cross_entropy(logits, y) + F.cross_entropy(logits.T, y)) / 2
