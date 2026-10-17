"""E34_PUBLIC_PRIOR rich-target block (private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.15, §6.1; §6.6 M4; inherited
PUBLIC_PRIOR_EXECUTION_v3_3.md §4: missing targets masked, never fabricated; per-head losses averaged over legal samples with fixed
weights, so a cohort with more heads is not implicitly up-weighted): the APR head pairs, the normalised rich loss and the
donor-side rich readout.

Member APR = SharedEncoder (trunk and the envelope projection proj) + RichHeads (rich.proj_ss, rich.proj_sc, fed by trunk()); the
audio side of each head is a SharedFixedHead (envelope: sigma, P; spectral structure: sigma_ss, P_ss; spectral change: sigma_sc,
P_sc). Each term is the audio_pair loss of the objective on its own head pair (CS: its own bandwidths):
  L = (L_env + 0.5 L_ss + 0.5 L_sc) / (1 + 0.5 [ss present] + 0.5 [sc present]).
Donor-side rich readout (§2.15 Downstream; descriptive, never used for selection): for APR and for the core AP of the same group,
the bridge_cal reconstruction r_bar of y_ss and y_sc from ridges fitted on the 300 fixed fit segments.

Interpretations (each also listed as a deviation in the M4 summary):
- rich_loss(u_heads, v_heads, present, objective, sigmas=None, *, keys=None, unknown_clock=None, temperature=TAU) -> (loss, stats):
  the four positional arguments of design §6.1, then the M4 task's sigmas, needed (and checked) for CS_SINGLE only; keys and
  unknown_clock are the NCE inputs of losses.nce_audio_pair, needed (and checked) for NCE only (unknown_clock: the unknown-clock
  family ids, () when none; see losses.py).
- u_heads[h] = (u1, u2), the head-h EEG outputs of both views [B, 32] (eeg_heads builds them from one trunk pass per view);
  v_heads[h] = the head-h audio output [B, 32], or None / absent when the batch has no such target.
- present[h]: a bool (the batch's cohort has the target or not; batches are single-cohort, so a Federici batch trains the envelope
  only) or a [B] bool row mask (rows whose stream has no rich target, e.g. a SparrKULee stream without a usable waveform or with a
  failed clock check). A missing target is masked, never zero-filled: absent rows are left out of that head's term (its mean is over
  its own queries) and are never read (they may hold NaN); a head without any present row leaves the numerator and the normaliser,
  and its EEG outputs get no gradient. Missing keys of `present` mean absent, except the envelope, which is the contract target and
  must be present on every row.
- objective: "NCE" or "CS_SINGLE", or an object with that `.name`; sigmas[h] = (sigma_u, sigma_v) or {"sigma_u", "sigma_v"}.
- stats: loss, norm (the denominator), and per head rows_<h> (present rows) and loss_<h> (its unweighted term).
- rich_readout(u_fit, y_fit, u_cal, y_cal, rel_ridge=1e-2) -> {h: record}. u_fit / u_cal: one member's encoder outputs u = enc(x)
  [n_seg, T, d] (the representation that transfers, as in the §2.10 dev score; the caller computes them on the 300 fixed SparrKULee
  donor-fit segments and on the bridge_cal segments, all ticks, full montage); y_fit[h] / y_cal[h]: the standardised targets
  y_h / sigma_h (mu == 0) [n_seg, T, D_h] of each head (ss 32, sc 8; env may be added as a reference). The ridge is the §2.10
  dev-score rule (no search): intercept, penalty rel_ridge * mean diag(U^T U) over the fit rows, as ev1._ridge with one alpha.
  r_bar = the mean over bridge_cal segments of S(q, own), the mean over the D_h dimensions of the Pearson r over the segment's ticks
  between reconstruction and target (ev1._zt semantics); r_dim = the per-dimension means. A segment whose head-h target is missing
  (any non-finite value: no waveform, failed clock check) is left out of that head's fit and evaluation and counted (masked, never
  zero-filled); a head without a present fit or bridge_cal segment gets r_bar None. Record: r_bar, r_dim, alpha, rel_ridge, dims,
  n_fit, n_fit_missing, n_cal, n_cal_missing.
"""
from __future__ import annotations

import numpy as np
import torch

from .contract import TAU
from .losses import CONTRACT_OBJECTIVES, cs_audio_pair, nce_audio_pair

HEADS = ("env", "ss", "sc")
RICH_WEIGHTS = {"env": 1.0, "ss": 0.5, "sc": 0.5}
READOUT_REL_RIDGE = 1e-2


def eeg_heads(enc, x1, x2, layout=None, mask=None):
    """APR EEG-side head pairs {"env", "ss", "sc"}: (view 1, view 2), one trunk pass per view (the same channel mask on both)."""
    z1, z2 = enc.trunk(x1, layout, mask), enc.trunk(x2, layout, mask)
    r1, r2 = enc.rich(z1), enc.rich(z2)
    return {"env": (enc.project(z1), enc.project(z2)), "ss": (r1["ss"], r2["ss"]), "sc": (r1["sc"], r2["sc"])}


def _sigmas(s):
    if isinstance(s, dict):
        return s["sigma_u"], s["sigma_v"]
    su, sv = s
    return su, sv


def _present_rows(h, present, v, n, device):
    p = torch.as_tensor((present or {}).get(h, h == "env"), device=device).bool()
    m = p.expand(n) if p.ndim == 0 else p.reshape(-1)
    if m.numel() != n:
        raise ValueError(f"rich_loss: present[{h!r}] has {m.numel()} rows for a batch of {n}")
    if h == "env" and not bool(m.all()):
        raise ValueError("rich_loss: the envelope (contract) target must be present on every row")
    if not bool(m.any()):
        return None
    if v is None:
        raise ValueError(f"rich_loss: head {h!r} is marked present but has no target")
    return m


def rich_loss(u_heads, v_heads, present, objective, sigmas=None, *, keys=None, unknown_clock=None, temperature=TAU):
    """Weighted mean of the present heads' audio_pair losses, normalised by the present weights -> (loss, stats)."""
    name = getattr(objective, "name", objective)
    if name not in CONTRACT_OBJECTIVES:
        raise ValueError(f"rich_loss: objective {name!r} is not one of {CONTRACT_OBJECTIVES}")
    if name == "NCE" and keys is None:
        raise ValueError("rich_loss: the NCE terms need the packed keys")
    if name == "NCE" and unknown_clock is None:
        raise ValueError("rich_loss: the NCE terms need unknown_clock (the unknown-clock family ids; () when there are none)")
    if name == "CS_SINGLE" and sigmas is None:
        raise ValueError("rich_loss: the CS terms need sigmas[h] = (sigma_u, sigma_v) of every present head")
    u_env = u_heads["env"][0]
    n, dev = len(u_env), u_env.device
    k = None if keys is None else torch.as_tensor(keys, device=dev).reshape(-1)
    num, den, st = 0.0, 0.0, {}
    for h in HEADS:
        m = _present_rows(h, present, v_heads.get(h), n, dev)
        st[f"rows_{h}"] = 0 if m is None else int(m.sum())
        if m is None:
            continue
        full = bool(m.all())
        (u1, u2), v = u_heads[h], v_heads[h]
        if not full:
            u1, u2, v = u1[m], u2[m], v[m]
        if not bool(torch.isfinite(v).all()):
            raise ValueError(f"rich_loss: non-finite {h!r} target on a present row")
        if name == "NCE":
            l, _ = nce_audio_pair(u1, u2, v, k if full else k[m], temperature, unknown_clock=unknown_clock)
        else:
            l, _ = cs_audio_pair(u1, u2, v, *_sigmas(sigmas[h]))
        num, den = num + RICH_WEIGHTS[h] * l, den + RICH_WEIGHTS[h]
        st[f"loss_{h}"] = float(l.detach())
    loss = num / den
    st.update({"loss": float(loss.detach()), "norm": den})
    return loss, st


def _np64(x):
    return x.detach().cpu().double().numpy() if torch.is_tensor(x) else np.asarray(x, dtype=np.float64)


def _zt(X):
    return (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-12)


def rich_readout(u_fit, y_fit, u_cal, y_cal, rel_ridge=READOUT_REL_RIDGE):
    """Donor-side rich readout: per head, the §2.10 ridge u -> standardised y_h on the fit segments, r_bar = mean S(q, own) on the
    bridge_cal segments; segments whose target is missing are left out and counted -> {h: record}."""
    Uf, Uc = _np64(u_fit), _np64(u_cal)
    if Uf.ndim != 3 or Uc.ndim != 3 or Uf.shape[2] != Uc.shape[2]:
        raise ValueError(f"rich_readout: u [n_seg, T, d] expected for fit and bridge_cal, got {Uf.shape} and {Uc.shape}")
    if set(y_fit) != set(y_cal):
        raise ValueError(f"rich_readout: heads differ between fit {sorted(y_fit)} and bridge_cal {sorted(y_cal)}")
    out = {}
    for h in y_fit:
        Yf, Yc = _np64(y_fit[h]), _np64(y_cal[h])
        if Yf.ndim != 3 or Yc.ndim != 3 or Yf.shape[:2] != Uf.shape[:2] or Yc.shape[:2] != Uc.shape[:2] or Yf.shape[2] != Yc.shape[2]:
            raise ValueError(f"rich_readout: {h!r} targets {Yf.shape} / {Yc.shape} do not match u {Uf.shape} / {Uc.shape}")
        mf, mc = np.isfinite(Yf).all((1, 2)), np.isfinite(Yc).all((1, 2))
        rec = {"dims": int(Yf.shape[2]), "rel_ridge": float(rel_ridge), "n_fit": int(mf.sum()), "n_fit_missing": int((~mf).sum()),
               "n_cal": int(mc.sum()), "n_cal_missing": int((~mc).sum())}
        if not (mf.any() and mc.any()):
            out[h] = {**rec, "r_bar": None, "r_dim": None, "alpha": None}
            continue
        X, Y, Q = Uf[mf].reshape(-1, Uf.shape[2]), Yf[mf].reshape(-1, Yf.shape[2]), Uc[mc]
        if not (np.isfinite(X).all() and np.isfinite(Q).all()):
            raise ValueError(f"rich_readout: non-finite u on a segment with a present {h!r} target")
        alpha = float(rel_ridge) * float(np.einsum("nd,nd->d", X, X).mean())
        mx, my = X.mean(0), Y.mean(0)
        Xc = X - mx
        B = np.linalg.solve(Xc.T @ Xc + alpha * np.eye(X.shape[1]), Xc.T @ (Y - my))
        r = (_zt((Q - mx) @ B + my) * _zt(Yc[mc])).mean(1)          # [n_cal, D_h]: Pearson r per segment and dimension
        out[h] = {**rec, "r_bar": float(r.mean()), "r_dim": r.mean(0).tolist(), "alpha": alpha}
    return out
