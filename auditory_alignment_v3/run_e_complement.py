"""ALN3 E_COMPLEMENT runner (see private_stage.py for the definition)."""
from __future__ import annotations

import json
import math
import os
import time
import traceback

import numpy as np
import torch
import torch.nn.functional as F

from . import core, private_stage as PS

VARIANT_AD = {"residual_pretrained_frozen": "pretrained_frozen", "residual_pretrained_peft": "pretrained_peft", "residual_random_trainable": "random_full"}
BATCH = 256


def base_row(row, rows):
    s = row["spec"]
    return next((r for r in rows if r["family_id"] == "E_LOCAL" and r["subject_fold"] == row["subject_fold"] and r["seed"] == row["seed"]
                 and r["spec"]["objective"] == s["objective"] and r["spec"]["architecture"] == s.get("local_architecture", "lag_local_tokens")
                 and r["spec"]["window"] == "full"), None)


def base_ready(row, rows, out):
    b = base_row(row, rows)
    if b is None:
        return None
    p = os.path.join(out, "units", f"{b['experiment_id']}.json")
    return b if os.path.exists(p) and json.load(open(p)).get("status") == "complete" and os.path.exists(os.path.join(out, "ckpt", f"{b['experiment_id']}_best.pt")) else None


def run(row, out, epochs=None):
    from auditory_alignment import data
    from auditory_alignment.train import _save_resume
    from auditory_alignment_v2.foundation_adapter import Backbone
    from auditory_alignment_v2.train_fm import PrivateFMBatcher
    from . import fm_dense
    from .aln3_reference.readouts import ChannelSpatialProjection, ZeroResidualPrediction
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    brow = base_ready(row, core.load_rows(), out)
    if brow is None:
        print("technical_pending (same-fold private local base not complete)", row["experiment_id"]); return
    s = row["spec"]; arch, ad = s["architecture"], VARIANT_AD[s["variant"]]
    b = core.bind(row); dev = torch.device("cuda"); t0 = time.time(); rec = core.new_record(row, b, out)
    rec["dependency"] = {"private_local_base_same_fold": brow["experiment_id"]}
    try:
        torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
        kids = data.load_private()
        enc_b, protos, brec, bt_l = PS.rebuild(brow["experiment_id"], kids, dev)
        tr = bt_l.train; te = [i for i, k in enumerate(kids) if k["fold"] == row["subject_fold"]]
        S = PS.native_scores(enc_b, protos.to(dev) if protos is not None else None, brec, bt_l, kids, tr + te)
        cal = PS.calibrator(S, kids, tr)
        from auditory_alignment.evaluate import _private_reps
        with torch.no_grad():
            U = {i: _private_reps(enc_b, bt_l, i) for i in tr + te}
        off = bt_l.off
        Uall = torch.zeros(off[-1], U[tr[0]].shape[1], device=dev); Lall = torch.zeros(off[-1], device=dev)
        for i in tr + te:
            Uall[off[i]:off[i + 1]] = torch.tensor(U[i], device=dev); Lall[off[i]:off[i + 1]] = torch.tensor(cal.logits(S[i]), device=dev, dtype=torch.float32)
        y = torch.tensor(np.concatenate([k["y"] for k in kids]), device=dev).float()
        bspec = dict(b["spec"]); bspec["architecture"] = arch
        bt_f = PrivateFMBatcher(kids, bspec, b, dev)
        bb = Backbone(arch, "private_bdf", ad, 250).to(dev)
        allowed = {id(p) for p in bb.parameters() if p.requires_grad}
        proj = ChannelSpatialProjection(len(bb.channel_names), bb.E, hidden=64).to(dev)
        res = ZeroResidualPrediction(U[tr[0]].shape[1], 64, 1).to(dev)
        lr_b, lr_h = fm_dense.LR[ad]; groups_bb = fm_dense.block_groups(bb); nb = sum(1 for g in groups_bb if g[0] == "block"); pg = []
        for kind, gi, ps in groups_bb:
            ps = [p for p in ps if id(p) in allowed]
            if ps:
                pg.append({"params": ps, "lr": lr_b * fm_dense.LLRD ** ((nb - 1 - gi) if kind == "block" else nb)})
        pg.append({"params": list(proj.parameters()) + list(res.parameters()), "lr": lr_h})
        opt = torch.optim.AdamW(pg, weight_decay=1e-4)
        fit_idx = np.concatenate([bt_l.fit_idx[i] for i in tr]); es_idx = np.concatenate([bt_l.es_idx[i] for i in tr])
        E = epochs or fm_dense.EPOCHS[arch]; spe = max(1, len(fit_idx) // BATCH)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=E * spe)

        def fwd(g):
            g = torch.as_tensor(g, device=dev)
            ctx = proj(bb(bt_f.Xall[g].float()))[:, 0]
            return res(Lall[g][:, None], Uall[g], ctx)[:, 0]

        def set_trainable(ep):
            n_open = 0 if ep < fm_dense.WARMUP else (len(groups_bb) if ad.endswith("peft") else 1 + (ep - fm_dense.WARMUP) // fm_dense.UNFREEZE_EVERY)
            for k, (kind, gi, ps) in enumerate(groups_bb):
                for p in ps:
                    p.requires_grad_(id(p) in allowed and k < n_open)
            return n_open
        with torch.no_grad():
            init_diff = float((fwd(es_idx[:512]) - Lall[torch.as_tensor(es_idx[:512], device=dev)]).abs().max())
        best, curve, ckp, ep0 = (math.inf, -1), [], os.path.join(out, "ckpt", f"{row['experiment_id']}_best.pt"), 0
        rpath = os.path.join(out, "ckpt", f"{row['experiment_id']}_resume.pt")
        if os.path.exists(rpath):  # runfill preemption: continue from the last completed epoch
            r = torch.load(rpath, map_location=dev, weights_only=False)
            bb.load_state_dict(r["bb"]); proj.load_state_dict(r["proj"]); res.load_state_dict(r["res"]); opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
            rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, curve, ep0 = tuple(r["best"]), r["curve"], r["epoch"]
            rec["resumed_from_epoch"] = ep0
        for ep in range(ep0, E):
            n_open = set_trainable(ep); bb.train(); proj.train(); res.train(); tl = []
            perm = rng.permutation(fit_idx)
            for k in range(spe):
                g = perm[k * BATCH:(k + 1) * BATCH]
                loss = F.binary_cross_entropy_with_logits(fwd(g), y[torch.as_tensor(g, device=dev)])
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_([p for gp in pg for p in gp["params"] if p.requires_grad], 5.0); opt.step(); sched.step(); tl.append(float(loss))
            bb.eval(); proj.eval(); res.eval()
            with torch.no_grad():
                el = float(np.mean([F.binary_cross_entropy_with_logits(fwd(es_idx[j:j + 1024]), y[torch.as_tensor(es_idx[j:j + 1024], device=dev)]).item() for j in range(0, len(es_idx), 1024)]))
            curve.append({"epoch": ep + 1, "open_groups": n_open, "train_bce": float(np.mean(tl)), "es_bce": el})
            if el < best[0]:
                best = (el, ep + 1); torch.save({"bb": bb.state_dict(), "proj": proj.state_dict(), "res": res.state_dict()}, ckp)
            _save_resume(rpath, bb=bb.state_dict(), proj=proj.state_dict(), res=res.state_dict(), opt=opt.state_dict(), sched=sched.state_dict(),
                         rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), curve=curve, epoch=ep + 1)
        if os.path.exists(rpath):
            os.remove(rpath)
        sd = torch.load(ckp, map_location=dev); bb.load_state_dict(sd["bb"]); proj.load_state_dict(sd["proj"]); res.load_state_dict(sd["res"]); bb.eval(); proj.eval(); res.eval()
        with torch.no_grad():
            Z = {i: torch.cat([fwd(np.arange(off[i], off[i + 1])[j:j + 1024]) for j in range(0, off[i + 1] - off[i], 1024)]).cpu().numpy() for i in tr + te}
        cal2 = PS.calibrator(Z, kids, tr)
        base_rate = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
        per = {kids[i]["id"]: {"combined": PS.metrics(cal2.predict(Z[i]), kids[i]["y"], base_rate), "local_only": PS.metrics(cal.predict(S[i]), kids[i]["y"], base_rate),
                               "group": kids[i]["group"]} for i in te}
        rec.update({"curve": curve, "best_epoch": best[1], "best_es_bce": best[0], "init_max_abs_logit_diff_vs_base": init_diff, "epochs_completed": E,
                    "variant": s["variant"], "context_adaptation": ad, "lr_backbone": lr_b, "lr_head": lr_h, "backbone_contract": bb.contract(),
                    "calibration": {"base": cal.to_dict(), "combined": cal2.to_dict()}, "objective_calibration": brec["objective_calibration"]})
        rec["eval"] = {"per_participant": per, "base_rate": base_rate, "readout": "positive affine on training children's early-stopping blocks"}
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
