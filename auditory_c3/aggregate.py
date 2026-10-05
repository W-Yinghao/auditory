"""Group-level aggregation (aggregate numbers only; per-participant inputs stay private).

  python -m auditory_c3.aggregate p2   -> results/auditory_c3/P2_positive_controls.json   (G2 gate: H1a, H1b, H1c)
  python -m auditory_c3.aggregate p3   -> results/auditory_c3/P3_public.json, P3_private.json (only after G2 passes)
Statistics: auditory_c3/stats.py (MEASUREMENT_AMENDMENT_001 §7).
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

from . import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(REPO, "private", "auditory_c3", "public")
PRIV = os.path.join(REPO, "private", "auditory_c3", "private")
RES = os.path.join(REPO, "results", "auditory_c3")
ROIS = ["frontocentral", "left_temporal", "right_temporal"]
GROUPS = ["th", "ha", "ci"]


def _load(mode, grp):
    return {os.path.basename(p)[:-5]: json.load(open(p)) for p in sorted(glob.glob(os.path.join(PUB, "fau_tud", mode, grp, "*.json")))}


def _expected(grp):
    return sorted(os.path.basename(p)[:-3] for p in glob.glob(f"/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/fau_tud_stageB/{grp}/*.h5"))


def coverage(mode):
    cov = {}
    for g in GROUPS:
        have, exp = set(_load(mode, g)), set(_expected(g))
        cov[g] = {"have": len(have & exp), "expected": len(exp), "missing": sorted(exp - have)}
    return cov


def p2():
    out = {"gate": "G2"}
    # H1a
    h1a = {}
    for g in GROUPS:
        subs = {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob(os.path.join(PUB, "fau_tud", "h1a", g, "*.json"))}
        exp = _expected(g)
        accs = [100 * v["accuracy"] for v in subs.values()]
        paper = {"th": 87.8, "ha": 88.5, "ci": 63.1}[g]
        h1a[g] = {"n": len(subs), "expected": len(exp), "complete": len(subs) == len(exp), "paper_pct": paper,
                  "mean_accuracy_pct": float(np.mean(accs)) if accs else float("nan"),
                  "within_3pt": bool(accs and abs(np.mean(accs) - paper) <= 3.0 and len(subs) == len(exp)),
                  "ci": stats.mean_ci(accs, seed=1) if len(accs) > 1 else None,
                  "n_windows_total": sum(v["n_windows"] for v in subs.values())}
    out["H1a"] = {"groups": h1a, "pass": all(v.get("within_3pt", False) for v in h1a.values())}
    # H1b: I(T;Att) - I(T;Ign) in window 1, CS trials, every group interval must contain 0
    cov = coverage("main"); out["coverage_main"] = cov
    h1b, fam = {}, []
    for g in GROUPS:
        subs = _load("main", g)
        for r in ROIS:
            d = [s[f"{r}/CS_TMIF_Env_att/w1"]["corr"] - s[f"{r}/CS_TMIF_Env_ign/w1"]["corr"] for s in subs.values()]
            m = stats.mean_ci(d, seed=2)
            m["contains_0"] = bool(m["ci_low"] <= 0 <= m["ci_high"])
            # descriptive (not gating): the attention effect in window 2, where Jehn reports N1/P2 modulation
            d2 = [s[f"{r}/CS_TMIF_Env_att/w2"]["corr"] - s[f"{r}/CS_TMIF_Env_ign/w2"]["corr"] for s in subs.values()]
            m["w2_att_minus_ign_descriptive"] = stats.mean_ci(d2, seed=3)
            h1b[f"{g}/{r}"] = m; fam.append(m["p_signflip"])
    q = stats.bh(fam)
    for k, qq in zip(h1b, q):
        h1b[k]["q_bh"] = float(qq)
    out["H1b"] = {"cells": h1b, "pass": all(v["contains_0"] for v in h1b.values()),
                  "complete": all(c["have"] == c["expected"] for c in cov.values())}
    # H1c: Federici envelope TMIF window 2, CI - HC < 0 with the interval excluding 0
    fd = json.load(open(os.path.join(PUB, "federici", "tmif.json")))["subjects"]
    val = lambda grp, w: [v[f"Env/{w}"]["corr"] for k, v in fd.items() if v["group"] == grp]
    w2 = stats.diff_ci(val("CI", "w2"), val("HC", "w2"), seed=4)
    w1 = stats.diff_ci(val("CI", "w1"), val("HC", "w1"), seed=5)
    art = {w: stats.mean_ci(val("Artifact", w), seed=6) for w in ("w1", "w2", "diag")}
    out["H1c"] = {"w2_CI_minus_HC": w2, "w1_CI_minus_HC_descriptive": w1,
                  "group_means": {grp: {w: stats.mean_ci(val(grp, w), seed=7) for w in ("diag", "w1", "w2")} for grp in ("HC", "CI", "HC-v")},
                  "phantom_head_artifact_only": art, "pass": bool(w2["est"] < 0 and w2["ci_high"] < 0)}
    out["G2_pass"] = bool(out["H1a"]["pass"] and out["H1b"]["pass"] and out["H1c"]["pass"])
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "P2_positive_controls.json"), "w"), indent=1)
    print(json.dumps({"H1a": {g: (round(v.get("mean_accuracy_pct", float("nan")), 1), v.get("paper_pct"), v.get("within_3pt")) for g, v in h1a.items()},
                      "H1b_pass": out["H1b"]["pass"], "H1b_complete": out["H1b"]["complete"],
                      "H1c": {k: round(w2[k], 5) for k in ("est", "ci_low", "ci_high")}, "H1c_pass": out["H1c"]["pass"],
                      "G2_pass": out["G2_pass"]}, indent=1))


def _contrast_family(mode, key, window="all", subset=None):
    """HA-TH and CI-TH for one per-subject quantity key (e.g. 'TMIF_Ac_att'), all ROIs; BH within the family."""
    data = {g: _load(mode, g) for g in GROUPS}
    if subset is not None:
        data["th"] = {k: v for k, v in data["th"].items() if k in subset}
    cells, ps = {}, []
    for r in ROIS:
        vals = {g: [s[f"{r}/{key}/{window}"]["corr"] for s in data[g].values()] for g in GROUPS}
        for g in GROUPS:
            cells[f"{r}/{g}/mean"] = stats.mean_ci(vals[g], seed=11)
        for g in ("ha", "ci"):
            d = stats.diff_ci(vals[g], vals["th"], seed=12)
            d["equivalence_15pct_th_median"] = stats.equivalence(d, vals["th"])
            cells[f"{r}/{g}-th"] = d; ps.append(d["p_perm"])
    keys = [k for k in cells if k.endswith("-th")]
    for k, q in zip(keys, stats.bh(ps)):
        cells[k]["q_bh"] = float(q)
    return cells


def _diff_key(mode, key_a, key_b, window="all"):
    """per-subject difference of two quantities (e.g. attended - ignored), group means and HA/CI - TH contrasts."""
    data = {g: _load(mode, g) for g in GROUPS}
    cells, ps = {}, []
    for r in ROIS:
        vals = {g: [s[f"{r}/{key_a}/{window}"]["corr"] - s[f"{r}/{key_b}/{window}"]["corr"] for s in data[g].values()] for g in GROUPS}
        for g in GROUPS:
            cells[f"{r}/{g}/mean"] = stats.mean_ci(vals[g], seed=13)
        for g in ("ha", "ci"):
            d = stats.diff_ci(vals[g], vals["th"], seed=14); cells[f"{r}/{g}-th"] = d; ps.append(d["p_perm"])
    keys = [k for k in cells if k.endswith("-th")]
    for k, q in zip(keys, stats.bh(ps)):
        cells[k]["q_bh"] = float(q)
    return cells


def _pid(mode):
    data = {g: _load(mode, g) for g in GROUPS}
    out = {}
    for r in ROIS:
        for term in ("UAc", "UL", "R", "S"):
            for meas in ("CCS", "MMI"):
                vals = {g: [s[f"{r}/MED/{meas}_{term}"]["corr"] for s in data[g].values()] for g in GROUPS}
                for g in GROUPS:
                    out[f"{r}/{meas}_{term}/{g}"] = stats.mean_ci(vals[g], seed=15)
                for g in ("ha", "ci"):
                    out[f"{r}/{meas}_{term}/{g}-th"] = stats.diff_ci(vals[g], vals["th"], seed=16)
            for g in ("ha", "ci"):
                a, b = out[f"{r}/CCS_{term}/{g}-th"]["est"], out[f"{r}/MMI_{term}/{g}-th"]["est"]
                out[f"{r}/{term}/{g}-th/same_sign"] = bool(np.sign(a) == np.sign(b))
        for k in ("I_T_yAc", "I_T_yL", "I_T_yAcyL", "CMI_T_yL_given_yAc"):
            vals = {g: [s[f"{r}/MED/{k}"]["corr"] for s in data[g].values()] for g in GROUPS}
            for g in GROUPS:
                out[f"{r}/{k}/{g}"] = stats.mean_ci(vals[g], seed=17)
            for g in ("ha", "ci"):
                out[f"{r}/{k}/{g}-th"] = stats.diff_ci(vals[g], vals["th"], seed=18)
    return out


def _curves(mode, key):
    data = {g: _load(mode, g) for g in GROUPS}
    out = {}
    for g in GROUPS:
        for r in ROIS:
            arr = np.array([np.array(s[f"{r}/{key}/per_lag_obs"]) - np.array(s[f"{r}/{key}/per_lag_sur_mean"]) for s in data[g].values()])
            out[f"{g}/{r}"] = {"mean": arr.mean(0).tolist(), "sem": (arr.std(0, ddof=1) / np.sqrt(len(arr))).tolist(), "n": len(arr)}
    return out


def p3_public():
    p2r = json.load(open(os.path.join(RES, "P2_positive_controls.json")))
    if not p2r.get("G2_pass") and not os.path.exists(os.path.join(REPO, "docs", "auditory_c3", "DECISION_001_POST_G2.md")):
        raise SystemExit("G2 has not passed and no post-G2 scope decision exists: P3 is not aggregated (04 §4.1)")
    split = json.load(open(os.path.join(PUB, "fau_tud", "th_split.json")))
    out = {"coverage": {m: coverage(m) for m in ("main", "main_noica", "main_pub")}, "G2_pass": bool(p2r.get("G2_pass")),
           "scope": "DECISION_001_POST_G2: claims only for TH/HA contrasts and within-group quantities; every CI contrast is ARTIFACT_LIMITED (reported, never claimed)"}
    W = ["all", "w1", "w2", "w3", "diag"]
    out["H2_TMIF_Ac"] = {w: _contrast_family("main", "TMIF_Ac_att", w) for w in W}
    out["H3a_CMI_L_given_yAc"] = {w: _contrast_family("main", "CMI_L_att_given_yAc", w) for w in W}
    out["H3b_attention_CMI_L"] = {w: _diff_key("main", "CS_CMI_L_att_given_yAc", "CS_CMI_L_ign_given_yAc", w) for w in W}
    out["H3c_PID_mediated"] = _pid("main")
    out["control_CMI_Ac_given_yL"] = {w: _contrast_family("main", "CMI_Ac_att_given_yL", w) for w in ("all", "w2")}
    out["sens_CMI_L_samelag"] = {w: _contrast_family("main", "CMI_L_att_given_Ac_samelag", w) for w in ("all", "w2")}
    out["sec43_attention_Ac"] = {w: _diff_key("main", "CS_TMIF_Ac_att", "CS_TMIF_Ac_ign", w) for w in ("all", "w1", "w2", "w3")}
    out["sec43_attention_Env"] = {w: _diff_key("main", "CS_TMIF_Env_att", "CS_TMIF_Env_ign", w) for w in ("all", "w1", "w2", "w3")}
    out["TMIF_Env_att"] = {w: _contrast_family("main", "TMIF_Env_att", w) for w in W}
    out["sens_noica"] = {"H2": _contrast_family("main_noica", "TMIF_Ac_att"), "H3a": _contrast_family("main_noica", "CMI_L_att_given_yAc")}
    out["sens_th_heldout_half"] = {"H2": _contrast_family("main", "TMIF_Ac_att", subset=set(split["heldout_half"])),
                                   "H3a": _contrast_family("main", "CMI_L_att_given_yAc", subset=set(split["heldout_half"]))}
    out["curves"] = {k: _curves("main", k) for k in ("TMIF_Ac_att", "TMIF_Env_att", "CMI_L_att_given_yAc", "CS_TMIF_Env_att", "CS_TMIF_Env_ign")}
    out["lags_ms"] = next(iter(_load("main", "th").values()))["lags_ms"]
    # ICA removals per group (artefact rule applied identically)
    ica = {}
    for g in GROUPS:
        lg = json.load(open(f"/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/_logs/stageB_{g}.json"))
        n = [v["n_removed"] for v in lg.values() if isinstance(v, dict) and "n_removed" in v]
        ica[g] = {"subjects": len(n), "mean_removed": float(np.mean(n)), "n_with_any": int(sum(x > 0 for x in n)), "max": int(max(n))}
    out["ica_removed_components"] = ica
    # DTU (envelope layer): attention effect per hearing status and HI-NH
    import pandas as pd
    part = pd.read_csv("/projects/EEG-foundation-model/auditory_public/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
    hs = dict(zip(part.participant_id, part.hearing_status))
    dtu = {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob(os.path.join(PUB, "dtu", "*.json"))}
    dd = {}
    for r in ROIS:
        for w in ("all", "w1", "w2", "w3", "diag"):
            for grp in ("nh", "hi"):
                v = [s[f"{r}/CS_TMIF_Env_att/{w}"]["corr"] - s[f"{r}/CS_TMIF_Env_ign/{w}"]["corr"] for k, s in dtu.items() if hs.get(k) == grp]
                dd[f"{r}/{w}/{grp}/att-ign"] = stats.mean_ci(v, seed=19)
                v2 = [s[f"{r}/TMIF_Env_att/{w}"]["corr"] for k, s in dtu.items() if hs.get(k) == grp]
                dd[f"{r}/{w}/{grp}/TMIF_att"] = stats.mean_ci(v2, seed=20)
            a = [s[f"{r}/CS_TMIF_Env_att/{w}"]["corr"] - s[f"{r}/CS_TMIF_Env_ign/{w}"]["corr"] for k, s in dtu.items() if hs.get(k) == "hi"]
            b = [s[f"{r}/CS_TMIF_Env_att/{w}"]["corr"] - s[f"{r}/CS_TMIF_Env_ign/{w}"]["corr"] for k, s in dtu.items() if hs.get(k) == "nh"]
            dd[f"{r}/{w}/hi-nh/att-ign"] = stats.diff_ci(a, b, seed=21)
    out["DTU_envelope_attention"] = {"n": {g: sum(1 for k in dtu if hs.get(k) == g) for g in ("nh", "hi")}, "cells": dd}
    json.dump(out, open(os.path.join(RES, "P3_public.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_public.json"))


def p3_private():
    d = json.load(open(os.path.join(PRIV, "h4h5_children.json")))["children"]
    out = {}
    HA = {k: v for k, v in d.items() if v["group"] == "HA"}; NH = {k: v for k, v in d.items() if v["group"] == "NH"}
    stage = lambda v: "early_0_2" if v["duration_months"] <= 2 else ("late_ge13" if v["duration_months"] >= 13 else "mid_2_13")
    for name, sel in (("NH", NH), ("HA_all", HA), *[(f"HA_{s}", {k: v for k, v in HA.items() if stage(v) == s}) for s in ("early_0_2", "mid_2_13", "late_ge13")]):
        out[f"H4a/I_T_Cur/{name}"] = stats.mean_ci([v["I_T_Cur"]["corr"] for v in sel.values()], seed=31) if len(sel) > 1 else {"n": len(sel)}
        for h in ("since_last_deviant", "prev_class", "prev_run_length"):
            out[f"H4b/I_T_Hist_given_Cur/{h}/{name}"] = stats.mean_ci([v[f"I_T_Hist_given_Cur/{h}"]["corr"] for v in sel.values()], seed=32) if len(sel) > 1 else {"n": len(sel)}
    e, n = out["H4a/I_T_Cur/HA_early_0_2"], out["H4a/I_T_Cur/NH"]
    out["H4a/criterion"] = {"early_excludes_0": bool(e["ci_low"] > 0), "overlaps_NH": bool(e["ci_low"] <= n["ci_high"] and n["ci_low"] <= e["ci_high"])}
    # H5a: child-level OLS I_Cur ~ 1 + age + D (calendar age primary; EEG age sensitivity), bootstrap over children
    def ols_beta(rows, age_key):
        X = np.array([[1.0, r[age_key], r["duration_months"]] for r in rows]); y = np.array([r["I_T_Cur"]["corr"] for r in rows])
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        rng = np.random.default_rng(33); bs = []
        for _ in range(stats.B):
            i = rng.integers(0, len(rows), len(rows)); bs.append(np.linalg.lstsq(X[i], y[i], rcond=None)[0])
        bs = np.array(bs)
        return {"beta_age": float(b[1]), "beta_D": float(b[2]), "beta_D_ci": [float(x) for x in np.percentile(bs[:, 2], [2.5, 97.5])],
                "beta_age_ci": [float(x) for x in np.percentile(bs[:, 1], [2.5, 97.5])], "n": len(rows)}
    rows = list(HA.values())
    out["H5a/ols_calendar_age"] = ols_beta(rows, "age_months")
    rows_e = [r for r in rows if r.get("eeg_age_bc") is not None]
    out["H5a/ols_eeg_age_sensitivity"] = ols_beta(rows_e, "eeg_age_bc")
    out["H5a/early_vs_late"] = stats.diff_ci([v["I_T_Cur"]["corr"] for v in HA.values() if stage(v) == "early_0_2"],
                                             [v["I_T_Cur"]["corr"] for v in HA.values() if stage(v) == "late_ge13"], seed=34)
    # H5b: child-level I(I_Cur; D | age) by Gaussian copula with a permutation null on D
    sys.path.insert(0, os.path.join(REPO, "AUDITORY_C3_SERVER_PACKAGE_v1_20261003", "reference"))
    from gcmi_core import gcmi_ccc
    icur = np.array([r["I_T_Cur"]["corr"] for r in rows]); D = np.array([r["duration_months"] for r in rows]); age = np.array([r["age_months"] for r in rows])
    obs = gcmi_ccc(icur, D, age); rng = np.random.default_rng(35)
    null = np.array([gcmi_ccc(icur, rng.permutation(D), age) for _ in range(2000)])
    out["H5b/I_ICur_D_given_age"] = {"obs": float(obs), "null_mean": float(null.mean()), "corr": float(obs - null.mean()),
                                     "p_perm": float((np.sum(null >= obs) + 1) / 2001), "n": len(rows)}
    out["H5c/paired_visits"] = {"status": "TECHNICALLY_UNEVALUABLE", "reason": "acquisition order/dates unknown for repeat visits (PF protocol: no acquisition dates); earliest-latest pairing cannot be established"}
    # H6
    h6 = json.load(open(os.path.join(PRIV, "h6_children.json")))["children"]
    for grp, sel in (("CI", {k: v for k, v in h6.items() if v["ci"]}), ("nonCI", {k: v for k, v in h6.items() if not v["ci"]})):
        for q in ("I_cls_low", "I_cls_high", "I_cls_high_given_low", "I_cls_full"):
            out[f"H6/{q}/{grp}"] = stats.mean_ci([v[q]["corr"] for v in sel.values()], seed=36)
        for t in ("R", "U_low", "U_high", "S"):
            out[f"H6/MMI_{t}/{grp}"] = stats.mean_ci([v["MMI"][t] for v in sel.values()], seed=37)
    out["H6/I_ccs"] = {"status": "TECHNICALLY_UNEVALUABLE", "reason": "the validated I_ccs port is Gaussian; H6 has a discrete target (class), so only MMI is reported"}
    json.dump(out, open(os.path.join(RES, "P3_private_aggregate.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_private_aggregate.json"))


def p3_controls():
    """04 §4.2 control checks (DECISION_001 §6) and the H1a CI audit (§5)."""
    out = {"coverage": coverage("controls")}
    for k in ("CMI_X20_given_yAc", "CMI_Sur_given_yAc", "CMI_Ons_given_yAc", "CMI_Sur_given_yAc_yOns", "CMI_L_given_yMel",
              "CMI_Lk3_given_yAc3", "CMI_Lk8_given_yAc8", "TMIF_Mel"):
        out[k] = {w: _contrast_family("controls", k, w) for w in ("all", "w2", "diag")}
    audit = {}
    for variant in ("h1a", "h1a_zero_removed", "h1a_trial_start"):
        for g in GROUPS:
            subs = [json.load(open(p_)) for p_ in glob.glob(os.path.join(PUB, "fau_tud", variant, g, "*.json"))]
            if subs:
                audit[f"{variant}/{g}"] = dict(stats.mean_ci([100 * v["accuracy"] for v in subs], seed=41), n_windows=sum(v["n_windows"] for v in subs))
    out["H1a_audit"] = audit
    json.dump(out, open(os.path.join(RES, "P3_controls.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_controls.json"))


# ----------------------------------------------------------------------------------------------- v2 (review addendum)
def _heldout():
    return set(json.load(open(os.path.join(PUB, "fau_tud", "th_split.json")))["heldout_half"])


def _fam2(mode, key, window="all", th="heldout"):
    """Contrast family with the TH reference restricted to the 14 TH never used for layer selection (addendum item 4)."""
    return _contrast_family(mode, key, window, subset=_heldout() if th == "heldout" else None)


def _diff_key2(mode, key_a, key_b, window="all", th="heldout"):
    data = {g: _load(mode, g) for g in GROUPS}
    if th == "heldout":
        data["th"] = {k: v for k, v in data["th"].items() if k in _heldout()}
    cells, ps = {}, []
    for r in ROIS:
        vals = {g: [x[f"{r}/{key_a}/{window}"]["corr"] - x[f"{r}/{key_b}/{window}"]["corr"] for x in data[g].values()] for g in GROUPS}
        for g in GROUPS:
            cells[f"{r}/{g}/mean"] = stats.mean_ci(vals[g], seed=13)
        for g in ("ha", "ci"):
            d = stats.diff_ci(vals[g], vals["th"], seed=14); cells[f"{r}/{g}-th"] = d; ps.append(d["p_perm"])
    for k, q in zip([k for k in cells if k.endswith("-th")], stats.bh(ps)):
        cells[k]["q_bh"] = float(q)
    return cells


def p3_public_v2():
    mode = "main_v2"
    p2r = json.load(open(os.path.join(RES, "P2_positive_controls.json")))
    out = {"analysis_version": "v2: tie-aware copula; TH reference = 14 held-out TH (selection half excluded); all-TH as sensitivity",
           "coverage": coverage(mode),
           "G2_T_technical": {"status": "PARTIAL", "detail": "Jehn pipeline reproduces TH (85.5) and HA (87.9) within 3 points; CI 56.2 vs 63.1 (audit in P3_controls); aux channels excluded; alignment checked (aux xcorr); estimator agrees with reference to 1e-6; engine checked against direct estimation"},
           "G2_S_scientific": {"H1b": p2r["H1b"]["pass"], "H1c": p2r["H1c"]["pass"],
                               "note": "new MI/TMIF orderings that differ from TRF/accuracy results are scientific outcomes, not automatically technical errors"},
           "scope": "claims: TH(held-out)/HA contrasts and within-group quantities; CI contrasts ARTIFACT_LIMITED"}
    W = ["all", "w1", "w2", "w3", "diag"]
    out["H2_TMIF_Ac"] = {w: _fam2(mode, "TMIF_Ac_att", w) for w in W}
    out["H3a_deep_increment_CMI_L_given_yAc"] = {w: _fam2(mode, "CMI_L_att_given_yAc", w) for w in W}
    out["H3b_attention_deep_increment"] = {w: _diff_key2(mode, "CS_CMI_L_att_given_yAc", "CS_CMI_L_ign_given_yAc", w) for w in W}
    # lag-specific deep increment: window minus the diagnostic (negative-lag) window, per subject
    def _win_excess(key, wa, wb="diag"):
        data = {g: _load(mode, g) for g in GROUPS}
        data["th"] = {k: v for k, v in data["th"].items() if k in _heldout()}
        cells = {}
        for r in ROIS:
            vals = {g: [x[f"{r}/{key}/{wa}"]["corr"] - x[f"{r}/{key}/{wb}"]["corr"] for x in data[g].values()] for g in GROUPS}
            for g in GROUPS:
                cells[f"{r}/{g}/mean"] = stats.mean_ci(vals[g], seed=19)
            for g in ("ha", "ci"):
                cells[f"{r}/{g}-th"] = stats.diff_ci(vals[g], vals["th"], seed=20)
        return cells
    out["H3a_lag_specific_excess"] = {"w2_minus_diag": _win_excess("CMI_L_att_given_yAc", "w2"), "all_minus_diag": _win_excess("CMI_L_att_given_yAc", "all")}
    out["sec43_attention_Ac"] = {w: _diff_key2(mode, "CS_TMIF_Ac_att", "CS_TMIF_Ac_ign", w) for w in ("all", "w2")}
    out["sec43_attention_Env"] = {w: _diff_key2(mode, "CS_TMIF_Env_att", "CS_TMIF_Env_ign", w) for w in ("all", "w1", "w2")}
    out["H1b_v2_w1_att_minus_ign"] = _diff_key2(mode, "CS_TMIF_Env_att", "CS_TMIF_Env_ign", "w1", th="all")
    out["control_CMI_Ac_given_yL"] = {w: _fam2(mode, "CMI_Ac_att_given_yL", w) for w in ("all",)}
    out["sens_all_TH"] = {"H2": _fam2(mode, "TMIF_Ac_att", "all", th="all"), "H3a": _fam2(mode, "CMI_L_att_given_yAc", "all", th="all"),
                          "H3b": _diff_key2(mode, "CS_CMI_L_att_given_yAc", "CS_CMI_L_ign_given_yAc", "all", th="all")}
    # PID on the mediated path with held-out TH
    data = {g: _load(mode, g) for g in GROUPS}; data["th"] = {k: v for k, v in data["th"].items() if k in _heldout()}
    pid = {}
    for r in ROIS:
        for term in ("UAc", "UL", "R", "S"):
            for meas in ("CCS", "MMI"):
                vals = {g: [x[f"{r}/MED/{meas}_{term}"]["corr"] for x in data[g].values()] for g in GROUPS}
                for g in GROUPS:
                    pid[f"{r}/{meas}_{term}/{g}"] = stats.mean_ci(vals[g], seed=15)
                pid[f"{r}/{meas}_{term}/ha-th"] = stats.diff_ci(vals["ha"], vals["th"], seed=16)
        for k in ("I_T_yAc", "I_T_yL", "CMI_T_yL_given_yAc"):
            vals = {g: [x[f"{r}/MED/{k}"]["corr"] for x in data[g].values()] for g in GROUPS}
            for g in GROUPS:
                pid[f"{r}/{k}/{g}"] = stats.mean_ci(vals[g], seed=17)
            pid[f"{r}/{k}/ha-th"] = stats.diff_ci(vals["ha"], vals["th"], seed=18)
    out["H3c_PID_mediated"] = pid
    # tie fractions actually encountered (max over subjects), per variable
    tf = {}
    for g in GROUPS:
        for x in _load(mode, g).values():
            for r in ROIS:
                for part in ("all", "cs"):
                    for k, v in x.get(f"{r}/tie_fraction", {}).get(part, {}).items():
                        tf[f"{part}/{k}"] = max(tf.get(f"{part}/{k}", 0.0), v)
    out["max_tie_fraction"] = tf
    # v1 vs v2 agreement for quantities without ties
    agree = {}
    for g in GROUPS:
        v1, v2 = _load("main", g), _load(mode, g)
        for key in ("TMIF_Ac_att", "CMI_L_att_given_yAc", "CS_TMIF_Env_ign", "CS_CMI_L_ign_given_yAc"):
            d = [abs(v1[s][f"right_temporal/{key}/all"]["corr"] - v2[s][f"right_temporal/{key}/all"]["corr"]) for s in v2 if s in v1]
            agree[f"{g}/{key}"] = float(np.max(d)) if d else None
    out["v1_v2_max_abs_diff_right_temporal_all"] = agree
    json.dump(out, open(os.path.join(RES, "P3_public_v2.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_public_v2.json"))


def p3_private_v2():
    d = json.load(open(os.path.join(PRIV, "h4h5_children_v2.json")))
    ch = d["children"]
    stage = lambda v: "early_0_2" if v["duration_months"] <= 2 else ("late_ge13" if v["duration_months"] >= 13 else "mid_2_13")
    groups = {"NH": [v for v in ch.values() if v["group"] == "NH"], "HA_all": [v for v in ch.values() if v["group"] == "HA"]}
    for st in ("early_0_2", "mid_2_13", "late_ge13"):
        groups[f"HA_{st}"] = [v for v in groups["HA_all"] if stage(v) == st]
    out = {"cohort_counts": d["cohort_counts"], "estimator": "class-conditional Gaussian on copula-normalised T; CMI within strata; one null per quantity (see private_mi2 docstring)"}
    qs = ["I_T_Cur", "I_T_Cur_circular_null"] + [f"{q}/{h}" for h in ("since_last_deviant", "prev_class", "prev_run_length")
                                                for q in ("I_T_Hist", "I_T_CurHist", "I_T_Cur_given_Hist", "I_T_Hist_given_Cur")]
    for tv in ("evidence", "model_agnostic_pc3"):
        for gname, rows in groups.items():
            for q in qs:
                vals = [r[tv][q]["null_excess"] for r in rows if np.isfinite(r[tv][q].get("null_excess", np.nan))]
                cell = stats.mean_ci(vals, seed=51) if len(vals) > 1 else {"n": len(vals)}
                cell["mean_retained_mass"] = float(np.mean([r[tv][q].get("retained_mass", np.nan) for r in rows])) if rows else None
                cell["n_bound_violations"] = int(sum(bool(r[tv][q].get("bound_violation", False)) for r in rows))
                out[f"{tv}/{gname}/{q}"] = cell
    rows = groups["HA_all"]
    for tv in ("evidence", "model_agnostic_pc3"):
        X = np.array([[1.0, r["age_months"], r["duration_months"]] for r in rows])
        y = np.array([r[tv]["I_T_Cur"]["null_excess"] for r in rows])
        b = np.linalg.lstsq(X, y, rcond=None)[0]; rng = np.random.default_rng(52)
        bs = np.array([np.linalg.lstsq(X[i], y[i], rcond=None)[0] for i in (rng.integers(0, len(y), len(y)) for _ in range(stats.B))])
        out[f"{tv}/H5a_ols_calendar_age"] = {"beta_D": float(b[2]), "beta_D_ci": [float(x) for x in np.percentile(bs[:, 2], [2.5, 97.5])],
                                             "beta_age": float(b[1]), "beta_age_ci": [float(x) for x in np.percentile(bs[:, 1], [2.5, 97.5])], "n": len(y)}
    h6 = json.load(open(os.path.join(PRIV, "h6_children_v2.json")))["children"]
    for grp, sel in (("CI", [v for v in h6.values() if v["ci"]]), ("nonCI", [v for v in h6.values() if not v["ci"]])):
        for q in ("I_cls_low", "I_cls_high", "I_cls_full", "I_cls_low_high"):
            out[f"H6/{q}/{grp}"] = stats.mean_ci([v[q]["null_excess"] for v in sel], seed=53)
        out[f"H6/I_cls_high_given_low/{grp}"] = stats.mean_ci([v["I_cls_high_given_low"]["null_excess"] for v in sel], seed=54)
        lo = np.array([v["I_cls_low"]["null_excess"] for v in sel]); hi = np.array([v["I_cls_high"]["null_excess"] for v in sel]); lh = np.array([v["I_cls_low_high"]["null_excess"] for v in sel])
        R = np.minimum(lo, hi)
        for t, arr in (("R", R), ("U_low", lo - R), ("U_high", hi - R), ("S", lh - lo - hi + R)):
            out[f"H6/MMI_{t}/{grp}"] = stats.mean_ci(arr, seed=55)
    json.dump(out, open(os.path.join(RES, "P3_private_v2.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_private_v2.json"))


def p3_controls_v2():
    out = {"coverage": coverage("controls"), "th_reference": "14 held-out TH"}
    for k in ("CMI_X20_given_yAc", "CMI_Sur_given_yAc", "CMI_Ons_given_yAc", "CMI_Sur_given_yAc_yOns", "CMI_L_given_yMel",
              "CMI_Lk3_given_yAc3", "CMI_Lk8_given_yAc8", "TMIF_Mel"):
        out[k] = {w: _fam2("controls", k, w) for w in ("all", "w2", "diag")}
    audit = {}
    for variant in ("h1a", "h1a_zero_removed", "h1a_trial_start"):
        for g in GROUPS:
            subs = [json.load(open(p_)) for p_ in glob.glob(os.path.join(PUB, "fau_tud", variant, g, "*.json"))]
            if subs:
                audit[f"{variant}/{g}"] = dict(stats.mean_ci([100 * v["accuracy"] for v in subs], seed=41), n_windows=sum(v["n_windows"] for v in subs))
    out["H1a_audit"] = audit
    json.dump(out, open(os.path.join(RES, "P3_controls_v2.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_controls_v2.json"))


def p3_l27z():
    """POST_G1_CHANGELOG 2026-10-05: L27 z-scored-coordinate sensitivity and per-PC decomposition (held-out TH)."""
    out = {"coverage": coverage("l27z"), "th_reference": "14 held-out TH"}
    for k in ["CMI_Lz_given_yAc", "CMI_L_given_yAc", "CMI_P25_given_yAc"] + [f"CMI_P{i}_given_yAc" for i in range(1, 6)]:
        out[k] = {w: _fam2("l27z", k, w) for w in ("all", "w2", "diag")}
    json.dump(out, open(os.path.join(RES, "P3_l27z.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_l27z.json"))


def p3_dtu_sur():
    """C3_EXTENSIONS_REG_v1 B1 (DTU): Danish surprisal beyond yAc (and onsets); NH > 0 and HI - NH."""
    import pandas as pd
    part = pd.read_csv("/projects/EEG-foundation-model/auditory_public/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
    hs = dict(zip(part.participant_id, part.hearing_status))
    dd = {os.path.basename(p_)[:-5]: json.load(open(p_)) for p_ in glob.glob(os.path.join(PUB, "dtu_sur", "*.json"))}
    out = {"n": {g: sum(hs[k] == g for k in dd) for g in ("nh", "hi")}}
    for key in ("CMI_Sur_given_yAc_yOns", "CMI_Sur_given_yAc", "CMI_Ons_given_yAc"):
        for w in ("all", "w2", "w3", "diag"):
            cells = {}
            for r in ROIS:
                vals = {g: [x[f"{r}/{key}/{w}"]["corr"] for k, x in dd.items() if hs[k] == g] for g in ("nh", "hi")}
                for g in ("nh", "hi"):
                    cells[f"{r}/{g}"] = stats.mean_ci(vals[g], seed=81)
                cells[f"{r}/hi-nh"] = stats.diff_ci(vals["hi"], vals["nh"], seed=82)
            for k, q in zip([k for k in cells if k.endswith("hi-nh")], stats.bh([cells[k]["p_perm"] for k in cells if k.endswith("hi-nh")])):
                cells[k]["q_bh"] = float(q)
            out[f"{key}/{w}"] = cells
    json.dump(out, open(os.path.join(RES, "P3_dtu_sur.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_dtu_sur.json"))


def p3_public_v2_eog():
    """EOG sensitivity (POST_G1_CHANGELOG 2026-10-05 ~15:30): main quantities on stage C, and paired stage C - stage B."""
    mode = "main_v2_eog"
    out = {"coverage": coverage(mode), "th_reference": "14 held-out TH"}
    W = ["all", "w2", "diag"]
    out["H2_TMIF_Ac"] = {w: _fam2(mode, "TMIF_Ac_att", w) for w in W}
    out["H3a_deep_increment_CMI_L_given_yAc"] = {w: _fam2(mode, "CMI_L_att_given_yAc", w) for w in W}
    out["H3b_attention_deep_increment"] = {w: _diff_key2(mode, "CS_CMI_L_att_given_yAc", "CS_CMI_L_ign_given_yAc", w) for w in W}
    out["control_CMI_Ac_given_yL"] = {w: _fam2(mode, "CMI_Ac_att_given_yL", w) for w in W}
    paired = {}
    for g in GROUPS:
        C, B = _load(mode, g), _load("main_v2", g)
        if g == "th":
            C = {k: v for k, v in C.items() if k in _heldout()}
        ks = sorted(set(C) & set(B))
        for r in ROIS:
            for key in ("TMIF_Ac_att", "CMI_L_att_given_yAc"):
                d = [C[k][f"{r}/{key}/all"]["corr"] - B[k][f"{r}/{key}/all"]["corr"] for k in ks]
                paired[f"{g}/{r}/{key}/C-B"] = stats.mean_ci(d, seed=71)
    out["paired_stageC_minus_stageB_all"] = paired
    json.dump(out, open(os.path.join(RES, "P3_public_v2_eog.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_public_v2_eog.json"))


def p3_nlbg_conv():
    p3_nlbg(mode="nlbg_conv")


def p3_nlbg(mode="nlbg"):
    """POST_G1_CHANGELOG 2026-10-05 ~14:40 (and ~15:10 for nlbg_conv): deep increment beyond the cross-fitted
    non-linear acoustic background."""
    out = {"coverage": coverage(mode), "th_reference": "14 held-out TH"}
    for k in ("CMI_L_given_yAc", "CMI_L_given_yAc_yBG", "CMI_L_given_yBG", "CMI_Lz_given_yAc", "CMI_Lz_given_yAc_yBGz",
              "CMI_BG_given_yAc", "CMI_Sur_given_yAc_yOns", "CMI_Sur_given_yAc_yOns_yBG"):
        out[k] = {w: _fam2(mode, k, w) for w in ("all", "w2", "diag")}
    out["retained_fraction_all"] = {}
    data = {g: _load(mode, g) for g in GROUPS}
    data["th"] = {k: v for k, v in data["th"].items() if k in _heldout()}
    for g in GROUPS:
        for r in ROIS:
            for a, b in (("CMI_L_given_yAc_yBG", "CMI_L_given_yAc"), ("CMI_Lz_given_yAc_yBGz", "CMI_Lz_given_yAc"), ("CMI_Sur_given_yAc_yOns_yBG", "CMI_Sur_given_yAc_yOns")):
                num = np.mean([x[f"{r}/{a}/all"]["corr"] for x in data[g].values()]); den = np.mean([x[f"{r}/{b}/all"]["corr"] for x in data[g].values()])
                out["retained_fraction_all"][f"{g}/{r}/{a}"] = float(num / den) if den != 0 else None
    fn = "P3_nlbg.json" if mode == "nlbg" else "P3_nlbg_conv.json"
    json.dump(out, open(os.path.join(RES, fn), "w"), indent=1)
    print("written", os.path.join(RES, fn))


def p3_dtu_v2():
    """DTU with audio (D1): H2/H3 HI vs NH, and H7c in its registered form (POST_G1_CHANGELOG, 2026-10-05 09:3x)."""
    import pandas as pd
    part = pd.read_csv("/projects/EEG-foundation-model/auditory_public/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
    cols = [f"audiogram_{e}_ear_{f}Hz" for e in ("right", "left") for f in (500, 1000, 2000, 4000)]
    part["pta4"] = part[cols].astype(float).mean(1)
    info = part.set_index("participant_id")
    dd = {os.path.basename(p_)[:-5]: json.load(open(p_)) for p_ in glob.glob(os.path.join(PUB, "dtu_v2", "*.json"))}
    grp = {k: info.loc[k, "hearing_status"] for k in dd}
    out = {"n": {g: sum(1 for k in dd if grp[k] == g) for g in ("nh", "hi")}}

    def fam(key_fn, label):
        cells = {}
        for r in ROIS:
            vals = {g: [key_fn(x, r) for k, x in dd.items() if grp[k] == g] for g in ("nh", "hi")}
            for g in ("nh", "hi"):
                cells[f"{r}/{g}"] = stats.mean_ci(vals[g], seed=61)
            d = stats.diff_ci(vals["hi"], vals["nh"], seed=62); d["equivalence_15pct_nh_median"] = stats.equivalence(d, vals["nh"])
            cells[f"{r}/hi-nh"] = d
        for k, q in zip([k for k in cells if k.endswith("hi-nh")], stats.bh([cells[k]["p_perm"] for k in cells if k.endswith("hi-nh")])):
            cells[k]["q_bh"] = float(q)
        out[label] = cells
    for w in ("all", "w1", "w2", "w3", "diag"):
        fam(lambda x, r, w=w: x[f"{r}/TMIF_Ac_att/{w}"]["corr"], f"H2_TMIF_Ac/{w}")
        fam(lambda x, r, w=w: x[f"{r}/CMI_L_att_given_yAc/{w}"]["corr"], f"H3a_CMI_L/{w}")
    fam(lambda x, r: x[f"{r}/CS_CMI_L_att_given_yAc/all"]["corr"] - x[f"{r}/CS_CMI_L_ign_given_yAc/all"]["corr"], "H3b_attention_CMI_L/all")
    fam(lambda x, r: x[f"{r}/CS_TMIF_Env_att/w1"]["corr"] - x[f"{r}/CS_TMIF_Env_ign/w1"]["corr"], "attention_Env/w1")
    fam(lambda x, r: x[f"{r}/CS_TMIF_Env_att/w2"]["corr"] - x[f"{r}/CS_TMIF_Env_ign/w2"]["corr"], "attention_Env/w2")
    fam(lambda x, r: x[f"{r}/CMI_Ac_att_given_yL/all"]["corr"], "control_CMI_Ac_given_yL/all")
    for term in ("UAc", "UL", "R", "S"):
        for meas in ("CCS", "MMI"):
            fam(lambda x, r, t=term, m=meas: x[f"{r}/MED/{m}_{t}"]["corr"], f"PID_{meas}_{term}")
    fam(lambda x, r: x[f"{r}/MED/CMI_T_yL_given_yAc"]["corr"], "MED_CMI_yL_given_yAc")
    # H7c registered form (within group): C + MI_total vs C + MI_total + CMI_L
    from .h7_explore import loo_risk
    h7 = {}
    for g in ("hi", "nh"):
        ks = [k for k in dd if grp[k] == g and np.isfinite(info.loc[k, "speech_reception_thresholds"])]
        C = info.loc[ks, ["age", "pta4"]].values.astype(float)
        mi_tot = np.array([np.mean([dd[k][f"{r}/MED/I_T_yAcyL"]["corr"] for r in ROIS]) for k in ks])
        cmi_l = np.array([np.mean([dd[k][f"{r}/CMI_L_att_given_yAc/all"]["corr"] for r in ROIS]) for k in ks])
        y = info.loc[ks, "speech_reception_thresholds"].values.astype(float)
        base = loo_risk(np.column_stack([C, mi_tot]), cmi_l, y, seed=63); base["status"] = "REGISTERED_H7c"
        base["step_C_to_C_plus_MI"] = loo_risk(C, mi_tot, y, seed=64)
        h7[g] = base
    out["H7c_registered"] = h7
    json.dump(out, open(os.path.join(RES, "P3_dtu_v2.json"), "w"), indent=1)
    print("written", os.path.join(RES, "P3_dtu_v2.json"))


if __name__ == "__main__":
    {"p2": p2, "p3_public": p3_public, "p3_private": p3_private, "p3_controls": p3_controls, "p3_public_v2": p3_public_v2, "p3_private_v2": p3_private_v2, "p3_controls_v2": p3_controls_v2, "p3_dtu_v2": p3_dtu_v2, "p3_l27z": p3_l27z, "p3_nlbg": p3_nlbg, "p3_nlbg_conv": p3_nlbg_conv, "p3_public_v2_eog": p3_public_v2_eog, "p3_dtu_sur": p3_dtu_sur}[sys.argv[1]]()
