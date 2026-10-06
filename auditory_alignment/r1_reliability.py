"""Post-hoc R1 (registered 2026-10-06 before computation): split-half reliability of the EEG-specific gain (spec 10.5).

The unit-level split-half columns use raw rank percentiles per half, which can be driven by which stimulus content a
participant's halves contain. R1 uses per-half gain = mean over the half's queries of [log loss(mismatched EEG) - log loss
(true EEG)], which cancels content effects (same candidates, same calibration, same query targets).
Exact reuse of the evaluation: each unit's best checkpoint is reloaded and evaluate.evaluate_continuous is run unchanged;
the only addition is a wrapper on evaluate._metrics that also returns per-query log losses. QC: the recomputed
full-sample metrics are compared with the stored unit record.

Usage: python -m auditory_alignment.r1_reliability <dataset> <content_fold> <experiment_id> [...]  (all ids share the cohort)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch

from . import data, evaluate, train
from .run import OUT

R1 = os.path.join(OUT, "r1_reliability")
_orig_metrics = evaluate._metrics


def _metrics_plus(s, own, tau):
    out = _orig_metrics(s, own, tau)
    z = s / tau; z = z - z.max(1, keepdims=True)
    out["ll_per_query"] = ((np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), own]) / evaluate.LN2).tolist()
    return out


def main():
    ds, cf, eids = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    os.makedirs(R1, exist_ok=True)
    evaluate._metrics = _metrics_plus
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    coh = {"fau": lambda: data.load_fau(cf, kinds=("ss", "cs")), "dtu": lambda: data.load_dtu(cf, kinds=("ss", "cs")),
           "federici": data.load_federici}[ds]()
    eeg, stim = coh.eeg, coh.stim
    for eid in eids:
        path = os.path.join(R1, f"{eid}.json")
        if os.path.exists(path):
            continue
        rec = json.load(open(os.path.join(OUT, "units", f"{eid}.json"))); job = rec["job"]
        coh.eeg, coh.stim = eeg, stim  # the batcher frees the host copies; restore them for the next unit
        enc, aud, bt = train.load_continuous(job, coh, dev, os.path.join(OUT, "ckpt", f"{eid}_best.pt"))
        ev = evaluate.evaluate_continuous(job["objective"], enc, aud, bt, coh, job, np.random.default_rng(job["seed"] + 1000), rec["objective_calibration"])
        out, qc = {}, []
        for pid, r in ev["per_participant"].items():
            row = {"group": r["group"]}
            for rd in ("unified", "native"):
                a = np.array(r[f"{rd}/regular"]["ll_per_query"]); b = np.array(r[f"{rd}/mismatched_eeg"]["ll_per_query"])
                h = len(a) // 2
                if h >= 2:
                    row[f"{rd}/gain_half0"] = float((b[:h] - a[:h]).mean()); row[f"{rd}/gain_half1"] = float((b[h:] - a[h:]).mean())
                row[f"{rd}/gain_full"] = float((b - a).mean())
                st = rec["eval"]["per_participant"][pid]
                qc.append(abs(row[f"{rd}/gain_full"] - (st[f"{rd}/mismatched_eeg"]["logloss_bits"] - st[f"{rd}/regular"]["logloss_bits"])))
            out[pid] = row
        json.dump({"job": job, "per_participant": out, "qc_max_abs_diff_vs_stored_gain": float(max(qc)) if qc else None}, open(path, "w"))
        print(eid, "qc", f"{max(qc):.2e}" if qc else None, flush=True)


if __name__ == "__main__":
    main()
