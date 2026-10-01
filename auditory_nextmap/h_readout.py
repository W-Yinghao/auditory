"""H-series CPU readouts (NEXTMAP_H_PROTOCOL_FROZEN.md sections 1-6). Saved inputs only; A0 rules for every readout.

Each command writes per-unit JSON (private) and one aggregate summary (results/). Child errors are averaged over seeds
(and encoders for H1) before paired child bootstrap with shared indices; negative differences are kept.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import age_core
from . import age_readout as ar
from . import representations as rp
from .adapters import AgeSource, units
from .runtime import ROOT, cfg, close_run, open_run, require_protocol, stable_int, write_json_atomic


def _boot(diff: np.ndarray, B: int, seed: int) -> dict:
    idx = np.random.default_rng(seed).integers(0, len(diff), size=(B, len(diff)))
    return age_core.paired_boot(diff, idx)


def _fit(design, y, n_tr, test_rows, config, kind, key, s, k):
    a = config["age"]
    alphas = a["kernel_alpha"] if kind == "rbf" else a["alpha_sse"]
    return ar.select_and_fit(design, y, n_tr, test_rows, kind=kind, alphas=alphas, inner_folds=int(a["inner_folds"]),
                             inner_seed=stable_int("nextmap_inner", *key) % (2 ** 31 - 1) if key else age_core.inner_seed(s, k),
                             tie_tol=float(a["tie_tolerance"]), ledger=[], key={"seed": s, "fold": k},
                             gamma_fallback=float(a["kernel_gamma_fallback"]))


def joint_design(mu0, mu1, X, floor=1e-8, missing=False):
    def design(tr, ev):
        c_tr, c_ev, _ = rp.paired_design("common", mu0, mu1, tr, ev, floor=floor)
        s_tr, s_ev, _ = rp.standard_design(X, tr, ev, floor=floor, missing_flags=missing)
        return np.concatenate([c_tr, s_tr], 1), np.concatenate([c_ev, s_ev], 1), {}
    return design


# ====================================================================== H1 cross-system (MFF)

def cmd_h1_readout(args, config) -> dict:
    require_protocol(config)
    run = open_run("h1_readout", args.run, config, args=vars(args))
    h1, a = config["h1"], config["age"]
    priv = ROOT / cfg(config, "paths.private_relative")
    coh = pd.read_csv(priv / args.prep_run / "h1_cohort.csv")
    coh = coh[coh.included].reset_index(drop=True)
    ids = coh.record_id.tolist()
    ages = coh.age_months.to_numpy(float)
    rec = {}
    for rid in ids:
        with np.load(priv / args.prep_run / "records" / f"{rid}.npz", allow_pickle=False) as z:
            rec[rid] = {k: z[k] for k in ("raw_mu0", "raw_mu1", "spec20", "specplus20", "spec128")}
    raw0 = np.stack([rec[r]["raw_mu0"] for r in ids]).astype(float)
    raw1 = np.stack([rec[r]["raw_mu1"] for r in ids]).astype(float)
    spec20 = np.stack([rec[r]["spec20"].ravel() for r in ids]).astype(float)
    plus20 = np.stack([rec[r]["specplus20"].ravel() for r in ids]).astype(float)
    spec128 = np.stack([rec[r]["spec128"].ravel() for r in ids]).astype(float)
    enc = {}
    for s, k in h1["encoder_units"]:
        with np.load(priv / args.infer_run / "items" / f"ha_s{s}_k{k}.npz", allow_pickle=False) as z:
            assert [str(x) for x in z["mff_ids"]] == ids
            enc[f"ha_s{s}"] = z["mff_means"].astype(float)
    rnd = {}
    for i in range(int(h1["random_inits"])):
        with np.load(priv / args.infer_run / "items" / f"rand_{i}.npz", allow_pickle=False) as z:
            assert [str(x) for x in z["mff_ids"]] == ids
            rnd[f"rand_{i}"] = z["mff_means"].astype(float)
    n = len(ids)
    groups = coh.identity_group.astype(str).to_numpy()
    uniq = sorted(set(groups))
    views = {"ha_encoder_common": [("ridge", "paired", enc[e]) for e in enc],
             "random_common": [("ridge", "paired", rnd[e]) for e in rnd],
             "raw_common": [("ridge", "paired", np.stack([raw0, raw1], 1))],
             "spec20_ridge": [("ridge", "std", spec20)], "spec20_rbf": [("rbf", "std", spec20)],
             "specplus20_ridge": [("ridge", "stdmiss", plus20)], "spec128_ridge": [("ridge", "std", spec128)],
             "median_train": [(None, None, None)]}
    err = {v: np.zeros((n, 0)) for v in views}
    n_fits = 0
    for cv in h1["cv_seeds"]:
        order = list(np.random.default_rng(int(cv)).permutation(uniq))
        fold_of = {g: i % int(h1["n_folds"]) for i, g in enumerate(order)}
        f = np.array([fold_of[g] for g in groups])
        for v, specs in views.items():
            for si, (kind, dtype_, X) in enumerate(specs):
                e = np.full(n, np.nan)
                for k in range(int(h1["n_folds"])):
                    tr, te = np.flatnonzero(f != k), np.flatnonzero(f == k)
                    rows = np.concatenate([tr, te])
                    y = ages[rows]
                    if kind is None:
                        e[te] = np.abs(np.median(ages[tr]) - ages[te])
                        continue
                    if dtype_ == "paired":
                        m0, m1 = X[rows, 0], X[rows, 1]
                        design = (lambda trr, evr, m0=m0, m1=m1: rp.paired_design("common", m0, m1, trr, evr, floor=float(a["scale_floor"])))
                    else:
                        Xr = X[rows]
                        design = (lambda trr, evr, Xr=Xr, miss=(dtype_ == "stdmiss"): rp.standard_design(Xr, trr, evr, missing_flags=miss))
                    res = _fit(design, y, len(tr), np.arange(len(tr), len(rows)), config, kind, ("h1", cv, k, v, si), cv, k)
                    n_fits += res["n_fits"]
                    e[te] = np.abs(res["pred"] - ages[te])
                err[v] = np.column_stack([err[v], e])
    E = {v: m.mean(1) for v, m in err.items()}
    B, bs = int(a["bootstrap_children"]), int(a["bootstrap_seed"])
    comps = {f"{b}_minus_ha_encoder": _boot(E[b] - E["ha_encoder_common"], B, bs)
             for b in ("median_train", "spec20_ridge", "spec20_rbf", "specplus20_ridge", "random_common", "raw_common", "spec128_ridge")}
    base = float(E["median_train"].mean())
    pt = (coh.lane == "mff_puretone").to_numpy()
    summary = {"status": "COMPLETED", "n_children": n, "age_range": [float(ages.min()), float(ages.max())],
               "views": {v: {"mae": float(E[v].mean()), "relative_to_median": float(E[v].mean() / base),
                             "replicate_mae_range": [float(err[v].mean(0).min()), float(err[v].mean(0).max())],
                             "puretone_subset_mae": float(E[v][pt].mean()) if pt.any() else None} for v in views},
               "puretone_subset_n": int(pt.sum()), "comparisons": comps, "small_age_fits": n_fits,
               "sign_convention": "error(view) - error(ha_encoder_common); positive = HA encoder better"}
    write_json_atomic(run["public"] / "summary_h1.json", summary, private=False)
    close_run(config, "h1_readout", args.run, "COMPLETED", small_age_fits=n_fits)
    return {v: round(d["mae"], 2) for v, d in summary["views"].items()} | {"n": n}


# ====================================================================== shared HA helpers

def _ha_tables(config, src, run_dir, name, unit_rows) -> dict:
    kids = src.main_children
    ages = {c: src.age(c) for c in kids}
    return age_core.view_table(age_core.collect_predictions(unit_rows, kids), ages, kids)


def _a0_rows(config, view="common", budget="single_draw80", a0_run="a0_001"):
    priv = ROOT / cfg(config, "paths.private_relative") / a0_run
    return [json.loads(age_core.unit_path(priv, budget, view, s, k).read_text()) for s, k in units(config)]


def _ha_fit_unit(src, config, s, k, design_from_rows, kind="ridge", key=None):
    tr, te = age_core.split(src, s, k)
    rows = tr + te
    y = np.array([src.age(c) for c in rows])
    res = _fit(design_from_rows(rows), y, len(tr), np.arange(len(tr), len(rows)), config, kind, key, s, k)
    return {"seed": s, "fold": k, "test_children": te, "pred": res["pred"].tolist(), "n_fits": res["n_fits"],
            "alpha": res["alpha"], "model": res["model"], "train": tr}


# ====================================================================== H2 budget curve

def cmd_h2_readout(args, config) -> dict:
    require_protocol(config)
    run = open_run("h2_readout", args.run, config, args=vars(args))
    src = AgeSource(config)
    co = src.co
    kids = src.main_children
    prim = {c: src.primary(c) for c in kids}
    priv = ROOT / cfg(config, "paths.private_relative")
    h2 = config["h2"]
    specs = [(kk, "random", d) for kk in h2["k_per_class"] for d in range(int(h2["random_draws"]))]
    specs += [(kk, "first", 0) for kk in h2["k_per_class"]] + [(0, "all", 0)]
    # per record trial positions inside emb_all (same order for every unit: trial_idx_of_records of the primary records)
    all_idx = co.trial_idx_of_records([prim[c] for c in kids])
    where = {int(t): i for i, t in enumerate(all_idx)}
    sel_cache, times = {}, {}
    for kk, scheme, d in specs:
        for c in kids:
            r = prim[c]
            tri = co.trial_idx_of_records([r])
            pos = {}
            for cls in (0, 1):
                cand = tri[co.t_y[tri] == cls]
                if scheme == "all":
                    pick = cand
                elif scheme == "first":
                    pick = cand[np.argsort(co.t_onset[cand], kind="stable")[:kk]]
                else:
                    rng = np.random.default_rng(stable_int("h2", str(src.rec.loc[r, "record_id"]), cls, kk, d) % (2 ** 63))
                    pick = rng.choice(cand, min(kk, len(cand)), replace=False)
                pos[cls] = np.array([where[int(t)] for t in pick])
            sel_cache[(kk, scheme, d, c)] = pos
            if scheme == "first":
                onsets = np.concatenate([co.t_onset[all_idx[pos[0]]], co.t_onset[all_idx[pos[1]]]])
                first_onset = co.t_onset[tri].min()
                times.setdefault(kk, []).append(float((onsets.max() - first_onset) / 60.0))
    results, n_fits = {}, 0
    for s, k in units(config):
        with np.load(priv / args.infer_run / "items" / f"ha_s{s}_k{k}.npz", allow_pickle=False) as z:
            emb = z["emb_all"].astype(np.float64)
            assert np.array_equal(z["all_idx"], all_idx)
        for kk, scheme, d in specs:
            mu0 = np.stack([emb[sel_cache[(kk, scheme, d, c)][0]].mean(0) for c in kids])
            mu1 = np.stack([emb[sel_cache[(kk, scheme, d, c)][1]].mean(0) for c in kids])
            pos_of = {c: i for i, c in enumerate(kids)}

            def design_from_rows(rows, mu0=mu0, mu1=mu1):
                ix = [pos_of[c] for c in rows]
                return lambda trr, evr: rp.paired_design("common", mu0[ix], mu1[ix], trr, evr, floor=float(config["age"]["scale_floor"]))
            u = _ha_fit_unit(src, config, s, k, design_from_rows)
            n_fits += u["n_fits"]
            results.setdefault((kk, scheme, d), []).append({k2: v for k2, v in u.items() if k2 not in ("model", "train")})
    ages = {c: src.age(c) for c in kids}
    out = {}
    for (kk, scheme, d), rows in results.items():
        t = age_core.view_table(age_core.collect_predictions(rows, kids), ages, kids)
        out.setdefault(f"{scheme}_k{kk}" if scheme != "all" else "all", []).append(t["mae"])
    summary = {"status": "COMPLETED", "n_children": len(kids), "small_age_fits": n_fits,
               "mae": {key: {"mean": float(np.mean(v)), "draw_range": [float(min(v)), float(max(v))]} for key, v in out.items()},
               "first_k_recording_minutes": {str(kk): {"median": float(np.median(v)), "range": [float(min(v)), float(max(v))]}
                                             for kk, v in times.items()},
               "a0_reference_draw0_k80": 23.22}
    write_json_atomic(run["public"] / "summary_h2.json", summary, private=False)
    close_run(config, "h2_readout", args.run, "COMPLETED", small_age_fits=n_fits)
    return {k2: round(v["mean"], 2) for k2, v in summary["mae"].items()}


# ====================================================================== H3 fine-tune / multitask

def cmd_h3_readout(args, config) -> dict:
    require_protocol(config)
    run = open_run("h3_readout", args.run, config, args=vars(args))
    src = AgeSource(config)
    kids = src.main_children
    ages = {c: src.age(c) for c in kids}
    priv = ROOT / cfg(config, "paths.private_relative")
    tables, n_fits, infos = {}, 0, {}
    for arm in config["h3"]["arms"]:
        direct, ridge, ep, vm = [], [], [], []
        for s, k in units(config):
            with np.load(priv / args.train_run / "units" / arm / f"s{s}_k{k}.npz", allow_pickle=False) as z:
                pred, emb, info = z["pred_months"], z["emb"].astype(float), json.loads(str(z["info"]))
            ep.append(info["epochs_run"]); vm.append(info["best_val_mae_months"])
            tr, te = age_core.split(src, s, k)
            direct.append({"seed": s, "fold": k, "test_children": te, "pred": [float(pred[src.primary(c)]) for c in te]})
            pos = [src.primary(c) for c in tr + te]

            def dfr(rows, emb=emb, pos=pos):
                return lambda trr, evr: rp.paired_design("common", emb[pos, 0], emb[pos, 1], trr, evr, floor=float(config["age"]["scale_floor"]))
            u = _ha_fit_unit(src, config, s, k, dfr)
            n_fits += u["n_fits"]
            ridge.append({k2: v for k2, v in u.items() if k2 not in ("model", "train")})
        tables[f"{arm}_direct"] = age_core.view_table(age_core.collect_predictions(direct, kids), ages, kids)
        tables[f"{arm}_common_ridge"] = age_core.view_table(age_core.collect_predictions(ridge, kids), ages, kids)
        infos[arm] = {"epochs_median": float(np.median(ep)), "epochs_range": [int(min(ep)), int(max(ep))], "val_mae_median": float(np.median(vm))}
    tables["trained_common"] = age_core.view_table(age_core.collect_predictions(_a0_rows(config), kids), ages, kids)
    g1 = [json.loads((priv / "g1_readout_001" / "units" / "age_trial_direct" / f"s{s}_k{k}.json").read_text()) for s, k in units(config)]
    tables["g1_age_trial_direct"] = age_core.view_table(age_core.collect_predictions(g1, kids), ages, kids)
    B, bs = int(config["age"]["bootstrap_children"]), int(config["age"]["bootstrap_seed"])
    comps = {}
    for name, (va, vb) in {"trained_common_minus_ft_direct": ("trained_common", "ft_from_stim_direct"),
                           "trained_common_minus_mt_direct": ("trained_common", "multitask_direct"),
                           "trained_common_minus_ft_common_ridge": ("trained_common", "ft_from_stim_common_ridge"),
                           "trained_common_minus_mt_common_ridge": ("trained_common", "multitask_common_ridge"),
                           "g1_age_trial_minus_ft_direct": ("g1_age_trial_direct", "ft_from_stim_direct"),
                           "g1_age_trial_minus_mt_direct": ("g1_age_trial_direct", "multitask_direct")}.items():
        comps[name] = {"a": va, "b": vb, **_boot(tables[va]["err"] - tables[vb]["err"], B, bs)}
    summary = {"status": "COMPLETED", "n_children": len(kids), "small_age_fits": n_fits, "training": infos,
               "views": {v: {k2: x for k2, x in t.items() if k2 != "err"} for v, t in tables.items()}, "comparisons": comps,
               "sign_convention": "error(a) - error(b); positive = b better"}
    write_json_atomic(run["public"] / "summary_h3.json", summary, private=False)
    close_run(config, "h3_readout", args.run, "COMPLETED", small_age_fits=n_fits)
    return {v: round(t["mae"], 2) for v, t in tables.items()}


# ====================================================================== H4 spectral-plus

def cmd_h4_readout(args, config) -> dict:
    require_protocol(config)
    run = open_run("h4_readout", args.run, config, args=vars(args))
    src = AgeSource(config)
    kids = src.main_children
    ages = {c: src.age(c) for c in kids}
    priv = ROOT / cfg(config, "paths.private_relative")
    with np.load(priv / args.features_run / "specplus_ha.npz", allow_pickle=False) as z:
        plus = z["specplus"]
    floor = float(config["age"]["scale_floor"])
    rows_out = {v: [] for v in ("specplus_ridge", "specplus_rbf", "spec_d2_plus_ridge", "event_plus_specplus", "event_plus_spec_d2")}
    n_fits = 0
    for s, k in units(config):
        tr, te = age_core.split(src, s, k)
        order = tr + te
        P = np.stack([plus[src.primary(c)].ravel() for c in order]).astype(float)
        S = src.spectral(order)
        mu0, mu1 = src.class_means(s, k, order, "single_draw80")
        designs = {"specplus_ridge": ("ridge", lambda trr, evr: rp.standard_design(P, trr, evr, floor=floor, missing_flags=True)),
                   "specplus_rbf": ("rbf", lambda trr, evr: rp.standard_design(P, trr, evr, floor=floor, missing_flags=True)),
                   "spec_d2_plus_ridge": ("ridge", lambda trr, evr: rp.standard_design(np.concatenate([S, P], 1), trr, evr, floor=floor, missing_flags=True)),
                   "event_plus_specplus": ("ridge", joint_design(mu0, mu1, P, floor, missing=True)),
                   "event_plus_spec_d2": ("ridge", joint_design(mu0, mu1, S, floor))}
        y = np.array([src.age(c) for c in order])
        for v, (kind, design) in designs.items():
            res = _fit(design, y, len(tr), np.arange(len(tr), len(order)), config, kind, None, s, k)
            n_fits += res["n_fits"]
            rows_out[v].append({"seed": s, "fold": k, "test_children": te, "pred": res["pred"].tolist()})
    tables = {v: age_core.view_table(age_core.collect_predictions(r, kids), ages, kids) for v, r in rows_out.items()}
    for v in ("common", "spectral_ridge", "spectral_rbf"):
        tables[f"a0_{v}"] = age_core.view_table(age_core.collect_predictions(_a0_rows(config, v), kids), ages, kids)
    B, bs = int(config["age"]["bootstrap_children"]), int(config["age"]["bootstrap_seed"])
    comps = {}
    for name, (va, vb) in {"specplus_ridge_minus_trained_common": ("specplus_ridge", "a0_common"),
                           "specplus_rbf_minus_trained_common": ("specplus_rbf", "a0_common"),
                           "spec_d2_plus_minus_trained_common": ("spec_d2_plus_ridge", "a0_common"),
                           "trained_common_minus_event_plus_specplus": ("a0_common", "event_plus_specplus"),
                           "trained_common_minus_event_plus_spec_d2": ("a0_common", "event_plus_spec_d2"),
                           "a0_spectral_ridge_minus_specplus_ridge": ("a0_spectral_ridge", "specplus_ridge")}.items():
        comps[name] = {"a": va, "b": vb, **_boot(tables[va]["err"] - tables[vb]["err"], B, bs)}
    summary = {"status": "COMPLETED", "n_children": len(kids), "small_age_fits": n_fits,
               "views": {v: {k2: x for k2, x in t.items() if k2 != "err"} for v, t in tables.items()}, "comparisons": comps,
               "sign_convention": "error(a) - error(b); positive = b better"}
    write_json_atomic(run["public"] / "summary_h4.json", summary, private=False)
    close_run(config, "h4_readout", args.run, "COMPLETED", small_age_fits=n_fits)
    return {v: round(t["mae"], 2) for v, t in tables.items()}


# ====================================================================== H5 association (descriptive)

def _residualise(v, age):
    Z = np.column_stack([np.ones_like(age), age, age ** 2])
    return v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]


def cmd_h5_assoc(args, config) -> dict:
    from scipy.stats import spearmanr
    require_protocol(config)
    run = open_run("h5_assoc", args.run, config, args=vars(args))
    src = AgeSource(config)
    kids = src.main_children
    age = np.array([src.age(c) for c in kids])
    preds = age_core.collect_predictions(_a0_rows(config), kids)
    pm = np.array([np.mean([preds[s][c] for s in preds]) for c in kids])
    resid = pm - age
    rr = _residualise(resid, age)
    rec = src.rec
    pr = [src.primary(c) for c in kids]
    dur = np.array([rec.loc[r, "duration_months"] for r in pr], float)
    var = {"log1p_duration_months": np.log1p(dur), "pta_unaided": np.array([rec.loc[r, "pta_unaided"] for r in pr], float),
           "pta_aided": np.array([rec.loc[r, "pta_aided"] for r in pr], float), "fitting_age_months": age - dur}
    out = {}
    rng = np.random.default_rng(27092705)
    for name, v in var.items():
        m = np.isfinite(v)
        rv = _residualise(v[m], age[m])
        rres = _residualise(resid[m], age[m])
        rho = float(spearmanr(rres, rv)[0])
        null = np.array([spearmanr(rres, rng.permutation(rv))[0] for _ in range(int(config["h5"]["permutations"]))])
        out[name] = {"n": int(m.sum()), "partial_spearman_given_age_age2": rho,
                     "perm_p_two_sided": float((1 + np.sum(np.abs(null) >= abs(rho) - 1e-12)) / (1 + len(null)))}
    lo, hi = config["h5"]["restricted_age_range_months"]
    ins = (age >= lo) & (age <= hi)
    t_common = age_core.view_table(preds, {c: a for c, a in zip(kids, age)}, kids)
    t_med = age_core.view_table(age_core.collect_predictions(_a0_rows(config, "median_train"), kids), {c: a for c, a in zip(kids, age)}, kids)
    summary = {"status": "COMPLETED", "n_children": len(kids), "associations": out,
               "spearman_pred_vs_age": float(spearmanr(pm, age)[0]),
               "restricted_range": {"range_months": [lo, hi], "n": int(ins.sum()),
                                    "mae_trained_common": float(t_common["err"][ins].mean()),
                                    "mae_median_train": float(t_med["err"][ins].mean())},
               "residual_age_correlation_before_correction": float(spearmanr(resid, age)[0]),
               "note": "descriptive; residuals and covariates both residualised on age and age^2 (no uncorrected brain-age gap)"}
    write_json_atomic(run["public"] / "summary_h5.json", summary, private=False)
    close_run(config, "h5_assoc", args.run, "COMPLETED")
    return summary


# ====================================================================== H6 occlusion

def cmd_h6_readout(args, config) -> dict:
    require_protocol(config)
    run = open_run("h6_readout", args.run, config, args=vars(args))
    src = AgeSource(config)
    kids = src.main_children
    ages = {c: src.age(c) for c in kids}
    priv = ROOT / cfg(config, "paths.private_relative")
    floor = float(config["age"]["scale_floor"])
    n_fits, names, preds, check = 0, None, {}, []
    a0 = {(u["seed"], u["fold"]): u for u in _a0_rows(config)}
    for s, k in units(config):
        with np.load(priv / args.infer_run / "items" / f"ha_s{s}_k{k}.npz", allow_pickle=False) as z:
            occ = z["occl_means"].astype(float)            # [O+1, 55, 2, 192] in main_children order
            names = [str(x) for x in z["occl_names"]]
        tr, te = age_core.split(src, s, k)
        idx = [kids.index(c) for c in tr + te]
        intact0, intact1 = occ[0, idx, 0], occ[0, idx, 1]

        def dfr(rows):
            return lambda trr, evr: rp.paired_design("common", intact0, intact1, trr, evr, floor=floor)
        u = _ha_fit_unit(src, config, s, k, dfr)
        n_fits += u["n_fits"]
        check.append(float(np.max(np.abs(np.array(u["pred"]) - np.array(a0[(s, k)]["pred"])))))
        n_tr = len(tr)
        for o in range(occ.shape[0]):
            m0, m1 = intact0.copy(), intact1.copy()
            m0[n_tr:], m1[n_tr:] = occ[o, idx[n_tr:], 0], occ[o, idx[n_tr:], 1]
            _, Xte, _ = rp.paired_design("common", m0, m1, np.arange(n_tr), np.arange(n_tr, len(idx)), floor=floor)
            p = ar.ridge_predict(u["model"], Xte)
            preds.setdefault(names[o], []).append({"seed": s, "fold": k, "test_children": te, "pred": p.tolist()})
    tables = {nm: age_core.view_table(age_core.collect_predictions(r, kids), ages, kids) for nm, r in preds.items()}
    base = tables["intact"]
    B, bs = int(config["age"]["bootstrap_children"]), int(config["age"]["bootstrap_seed"])
    prof = {nm: {"delta_mae": float(t["mae"] - base["mae"]),
                 "delta_mae_per_seed": [float(a - b) for a, b in zip(t["mae_per_seed"], base["mae_per_seed"])],
                 **{f"boot_{kk}": v for kk, v in _boot(t["err"] - base["err"], B, bs).items() if kk in ("ci95", "reading")}}
            for nm, t in tables.items() if nm != "intact"}
    summary = {"status": "COMPLETED", "n_children": len(kids), "small_age_fits": n_fits, "intact_mae": base["mae"],
               "intact_vs_a0_max_abs_pred_diff": float(max(check)), "occlusion_delta_mae": prof,
               "note": "test-only occlusion of the M_o input; model and scaling fitted on intact training embeddings"}
    write_json_atomic(run["public"] / "summary_h6.json", summary, private=False)
    close_run(config, "h6_readout", args.run, "COMPLETED", small_age_fits=n_fits)
    return {"intact": round(base["mae"], 2), "check": max(check), "top": sorted(((v["delta_mae"], k2) for k2, v in prof.items()), reverse=True)[:6]}


# ====================================================================== H7 age-range restriction (post-hoc, addendum 001)

def cmd_h7_range(args, config) -> dict:
    """(1) evaluation-only restriction of SAVED full-range predictions (A0 views; H2/H4 per-unit predictions were not
    persisted and identical models are not refitted merely to re-evaluate them); (2) refits on in-range children only."""
    require_protocol(config)
    run = open_run("h7_range", args.run, config, args=vars(args))
    src = AgeSource(config)
    kids = src.main_children
    lo, hi = config["h7"]["range_months"]
    ages = {c: src.age(c) for c in kids}
    inr = [c for c in kids if lo <= ages[c] <= hi]
    B, bs = int(config["age"]["bootstrap_children"]), int(config["age"]["bootstrap_seed"])
    priv = ROOT / cfg(config, "paths.private_relative")
    # (1) evaluation-only
    eval_only = {}
    for v in ("common", "spectral_ridge", "spectral_rbf", "technical", "median_train"):
        t = age_core.view_table(age_core.collect_predictions(_a0_rows(config, v), kids), ages, kids)
        eval_only[v] = np.array([t["err"][kids.index(c)] for c in inr])
    part1 = {"views": {v: float(e.mean()) for v, e in eval_only.items()},
             "comparisons": {f"{v}_minus_common": _boot(eval_only[v] - eval_only["common"], B, bs)
                             for v in ("spectral_ridge", "spectral_rbf", "technical", "median_train")},
             "not_computed": "H2 all-trials and H4 specplus views (per-unit predictions not persisted; no duplicate refits)"}
    # (2) in-range refits
    with np.load(priv / args.features_run / "specplus_ha.npz", allow_pickle=False) as z:
        plus = z["specplus"]
    floor = float(config["age"]["scale_floor"])
    co = src.co
    rows = {v: [] for v in ("event_common_draw0", "event_common_all", "spectral_ridge", "spectral_rbf",
                            "specplus_ridge", "specplus_rbf", "median_train")}
    n_fits = 0
    for s, k in units(config):
        tr, te = age_core.split(src, s, k, inr)
        order = tr + te
        y = np.array([ages[c] for c in order])
        with np.load(priv / args.infer_run / "items" / f"ha_s{s}_k{k}.npz", allow_pickle=False) as z:
            emb = z["emb_all"].astype(np.float64)
            where = {int(t): i for i, t in enumerate(z["all_idx"])}
        allm = np.zeros((len(order), 2, emb.shape[1]))
        for i, c in enumerate(order):
            tri = co.trial_idx_of_records([src.primary(c)])
            for cls in (0, 1):
                allm[i, cls] = emb[[where[int(t)] for t in tri[co.t_y[tri] == cls]]].mean(0)
        d0 = src.class_means(s, k, order, "single_draw80")
        S = src.spectral(order)
        P = np.stack([plus[src.primary(c)].ravel() for c in order]).astype(float)
        specs = {"event_common_draw0": ("ridge", lambda a, b: rp.paired_design("common", d0[0], d0[1], a, b, floor=floor)),
                 "event_common_all": ("ridge", lambda a, b: rp.paired_design("common", allm[:, 0], allm[:, 1], a, b, floor=floor)),
                 "spectral_ridge": ("ridge", lambda a, b: rp.standard_design(S, a, b, floor=floor)),
                 "spectral_rbf": ("rbf", lambda a, b: rp.standard_design(S, a, b, floor=floor)),
                 "specplus_ridge": ("ridge", lambda a, b: rp.standard_design(P, a, b, floor=floor, missing_flags=True)),
                 "specplus_rbf": ("rbf", lambda a, b: rp.standard_design(P, a, b, floor=floor, missing_flags=True))}
        for v, (kind, design) in specs.items():
            res = _fit(design, y, len(tr), np.arange(len(tr), len(order)), config, kind, None, s, k)
            n_fits += res["n_fits"]
            rows[v].append({"seed": s, "fold": k, "test_children": te, "pred": res["pred"].tolist()})
        rows["median_train"].append({"seed": s, "fold": k, "test_children": te, "pred": [float(np.median(y[:len(tr)]))] * len(te)})
    for v, r in rows.items():
        write_json_atomic(run["private"] / "units" / f"{v}.json", r, private=True)
    ages_in = {c: ages[c] for c in inr}
    tables = {v: age_core.view_table(age_core.collect_predictions(r, inr), ages_in, inr) for v, r in rows.items()}
    base = tables["median_train"]["mae"]
    part2 = {"views": {v: {"mae": t["mae"], "relative_to_median": t["mae"] / base,
                           "seed_range": [min(t["mae_per_seed"]), max(t["mae_per_seed"])]} for v, t in tables.items()},
             "comparisons": {f"{v}_minus_{e}": _boot(tables[v]["err"] - tables[e]["err"], B, bs)
                             for e in ("event_common_draw0", "event_common_all")
                             for v in ("spectral_ridge", "spectral_rbf", "specplus_ridge", "specplus_rbf", "median_train")}}
    summary = {"status": "COMPLETED", "exploratory_post_hoc": True, "range_months": [lo, hi], "n_in_range": len(inr),
               "n_out_of_range": len(kids) - len(inr), "evaluation_only": part1, "in_range_refit": part2,
               "small_age_fits": n_fits, "sign_convention": "error(view) - error(event); positive = event better"}
    write_json_atomic(run["public"] / "summary_h7.json", summary, private=False)
    close_run(config, "h7_range", args.run, "COMPLETED", small_age_fits=n_fits)
    return {"n_in": len(inr), "eval_only": {v: round(x, 2) for v, x in part1["views"].items()},
            "refit": {v: round(x["mae"], 2) for v, x in part2["views"].items()}}
