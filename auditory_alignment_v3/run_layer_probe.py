"""ALN3 B_LAYER_PROBE runner (definition in fm_probe.py)."""
from __future__ import annotations

import os
import time
import traceback

import torch

from . import core


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from . import fm_dense, fm_probe
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    b = core.bind(row); s = row["spec"]; d = int(s.get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    try:
        coh = load_cohort(b); g = core.grid_samples(coh.fs); log = {}
        probe, head, bt = fm_probe.fit_probe(b, coh, dev, s["layer"], d=d, grid=g, log=log)
        rec.update(log); rec["resolved_config"] = {"d": d, "grid_samples": g, "fs": coh.fs, "readout": s["readout"], "adaptation": "pretrained_frozen",
                                                   "native_readout": "regression readout of CS_SINGLE (training-side ridge, negative squared error)"}
        be = {**b, "spec": {**b["spec"], "objective": "CS_SINGLE"}}
        rec["eval"] = fm_dense.evaluate_dense(be, probe, head, bt, coh, log["objective_calibration"], g)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
