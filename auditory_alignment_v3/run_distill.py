"""ALN3 E_DISTILL runner (definition in private_stage.py; trainer distill_train.py).

Teacher candidates (same outer fold, seed and objective as the row; all must be complete before the choice is made, so the
choice never depends on completion order):
  local_teacher               ALN3 E_LOCAL, every local architecture, window full or joint (whole-epoch input)
  generic_pretrained_teacher  ALN3 E_GENERIC, CBraMod / REVE, adaptation pretrained_frozen | _peft | _partial | _full
  auditory_adapted_teacher    ALN2 D_FM_PUBLIC (repaired), CBraMod / REVE, auditory_pretrained_peft
  legacy_full_teacher_control ALN2 D_FM_PUBLIC (repaired), CBraMod / REVE, auditory_pretrained_full
Choice: minimum recorded best_selection_score (early-stopping loss of training children minus its label-permuted value;
training side only). Teacher probability per training trial: positive-affine calibration of the teacher's native score on
the training children's early-stopping blocks. Students: lambda = 0 (complete baseline), 0.1, 1.0; the reported lambda is
chosen from {0.1, 1.0} by the student's own best_selection_score; all three are evaluated and recorded.
"""
from __future__ import annotations

import glob
import json
import os
import time
import traceback

import numpy as np
import torch

from . import core, private_stage as PS

V2_INDEX = os.path.join(core.OUT, "v2_fm_public_index.json")


def _v2_index():
    if not os.path.exists(V2_INDEX):
        idx = []
        for f in glob.glob(os.path.join(core.V2_OUT, "units", "ALN2_D_FM_PUBLIC_*.json")):
            if f.endswith(".FAILED.json"):
                continue
            r = json.load(open(f))
            if r.get("status") == "complete":
                rw = r["row"]; idx.append({"experiment_id": r["experiment_id"], "subject_fold": rw["subject_fold"], "seed": rw["seed"], **rw["spec"]})
        json.dump(idx, open(V2_INDEX + ".tmp", "w")); os.replace(V2_INDEX + ".tmp", V2_INDEX)
    return json.load(open(V2_INDEX))


def candidates(row, rows):
    s, pol = row["spec"], row["spec"]["teacher_policy"]
    same = lambda r: r["subject_fold"] == row["subject_fold"] and r["seed"] == row["seed"] and r["spec"]["objective"] == s["objective"]
    if pol == "local_teacher":
        return [r["experiment_id"] for r in rows if r["family_id"] == "E_LOCAL" and same(r) and r["spec"]["window"] in ("full", "joint")]
    if pol == "generic_pretrained_teacher":
        return [r["experiment_id"] for r in rows if r["family_id"] == "E_GENERIC" and same(r) and r["spec"]["adaptation"].startswith("pretrained")]
    ad = {"auditory_adapted_teacher": "auditory_pretrained_peft", "legacy_full_teacher_control": "auditory_pretrained_full"}[pol]
    return [x["experiment_id"] for x in _v2_index() if x["adaptation"] == ad and x["subject_fold"] == row["subject_fold"] and x["seed"] == row["seed"]
            and x["objective"] == s["objective"]]


def teachers_ready(row, rows):
    c = candidates(row, rows)
    if not c:
        return None
    recs = {}
    for eid in c:
        out, p = PS.unit_paths(eid)
        if p is None or not os.path.exists(os.path.join(out, "ckpt", f"{eid}_best.pt")):
            return None
        r = json.load(open(p))
        if r.get("status") != "complete":
            return None
        recs[eid] = r["best_selection_score"]
    return recs


def run(row, out, epochs=None):
    from auditory_alignment import data
    from auditory_alignment_v2 import evaluate as ev2
    from . import calib, distill_train
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    scores = teachers_ready(row, core.load_rows())
    if scores is None:
        print("technical_pending (teacher candidates not all complete)", row["experiment_id"]); return
    t_eid = min(scores, key=scores.get)
    b = core.bind(row); b["spec"]["architecture"] = row["spec"]["student"]; b["spec"]["window"] = row["spec"]["window"]
    E = epochs or core.EPOCHS_SMALL; d = int(row["spec"].get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out)
    rec["teacher"] = {"policy": row["spec"]["teacher_policy"], "candidates_best_selection_score": scores, "chosen": t_eid,
                      "rule": "min recorded best_selection_score (training children's early-stopping blocks)"}
    try:
        kids = data.load_private()
        enc_t, protos_t, trec, bt_t = PS.rebuild(t_eid, kids, dev)
        tr = bt_t.train
        S = PS.native_scores(enc_t, protos_t.to(dev) if protos_t is not None else None, trec, bt_t, kids, tr)
        cal = PS.calibrator(S, kids, tr)
        p_t = torch.full((int(bt_t.off[-1]),), 0.5, device=dev)
        for i in tr:
            p_t[bt_t.off[i]:bt_t.off[i + 1]] = torch.tensor(cal.predict(S[i]), device=dev, dtype=torch.float32)
        rec["teacher"].update({"family": trec["row"]["family_id"], "spec": trec["row"]["spec"], "calibration": cal.to_dict(),
                               "p_teacher_train_mean": float(np.mean(np.concatenate([cal.predict(S[i]) for i in tr])))})
        del enc_t, bt_t; torch.cuda.empty_cache()
        fits = []
        for ci, lam in enumerate((0.0, 0.1, 1.0)):
            log = {}
            enc, bt, protos = distill_train.fit_private_distill(b, kids, dev, os.path.join(out, "ckpt", f"{row['experiment_id']}_c{ci}"), log, p_t, lam, epochs=E, d=d)
            ev = ev2.evaluate_private(b, enc, bt, log["objective_calibration"], protos)
            ev["native_calibration"] = calib.private_variants(b, enc, bt, protos, log["objective_calibration"])
            fits.append({"distill_weight": lam, "log": log, "eval": ev})
            del enc, bt; torch.cuda.empty_cache()
        k = 1 + int(np.argmin([f["log"]["best_selection_score"] for f in fits[1:]]))
        rec["candidates"] = [{"distill_weight": f["distill_weight"], "best_epoch": f["log"]["best_epoch"], "best_selection_score": f["log"]["best_selection_score"],
                              "curve": f["log"]["curve"], "eval": f["eval"]} for f in fits]
        rec["chosen_candidate"] = {"distill_weight": fits[k]["distill_weight"], "rule": "min best_selection_score over lambda in {0.1, 1.0}"}
        rec.update({kk: v for kk, v in fits[k]["log"].items() if kk != "curve"}); rec["curve"] = fits[k]["log"]["curve"]
        rec["eval"] = fits[k]["eval"]; rec["baseline_lambda0_eval"] = fits[0]["eval"]
        rec["resolved_config"] = {"d": d, "epochs": E, "student": row["spec"]["student"], "window": row["spec"]["window"]}
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
