"""Private H4-H6 (05_PRIVATE_ANALYSIS as amended by MEASUREMENT_AMENDMENT_001 §2, §8). Reuses cached frozen-EEGNet
single-trial evidence only (no new model, no inference). Per-child outputs stay in private/auditory_c3/private/.

H4/H5 (HA/BDF pure-tone lane, GX1_bdf_puretone_shared): T = seed-averaged out-of-fold evidence (logit1 - logit0) per
QC-accepted trial; Cur = current class; Hist (primary) = standards since the last deviant, capped at 8 (0 when the
previous sound was a deviant), from the pre-QC event chain stored with each staged record; trials whose previous run is
incomplete are excluded from Hist quantities. Sensitivity: Hist = previous class; Hist = previous run length (cap 8).
Child level = the PF primary record (private/auditory_pf/prepare_002/children.csv; eligible HA = labelled with >= 80
trials per class; NH eligible likewise). Nulls: I(T;Cur) by within-child label permutation (class ratio preserved);
I(T;Hist|Cur) by permuting T within each current class (S7). n_sur = 200.
H6 (MFF unknown-event lane, allqc runs): per child, I(cls; low) with low = (1-4 Hz, 4-8 Hz evidence) and
I(cls; high | low) with high = 30-45 Hz evidence; null by within-child label permutation.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(REPO, "private")
sys.path.insert(0, os.path.join(REPO, "AUDITORY_C3_SERVER_PACKAGE_v1_20261003", "reference"))
from gcmi_core import cmi_model_gdd, gcmi_ccc, gcmi_model_cd  # noqa: E402

OUT = os.path.join(P, "auditory_c3", "private")
N_SUR = 200
CAP = 8


def seed_avg_evidence(run, n):
    acc = np.zeros((n, 2)); cnt = np.zeros(n)
    with np.load(os.path.join(P, "auditory_gx", run, "predictions_shared.npz")) as s:
        for k in s.files:
            a = s[k]; idx = a[:, 0].astype(int)
            acc[idx] += a[:, 1:3]; cnt[idx] += 1
    ev = np.full(n, np.nan); ok = cnt > 0
    ev[ok] = (acc[ok, 1] - acc[ok, 0]) / cnt[ok]
    return ev, cnt


def lane_bank(lane, accepted_only):
    """Trial arrays in auditory_gx.data.load_lane order (same staged files, majority channels, accept rule)."""
    pay = []
    for p in sorted(glob.glob(os.path.join(P, "auditory_gx", "GX_stage_001", "epochs", "*.npz"))):
        with np.load(p) as s:
            if str(s["lane"]) != lane:
                continue
            pay.append({k: s[k] for k in ("record_id", "identity_group", "y", "accepted", "previous_code",
                                          "previous_run_length", "history_status", "n_channels", "source_cohort_evidence")})
    counts = {}
    for d in pay:
        counts[int(d["n_channels"])] = counts.get(int(d["n_channels"]), 0) + 1
    maj = max(counts, key=counts.get)
    rows, out = [], {k: [] for k in ("rec", "y", "pc", "prl", "hs")}
    for d in pay:
        if int(d["n_channels"]) != maj:
            continue
        keep = d["accepted"].astype(bool) if accepted_only else np.ones(len(d["y"]), bool)
        if keep.sum() == 0:
            continue
        ri = len(rows)
        rows.append({"rec": ri, "record_id": str(d["record_id"]), "identity_group": str(d["identity_group"]),
                     "source": str(d["source_cohort_evidence"]), "n": int(keep.sum())})
        out["rec"].append(np.full(int(keep.sum()), ri)); out["y"].append(d["y"][keep])
        out["pc"].append(d["previous_code"][keep]); out["prl"].append(d["previous_run_length"][keep]); out["hs"].append(d["history_status"][keep])
    return pd.DataFrame(rows), {k: np.concatenate(v) for k, v in out.items()}


def hist_vars(pc, prl, hs):
    known = (pc >= 0)
    since = np.full(len(pc), np.nan)
    since[known & (pc == 1)] = 0
    ok_run = known & (pc == 0) & (prl >= 1)
    since[ok_run] = np.minimum(prl[ok_run], CAP)
    run = np.where(known & (prl >= 1), np.minimum(prl, CAP), np.nan)
    prev = np.where(known, pc, np.nan)
    return {"since_last_deviant": since, "prev_class": prev, "prev_run_length": run}


def child_quantities(T, cur, H, rng):
    out = {}
    obs = gcmi_model_cd(T, cur)
    sur = np.array([gcmi_model_cd(T, rng.permutation(cur)) for _ in range(N_SUR)])
    out["I_T_Cur"] = {"obs": obs, "sur_mean": float(sur.mean()), "corr": float(obs - sur.mean()), "p": float((np.sum(sur >= obs) + 1) / (N_SUR + 1))}
    for hname, h in H.items():
        m = np.isfinite(h)
        t, c, hh = T[m], cur[m], h[m].astype(int)
        obs = cmi_model_gdd(t, hh, c)
        sur = np.empty(N_SUR)
        for b in range(N_SUR):
            tp = t.copy()
            for cl in np.unique(c):
                idx = np.flatnonzero(c == cl); tp[idx] = t[rng.permutation(idx)]
            sur[b] = cmi_model_gdd(tp, hh, c)
        i_th = gcmi_model_cd(t, hh)
        out[f"I_T_Hist_given_Cur/{hname}"] = {"obs": float(obs), "sur_mean": float(sur.mean()), "corr": float(obs - sur.mean()),
                                              "p": float((np.sum(sur >= obs) + 1) / (N_SUR + 1)), "n_trials": int(m.sum()),
                                              "I_T_Hist_raw": float(i_th)}
    return out


def run_h4h5():
    rec, bank = lane_bank("bdf_puretone", accepted_only=True)
    pf = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "records.csv"))
    ch = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "children.csv"))
    assert list(rec.record_id) == list(pf.record_id), "record order differs from PF/GX bank"
    n = len(bank["y"])
    ev, cnt = seed_avg_evidence("GX1_bdf_puretone_shared", n)
    assert n == 74921 and np.all(cnt == 3), (n, np.unique(cnt))
    H = hist_vars(bank["pc"], bank["prl"], bank["hs"])
    # EEG-age sensitivity covariate: bias-corrected age prediction mapped via D1 container ids
    gap = json.load(open(os.path.join(P, "auditory_d2", "D2_bdf_clinical_002_gap.json")))
    units = json.load(open(os.path.join(P, "auditory_d2", "D1_bdf_001_cohort.json")))["units"]
    cont = {u["identity"]: u["container_id"] for u in units}
    eeg_age = {cont[i]: a + g for i, a, g in zip(gap["identities"], gap["ages"], gap["corrected_gap"]) if i in cont}
    pf["eeg_age_bc"] = pf.d1_container_id.map(eeg_age)
    res = {}
    rng = np.random.default_rng(20261005)
    for _, c in ch.iterrows():
        grp = "HA" if (c.group == "labelled" and bool(c.eligible)) else ("NH" if (c.group == "nh" and bool(c.nh_eligible)) else None)
        if grp is None:
            continue
        r = pf.loc[int(c.primary_rec)]
        m = bank["rec"] == int(c.primary_rec)
        q = child_quantities(ev[m], bank["y"][m].astype(int), {k: v[m] for k, v in H.items()}, rng)
        q.update(group=grp, age_months=float(c.age_months), duration_months=float(c.duration_months) if grp == "HA" else None,
                 eeg_age_bc=float(r.eeg_age_bc) if pd.notna(r.eeg_age_bc) else None, n_trials=int(m.sum()),
                 n_dev=int((bank["y"][m] == 1).sum()))
        res[f"child{int(c.child)}"] = q
        print(grp, int(c.child), "I_T_Cur %.4f  I_T_Hist|Cur %.4f" % (q["I_T_Cur"]["corr"], q["I_T_Hist_given_Cur/since_last_deviant"]["corr"]), flush=True)
    os.makedirs(OUT, mode=0o700, exist_ok=True)
    json.dump({"note": "per-child, private; do not publish", "children": res}, open(os.path.join(OUT, "h4h5_children.json"), "w"), indent=1)


def run_h6():
    rec, bank = lane_bank("mff_unknown_event", accepted_only=False)
    meta = json.load(open(os.path.join(P, "auditory_gx", "GX1_mff_unknown_event_shared_allqc", "record_meta.json")))
    assert [m["record_id"] for m in meta] == list(rec.record_id) and [m["n_trials"] for m in meta] == list(rec.n), "bank order"
    n = len(bank["y"])
    E = {}
    for name, run in (("full", "GX1_mff_unknown_event_shared_allqc"), ("b1_4", "GX1_mff_unknown_event_shared_allqc_band_1_4"),
                      ("b4_8", "GX1_mff_unknown_event_shared_allqc_band_4_8"), ("b30_45", "GX1_mff_unknown_event_shared_allqc_band_30_45")):
        E[name], cnt = seed_avg_evidence(run, n)
        assert np.all(cnt == 3), (name, np.unique(cnt))
    child_of = {m["record_id"]: m["child"] for m in meta}
    ci_child = {}
    for _, r in rec.iterrows():
        c = child_of[r.record_id]
        ci_child[c] = ci_child.get(c, False) or r.source in ("CI", "CIHA_label")
    res = {}
    rng = np.random.default_rng(20261006)
    trial_child = np.array([child_of[rec.record_id[i]] for i in bank["rec"]])
    for c in sorted(ci_child):
        m = trial_child == c
        y = bank["y"][m].astype(int)
        low = np.column_stack([E["b1_4"][m], E["b4_8"][m]]); high = E["b30_45"][m][:, None]
        both = np.column_stack([low, high])
        def stats(fn):
            obs = fn(y); sur = np.array([fn(rng.permutation(y)) for _ in range(N_SUR)])
            return {"obs": float(obs), "sur_mean": float(sur.mean()), "corr": float(obs - sur.mean()), "p": float((np.sum(sur >= obs) + 1) / (N_SUR + 1))}
        q = {"I_cls_low": stats(lambda yy: gcmi_model_cd(low, yy)),
             "I_cls_high": stats(lambda yy: gcmi_model_cd(high, yy)),
             "I_cls_low_high": stats(lambda yy: gcmi_model_cd(both, yy)),
             "I_cls_full": stats(lambda yy: gcmi_model_cd(E["full"][m], yy))}
        q["I_cls_high_given_low"] = {k: q["I_cls_low_high"][k] - q["I_cls_low"][k] for k in ("obs", "sur_mean", "corr")}
        r_ = min(q["I_cls_low"]["corr"], q["I_cls_high"]["corr"])
        q["MMI"] = {"R": r_, "U_low": q["I_cls_low"]["corr"] - r_, "U_high": q["I_cls_high"]["corr"] - r_,
                    "S": q["I_cls_low_high"]["corr"] - q["I_cls_low"]["corr"] - q["I_cls_high"]["corr"] + r_}
        q.update(ci=bool(ci_child[c]), n_trials=int(m.sum()))
        res[f"child{c}"] = q
        print("CI" if ci_child[c] else "nonCI", c, "low %.4f high|low %.4f" % (q["I_cls_low"]["corr"], q["I_cls_high_given_low"]["corr"]), flush=True)
    os.makedirs(OUT, mode=0o700, exist_ok=True)
    json.dump({"note": "per-child, private; do not publish", "children": res}, open(os.path.join(OUT, "h6_children.json"), "w"), indent=1)


if __name__ == "__main__":
    {"h4h5": run_h4h5, "h6": run_h6}[sys.argv[1]]()
