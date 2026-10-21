"""Auditable Torch objectives for ALN4 time-bank source episodes.

Depends on the unchanged classical ``cs_qmi_reference.py`` placed alongside
this file (or importable on PYTHONPATH). This is an objective/reference layer,
not a dataset loader, model adapter, sampler, or production training runner.

One episode contains ONE person's separate support and query. EEG features
must have been computed independently from fixed physical windows by the same
backbone/projector; this module cannot establish their data provenance. Inputs
are [N,K,D] EEG-only features and [N,D_audio] fixed audio features. The caller
owns shared per-view L2 normalization and source-fit bandwidth calibration.

TCS: classical KDE-CS on (U,T) x A, counting measure on time slots, q^2 mixture.
TNCE: q-weighted symmetric masked multi-positive InfoNCE across the same slots.
GCS: q-weighted feature pool, L2 normalize, then classical within-person CS.
All use the same support-only delta adaptation and live-prior first-order
query objective. No higher-order derivative through cdist is required.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Iterable, Sequence

import torch
from torch import Tensor
import torch.nn.functional as F

if __package__:
    from .cs_qmi_reference import cs_qmi, gaussian_log_gram
else:
    from cs_qmi_reference import cs_qmi, gaussian_log_gram


@dataclass(frozen=True)
class ViewBatch:
    u: Tensor
    v: Tensor
    sigma_u: float
    sigma_v: float
    sigma_pooled_u: float | None = None
    name: str = "view"


def _scalar(value, name, *, allow_zero=False):
    if isinstance(value, Tensor):
        if value.ndim != 0 or value.requires_grad:
            raise ValueError(f"{name} must be one fixed scalar")
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be one fixed scalar") from exc
    if not math.isfinite(value) or (value < 0 if allow_zero else value <= 0):
        raise ValueError(f"{name} is outside its finite valid range")
    return value


def _validate_view(view: ViewBatch):
    u, v = view.u, view.v
    if not isinstance(u, Tensor) or not isinstance(v, Tensor):
        raise ValueError("EEG/audio features must be tensors")
    if u.ndim != 3 or v.ndim != 2 or len(u) != len(v):
        raise ValueError("expected u=[N,K,D_u], v=[N,D_v] with matching N")
    if len(u) < 2 or min(u.shape[1:]) < 1 or v.shape[1] < 1:
        raise ValueError("nonempty features/slots and N>=2 required")
    if not u.is_floating_point() or not v.is_floating_point() or u.device != v.device:
        raise ValueError("real floating features on the same device required")
    if not bool(torch.isfinite(u).all()) or not bool(torch.isfinite(v).all()):
        raise ValueError("nonfinite EEG/audio feature")
    if v.requires_grad:
        raise ValueError("audio features are fixed in this recipe; detach fixed audio heads")
    _scalar(view.sigma_u, "sigma_u")
    _scalar(view.sigma_v, "sigma_v")
    if view.sigma_pooled_u is not None:
        _scalar(view.sigma_pooled_u, "sigma_pooled_u")
    return u.to(torch.float64), v.to(torch.float64)


def _logits(logits: Tensor, slots: int, device):
    if not isinstance(logits, Tensor) or logits.shape != (slots,):
        raise ValueError("one shared gate logit per time slot required")
    if logits.device != device or not logits.is_floating_point():
        raise ValueError("gate logits must be floating and on the feature device")
    if not bool(torch.isfinite(logits).all()):
        raise ValueError("nonfinite gate logits")
    return logits.to(torch.float64)


def _as_list(value: Tensor):
    return value.detach().cpu().tolist()


def tcs_slot_log_potentials(view: ViewBatch) -> tuple[Tensor, Tensor, Tensor]:
    """Graph-preserving log A_k, B_k, C_k; one sigma across all slots."""
    u, v = _validate_view(view)
    log_l = gaussian_log_gram(v, view.sigma_v)
    nlog = math.log(len(u))
    audio_square = torch.logsumexp(log_l, dim=(0, 1)) - 2 * nlog
    audio_rows = torch.logsumexp(log_l, dim=1)
    la, lb, lc = [], [], []
    for k in range(u.shape[1]):
        log_k = gaussian_log_gram(u[:, k], view.sigma_u)
        la.append(torch.logsumexp(log_k + log_l, dim=(0, 1)) - 2 * nlog)
        lb.append(torch.logsumexp(log_k, dim=(0, 1)) - 2 * nlog + audio_square)
        lc.append(torch.logsumexp(torch.logsumexp(log_k, dim=1) + audio_rows, dim=0) - 3 * nlog)
    return torch.stack(la), torch.stack(lb), torch.stack(lc)


def tcs_from_log_potentials(potentials: tuple[Tensor, Tensor, Tensor], logits: Tensor):
    la, lb, lc = potentials
    if la.ndim != 1 or lb.shape != la.shape or lc.shape != la.shape:
        raise ValueError("one equally sized potential vector per slot required")
    b = _logits(logits, len(la), la.device)
    log_q = F.log_softmax(b, dim=0)
    log_a = torch.logsumexp(2 * log_q + la, dim=0)
    log_b = torch.logsumexp(2 * log_q + lb, dim=0)
    log_c = torch.logsumexp(2 * log_q + lc, dim=0)
    score = log_a + log_b - 2 * log_c
    if not bool(torch.isfinite(score)):
        raise FloatingPointError("nonfinite time-tagged CS score")
    stats = {
        "score_nats": float(score.detach()),
        "q": _as_list(log_q.exp()),
        "normalized_q_squared": _as_list(F.softmax(2 * log_q, dim=0)),
        "log_A_slot": _as_list(la), "log_B_slot": _as_list(lb), "log_C_slot": _as_list(lc),
        "log_A": float(log_a.detach()), "log_B": float(log_b.detach()), "log_C": float(log_c.detach()),
        "slot_scores_nats": _as_list(la + lb - 2 * lc),
        "A_shares": _as_list(F.softmax(2 * log_q + la, dim=0)),
        "B_shares": _as_list(F.softmax(2 * log_q + lb, dim=0)),
        "C_shares": _as_list(F.softmax(2 * log_q + lc, dim=0)),
        "potential_normalization": "common Gaussian constants omitted within each view",
    }
    return score, stats


def temporal_cs_score(view: ViewBatch, logits: Tensor):
    return tcs_from_log_potentials(tcs_slot_log_potentials(view), logits)


def global_cs_score(view: ViewBatch, logits: Tensor, *, pool_norm_eps=1e-12):
    """Same adaptive q as TCS; pool features before computing ordinary CS."""
    u, v = _validate_view(view)
    if view.sigma_pooled_u is None:
        raise ValueError("GCS requires its separately calibrated uniform-pooled EEG sigma")
    eps = _scalar(pool_norm_eps, "pool_norm_eps")
    q = F.softmax(_logits(logits, u.shape[1], u.device), dim=0)
    pooled = torch.sum(q[None, :, None] * u, dim=1)
    norms = torch.linalg.vector_norm(pooled, dim=-1)
    pooled = F.normalize(pooled, dim=-1, eps=eps)
    score, stats = cs_qmi(pooled, v, sigma_u=view.sigma_pooled_u, sigma_v=view.sigma_v)
    stats = dict(stats)
    stats.update(q=_as_list(q), pooled_norm_min=float(norms.min().detach()),
                 pooled_norm_mean=float(norms.mean().detach()),
                 pooled_norm_at_or_below_epsilon=int((norms <= eps).sum().detach()),
                 pool_norm_eps=eps, sigma_pooled_u=float(view.sigma_pooled_u))
    return score, stats


def masks_from_packed_keys(keys: Tensor, *, unknown_clock_families: Iterable[int] = (), neighbor_samples=128):
    """Within-person audio-pair masks, mirroring prior33.losses.nce_masks.

    key=(family<<40)|(presentation<<24)|clock_sample. Equal keys are all
    positives; same-family neighbors within 128 samples (2 s at 64 Hz) are
    excluded unless positive. Unknown-clock cross-presentation family members
    are excluded at all clock offsets. Do NOT apply a same-person exclusion:
    these are EEG/audio pairs within a person, not cross-person EEG positives.
    """
    if not isinstance(keys, Tensor) or keys.ndim != 1 or keys.dtype != torch.int64:
        raise ValueError("keys must be one-dimensional int64 packed keys")
    if len(keys) < 2 or bool((keys < 0).any()) or neighbor_samples < 0:
        raise ValueError("invalid packed keys or neighbor range")
    family = keys >> 40
    presentation = (keys >> 24) & ((1 << 16) - 1)
    clock = keys & ((1 << 24) - 1)
    positive = keys[:, None] == keys[None, :]
    near = (clock[:, None] - clock[None, :]).abs() <= int(neighbor_samples)
    unknown = torch.as_tensor(tuple(unknown_clock_families), dtype=torch.int64, device=keys.device)
    if unknown.numel():
        near = near | (torch.isin(family, unknown)[:, None]
                       & (presentation[:, None] != presentation[None, :]))
    exclusion = (family[:, None] == family[None, :]) & near & ~positive
    return positive, exclusion


def masked_symmetric_nce(logits: Tensor, positive: Tensor, exclusion: Tensor):
    """Positive log-sum-exp in numerator; allowed denominator includes positives."""
    if logits.ndim != 2 or positive.shape != logits.shape or exclusion.shape != logits.shape:
        raise ValueError("logits/positive/exclusion matrix shapes must agree")
    positive = positive.to(device=logits.device, dtype=torch.bool)
    exclusion = exclusion.to(device=logits.device, dtype=torch.bool)
    if bool((positive & exclusion).any()):
        raise ValueError("positive and excluded pairs must be disjoint")
    if not bool(positive.any(1).all()) or not bool(positive.any(0).all()):
        raise ValueError("every query in both directions requires a positive")
    logits = logits.to(torch.float64)
    allowed_logits = logits.masked_fill(exclusion, -torch.inf)
    positive_logits = logits.masked_fill(~positive, -torch.inf)
    e2a = torch.logsumexp(allowed_logits, dim=1) - torch.logsumexp(positive_logits, dim=1)
    a2e = torch.logsumexp(allowed_logits, dim=0) - torch.logsumexp(positive_logits, dim=0)
    loss = .5 * (e2a.mean() + a2e.mean())
    if not bool(torch.isfinite(loss)):
        raise FloatingPointError("nonfinite masked NCE")
    return loss


def temporal_nce_loss(view: ViewBatch, logits: Tensor, *, positive: Tensor, exclusion: Tensor,
                      temperature=.1, norm_eps=1e-12):
    u, v = _validate_view(view)
    if u.shape[-1] != v.shape[-1]:
        raise ValueError("cosine NCE requires equal EEG/audio projected dimensions")
    tau, eps = _scalar(temperature, "temperature"), _scalar(norm_eps, "norm_eps")
    q = F.softmax(_logits(logits, u.shape[1], u.device), dim=0)
    v_unit = F.normalize(v, dim=-1, eps=eps)
    losses = []
    for k in range(u.shape[1]):
        scores = F.normalize(u[:, k], dim=-1, eps=eps) @ v_unit.T / tau
        losses.append(masked_symmetric_nce(scores, positive, exclusion))
    slots = torch.stack(losses)
    loss = torch.sum(q * slots)
    return loss, {"loss_nats": float(loss.detach()), "q": _as_list(q),
                  "slot_loss_nats": _as_list(slots), "temperature": tau,
                  "positive_count": int(positive.sum()), "excluded_count": int(exclusion.sum())}


def objective_loss(kind: str, views: Sequence[ViewBatch], logits: Tensor, *,
                   keys: Tensor | None = None, unknown_clock_families: Iterable[int] = (),
                   positive: Tensor | None = None, exclusion: Tensor | None = None,
                   temperature=.1, pool_norm_eps=1e-12):
    """Equally weighted view loss for one person's N anchors.

    Wrong pairing is a SAMPLER action, not a separate estimator: pass already
    consistently permuted audio to kind='TCS'. This layer never changes a
    person's identity, pairs, time windows, bandwidth or sample count.
    """
    if kind not in {"TCS", "TNCE", "GCS"} or not views:
        raise ValueError("kind must be TCS/TNCE/GCS and views must be nonempty")
    shape = views[0].u.shape[:2]
    if any(v.u.shape[:2] != shape for v in views):
        raise ValueError("all views must use the same anchors and slots")
    if kind == "TNCE":
        if keys is not None:
            if positive is not None or exclusion is not None:
                raise ValueError("provide packed keys OR explicit masks, not both")
            if keys.device != views[0].u.device or len(keys) != shape[0]:
                raise ValueError("keys must match the episode's anchors and device")
            positive, exclusion = masks_from_packed_keys(keys, unknown_clock_families=unknown_clock_families)
        elif positive is None or exclusion is None:
            raise ValueError("TNCE requires packed keys or both explicit masks")
    elif positive is not None or exclusion is not None:
        raise ValueError("NCE exclusion/positive masks must not enter a CS Gram")
    values, reports = [], []
    for view in views:
        if kind == "TCS":
            score, report = temporal_cs_score(view, logits); value = -score
        elif kind == "GCS":
            score, report = global_cs_score(view, logits, pool_norm_eps=pool_norm_eps); value = -score
        else:
            value, report = temporal_nce_loss(view, logits, positive=positive, exclusion=exclusion,
                                             temperature=temperature)
        values.append(value); reports.append({"view": view.name, **report})
    loss = torch.stack(values).mean()
    return loss, {"objective": kind, "loss_nats": float(loss.detach()),
                  "n_anchor": int(shape[0]), "n_slot": int(shape[1]), "views": reports}


def prior_uniform_kl(prior_logits: Tensor):
    if prior_logits.ndim != 1 or not prior_logits.is_floating_point():
        raise ValueError("one-dimensional floating prior logits required")
    if not bool(torch.isfinite(prior_logits).all()):
        raise ValueError("nonfinite prior logits")
    log_q = F.log_softmax(prior_logits.to(torch.float64), dim=0)
    return torch.sum(log_q.exp() * (log_q + math.log(len(log_q))))


def adapt_delta_fo(kind: str, support: Sequence[ViewBatch], prior_logits: Tensor, *,
                   support_keys: Tensor | None = None, unknown_clock_families: Iterable[int] = (),
                   steps=5, step_size=.1, delta_l2=.1, temperature=.1, pool_norm_eps=1e-12):
    """Support-only first-order update. Returns a detached delta for query use.

    Inner loss = objective_loss_support + delta_l2/2 * ||delta||^2.
    The support EEG/audio and a are detached before EVERY inner calculation.
    delta starts at zero for EVERY episode. Query data are not accepted here.
    """
    if not isinstance(steps, int) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    eta = _scalar(step_size, "step_size")
    lam = _scalar(delta_l2, "delta_l2", allow_zero=True)
    unknown_clock_families = tuple(unknown_clock_families)
    support_detached = [replace(v, u=v.u.detach(), v=v.v.detach()) for v in support]
    a_detached = prior_logits.detach()
    delta = torch.zeros_like(a_detached)
    history = []
    with torch.enable_grad():
        for j in range(steps):
            delta = delta.detach().requires_grad_(True)
            inner, _ = objective_loss(kind, support_detached, a_detached + delta,
                                      keys=support_keys, unknown_clock_families=unknown_clock_families,
                                      temperature=temperature, pool_norm_eps=pool_norm_eps)
            inner = inner + .5 * lam * delta.to(torch.float64).square().sum()
            grad, = torch.autograd.grad(inner, delta, create_graph=False, retain_graph=False)
            if not bool(torch.isfinite(grad).all()):
                raise FloatingPointError("nonfinite support delta gradient")
            history.append({"step": j, "support_inner_loss_nats": float(inner.detach()),
                            "delta_l2": float(torch.linalg.vector_norm(delta).detach()),
                            "q": _as_list(F.softmax((a_detached + delta).to(torch.float64), dim=0))})
            delta = (delta - eta * grad).detach()
            delta = delta - delta.mean()
    return delta.detach(), {"steps": steps, "step_size": eta, "delta_penalty": lam,
                            "history": history, "delta": _as_list(delta),
                            "q_support": _as_list(F.softmax((a_detached + delta).to(torch.float64), dim=0))}


def episode_loss_fo(kind: str, support: Sequence[ViewBatch], query: Sequence[ViewBatch],
                    prior_logits: Tensor, *, support_keys: Tensor | None = None,
                    query_keys: Tensor | None = None, unknown_clock_families: Iterable[int] = (),
                    steps=5, step_size=.1, delta_l2=.1, prior_kl_weight=.01,
                    temperature=.1, pool_norm_eps=1e-12):
    """One person's outer query loss; mean across people outside this function.

    theta gradients enter QUERY EEG only; prior a remains live in the query.
    The dependency of optimized delta on support/theta/a is deliberately
    ignored. This is first-order adaptation, not exact MAML/bilevel gradients.
    Dataset code must independently enforce disjoint S/Q IDs and EEG support.
    """
    lam0 = _scalar(prior_kl_weight, "prior_kl_weight", allow_zero=True)
    if len(support) != len(query) or not support:
        raise ValueError("same nonempty view roster in support and query required")
    for s, q in zip(support, query):
        if (s.name != q.name or s.u.shape[1:] != q.u.shape[1:] or s.v.shape[1:] != q.v.shape[1:]
                or s.sigma_u != q.sigma_u or s.sigma_v != q.sigma_v
                or s.sigma_pooled_u != q.sigma_pooled_u):
            raise ValueError("support/query view schemas and fixed bandwidths must agree")
    # Materialize an iterable once; a generator must not be exhausted by S.
    unknown_clock_families = tuple(unknown_clock_families)
    delta, adaptation = adapt_delta_fo(kind, support, prior_logits, support_keys=support_keys,
                                      unknown_clock_families=unknown_clock_families,
                                      steps=steps, step_size=step_size, delta_l2=delta_l2,
                                      temperature=temperature, pool_norm_eps=pool_norm_eps)
    query_loss, query_report = objective_loss(kind, query, prior_logits + delta.detach(),
                                             keys=query_keys, unknown_clock_families=unknown_clock_families,
                                             temperature=temperature, pool_norm_eps=pool_norm_eps)
    prior_kl = prior_uniform_kl(prior_logits)
    loss = query_loss + lam0 * prior_kl
    return loss, {"delta": delta.detach(), "adaptation": adaptation, "query": query_report,
                  "prior_kl_uniform_nats": float(prior_kl.detach()), "prior_kl_weight": lam0,
                  "loss_nats": float(loss.detach()), "first_order": True,
                  "query_gradient_into_delta": False}
