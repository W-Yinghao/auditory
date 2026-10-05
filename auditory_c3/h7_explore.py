"""H7 envelope-level substitutes (MEASUREMENT_AMENDMENT_001 §8): EXPLORATORY, never a claim. The registered H7 needs
I(T; L | Ac) and is not evaluable without audio (DTU, Federici) or behaviour (FAU/TUD).

For each cohort: leave-one-out linear prediction of the behavioural outcome from C (clinical baseline) versus
C + envelope information (frontocentral ROI, bias- and surrogate-corrected), squared-error risk; risk difference
(C+MI minus C, negative = MI helps) with a paired bootstrap over participants (10 000).
  DTU (within group, HI and NH separately): outcome SRT (dB, lower = better); C = age, PTA4 (0.5/1/2/4 kHz, both ears);
      MI = TMIF_Env_att over 0-600 ms.
  Federici CI: outcome % comprehension accuracy; C = age (months), implant experience (months); MI = Env TMIF 150-600 ms.
  Federici HC: outcome comprehension accuracy; C = age; MI as above.
Output: results/auditory_c3/H7_exploratory_envelope.json (aggregate only).
"""
from __future__ import annotations

import glob
import json
import os
import re

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(REPO, "private", "auditory_c3", "public")
RES = os.path.join(REPO, "results", "auditory_c3")


def loo_risk(C, m, y, seed=0):
    C, y = np.asarray(C, float), np.asarray(y, float)
    X0 = np.column_stack([np.ones(len(y)), C]); X1 = np.column_stack([X0, m])
    e0, e1 = [], []
    for i in range(len(y)):
        tr = np.arange(len(y)) != i
        for X, e in ((X0, e0), (X1, e1)):
            b = np.linalg.lstsq(X[tr], y[tr], rcond=None)[0]; e.append((y[i] - X[i] @ b) ** 2)
    e0, e1 = np.array(e0), np.array(e1)
    d = e1 - e0
    rng = np.random.default_rng(seed)
    bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(10_000)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"n": int(len(y)), "risk_C": float(e0.mean()), "risk_C_plus_MI": float(e1.mean()), "risk_diff": float(d.mean()),
            "ci_low": float(lo), "ci_high": float(hi), "excludes_0": bool(hi < 0 or lo > 0), "status": "EXPLORATORY_NOT_A_CLAIM"}


def main():
    out = {}
    part = pd.read_csv("/projects/EEG-foundation-model/auditory_public/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
    cols = [f"audiogram_{e}_ear_{f}Hz" for e in ("right", "left") for f in (500, 1000, 2000, 4000)]
    part["pta4"] = part[cols].astype(float).mean(1)
    dtu = {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob(os.path.join(PUB, "dtu", "*.json"))}
    for grp in ("hi", "nh"):
        rows = part[(part.hearing_status == grp) & part.participant_id.isin(dtu)].dropna(subset=["speech_reception_thresholds", "age", "pta4"])
        mi = [dtu[s]["frontocentral/TMIF_Env_att/all"]["corr"] for s in rows.participant_id]
        out[f"DTU_SRT/{grp}"] = loo_risk(rows[["age", "pta4"]].values, mi, rows.speech_reception_thresholds.values, seed=1)
    B = glob.glob("/projects/EEG-foundation-model/auditory_public/federici_ci_children/mendeley_nzg5g2gzrd_v2/files/*/Code")[0]
    fd = json.load(open(os.path.join(PUB, "federici", "tmif.json")))["subjects"]
    num = lambda x: int(re.sub(r"\D", "", str(x))) if re.sub(r"\D", "", str(x)) else None
    ci = pd.read_excel(os.path.join(B, "07_TRF_CI_biomarker", "CDAD_variable.xlsx"))
    ci["id"] = ci["Progressive_Code_Exp "].map(num)
    eeg_ci = {num(k.split("/")[1]): v for k, v in fd.items() if v["group"] == "CI"}
    ci = ci[ci.id.isin(eeg_ci)].dropna(subset=["% Beahv Acc", "Age when participated in the experiment in MONTHS", "Experience with implants (months)"])
    out["Federici_comprehension/CI"] = loo_risk(ci[["Age when participated in the experiment in MONTHS", "Experience with implants (months)"]].values,
                                                [eeg_ci[i]["Env/w2"]["corr"] for i in ci.id], ci["% Beahv Acc"].values, seed=2)
    out["Federici_comprehension/CI"]["linked"] = int(len(ci))
    hc = pd.read_excel(os.path.join(B, "02_HC_Encoding_model", "Descrittive&BehavHC.xlsx"))
    hc["id"] = hc["codice exp"].map(num)
    eeg_hc = {num(k.split("/")[1]): v for k, v in fd.items() if v["group"] == "HC"}
    hc = hc[hc.id.isin(eeg_hc)].dropna(subset=["Behav acc", "età al test in anni"])
    out["Federici_comprehension/HC"] = loo_risk(hc[["età al test in anni"]].values, [eeg_hc[i]["Env/w2"]["corr"] for i in hc.id], hc["Behav acc"].values, seed=3)
    out["Federici_comprehension/HC"]["linked"] = int(len(hc))
    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "H7_exploratory_envelope.json"), "w"), indent=1)
    print(json.dumps({k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()
