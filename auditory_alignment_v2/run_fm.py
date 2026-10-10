"""ALN2 foundation-model runner (module B, and the foundation arms of D). Usage:
  python -m auditory_alignment_v2.run_fm --job-index <i> [--manifest PLAN] [--epochs N] [--out DIR]
  python -m auditory_alignment_v2.run_fm --lr-select <arch>|<adaptation>|<dataset>|<objective> [--epochs N]

Learning rates are chosen on the training side (package study.json: 'training_side_task_validation'): every candidate is
trained on the development cell (subject fold 0, content fold 0, seed 3401) and scored by the checkpoint-selection score
on the training participants' early-stopping content only; the chosen pair is then fixed for every fold / seed.
Candidates: frozen head {1e-4, 1e-3}; random_full (one group) {1e-4, 3e-4, 1e-3}; partial / full backbone
{1e-5, 3e-5, 1e-4} x head {1e-4, 1e-3} (package start values); LoRA adapters {1e-4, 3e-4, 1e-3} x head {1e-4, 1e-3}
(adapter parameters start at identity and need larger steps; recorded as a resolved deviation from the package list).
Units whose recipe is not yet resolved exit as technical_pending (no record written).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import traceback

import numpy as np
import torch

from .fm_readout import HEAD_VERSION, channel_probe_private, channel_probe_segments
from .run import OUT, PLAN, REPO, canonical, load_cohort, load_row


def _probe(rec, fn):
    """Channels-preserved linear-probe reference (amendment A1); a failure is recorded in the unit, never hidden."""
    try:
        rec["eval"]["channel_probe"] = fn()
    except Exception as ex:  # noqa: BLE001
        rec["eval"]["channel_probe_error"] = f"{type(ex).__name__}: {ex}"

FM_CODE = [("auditory_alignment_v2", f) for f in ("foundation_adapter.py", "fm_readout.py", "train_fm.py", "eval_fm.py", "run_fm.py", "train.py", "evaluate.py", "audio_targets.py", "gx.py", "temporal.py")] + \
          [("auditory_alignment", f) for f in ("data.py", "evaluate.py", "losses.py", "losses_reference.py", "train.py")]
RECIPE = os.path.join(OUT, "fm_recipe")
DEV_CELL = {"subject_fold": 0, "content_fold": 0, "seed": 3401}
FM_FAMILIES = {"B_FM", "D_FM_GENERIC", "D_GX", "C_ATTENTION", "C_SELECTION", "C_COVERAGE"}
SMALL_ARCH = {"legacy_pool4", "density_tokens", "lag_local_tokens"}
LR_SEL_EPOCHS = 20  # learning-rate candidates are compared over the first 20 epochs on the development cell


def code_hash():
    h = hashlib.sha256()
    for d, f in FM_CODE:
        h.update(open(os.path.join(REPO, d, f), "rb").read())
    return h.hexdigest()[:16]


def lr_grid(adaptation):
    if adaptation == "pretrained_frozen":
        return [(0.0, h) for h in (1e-4, 1e-3)]
    if adaptation == "random_full":
        return [(lr, lr) for lr in (1e-4, 3e-4, 1e-3)]
    if adaptation.endswith("peft"):
        return [(b, h) for b in (1e-4, 3e-4, 1e-3) for h in (1e-4, 1e-3)]
    return [(b, h) for b in (1e-5, 3e-5, 1e-4) for h in (1e-4, 1e-3)]


def recipe_key(row):
    """C-family foundation arms reuse the matching B_FM recipe (selection-only uses the NCE / cosine recipe)."""
    s = row["spec"]
    obj = "NCE" if s["objective"] == "SELECTION_CE" else s["objective"]
    return "|".join((s["architecture"], s["adaptation"], row["dataset"], obj))


def candidates(row):
    if row["spec"].get("training_task") == "alignment_plus_selection":
        return [{"sel_weight": w} for w in (0.1, 1.0)]
    return [{}]


def recipe_dir(out):
    return os.path.join(out, "fm_recipe")


def epochs_for(arch, out=OUT):
    f = os.path.join(recipe_dir(out), "epochs.json")
    return json.load(open(f)).get(arch) if os.path.exists(f) else None


def _fit(row, dev, ck, log, lr_b, lr_h, epochs, cand=None):
    from auditory_alignment import data
    from .train_fm import fit_private_fm, fit_segments
    a = row["spec"]["adaptation"]
    if row["dataset"] == "private_bdf":
        return ("private", fit_private_fm(row, data.load_private(), dev, ck, log, lr_b, lr_h, epochs, a))
    coh = load_cohort(row)
    return ("segments", fit_segments(row, coh, dev, ck, log, lr_b, lr_h, epochs, a, **(cand or {})) + (coh,))


def lr_select(key, out=OUT, epochs=None):
    arch, adaptation, dataset, objective = key.split("|")
    os.makedirs(recipe_dir(out), exist_ok=True)
    path = os.path.join(recipe_dir(out), key.replace("|", "__") + ".json")
    if os.path.exists(path):
        print("skip", key); return
    E = epochs or LR_SEL_EPOCHS
    dev = torch.device("cuda")
    row = {"experiment_id": "LRSEL_" + key.replace("|", "_"), "dataset": dataset, **DEV_CELL,
           "spec": {"architecture": arch, "adaptation": adaptation, "objective": objective,
                    "target": "current_class" if dataset == "private_bdf" else {"federici": "envelope"}.get(dataset, "local"),
                    "training_task": "current_class" if dataset == "private_bdf" else "paired_alignment"}}
    res = {"key": key, "dev_cell": DEV_CELL, "epochs": E, "code_hash": code_hash(), "readout_head": HEAD_VERSION, "candidates": []}
    for lr_b, lr_h in lr_grid(adaptation):
        log = {}; t0 = time.time()
        ck = os.path.join(out, "ckpt", "lrsel", f"{key.replace('|', '__')}__{lr_b:g}__{lr_h:g}")  # scratch; removed after scoring
        os.makedirs(os.path.dirname(ck), exist_ok=True)
        try:
            _fit(row, dev, ck, log, lr_b, lr_h, E)
            res["candidates"].append({"lr_backbone": lr_b, "lr_head": lr_h, "score": log["best_selection_score"], "best_epoch": log["best_epoch"],
                                      "curve": log["curve"], "seconds": round(time.time() - t0, 1)})
        except Exception as ex:
            res["candidates"].append({"lr_backbone": lr_b, "lr_head": lr_h, "error": f"{type(ex).__name__}: {ex}", "traceback": traceback.format_exc()[-2000:]})
        for suf in ("_best.pt", "_resume.pt", "_last.pt"):  # candidate states are never reused (user 2026-10-07: delete files no longer useful)
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


def run_unit(row, out=OUT, epochs=None):
    from auditory_alignment import data  # noqa: F401
    from . import evaluate
    from .eval_fm import evaluate_segments
    eid = row["experiment_id"]; path = os.path.join(out, "units", f"{eid}.json")
    if os.path.exists(path):
        print("skip", eid); return
    if row["family_id"] not in FM_FAMILIES or (row["family_id"].startswith("C_") and row["spec"]["architecture"] in SMALL_ARCH):
        print("technical_pending", eid, row["family_id"]); return
    canon = canonical(row); idx = os.path.join(out, "canon", canon)
    if os.path.exists(idx) and epochs is None:  # identical resolved configuration already complete under this code hash
        src = open(idx).read().strip(); sp = os.path.join(out, "units", f"{src}.json")
        if os.path.exists(sp):
            r = json.load(open(sp))
            if r.get("status") == "complete" and r.get("code_hash") == code_hash():
                rec = {"experiment_id": eid, "row": row, "status": "complete", "reuse_of": src, "canonical": canon, "code_hash": code_hash(), "runner": "run_fm"}
                json.dump(rec, open(path + ".tmp", "w")); os.replace(path + ".tmp", path); print("reuse", eid, "->", src); return
    if row["family_id"] == "D_GX":
        return run_gx(row, out)
    rf = os.path.join(recipe_dir(out), recipe_key(row).replace("|", "__") + ".json")
    E = epochs or epochs_for(row["spec"]["architecture"], out)
    if not os.path.exists(rf) or not E:
        print("technical_pending (recipe unresolved)", eid); return
    lr = json.load(open(rf))["chosen"]
    os.makedirs(os.path.join(out, "units"), exist_ok=True); os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    dev = torch.device("cuda"); t0 = time.time()
    rec = {"experiment_id": eid, "row": row, "canonical": canonical(row), "code_hash": code_hash(), "runner": "run_fm", "status": "running",
           "readout_head": HEAD_VERSION,
           "device": torch.cuda.get_device_name(0), "resolved_config": {"epochs": E, **lr, "recipe_file": os.path.relpath(rf, REPO), "d": 16,
                                                                         "optimizer": "AdamW (backbone / head groups)", "weight_decay": 1e-4,
                                                                         "scheduler": "cosine_by_actual_updates"}}
    try:
        cands = candidates(row); fits = []
        for ci, cand in enumerate(cands):
            log = {}
            ck = os.path.join(out, "ckpt", eid + (f"_c{ci}" if len(cands) > 1 else ""))
            fits.append((cand, log, _fit(row, dev, ck, log, lr["lr_backbone"], lr["lr_head"], E, cand)))
        k = 0
        if len(fits) > 1:  # training-side choice: early-stopping 2AFC accuracy at the selected checkpoint
            acc = [[c for c in f[1]["curve"] if c["epoch"] == f[1]["best_epoch"]][0]["es_sel_acc"] for f in fits]
            k = int(np.argmax(acc))
            rec["candidates"] = [{"candidate": f[0], "curve": f[1]["curve"], "best_epoch": f[1]["best_epoch"], "es_sel_acc_at_best": a} for f, a in zip(fits, acc)]
            rec["chosen_candidate"] = fits[k][0]
        _, log, (kind, objs) = fits[k]
        rec.update(log)
        if kind == "private":
            enc, bt, protos = objs
            rec["eval"] = evaluate.evaluate_private(row, enc, bt, log["objective_calibration"], protos)
            _probe(rec, lambda: channel_probe_private(row, enc, bt))
        else:
            enc, head, bt, sel, coh = objs
            rec["eval"] = evaluate_segments(row, enc, head, bt, coh, log["objective_calibration"])
            _probe(rec, lambda: channel_probe_segments(row, enc, head, bt, coh, log["objective_calibration"]))
            if sel is not None:
                from .eval_fm import trained_selection_2afc_segments
                rec["eval"]["attention_2afc_trained_score"] = trained_selection_2afc_segments(enc, head, bt, coh, row, sel)
        rec["status"] = "complete"
    except Exception as ex:
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    rec["total_seconds"] = round(time.time() - t0, 1); rec["gpu_peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
    p = path if rec["status"] == "complete" else path.replace(".json", ".FAILED.json")
    json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
    if rec["status"] == "complete" and epochs is None:
        os.makedirs(os.path.join(out, "canon"), exist_ok=True)
        if not os.path.exists(idx):
            open(idx, "w").write(eid)
    print(eid, rec["status"], rec["total_seconds"], rec.get("error", ""), flush=True)
    if rec["status"] != "complete":
        raise SystemExit(1)


def run_gx(row, out):
    from auditory_alignment import data
    from . import evaluate
    from .gx import fit_gx, native_gx
    eid = row["experiment_id"]; path = os.path.join(out, "units", f"{eid}.json")
    os.makedirs(os.path.join(out, "units"), exist_ok=True); os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    dev = torch.device("cuda"); t0 = time.time()
    rec = {"experiment_id": eid, "row": row, "canonical": canonical(row), "code_hash": code_hash(), "runner": "run_fm/gx", "status": "running",
           "device": torch.cuda.get_device_name(0), "resolved_config": {"protocol": "GX configs/auditory_gx_v1.yaml train/model sections", "batch": 256,
                                                                         "lr": 1e-3, "weight_decay": 0.01, "max_epochs": 40, "patience": 6}}
    try:
        log = {}
        enc, bt = fit_gx(row, data.load_private(), dev, os.path.join(out, "ckpt", eid), log)
        rec.update(log)
        rec["eval"] = native_gx(enc, bt, row, evaluate.evaluate_private(row, enc, bt, log["objective_calibration"]))
        rec["status"] = "complete"
    except Exception as ex:
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    rec["total_seconds"] = round(time.time() - t0, 1)
    p = path if rec["status"] == "complete" else path.replace(".json", ".FAILED.json")
    json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
    print(eid, rec["status"], rec["total_seconds"], rec.get("error", ""), flush=True)
    if rec["status"] != "complete":
        raise SystemExit(1)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--manifest", default=PLAN); a.add_argument("--job-index", type=int); a.add_argument("--experiment-id")
    a.add_argument("--lr-select"); a.add_argument("--epochs", type=int); a.add_argument("--out", default=OUT)
    args = a.parse_args()
    if args.lr_select:
        lr_select(args.lr_select, args.out, args.epochs)
    else:
        run_unit(load_row(args.manifest, args.job_index, args.experiment_id), args.out, args.epochs)


if __name__ == "__main__":
    main()
