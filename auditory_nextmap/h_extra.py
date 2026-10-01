"""H8 and H9 (post-hoc, exploratory; NEXTMAP_H_PROTOCOL_ADDENDUM_002.md).

H8: spectral-plus features on the D2 continuous MFF cohort with D2's exact readout (saved folds, inner identity folds,
penalty / gamma grids, inner-MSE selection), against the saved D2 full-array predictions; the D2 feature refit must
reproduce those predictions. H9: split-half reliability and RMS of the draw0 common evoked average in both systems.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from auditory_d2 import spectral as d2s
from auditory_d2.budget import identity_folds
from auditory_d2.data import RecordStore, record_scale
from auditory_d2.ridge_budget import GAMMAS, PENALTIES, _kernel_ridge, _ridge

from . import age_core
from .adapters import AgeSource
from .h_prep import mapped_channels, specplus_from_psd, store_windows, welch_mean
from .runtime import ROOT, ProvenanceError, cfg, close_run, open_run, require_protocol, save_npz_atomic, write_json_atomic

D2_SEEDS = (11, 22, 33, 44)


def d2_readout(design: np.ndarray, ages: np.ndarray, identities: np.ndarray, folds: list, seed: int, nonlinear: bool):
    """auditory_d2.ridge_budget's nested selection, verbatim in structure."""
    predicted = np.full(ages.shape, np.nan)
    n_fits = 0
    everyone = np.arange(len(ages))
    raw_design = design
    for fold in folds:
        test_idx = np.asarray(fold["test"], int)
        train_idx = np.asarray(fold["train"], int) if "train" in fold else np.setdiff1d(everyone, test_idx)  # D2 saved test only
        design = raw_design
        if not np.isfinite(design).all():                     # fold-wise training-median imputation (addendum 002 view)
            med = np.nanmedian(design[train_idx], axis=0)
            med = np.where(np.isfinite(med), med, 0.0)
            design = np.where(np.isfinite(raw_design), raw_design, med[None, :])
        inner = identity_folds(identities[train_idx], min(3, max(2, len(train_idx) // 8)), seed + 7)
        settings = [(p, g) for p in PENALTIES for g in GAMMAS] if nonlinear else [(p, None) for p in PENALTIES]
        errors = {key: [] for key in settings}
        for part in inner:
            a, b = train_idx[part["train"]], train_idx[part["test"]]
            if b.size == 0:
                continue
            for key in settings:
                penalty, gamma = key
                fit = (_kernel_ridge(design[a], ages[a], design[b], penalty, gamma) if nonlinear
                       else _ridge(design[a], ages[a], design[b], penalty))
                errors[key].append(fit - ages[b])
                n_fits += 1
        scored = {k: float(np.mean(np.concatenate(v) ** 2)) for k, v in errors.items() if v}
        penalty, gamma = min(scored, key=scored.get)
        predicted[test_idx] = (_kernel_ridge(design[train_idx], ages[train_idx], design[test_idx], penalty, gamma)
                               if nonlinear else _ridge(design[train_idx], ages[train_idx], design[test_idx], penalty))
        n_fits += 1
    return predicted, n_fits


def cmd_h8_d2plus(args, config) -> dict:
    require_protocol(config)
    run = open_run("h8_d2plus", args.run, config, args=vars(args))
    d2 = ROOT / "private/auditory_d2"
    cohort = json.loads((d2 / "D1_mff_001_cohort.json").read_text())
    layouts = json.loads((d2 / "D1_mff_001_geometry.json").read_text())
    counts = {}
    for u in cohort["units"]:
        counts[str(u["layout_hash"])] = counts.get(str(u["layout_hash"]), 0) + 1
    lh = max(counts, key=counts.get)
    keep = np.array([i for i, p in enumerate(layouts[lh]["xyz_m"]) if p is not None], int)
    names, diag = mapped_channels(config)
    h4 = config["h4"]
    feat_path = run["private"] / "features.npz"
    reuse = getattr(args, "reuse_features", "")
    if not feat_path.exists() and reuse:                       # read-only reuse of an earlier run's identical features
        with np.load(ROOT / cfg(config, "paths.private_relative") / reuse / "features.npz", allow_pickle=False) as z:
            save_npz_atomic(feat_path, **{k: z[k] for k in z.files})
    if not feat_path.exists():
        rows = {"d2_128": [], "plus_128": [], "plus_20map": [], "d2_20map": []}
        ages, ids = [], []
        for u in [u for u in cohort["units"] if str(u["layout_hash"]) == lh]:
            store = RecordStore(ROOT, "D1_mff_001", u["container_id"], max_bad_fraction=0.25, preload=False)
            if store.starts.size < 8:
                continue
            scale = record_scale(store)
            try:
                m = d2s.record_feature_matrix(store, scale, max_windows=400)
            except ValueError:
                continue
            rows["d2_128"].append(m[keep].ravel())
            f, p = welch_mean(store_windows(store, scale, 400), store.rate)
            rows["plus_128"].append(specplus_from_psd(f, p, h4)[keep].ravel())
            idx = np.array([store.meta["channels"].index(n) for n in names])
            vals = []
            for s0 in np.random.default_rng(20260919).choice(store.starts, min(24, store.starts.size), replace=False):
                w = np.asarray(store.read(int(s0)), np.float64)[idx]
                vals.append(np.abs(w - w.mean(0, keepdims=True)).ravel())
            sc20 = float(np.median(np.concatenate(vals)))
            sc20 = sc20 if sc20 > 1e-6 else 1.0
            wins = list(store_windows(store, sc20, 400, idx, rereference=True))
            rows["d2_20map"].append(np.mean([d2s.window_features(w, store.rate) for w in wins], 0).ravel())
            f, p = welch_mean(wins, store.rate)
            rows["plus_20map"].append(specplus_from_psd(f, p, h4).ravel())
            ages.append(float(u["age_months"]))
            ids.append(str(u["identity"]))
        save_npz_atomic(feat_path, ages=np.array(ages), identities=np.array(ids), **{k: np.array(v) for k, v in rows.items()})
    with np.load(feat_path, allow_pickle=False) as z:
        F = {k: z[k].astype(float) for k in z.files if k not in ("ages", "identities")}
        ages, ids = z["ages"].astype(float), z["identities"].astype(str)
    F["d2plus_128"] = np.concatenate([F["d2_128"], F["plus_128"]], 1)
    only = [v for v in getattr(args, "only_views", "").split(",") if v]
    if only:
        F = {k: v for k, v in F.items() if k in only}
    out, n_fits, child_err = {"views_computed": sorted(F)}, 0, {}
    for readout in ("lin", "rbf"):
        for seed in D2_SEEDS:
            ref = json.loads((d2 / f"D2_rep_{readout}_s{seed}_predictions.json").read_text())
            if list(map(str, ref["identities"])) != list(ids) or not np.allclose(ref["ages"], ages):
                raise ProvenanceError("D2_COHORT_NOT_REPRODUCED")
            base = np.asarray(ref["predictions"]["b128_v0"], float)
            child_err.setdefault((readout, "d2_saved"), []).append(np.abs(base - ages))
            for name, X in F.items():
                pred, nf = d2_readout(X, ages, ids, ref["folds"], seed, readout == "rbf")
                n_fits += nf
                child_err.setdefault((readout, name), []).append(np.abs(pred - ages))
                if name == "d2_128":
                    out.setdefault("reproduction_max_abs_diff", {})[f"{readout}_s{seed}"] = float(np.max(np.abs(pred - base)))
    out.setdefault("reproduction_max_abs_diff", "not recomputed in this run (see h8_d2plus_002)")
    B, bs = int(config["age"]["bootstrap_children"]), int(config["age"]["bootstrap_seed"])
    E = {f"{r}/{n}": np.mean(v, 0) for (r, n), v in child_err.items()}
    out["views"] = {k: {"mae": float(v.mean()), "per_seed": [float(x.mean()) for x in child_err[tuple(k.split("/"))]]}
                    for k, v in E.items()}
    out["comparisons"] = {}
    for r in ("lin", "rbf"):
        for n in ("plus_128", "d2plus_128", "plus_20map", "d2_20map"):
            if f"{r}/{n}" in E:
                idx = np.random.default_rng(bs).integers(0, len(ages), size=(B, len(ages)))
                out["comparisons"][f"{r}: d2_saved - {n}"] = age_core.paired_boot(E[f"{r}/d2_saved"] - E[f"{r}/{n}"], idx)
    out.update({"status": "COMPLETED", "exploratory_post_hoc": True, "n_records": int(len(ages)),
                "n_identities": int(len(set(ids))), "naive_mean_mae": float(np.abs(ages - ages.mean()).mean()),
                "small_fits": int(n_fits), "sign_convention": "error(D2 saved) - error(view); positive = view better"})
    write_json_atomic(run["public"] / "summary_h8.json", out, private=False)
    close_run(config, "h8_d2plus", args.run, "COMPLETED", small_fits=int(n_fits))
    return {k: round(v["mae"], 2) for k, v in out["views"].items()}


def _split_half(x0: np.ndarray, x1: np.ndarray) -> tuple[float, float]:
    x0, x1 = np.asarray(x0, np.float64), np.asarray(x1, np.float64)
    a = (x0[0::2].mean(0) + x1[0::2].mean(0)) / 2
    b = (x0[1::2].mean(0) + x1[1::2].mean(0)) / 2
    r = float(np.corrcoef(a.ravel(), b.ravel())[0, 1])
    full = (x0.mean(0) + x1.mean(0)) / 2
    return 2 * r / (1 + r), float(np.sqrt(np.mean(full ** 2)))


def cmd_h9_reliability(args, config) -> dict:
    from scipy.stats import spearmanr
    require_protocol(config)
    run = open_run("h9_reliability", args.run, config, args=vars(args))
    priv = ROOT / cfg(config, "paths.private_relative")
    src = AgeSource(config)
    rows = []
    for c in src.main_children:
        rid = str(src.rec.loc[src.primary(c), "record_id"])
        with np.load(priv / args.a1_prep_run / "inputs" / f"{rid}.npz", allow_pickle=False) as z:
            sb, rms = _split_half(z["x_std"], z["x_dev"])
        rows.append({"system": "HA_BDF", "age": src.age(c), "sb_r": sb, "rms": rms})
    coh = pd.read_csv(priv / args.h1_prep_run / "h1_cohort.csv")
    for r in coh[coh.included].itertuples():
        with np.load(priv / args.h1_prep_run / "records" / f"{r.record_id}.npz", allow_pickle=False) as z:
            sb, rms = _split_half(z["x_std"], z["x_dev"])
        rows.append({"system": "MFF_mapped20", "age": float(r.age_months), "sb_r": sb, "rms": rms})
    R = pd.DataFrame(rows)
    out = {}
    for sysname, g in R.groupby("system"):
        out[sysname] = {"n": int(len(g)),
                        "split_half_sb_median": float(g.sb_r.median()), "split_half_sb_iqr": [float(g.sb_r.quantile(.25)), float(g.sb_r.quantile(.75))],
                        "evoked_rms_median": float(g.rms.median()), "evoked_rms_iqr": [float(g.rms.quantile(.25)), float(g.rms.quantile(.75))],
                        "spearman_sb_vs_age": float(spearmanr(g.sb_r, g.age)[0]), "spearman_rms_vs_age": float(spearmanr(g.rms, g.age)[0])}
    summary = {"status": "COMPLETED", "exploratory_post_hoc": True, "systems": out,
               "note": "draw0 80+80 trials, record-scale units, 20 channels (MFF mapped + 20-channel average reference)"}
    write_json_atomic(run["public"] / "summary_h9.json", summary, private=False)
    close_run(config, "h9_reliability", args.run, "COMPLETED")
    return summary



def cmd_h8b_bdf(args, config) -> dict:
    """H8b (addendum 003): D2 + spectral-plus on the D2 BDF cohort with D2's saved folds and readout."""
    require_protocol(config)
    run = open_run("h8b_bdf", args.run, config, args=vars(args))
    d2 = ROOT / "private/auditory_d2"
    cohort = json.loads((d2 / "D1_bdf_001_cohort.json").read_text())
    h4 = config["h4"]
    feat_path = run["private"] / "features.npz"
    if not feat_path.exists():
        rows = {"d2_20": [], "plus_20": []}
        ages, ids = [], []
        for u in cohort["units"]:
            store = RecordStore(ROOT, "D1_bdf_001", u["container_id"], max_bad_fraction=0.25, preload=False)
            if store.starts.size < 8:
                continue
            scale = record_scale(store)
            try:
                m = d2s.record_feature_matrix(store, scale, max_windows=400)
            except ValueError:
                continue
            rows["d2_20"].append(m.ravel())
            f, p = welch_mean(store_windows(store, scale, 400), store.rate)
            rows["plus_20"].append(specplus_from_psd(f, p, h4).ravel())
            ages.append(float(u["age_months"]))
            ids.append(str(u["identity"]))
        save_npz_atomic(feat_path, ages=np.array(ages), identities=np.array(ids), **{k: np.array(v) for k, v in rows.items()})
    with np.load(feat_path, allow_pickle=False) as z:
        F = {k: z[k].astype(float) for k in z.files if k not in ("ages", "identities")}
        ages, ids = z["ages"].astype(float), z["identities"].astype(str)
    F["d2plus_20"] = np.concatenate([F["d2_20"], F["plus_20"]], 1)
    out, n_fits, child_err = {}, 0, {}
    for readout in ("lin", "rbf"):
        for seed in (11, 22, 33):
            ref = json.loads((d2 / f"D2_rep_bdf_{readout}_s{seed}_predictions.json").read_text())
            if list(map(str, ref["identities"])) != list(ids) or not np.allclose(ref["ages"], ages):
                raise ProvenanceError("D2_BDF_COHORT_NOT_REPRODUCED")
            key = max(ref["predictions"], key=lambda k2: int(k2.split("_")[0][1:]))      # full-array budget
            base = np.asarray(ref["predictions"][key], float)
            child_err.setdefault((readout, "d2_saved"), []).append(np.abs(base - ages))
            for name, X in F.items():
                pred, nf = d2_readout(X, ages, ids, ref["folds"], seed, readout == "rbf")
                n_fits += nf
                child_err.setdefault((readout, name), []).append(np.abs(pred - ages))
                if name == "d2_20":
                    out.setdefault("reproduction_max_abs_diff", {})[f"{readout}_s{seed}"] = float(np.max(np.abs(pred - base)))
            out.setdefault("baseline_key", key)
    B, bs = int(config["age"]["bootstrap_children"]), int(config["age"]["bootstrap_seed"])
    E = {f"{r}/{n}": np.mean(v, 0) for (r, n), v in child_err.items()}
    out["views"] = {k: {"mae": float(v.mean()), "per_seed": [float(x.mean()) for x in child_err[tuple(k.split("/"))]]} for k, v in E.items()}
    idx = np.random.default_rng(bs).integers(0, len(ages), size=(B, len(ages)))
    out["comparisons"] = {f"{r}: d2_saved - {n}": age_core.paired_boot(E[f"{r}/d2_saved"] - E[f"{r}/{n}"], idx)
                          for r in ("lin", "rbf") for n in ("plus_20", "d2plus_20")}
    out.update({"status": "COMPLETED", "exploratory_post_hoc": True, "n_records": int(len(ages)),
                "naive_mean_mae": float(np.abs(ages - ages.mean()).mean()), "small_fits": int(n_fits),
                "sign_convention": "error(D2 saved) - error(view); positive = view better"})
    write_json_atomic(run["public"] / "summary_h8b.json", out, private=False)
    close_run(config, "h8b_bdf", args.run, "COMPLETED", small_fits=int(n_fits))
    return {k: round(v["mae"], 2) for k, v in out["views"].items()}



def d2_fold(design, ages, ids, train_idx, test_idx, seed, nonlinear):
    """One outer fold of auditory_d2's nested selection (fold-wise training-median imputation)."""
    if not np.isfinite(design).all():
        med = np.nanmedian(design[train_idx], axis=0)
        design = np.where(np.isfinite(design), design, np.where(np.isfinite(med), med, 0.0)[None, :])
    inner = identity_folds(ids[train_idx], min(3, max(2, len(train_idx) // 8)), seed + 7)
    settings = [(p_, g) for p_ in PENALTIES for g in GAMMAS] if nonlinear else [(p_, None) for p_ in PENALTIES]
    errors, n = {key: [] for key in settings}, 0
    for part in inner:
        a, b = train_idx[part["train"]], train_idx[part["test"]]
        if b.size == 0:
            continue
        for key in settings:
            pen, gam = key
            fit = (_kernel_ridge(design[a], ages[a], design[b], pen, gam) if nonlinear else _ridge(design[a], ages[a], design[b], pen))
            errors[key].append(fit - ages[b])
            n += 1
    scored = {k: float(np.mean(np.concatenate(v) ** 2)) for k, v in errors.items() if v}
    pen, gam = min(scored, key=scored.get)
    pred = (_kernel_ridge(design[train_idx], ages[train_idx], design[test_idx], pen, gam) if nonlinear
            else _ridge(design[train_idx], ages[train_idx], design[test_idx], pen))
    return pred, n + 1


def cmd_h8c_grid(args, config) -> dict:
    """H8c (addendum 004): A0 units/folds, D2 readout grid for event and spectral views."""
    from . import representations as rp
    from .adapters import units
    require_protocol(config)
    run = open_run("h8c_grid", args.run, config, args=vars(args))
    src = AgeSource(config)
    co = src.co
    kids = src.main_children
    ages = np.array([src.age(c) for c in kids])
    ids = np.array([str(c) for c in kids])
    priv = ROOT / cfg(config, "paths.private_relative")
    with np.load(priv / args.features_run / "specplus_ha.npz", allow_pickle=False) as z:
        plus = z["specplus"]
    S = src.spectral(kids)
    P = np.stack([plus[src.primary(c)].ravel() for c in kids]).astype(float)
    fixed = {"spec_d2": S, "specplus": P, "spec_d2_plus": np.concatenate([S, P], 1)}
    preds = {}
    n_fits = 0
    for s, k in units(config):
        outer = co.outer(s)
        test_idx = np.array([i for i, c in enumerate(kids) if outer[c] == k])
        train_idx = np.array([i for i, c in enumerate(kids) if outer[c] != k])
        mu0, mu1 = src.class_means(s, k, kids, "single_draw80")
        with np.load(priv / args.infer_run / "items" / f"ha_s{s}_k{k}.npz", allow_pickle=False) as z:
            emb = z["emb_all"].astype(np.float64)
            where = {int(t): i for i, t in enumerate(z["all_idx"])}
        allm = np.zeros((len(kids), 2, emb.shape[1]))
        for i, c in enumerate(kids):
            tri = co.trial_idx_of_records([src.primary(c)])
            for cls in (0, 1):
                allm[i, cls] = emb[[where[int(t)] for t in tri[co.t_y[tri] == cls]]].mean(0)
        views = dict(fixed)
        # common features scaled on the training children only (paired scale), then handed to the D2 readout
        views["event_draw0"] = np.zeros((len(kids), mu0.shape[1]))
        c_tr, c_te, _ = rp.paired_design("common", mu0, mu1, train_idx, test_idx)
        views["event_draw0"][train_idx], views["event_draw0"][test_idx] = c_tr, c_te
        views["event_all"] = np.zeros((len(kids), allm.shape[2]))
        a_tr, a_te, _ = rp.paired_design("common", allm[:, 0], allm[:, 1], train_idx, test_idx)
        views["event_all"][train_idx], views["event_all"][test_idx] = a_tr, a_te
        for name, X in views.items():
            for readout in ("lin", "rbf"):
                p, nf = d2_fold(X, ages, ids, train_idx, test_idx, s, readout == "rbf")
                n_fits += nf
                preds.setdefault((readout, name, s), np.full(len(kids), np.nan))[test_idx] = p
    child_err = {}
    for (readout, name, s), p in preds.items():
        child_err.setdefault((readout, name), []).append(np.abs(p - ages))
    E = {f"{r}/{n}": np.mean(v, 0) for (r, n), v in child_err.items()}
    B, bs = int(config["age"]["bootstrap_children"]), int(config["age"]["bootstrap_seed"])
    idx = np.random.default_rng(bs).integers(0, len(kids), size=(B, len(kids)))
    comps = {f"{r}: {n} - {e}": age_core.paired_boot(E[f"{r}/{n}"] - E[f"{r}/{e}"], idx)
             for r in ("lin", "rbf") for e in ("event_draw0", "event_all") for n in ("spec_d2", "specplus", "spec_d2_plus")}
    out = {"status": "COMPLETED", "exploratory_post_hoc": True, "n_children": len(kids), "small_fits": int(n_fits),
           "views": {k: {"mae": float(v.mean()), "per_seed": [float(x.mean()) for x in child_err[tuple(k.split("/"))]]} for k, v in E.items()},
           "comparisons": comps, "median_reference_a0": 32.69,
           "sign_convention": "error(spectral view) - error(event view); positive = event better"}
    write_json_atomic(run["public"] / "summary_h8c.json", out, private=False)
    close_run(config, "h8c_grid", args.run, "COMPLETED", small_fits=int(n_fits))
    return {k: round(v["mae"], 2) for k, v in out["views"].items()}



def ridge_fast(design_train, y_train, design_eval, penalty):
    """auditory_d2.ridge_budget._ridge, solved in the dual when p > n (identical solution)."""
    centre = design_train.mean(axis=0, keepdims=True)
    spread = design_train.std(axis=0, keepdims=True)
    spread = np.where(spread <= 1e-12, 1.0, spread)
    z = (design_train - centre) / spread
    intercept = float(y_train.mean())
    if z.shape[1] > z.shape[0]:
        coef = z.T @ np.linalg.solve(z @ z.T + penalty * np.eye(z.shape[0]), y_train - intercept)
    else:
        coef = np.linalg.solve(z.T @ z + penalty * np.eye(z.shape[1]), z.T @ (y_train - intercept))
    return intercept + ((design_eval - centre) / spread) @ coef


def linear_nested(design, ages, ids, folds, seed):
    everyone = np.arange(len(ages))
    pred, n = np.full(len(ages), np.nan), 0
    for fold in folds:
        te = np.asarray(fold["test"], int)
        tr = np.setdiff1d(everyone, te)
        inner = identity_folds(ids[tr], min(3, max(2, len(tr) // 8)), seed + 7)
        errs = {pen: [] for pen in PENALTIES}
        for part in inner:
            a, b = tr[part["train"]], tr[part["test"]]
            if b.size == 0:
                continue
            for pen in PENALTIES:
                errs[pen].append(ridge_fast(design[a], ages[a], design[b], pen) - ages[b])
                n += 1
        scored = {k: float(np.mean(np.concatenate(v) ** 2)) for k, v in errs.items() if v}
        pen = min(scored, key=scored.get)
        pred[te] = ridge_fast(design[tr], ages[tr], design[te], pen)
        n += 1
    return pred, n


def cmd_h10_budget(args, config) -> dict:
    """H10 (addendum 005): D2 electrode-budget curve with D2 vs D2 + spectral-plus features (linear readout)."""
    from auditory_d2 import channels as chs
    require_protocol(config)
    run = open_run("h10_budget", args.run, config, args=vars(args))
    d2 = ROOT / "private/auditory_d2"
    layouts = json.loads((d2 / "D1_mff_001_geometry.json").read_text())
    cohort = json.loads((d2 / "D1_mff_001_cohort.json").read_text())
    counts = {}
    for u in cohort["units"]:
        counts[str(u["layout_hash"])] = counts.get(str(u["layout_hash"]), 0) + 1
    lh = max(counts, key=counts.get)
    keep = [i for i, p_ in enumerate(layouts[lh]["xyz_m"]) if p_ is not None]
    geometry = np.asarray([layouts[lh]["xyz_m"][i] for i in keep], float)
    with np.load(ROOT / cfg(config, "paths.private_relative") / args.features_run / "features.npz", allow_pickle=False) as z:
        ages, ids = z["ages"].astype(float), z["identities"].astype(str)
        M_d2 = z["d2_128"].astype(float).reshape(len(ages), 128, 9)
        M_plus = z["plus_128"].astype(float).reshape(len(ages), 128, 8)
    M_both = np.concatenate([M_d2, M_plus], 2)
    budgets = [1, 2, 4, 8, 16, 32, 48, 64, 96, 128]
    err = {}
    repro, n_fits = [], 0
    for seed in D2_SEEDS:
        ref = json.loads((d2 / f"D2_rep_lin_s{seed}_predictions.json").read_text())
        if list(map(str, ref["identities"])) != list(ids):
            raise ProvenanceError("D2_COHORT_NOT_REPRODUCED")
        for b in budgets:
            for v, subset in enumerate(chs.subset_variants(geometry, min(b, geometry.shape[0]), 3, seed=seed)):
                saved = np.asarray(ref["predictions"][f"b{b}_v{v}"], float)
                Xd = M_d2[:, subset, :].reshape(len(ages), -1)
                pd_, nf1 = linear_nested(Xd, ages, ids, ref["folds"], seed)
                repro.append(float(np.max(np.abs(pd_ - saved))))
                Xb = M_both[:, subset, :]
                Xb = Xb.reshape(len(ages), -1)
                if not np.isfinite(Xb).all():
                    med = np.nanmedian(Xb, axis=0)
                    Xb = np.where(np.isfinite(Xb), Xb, np.where(np.isfinite(med), med, 0.0)[None, :])
                pb, nf2 = linear_nested(Xb, ages, ids, ref["folds"], seed)
                n_fits += nf1 + nf2
                err.setdefault(("d2", b), []).append(np.abs(saved - ages))
                err.setdefault(("d2plus", b), []).append(np.abs(pb - ages))
    B, bs = int(config["age"]["bootstrap_children"]), int(config["age"]["bootstrap_seed"])
    idx = np.random.default_rng(bs).integers(0, len(ages), size=(B, len(ages)))
    curve = {}
    for b in budgets:
        ed, eb = np.mean(err[("d2", b)], 0), np.mean(err[("d2plus", b)], 0)
        seeds_d = [float(np.mean([np.mean(x) for x in err[("d2", b)][i * 3:(i + 1) * 3]])) for i in range(len(D2_SEEDS))]
        seeds_b = [float(np.mean([np.mean(x) for x in err[("d2plus", b)][i * 3:(i + 1) * 3]])) for i in range(len(D2_SEEDS))]
        curve[str(b)] = {"d2_mae": float(ed.mean()), "d2plus_mae": float(eb.mean()),
                         "d2_seed_range": [min(seeds_d), max(seeds_d)], "d2plus_seed_range": [min(seeds_b), max(seeds_b)],
                         "d2_minus_d2plus": age_core.paired_boot(ed - eb, idx)}

    def saturation(key):
        lo = curve["128"][f"{key}_seed_range"][0]
        hi = curve["128"][f"{key}_seed_range"][1]
        for b in budgets:
            if curve[str(b)][f"{key}_mae"] <= hi:
                return b
        return None
    out = {"status": "COMPLETED", "exploratory_post_hoc": True, "n_records": int(len(ages)), "curve": curve,
           "first_budget_within_128_seed_range": {"d2": saturation("d2"), "d2plus": saturation("d2plus")},
           "reproduction_max_abs_diff": float(max(repro)), "small_fits": int(n_fits),
           "naive_mean_mae": float(np.abs(ages - ages.mean()).mean())}
    write_json_atomic(run["public"] / "summary_h10.json", out, private=False)
    close_run(config, "h10_budget", args.run, "COMPLETED", small_fits=int(n_fits))
    return {b: (round(c["d2_mae"], 2), round(c["d2plus_mae"], 2)) for b, c in curve.items()} | {"repro": max(repro)}



def first_minutes_windows(store, scale, minutes, max_windows=400):
    """D2's `minutes` rule: earliest usable windows that end inside the first N minutes, then <= max_windows spread."""
    starts = store.starts
    limit = int(round(minutes * 60.0 * store.rate))
    starts = starts[starts + store.window <= limit]
    if starts.size == 0:
        raise ValueError("NO_WINDOW_WITHIN_MINUTES")
    if starts.size > max_windows:
        starts = starts[np.linspace(0, starts.size - 1, max_windows).astype(int)]
    return [np.asarray(store.read(int(s0)), np.float64) / scale for s0 in starts]


def cmd_h11_duration(args, config) -> dict:
    """H11 (addendum 006): D2 duration curve (first 1/2/4 minutes) with D2 vs D2 + spectral-plus features."""
    require_protocol(config)
    run = open_run("h11_duration", args.run, config, args=vars(args))
    d2 = ROOT / "private/auditory_d2"
    cohort = json.loads((d2 / "D1_mff_001_cohort.json").read_text())
    layouts = json.loads((d2 / "D1_mff_001_geometry.json").read_text())
    counts = {}
    for u in cohort["units"]:
        counts[str(u["layout_hash"])] = counts.get(str(u["layout_hash"]), 0) + 1
    lh = max(counts, key=counts.get)
    keep = np.array([i for i, p_ in enumerate(layouts[lh]["xyz_m"]) if p_ is not None], int)
    h4 = config["h4"]
    out, n_fits = {"durations": {}}, 0
    for minutes in (1, 2, 4):
        fp = run["private"] / f"features_m{minutes}.npz"
        if not fp.exists():
            d2f, plf, ages, ids = [], [], [], []
            for u in [u for u in cohort["units"] if str(u["layout_hash"]) == lh]:
                store = RecordStore(ROOT, "D1_mff_001", u["container_id"], max_bad_fraction=0.25, preload=False)
                if store.starts.size < 8:
                    continue
                scale = record_scale(store)
                try:
                    m = d2s.record_feature_matrix(store, scale, max_windows=400, minutes=float(minutes))
                    wins = first_minutes_windows(store, scale, float(minutes))
                except ValueError:
                    continue
                d2f.append(m[keep].ravel())
                f, p = welch_mean(wins, store.rate)
                plf.append(specplus_from_psd(f, p, h4)[keep].ravel())
                ages.append(float(u["age_months"]))
                ids.append(str(u["identity"]))
            save_npz_atomic(fp, d2=np.array(d2f), plus=np.array(plf), ages=np.array(ages), identities=np.array(ids))
        with np.load(fp, allow_pickle=False) as z:
            Xd, Xp, ages, ids = z["d2"].astype(float), z["plus"].astype(float), z["ages"].astype(float), z["identities"].astype(str)
        Xb = np.concatenate([Xd, Xp], 1)
        res = {}
        for seed in (11, 22, 33):
            ref = json.loads((d2 / f"D2_dur_m{minutes}_s{seed}_predictions.json").read_text())
            if list(map(str, ref["identities"])) != list(ids) or not np.allclose(ref["ages"], ages):
                raise ProvenanceError(f"D2_DURATION_COHORT_NOT_REPRODUCED:m{minutes}")
            saved = np.asarray(ref["predictions"]["b128_v0"], float)
            pr, nf0 = d2_readout(Xd, ages, ids, ref["folds"], seed, True)
            pb_rbf, nf1 = d2_readout(Xb, ages, ids, ref["folds"], seed, True)
            pb_lin, nf2 = linear_nested(np.where(np.isfinite(Xb), Xb, np.nanmedian(Xb, 0)[None, :]), ages, ids, ref["folds"], seed)
            n_fits += nf0 + nf1 + nf2
            res.setdefault("repro_max_abs_diff", []).append(float(np.max(np.abs(pr - saved))))
            for name, pred in (("d2_rbf_saved", saved), ("d2plus_rbf", pb_rbf), ("d2plus_lin", pb_lin)):
                res.setdefault(name, []).append(float(np.mean(np.abs(pred - ages))))
        out["durations"][str(minutes)] = {"n_records": int(len(ages)), **{k: (v if k == "repro_max_abs_diff" else
                                          {"mean": float(np.mean(v)), "per_seed": v}) for k, v in res.items()}}
    full = json.loads((ROOT / cfg(config, "paths.results_relative") / "h8_d2plus_003" / "summary_h8.json").read_text())["views"]
    out["full_length_reference_seeds_11_22_33"] = {
        "d2plus_lin": {"mean": float(np.mean(full["lin/d2plus_128"]["per_seed"][:3])), "per_seed": full["lin/d2plus_128"]["per_seed"][:3]},
        "d2plus_rbf": {"mean": float(np.mean(full["rbf/d2plus_128"]["per_seed"][:3])), "per_seed": full["rbf/d2plus_128"]["per_seed"][:3]},
        "d2_rbf_saved": {"mean": float(np.mean(full["rbf/d2_saved"]["per_seed"][:3])), "per_seed": full["rbf/d2_saved"]["per_seed"][:3]}}
    out.update({"status": "COMPLETED", "exploratory_post_hoc": True, "small_fits": int(n_fits),
                "note": "duration cohorts differ slightly (59/60/61 vs 62 full length); seed-level MAE, not paired across durations"})
    write_json_atomic(run["public"] / "summary_h11.json", out, private=False)
    close_run(config, "h11_duration", args.run, "COMPLETED", small_fits=int(n_fits))
    return {m: {k: (round(v["mean"], 2) if isinstance(v, dict) else max(v)) for k, v in d.items() if k != "n_records"}
            for m, d in out["durations"].items()}
