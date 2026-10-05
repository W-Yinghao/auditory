"""Aggregate-only figures for the C3 results (results/auditory_c3/figures/). No per-participant point is drawn for
private data; public per-lag curves are group means with SEM bands."""
from __future__ import annotations

import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results", "auditory_c3")
FIG = os.path.join(RES, "figures")
COL = {"th": "#1f77b4", "ha": "#2ca02c", "ci": "#9e9e9e"}
LAB = {"th": "TH (n=28)", "ha": "HA (n=29)", "ci": "CI (n=24, artefact-limited)"}


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(FIG, exist_ok=True)
    d = json.load(open(os.path.join(RES, "P3_public.json")))
    lags = np.array(d["lags_ms"])
    keys = [("TMIF_Env_att", "I(T; envelope)"), ("TMIF_Ac_att", "I(T; Ac)  [Whisper L1-2, k=5]"),
            ("CMI_L_att_given_yAc", "I(T; L27 | ŷ_Ac)")]
    rois = ["frontocentral", "left_temporal", "right_temporal"]
    fig, ax = plt.subplots(3, 3, figsize=(13, 9), sharex=True)
    for i, (k, title) in enumerate(keys):
        for j, r in enumerate(rois):
            a = ax[i, j]
            for g in ("th", "ha", "ci"):
                c = d["curves"][k][f"{g}/{r}"]
                m, se = np.array(c["mean"]) * 1e4, np.array(c["sem"]) * 1e4
                a.plot(lags, m, color=COL[g], ls="--" if g == "ci" else "-", lw=1.4, label=LAB[g])
                a.fill_between(lags, m - se, m + se, color=COL[g], alpha=0.15)
            a.axvline(0, color="k", lw=0.6); a.axhline(0, color="k", lw=0.4)
            for x in (80, 90, 300):
                a.axvline(x, color="#bbbbbb", lw=0.5, ls=":")
            a.set_title(f"{title}\n{r}", fontsize=9)
            if j == 0:
                a.set_ylabel("bits × 1e-4 (bias- and surrogate-corrected)", fontsize=8)
            if i == 2:
                a.set_xlabel("lag (ms; stimulus leads)")
    ax[0, 0].legend(fontsize=7)
    fig.suptitle("FAU/TUD speech tracking by group (mean ± SEM). G2 failed in CI: CI curves are descriptive only.", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fau_tud_tmif_cmi.png"), dpi=130); plt.close(fig)

    # Federici + phantom head (P2 data)
    fd = json.load(open(os.path.join(REPO, "private", "auditory_c3", "public", "federici", "tmif.json")))
    fl = np.array(fd["lags_ms"])
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for g, c in (("HC", "#1f77b4"), ("CI", "#d62728"), ("HC-v", "#ff7f0e"), ("Artifact", "#555555")):
        A = np.array([np.array(v["Env/per_lag_obs"]) - np.array(v["Env/per_lag_sur_mean"]) for v in fd["subjects"].values() if v["group"] == g]) * 1e4
        m, se = A.mean(0), A.std(0, ddof=1) / np.sqrt(len(A))
        for a in ax:
            a.plot(fl, m, color=c, label=f"{g} (n={len(A)})"); a.fill_between(fl, m - se, m + se, color=c, alpha=0.15)
    ax[1].set_ylim(-1, 16)
    for a in ax:
        a.axvline(0, color="k", lw=0.6); a.axvline(150, color="#bbbbbb", ls=":"); a.set_xlabel("lag (ms)"); a.set_ylabel("bits × 1e-4")
    ax[0].set_title("Federici children: envelope TMIF incl. phantom head"); ax[1].set_title("same, zoomed (humans)")
    ax[0].legend(fontsize=8); fig.tight_layout(); fig.savefig(os.path.join(FIG, "federici_phantom.png"), dpi=130); plt.close(fig)

    # private H4 by stage (aggregate means and intervals only)
    p = json.load(open(os.path.join(RES, "P3_private_aggregate.json")))
    groups = ["NH", "HA_early_0_2", "HA_mid_2_13", "HA_late_ge13"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    for a, key, title in ((ax[0], "H4a/I_T_Cur/{}", "I(T; current class)"), (ax[1], "H4b/I_T_Hist_given_Cur/since_last_deviant/{}", "I(T; history | current)")):
        for x, g in enumerate(groups):
            v = p[key.format(g)]
            if "est" in v:
                a.errorbar(x, v["est"] * 1e3, yerr=[[(v["est"] - v["ci_low"]) * 1e3], [(v["ci_high"] - v["est"]) * 1e3]], fmt="o", color="k", capsize=3)
                a.text(x, v["ci_high"] * 1e3, f" n={v['n']}", fontsize=7, va="bottom", ha="center")
        a.axhline(0, color="k", lw=0.5); a.set_xticks(range(len(groups))); a.set_xticklabels(["NH", "HA 0-2 m", "HA 2-13 m", "HA ≥13 m"], fontsize=8)
        a.set_ylabel("bits × 1e-3 (mean, 95% bootstrap CI)"); a.set_title(title, fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "private_h4.png"), dpi=130); plt.close(fig)
    print("figures written", sorted(os.listdir(FIG)))


if __name__ == "__main__":
    main()
