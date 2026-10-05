"""B2 EEG side (docs/auditory_c3/CI_EDG_REG_v1.md): CI-artefact background from simulated electrodograms.

Per participant, EDG features = PCA-5 of the simulated electrodogram of the participant's device family (CI, from
Table 4 coding strategies; both sides' families concatenated when they differ) or of the generic ACE family (TH, HA).
yEDG = ridge LOTO prediction of T from EDG (attended + distractor streams; lags as LAGS). Same estimator, surrogates,
ROIs and mediators (yAc, yBG from the cross-fitted non-linear background bg_l27, yOns) as public_mi.cmd_nlbg.

Usage: python -m auditory_c3.ci_edg_mi run <grp> <subj>
       python -m auditory_c3.ci_edg_mi aggregate
Outputs: private/auditory_c3/public/fau_tud/edg/<grp>/<subj>.json; results/auditory_c3/P3_ci_edg.json (aggregate)
"""
from __future__ import annotations

import csv
import glob
import json
import os
import sys

import numpy as np

from . import stats
from .ci_edg import FEAT as EDG_FEAT, STRATEGY_FAMILY
from .public_mi import FEAT, OUT, _bp, _raw_stim, _subject_obj, _word_trains, _z, ALPHAS, LAGS, build, ridge_loto, window_summary

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROIS = ["frontocentral", "left_temporal", "right_temporal"]
MODE = "edg"
T4 = os.path.join(REPO, "private", "auditory_c3", "jehn_behaviour", "table4_parsed.csv")


def families(grp, subj):
    """Device families of a participant: CI from Table 4 (sorted unique over sides); TH and HA: generic ACE."""
    if grp != "ci":
        return ["ace"]
    rows = {r["ID"]: r for r in csv.DictReader(open(T4))}
    r = rows[subj]
    return sorted({STRATEGY_FAMILY[r["CodR"]], STRATEGY_FAMILY[r["CodL"]]})


class EDG:
    def __init__(self):
        import h5py
        self.f = {fam: h5py.File(os.path.join(EDG_FEAT, f"ci_edg_{fam}_pca5_128hz.h5"), "r") for fam in ("ace", "ab", "medel")}
        self.cache = {}

    def get(self, fams, code, stream, n):
        key = (tuple(fams), code, stream, n)
        if key not in self.cache:
            parts = []
            for fam in fams:
                path = f"{code}/{stream}/edg"
                if path not in self.f[fam]:
                    self.cache[key] = None
                    return None
                v = _bp(self.f[fam][path][()])[:, :n]
                parts.append(np.pad(v, ((0, 0), (0, n - v.shape[1]))) if v.shape[1] < n else v)
            self.cache[key] = np.vstack(parts)
        return self.cache[key]


def run(grp, subj, layer=27):
    words = json.load(open(os.path.join(FEAT, "gpt2_german_word_surprisal.json")))
    fams = families(grp, subj)
    edg = EDG()
    built, stim = build(grp, subj, [layer])
    lname = f"L{layer:02d}"
    res = {"subject": subj, "group": grp, "mode": MODE, "edg_families": fams}
    for roi, b in built.items():
        recs = b["recs"]
        for r in recs:
            n, code = r["n"], r["code"]
            for stream, tag in (("attended", "att"), ("distractor", "ign")):
                v = _raw_stim(stim, code, stream, "bg", "bg_l27", 5, n)
                if v is not None:
                    r["stim"][f"BGl_{tag}"] = v
                e = edg.get(fams, code, stream, n)
                if e is not None:
                    r["stim"][f"EDG_{tag}"] = e
                su, on = _word_trains(words, code, stream, n)
                if su is not None:
                    r["stim"][f"Sur_{tag}"] = su; r["stim"][f"Ons_{tag}"] = on
        tz = [_z(r["T"]) for r in recs]

        def med(kind, k):
            X = [_z(np.vstack([r["stim"].get(f"{kind}_att", np.zeros((k, r["n"]))), r["stim"].get(f"{kind}_ign", np.zeros((k, r["n"])))])) for r in recs]
            return ridge_loto(X, tz, LAGS, ALPHAS)
        k_edg = 5 * len(fams)
        yBG, aB, rB = med("BGl", 5); yEDG, aE, rE = med("EDG", k_edg); yOns, aO, rO = med("Ons", 1)
        keys = ["Ac_att", f"{lname}_att", "EDG_att", "Sur_att"]
        S = _subject_obj(recs, keys, {"yAc": b["yAc"], "yBG": yBG, "yEDG": yEDG, "yOns": yOns}, seed=int(subj) + 13)
        q = {"TMIF_Ac": S.mi("Ac_att"),
             "TMIF_EDG": S.mi("EDG_att"),
             "CMI_EDG_given_yAc": S.cmi("EDG_att", cond_meds=("yAc",)),
             "CMI_Ac_given_yEDG": S.cmi("Ac_att", cond_meds=("yEDG",)),
             "CMI_L_given_yAc": S.cmi(f"{lname}_att", cond_meds=("yAc",)),
             "CMI_L_given_yAc_yEDG": S.cmi(f"{lname}_att", cond_meds=("yAc", "yEDG")),
             "CMI_L_given_yAc_yBG": S.cmi(f"{lname}_att", cond_meds=("yAc", "yBG")),
             "CMI_L_given_yAc_yBG_yEDG": S.cmi(f"{lname}_att", cond_meds=("yAc", "yBG", "yEDG")),
             "CMI_Sur_given_yAc_yOns_yBG": S.cmi("Sur_att", cond_meds=("yAc", "yOns", "yBG")),
             "CMI_Sur_given_yAc_yOns_yBG_yEDG": S.cmi("Sur_att", cond_meds=("yAc", "yOns", "yBG", "yEDG"))}
        for k, arr in q.items():
            for w, v in window_summary(arr).items():
                if w in ("all", "w2", "diag"):
                    res[f"{roi}/{k}/{w}"] = {kk: (vv if kk != "sur" else None) for kk, vv in v.items()}
        res[f"{roi}/tie_fraction"] = S.tie_fraction
        res[f"{roi}/ridge"] = {"BG": {"alpha": aB, "r": rB}, "EDG": {"alpha": aE, "r": rE}, "Ons": {"alpha": aO, "r": rO}}
        res["analysis_version"] = "v2_tie_aware_copnorm"
        print(subj, roi, "EDG|Ac %.5f L|Ac,BG %.5f L|Ac,BG,EDG %.5f Sur|..EDG %.5f" % tuple(
            res[f"{roi}/{k}/all"]["corr"] for k in ("CMI_EDG_given_yAc", "CMI_L_given_yAc_yBG", "CMI_L_given_yAc_yBG_yEDG", "CMI_Sur_given_yAc_yOns_yBG_yEDG")), flush=True)
    d = os.path.join(OUT, MODE, grp); os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, f"{subj}.json"), "w"), default=float)


# ------------------------------------------------------------------------------------------------ aggregate
def _load(grp):
    return {os.path.basename(p)[:-5]: json.load(open(p)) for p in sorted(glob.glob(os.path.join(OUT, MODE, grp, "*.json")))}


def aggregate():
    heldout = set(json.load(open(os.path.join(OUT, "th_split.json")))["heldout_half"])
    data = {g: _load(g) for g in ("th", "ha", "ci")}
    data["th"] = {k: v for k, v in data["th"].items() if k in heldout}
    out = {"n": {g: len(v) for g, v in data.items()}, "th_reference": "14 held-out TH", "spec": "docs/auditory_c3/CI_EDG_REG_v1.md"}
    keys = ("TMIF_Ac", "TMIF_EDG", "CMI_EDG_given_yAc", "CMI_Ac_given_yEDG", "CMI_L_given_yAc", "CMI_L_given_yAc_yEDG", "CMI_L_given_yAc_yBG",
            "CMI_L_given_yAc_yBG_yEDG", "CMI_Sur_given_yAc_yOns_yBG", "CMI_Sur_given_yAc_yOns_yBG_yEDG")
    for key in keys:
        out[key] = {}
        for w in ("all", "w2", "diag"):
            cells, ps = {}, []
            for r in ROIS:
                vals = {g: [x[f"{r}/{key}/{w}"]["corr"] for x in data[g].values()] for g in data}
                for g in data:
                    cells[f"{r}/{g}/mean"] = stats.mean_ci(vals[g], seed=11)
                for g in ("ha", "ci"):
                    d = stats.diff_ci(vals[g], vals["th"], seed=12); cells[f"{r}/{g}-th"] = d; ps.append(d["p_perm"])
            for k, q in zip([k for k in cells if k.endswith("-th")], stats.bh(ps)):
                cells[k]["q_bh"] = float(q)
            out[key][w] = cells
    # paired change from adding yEDG (per participant), all window
    out["paired_change_all"] = {}
    for a, b in (("CMI_L_given_yAc_yBG_yEDG", "CMI_L_given_yAc_yBG"), ("CMI_L_given_yAc_yEDG", "CMI_L_given_yAc"),
                 ("CMI_Sur_given_yAc_yOns_yBG_yEDG", "CMI_Sur_given_yAc_yOns_yBG")):
        for g in data:
            for r in ROIS:
                dd = [x[f"{r}/{a}/all"]["corr"] - x[f"{r}/{b}/all"]["corr"] for x in data[g].values()]
                out["paired_change_all"][f"{g}/{r}/{a} - {b}"] = stats.mean_ci(dd, seed=21)
    fn = os.path.join(REPO, "results", "auditory_c3", "P3_ci_edg.json")
    json.dump(out, open(fn, "w"), indent=1); print("written", fn)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "run":
        run(a[1], a[2])
    else:
        aggregate()
