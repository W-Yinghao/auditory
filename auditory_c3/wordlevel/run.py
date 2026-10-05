"""Word-level conditional decoding runner (docs/auditory_c3/WORDLEVEL_REG_v1.md).

Usage: python -m auditory_c3.wordlevel.run checks                 # synthetic implementation checks (GPU or CPU)
       python -m auditory_c3.wordlevel.run select                 # GPT-2 layer selection on the 14 development TH
       python -m auditory_c3.wordlevel.run probe <dev TH id>      # one development participant held out, CF1, seed 1
       python -m auditory_c3.wordlevel.run unit <outer> <cf> <seed>
       python -m auditory_c3.wordlevel.run aggregate
Outputs: private/auditory_c3/wordlevel/{checks,layer_selection,probe_*,unit_*}.json; results/auditory_c3/WORDLEVEL_full.json
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import torch

from ..c3dl.core import Timer, device
from . import models as M
from . import table as T

REPO = T.REPO
OUT = os.path.join(REPO, "private", "auditory_c3", "wordlevel")
SEL = os.path.join(OUT, "layer_selection.json")
CF = {1: (("1",), ("2",), ("3", "4")), 2: (("3",), ("4",), ("1", "2"))}
CFG = {"lr": 1e-3, "wd": 1e-4, "bs": 256, "epochs": 30, "patience": 6, "K": 8, "eta": 0.02, "tau": 10.0}


def _gpu():
    return torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"


def epochs_for(tab, grp, subj, stage_dir=None):
    from ..c3dl import pl
    eeg, _ = pl.load_eeg(grp, subj, stage_dir)
    rows, X = [], []
    for i in range(len(tab["code"])):
        x = eeg.get(str(tab["code"][i])); o = int(tab["onset"][i])
        if x is None or o - T.PRE < 0 or o + T.POST > x.shape[1]:
            continue
        rows.append(i); X.append(x[:, o - T.PRE:o + T.POST])
    return np.array(rows), np.stack(X).astype(np.float16)


def _standardise(C, fit):
    mu, sd = C[fit].mean(0), C[fit].std(0); sd[sd == 0] = 1
    return ((C - mu) / sd).astype(np.float32)


def run_split(tab, train_subj, test_subj, eeg, parts, seed, log, arms=("D2s", "D4s"), with_twins=True):
    """One (content split, seed): both targets; returns {target: {arm: per-participant metrics}} plus run info."""
    dev = device()
    P = M.pools(tab, *parts)
    Cz = _standardise(tab["C"], P["fit"])
    mf = M.matched(tab, Cz, P["fit"], CFG["K"]); me = M.matched(tab, Cz, P["es"], CFG["K"]); mt = M.matched(tab, Cz, P["test"], CFG["K"])
    cfg = dict(CFG, seed=seed, matched_fit=mf, matched_es=me)
    res, info, shared = {}, {}, None
    for tgt in ("L", "S"):
        Y = tab["YL"] if tgt == "L" else tab["YS"]
        y0, W, a0 = M.fit_b0(tab, Y.astype(np.float64), Cz, P["fit"], P["es"])
        B = M.Bundle(tab, Y, Cz, y0, W, {} if shared else eeg, dev)
        if shared:
            B.subj, B.loc = shared
        else:
            shared = (B.subj, B.loc)
        t = Timer(); bg = M.train_bg(B, P["fit"], P["es"], seed)
        info[tgt] = {"b0_alpha": a0, "bg_best_epoch": bg.best_epoch, "bg_epochs_run": bg.n_epochs, "bg_seconds": t.s(), "arm_seconds": {}}
        out = {"B0": M.evaluate(B, test_subj, P["test"], mt, "B0"), "BG": M.evaluate(B, test_subj, P["test"], mt, "BG")}
        t = Timer(); b1, a1 = M.fit_b1(B, train_subj, P["fit"]); out["B1"] = M.evaluate(B, test_subj, P["test"], mt, "B1", b1=b1)
        info[tgt]["b1_alpha"] = a1; info[tgt]["arm_seconds"]["B1"] = t.s()
        for arm in arms:
            for tw in ((False, True) if with_twins else (False,)):
                t = Timer(); net = M.train_arm(arm, B, train_subj, P["fit"], P["es"], cfg, log, twin=tw)
                for r in log:
                    r.setdefault("target", tgt)
                name = arm + ("_twin" if tw else "")
                out[name] = M.evaluate(B, test_subj, P["test"], mt, "net", model=net, twin=tw)
                info[tgt]["arm_seconds"][name] = t.s(); info[tgt].setdefault("best_epoch", {})[name] = net.best_epoch
                print(tgt, name, t.s(), net.best_epoch, round(float(np.mean([v["e_bits_per_word"] for v in out[name].values()])), 5), flush=True)
        res[tgt] = out
        del B
    return res, info


def cmd_unit(outer, cf, seed, tag=None, train=None, test=None):
    from ..c3dl.full import panel
    t_all = Timer()
    layer = json.load(open(SEL))["chosen_layer"]
    tab = T.build(layer)
    dev_th, fold = panel()
    if train is None:
        train = [("th", s) for s in dev_th] + [(g, s) for s, (g, f) in fold.items() if f != outer and g in ("th", "ha")]
        test = [(g, s) for s, (g, f) in fold.items() if f == outer]
    assert not any(g == "ci" for g, _ in train)
    grp = {s: g for g, s in train + test}
    eeg = {s: epochs_for(tab, g, s) for g, s in train + test}
    log = []
    res, info = run_split(tab, [s for _, s in train], [s for _, s in test], eeg, CF[cf], seed, log)
    out = {"gpu": _gpu(), "outer": outer, "cf": cf, "seed": seed, "layer": layer, "table": tab["meta"], "groups": grp,
           "n_train": len(train), "n_words_per_subject": {s: int(len(v[0])) for s, v in eeg.items()}, "info": info, "results": res,
           "logs": log, "total_seconds": t_all.s(), "max_nonfinite": max((r["nonfinite"] for r in log), default=0),
           "restore_ok": all(r["mode_after_val"] == "train" for r in log)}
    tag = tag or f"unit_o{outer}_cf{cf}_s{seed}"
    path = os.path.join(OUT, tag + ".json")
    json.dump(out, open(path + ".tmp", "w"), default=float); os.replace(path + ".tmp", path); os.chmod(path, 0o600)
    print("written", path, "seconds", out["total_seconds"])


def cmd_probe(subj):
    split = json.load(open(os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud", "th_split.json")))
    dev_th = sorted(split["selection_half"]); assert subj in dev_th
    cmd_unit(-1, 1, 1, tag=f"probe_{subj}", train=[("th", s) for s in dev_th if s != subj], test=[("th", subj)])


# ------------------------------------------------------------------------------------------------ layer selection
def cmd_select():
    """Dev TH only: for each GPT-2 layer, linear B1 evidence minus its mismatch (EEG of the background-matched word),
    two content folds x leave-one-participant-out; chosen = argmax. No held-out participant is touched."""
    import h5py
    split = json.load(open(os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud", "th_split.json")))
    dev_th = sorted(split["selection_half"])
    tab = T.build(0)
    eeg = {s: epochs_for(tab, "th", s) for s in dev_th}
    with h5py.File(T.STATES, "r") as f:
        keys = [f"{c}/attended" for c in tab["code"]]
        layers = sorted(k for k in f[keys[0]].keys() if k.startswith("layer_"))
        scores = {}
        for lay in layers:
            H = np.stack([f[k][lay][int(i)] for k, i in zip(keys, tab["i"])]).astype(np.float64)
            H -= H.mean(0); _, S, Vt = np.linalg.svd(H, full_matrices=False); Y = H @ Vt[:T.K_L].T
            per = []
            for fit_p, te_p in ((("1", "2"), ("3", "4")), (("3", "4"), ("1", "2"))):
                fit = np.flatnonzero(np.isin(tab["part"], fit_p)); te = np.flatnonzero(np.isin(tab["part"], te_p))
                Cz = _standardise(tab["C"], fit)
                X0 = np.c_[np.ones(len(Cz)), Cz]
                B0 = np.linalg.solve(X0[fit].T @ X0[fit] + 10 * np.eye(X0.shape[1]), X0[fit].T @ Y[fit]); y0 = X0 @ B0
                R = Y[fit] - y0[fit]; w, V = np.linalg.eigh(np.cov(R.T)); Wm = V @ np.diag(w ** -0.5) @ V.T
                mt = M.matched(tab, Cz, te, 1)
                acc = {}
                for s in dev_th:
                    rows, X = eeg[s]; loc = {int(i): k for k, i in enumerate(rows)}
                    fr = [loc[i] for i in fit if i in loc]; gi = [int(rows[k]) for k in fr]
                    Fx = np.c_[np.ones(len(fr)), M._feats(torch.tensor(X[fr]).float()).numpy()]
                    Rw = (Y[gi] - y0[gi]) @ Wm.T
                    acc[s] = (Fx.T @ Fx, Fx.T @ Rw)
                tot = [sum(a[k] for a in acc.values()) for k in range(2)]
                I = np.eye(tot[0].shape[0]); I[0, 0] = 0
                for s in dev_th:
                    Bs = np.linalg.solve(tot[0] - acc[s][0] + 1e3 * I, tot[1] - acc[s][1])
                    rows, X = eeg[s]; loc = {int(i): k for k, i in enumerate(rows)}
                    ti = [i for i in te if i in loc and mt[int(i)][0] in loc]
                    Ft = np.c_[np.ones(len(ti)), M._feats(torch.tensor(X[[loc[i] for i in ti]]).float()).numpy()]
                    Fm = np.c_[np.ones(len(ti)), M._feats(torch.tensor(X[[loc[mt[int(i)][0]] for i in ti]]).float()).numpy()]
                    r0 = (Y[ti] - y0[ti]) @ Wm.T
                    e = ((r0 ** 2).sum(1) - ((r0 - Ft @ Bs) ** 2).sum(1)) / (2 * np.log(2))
                    em = ((r0 ** 2).sum(1) - ((r0 - Fm @ Bs) ** 2).sum(1)) / (2 * np.log(2))
                    per.append(float((e - em).mean()))
            scores[lay] = {"mean_e_minus_mismatch": float(np.mean(per)), "per_subject_fold": per}
            print(lay, scores[lay]["mean_e_minus_mismatch"], flush=True)
    chosen = max(scores, key=lambda k: scores[k]["mean_e_minus_mismatch"])
    out = {"rule": "argmax over layers of dev-TH linear (B1, alpha=1e3) e - e_mismatch, 2 content folds x LOSO; B0 ridge alpha=10",
           "scores": {k: v["mean_e_minus_mismatch"] for k, v in scores.items()}, "chosen_layer": int(chosen.split("_")[1]),
           "detail": scores}
    json.dump(out, open(SEL, "w"), indent=1); os.chmod(SEL, 0o600)
    print("chosen", chosen)


# ------------------------------------------------------------------------------------------------ synthetic checks
def cmd_checks():
    """Zero correction (q1 == BG exactly); null world (EEG independent of the target residual) -> G_EEG ~ 0;
    increment world (EEG carries the residual) -> G_EEG > 0.05 bits/word."""
    dev = device(); rng = np.random.default_rng(0)
    res = {}
    net = M.WordNet(31, 10, 4).to(dev)
    for p in net.parameters():
        torch.nn.init.normal_(p)
    torch.nn.init.zeros_(net.l2.weight); torch.nn.init.zeros_(net.l2.bias)
    base = torch.randn(5, 4, device=dev)
    with torch.no_grad():
        d0 = float((net(torch.randn(5, 31, 128, device=dev), torch.randn(5, 10, device=dev), base) - base).abs().max())
    res["zero_correction_max_abs"] = d0
    N, p, d = 2400, 10, 4
    for world in ("null", "increment"):
        C = rng.standard_normal((N, p)).astype(np.float32)
        Yb = np.tanh(C[:, :d]) + 0.5 * C[:, d:2 * d] * C[:, :d]
        Rr = rng.standard_normal((N, d))
        Y = (Yb + Rr).astype(np.float32)
        tab = {"C": C, "code": np.array(["1" + str(1 + (k % 2)) + str(1 + (k // 600)) for k in range(N)]), "t0": np.tile(np.arange(600) * 1.0, 4)}
        tab["part"] = np.array([c[2] for c in tab["code"]]); tab["story"] = np.array([c[1] for c in tab["code"]])
        G = rng.standard_normal((d, 31, 20)) * 0.6
        eeg = {}
        for s in range(10):
            X = rng.standard_normal((N, 31, 128)).astype(np.float32)
            if world == "increment":
                X[:, :, 40:60] += np.einsum("nd,dct->nct", Rr, G)
            eeg[f"s{s}"] = (np.arange(N), X.astype(np.float16))
        P = M.pools(tab, ("1",), ("2",), ("3", "4"))
        Cz = _standardise(C, P["fit"])
        y0, W, _ = M.fit_b0(tab, Y.astype(np.float64), Cz, P["fit"], P["es"])
        B = M.Bundle(tab, Y, Cz, y0, W, eeg, dev)
        M.train_bg(B, P["fit"], P["es"], 1, max_epochs=500, patience=30)
        mf = M.matched(tab, Cz, P["fit"], 8); me = M.matched(tab, Cz, P["es"], 8); mt = M.matched(tab, Cz, P["test"], 8)
        cfg = dict(CFG, seed=1, matched_fit=mf, matched_es=me, epochs=15)
        log = []
        tr = [f"s{s}" for s in range(7)]; te = [f"s{s}" for s in range(7, 10)]
        r = {}
        for tw in (False, True):
            net = M.train_arm("D2s", B, tr, P["fit"], P["es"], cfg, log, twin=tw)
            r["D2s" + ("_twin" if tw else "")] = float(np.mean([v["e_bits_per_word"] for v in M.evaluate(B, te, P["test"], mt, "net", model=net, twin=tw).values()]))
        r["BG"] = float(np.mean([v["e_bits_per_word"] for v in M.evaluate(B, te, P["test"], mt, "BG").values()]))
        r["G_EEG"] = r["D2s"] - r["D2s_twin"]
        r["nonfinite"] = max(x["nonfinite"] for x in log); r["restore_ok"] = all(x["mode_after_val"] == "train" for x in log)
        res[world] = r
        print(world, r, flush=True)
    res["pass"] = bool(res["zero_correction_max_abs"] == 0.0 and abs(res["null"]["G_EEG"]) <= 0.05 and res["increment"]["G_EEG"] > 0.05
                       and res["null"]["nonfinite"] == 0 and res["increment"]["nonfinite"] == 0)
    path = os.path.join(OUT, "checks.json"); json.dump(res, open(path, "w"), indent=1); os.chmod(path, 0o600)
    print("checks", res["pass"])


# ------------------------------------------------------------------------------------------------ aggregate
def _boot(x, seed=0, n=10000):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if not len(x):
        return {"est": None, "n": 0}
    r = np.random.default_rng(seed); b = np.array([x[r.integers(0, len(x), len(x))].mean() for _ in range(n)])
    lo, hi = np.percentile(b, [2.5, 97.5])
    return {"est": float(x.mean()), "ci_low": float(lo), "ci_high": float(hi), "n": int(len(x))}


def cmd_aggregate():
    files = sorted(glob.glob(os.path.join(OUT, "unit_o*_cf*_s*.json")))
    per, grp = {}, {}
    for p in files:
        d = json.load(open(p)); grp.update(d["groups"])
        for tgt, arms in d["results"].items():
            for arm, subs in arms.items():
                for s, m in subs.items():
                    for k, v in m.items():
                        if isinstance(v, (int, float)):
                            per.setdefault(tgt, {}).setdefault(s, {}).setdefault(arm, {}).setdefault(k, []).append(v)
    out = {"n_units": len(files), "expected": 30}
    for tgt, S in per.items():
        Mn = {s: {a: {k: float(np.mean(v)) for k, v in ks.items()} for a, ks in arms.items()} for s, arms in S.items()}
        cells = {}
        for g in ("th", "ha", "ci"):
            ss = [s for s in Mn if grp.get(s) == g]
            e = lambda s, a: Mn[s][a]["e_bits_per_word"]
            cells[g] = {"n": len(ss),
                        "G_EEG = D2s - D2s_twin": _boot([e(s, "D2s") - e(s, "D2s_twin") for s in ss]),
                        "D4s - D4s_twin": _boot([e(s, "D4s") - e(s, "D4s_twin") for s in ss]),
                        "D4s - D2s": _boot([e(s, "D4s") - e(s, "D2s") for s in ss]),
                        "BG - B0": _boot([e(s, "BG") for s in ss]),
                        "D2s - BG": _boot([e(s, "D2s") - e(s, "BG") for s in ss]),
                        "B1: e - e_mismatch": _boot([Mn[s]["B1"]["e_bits_per_word"] - Mn[s]["B1"]["e_mismatch"] for s in ss]),
                        "cond_top1 D2s / twin": [_boot([Mn[s]["D2s"]["cond_top1"] for s in ss]), _boot([Mn[s]["D2s_twin"]["cond_top1"] for s in ss])]}
        out[tgt] = cells
    path = os.path.join(REPO, "results", "auditory_c3", "WORDLEVEL_full.json")
    json.dump(out, open(path, "w"), indent=1, default=float); print("written", path)


def main():
    a = sys.argv[1:]
    {"checks": lambda: cmd_checks(), "select": lambda: cmd_select(), "probe": lambda: cmd_probe(a[1]),
     "unit": lambda: cmd_unit(int(a[1]), int(a[2]), int(a[3])), "aggregate": lambda: cmd_aggregate()}[a[0]]()


if __name__ == "__main__":
    main()
