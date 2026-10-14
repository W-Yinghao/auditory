"""ALN3 D_COVERAGE complement_policy arm (ADDENDUM_04 §2; package docs/07 §2).

FAU training population P = TH_ONLY | TH_HA | TH_HA_CI. The C_COMPLEMENT variant and backbone are chosen by the training-only
model policy (policy.py). The local base is the D_COVERAGE lag_local_tokens unit of the same (P, subject fold, content fold,
seed, objective): its fit of the same sampling control is loaded and frozen. The chosen variant is trained on population P's
training participants with the C recipe (complement_coverage_train = fm_complement.fit_complement plus the matched-exposure
cap). As in the lag arm each unit trains two models: full_available (all training participants of P) and matched_exposure
(same pool, optimizer updates per epoch and cosine length capped at the TH_ONLY count of the same fold). Evaluation: the C
complement evaluation (fm_complement.evaluate_complement); the primary readout is full_available.
"""
from __future__ import annotations

import json
import os
import time
import traceback

import torch

from . import core, policy

CONTROLS = ("full_available", "matched_exposure")


def lag_base_row(row, rows):
    s = row["spec"]
    for r in rows:
        if r["family_id"] == "D_COVERAGE" and r["spec"].get("architecture") == "lag_local_tokens" and r["dataset"] == row["dataset"] \
                and r["subject_fold"] == row["subject_fold"] and r["content_fold"] == row["content_fold"] and r["seed"] == row["seed"] \
                and r["spec"]["objective"] == s["objective"] and r["spec"]["population"] == s["population"]:
            return r
    return None


def lag_base_ready(row, rows, out=core.OUT):
    b = lag_base_row(row, rows)
    if b is None:
        return None
    p = os.path.join(out, "units", f"{b['experiment_id']}.json")
    cks = {c: os.path.join(out, "ckpt", f"{b['experiment_id']}_{c}_best.pt") for c in CONTROLS}
    if not (os.path.exists(p) and all(os.path.exists(c) for c in cks.values()) and json.load(open(p)).get("status") == "complete"):
        return None
    return b, p, cks


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.train import ROWS, train_participants
    from . import complement_coverage_train, fm_complement
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    rows = core.load_rows()
    pol = policy.resolve(row, rows, core.OUT)
    lb = lag_base_ready(row, rows)
    if pol is None or lb is None:
        print("technical_pending (policy or same-population lag base not ready)", row["experiment_id"]); return
    b_row, b_path, b_cks = lb
    cs = pol["chosen_row"]["spec"]
    b = core.bind(row); b["spec"].update({"architecture": cs["architecture"], "window": "full", "train_population": row["spec"]["population"]})
    d = int(row["spec"].get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    rec["policy"] = {k: v for k, v in pol.items() if k != "chosen_row"}; rec["policy"]["chosen_spec"] = cs
    rec["dependency"] = {"policy_chosen": pol["chosen"], "lag_base_same_population": b_row["experiment_id"],
                         "lag_base_code_hash": json.load(open(b_path))["code_hash"],
                         "lag_base_checkpoints": {c: os.path.relpath(k, core.REPO) for c, k in b_cks.items()}}
    rec["fits"] = {}
    try:
        n_seg = max(2, ROWS.get(row["spec"]["objective"], 256) // 8)
        for ctrl in CONTROLS:
            coh = load_cohort(b); g = core.grid_samples(coh.fs)
            th = train_participants(coh, {"train_population": "TH_ONLY"}, b["subject_fold"])
            cap = max(1, sum(1 for s in coh.segments if s["p"] in th and s["role"] == "fit" and s["kind"] == "ss") // n_seg)
            log = {}
            model, head, bt = complement_coverage_train.fit_complement(
                b, coh, dev, os.path.join(out, "ckpt", f"{row['experiment_id']}_{ctrl}"), log, b_cks[ctrl], cs["variant"], cs["architecture"],
                d=d, grid=g, epochs=epochs, max_batches=cap if ctrl == "matched_exposure" else None)
            rec["fits"][ctrl] = {**{k: v for k, v in log.items() if k != "curve"}, "curve": log["curve"],
                                 "updates_per_epoch_cap": cap if ctrl == "matched_exposure" else None,
                                 "eval": fm_complement.evaluate_complement(b, model, head, bt, coh, log["objective_calibration"], g)}
            del model, head, bt, coh; torch.cuda.empty_cache()
        rec["eval"] = rec["fits"]["full_available"]["eval"]  # primary readout = full_available; matched_exposure under fits
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
