"""Diagnostic probe (not part of the unit protocol): does fitting the private readouts on gradient-exposed trials explain the
negative head gains? For fitted private units, refit the calibrated head and the history offset model on (a) all trials of
the training children (current protocol), (b) only their early-stopping blocks (never used for gradient steps), and report
test-child gains, plus the head's AUC on the training children's fit trials (representation overfit indicator).

Usage: python -m auditory_alignment.probe_private_head <experiment_id> [...]
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch

from . import data, evaluate, train
from .run import OUT


def main():
    from sklearn.linear_model import LogisticRegression
    from auditory_c3.c3dl.hc import _logit, q0_table
    from auditory_c3.c3dl_stage0 import _fit_offset_logistic
    kids = data.load_private(); dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = {}
    for eid in sys.argv[1:]:
        rec = json.load(open(os.path.join(OUT, "units", f"{eid}.json"))); job = rec["job"]
        enc, bt = train.load_private_unit(job, kids, dev, os.path.join(OUT, "ckpt", f"{eid}_best.pt"))
        tr = bt.train; te = [i for i, k in enumerate(kids) if k["fold"] == job["subject_fold"]]
        U = {i: evaluate._private_reps(enc, bt, i) for i in tr + te}
        q0 = q0_table([kids[i] for i in tr])
        ll = lambda q, y: np.where(y == 1, np.log2(np.clip(q, 1e-12, 1)), np.log2(np.clip(1 - q, 1e-12, 1)))
        res = {}
        for mode in ("all", "es_only", "fit_only"):
            sel = {i: (np.ones(len(kids[i]["y"]), bool) if mode == "all" else (kids[i]["es_mask"] if mode == "es_only" else ~kids[i]["es_mask"])) for i in tr}
            X = np.concatenate([U[i][sel[i]] for i in tr]); y = np.concatenate([kids[i]["y"][sel[i]] for i in tr])
            off = _logit(q0[np.concatenate([kids[i]["bin"][sel[i]] for i in tr])])
            head = LogisticRegression(C=1.0, max_iter=2000).fit(X, y); base = float(y.mean())
            w = _fit_offset_logistic(X, y, off)
            hg, hgw, auc = [], [], []
            for i in te:
                k = kids[i]; yy = k["y"]; p = head.predict_proba(U[i])[:, 1]
                pw = 1 / (1 + np.exp(-(_logit(q0[k["bin"]]) + np.c_[np.ones(len(yy)), U[i]] @ w)))
                hg.append(float((ll(np.clip(p, 1e-6, 1 - 1e-6), yy) - ll(np.full(len(yy), base), yy)).mean()))
                hgw.append(float((ll(pw, yy) - ll(q0[k["bin"]], yy)).mean())); auc.append(evaluate._auc(p, yy))
            Xf = np.concatenate([U[i][~kids[i]["es_mask"]] for i in tr]); yf = np.concatenate([kids[i]["y"][~kids[i]["es_mask"]] for i in tr])
            Xe = np.concatenate([U[i][kids[i]["es_mask"]] for i in tr]); ye = np.concatenate([kids[i]["y"][kids[i]["es_mask"]] for i in tr])
            res[mode] = {"test_head_gain_vs_base_bits": float(np.mean(hg)), "test_head_auc": float(np.nanmean(auc)), "test_hist_gain_bits": float(np.mean(hgw)),
                         "n_fit_rows": int(len(y)), "train_fit_trials_auc": evaluate._auc(head.predict_proba(Xf)[:, 1], yf),
                         "train_es_trials_auc": evaluate._auc(head.predict_proba(Xe)[:, 1], ye)}
        out[eid] = res
        print(eid, json.dumps(res), flush=True)
    json.dump(out, open(os.path.join(OUT, "probe_private_head.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
