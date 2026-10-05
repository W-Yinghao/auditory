"""Private H4-H6, version 2 (C3 review addendum 2026-10-05, items 2, 5, 6, 7, 9). Supersedes the interpretation of
private_mi.py (v1 outputs kept). Changes:
  * mixed-type estimators with an explicit definition: I(T; Y) for continuous T and discrete Y is the class-
    conditional Gaussian model on the copula-normalised T of the analysed sample set; I(T; Y | Z) = sum_z p(z) of that
    model fitted *within* each stratum z (T copula-normalised within the stratum). Classes / strata without support
    (< MIN_SUPPORT trials) are excluded and their probability mass is recorded - never merged by numeric proximity,
    never returned as a scientific 0. The plug-in bound H(Y | Z) is stored next to every CMI and violations flagged;
  * full ledger: I(T;Cur), I(T;Hist), I(T;Cur,Hist), I(T;Cur|Hist), I(T;Hist|Cur);
  * Hist bins fixed for every child and surrogate: standards since the last deviant {0},{1},{2},{3},{4,5},{6+}
    (0 = previous sound was a deviant); previous class; previous run length {1},{2},{3},{4,5},{6+}. History is the
    pre-QC chain up to the previous sound (strictly before the current event; unknown at chain starts -> excluded);
  * one null per quantity: total MI -> T permuted across trials; I(T;Hist|Cur) -> T permuted within Cur;
    I(T;Cur|Hist) -> T permuted within Hist bins; a time-series sensitivity for I(T;Cur) -> circular shift of T.
    Stored: estimate_analytic, surrogate_mean, null_excess, surrogate_type, n_sur;
  * T: frozen EEGNet evidence (primary; conclusions concern that readout only) and the package's model-agnostic
    sensitivity (mean 120-320 ms amplitude per channel, first 3 PCs within child);
  * cohort count <24 months AND HA duration <= 2 months.
Usage: python -m auditory_c3.private_mi2 <h4h5|h6>
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from scipy.special import psi

from .engine import copnorm_rows
from .private_mi import OUT, P, lane_bank, seed_avg_evidence

LN2 = np.log(2.0)
MIN_SUPPORT = 10
N_SUR = 200
BINS_SINCE = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 5), (6, 99)]
BINS_RUN = [(1, 1), (2, 2), (3, 3), (4, 5), (6, 99)]


def _ent_g(X):
    """Bias-corrected Gaussian entropy (bits), X (n, d) - Ince's correction, as gcmi_core.ent_g."""
    n, d = X.shape
    C = np.cov(X, rowvar=False).reshape(d, d)
    h = np.sum(np.log(np.diag(np.linalg.cholesky(C)))) + 0.5 * d * np.log(2 * np.pi * np.e)
    h -= d * (LN2 - np.log(n - 1)) / 2.0 + psi((n - np.arange(1, d + 1)) / 2.0).sum() / 2.0
    return h / LN2


def mi_cd(T, y):
    """Class-conditional Gaussian MI on copula-normalised T (n, d) with discrete y. Returns (bits or nan, info)."""
    T = np.atleast_2d(np.asarray(T, float).T).T if np.ndim(T) == 1 else np.asarray(T, float)
    y = np.asarray(y)
    vals, cnt = np.unique(y, return_counts=True)
    keep_vals = vals[cnt >= MIN_SUPPORT]
    m = np.isin(y, keep_vals)
    info = {"n": int(len(y)), "classes": int(len(vals)), "classes_kept": int(len(keep_vals)), "retained_mass": float(m.mean())}
    if len(keep_vals) < 2:
        return np.nan, dict(info, status="INSUFFICIENT_SUPPORT")
    Z = copnorm_rows(T[m].T).T
    yy = y[m]
    h = _ent_g(Z) - sum(np.mean(yy == v) * _ent_g(Z[yy == v]) for v in keep_vals)
    p = np.array([np.mean(yy == v) for v in keep_vals])
    info["H_y_bits"] = float(-(p * np.log2(p)).sum())
    return float(h), dict(info, status="OK")


def cmi_cd(T, y, z):
    """sum_z p(z) mi_cd(T_z, y_z), T copula-normalised within each stratum; unsupported strata excluded (mass kept)."""
    T = np.asarray(T, float).reshape(len(y), -1)
    zs, zc = np.unique(z, return_counts=True)
    tot, mass, hb = 0.0, 0.0, 0.0
    for zv, c in zip(zs, zc):
        m = z == zv
        v, inf = mi_cd(T[m], y[m])
        if np.isfinite(v):
            tot += c * v; mass += c; hb += c * inf["H_y_bits"]
    if mass == 0:
        return np.nan, {"status": "INSUFFICIENT_SUPPORT", "retained_mass": 0.0}
    est, bound = tot / mass, hb / mass
    return float(est), {"status": "OK", "retained_mass": float(mass / len(y)), "H_y_given_z_bits": float(bound),
                        "bound_violation": bool(est > bound + 1e-9)}


def _bin(v, bins):
    out = np.full(len(v), -1)
    for i, (lo, hi) in enumerate(bins):
        out[(v >= lo) & (v <= hi)] = i
    return out


def hist_codes(pc, prl):
    known = pc >= 0
    since = np.full(len(pc), -1)
    since[known & (pc == 1)] = 0
    ok = known & (pc == 0) & (prl >= 1)
    since[ok] = _bin(np.minimum(prl[ok], 99), BINS_SINCE[1:]) + 1  # previous sound a standard closing a run of prl standards
    run = np.where(known & (prl >= 1), _bin(prl, BINS_RUN), -1)
    prev = np.where(known, pc, -1)
    return {"since_last_deviant": since, "prev_class": prev, "prev_run_length": run}


def ledger(T, cur, hist, rng):
    """Full current/history ledger with one null per quantity."""
    T = np.asarray(T, float).reshape(len(cur), -1)
    out = {}

    def stats(name, fn, null):
        obs, info = fn(T)
        sur = []
        for _ in range(N_SUR):
            Tp = null(T)
            v, _ = fn(Tp)
            sur.append(v)
        sur = np.array(sur, float)
        out[name] = dict(info, estimate_analytic=obs, surrogate_mean=float(np.nanmean(sur)),
                         null_excess=float(obs - np.nanmean(sur)) if np.isfinite(obs) else np.nan,
                         surrogate_type=null.__name__, n_sur=int(np.isfinite(sur).sum()))

    def perm_all(X):
        return X[rng.permutation(len(X))]

    def within(labels):
        def perm_within(X):
            Y = X.copy()
            for v in np.unique(labels):
                i = np.flatnonzero(labels == v); Y[i] = X[rng.permutation(i)]
            return Y
        return perm_within

    def circ(X):
        return np.roll(X, int(rng.integers(len(X) // 10, len(X) - len(X) // 10)), axis=0)

    stats("I_T_Cur", lambda X: mi_cd(X, cur), perm_all)
    stats("I_T_Cur_circular_null", lambda X: mi_cd(X, cur), circ)
    for hn, h in hist.items():
        m = h >= 0
        Tm, cm, hm = T[m], cur[m], h[m]
        joint = cm * 100 + hm
        for name, fn, null in ((f"I_T_Hist/{hn}", lambda X: mi_cd(X, hm), perm_all),
                               (f"I_T_CurHist/{hn}", lambda X: mi_cd(X, joint), perm_all),
                               (f"I_T_Cur_given_Hist/{hn}", lambda X: cmi_cd(X, cm, hm), within(hm)),
                               (f"I_T_Hist_given_Cur/{hn}", lambda X: cmi_cd(X, hm, cm), within(cm))):
            obs, info = fn(Tm)
            sur = np.array([fn(null(Tm))[0] for _ in range(N_SUR)], float)
            out[name] = dict(info, estimate_analytic=obs, surrogate_mean=float(np.nanmean(sur)),
                             null_excess=float(obs - np.nanmean(sur)) if np.isfinite(obs) else np.nan,
                             surrogate_type=null.__name__, n_sur=int(np.isfinite(sur).sum()), n_trials=int(m.sum()))
    return out


def model_agnostic_T(rec_ids, mask_bank, bank_rec):
    """Mean 120-320 ms amplitude per channel (250 Hz epochs, pre 50 samples) -> first 3 PCs within the child."""
    import glob
    out = []
    for rid in rec_ids:
        with np.load(os.path.join(P, "auditory_gx", "GX_stage_001", "epochs", f"{rid}.npz")) as s:
            x = s["x"][s["accepted"].astype(bool)].astype(np.float32)
            pre, fs = int(s["pre_samples"]), float(s["rate_hz"])
        a, b = pre + int(round(0.120 * fs)), pre + int(round(0.320 * fs))
        out.append(x[:, :, a:b].mean(2))
    A = np.concatenate(out)
    A = A - A.mean(0)
    w, V = np.linalg.eigh(A.T @ A)
    return A @ V[:, np.argsort(w)[::-1][:3]]


def run_h4h5():
    import pandas as pd
    rec, bank = lane_bank("bdf_puretone", accepted_only=True)
    pf = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "records.csv"))
    ch = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "children.csv"))
    assert list(rec.record_id) == list(pf.record_id)
    ev, cnt = seed_avg_evidence("GX1_bdf_puretone_shared", len(bank["y"]))
    H = hist_codes(bank["pc"], bank["prl"])
    res = {"definition": __doc__, "children": {}}
    rng = np.random.default_rng(20261005)
    elig = []
    for _, c in ch.iterrows():
        grp = "HA" if (c.group == "labelled" and bool(c.eligible)) else ("NH" if (c.group == "nh" and bool(c.nh_eligible)) else None)
        if grp is None:
            continue
        elig.append((c, grp))
        m = bank["rec"] == int(c.primary_rec)
        cur = bank["y"][m].astype(int)
        hist = {k: v[m] for k, v in H.items()}
        q = {"group": grp, "age_months": float(c.age_months), "duration_months": float(c.duration_months) if grp == "HA" else None,
             "n_trials": int(m.sum())}
        q["evidence"] = ledger(ev[m], cur, hist, rng)
        Tma = model_agnostic_T([pf.record_id[int(c.primary_rec)]], None, None)
        assert len(Tma) == len(cur), (len(Tma), len(cur))
        q["model_agnostic_pc3"] = ledger(Tma, cur, hist, rng)
        res["children"][f"child{int(c.child)}"] = q
        e = q["evidence"]
        print(grp, int(c.child), "I(T;Cur) %.4f I(T;Cur|Hist) %.4f I(T;Hist|Cur) %.4f" % (
            e["I_T_Cur"]["null_excess"], e["I_T_Cur_given_Hist/since_last_deviant"]["null_excess"],
            e["I_T_Hist_given_Cur/since_last_deviant"]["null_excess"]), flush=True)
    young = [c for c, g in elig if g == "HA" and c.age_months < 24 and c.duration_months <= 2]
    res["cohort_counts"] = {"HA_eligible": sum(g == "HA" for _, g in elig), "NH_eligible": sum(g == "NH" for _, g in elig),
                            "HA_age_lt24_and_duration_le2": len(young),
                            "HA_duration_le2_any_age": sum(1 for c, g in elig if g == "HA" and c.duration_months <= 2)}
    os.makedirs(OUT, mode=0o700, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "h4h5_children_v2.json"), "w"), indent=1, default=float)
    print("cohort", res["cohort_counts"])


def run_h6():
    from .private_mi import lane_bank as lb
    rec, bank = lb("mff_unknown_event", accepted_only=False)
    meta = json.load(open(os.path.join(P, "auditory_gx", "GX1_mff_unknown_event_shared_allqc", "record_meta.json")))
    assert [m["record_id"] for m in meta] == list(rec.record_id)
    n = len(bank["y"])
    E = {name: seed_avg_evidence(run, n)[0] for name, run in (
        ("full", "GX1_mff_unknown_event_shared_allqc"), ("b1_4", "GX1_mff_unknown_event_shared_allqc_band_1_4"),
        ("b4_8", "GX1_mff_unknown_event_shared_allqc_band_4_8"), ("b30_45", "GX1_mff_unknown_event_shared_allqc_band_30_45"))}
    child_of = {m["record_id"]: m["child"] for m in meta}
    ci = {}
    for _, r in rec.iterrows():
        ci[child_of[r.record_id]] = ci.get(child_of[r.record_id], False) or r.source in ("CI", "CIHA_label")
    tc = np.array([child_of[rec.record_id[i]] for i in bank["rec"]])
    rng = np.random.default_rng(20261006)
    res = {"definition": "class-conditional Gaussian on copula-normalised band evidence; no class merging; T permuted across trials as null", "children": {}}
    for c in sorted(ci):
        m = tc == c; y = bank["y"][m].astype(int)
        low = np.column_stack([E["b1_4"][m], E["b4_8"][m]]); high = E["b30_45"][m][:, None]
        q = {"ci": bool(ci[c]), "n_trials": int(m.sum())}
        for name, X in (("I_cls_low", low), ("I_cls_high", high), ("I_cls_low_high", np.column_stack([low, high])), ("I_cls_full", E["full"][m][:, None])):
            obs, info = mi_cd(X, y)
            sur = np.array([mi_cd(X[rng.permutation(len(X))], y)[0] for _ in range(N_SUR)])
            q[name] = dict(info, estimate_analytic=obs, surrogate_mean=float(np.nanmean(sur)), null_excess=float(obs - np.nanmean(sur)), surrogate_type="perm_all")
        q["I_cls_high_given_low"] = {"null_excess": q["I_cls_low_high"]["null_excess"] - q["I_cls_low"]["null_excess"],
                                     "note": "difference of two model MIs under the same null (chain rule within one model family)"}
        res["children"][f"child{c}"] = q
    json.dump(res, open(os.path.join(OUT, "h6_children_v2.json"), "w"), indent=1, default=float)
    print("h6 v2 children", len(res["children"]))


if __name__ == "__main__":
    {"h4h5": run_h4h5, "h6": run_h6}[sys.argv[1]]()
