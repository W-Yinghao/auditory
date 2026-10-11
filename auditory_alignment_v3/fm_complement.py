"""ALN3 workpackage C: local pathway + pretrained complement (C_COMPLEMENT, C_CAPACITY_CONTROL; package docs/06).

Base: the completed same-fold A_LOCAL lag_local_tokens full-window unit (same dataset, subject fold, content fold, seed and
objective); its encoder and fixed audio head are loaded from its best checkpoint and kept frozen (first stage of docs/06).
Common prediction space: both branches live in the same fixed d = 32 target space (the base was trained against the fixed
training-side audio projection that is reused here unchanged), so the residual is added there:
  residual_* / residual_small_capacity:  u(t) = normalise(base(t) + R([h_local(t); c(t)]))     R = ZeroResidualPrediction,
      last layer zero-initialised -> at initialisation u(t) == base(t) exactly (checked by the engineering probe);
  concat_pretrained:  u(t) = normalise(W [base(t); c(t)]) with a fresh common head (no residual structure).
h_local(t) = the base's token sequence at t (flattened); c(t) = context features at t from
  FM variants: Backbone (CBraMod / REVE; pretrained or random; frozen | PEFT | full) -> DenseQueryReadout(C, D, 64) on the
               foundation_context input of fm_dense (segment + 0.6 s, whole patches);
  small_capacity_branch: ALN2 conv body over the same context EEG -> 0.1 s tokens -> DenseQueryReadout(1, 32, 64).
Training recipe for adapted FM branches = fm_dense (warm-up, top-down unfreezing, layer-wise decay, per-epoch validation);
learning rates as fm_dense.LR. Epochs: FM branch as fm_dense.EPOCHS; small branch 100.
"""
from __future__ import annotations

import math
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from auditory_alignment.train import Objective, _eff_rank, _save_resume, cs_diag
from auditory_alignment_v2.audio_targets import build_head, target_stats
from auditory_alignment_v2.foundation_adapter import Backbone
from auditory_alignment_v2.temporal import build_encoder, conv_body
from auditory_alignment_v2.train import N_SEL, ROWS
from . import fm_dense
from .aln3_reference.readouts import DenseQueryReadout, ZeroResidualPrediction

CTX_DIM = 64
VARIANT_FM = {"concat_pretrained": ("pretrained_frozen", True), "residual_pretrained_frozen": ("pretrained_frozen", True),
              "residual_pretrained_peft": ("pretrained_peft", True), "residual_pretrained_full": ("pretrained_full", True),
              "residual_random_frozen": ("random_frozen", False), "residual_random_trainable": ("random_full", False)}


class SmallContext(nn.Module):
    """small_capacity_branch: conv body over the context EEG, 0.1 s tokens [B, 1, P, 32]."""

    def __init__(self, n_ch, fs, ctx_len):
        super().__init__()
        self.body = conv_body(n_ch); self.pool = max(1, int(round(0.1 * fs)))
        P = ctx_len // self.pool
        self.register_buffer("patch_times", torch.tensor([(p + 0.5) * self.pool / fs for p in range(P)], dtype=torch.float32))
        self.register_buffer("valid", torch.ones(P, dtype=torch.bool))
        self.readout = DenseQueryReadout(1, 32, CTX_DIM)

    def forward(self, x, q):
        h = self.body(x)  # [B, 32, L]
        P = len(self.patch_times); h = h[:, :, :P * self.pool].reshape(h.shape[0], 32, P, self.pool).mean(-1)  # [B, 32, P]
        tok = h.permute(0, 2, 1)[:, None]  # [B, 1, P, 32]
        B = x.shape[0]
        return self.readout(tok, self.patch_times[None].expand(B, -1), q, self.valid[None].expand(B, -1))


class FMContext(nn.Module):
    def __init__(self, bb, fs, seg_len, ctx_len):
        super().__init__()
        self.dfm = fm_dense.DenseFM(bb, "dense_query", CTX_DIM, fs, seg_len, ctx_len)  # reuse geometry; readout output = context dim

    def forward(self, x, q):
        h = self.dfm.tokens(x); B = h.shape[0]
        return self.dfm.readout(h, self.dfm.patch_times[None].expand(B, -1), q, self.dfm.valid[None].expand(B, -1))

    @property
    def bb(self):
        return self.dfm.bb


class Complement(nn.Module):
    def __init__(self, base_enc, ctx, variant, d, local_dim):
        super().__init__()
        self.base, self.ctx, self.variant, self.d = base_enc, ctx, variant, d
        for p in self.base.parameters():
            p.requires_grad_(False)
        if variant == "concat_pretrained":
            self.common = nn.Linear(d + CTX_DIM, d)
        else:
            self.res = ZeroResidualPrediction(local_dim, CTX_DIM, d)

    def forward(self, patches, x_ctx, q):  # patches: base windows for the B*Q rows; x_ctx [B, C, ctx]; q [B, Q]
        B, Q = q.shape
        with torch.no_grad():
            tok = self.base.forward_tokens(patches).flatten(1)  # [B*Q, local_dim]
            base = self.base(patches)  # [B*Q, d] (normalised base prediction)
        c = self.ctx(x_ctx, q).reshape(B * Q, CTX_DIM)
        if self.variant == "concat_pretrained":
            return F.normalize(self.common(torch.cat([base, c], 1)), dim=1)
        return F.normalize(self.res(base, tok, c), dim=1)


def fit_complement(row, coh, dev, ckpt_prefix, log, base_ckpt, variant, fm_arch, d=32, grid=3, epochs=None, n_seg=32):
    from .local_train import GridBatcher  # noqa: F401 (DenseBatcher subclasses it)
    spec = row["spec"]; obj_name = spec["objective"]
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bspec = dict(spec); bspec["architecture"] = "lag_local_tokens"; bspec["window"] = "full"
    bt = fm_dense.DenseBatcher(coh, bspec, row, dev, grid)
    base = build_encoder("lag_local_tokens", coh.n_ch, d, bt.W, coh.fs).to(dev)
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(row["seed"] + 5))).to(dev)
    sd = torch.load(base_ckpt, map_location=dev); base.load_state_dict(sd["enc"], strict=True); head.load_state_dict(sd["head"], strict=True)
    base.eval(); head.eval()
    if variant == "residual_small_capacity":
        ctx = SmallContext(coh.n_ch, coh.fs, bt.ctx_len).to(dev); ad = None; groups_bb = []; allowed = set()
    else:
        ad, pretrained = VARIANT_FM[variant]
        bb = Backbone(fm_arch, coh.meta["dataset"], "random_full" if ad == "random_frozen" else ad, coh.fs)
        if ad == "random_frozen":
            for p in bb.parameters():
                p.requires_grad_(False)
        allowed = {id(p) for p in bb.parameters() if p.requires_grad}
        ctx = FMContext(bb, coh.fs, bt.seg_len, bt.ctx_len).to(dev); groups_bb = fm_dense.block_groups(bb)
    local_dim = base.n_tokens * 32
    model = Complement(base, ctx, variant, d, local_dim).to(dev)
    lr_b, lr_h = fm_dense.LR.get(ad, (0.0, 1e-3)) if ad not in (None, "random_frozen") else (0.0, 1e-3)
    E = epochs or (fm_dense.EPOCHS[fm_arch] if ad is not None else 100)
    nb = sum(1 for g in groups_bb if g[0] == "block"); pg = []
    for kind, i, ps in groups_bb:
        ps = [p for p in ps if id(p) in allowed]
        if ps:
            depth = (nb - 1 - i) if kind == "block" else nb
            pg.append({"params": ps, "lr": lr_b * fm_dense.LLRD ** depth})
    head_params = [p for n, p in model.named_parameters() if not n.startswith("base.") and not n.startswith("ctx.dfm.bb.")]
    pg.append({"params": head_params, "lr": lr_h})
    opt = torch.optim.AdamW(pg, weight_decay=1e-4)
    Q = 8; n_seg = max(2, ROWS.get(obj_name, 256) // Q)
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=E * steps_per_epoch)
    obj_job = {"objective": obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}

    def set_trainable(ep):
        if not groups_bb:
            return 0
        n_open = 0 if ep < fm_dense.WARMUP else (len(groups_bb) if (ad or "").endswith("peft") else 1 + (ep - fm_dense.WARMUP) // fm_dense.UNFREEZE_EVERY)
        for gi, (kind, i, ps) in enumerate(groups_bb):
            for p in ps:
                p.requires_grad_(id(p) in allowed and gi < n_open)
        return n_open

    def fwd(rows_):
        e0, t, s0, keys = rows_
        patches = bt.patches((e0[:, None] + t).reshape(-1))
        return model(patches, bt.context(e0), t.float() / bt.fs), head(bt.audio(s0)), keys

    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), n_seg))
    with torch.no_grad():
        r0 = bt.dense_rows(calib, np.random.default_rng(row["seed"] + 98), anchors=Q); u0, v0, _ = fwd(r0)
        obj = Objective(obj_job, u0, v0)
        b0 = base(bt.patches((r0[0][:, None] + r0[1]).reshape(-1)))
        log["init_max_abs_diff_vs_base"] = float((u0 - b0).abs().max()) if variant != "concat_pretrained" else None
    es_rng = np.random.default_rng(12345); es_sel = []
    while len(es_sel) < N_SEL:
        got = [b for b, _ in zip(bt.epoch_batches(es_rng, n_seg, bt.es), range(N_SEL - len(es_sel)))]
        if not got:
            break
        es_sel += got
    es_sets = [(bt.dense_rows(b, np.random.default_rng(k), anchors=Q), bt.dense_rows(b, np.random.default_rng(k), anchors=Q, roll=True)) for k, b in enumerate(es_sel)]
    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        model.load_state_dict(r["model"]); opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    for ep in range(ep0, E):
        n_open = set_trainable(ep)
        params = [p for g in pg for p in g["params"] if p.requires_grad]
        model.train(); model.base.eval(); tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            u, v, keys = fwd(bt.dense_rows(batch, rng, anchors=Q))
            loss, _ = obj(u, v, keys=keys)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        model.eval()
        with torch.no_grad():
            el, elr, dm, dx = [], [], [], []
            for (a, b) in es_sets:
                u, v, keys = fwd(a); _, vr, kr = fwd(b)
                l1, _ = obj(u, v, keys=keys); l2, _ = obj(u, vr, keys=kr)
                el.append(float(l1)); elr.append(float(l2))
                dm.append(cs_diag(u, v, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v)); dx.append(cs_diag(u, vr, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
        es_loss, es_mm = float(np.mean(el)), float(np.mean(elr)); selsc = es_loss - es_mm
        curve.append({"epoch": ep + 1, "step": step, "open_groups": n_open, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss,
                      "es_loss_mismatched": es_mm, "selection_score": selsc, "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin,
                      "seconds": round(time.time() - t0, 1), "es_cs_true_nats": float(np.mean([x["cs_qmi_nats"] for x in dm])),
                      "es_cs_mismatched_nats": float(np.mean([x["cs_qmi_nats"] for x in dx])), "u_eff_rank": _eff_rank(u)})
        if selsc < best[0]:
            best = (selsc, ep + 1); torch.save({"model": model.state_dict()}, ckpt_prefix + "_best.pt")
        _save_resume(rpath, model=model.state_dict(), opt=opt.state_dict(), sched=sched.state_dict(), rng=rng.bit_generator.state,
                     torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0], "epochs_completed": E,
                "optimizer_steps": step, "n_fit_segments": len(bt.fit), "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1),
                "variant": variant, "context_branch": fm_arch if ad is not None else "small_capacity_branch", "context_adaptation": ad,
                "trainable_params": int(sum(p.numel() for g in pg for p in g["params"])), "lr_backbone": lr_b, "lr_head": lr_h, "base_checkpoint": os.path.basename(base_ckpt),
                "backbone_contract": ctx.bb.contract() if ad is not None else None})
    model.load_state_dict(torch.load(ckpt_prefix + "_best.pt", map_location=dev)["model"]); model.eval()
    return model, head, bt


class CompReps:
    """ev1.Reps interface: per segment one context forward; base windows at every grid query."""

    def __init__(self, model, aud, bt, stride, chunk=8):
        self.model, self.aud, self.bt, self.chunk = model, aud, bt, chunk
        self.offs = np.arange(0, bt.seg_len, stride)

    @torch.no_grad()
    def u(self, e0s):
        e0s = np.asarray(e0s); out = []; dev = self.bt.dev
        q = torch.tensor(self.offs, device=dev)
        for k in range(0, len(e0s), self.chunk):
            e = torch.tensor(e0s[k:k + self.chunk], device=dev)
            patches = self.bt.patches((e[:, None] + q[None]).reshape(-1))
            u = self.model(patches, self.bt.context(e), (q.float() / self.bt.fs)[None].expand(len(e), -1))
            out.append(u.reshape(len(e), len(self.offs), -1).float().cpu().numpy())
        return np.concatenate(out)

    va = fm_dense.DenseReps.va


def evaluate_complement(b, model, head, bt, coh, calib, grid):
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v2 import evaluate as ev2
    orig = ev1.Reps
    ev1.Reps = lambda enc, aud, bt_, **kw: CompReps(model, aud, bt_, grid)
    try:
        return ev2.evaluate_continuous(b, model, head, bt, coh, calib, None)
    finally:
        ev1.Reps = orig
