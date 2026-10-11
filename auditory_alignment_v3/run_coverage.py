"""ALN3 D_COVERAGE (lag_local_tokens arm; package docs/07 §2): FAU training population TH_ONLY | TH_HA | TH_HA_CI, same test
participants and candidates. Each unit trains two models: full_available (all training participants of the population) and
matched_exposure (same pool, optimizer updates per epoch and cosine length capped at the TH_ONLY count of the same fold), so
added population and added updates are separated. complement_policy arm waits for the C training-side policy."""
from __future__ import annotations

import os
import time
import traceback

import torch

from . import core


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.train import ROWS, train_participants
    from . import coverage_train
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    if row["spec"]["architecture"] != "lag_local_tokens":
        print("technical_pending (complement_policy arm waits for the C training-side policy)", row["experiment_id"]); return
    b = core.bind(row); b["spec"].update({"architecture": "lag_local_tokens", "window": "full", "train_population": row["spec"]["population"]})
    if epochs is not None:
        b["spec"]["epochs"] = epochs
    d = int(row["spec"].get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out); rec["fits"] = {}
    try:
        n_seg = max(2, ROWS.get(b["spec"]["objective"], 256) // 8)
        for ctrl in ("full_available", "matched_exposure"):
            coh = load_cohort(b); g = core.grid_samples(coh.fs)
            th = train_participants(coh, {"train_population": "TH_ONLY"}, b["subject_fold"])
            cap = max(1, sum(1 for s in coh.segments if s["p"] in th and s["role"] == "fit" and s["kind"] == "ss") // n_seg)
            log = {}
            enc, head, bt, _ = coverage_train.fit_continuous(b, coh, dev, os.path.join(out, "ckpt", f"{row['experiment_id']}_{ctrl}"), log, d=d, grid=g,
                                                             max_batches=cap if ctrl == "matched_exposure" else None)
            rec["fits"][ctrl] = {**{k: v for k, v in log.items() if k != "curve"}, "curve": log["curve"], "updates_per_epoch_cap": cap if ctrl == "matched_exposure" else None,
                                 "eval": core.evaluate_grid(b, enc, head, bt, coh, log["objective_calibration"], g)}
            del enc, head, bt, coh; torch.cuda.empty_cache()
        rec["eval"] = rec["fits"]["full_available"]["eval"]  # primary readout = full_available; matched_exposure under fits
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
