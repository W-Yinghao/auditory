"""ALN2 D_LOCAL_DISTILL: a restricted-window student (lag_local_tokens) learns the private current-class task with a
distillation term toward a frozen teacher (package docs/04 §4.7).

Teacher: the D_FM_PUBLIC unit (same architecture family 'cbramod_auditory' / 'reve_auditory', adaptation
auditory_pretrained_full, same objective, outer fold and seed): public auditory donor -> private full-epoch fine-tuning on
the same training children, so it never saw the student's test children. Distillation object (one, fixed): the teacher's
16-d L2-normalised trial embedding; student loss = class objective + lambda * mean(1 - cos(W u_student, u_teacher)), W a
trainable 16 x 16 map. lambda in {0.1, 1.0} chosen on the training side (early-stopping selection score). At inference
the student uses only its own window; the teacher is not used.
"""
from __future__ import annotations

import math
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from auditory_alignment.train import Objective, _save_resume
from .foundation_adapter import Backbone
from .temporal import build_encoder, describe
from .train import N_SEL, ROWS, PrivateBatcher
from .train_fm import EpochEncoder


def load_teacher(arch, ckpt, dev):
    bb = Backbone(arch, "private_bdf", "auditory_pretrained_full", 250)
    enc = EpochEncoder(bb).to(dev)
    enc.load_state_dict(torch.load(ckpt, map_location=dev)["enc"]); enc.eval()
    for p in enc.parameters():
        p.requires_grad_(False)
    return enc


def fit_private_distill(row, kids, dev, ckpt_prefix, log, teacher_arch, teacher_ckpt, lam, epochs=200):
    spec = dict(row["spec"]); obj_name = spec["objective"]
    rows = ROWS.get(obj_name, 256); per = max(1, rows // 32)
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bt = PrivateBatcher(kids, spec, row, dev)
    full = torch.tensor(np.concatenate([k["x"] for k in kids]), device=dev, dtype=torch.float16)  # teacher input: full epochs
    teacher = load_teacher(teacher_arch, teacher_ckpt, dev)
    enc = build_encoder("lag_local_tokens", 20, 16, bt.W, 250).to(dev)
    Wd = nn.Linear(16, 16, bias=False).to(dev)
    protos = nn.Parameter(torch.randn(2, 16, device=dev))
    params = list(enc.parameters()) + list(Wd.parameters()) + ([protos] if obj_name == "NCE" else [])
    opt = torch.optim.AdamW(params, lr=1e-3, weight_decay=1e-4)
    n_fit = sum(len(bt.fit_idx[i]) for i in bt.train); steps_per_epoch = max(1, n_fit // rows)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    obj_job = {"objective": obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}

    def draw(rng_, es=False, true_labels=False):
        src = bt.es_idx if es else bt.fit_idx
        pool = [i for i in bt.train if len(src[i])]
        ks = rng_.choice(pool, size=min(32, len(pool)), replace=False)
        g = torch.tensor(np.concatenate([src[i][rng_.integers(0, len(src[i]), size=per)] for i in ks]), device=dev)
        x = bt.Xall[g].float()
        return [x[:, :, a:b] for a, b in bt.W], (bt.ytrue[g] if true_labels else bt.yall[g]), g

    @torch.no_grad()
    def teach(g):
        return teacher([full[g].float()])

    with torch.no_grad():
        Pb, Y, _ = draw(np.random.default_rng(row["seed"] + 99))
        obj = Objective(obj_job, enc(Pb), None, labels0=Y)
    es_batches = [draw(np.random.default_rng(k), es=True) for k in range(N_SEL)]
    perm_rng = np.random.default_rng(54321)
    es_perm = [Y[torch.tensor(perm_rng.permutation(len(Y)), device=dev)] for _, Y, _ in es_batches]
    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        enc.load_state_dict(r["enc"]); Wd.load_state_dict(r["Wd"]); protos.data.copy_(r["protos"]); opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    for ep in range(ep0, epochs):
        enc.train(); tl, dl = [], []
        for _ in range(steps_per_epoch):
            Pb, Y, g = draw(rng)
            u = enc(Pb)
            lc, _ = obj(u, labels=Y, prototypes=protos)
            ld = (1 - F.cosine_similarity(Wd(u), teach(g), dim=1)).mean()
            loss = lc + lam * ld
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(params, 5.0)
            if torch.isfinite(loss):
                opt.step(); sched.step(); step += 1; tl.append(float(lc)); dl.append(float(ld))
        if ep % 5 == 4 or ep == epochs - 1:
            enc.eval()
            with torch.no_grad():
                el = [float(obj(enc(Pb), labels=Y, prototypes=protos)[0]) for Pb, Y, _ in es_batches]
                elr = [float(obj(enc(Pb), labels=Yp, prototypes=protos)[0]) for (Pb, _, _), Yp in zip(es_batches, es_perm)]
            sel = float(np.mean(el)) - float(np.mean(elr))
            curve.append({"epoch": ep + 1, "step": step, "class_loss": float(np.mean(tl)) if tl else None, "distill_loss": float(np.mean(dl)) if dl else None,
                          "es_loss": float(np.mean(el)), "es_loss_mismatched": float(np.mean(elr)), "selection_score": sel, "seconds": round(time.time() - t0, 1)})
            if sel < best[0]:
                best = (sel, ep + 1); torch.save({"enc": enc.state_dict(), "protos": protos.detach()}, ckpt_prefix + "_best.pt")
            enc.train()
            if (ep + 1) % 20 == 0 and ep + 1 < epochs:
                _save_resume(rpath, enc=enc.state_dict(), Wd=Wd.state_dict(), protos=protos.detach(), opt=opt.state_dict(), sched=sched.state_dict(),
                             rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0], "distill_weight": lam,
                "selection_rule": "min over validations of es_loss(training labels) - es_loss(labels permuted within batch)", "epochs_completed": epochs,
                "optimizer_steps": step, "encoder": describe(enc), "windows_samples_from_epoch_start": [[a + bt.lo, b + bt.lo] for a, b in bt.W],
                "teacher": {"arch": teacher_arch, "ckpt": os.path.basename(teacher_ckpt)}, "train_seconds": round(time.time() - t0, 1)})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    enc.load_state_dict(sd["enc"]); protos.data.copy_(sd["protos"]); enc.eval()
    return enc, bt, protos
