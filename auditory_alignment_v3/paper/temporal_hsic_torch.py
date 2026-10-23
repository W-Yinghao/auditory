"""Temporal HSIC with temporal-mass correction (manuscript v2, Appendix A.2 / B.2), as a Stage2 objective beside the
unchanged package reference aln41/temporal_objectives_torch.py (TO).

Same within-person Gram potentials as TCS (TO.tcs_slot_log_potentials: one sigma per view across slots, full Grams incl.
diagonal, float64 log domain). Per slot the biased empirical HSIC H_k = A_k + B_k - 2 C_k (n^-2 convention); the
time-tagged kernel gives sum_k q_k^2 H_k, and the mass-corrected control divides by sum_k q_k^2:
    H~(q) = sum_k q_k^2 H_k / sum_k q_k^2 = sum_k softmax(2 b)_k H_k,      q = softmax(b),
so gradients pass through the denominator and identical windows give a q-independent score (no concentration reward).
One fixed scalar objective scale (calibrated once at the seed-3401 initial state before any training; see
paper/arms.py) multiplies H~ so that the five-step support update of size 0.1 acts on a comparable scale to TCS.

episode_loss_fo mirrors TO.episode_loss_fo / TO.adapt_delta_fo exactly (support-only first-order delta, detached support,
centred delta, query loss with live prior + 0.01 KL to uniform); any other kind is delegated to TO unchanged.
"""
from __future__ import annotations

import math
from dataclasses import replace
from typing import Iterable, Sequence

import torch
import torch.nn.functional as F

from ..aln41 import temporal_objectives_torch as TO

_REFERENCE_EPISODE_LOSS = TO.episode_loss_fo


def thsic_from_log_potentials(potentials, logits, scale):
    la, lb, lc = potentials
    b = TO._logits(logits, len(la), la.device)
    w = F.softmax(2 * b, dim=0)                       # q_k^2 / sum_l q_l^2
    h = la.exp() + lb.exp() - 2 * lc.exp()
    score = scale * torch.sum(w * h)
    if not bool(torch.isfinite(score)):
        raise FloatingPointError("nonfinite temporal HSIC score")
    return score, {"score_scaled": float(score.detach()), "scale": float(scale), "q": TO._as_list(F.softmax(b, dim=0)),
                   "normalized_q_squared": TO._as_list(w), "slot_hsic": TO._as_list(h),
                   "log_A_slot": TO._as_list(la), "log_B_slot": TO._as_list(lb), "log_C_slot": TO._as_list(lc)}


def temporal_hsic_score(view, logits, scale=1.0):
    return thsic_from_log_potentials(TO.tcs_slot_log_potentials(view), logits, scale)


def objective_loss(views: Sequence, logits, *, scale):
    if not views:
        raise ValueError("views must be nonempty")
    shape = views[0].u.shape[:2]
    if any(v.u.shape[:2] != shape for v in views):
        raise ValueError("all views must use the same anchors and slots")
    values, reports = [], []
    for view in views:
        score, report = temporal_hsic_score(view, logits, scale)
        values.append(-score); reports.append({"view": view.name, **report})
    loss = torch.stack(values).mean()
    return loss, {"objective": "THSIC", "loss_nats": float(loss.detach()), "n_anchor": int(shape[0]), "n_slot": int(shape[1]),
                  "views": reports}


def adapt_delta_fo(support, prior_logits, *, scale, steps=5, step_size=.1, delta_l2=.1):
    eta = TO._scalar(step_size, "step_size"); lam = TO._scalar(delta_l2, "delta_l2", allow_zero=True)
    support_detached = [replace(v, u=v.u.detach(), v=v.v.detach()) for v in support]
    a_detached = prior_logits.detach(); delta = torch.zeros_like(a_detached); history = []
    with torch.enable_grad():
        for j in range(steps):
            delta = delta.detach().requires_grad_(True)
            inner, _ = objective_loss(support_detached, a_detached + delta, scale=scale)
            inner = inner + .5 * lam * delta.to(torch.float64).square().sum()
            grad, = torch.autograd.grad(inner, delta, create_graph=False, retain_graph=False)
            if not bool(torch.isfinite(grad).all()):
                raise FloatingPointError("nonfinite support delta gradient")
            history.append({"step": j, "support_inner_loss": float(inner.detach()),
                            "delta_l2": float(torch.linalg.vector_norm(delta).detach()),
                            "q": TO._as_list(F.softmax((a_detached + delta).to(torch.float64), dim=0))})
            delta = (delta - eta * grad).detach()
            delta = delta - delta.mean()
    return delta.detach(), {"steps": steps, "step_size": eta, "delta_penalty": lam, "history": history, "delta": TO._as_list(delta),
                            "q_support": TO._as_list(F.softmax((a_detached + delta).to(torch.float64), dim=0))}


def make_episode_loss(kind_map: dict, scale: float | None):
    """Returns an episode_loss_fo replacement: kinds in kind_map are renamed (paper arm -> objective kind); THSIC is
    computed here with the fixed scale; every other kind goes to the unchanged reference implementation."""
    def episode_loss_fo(kind, support, query, prior_logits, *, support_keys=None, query_keys=None,
                        unknown_clock_families: Iterable[int] = (), steps=5, step_size=.1, delta_l2=.1, prior_kl_weight=.01,
                        temperature=.1, pool_norm_eps=1e-12):
        kind = kind_map.get(kind, kind)
        if kind != "THSIC":
            return _REFERENCE_EPISODE_LOSS(kind, support, query, prior_logits, support_keys=support_keys, query_keys=query_keys,
                                           unknown_clock_families=unknown_clock_families, steps=steps, step_size=step_size,
                                           delta_l2=delta_l2, prior_kl_weight=prior_kl_weight, temperature=temperature,
                                           pool_norm_eps=pool_norm_eps)
        assert scale is not None and math.isfinite(scale) and scale > 0
        lam0 = TO._scalar(prior_kl_weight, "prior_kl_weight", allow_zero=True)
        if len(support) != len(query) or not support:
            raise ValueError("same nonempty view roster in support and query required")
        delta, adaptation = adapt_delta_fo(support, prior_logits, scale=scale, steps=steps, step_size=step_size, delta_l2=delta_l2)
        query_loss, query_report = objective_loss(query, prior_logits + delta.detach(), scale=scale)
        prior_kl = TO.prior_uniform_kl(prior_logits)
        loss = query_loss + lam0 * prior_kl
        return loss, {"delta": delta.detach(), "adaptation": adaptation, "query": query_report,
                      "prior_kl_uniform_nats": float(prior_kl.detach()), "prior_kl_weight": lam0, "loss_nats": float(loss.detach()),
                      "first_order": True, "query_gradient_into_delta": False}
    return episode_loss_fo
