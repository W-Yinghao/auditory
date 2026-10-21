"""NumPy reference for classical CS on (EEG representation, time slot) x audio.

This is a reference calculation, not a production trainer or a new divergence.
One call represents ONE person's episode. Physical time windows and person
identities are provided by the data interface, not inferred by this module.

u: [n_anchor, n_slot, d_eeg]; v: [n_anchor, d_audio].
q: [n_slot], shared by all anchors in the episode, summing to one.

Within each view, all slots MUST use the same Gaussian overlap sigma_u and
the same EEG representation dimension/scale. A separate view may use its own
sigma. Time uses counting measure, with overlap 1[slot == slot']. The source
audio marginal remains uniform over anchors. No diagonal removal, Gram
centering, arbitrary temporal kernel, NCE mask, score clamp, or bandwidth fit
on support/query is implemented here.
"""

from __future__ import annotations

import numpy as np


def logsumexp(x, axis=None):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(x, axis=axis, keepdims=True)
    safe = np.where(np.isfinite(m), m, 0.0)
    with np.errstate(under="ignore", divide="ignore", invalid="ignore"):
        out = safe + np.log(np.sum(np.exp(x - safe), axis=axis, keepdims=True))
    return np.squeeze(out, axis=axis) if axis is not None else out.reshape(()).item()


def softmax(logits):
    logits = np.asarray(logits, dtype=np.float64)
    if logits.ndim != 1 or not np.isfinite(logits).all():
        raise ValueError("finite one-dimensional logits required")
    return np.exp(logits - logsumexp(logits))


def gaussian_log_gram(x, sigma):
    """sigma denotes overlap-kernel SD, sqrt(2) times KDE component SD."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("at least two finite sample rows required")
    if np.ndim(sigma) != 0 or not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("one finite positive scalar sigma required")
    delta = (x[:, None, :] - x[None, :, :]) / float(sigma)
    with np.errstate(over="raise", invalid="raise"):
        return -0.5 * np.sum(delta * delta, axis=-1)


def _validate_q(q, n_slot):
    q = np.asarray(q, dtype=np.float64)
    if q.shape != (n_slot,) or not np.isfinite(q).all() or np.any(q < 0):
        raise ValueError("one nonnegative finite probability per slot required")
    if not np.isclose(q.sum(), 1.0, atol=1e-12, rtol=1e-12):
        raise ValueError("q must sum to one; no silent renormalization")
    return q


def _validate_views(u, v):
    u, v = np.asarray(u, dtype=np.float64), np.asarray(v, dtype=np.float64)
    if u.ndim != 3 or v.ndim != 2 or u.shape[0] != v.shape[0]:
        raise ValueError("u=[n,slot,d_u], v=[n,d_v] with the same anchors required")
    if u.shape[0] < 2 or u.shape[1] < 1 or u.shape[2] < 1 or v.shape[1] < 1:
        raise ValueError("empty feature/slot axes or fewer than two anchors")
    if not np.isfinite(u).all() or not np.isfinite(v).all():
        raise ValueError("all representations must be finite")
    return u, v


def temporal_cs_potentials(u, v, sigma_u, sigma_v):
    """Return log A_l, log B_l, log C_l for each slot.

    Gaussian global normalization constants are omitted. They cancel from the
    FINAL score only because sigma_u, dimension and measure are shared across
    slots in a view. The potentials themselves are unnormalized overlaps.
    """
    u, v = _validate_views(u, v)
    n, n_slot, _ = u.shape
    if np.ndim(sigma_u) != 0:
        raise ValueError("slot-specific EEG sigmas are not permitted")
    log_l = gaussian_log_gram(v, sigma_v)
    log_n = np.log(n)
    log_audio_integral = logsumexp(log_l) - 2 * log_n
    row_l = logsumexp(log_l, axis=1)
    log_a, log_b, log_c = [], [], []
    for slot in range(n_slot):
        log_k = gaussian_log_gram(u[:, slot], sigma_u)
        log_a.append(logsumexp(log_k + log_l) - 2 * log_n)
        log_b.append(logsumexp(log_k) - 2 * log_n + log_audio_integral)
        row_k = logsumexp(log_k, axis=1)
        log_c.append(logsumexp(row_k + row_l) - 3 * log_n)
    return {
        "log_A_slot": np.asarray(log_a),
        "log_B_slot": np.asarray(log_b),
        "log_C_slot": np.asarray(log_c),
        "n_anchor": n,
        "n_slot": n_slot,
    }


def temporal_cs_from_potentials(potentials, q):
    """Classical CS: log(sum q^2 A)+log(sum q^2 B)-2log(sum q^2 C)."""
    la = np.asarray(potentials["log_A_slot"], dtype=np.float64)
    lb = np.asarray(potentials["log_B_slot"], dtype=np.float64)
    lc = np.asarray(potentials["log_C_slot"], dtype=np.float64)
    if la.ndim != 1 or lb.shape != la.shape or lc.shape != la.shape:
        raise ValueError("same one-dimensional slot shape for A, B and C required")
    if not (np.isfinite(la).all() and np.isfinite(lb).all() and np.isfinite(lc).all()):
        raise ValueError("finite slot log-potentials required")
    q = _validate_q(q, len(la))
    with np.errstate(divide="ignore"):
        two_log_q = 2 * np.log(q)
    log_a = logsumexp(two_log_q + la)
    log_b = logsumexp(two_log_q + lb)
    log_c = logsumexp(two_log_q + lc)
    share_a = np.exp(two_log_q + la - log_a)
    share_b = np.exp(two_log_q + lb - log_b)
    share_c = np.exp(two_log_q + lc - log_c)
    # d score / d logits when q = softmax(logits). Common -2q terms cancel.
    grad_logits = 2 * (share_a + share_b - 2 * share_c)
    return {
        "score_nats": float(log_a + log_b - 2 * log_c),
        "log_A": float(log_a),
        "log_B": float(log_b),
        "log_C": float(log_c),
        "slot_scores_nats": la + lb - 2 * lc,
        "q": q.copy(),
        "normalized_q_squared": q * q / np.sum(q * q),
        "A_shares": share_a,
        "B_shares": share_b,
        "C_shares": share_c,
        "score_gradient_logits": grad_logits,
    }


def temporal_cs(u, v, q, sigma_u, sigma_v):
    p = temporal_cs_potentials(u, v, sigma_u, sigma_v)
    return {**p, **temporal_cs_from_potentials(p, q)}


def weighted_cs_from_log_grams(log_k, log_l, weights):
    """Generic exact KDE-overlap formula, used for independent expanded checks."""
    log_k, log_l = np.asarray(log_k), np.asarray(log_l)
    w = np.asarray(weights, dtype=np.float64)
    if log_k.shape != (len(w), len(w)) or log_l.shape != log_k.shape:
        raise ValueError("Gram and weight shapes differ")
    _validate_q(w, len(w))
    with np.errstate(divide="ignore"):
        lw = np.log(w)
    log_a = logsumexp(log_k + log_l + lw[:, None] + lw[None, :])
    log_b = (logsumexp(log_k + lw[:, None] + lw[None, :])
             + logsumexp(log_l + lw[:, None] + lw[None, :]))
    rk = logsumexp(log_k + lw[None, :], axis=1)
    rl = logsumexp(log_l + lw[None, :], axis=1)
    log_c = logsumexp(lw + rk + rl)
    return float(log_a + log_b - 2 * log_c)


def temporal_cs_expanded(u, v, q, sigma_u, sigma_v):
    """Slow explicit (anchor,slot) KDE; independent of q^2 simplification."""
    u, v = _validate_views(u, v)
    n, n_slot, d_u = u.shape
    q = _validate_q(q, n_slot)
    u_flat = u.transpose(1, 0, 2).reshape(n * n_slot, d_u)
    v_flat = np.tile(v, (n_slot, 1))
    times = np.repeat(np.arange(n_slot), n)
    log_k = gaussian_log_gram(u_flat, sigma_u)
    log_k[times[:, None] != times[None, :]] = -np.inf
    log_l = gaussian_log_gram(v_flat, sigma_v)
    w = np.repeat(q / n, n)
    return weighted_cs_from_log_grams(log_k, log_l, w)


def adapt_delta_cs(support_potentials_by_view, prior_logits, *,
                   steps=5, step_size=0.1, l2=0.1):
    """Reference support-only gate update with an exactly stated objective.

    Inner loss = -mean_view CS(support; softmax(a+delta))
                 + l2/2 * ||delta||_2^2.
    delta starts at zero for EVERY episode; mean-zero projection removes its
    softmax-null direction. Defaults are reference examples, not tuned values.

    Production FO training must build these potentials from detached support
    representations and detached a, then evaluate QUERY using live a +
    stop_gradient(delta_final). No query is accepted by this function.
    """
    a = np.asarray(prior_logits, dtype=np.float64)
    if a.ndim != 1 or not np.isfinite(a).all():
        raise ValueError("finite 1-D prior logits required")
    if steps < 0 or step_size <= 0 or l2 < 0:
        raise ValueError("invalid inner optimization settings")
    if not support_potentials_by_view:
        raise ValueError("at least one support view required")
    delta = np.zeros_like(a)
    history = []
    for step in range(steps):
        q = softmax(a + delta)
        states = [temporal_cs_from_potentials(p, q) for p in support_potentials_by_view]
        score = np.mean([r["score_nats"] for r in states])
        grad_score = np.mean([r["score_gradient_logits"] for r in states], axis=0)
        loss = -score + 0.5 * l2 * np.dot(delta, delta)
        gradient = -grad_score + l2 * delta
        history.append({"step": step, "support_inner_loss": float(loss),
                        "q": q.tolist(), "delta_l2": float(np.linalg.norm(delta))})
        delta = delta - step_size * gradient
        delta = delta - delta.mean()
    return {"delta": delta, "q": softmax(a + delta), "history": history,
            "steps": int(steps), "step_size": float(step_size), "l2": float(l2)}


def uniform_prior_kl(prior_logits):
    q = softmax(prior_logits)
    log_ratio = np.log(q) + np.log(len(q))
    value = np.dot(q, log_ratio)
    return float(value), q * (log_ratio - value)
