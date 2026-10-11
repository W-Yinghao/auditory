"""Markdown tables from the round-1 aggregates (results/auditory_alignment_v3/sci_r1/*.json and private_agg/), so the SCI_* documents
carry no hand-transcribed numbers. Writes table fragments to private/auditory_alignment_v3/sci_r1/report/ (continuous) and
results/.../private_agg/report/ (private task; 0700). Also draws S3 channel maps (MNE topomaps on the standard_1005 layout) for the
continuous datasets. Usage: python -m auditory_alignment_v3.sci_r1.report"""
from __future__ import annotations

import json
import os

import numpy as np

from auditory_alignment_v3 import core

RES = os.path.join(core.REPO, "results", "auditory_alignment_v3", "sci_r1")
PRIV = os.path.join(RES, "private_agg")
OUTD = os.path.join(core.OUT, "sci_r1", "report")
DSN = {"fau": "FAU", "dtu": "DTU", "federici": "Federici", "private_bdf": "私有"}


def load(name, priv=False):
    return json.load(open(os.path.join(PRIV if priv else RES, name)))["data"]


def f3(x, d=3):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{d}f}" if isinstance(x, (int, float)) else str(x)


def ci(s, d=3, sim=None):
    """'est [lo, hi] (n)' for a scalar summary; sim = (lo, hi) simultaneous interval."""
    if not s or "est" not in s:
        return f"n={s.get('n', 0)}（不报）" if isinstance(s, dict) else "—"
    est = s["est"] if not isinstance(s["est"], list) else s["est"][0]
    lo = s["ci_low"] if not isinstance(s["ci_low"], list) else s["ci_low"][0]
    hi = s["ci_high"] if not isinstance(s["ci_high"], list) else s["ci_high"][0]
    out = f"{f3(est, d)} [{f3(lo, d)}, {f3(hi, d)}]"
    if sim:
        out += f" {{{f3(sim[0], d)}, {f3(sim[1], d)}}}"
    n = s.get("n", s.get("n_a"))
    return out + (f" (n={n})" if n is not None else "")


def table(header, rows):
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + ["| " + " | ".join(map(str, r)) + " |" for r in rows]) + "\n"


def primary_tables(prim):
    out = []
    for ds, r in prim.items():
        for fam, fr in r.items():
            if "members" not in fr:
                continue
            sims = (fr.get("family_maxt") or {}).get("intervals", {})
            rows = [[m, ci(s, sim=(sims[m]["sim_low"], sims[m]["sim_high"]) if m in sims else None)] for m, s in fr["members"].items()]
            side = fr.get("listed_alongside_not_in_family", {}).get("members", {})
            rows += [[f"（并列，不进族）{m}", ci(s)] for m, s in side.items()]
            out.append(f"**{DSN[ds]} · {fam}**（共同身份 n={fr['n_common']}；族内 max-t 临界值 {(fr.get('family_maxt') or {}).get('crit', float('nan')):.2f}；"
                       f"{fr.get('seed_policy', '')}）\n\n" + table(["量", "估计 [95% CI] {族内同时区间} (n)"], rows))
    return "\n".join(out)


def window_tables(s1, ds, metric="gain_bits"):
    r = s1[ds]; rows = []
    for w in ("early", "late"):
        rows.append([f"原始 · {w}", ci(r["raw"]["windows"][metric][w]["all"])])
    for obj, ro in r["objectives"].items():
        for n in ("frozen", "frozen_3seed", "aln2", "untrained_s3401", "untrained_3draws"):
            if n in ro["windows"]:
                for w in ("early", "late"):
                    rows.append([f"{obj} {n} · {w}", ci(ro["windows"][n][metric][w]["all"])])
    return table(["曲线 · 窗口（全部人类身份）", f"{metric} 估计 [95% CI] (n)"], rows)


def paired_tables(s1, ds):
    rows = []
    for obj, ro in s1[ds]["objectives"].items():
        for name, pr in ro["paired"].items():
            for m in ("rank_gain", "gain_bits", "regular_logloss_bits"):
                rows.append([f"{obj} {name}", m, ci(pr[m]["early"]["all"]), ci(pr[m]["late"]["all"])])
    return table(["配对差", "指标", "早窗", "晚窗"], rows)


def mdsb_tables(s1, ds):
    rows = []
    for obj, ro in s1[ds]["objectives"].items():
        for key in ("md_P0", "sb_P0", "md_P1", "sb_P1"):
            if key in ro:
                d = ro[key]
                rows.append([f"{obj} {key}", ci(d["early_R"]["all"]), ci(d["late_R"]["all"]), ci(d["early_touching_R"]["all"]), ci(d["late_touching_R"]["all"])])
    return table(["面板", "早窗（完全落窗 token）ΔR", "晚窗 ΔR", "早窗（含跨界）ΔR", "晚窗（含跨界）ΔR"], rows)


def triad_tables(tri, ds):
    rows = []
    for key, d in tri[ds].items():
        rows.append([key, ",".join(map(str, d["seeds"])), ci(d["R_early_minus_R_joint"]["all"]), ci(d["R_late_minus_R_joint"]["all"]), ci(d["R_joint_minus_R_full"]["all"])])
    return table(["目标|objective", "seed", "R(E)−R(E,L)", "R(L)−R(E,L)", "R(E,L)−R(full)"], rows)


def group_window_table(s1, ds, obj, n="frozen", metric="gain_bits"):
    from auditory_alignment_v3.sci_r1.aggregate import GROUPS
    rows = []
    ro = s1[ds]["objectives"][obj]
    for g in GROUPS[ds]:
        rows.append([g, ci(ro["windows"][n][metric]["early"].get(g, {})), ci(ro["windows"][n][metric]["late"].get(g, {})),
                     ci(s1[ds]["raw"]["windows"][metric]["early"].get(g, {})), ci(s1[ds]["raw"]["windows"][metric]["late"].get(g, {}))])
    return table(["组", f"冻结 {obj} 早", f"冻结 {obj} 晚", "原始 早", "原始 晚"], rows)


def tg_tables(tg, ds):
    rows = []
    for obj, ro in tg[ds].items():
        for n in ("frozen", "raw", "untrained_s3401", "aln2"):
            if n not in ro:
                continue
            for cname in ("R", "G") if ds != "private_bdf" else ("AUC", "NLL"):
                if cname not in ro[n]:
                    continue
                b = ro[n][cname]["blocks"]
                rows.append([f"{obj} {n}", cname, ci(b["D_E"]["all"]), ci(b["D_L"]["all"]), ci(b["G_EL"]["all"]), ci(b["G_LE"]["all"]),
                             ci(b["D_E_minus_G_EL"]["all"]), ci(b["D_L_minus_G_LE"]["all"])])
    return table(["模型", "格值", "D_E", "D_L", "G_EL", "G_LE", "D_E−G_EL", "D_L−G_LE"], rows)


def contrast_tables(s4, ds):
    rows = []
    fams = s4[ds].get("families", {})
    for key, c in s4[ds]["contrasts"].items():
        fam, name, pair = key.split("|")
        sims = (fams.get(f"group|{fam}") or {}).get("intervals", {}).get(f"{name}|{pair}")
        rows.append([fam, name, pair, ci(c, sim=(sims["sim_low"], sims["sim_high"]) if sims else None)])
    return table(["族", "对象", "组差", "估计 [95% CI] {族内同时区间}"], rows)


def dev_tables(s4, ds):
    rows = []
    fams = s4[ds].get("families", {})
    for key, o in s4[ds]["development"].items():
        if key.endswith("stage_bins"):
            rows.append([key, "阶段分箱", "; ".join(f"{b}: {ci(v)}" for b, v in o.items())]); continue
        if "coef" not in o:
            rows.append([key, "—", f"n={o.get('n')}"]); continue
        cname = [c for c in o["coef"] if c != "intercept"][0] if "duration" not in key else "duration_months"
        cf = o["coef"][cname]
        rows.append([key, cname, f"{f3(cf['est'], 4)} [{f3(cf['ci_low'], 4)}, {f3(cf['ci_high'], 4)}] (n={o['n']}) {o.get('note', '')}"])
    return table(["模型", "系数", "估计 [95% CI] (n)"], rows)


def fun_tables(s4, ds):
    rows = []
    for key, o in s4[ds]["function"].items():
        if "coef" not in o:
            rows.append([key, f"n={o.get('n')}", "—"]); continue
        cf = o["coef"]["readability"]; nl = o.get("nested_loo", {})
        st = nl.get("step1_minus_step0", {})
        rows.append([key, f"{f3(cf['est'], 3)} [{f3(cf['ci_low'], 3)}, {f3(cf['ci_high'], 3)}] (n={o['n']})",
                     f"{f3(st.get('est'), 4)} [{f3(st.get('ci_low'), 4)}, {f3(st.get('ci_high'), 4)}]" if st else "—"])
    return table(["测量模型", "可读性系数 [95% CI] (n)", "嵌套留一风险差（协变量+可读性 − 协变量；负 = 改善）"], rows)


def topomaps(s3, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mne
    made = []
    alias = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}
    for ds, d in s3.items():
        chans = [alias.get(c, c) for c in d["channels"]]
        info = mne.create_info(chans, 100.0, "eeg")
        try:
            info.set_montage(mne.channels.make_standard_montage("standard_1005"), on_missing="ignore")
        except Exception:  # noqa: BLE001
            continue
        panels = [(f"raw Haufe {w}", np.asarray(d["raw_haufe"][w]["mean"])) for w in ("early", "late") if w in d.get("raw_haufe", {})]
        for obj in ("NCE", "CS_SINGLE"):
            fe = d.get(f"first_layer_explained_fraction_{obj}")
            if fe:
                panels.append((f"1st-layer expl. {obj}", np.asarray(fe["mean"])))
            co = d.get(f"channel_occlusion_{obj}", {}).get("all")
            if co and "est" in co:
                panels.append((f"channel occlusion {obj}", np.asarray(co["est"])))
        if not panels:
            continue
        fig, axes = plt.subplots(1, len(panels), figsize=(2.6 * len(panels), 2.8))
        for ax, (title, v) in zip(np.atleast_1d(axes), panels):
            if (v >= 0).all():  # non-negative summaries: sequential scale over the map's own range (relative pattern)
                lo, hi = float(v.min()), float(v.max())
                mne.viz.plot_topomap(v, info, axes=ax, show=False, contours=0, cmap="viridis", vlim=(lo, hi))
            else:  # signed (channel occlusion): symmetric diverging scale
                m = float(np.abs(v).max()); lo, hi = -m, m
                mne.viz.plot_topomap(v, info, axes=ax, show=False, contours=0, cmap="RdBu_r", vlim=(lo, hi))
            ax.set_title(f"{title}\n[{lo:.3g}, {hi:.3g}]", fontsize=6)
        fig.suptitle(f"{ds}: model-level maps (descriptive; not source estimates)", fontsize=8)
        p = os.path.join(outdir, f"S3_{ds}_maps.png"); fig.tight_layout(); fig.savefig(p, dpi=120); plt.close(fig); made.append(p)
    return made


def main():
    os.makedirs(OUTD, mode=0o700, exist_ok=True)
    s1 = load("SCI_R1_S1_time_curves.json"); prim = load("SCI_R1_primary_families.json"); tg = load("SCI_R1_temporal_generalization.json")
    tri = load("SCI_R1_window_triad.json"); s3 = load("SCI_R1_spatial_readout.json"); s4 = load("SCI_R1_group_development.json")
    parts = {"primary": primary_tables(prim)}
    for ds in ("fau", "dtu", "federici"):
        parts[f"windows_{ds}"] = window_tables(s1, ds) + "\n" + window_tables(s1, ds, "rank_gain")
        parts[f"paired_{ds}"] = paired_tables(s1, ds)
        parts[f"mdsb_{ds}"] = mdsb_tables(s1, ds)
        parts[f"triad_{ds}"] = triad_tables(tri, ds)
        parts[f"tg_{ds}"] = tg_tables(tg, ds)
        parts[f"contrasts_{ds}"] = contrast_tables(s4, ds)
        parts[f"development_{ds}"] = dev_tables(s4, ds)
        parts[f"function_{ds}"] = fun_tables(s4, ds)
        for obj in ("NCE", "CS_SINGLE"):
            parts[f"groupwin_{ds}_{obj}"] = group_window_table(s1, ds, obj)
    for k, v in parts.items():
        open(os.path.join(OUTD, f"{k}.md"), "w").write(v)
    figs = topomaps(s3, os.path.join(RES, "figures"))
    # private task tables (0700 area)
    pd_ = os.path.join(PRIV, "report"); os.makedirs(pd_, mode=0o700, exist_ok=True)
    ps1 = load("SCI_R1_private_S1.json", True); ptg = load("SCI_R1_private_TG.json", True); ptri = load("SCI_R1_private_triad.json", True)
    ps4 = load("SCI_R1_private_S4.json", True)
    rows = []
    for obj, ro in ps1["objectives"].items():
        for n in ("frozen", "frozen_3seed", "aln2", "untrained_s3401", "untrained_3draws"):
            for m in ("auc", "hist_gain_bits"):
                w = ro["windows"].get(f"{n}/{m}")
                if w:
                    rows.append([f"{obj} {n}", m, ci(w["early"]["all"], 4), ci(w["late"]["all"], 4)])
    for key in ("md", "sb"):
        for obj, ro in ps1["objectives"].items():
            if key in ro:
                rows.append([f"{obj} {key} (P0)", "NLL increase", ci(ro[key]["early_NLL_increase"]["all"], 4), ci(ro[key]["late_NLL_increase"]["all"], 4)])
    open(os.path.join(pd_, "windows_private.md"), "w").write(table(["曲线", "指标", "早窗", "晚窗"], rows))
    open(os.path.join(pd_, "triad_private.md"), "w").write(triad_tables({"private_bdf": ptri}, "private_bdf"))
    open(os.path.join(pd_, "tg_private.md"), "w").write(tg_tables({"private_bdf": ptg}, "private_bdf"))
    open(os.path.join(pd_, "contrasts_private.md"), "w").write(contrast_tables({"private_bdf": ps4}, "private_bdf"))
    open(os.path.join(pd_, "development_private.md"), "w").write(dev_tables({"private_bdf": ps4}, "private_bdf"))
    for f in os.listdir(pd_):
        os.chmod(os.path.join(pd_, f), 0o600)
    print("tables", len(parts), "+ private 5; figures", figs)


if __name__ == "__main__":
    main()
