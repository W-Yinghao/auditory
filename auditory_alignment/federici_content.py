"""Federici stimulus-content groups for a strict unseen-content split (replaces the block split after the manifest showed
612 / 639 test stimulus segments also present in fit).

Content identity is defined from the data: each 50 s block's envelope (z-scored) is one stimulus item; exact duplicates are
merged by hash (as in data.load_federici); near-duplicates (vocoded vs natural versions, overlapping excerpts at other
offsets) are merged by union-find when the maximum over all lags of the normalised cross-correlation
sum_t a(t) b(t+l) / N reaches the threshold (a fully aligned identical pair = 1; a partial overlap of fraction f ~ f).
Groups are assigned to fit / es / test (60 / 15 / 25 % of groups) by a seeded permutation.

Usage: python -m auditory_alignment.federici_content [--threshold 0.3]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os

import numpy as np

from .data import FED_PRE, PUB

OUT = f"{PUB}/derived/c3_features_v1/federici/kcs_targets_v1"


def env_key(ez):
    """Stable identity of one z-scored float32 envelope block (rounded to 1e-3)."""
    return hashlib.sha1(np.round(np.asarray(ez, dtype=np.float32).reshape(-1), 3).tobytes()).hexdigest()


def envelopes():
    import h5py
    items, seen = [], {}
    for grp in ("HC", "CI", "HC-v", "Artifact"):
        for p in sorted(glob.glob(os.path.join(FED_PRE, grp, "*.h5"))):
            with h5py.File(p, "r") as f:
                env = f["env"][()].astype(np.float64)
            for b, e in enumerate(env):
                ez = ((e - e.mean()) / (e.std() + 1e-12)).astype(np.float32)
                h = env_key(ez)
                if h not in seen:
                    seen[h] = len(items); items.append({"key": h, "env": ez.astype(np.float64), "first": f"{grp}/{os.path.basename(p)}#{b}", "n_listeners": 0})
                items[seen[h]]["n_listeners"] += 1
    return items


def max_xcorr(E):
    n, N = E.shape
    L = 1 << int(np.ceil(np.log2(2 * N)))
    F = np.fft.rfft(E, L, axis=1)
    M = np.zeros((n, n))
    for i in range(n):
        c = np.fft.irfft(F[i][None].conj() * F[i:], L, axis=1) / N
        M[i, i:] = c.max(1); M[i:, i] = M[i, i:]
    return M


def main():
    a = argparse.ArgumentParser(); a.add_argument("--threshold", type=float, default=0.3); args = a.parse_args()
    items = envelopes()
    lens = {len(it["env"]) for it in items}
    N = min(lens)
    E = np.stack([it["env"][:N] for it in items])
    M = max_xcorr(E)
    off = M[~np.eye(len(M), dtype=bool)]
    hist = np.histogram(off, bins=[0, .05, .1, .15, .2, .25, .3, .4, .5, .6, .7, .8, .9, 1.01])
    parent = list(range(len(items)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if M[i, j] >= args.threshold:
                parent[find(i)] = find(j)
    roots = sorted({find(i) for i in range(len(items))})
    gid = {r: k for k, r in enumerate(roots)}
    groups = [gid[find(i)] for i in range(len(items))]
    perm = np.random.default_rng(20261005).permutation(len(roots))
    n_fit, n_es = int(round(0.60 * len(roots))), int(round(0.15 * len(roots)))
    role = {}
    for rank, g in enumerate(perm):
        role[int(g)] = "fit" if rank < n_fit else ("es" if rank < n_fit + n_es else "test")
    out = {"rule": f"envelope items (exact-hash dedup); union-find on max-lag normalised cross-correlation >= {args.threshold}; "
                   "groups permuted (seed 20261005): 60% fit, 15% es, 25% test",
           "n_items": len(items), "n_groups": len(roots), "item_samples": N, "lengths": sorted(lens),
           "offdiag_maxxcorr_hist": {"edges": hist[1].tolist(), "counts": hist[0].tolist()},
           "offdiag_maxxcorr_quantiles": {q: float(np.quantile(off, q)) for q in (0.5, 0.9, 0.99, 0.999)},
           "group_sizes": sorted(np.bincount(groups).tolist(), reverse=True)[:20],
           "role_counts_groups": {r: sum(1 for v in role.values() if v == r) for r in ("fit", "es", "test")},
           "items": [{"key": it["key"], "first": it["first"], "n_listeners": it["n_listeners"], "group": groups[i], "role": role[groups[i]],
                      "max_xcorr_other": float(np.max(np.r_[M[i, :i], M[i, i + 1:]])) if len(items) > 1 else None} for i, it in enumerate(items)]}
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "content_groups.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "items"}, indent=1))


if __name__ == "__main__":
    main()
