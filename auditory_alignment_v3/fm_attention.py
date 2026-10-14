"""ALN3 D_ATTENTION policy arms: foundation-model training on the attention tasks (ADDENDUM_04 §2; package docs/07 §1).

fit_dense_task      the chosen B_DENSE configuration (backbone, adaptation, readout, learning rates, epochs, aln3 recipe:
                    head warm-up, top-down unfreezing, layer-wise decay, validation every epoch) = fm_dense.fit_dense, trained on
                    the row's training task instead of paired alignment.
fit_complement_task the chosen C_COMPLEMENT variant / backbone on top of a frozen lag_local_tokens base (the D_ATTENTION lag
                    arm unit of the same training task, its selected checkpoint) = fm_complement.fit_complement (base kept in
                    eval mode), trained on the row's training task.
Task machinery = auditory_alignment_v3.local_train.fit_continuous (ALN2): competing-speech segments (attended stream as the
paired target); attended_alignment = the unit's objective on the attended stream; selection_only = 2AFC selection loss only
(SelectionScore cosine, bilinear for CS_SINGLE; SELECTION_CE rows calibrate the NCE objective); alignment_plus_selection =
objective + sel_weight x selection loss. Checkpoint = min over validations of es_loss(training pairing) - es_loss(within-batch
roll) (selection_only: min early-stopping 2AFC loss), as fit_continuous; the selection head is saved with the model.
"""
from __future__ import annotations

import math
import os
import time

import numpy as np
import torch

from auditory_alignment.train import Objective, _eff_rank, _save_resume
from auditory_alignment_v2.audio_targets import build_head, target_stats
from auditory_alignment_v2.foundation_adapter import Backbone
from auditory_alignment_v2.temporal import build_encoder
from auditory_alignment_v2.train import N_SEL, ROWS, SelectionScore, selection_loss
from . import fm_complement, fm_dense

Q = 8


def task_rows(bt, batch, rng, roll=False):
    """GridBatcher.rows grouped per segment (as DenseBatcher.dense_rows) keeping the ignored-stream starts and segment index."""
    r = bt.rows(batch, rng, anchors=Q, roll=roll)
    e0 = torch.tensor([bt.coh_segments[i]["e0"] for i in batch], device=bt.dev)
    return {"e0": e0, "t": r[0].reshape(len(batch), Q) - e0[:, None], "s0": r[1], "keys": r[2], "n": len(batch),
            "s0_ign": r[3] if bt.selection else None, "seg": r[4] if bt.selection else None}


def _fit(row, bt, model, head, fwd, groups_bb, allowed, lr_b, lr_h, ad, E, ckpt_prefix, log, sel_weight, d, rng, head_params, base_eval=False):
    spec = row["spec"]; obj_name = spec["objective"]; dev = bt.dev
    task = spec.get("training_task", "paired_alignment"); use_align = task != "selection_only"
    sel = SelectionScore(d, "bilinear" if obj_name == "CS_SINGLE" else "cosine").to(dev) if bt.selection else None
    nb = sum(1 for g in groups_bb if g[0] == "block"); pg = []
    for kind, i, ps in groups_bb:
        ps = [p for p in ps if id(p) in allowed]
        if ps:
            depth = (nb - 1 - i) if kind == "block" else nb
            pg.append({"params": ps, "lr": lr_b * fm_dense.LLRD ** depth, "name": f"{kind}{i}"})
    pg.append({"params": head_params + (list(sel.parameters()) if sel is not None else []), "lr": lr_h, "name": "head"})
    opt = torch.optim.AdamW(pg, weight_decay=1e-4)
    n_seg = max(2, ROWS.get(obj_name, 256) // Q)
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=E * steps_per_epoch)
    obj_job = {"objective": "NCE" if obj_name == "SELECTION_CE" else obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    sw = 1.0 if sel_weight is None else sel_weight

    def set_trainable(ep):
        if not groups_bb:
            return 0
        n_open = 0 if ep < fm_dense.WARMUP else (len(groups_bb) if (ad or "").endswith("peft") else 1 + (ep - fm_dense.WARMUP) // fm_dense.UNFREEZE_EVERY)
        for gi, (kind, i, ps) in enumerate(groups_bb):
            for p in ps:
                p.requires_grad_(id(p) in allowed and gi < n_open)
        return n_open

    def batch_loss(R, rng_l):
        u, v, keys = fwd(R)
        loss, parts = 0.0, {}
        if use_align:
            la, _ = obj(u, v, keys=keys); loss = loss + la; parts["align"] = float(la)
        if sel is not None:
            vi = head(bt.audio(R["s0_ign"]))
            ls, acc = selection_loss(sel, u, v, vi, R["seg"], R["n"], rng_l)
            loss = loss + (sw if use_align else 1.0) * ls; parts["selection"] = float(ls); parts["sel_acc"] = acc
        return loss, parts, u

    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), n_seg))
    with torch.no_grad():
        R0 = task_rows(bt, calib, np.random.default_rng(row["seed"] + 98)); u0, v0, _ = fwd(R0)
        obj = Objective(obj_job, u0, v0)
    es_rng = np.random.default_rng(12345); es_sel = []
    while len(es_sel) < N_SEL:
        got = [b for b, _ in zip(bt.epoch_batches(es_rng, n_seg, bt.es), range(N_SEL - len(es_sel)))]
        if not got:
            break
        es_sel += got
    es_sets = [(task_rows(bt, b, np.random.default_rng(k)), task_rows(bt, b, np.random.default_rng(k), roll=True)) for k, b in enumerate(es_sel)]
    mods = {"model": model, **({"sel": sel} if sel is not None else {})}
    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        for k, m in mods.items():
            m.load_state_dict(r[k])
        opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    for ep in range(ep0, E):
        n_open = set_trainable(ep)
        params = [p for g in pg for p in g["params"] if p.requires_grad]
        for m in mods.values():
            m.train()
        if base_eval:
            model.base.eval()
        tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            loss, _, _ = batch_loss(task_rows(bt, batch, rng), rng)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        for m in mods.values():
            m.eval()
        with torch.no_grad():
            el, elr, accs = [], [], []
            for (a, b) in es_sets:
                l1, parts, u = batch_loss(a, np.random.default_rng(0)); l2, _, _ = batch_loss(b, np.random.default_rng(0))
                el.append(float(l1)); elr.append(float(l2))
                if "sel_acc" in parts:
                    accs.append(parts["sel_acc"])
        es_loss, es_mm = float(np.mean(el)), float(np.mean(elr))
        sel_score = es_loss if not use_align else es_loss - es_mm
        curve.append({"epoch": ep + 1, "step": step, "open_groups": n_open, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss,
                      "es_loss_mismatched": es_mm, "selection_score": sel_score, "es_sel_acc": float(np.mean(accs)) if accs else None,
                      "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1),
                      "u_eff_rank": _eff_rank(u)})
        if sel_score < best[0]:
            best = (sel_score, ep + 1); torch.save({k: m.state_dict() for k, m in mods.items()}, ckpt_prefix + "_best.pt")
        _save_resume(rpath, **{k: m.state_dict() for k, m in mods.items()}, opt=opt.state_dict(), sched=sched.state_dict(), rng=rng.bit_generator.state,
                     torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": ("min es 2AFC loss" if not use_align else "min over validations of es_loss(training pairing) - es_loss(within-batch roll)"),
                "epochs_completed": E, "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit), "n_es_segments": len(bt.es),
                "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1), "training_task": task,
                "selection_weight": sw if bt.selection else None, "lr_backbone": lr_b, "lr_head": lr_h, "param_group_lrs": [g["lr"] for g in pg],
                "trainable_params": int(sum(p.numel() for g in pg for p in g["params"]))})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    for k, m in mods.items():
        m.load_state_dict(sd[k]); m.eval()
    return sel


def fit_dense_task(row, coh, dev, ckpt_prefix, log, chosen_spec, sel_weight=None, d=32, grid=3, epochs=None):
    """row: the bound D_ATTENTION row (spec carries training_task / objective); chosen_spec: the chosen B_DENSE row's spec."""
    arch, ad, readout = chosen_spec["architecture"], chosen_spec["adaptation"], chosen_spec["readout"]
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bb = Backbone(arch, coh.meta["dataset"], ad, coh.fs)
    allowed = {id(p) for p in bb.parameters() if p.requires_grad}
    bt = fm_dense.DenseBatcher(coh, row["spec"], row, dev, grid)
    model = fm_dense.DenseFM(bb, readout, d, coh.fs, bt.seg_len, bt.ctx_len).to(dev)
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(row["seed"] + 5))).to(dev)
    lr_b, lr_h = fm_dense.LR[ad]
    E = epochs or fm_dense.EPOCHS[arch]

    def fwd(R):
        u = model(bt.context(R["e0"]), R["t"].float() / bt.fs).reshape(-1, d)
        return u, head(bt.audio(R["s0"])), R["keys"]
    sel = _fit(row, bt, model, head, fwd, fm_dense.block_groups(bb), allowed, lr_b, lr_h, ad, E, ckpt_prefix, log, sel_weight, d, rng,
               list(model.readout.parameters()))
    log.update({"backbone_contract": bb.contract(), "readout": readout, "adaptation": ad, "architecture": arch, "recipe": "aln3 (fm_dense)",
                "queries_per_segment": Q, "context_after_s": fm_dense.CTX_AFTER_S})
    return model, head, bt, sel


def fit_complement_task(row, coh, dev, ckpt_prefix, log, base_ckpt, chosen_spec, sel_weight=None, d=32, grid=3, epochs=None):
    """row: the bound D_ATTENTION row; base_ckpt: the lag arm twin's selected checkpoint (enc + fixed head); chosen_spec: the
    chosen C_COMPLEMENT row's spec (variant, architecture)."""
    variant, fm_arch = chosen_spec["variant"], chosen_spec["architecture"]
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bspec = dict(row["spec"]); bspec["architecture"] = "lag_local_tokens"; bspec["window"] = "full"
    bt = fm_dense.DenseBatcher(coh, bspec, row, dev, grid)
    base = build_encoder("lag_local_tokens", coh.n_ch, d, bt.W, coh.fs).to(dev)
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(row["seed"] + 5))).to(dev)
    sd = torch.load(base_ckpt, map_location=dev); base.load_state_dict(sd["enc"], strict=True); head.load_state_dict(sd["head"], strict=True)
    base.eval(); head.eval()
    ad, _ = fm_complement.VARIANT_FM[variant]
    bb = Backbone(fm_arch, coh.meta["dataset"], "random_full" if ad == "random_frozen" else ad, coh.fs)
    if ad == "random_frozen":
        for p in bb.parameters():
            p.requires_grad_(False)
    allowed = {id(p) for p in bb.parameters() if p.requires_grad}
    ctx = fm_complement.FMContext(bb, coh.fs, bt.seg_len, bt.ctx_len).to(dev)
    model = fm_complement.Complement(base, ctx, variant, d, base.n_tokens * 32).to(dev)
    lr_b, lr_h = fm_dense.LR.get(ad, (0.0, 1e-3)) if ad != "random_frozen" else (0.0, 1e-3)
    E = epochs or fm_dense.EPOCHS[fm_arch]

    def fwd(R):
        patches = bt.patches((R["e0"][:, None] + R["t"]).reshape(-1))
        return model(patches, bt.context(R["e0"]), R["t"].float() / bt.fs), head(bt.audio(R["s0"])), R["keys"]
    with torch.no_grad():
        R0 = task_rows(bt, next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), max(2, ROWS.get(row["spec"]["objective"], 256) // Q))),
                       np.random.default_rng(row["seed"] + 98))
        u0 = fwd(R0)[0]; b0 = base(bt.patches((R0["e0"][:, None] + R0["t"]).reshape(-1)))
        log["init_max_abs_diff_vs_base"] = float((u0 - b0).abs().max()) if variant != "concat_pretrained" else None
    head_params = [p for n, p in model.named_parameters() if not n.startswith("base.") and not n.startswith("ctx.dfm.bb.")]
    sel = _fit(row, bt, model, head, fwd, fm_dense.block_groups(bb), allowed, lr_b, lr_h, ad, E, ckpt_prefix, log, sel_weight, d, rng,
               head_params, base_eval=True)
    log.update({"variant": variant, "context_branch": fm_arch, "context_adaptation": ad, "base_checkpoint": os.path.basename(base_ckpt),
                "recipe": "C recipe (fm_complement)", "queries_per_segment": Q})
    return model, head, bt, sel
