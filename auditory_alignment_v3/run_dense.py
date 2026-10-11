"""ALN3 B_DENSE: foundation-model dense readouts (fm_dense.py)."""
from __future__ import annotations

import os
import time
import traceback

import torch

from . import core


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from . import fm_dense
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    b = core.bind(row); s = row["spec"]
    d = int(s.get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    try:
        log = {}; coh = load_cohort(b); g = core.grid_samples(coh.fs)
        E = epochs or fm_dense.EPOCHS[s["architecture"]]
        rec["resolved_config"] = {"d": d, "grid_samples": g, "grid_ms": round(1000 * g / coh.fs, 2), "fs": coh.fs, "epochs": E, "readout": s["readout"],
                                  "lr_backbone_head": fm_dense.LR[s["adaptation"]], "recipe": "aln3 (item-3 addendum 01)"}
        model, head, bt = fm_dense.fit_dense(b, coh, dev, os.path.join(out, "ckpt", row["experiment_id"]), log, s["readout"], d=d, grid=g, epochs=E)
        rec.update(log)
        rec["eval"] = fm_dense.evaluate_dense(b, model, head, bt, coh, log["objective_calibration"], g)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
