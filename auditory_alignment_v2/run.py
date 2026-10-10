"""ALN2 unit runner. Usage:
  python -m auditory_alignment_v2.run --job-index <i> [--manifest PLAN] [--epochs N] [--out DIR]

Reads one planned comparison row (package plan, read-only), resolves it, and either
  - trains + evaluates it (writes <out>/units/<experiment_id>.json, checkpoints under <out>/ckpt/), or
  - records a reuse pointer when an identical resolved configuration (canonical signature) is already complete, or
  - exits with status technical_pending when its family is not yet integrated (no record written; nothing is faked).
Training-side choices inside a unit (anchored weight, selection weight) run every candidate and select on the
training side (early-stopping task metric); all candidate curves are kept.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time
import traceback

import numpy as np
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(REPO, "AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006")
PLAN = os.path.join(PKG, "plans", "planned_comparisons.jsonl")
OUT = os.path.join(REPO, "private", "auditory_alignment_v2")
CODE = [("auditory_alignment_v2", f) for f in ("temporal.py", "audio_targets.py", "train.py", "evaluate.py", "run.py")] + \
       [("auditory_alignment", f) for f in ("data.py", "evaluate.py", "losses.py", "losses_reference.py", "model.py", "train.py")]
DEFAULT_POP = {"fau": "TH_HA_CI"}


def code_hash():
    h = hashlib.sha256()
    for d, f in CODE:
        h.update(open(os.path.join(REPO, d, f), "rb").read())
    return h.hexdigest()[:16]


def canonical(row):
    """Resolved signature: identical models share it whatever family registered them (defaults normalised)."""
    s = dict(row["spec"])
    if s.get("pairing") == "correct":
        s.pop("pairing")
    if "train_population" in s and s["train_population"] == DEFAULT_POP.get(row["dataset"]):
        s.pop("train_population")
    return hashlib.sha256(json.dumps({"dataset": row["dataset"], "spec": s, "subject_fold": row["subject_fold"],
                                      "content_fold": row["content_fold"], "seed": row["seed"]}, sort_keys=True).encode()).hexdigest()[:20]


def load_row(manifest, index=None, eid=None):
    with open(manifest) as f:
        for i, line in enumerate(f):
            r = json.loads(line)
            if (index is not None and i == index) or (eid is not None and r["experiment_id"] == eid):
                return r
    raise SystemExit("row not found")


def load_cohort(row):
    from auditory_alignment import data
    ds, cf = row["dataset"], row["content_fold"]
    if ds == "fau":
        return data.load_fau(cf, kinds=("ss", "cs"))
    if ds == "dtu":
        return data.load_dtu(cf, kinds=("ss", "cs"))
    if ds == "federici":
        return data.load_federici()
    raise ValueError(ds)


def candidates(row):
    spec, fam = row["spec"], row["family_id"]
    if spec.get("audio_head") == "anchored_head":
        return [{"anchor_weight": w} for w in (0.1, 1.0)]
    if spec.get("training_task") == "alignment_plus_selection":
        return [{"sel_weight": w} for w in (0.1, 1.0)]
    return [{}]


def run_unit(row, out=OUT, epochs=None):
    from . import evaluate, train
    from .registry import integrated
    from auditory_alignment import data
    os.makedirs(os.path.join(out, "units"), exist_ok=True); os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    eid = row["experiment_id"]; path = os.path.join(out, "units", f"{eid}.json")
    if os.path.exists(path):
        print("skip", eid); return
    if not integrated(row):
        print("technical_pending", eid, row["family_id"]); return
    canon = canonical(row)
    if epochs is not None:
        row = json.loads(json.dumps(row)); row["spec"]["epochs"] = epochs
    # reuse an identical, already complete resolved configuration (canonical signature index + same code hash)
    idx = os.path.join(out, "canon", canon)
    if os.path.exists(idx) and epochs is None:
        src = open(idx).read().strip(); sp = os.path.join(out, "units", f"{src}.json")
        if os.path.exists(sp):
            r = json.load(open(sp))
            if r.get("status") == "complete" and r.get("code_hash") == code_hash():
                rec = {"experiment_id": eid, "row": row, "status": "complete", "reuse_of": src, "canonical": canon, "code_hash": code_hash()}
                json.dump(rec, open(path + ".tmp", "w")); os.replace(path + ".tmp", path); print("reuse", eid, "->", src); return
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t0 = time.time()
    rec = {"experiment_id": eid, "row": row, "canonical": canon, "code_hash": code_hash(), "status": "running",
           "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
           "resolved_config": {"d": 16, "rows": train.ROWS.get(row["spec"]["objective"]), "optimizer": "AdamW", "lr": 1e-3, "weight_decay": 1e-4,
                               "scheduler": "cosine_by_actual_updates", "epochs": row["spec"].get("epochs", 200), "token_step_ms": 20, "local_patch_ms": 40,
                               "token_dim": 32, "temperature": 0.1, "bandwidth": "initial_training_calibration_median_x1", "fmca_relative_ridge": 1e-3,
                               "checkpoint_rule": "own objective minus legal mismatch (40 early-stopping batches); selection-only: 2AFC loss",
                               "seeds_from_plan": row["seed"]}}
    try:
        cands = candidates(row); fits = []
        for ci, cand in enumerate(cands):
            log = {}
            ck = os.path.join(out, "ckpt", f"{eid}" + (f"_c{ci}" if len(cands) > 1 else ""))
            if row["dataset"] == "private_bdf":
                kids = data.load_private()
                enc, bt, protos = train.fit_private(row, kids, dev, ck, log)
                fits.append((cand, log, (enc, bt, protos)))
            else:
                coh = load_cohort(row)
                enc, head, bt, sel = train.fit_continuous(row, coh, dev, ck, log, **cand)
                fits.append((cand, log, (enc, head, bt, sel, coh)))
        if len(fits) > 1:  # training-side choice among candidates
            def score(f):
                c = [x for x in f[1]["curve"] if x["epoch"] == f[1]["best_epoch"]][0]
                return -c["es_sel_acc"] if "sel_weight" in f[0] else f[1]["best_selection_score"]
            k = int(np.argmin([score(f) for f in fits]))
            rec["candidates"] = [{"candidate": f[0], "curve": f[1]["curve"], "best_epoch": f[1]["best_epoch"], "training_side_score": score(f)} for f in fits]
            rec["chosen_candidate"] = fits[k][0]
        else:
            k = 0
        cand, log, objs = fits[k]
        rec.update(log)
        if row["dataset"] == "private_bdf":
            enc, bt, protos = objs
            rec["eval"] = evaluate.evaluate_private(row, enc, bt, log["objective_calibration"], protos)
        else:
            enc, head, bt, sel, coh = objs
            rec["eval"] = evaluate.evaluate_continuous(row, enc, head, bt, coh, log["objective_calibration"], sel)
        rec["status"] = "complete"
    except Exception as ex:  # technical failure is recorded as such, never as a scientific result
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    rec["total_seconds"] = round(time.time() - t0, 1)
    if torch.cuda.is_available():
        rec["gpu_peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
    p = path if rec["status"] == "complete" else path.replace(".json", ".FAILED.json")
    json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
    if rec["status"] == "complete" and epochs is None:
        os.makedirs(os.path.join(out, "canon"), exist_ok=True)
        if not os.path.exists(os.path.join(out, "canon", canon)):
            open(os.path.join(out, "canon", canon), "w").write(eid)
    print(eid, rec["status"], rec["total_seconds"], rec.get("error", ""), flush=True)
    if rec["status"] != "complete":
        raise SystemExit(1)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--manifest", default=PLAN); a.add_argument("--job-index", type=int); a.add_argument("--experiment-id")
    a.add_argument("--epochs", type=int); a.add_argument("--out", default=OUT)
    args = a.parse_args()
    run_unit(load_row(args.manifest, args.job_index, args.experiment_id), args.out, args.epochs)


if __name__ == "__main__":
    main()
