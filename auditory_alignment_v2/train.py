"""ALN2 anchor-level training (modules A, C-small, S, D-local). Built on the validated previous-round components:
the participant-balanced unique-segment batches, the reference losses (NCE dedup, traditional kernel CS, FMCA logdet),
the training-calibrated bandwidth / ridge, and the checkpoint rule "own objective minus legal mismatch" (40 fixed
early-stopping batches). New: encoder architectures (temporal.py), audio reference heads (audio_targets.py), anchored
reconstruction, same-trial attention selection, the TH_ONLY population, half-open windows for new architectures.
"""
from __future__ import annotations

import math
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from auditory_alignment.data import AUDIO_FRAMES
from auditory_alignment.train import Objective, _eff_rank, _kernel_stats, _save_resume, cs_diag
from .audio_targets import build_head, target_stats
from .temporal import build_encoder, describe, window_ranges

TARGET = {"local": "Local", "Ac": "Ac", "Lz": "Lz", "envelope": "envelope"}
N_SEL = 40
ROWS = {"NCE": 256, "CS_SINGLE": 256, "FMCA": 512, "SELECTION_CE": 256}
POP_EXCLUDE = {"TH_ONLY": {"ha", "ci"}, "TH_HA": {"ci"}}


def train_participants(coh, spec, subject_fold):
    ex = POP_EXCLUDE.get(spec.get("train_population", ""), set())
    return {i for i, p in enumerate(coh.participants)
            if not p.get("test_only") and (p.get("dev") or p["fold"] != subject_fold) and p["group"] not in ex}


class Batcher:
    """Anchor rows from unique-stimulus segments of training participants (kind: ss single speaker, cs competing)."""

    def __init__(self, coh, spec, row, dev):
        self.coh_segments, self.dev = coh.segments, dev
        self.fs, self.seg_len = coh.fs, coh.meta["seg_len"]
        self.W = window_ranges(spec["architecture"], coh.meta["dataset"], spec["window"], coh.fs)
        self.E = torch.tensor(coh.eeg, device=dev, dtype=torch.float16)
        self.S = torch.tensor(coh.stim[TARGET[spec["target"]]], device=dev)
        coh.eeg, coh.stim = None, None
        task = spec.get("training_task", "paired_alignment")
        self.kind = "cs" if task in ("attended_alignment", "alignment_plus_selection", "selection_only") else "ss"
        self.selection = task in ("alignment_plus_selection", "selection_only")
        self.wrong = spec.get("pairing") == "declared_wrong_pair"
        tp = train_participants(coh, spec, row["subject_fold"])
        segs = coh.segments
        self.fit = [i for i, s in enumerate(segs) if s["p"] in tp and s["role"] == "fit" and s["kind"] == self.kind]
        self.es = [i for i, s in enumerate(segs) if s["p"] in tp and s["role"] == "es" and s["kind"] == self.kind]
        self.train_p = tp
        self.audio_dim = self.S.shape[0] * AUDIO_FRAMES
        self.s0_true = np.array([s["s0"] for s in segs])
        self.s0_ign = np.array([s["s0_ign"] if s.get("s0_ign") is not None else -1 for s in segs])
        self.key_true = np.array([hash(s["uid"]) % (2 ** 31) for s in segs], dtype=np.int64)
        self.s0_train, self.key_train = self.s0_true, self.key_true
        if self.wrong:  # fixed seeded derangement of stimulus identity within fit and within es content (as E8)
            self.s0_train, self.key_train = self.s0_true.copy(), self.key_true.copy()
            r = np.random.default_rng(row["seed"] + 7)
            for units in (self.fit, self.es):
                uids = sorted({segs[i]["uid"] for i in units}); rep = {}
                for i in units:
                    rep.setdefault(segs[i]["uid"], i)
                perm = r.permutation(len(uids))
                while len(uids) > 1 and (perm == np.arange(len(uids))).any():
                    perm = r.permutation(len(uids))
                mapped = {u: rep[uids[perm[k]]] for k, u in enumerate(uids)}
                for i in units:
                    j = mapped[segs[i]["uid"]]
                    self.s0_train[i], self.key_train[i] = self.s0_true[j], self.key_true[j]

    def patches(self, e_idx):
        return [self.E[:, (e_idx[:, None] + torch.arange(a, b, device=self.dev)[None])].permute(1, 0, 2).float() for a, b in self.W]

    def audio(self, s_idx):
        return self.S[:, (s_idx[:, None] + torch.arange(AUDIO_FRAMES, device=self.dev)[None])].permute(1, 0, 2).flatten(1)

    def epoch_batches(self, rng, n_seg, units=None):
        units = self.fit if units is None else units
        segs = self.coh_segments
        by_p = {}
        for i in units:
            by_p.setdefault(segs[i]["p"], []).append(i)
        w = np.array([1.0 / len(by_p[segs[i]["p"]]) for i in units]); w /= w.sum()
        draw = list(rng.choice(units, size=len(units), replace=True, p=w))
        while draw:
            batch, used, rest = [], set(), []
            for i in draw:
                if len(batch) < n_seg and segs[i]["uid"] not in used:
                    batch.append(i); used.add(segs[i]["uid"])
                else:
                    rest.append(i)
            if len(batch) >= 2:
                yield batch
            if len(rest) == len(draw):
                break
            draw = rest

    def rows(self, batch, rng, anchors=8, pairing="train", roll=False):
        step = self.seg_len // anchors
        phase = rng.integers(0, step, size=len(batch))
        t = (phase[:, None] + np.arange(anchors)[None] * step).reshape(-1)
        b = np.repeat(np.arange(len(batch)), anchors)
        bi = np.asarray(batch)
        e0 = np.array([self.coh_segments[i]["e0"] for i in batch])[b] + t
        s0s, ks = (self.s0_train, self.key_train) if pairing == "train" else (self.s0_true, self.key_true)
        src = np.roll(np.arange(len(batch)), 1) if roll else np.arange(len(batch))
        s0 = s0s[bi][src][b] + t
        keys = torch.tensor(ks[bi][src][b] * 1000 + t, device=self.dev)
        out = [torch.tensor(e0, device=self.dev), torch.tensor(s0, device=self.dev), keys]
        if self.selection:
            out.append(torch.tensor(self.s0_ign[bi][b] + t, device=self.dev))
            out.append(torch.tensor(b, device=self.dev))
        return out


class SelectionScore(nn.Module):
    """Pair score for the two simultaneous streams: cosine in the common space (NCE / fixed-head paths) or an explicitly
    trained low-rank bilinear bridge (CS path; declared, trained by the selection loss)."""

    def __init__(self, d, kind):
        super().__init__()
        self.kind = kind
        if kind == "bilinear":
            self.Wb = nn.Parameter(torch.eye(d) + 0.01 * torch.randn(d, d))

    def forward(self, u, v):
        return (u * v).sum(1) if self.kind == "cosine" else ((u @ self.Wb) * v).sum(1)


def selection_loss(score, u, va, vi, seg_idx, n_seg, rng, temperature=0.1):
    """2AFC over the attended and ignored stream of the same segment; candidate order randomised (label swapped)."""
    sa = torch.zeros(n_seg, device=u.device).index_add_(0, seg_idx, score(u, va))
    si = torch.zeros(n_seg, device=u.device).index_add_(0, seg_idx, score(u, vi))
    cnt = torch.zeros(n_seg, device=u.device).index_add_(0, seg_idx, torch.ones_like(seg_idx, dtype=torch.float))
    sa, si = sa / cnt, si / cnt
    swap = torch.tensor(rng.integers(0, 2, n_seg), device=u.device).bool()
    logits = torch.stack([torch.where(swap, si, sa), torch.where(swap, sa, si)], 1) / temperature
    return F.cross_entropy(logits, swap.long()), float(((sa > si).float()).mean())


def fit_continuous(row, coh, dev, ckpt_prefix, log, sel_weight=None, anchor_weight=None):
    spec = row["spec"]
    d, obj_name = 16, spec["objective"]
    n_seg = max(2, ROWS.get(obj_name, 256) // 8)
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bt = Batcher(coh, spec, row, dev)
    enc = build_encoder(spec["architecture"], coh.n_ch, d, bt.W, coh.fs).to(dev)
    stats = target_stats(bt, np.random.default_rng(row["seed"] + 5))
    head = build_head(spec.get("audio_head", "trainable_head"), bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)
    task = spec.get("training_task", "paired_alignment")
    use_align = task != "selection_only"
    sel = SelectionScore(d, "bilinear" if obj_name == "CS_SINGLE" else "cosine").to(dev) if bt.selection else None
    params = [p for m in (enc, head, sel) if m is not None for p in m.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=1e-3, weight_decay=1e-4)
    epochs = int(spec.get("epochs", 200))
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), n_seg))
    obj_job = {"objective": "NCE" if obj_name == "SELECTION_CE" else obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    with torch.no_grad():
        r0 = bt.rows(calib, np.random.default_rng(row["seed"] + 98))
        obj = Objective(obj_job, enc(bt.patches(r0[0])), head(bt.audio(r0[1])))
    es_rng = np.random.default_rng(12345)
    es_sel = []
    while len(es_sel) < N_SEL:
        got = [b for b, _ in zip(bt.epoch_batches(es_rng, n_seg, bt.es), range(N_SEL - len(es_sel)))]
        if not got:
            break
        es_sel += got
    es_sets = [(bt.rows(b, np.random.default_rng(k)), bt.rows(b, np.random.default_rng(k), roll=True), len(b)) for k, b in enumerate(es_sel)]
    sw = 1.0 if sel_weight is None else sel_weight
    aw = 0.0 if anchor_weight is None else anchor_weight

    def batch_loss(rws, n_b, rng_l, train_mode):
        u, v = enc(bt.patches(rws[0])), head(bt.audio(rws[1]))
        loss, parts = 0.0, {}
        if use_align:
            la, _ = obj(u, v, keys=rws[2]); loss = loss + la; parts["align"] = float(la)
        if bt.selection:
            vi = head(bt.audio(rws[3]))
            ls, acc = selection_loss(sel, u, v, vi, rws[4], n_b, rng_l)
            loss = loss + (sw if use_align else 1.0) * ls; parts["selection"] = float(ls); parts["sel_acc"] = acc
        if aw and train_mode:
            ax = head.aux_loss()
            if ax is not None:
                loss = loss + aw * ax; parts["anchor"] = float(ax)
        return loss, parts, u, v

    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    mods = {"enc": enc, "head": head, **({"sel": sel} if sel is not None else {})}
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        for k, m in mods.items():
            m.load_state_dict(r[k])
        opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    for ep in range(ep0, epochs):
        for m in mods.values():
            m.train()
        tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            rws = bt.rows(batch, rng)
            loss, parts, _, _ = batch_loss(rws, len(batch), rng, True)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if ep % 5 == 4 or ep == epochs - 1:
            for m in mods.values():
                m.eval()
            with torch.no_grad():
                el, elr, accs, dm, dx = [], [], [], [], []
                for (rws, rr, n_b) in es_sets:
                    l_, parts, u, v = batch_loss(rws, n_b, np.random.default_rng(0), False)
                    lr_, _, _, vr = batch_loss(rr, n_b, np.random.default_rng(0), False)
                    el.append(float(l_)); elr.append(float(lr_))
                    if "sel_acc" in parts:
                        accs.append(parts["sel_acc"])
                    if obj.sigma_v is not None:
                        dm.append(cs_diag(u, v, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v)); dx.append(cs_diag(u, vr, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
                es_loss, es_mm = float(np.mean(el)), float(np.mean(elr))
                # selection-only: the legal mismatch does not define the task; select on the 2AFC loss itself
                sel_score = es_loss if not use_align else es_loss - es_mm
                avg = lambda L, k: float(np.mean([x[k] for x in L])) if L else None
                rec = {"epoch": ep + 1, "step": step, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss, "es_loss_mismatched": es_mm,
                       "selection_score": sel_score, "es_sel_acc": float(np.mean(accs)) if accs else None,
                       "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1),
                       "es_cs_true_nats": avg(dm, "cs_qmi_nats"), "es_cs_mismatched_nats": avg(dx, "cs_qmi_nats"),
                       "u_eff_rank": _eff_rank(u), "kernel_u": _kernel_stats(u, obj.sigma_u), "lr": float(sched.get_last_lr()[0])}
            curve.append(rec)
            if sel_score < best[0]:
                best = (sel_score, ep + 1)
                torch.save({k: m.state_dict() for k, m in mods.items()}, ckpt_prefix + "_best.pt")
            if (ep + 1) % 20 == 0 and ep + 1 < epochs:
                _save_resume(rpath, **{k: m.state_dict() for k, m in mods.items()}, opt=opt.state_dict(), sched=sched.state_dict(),
                             rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    torch.save({k: m.state_dict() for k, m in mods.items()}, ckpt_prefix + "_last.pt")
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": ("min es 2AFC loss" if not use_align else "min over validations of es_loss(training pairing) - es_loss(within-batch roll)"),
                "epochs_completed": epochs, "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit),
                "n_es_segments": len(bt.es), "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1),
                "encoder": describe(enc), "windows_samples": [list(w) for w in bt.W], "window_rule": "legacy_plus1" if spec["architecture"] == "legacy_pool4" else "half_open",
                "audio_head": spec.get("audio_head"), "selection_weight": sw if bt.selection else None, "anchor_weight": aw or None})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    for k, m in mods.items():
        m.load_state_dict(sd[k]); m.eval()
    return enc, head, bt, sel


# ------------------------------------------------------------------------------------------------ private current class
class PrivateBatcher:
    """All trials of all children on the GPU (fp16), cropped to the union of the unit's windows; batches of 32 children x
    per trials; labels follow the training pairing (also on early-stopping blocks) unless true_labels."""

    def __init__(self, kids, spec, row, dev):
        self.dev, self.kids = dev, kids
        W = window_ranges(spec["architecture"], "private_bdf", spec["window"], 250, pre=50)
        lo, hi = min(a for a, _ in W), max(b for _, b in W)
        self.W, self.lo, self.hi = [(a - lo, b - lo) for a, b in W], lo, hi
        self.train = [i for i, k in enumerate(kids) if k["fold"] != row["subject_fold"]]
        self.off = np.cumsum([0] + [len(k["y"]) for k in kids])
        self.Xall = torch.tensor(np.concatenate([k["x"][:, :, lo:hi] for k in kids]), device=dev, dtype=torch.float16)
        yall = np.concatenate([k["y"] for k in kids])
        self.wrong = spec.get("pairing") == "declared_wrong_pair"
        if self.wrong:
            r = np.random.default_rng(row["seed"] + 7); yall = yall.copy()
            for i in self.train:
                a, b = self.off[i], self.off[i + 1]; yall[a:b] = yall[a:b][r.permutation(b - a)]
        self.yall = torch.tensor(yall, device=dev)
        self.ytrue = torch.tensor(np.concatenate([k["y"] for k in kids]), device=dev)
        self.fit_idx = {i: self.off[i] + np.flatnonzero(~kids[i]["es_mask"]) for i in self.train}
        self.es_idx = {i: self.off[i] + np.flatnonzero(kids[i]["es_mask"]) for i in self.train}

    def patches(self, i, idx):
        x = self.Xall[torch.as_tensor(self.off[i], device=self.dev) + idx].float()
        return [x[:, :, a:b] for a, b in self.W]

    def batch(self, rng, es=False, n_kids=32, per=8, true_labels=False):
        src = self.es_idx if es else self.fit_idx
        pool = [i for i in self.train if len(src[i])]
        ks = rng.choice(pool, size=min(n_kids, len(pool)), replace=False)
        g = torch.tensor(np.concatenate([src[i][rng.integers(0, len(src[i]), size=per)] for i in ks]), device=self.dev)
        x = self.Xall[g].float()
        return [x[:, :, a:b] for a, b in self.W], (self.ytrue[g] if true_labels else self.yall[g])


def fit_private(row, kids, dev, ckpt_prefix, log):
    spec = row["spec"]
    d, obj_name = 16, spec["objective"]
    rows = ROWS.get(obj_name, 256); per = max(1, rows // 32)
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bt = PrivateBatcher(kids, spec, row, dev)
    enc = build_encoder(spec["architecture"], 20, d, bt.W, 250).to(dev)
    protos = nn.Parameter(torch.randn(2, d, device=dev))
    params = list(enc.parameters()) + ([protos] if obj_name == "NCE" else [])
    opt = torch.optim.AdamW(params, lr=1e-3, weight_decay=1e-4)
    epochs = int(spec.get("epochs", 200))
    n_fit = sum(len(bt.fit_idx[i]) for i in bt.train)
    steps_per_epoch = max(1, n_fit // rows)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    obj_job = {"objective": obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    with torch.no_grad():
        P, Y = bt.batch(np.random.default_rng(row["seed"] + 99), per=per)
        obj = Objective(obj_job, enc(P), None, labels0=Y)
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
    for ep in range(ep0, epochs):
        enc.train(); tl, gns, nonfin = [], [], 0
        for _ in range(steps_per_epoch):
            P, Y = bt.batch(rng, per=per)
            loss, _ = obj(enc(P), labels=Y, prototypes=protos)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if ep % 5 == 4 or ep == epochs - 1:
            enc.eval()
            with torch.no_grad():
                el = [float(obj(enc(P), labels=Y, prototypes=protos)[0]) for P, Y in es_batches]
                elr = [float(obj(enc(P), labels=Yp, prototypes=protos)[0]) for (P, _), Yp in zip(es_batches, es_perm)]
            es_loss, es_mm = float(np.mean(el)), float(np.mean(elr)); sel = es_loss - es_mm
            curve.append({"epoch": ep + 1, "step": step, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss,
                          "es_loss_mismatched": es_mm, "selection_score": sel, "grad_norm": float(np.mean(gns)) if gns else None,
                          "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1), "lr": float(sched.get_last_lr()[0])})
            if sel < best[0]:
                best = (sel, ep + 1)
                torch.save({"enc": enc.state_dict(), "protos": protos.detach()}, ckpt_prefix + "_best.pt")
            enc.train()
            if (ep + 1) % 20 == 0 and ep + 1 < epochs:
                _save_resume(rpath, enc=enc.state_dict(), protos=protos.detach(), opt=opt.state_dict(), sched=sched.state_dict(),
                             rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    torch.save({"enc": enc.state_dict(), "protos": protos.detach()}, ckpt_prefix + "_last.pt")
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": "min over validations of es_loss(training labels) - es_loss(labels permuted within batch)",
                "epochs_completed": epochs, "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_trials": n_fit,
                "n_train_children": len(bt.train), "train_seconds": round(time.time() - t0, 1), "encoder": describe(enc),
                "windows_samples_from_epoch_start": [[a + bt.lo, b + bt.lo] for a, b in bt.W],
                "window_rule": "legacy_plus1" if spec["architecture"] == "legacy_pool4" else "half_open"})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    enc.load_state_dict(sd["enc"]); protos.data.copy_(sd["protos"]); enc.eval()
    return enc, bt, protos
