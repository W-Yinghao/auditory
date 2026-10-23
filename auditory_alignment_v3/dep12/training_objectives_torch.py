"""Matched-episode loss references; no training loop or data sampler.

All objectives consume already L2-normalized, 32-D EEG/audio rows from ONE
listener episode with n>=4. Audio is fixed (requires_grad=False). The sampler
must make every off-diagonal pair an eligible contrast: no near-neighbor or
same-content masking is applied inside these losses.

CS is the traditional, self-pair-inclusive Gaussian-Parzen statistic.
"Permutation-centered CS" is a difference of CS scores, not a new divergence.
Both the paired and permuted terms retain gradients to EEG outputs.
"""
from __future__ import annotations

import math
from typing import Any

import torch
from torch import Tensor
from torch.nn import functional as F


def _fixed_positive(value: Any, name: str) -> float:
    if isinstance(value, Tensor) and value.requires_grad:
        raise ValueError(f"{name} must be fixed, not trainable")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and strictly positive")
    return result


def _fixed_real(value: Any, name: str) -> float:
    if isinstance(value, Tensor) and value.requires_grad:
        raise ValueError(f"{name} must be fixed, not trainable")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _episode(u: Tensor, y: Tensor, *, unit_norm_atol: float) -> tuple[Tensor, Tensor]:
    if not isinstance(u, Tensor) or not isinstance(y, Tensor):
        raise ValueError("u and y must be torch tensors")
    if u.ndim != 2 or y.ndim != 2 or u.shape != y.shape:
        raise ValueError("u and y must have matching (n,32) shapes")
    if u.shape[0] < 4 or u.shape[1] != 32:
        raise ValueError("A single-listener episode needs n>=4 and 32-D rows")
    if not u.is_floating_point() or not y.is_floating_point():
        raise ValueError("u and y must be real floating tensors")
    if u.device != y.device:
        raise ValueError("u and y must be on the same device")
    if y.requires_grad:
        raise ValueError("Audio y must be fixed (requires_grad=False)")
    if not bool(torch.isfinite(u).all()) or not bool(torch.isfinite(y).all()):
        raise ValueError("u/y contain NaN or Inf")
    tol = _fixed_positive(unit_norm_atol, "unit_norm_atol")
    with torch.no_grad():
        for value, name in ((u, "u"), (y, "y")):
            maximum = float((value.to(torch.float64).norm(dim=1) - 1.0).abs().max())
            if maximum > tol:
                raise ValueError(
                    f"{name} rows must already be L2-normalized; "
                    f"max norm error {maximum:.6g} exceeds {tol:.6g}"
                )
    return u, y


def _log_gram(rows: Tensor, sigma: float) -> Tensor:
    rows64 = rows.to(dtype=torch.float64)  # keeps the EEG autograd path
    with torch.autocast(device_type=rows.device.type, enabled=False):
        distance = torch.cdist(
            rows64, rows64, p=2, compute_mode="donot_use_mm_for_euclid_dist"
        )
        log_gram = -0.5 * (distance / sigma).square()
    if not bool(torch.isfinite(log_gram).all()):
        raise FloatingPointError("Nonfinite CS log Gram; inspect fixed sigma/scale")
    return log_gram


def _cs_score(log_k: Tensor, log_l: Tensor) -> tuple[Tensor, dict[str, Tensor]]:
    n = len(log_k)
    ln = math.log(n)
    log_a = torch.logsumexp(log_k + log_l, dim=(0, 1)) - 2.0 * ln
    log_k_mean = torch.logsumexp(log_k, dim=(0, 1)) - 2.0 * ln
    log_l_mean = torch.logsumexp(log_l, dim=(0, 1)) - 2.0 * ln
    log_b = log_k_mean + log_l_mean
    row_log_k = torch.logsumexp(log_k, dim=1) - ln
    row_log_l = torch.logsumexp(log_l, dim=1) - ln
    log_c = torch.logsumexp(row_log_k + row_log_l, dim=0) - ln
    score = log_a + log_b - 2.0 * log_c
    if not bool(torch.isfinite(score)):
        raise FloatingPointError("Nonfinite CS score")
    return score, {
        "log_joint_square": log_a,
        "log_marginal_product_square": log_b,
        "log_cross_overlap": log_c,
    }


def _base_stats(u: Tensor, name: str) -> dict[str, Any]:
    return {
        "objective": name,
        "n_rows": int(len(u)),
        "feature_dim": 32,
        "audio_fixed": True,
        "input_unit_normalization_performed_inside_loss": False,
        "episode_unit": "one_listener",
        "sampler_contract_assumed": "all_offdiagonal_pairs_are_eligible_negatives",
    }


def _float(value: Tensor) -> float:
    return float(value.detach().cpu())


def _validate_permutations(
    permutations: Any, n: int, device: torch.device, *, require_derangements: bool
) -> Tensor:
    p = torch.as_tensor(permutations, device=device)
    if p.ndim != 2 or p.shape[0] < 4 or p.shape[1] != n:
        raise ValueError("CS needs explicit permutations with shape (B>=4,n)")
    if p.dtype not in (
        torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8
    ):
        raise ValueError("Permutation indices must have integer dtype")
    p = p.to(torch.int64)
    expected = torch.arange(n, device=device)
    if not bool(torch.all(torch.sort(p, dim=1).values == expected[None, :])):
        raise ValueError("Each permutation must contain all indices 0..n-1 exactly once")
    fixed = p == expected[None, :]
    if bool(torch.any(torch.all(fixed, dim=1))):
        raise ValueError("Identity permutations are not allowed for training")
    if require_derangements and bool(torch.any(fixed)):
        raise ValueError(
            "Training nulls must be derangements: no row may retain its true match"
        )
    return p


def raw_cs(
    u: Tensor,
    y: Tensor,
    *,
    sigma_u: float,
    sigma_y: float,
    unit_norm_atol: float = 1e-4,
) -> tuple[Tensor, dict[str, Any]]:
    """Minimize loss=-D_CS; returns (loss, detached diagnostic dictionary)."""
    u, y = _episode(u, y, unit_norm_atol=unit_norm_atol)
    su, sy = _fixed_positive(sigma_u, "sigma_u"), _fixed_positive(sigma_y, "sigma_y")
    with torch.autocast(device_type=u.device.type, enabled=False):
        score, potentials = _cs_score(_log_gram(u, su), _log_gram(y, sy))
        loss = -score
    stats = _base_stats(u, "raw_Parzen_CS")
    stats.update(
        loss=_float(loss), raw_cs_nats=_float(score), sigma_u=su, sigma_y=sy,
        includes_self_pairs=True, compute_dtype="float64",
        score_nonnegative_clipping=False,
    )
    stats.update({name: _float(value) for name, value in potentials.items()})
    return loss, stats


def centered_cs(
    u: Tensor,
    y: Tensor,
    *,
    sigma_u: float,
    sigma_y: float,
    permutations: Any,
    require_derangements: bool = True,
    unit_norm_atol: float = 1e-4,
) -> tuple[Tensor, dict[str, Any]]:
    """Minimize -(D_paired - mean_b D_permuted), with BOTH terms differentiable.

    A whole row/column permutation of the same audio Gram is used. There is no
    pair mask, kernel centering, learned bandwidth, stop-gradient null, z-score,
    nonnegative clipping, or claim of an unbiased/new divergence estimator.
    """
    u, y = _episode(u, y, unit_norm_atol=unit_norm_atol)
    su, sy = _fixed_positive(sigma_u, "sigma_u"), _fixed_positive(sigma_y, "sigma_y")
    p = _validate_permutations(
        permutations, len(u), u.device, require_derangements=require_derangements
    )
    with torch.autocast(device_type=u.device.type, enabled=False):
        log_k, log_l = _log_gram(u, su), _log_gram(y, sy)
        real, potentials = _cs_score(log_k, log_l)
        wrong_scores = []
        for indices in p:
            wrong_l = log_l.index_select(0, indices).index_select(1, indices)
            wrong, _ = _cs_score(log_k, wrong_l)
            wrong_scores.append(wrong)
        wrong = torch.stack(wrong_scores)
        wrong_mean = wrong.mean()
        excess = real - wrong_mean
        loss = -excess
    if not bool(torch.isfinite(loss)):
        raise FloatingPointError("Nonfinite centered CS loss")
    fixed_fraction = float((p == torch.arange(len(u), device=u.device)[None, :]).double().mean())
    stats = _base_stats(u, "permutation_centered_Parzen_CS")
    stats.update(
        loss=_float(loss), raw_cs_nats=_float(real),
        training_null_mean_nats=_float(wrong_mean),
        centered_cs_nats=_float(excess),
        training_null_scores_nats=wrong.detach().cpu().tolist(),
        n_permutations=int(len(p)),
        n_unique_permutations=int(torch.unique(p, dim=0).shape[0]),
        null_fixed_pair_fraction=fixed_fraction,
        require_derangements=bool(require_derangements),
        null_stop_gradient=False,
        sigma_u=su, sigma_y=sy,
        includes_self_pairs=True, compute_dtype="float64",
        score_nonnegative_clipping=False,
        new_divergence_claim=False,
    )
    stats.update({name: _float(value) for name, value in potentials.items()})
    return loss, stats


def _cosine_logits(u: Tensor, y: Tensor, temperature: float) -> Tensor:
    dtype = torch.float64 if torch.float64 in (u.dtype, y.dtype) else torch.float32
    return (u.to(dtype) @ y.to(dtype).T) / temperature


def symmetric_info_nce(
    u: Tensor,
    y: Tensor,
    *,
    temperature: float = 0.07,
    unit_norm_atol: float = 1e-4,
) -> tuple[Tensor, dict[str, Any]]:
    """Mean of EEG->audio and audio->EEG cross entropy; no trainable scale."""
    u, y = _episode(u, y, unit_norm_atol=unit_norm_atol)
    temp = _fixed_positive(temperature, "temperature")
    with torch.autocast(device_type=u.device.type, enabled=False):
        logits = _cosine_logits(u, y, temp)
        targets = torch.arange(len(u), device=u.device)
        loss_eeg = F.cross_entropy(logits, targets)
        loss_audio = F.cross_entropy(logits.T, targets)
        loss = 0.5 * (loss_eeg + loss_audio)
    stats = _base_stats(u, "symmetric_InfoNCE")
    stats.update(
        loss=_float(loss), loss_eeg_to_audio=_float(loss_eeg),
        loss_audio_to_eeg=_float(loss_audio),
        temperature=temp, trainable_scale=False, n_negatives_per_row=int(len(u)-1),
        compute_dtype=str(logits.dtype),
    )
    return loss, stats


def sigmoid_pair_loss(
    u: Tensor,
    y: Tensor,
    *,
    temperature: float = 0.07,
    bias: float | None = None,
    unit_norm_atol: float = 1e-4,
) -> tuple[Tensor, dict[str, Any]]:
    """All-pair logistic sum/n, with diagonal positives and off-diagonal negatives.

    Default fixed bias=-log(n-1). This is a declared SigLIP-style objective,
    not a claim to reproduce every original SigLIP optimization choice.
    """
    u, y = _episode(u, y, unit_norm_atol=unit_norm_atol)
    temp = _fixed_positive(temperature, "temperature")
    actual_bias = -math.log(len(u) - 1) if bias is None else _fixed_real(bias, "bias")
    with torch.autocast(device_type=u.device.type, enabled=False):
        logits = _cosine_logits(u, y, temp) + actual_bias
        targets = torch.eye(len(u), device=u.device, dtype=logits.dtype)
        loss = F.binary_cross_entropy_with_logits(logits, targets, reduction="sum") / len(u)
    stats = _base_stats(u, "fixed_scale_sigmoid_all_pair")
    stats.update(
        loss=_float(loss), temperature=temp, bias=actual_bias,
        bias_rule="minus_log_n_minus_1" if bias is None else "caller_fixed",
        normalization="sum_all_n_squared_pairs_divided_by_n",
        trainable_scale=False, trainable_bias=False, compute_dtype=str(logits.dtype),
    )
    return loss, stats

