"""ALN2 D_GX: the GX task model under the new common protocol (same children, outer folds, early-stopping blocks,
inputs and evaluation as every D unit); 'same_new_protocol_not_claim_exact_old_result'.

GX configuration reused (configs/auditory_gx_v1.yaml, auditory_gx.models.EEGNet): EEGNet-8,2 (F1 16, D 2, F2 32, k1 25,
k2 15, dropout 0.25), class-weighted CE, AdamW lr 1e-3 / wd 0.01, OneCycle over 40 epochs, patience 6 on the balanced
validation CE (here: the training children's early-stopping blocks), augmentation noise 0.05 / channel dropout 0.10 /
shift 3 samples / amplitude jitter 0.2. Necessary adaptations (recorded): restricted windows (early / late = 20 samples)
are too short for the original 4 x 8 pooling, so pool2 is min(8, T // 4); the joint window concatenates early and late
in time. Native head: GX logits recalibrated (logistic on the logit difference) on the training children's
early-stopping blocks, because class-weighted training does not give natural-distribution probabilities.
"""
from __future__ import annotations

import math
import os
import time

import numpy as np
import torch
import torch.nn.functional as F

from auditory_gx.models import EEGNet
from .temporal import window_ranges
from .train import PrivateBatcher


class GXNet(EEGNet):
    def __init__(self, n_channels, n_times):
        super().__init__(n_channels, n_times, 2, F1=16, D=2, F2=32, k1=25, k2=15, dropout=0.25)
        t1 = n_times // 4; p2 = max(1, min(8, t1))
        self.pool2 = torch.nn.AvgPool2d((1, p2))
        self.feature_dim = 32 * (t1 // p2)
        self.head = torch.nn.Linear(self.feature_dim, 2)
        self.pool2_kernel = p2


class GXWrap(torch.nn.Module):
    """list of window crops -> concatenated in time -> EEGNet embedding (frozen-representation readout) / logits."""

    def __init__(self, net):
        super().__init__(); self.net = net

    def forward(self, patches):
        return self.net.embed(torch.cat(patches, -1))

    def logits(self, patches):
        return self.net(torch.cat(patches, -1))


def _augment(x, rng_t):
    B, C, T = x.shape
    x = x * (1 + 0.2 * (torch.rand(B, 1, 1, device=x.device, generator=rng_t) * 2 - 1))
    x = x * (torch.rand(B, C, 1, device=x.device, generator=rng_t) > 0.10).float()
    s = int(torch.randint(-3, 4, (1,), generator=rng_t, device=x.device))
    x = torch.roll(x, s, dims=-1)
    return x + 0.05 * torch.randn(x.shape, device=x.device, generator=rng_t)


def fit_gx(row, kids, dev, ckpt_prefix, log, max_epochs=40, patience=6):
    spec = dict(row["spec"]); spec["architecture"] = "density_tokens"  # half-open window rule of the new protocol
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    rng_t = torch.Generator(device=dev); rng_t.manual_seed(row["seed"])
    bt = PrivateBatcher(kids, spec, row, dev)
    T = sum(b - a for a, b in bt.W)
    net = GXNet(20, T).to(dev); enc = GXWrap(net)
    tr_idx = np.concatenate([bt.fit_idx[i] for i in bt.train]); es_idx = np.concatenate([bt.es_idx[i] for i in bt.train])
    ytr = bt.ytrue[torch.tensor(tr_idx, device=dev)]
    counts = torch.bincount(ytr, minlength=2).float(); w = counts.sum() / (2 * counts.clamp(min=1))
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=0.01)
    bs = 256; steps = max(1, len(tr_idx) // bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=max_epochs * steps)
    def crops(g):
        x = bt.Xall[torch.as_tensor(g, device=dev)].float()
        return [x[:, :, a:b] for a, b in bt.W]
    yes = bt.ytrue[torch.tensor(es_idx, device=dev)].cpu().numpy()
    best, bad, curve, t0 = (math.inf, -1), 0, [], time.time()
    for ep in range(max_epochs):
        net.train(); perm = rng.permutation(len(tr_idx)); tl = []
        for k in range(steps):
            g = tr_idx[perm[k * bs:(k + 1) * bs]]
            x = _augment(torch.cat(crops(g), -1), rng_t)
            loss = F.cross_entropy(net(x), bt.ytrue[torch.as_tensor(g, device=dev)], weight=w)
            opt.zero_grad(); loss.backward(); opt.step(); sched.step(); tl.append(float(loss))
        net.eval()
        with torch.no_grad():
            lg = torch.cat([enc.logits(crops(es_idx[k:k + 4096])) for k in range(0, len(es_idx), 4096)]).float()
            lp = F.log_softmax(lg, 1).cpu().numpy()
        val = float(np.mean([-lp[yes == c, c].mean() / math.log(2) for c in (0, 1)]))  # balanced CE, bits
        curve.append({"epoch": ep + 1, "train_loss": float(np.mean(tl)), "es_balanced_ce_bits": val, "seconds": round(time.time() - t0, 1)})
        if val < best[0] - 1e-5:
            best, bad = (val, ep + 1), 0; torch.save({"net": net.state_dict()}, ckpt_prefix + "_best.pt")
        else:
            bad += 1
            if bad >= patience:
                break
    net.load_state_dict(torch.load(ckpt_prefix + "_best.pt", map_location=dev)["net"]); net.eval()
    with torch.no_grad():  # sigma_u of the frozen embedding for the test-side kernel dependence
        e = enc(crops(es_idx[:256])).double(); d = torch.cdist(e, e)
        sig = float(d[~torch.eye(len(e), dtype=torch.bool, device=d.device)].median())
    log.update({"curve": curve, "best_epoch": best[1], "best_es_balanced_ce_bits": best[0], "epochs_run": len(curve),
                "selection_rule": "GX: min balanced CE on the training children's early-stopping blocks, patience 6",
                "objective_calibration": {"sigma_u": sig, "sigma_v": None}, "gx_input_samples": int(T), "pool2_kernel": net.pool2_kernel,
                "windows_samples_from_epoch_start": [[a + bt.lo, b + bt.lo] for a, b in bt.W], "train_seconds": round(time.time() - t0, 1)})
    return enc, bt


@torch.no_grad()
def native_gx(enc, bt, row, out):
    from auditory_alignment import evaluate as ev1
    kids = bt.kids; tr = bt.train; te = [i for i, k in enumerate(kids) if k["fold"] == row["subject_fold"]]
    def z_of(i):
        x = bt.Xall[torch.as_tensor(bt.off[i], device=bt.dev) + torch.arange(len(kids[i]["y"]), device=bt.dev)].float()
        lg = enc.logits([x[:, :, a:b] for a, b in bt.W]).float().cpu().numpy(); return lg[:, 1] - lg[:, 0]
    zr = np.concatenate([z_of(i)[kids[i]["es_mask"]] for i in tr]); yr = np.concatenate([kids[i]["y"][kids[i]["es_mask"]] for i in tr])
    from sklearn.linear_model import LogisticRegression
    cal = LogisticRegression(C=1e6, max_iter=1000).fit(zr[:, None], yr)
    base = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
    ll = lambda q, y: np.where(y == 1, np.log2(np.clip(q, 1e-12, 1)), np.log2(np.clip(1 - q, 1e-12, 1)))
    for i in te:
        k = kids[i]; y = k["y"]; p = np.clip(cal.predict_proba(z_of(i)[:, None])[:, 1], 1e-6, 1 - 1e-6)
        hg = ll(p, y) - ll(np.full(len(y), base), y); hh = len(y) // 2
        out["per_participant"][k["id"]].update({"native_auc": ev1._auc(p, y), "native_brier": float(((p - y) ** 2).mean()),
                                                "native_gain_vs_base_bits": float(hg.mean()), "native_gain_half0": float(hg[:hh].mean()),
                                                "native_gain_half1": float(hg[hh:].mean())})
    out["native_head"] = {"kind": "GX logits recalibrated on training children's early-stopping blocks", "slope": float(cal.coef_[0, 0]), "intercept": float(cal.intercept_[0])}
    return out
