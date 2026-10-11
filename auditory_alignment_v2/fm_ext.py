"""ALN2 supplementary item 3 (pre-registration docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md, frozen 2026-10-10).

Arms (plan rows in private/auditory_alignment_v2/plan_item3.jsonl, built by --make-plan from the seed-3401 B_FM rows):
  X_READOUT_DIAG  evaluation only: reload a completed B_FM unit's best checkpoint and add the unified ridge readout of the
                  spatial components z (K x e = 256 per patch, before the readout's LayerNorm / 16-d map).
  X_FT_VAL        the B_FM recipe, validated every epoch (finer checkpoint selection).
  X_FT_REG        X_FT_VAL + layer-wise learning-rate decay 0.75 (top transformer block = backbone lr; x0.75 per block
                  downwards; parameters outside the blocks get the lowest value) and backbone / head learning rates
                  re-selected on the development cell from the downward-extended grid (fm_recipe_ext/).
  X_PHASE         the B_FM recipe; each training batch uses one phase offset o in {0, .25, .5, .75} s: EEG cropped from
                  e0 + o (whole backbone patches), each patch's audio window shifted by o. Validation / evaluation at o = 0.
Everything else (data, folds, targets, candidates, readout head, objective, checkpoint rule, evaluation, channel probe) is
the B_FM path. New code lives here only, so the code hashes of the running item-2 units are unchanged.

Usage: python -m auditory_alignment_v2.fm_ext --make-plan
       python -m auditory_alignment_v2.fm_ext --job-index <i>          (row i of plan_item3.jsonl)
       python -m auditory_alignment_v2.fm_ext --lr-select <arch>|<adaptation>|<dataset>|NCE
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import traceback

import numpy as np
import torch

from auditory_alignment.train import Objective, _eff_rank, _save_resume, cs_diag
from .fm_readout import HEAD_VERSION, channel_probe_segments
from .foundation_adapter import Backbone
from .run import OUT, PLAN, REPO, load_cohort
from .run_fm import DEV_CELL, FM_CODE, LR_SEL_EPOCHS, _probe, epochs_for, recipe_dir
from .train import N_SEL
from .train_fm import BIN, LEAD_S, FMEncoder, SegmentAudioHead, SegmentBatcher, param_groups, seg_target_stats

PLAN_X = os.path.join(OUT, "plan_item3.jsonl")
X_OFFSET = 100000  # queue index offset that routes a line to this module (dispatch.py)
LLRD = 0.75
PHASES = (0.0, 0.25, 0.5, 0.75)
GRID_X = {"full": [(b, h) for b in (1e-6, 3e-6, 1e-5, 3e-5) for h in (1e-4, 1e-3)],
          "partial": [(b, h) for b in (1e-6, 3e-6, 1e-5, 3e-5) for h in (1e-4, 1e-3)],
          "peft": [(b, h) for b in (3e-5, 1e-4, 3e-4) for h in (1e-4, 1e-3)]}
ARMS = {"X_FT_VAL": {"val_every": 1}, "X_FT_REG": {"val_every": 1, "llrd": LLRD}, "X_PHASE": {"phases": PHASES}}
EXT_CODE = FM_CODE + [("auditory_alignment_v2", "fm_ext.py")]


def code_hash():
    h = hashlib.sha256()
    for d, f in EXT_CODE:
        h.update(open(os.path.join(REPO, d, f), "rb").read())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------------------------------------ building blocks
def build_segments(row, coh, dev, adaptation):
    """The B_FM setup without training: backbone + repaired readout, batcher, fixed audio head (same seeds as fit_segments)."""
    spec = row["spec"]
    torch.manual_seed(row["seed"])
    bb = Backbone(spec["architecture"], coh.meta["dataset"], adaptation, coh.fs)
    enc = FMEncoder(bb).to(dev)
    bt = SegmentBatcher(coh, spec, row, dev, bb.patch_starts(int(round(coh.meta["seg_len"] * 200 / coh.fs))))
    stats = seg_target_stats(bt, np.random.default_rng(row["seed"] + 5))
    head = SegmentAudioHead(bt.nbin * bt.S.shape[0], 16, *stats, coh.meta["dataset"]).to(dev)
    return enc, head, bt


def phase_geometry(bt, bb, o):
    """(EEG sample offset, crop length, per-patch audio offsets) for phase o seconds."""
    off_e = int(round(o * bt.fs)); L = bt.seg_len - off_e
    starts = bb.patch_starts(int(round(L * 200 / bt.fs)))
    return off_e, L, [int(round((a + o - LEAD_S) * bt.fs)) for a in starts]


def segments_at(bt, e_idx, off_e, L):
    return bt.E[:, (e_idx[:, None] + off_e + torch.arange(L, device=bt.dev)[None])].permute(1, 0, 2).float()


def audio_at(bt, s_idx, offs):
    out = []
    for o in offs:
        fr = bt.S[:, ((s_idx + o)[:, None] + torch.arange(bt.nbin * BIN, device=bt.dev)[None])]
        fr = fr.reshape(fr.shape[0], fr.shape[1], bt.nbin, BIN).mean(-1)
        out.append(fr.permute(1, 2, 0).flatten(1))
    return torch.stack(out, 1)


def llrd_groups(enc, lr_backbone, lr_head, decay):
    bb = enc.bb; n = len(bb.blocks); block_of = {}
    for i, blk in enumerate(bb.blocks):
        for p in blk.parameters():
            block_of[id(p)] = i
    by_lr = {}
    for p in bb.parameters():
        if p.requires_grad:
            i = block_of.get(id(p))
            lr = lr_backbone * decay ** (n - 1 - i) if i is not None else lr_backbone * decay ** n
            by_lr.setdefault(lr, []).append(p)
    groups = [{"params": v, "lr": k} for k, v in sorted(by_lr.items())]
    groups.append({"params": [p for p in enc.head.parameters() if p.requires_grad], "lr": lr_head})
    return groups, [p for g in groups for p in g["params"]]


def fit_ext(row, coh, dev, ckpt_prefix, log, lr_backbone, lr_head, epochs, adaptation, val_every=None, llrd=None, phases=None, n_seg=32):
    """fit_segments (paired alignment, no selection head) with the item-3 switches; all switches off = the B_FM path."""
    spec = row["spec"]; obj_name = spec["objective"]
    enc, head, bt = build_segments(row, coh, dev, adaptation)
    rng = np.random.default_rng(row["seed"]); prng = np.random.default_rng(row["seed"] + 7777)  # phase draws: own generator
    groups, params = llrd_groups(enc, lr_backbone, lr_head, llrd) if llrd else param_groups(enc, lr_backbone, lr_head)
    opt = torch.optim.AdamW(groups, weight_decay=1e-4)
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    obj_job = {"objective": obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    geom = {o: phase_geometry(bt, enc.bb, o) for o in (phases or (0.0,))}
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

    def loss_of(rws, enc_out=None, o=0.0):
        if o == 0.0:
            U = enc(bt.segments(rws[0])) if enc_out is None else enc_out
            V = head(bt.audio_patches(rws[1])); P = U.shape[1]
            keys = rws[2]
        else:
            off_e, L, offs = geom[o]
            U = enc(segments_at(bt, rws[0], off_e, L)); V = head(audio_at(bt, rws[1], offs)); P = U.shape[1]
            assert P == len(offs), (P, len(offs))
            keys = (rws[2].reshape(-1, len(bt.starts))[:, :1] + torch.arange(P, device=bt.dev)[None]).reshape(-1)  # (stimulus, patch) keys
        u, v = U.reshape(-1, 16), V.reshape(-1, 16)
        la, _ = obj(u, v, keys=keys)
        return la, u, v

    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        enc.load_state_dict(r["enc"]); opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; prng.bit_generator.state = r["prng"]; torch.set_rng_state(r["torch_rng"].cpu())
        best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        log["resumed_from_epoch"] = ep0
    ve = val_every or max(1, epochs // 20)
    phase_counts = {str(o): 0 for o in geom}
    for ep in range(ep0, epochs):
        enc.train(); tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            o = float(prng.choice(list(geom))) if phases else 0.0
            phase_counts[str(o)] += 1
            loss, _, _ = loss_of(bt.seg_rows(batch), o=o)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if (ep + 1) % ve == 0 or ep == epochs - 1:
            enc.eval()
            with torch.no_grad():
                el, elr, dm, dx = [], [], [], []
                for b in es_sel:
                    rws, rr = bt.seg_rows(b), bt.seg_rows(b, roll=True)
                    eo = enc(bt.segments(rws[0]))
                    l1, u, v = loss_of(rws, eo); l2, _, vr = loss_of(rr, eo)
                    el.append(float(l1)); elr.append(float(l2))
                    dm.append(cs_diag(u, v, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v)); dx.append(cs_diag(u, vr, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
            es_loss, es_mm = float(np.mean(el)), float(np.mean(elr)); selsc = es_loss - es_mm
            curve.append({"epoch": ep + 1, "step": step, "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss, "es_loss_mismatched": es_mm,
                          "selection_score": selsc, "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin,
                          "seconds": round(time.time() - t0, 1), "es_cs_true_nats": float(np.mean([x["cs_qmi_nats"] for x in dm])),
                          "es_cs_mismatched_nats": float(np.mean([x["cs_qmi_nats"] for x in dx])), "u_eff_rank": _eff_rank(u)})
            if selsc < best[0]:
                best = (selsc, ep + 1); torch.save({"enc": enc.state_dict()}, ckpt_prefix + "_best.pt")
            _save_resume(rpath, enc=enc.state_dict(), opt=opt.state_dict(), sched=sched.state_dict(), rng=rng.bit_generator.state,
                         prng=prng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1)
    if os.path.exists(rpath):
        os.remove(rpath)
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": "min over validations of es_loss(training pairing) - es_loss(within-batch roll)", "epochs_completed": epochs,
                "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit), "n_es_segments": len(bt.es),
                "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1), "backbone_contract": enc.bb.contract(),
                "patch_starts_s": bt.starts, "lr_backbone": lr_backbone, "lr_head": lr_head, "val_every": ve, "llrd": llrd,
                "phases": list(phases) if phases else None, "phase_batches": phase_counts if phases else None,
                "phase_patches": {str(o): len(g[2]) for o, g in geom.items()},
                "param_group_lrs": sorted({float(g["lr"]) for g in groups}), "n_param_groups": len(groups)})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    enc.load_state_dict(sd["enc"]); enc.eval()
    return enc, head, bt


# ------------------------------------------------------------------------------------------------ 3a: spatial-component readout
class SpatialReps:
    """eval_fm.SegmentReps interface; u() returns the readout's spatial components z [n, T, K*e] (before LayerNorm)."""

    def __init__(self, enc, head, bt, chunk=32):
        self.enc, self.head, self.bt, self.chunk = enc, head, bt, chunk

    @torch.no_grad()
    def u(self, e0s):
        e0s = np.asarray(e0s); out = []
        h = self.enc.head
        for a in range(0, len(e0s), self.chunk):
            tok = self.enc.bb(self.bt.segments(torch.tensor(e0s[a:a + self.chunk], device=self.bt.dev)))
            out.append(torch.einsum("kc,bcte->btke", h.W, h.proj(tok)).flatten(2).float().cpu().numpy())
        return np.concatenate(out)

    @torch.no_grad()
    def va(self, s0s):
        s0s = np.asarray(s0s); v, a = [], []
        for k in range(0, len(s0s), self.chunk):
            A = self.bt.audio_patches(torch.tensor(s0s[k:k + self.chunk], device=self.bt.dev))
            a.append(A.cpu().numpy()); v.append(self.head(A).cpu().numpy())
        return np.concatenate(v), np.concatenate(a)


def run_diag(row, out, rec):
    from .eval_fm import evaluate_segments
    base = row["base_unit"]; bp = os.path.join(out, "units", f"{base}.json")
    b = json.load(open(bp))
    if b.get("reuse_of"):
        base = b["reuse_of"]; b = json.load(open(os.path.join(out, "units", f"{base}.json")))
    assert str(b.get("readout_head", "")).startswith("spatial_signed"), base
    dev = torch.device("cuda")
    coh = load_cohort(row)
    enc, head, bt = build_segments(row, coh, dev, row["spec"]["adaptation"])
    enc.load_state_dict(torch.load(os.path.join(out, "ckpt", f"{base}_best.pt"), map_location=dev)["enc"], strict=True); enc.eval()
    ev = evaluate_segments(row, enc, head, bt, coh, b["objective_calibration"], reps=SpatialReps(enc, head, bt), readouts=("unified",), dependence=False)
    ren = lambda d: {k.replace("unified", "spatial"): v for k, v in d.items()}
    rec["eval"] = {"spatial_readout": {"per_participant": {p: ren(v) for p, v in ev["per_participant"].items()},
                                       "readout": {"alpha_spatial": ev["readout"]["alpha_unified"], "tau_spatial": ev["readout"]["tau"].get("unified")}}}
    if "attention_2afc" in ev:
        rec["eval"]["spatial_readout"]["attention_2afc"] = {p: ren(v) for p, v in ev["attention_2afc"].items()}
    rec.update({"base_unit_resolved": base, "base_code_hash": b.get("code_hash"), "base_readout_head": b.get("readout_head"),
                "spatial_dim": int(enc.head.W.shape[0] * enc.head.proj.out_features)})


# ------------------------------------------------------------------------------------------------ units
def recipe_x(row, out=OUT):
    s = row["spec"]; depth = s["adaptation"].split("_")[-1]
    p = os.path.join(out, "fm_recipe_ext", f"{s['architecture']}__pretrained_{depth}__{row['dataset']}__{s['objective']}.json")
    return (json.load(open(p))["chosen"], p) if os.path.exists(p) else (None, p)


def run_unit(row, out=OUT):
    from .eval_fm import evaluate_segments
    eid = row["experiment_id"]; path = os.path.join(out, "units", f"{eid}.json")
    if os.path.exists(path):
        print("skip", eid); return
    fam = row["family_id"]
    os.makedirs(os.path.join(out, "units"), exist_ok=True); os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    t0 = time.time()
    rec = {"experiment_id": eid, "row": row, "code_hash": code_hash(), "runner": "fm_ext", "status": "running", "readout_head": HEAD_VERSION,
           "prereg": "docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md", "device": torch.cuda.get_device_name(0)}
    try:
        if fam == "X_READOUT_DIAG":
            run_diag(row, out, rec)
        else:
            if fam == "X_FT_REG":
                lr, rf = recipe_x(row, out)
                if lr is None:
                    print("technical_pending (item-3 recipe unresolved)", eid); return
            else:
                rf = os.path.join(recipe_dir(out), f"{row['spec']['architecture']}__{row['spec']['adaptation']}__{row['dataset']}__{row['spec']['objective']}.json")
                lr = json.load(open(rf))["chosen"]
            E = epochs_for(row["spec"]["architecture"], out)
            rec["resolved_config"] = {"epochs": E, **lr, "recipe_file": os.path.relpath(rf, REPO), "arm": ARMS[fam]}
            log = {}
            coh = load_cohort(row)
            enc, head, bt = fit_ext(row, coh, torch.device("cuda"), os.path.join(out, "ckpt", eid), log, lr["lr_backbone"], lr["lr_head"], E,
                                    row["spec"]["adaptation"], **ARMS[fam])
            rec.update(log)
            rec["eval"] = evaluate_segments(row, enc, head, bt, coh, log["objective_calibration"])
            _probe(rec, lambda: channel_probe_segments(row, enc, head, bt, coh, log["objective_calibration"]))
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001 - recorded, never hidden
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    rec["total_seconds"] = round(time.time() - t0, 1); rec["gpu_peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
    p = path if rec["status"] == "complete" else path.replace(".json", ".FAILED.json")
    json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
    print(eid, rec["status"], rec["total_seconds"], rec.get("error", ""), flush=True)
    if rec["status"] != "complete":
        raise SystemExit(1)


def lr_select(key, out=OUT, epochs=None):
    """X_FT_REG recipe: dev cell, 20 epochs, layer-wise decay, validation every epoch; candidate states deleted after scoring."""
    arch, adaptation, dataset, objective = key.split("|")
    rx = os.path.join(out, "fm_recipe_ext"); os.makedirs(rx, exist_ok=True)
    path = os.path.join(rx, key.replace("|", "__") + ".json")
    marker = os.path.join(out, "units", "LRX__" + key.replace("|", "__") + ".json")
    if os.path.exists(path):
        print("skip", key)
    else:
        E = epochs or LR_SEL_EPOCHS
        row = {"experiment_id": "LRX_" + key.replace("|", "_"), "dataset": dataset, **DEV_CELL,
               "spec": {"architecture": arch, "adaptation": adaptation, "objective": objective,
                        "target": {"federici": "envelope"}.get(dataset, "local"), "training_task": "paired_alignment"}}
        res = {"key": key, "dev_cell": DEV_CELL, "epochs": E, "code_hash": code_hash(), "readout_head": HEAD_VERSION, "llrd": LLRD,
               "val_every": 1, "prereg": "docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md", "candidates": []}
        for lr_b, lr_h in GRID_X[adaptation.split("_")[-1]]:
            log = {}; t0 = time.time()
            ck = os.path.join(out, "ckpt", "lrsel", f"X__{key.replace('|', '__')}__{lr_b:g}__{lr_h:g}")
            os.makedirs(os.path.dirname(ck), exist_ok=True)
            try:
                fit_ext(row, load_cohort(row), torch.device("cuda"), ck, log, lr_b, lr_h, E, adaptation, val_every=1, llrd=LLRD)
                res["candidates"].append({"lr_backbone": lr_b, "lr_head": lr_h, "score": log["best_selection_score"], "best_epoch": log["best_epoch"],
                                          "curve": log["curve"], "seconds": round(time.time() - t0, 1)})
            except Exception as ex:  # noqa: BLE001
                res["candidates"].append({"lr_backbone": lr_b, "lr_head": lr_h, "error": f"{type(ex).__name__}: {ex}", "traceback": traceback.format_exc()[-2000:]})
            for suf in ("_best.pt", "_resume.pt"):
                if os.path.exists(ck + suf):
                    os.remove(ck + suf)
            torch.cuda.empty_cache()
        ok = [c for c in res["candidates"] if "score" in c and np.isfinite(c["score"])]
        if not ok:
            json.dump(res, open(path.replace(".json", ".FAILED.json"), "w"), default=float); raise SystemExit(1)
        best = min(ok, key=lambda c: c["score"])
        res["chosen"] = {"lr_backbone": best["lr_backbone"], "lr_head": best["lr_head"]}
        json.dump(res, open(path + ".tmp", "w"), default=float); os.replace(path + ".tmp", path)
        print(key, "chosen", res["chosen"])
    os.makedirs(os.path.dirname(marker), exist_ok=True)
    json.dump({"experiment_id": os.path.basename(marker)[:-5], "status": "complete", "kind": "item3_recipe_marker"}, open(marker, "w"))


def make_plan():
    rows = [json.loads(l) for l in open(PLAN)]
    out = []
    def xrow(fam, r):
        h = hashlib.sha256((fam + "|" + r["experiment_id"]).encode()).hexdigest()[:16]
        return {**{k: r[k] for k in ("dataset", "spec", "subject_fold", "content_fold", "seed")}, "experiment_id": f"ALN2X_{fam[2:]}_{r['dataset']}_{h}",
                "family_id": fam, "base_unit": r["experiment_id"], "module": "X", "prereg": "docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md"}
    b = [r for r in rows if r["family_id"] == "B_FM" and r["seed"] == 3401]
    out += [xrow("X_READOUT_DIAG", r) for r in b]
    for fam, ads in (("X_FT_VAL", ("pretrained_full", "pretrained_partial", "pretrained_peft")), ("X_FT_REG", ("pretrained_full", "pretrained_partial", "pretrained_peft")),
                     ("X_PHASE", ("pretrained_frozen", "pretrained_peft"))):
        out += [xrow(fam, r) for r in b if r["spec"]["objective"] == "NCE" and r["spec"]["adaptation"] in ads]
    assert len({r["experiment_id"] for r in out}) == len(out)
    open(PLAN_X + ".tmp", "w").write("".join(json.dumps(r) + "\n" for r in out)); os.replace(PLAN_X + ".tmp", PLAN_X)
    from collections import Counter
    print(len(out), "rows", dict(Counter(r["family_id"] for r in out)))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--job-index", type=int); a.add_argument("--lr-select"); a.add_argument("--make-plan", action="store_true"); a.add_argument("--out", default=OUT)
    args = a.parse_args()
    if args.make_plan:
        return make_plan()
    if args.lr_select:
        return lr_select(args.lr_select, args.out)
    run_unit([json.loads(l) for l in open(PLAN_X)][args.job_index], args.out)


if __name__ == "__main__":
    main()
