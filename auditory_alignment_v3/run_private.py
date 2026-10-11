"""ALN3 E_LOCAL / E_GX / E_GENERIC: private current class with the calibration variants of calib.py (see core.py)."""
from __future__ import annotations

import json
import os
import time
import traceback

import torch

from . import core


def fm_recipe(arch, adaptation, objective):
    p = os.path.join(core.V2_OUT, "fm_recipe", f"{arch}__{adaptation}__private_bdf__{objective}.json")
    E = json.load(open(os.path.join(core.V2_OUT, "fm_recipe", "epochs.json")))[arch]
    return json.load(open(p))["chosen"], p, E


def run(row, out, epochs=None):
    from auditory_alignment import data
    from auditory_alignment_v2 import evaluate as ev2
    from . import calib, local_train
    fam = row["family_id"]; path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    b = core.bind(row)
    if epochs is not None:
        b["spec"]["epochs"] = epochs
    d = int(row["spec"].get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out); ck = os.path.join(out, "ckpt", row["experiment_id"])
    try:
        log = {}; kids = data.load_private()
        if fam == "E_GX":
            from auditory_alignment_v2.gx import fit_gx, native_gx
            enc, bt = fit_gx(b, kids, dev, ck, log)
            rec.update(log)
            rec["eval"] = native_gx(enc, bt, b, ev2.evaluate_private(b, enc, bt, log["objective_calibration"]))
            rec["eval"]["native_calibration"] = calib.gx_variants(b, enc, bt)
        elif fam == "E_LOCAL":
            enc, bt, protos = local_train.fit_private(b, kids, dev, ck, log, d=d)
            rec.update(log); rec["resolved_config"] = {"d": d, "epochs": b["spec"]["epochs"], "optimizer": "AdamW", "lr": 1e-3}
            rec["eval"] = ev2.evaluate_private(b, enc, bt, log["objective_calibration"], protos)
            rec["eval"]["native_calibration"] = calib.private_variants(b, enc, bt, protos, log["objective_calibration"])
        else:  # E_GENERIC
            s = row["spec"]; lr, rf, E = fm_recipe(s["architecture"], s["adaptation"], s["objective"])
            E = epochs or E
            rec["resolved_config"] = {"d": d, "epochs": E, **lr, "recipe_file": os.path.relpath(rf, core.REPO), "readout": "spatial_signed_k8_e32_v1",
                                      "input": "full epoch -200..600 ms zero-padded (padded_private_epoch_no_extra_EEG)"}
            enc, bt, protos = local_train.fit_private_fm(b, kids, dev, ck, log, lr["lr_backbone"], lr["lr_head"], E, s["adaptation"], d=d)
            rec.update(log)
            rec["eval"] = ev2.evaluate_private(b, enc, bt, log["objective_calibration"], protos)
            rec["eval"]["native_calibration"] = calib.private_variants(b, enc, bt, protos, log["objective_calibration"])
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
