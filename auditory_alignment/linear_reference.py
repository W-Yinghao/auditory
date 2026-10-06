"""Extension E9 (spec 5.4): linear, non-deep reference on the identical evaluation protocol.

The "encoder" is the flattened EEG window itself (channels x samples of the unit's window, concatenated for the joint
window) and the "audio representation" is the flattened 8-frame target; both readouts are therefore training-side ridge
bridges from raw EEG lags to the target (a backward / stimulus-reconstruction TRF). No seeds, no training. Same folds,
content folds, candidates, mismatched-EEG control, calibration and attention 2AFC as the fitted units.

Usage: python -m auditory_alignment.linear_reference <dataset> <target> <window> <subject_fold> <content_fold>
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

from . import data, evaluate, train
from .run import OUT, code_hash


class Flat(nn.Module):
    def forward(self, patches):
        return torch.cat([p.flatten(1) for p in patches], 1) if isinstance(patches, list) else patches.flatten(1)


def main():
    ds, tgt, win, sf, cf = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    eid = f"linear_{ds}_{tgt}_{win}_sf{sf}_cf{cf}"
    path = os.path.join(OUT, "units_linear", f"{eid}.json")
    if os.path.exists(path):
        print("skip", eid); return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pop = {"fau": "TH_HA_CI", "dtu": "NH_HI", "federici": "HC_CI_available_vocoder_conditions", "private_bdf": "HA_NH"}[ds]
    job = {"experiment_id": eid, "block": "linear_reference", "dataset": ds, "objective": "LINEAR", "target": tgt, "window": win,
           "subject_fold": sf, "content_fold": cf, "seed": 0, "train_population": pop, "config": {}}
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t0 = time.time(); rec = {"job": job, "code_hash": code_hash(), "status": "running"}
    enc = Flat()
    if ds == "private_bdf":
        bt = train.PrivateBatcher(data.load_private(), job, dev)
        with torch.no_grad():
            P, Y = bt.batch(np.random.default_rng(99), per=8)
            u0 = enc(P)
        rec["objective_calibration"] = {"sigma_u": train._offdiag_median_dist(u0), "sigma_v": None}
        rec["eval"] = evaluate.evaluate_private(enc, bt, job, rec["objective_calibration"])
    else:
        coh = {"fau": lambda: data.load_fau(cf, kinds=("ss", "cs")), "dtu": lambda: data.load_dtu(cf, kinds=("ss", "cs")),
               "federici": data.load_federici}[ds]()
        bt = train.ContinuousBatcher(coh, job, dev)
        aud = Flat()
        b = next(bt.epoch_batches(np.random.default_rng(99), 32))
        with torch.no_grad():
            e0, s0, _ = bt.rows(b, np.random.default_rng(98))
            u0, v0 = enc(bt.patches(e0)), aud(bt.audio(s0))
        rec["objective_calibration"] = {"sigma_u": train._offdiag_median_dist(u0), "sigma_v": train._offdiag_median_dist(v0)}
        # native readout = ridge bridge into the raw (flattened) target space, as for the CS methods
        rec["eval"] = evaluate.evaluate_continuous("CS_SINGLE", enc, aud, bt, coh, job, np.random.default_rng(1000), rec["objective_calibration"])
    rec["status"] = "complete"; rec["total_seconds"] = round(time.time() - t0, 1)
    json.dump(rec, open(path + ".tmp", "w"), default=float); os.replace(path + ".tmp", path)
    print(eid, "complete", rec["total_seconds"], flush=True)


if __name__ == "__main__":
    main()
