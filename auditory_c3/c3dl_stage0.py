"""C3-DL stage 0 (docs/auditory_c3/C3DL_STAGE0_PREREG.md): conditional decoding gain of the frozen GX readout beyond
sequence history, leave-one-child-out logistic heads, null twin. No EEG model is trained.

Usage: python -m auditory_c3.c3dl_stage0
Output: private/auditory_c3/private/c3dl_stage0_children.json (per child, private);
        results/auditory_c3/C3DL_stage0.json (aggregate).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from . import stats
from .private_mi import OUT, P, lane_bank, seed_avg_evidence
from .private_mi2 import hist_codes

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LN2 = np.log(2.0)
C_REG = 1.0


def _ll(p, y):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return np.where(y == 1, np.log(p), np.log(1 - p)) / LN2  # bits


def _logit(p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return np.log(p / (1 - p))


def _ma_amplitude(rid):
    """Model-agnostic, child-comparable T: mean amplitude over all 20 channels and 120-320 ms (250 Hz, pre 50 samples),
    QC-accepted trials in bank order."""
    with np.load(os.path.join(P, "auditory_gx", "GX_stage_001", "epochs", f"{rid}.npz")) as s:
        x = s["x"][s["accepted"].astype(bool)].astype(np.float32)
        pre, fs = int(s["pre_samples"]), float(s["rate_hz"])
    a, b = pre + int(round(0.120 * fs)), pre + int(round(0.320 * fs))
    return x[:, :, a:b].mean(axis=(1, 2))[:, None]


def _fit_offset_logistic(X, y, offset):
    """L2 logistic regression (intercept unpenalised) with a fixed per-sample offset, optimised directly."""
    from scipy.optimize import minimize
    Xa = np.column_stack([np.ones(len(X)), X])

    def f(w):
        z = offset + Xa @ w
        nll = np.sum(np.logaddexp(0, z) - y * z) + 0.5 / C_REG * np.sum(w[1:] ** 2)
        g = Xa.T @ (1 / (1 + np.exp(-z)) - y); g[1:] += w[1:] / C_REG
        return nll, g
    return minimize(f, np.zeros(Xa.shape[1]), jac=True, method="L-BFGS-B").x


def _pred_offset(w, X, offset):
    return 1 / (1 + np.exp(-(offset + np.column_stack([np.ones(len(X)), X]) @ w)))


def main():
    rec, bank = lane_bank("bdf_puretone", accepted_only=True)
    pf = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "records.csv"))
    ch = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "children.csv"))
    assert list(rec.record_id) == list(pf.record_id)
    ev, _ = seed_avg_evidence("GX1_bdf_puretone_shared", len(bank["y"]))
    H = hist_codes(bank["pc"], bank["prl"])
    kids = []
    for _, c in ch.iterrows():
        grp = "HA" if (c.group == "labelled" and bool(c.eligible)) else ("NH" if (c.group == "nh" and bool(c.nh_eligible)) else None)
        if grp is None:
            continue
        m = bank["rec"] == int(c.primary_rec)
        ok = H["since_last_deviant"][m] >= 0
        ma = _ma_amplitude(pf.record_id[int(c.primary_rec)])
        assert len(ma) == int(m.sum())
        kids.append({"id": f"child{int(c.child)}", "group": grp, "duration": float(c.duration_months) if grp == "HA" else None,
                     "y": bank["y"][m][ok].astype(int), "bin": H["since_last_deviant"][m][ok], "prev": H["prev_class"][m][ok].astype(int),
                     "e": ev[m][ok][:, None], "amp": ma[ok]})
    rng = np.random.default_rng(20261008)
    for k in kids:  # null twin: z permuted within (child, history bin), fixed once
        for name in ("e", "amp"):
            Z = k[name].copy()
            for b in np.unique(k["bin"]):
                i = np.flatnonzero(k["bin"] == b); Z[i] = k[name][rng.permutation(i)]
            k[name + "_twin"] = Z
    res = {}
    for i, test in enumerate(kids):
        train = [k for j, k in enumerate(kids) if j != i]
        y_tr = np.concatenate([k["y"] for k in train]); bin_tr = np.concatenate([k["bin"] for k in train])
        prior = y_tr.mean()
        q0_bin = {b: (y_tr[bin_tr == b].sum() + 0.5) / ((bin_tr == b).sum() + 1.0) for b in np.unique(np.r_[bin_tr, test["bin"]])}
        y = test["y"]
        p_prior = np.full(len(y), prior)
        p_hist = np.array([q0_bin[b] for b in test["bin"]])
        off_tr = _logit(np.array([q0_bin[b] for b in bin_tr])); off_te = _logit(p_hist)
        out = {"group": test["group"], "duration": test["duration"], "n_trials": int(len(y)),
               "G_hist": float(np.mean(_ll(p_hist, y) - _ll(p_prior, y)))}
        for zname in ("e", "amp"):
            Ztr = np.concatenate([k[zname] for k in train]); mu, sd = Ztr.mean(0), Ztr.std(0) + 1e-12
            zs = lambda Z: (Z - mu) / sd
            prev_tr = np.concatenate([k["prev"] for k in train])[:, None]
            # naive: calibrated evidence, no history
            lr = LogisticRegression(C=C_REG, max_iter=1000).fit(zs(Ztr), y_tr)
            p_ev = lr.predict_proba(zs(test[zname]))[:, 1]
            # conditional: history offset + evidence + evidence x previous class
            Xtr = np.column_stack([zs(Ztr), zs(Ztr) * prev_tr])
            w = _fit_offset_logistic(Xtr, y_tr, off_tr)
            Xte = np.column_stack([zs(test[zname]), zs(test[zname]) * test["prev"][:, None]])
            p_he = _pred_offset(w, Xte, off_te)
            # null twin
            Ztw = np.concatenate([k[zname + "_twin"] for k in train])
            wt = _fit_offset_logistic(np.column_stack([zs(Ztw), zs(Ztw) * prev_tr]), y_tr, off_tr)
            p_tw = _pred_offset(wt, np.column_stack([zs(test[zname + "_twin"]), zs(test[zname + "_twin"]) * test["prev"][:, None]]), off_te)
            g_naive = float(np.mean(_ll(p_ev, y) - _ll(p_prior, y)))
            g_cond = float(np.mean(_ll(p_he, y) - _ll(p_hist, y)))
            g_null = float(np.mean(_ll(p_tw, y) - _ll(p_hist, y)))
            out[zname] = {"G_naive": g_naive, "G_cond": g_cond, "G_null": g_null, "G_cond_corr": g_cond - g_null}
        res[test["id"]] = out
        print(test["id"], test["group"], "G_hist %.4f | e: naive %.4f cond %.4f null %.4f" % (
            out["G_hist"], out["e"]["G_naive"], out["e"]["G_cond"], out["e"]["G_null"]), flush=True)
    os.makedirs(OUT, mode=0o700, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "c3dl_stage0_children.json"), "w"), indent=1)
    # aggregate
    def stage(v):
        return "HA_early_0_2" if v["duration"] <= 2 else ("HA_late_ge13" if v["duration"] >= 13 else "HA_mid_2_13")
    groups = {"NH": [v for v in res.values() if v["group"] == "NH"], "HA_all": [v for v in res.values() if v["group"] == "HA"]}
    for st in ("HA_early_0_2", "HA_mid_2_13", "HA_late_ge13"):
        groups[st] = [v for v in groups["HA_all"] if stage(v) == st]
    agg = {"prereg": "docs/auditory_c3/C3DL_STAGE0_PREREG.md", "unit": "bits per trial, held-out child"}
    for g, rows in groups.items():
        if len(rows) < 2:
            agg[g] = {"n": len(rows)}; continue
        cell = {"G_hist": stats.mean_ci([r["G_hist"] for r in rows], seed=71)}
        for zname in ("e", "amp"):
            for q in ("G_naive", "G_cond", "G_null", "G_cond_corr"):
                cell[f"{zname}/{q}"] = stats.mean_ci([r[zname][q] for r in rows], seed=72)
            gc, gn, gnull = cell[f"{zname}/G_cond_corr"], cell[f"{zname}/G_naive"], cell[f"{zname}/G_null"]
            cell[f"{zname}/reading"] = (
                "1_current_beyond_history" if gc["ci_low"] > 0 else
                "2_explained_by_history" if (gn["ci_low"] > 0 and gc["ci_low"] <= 0 <= gc["ci_high"] and gc["est"] < 0.25 * gn["est"]) else
                "3_no_detectable_readout_information" if (gn["ci_low"] <= 0 <= gn["ci_high"] and gc["ci_low"] <= 0 <= gc["ci_high"]) else "between_cells")
            cell[f"{zname}/technically_limited"] = bool(abs(gnull["est"]) > 0.25 * abs(cell[f"{zname}/G_cond"]["est"]))
        agg[g] = cell
    os.makedirs(os.path.join(REPO, "results", "auditory_c3"), exist_ok=True)
    json.dump(agg, open(os.path.join(REPO, "results", "auditory_c3", "C3DL_stage0.json"), "w"), indent=1)
    print(json.dumps({g: {k: (round(v["est"], 5), round(v["ci_low"], 5), round(v["ci_high"], 5)) if isinstance(v, dict) and "est" in v else v
                          for k, v in c.items()} for g, c in agg.items() if isinstance(c, dict) and "G_hist" in c}, indent=1))


if __name__ == "__main__":
    main()
