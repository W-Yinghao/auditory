"""C3-DL v1 full matrix (docs/auditory_c3/C3DL_PROTOCOL_v1_FROZEN.md).

Usage: python -m auditory_c3.c3dl.full pl <outer 0-4> <cf 1|2> <seed>
       python -m auditory_c3.c3dl.full hc <outer 0-4> <seed>
       python -m auditory_c3.c3dl.full aggregate
Outputs: private/auditory_c3/c3dl_full/{pl_o*_cf*_s*, hc_o*_s*}.json (per participant, private);
         results/auditory_c3/C3DL_full.json (aggregate)
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

from . import hc, pl
from .core import Timer, device

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "private", "auditory_c3", "c3dl_full")
RES = os.path.join(REPO, "results", "auditory_c3", "C3DL_full.json")
STAGEB = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/fau_tud_stageB"
CF = {1: (("1",), ("2",), ("3", "4")), 2: (("3",), ("4",), ("1", "2"))}
ETA, TAU = 0.02, 10.0
PL_ARMS = [("D0", False), ("D1", False), ("D1", True), ("D2", False), ("D2", True), ("D2s", False), ("D2s", True),
           ("D3s", False), ("D4s", False), ("D4s", True)]
HC_ARMS = [("D0", False), ("D1", False), ("D1", True), ("D2", False), ("D2", True), ("D3", False), ("D4", False), ("D4", True)]


def _gpu():
    import torch
    return torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"


def panel():
    split = json.load(open(os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud", "th_split.json")))
    ids = {"th": sorted(split["heldout_half"]),
           "ha": sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(STAGEB, "ha", "*.h5"))),
           "ci": sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(STAGEB, "ci", "*.h5")))}
    rng = np.random.default_rng(20261005); fold = {}
    for g in ("th", "ha", "ci"):
        for p_, i in enumerate(rng.permutation(len(ids[g]))):
            fold[ids[g][i]] = (g, p_ % 5)
    return sorted(split["selection_half"]), fold


STAGEC = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/fau_tud_stageC"
STAGEM = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/fau_tud_stageM"
EOG_ARMS = [("D2s", False), ("D2s", True)]
VARIANTS = {"B": ("pl", None, {}), "C": ("pleog", STAGEC, {}), "M": ("plmin", STAGEM, {"dataset": "eeg_min", "robust": True}),
            "clipB": ("plclipB", None, {}), "ciT": ("plciT", None, {})}


def run_pl(outer, cf, seed, eog=False, variant=None):
    variant = variant or ("C" if eog else "B")
    prefix, sdir, lkw = VARIANTS[variant]
    t_all = Timer(); dev = device()
    dev_th, fold = panel()
    train_groups = ("th", "ha", "ci") if variant == "ciT" else ("th", "ha")  # C3_EXTENSIONS_REG_v1 B3: CI in training
    train = [("th", s) for s in dev_th] + [(g, s) for s, (g, f) in fold.items() if f != outer and g in train_groups]
    test = [(g, s) for s, (g, f) in fold.items() if f == outer]
    assert variant == "ciT" or not any(g == "ci" for g, _ in train)
    fit_p, es_p, te_p = CF[cf]
    streams = pl.load_streams("z27", "ac"); codes = sorted(streams)
    m0, W, m0_info, norm = pl.fit_m0(streams, [c for c in codes if c[2] in fit_p + es_p])
    stim = pl.build_stim(streams, m0, codes, 77)
    subj = {s: pl.subject_segments(stim, pl.load_eeg(g, s, sdir, **lkw)[0], 77) for g, s in train + test}
    B = pl.Bundle(stim, subj, W, dev); P = pl.pools(stim, fit_p, es_p, te_p)
    cfg = pl.default_cfg(stim, P, norm, epochs=40); cfg.update(seed=seed, eta=ETA, tau=TAU)
    tr_s = [s for _, s in train]; te_s = [s for _, s in test]
    grp = {s: g for g, s in train + test}
    tag = f"{prefix}_o{outer}_cf{cf}_s{seed}"
    out = {"gpu": _gpu(), "outer": outer, "cf": cf, "seed": seed, "parts": {"fit": fit_p, "es": es_p, "test": te_p},
           "n_train": len(tr_s), "test": {s: grp[s] for s in te_s}, "m0": m0_info, "arms": {}, "per_subject": {}, "logs": []}
    t = Timer()
    bg = pl.train_bg(B, P["fit"], P["es"], cfg); cfg["bg_model"] = bg
    out["bg"] = {"best_epoch": bg.best_epoch, "n_epochs_run": len(bg.es_history), "es_best": float(min(bg.es_history)),
                 "bgL_checksum": float(B.bgL.double().abs().sum()), "seconds": t.s()}
    runs = {"B": [("B0", False), ("B1", False), ("BG", False)] + PL_ARMS, "C": [("B0", False), ("B1", False), ("BG", False)] + EOG_ARMS,
            "M": [("B0", False), ("B1", False), ("BG", False)] + EOG_ARMS + [("CLIP_L", False), ("CLIP_Ac", False)],
            "clipB": [("CLIP_L", False), ("CLIP_Ac", False)],
            "ciT": [("B0", False), ("B1", False), ("BG", False)] + EOG_ARMS}[variant]
    for arm, tw in runs:
        if arm.startswith("CLIP"):
            t = Timer(); tgt = arm.split("_")[1]
            model = pl.train_clip(B, tr_s, P["fit"], P["es"], cfg, tgt, out["logs"])
            ev = pl.evaluate_clip(model, B, te_s, P["unseen"], tgt)
            out["arms"][arm] = {"seconds": t.s(), "best_epoch": model.best_epoch, "mean": ev["mean_over_subjects"]}
            for s_, v in ev["per_subject"].items():
                out["per_subject"].setdefault(s_, {"group": grp[s_]})[arm] = v
            print(arm, t.s(), model.best_epoch, ev["mean_over_subjects"], flush=True)
            continue
        name = arm + ("_twin" if tw else ""); t = Timer(); extra = {}
        if arm == "B0":
            model = pl.FixedPred(B, "B0")
        elif arm == "B1":
            b1, a = pl.fit_b1(B, tr_s, P["fit"]); model = pl.FixedPred(B, "B1", b1); extra = {"alpha": a}
        elif arm == "BG":
            model = bg
        else:
            model = pl.train_arm(arm, B, tr_s, P["fit"], P["es"], cfg, out["logs"], twin=tw); extra = {"best_epoch": model.best_epoch}
        ev = pl.evaluate(model, B, te_s, P["unseen"], 8, twin=tw)
        out["arms"][name] = {"seconds": t.s(), **extra, "mean": ev["mean_over_subjects"]}
        for s, v in ev["per_subject"].items():
            out["per_subject"].setdefault(s, {"group": grp[s]})[name] = v
        print(name, t.s(), extra, round(ev["mean_over_subjects"]["e_bits_per_sample"], 5), flush=True)
    out["total_seconds"] = t_all.s()
    out["max_nonfinite"] = max((r["nonfinite"] for r in out["logs"]), default=0)
    out["restore_ok"] = all(r["mode_after_val"] == "train" for r in out["logs"])
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)


def run_hc(outer, seed):
    t_all = Timer(); dev = device()
    kids = hc.load_children(); hc.add_swaps(kids)
    f = hc.folds(kids)
    train = [k for k in kids if f[k["id"]] != outer]; test = [k for k in kids if f[k["id"]] == outer]
    rng = np.random.default_rng(20261009 + outer); es_ids = set()
    for g in sorted({k["group"] for k in train}):
        ids = sorted(k["id"] for k in train if k["group"] == g)
        es_ids |= set(np.array(ids)[rng.permutation(len(ids))[:max(1, int(np.ceil(0.15 * len(ids))))]].tolist())
    fit = [k for k in train if k["id"] not in es_ids]; es = [k for k in train if k["id"] in es_ids]
    q0 = hc.q0_table(train)
    cfg = {"seed": seed, "lr": 1e-3, "wd": 1e-4, "epochs": 30, "eta": 0.5, "tau": 0.1}
    tag = f"hc_o{outer}_s{seed}"
    out = {"gpu": _gpu(), "outer": outer, "seed": seed, "n_fit": len(fit), "n_es": len(es), "test": {k["id"]: k["group"] for k in test},
           "q0": q0.tolist(), "arms": {}, "per_child": {}, "logs": []}
    runs = [("B0", False), ("B1", False)] + HC_ARMS
    for arm, tw in runs:
        name = arm + ("_twin" if tw else ""); t = Timer(); extra = {}
        if arm == "B0":
            ev = hc.evaluate(None, test, q0, dev)
        elif arm == "B1":
            b1 = hc.fit_b1(train, q0); ev = hc.evaluate(None, test, q0, dev, b1=b1); extra = {"b1": b1}
        else:
            model = hc.train_arm(arm, fit, es, q0, cfg, out["logs"], dev, twin=tw); ev = hc.evaluate(model, test, q0, dev, twin=tw)
            extra = {"best_epoch": model.best_epoch}
        out["arms"][name] = {"seconds": t.s(), **extra, "mean": ev["mean_over_children"]}
        for cid, v in ev["per_child"].items():
            out["per_child"].setdefault(cid, {})[name] = v
        print(name, t.s(), extra, round(ev["mean_over_children"]["G_bits_per_trial"], 5), flush=True)
    out["total_seconds"] = t_all.s()
    out["max_nonfinite"] = max((r["nonfinite"] for r in out["logs"]), default=0)
    out["restore_ok"] = all(r["mode_after_val"] == "train" for r in out["logs"])
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)


# ------------------------------------------------------------------------------------------------ aggregate
def _boot(x, seed=0, n=10000):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"est": None, "n": 0}
    r = np.random.default_rng(seed); b = np.array([x[r.integers(0, len(x), len(x))].mean() for _ in range(n)])
    lo, hi = np.percentile(b, [2.5, 97.5])
    return {"est": float(x.mean()), "ci_low": float(lo), "ci_high": float(hi), "n": int(len(x))}


def _diff(a, b, seed=0, n=10000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    r = np.random.default_rng(seed)
    bs = np.array([a[r.integers(0, len(a), len(a))].mean() - b[r.integers(0, len(b), len(b))].mean() for _ in range(n)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"est": float(a.mean() - b.mean()), "ci_low": float(lo), "ci_high": float(hi)}


def aggregate_eog():
    """EOG sensitivity (POST_G1_CHANGELOG ~15:30): G_EEG on stage C vs stage B, paired per participant."""
    def means(prefix):
        per, grp = {}, {}
        for p in sorted(glob.glob(os.path.join(OUT, f"{prefix}_o*_cf*_s*.json"))):
            d = json.load(open(p))
            for s_, v in d["per_subject"].items():
                grp[s_] = v["group"]
                for arm in ("B1", "BG", "D2s", "D2s_twin"):
                    for k in ("e_bits_per_sample", "e_mismatch"):
                        per.setdefault(s_, {}).setdefault(arm, {}).setdefault(k, []).append(v[arm][k])
        return {s_: {a: {k: float(np.mean(x)) for k, x in ks.items()} for a, ks in arms.items()} for s_, arms in per.items()}, grp, len(glob.glob(os.path.join(OUT, f"{prefix}_o*.json")))
    C, grp, nC = means("pleog"); B, _, nB = means("pl")
    res = {"n_units_stageC": nC, "n_units_stageB": nB}
    for g in ("th", "ha", "ci"):
        ss = sorted(s_ for s_ in C if grp[s_] == g and s_ in B)
        gC = [C[s_]["D2s"]["e_bits_per_sample"] - C[s_]["D2s_twin"]["e_bits_per_sample"] for s_ in ss]
        gB = [B[s_]["D2s"]["e_bits_per_sample"] - B[s_]["D2s_twin"]["e_bits_per_sample"] for s_ in ss]
        res[g] = {"n": len(ss), "G_EEG_stageC": _boot(gC), "G_EEG_stageB": _boot(gB), "C_minus_B_paired": _boot(np.array(gC) - np.array(gB)),
                  "B1_e_minus_mismatch_stageC": _boot([C[s_]["B1"]["e_bits_per_sample"] - C[s_]["B1"]["e_mismatch"] for s_ in ss]),
                  "B1_e_minus_mismatch_stageB": _boot([B[s_]["B1"]["e_bits_per_sample"] - B[s_]["B1"]["e_mismatch"] for s_ in ss])}
    fn = os.path.join(REPO, "results", "auditory_c3", "C3DL_full_eog.json")
    json.dump(res, open(fn, "w"), indent=1, default=float); print("written", fn)


def _variant_means(prefix):
    per, grp, n = {}, {}, 0
    for p in sorted(glob.glob(os.path.join(OUT, f"{prefix}_o*_cf*_s*.json"))):
        d = json.load(open(p)); n += 1
        for s_, v in d["per_subject"].items():
            grp[s_] = v["group"]
            for arm, m in v.items():
                if arm == "group":
                    continue
                for k, x in m.items():
                    if isinstance(x, (int, float)):
                        per.setdefault(s_, {}).setdefault(arm, {}).setdefault(k, []).append(x)
    return {s_: {a: {k: float(np.mean(x)) for k, x in ks.items()} for a, ks in arms.items()} for s_, arms in per.items()}, grp, n


def aggregate_variants():
    """Stage M / CLIP (FROZEN §7) and CI-in-training (C3_EXTENSIONS_REG_v1 B3)."""
    res = {}
    Bm, grp, nB = _variant_means("pl"); Mm, _, nM = _variant_means("plmin"); Cm, _, nC = _variant_means("plclipB"); Tm, _, nT = _variant_means("plciT")
    res["n_units"] = {"pl": nB, "plmin": nM, "plclipB": nC, "plciT": nT}
    geeg = lambda M, s_: M[s_]["D2s"]["e_bits_per_sample"] - M[s_]["D2s_twin"]["e_bits_per_sample"]
    for g in ("th", "ha", "ci"):
        cell = {}
        ss = sorted(s_ for s_ in grp if grp[s_] == g)
        for name, M in (("stageM", Mm), ("ciTrain", Tm)):
            sm = [s_ for s_ in ss if s_ in M and s_ in Bm]
            if sm:
                cell[f"G_EEG_{name}"] = _boot([geeg(M, s_) for s_ in sm])
                cell[f"G_EEG_{name}_minus_stageB"] = _boot([geeg(M, s_) - geeg(Bm, s_) for s_ in sm])
                cell[f"B1_e_minus_mismatch_{name}"] = _boot([M[s_]["B1"]["e_bits_per_sample"] - M[s_]["B1"]["e_mismatch"] for s_ in sm])
        for name, M in (("stageM", Mm), ("stageB", Cm)):
            for arm in ("CLIP_L", "CLIP_Ac"):
                sm = [s_ for s_ in ss if s_ in M and arm in M[s_]]
                if sm:
                    for k in ("top1", "top5", "rank_pct", "cond_top1"):
                        vals = [M[s_][arm][k] for s_ in sm if k in M[s_][arm]]
                        if vals:
                            cell[f"{arm}_{name}_{k}"] = _boot(vals)
                    cell[f"{arm}_{name}_chance_top1"] = float(np.mean([1 / M[s_][arm].get("n_candidates", 100) for s_ in sm])) if "n_candidates" in M[sm[0]][arm] else None
        sm = [s_ for s_ in ss if s_ in Mm and s_ in Cm and "CLIP_L" in Mm[s_] and "CLIP_L" in Cm[s_]]
        if sm:
            cell["CLIP_L_top1_stageM_minus_stageB"] = _boot([Mm[s_]["CLIP_L"]["top1"] - Cm[s_]["CLIP_L"]["top1"] for s_ in sm])
            cell["CLIP_L_minus_CLIP_Ac_top1_stageB"] = _boot([Cm[s_]["CLIP_L"]["top1"] - Cm[s_]["CLIP_Ac"]["top1"] for s_ in sm])
        res[g] = cell
    for name, M in (("ciTrain", Tm),):
        th = [geeg(M, s_) for s_ in M if grp.get(s_) == "th"]; ci = [geeg(M, s_) for s_ in M if grp.get(s_) == "ci"]; ha = [geeg(M, s_) for s_ in M if grp.get(s_) == "ha"]
        if th and ci:
            res[f"{name}_ci-th_G_EEG"] = _diff(ci, th, seed=2)
        if th and ha:
            res[f"{name}_ha-th_G_EEG"] = _diff(ha, th, seed=3)
    fn = os.path.join(REPO, "results", "auditory_c3", "C3DL_variants.json")
    json.dump(res, open(fn, "w"), indent=1, default=float); print("written", fn)


def aggregate():
    res = {"spec": "docs/auditory_c3/C3DL_PROTOCOL_v1_FROZEN.md"}
    # ---- P-L: per participant, mean over seeds and content folds
    files = sorted(glob.glob(os.path.join(OUT, "pl_o*_cf*_s*.json")))  # stage B only (pleog_* excluded by the prefix)
    res["pl_units"] = {"n": len(files), "expected": 30}
    per, grp, meta = {}, {}, []
    for p in files:
        d = json.load(open(p)); meta.append({k: d[k] for k in ("outer", "cf", "seed", "total_seconds", "max_nonfinite", "restore_ok", "gpu")} | {"bg": d["bg"]})
        for s, v in d["per_subject"].items():
            grp[s] = v["group"]
            for arm, m in v.items():
                if arm == "group":
                    continue
                for k, x in m.items():
                    if isinstance(x, (int, float)):
                        per.setdefault(s, {}).setdefault(arm, {}).setdefault(k, []).append(x)
    M = {s: {a: {k: float(np.mean(x)) for k, x in ks.items()} for a, ks in arms.items()} for s, arms in per.items()}
    res["pl_units_meta"] = meta
    contrasts = {"G_EEG = D2s - D2s_twin": ("D2s", "D2s_twin"), "D4s - D4s_twin": ("D4s", "D4s_twin"), "D2 - D2_twin": ("D2", "D2_twin"),
                 "D1 - D1_twin": ("D1", "D1_twin"), "D4s - D1": ("D4s", "D1"), "D4s - D3s": ("D4s", "D3s"), "D4s - D2s": ("D4s", "D2s"),
                 "D2s - BG": ("D2s", "BG"), "BG - B0 (background capacity)": ("BG", "B0")}
    out_pl = {}
    for g in ("th", "ha", "ci"):
        ss = sorted(s for s in M if grp[s] == g)
        cell = {"n": len(ss)}
        for nm, (a, b) in contrasts.items():
            cell[nm] = _boot([M[s][a]["e_bits_per_sample"] - M[s][b]["e_bits_per_sample"] for s in ss])
        cell["B1: e - e_mismatch"] = _boot([M[s]["B1"]["e_bits_per_sample"] - M[s]["B1"]["e_mismatch"] for s in ss])
        cell["D2s: e - e_mismatch"] = _boot([M[s]["D2s"]["e_bits_per_sample"] - M[s]["D2s"]["e_mismatch"] for s in ss])
        cell["arms_e"] = {a: _boot([M[s][a]["e_bits_per_sample"] for s in ss]) for a in M[ss[0]]} if ss else {}
        cell["retrieval_condbg_top1"] = {a: _boot([M[s][a].get("retrieval_condbg_top1", np.nan) for s in ss]) for a in M[ss[0]]} if ss else {}
        out_pl[g] = cell
    g_eeg = lambda s: M[s]["D2s"]["e_bits_per_sample"] - M[s]["D2s_twin"]["e_bits_per_sample"]
    th = [g_eeg(s) for s in M if grp[s] == "th"]; ha = [g_eeg(s) for s in M if grp[s] == "ha"]
    out_pl["ha-th G_EEG"] = _diff(ha, th, seed=1) if th and ha else None
    res["pl"] = out_pl
    res["pl_per_subject_G_EEG"] = {s: {"group": grp[s], "G_EEG": g_eeg(s)} for s in M}
    # ---- H-Cur: per child, mean over seeds
    files = sorted(glob.glob(os.path.join(OUT, "hc_o*_s*.json")))
    res["hc_units"] = {"n": len(files), "expected": 15}
    per = {}
    for p in files:
        d = json.load(open(p))
        for cid, arms in d["per_child"].items():
            for arm, m in arms.items():
                for k, x in m.items():
                    if isinstance(x, (int, float)) and k not in ("n",):
                        per.setdefault(cid, {}).setdefault(arm, {}).setdefault(k, []).append(x)
                per[cid]["_group"] = m["group"]
    H = {c: {a: {k: float(np.mean(x)) for k, x in ks.items()} for a, ks in arms.items() if a != "_group"} for c, arms in per.items()}
    hg = {c: per[c]["_group"] for c in per}
    out_hc = {}
    for g in ("HA", "NH", "all"):
        cs = sorted(c for c in H if g == "all" or hg[c] == g)
        cell = {"n": len(cs)}
        for a in H[cs[0]]:
            cell[a] = {k: _boot([H[c][a].get(k, np.nan) for c in cs]) for k in ("G_bits_per_trial", "G_common_support", "auc", "auc_common_support", "brier")}
        for nm, (a, b) in {"D2 - D2_twin": ("D2", "D2_twin"), "D4 - D4_twin": ("D4", "D4_twin"), "D1 - D1_twin": ("D1", "D1_twin"),
                           "D4 - D1": ("D4", "D1"), "D4 - D3": ("D4", "D3"), "D2 - B1": ("D2", "B1"), "D4 - B1": ("D4", "B1")}.items():
            cell[nm] = _boot([H[c][a]["G_bits_per_trial"] - H[c][b]["G_bits_per_trial"] for c in cs])
            cell[nm + " (common support)"] = _boot([H[c][a]["G_common_support"] - H[c][b]["G_common_support"] for c in cs])
        cell["q0_violations_per_child"] = _boot([H[cs_]["B0"]["n_q0_violations"] for cs_ in cs])
        out_hc[g] = cell
    res["hc"] = out_hc
    os.makedirs(os.path.dirname(RES), exist_ok=True)
    json.dump(res, open(RES, "w"), indent=1, default=float)
    json.dump({"pl_per_subject": M, "pl_group": grp, "hc_per_child": H, "hc_group": hg}, open(os.path.join(OUT, "per_participant_means.json"), "w"), default=float)
    print("written", RES)


def main():
    a = sys.argv[1:]
    if a[0] == "pl":
        run_pl(int(a[1]), int(a[2]), int(a[3]))
    elif a[0] == "pl_eog":
        run_pl(int(a[1]), int(a[2]), int(a[3]), eog=True)
    elif a[0] == "pl_var":  # pl_var <outer> <cf> <seed> <M|clipB>
        run_pl(int(a[1]), int(a[2]), int(a[3]), variant=a[4])
    elif a[0] == "aggregate_eog":
        aggregate_eog()
    elif a[0] == "aggregate_variants":
        aggregate_variants()
    elif a[0] == "hc":
        run_hc(int(a[1]), int(a[2]))
    else:
        aggregate()


if __name__ == "__main__":
    main()
