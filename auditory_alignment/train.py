"""Training of one fit unit (IMPLEMENTATION_NOTES §3). Bandwidths / ridges are set on a training calibration batch from
the initial representations and frozen for the fit; the best checkpoint is chosen on the early-stopping content (or
blocks) with each method's own objective; curves log the objective, the CS information potentials, off-diagonal kernel
values, representation scale, effective rank, gradient norm and non-finite counts.
"""
from __future__ import annotations

import math
import os
import time

import numpy as np
import torch
import torch.nn.functional as F

from .data import AUDIO_FRAMES
from .losses import cs_qmi, deduplicated_infonce, fmca_logdet_loss, multiscale_cs_loss, prototype_nce
from .model import AudioProjection, EEGEncoder, window_samples

TARGET = {"local": "Local", "Ac": "Ac", "Lz": "Lz", "envelope": "envelope"}
N_SEL = 40  # fixed early-stopping batches used for checkpoint selection


def windows_for(job):
    return ["early", "late"] if job["window"] == "joint" else [job["window"]]


def train_participants(coh, job):
    pop = job["train_population"]
    keep = []
    for i, p in enumerate(coh.participants):
        if p.get("test_only") or (p["fold"] == job["subject_fold"] and not p.get("dev")):
            continue
        if pop == "TH_HA" and p["group"] == "ci":
            continue
        keep.append(i)
    return set(keep)


def _offdiag_median_dist(x):
    d = torch.cdist(x.double(), x.double())
    n = d.shape[0]
    return float(d[~torch.eye(n, dtype=torch.bool, device=d.device)].median())


def _eff_rank(x):
    s = torch.linalg.svdvals(x.double() - x.double().mean(0))
    p = s / s.sum()
    return float(torch.exp(-(p * torch.log(p + 1e-12)).sum()))


def cs_diag(u, v=None, labels=None, sigma_u=None, sigma_v=None):
    """Single-scale CS-QMI at the unit's calibrated bandwidths (diagnostic for every objective)."""
    _, st = cs_qmi(u, v, sigma_u=sigma_u, sigma_v=sigma_v, labels=labels)
    return st


def _save_resume(path, **kw):
    torch.save(kw, path + ".tmp"); os.replace(path + ".tmp", path)


def _kernel_stats(u, sigma):
    if sigma is None:
        return None
    d2 = torch.cdist(u.double(), u.double()).pow(2)
    k = torch.exp(-d2 / (2 * sigma ** 2))
    n = k.shape[0]
    off = k[~torch.eye(n, dtype=torch.bool, device=k.device)]
    return {"k_off_mean": float(off.mean()), "k_off_p10": float(off.quantile(0.1)), "k_off_p90": float(off.quantile(0.9))}


class Objective:
    def __init__(self, job, u0, v0, labels0=None):
        c = job["config"]; self.name = job["objective"]
        self.temperature = c.get("temperature") or 0.1
        self.scales = c.get("bandwidth_scales") or [0.5, 1.0, 2.0]
        mult = c.get("bandwidth_multiplier") or 1.0
        self.sigma_u = _offdiag_median_dist(u0) * mult
        self.sigma_v = _offdiag_median_dist(v0) * mult if v0 is not None else None
        rel = c.get("fmca_relative_ridge") or 1e-3
        uc = u0.double() - u0.double().mean(0)
        self.ridge_u = rel * float((uc.T @ uc / len(uc)).diagonal().mean())
        if v0 is not None:
            vc = v0.double() - v0.double().mean(0)
            self.ridge_v = rel * float((vc.T @ vc / len(vc)).diagonal().mean())
        else:
            yc = labels0.double() - labels0.double().mean()
            self.ridge_v = rel * float((yc ** 2).mean())

    def record(self):
        return {"sigma_u": self.sigma_u, "sigma_v": self.sigma_v, "ridge_u": self.ridge_u, "ridge_v": self.ridge_v,
                "temperature": self.temperature, "scales": self.scales}

    def __call__(self, u, v=None, keys=None, labels=None, prototypes=None):
        if self.name == "NCE":
            if labels is not None:
                return prototype_nce(u, labels, prototypes, self.temperature), {}
            return deduplicated_infonce(u, v, keys, self.temperature), {}
        if self.name == "FMCA":
            vv = v if v is not None else (labels.double() - labels.double().mean())[:, None]
            return fmca_logdet_loss(u, vv, ridge_u=self.ridge_u, ridge_v=self.ridge_v), {}
        if self.name == "CS_SINGLE":
            val, st = cs_qmi(u, v, sigma_u=self.sigma_u, sigma_v=self.sigma_v, labels=labels)
            return -val, st
        if self.name == "CS_MULTI":
            loss, st = multiscale_cs_loss(u, v, sigma_u=self.sigma_u, sigma_v=self.sigma_v, scales=self.scales, labels=labels)
            return loss, {"mean_cs_nats": st["mean_cs_nats"]}
        raise ValueError(self.name)


# ------------------------------------------------------------------------------------------------ continuous speech
class ContinuousBatcher:
    def __init__(self, coh, job, dev):
        self.coh, self.dev = coh, dev
        self.fs, self.seg_len = coh.fs, coh.meta["seg_len"]
        self.W = [window_samples(coh.meta["dataset"], w, coh.fs) for w in windows_for(job)]
        self.E = torch.tensor(coh.eeg, device=dev, dtype=torch.float16)  # storage precision only; patches are cast to float32
        self.S = torch.tensor(coh.stim[TARGET[job["target"]]], device=dev)
        coh.eeg, coh.stim = None, None  # host copies are not used after the GPU transfer (host-memory budget of the pool)
        self.wrong = job["config"].get("pairing") == "training_side_mismatch_preserving_declared_structure"
        self.kind = "cs" if job["config"].get("training_task") == "competing_speech_attended_alignment" else "ss"
        tp = train_participants(coh, job)
        self.fit = [i for i, s in enumerate(coh.segments) if s["p"] in tp and s["role"] == "fit" and s["kind"] == self.kind]
        self.es = [i for i, s in enumerate(coh.segments) if s["p"] in tp and s["role"] == "es" and s["kind"] == self.kind]
        self.train_p = tp
        self.audio_dim = self.S.shape[0] * AUDIO_FRAMES
        self.s0_true = np.array([s["s0"] for s in coh.segments])
        self.key_true = np.array([hash(s["uid"]) % (2 ** 31) for s in coh.segments], dtype=np.int64)
        self.s0_train, self.key_train = self.s0_true, self.key_true
        if self.wrong:  # fixed seeded derangement of stimulus identity (separately within fit and es content)
            self.s0_train, self.key_train = self.s0_true.copy(), self.key_true.copy()
            r = np.random.default_rng(job["seed"] + 7)
            for units in (self.fit, self.es):
                uids = sorted({coh.segments[i]["uid"] for i in units})
                rep_i = {}
                for i in units:
                    rep_i.setdefault(coh.segments[i]["uid"], i)
                perm = r.permutation(len(uids))
                while len(uids) > 1 and (perm == np.arange(len(uids))).any():
                    perm = r.permutation(len(uids))
                mapped = {u: rep_i[uids[perm[k]]] for k, u in enumerate(uids)}
                for i in units:
                    j = mapped[coh.segments[i]["uid"]]
                    self.s0_train[i], self.key_train[i] = self.s0_true[j], self.key_true[j]

    def patches(self, e_idx):
        return [self.E[:, (e_idx[:, None] + torch.arange(a, b, device=self.dev)[None])].permute(1, 0, 2).float() for a, b in self.W]

    def audio(self, s_idx):
        return self.S[:, (s_idx[:, None] + torch.arange(AUDIO_FRAMES, device=self.dev)[None])].permute(1, 0, 2).flatten(1)

    def epoch_batches(self, rng, n_seg, units=None):
        """Participant-balanced draw of the fit segments, grouped into batches of n_seg unique stimulus segments."""
        units = self.fit if units is None else units
        segs = self.coh.segments
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
        """pairing: 'train' (the unit's training pairing) or 'true'; roll: audio of the next segment in the batch (legal
        mismatch: real speech, same anchor times). The EEG rows depend only on (batch, rng), not on the pairing."""
        segs = self.coh.segments
        step = self.seg_len // anchors
        phase = rng.integers(0, step, size=len(batch))
        t = (phase[:, None] + np.arange(anchors)[None] * step).reshape(-1)
        b = np.repeat(np.arange(len(batch)), anchors)
        bi = np.asarray(batch)
        e0 = np.array([segs[i]["e0"] for i in batch])[b] + t
        s0s, ks = (self.s0_train, self.key_train) if pairing == "train" else (self.s0_true, self.key_true)
        src = np.roll(np.arange(len(batch)), 1) if roll else np.arange(len(batch))
        s0 = s0s[bi][src][b] + t
        keys = torch.tensor(ks[bi][src][b] * 1000 + t, device=self.dev)
        return torch.tensor(e0, device=self.dev), torch.tensor(s0, device=self.dev), keys


def fit_continuous(job, coh, dev, ckpt_prefix, log):
    c = job["config"]
    d = c.get("projection_dim") or 16
    n_seg = max(2, (c.get("kernel_rows") or 256) // 8)
    torch.manual_seed(job["seed"]); rng = np.random.default_rng(job["seed"])
    bt = ContinuousBatcher(coh, job, dev)
    enc = EEGEncoder(coh.n_ch, d, bt.W).to(dev)
    aud = AudioProjection(bt.audio_dim, d, frozen=c.get("audio_projection") == "frozen_initial_projection").to(dev)
    params = [p for p in list(enc.parameters()) + list(aud.parameters()) if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=c.get("learning_rate", 1e-3), weight_decay=c.get("weight_decay", 1e-4))
    epochs = int(c.get("epochs_initial", 200))
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    calib = next(bt.epoch_batches(np.random.default_rng(job["seed"] + 99), n_seg))
    with torch.no_grad():
        e0, s0, _ = bt.rows(calib, np.random.default_rng(job["seed"] + 98))
        obj = Objective(job, enc(bt.patches(e0)), aud(bt.audio(s0)))
    es_rng = np.random.default_rng(12345)
    es_sel = []  # 40 fixed selection batches (several passes over the early-stop content when it is small)
    while len(es_sel) < N_SEL:
        got = [b for b, _ in zip(bt.epoch_batches(es_rng, n_seg, bt.es), range(N_SEL - len(es_sel)))]
        if not got:
            break
        es_sel += got
    # per early-stop batch: EEG rows, audio under the training pairing, its legal mismatch, and (wrong-pair units) the true pairing
    es_sets = []
    for k, b in enumerate(es_sel):
        e0, s0, kk = bt.rows(b, np.random.default_rng(k))
        _, s0r, kr = bt.rows(b, np.random.default_rng(k), roll=True)
        _, s0t, _ = bt.rows(b, np.random.default_rng(k), pairing="true")
        _, s0tr, _ = bt.rows(b, np.random.default_rng(k), pairing="true", roll=True)
        es_sets.append((e0, s0, kk, s0r, kr, s0t, s0tr))
    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):  # runfill preemption: continue from the last saved epoch
        r = torch.load(rpath, map_location=dev, weights_only=False)
        enc.load_state_dict(r["enc"]); aud.load_state_dict(r["aud"]); opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    for ep in range(ep0, epochs):
        enc.train(); aud.train()
        tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            e0, s0, keys = bt.rows(batch, rng)
            u, v = enc(bt.patches(e0)), aud(bt.audio(s0))
            loss, st = obj(u, v, keys=keys)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1
            tl.append(float(loss)); gns.append(gn)
        if ep % 5 == 4 or ep == epochs - 1:
            enc.eval(); aud.eval()
            with torch.no_grad():
                el, elr, cs_vals, dm, dx = [], [], [], [], []
                for e0, s0, kk, s0r, kr, s0t, s0tr in es_sets:
                    u = enc(bt.patches(e0)); v = aud(bt.audio(s0)); vr = aud(bt.audio(s0r))
                    l_, st = obj(u, v, keys=kk); el.append(float(l_)); elr.append(float(obj(u, vr, keys=kr)[0]))
                    if "cs_qmi_nats" in st:
                        cs_vals.append(st["cs_qmi_nats"])
                    vt, vtr = (aud(bt.audio(s0t)), aud(bt.audio(s0tr))) if bt.wrong else (v, vr)
                    dm.append(cs_diag(u, vt, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
                    dx.append(cs_diag(u, vtr, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
                es_loss, es_loss_mm = float(np.mean(el)), float(np.mean(elr))
                sel = es_loss - es_loss_mm  # own objective, debiased by the legal mismatch (spec 4.6: raw CS cannot select)
                avg = lambda L, k: float(np.mean([x[k] for x in L]))
                rec = {"epoch": ep + 1, "step": step, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss,
                       "es_loss_mismatched": es_loss_mm, "selection_score": sel,
                       "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1),
                       "es_objective_cs_nats": float(np.mean(cs_vals)) if cs_vals else None,
                       "es_cs_true_nats": avg(dm, "cs_qmi_nats"), "es_cs_mismatched_nats": avg(dx, "cs_qmi_nats"),
                       "es_log_joint_square": avg(dm, "log_joint_square"), "es_log_marginal_product_square": avg(dm, "log_marginal_product_square"),
                       "es_log_cross_overlap": avg(dm, "log_cross_overlap"),
                       "u_eff_rank": _eff_rank(u), "v_eff_rank": _eff_rank(v), "u_norm_mean": float(u.norm(dim=1).mean()),
                       "kernel_u": _kernel_stats(u, obj.sigma_u), "kernel_v": _kernel_stats(v, obj.sigma_v), "lr": float(sched.get_last_lr()[0])}
            curve.append(rec)
            if sel < best[0]:
                best = (sel, ep + 1)
                torch.save({"enc": enc.state_dict(), "aud": aud.state_dict()}, ckpt_prefix + "_best.pt")
            enc.train(); aud.train()
            if (ep + 1) % 20 == 0 and ep + 1 < epochs:
                _save_resume(rpath, enc=enc.state_dict(), aud=aud.state_dict(), opt=opt.state_dict(), sched=sched.state_dict(),
                             rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    torch.save({"enc": enc.state_dict(), "aud": aud.state_dict(), "opt": opt.state_dict()}, ckpt_prefix + "_last.pt")
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": "min over validations of es_loss(training pairing) - es_loss(within-batch roll mismatch)",
                "epochs_completed": epochs, "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit),
                "n_es_segments": len(bt.es), "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1)})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    enc.load_state_dict(sd["enc"]); aud.load_state_dict(sd["aud"]); enc.eval(); aud.eval()
    return enc, aud, bt


def load_continuous(job, coh, dev, ckpt_path):
    """Rebuild a fitted continuous unit from its checkpoint (evaluation-only reruns)."""
    c = job["config"]; d = c.get("projection_dim") or 16
    bt = ContinuousBatcher(coh, job, dev)
    enc = EEGEncoder(coh.n_ch, d, bt.W).to(dev)
    aud = AudioProjection(bt.audio_dim, d, frozen=c.get("audio_projection") == "frozen_initial_projection").to(dev)
    sd = torch.load(ckpt_path, map_location=dev)
    enc.load_state_dict(sd["enc"]); aud.load_state_dict(sd["aud"]); enc.eval(); aud.eval()
    return enc, aud, bt


def load_private_unit(job, kids, dev, ckpt_path):
    c = job["config"]; d = c.get("projection_dim") or 16
    bt = PrivateBatcher(kids, job, dev)
    enc = EEGEncoder(20, d, bt.W).to(dev)
    enc.load_state_dict(torch.load(ckpt_path, map_location=dev)["enc"]); enc.eval()
    return enc, bt


# ------------------------------------------------------------------------------------------------ private category task
class PrivateBatcher:
    """All trials of all children in one GPU tensor; batches are drawn with one gather (32 children x per trials)."""

    def __init__(self, kids, job, dev):
        self.dev = dev
        W = [window_samples("private_bdf", w, 250, pre=50) for w in windows_for(job)]
        lo, hi = min(a for a, _ in W), max(b for _, b in W)
        self.W = [(a - lo, b - lo) for a, b in W]  # epochs cropped to the union of this unit's windows
        self.kids = kids
        self.train = [i for i, k in enumerate(kids) if k["fold"] != job["subject_fold"]]
        self.off = np.cumsum([0] + [len(k["y"]) for k in kids])
        self.Xall = torch.tensor(np.concatenate([k["x"][:, :, lo:hi] for k in kids]), device=dev, dtype=torch.float16)
        yall = np.concatenate([k["y"] for k in kids])
        self.wrong = job["config"].get("pairing") == "training_side_mismatch_preserving_declared_structure"
        if self.wrong:  # labels permuted within child (declared structure: child and class counts preserved)
            r = np.random.default_rng(job["seed"] + 7)
            yall = yall.copy()
            for i in self.train:
                a, b = self.off[i], self.off[i + 1]
                yall[a:b] = yall[a:b][r.permutation(b - a)]
        self.yall = torch.tensor(yall, device=dev)
        self.ytrue = torch.tensor(np.concatenate([k["y"] for k in kids]), device=dev)
        self.fit_idx = {i: self.off[i] + np.flatnonzero(~kids[i]["es_mask"]) for i in self.train}
        self.es_idx = {i: self.off[i] + np.flatnonzero(kids[i]["es_mask"]) for i in self.train}

    def patches(self, i, idx):
        """Patches of child i's local trial indices (used by evaluation)."""
        g = torch.as_tensor(self.off[i], device=self.dev) + idx
        x = self.Xall[g].float()
        return [x[:, :, a:b] for a, b in self.W]

    def batch(self, rng, es=False, n_kids=32, per=8, true_labels=False):
        """Labels follow the unit's training pairing (also on the early-stopping blocks) unless true_labels."""
        src = self.es_idx if es else self.fit_idx
        pool = [i for i in self.train if len(src[i])]
        ks = rng.choice(pool, size=min(n_kids, len(pool)), replace=False)
        g = np.concatenate([src[i][rng.integers(0, len(src[i]), size=per)] for i in ks])
        gt = torch.tensor(g, device=self.dev)
        x = self.Xall[gt].float()
        y = self.ytrue[gt] if true_labels else self.yall[gt]
        return [x[:, :, a:b] for a, b in self.W], y


def fit_private(job, kids, dev, ckpt_prefix, log):
    c = job["config"]
    d = c.get("projection_dim") or 16
    rows = c.get("kernel_rows") or 256
    torch.manual_seed(job["seed"]); rng = np.random.default_rng(job["seed"])
    bt = PrivateBatcher(kids, job, dev)
    enc = EEGEncoder(20, d, bt.W).to(dev)
    protos = torch.nn.Parameter(torch.randn(2, d, device=dev))
    params = list(enc.parameters()) + ([protos] if job["objective"] == "NCE" else [])
    opt = torch.optim.AdamW(params, lr=c.get("learning_rate", 1e-3), weight_decay=c.get("weight_decay", 1e-4))
    epochs = int(c.get("epochs_initial", 200))
    n_fit = sum(int((~kids[i]["es_mask"]).sum()) for i in bt.train)
    steps_per_epoch = max(1, n_fit // rows)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    per = max(1, rows // 32)
    with torch.no_grad():
        P, Y = bt.batch(np.random.default_rng(job["seed"] + 99), per=per)
        obj = Objective(job, enc(P), None, labels0=Y)
    es_batches = [bt.batch(np.random.default_rng(k), es=True, per=per) for k in range(N_SEL)]
    es_true = [bt.batch(np.random.default_rng(k), es=True, per=per, true_labels=True) for k in range(N_SEL)]
    perm_rng = np.random.default_rng(54321)
    pidx = [torch.tensor(perm_rng.permutation(len(Y)), device=dev) for _, Y in es_true]
    es_perm = [Y[q] for (_, Y), q in zip(es_true, pidx)]          # true labels, permuted within batch
    es_tperm = [Y[q] for (_, Y), q in zip(es_batches, pidx)]      # training labels, permuted within batch
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
            u = enc(P)
            loss, st = obj(u, labels=Y, prototypes=protos)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if ep % 5 == 4 or ep == epochs - 1:
            enc.eval()
            with torch.no_grad():
                el = [float(obj(enc(P), labels=Y, prototypes=protos)[0]) for P, Y in es_batches]
                elr = [float(obj(enc(P), labels=Yp, prototypes=protos)[0]) for (P, _), Yp in zip(es_batches, es_tperm)]
                dm, dx = [], []
                for (P, Y), Yp in zip(es_true, es_perm):
                    u = enc(P)
                    dm.append(cs_diag(u, labels=Y, sigma_u=obj.sigma_u)); dx.append(cs_diag(u, labels=Yp, sigma_u=obj.sigma_u))
            es_loss, es_loss_mm = float(np.mean(el)), float(np.mean(elr))
            sel = es_loss - es_loss_mm
            avg = lambda L, k: float(np.mean([x[k] for x in L]))
            curve.append({"epoch": ep + 1, "step": step, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss,
                          "es_loss_mismatched": es_loss_mm, "selection_score": sel,
                          "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1),
                          "es_cs_true_nats": avg(dm, "cs_qmi_nats"), "es_cs_mismatched_nats": avg(dx, "cs_qmi_nats"),
                          "es_log_joint_square": avg(dm, "log_joint_square"), "es_log_marginal_product_square": avg(dm, "log_marginal_product_square"),
                          "es_log_cross_overlap": avg(dm, "log_cross_overlap"), "u_eff_rank": _eff_rank(u), "kernel_u": _kernel_stats(u, obj.sigma_u),
                          "lr": float(sched.get_last_lr()[0])})
            if sel < best[0]:
                best = (sel, ep + 1)
                torch.save({"enc": enc.state_dict(), "protos": protos.detach()}, ckpt_prefix + "_best.pt")
            enc.train()
            if (ep + 1) % 20 == 0 and ep + 1 < epochs:
                _save_resume(rpath, enc=enc.state_dict(), protos=protos.detach(), opt=opt.state_dict(), sched=sched.state_dict(),
                             rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    torch.save({"enc": enc.state_dict(), "protos": protos.detach(), "opt": opt.state_dict()}, ckpt_prefix + "_last.pt")
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": "min over validations of es_loss(training labels) - es_loss(labels permuted within batch)",
                "epochs_completed": epochs, "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_trials": n_fit,
                "n_train_children": len(bt.train), "train_seconds": round(time.time() - t0, 1)})
    enc.load_state_dict(torch.load(ckpt_prefix + "_best.pt", map_location=dev)["enc"]); enc.eval()
    return enc, bt
