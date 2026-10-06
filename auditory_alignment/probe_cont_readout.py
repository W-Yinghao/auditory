"""Diagnostic probe (not part of the unit protocol): continuous-speech readouts fitted on gradient-exposed training segments
(current: training participants' fit + es segments, alpha on es, temperature on es queries) versus fitted only on content
never used for gradient steps (es content split by stimulus uid into half A = bridge fit, half B = alpha and temperature).
Reports test-participant gain_bits / rank_pct for both readouts.

Usage: python -m auditory_alignment.probe_cont_readout <experiment_id> [...]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
import torch

from . import data, evaluate, train
from .run import OUT


def es_split_readouts(objective, reps, segs, train_p, kind, rng):
    half = lambda uid: int(hashlib.sha1(uid.encode()).hexdigest(), 16) % 2
    es = [dict(s) for s in segs if s["p"] in train_p and s["role"] == "es" and s["kind"] == kind]
    for s in es:
        s["role"] = "fit" if half(s["uid"]) == 0 else "es"
    ro = evaluate.Readouts(objective, reps, es, rng)
    # Readouts refits on fit+es with the chosen alpha; restore the half-A-only bridge to keep half B held out
    A = [s for s in es if s["role"] == "fit"]; sel = rng.choice(len(A), size=min(400, len(A)), replace=False); A = [A[i] for i in sel]
    U = reps.u([s["e0"] for s in A]); V, Aa = reps.va([s["s0"] for s in A])
    U2, V2, A2 = (x.reshape(-1, x.shape[-1]) for x in (U, V, Aa))
    ro.B_uni = evaluate._ridge(U2, (A2 - ro.a_mu) / ro.a_sd, [ro.alpha_uni])[0]
    if objective in ("CS_SINGLE", "CS_MULTI"):
        ro.B_nat = evaluate._ridge(U2, V2, [ro.alpha_nat])[0]
    if objective == "FMCA":
        ro.Wu, ro.Wv, ro.rho = evaluate._cca(U2, V2); ro.mu_u, ro.mu_v = U2.mean(0), V2.mean(0)
    B = [s for s in es if s["role"] == "es"]
    uid, rows = {}, []
    for s in B:
        if s["uid"] not in uid:
            uid[s["uid"]] = len(rows); rows.append(s)
    q = [B[i] for i in rng.choice(len(B), size=min(300, len(B)), replace=False)]
    Vc, Ac = reps.va([r["s0"] for r in rows]); Uq = reps.u([s["e0"] for s in q]); own = np.array([uid[s["uid"]] for s in q])
    ro.calibrate({"unified": ro.scores(Uq, Vc, Ac, "unified"), "native": ro.scores(Uq, Vc, Ac, "native")}, own)
    return ro


def test_metrics(ro, reps, coh, job, kind="ss"):
    segs = coh.segments
    uid, rows = {}, []
    for s in segs:
        if s["role"] == "test" and s["kind"] == kind and s["uid"] not in uid:
            uid[s["uid"]] = len(rows); rows.append(s)
    Vc, Ac = reps.va([r["s0"] for r in rows])
    out = {"unified": [], "native": []}
    for p in sorted({s["p"] for s in segs if s["role"] == "test" and coh.participants[s["p"]]["fold"] == job["subject_fold"]}):
        q = [s for s in segs if s["p"] == p and s["role"] == "test" and s["kind"] == kind]
        if not q:
            continue
        Uq = reps.u([s["e0"] for s in q]); own = np.array([uid[s["uid"]] for s in q]); Umm = np.roll(Uq, 1, axis=0)
        for r in out:
            a = evaluate._metrics(ro.scores(Uq, Vc, Ac, r), own, ro.tau[r]); b = evaluate._metrics(ro.scores(Umm, Vc, Ac, r), own, ro.tau[r])
            out[r].append((b["logloss_bits"] - a["logloss_bits"], a["rank_pct"]))
    return {r: {"gain_bits": float(np.mean([x[0] for x in v])), "rank_pct": float(np.mean([x[1] for x in v])), "n": len(v)} for r, v in out.items()}


def main():
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); res = {}
    for eid in sys.argv[1:]:
        rec = json.load(open(os.path.join(OUT, "units", f"{eid}.json"))); job = rec["job"]
        coh = {"fau": lambda: data.load_fau(job["content_fold"], kinds=("ss", "cs")), "dtu": lambda: data.load_dtu(job["content_fold"], kinds=("ss", "cs")),
               "federici": data.load_federici}[job["dataset"]]()
        enc, aud, bt = train.load_continuous(job, coh, dev, os.path.join(OUT, "ckpt", f"{eid}_best.pt"))
        reps = evaluate.Reps(enc, aud, bt)
        cur = {r: {"gain_bits": float(np.mean([v[f"{r}/mismatched_eeg"]["logloss_bits"] - v[f"{r}/regular"]["logloss_bits"] for v in rec["eval"]["per_participant"].values()])),
                   "rank_pct": float(np.mean([v[f"{r}/regular"]["rank_pct"] for v in rec["eval"]["per_participant"].values()]))} for r in ("unified", "native")}
        ro = es_split_readouts(job["objective"], reps, coh.segments, bt.train_p, bt.kind, np.random.default_rng(job["seed"] + 1000))
        res[eid] = {"current_protocol": cur, "es_split": test_metrics(ro, reps, coh, job), "alpha_es_split": ro.alpha_uni}
        print(eid, json.dumps(res[eid]), flush=True)
    json.dump(res, open(os.path.join(OUT, "probe_cont_readout.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
