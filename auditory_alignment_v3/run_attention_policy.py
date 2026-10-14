"""ALN3 D_ATTENTION policy arms dense_fm_policy / complement_policy (ADDENDUM_04 §2; package docs/07 §1).

The training-only model policy (policy.py) chooses the B_DENSE configuration (dense_fm_policy) or the C_COMPLEMENT variant and
backbone (complement_policy). Training (fm_attention): the chosen configuration on the row's training task; the complement arm
stacks the chosen residual on the frozen D_ATTENTION lag_local_tokens unit of the same training task (its selected
checkpoint). As for the lag arm (run_attention): alignment_plus_selection trains selection weights {0.1, 1.0} and keeps the one
with the higher training-side early-stopping 2AFC accuracy at its selected checkpoint; evaluation = the dense-grid evaluation
plus attention windows of 5 / 10 / 20 s with the mean_score and learned_temporal integrators (run_attention.attention_windows
on the FM representations); the learned_temporal row is a derived record of its mean_score twin (shared_model_with).
"""
from __future__ import annotations

import json
import os
import time
import traceback

import numpy as np
import torch

from . import core, policy

ARMS = ("dense_fm_policy", "complement_policy")


def lag_twin_row(row, rows):
    """the D_ATTENTION lag_local_tokens mean_score unit with the same dataset / folds / seed / objective / training task."""
    s = row["spec"]
    for r in rows:
        if r["family_id"] == "D_ATTENTION" and r["spec"].get("architecture") == "lag_local_tokens" and r["spec"].get("integrator") == "mean_score" \
                and all(r[k] == row[k] for k in ("dataset", "subject_fold", "content_fold", "seed")) \
                and all(r["spec"].get(k) == s.get(k) for k in s if k not in ("architecture", "integrator")):
            return r
    return None


def lag_twin_ready(row, rows, out=core.OUT):
    t = lag_twin_row(row, rows)
    if t is None:
        return None
    p = os.path.join(out, "units", f"{t['experiment_id']}.json")
    if not os.path.exists(p):
        return None
    rec = json.load(open(p))
    if rec.get("status") != "complete":
        return None
    k = [0.1, 1.0].index(rec["chosen_sel_weight"]) if rec.get("chosen_sel_weight") is not None else None
    ck = os.path.join(out, "ckpt", t["experiment_id"] + (f"_c{k}" if k is not None else "") + "_best.pt")
    return (t, p, ck) if os.path.exists(ck) else None


def policy_twin_row(row, rows):
    """the mean_score row of the same policy arm (shared model)."""
    s = row["spec"]
    return next(r for r in rows if r["family_id"] == "D_ATTENTION" and r["spec"].get("integrator") == "mean_score"
                and all(r[k] == row[k] for k in ("dataset", "subject_fold", "content_fold", "seed"))
                and all(r["spec"].get(k) == s.get(k) for k in s if k != "integrator"))


def _windows(b, model, head, bt, coh, g, reps_cls):
    from auditory_alignment import evaluate as ev1
    from .run_attention import attention_windows
    orig = ev1.Reps
    ev1.Reps = lambda enc, aud, bt_, **kw: reps_cls(model, aud, bt_, g)
    try:
        return attention_windows(b, model, head, bt, coh, g)
    finally:
        ev1.Reps = orig


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from . import fm_attention, fm_complement, fm_dense
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    rows = core.load_rows(); arm = row["spec"]["architecture"]
    if row["spec"]["integrator"] != "mean_score":
        tw = policy_twin_row(row, rows); tp = os.path.join(out, "units", f"{tw['experiment_id']}.json")
        if not (os.path.exists(tp) and json.load(open(tp)).get("status") == "complete"):
            print("technical_pending (shared-model twin not complete)", row["experiment_id"]); return
        t0 = time.time(); tr = json.load(open(tp)); rec = core.new_record(row, tr["bound_row"], out)
        rec.update({k: v for k, v in tr.items() if k not in rec and k not in ("total_seconds", "gpu_peak_allocated_mb")})
        rec["shared_model_with"] = tw["experiment_id"]; rec["resolved_config"] = {**tr["resolved_config"], "integrator_primary": row["spec"]["integrator"]}
        rec["status"] = "complete"; core.write_record(path, rec, t0); return
    pol = policy.resolve(row, rows, core.OUT)
    twin = lag_twin_ready(row, rows) if arm == "complement_policy" else None
    if pol is None or (arm == "complement_policy" and twin is None):
        print("technical_pending (policy or lag-arm base not ready)", row["experiment_id"]); return
    cs = pol["chosen_row"]["spec"]; task = row["spec"]["training_task"]
    b = core.bind(row)
    b["spec"].update({"architecture": cs["architecture"], "window": "full", "training_task": task,
                      "objective": "SELECTION_CE" if task == "selection_only" else row["spec"]["objective"]})
    if arm == "dense_fm_policy":
        b["spec"]["adaptation"] = cs["adaptation"]
    d = int(row["spec"].get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    rec["policy"] = {k: v for k, v in pol.items() if k != "chosen_row"}; rec["policy"]["chosen_spec"] = cs
    rec["dependency"] = {"policy_chosen": pol["chosen"]}
    if twin is not None:
        rec["dependency"].update({"lag_base_same_task": twin[0]["experiment_id"], "lag_base_code_hash": json.load(open(twin[1]))["code_hash"],
                                  "lag_base_checkpoint": os.path.relpath(twin[2], core.REPO)})
    try:
        cands = [0.1, 1.0] if task == "alignment_plus_selection" else [None]; fits = []; last = None
        for ci, w in enumerate(cands):
            last = bt = coh = None; torch.cuda.empty_cache()  # one cohort / batcher on the GPU at a time (identical for both candidates)
            log = {}; coh = load_cohort(b); g = core.grid_samples(coh.fs)
            ck = os.path.join(out, "ckpt", row["experiment_id"] + (f"_c{ci}" if len(cands) > 1 else ""))
            if arm == "dense_fm_policy":
                model, head, bt, sel = fm_attention.fit_dense_task(b, coh, dev, ck, log, cs, sel_weight=w, d=d, grid=g, epochs=epochs)
            else:
                model, head, bt, sel = fm_attention.fit_complement_task(b, coh, dev, ck, log, twin[2], cs, sel_weight=w, d=d, grid=g, epochs=epochs)
            fits.append((w, log, model.cpu(), head))
            last = (bt, coh, g); model = sel = None; torch.cuda.empty_cache()
        k = 0
        if len(fits) > 1:
            acc = [[c for c in f[1]["curve"] if c["epoch"] == f[1]["best_epoch"]][0]["es_sel_acc"] for f in fits]
            k = int(np.argmax(acc))
            rec["candidates"] = [{"sel_weight": f[0], "best_epoch": f[1]["best_epoch"], "es_sel_acc_at_best": a, "curve": f[1]["curve"]} for f, a in zip(fits, acc)]
            rec["chosen_sel_weight"] = fits[k][0]
        w, log, model, head = fits[k]; model = model.to(dev).eval(); bt, coh, g = last
        rec.update(log); rec["resolved_config"] = {"d": d, "grid_samples": g, "fs": coh.fs, "training_task": task, "integrator_primary": row["spec"]["integrator"],
                                                   "arm": arm, "chosen": pol["chosen"]}
        evf, reps_cls = (fm_dense.evaluate_dense, fm_dense.DenseReps) if arm == "dense_fm_policy" else (fm_complement.evaluate_complement, fm_complement.CompReps)
        rec["eval"] = evf(b, model, head, bt, coh, log["objective_calibration"], g)
        rec["eval"]["attention_windows"] = _windows(b, model, head, bt, coh, g, reps_cls)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
