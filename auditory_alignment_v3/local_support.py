"""ALN3 ADDENDUM_07 ALN32_LOCAL_SUPPORT: support-matched local controls for the query-aligned FM (B_ALIGNED).

  local_aligned1000      the A_LOCAL lag_local_tokens encoder and recipe (local_train.fit_continuous, unchanged) on the
                         B_ALIGNED window [t - 0.4 s, t + 0.6 s), zero before the segment start (segments are contiguous and
                         non-overlapping within a trial, so each anchor's segment is the latest segment start <= anchor)
  raw_aligned1000_ridge  closed-form ridge from that raw masked window to the fixed d = 32 target projection
  raw_post600_ridge      the same ridge on the A_LOCAL window [t, t + 0.6 s)
Evaluation: core.evaluate_grid, as A_LOCAL. The batcher is patched per process (local_train.GridBatcher); no hashed file is
edited."""
from __future__ import annotations

import os
import time
import traceback

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import core
from .local_train import GridBatcher

PRE_S = 0.4
SUPPORT = {"local_aligned1000": "aligned1000", "raw_aligned1000_ridge": "aligned1000", "raw_post600_ridge": "post600"}


def masked_windows(E, e_idx, a, b, starts):
    """E [C, N]; e_idx [n] anchors; window [e + a, e + b); zero where before the anchor's segment start -> [n, C, b - a]."""
    idx = e_idx[:, None] + torch.arange(a, b, device=E.device)[None]
    s = starts[torch.searchsorted(starts, e_idx, right=True) - 1]
    x = E[:, idx.clamp(min=0)].permute(1, 0, 2).float()
    return x * (idx >= s[:, None])[:, None, :].to(x.dtype)


def batcher_for(support):
    class LocalSupportBatcher(GridBatcher):
        def __init__(self, coh, spec, row, dev, grid):
            super().__init__(coh, {**spec, "window": "full"}, row, dev, grid)
            assert len(self.W) == 1 and self.W[0][0] == 0, self.W  # lag_local_tokens full = one window [0, post)
            post = self.W[0][1]; pre = int(round(PRE_S * self.fs)) if support == "aligned1000" else 0
            self.W = [(-pre, post)]; self.pre, self.post, self.support = pre, post, support
            self.starts = torch.tensor(sorted({s["e0"] for s in self.coh_segments}), device=dev)

        def patches(self, e_idx):
            e_idx = torch.as_tensor(e_idx, device=self.dev)
            return [masked_windows(self.E, e_idx, self.W[0][0], self.W[0][1], self.starts)]
    return LocalSupportBatcher


class RawRidge(nn.Module):
    """u = normalise(((x - mu) / sd) @ B + v_bar) on the flattened masked window."""

    def __init__(self, p, d):
        super().__init__()
        self.register_buffer("mu", torch.zeros(p)); self.register_buffer("sd", torch.ones(p)); self.lin = nn.Linear(p, d)

    def forward(self, patches):
        return F.normalize(self.lin((patches[0].flatten(1) - self.mu) / self.sd), dim=-1)


def _rows(bt, units, rng, chunk=32):
    for k in range(0, len(units), chunk):
        r = bt.rows(list(units[k:k + chunk]), rng, anchors=8)
        yield r[0], r[1], r[2]


@torch.no_grad()
def fit_raw_ridge(b, coh, dev, log, d=32, grid=3, support="aligned1000"):
    from auditory_alignment.train import Objective
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    bt = batcher_for(support)(coh, b["spec"], b, dev, grid)
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(b["seed"] + 5))).to(dev).eval()
    rng = np.random.default_rng(b["seed"])
    n = 0; Sx = Sxx = Sxv = Sv = None
    for e, s, _ in _rows(bt, bt.fit, rng):
        X = bt.patches(e)[0].flatten(1).double(); V = head(bt.audio(s)).double()
        if Sx is None:
            p = X.shape[1]; Sx = torch.zeros(p, dtype=torch.float64, device=dev); Sxx = torch.zeros(p, p, dtype=torch.float64, device=dev)
            Sxv = torch.zeros(p, V.shape[1], dtype=torch.float64, device=dev); Sv = torch.zeros(V.shape[1], dtype=torch.float64, device=dev)
        n += len(X); Sx += X.sum(0); Sxx += X.T @ X; Sxv += X.T @ V; Sv += V.sum(0)
    mu = Sx / n; vbar = Sv / n
    cov = Sxx / n - torch.outer(mu, mu); sd = torch.sqrt(torch.clamp(torch.diag(cov), min=0)) + 1e-6
    G = cov / torch.outer(sd, sd); H = (Sxv / n - torch.outer(mu, vbar)) / sd[:, None]
    es = [(bt.patches(e)[0].flatten(1).double(), head(bt.audio(s)).double()) for e, s, _ in _rows(bt, bt.es, np.random.default_rng(b["seed"] + 1))]
    Xe = torch.cat([x for x, _ in es]); Ve = torch.cat([v for _, v in es]); Ze = (Xe - mu) / sd
    tr = float(torch.trace(G)) / G.shape[0]; curve = []; best = None
    for a in np.logspace(-4, 2, 7):
        B = torch.linalg.solve(G + float(a) * tr * torch.eye(G.shape[0], dtype=G.dtype, device=dev), H)
        P = Ze @ B + vbar; P0 = P - P.mean(0); V0 = Ve - Ve.mean(0)
        r = float(((P0 * V0).sum(0) / (torch.sqrt((P0 ** 2).sum(0) * (V0 ** 2).sum(0)) + 1e-12)).mean())
        curve.append({"alpha_rel": float(a), "es_mean_corr": r})
        if best is None or r > best[0]:
            best = (r, float(a), B)
    enc = RawRidge(G.shape[0], d).to(dev)
    enc.mu.copy_(mu.float()); enc.sd.copy_(sd.float()); enc.lin.weight.copy_(best[2].T.float()); enc.lin.bias.copy_(vbar.float())
    enc.eval()
    calib = next(bt.epoch_batches(np.random.default_rng(b["seed"] + 99), 32))
    r0 = bt.rows(calib, np.random.default_rng(b["seed"] + 98), anchors=8)
    obj = Objective({"objective": b["spec"]["objective"], "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}},
                    enc(bt.patches(r0[0])), head(bt.audio(r0[1])))
    log.update({"objective_calibration": obj.record(), "ridge_alpha_rel": best[1], "ridge_curve": curve, "n_fit_rows": int(n), "n_es_rows": int(len(Xe)),
                "feature_dim": int(G.shape[0]), "window_samples": [int(bt.W[0][0]), int(bt.W[0][1])], "support": support,
                "n_fit_segments": len(bt.fit), "n_es_segments": len(bt.es), "n_train_participants": len(bt.train_p)})
    return enc, head, bt


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from . import local_train
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    s = row["spec"]; v = s["variant"]; support = SUPPORT[v]
    b = core.bind(row)
    if epochs is not None:
        b["spec"]["epochs"] = epochs
    d = int(s.get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    try:
        log = {}; coh = load_cohort(b); g = core.grid_samples(coh.fs)
        rec["resolved_config"] = {"d": d, "grid_samples": g, "fs": coh.fs, "variant": v, "support": support, "pre_s": PRE_S if support == "aligned1000" else 0.0,
                                  "mask": "zero before the anchor's segment start"}
        if v == "local_aligned1000":
            orig = local_train.GridBatcher
            local_train.GridBatcher = batcher_for(support)
            try:
                enc, head, bt, _ = local_train.fit_continuous(b, coh, dev, os.path.join(out, "ckpt", row["experiment_id"]), log, d=d, grid=g)
            finally:
                local_train.GridBatcher = orig
            rec["resolved_config"].update({"epochs": b["spec"]["epochs"], "window_samples": [int(bt.W[0][0]), int(bt.W[0][1])], "n_tokens": int(enc.n_tokens)})
        else:
            enc, head, bt = fit_raw_ridge(b, coh, dev, log, d=d, grid=g, support=support)
            torch.save({"enc": enc.state_dict()}, os.path.join(out, "ckpt", row["experiment_id"] + "_best.pt"))
        rec.update(log)
        rec["eval"] = core.evaluate_grid(b, enc, head, bt, coh, log["objective_calibration"], g)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
