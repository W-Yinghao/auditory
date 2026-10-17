"""E34_PUBLIC_PRIOR losses (private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.5, §2.7-§2.9, §2.12; §6.6 M4; inherited
OBJECTIVES_v3_3.md §2-§4): the contract NCE (multi-positive log-sum-exp with the +-2 s same-content neighbour mask on the shared
stimulus clock) at both stages, the traditional kernel CS with the full kernel formula, the bandwidth rule, and ContractObjective.

NCE. s_qj = cos(q, j) / tau (tau = 0.1), float64. l_q = -log sum_{j in P(q)} e^{s_qj} + log sum_{j not in E(q)} e^{s_qj}; positives
stay in the denominator and P(q) and E(q) are disjoint. From packed keys (contract.pack_key: family, presentation, family-clock
sample s): P(q) = equal keys; E(q) = same family, |s_q - s_j| <= NEIGHBOR (128 samples, 2.000 s, inclusive), not positive; for a
family whose relative clock is unknown (`unknown_clock`, e.g. Federici natural / vocoded pairs without a measurable lag) also every
candidate of another presentation of that family at any time. cross_person (and XM, called with X2[pi] and X1's keys) also puts any
candidate of the same participant at the same key into E, so a physical observation is never its own positive.
  audio_pair: EEG -> audio (the 2B rows of both views over the B unique audio rows, 1 positive each) and audio -> EEG (B queries over
  the 2B EEG rows, 2 positives each); L = (mean l_E->A + mean l_A->E) / 2. cross_person: bipartite view 1 -> view 2 and view 2 ->
  view 1 (B x B each); L = (mean + mean) / 2. single_view (target stage, A_LOCAL batches): u -> v and v -> u over the n rows; with
  unique keys and no mask it equals auditory_alignment.losses_reference.symmetric_infonce.
CS. I = log A + log B - 2 log C via auditory_alignment.losses_reference.cs_qmi, imported unchanged (diagonal kept, uniform weights,
Gaussian kernels; no mask argument exists, so no NCE mask can enter K or L); loss = -I. audio_pair rows (u_r, v_a(r)), r = 1..2B,
v repeated; cross_person rows ([u1; u2], [u2; u1]) with sigma_u on both sides.

Interpretations (each also listed as a deviation in the M4 summary):
- Every loss function returns (loss, stats) like cs_qmi and Objective.__call__: loss a differentiable float64 scalar, stats a dict
  of numbers. NCE stats: loss, and per direction (audio_pair e2a / a2e, cross_person 12 / 21, single_view uv / vu) loss_<dir>,
  n_q_<dir>, nopos_<dir> (queries without a positive), pos_per_q_<dir> and masked_per_q_<dir> (means over the counted queries);
  one device sync per call. CS stats are cs_qmi's (cs_qmi_nats, log_joint_square = log A,
  log_marginal_product_square = log B, log_cross_overlap = log C, n_rows).
- masked_lse_nce(S, pos, excl): S = logits [nq, nc] (already divided by tau); returns l_q [nq] (float64); overlapping P / E or a
  query without a positive raises. The pair losses instead drop a query without a positive from its direction's mean (it gets a
  finite dummy term with weight 0, so no NaN gradient) and count it: that happens only when the sole same-key candidate is the same
  participant (an XM derangement violation on a small stratum, or a self pair).
- Keys are torch.int64 packed contract keys (numpy int64 accepted); participant ids are integer ids, one per row.
- nce_cross_person (and XM) requires the participant ids of both views; None raises, because without them the same physical
  observation at the same key would become its own positive (OBJECTIVES §2, design §2.7).
- unknown_clock is a required keyword-only input of nce_masks, nce_audio_pair, nce_cross_person, nce_single_view and
  ContractObjective: the family ids whose relative clock is unknown (unknown_clock_families(manifest): the manifest families with
  clock "unknown"), or () when there are none; None raises ValueError and omission raises TypeError. Reason: §2.5 makes the mask
  cover the whole partner item of such a family, but the clock status is not in the packed key, so a default would silently drop
  the rule. Callers: donor training passes unknown_clock_families(manifest) on every batch (family ids are global, so the whole set
  is safe for every stratum); the generated target copy writes §2.12 substitution 4 as ContractObjective(obj_job, ...,
  unknown_clock=unknown_clock_families(manifest)), so the literal ContractObjective(obj_job, ...) raises instead of dropping the rule.
- calibrate_sigma(rows, weights=None, multiplier=1.0): the median off-diagonal Euclidean distance (the Objective rule:
  auditory_alignment.train._offdiag_median_dist, lower median for an even count) of one calibration batch, or the stratum-weighted
  mean of the per-batch medians of a list of batches; the caller passes [u1; u2] of the initial encoder per donor cohort for sigma_u
  and the unique audio rows for sigma_v (cross_person and XM use sigma_u on both sides).
- ContractObjective(job, u0, v0, labels0=None, *, unknown_clock) subclasses auditory_alignment.train.Objective (the task text
  places Objective in auditory_alignment/losses.py; it is defined in auditory_alignment/train.py). Same calibration (median rule,
  multiplier from the job), same record() plus the NCE tag and the unknown-clock families; the NCE continuous path is
  nce_single_view on the packed keys the batcher passes (for a rolled early-stopping batch these are the rolled audio's keys, so
  its mask is the rolled audio's mask); the labels / prototypes path and CS_SINGLE delegate unchanged; objectives other than NCE
  and CS_SINGLE raise.
Design-text note (§2.8 "the n = 512 ceiling of log n is 6.24 nats", §7.1 6 "approaches log n when sigma -> 0"): with narrow kernels
(K, L -> I on distinct rows) the estimator tends to log n, which is cross_person's limit (2B = 512 distinct rows: 6.24 nats);
audio_pair repeats each v twice, so its limit is log(n / 2) = log B (n = 512 rows: log 256 = 5.55 nats). Independent random rows
reach both limits (test_model_losses.py::test_cs_narrow_kernel_limit_is_log_n_even_without_dependence).
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn.functional as F

from auditory_alignment.losses_reference import cs_qmi
from auditory_alignment.train import Objective, _offdiag_median_dist

from .contract import FAMILY_BITS, NEIGHBOR, TAU, unpack_key

CONTRACT_OBJECTIVES = ("NCE", "CS_SINGLE")
NCE_TAG = "contract_lse_mask2s_v1"
CLOCKS = ("known", "unknown")


def _keys(k, device=None, n=None):
    if k is None:
        raise ValueError("the contract NCE needs the packed keys of the rows")
    k = torch.as_tensor(k, device=device)
    if k.dtype != torch.int64:
        raise TypeError(f"packed contract keys must be int64, got {k.dtype}")
    k = k.reshape(-1)
    if n is not None and len(k) != n:
        raise ValueError(f"{len(k)} keys for {n} rows")
    return k


def _ids(p, device, n):
    p = torch.as_tensor(p, device=device).reshape(-1)
    if p.dtype.is_floating_point or p.dtype == torch.bool or len(p) != n:
        raise ValueError(f"participant ids: {n} integers expected, got {p.dtype} x {len(p)}")
    return p


def _clock_families(unknown_clock, device=None):
    """The unknown-clock family ids as int64 [m] (m may be 0); None raises: the caller names the families or passes ()."""
    if unknown_clock is None:
        raise ValueError("unknown_clock: pass the unknown-clock family ids (unknown_clock_families(manifest)), or () if none")
    a = np.asarray(unknown_clock.detach().cpu() if torch.is_tensor(unknown_clock) else list(unknown_clock))
    if a.size and (a.dtype.kind not in "iu" or a.min() < 0 or a.max() >= 1 << FAMILY_BITS):
        raise TypeError(f"unknown_clock: family ids in [0, 2**{FAMILY_BITS}) expected, got {a.dtype} {a.ravel()[:4].tolist()}")
    return torch.as_tensor(a.astype(np.int64).reshape(-1), device=device)


def unknown_clock_families(manifest):
    """Family ids whose members' relative clock is unknown: the manifest families with clock 'unknown' (§2.5, decided by C3)."""
    fams = manifest["families"]
    bad = sorted({str(f.get("clock")) for f in fams} - set(CLOCKS))
    if bad:
        raise ValueError(f"unknown_clock_families: family clock must be one of {CLOCKS}, got {bad}")
    return sorted(int(f["id"]) for f in fams if f["clock"] == "unknown")


def nce_masks(kq, kc, pid_q=None, pid_c=None, *, unknown_clock):
    """(pos, excl) [nq, nc]: positives = equal keys (different participant when ids are given); excl = same family within +-128
    family-clock samples and not positive, every other presentation of an unknown-clock family, and (ids) same participant at the
    same key."""
    kq = _keys(kq)
    kc = _keys(kc, kq.device)
    uc = _clock_families(unknown_clock, kq.device)
    fq, pq, sq = unpack_key(kq)
    fc, pc, sc = unpack_key(kc)
    same = kq[:, None] == kc[None, :]
    near = (sq[:, None] - sc[None, :]).abs() <= NEIGHBOR
    if uc.numel():
        near = near | (torch.isin(fq, uc)[:, None] & (pq[:, None] != pc[None, :]))
    pos, excl = same, (fq[:, None] == fc[None, :]) & near & ~same
    if (pid_q is None) != (pid_c is None):
        raise ValueError("nce_masks: give participant ids for both sides or for neither")
    if pid_q is not None:
        own = same & (_ids(pid_q, kq.device, len(kq))[:, None] == _ids(pid_c, kq.device, len(kc))[None, :])
        pos, excl = same & ~own, excl | own
    return pos, excl


def _lse(S, pos, excl):
    return torch.logsumexp(S.masked_fill(excl, float("-inf")), 1) - torch.logsumexp(S.masked_fill(~pos, float("-inf")), 1)


def masked_lse_nce(S, pos, excl):
    """Per-query multi-positive NCE l_q = -log sum_{P(q)} e^S + log sum_{not E(q)} e^S, float64 [nq]; S are logits (cos / tau)."""
    S = S.double()
    pos, excl = torch.as_tensor(pos, device=S.device).bool(), torch.as_tensor(excl, device=S.device).bool()
    if S.ndim != 2 or pos.shape != S.shape or excl.shape != S.shape:
        raise ValueError(f"masked_lse_nce: S {tuple(S.shape)}, pos {tuple(pos.shape)}, excl {tuple(excl.shape)}")
    if bool((pos & excl).any()):
        raise ValueError("masked_lse_nce: P(q) and E(q) must be disjoint")
    if not bool(pos.any(1).all()):
        raise ValueError("masked_lse_nce: every query needs at least one positive")
    return _lse(S, pos, excl)


def _cos(a, b, temperature):
    t = float(temperature)
    if not (math.isfinite(t) and t > 0):
        raise ValueError(f"temperature must be finite and > 0, got {temperature!r}")
    return F.normalize(a.double(), dim=1) @ F.normalize(b.double(), dim=1).T / t


def _direction(S, pos, excl):
    has = pos.any(1)
    w = has.double()
    n = w.sum().clamp_min(1)
    loss = (_lse(S, pos | ~has[:, None], excl & has[:, None]) * w).sum() / n
    return loss, [loss.detach(), (~has).sum().double(), (pos.sum(1) * w).sum() / n, (excl.sum(1) * w).sum() / n]


def _result(loss, parts):
    names, vals = ["loss"], [loss.detach()]
    for tag, (st, nq) in parts.items():
        names += [f"loss_{tag}", f"nopos_{tag}", f"pos_per_q_{tag}", f"masked_per_q_{tag}"]
        vals += st
    out = dict(zip(names, torch.stack([v.double().reshape(()) for v in vals]).tolist()))
    for tag, (_, nq) in parts.items():
        out[f"n_q_{tag}"], out[f"nopos_{tag}"] = int(nq), int(out[f"nopos_{tag}"])
    return loss, out


def _rows(*xs):
    n = len(xs[0])
    if any(x.ndim != 2 or len(x) != n for x in xs) or len({x.shape[1] for x in xs}) != 1:
        raise ValueError(f"paired rows [n, d] expected, got {[tuple(x.shape) for x in xs]}")
    return n


def nce_audio_pair(u1, u2, v, keys, temperature=TAU, *, unknown_clock):
    """audio_pair NCE of two EEG views u1, u2 [B, d] against the B audio rows v [B, d] with packed keys [B] -> (loss, stats)."""
    k = _keys(keys, v.device, _rows(u1, u2, v))
    kU = torch.cat([k, k])
    S = _cos(torch.cat([u1, u2]), v, temperature)
    pos, excl = nce_masks(kU, k, unknown_clock=unknown_clock)
    l1, s1 = _direction(S, pos, excl)
    l2, s2 = _direction(S.T, pos.T, excl.T)
    return _result((l1 + l2) / 2, {"e2a": (s1, len(kU)), "a2e": (s2, len(k))})


def nce_cross_person(u1, u2, keys, pid1, pid2, temperature=TAU, *, unknown_clock):
    """cross_person (XM: u2 = X2[pi] with X1's keys and pid2 = the deranged partners) bipartite NCE -> (loss, stats)."""
    if pid1 is None or pid2 is None:
        raise ValueError("nce_cross_person: the participant ids of both views are required (an observation is never its own positive)")
    n = _rows(u1, u2)
    k = _keys(keys, u1.device, n)
    S = _cos(u1, u2, temperature)
    pos, excl = nce_masks(k, k, pid1, pid2, unknown_clock=unknown_clock)
    l1, s1 = _direction(S, pos, excl)
    l2, s2 = _direction(S.T, pos.T, excl.T)
    return _result((l1 + l2) / 2, {"12": (s1, n), "21": (s2, n)})


def nce_single_view(u, v, keys, temperature=TAU, *, unknown_clock):
    """Target-stage NCE of n paired rows u, v [n, d] with packed keys [n] (u -> v and v -> u) -> (loss, stats)."""
    n = _rows(u, v)
    k = _keys(keys, u.device, n)
    S = _cos(u, v, temperature)
    pos, excl = nce_masks(k, k, unknown_clock=unknown_clock)
    l1, s1 = _direction(S, pos, excl)
    l2, s2 = _direction(S.T, pos.T, excl.T)
    return _result((l1 + l2) / 2, {"uv": (s1, n), "vu": (s2, n)})


def cs_audio_pair(u1, u2, v, sigma_u, sigma_v):
    """-I_CS of the rows (u_r, v_a(r)), r = 1..2B (v repeated), full kernel formula -> (loss, cs_qmi stats)."""
    _rows(u1, u2, v)
    val, st = cs_qmi(torch.cat([u1, u2]), torch.cat([v, v]), sigma_u=float(sigma_u), sigma_v=float(sigma_v))
    return -val, st


def cs_cross_person(u1, u2, sigma_u):
    """-I_CS of the rows ([u1; u2], [u2; u1]) (both orderings), sigma_u on both sides -> (loss, cs_qmi stats)."""
    _rows(u1, u2)
    val, st = cs_qmi(torch.cat([u1, u2]), torch.cat([u2, u1]), sigma_u=float(sigma_u), sigma_v=float(sigma_u))
    return -val, st


def calibrate_sigma(rows, weights=None, multiplier=1.0):
    """Median off-diagonal distance of a calibration batch [n, d], or the weighted mean over a list of per-stratum batches."""
    batches = [rows] if torch.is_tensor(rows) else list(rows)
    meds = [_offdiag_median_dist(x.detach()) for x in batches]
    w = [1.0] * len(meds) if weights is None else [float(a) for a in weights]
    if not meds or len(w) != len(meds) or min(w) < 0 or sum(w) <= 0:
        raise ValueError(f"calibrate_sigma: {len(meds)} batches with weights {weights}")
    s = sum(a * m for a, m in zip(w, meds)) / sum(w) * float(multiplier)
    if not (math.isfinite(s) and s > 0):
        raise ValueError(f"calibrate_sigma: degenerate bandwidth {s}")
    return s


class ContractObjective(Objective):
    """auditory_alignment.train.Objective with the contract NCE on the continuous path; labels / prototypes and CS unchanged."""

    def __init__(self, job, u0, v0, labels0=None, *, unknown_clock):
        uc = sorted(_clock_families(unknown_clock).tolist())
        super().__init__(job, u0, v0, labels0=labels0)
        if self.name not in CONTRACT_OBJECTIVES:
            raise ValueError(f"ContractObjective: objective {self.name!r} is not one of {CONTRACT_OBJECTIVES}")
        self.unknown_clock = uc

    def record(self):
        r = super().record()
        r.update({"nce": NCE_TAG, "neighbor_samples": NEIGHBOR, "unknown_clock_families": self.unknown_clock})
        return r

    def __call__(self, u, v=None, keys=None, labels=None, prototypes=None):
        if labels is not None or self.name != "NCE":
            return super().__call__(u, v, keys=keys, labels=labels, prototypes=prototypes)
        return nce_single_view(u, v, keys, self.temperature, unknown_clock=self.unknown_clock)
