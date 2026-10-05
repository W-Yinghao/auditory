"""C3-DL development pilot (docs/auditory_c3/C3DL_PILOT_SPEC.md). Interface, numerical health, checks, timing only;
pilot scores are NOT used to judge methods.

Usage: python -m auditory_c3.c3dl.pilot checks [additive|bilinear]
       python -m auditory_c3.c3dl.pilot pl <seed> <heads,comma-separated> <z27|l27> <ac|mel>
       python -m auditory_c3.c3dl.pilot hc <seed>
       python -m auditory_c3.c3dl.pilot summary
Outputs: private/auditory_c3/c3dl_pilot/{checks*,pl_*,hc_*}.json; results/auditory_c3/C3DL_pilot.json (summary)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch

from . import checks, hc, pl
from .core import Timer, device

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "private", "auditory_c3", "c3dl_pilot")
RES = os.path.join(REPO, "results", "auditory_c3", "C3DL_pilot.json")
ARMS = ["D0", "D1", "D2", "D3", "D4"]


def _gpu():
    return torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"


def _require_checks():
    """Correctness checks (1, 3, 4, 5) block; the synthetic worlds only label capability (spec §8)."""
    p = os.path.join(OUT, "checks.json")
    d = json.load(open(p)) if os.path.exists(p) else {}
    if not all(d.get(k, {}).get("pass") for k in ("1_zero_correction", "3_candidate_permutation", "4_train_mode_restored", "5_channels")):
        raise SystemExit("correctness checks have not passed; pilot not run")


def run_pl(seed, heads, target, bg):
    _require_checks()
    t_all = Timer(); dev = device()
    split = json.load(open(os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud", "th_split.json")))
    devs = sorted(split["selection_half"])
    order = [devs[i] for i in np.random.default_rng(20261005).permutation(len(devs))]
    tr_s, va_s = order[:10], order[10:]
    streams = pl.load_streams(target, bg)
    codes = sorted(streams)
    m0, W, m0_info, norm = pl.fit_m0(streams, [c for c in codes if c[2] in "12"])
    rf = 77
    stim = pl.build_stim(streams, m0, codes, rf)
    subj = {}
    for s in devs:
        eeg, _ = pl.load_eeg("th", s)
        subj[s] = pl.subject_segments(stim, eeg, rf)
    B = pl.Bundle(stim, subj, W, dev)
    P = pl.pools(stim)
    cfg = pl.default_cfg(stim, P, norm, epochs=40); cfg["seed"] = seed
    tag = f"pl_{target}_{bg}_s{seed}"
    out = {"gpu": _gpu(), "seed": seed, "target": target, "background": bg, "heads": heads, "train_subjects": tr_s, "val_subjects": va_s,
           "m0": m0_info, "n_stim_segments": int(len(stim["code"])), "segments_per_subject": {s: int(len(v[0])) for s, v in subj.items()},
           "pool_sizes": {k: int(len(v)) for k, v in P.items()},
           "design": "fit part 1, early stop part 2 (training subjects), primary = held-out dev subjects x unseen content (parts 3-4); seen = stimulus-known",
           "arms": {}, "logs": [], "setup_s": t_all.s()}
    plan = [("-", "B0", False), ("-", "B1", False)] + [(h, a, tw) for h in heads for a, tw in
            (("D0", False), ("D1", False), ("D1", True), ("D2", False), ("D2", True), ("D3", False), ("D4", False), ("D4", True))]
    for h, arm, tw in plan:
        name = (arm if h == "-" else f"{h}/{arm}") + ("_twin" if tw else ""); t = Timer(); extra = {}
        if arm == "B0":
            model = pl.FixedPred(B, "B0")
        elif arm == "B1":
            b1, a = pl.fit_b1(B, tr_s, P["fit"]); model = pl.FixedPred(B, "B1", b1); extra = {"alpha": a}
        else:
            c = dict(cfg, head=h)
            model = pl.train_arm(arm, B, tr_s, P["fit"], P["es"], c, out["logs"], twin=tw); extra = {"best_epoch": model.best_epoch}
            for r in out["logs"]:
                r.setdefault("head", h)
        fit_s = t.s()
        ev = {"unseen_content": pl.evaluate(model, B, va_s, P["unseen"], 8, twin=tw), "seen_sound": pl.evaluate(model, B, va_s, P["seen"], 8, twin=tw)}
        out["arms"][name] = {"fit_seconds": fit_s, "total_seconds": t.s(), **extra, "eval_interface_only": ev}
        print(name, fit_s, extra, {k: {kk: round(vv, 4) for kk, vv in v["mean_over_subjects"].items()} for k, v in ev.items()}, flush=True)
        json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)
    out["total_seconds"] = t_all.s()
    json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)


CONFIGS = {"A": (("1",), ("2",), ("3", "4")), "B": (("1", "2"), ("3",), ("4",))}


def run_pl2(seed, conf):
    """Round 2 (spec §10): 7-fold subject CV over the 14 development TH; strong two-stage background; data configs."""
    _require_checks()
    t_all = Timer(); dev = device()
    split = json.load(open(os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud", "th_split.json")))
    devs = sorted(split["selection_half"])
    order = [devs[i] for i in np.random.default_rng(20261005).permutation(len(devs))]
    fit_p, es_p, te_p = CONFIGS[conf]
    streams = pl.load_streams("z27", "ac")
    codes = sorted(streams)
    m0, W, m0_info, norm = pl.fit_m0(streams, [c for c in codes if c[2] in fit_p + es_p])
    rf = 77
    stim = pl.build_stim(streams, m0, codes, rf)
    subj = {}
    for s in devs:
        eeg, _ = pl.load_eeg("th", s)
        subj[s] = pl.subject_segments(stim, eeg, rf)
    B = pl.Bundle(stim, subj, W, dev)
    P = pl.pools(stim, fit_p, es_p, te_p)
    cfg0 = pl.default_cfg(stim, P, norm, epochs=40); cfg0["seed"] = seed
    min_sep = 40 * pl.FS if len(te_p) == 1 else None
    tag = f"pl2_{conf}_s{seed}"
    out = {"gpu": _gpu(), "seed": seed, "config": conf, "parts": {"fit": fit_p, "es": es_p, "test": te_p}, "m0": m0_info,
           "pool_sizes": {k: int(len(v)) for k, v in P.items()}, "folds": [], "per_subject": {}, "logs": [], "setup_s": t_all.s()}
    for f in range(7):
        te_s = order[2 * f:2 * f + 2]; tr_s = [x for x in order if x not in te_s]
        fold = {"test": te_s, "arms": {}}
        cfg = dict(cfg0)
        for arm, tw in (("B0", False), ("B1", False), ("BG", False), ("D2", False), ("D2", True), ("D2s", False), ("D2s", True), ("D4s", False), ("D4s", True)):
            name = arm + ("_twin" if tw else ""); t = Timer(); extra = {}
            if arm == "B0":
                model = pl.FixedPred(B, "B0")
            elif arm == "B1":
                b1, a = pl.fit_b1(B, tr_s, P["fit"]); model = pl.FixedPred(B, "B1", b1); extra = {"alpha": a}
            else:
                model = pl.train_arm(arm, B, tr_s, P["fit"], P["es"], cfg, out["logs"], twin=tw); extra = {"best_epoch": model.best_epoch}
                if arm == "BG":
                    cfg["bg_model"] = model
            ev = {"unseen_content": pl.evaluate(model, B, te_s, P["unseen"], 8, twin=tw, min_sep=min_sep)}
            fold["arms"][name] = {"seconds": t.s(), **extra, "mean": ev["unseen_content"]["mean_over_subjects"]}
            for sj, v in ev["unseen_content"]["per_subject"].items():
                out["per_subject"].setdefault(sj, {})[name] = v
        out["folds"].append(fold)
        print("fold", f, te_s, {a: round(v["mean"]["e_bits_per_sample"], 4) for a, v in fold["arms"].items()}, flush=True)
        json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)
    out["total_seconds"] = t_all.s()
    json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)


def run_pl3(seed):
    """Round 3 (spec §11): eta x tau selection for D4s on the development TH (config A, 7-fold subject CV)."""
    _require_checks()
    t_all = Timer(); dev = device()
    split = json.load(open(os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud", "th_split.json")))
    devs = sorted(split["selection_half"])
    order = [devs[i] for i in np.random.default_rng(20261005).permutation(len(devs))]
    fit_p, es_p, te_p = CONFIGS["A"]
    streams = pl.load_streams("z27", "ac"); codes = sorted(streams)
    m0, W, m0_info, norm = pl.fit_m0(streams, [c for c in codes if c[2] in fit_p + es_p])
    stim = pl.build_stim(streams, m0, codes, 77)
    subj = {s: pl.subject_segments(stim, pl.load_eeg("th", s)[0], 77) for s in devs}
    B = pl.Bundle(stim, subj, W, dev); P = pl.pools(stim, fit_p, es_p, te_p)
    cfg0 = pl.default_cfg(stim, P, norm, epochs=40); cfg0["seed"] = seed
    grid = [(e, t) for e in (0.02, 0.1, 0.5) for t in (1.0, 10.0)]
    tag = f"pl3_A_s{seed}"
    out = {"gpu": _gpu(), "seed": seed, "grid": grid, "bg_epochs": 100, "folds": [], "per_subject": {}, "logs": [], "setup_s": t_all.s()}
    for f in range(7):
        te_s = order[2 * f:2 * f + 2]; tr_s = [x for x in order if x not in te_s]
        fold = {"test": te_s, "arms": {}}
        cfg = dict(cfg0)
        runs = [("BG", False, None), ("D2s", False, None), ("D2s", True, None)] + [("D4s", tw, g) for g in grid for tw in (False, True)]
        for arm, tw, g in runs:
            name = arm + ("" if g is None else f"_eta{g[0]}_tau{g[1]}") + ("_twin" if tw else ""); t = Timer()
            c = dict(cfg, epochs=100) if arm == "BG" else dict(cfg) if g is None else dict(cfg, eta=g[0], tau=g[1])
            model = pl.train_arm(arm, B, tr_s, P["fit"], P["es"], c, out["logs"], twin=tw)
            if arm == "BG":
                cfg["bg_model"] = model
            ev = pl.evaluate(model, B, te_s, P["unseen"], 8, twin=tw)
            fold["arms"][name] = {"seconds": t.s(), "best_epoch": model.best_epoch, "mean": ev["mean_over_subjects"]}
            for sj, v in ev["per_subject"].items():
                out["per_subject"].setdefault(sj, {})[name] = v
        out["folds"].append(fold)
        print("fold", f, {a: (round(v["mean"]["e_bits_per_sample"], 4), v["best_epoch"]) for a, v in fold["arms"].items()}, flush=True)
        json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)
    out["total_seconds"] = t_all.s()
    json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)


def _es_split(kids, seed, frac=0.15):
    rng = np.random.default_rng(seed); es = set()
    for g in sorted({k["group"] for k in kids}):
        ids = sorted(k["id"] for k in kids if k["group"] == g)
        es |= set(np.array(ids)[rng.permutation(len(ids))[:max(1, int(np.ceil(frac * len(ids))))]].tolist())
    return [k for k in kids if k["id"] not in es], [k for k in kids if k["id"] in es]


def run_hc(seed):
    _require_checks()
    t_all = Timer(); dev = device()
    kids = hc.load_children()
    hc.add_swaps(kids)
    f = hc.folds(kids)
    train = [k for k in kids if f[k["id"]] != 0]
    tr, va = hc.inner_split(train, seed=20261006)
    fit, es = _es_split(tr, seed=20261009)
    q0 = hc.q0_table(tr)
    cfg = {"seed": seed, "lr": 1e-3, "wd": 1e-4, "epochs": 30, "eta": 0.5, "tau": 0.1}
    tag = f"hc_s{seed}"
    out = {"gpu": _gpu(), "seed": seed, "n_children": len(kids), "fold1_train": len(train), "fit": len(fit), "es": len(es), "scored": len(va),
           "scored_groups": {g: sum(k["group"] == g for k in va) for g in ("HA", "NH")}, "q0": q0.tolist(),
           "n_trials_fit": int(sum(len(k["y"]) for k in fit)), "swap_strict_fraction_mean": float(np.mean([k["swap_strict_fraction"] for k in kids])),
           "arms": {}, "logs": [], "setup_s": t_all.s()}
    plan = [("B0", False), ("B1", False), ("D0", False), ("D1", False), ("D1", True), ("D2", False), ("D2", True), ("D3", False), ("D4", False), ("D4", True)]
    for arm, tw in plan:
        name = arm + ("_twin" if tw else ""); t = Timer(); extra = {}
        if arm == "B0":
            ev = hc.evaluate(None, va, q0, dev)
        elif arm == "B1":
            b1 = hc.fit_b1(tr, q0); ev = hc.evaluate(None, va, q0, dev, b1=b1); extra = {"b1": b1}
        else:
            model = hc.train_arm(arm, fit, es, q0, cfg, out["logs"], dev, twin=tw)
            ev = hc.evaluate(model, va, q0, dev, twin=tw); extra = {"best_epoch": model.best_epoch}
        out["arms"][name] = {"total_seconds": t.s(), **extra, "eval_interface_only": ev}
        print(name, t.s(), extra, {k: round(v, 4) for k, v in ev["mean_over_children"].items()}, flush=True)
        json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)
    out["total_seconds"] = t_all.s()
    json.dump(out, open(os.path.join(OUT, tag + ".json"), "w"), indent=1, default=float)


def summary():
    import glob
    res = {"spec": "docs/auditory_c3/C3DL_PILOT_SPEC.md", "note": "pilot scores are interface/information checks on development data only; not claims",
           "checks": {os.path.basename(p)[:-5]: json.load(open(p)) for p in sorted(glob.glob(os.path.join(OUT, "checks*.json")))}}
    for p in sorted(glob.glob(os.path.join(OUT, "pl_*.json")) + glob.glob(os.path.join(OUT, "hc_*.json"))):
        d = json.load(open(p)); logs = d["logs"]; task = os.path.basename(p)[:-5]
        sc = {}
        for a, v in d["arms"].items():
            e = v["eval_interface_only"]
            sc[a] = e["mean_over_children"] | {"by_group": e["by_group"]} if task.startswith("hc") else {k: x["mean_over_subjects"] for k, x in e.items()}
            sc[a] = dict(sc[a], seconds=v["total_seconds"], best_epoch=v.get("best_epoch"))
        res[task] = {"gpu": d["gpu"], "total_seconds": d.get("total_seconds"), "setup_s": d["setup_s"],
                     "max_nonfinite": max((r["nonfinite"] for r in logs), default=0),
                     "all_val_passes_restore_train": all(r["mode_after_val"] == "train" for r in logs), "arms": sc}
    os.makedirs(os.path.dirname(RES), exist_ok=True)
    json.dump(res, open(RES, "w"), indent=1, default=float)
    print("written", RES)


def main():
    os.makedirs(OUT, exist_ok=True)
    a = sys.argv[1:]
    if a[0] == "checks":
        h = a[1] if len(a) > 1 else "additive"
        ok = checks.main(os.path.join(OUT, "checks.json" if h == "additive" else f"checks_{h}.json"), head=h)
        sys.exit(0)
    if a[0] == "pl":
        run_pl(int(a[1]), a[2].split(","), a[3], a[4])
    elif a[0] == "pl3":
        run_pl3(int(a[1]))
    elif a[0] == "pl2":
        run_pl2(int(a[1]), a[2])
    elif a[0] == "hc":
        run_hc(int(a[1]))
    else:
        summary()


if __name__ == "__main__":
    main()
