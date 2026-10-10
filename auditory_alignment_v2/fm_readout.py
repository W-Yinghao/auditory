"""ALN2 repaired foundation-model readouts (2026-10-07; package amendment A1, implementation receipt §12).

Amendment A1: preserve channel identity and spatial contrasts until a learned task-specific operation combines them;
preserve the temporal-token axis until the declared temporal aggregation stage; an unweighted channel mean is an ablation
(the legacy_chmean_v1 variant), not the default foundation-model interface.

SpatialPatchHead (main trainable readout). Backbone tokens H [B, C, T, D] (C channels in the order of the dataset's layout,
foundation_adapter.CHANNELS[dataset]; T patches) -> shared feature projection P: D -> e applied to every channel token ->
K learned signed spatial filters W [K, C] (Z_{b,k,t} = sum_c W_{k,c} P H_{b,c,t}; unconstrained sign, so channel
contrasts are representable) -> per patch, the K x e components are kept, LayerNorm, linear map to d, L2 normalisation:
[B, T, d]. The patch axis is never pooled here: each patch is one alignment row in training, and the evaluation's declared
temporal aggregation (mean patch score per 5 s segment) is unchanged. W belongs to one channel layout: multi-cohort donor
training uses one head per cohort on the shared backbone, and every downstream unit trains a fresh head for its layout.

ChannelProbe (fixed reference readout with no task training of its own; the channels-preserved linear probe of the
diagnostic). Every channel's token of the unit's own backbone is concatenated per patch ([C * D]), reduced by PCA
(PROBE_K components, fitted on training participants' fit + es segments), and read out by the previous-round unified ridge
readout (continuous; metrics stored under 'probe/...') or by a logistic head fitted on the training children's
early-stopping blocks (private; 'probe_auc', 'probe_gain_vs_base_bits').
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

K_SPATIAL, E_PROJ, PROBE_K, PROBE_FIT_SEGMENTS = 8, 32, 256, 300
HEAD_VERSION = "spatial_signed_k8_e32_v1"


class SpatialPatchHead(nn.Module):
    def __init__(self, E, C, d=16, K=K_SPATIAL, e=E_PROJ):
        super().__init__()
        self.C = C
        self.proj = nn.Linear(E, e)
        self.W = nn.Parameter(torch.randn(K, C) / math.sqrt(C))
        self.ln = nn.LayerNorm(K * e)
        self.lin = nn.Linear(K * e, d)

    def forward(self, tok):  # [B, C, T, E] -> [B, T, d]
        assert tok.dim() == 4 and tok.shape[1] == self.C, (tuple(tok.shape), self.C)
        z = torch.einsum("kc,bcte->btke", self.W, self.proj(tok))
        return F.normalize(self.lin(self.ln(z.flatten(2))), dim=-1)


def make_head(backbone, d=16):
    return SpatialPatchHead(backbone.E, len(backbone.channel_names), d)


# ------------------------------------------------------------------------------------------------ channels-preserved probe
class ProbeReps:
    """eval_fm.SegmentReps interface: u() returns PCA-reduced all-channel tokens [n, T, k]; va() as for the trained head."""

    def __init__(self, bb, head, bt, fit_e0s, k=PROBE_K, chunk=32):
        self.bb, self.head, self.bt, self.chunk = bb, head, bt, chunk
        X = self._tok(fit_e0s)
        X2 = X.reshape(-1, X.shape[-1])
        self.mu = X2.mean(0)
        _, S, Vt = torch.linalg.svd(X2 - self.mu, full_matrices=False)
        k = min(k, Vt.shape[0])
        self.W = Vt[:k].T.contiguous()
        self.info = {"k": int(k), "explained_variance": float((S[:k] ** 2).sum() / (S ** 2).sum()), "n_fit_rows": int(X2.shape[0]),
                     "token_dim": int(X2.shape[1])}

    @torch.no_grad()
    def _tok(self, e0s):
        e0s = np.asarray(e0s); out = []
        for a in range(0, len(e0s), self.chunk):
            tok = self.bb(self.bt.segments(torch.tensor(e0s[a:a + self.chunk], device=self.bt.dev)))  # [n, C, T, E]
            out.append(tok.permute(0, 2, 1, 3).flatten(2).float())
        return torch.cat(out)

    @torch.no_grad()
    def u(self, e0s):
        e0s = np.asarray(e0s); out = []
        for a in range(0, len(e0s), self.chunk):
            out.append(((self._tok(e0s[a:a + self.chunk]) - self.mu) @ self.W).cpu().numpy())
        return np.concatenate(out)

    @torch.no_grad()
    def va(self, s0s):
        s0s = np.asarray(s0s); v, a = [], []
        for k in range(0, len(s0s), self.chunk):
            A = self.bt.audio_patches(torch.tensor(s0s[k:k + self.chunk], device=self.bt.dev))
            a.append(A.cpu().numpy()); v.append(self.head(A).cpu().numpy())
        return np.concatenate(v), np.concatenate(a)


@torch.no_grad()
def channel_probe_segments(row, enc, head, bt, coh, calib):
    """Unified-readout evaluation of the channels-preserved probe; keys renamed unified/* -> probe/*."""
    from .eval_fm import evaluate_segments
    enc.eval()
    segs = coh.segments
    tr = [s for s in segs if s["p"] in bt.train_p and s["role"] in ("fit", "es") and s["kind"] == bt.kind]
    r = np.random.default_rng(row["seed"] + 2024)
    pick = [tr[i]["e0"] for i in r.choice(len(tr), size=min(PROBE_FIT_SEGMENTS, len(tr)), replace=False)]
    reps = ProbeReps(enc.bb, head, bt, pick)
    out = evaluate_segments(row, enc, head, bt, coh, calib, reps=reps, readouts=("unified",), dependence=False)
    ren = lambda d: {k.replace("unified", "probe"): v for k, v in d.items()}
    res = {"per_participant": {p: ren(v) for p, v in out["per_participant"].items()},
           "readout": {"alpha_probe": out["readout"]["alpha_unified"], "tau_probe": out["readout"]["tau"].get("unified"), "pca": reps.info}}
    if "attention_2afc" in out:
        res["attention_2afc"] = {p: ren(v) for p, v in out["attention_2afc"].items()}
    return res


@torch.no_grad()
def channel_probe_private(row, enc, bt, k=PROBE_K):
    """Channels-preserved probe for the private full-epoch task: all-channel tokens of the single patch, PCA on the training
    children's early-stopping trials, logistic head on the same trials (the unified head's fitting rule)."""
    from sklearn.linear_model import LogisticRegression
    from auditory_alignment.evaluate import _auc
    enc.eval()
    kids = bt.kids; tr = bt.train; te = [i for i, kk in enumerate(kids) if kk["fold"] == row["subject_fold"]]

    def tok(i, idx):
        out = []
        for a in range(0, len(idx), 512):
            t = torch.tensor(idx[a:a + 512], device=bt.dev)
            out.append(enc.bb(bt.patches(i, t)[0]).permute(0, 2, 1, 3).flatten(2)[:, 0].float())  # [n, C*E] (one patch)
        return torch.cat(out)
    Xtr = torch.cat([tok(i, np.flatnonzero(kids[i]["es_mask"])) for i in tr]); ytr = np.concatenate([kids[i]["y"][kids[i]["es_mask"]] for i in tr])
    mu = Xtr.mean(0); r = np.random.default_rng(row["seed"] + 2024)
    sub = torch.tensor(r.choice(len(Xtr), size=min(4000, len(Xtr)), replace=False), device=Xtr.device)
    _, S, Vt = torch.linalg.svd(Xtr[sub] - mu, full_matrices=False); W = Vt[:k].T
    Ztr = ((Xtr - mu) @ W).cpu().numpy()
    m, s = Ztr.mean(0), Ztr.std(0) + 1e-6
    clf = LogisticRegression(C=1.0, max_iter=3000).fit((Ztr - m) / s, ytr)
    base = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
    ll = lambda q, y: np.where(y == 1, np.log2(np.clip(q, 1e-12, 1)), np.log2(np.clip(1 - q, 1e-12, 1)))
    per = {}
    for i in te:
        kk = kids[i]; y = kk["y"]
        Z = ((tok(i, np.arange(len(y))) - mu) @ W).cpu().numpy()
        p = np.clip(clf.predict_proba((Z - m) / s)[:, 1], 1e-6, 1 - 1e-6)
        g = ll(p, y) - ll(np.full(len(y), base), y)
        per[kk["id"]] = {"probe_auc": _auc(p, y), "probe_gain_vs_base_bits": float(g.mean()), "probe_brier": float(((p - y) ** 2).mean())}
    return {"per_participant": per, "pca": {"k": int(W.shape[1]), "explained_variance": float((S[:k] ** 2).sum() / (S ** 2).sum()),
                                            "n_fit_trials": int(len(Xtr))}}
