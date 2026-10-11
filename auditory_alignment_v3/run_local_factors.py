"""ALN3 A_LOCAL_FACTORS: the run_local path with the control encoders of temporal_ext.py (encoder factory swapped in-process)."""
from __future__ import annotations

import json
import os

from . import local_train, run_local, temporal_ext


def run(row, out, epochs=None):
    local_train.build_encoder = temporal_ext.build_encoder  # A_LOCAL_FACTORS only; other families never import this module
    run_local.run(row, out, epochs)
    p = os.path.join(out, "units", f"{row['experiment_id']}.json")
    if os.path.exists(p):  # add the capacity record (parameter counts of the control and of both references)
        rec = json.load(open(p)); rec["capacity_control"] = dict(temporal_ext.LAST)
        json.dump(rec, open(p + ".tmp", "w"), default=float); os.replace(p + ".tmp", p)
