"""Traditional Gaussian-KDE Cauchy--Schwarz QMI, independent reference.

The score compares p_xy with p_x*p_y; minimize NEGATIVE score. Natural logs.
All self-pairs are retained (V-statistic). No centering, exclusion mask, critic,
learned bandwidth, automatic normalization, or nonnegative score clipping.

``sigma_u`` is the OVERLAP-kernel SD, not the KDE component SD:
    K_ij = exp(-||u_i-u_j||^2 / (2*sigma_u^2)); h_u = sigma_u / sqrt(2).
Unnormalized overlaps give exactly the same CS score as normalized KDE
overlaps. ``normalized_overlap=True`` also gives literal density-integral logs.
The caller owns training-only calibration, paired sampling, and feature scaling.
Requires Python >=3.10 and PyTorch; no repository dependency.
"""
from __future__ import annotations

import math
from typing import Any

import torch
from torch import Tensor


def _rows(x: Tensor, name: str) -> Tensor:
    if not isinstance(x, Tensor) or x.ndim != 2:
        raise ValueError(f"{name} must be a tensor of shape [n>=2, d>=1]")
    if x.shape[0] < 2 or x.shape[1] < 1 or not x.is_floating_point():
        raise ValueError(f"{name} needs n>=2, d>=1 and a real floating dtype")
    if not bool(torch.isfinite(x).all()):
        raise ValueError(f"{name} contains NaN or Inf")
    return x.to(dtype=torch.float64)  # preserves the encoder autograd graph


def _fixed_sigma(sigma: float, name: str) -> float:
    if isinstance(sigma, Tensor) and sigma.requires_grad:
        raise ValueError(f"{name} must be a fixed calibrated scalar")
    s = float(sigma)
    if not math.isfinite(s) or s <= 0:
        raise ValueError(f"{name} must be finite and strictly positive")
    return s


def gaussian_log_gram(
    x: Tensor, sigma: float, *, normalized_overlap: bool = False
) -> Tensor:
    """Log Gaussian density-overlap matrix; its diagonal is included.

    Direct-distance cdist avoids cancellation in ||x||^2+||y||^2-2*x@y.
    The kernel algebra runs in float64, outside mixed-precision autocast.
    """
    x = _rows(x, "x")
    s = _fixed_sigma(sigma, "sigma")
    with torch.autocast(device_type=x.device.type, enabled=False):
        dist = torch.cdist(x, x, p=2, compute_mode="donot_use_mm_for_euclid_dist")
        result = -0.5 * (dist / s).square()
        if normalized_overlap:
            result = result - x.shape[1] * (0.5 * math.log(2 * math.pi) + math.log(s))
        if not bool(torch.isfinite(result).all()):
            raise FloatingPointError("Gaussian log-overlap overflow; inspect feature scale and fixed sigma")
    return result


def _log_weights(weights: Tensor | None, n: int, device: torch.device) -> Tensor:
    if weights is None:
        return torch.full((n,), -math.log(n), dtype=torch.float64, device=device)
    if not isinstance(weights, Tensor) or weights.requires_grad:
        raise ValueError("weights must be a fixed tensor; learned sampling weights are unsupported")
    w = weights.to(device=device, dtype=torch.float64).reshape(-1)
    if w.shape != (n,) or not bool(torch.isfinite(w).all()) or bool((w < 0).any()):
        raise ValueError("weights must be finite, nonnegative, and length n")
    if not bool((w > 0).any()):
        raise ValueError("weights must have positive total mass")
    # Scaling first prevents overflow in a sum of individually finite weights.
    w = w / w.max()
    return (w / w.sum()).log()  # zero-mass observations have log weight -inf


def _score_from_log_overlaps(
    log_k: Tensor, log_l: Tensor, log_w: Tensor
) -> tuple[Tensor, dict[str, Any]]:
    """Internal only: callers must supply actual density-overlap matrices."""
    pair_log_w = log_w[:, None] + log_w[None, :]
    # A = integral p_xy^2.
    log_a = torch.logsumexp(log_k + log_l + pair_log_w, dim=(0, 1))
    # B = integral (p_x*p_y)^2.
    log_x = torch.logsumexp(log_k + pair_log_w, dim=(0, 1))
    log_y = torch.logsumexp(log_l + pair_log_w, dim=(0, 1))
    log_b = log_x + log_y
    # C = integral p_xy*(p_x*p_y): a genuine triple sum, factored by i.
    log_k_w = torch.logsumexp(log_k + log_w[None, :], dim=1)
    log_l_w = torch.logsumexp(log_l + log_w[None, :], dim=1)
    log_c = torch.logsumexp(log_w + log_k_w + log_l_w, dim=0)
    value = log_a + log_b - 2 * log_c
    potentials = torch.stack([value, log_a, log_b, log_c])
    if not bool(torch.isfinite(potentials).all()):
        raise FloatingPointError("nonfinite CS score/potentials; inspect feature scale and bandwidth")
    vals = potentials.detach().cpu().tolist()
    return value, dict(
        cs_qmi_nats=vals[0], log_joint_square=vals[1],
        log_marginal_product_square=vals[2], log_cross_overlap=vals[3],
        n_rows=int(log_k.shape[0]),
        effective_weight_count=float(torch.exp(-torch.logsumexp(2 * log_w, dim=0))),
    )


def cs_qmi(
    u: Tensor,
    v: Tensor | None = None,
    *,
    sigma_u: float,
    sigma_v: float | None = None,
    labels: Tensor | None = None,
    weights: Tensor | None = None,
    normalized_overlap: bool = False,
) -> tuple[Tensor, dict[str, Any]]:
    """Return (CS score, diagnostics); optimize ``loss = -score``.

    Supply exactly one of v and labels. u and v need equal row counts, not equal
    feature dimensions. Categories use counting measure, L_ij=1[label_i=label_j],
    not artificial audio vectors. Labels must have an integer or bool dtype.
    The SAME empirical weights define the joint and both marginals.
    """
    if (v is None) == (labels is None):
        raise ValueError("provide exactly one of v and labels")
    u = _rows(u, "u")
    log_k = gaussian_log_gram(u, sigma_u, normalized_overlap=normalized_overlap)
    if v is not None:
        v = _rows(v, "v")
        if len(v) != len(u) or v.device != u.device or sigma_v is None:
            raise ValueError("v must match u rows/device; sigma_v is required")
        log_l = gaussian_log_gram(v, sigma_v, normalized_overlap=normalized_overlap)
        kind = "continuous_continuous"
    else:
        if not isinstance(labels, Tensor) or labels.numel() != len(u):
            raise ValueError("labels must be a tensor with one category per row")
        if labels.is_floating_point() or labels.is_complex():
            raise ValueError("labels must use an integer or bool dtype")
        if sigma_v is not None:
            raise ValueError("sigma_v does not apply to a counting-measure category kernel")
        y = labels.to(device=u.device).reshape(-1)
        same = y[:, None] == y[None, :]
        log_l = torch.full(same.shape, -torch.inf, dtype=torch.float64, device=u.device)
        log_l = log_l.masked_fill(same, 0.0)
        kind = "continuous_categorical"
    log_w = _log_weights(weights, len(u), u.device)
    with torch.autocast(device_type=u.device.type, enabled=False):
        score, stats = _score_from_log_overlaps(log_k, log_l, log_w)
    stats.update(kernel_kind=kind, normalized_overlap=bool(normalized_overlap))
    return score, stats


@torch.no_grad()
def calibrate_overlap_sigma(
    training_rows: Tensor, *, multiplier: float = 1.0
) -> tuple[float, dict[str, Any]]:
    """Fixed training-panel calibration, never called inside the loss.

    Uses each unordered off-diagonal pair once, INCLUDING repeated-row zero
    distances; PyTorch's lower median is explicit for an even number of pairs.
    No automatic fallback when the median is zero. Calibration does not train
    a model and cannot enforce data provenance: the caller must ensure that the
    rows belong to the permitted training split / declared support only.
    Save the returned scalar and metadata, panel identifiers and checkpoint.
    """
    x = _rows(training_rows, "training_rows").detach()
    mult = _fixed_sigma(multiplier, "multiplier")
    distances = torch.pdist(x, p=2)
    median = float(distances.median())
    sigma = median * mult
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("training-panel median is nonpositive/nonfinite; inspect repeated or collapsed rows")
    return sigma, dict(
        rule="unordered_offdiagonal_lower_median",
        n_rows=int(len(x)), n_pairs=int(distances.numel()), feature_dim=int(x.shape[1]),
        distance_median=median, multiplier=mult,
        overlap_sigma=sigma, kde_component_sd=sigma / math.sqrt(2),
        calibration_scope="caller_must_supply_training_only_rows",
        fixed_after_calibration=True,
    )


@torch.no_grad()
def kernel_diagnostics(rows: Tensor, sigma: float) -> dict[str, float]:
    """Descriptive diagnostics, with no automatic thresholds or loss changes."""
    x = _rows(rows, "rows")
    s = _fixed_sigma(sigma, "sigma")
    distances = torch.pdist(x, p=2)
    values = torch.exp(-0.5 * (distances / s).square())
    qs = torch.quantile(values, torch.tensor([0.05, 0.5, 0.95], device=x.device, dtype=x.dtype))
    return dict(
        offdiag_mean=float(values.mean()), offdiag_q05=float(qs[0]),
        offdiag_median=float(qs[1]), offdiag_q95=float(qs[2]),
        exact_duplicate_pair_fraction=float((distances == 0).double().mean()),
        mean_feature_variance=float(x.var(dim=0, unbiased=False).mean()),
    )
