"""DATA_AND_SPLIT_MANIFEST (spec 16.1): participants per outer fold and group, segments / unique stimulus contents per
role and kind, for every cohort and content fold. Counts go to results/; per-participant fold maps stay private.

Usage: python -m auditory_alignment.manifest
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

import numpy as np

from . import data

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results", "auditory_alignment_kernel_cs")
PRIV = os.path.join(REPO, "private", "auditory_alignment_kernel_cs")


def cohort_summary(coh):
    P = coh.participants
    by_fold = defaultdict(Counter)
    for p in P:
        f = "test_only" if p.get("test_only") else ("dev_train_only" if p.get("dev") else f"fold{p['fold']}")
        by_fold[f][p["group"]] += 1
    seg = defaultdict(Counter); uids = defaultdict(set); seconds = defaultdict(float)
    for s in coh.segments:
        k = f"{s['kind']}/{s['role']}"
        seg[k][P[s["p"]]["group"]] += 1; uids[k].add(s["uid"]); seconds[k] += coh.meta["seg_len"] / coh.fs
    leak = {}
    for kind in ("ss", "cs"):
        a = {r: uids.get(f"{kind}/{r}", set()) for r in ("fit", "es", "test")}
        leak[kind] = {"fit&test": len(a["fit"] & a["test"]), "es&test": len(a["es"] & a["test"]), "fit&es": len(a["fit"] & a["es"])}
    return {"fs": coh.fs, "n_channels": coh.n_ch, "segment_seconds": coh.meta["seg_len"] / coh.fs,
            "participants_by_fold": {k: dict(v) for k, v in sorted(by_fold.items())},
            "segments_by_kind_role_group": {k: dict(v) for k, v in sorted(seg.items())},
            "unique_stimulus_segments_by_kind_role": {k: len(v) for k, v in sorted(uids.items())},
            "eeg_hours_by_kind_role": {k: round(v / 3600, 2) for k, v in sorted(seconds.items())},
            "content_overlap_between_roles": leak}


def main():
    out, priv = {}, {}
    for cf in (0, 1):
        coh = data.load_fau(cf, kinds=("ss", "cs")); out[f"fau_cf{cf}"] = cohort_summary(coh)
        priv[f"fau_cf{cf}"] = {p["id"]: {"group": p["group"], "fold": p["fold"], "dev": bool(p.get("dev"))} for p in coh.participants}
        coh = data.load_dtu(cf, kinds=("ss", "cs")); out[f"dtu_cf{cf}"] = cohort_summary(coh)
        priv[f"dtu_cf{cf}"] = {p["id"]: {"group": p["group"], "fold": p["fold"]} for p in coh.participants}
    coh = data.load_federici(); out["federici"] = cohort_summary(coh)
    priv["federici"] = {p["id"]: {"group": p["group"], "fold": p["fold"], "test_only": bool(p.get("test_only"))} for p in coh.participants}
    kids = data.load_private()
    pf = defaultdict(Counter)
    for k in kids:
        pf[f"fold{k['fold']}"][k["group"]] += 1
    out["private_bdf"] = {"participants_by_fold": {k: dict(v) for k, v in sorted(pf.items())},
                          "trials_total": int(sum(len(k["y"]) for k in kids)),
                          "trials_early_stop_blocks": int(sum(int(k["es_mask"].sum()) for k in kids)),
                          "deviant_rate": float(np.mean(np.concatenate([k["y"] for k in kids]))),
                          "children_with_age": int(sum(k["age_months"] is not None for k in kids)),
                          "ha_children_with_duration": int(sum(k["duration_months"] is not None for k in kids))}
    priv["private_bdf"] = {k["id"]: {"group": k["group"], "fold": k["fold"], "n_trials": int(len(k["y"])), "n_es": int(k["es_mask"].sum())} for k in kids}
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "DATA_AND_SPLIT_MANIFEST.json"), "w"), indent=1)
    json.dump(priv, open(os.path.join(PRIV, "DATA_AND_SPLIT_MANIFEST_participants.json"), "w"), indent=1)
    print(json.dumps(out, indent=1)[:6000])


if __name__ == "__main__":
    main()
