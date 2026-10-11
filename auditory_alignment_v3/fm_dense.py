"""ALN3 workpackage B: foundation-model dense readouts (B_DENSE) on the dense20ms_v1 target contract.

Model: Backbone (CBraMod / REVE, foundation_adapter; adaptation random_full | pretrained_frozen | _peft | _partial | _full)
-> channel tokens H [B, C, P, D] -> readout (package reference, vendored byte-identically):
  dense_query          DenseQueryReadout(C, D, d, hidden 128, heads 4, 8 signed spatial filters, projection 32)
  channel_phase_linear ChannelPhaseLinearReadout(C, D, d) (all channels kept; linear in tokens for fixed query times)
-> L2-normalised prediction per query, in the same fixed d = 32 target space as the local models (A_LOCAL): the audio
target at query t is the ALN2 8-frame window from t, standardised on the training side and projected by the fixed
semi-orthogonal cohort map. Queries carry only relative time (seconds from the segment start), never audio or identity.
Information stratum foundation_context: the backbone reads the EEG from the segment start to 0.6 s after the segment end
(the local models' maximal lag access), zero-padded to whole backbone patches; patches starting at or after that point are
masked. Query grid = round(20 ms x fs) samples, as A_LOCAL. Evaluation: ALN2 candidate pools, readouts and risks on that
grid (ev1.evaluate_continuous with dense representations).
Training recipe (item-3 addendum 01 / ALN3 B): head warm-up (backbone frozen) for WARMUP epochs; then progressive
unfreezing top-down (one more block group every UNFREEZE_EVERY epochs) up to what the adaptation allows (PEFT: LoRA
parameters at once; frozen: never); layer-wise learning-rate decay 0.75; validation on the training participants'
early-stopping content every epoch; checkpoint = min (early-stopping own loss - legal within-batch mismatch). Learning rates
fixed a priori (see LR below); recipe='aln2_onestep' reproduces the ALN2 one-step recipe as the controlled comparison.
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
from auditory_alignment_v2.foundation_adapter import Backbone, FS_FM
from auditory_alignment_v2.train import N_SEL, ROWS
from .aln3_reference.readouts import ChannelPhaseLinearReadout, DenseQueryReadout
from .local_train import GridBatcher

CTX_AFTER_S = 0.6
WARMUP, UNFREEZE_EVERY, LLRD = 5, 5, 0.75
LR = {"random_full": (3e-4, 1e-3), "pretrained_frozen": (0.0, 1e-3), "pretrained_peft": (1e-4, 1e-3),
      "pretrained_partial": (1e-5, 1e-3), "pretrained_full": (1e-5, 1e-3)}
EPOCHS = {"cbramod": 100, "reve": 50}


class DenseFM(nn.Module):
    def __init__(self, bb, readout_kind, d, fs_native, seg_len, ctx_len):
        super().__init__()
        self.bb, self.kind, self.fs, self.d = bb, readout_kind, fs_native, d
        C, D = len(bb.channel_names), bb.E
        self.readout = DenseQueryReadout(C, D, d) if readout_kind == "dense_query" else ChannelPhaseLinearReadout(C, D, d)
        n200 = int(math.ceil(ctx_len * FS_FM / fs_native / 200.0) * 200) if bb.arch == "cbramod" else int(round(ctx_len * FS_FM / fs_native))
        self.pad_native = int(round(n200 * fs_native / FS_FM)) - ctx_len if bb.arch == "cbramod" else 0
        starts = bb.patch_starts(n200 if bb.arch == "cbramod" else int(round(ctx_len * FS_FM / fs_native)))
        self.register_buffer("patch_times", torch.tensor([a + 0.5 for a in starts], dtype=torch.float32))
        self.register_buffer("valid", torch.tensor([a < ctx_len / fs_native for a in starts]))

    def tokens(self, x):  # x [B, C, ctx_len] native -> [B, C, P, D]
        if self.pad_native > 0:
            x = F.pad(x, (0, self.pad_native))
        h = self.bb(x)
        assert h.shape[2] == len(self.patch_times), (h.shape, len(self.patch_times))
        return h

    def forward(self, x, q_times):  # q_times [B, Q] seconds -> [B, Q, d]
        h = self.tokens(x); B = h.shape[0]
        pt = self.patch_times[None].expand(B, -1); vp = self.valid[None].expand(B, -1)
        return F.normalize(self.readout(h, pt, q_times, vp), dim=-1)


class DenseBatcher(GridBatcher):
    def __init__(self, coh, spec, row, dev, grid):
        super().__init__(coh, spec, row, dev, grid)
        self.ctx_len = self.seg_len + int(round(CTX_AFTER_S * self.fs))

    def context(self, e0):  # [n] segment starts -> [n, C, ctx_len]
        return self.E[:, (e0[:, None] + torch.arange(self.ctx_len, device=self.dev)[None])].permute(1, 0, 2).float()

    def dense_rows(self, batch, rng, anchors=8, pairing="train", roll=False):
        """rows of GridBatcher.rows grouped per segment: (e0 per segment [n], t per segment [n, Q], audio starts [n*Q], keys)."""
        r = self.rows(batch, rng, anchors=anchors, pairing=pairing, roll=roll)
        e0_seg = torch.tensor([self.coh_segments[i]["e0"] for i in batch], device=self.dev)
        t = (r[0].reshape(len(batch), anchors) - e0_seg[:, None])
        return e0_seg, t, r[1], r[2]


def block_groups(bb):
    """trainable-eventually parameter groups, top block first; non-block parameters last."""
    blocks = list(bb.blocks)[::-1]
    ids = set(); groups = []
    for i, blk in enumerate(blocks):
        ps = [p for p in blk.parameters()]; ids |= {id(p) for p in ps}; groups.append(("block", len(blocks) - 1 - i, ps))
    rest = [p for p in bb.parameters() if id(p) not in ids]
    groups.append(("other", -1, rest))
    return groups


def fit_dense(row, coh, dev, ckpt_prefix, log, readout_kind, d=32, grid=3, epochs=None, recipe="aln3", lr=None, n_seg=32):
    spec = row["spec"]; arch, ad, obj_name = spec["architecture"], spec["adaptation"], spec["objective"]
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bb = Backbone(arch, coh.meta["dataset"], ad, coh.fs)
    allowed = {id(p) for p in bb.parameters() if p.requires_grad}  # what the adaptation permits (Backbone._apply_adaptation)
    bt = DenseBatcher(coh, spec, row, dev, grid)
    model = DenseFM(bb, readout_kind, d, coh.fs, bt.seg_len, bt.ctx_len).to(dev)
    stats = target_stats(bt, np.random.default_rng(row["seed"] + 5))
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)
    lr_b, lr_h = lr or LR[ad]
    E = epochs or EPOCHS[arch]
    groups_bb = block_groups(bb); nb = sum(1 for g in groups_bb if g[0] == "block")
    pg = []
    for kind, i, ps in groups_bb:
        ps = [p for p in ps if id(p) in allowed]
        if ps:
            depth = (nb - 1 - i) if kind == "block" else nb
            pg.append({"params": ps, "lr": lr_b * (LLRD ** depth if recipe == "aln3" else 1.0), "name": f"{kind}{i}"})
    pg.append({"params": list(model.readout.parameters()), "lr": lr_h, "name": "readout"})
    opt = torch.optim.AdamW(pg, weight_decay=1e-4)
    rows_ = ROWS.get(obj_name, 256); Q = 8; n_seg = max(2, rows_ // Q)
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=E * steps_per_epoch)
    obj_job = {"objective": obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}

    def set_trainable(ep):
        """recipe aln3: warm-up then top-down unfreezing; aln2_onestep: everything allowed from the start."""
        if recipe != "aln3":
            n_open = len(groups_bb)
        elif ep < WARMUP:
            n_open = 0
        elif ad.endswith("peft"):
            n_open = len(groups_bb)
        else:
            n_open = 1 + (ep - WARMUP) // UNFREEZE_EVERY
        for gi, (kind, i, ps) in enumerate(groups_bb):
            for p in ps:
                p.requires_grad_(id(p) in allowed and gi < n_open)
        return n_open

    def loss_of(e0, t, s0, keys, enc_out=None):
        U = model(bt.context(e0), t.float() / bt.fs) if enc_out is None else enc_out
        u = U.reshape(-1, d); v = head(bt.audio(s0))
        la, _ = obj(u, v, keys=keys)
        return la, u, v, U

    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), n_seg))
    with torch.no_grad():
        e0, t, s0, keys = bt.dense_rows(calib, np.random.default_rng(row["seed"] + 98), anchors=Q)
        obj = Objective(obj_job, model(bt.context(e0), t.float() / bt.fs).reshape(-1, d), head(bt.audio(s0)))
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
    ve = 1 if recipe == "aln3" else max(1, E // 20)
    for ep in range(ep0, E):
        n_open = set_trainable(ep)
        params = [p for g in pg for p in g["params"] if p.requires_grad]
        model.train(); tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            e0, t, s0, keys = bt.dense_rows(batch, rng, anchors=Q)
            loss, _, _, _ = loss_of(e0, t, s0, keys)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if (ep + 1) % ve == 0 or ep == E - 1:
            model.eval()
            with torch.no_grad():
                el, elr, dm, dx = [], [], [], []
                for (a, b) in es_sets:
                    l1, u, v, U = loss_of(*a); l2, _, vr, _ = loss_of(b[0], b[1], b[2], b[3], enc_out=U)
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
                "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit), "n_es_segments": len(bt.es),
                "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1), "backbone_contract": bb.contract(),
                "readout": readout_kind, "readout_params": int(sum(p.numel() for p in model.readout.parameters())), "recipe": recipe,
                "lr_backbone": lr_b, "lr_head": lr_h, "llrd": LLRD if recipe == "aln3" else None, "warmup_epochs": WARMUP if recipe == "aln3" else 0,
                "unfreeze_every": UNFREEZE_EVERY if recipe == "aln3" else None, "val_every": ve, "queries_per_segment": Q,
                "context_after_s": CTX_AFTER_S, "pad_native": model.pad_native, "patch_times_s": model.patch_times.tolist(),
                "valid_patches": model.valid.tolist(), "param_group_lrs": [g["lr"] for g in pg]})
    model.load_state_dict(torch.load(ckpt_prefix + "_best.pt", map_location=dev)["model"]); model.eval()
    return model, head, bt


class DenseReps:
    """ev1.Reps interface for the dense FM: one forward per segment, queries on the evaluation grid."""

    def __init__(self, model, aud, bt, stride, chunk=16):
        self.model, self.aud, self.bt, self.chunk = model, aud, bt, chunk
        self.offs = np.arange(0, bt.seg_len, stride)

    @torch.no_grad()
    def u(self, e0s):
        e0s = np.asarray(e0s); out = []
        q = torch.tensor(self.offs, device=self.bt.dev).float() / self.bt.fs
        for k in range(0, len(e0s), self.chunk):
            e = torch.tensor(e0s[k:k + self.chunk], device=self.bt.dev)
            out.append(self.model(self.bt.context(e), q[None].expand(len(e), -1)).float().cpu().numpy())
        return np.concatenate(out)

    @torch.no_grad()
    def va(self, s0s):
        idx = (np.asarray(s0s)[:, None] + self.offs[None]).reshape(-1); v, a = [], []
        for k in range(0, len(idx), 2048):
            t = torch.tensor(idx[k:k + 2048], device=self.bt.dev)
            A = self.bt.audio(t); a.append(A.cpu().numpy()); v.append(self.aud(A).cpu().numpy())
        shp = (len(s0s), len(self.offs), -1)
        return np.concatenate(v).reshape(shp), np.concatenate(a).reshape(shp)


def evaluate_dense(b, model, head, bt, coh, calib, grid):
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v2 import evaluate as ev2
    orig = ev1.Reps
    ev1.Reps = lambda enc, aud, bt_, **kw: DenseReps(model, aud, bt_, grid)
    try:
        return ev2.evaluate_continuous(b, model, head, bt, coh, calib, None)
    finally:
        ev1.Reps = orig
