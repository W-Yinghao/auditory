#!/usr/bin/env python3
"""Read-only numerical reference for pre-exported source episode diagnostics.

No checkpoint loader, optimizer, data loader, or CS training replacement.
NPZ: logits[V,K,N,N] (already divided by temperature), positive[N,N],
exclusion[N,N], q_prior[K], q_support[K]. Optional eeg[V,K,N,D],
audio[V,N,D]. Labels/identity provenance live in a separate server receipt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np

def require(condition, message):
    if not condition:
        raise ValueError(message)

def finite(a, name):
    a = np.asarray(a, dtype=np.float64)
    require(np.isfinite(a).all(), name + " contains non-finite values")
    return a

def mask(a, name):
    a = np.asarray(a)
    require(a.dtype == np.bool_ or np.isin(a, [0, 1]).all(),
            name + " must be Boolean or 0/1")
    return a.astype(bool)

def logsumexp_masked(scores, legal, axis):
    x = np.where(legal, scores, -np.inf)
    m = x.max(axis=axis, keepdims=True)
    require(np.isfinite(m).all(), "empty mask reduction")
    return (m + np.log(np.exp(x - m).sum(axis=axis, keepdims=True))).squeeze(axis)

def symmetric_loss(scores, positive, exclusion):
    require(scores.ndim == 2, "score matrix must be 2D")
    allowed = ~exclusion
    row = logsumexp_masked(scores, allowed, 1) - logsumexp_masked(scores, positive, 1)
    col = logsumexp_masked(scores, allowed, 0) - logsumexp_masked(scores, positive, 0)
    return float(0.5 * (row.mean() + col.mean()))

def uniform_loss(positive, exclusion):
    allowed = ~exclusion
    return float(0.5 * (
        np.log(allowed.sum(1) / positive.sum(1)).mean()
        + np.log(allowed.sum(0) / positive.sum(0)).mean()
    ))

def tie_credit(scores, positive, exclusion, axis):
    x = np.where(exclusion, -np.inf, scores)
    winners = (x == x.max(axis=axis, keepdims=True)) & ~exclusion
    return float(((winners & positive).sum(axis=axis) / winners.sum(axis=axis)).mean())

def representation_stats(x):
    """Sample-centred squared-singular-value entropy rank, not information."""
    x = finite(x, "features")
    require(x.ndim == 2 and len(x) >= 2, "features require [N,D], N>=2")
    xc = x - x.mean(axis=0, keepdims=True)
    ss = np.linalg.svd(xc, compute_uv=False) ** 2
    norms = np.linalg.norm(x, axis=1)
    raw_scale = max(float(np.square(x).sum()), np.finfo(float).tiny)
    variation = float(ss.sum())
    # Relative roundoff guard detects constant nonzero arrays without deleting them.
    degenerate = variation <= np.finfo(float).eps ** 2 * raw_scale * x.size
    if degenerate:
        effective_rank = 0.0
        top_share = None
    else:
        weights = ss[ss > 0] / variation
        effective_rank = float(np.exp(-np.sum(weights * np.log(weights))))
        top_share = float(weights.max())
    unit = x / np.maximum(norms[:, None], 1e-12)
    cosine = unit @ unit.T
    offdiag = cosine[~np.eye(len(x), dtype=bool)]
    return {
        "n": len(x), "dimension": x.shape[1],
        "centred_total_variance_ddof1": variation / (len(x)-1),
        "effective_rank": effective_rank,
        "top_variance_share": top_share,
        "zero_variance_flag": bool(degenerate),
        "norm_quantiles_0_50_100": np.quantile(norms, [0, .5, 1]).tolist(),
        "near_zero_norm_count": int((norms <= 1e-12).sum()),
        "offdiagonal_cosine_mean": float(offdiag.mean()),
    }

def analyse(arrays):
    required = {"logits", "positive", "exclusion", "q_prior", "q_support"}
    require(required.issubset(arrays), "missing keys: " + str(sorted(required-set(arrays))))
    z = finite(arrays["logits"], "logits")
    require(z.ndim == 4 and z.shape[2] == z.shape[3] and z.shape[2] >= 2,
            "logits must have shape [V,K,N,N], N>=2")
    views, slots, n, _ = z.shape
    require(views > 0 and slots > 0, "empty views/slots")
    pos, exc = mask(arrays["positive"], "positive"), mask(arrays["exclusion"], "exclusion")
    require(pos.shape == exc.shape == (n, n), "mask shapes must match N")
    require(not (pos & exc).any(), "positive and excluded overlap")
    require(pos.any(0).all() and pos.any(1).all(), "every row/column needs a positive")
    qs = {}
    for key in ("q_prior", "q_support"):
        q = finite(arrays[key], key)
        require(q.shape == (slots,) and (q >= 0).all() and abs(q.sum()-1) <= 1e-8,
                key + " must be a probability vector over slots")
        qs[key] = q
    qs["q_uniform"] = np.full(slots, 1.0/slots)
    allowed, neg = ~exc, (~exc & ~pos)
    chance = uniform_loss(pos, exc)
    records, losses = [], np.empty((views, slots))
    for v in range(views):
        for k in range(slots):
            scores = z[v, k]
            loss = symmetric_loss(scores, pos, exc)
            losses[v, k] = loss
            records.append({
                "view_index": v, "slot_index": k,
                "loss_nats": loss, "uniform_score_loss_nats": chance,
                "gain_over_uniform_score_nats": chance-loss,
                "positive_score_mean": float(scores[pos].mean()),
                "legal_negative_score_mean": float(scores[neg].mean()) if neg.any() else None,
                "top1_tie_credit_eeg_to_audio": tie_credit(scores, pos, exc, 1),
                "top1_tie_credit_audio_to_eeg": tie_credit(scores, pos, exc, 0),
            })
    mixes = {key: float(np.mean(losses @ q)) for key, q in qs.items()}
    out = {
        "schema": "aln42_source_probe_metrics_v1",
        "status": "COMPLETE_VALID",
        "scope": "conditional fixed-episode diagnostic; not a population test or CS estimate",
        "n_views": views, "n_slots": slots, "n_anchors": n,
        "positive_count": int(pos.sum()), "excluded_count": int(exc.sum()),
        "allowed_row_counts": allowed.sum(1).tolist(),
        "positive_row_counts": pos.sum(1).tolist(),
        "allowed_col_counts": allowed.sum(0).tolist(),
        "positive_col_counts": pos.sum(0).tolist(),
        "rows_without_legal_negatives": int((neg.sum(1)==0).sum()),
        "cols_without_legal_negatives": int((neg.sum(0)==0).sum()),
        "uniform_score_loss_nats": chance,
        "ln_n_reference_nats": math.log(n),
        "slot_diagnostics": records,
        "q": {key: value.tolist() for key, value in qs.items()},
        "q_weighted_nce_diagnostic_nats": mixes,
        "support_gate_gain_in_supplied_nce_nats": mixes["q_prior"]-mixes["q_support"],
        "group_gate_gain_in_supplied_nce_nats": mixes["q_uniform"]-mixes["q_prior"],
    }
    if "eeg" in arrays:
        e = finite(arrays["eeg"], "eeg")
        require(e.ndim == 4 and e.shape[:3] == (views, slots, n),
                "eeg must be [V,K,N,D]")
        out["eeg_feature_stats"] = [
            {"view_index": v, "slot_index": k, **representation_stats(e[v,k])}
            for v in range(views) for k in range(slots)]
    if "audio" in arrays:
        a = finite(arrays["audio"], "audio")
        require(a.ndim == 3 and a.shape[:2] == (views, n), "audio must be [V,N,D]")
        out["audio_feature_stats"] = [
            {"view_index": v, **representation_stats(a[v])} for v in range(views)]
    return out

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "output exists; use a new path")
        with np.load(args.input, allow_pickle=False) as f:
            report = analyse({k: f[k] for k in f.files})
        report["input_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
        payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as f:
            f.write(payload)
        print(json.dumps({"status": report["status"], "output": str(args.output),
                          "input_sha256": report["input_sha256"]}))
        return 0
    except (ValueError, OSError, KeyError, np.linalg.LinAlgError) as exc:
        print("INVALID_INPUT: " + str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())

