"""W7 objectives (frozen design docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md, sections 2.3-2.4, and
private/auditory_alignment_v3/paper/w7_v1/APPENDUM_01.md) beside the unchanged package reference
aln41/temporal_objectives_torch.py (TO) and aln41/cs_qmi_reference.py. Nothing in aln41 is edited.

RES   history-residualised TCS (partial dependence): the env audio vector a (8 raw envelope samples) becomes a - h(H), with
      H = the envelope at -20/-100/-200/-500 ms and h a ridge map fitted once on source fit rows (alpha on source dev rows).
      The residual passes through the unchanged fixed env head. Not a conditional CS divergence.
CCS   kernel conditional CS-QMI  I_CS(U;A|H) := D_CS(f1 || f2),  f1 = p(u,a,h) p(h),  f2 = p(u,h) p(a,h),  Gaussian KDE with
      uniform weights (V-statistic, self-pairs kept), D_CS(f||g) = log int f^2 + log int g^2 - 2 log int f g (the convention of
      cs_qmi_reference / TCS, i.e. without the factor 1/2). For positive p(h), D_CS = 0 iff U _||_ A | H.
      Closed form: a product of m equal-variance Gaussians integrates to a constant times prod_{m<m'} exp(-|x_m-x_m'|^2/(2 m s^2)).
      With the overlap-SD convention of cs_qmi_reference (sigma = sqrt(2) x component SD; overlap log-Gram G = -d^2/(2 sigma^2))
      a two-component integral is G and a four-component integral is sum over its six pairs of G/2. In every one of the three
      integrals u and a carry two kernels and h four, so all Gaussian constants and the 1/N^4 weights cancel in D_CS:
        int f1^2  ~ sum_{ikjl} exp(Lu_ik + La_ik + Hh_ik + W_ikj + Hh_jl + W_ikl)
        int f2^2  ~ sum_{ikjl} exp(Lu_ik + La_jl + Hh_ik + W_ikj + Hh_jl + W_ikl)
        int f1 f2 ~ sum_{ikjl} exp(Lu_ik + La_il + Hh_ik + W_ikj + Hh_jl + W_ikl)
      with Hh = G_h/2 and W_ikj = Hh_ij + Hh_kj. The (j,l) sums do not involve u, so they are computed once per (a,h) batch
      without gradient (O(N^4), 1M terms at N = 32); the remaining sums are O(N^2) per slot, like TCS. Time slots: per-slot
      potentials, q^2 mixture through TO.tcs_from_log_potentials (the exact time-tagged form with counting measure on slots).
PRES  TCS loss - beta * mean_slot I_CS(P z_theta ; P z0): z_theta = current backbone tokens of a person's query crops, z0 =
      the same crops through the initial (Stage1 = B0) backbone without gradient, P = frozen PCA64 of B0 tokens on the source dev
      panel, one fixed bandwidth (median rule at the initial state). I_CS = cs_qmi_reference.cs_qmi per slot.

The episode objective mirrors TO.episode_loss_fo / TO.adapt_delta_fo exactly (support-only first-order delta of 5 steps,
step 0.1, L2 0.1, centred; detached support; query loss with live prior + 0.01 KL to uniform); with no CCS view it is the
reference itself (tested). `validation_suite` is the CCS estimator-validation gate (i)-(v) on synthetic data only.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, fields, replace
from typing import Iterable, Sequence

import numpy as np
import torch
from torch import Tensor
import torch.nn.functional as F

from ..aln41 import temporal_objectives_torch as TO
from ..aln41.cs_qmi_reference import cs_qmi, gaussian_log_gram

_REFERENCE_EPISODE_LOSS = TO.episode_loss_fo
assert _REFERENCE_EPISODE_LOSS.__module__ == TO.__name__ and _REFERENCE_EPISODE_LOSS.__name__ == "episode_loss_fo", "TO re-pointed at import"
LAGS_MS = (20, 100, 200, 500)


def lag_samples(fs=64):
    """Downstream lag formula of aln41/frozen.py: round(ms * fs / 1000) -> (1, 6, 13, 32) at 64 Hz."""
    return tuple(int(round(ms * fs / 1000)) for ms in LAGS_MS)


def lower_median(d):
    d = np.sort(np.asarray(d, np.float64).ravel())
    return float(d[(len(d) - 1) // 2])


def pooled_slot_sigma(Z):
    """TCS sigma rule (source.calibrate_sigmas): lower median of within-slot distinct-anchor distances pooled over slots."""
    Z = torch.as_tensor(Z, dtype=torch.float64)
    if Z.ndim == 2:
        Z = Z[:, None]
    off = ~torch.eye(len(Z), dtype=torch.bool)
    return lower_median(torch.cat([torch.cdist(Z[:, k], Z[:, k])[off] for k in range(Z.shape[1])]).numpy())


# ----------------------------------------------------------------------------------------------------- RES: history map
def ridge(x, y, alpha):
    """content_time.ridge: standardised x, relative alpha on the standardised Gram, intercept."""
    mx = x.mean(0); my = y.mean(0); sd = x.std(0) + 1e-8; z = (x - mx) / sd
    gram = z.T @ z / len(z); coef = np.linalg.solve(gram + alpha * np.eye(z.shape[1]), z.T @ (y - my) / len(z))
    return coef / sd[:, None], my - mx @ (coef / sd[:, None])


def mean_correlation(y, p):
    """content_time.correlation: mean over columns of Pearson r."""
    a = y - y.mean(0); b = p - p.mean(0)
    return float(np.mean((a * b).sum(0) / np.sqrt(np.maximum((a * a).sum(0) * (b * b).sum(0), 1e-24))))


ALPHAS = np.logspace(-3, 4, 8)                    # content_time.ALPHAS


def fit_history_map(H_fit, A_fit, H_dev, A_dev, alphas=ALPHAS):
    """Ridge H -> a on fit rows only; alpha by mean dev Pearson r (content_time.fitted's criterion; first maximum, i.e. the
    smallest alpha on an exact tie); the returned map is the fit-rows-only solution at that alpha (no refit on dev)."""
    H_fit, A_fit, H_dev, A_dev = (np.asarray(v, np.float64) for v in (H_fit, A_fit, H_dev, A_dev))
    curve, mse = [], []
    for alpha in alphas:
        w, b = ridge(H_fit, A_fit, alpha); p = H_dev @ w + b
        curve.append(mean_correlation(A_dev, p)); mse.append(float(((A_dev - p) ** 2).mean()))
    i = int(np.argmax(curve)); w, b = ridge(H_fit, A_fit, alphas[i])
    res_dev = A_dev - (H_dev @ w + b); res_fit = A_fit - (H_fit @ w + b)
    return {'coef': w.tolist(), 'intercept': b.tolist(), 'alpha_relative': float(alphas[i]), 'alphas': [float(a) for a in alphas],
            'dev_mean_r_curve': curve, 'dev_mse_curve': mse,
            'fit_residual_var_ratio': float(res_fit.var(0).sum() / A_fit.var(0).sum()),
            'dev_residual_var_ratio': float(res_dev.var(0).sum() / A_dev.var(0).sum()),
            'n_fit': int(len(H_fit)), 'n_dev': int(len(H_dev))}


def apply_history_map(a, H, hmap):
    """a - h(H) in float64 (torch or numpy), returned in a's dtype."""
    if isinstance(a, Tensor):
        w = torch.as_tensor(hmap['coef'], dtype=torch.float64, device=a.device)
        b = torch.as_tensor(hmap['intercept'], dtype=torch.float64, device=a.device)
        return (a.double() - (H.double() @ w + b)).to(a.dtype)
    return np.asarray(a, np.float64) - (np.asarray(H, np.float64) @ np.asarray(hmap['coef']) + np.asarray(hmap['intercept']))


# ----------------------------------------------------------------------------------------------------- CCS estimator
@dataclass(frozen=True)
class CondViewBatch(TO.ViewBatch):
    """A TO.ViewBatch plus the conditioning history h [N, D_h] (fixed, no gradient) and its fixed overlap SD."""
    h: Tensor | None = None
    sigma_h: float | None = None


def _fixed_rows(x, name, n, device):
    if not isinstance(x, Tensor) or x.ndim != 2 or len(x) != n or x.device != device or not x.is_floating_point():
        raise ValueError(f"{name} must be a floating [N, D] tensor matching the view")
    if x.requires_grad:
        raise ValueError(f"{name} is fixed data in this recipe; it must not carry a gradient")
    if not bool(torch.isfinite(x).all()):
        raise ValueError(f"nonfinite {name}")
    return x.to(torch.float64)


def ccs_fixed_terms_reference(v: Tensor, h: Tensor, sigma_v: float, sigma_h: float):
    """Log-domain reference of ccs_fixed_terms (explicit [N, N, N, N] log-sum-exp); tests only."""
    with torch.no_grad(), torch.autocast(device_type=v.device.type, enabled=False):
        La = gaussian_log_gram(v, sigma_v); Hh = 0.5 * gaussian_log_gram(h, sigma_h)
        W = Hh[:, None, :] + Hh[None, :, :]                       # W[i,k,j] = Hh[i,j] + Hh[k,j]
        Wj, Wl = W[:, :, :, None], W[:, :, None, :]
        S1 = torch.logsumexp(Wj + Hh + Wl, dim=(2, 3))
        S2 = torch.logsumexp(Wj + (La + Hh) + Wl, dim=(2, 3))
        S3 = torch.logsumexp(Wj + Hh + Wl + La[:, None, None, :], dim=(2, 3))
        return La + Hh + S1, Hh + S2, Hh + S3


def ccs_fixed_terms(v: Tensor, h: Tensor, sigma_v: float, sigma_h: float):
    """B1, B2, B3 [N, N]: everything in the three D_CS integrals except the U overlap (no gradient; O(N^4) arithmetic as
    max-shifted exponential quadratic forms, S[i,k] = log sum_jl exp(W_ikj + M_jl + W'_ikl) = log((E M E'^T)_diag))."""
    with torch.no_grad(), torch.autocast(device_type=v.device.type, enabled=False):
        La = gaussian_log_gram(v, sigma_v); Hh = 0.5 * gaussian_log_gram(h, sigma_h); n = len(Hh)
        W = (Hh[:, None, :] + Hh[None, :, :]).reshape(n * n, n)  # row i*n + k, column j: Hh[i,j] + Hh[k,j]
        m = W.max(1, keepdim=True).values; E = (W - m).exp()

        def quad(M, E2, m2):
            mM = M.max()
            return (m[:, 0] + m2[:, 0] + mM + ((E @ (M - mM).exp()) * E2).sum(1).log()).reshape(n, n)
        W3 = W + La.repeat_interleave(n, dim=0)                  # row (i, k) gains La[i, l]
        m3 = W3.max(1, keepdim=True).values
        out = (La + Hh + quad(Hh, E, m), Hh + quad(La + Hh, E, m), Hh + quad(Hh, (W3 - m3).exp(), m3))
    if not all(bool(torch.isfinite(t).all()) for t in out):
        raise FloatingPointError("nonfinite CCS fixed terms; inspect feature scale and bandwidth")
    return out


def ccs_from_fixed(u: Tensor, fixed, sigma_u: float):
    """Per-slot log potentials (log int f1^2, log int f2^2, log int f1 f2) up to common constants; u [N, K, D] float64."""
    B1, B2, B3 = fixed
    p1, p2, p3 = [], [], []
    for k in range(u.shape[1]):
        Lu = gaussian_log_gram(u[:, k], sigma_u)
        p1.append(torch.logsumexp(Lu + B1, dim=(0, 1))); p2.append(torch.logsumexp(Lu + B2, dim=(0, 1)))
        p3.append(torch.logsumexp(Lu + B3, dim=(0, 1)))
    return torch.stack(p1), torch.stack(p2), torch.stack(p3)


def ccs_slot_log_potentials(view: CondViewBatch, fixed=None):
    u, v = TO._validate_view(view)
    if view.h is None or view.sigma_h is None:
        raise ValueError("CCS requires the conditioning history h and its fixed bandwidth")
    TO._scalar(view.sigma_h, "sigma_h")
    h = _fixed_rows(view.h, "h", len(u), u.device)
    if fixed is None:
        fixed = ccs_fixed_terms(v, h, view.sigma_v, view.sigma_h)
    return ccs_from_fixed(u, fixed, view.sigma_u)


def conditional_cs(u: Tensor, a: Tensor, h: Tensor, *, sigma_u, sigma_a, sigma_h):
    """I_CS(U;A|H) (nats) per slot (a scalar for u [N, D]) and the three log integrals; u may carry a gradient."""
    view = CondViewBatch(u[:, None] if u.ndim == 2 else u, a, sigma_u, sigma_a, None, "ccs", h, sigma_h)
    p1, p2, p3 = ccs_slot_log_potentials(view)
    d = p1 + p2 - 2 * p3
    return (d[0] if u.ndim == 2 else d), (p1, p2, p3)


def view_potentials(view, fixed=None):
    if isinstance(view, CondViewBatch) and view.h is not None:
        return "CCS", ccs_slot_log_potentials(view, fixed)
    return "TCS", TO.tcs_slot_log_potentials(view)


def objective_from_potentials(views: Sequence, potentials, logits):
    """Equal-weight mean over views of -score; score = q^2-mixed CS from per-slot potentials (TCS or CCS)."""
    shape = views[0].u.shape[:2]
    values, reports = [], []
    for view, (kind, pot) in zip(views, potentials):
        score, report = TO.tcs_from_log_potentials(pot, logits)
        values.append(-score); reports.append({"view": view.name, "estimator": kind, **report})
    loss = torch.stack(values).mean()
    return loss, {"objective": "TCS_CCS", "loss_nats": float(loss.detach()), "n_anchor": int(shape[0]), "n_slot": int(shape[1]),
                  "views": reports}


def ccs_objective_loss(views: Sequence, logits):
    if not views:
        raise ValueError("views must be nonempty")
    shape = views[0].u.shape[:2]
    if any(v.u.shape[:2] != shape for v in views):
        raise ValueError("all views must use the same anchors and slots")
    return objective_from_potentials(views, [view_potentials(v) for v in views], logits)


def ccs_adapt_delta_fo(support: Sequence, prior_logits: Tensor, *, steps=5, step_size=.1, delta_l2=.1):
    """TO.adapt_delta_fo with the support potentials computed once (they do not depend on delta; identical values)."""
    if not isinstance(steps, int) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    eta = TO._scalar(step_size, "step_size"); lam = TO._scalar(delta_l2, "delta_l2", allow_zero=True)
    support_detached = [replace(v, u=v.u.detach(), v=v.v.detach()) for v in support]
    with torch.no_grad():
        pots = [view_potentials(v) for v in support_detached]
    a_detached = prior_logits.detach(); delta = torch.zeros_like(a_detached); history = []
    with torch.enable_grad():
        for j in range(steps):
            delta = delta.detach().requires_grad_(True)
            inner, _ = objective_from_potentials(support_detached, pots, a_detached + delta)
            inner = inner + .5 * lam * delta.to(torch.float64).square().sum()
            grad, = torch.autograd.grad(inner, delta, create_graph=False, retain_graph=False)
            if not bool(torch.isfinite(grad).all()):
                raise FloatingPointError("nonfinite support delta gradient")
            history.append({"step": j, "support_inner_loss_nats": float(inner.detach()),
                            "delta_l2": float(torch.linalg.vector_norm(delta).detach()),
                            "q": TO._as_list(F.softmax((a_detached + delta).to(torch.float64), dim=0))})
            delta = (delta - eta * grad).detach()
            delta = delta - delta.mean()
    return delta.detach(), {"steps": steps, "step_size": eta, "delta_penalty": lam, "history": history, "delta": TO._as_list(delta),
                            "q_support": TO._as_list(F.softmax((a_detached + delta).to(torch.float64), dim=0))}


def ccs_episode_loss_fo(support: Sequence, query: Sequence, prior_logits: Tensor, *, steps=5, step_size=.1, delta_l2=.1,
                        prior_kl_weight=.01):
    """TO.episode_loss_fo for a view roster in which CondViewBatch views use CCS and the others TCS."""
    lam0 = TO._scalar(prior_kl_weight, "prior_kl_weight", allow_zero=True)
    if len(support) != len(query) or not support:
        raise ValueError("same nonempty view roster in support and query required")
    for s, q in zip(support, query):
        if (s.name != q.name or type(s) is not type(q) or s.u.shape[1:] != q.u.shape[1:] or s.v.shape[1:] != q.v.shape[1:]
                or s.sigma_u != q.sigma_u or s.sigma_v != q.sigma_v or s.sigma_pooled_u != q.sigma_pooled_u
                or getattr(s, "sigma_h", None) != getattr(q, "sigma_h", None)):
            raise ValueError("support/query view schemas and fixed bandwidths must agree")
    delta, adaptation = ccs_adapt_delta_fo(support, prior_logits, steps=steps, step_size=step_size, delta_l2=delta_l2)
    query_loss, query_report = ccs_objective_loss(query, prior_logits + delta.detach())
    prior_kl = TO.prior_uniform_kl(prior_logits)
    loss = query_loss + lam0 * prior_kl
    return loss, {"delta": delta.detach(), "adaptation": adaptation, "query": query_report,
                  "prior_kl_uniform_nats": float(prior_kl.detach()), "prior_kl_weight": lam0, "loss_nats": float(loss.detach()),
                  "first_order": True, "query_gradient_into_delta": False}


# ----------------------------------------------------------------------------------------------------- PRES
def pca_project(x: Tensor, pca):
    """frozen.pca_apply convention: ((x - mu) / sd) @ components^T; x [n, F] keeps its graph."""
    mu, sd, comp = (pca[k].to(device=x.device, dtype=x.dtype) for k in ("mu", "sd", "components"))
    return ((x - mu) / sd) @ comp.T


def pres_dependence(z_theta: Tensor, z0: Tensor, pca, sigma: float):
    """mean over slots of I_CS(P z_theta^k ; P z0^k); z_theta/z0 [N, K, F]; z0 must carry no gradient."""
    if z0.requires_grad or z0.grad_fn is not None:
        raise AssertionError("PRES: z0 must not carry a gradient")
    if z_theta.shape != z0.shape or z_theta.ndim != 3:
        raise ValueError("PRES: z_theta and z0 must be [N, K, F] of equal shape")
    vals, stats = [], []
    for k in range(z_theta.shape[1]):
        a = pca_project(z_theta[:, k].float(), pca); b = pca_project(z0[:, k].float(), pca)
        s, st = cs_qmi(a, b, sigma_u=sigma, sigma_v=sigma)
        vals.append(s); stats.append(st["cs_qmi_nats"])
    value = torch.stack(vals).mean()
    if not bool(torch.isfinite(value)):
        raise FloatingPointError("nonfinite PRES dependence")
    return value, {"pres_cs_qmi_nats": float(value.detach()), "slot_cs_qmi_nats": stats}


# ----------------------------------------------------------------------------------------------------- episode factory
def make_episode_loss(arm: str, spec: dict, state: dict):
    """episode_loss_fo replacement for one W7 arm. spec: {'ccs', 'pres'}; state: mutable dict owned by w7_arms with keys
    'beta', 'pres' (callable(query) -> (dependence, report)), 'trace' (list)."""
    def episode_loss_fo(kind, support, query, prior_logits, *, support_keys=None, query_keys=None,
                        unknown_clock_families: Iterable[int] = (), steps=5, step_size=.1, delta_l2=.1, prior_kl_weight=.01,
                        temperature=.1, pool_norm_eps=1e-12):
        if kind != arm:
            raise ValueError(f"W7 objective for {arm} called with kind {kind}")
        if spec["ccs"]:
            loss, rep = ccs_episode_loss_fo(support, query, prior_logits, steps=steps, step_size=step_size, delta_l2=delta_l2,
                                            prior_kl_weight=prior_kl_weight)
            assert [(v["view"], v["estimator"]) for v in rep["query"]["views"]] == [("env", "CCS"), ("ss", "TCS"), ("sc", "TCS")]
            state["ccs_calls"] = state.get("ccs_calls", 0) + 1
        else:
            if any(isinstance(v, CondViewBatch) and v.h is not None for v in list(support) + list(query)):
                raise ValueError("a conditional view reached the TCS reference")
            loss, rep = _REFERENCE_EPISODE_LOSS("TCS", support, query, prior_logits, support_keys=None, query_keys=None,
                                                unknown_clock_families=unknown_clock_families, steps=steps, step_size=step_size,
                                                delta_l2=delta_l2, prior_kl_weight=prior_kl_weight, temperature=temperature,
                                                pool_norm_eps=pool_norm_eps)
        if spec["pres"]:
            beta = state["beta"]
            assert beta is not None and math.isfinite(beta) and beta > 0, "PRES beta not set"
            dep, prep = state["pres"](query)
            loss = loss - beta * dep
            rep = {**rep, "pres": {**prep, "beta": beta}, "loss_nats": float(loss.detach())}
            state["trace"].append(prep["pres_cs_qmi_nats"])
        return loss, rep
    return episode_loss_fo


# ===================================================================================================== CCS validation gate
def _normalize(x):
    return F.normalize(x, dim=-1)


def _semi_orthogonal(rows, cols, g):
    q, _ = torch.linalg.qr(torch.randn(rows, cols, generator=g, dtype=torch.float64))
    return q                                                     # [rows, cols], q^T q = I


class Synth:
    """Synthetic triples shaped like the real env view: U 32-d unit vectors, A = normalise(P a_raw) 32-d unit vectors from 8 raw
    samples, H 4 raw lags. Envelope-like stationary AR(1) series (rho 0.95 per 64 Hz sample): H = x[t-1, t-6, t-13, t-32],
    a_raw = x[t .. t+7]. Fixed random maps from one generator seed.
      'common' (i):  u = normalise(Wu H + e)                    -> U _||_ A | H (Markov: a depends on the past via x[t-1] only)
      'chain'  (ii): a_raw ~ AR window, H = M a_raw + 0.5 e', u = normalise(Wu H + e)   -> A -> H -> U
      'coupled'(iii): u = normalise(Wu H + c Wa a_raw + e)     -> U depends on A given H for c > 0
    """
    LAGS = (1, 6, 13, 32)

    def __init__(self, seed=20261022):
        g = torch.Generator().manual_seed(seed)
        self.Pa = _semi_orthogonal(32, 8, g)
        self.Wu = torch.randn(32, 4, generator=g, dtype=torch.float64) / 2.0
        self.Wa = torch.randn(32, 8, generator=g, dtype=torch.float64) / math.sqrt(8)
        self.M = torch.randn(4, 8, generator=g, dtype=torch.float64) / math.sqrt(8)
        self.rho = 0.95

    def ar(self, n, length, g):
        x = torch.empty(n, length, dtype=torch.float64)
        x[:, 0] = torch.randn(n, generator=g, dtype=torch.float64)
        s = math.sqrt(1 - self.rho ** 2)
        e = torch.randn(n, length, generator=g, dtype=torch.float64)
        for t in range(1, length):
            x[:, t] = self.rho * x[:, t - 1] + s * e[:, t]
        return x

    def sample(self, kind, n, g, c=0.0):
        if kind == "chain":
            a_raw = self.ar(n, 8, g)
            H = a_raw @ self.M.T + .5 * torch.randn(n, 4, generator=g, dtype=torch.float64)
        else:
            x = self.ar(n, 40, g)                                # x[:, 32] is time t
            H = torch.stack([x[:, 32 - L] for L in self.LAGS], 1)
            a_raw = x[:, 32:40]
        e = torch.randn(n, 32, generator=g, dtype=torch.float64)
        u = H @ self.Wu.T + e
        if kind == "coupled":
            u = u + c * (a_raw @ self.Wa.T)
        return _normalize(u), _normalize(a_raw @ self.Pa.T), H


def _quantile_of(obs, null):
    null = np.asarray(null)
    return float(((null < obs).sum() + .5 * (null == obs).sum()) / len(null))


def _estimators(u, a, h, s):
    """CCS (the estimator under test) and the descriptive contrast marginal CS-QMI(U,A) (TCS single slot)."""
    ccs, _ = conditional_cs(u, a, h, sigma_u=s["u"], sigma_a=s["a"], sigma_h=s["h"])
    marg, _ = cs_qmi(u, a, sigma_u=s["u"], sigma_v=s["a"])
    return float(ccs), float(marg)


def _perm_null(u, a, h, s, M, g):
    out_c, out_m = [], []
    for _ in range(M):
        p = torch.randperm(len(a), generator=g)
        c, m = _estimators(u, a[p], h, s)
        out_c.append(c); out_m.append(m)
    return np.array(out_c), np.array(out_m)


def calibrate_synth(synth, kind, g, n=512, c=0.0):
    u, a, h = synth.sample(kind, n, g, c)
    return {"u": pooled_slot_sigma(u), "a": pooled_slot_sigma(a), "h": pooled_slot_sigma(h)}


def scenario(synth, kind, *, R, N, M, seed, c=0.0, sig=None, h_mult=1.0):
    g = torch.Generator().manual_seed(seed)
    s = dict(sig if sig is not None else calibrate_synth(synth, kind, g, c=c)); s["h"] = s["h"] * h_mult
    rows = []
    for r in range(R):
        u, a, h = synth.sample(kind, N, g, c)
        oc, om = _estimators(u, a, h, s)
        nc, nm = _perm_null(u, a, h, s, M, g)
        rows.append({"ccs": oc, "ccs_null_q025": float(np.quantile(nc, .025)), "ccs_null_median": float(np.median(nc)),
                     "ccs_null_q975": float(np.quantile(nc, .975)), "ccs_quantile": _quantile_of(oc, nc),
                     "marginal": om, "marginal_quantile": _quantile_of(om, nm)})
    q = np.array([x["ccs_quantile"] for x in rows]); qm = np.array([x["marginal_quantile"] for x in rows])
    obs = np.array([x["ccs"] for x in rows]); med = np.array([x["ccs_null_median"] for x in rows])
    return {"kind": kind, "c": c, "R": R, "N": N, "M": M, "seed": seed, "sigmas": s, "h_multiplier": h_mult,
            "ccs_mean": float(obs.mean()), "ccs_excess_over_null_median_mean": float((obs - med).mean()),
            "ccs_null_q025_mean": float(np.mean([x["ccs_null_q025"] for x in rows])),
            "ccs_null_q975_mean": float(np.mean([x["ccs_null_q975"] for x in rows])),
            "ccs_quantile_median": float(np.median(q)), "ccs_rejection_rate_975": float((q > .975).mean()),
            "marginal_quantile_median": float(np.median(qm)), "marginal_rejection_rate_975": float((qm > .975).mean()),
            "replicates": rows}


def gradient_check():
    """(iv): float64 gradcheck of the q^2-mixed CCS score w.r.t. U and the gate logits (small N), and central finite
    differences along random directions at the real size N = 32, K = 3, D = 32 (relative error)."""
    g = torch.Generator().manual_seed(7)
    synth = Synth()
    out = {}
    u0, a, h = synth.sample("coupled", 6, g, 1.0)
    U = torch.stack([u0, _normalize(u0 + .3 * torch.randn(6, 32, generator=g, dtype=torch.float64))], 1).requires_grad_(True)
    lg = torch.randn(2, generator=g, dtype=torch.float64).requires_grad_(True)

    def f(U, lg):
        view = CondViewBatch(U, a, .9, 1.2, None, "env", h, 1.5)
        return TO.tcs_from_log_potentials(ccs_slot_log_potentials(view), lg)[0]
    out["gradcheck_small"] = bool(torch.autograd.gradcheck(f, (U, lg), eps=1e-6, atol=1e-6, rtol=1e-4))
    u0, a, h = synth.sample("coupled", 32, g, 1.0)
    U = torch.stack([_normalize(u0 + .2 * k * torch.randn(32, 32, generator=g, dtype=torch.float64)) for k in range(3)], 1)
    U.requires_grad_(True); lg = torch.zeros(3, dtype=torch.float64, requires_grad=True)
    val = f(U, lg); gu, gl = torch.autograd.grad(val, (U, lg))
    out["finite_gradients"] = bool(torch.isfinite(gu).all() and torch.isfinite(gl).all())
    errs = []
    with torch.no_grad():
        for _ in range(8):
            d = torch.randn(U.shape, generator=g, dtype=torch.float64); d = d / d.norm()
            e = 1e-5
            fd = (f(U + e * d, lg) - f(U - e * d, lg)) / (2 * e)
            an = (gu * d).sum()
            errs.append(float(abs(fd - an) / max(abs(float(an)), 1e-12)))
    out["fd_relative_error_max_N32"] = max(errs)
    out["pass"] = bool(out["gradcheck_small"] and out["finite_gradients"] and out["fd_relative_error_max_N32"] <= 1e-5)
    return out


def objective_step_timing(device, reps=50, warmup=5, seed=11):
    """(v): one objective step (support delta adaptation, query objective, backward to U) at N = 32, K = 3, D = 32, three views;
    TCS reference vs the CCS arm (env CCS + ss/sc TCS). Median wall time over reps after warm-up."""
    g = torch.Generator().manual_seed(seed); synth = Synth()

    def batch():
        u, a, h = synth.sample("coupled", 32, g, 1.0)
        U = torch.stack([_normalize(u + .2 * k * torch.randn(32, 32, generator=g, dtype=torch.float64)) for k in range(3)], 1)
        return U.float().to(device), a.float().to(device), h.float().to(device)
    data = [(batch(), batch()) for _ in range(4)]
    prior = torch.zeros(3, device=device, requires_grad=True)

    def views(U, a, h, ccs):
        out = []
        for name in ("env", "ss", "sc"):
            if ccs and name == "env":
                out.append(CondViewBatch(U, a.double(), 1.06, 1.42, .8, name, h, 1.5))
            else:
                out.append(TO.ViewBatch(U, a.double(), 1.06, 1.42, .8, name))
        return out

    def step(i, ccs):
        (Us, a_s, hs), (Uq, aq, hq) = data[i % len(data)]
        Uq = Uq.clone().requires_grad_(True)
        sv, qv = views(Us, a_s, hs, ccs), views(Uq, aq, hq, ccs)
        if ccs:
            loss, _ = ccs_episode_loss_fo(sv, qv, prior)
        else:
            loss, _ = _REFERENCE_EPISODE_LOSS("TCS", sv, qv, prior)
        loss.backward()
        return float(loss.detach())

    def timed(ccs):
        for i in range(warmup):
            step(i, ccs)
        ts = []
        for i in range(reps):
            if device.type == "cuda":
                torch.cuda.synchronize()
            t0 = time.perf_counter(); step(i, ccs)
            if device.type == "cuda":
                torch.cuda.synchronize()
            ts.append(time.perf_counter() - t0)
        return float(np.median(ts))
    t_tcs, t_ccs = timed(False), timed(True)
    return {"device": str(device) if device.type == "cpu" else torch.cuda.get_device_name(device), "N": 32, "K": 3, "D": 32,
            "reps": reps, "warmup": warmup, "tcs_seconds_median": t_tcs, "ccs_arm_seconds_median": t_ccs, "ratio": t_ccs / t_tcs,
            "pass": bool(t_ccs / t_tcs <= 2.0)}


COUPLINGS = (0.0, 0.5, 1.0, 2.0, 4.0)
# APPENDUM_02 ladder (0.5 / seed 20261023, 0.25 / seed 20261024) failed under the two-sided band; APPENDUM_03: sigma_h = 0.5 x
# median, (i)/(ii) one-sided ('upper': not above the A-row permutation band), re-validated on fresh draws (seed 20261025).
CCS_VALIDATION = (0.5, 20261025, 'upper')


def validation_suite(R=20, N=32, M=200, seed=20261022, h_multipliers=(1.0,), sensitivity=(0.5, 0.25), sided='two'):
    """Estimator-validation gate (frozen design 2.3 (i)-(v); APPENDUM_01 A5), synthetic data only, CPU.
    (i) 'common' and (ii) 'chain': pass if the median over replicates of the CCS estimate's quantile in its A-row permutation
    null lies in [0.025, 0.975]. (iii) 'coupled' at c in {0, .25, .5, 1, 2} with bandwidths fixed at c = 0: pass if the mean CCS
    estimate is strictly increasing in c and its mean excess over the permutation-null median is > 0 for every c > 0.
    (iv) gradient check. (v) CPU timing reported here (the gate itself is measured on the training GPU before any Stage2 unit).
    The marginal CS-QMI(U,A) under the same tests and an H-bandwidth sensitivity sweep are descriptive."""
    synth = Synth(seed)
    out = {"design": {"R": R, "N": N, "M": M, "seed": seed, "couplings": list(COUPLINGS),
                      "generator": Synth.__doc__, "coupled_common_random_numbers": True}, "gate": {}}
    for hm in h_multipliers:
        key = f"h_mult_{hm:g}"
        common = scenario(synth, "common", R=R, N=N, M=M, seed=seed + 1, h_mult=hm)
        chain = scenario(synth, "chain", R=R, N=N, M=M, seed=seed + 2, h_mult=hm)
        g = torch.Generator().manual_seed(seed + 3); sig = calibrate_synth(synth, "coupled", g, c=0.0)
        coupled = [scenario(synth, "coupled", R=R, N=N, M=M, seed=seed + 10, c=c, sig=sig, h_mult=hm) for c in COUPLINGS]
        means = [s_["ccs_mean"] for s_ in coupled]
        lo = .025 if sided == "two" else 0.0
        assert sided in ("two", "upper")
        gate = {"i_common": bool(lo <= common["ccs_quantile_median"] <= .975),
                "ii_chain": bool(lo <= chain["ccs_quantile_median"] <= .975),
                "iii_monotone": bool(all(b > a for a, b in zip(means, means[1:]))),
                "iii_positive": bool(all(s_["ccs_excess_over_null_median_mean"] > 0 for s_ in coupled[1:]))}
        gate["pass_i_to_iii"] = all(gate.values())
        gate["sided"] = sided
        gate["i_common_two_sided"] = bool(.025 <= common["ccs_quantile_median"] <= .975)
        gate["ii_chain_two_sided"] = bool(.025 <= chain["ccs_quantile_median"] <= .975)
        out[key] = {"common": common, "chain": chain, "coupled": coupled, "gate": gate}
    out["gate"] = dict(out[f"h_mult_{h_multipliers[0]:g}"]["gate"])
    out["iv_gradients"] = gradient_check(); out["gate"]["iv_gradients"] = out["iv_gradients"]["pass"]
    out["v_cpu_timing"] = objective_step_timing(torch.device("cpu"))
    sens = {}
    for hm in sensitivity:                                     # descriptive only: not part of the gate
        common = scenario(synth, "common", R=R, N=N, M=M // 2, seed=seed + 1, h_mult=hm)
        g = torch.Generator().manual_seed(seed + 3); sig = calibrate_synth(synth, "coupled", g, c=0.0)
        c2 = scenario(synth, "coupled", R=R, N=N, M=M // 2, seed=seed + 10, c=2.0, sig=sig, h_mult=hm)
        sens[f"{hm:g}"] = {"common_quantile_median": common["ccs_quantile_median"], "common_rejection": common["ccs_rejection_rate_975"],
                           "coupled_c2_excess": c2["ccs_excess_over_null_median_mean"], "coupled_c2_rejection": c2["ccs_rejection_rate_975"],
                           "coupled_c2_quantile_median": c2["ccs_quantile_median"]}
    out["descriptive_h_bandwidth_sensitivity"] = sens
    out["gate"]["pass_cpu_part"] = bool(out["gate"]["pass_i_to_iii"] and out["gate"]["iv_gradients"])
    return out
