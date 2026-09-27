"""Drivers: (b) permutations, H12 shuffles, B1/B2/B3 analyses, claim states (protocol sections 6-7).

`--blind` replaces every stage and SIR label by a child-level permutation (perm 1) so that the whole
analysis chain can be exercised before the real labels are touched (technical dry run only).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import stats as st
from .analysis_b1 import (B1, b_ord_scores, blocks_of, ensemble_occ_scores, ensemble_trial_scores, h14_models,
                          one_d_ordinal, si_eval, sir_labels, three_category)
from .cohort import Cohort
from .e2e import permuted_labels
from .runtime import (cfg, open_run, private_dir, read_json, results_dir, stable_int, task_units, write_csv_atomic,
                      write_json_atomic)


def _labels(b: B1, blind: bool) -> tuple[dict, dict]:
    stage = {c: b.stage[c] for c in b.E}
    sir = sir_labels(b)
    if blind:
        stage = permuted_labels(b.co, 1, "stage")
        sir = permuted_labels(b.co, 1, "sir")
    return stage, sir


# ============================================================================ array jobs

def cmd_perm_b(args, config) -> dict:
    run = open_run("perm_b", args.run, config, args=vars(args))
    b = B1(config, prepare_run=args.prepare_run, stim_run=args.stim_run, embed_source=args.embed_source)
    P = int(cfg(config, "stats.perm_b"))
    n = 0
    for p in task_units(list(range(1, P + 1))):
        path = run["private"] / f"p{p:04d}.json"
        if path.exists():
            continue
        lab = permuted_labels(b.co, p, "stage")
        oof = b.b_scores(lab)["oof"]
        write_json_atomic(path, {"p": p, "auc": b.auc_seeds(oof, lab)["mean"]}, private=True)
        n += 1
    return {"perms": n}


def shuffled_sir(b: B1, j: int, strata: str) -> dict[int, float]:
    """SIR permuted among eligible labelled children within stage strata (binary) or 4 duration bins."""
    rng = np.random.default_rng(stable_int("pf_h12", strata, j))
    kids = np.array(b.E)
    sir = np.array([b.ch.loc[c, "sir"] for c in kids], float)
    dur = np.array([b.ch.loc[c, "duration_months"] for c in kids], float)
    if strata == "stage":
        key = (dur >= float(cfg(b.config, "labels.stage1_min_months"))).astype(int)
    else:
        key = np.digitize(dur, [2.5, 12.5, 36.5])
    out = sir.copy()
    for g in np.unique(key):
        m = np.flatnonzero(key == g)
        out[m] = sir[m][rng.permutation(len(m))]
    return dict(zip(kids.astype(int), out))


def cmd_shuffle_h12(args, config) -> dict:
    run = open_run("shuffle_h12", args.run, config, args=vars(args))
    b = B1(config, prepare_run=args.prepare_run, stim_run=args.stim_run, embed_source=args.embed_source)
    S = int(cfg(config, "stats.shuffles_h12"))
    units = [(strata, j) for strata in ("stage", "bins4") for j in range(1, S + 1)]
    n = 0
    for strata, j in task_units(units):
        path = run["private"] / f"{strata}_{j:04d}.json"
        if path.exists():
            continue
        sir = shuffled_sir(b, j, strata)
        res = b_ord_scores(b, sir)
        ev = si_eval(b, res["latent"], res["expected"], sir)
        write_json_atomic(path, {"strata": strata, "j": j, "auc": ev["auc_sir_gt3"]["mean"], "mae": ev["mae"]["mean"]}, private=True)
        n += 1
    return {"shuffles": n}


# ============================================================================ status helper

def status(*, supported=False, refuted=False, partial=False, direction=False, not_evaluable: str | None = None) -> str:
    if not_evaluable:
        return f"不可评估（{not_evaluable}）"
    if refuted:
        return "推翻"
    if supported:
        return "成立"
    if partial:
        return "部分成立"
    return "精度不足（方向一致）" if direction else "精度不足（方向不一致）"


def _r(x, n=3):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


# ============================================================================ B1

def analyze_b1(config, args, blind: bool) -> dict:
    b = B1(config, prepare_run=args.prepare_run, stim_run=args.stim_run, e2e_run=args.e2e_run, features_run=args.features_run, embed_source=args.embed_source)
    stage, sir = _labels(b, blind)
    out: dict = {"blind": blind, "embed_source": b.embed_source, "n_eligible": len(b.E), "n_nh": len(b.NH),
                 "n_stage0": int(sum(1 for c in b.E if stage[c] == 0)), "n_stage1": int(sum(1 for c in b.E if stage[c] == 1))}
    priv = {}
    P_a = int(cfg(config, "stats.perm_a"))
    # ---------------- (a1)
    a1 = b.a1_scores()
    a1s = b.a1_scores(strict=True)
    A1 = b.auc_seeds(a1["oof"], stage)
    null_a1 = [b.auc_seeds(a1["oof"], permuted_labels(b.co, p, "stage"))["mean"] for p in range(1, P_a + 1)]
    # sensitivity 0-2 vs >=13 months: children outside both sets are dropped; permutation within that subset
    sens = [c for c in b.E if b.ch.loc[c, "new02"] == 1 or b.ch.loc[c, "stage"] == 1]
    A1_sens = b.auc_seeds(a1["oof"], stage, sens)
    ys = np.array([stage[c] for c in sens])
    null_s = []
    for p in range(1, P_a + 1):
        perm = dict(zip(sens, ys[np.random.default_rng(stable_int("pf_sens", p)).permutation(len(ys))]))
        null_s.append(b.auc_seeds(a1["oof"], perm, sens)["mean"])
    tmpl = {f"{s}_{k}": b.templates(s, k) for s, k in b.units}
    out["a1"] = {"auc": A1, "perm_p": st.perm_p(A1["mean"], null_a1), "ci": b.boot_auc(a1["oof"], stage),
                 "strict_single_draw": b.auc_seeds(a1s["oof"], stage),
                 "sens_0_2_vs_13": {**A1_sens, "perm_p": st.perm_p(A1_sens["mean"], null_s), "n": len(sens)},
                 "templates": {key: {"early": v[3], "late": v[4]} for key, v in tmpl.items()}}
    # ---------------- (a2)
    a2 = b.a2_scores(stage)
    A2 = b.auc_seeds(a2, stage)
    null_a2 = []
    for p in range(1, P_a + 1):
        lab = permuted_labels(b.co, p, "stage")
        null_a2.append(b.auc_seeds(b.a2_scores(lab), lab)["mean"])
    out["a2"] = {"auc": A2, "perm_p": st.perm_p(A2["mean"], null_a2)}
    # ---------------- (b)
    bb = b.b_scores(stage)
    B_ = b.auc_seeds(bb["oof"], stage)
    null_b = [read_json(p)["auc"] for p in sorted(private_dir(config, args.perm_b_run).glob("p*.json"))] if not blind else []
    out["b"] = {"auc": B_, "perm_p": st.perm_p(B_["mean"], null_b) if null_b else None, "n_perm": len(null_b),
                "ci": b.boot_auc(bb["oof"], stage), "strict_single_draw": b.auc_seeds(b.b_scores(stage, strict=True)["oof"], stage),
                "C_chosen": pd.Series([v["C"] for v in bb["info"].values()]).value_counts().to_dict()}
    bdev = b.b_scores(stage, kind="dev")
    bstd = b.b_scores(stage, kind="std")
    out["b_dev"] = {"auc": b.auc_seeds(bdev["oof"], stage)}
    out["b_std"] = {"auc": b.auc_seeds(bstd["oof"], stage)}
    out["b_dev_minus_std"] = {"diff": out["b_dev"]["auc"]["mean"] - out["b_std"]["auc"]["mean"],
                              "ci": b.boot_diff(bdev["oof"], bstd["oof"], stage)}
    # addendum A5 (post-hoc, exploratory): permutation nulls of the condition-specific aggregates
    pdir = private_dir(config, "perm_bdev_001")
    if not blind and b.embed_source == "mo" and pdir.exists():
        rows = [read_json(p) for p in sorted(pdir.glob("p*.json"))]
        if rows:
            dv = np.array([r["auc_dev"] for r in rows])
            sv = np.array([r["auc_std"] for r in rows])
            obs_std = out["b_std"]["auc"]["mean"]
            out["a5_perm"] = {"n": len(rows), "p_dev": st.perm_p(out["b_dev"]["auc"]["mean"], dv),
                              "p_std_lower_tail": float((1 + np.sum(sv <= obs_std + 1e-12)) / (1 + len(sv))),
                              "p_diff": st.perm_p(out["b_dev_minus_std"]["diff"], dv - sv)}
    # ---------------- (c)
    cres = {}
    for v in ("rec", "bc", "rec_dev", "rec_std"):
        c = b.c_scores(v)
        if c is None:
            cres[v] = None
            continue
        cres[v] = c
        entry = {"auc": b.auc_seeds(c["oof"], stage), "strict_single_draw": b.auc_seeds(b.c_scores(v, strict=True)["oof"], stage)}
        if v in ("rec", "bc") and not blind:
            null = []
            for p in range(1, int(cfg(config, "stats.perm_c")) + 1):
                cp = b.c_scores(v, p)
                if cp is not None:
                    null.append(b.auc_seeds(cp["oof"], permuted_labels(b.co, p, "stage"))["mean"])
            entry.update(perm_p=st.perm_p(entry["auc"]["mean"], null) if null else None, n_perm=len(null))
        out[f"c_{v}"] = entry
    if cres.get("rec") and cres.get("bc"):
        out["c_rec_minus_bc"] = {"diff": out["c_rec"]["auc"]["mean"] - out["c_bc"]["auc"]["mean"],
                                 "ci": b.boot_diff(cres["rec"]["oof"], cres["bc"]["oof"], stage)}
    # ---------------- baselines
    out["background"] = background_models(b, stage, a1, bb)
    # ---------------- H3 (b remove-and-retrain; c test-only)
    names = list(b.units[next(iter(b.units))]["occl_names"])
    h3 = {}
    for o, name in enumerate(names):
        h3[name] = B_["mean"] - b.auc_seeds(b.b_scores(stage, occl=o)["oof"], stage)["mean"]
    out["h3_b_drop"] = h3
    if cres.get("rec"):
        out["h3_c_drop"] = c_occlusion(b, stage, names)
    # ---------------- H5
    out["h5"] = h5_nh(b, a1, bb, cres, stage)
    # ---------------- H6
    out["h6"] = h6_pairs(b, a1, stage)
    # ---------------- H9 + all-children report
    out["h9"], priv["child_report"] = h9_report(b, config)
    # ---------------- SI line (H11-H15)
    out["si"], priv["si"] = si_line(b, config, args, stage, sir, a1, blind)
    # ---------------- linear baseline and descriptive stimulus AUC
    out["stimulus"] = stimulus_descriptives(b)
    priv["a1_oof"] = {str(s): {str(c): v for c, v in d.items()} for s, d in a1["oof"].items()}
    priv["b_oof"] = {str(s): {str(c): v for c, v in d.items()} for s, d in bb["oof"].items()}
    return {"public": out, "private": priv}


def background_models(b: B1, stage, a1, bb) -> dict:
    grid = cfg(b.config, "stats.logistic_C")
    feats = np.load(b.feat_dir / "features.npz")
    pre = feats["prestim"]
    rec = b.co.rec.set_index("rec")
    tech_cols = ["record_scale", "n_acc", "accept_fraction", "d1_seconds", "qc_over_mean"]

    def tech(c):
        return rec.loc[b.primary[c], tech_cols].to_numpy(float)

    def bg_rows(cs, med):
        rows = []
        for c in cs:
            pta = b.ch.loc[c, "pta_unaided"]
            miss = float(not np.isfinite(pta))
            rows.append(np.concatenate([[b.ch.loc[c, "age_months"], med if miss else pta, miss], tech(c)]))
        return np.array(rows, float)

    res = {"stage_background": {}, "h2_background": {}, "a1_plus_background": {}, "b_plus_background": {}}
    oofs = {k: {} for k in res}
    for s in b.seeds:
        for k2 in oofs:
            oofs[k2][s] = {}
        for k in range(b.n_outer):
            tr, te = b.train_children(s, k, b.E), b.test_children(s, k, b.E)
            ptas = np.array([b.ch.loc[c, "pta_unaided"] for c in tr], float)
            med = float(np.nanmedian(ptas))
            Xtr, Xte = bg_rows(tr, med), bg_rows(te, med)
            y = np.array([stage[c] for c in tr]).astype(int)
            f, _ = st.logistic_cv(Xtr, y, grid, seed=s * 10 + k)
            oofs["stage_background"][s].update(dict(zip(te, f(Xte).tolist())))
            P = lambda cs: np.array([np.concatenate([tech(c), pre[b.primary[c]].ravel()]) for c in cs])  # noqa: E731
            f, _ = st.logistic_cv(P(tr), y, grid, seed=s * 10 + k)
            oofs["h2_background"][s].update(dict(zip(te, f(P(te)).tolist())))
            w_tr = a1["train"][(s, k)]
            ok = [c for c in tr if c in w_tr and np.isfinite(w_tr[c])]
            okt = [c for c in te if c in a1["oof"][s] and np.isfinite(a1["oof"][s][c])]
            Xa = np.column_stack([bg_rows(ok, med), [w_tr[c] for c in ok]])
            f, _ = st.logistic_cv(Xa, np.array([stage[c] for c in ok]).astype(int), grid, seed=s * 10 + k)
            oofs["a1_plus_background"][s].update(dict(zip(okt, f(np.column_stack([bg_rows(okt, med), [a1["oof"][s][c] for c in okt]])).tolist())))
            nb = b.b_train_crossfit(s, k, stage)
            okb = [c for c in tr if c in nb]
            Xb = np.column_stack([bg_rows(okb, med), [nb[c] for c in okb]])
            f, _ = st.logistic_cv(Xb, np.array([stage[c] for c in okb]).astype(int), grid, seed=s * 10 + k)
            oofs["b_plus_background"][s].update(dict(zip(te, f(np.column_stack([Xte, [bb["oof"][s][c] for c in te]])).tolist())))
    # exploratory (addendum A3, post-hoc): does w_late add to age alone? nested logistic, same folds
    for key in ("age_lr", "age_plus_a1"):
        oofs[key] = {}
    for s in b.seeds:
        oofs["age_lr"][s], oofs["age_plus_a1"][s] = {}, {}
        for k in range(b.n_outer):
            w_tr = a1["train"][(s, k)]
            tr = [c for c in b.train_children(s, k, b.E) if c in w_tr and np.isfinite(w_tr[c])]
            te = [c for c in b.test_children(s, k, b.E) if c in a1["oof"][s] and np.isfinite(a1["oof"][s][c])]
            y = np.array([stage[c] for c in tr]).astype(int)
            A = lambda cs: np.array([[b.ch.loc[c, "age_months"]] for c in cs], float)  # noqa: E731
            f, _ = st.logistic_cv(A(tr), y, grid, seed=s * 10 + k)
            oofs["age_lr"][s].update(dict(zip(te, f(A(te)).tolist())))
            Xtr = np.column_stack([A(tr), [w_tr[c] for c in tr]])
            Xte = np.column_stack([A(te), [a1["oof"][s][c] for c in te]])
            f, _ = st.logistic_cv(Xtr, y, grid, seed=s * 10 + k)
            oofs["age_plus_a1"][s].update(dict(zip(te, f(Xte).tolist())))
    res["exploratory_age_lr"] = b.auc_seeds(oofs["age_lr"], stage)
    res["exploratory_age_plus_a1"] = b.auc_seeds(oofs["age_plus_a1"], stage)
    res["exploratory_age_plus_a1_minus_age_ci"] = b.boot_diff(oofs["age_plus_a1"], oofs["age_lr"], stage)
    for k2 in ("stage_background", "h2_background", "a1_plus_background", "b_plus_background"):
        res[k2] = b.auc_seeds(oofs[k2], stage)
    res["age_only_auc"] = b.auc_seeds({s: {c: b.ch.loc[c, "age_months"] for c in b.E} for s in b.seeds}, stage)
    return res


def c_occlusion(b: B1, stage, names) -> dict:
    per = {n: [] for n in names}
    base = []
    for s in b.seeds:
        sc, occ = {}, {n: {} for n in names}
        for k in range(b.n_outer):
            with np.load(b.e2e_dir / "rec" / f"p000_s{s}_k{k}.npz", allow_pickle=False) as z:
                recs, scores, osc = z["occl_recs"], z["scores"], z["occl_scores"]
                rid_to_score = {int(r): float(v) for r, v in zip(z["recs"], z["scores"].mean(1))}
            child_of = b.co.rec.child.to_numpy()
            for i, r in enumerate(recs):
                c = int(child_of[int(r)])
                sc[c] = rid_to_score[int(r)]
                for j, n in enumerate(names):
                    occ[n][c] = float(osc[j, i])
        cs = [c for c in b.E if c in sc]
        a0 = st.auc([stage[c] for c in cs], [sc[c] for c in cs])
        base.append(a0)
        for n in names:
            per[n].append(a0 - st.auc([stage[c] for c in cs], [occ[n][c] for c in cs]))
    return {n: float(np.mean(v)) for n, v in per.items()} | {"_base_auc": float(np.mean(base))}


def h5_nh(b: B1, a1, bb, cres, stage) -> dict:
    from scipy.special import expit
    out = {}
    # (a1): balanced 1-D logistic of stage on cross-fitted training w_late, applied to NH test children
    P = {c: [] for c in b.NH}
    for s in b.seeds:
        for k in range(b.n_outer):
            tr = {c: v for c, v in a1["train"][(s, k)].items() if np.isfinite(v)}
            X = np.array([[v] for v in tr.values()])
            y = np.array([stage[c] for c in tr]).astype(int)
            m = st.logistic_fit(X, y, C=1e4)
            for c in b.test_children(s, k, b.NH):
                v = a1["oof"][s].get(c)
                if v is not None and np.isfinite(v):
                    P[c].append(float(m.predict_proba([[v]])[0, 1]))
    pa = {c: float(np.mean(v)) for c, v in P.items() if v}
    out["a1"] = {"median": float(np.median(list(pa.values()))) if pa else None,
                 "n_below_half": int(sum(v < 0.5 for v in pa.values())), "n": len(pa)}
    pb = b.child_mean({s: {c: float(expit(v)) for c, v in bb["oof"][s].items()} for s in b.seeds}, b.NH)
    out["b"] = {"median": float(np.median(list(pb.values()))), "n_below_half": int(sum(v < 0.5 for v in pb.values())), "n": len(pb)}
    if cres.get("rec"):
        c = cres["rec"]
        pc = {}
        for ch_ in b.NH:
            vals = []
            for s in b.seeds:
                k = b.fold_of(s)[ch_]
                if ch_ in c["oof"][s]:
                    vals.append(float(expit(c["oof"][s][ch_] - c["prior"][(s, k)])))
            if vals:
                pc[ch_] = float(np.mean(vals))
        out["c_rec"] = {"median": float(np.median(list(pc.values()))) if pc else None,
                        "n_below_half": int(sum(v < 0.5 for v in pc.values())), "n": len(pc)}
    return out


def h6_pairs(b: B1, a1, stage) -> dict:
    score = b.child_mean(a1["oof"], b.E)
    pairs = [(p["new_child"], p["exp_child"]) for p in b.co.mapped["pairs"]]
    usable = [(n, e) for n, e in pairs if n in score and e in score and np.isfinite(score[n]) and np.isfinite(score[e])]
    diffs = [score[e] - score[n] for n, e in usable]
    age = st.spearman([score[c] for c in b.E], [b.ch.loc[c, "age_months"] for c in b.E])
    s1 = [c for c in b.E if stage[c] == 1]
    return {"pairs_total": len(pairs), "pairs_usable": len(usable), "exp_higher": int(sum(d > 0 for d in diffs)),
            "mean_diff_exp_minus_new": float(np.mean(diffs)) if diffs else None, "rho_score_age": age,
            "within_stage1": {"rho_fitting_age": st.spearman([score[c] for c in s1], [b.ch.loc[c, "fitting_age"] for c in s1]),
                              "rho_duration": st.spearman([score[c] for c in s1], [b.ch.loc[c, "duration_months"] for c in s1])}}


def h9_report(b: B1, config) -> tuple[dict, list]:
    ens = ensemble_trial_scores(b)
    late = [int(np.flatnonzero(np.isclose(b.centres, c))[0]) for c in cfg(config, "windows.late_centres_s")]
    occ_late = [ensemble_occ_scores(b, w) for w in late]
    rng = np.random.default_rng(stable_int("pf_h9"))
    rows = []
    for c in b.co.ch.child.astype(int):
        r = b.primary[c]
        idx = np.flatnonzero(b.co.t_record == r)
        y, sc, on = b.co.t_y[idx], ens[idx], b.co.t_onset[idx]
        if not np.isfinite(sc).all():
            continue
        cat = three_category(y, sc, on, config, rng)
        base = st.auc(y, sc)
        drop_late = float(np.mean([base - st.auc(y, o[idx]) for o in occ_late]))
        rows.append({"child": c, "group": b.ch.loc[c, "group"], "stage": b.ch.loc[c, "stage"], "auc_full": base,
                     "drop_late": drop_late, **cat})
    rep = pd.DataFrame(rows)
    low = [c for c in b.co.mapped["low_auc_children"] if c is not None]
    L = rep[rep.child.isin(low)]
    opp = L[L.category == "opposite"]
    out = {"n_low": int(len(L)), "categories_low": L.category.value_counts().to_dict(),
           "opposite_late_negative": int((opp.drop_late < 0).sum()), "n_opposite": int(len(opp)),
           "population_drop_late_mean": float(rep.drop_late.mean()),
           "categories_all": rep.category.value_counts().to_dict(),
           "categories_by_group": {g: d.category.value_counts().to_dict() for g, d in rep.groupby("group")},
           "low_auc_full_below_half_now": int((L.auc_full < 0.5).sum())}
    return out, rep.to_dict("records")


def si_line(b: B1, config, args, stage, sir, a1, blind: bool) -> tuple[dict, dict]:
    out, priv = {}, {}
    full = b_ord_scores(b, sir, crossfit_train=True)
    ev = si_eval(b, full["latent"], full["expected"], sir)
    out["h11_b_ord"] = ev
    # c-ord (secondary)
    c = b.c_scores("ord")
    if c is not None:
        high = {k: float(v > 3) for k, v in sir.items()}
        out["h11_c_ord"] = {"auc_sir_gt3": b.auc_seeds(c["oof"], high)}
    # H12
    if not blind:
        sh = [read_json(p) for p in sorted(private_dir(config, args.shuffle_run).glob("*.json"))]
        res = {}
        for strata in ("stage", "bins4"):
            vals = [x for x in sh if x["strata"] == strata]
            if not vals:
                continue
            A = np.array([x["auc"] for x in vals])
            M = np.array([x["mae"] for x in vals])
            res[strata] = {"n": len(vals), "auc_shuffled_mean": float(A.mean()), "mae_shuffled_mean": float(M.mean()),
                           "delta_auc": ev["auc_sir_gt3"]["mean"] - float(A.mean()),
                           "delta_mae": float(M.mean()) - ev["mae"]["mean"],
                           "p_auc": st.perm_p(ev["auc_sir_gt3"]["mean"], A),
                           "p_mae": float((1 + np.sum(M <= ev["mae"]["mean"] + 1e-12)) / (1 + len(M)))}
        out["h12"] = res
    # H13: (a1) stage score -> SIR
    one = one_d_ordinal(b, a1["train"], a1["oof"], sir)
    ev13 = si_eval(b, one["latent"], one["expected"], sir)
    full_auc = ev["auc_sir_gt3"]["mean"]
    out["h13"] = {"auc_stage_score": ev13["auc_sir_gt3"], "mae_stage_score": ev13["mae"], "auc_full": full_auc,
                  "skill_ratio": (ev13["auc_sir_gt3"]["mean"] - 0.5) / (full_auc - 0.5) if full_auc > 0.5 else None}
    # (b) stage score as secondary
    btrain = {(s, k): b.b_train_crossfit(s, k, stage) for s, k in b.units}
    bstage = b.b_scores(stage)["oof"]
    one_b = one_d_ordinal(b, btrain, bstage, sir)
    ev13b = si_eval(b, one_b["latent"], one_b["expected"], sir)
    out["h13_b_stage_score"] = {"auc": ev13b["auc_sir_gt3"], "skill_ratio": (ev13b["auc_sir_gt3"]["mean"] - 0.5) / (full_auc - 0.5)
                                if full_auc > 0.5 else None}
    # H14
    hm = h14_models(b, sir, full["train_latent"], full["latent"])
    errC = b.child_mean({s: {c: abs(hm["C"][1][s][c] - sir[c]) for c in hm["C"][1][s]} for s in b.seeds}, b.E)
    errCZ = b.child_mean({s: {c: abs(hm["CZ"][1][s][c] - sir[c]) for c in hm["CZ"][1][s]} for s in b.seeds}, b.E)
    d = np.array([errC[c] - errCZ[c] for c in b.E])
    rng = np.random.default_rng(stable_int("pf_h14"))
    boots = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(int(cfg(config, "stats.bootstrap")))]
    high = {k: float(v > 3) for k, v in sir.items()}
    out["h14"] = {"mae_C": float(np.mean(list(errC.values()))), "mae_CZ": float(np.mean(list(errCZ.values()))),
                  "delta": float(d.mean()), "ci": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                  "auc_C": b.auc_seeds(hm["C"][0], high), "auc_CZ": b.auc_seeds(hm["CZ"][0], high)}
    # H15
    score = b.child_mean(a1["oof"], b.E)
    res15 = {}
    for name, (lo, hi) in (("12_24", cfg(config, "labels.h15_stratum")), ("12_36", cfg(config, "labels.h15_sensitivity"))):
        cs = [c for c in b.E if lo <= b.ch.loc[c, "duration_months"] <= hi]
        hi_ = [score[c] for c in cs if sir[c] > 3]
        lo_ = [score[c] for c in cs if sir[c] <= 3]
        dlt = st.cliff_delta(hi_, lo_)
        rng = np.random.default_rng(stable_int("pf_h15", name))
        bs = [st.cliff_delta(rng.choice(hi_, len(hi_)), rng.choice(lo_, len(lo_))) for _ in range(2000)] if hi_ and lo_ else []
        res15[name] = {"n_high": len(hi_), "n_low": len(lo_), "delta": dlt,
                       "ci": [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))] if bs else None}
    out["h15"] = res15
    # MUSS (secondary): ridge on (b) features
    muss = {c: float(b.ch.loc[c, "muss"]) for c in b.E}
    if blind:
        muss = permuted_labels(b.co, 1, "muss")
    pred = {}
    for s in b.seeds:
        pred[s] = {}
        for k in range(b.n_outer):
            tr, te = b.train_children(s, k, b.E), b.test_children(s, k, b.E)
            f, _ = st.ridge_cv(np.stack([b.features(s, k, c) for c in tr]), np.array([muss[c] for c in tr]),
                               cfg(config, "stats.ridge_alpha"), seed=s * 10 + k)
            pred[s].update(dict(zip(te, f(np.stack([b.features(s, k, c) for c in te])).tolist())))
    pm = b.child_mean(pred, b.E)
    out["muss_b_ridge"] = {"mae": float(np.mean([abs(pm[c] - muss[c]) for c in b.E])),
                           "mae_train_mean_baseline": float(np.mean([abs(np.mean([muss[x] for x in b.E if x != c]) - muss[c]) for c in b.E])),
                           "spearman": st.spearman([pm[c] for c in b.E], [muss[c] for c in b.E])}
    priv["h14_err"] = {"C": errC, "CZ": errCZ}
    return out, priv


def stimulus_descriptives(b: B1) -> dict:
    ens = ensemble_trial_scores(b)
    lin = ensemble_trial_scores(b, "diff_lin")
    rows = []
    for c in b.co.ch.child.astype(int):
        idx = np.flatnonzero(b.co.t_record == b.primary[c])
        y = b.co.t_y[idx]
        rows.append({"child": c, "eegnet": st.auc(y, ens[idx]), "linear": st.auc(y, lin[idx])})
    t = pd.DataFrame(rows)
    per_seed = []
    for s in b.seeds:
        vals = []
        for k in range(b.n_outer):
            u = b.units[(s, k)]
            for c in u["test_children"]:
                idx = np.flatnonzero(b.co.t_record == b.primary[int(c)])
                vals.append((st.auc(b.co.t_y[idx], u["diff_base"][idx]), st.auc(b.co.t_y[idx], u["diff_lin"][idx])))
        v = np.array(vals)
        per_seed.append(v.mean(0))
    ps = np.array(per_seed)
    return {"eegnet_child_mean_auc_seedmean": float(ps[:, 0].mean()), "linear_child_mean_auc_seedmean": float(ps[:, 1].mean()),
            "eegnet_per_seed": ps[:, 0].tolist(), "linear_per_seed": ps[:, 1].tolist(),
            "ensemble_eegnet_child_mean": float(t.eegnet.mean()), "ensemble_linear_child_mean": float(t.linear.mean()),
            "children_linear_better": int((t.linear > t.eegnet).sum()), "n_children": int(len(t))}


# ============================================================================ B2

def analyze_b2(config, args, blind: bool) -> dict:
    b = B1(config, prepare_run=args.prepare_run, stim_run=args.stim_run, embed_source=args.embed_source)
    stage, _ = _labels(b, blind)
    b2dir = private_dir(config, args.b2_run)
    child_of_trial = b.co.rec.child.to_numpy()[b.co.t_record]
    names = ["blind", "heads_stage", "film_stage"] + [f"heads_rand{r}" for r in range(int(cfg(config, "b2.random_draws")))] \
        + [f"film_rand{r}" for r in range(int(cfg(config, "b2.random_draws")))]
    auc = {n: {c: [] for c in b.E} for n in names}
    diffs = {n: {} for n in ("blind", "heads_stage")}
    for s in b.seeds:
        for k in range(b.n_outer):
            for n in names:
                p = b2dir / f"unit_s{s}_k{k}" / f"{n}.npz"
                if not p.exists():
                    continue
                with np.load(p, allow_pickle=False) as z:
                    idx, d = z["idx"], z["diff"]
                ch_ = child_of_trial[idx]
                for c in np.unique(ch_):
                    if int(c) in auc[n]:
                        m = ch_ == c
                        auc[n][int(c)].append(st.auc(b.co.t_y[idx[m]], d[m]))
                        if n in diffs:
                            diffs[n].setdefault(int(c), []).append((idx[m], d[m]))
    mean = {n: {c: float(np.mean(v)) for c, v in auc[n].items() if v} for n in names}
    S0 = [c for c in b.E if stage[c] == 0]
    S1 = [c for c in b.E if stage[c] == 1]

    def gain(model, group):
        return float(np.mean([mean[model][c] - mean["blind"][c] for c in group if c in mean[model] and c in mean["blind"]]))
    R = int(cfg(config, "b2.random_draws"))
    out = {"n_stage0": len(S0), "n_stage1": len(S1)}
    for fam in ("heads", "film"):
        g_new, g_exp = gain(f"{fam}_stage", S0), gain(f"{fam}_stage", S1)
        g_rand = float(np.mean([gain(f"{fam}_rand{r}", S0) for r in range(R)]))
        g_rand_exp = float(np.mean([gain(f"{fam}_rand{r}", S1) for r in range(R)]))
        dd = np.array([mean[f"{fam}_stage"][c] - mean["blind"][c] for c in S0])
        rng = np.random.default_rng(stable_int("pf_h7", fam))
        bs = [dd[rng.integers(0, len(dd), len(dd))].mean() for _ in range(2000)]
        out[fam] = {"g_new": g_new, "g_exp": g_exp, "g_rand_new": g_rand, "g_rand_exp": g_rand_exp,
                    "g_new_ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                    "g_rand_new_each": [gain(f"{fam}_rand{r}", S0) for r in range(R)]}
    out["blind_mean_auc"] = float(np.mean(list(mean["blind"].values())))
    # H8 (stim run: M_13 vs M_o on >=13-month test children)
    per = {c: ([], []) for c in S1}
    for (s, k), u in b.units.items():
        for c in u["test_children"]:
            c = int(c)
            if c in per:
                idx = np.flatnonzero(b.co.t_record == b.primary[c])
                per[c][0].append(st.auc(b.co.t_y[idx], u["diff_13"][idx]))
                per[c][1].append(st.auc(b.co.t_y[idx], u["diff_base"][idx]))
    d8 = np.array([np.mean(v[0]) - np.mean(v[1]) for v in per.values() if v[0]])
    rng = np.random.default_rng(stable_int("pf_h8"))
    bs = [d8[rng.integers(0, len(d8), len(d8))].mean() for _ in range(2000)]
    out["h8"] = {"delta": float(d8.mean()), "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "n": int(len(d8)),
                 "m13_mean": float(np.mean([np.mean(v[0]) for v in per.values() if v[0]])),
                 "mo_mean": float(np.mean([np.mean(v[1]) for v in per.values() if v[1]]))}
    # H10: undetermined fraction, stage-blind vs stage-heads (ensembles over seeds)
    rng = np.random.default_rng(stable_int("pf_h10"))
    cats = {}
    for n in ("blind", "heads_stage"):
        cnt = {"consistent": 0, "opposite": 0, "undetermined": 0}
        for c in b.E:
            if c not in diffs[n]:
                continue
            idx = diffs[n][c][0][0]
            sc = np.mean([d for _, d in diffs[n][c]], 0)
            res = three_category(b.co.t_y[idx], sc, b.co.t_onset[idx], config, rng)
            cnt[res["category"]] += 1
        cats[n] = cnt
    ub, uh = cats["blind"]["undetermined"], cats["heads_stage"]["undetermined"]
    out["h10"] = {"categories": cats, "relative_reduction": (ub - uh) / ub if ub else None}
    return out


# ============================================================================ B3

def analyze_b3(config, args, blind: bool) -> dict:
    b = B1(config, prepare_run=args.prepare_run, stim_run=args.stim_run, embed_source=args.embed_source)
    stage, _ = _labels(b, blind)
    age = {c: float(b.ch.loc[c, "age_months"]) for c in b.E}
    if blind:
        age = permuted_labels(b.co, 1, "age_months")
    feats = np.load(private_dir(config, args.features_run) / "features.npz")
    cont = feats["cont"]
    out = {}
    # H16/H17
    reps = {"cont": lambda s, k, c: cont[b.primary[c]].ravel(), "event": lambda s, k, c: b.features(s, k, c),
            "joint": lambda s, k, c: np.concatenate([cont[b.primary[c]].ravel(), b.features(s, k, c)])}
    kids = [c for c in b.E if np.isfinite(cont[b.primary[c]]).all()]
    pred_age, pred_stage = {}, {}
    for name, fn in reps.items():
        pa, ps = {}, {}
        for s in b.seeds:
            pa[s], ps[s] = {}, {}
            for k in range(b.n_outer):
                tr = [c for c in b.train_children(s, k, kids)]
                te = [c for c in b.test_children(s, k, kids)]
                X = np.stack([fn(s, k, c) for c in tr])
                Xt = np.stack([fn(s, k, c) for c in te])
                f, _ = st.ridge_cv(X, np.array([age[c] for c in tr]), cfg(config, "stats.ridge_alpha"), seed=s * 10 + k)
                pa[s].update(dict(zip(te, f(Xt).tolist())))
                g, _ = st.logistic_cv(X, np.array([stage[c] for c in tr]).astype(int), cfg(config, "stats.logistic_C"), seed=s * 10 + k)
                ps[s].update(dict(zip(te, g(Xt).tolist())))
        pred_age[name], pred_stage[name] = pa, ps
    err = {n: b.child_mean({s: {c: abs(pred_age[n][s][c] - age[c]) for c in kids} for s in b.seeds}, kids) for n in reps}
    mae = {n: float(np.mean(list(err[n].values()))) for n in reps}
    aucs = {n: b.auc_seeds(pred_stage[n], stage, kids) for n in reps}
    rng = np.random.default_rng(stable_int("pf_h16"))
    B = int(cfg(config, "stats.bootstrap"))
    y = np.array([stage[c] for c in kids])
    S = {n: np.array([[pred_stage[n][s][c] for c in kids] for s in b.seeds]) for n in reps}
    E_ = {n: np.array([err[n][c] for c in kids]) for n in reps}
    bs = {"D_age": [], "D_stage": [], "stage_gain": [], "age_gain": []}
    for _ in range(B):
        i = rng.integers(0, len(kids), len(kids))
        au = {n: np.nanmean([st.auc(y[i], S[n][j, i]) for j in range(len(b.seeds))]) for n in reps}
        bs["D_age"].append(E_["event"][i].mean() - E_["cont"][i].mean())
        bs["D_stage"].append(au["event"] - au["cont"])
        bs["stage_gain"].append(au["joint"] - au["event"])
        bs["age_gain"].append(E_["cont"][i].mean() - E_["joint"][i].mean())
    ci = {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] for k, v in bs.items()}
    mean_age_baseline = float(np.mean([abs(np.mean([age[x] for x in kids if x != c]) - age[c]) for c in kids]))
    out["h16_h17"] = {"n": len(kids), "mae": mae, "auc": aucs, "mae_mean_baseline": mean_age_baseline,
                      "D_age": mae["event"] - mae["cont"], "D_stage": aucs["event"]["mean"] - aucs["cont"]["mean"],
                      "stage_gain": aucs["joint"]["mean"] - aucs["event"]["mean"], "age_gain": mae["cont"] - mae["joint"], "ci": ci}
    # H18
    h18 = private_dir(config, args.b3_run) / "h18"
    if h18.exists():
        rows = []
        for p in sorted(h18.glob("*.npz")):
            with np.load(p) as z:
                rows.append({"file": p.stem, "mean_auc": float(np.nanmean(z["auc"])), "panel": z["panel"].tolist(), "auc": z["auc"].tolist(),
                             "n_children": int(z["n_children"]), "per_child": int(z["per_child"]), "n_eligible": int(z["n_eligible"])})
        t = pd.DataFrame(rows)
        t["key"] = t.file.str.replace(r"_a\d$", "", regex=True)
        t["alloc"] = t.file.str[-1].astype(int)
        piv = t.pivot(index="key", columns="alloc", values="auc")
        diffs = np.concatenate([np.array(a0) - np.array(a1) for a0, a1 in zip(piv[0], piv[1])])
        rng = np.random.default_rng(stable_int("pf_h18"))
        bs18 = [np.nanmean(diffs[rng.integers(0, len(diffs), len(diffs))]) for _ in range(2000)]
        out["h18"] = {"delta_60x450_minus_30x900": float(np.nanmean(diffs)), "ci": [float(np.nanpercentile(bs18, 2.5)), float(np.nanpercentile(bs18, 97.5))],
                      "mean_auc_60x450": float(t[t.alloc == 0].mean_auc.mean()), "mean_auc_30x900": float(t[t.alloc == 1].mean_auc.mean()),
                      "units": int(len(t)), "n_children_used": t.groupby("alloc").n_children.min().to_dict(),
                      "eligible_min": t.groupby("alloc").n_eligible.min().to_dict()}
    # H19
    out["h19"] = h19_endpoint(b, config)
    # H20
    h20 = private_dir(config, args.b3_run) / "h20"
    if h20.exists():
        rows = []
        for p in h20.glob("*.npz"):
            with np.load(p) as z:
                rows.append({"child": int(z["child"]), "n": int(z["n"]), "seed": int(z["seed"]), "auc": float(z["auc"])})
        t = pd.DataFrame(rows).groupby(["child", "n"]).auc.mean().unstack()
        sizes = cfg(config, "b3.h20_sizes")
        g1 = (t[sizes[1]] - t[sizes[0]]).dropna()
        g2 = (t[sizes[2]] - t[sizes[1]]).dropna()
        rng = np.random.default_rng(stable_int("pf_h20"))
        bs2 = [g2.to_numpy()[rng.integers(0, len(g2), len(g2))].mean() for _ in range(2000)]
        out["h20"] = {"mean_auc": {int(n): float(t[n].mean()) for n in sizes}, "gain_40_60": float(g1.mean()),
                      "gain_60_72": float(g2.mean()), "gain_60_72_ci": [float(np.percentile(bs2, 2.5)), float(np.percentile(bs2, 97.5))],
                      "children": int(len(t))}
    return out


def h19_endpoint(b: B1, config) -> dict:
    ens = ensemble_trial_scores(b)
    pre = ensemble_trial_scores(b, "diff_pre")
    first = 60.0 * float(cfg(config, "blocks.first_minutes"))
    guard = float(cfg(config, "blocks.guard_seconds"))
    rng = np.random.default_rng(stable_int("pf_h19"))
    n_perm = int(cfg(config, "stats.query_perm"))
    rows = []
    for r in b.co.rec[b.co.rec.source == "HA"].itertuples():
        idx = np.flatnonzero(b.co.t_record == int(r.rec))
        on = b.co.t_onset[idx] - b.co.t_onset[idx].min()
        y = b.co.t_y[idx]
        f5 = on + 0.6 <= first
        rest = on - 0.2 >= first + guard
        a5, p5 = st.two_sided_perm(y[f5], ens[idx][f5], n_perm, rng)
        ar = st.auc(y[rest], ens[idx][rest])
        ap, pp = st.two_sided_perm(y[f5], pre[idx][f5], n_perm, rng)
        rows.append({"rec": int(r.rec), "auc5": a5, "p5": p5, "auc_rest": ar, "agree": bool(np.sign(a5 - 0.5) == np.sign(ar - 0.5)),
                     "pre_auc5": ap, "pre_p5": pp, "n5": int(f5.sum()), "n_rest": int(rest.sum())})
    t = pd.DataFrame(rows)
    ok = (t.agree & (t.p5 < 0.05))
    return {"records": int(len(t)), "fraction_agree_and_sig": float(ok.mean()), "n_agree_and_sig": int(ok.sum()),
            "fraction_agree": float(t.agree.mean()), "fraction_sig": float((t.p5 < 0.05).mean()),
            "pre_false_positive_rate": float((t.pre_p5 < 0.05).mean()), "median_trials_first5": float(t.n5.median())}


# ============================================================================ claims

def claims(b1: dict, b2: dict, b3: dict) -> dict:
    C = {}
    a1 = b1["a1"]
    A, p = a1["auc"]["mean"], a1["perm_p"]
    C["H1"] = {"estimate": _r(A), "perm_p": _r(p, 4), "ci": a1["ci"],
               "status": status(supported=A >= 0.70 and p < 0.05, refuted=p > 0.05 and A < 0.60,
                                partial=(p < 0.05) != (A >= 0.70), direction=A > 0.5)}
    dA, bg = b1["b_dev_minus_std"]["diff"], b1["background"]["h2_background"]["mean"]
    sA, dvA = b1["b_std"]["auc"]["mean"], b1["b_dev"]["auc"]["mean"]
    clA, clB = dA >= 0.10, bg <= 0.60
    ref2 = (sA >= 0.65 and sA >= dvA - 0.03) or bg >= 0.65
    C["H2"] = {"dev_minus_std": _r(dA), "ci": b1["b_dev_minus_std"]["ci"], "background_auc": _r(bg),
               "status": status(supported=clA and clB, refuted=ref2, partial=clA != clB, direction=dA > 0)}
    base = b1["b"]["auc"]["mean"]
    drops = b1["h3_b_drop"]
    tnames = [n for n in drops if n.startswith("t+") or n.startswith("t-")]
    tv = np.array([drops[n] for n in tnames])
    cen = np.array([float(n[1:]) for n in tnames])
    target = tnames[int(np.argmin(np.abs(cen - 0.28)))]
    others = [drops[n] for n in tnames if n != target]
    clA3 = drops[target] > max(others)
    clB3 = drops["frontocentral"] > drops["lateral"]
    mx = tv.max()
    ref3 = cen[int(np.argmax(tv))] < 0 or (mx > 0 and int(np.sum(tv >= 0.5 * mx)) >= 5)
    C["H3"] = {"base_auc_b": _r(base), "target_drop": _r(drops[target], 4), "max_other_drop": _r(max(others), 4),
               "argmax_centre": float(cen[int(np.argmax(tv))]), "frontocentral": _r(drops["frontocentral"], 4), "lateral": _r(drops["lateral"], 4),
               "status": status(supported=clA3 and clB3, refuted=ref3, partial=clA3 != clB3, direction=drops[target] > np.median(tv),
                                not_evaluable="upstream_null" if base < 0.60 else None)}
    if "c_rec_minus_bc" in b1:
        d4 = b1["c_rec_minus_bc"]["diff"]
        C["H4"] = {"delta": _r(d4), "ci": b1["c_rec_minus_bc"]["ci"],
                   "status": status(supported=d4 >= 0.03, refuted=d4 < 0.01, direction=d4 > 0)}
    h5 = b1["h5"]["a1"]
    n5 = h5["n"]
    C["H5"] = {"median_P": _r(h5["median"]), "n_below_half": h5["n_below_half"], "n": n5,
               "status": status(supported=h5["median"] < 0.5 and h5["n_below_half"] >= 7, refuted=(n5 - h5["n_below_half"]) >= 6,
                                direction=h5["median"] < 0.5)}
    h6 = b1["h6"]
    frac = h6["exp_higher"] / max(h6["pairs_usable"], 1)
    rho = h6["rho_score_age"]["rho"]
    C["H6"] = {"exp_higher": f'{h6["exp_higher"]}/{h6["pairs_usable"]}', "rho_age": _r(rho),
               "status": status(supported=frac >= 10 / 13 and abs(rho) < 0.2, refuted=frac <= 8 / 13,
                                partial=(frac >= 10 / 13) != (abs(rho) < 0.2), direction=frac > 0.5)}
    h9 = b1["h9"]
    cats = h9["categories_low"]
    n_opp, n_und = cats.get("opposite", 0), cats.get("undetermined", 0)
    late_ok = h9["n_opposite"] > 0 and h9["opposite_late_negative"] > h9["n_opposite"] / 2
    C["H9"] = {"categories": cats, "opposite_late_negative": f'{h9["opposite_late_negative"]}/{h9["n_opposite"]}',
               "status": status(supported=n_opp >= 5 and late_ok, refuted=n_und >= 7, partial=n_opp >= 5 and not late_ok,
                                direction=n_opp > cats.get("consistent", 0))}
    si = b1["si"]
    a11 = si["h11_b_ord"]["auc_sir_gt3"]["mean"]
    C["H11"] = {"auc": _r(a11), "status": status(supported=a11 >= 0.65, refuted=a11 < 0.60, direction=a11 > 0.5)}
    if "h12" in si and "stage" in si["h12"]:
        h = si["h12"]["stage"]
        within = h["delta_auc"] <= 0.02 and h["delta_mae"] <= 0.1
        beyond = h["delta_auc"] > 0.02 or h["delta_mae"] > 0.1
        C["H12"] = {"delta_auc": _r(h["delta_auc"]), "delta_mae": _r(h["delta_mae"]), "p_auc": _r(h["p_auc"], 4),
                    "status": status(supported=within and h["p_auc"] >= 0.05, refuted=beyond and h["p_auc"] < 0.05,
                                     partial=within != (h["p_auc"] >= 0.05), direction=h["delta_auc"] <= 0.02)}
    h13 = si["h13"]
    ratio = h13["skill_ratio"]
    C["H13"] = {"auc_stage_score": _r(h13["auc_stage_score"]["mean"]), "auc_full": _r(h13["auc_full"]), "skill_ratio": _r(ratio),
                "status": status(supported=ratio is not None and ratio >= 0.8, refuted=ratio is not None and ratio < 0.5,
                                 direction=ratio is not None and ratio >= 0.5,
                                 not_evaluable="upstream_null" if h13["auc_full"] < 0.55 else None)}
    h14 = si["h14"]
    C["H14"] = {"delta": _r(h14["delta"]), "ci": [_r(v) for v in h14["ci"]],
                "status": status(supported=h14["ci"][1] < 0.5, refuted=h14["ci"][0] > 0, direction=h14["delta"] < 0.5)}
    h15 = si["h15"]["12_24"]
    C["H15"] = {"delta": _r(h15["delta"]), "n": f'{h15["n_high"]} vs {h15["n_low"]}',
                "status": status(supported=h15["delta"] > 0.3, refuted=h15["delta"] <= 0, direction=h15["delta"] > 0)}
    if b2:
        h = b2["heads"]
        sup7 = h["g_new"] >= 0.02 and h["g_exp"] >= 0 and h["g_rand_new"] < 0.01 and h["g_new"] - h["g_rand_new"] >= 0.01
        ref7 = h["g_new"] < 0.01 or abs(h["g_new"] - h["g_rand_new"]) < 0.01
        C["H7"] = {"g_new": _r(h["g_new"], 4), "g_exp": _r(h["g_exp"], 4), "g_rand_new": _r(h["g_rand_new"], 4),
                   "status": status(supported=sup7, refuted=ref7, partial=h["g_new"] >= 0.02, direction=h["g_new"] > h["g_rand_new"])}
        d8 = b2["h8"]["delta"]
        C["H8"] = {"delta": _r(d8, 4), "ci": b2["h8"]["ci"], "status": status(supported=d8 >= 0.01, refuted=d8 <= 0, direction=d8 > 0)}
        rr = b2["h10"]["relative_reduction"]
        C["H10"] = {"relative_reduction": _r(rr), "categories": b2["h10"]["categories"],
                    "status": status(supported=rr is not None and rr >= 1 / 3, refuted=rr is None or rr < 0.10, direction=rr is not None and rr > 0)}
    if b3:
        h = b3["h16_h17"]
        ci = h["ci"]
        sup16 = h["D_age"] > 0 and h["D_stage"] > 0 and ci["D_age"][0] > 0 and ci["D_stage"][0] > 0
        C["H16"] = {"D_age": _r(h["D_age"]), "D_stage": _r(h["D_stage"]), "ci": {k: ci[k] for k in ("D_age", "D_stage")},
                    "status": status(supported=sup16, refuted=h["D_age"] <= 0 or h["D_stage"] <= 0, direction=h["D_age"] > 0 and h["D_stage"] > 0)}
        sg, ag = h["stage_gain"], h["age_gain"]
        C["H17"] = {"stage_gain": _r(sg), "age_gain": _r(ag),
                    "status": status(supported=sg >= 0.02 and ag < 1, refuted=(sg >= 0.02 and ag >= 1) or (sg < 0.02 and ag < 1),
                                     direction=sg > 0)}
        if "h18" in b3:
            d = b3["h18"]["delta_60x450_minus_30x900"]
            C["H18"] = {"delta": _r(d, 4), "ci": b3["h18"]["ci"], "status": status(supported=d >= 0.01, refuted=d <= 0, direction=d > 0)}
        h19 = b3["h19"]
        f = h19["fraction_agree_and_sig"]
        C["H19"] = {"fraction": _r(f), "false_positive": _r(h19["pre_false_positive_rate"]),
                    "status": status(supported=f >= 2 / 3 and h19["pre_false_positive_rate"] <= 0.05, refuted=f < 0.5,
                                     partial=f >= 2 / 3, direction=f >= 0.5)}
        if "h20" in b3:
            g = b3["h20"]["gain_60_72"]
            C["H20"] = {"gain_60_72": _r(g, 4), "gain_40_60": _r(b3["h20"]["gain_40_60"], 4),
                        "status": status(supported=0 <= g <= 0.01, refuted=g < 0, partial=g > 0.01, direction=g >= 0)}
    return C


def cmd_analyze(args, config) -> dict:
    run = open_run("analyze", args.run, config, args=vars(args))
    blind = bool(args.blind)
    res1 = analyze_b1(config, args, blind)
    b2 = analyze_b2(config, args, blind) if args.b2_run else {}
    b3 = analyze_b3(config, args, blind) if args.b3_run else {}
    C = claims(res1["public"], b2, b3)
    tag = "blind" if blind else "real"
    write_json_atomic(run["private"] / f"private_{tag}.json", res1["private"], private=True)
    summary = {"b1": res1["public"], "b2": b2, "b3": b3, "claims": C}
    target = run["private"] if blind else run["public"]
    write_json_atomic(target / f"summary_{tag}.json", summary, private=blind)
    return {"claims": {k: v["status"] for k, v in C.items()}}


# ============================================================================ H14 three-world simulation (protocol 6.1)

def cmd_h14_sim(args, config) -> dict:
    """Run only if H14 is refuted: can the H14 control tell a replaceable Z from an informative one?"""
    run = open_run("h14_sim", args.run, config, args=vars(args))
    b = B1(config, prepare_run=args.prepare_run, stim_run=args.stim_run, embed_source=args.embed_source)
    sir = sir_labels(b)
    full = b_ord_scores(b, sir, crossfit_train=False)
    z_obs = b.child_mean(full["latent"], b.E)
    kids = np.array(b.E)
    Z = np.array([z_obs[c] for c in kids])
    Y = np.array([sir[c] for c in kids])
    S = np.array([b.stage[c] for c in kids])
    # residual of SIR given the clinical design (in-sample, used only to build world W2)
    Xc, _ = __import__("auditory_pf.analysis_b1", fromlist=["clinical_design"]).clinical_design(b, list(kids), list(kids))
    beta = np.linalg.lstsq(np.column_stack([np.ones(len(Y)), Xc]), Y, rcond=None)[0]
    resid = Y - np.column_stack([np.ones(len(Y)), Xc]) @ beta
    r_stage = abs(np.corrcoef(Z, S)[0, 1])
    r_y = abs(np.corrcoef(Z, Y)[0, 1])
    n_sim = int(args.n_sim)
    units = [(w, j) for w in ("W0", "W1", "W2") for j in range(n_sim)]
    rows = []
    for w, j in task_units(units):
        path = run["private"] / f"{w}_{j:04d}.json"
        if path.exists():
            continue
        rng = np.random.default_rng(stable_int("pf_h14sim", w, j))
        if w == "W0":
            zs = rng.permutation(Z)
        elif w == "W1":
            sig = (S - S.mean()) / S.std()
            zs = r_stage * sig + np.sqrt(max(1 - r_stage ** 2, 1e-6)) * rng.normal(size=len(S))
        else:
            sig = (resid - resid.mean()) / resid.std()
            zs = r_y * sig + np.sqrt(max(1 - r_y ** 2, 1e-6)) * rng.normal(size=len(S))
        zd = dict(zip(kids.astype(int), zs))
        z_train = {(s, k): {c: zd[c] for c in b.train_children(s, k, b.E)} for s, k in b.units}
        z_test = {s: zd for s in b.seeds}
        hm = h14_models(b, sir, z_train, z_test)
        errC = b.child_mean({s: {c: abs(hm["C"][1][s][c] - sir[c]) for c in hm["C"][1][s]} for s in b.seeds}, b.E)
        errCZ = b.child_mean({s: {c: abs(hm["CZ"][1][s][c] - sir[c]) for c in hm["CZ"][1][s]} for s in b.seeds}, b.E)
        d = np.array([errC[c] - errCZ[c] for c in b.E])
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        write_json_atomic(path, {"world": w, "j": j, "delta": float(d.mean()), "lower": float(np.percentile(bs, 2.5))}, private=True)
    return {"done": True}


# ============================================================================ addendum A5 (post-hoc, exploratory)

def cmd_perm_bdev(args, config) -> dict:
    """Full-pipeline permutation null for the condition-specific (b) aggregates (dev, std and their difference)."""
    run = open_run("perm_bdev", args.run, config, args=vars(args))
    b = B1(config, prepare_run=args.prepare_run, stim_run=args.stim_run, embed_source=args.embed_source)
    n = 0
    for p in task_units(list(range(1, int(cfg(config, "stats.perm_b")) + 1))):
        path = run["private"] / f"p{p:04d}.json"
        if path.exists():
            continue
        lab = permuted_labels(b.co, p, "stage")
        a_dev = b.auc_seeds(b.b_scores(lab, kind="dev")["oof"], lab)["mean"]
        a_std = b.auc_seeds(b.b_scores(lab, kind="std")["oof"], lab)["mean"]
        write_json_atomic(path, {"p": p, "auc_dev": a_dev, "auc_std": a_std}, private=True)
        n += 1
    return {"perms": n}
