"""ALN3 core binding shared by every family runner: rows of AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010/plans/units.jsonl ->
ALN2-compatible rows, the dense target grid, per-family code hashes and record helpers.

Resolved defaults (docs/auditory_alignment_v3/IMPLEMENTATION_RECEIPT.md):
  dense20ms_v1: grid = round(20 ms x fs) samples (FAU/DTU 128 Hz: 3 = 23.4 ms; Federici 100 Hz: 2 = 20 ms); training anchors
  8 per 5 s segment at grid-aligned random phases; target = the ALN2 'local'/Ac/Lz/envelope 8-frame window from the anchor,
  training-side standardised, fixed semi-orthogonal projection to d = projection_dim (fixed_latent; Federici's 8-dim
  envelope window embeds isometrically, effective rank 8); evaluation on the same grid with the ALN2 candidate pools,
  readouts and checkpoint rule. Small encoders 200 epochs (ALN2-validated; package start value 100), AdamW 1e-3.
  Private: ALN2 trial sets, folds and windows; representation d = 32; GX native network unchanged.
Each family group has its own code hash (FAMILY_CODE + the ALN2 dependencies), so binding a new family never changes the
version of units already running; run.py (dispatcher) and registry.py (family -> code list) are not part of any hash.
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import time

import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(REPO, "AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010")
PLAN = os.path.join(PKG, "plans", "units.jsonl")
OUT = os.path.join(REPO, "private", "auditory_alignment_v3")
V2_OUT = os.path.join(REPO, "private", "auditory_alignment_v2")
DEFAULT_TARGET = {"fau": "local", "dtu": "local", "federici": "envelope", "private_bdf": "current_class"}
EPOCHS_SMALL = 200
TARGET_CONTRACT = "dense20ms_v1"
V2_DEPS = [("auditory_alignment_v2", f) for f in ("temporal.py", "audio_targets.py", "train.py", "evaluate.py", "gx.py", "foundation_adapter.py",
                                                  "fm_readout.py", "train_fm.py", "eval_fm.py")] + \
          [("auditory_alignment", f) for f in ("data.py", "evaluate.py", "losses.py", "losses_reference.py", "train.py")]
from .registry import FAMILY_CODE, FAMILY_GROUP  # noqa: E402 (registry is not part of any code hash)


def code_hash(family):
    h = hashlib.sha256()
    for d, f in FAMILY_CODE[FAMILY_GROUP[family]] + V2_DEPS:
        h.update(open(os.path.join(REPO, d, f), "rb").read())
    return h.hexdigest()[:16]


def grid_samples(fs):
    return max(1, int(round(0.020 * fs)))


def load_rows():
    return [json.loads(l) for l in open(PLAN)]


def bind(row):
    """ALN3 plan row -> ALN2-compatible row (fields used by the ALN2 batchers / loaders)."""
    s, ds = row["spec"], row["dataset"]
    private = ds == "private_bdf"
    spec = {"architecture": s.get("architecture"), "window": s.get("window", "full"), "objective": s["objective"],
            "target": s.get("target") or DEFAULT_TARGET[ds], "audio_head": "fixed_features",
            "training_task": "current_class" if private else s.get("training_task", "paired_alignment"), "epochs": EPOCHS_SMALL}
    if s.get("adaptation"):
        spec["adaptation"] = s["adaptation"]
    return {"experiment_id": row["experiment_id"], "family_id": row["family_id"], "dataset": ds, "subject_fold": row["subject_fold"],
            "content_fold": row["content_fold"] if row["content_fold"] is not None else 0, "seed": row["seed"], "spec": spec}


def evaluate_grid(b, enc, head, bt, coh, calib, grid):
    """ALN2 continuous evaluation with the evaluation grid set to the dense target grid."""
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v2 import evaluate as ev2
    orig = ev1.Reps
    ev1.Reps = functools.partial(orig, stride=grid)
    try:
        return ev2.evaluate_continuous(b, enc, head, bt, coh, calib, None)
    finally:
        ev1.Reps = orig


def new_record(row, b, out):
    os.makedirs(os.path.join(out, "units"), exist_ok=True); os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    return {"experiment_id": row["experiment_id"], "row": row, "bound_row": b, "code_hash": code_hash(row["family_id"]),
            "code_group": FAMILY_GROUP[row["family_id"]], "runner": "auditory_alignment_v3", "status": "running", "device": torch.cuda.get_device_name(0),
            "target_contract": TARGET_CONTRACT if b["dataset"] != "private_bdf" else "current_class", "information_stratum": row["spec"].get("information_stratum")}


def write_record(path, rec, t0):
    rec["total_seconds"] = round(time.time() - t0, 1); rec["gpu_peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
    p = path if rec["status"] == "complete" else path.replace(".json", ".FAILED.json")
    json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
    print(rec["experiment_id"], rec["status"], rec["total_seconds"], rec.get("error", ""), flush=True)
    if rec["status"] != "complete":
        raise SystemExit(1)
