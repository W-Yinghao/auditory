"""ALN3 A_LOCAL / A_TARGETS / A_DIMENSION: local_only small encoders on dense20ms_v1 (see core.py)."""
from __future__ import annotations

import os
import time
import traceback

import torch

from . import core


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from . import local_train
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    b = core.bind(row)
    if epochs is not None:
        b["spec"]["epochs"] = epochs
    d = int(row["spec"].get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    try:
        log = {}; coh = load_cohort(b); g = core.grid_samples(coh.fs)
        rec["resolved_config"] = {"d": d, "grid_samples": g, "grid_ms": round(1000 * g / coh.fs, 2), "fs": coh.fs, "epochs": b["spec"]["epochs"],
                                  "optimizer": "AdamW", "lr": 1e-3, "weight_decay": 1e-4, "anchors_per_segment": 8, "target_frames": 8,
                                  "audio_head": "fixed_features (training-side standardised, fixed semi-orthogonal projection)"}
        enc, head, bt, _ = local_train.fit_continuous(b, coh, dev, os.path.join(out, "ckpt", row["experiment_id"]), log, d=d, grid=g)
        rec.update(log)
        rec["eval"] = core.evaluate_grid(b, enc, head, bt, coh, log["objective_calibration"], g)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001 - recorded, never hidden
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
