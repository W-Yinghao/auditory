"""ALN3 ADDENDUM_07: ALN32_POSTONLY_FM (B_ALIGNED twin with the 0.4 s past EEG zeroed; legacy recipe) and ALN32_TRUE_FULL (aligned
interface, recipe full_onestep_v1 / warmup_then_all_v1, shared numeric backbone lr, LLRD 1, update ledger). Evaluation = B_ALIGNED."""
from __future__ import annotations

import os
import time
import traceback

import torch

from . import core


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from . import fm_aligned, fm_aligned32, fm_dense
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    b = core.bind(row); s = row["spec"]
    d = int(s.get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    try:
        log = {}; coh = load_cohort(b); g = core.grid_samples(coh.fs)
        E = epochs or fm_dense.EPOCHS[s["architecture"]]
        if row["family_id"] == "ALN32_POSTONLY_FM":
            recipe, lr, bcls = "aln3", None, fm_aligned32.PostOnlyAlignedBatcher
        else:
            recipe, lr, bcls = s["recipe"], (float(s["lr_backbone"]), float(s["lr_head"])), None
            assert recipe in ("full_onestep_v1", "warmup_then_all_v1") and s["adaptation"] in ("random_full", "pretrained_full"), (recipe, s["adaptation"])
        rec["resolved_config"] = {"d": d, "grid_samples": g, "fs": coh.fs, "epochs": E, "readout": s["readout"], "recipe": recipe,
                                  "lr_backbone_head": list(lr) if lr else fm_dense.LR[s["adaptation"]], "llrd": 1.0 if recipe != "aln3" else fm_dense.LLRD,
                                  "input_support": s.get("input_support", "aligned1000"), "window_s": [-fm_aligned.PRE_S, fm_aligned.POST_S]}
        model, head, bt = fm_aligned32.fit_aligned32(b, coh, dev, os.path.join(out, "ckpt", row["experiment_id"]), log, s["readout"], d=d, grid=g, epochs=E,
                                                     recipe=recipe, lr=lr, batcher_cls=bcls)
        rec.update(log)
        t1 = time.time()
        rec["eval"] = fm_aligned.evaluate_aligned(b, model, head, bt, coh, log["objective_calibration"], g)
        rec["eval_seconds"] = round(time.time() - t1, 1)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
