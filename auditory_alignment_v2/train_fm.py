"""ALN2 module B training: foundation backbones on full 5 s segments (B-full; information-budget stratum
'foundation_segment') and on private full epochs ('padded_private_epoch_no_extra_EEG').

Continuous: each backbone patch p (start a_p s; CBraMod 0,1,..,4; REVE 0,0.9,..,3.6) is one alignment row, paired with
the audio target over [a_p - 0.2 s, a_p + 1.0 s) (the 0.2 s lead never crosses a segment's start guard; Federici's guard
is exactly 0.2 s), average-pooled in bins of 8 frames, standardised on the training side and projected by the fixed
semi-orthogonal cohort map (fixed_features). Rows per batch = 32 segments x P patches; NCE keys = (stimulus uid, patch).
Same objectives (reference NCE / traditional kernel CS), training-calibrated bandwidth, checkpoint rule (own objective
minus legal within-batch mismatch over 40 fixed early-stopping batches) and resume points as the anchor-level trainer.
Parameter groups: backbone (lr_backbone) and head (lr_head), AdamW, cosine schedule over actual updates.
Readout (amendment A1, 2026-10-07): fm_readout.SpatialPatchHead (channel-aware, signed spatial filters, patch axis kept);
the earlier channel-mean head is the legacy_chmean_v1 variant. Final-epoch states are not saved (never read).
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
from .audio_targets import COHORT_SEED, Standardiser, semi_orthogonal
from .fm_readout import make_head
from .foundation_adapter import Backbone
from .train import N_SEL, TARGET, Batcher, SelectionScore

LEAD_S, SPAN_S, BIN = 0.2, 1.2, 8


class FMEncoder(nn.Module):
    def __init__(self, backbone, d=16):
        super().__init__(); self.bb = backbone; self.head = make_head(backbone, d)  # amendment A1: channel-aware spatial readout

    def forward(self, x):  # x [B, C, T] -> [B, P, d]
        return self.head(self.bb(x))


class SegmentAudioHead(nn.Module):
    """fixed_features for patch-level audio windows: standardise the flattened [n_bins x D] window, fixed projection."""

    def __init__(self, in_dim, d, mu, sd, cohort):
        super().__init__()
        self.std = Standardiser(mu, sd)
        self.register_buffer("P", semi_orthogonal(d, in_dim, COHORT_SEED[cohort] + 101))

    def forward(self, a):
        return F.normalize(self.std(a) @ self.P.T, dim=-1)


class SegmentBatcher(Batcher):
    """Segment rows for foundation models (inherits population / pairing / content logic of the anchor batcher)."""

    def __init__(self, coh, spec, row, dev, patch_starts):
        spec = dict(spec); spec["architecture"] = "density_tokens"; spec["window"] = "full"  # windows unused here
        super().__init__(coh, spec, row, dev)
        self.starts = patch_starts
        self.nbin = int(SPAN_S * self.fs) // BIN
        self.offs = [int(round((a - LEAD_S) * self.fs)) for a in patch_starts]

    def segments(self, e_idx):  # [n] -> [n, C, seg_len]
        return self.E[:, (e_idx[:, None] + torch.arange(self.seg_len, device=self.dev)[None])].permute(1, 0, 2).float()

    def audio_patches(self, s_idx):  # [n] -> [n, P, nbin * D]
        out = []
        for o in self.offs:
            st = s_idx + o
            fr = self.S[:, (st[:, None] + torch.arange(self.nbin * BIN, device=self.dev)[None])]  # [D, n, nbin*BIN]
            fr = fr.reshape(fr.shape[0], fr.shape[1], self.nbin, BIN).mean(-1)  # [D, n, nbin]
            out.append(fr.permute(1, 2, 0).flatten(1))
        return torch.stack(out, 1)

    def seg_rows(self, batch, pairing="train", roll=False):
        bi = np.asarray(batch)
        e0 = torch.tensor([self.coh_segments[i]["e0"] for i in batch], device=self.dev)
        s0s, ks = (self.s0_train, self.key_train) if pairing == "train" else (self.s0_true, self.key_true)
        src = np.roll(np.arange(len(batch)), 1) if roll else np.arange(len(batch))
        s0 = torch.tensor(s0s[bi][src], device=self.dev)
        keys = torch.tensor(ks[bi][src], device=self.dev)[:, None] * 100 + torch.arange(len(self.starts), device=self.dev)[None]
        out = [e0, s0, keys.reshape(-1)]
        if self.selection:
            out.append(torch.tensor(self.s0_ign[bi], device=self.dev))
        return out


@torch.no_grad()
def seg_target_stats(bt, rng, n_seg=300):
    segs = [bt.fit[i] for i in rng.choice(len(bt.fit), size=min(n_seg, len(bt.fit)), replace=False)]
    A = bt.audio_patches(torch.tensor([bt.coh_segments[i]["s0"] for i in segs], device=bt.dev))
    return A.mean((0, 1)).cpu().numpy(), (A.std((0, 1)) + 1e-6).cpu().numpy()


def param_groups(enc, lr_backbone, lr_head):
    bb = [p for p in enc.bb.parameters() if p.requires_grad]
    hd = [p for p in enc.head.parameters() if p.requires_grad]
    groups = ([{"params": bb, "lr": lr_backbone}] if bb else []) + [{"params": hd, "lr": lr_head}]
    return groups, bb + hd


def seg_selection_loss(score, u, va, vi, rng, temperature=0.1):
    """2AFC between the simultaneous attended / ignored streams; pair score averaged over a segment's patches."""
    B, Pn, d = u.shape
    sa = score(u.reshape(-1, d), va.reshape(-1, d)).reshape(B, Pn).mean(1)
    si = score(u.reshape(-1, d), vi.reshape(-1, d)).reshape(B, Pn).mean(1)
    swap = torch.tensor(rng.integers(0, 2, B), device=u.device).bool()
    logits = torch.stack([torch.where(swap, si, sa), torch.where(swap, sa, si)], 1) / temperature
    return F.cross_entropy(logits, swap.long()), float((sa > si).float().mean())


def fit_segments(row, coh, dev, ckpt_prefix, log, lr_backbone, lr_head, epochs, adaptation, n_seg=32, init_state=None, sel_weight=None):
    spec = row["spec"]; arch = spec["architecture"]; obj_name = spec["objective"]
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bb = Backbone(arch, coh.meta["dataset"], adaptation, coh.fs, init_state=init_state)  # donor loaded before LoRA
    enc = FMEncoder(bb).to(dev)
    bt = SegmentBatcher(coh, spec, row, dev, bb.patch_starts(int(round(coh.meta["seg_len"] * 200 / coh.fs))))
    stats = seg_target_stats(bt, np.random.default_rng(row["seed"] + 5))
    head = SegmentAudioHead(bt.nbin * bt.S.shape[0], 16, *stats, coh.meta["dataset"]).to(dev)
    groups, params = param_groups(enc, lr_backbone, lr_head)
    use_align = spec.get("training_task") != "selection_only"
    sel = SelectionScore(16, "bilinear" if obj_name == "CS_SINGLE" else "cosine").to(dev) if bt.selection else None
    if sel is not None and any(p.requires_grad for p in sel.parameters()):
        sp = list(sel.parameters()); groups[-1]["params"] = groups[-1]["params"] + sp; params = params + sp
    sw = 1.0 if sel_weight is None else sel_weight
    opt = torch.optim.AdamW(groups, weight_decay=1e-4)
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    obj_job = {"objective": "NCE" if obj_name == "SELECTION_CE" else obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    P = len(bt.starts)
    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), n_seg))
    with torch.no_grad():
        r0 = bt.seg_rows(calib)
        obj = Objective(obj_job, enc(bt.segments(r0[0])).reshape(-1, 16), head(bt.audio_patches(r0[1])).reshape(-1, 16))
    es_rng = np.random.default_rng(12345); es_sel = []
    while len(es_sel) < N_SEL:
        got = [b for b, _ in zip(bt.epoch_batches(es_rng, n_seg, bt.es), range(N_SEL - len(es_sel)))]
        if not got:
            break
        es_sel += got

    def loss_of(rws, enc_out=None, rng_l=None):
        U = enc(bt.segments(rws[0])) if enc_out is None else enc_out
        V = head(bt.audio_patches(rws[1]))
        u, v = U.reshape(-1, 16), V.reshape(-1, 16)
        l = 0.0; acc = None
        if use_align:
            la, _ = obj(u, v, keys=rws[2]); l = l + la
        if sel is not None:
            ls, acc = seg_selection_loss(sel, U, V, head(bt.audio_patches(rws[3])), rng_l or np.random.default_rng(0))
            l = l + (sw if use_align else 1.0) * ls
        loss_of.acc = acc
        return l, u, v

    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        enc.load_state_dict(r["enc"]); opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    val_every = max(1, epochs // 20)
    for ep in range(ep0, epochs):
        enc.train(); tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            loss, _, _ = loss_of(bt.seg_rows(batch), rng_l=rng)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if (ep + 1) % val_every == 0 or ep == epochs - 1:
            enc.eval()
            with torch.no_grad():
                el, elr, dm, dx, accs = [], [], [], [], []
                for b in es_sel:
                    rws, rr = bt.seg_rows(b), bt.seg_rows(b, roll=True)
                    eo = enc(bt.segments(rws[0]))
                    l1, u, v = loss_of(rws, eo)
                    if loss_of.acc is not None:
                        accs.append(loss_of.acc)
                    l2, _, vr = loss_of(rr, eo)
                    el.append(float(l1)); elr.append(float(l2))
                    dm.append(cs_diag(u, v, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v)); dx.append(cs_diag(u, vr, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
            es_loss, es_mm = float(np.mean(el)), float(np.mean(elr)); selsc = es_loss - es_mm if use_align else es_loss
            curve.append({"epoch": ep + 1, "step": step, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss, "es_loss_mismatched": es_mm,
                          "selection_score": selsc, "es_sel_acc": float(np.mean(accs)) if accs else None, "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin,
                          "seconds": round(time.time() - t0, 1), "es_cs_true_nats": float(np.mean([x["cs_qmi_nats"] for x in dm])),
                          "es_cs_mismatched_nats": float(np.mean([x["cs_qmi_nats"] for x in dx])), "u_eff_rank": _eff_rank(u)})
            if selsc < best[0]:
                best = (selsc, ep + 1); torch.save({"enc": enc.state_dict(), **({"sel": sel.state_dict()} if sel is not None else {})}, ckpt_prefix + "_best.pt")
            _save_resume(rpath, enc=enc.state_dict(), opt=opt.state_dict(), sched=sched.state_dict(), rng=rng.bit_generator.state,
                         torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": "min over validations of es_loss(training pairing) - es_loss(within-batch roll)", "epochs_completed": epochs,
                "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit), "n_es_segments": len(bt.es),
                "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1), "backbone_contract": bb.contract(),
                "patch_starts_s": bt.starts, "audio_window": f"[a_p - {LEAD_S} s, a_p + {SPAN_S - LEAD_S} s), bins of {BIN} frames",
                "rows_per_batch": n_seg * P, "lr_backbone": lr_backbone, "lr_head": lr_head})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    enc.load_state_dict(sd["enc"]); enc.eval()
    if sel is not None:
        sel.load_state_dict(sd["sel"]); sel.eval()
    log["selection_weight"] = sw if sel is not None else None
    return enc, head, bt, sel


# ------------------------------------------------------------------------------------------------ private full epochs
from .train import PrivateBatcher, ROWS  # noqa: E402


class PrivateFMBatcher(PrivateBatcher):
    """Full private epoch (-200..600 ms, 200 samples at 250 Hz) for foundation backbones; no EEG outside the epoch."""

    def __init__(self, kids, spec, row, dev):
        spec = dict(spec); spec["architecture"] = "density_tokens"; spec["window"] = "full"
        super().__init__(kids, spec, row, dev)
        n = kids[0]["x"].shape[-1]
        self.W, self.lo, self.hi = [(0, n)], 0, n
        self.Xall = torch.tensor(np.concatenate([k["x"] for k in kids]), device=dev, dtype=torch.float16)


class EpochEncoder(nn.Module):
    """list([x [B, C, T]]) -> [B, d] (one backbone patch per padded epoch)."""

    def __init__(self, backbone, d=16):
        super().__init__(); self.bb = backbone; self.head = make_head(backbone, d)  # amendment A1: channel-aware spatial readout

    def forward(self, patches):
        return self.head(self.bb(patches[0]))[:, 0]


def fit_private_fm(row, kids, dev, ckpt_prefix, log, lr_backbone, lr_head, epochs, adaptation, init_state=None):
    spec = row["spec"]; obj_name = spec["objective"]; arch = spec["architecture"]
    rows = ROWS.get(obj_name, 256); per = max(1, rows // 32)
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bb = Backbone(arch, "private_bdf", adaptation, 250, init_state=init_state)  # donor loaded before LoRA
    enc = EpochEncoder(bb).to(dev)
    bt = PrivateFMBatcher(kids, spec, row, dev)
    protos = nn.Parameter(torch.randn(2, 16, device=dev))
    groups, params = param_groups(enc, lr_backbone, lr_head)
    if obj_name == "NCE":
        groups[-1]["params"] = groups[-1]["params"] + [protos]; params = params + [protos]
    opt = torch.optim.AdamW(groups, weight_decay=1e-4)
    n_fit = sum(len(bt.fit_idx[i]) for i in bt.train)
    steps_per_epoch = max(1, n_fit // rows)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    obj_job = {"objective": obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    with torch.no_grad():
        Pb, Y = bt.batch(np.random.default_rng(row["seed"] + 99), per=per)
        obj = Objective(obj_job, enc(Pb), None, labels0=Y)
    es_batches = [bt.batch(np.random.default_rng(k), es=True, per=per) for k in range(N_SEL)]
    perm_rng = np.random.default_rng(54321)
    es_perm = [Y[torch.tensor(perm_rng.permutation(len(Y)), device=dev)] for _, Y in es_batches]
    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        enc.load_state_dict(r["enc"]); protos.data.copy_(r["protos"]); opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    val_every = max(1, epochs // 20)
    for ep in range(ep0, epochs):
        enc.train(); tl, gns, nonfin = [], [], 0
        for _ in range(steps_per_epoch):
            Pb, Y = bt.batch(rng, per=per)
            loss, _ = obj(enc(Pb), labels=Y, prototypes=protos)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if (ep + 1) % val_every == 0 or ep == epochs - 1:
            enc.eval()
            with torch.no_grad():
                el = [float(obj(enc(Pb), labels=Y, prototypes=protos)[0]) for Pb, Y in es_batches]
                elr = [float(obj(enc(Pb), labels=Yp, prototypes=protos)[0]) for (Pb, _), Yp in zip(es_batches, es_perm)]
            es_loss, es_mm = float(np.mean(el)), float(np.mean(elr)); sel = es_loss - es_mm
            curve.append({"epoch": ep + 1, "step": step, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss, "es_loss_mismatched": es_mm,
                          "selection_score": sel, "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1)})
            if sel < best[0]:
                best = (sel, ep + 1); torch.save({"enc": enc.state_dict(), "protos": protos.detach()}, ckpt_prefix + "_best.pt")
            _save_resume(rpath, enc=enc.state_dict(), protos=protos.detach(), opt=opt.state_dict(), sched=sched.state_dict(), rng=rng.bit_generator.state,
                         torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": "min over validations of es_loss(training labels) - es_loss(labels permuted within batch)", "epochs_completed": epochs,
                "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_trials": n_fit, "n_train_children": len(bt.train),
                "train_seconds": round(time.time() - t0, 1), "backbone_contract": bb.contract(), "epoch_support": "full epoch -200..600 ms, zero-padded to 1 s at 200 Hz",
                "lr_backbone": lr_backbone, "lr_head": lr_head})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    enc.load_state_dict(sd["enc"]); protos.data.copy_(sd["protos"]); enc.eval()
    return enc, bt, protos
