"""Realistic null calibration (C3 review addendum item 7): the real stimulus variables, trial structure, valid ranges,
ridge mediators and surrogate scheme of real subjects, but T replaced by stimulus-independent EEG-like noise
(3-d AR(2) with an alpha/theta-like spectrum, then the same 1-8 Hz FIR). Under this null every null_excess should be
centred on 0; its spread is the per-subject noise floor of the pipeline.

Usage: python -m auditory_c3.nullcal
Output: results/auditory_c3/null_calibration.json (aggregate only; no EEG values)
"""
from __future__ import annotations

import json
import os

import numpy as np

from .public_mi import (ALPHAS, LAGS, OUT as PUBOUT, REPO, _bp, _subject_obj, _z, build, ridge_loto, window_summary)

SUBJECTS = ["303", "305", "306", "308"]  # held-out-half TH stimulus/trial structures (their EEG is not used)
REPS = 5


def _ar2_noise(rng, n, d=3):
    a1, a2 = 1.6, -0.8  # resonance ~ 7 Hz at 128 Hz with strong low-frequency power
    x = np.zeros((d, n)); e = rng.standard_normal((d, n))
    for i in range(2, n):
        x[:, i] = a1 * x[:, i - 1] + a2 * x[:, i - 2] + e[:, i]
    return _bp(x)


def main():
    split = json.load(open(os.path.join(PUBOUT, "th_split.json")))
    subs = [s for s in SUBJECTS if s in split["heldout_half"]] or split["heldout_half"][:4]
    rng = np.random.default_rng(20261007)
    res = {k: [] for k in ("TMIF_Ac_att/all", "CMI_L_att_given_yAc/all", "CMI_L_att_given_yAc/w2", "CMI_L_att_given_yAc/diag",
                           "CS_TMIF_Env_ign/all", "CS_CMI_L_ign_given_yAc/all", "TMIF_Env_att/all")}
    for s in subs:
        built, _ = build("th", s, [27])
        b = built["frontocentral"]
        for rep in range(REPS):
            recs = [dict(r, T=_ar2_noise(rng, r["n"])) for r in b["recs"]]
            feats = [_z(np.vstack([r["stim"].get("Ac_att", np.zeros((5, r["n"]))), r["stim"].get("Ac_ign", np.zeros((5, r["n"])))])) for r in recs]
            yAc, _, _ = ridge_loto(feats, [_z(r["T"]) for r in recs], LAGS, ALPHAS)
            S = _subject_obj(recs, ["Ac_att", "L27_att", "Env_att"], {"yAc": yAc}, seed=rep)
            Sc = _subject_obj(recs, ["Env_ign", "L27_ign"], {"yAc": yAc}, seed=rep + 1, cs=True)
            q = {"TMIF_Ac_att": S.mi("Ac_att"), "CMI_L_att_given_yAc": S.cmi("L27_att", cond_meds=("yAc",)),
                 "TMIF_Env_att": S.mi("Env_att"), "CS_TMIF_Env_ign": Sc.mi("Env_ign"),
                 "CS_CMI_L_ign_given_yAc": Sc.cmi("L27_ign", cond_meds=("yAc",))}
            for k in res:
                name, w = k.split("/")
                res[k].append(window_summary(q[name])[w]["corr"])
            print(s, rep, {k: round(v[-1] * 1e4, 3) for k, v in res.items()}, flush=True)
    out = {k: {"n_runs": len(v), "mean_x1e4": float(np.mean(v) * 1e4), "sd_x1e4": float(np.std(v, ddof=1) * 1e4),
               "max_abs_x1e4": float(np.max(np.abs(v)) * 1e4)} for k, v in res.items()}
    out["design"] = {"subjects_structure_only": subs, "reps": REPS, "T": "3-d AR(2) noise (a1 1.6, a2 -0.8) + 1-8 Hz FIR, independent of the stimulus", "roi": "frontocentral structure"}
    os.makedirs(os.path.join(REPO, "results", "auditory_c3"), exist_ok=True)
    json.dump(out, open(os.path.join(REPO, "results", "auditory_c3", "null_calibration.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
