"""ALN3 C_COMPLEMENT / C_CAPACITY_CONTROL runner: resolves the same-fold A_LOCAL lag_local_tokens full base (local_base_same_fold)."""
from __future__ import annotations

import json
import os
import time
import traceback

import torch

from . import core


def base_row(row, rows):
    s = row["spec"]
    for r in rows:
        if r["family_id"] == "A_LOCAL" and r["dataset"] == row["dataset"] and r["subject_fold"] == row["subject_fold"] and r["content_fold"] == row["content_fold"] \
                and r["seed"] == row["seed"] and r["spec"]["objective"] == s["objective"] and r["spec"]["architecture"] == s.get("local_architecture", "lag_local_tokens") \
                and r["spec"]["window"] == s.get("window", "full"):
            return r
    return None


def base_ready(row, rows, out):
    b = base_row(row, rows)
    if b is None:
        return None
    p = os.path.join(out, "units", f"{b['experiment_id']}.json"); ck = os.path.join(out, "ckpt", f"{b['experiment_id']}_best.pt")
    return (b, p, ck) if os.path.exists(p) and os.path.exists(ck) and json.load(open(p)).get("status") == "complete" else None


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from . import fm_complement
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    br = base_ready(row, core.load_rows(), out)
    if br is None:
        print("technical_pending (same-fold local base not complete)", row["experiment_id"]); return
    b_row, b_path, b_ck = br
    b = core.bind(row); s = row["spec"]; d = int(s.get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    rec["dependency"] = {"local_base_same_fold": b_row["experiment_id"], "base_code_hash": json.load(open(b_path))["code_hash"], "base_checkpoint": os.path.relpath(b_ck, core.REPO)}
    try:
        log = {}; coh = load_cohort(b); g = core.grid_samples(coh.fs)
        fm_arch = s["architecture"] if s["architecture"] in ("cbramod", "reve") else None
        model, head, bt = fm_complement.fit_complement(b, coh, dev, os.path.join(out, "ckpt", row["experiment_id"]), log, b_ck, s["variant"], fm_arch, d=d, grid=g, epochs=epochs)
        rec.update(log); rec["resolved_config"] = {"d": d, "grid_samples": g, "fs": coh.fs, "variant": s["variant"], "context_dim": fm_complement.CTX_DIM}
        rec["eval"] = fm_complement.evaluate_complement(b, model, head, bt, coh, log["objective_calibration"], g)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
