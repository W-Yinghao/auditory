"""ALN3 ADDENDUM_08: private researcher summary - group (HA - NH), age, wearing duration and HA-stage associations of the task scores
of the completed seed-3401 E units (predeclared configurations), plus the ADDENDUM_05 private interim tables. Output private (0600).
Usage: python -m auditory_alignment_v3.aln32_private_summary"""
from __future__ import annotations

import json
import os
import re
import time

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core
from auditory_alignment_v3.sci_r1 import stats as S

OUTD = os.path.join(core.OUT, "bc_interim", "private")
CONFIGS = [("E_LOCAL", "NCE", "lag_local_tokens", "full"), ("E_LOCAL", "CS_SINGLE", "lag_local_tokens", "full"), ("E_GX", "GX_NATIVE", "GX", "full"),
           ("E_GENERIC", "NCE", "reve", "pretrained_full"), ("E_GENERIC", "NCE", "reve", "random_full"),
           ("E_GENERIC", "NCE", "cbramod", "pretrained_full"), ("E_GENERIC", "NCE", "cbramod", "random_full"),
           ("E_PUBLIC_TRANSFER", "NCE", "lag_local_tokens", "task_full"), ("E_COMPLEMENT", "NCE", "reve", "residual_pretrained_frozen", "combined"),
           ("E_DISTILL", "NCE", "local_teacher", "full", "chosen")]
ENDPOINTS = ("AUC", "NLL", "hist_gain")
STAGES = (("0-2 m", lambda m: m <= 2), ("2-13 m", lambda m: 2 < m < 13), (">=13 m", lambda m: m >= 13))


def covariates(rows, load):
    cov = {}
    for r in rows:
        if r["family_id"] == "E_LOCAL" and r["seed"] == BI.SEED and r["spec"]["architecture"] == "lag_local_tokens" and r["spec"]["window"] == "full" and r["spec"]["objective"] == "NCE":
            rec = load(r["experiment_id"])
            for c, v in rec["eval"]["per_participant"].items():
                cov[c] = {"group": v.get("group"), "age_m": v.get("age_months"), "dur_m": v.get("duration_months")}
    return cov


def cell(Y, cov, fn):
    """Y {child: value} -> analyses of ADDENDUM_08 §3."""
    ha = {c: y for c, y in Y.items() if cov.get(c, {}).get("group") == "HA" and np.isfinite(y)}
    nh = {c: y for c, y in Y.items() if cov.get(c, {}).get("group") == "NH" and np.isfinite(y)}
    out = {"n_HA": len(ha), "n_NH": len(nh)}
    g = S.contrast(np.array(list(ha.values())), np.array(list(nh.values())), seed=S.group_seed(fn, "group"))
    out["HA_minus_NH"] = {k: float(g[k]) for k in ("est", "ci_low", "ci_high")} if "est" in g else {"note": g.get("note")}
    for name, key in (("age_per_year", "age_m"), ("duration_per_year", "dur_m")):
        ids = [c for c in ha if cov[c].get(key) is not None and np.isfinite(cov[c][key])]
        if len(ids) < 8:
            out[name] = {"n": len(ids), "note": "too few"}; continue
        o = S.ols(np.array([cov[c][key] / 12.0 for c in ids]), np.array([ha[c] for c in ids]), [name], seed=S.group_seed(fn, name))
        cf = o["coef"][name] if "coef" in o else {}
        out[name] = {"n": len(ids), **{k: cf[k] for k in ("est", "ci_low", "ci_high")}} if cf else {"n": len(ids), "note": o.get("note")}
    bins = {}
    for lab, f in STAGES:
        bins[lab] = np.array([ha[c] for c in ha if cov[c].get("dur_m") is not None and f(cov[c]["dur_m"])])
    out["stage_means"] = {lab: ({"n": len(v), "mean": float(v.mean())} if len(v) >= BI.MIN_N else {"n": len(v)}) for lab, v in bins.items()}
    for lab in (">=13 m", "2-13 m"):
        a, b = bins[lab], bins["0-2 m"]
        if len(a) >= BI.MIN_N and len(b) >= BI.MIN_N:
            c = S.contrast(a, b, seed=S.group_seed(fn, lab))
            out[f"stage_{lab}_minus_0-2"] = {k: float(c[k]) for k in ("est", "ci_low", "ci_high")}
        else:
            out[f"stage_{lab}_minus_0-2"] = {"n": [len(a), len(b)], "note": "n < 5 in a bin"}
    return out


def main():
    from auditory_alignment_v3 import run as r3
    rows = r3.all_rows(); load = BI.unit_loader()
    pdata = BI.load_private(rows, load)
    cov = covariates(rows, load)
    res = {"meta": {"addendum": "ADDENDUM_08_PRIVATE_RESEARCHER_SUMMARY.md", "seed": BI.SEED, "n_boot": S.NB}, "cells": {}}
    for c in CONFIGS:
        vals = pdata["vals"].get(tuple(c)) or {}
        for ep in ENDPOINTS:
            Y = {ch: v[ep] for ch, v in vals.items() if ep in v}
            if not Y:
                continue
            res["cells"][f"{BI.ckey(c)}|{ep}"] = cell(Y, cov, f"{BI.ckey(c)}|{ep}")
    n_cells = sum(1 for v in res["cells"].values() for k in v if k not in ("n_HA", "n_NH", "stage_means"))
    f = lambda d: "–" if not isinstance(d, dict) or "est" not in d else f"{d['est']:+.3f} [{d['ci_low']:+.3f}, {d['ci_high']:+.3f}]" + (f" (n={d['n']})" if "n" in d else "")
    L = ["# Private researcher summary — ALN3 E units (PRIVATE, 0600; not for publication)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} (Slurm {os.environ.get('SLURM_JOB_ID', 'local')}) under the frozen `ADDENDUM_08_PRIVATE_RESEARCHER_SUMMARY.md`. "
         "Seed 3401; identity-level bootstrap-t intervals (pointwise; conditional on the fitted models). AUC = positive-affine (= native ranking); NLL = "
         "natural-distribution NLL in bits (lower is better); hist gain = q_hist+EEG vs q_hist (bits). Age and duration are fitted in separate models "
         "(age = fitting age + duration). E_GENERIC pretrained_full vs random_full are recipe contrasts (CORRECTION_01).", "",
         f"{n_cells} interval cells in the table below; none is singled out. Precision is limited (HA n ≈ 55, NH n = 9) and the task signal is weak; "
         "an unresolved association is not evidence of no effect.", "",
         "## 1. Group, age, wearing duration and HA stage", "",
         "| configuration · endpoint | n HA / NH | HA − NH | age (per year, HA) | duration (per year, HA) | stage means 0–2 / 2–13 / ≥13 m | ≥13 − 0–2 | 2–13 − 0–2 |",
         "|---|---|---|---|---|---|---|---|"]
    for k, v in res["cells"].items():
        sm = " / ".join((f"{x['mean']:.3f} (n={x['n']})" if "mean" in x else f"n={x['n']}") for x in v["stage_means"].values())
        L.append(f"| {k.replace('|', ' · ')} | {v['n_HA']} / {v['n_NH']} | {f(v['HA_minus_NH'])} | {f(v['age_per_year'])} | {f(v['duration_per_year'])} | {sm} | "
                 f"{f(v['stage_>=13 m_minus_0-2'])} | {f(v['stage_2-13 m_minus_0-2'])} |")
    L += ["", "## 2. Method comparisons (ADDENDUM_05 private interim, unchanged)", ""]
    interim = os.path.join(OUTD, "PRIVATE_E_INTERIM.md")
    if os.path.exists(interim):
        L += [l for l in open(interim).read().splitlines()[1:]]
    L += ["", "## 3. Related private documents", "", "- `docs/auditory_alignment_v3/SCI_R1_PRIVATE_RESULTS.md` (S4 group / age / stage of the lag curves)",
          "- `docs/auditory_alignment_v3/R_PRIVATE_CALIBRATION_RESULTS.md` (calibration variants)", ""]
    os.makedirs(OUTD, exist_ok=True)
    jp, mp = os.path.join(OUTD, "private_age_stage.json"), os.path.join(OUTD, "PRIVATE_RESEARCHER_SUMMARY.md")
    BI.write_json(jp, res, private=True)
    open(mp, "w").write("\n".join(L)); os.chmod(mp, 0o600)
    kids = set(cov)
    bad = [p for p in (jp, mp) if re.search(r"\bchild\d+\b", open(p).read()) or any(re.search(rf"\b{re.escape(c)}\b", open(p).read()) for c in kids)]
    print("cells", len(res["cells"]), "| privacy scan:", "PASS" if not bad else bad)
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
