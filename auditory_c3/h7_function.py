"""H7a function analysis (docs/auditory_c3/H7_FUNCTION_PREREG.md, registered before any behavioural value was seen).

CI adults (FAU/TUD): leave-one-participant-out OLS prediction of logit-transformed HSM (and, secondary, better-ear
Freiburg 65 dB) from C (age, longer-side CI experience), S = I(T;Ac), G = I(T;L27 | yAc) and the artifact index
A = I(T;Ac) in the pre-stimulus diagnostic window; all neural terms are the 3-ROI mean of the frozen main_v2 outputs
(0-600 ms window except A). Sensitivity: G replaced by Gz = I(T;Lz | yAc) (l27z).

Table 4 of Jehn et al. (NeuroImage 2026, doi 10.1016/j.neuroimage.2026.121771) is parsed from the private PDF copy by
word coordinates; the parsed table and a linkage receipt stay under private/.

Usage: python -m auditory_c3.h7_function  ->  results/auditory_c3/H7_function.json (summary values only)
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re

import numpy as np

from . import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIV = os.path.join(REPO, "private", "auditory_c3", "jehn_behaviour")
PDF = os.path.join(PRIV, "neuroimage_2026_121771.pdf")
PUB = os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud")
OUT = os.path.join(REPO, "results", "auditory_c3", "H7_function.json")
ROIS = ["frontocentral", "left_temporal", "right_temporal"]
COLS = [("ID", 40), ("Age", 58), ("Sex", 76), ("CIexpR", 95), ("CIexpL", 124), ("ImplR", 150), ("ImplL", 186),
        ("ProcR", 222), ("ProcL", 262), ("CodR", 304), ("CodL", 340), ("MonoR", 376), ("MonoL", 416), ("HSM", 453),
        ("Etio", 489)]
N_BOOT, SEED = 2000, 7701


def parse_table4():
    import fitz
    page = fitz.open(PDF)[16]
    W = page.get_text("words")
    rows = sorted([w for w in W if 40 < w[0] < 50 and re.fullmatch(r"\d{3}", w[4]) and w[1] > 150], key=lambda w: w[1])
    gaps = np.diff([r[1] for r in rows])
    ends = [r[1] for r in rows[1:]] + [rows[-1][1] + float(np.median(gaps))]
    out = []
    for r, e in zip(rows, ends):
        cells = {k: [] for k, _ in COLS}
        for w in W:
            if r[1] - 1 <= w[1] < e - 1 and 40 <= w[0] < 560:
                cells[[k for k, x in COLS if w[0] >= x][-1]].append(w[4])
        out.append({k: " ".join(v) for k, v in cells.items()})
    return out


def _num(x):
    return float(x) if re.fullmatch(r"\d+(\.\d+)?", x) else np.nan


def _logit_pct(p):
    return np.log((p + 0.5) / 101.0) - np.log(1 - (p + 0.5) / 101.0)


def _loo(X, y):
    """Leave-one-out OLS squared errors; predictors standardised within each training fold."""
    n = len(y); e = np.empty(n); pred = np.empty(n)
    for i in range(n):
        tr = np.arange(n) != i
        if X.shape[1]:
            mu, sd = X[tr].mean(0), X[tr].std(0); sd[sd == 0] = 1
            Z = (X - mu) / sd
        else:
            Z = X
        A = np.column_stack([np.ones(n), Z])
        b = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
        pred[i] = A[i] @ b; e[i] = (y[i] - pred[i]) ** 2
    return e, pred


def _diff(e_big, e_small, seed):
    d = e_big - e_small
    rng = np.random.default_rng(seed)
    bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(N_BOOT)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    p = float(min(1.0, 2 * min((bs <= 0).mean(), (bs >= 0).mean())))
    return {"risk_diff_big_minus_small": float(d.mean()), "ci_low": float(lo), "ci_high": float(hi), "p_boot": p,
            "excludes_0": bool(lo > 0 or hi < 0)}


def analyse(y, C, S, G, A):
    models = {"M1": C, "M2": np.column_stack([C, S]), "M3": np.column_stack([C, S, G]),
              "M1a": np.column_stack([C, A]), "M2a": np.column_stack([C, A, S]), "M3a": np.column_stack([C, A, S, G])}
    E, P = {}, {}
    for k, X in models.items():
        E[k], P[k] = _loo(X, y)
    res = {"n": int(len(y)), "risk": {k: float(v.mean()) for k, v in E.items()},
           "loo_pred_r": {k: float(np.corrcoef(P[k], y)[0, 1]) for k in E}}
    # convention: big - small; negative = adding the term improves held-out prediction
    res["primary_M3_minus_M2"] = _diff(E["M3"], E["M2"], SEED)
    res["M3a_minus_M2a"] = _diff(E["M3a"], E["M2a"], SEED + 1)
    res["M2_minus_M1"] = _diff(E["M2"], E["M1"], SEED + 2)
    res["M1a_minus_M1"] = _diff(E["M1a"], E["M1"], SEED + 3)
    return res


def main():
    rows = parse_table4()
    with open(os.path.join(PRIV, "table4_parsed.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[k for k, _ in COLS]); w.writeheader(); w.writerows(rows)
    t4 = {r["ID"]: r for r in rows}
    eeg = sorted(os.path.basename(p)[:-5] for p in os.listdir(os.path.join(PUB, "main_v2", "ci")) if p.endswith(".json"))
    eeg = [os.path.basename(x) for x in eeg]
    hsm = {k: _num(t4[k]["HSM"]) for k in eeg if k in t4}
    receipt = {"pdf_sha256": hashlib.sha256(open(PDF, "rb").read()).hexdigest(), "n_table4_rows": len(rows),
               "n_eeg": len(eeg), "eeg_not_in_table4": sorted(set(eeg) - set(t4)), "table4_not_in_eeg": sorted(set(t4) - set(eeg)),
               "hsm_missing": sorted(k for k, v in hsm.items() if not np.isfinite(v)),
               "check_hsm_median_range": [float(np.nanmedian(list(hsm.values()))), float(np.nanmin(list(hsm.values()))), float(np.nanmax(list(hsm.values())))]}
    json.dump(receipt, open(os.path.join(PRIV, "linkage_receipt.json"), "w"), indent=1)
    assert receipt["check_hsm_median_range"] == [23.5, 0.0, 82.0], receipt  # Table 1 summary

    def neural(k, key, win, mode="main_v2"):
        d = json.load(open(os.path.join(PUB, mode, "ci", f"{k}.json")))
        return float(np.mean([d[f"{r}/{key}/{win}"]["corr"] for r in ROIS]))

    out = {"spec": "docs/auditory_c3/H7_FUNCTION_PREREG.md", "cohort": "FAU/TUD CI adults", "receipt": {k: v for k, v in receipt.items() if k != "check_hsm_median_range"},
           "risk_units": "squared error of logit((p+0.5)/101)", "sign": "risk_diff = bigger model - smaller model; negative = improvement"}
    for endpoint in ("HSM", "Freiburg_better_ear_65dB"):
        ks = [k for k in eeg if k in t4]
        if endpoint == "HSM":
            yv = {k: hsm[k] for k in ks}
        else:
            yv = {k: np.nanmax([_num(t4[k]["MonoR"]), _num(t4[k]["MonoL"])]) for k in ks}
        ks = [k for k in ks if np.isfinite(yv[k])]
        y = _logit_pct(np.array([yv[k] for k in ks]))
        C = np.array([[_num(t4[k]["Age"]), max(_num(t4[k]["CIexpR"]), _num(t4[k]["CIexpL"]))] for k in ks])
        S = np.array([neural(k, "TMIF_Ac_att", "all") for k in ks])
        G = np.array([neural(k, "CMI_L_att_given_yAc", "all") for k in ks])
        A = np.array([neural(k, "TMIF_Ac_att", "diag") for k in ks])
        Gz = np.array([neural(k, "CMI_Lz_given_yAc", "all", "l27z") for k in ks])
        out[endpoint] = {"main": analyse(y, C, S, G, A), "sensitivity_Lz": analyse(y, C, S, Gz, A),
                         "descriptive_spearman_with_y": {nm: float(stats_spearman(v, y)) for nm, v in (("S", S), ("G", G), ("A", A), ("Gz", Gz))}}
    ps = [out[e]["main"]["primary_M3_minus_M2"]["p_boot"] for e in ("HSM", "Freiburg_better_ear_65dB")]
    for e, q in zip(("HSM", "Freiburg_better_ear_65dB"), stats.bh(ps)):
        out[e]["main"]["primary_M3_minus_M2"]["q_bh_H7_family"] = float(q)
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(out, indent=1))


def main_c3dl():
    """C3-DL function layer (C3DL_PROTOCOL_v1_FROZEN.md §3): as H7a, with G replaced by the out-of-fold
    G_EEG = e(D2s) - e(D2s_twin) (mean over seeds and content folds) of each CI participant."""
    t4 = {r["ID"]: r for r in parse_table4()}
    M = json.load(open(os.path.join(REPO, "private", "auditory_c3", "c3dl_full", "per_participant_means.json")))
    geeg = {s: v["D2s"]["e_bits_per_sample"] - v["D2s_twin"]["e_bits_per_sample"] for s, v in M["pl_per_subject"].items() if M["pl_group"][s] == "ci"}

    def neural(k, key, win):
        d = json.load(open(os.path.join(PUB, "main_v2", "ci", f"{k}.json")))
        return float(np.mean([d[f"{r}/{key}/{win}"]["corr"] for r in ROIS]))
    out = {"spec": "docs/auditory_c3/C3DL_PROTOCOL_v1_FROZEN.md §3", "n_ci_with_G_EEG": len(geeg),
           "sign": "risk_diff = bigger model - smaller model; negative = improvement"}
    for endpoint in ("HSM", "Freiburg_better_ear_65dB"):
        ks = sorted(k for k in geeg if k in t4)
        yv = {k: (_num(t4[k]["HSM"]) if endpoint == "HSM" else np.nanmax([_num(t4[k]["MonoR"]), _num(t4[k]["MonoL"])])) for k in ks}
        ks = [k for k in ks if np.isfinite(yv[k])]
        y = _logit_pct(np.array([yv[k] for k in ks]))
        C = np.array([[_num(t4[k]["Age"]), max(_num(t4[k]["CIexpR"]), _num(t4[k]["CIexpL"]))] for k in ks])
        S = np.array([neural(k, "TMIF_Ac_att", "all") for k in ks]); A = np.array([neural(k, "TMIF_Ac_att", "diag") for k in ks])
        G = np.array([geeg[k] for k in ks])
        out[endpoint] = {"main": analyse(y, C, S, G, A), "descriptive_spearman_G_EEG_y": float(stats_spearman(G, y)),
                         "descriptive_spearman_G_EEG_A": float(stats_spearman(G, A))}
    fn = os.path.join(REPO, "results", "auditory_c3", "H7_function_c3dl.json")
    json.dump(out, open(fn, "w"), indent=1); print("written", fn)


def stats_spearman(a, b):
    from scipy.stats import spearmanr
    return spearmanr(a, b)[0]


if __name__ == "__main__":
    import sys
    main_c3dl() if len(sys.argv) > 1 and sys.argv[1] == "c3dl" else main()
