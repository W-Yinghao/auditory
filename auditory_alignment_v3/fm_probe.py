"""ALN3 B_LAYER_PROBE: fixed-backbone channel-preserving ridge probe per layer (package docs/05 §3 B1, §4).

Backbone: CBraMod / REVE pretrained_frozen; input = the B_DENSE foundation_context (segment + 0.6 s, zero-padded to whole
patches; fm_dense.DenseBatcher / DenseFM geometry). Layer (bound to the real architecture; all three reported, none chosen):
  patch_embedding  input of block 1 (patch embedding + position encoding)
  middle           output of block n/2 (CBraMod 6 of 12, REVE 11 of 22)
  last             backbone output (the tokens every B_DENSE readout reads)
Probe = the package ChannelPhaseLinearReadout functional form fitted in closed form ("a separate ridge implementation on the
explicit basis features"): per patch p the channel x feature token h_p (all channels retained, flattened C*D) is z-scored and
reduced by PCA (r = 256 components fitted on the tokens of 300 training segments: the reference starting point, recorded);
per query q, phi(q) = sum_p w_qp * basis(rel_qp) (x) [z_p, 1] with w = softmax(-0.5 (rel / 0.75 s)^2) over valid patches and
basis = TimeFeatures(4) of the relative time only (no audio, no file identity), plus an unpenalised intercept. Target = the
dense20ms_v1 fixed projection (d = 32) at the query. Fit queries: 16 grid-aligned queries per training-participant fit segment
(all fit segments, one pass); ridge alpha from a relative grid chosen on training participants' early-stopping segments by
mean per-dimension correlation, then refit on fit + early-stopping. Evaluation: the common dense-grid evaluation with the
probe output as the representation (unified reconstruction readout; native = the regression readout of CS_SINGLE).
"""
from __future__ import annotations

import time

import numpy as np
import torch
import torch.nn as nn

PCA_R, PCA_SEGMENTS, Q_FIT, ES_MAX, CHUNK = 256, 300, 16, 1000, 16
ALPHAS = np.logspace(-4, 4, 9)  # x mean diagonal of the fit Gram matrix; extended downward by 2 decades (at most 3 times)
# while the early-stopping optimum lies on the lower edge of the grid (training-side rule, recorded per unit)
BANDWIDTH_S = 0.75


class LayerTap:
    def __init__(self, bb, layer):
        self.bb, self.layer, self.h = bb, layer, None
        n = len(bb.blocks); self.mid = n // 2
        self.binding = {"patch_embedding": "input of block 1 (patch embedding + position)", "middle": f"output of block {self.mid} of {n}",
                        "last": "backbone output"}[layer]
        if layer == "last":
            return
        if bb.arch == "cbramod":
            if layer == "patch_embedding":
                bb.blocks[0].register_forward_pre_hook(lambda m, a: setattr(self, "h", a[0]))
            else:
                bb.blocks[self.mid - 1].register_forward_hook(lambda m, a, o: setattr(self, "h", o))
        else:
            tr = bb.net.transformer; orig = tr.forward

            def fwd(x, return_out_layers=False):
                outs = orig(x, return_out_layers=True)
                self.h = outs[0] if layer == "patch_embedding" else outs[self.mid]
                return outs if return_out_layers else outs[-1]
            tr.forward = fwd

    def tokens(self, out):  # backbone output [B, C, P, E] -> selected layer [B, C, P, E]
        if self.layer == "last":
            return out
        h = self.h
        if h.ndim == 3:  # REVE flattens tokens channel-major: b (c h) e
            h = h.reshape(out.shape[0], out.shape[1], out.shape[2], -1)
        assert h.shape[:3] == out.shape[:3], (h.shape, out.shape)
        return h


class RidgeProbe(nn.Module):
    def __init__(self, dfm, tap, d):
        super().__init__()
        from .aln3_reference.readouts import TimeFeatures
        self.dfm, self.tap, self.d = dfm, tap, d
        self.time = TimeFeatures(4)
        self.mu = self.sd = self.V = self.B = None

    @torch.no_grad()
    def flat_tokens(self, x):  # [n, C, ctx] -> [n, P, C*D]
        h = self.tap.tokens(self.dfm.tokens(x)).float(); n, C, P, D = h.shape
        return h.permute(0, 2, 1, 3).reshape(n, P, C * D)

    @torch.no_grad()
    def features(self, x, q):  # q [n, Q] seconds from the segment start -> [n, Q, F*(r+1) + 1]
        z = ((self.flat_tokens(x) - self.mu) / self.sd) @ self.V
        z1 = torch.cat([z, torch.ones_like(z[..., :1])], -1)
        rel = q[:, :, None] - self.dfm.patch_times[None, None, :]
        lg = (-0.5 * (rel / BANDWIDTH_S) ** 2).masked_fill(~self.dfm.valid[None, None, :], -torch.inf)
        phi = torch.einsum("nqp,nqpf,npr->nqfr", lg.softmax(-1), self.time(rel), z1).flatten(2)
        return torch.cat([phi, torch.ones_like(phi[..., :1])], -1)

    @torch.no_grad()
    def forward(self, x, q):
        return self.features(x, q) @ self.B


def fit_probe(b, coh, dev, layer, d=32, grid=3, log=None):
    from auditory_alignment.train import Objective
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.foundation_adapter import Backbone
    from .fm_dense import DenseBatcher, DenseFM
    spec = b["spec"]; t0 = time.time(); torch.manual_seed(b["seed"]); rng = np.random.default_rng(b["seed"])
    bb = Backbone(spec["architecture"], coh.meta["dataset"], "pretrained_frozen", coh.fs)
    bt = DenseBatcher(coh, spec, b, dev, grid)
    dfm = DenseFM(bb, "channel_phase_linear", d, coh.fs, bt.seg_len, bt.ctx_len).to(dev).eval()
    tap = LayerTap(bb, layer); probe = RidgeProbe(dfm, tap, d).to(dev)
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(b["seed"] + 5))).to(dev).eval()
    segs = bt.coh_segments
    e0_of = lambda idx: torch.tensor([segs[i]["e0"] for i in idx], device=dev)
    # PCA of the z-scored channel x feature tokens (valid patches of 300 training fit segments)
    pidx = rng.choice(bt.fit, size=min(PCA_SEGMENTS, len(bt.fit)), replace=False)
    chunks = []
    for k in range(0, len(pidx), CHUNK):
        ft = probe.flat_tokens(bt.context(e0_of(pidx[k:k + CHUNK])))
        chunks.append(ft[:, dfm.valid].reshape(-1, ft.shape[-1]))
    X = torch.cat(chunks); del chunks
    probe.mu, probe.sd = X.mean(0), X.std(0) + 1e-6
    _, S, Vh = torch.linalg.svd((X - probe.mu) / probe.sd, full_matrices=False)
    r = min(PCA_R, Vh.shape[0]); probe.V = Vh[:r].T.contiguous()
    evr = float((S[:r] ** 2).sum() / (S ** 2).sum()); del X
    # one pass over the training fit segments: Gram accumulation; early-stopping features kept for the alpha choice
    def rows(idx, rg):
        e0, t, s0, _ = bt.dense_rows(list(idx), rg, anchors=Q_FIT)
        phi = probe.features(bt.context(e0), t.float() / bt.fs)
        return phi.reshape(-1, phi.shape[-1]).double(), head(bt.audio(s0)).double()
    G = H = None; n_q = 0
    order = rng.permutation(bt.fit)
    for k in range(0, len(order), CHUNK):
        P, Y = rows(order[k:k + CHUNK], rng)
        G = P.T @ P if G is None else G + P.T @ P; H = P.T @ Y if H is None else H + P.T @ Y; n_q += len(P)
    es = list(rng.permutation(bt.es)[:ES_MAX]); Pe, Ye = [], []
    for k in range(0, len(es), CHUNK):
        P, Y = rows(es[k:k + CHUNK], np.random.default_rng(k)); Pe.append(P); Ye.append(Y)
    Pe, Ye = torch.cat(Pe), torch.cat(Ye)
    R = torch.eye(G.shape[0], dtype=G.dtype, device=dev); R[-1, -1] = 0; scale = float(G.diagonal().mean())
    curve, grid_ = [], list(ALPHAS)
    for ext in range(4):
        for a in grid_:
            if any(c["alpha_rel"] == float(a) for c in curve):
                continue
            Bm = torch.linalg.solve(G + a * scale * R, H); Pr = Pe @ Bm
            Pc, Yc = Pr - Pr.mean(0), Ye - Ye.mean(0)
            corr = float(((Pc * Yc).sum(0) / (torch.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12)).mean())
            curve.append({"alpha_rel": float(a), "es_mean_corr": corr})
        curve.sort(key=lambda c: c["alpha_rel"])
        a_best = max(curve, key=lambda c: c["es_mean_corr"])["alpha_rel"]
        if a_best != curve[0]["alpha_rel"] or ext == 3:
            break
        grid_ = [a_best / 10, a_best / 100]
    probe.B = torch.linalg.solve(G + Pe.T @ Pe + a_best * scale * R, H + Pe.T @ Ye).float()
    # objective calibration for the CS dependence diagnostic (training-side batch of probe outputs and targets)
    cidx = rng.choice(bt.fit, size=min(32, len(bt.fit)), replace=False)
    e0, t, s0, _ = bt.dense_rows(list(cidx), np.random.default_rng(b["seed"] + 98), anchors=8)
    obj = Objective({"objective": "CS_SINGLE", "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}, probe(bt.context(e0), t.float() / bt.fs).reshape(-1, d), head(bt.audio(s0)))
    if log is not None:
        log.update({"layer": layer, "layer_binding": tap.binding, "pca_components": r, "pca_segments": int(len(pidx)), "pca_explained_variance": evr,
                    "token_dim": int(probe.V.shape[0]), "feature_dim": int(G.shape[0]), "n_fit_segments": int(len(bt.fit)), "n_fit_queries": int(n_q),
                    "n_es_segments_alpha": int(len(es)), "alpha_curve": curve, "alpha_rel_chosen": a_best, "alpha_on_lower_edge": a_best == curve[0]["alpha_rel"], "queries_per_fit_segment": Q_FIT,
                    "bandwidth_s": BANDWIDTH_S, "time_frequencies": 4, "objective_calibration": obj.record(), "backbone_contract": bb.contract(),
                    "patch_times_s": dfm.patch_times.tolist(), "valid_patches": dfm.valid.tolist(), "fit_seconds": round(time.time() - t0, 1)})
    return probe, head, bt
