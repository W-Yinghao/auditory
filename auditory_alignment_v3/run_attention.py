"""ALN3 D_ATTENTION (lag_local_tokens arm; package docs/07 §1). dense_fm_policy / complement_policy arms wait for the
training-side model policy of B / C.

Training: local_train.fit_continuous on competing-speech segments with training_task attended_alignment | selection_only |
alignment_plus_selection (the ALN2 selection machinery on the dense20ms_v1 grid); for alignment_plus_selection the selection
weight is chosen from {0.1, 1.0} on the training side (early-stopping 2AFC accuracy at the selected checkpoint), as in ALN2.
Evaluation: the standard dense-grid evaluation (incl. per-segment 2AFC) plus attention windows of 5 / 10 / 20 s = 1 / 2 / 4
consecutive 5 s segments of the same trial (never across trials or stories; the same window lengths for every group).
Per window, the per-segment score differences d = score(attended) - score(ignored) (unified and native readouts fitted on
training participants' single-speaker segments) are integrated by
  mean_score       sign(mean d)
  learned_temporal logistic regression on fixed summaries of the d-sequence [mean, sd, min, max, last - first], fitted on the
                   training participants' competing-speech windows of the same length (order randomly mirrored with the label)
The row's integrator is its primary readout; both are recorded. Window length is an evidence-integration question, not a
recording-budget claim.
The integrator is an evaluation-time choice, so the two rows of one trained configuration (integrator mean_score /
learned_temporal) share one model: the mean_score row trains and evaluates both integrators; the learned_temporal row is a
derived record of that model (shared_model_with), which makes the integrator comparison paired.
"""
from __future__ import annotations

import json
import os
import time
import traceback

import numpy as np
import torch

from . import core

SECONDS = (5, 10, 20)


def _runs(segs, seg_len):
    """consecutive segments of one trial: same participant + trial code, e0 step == seg_len."""
    by = {}
    for s in segs:
        by.setdefault((s["p"], s.get("code")), []).append(s)
    runs = []
    for k, ss in by.items():
        ss = sorted(ss, key=lambda s: s["e0"]); cur = [ss[0]]
        for a, b in zip(ss, ss[1:]):
            if b["e0"] - a["e0"] == seg_len:
                cur.append(b)
            else:
                runs.append(cur); cur = [b]
        runs.append(cur)
    return runs


def _windows(runs, k):
    return [r[i:i + k] for r in runs for i in range(0, len(r) - k + 1, k)]


def _summ(d):
    d = np.asarray(d, float)
    return [d.mean(), d.std(), d.min(), d.max(), d[-1] - d[0]]


def attention_windows(b, enc, head, bt, coh, grid):
    from sklearn.linear_model import LogisticRegression
    from auditory_alignment import evaluate as ev1
    segs = coh.segments; obj = "NCE" if b["spec"]["objective"] == "SELECTION_CE" else b["spec"]["objective"]
    reps = ev1.Reps(enc, head, bt, stride=grid)
    train_ss = [s for s in segs if s["p"] in bt.train_p and s["role"] in ("fit", "es") and s["kind"] == "ss"]
    ro = ev1.Readouts(obj, reps, train_ss, np.random.default_rng(b["seed"] + 1000))
    cs = [s for s in segs if s["kind"] == "cs" and s.get("s0_ign") is not None]
    D = {}
    for k in range(0, len(cs), 64):
        q = cs[k:k + 64]
        U = reps.u([s["e0"] for s in q]); Va, Aa = reps.va([s["s0"] for s in q]); Vi, Ai = reps.va([s["s0_ign"] for s in q])
        for i, s in enumerate(q):
            D[id(s)] = {kr: float(ro.scores(U[i:i + 1], Va[i:i + 1], Aa[i:i + 1], kr)[0, 0] - ro.scores(U[i:i + 1], Vi[i:i + 1], Ai[i:i + 1], kr)[0, 0]) for kr in ("unified", "native")}
    tr = [s for s in cs if s["p"] in bt.train_p and s["role"] in ("fit", "es")]
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and coh.participants[s["p"]]["fold"] == b["subject_fold"]})
    te = [s for s in cs if s["p"] in test_p and s["role"] == "test"]
    out = {"per_participant": {}, "integrators": {}, "window_counts": {}}
    rng = np.random.default_rng(b["seed"] + 4242)
    for L in SECONDS:
        k = L // 5
        wtr, wte = _windows(_runs(tr, bt.seg_len), k), _windows(_runs(te, bt.seg_len), k)
        out["window_counts"][L] = {"train": len(wtr), "test": len(wte)}
        for kr in ("unified", "native"):
            lr = None
            if len(wtr) >= 20:
                X, y = [], []
                for w in wtr:
                    d = np.array([D[id(s)][kr] for s in w]); flip = rng.random() < 0.5
                    X.append(_summ(-d if flip else d)); y.append(0 if flip else 1)
                lr = LogisticRegression(C=1.0, max_iter=1000).fit(np.array(X), np.array(y))
                out["integrators"][f"{L}s|{kr}"] = {"coef": lr.coef_[0].tolist(), "intercept": float(lr.intercept_[0]), "n_train_windows": len(wtr)}
            for w in wte:
                pid = coh.participants[w[0]["p"]]["id"]; d = np.array([D[id(s)][kr] for s in w])
                rec = out["per_participant"].setdefault(pid, {"group": coh.participants[w[0]["p"]]["group"]}).setdefault(f"{L}s|{kr}", {"mean_score": [], "learned_temporal": [], "margin": []})
                rec["mean_score"].append(float(d.mean() > 0)); rec["margin"].append(float(d.mean()))
                if lr is not None:
                    rec["learned_temporal"].append(float(lr.predict_proba(np.array([_summ(d)]))[0, 1] > 0.5))
    for pid, r in out["per_participant"].items():
        for key, v in list(r.items()):
            if isinstance(v, dict):
                r[key] = {"mean_score_accuracy": float(np.mean(v["mean_score"])) if v["mean_score"] else None,
                          "learned_temporal_accuracy": float(np.mean(v["learned_temporal"])) if v["learned_temporal"] else None,
                          "mean_margin": float(np.mean(v["margin"])) if v["margin"] else None, "n_windows": len(v["mean_score"])}
    return out


def twin_row(row, rows):
    s = row["spec"]
    return next(r for r in rows if r["family_id"] == row["family_id"] and r["spec"]["integrator"] == "mean_score"
                and all(r[k] == row[k] for k in ("dataset", "subject_fold", "content_fold", "seed"))
                and all(r["spec"].get(k) == s.get(k) for k in s if k != "integrator"))


def twin_ready(row, rows, out):
    t = twin_row(row, rows); p = os.path.join(out, "units", f"{t['experiment_id']}.json")
    return (t, p) if os.path.exists(p) and json.load(open(p)).get("status") == "complete" else None


def run(row, out, epochs=None):
    from auditory_alignment_v2.run import load_cohort
    from . import local_train
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    if row["spec"]["architecture"] != "lag_local_tokens":
        print("technical_pending (model policy arm waits for B/C training-side policy)", row["experiment_id"]); return
    if row["spec"]["integrator"] != "mean_score":
        tw = twin_ready(row, core.load_rows(), out)
        if tw is None:
            print("technical_pending (shared-model twin not complete)", row["experiment_id"]); return
        t0 = time.time(); tr = json.load(open(tw[1])); rec = core.new_record(row, tr["bound_row"], out)
        rec.update({k: v for k, v in tr.items() if k not in rec and k not in ("total_seconds", "gpu_peak_allocated_mb")})
        rec["shared_model_with"] = tw[0]["experiment_id"]; rec["resolved_config"] = {**tr["resolved_config"], "integrator_primary": row["spec"]["integrator"]}
        rec["status"] = "complete"; core.write_record(path, rec, t0); return
    b = core.bind(row); task = row["spec"]["training_task"]
    b["spec"].update({"architecture": "lag_local_tokens", "window": "full", "training_task": task,
                      "objective": "SELECTION_CE" if task == "selection_only" else row["spec"]["objective"]})
    if epochs is not None:
        b["spec"]["epochs"] = epochs
    d = int(row["spec"].get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    try:
        cands = [0.1, 1.0] if task == "alignment_plus_selection" else [None]; fits = []
        for ci, w in enumerate(cands):
            log = {}; coh = load_cohort(b); g = core.grid_samples(coh.fs)
            ck = os.path.join(out, "ckpt", row["experiment_id"] + (f"_c{ci}" if len(cands) > 1 else ""))
            enc, head, bt, sel = local_train.fit_continuous(b, coh, dev, ck, log, sel_weight=w, d=d, grid=g)
            fits.append((w, log, (enc, head, bt, coh, g)))
        k = 0
        if len(fits) > 1:
            acc = [[c for c in f[1]["curve"] if c["epoch"] == f[1]["best_epoch"]][0]["es_sel_acc"] for f in fits]
            k = int(np.argmax(acc))
            rec["candidates"] = [{"sel_weight": f[0], "best_epoch": f[1]["best_epoch"], "es_sel_acc_at_best": a, "curve": f[1]["curve"]} for f, a in zip(fits, acc)]
            rec["chosen_sel_weight"] = fits[k][0]
        w, log, (enc, head, bt, coh, g) = fits[k]
        rec.update(log); rec["resolved_config"] = {"d": d, "grid_samples": g, "fs": coh.fs, "training_task": task, "integrator_primary": row["spec"]["integrator"]}
        rec["eval"] = core.evaluate_grid(b, enc, head, bt, coh, log["objective_calibration"], g)
        rec["eval"]["attention_windows"] = attention_windows(b, enc, head, bt, coh, g)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
