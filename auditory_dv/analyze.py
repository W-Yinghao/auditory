"""DV analyses and claim states (docs/auditory_dv/DV_PROTOCOL_FROZEN.md): A1-A3, B, D (if audit passes), E, G."""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from auditory_pf import stats as st
from auditory_pf.analyze import status

from .mff import MffCohort
from .runtime import ROOT, cfg, open_run, private_dir, read_json, stable_int, write_json_atomic


# ============================================================================ shared helpers

def ridge_oof(X_tr, y_tr, X_te, grid, seed):
    f, info = st.ridge_cv(X_tr, y_tr, grid, seed=seed)
    return f(X_te), info


def inner_oof(X, y, grid, seed, n_splits=5):
    """Out-of-fold predictions inside a training set (nested alpha selection), for in-fold bias correction."""
    from sklearn.model_selection import KFold
    pred = np.full(len(y), np.nan)
    for tr, te in KFold(n_splits, shuffle=True, random_state=seed).split(X):
        f, _ = st.ridge_cv(X[tr], y[tr], grid, seed=seed + 1)
        pred[te] = f(X[te])
    return pred


def boot_mean_ci(v, B=2000, seed=0):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(B)]
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def age_models(units: dict, folds_of_seed, children: list[int], feats: dict, age: dict, grid, *, bias_correct=False):
    """feats[name](seed, k, child) -> vector. Returns per-seed OOF predictions (and bias-corrected gaps)."""
    out = {n: {} for n in feats}
    gaps = {n: {} for n in feats}
    for s, fold in folds_of_seed.items():
        for n in feats:
            out[n][s], gaps[n][s] = {}, {}
        for k in sorted(set(fold[c] for c in children)):
            tr = [c for c in children if fold[c] != k]
            te = [c for c in children if fold[c] == k]
            ytr = np.array([age[c] for c in tr])
            for n, fn in feats.items():
                Xtr = np.stack([fn(s, k, c) for c in tr])
                Xte = np.stack([fn(s, k, c) for c in te])
                p, _ = ridge_oof(Xtr, ytr, Xte, grid, seed=s * 10 + k)
                out[n][s].update(dict(zip(te, p.tolist())))
                if bias_correct:
                    ptr = inner_oof(Xtr, ytr, grid, seed=s * 100 + k)
                    g = ptr - ytr
                    c1, c0 = np.polyfit(ytr, g, 1)
                    ag = np.array([age[c] for c in te])
                    gaps[n][s].update(dict(zip(te, (p - ag - (c0 + c1 * ag)).tolist())))
    return out, gaps


def summarise_age(pred: dict, age: dict, children: list[int]) -> dict:
    err = {n: {c: float(np.mean([abs(pred[n][s][c] - age[c]) for s in pred[n]])) for c in children} for n in pred}
    per_seed = {n: [float(np.mean([abs(pred[n][s][c] - age[c]) for c in children])) for s in pred[n]] for n in pred}
    base = float(np.mean([abs(np.mean([age[x] for x in children if x != c]) - age[c]) for c in children]))
    res = {"n": len(children), "mae": {n: float(np.mean(list(err[n].values()))) for n in pred},
           "mae_per_seed": per_seed, "mae_mean_baseline": base}
    e, s_, j = (np.array([err[n][c] for c in children]) for n in ("event", "spectral", "joint"))
    res["event_minus_spectral"] = {"mean": float((e - s_).mean()), "ci": boot_mean_ci(e - s_, seed=1)}
    res["spectral_minus_joint"] = {"mean": float((s_ - j).mean()), "ci": boot_mean_ci(s_ - j, seed=2)}
    return res


# ============================================================================ A1 / A3 (HA/BDF, PF2 partitions)

def analyze_a_bdf(config) -> tuple[dict, dict]:
    from auditory_pf.cohort import Cohort
    from auditory_pf.runtime import load_config as pf_load
    pfc = pf_load(cfg(config, "sources.pf_config_v2"))
    co = Cohort(pfc, cfg(config, "sources.pf_prepare_v2"))
    stim_dir = ROOT / "private/auditory_pf" / cfg(config, "sources.pf_stim_v2")
    units = {}
    for s in co.seeds:
        for k in range(5):
            with np.load(stim_dir / f"unit_s{s}_k{k}" / "exports.npz") as z:
                units[(s, k)] = z["agg_base"]
    with np.load(ROOT / cfg(config, "sources.pf_features")) as z:
        cont = z["cont"]
    ch = co.ch.set_index("child")
    rec = co.rec.set_index("rec")
    kids = [int(c) for c in ch.index if int(ch.loc[c, "primary_rec"]) in co.draw_row
            and np.isfinite(rec.loc[int(ch.loc[c, "primary_rec"]), "age_months"])]
    age = {c: float(rec.loc[int(ch.loc[c, "primary_rec"]), "age_months"]) for c in kids}
    prim = {c: int(ch.loc[c, "primary_rec"]) for c in kids}

    def ev(s, k, c):
        a = units[(s, k)][prim[c]].mean(0)
        return np.concatenate([a[1], a[0]])

    feats = {"event": ev, "spectral": lambda s, k, c: cont[prim[c]].ravel(),
             "joint": lambda s, k, c: np.concatenate([cont[prim[c]].ravel(), ev(s, k, c)])}
    folds = {s: co.outer(s) for s in co.seeds}
    pred, gaps = age_models(units, folds, kids, feats, age, cfg(config, "stats.ridge_alpha"), bias_correct=True)
    a1 = summarise_age(pred, age, kids)
    a1["n_ha"] = int(sum(ch.loc[c, "group"] == "labelled" for c in kids))
    a1["n_nh"] = int(sum(ch.loc[c, "group"] == "nh" for c in kids))
    # A3: auditory maturation residual = corrected event gap - corrected spectral gap
    amr = {c: float(np.mean([gaps["event"][s][c] - gaps["spectral"][s][c] for s in gaps["event"]])) for c in kids}
    ha = [c for c in kids if ch.loc[c, "group"] == "labelled" and np.isfinite(ch.loc[c, "duration_months"])]
    nh = [c for c in kids if ch.loc[c, "group"] == "nh"]
    ld = np.array([np.log1p(ch.loc[c, "duration_months"]) for c in ha])
    ag = np.array([age[c] for c in ha])
    av = np.array([amr[c] for c in ha])

    def partial(v, x, z):
        Z = np.column_stack([np.ones(len(z)), z])
        rv = v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]
        rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
        from scipy.stats import spearmanr
        return float(spearmanr(rv, rx)[0])
    rho = partial(av, ld, ag)
    null = []
    for p in range(1, int(cfg(config, "stats.perm_a3")) + 1):
        rng = np.random.default_rng(stable_int("dv_a3", p))
        null.append(partial(av, ld[rng.permutation(len(ld))], ag))
    a3 = {"n_ha": len(ha), "partial_spearman_amr_logdur_given_age": rho,
          "perm_p_one_sided": st.perm_p(rho, null), "amr_mean_ha": float(av.mean()),
          "amr_mean_nh": float(np.mean([amr[c] for c in nh])) if nh else None, "n_nh": len(nh),
          "amr_sd_ha": float(av.std())}
    return {"A1": a1, "A3": a3}, {"amr": {str(c): v for c, v in amr.items()}}


# ============================================================================ A2 (MFF)

def load_mff_units(config, co: MffCohort):
    d = private_dir(config, cfg(config, "runs.stim_mff"))
    units = {}
    for s in co.seeds:
        for k in range(int(cfg(config, "mff.n_outer"))):
            p = d / f"unit_s{s}_k{k}" / "exports.npz"
            if p.exists():
                with np.load(p) as z:
                    units[(s, k)] = {n: z[n] for n in z.files}
    return units


def analyze_a_mff(config, co: MffCohort, units) -> dict:
    with np.load(private_dir(config, cfg(config, "runs.features_mff")) / "features_mff.npz") as z:
        cont = z["cont"]
    ch = co.ch.set_index("child")
    kids = [int(c) for c in ch.index if bool(ch.loc[c, "has_age"]) and int(ch.loc[c, "primary_rec"]) in co.draw_row
            and np.isfinite(cont[int(ch.loc[c, "primary_rec"]), 0, 0])]
    age = {c: float(ch.loc[c, "age_months"]) for c in kids}
    prim = {c: int(ch.loc[c, "primary_rec"]) for c in kids}

    def ev(s, k, c):
        a = units[(s, k)]["agg"][prim[c]].mean(0)
        return np.concatenate([a[1], a[0]])
    feats = {"event": ev, "spectral": lambda s, k, c: cont[prim[c]].ravel(),
             "joint": lambda s, k, c: np.concatenate([cont[prim[c]].ravel(), ev(s, k, c)])}
    folds = {s: co.outer(s) for s in co.seeds}
    pred, _ = age_models(units, folds, kids, feats, age, cfg(config, "stats.ridge_alpha"))
    res = summarise_age(pred, age, kids)
    res["n_ci_label"] = int(sum(bool(ch.loc[c, "ci_label"]) for c in kids))
    return res


# ============================================================================ held-out trial scores

def heldout_scores_mff(co: MffCohort, units) -> np.ndarray:
    acc, cnt = np.zeros(co.n_trials), np.zeros(co.n_trials)
    for (s, k), u in units.items():
        m = np.isin(co.child_of_trial, u["test_children"])
        acc[m] += u["diff"][m]
        cnt[m] += 1
    out = np.full(co.n_trials, np.nan)
    out[cnt > 0] = acc[cnt > 0] / cnt[cnt > 0]
    return out


def heldout_scores_bdf(config):
    from auditory_pf.cohort import Cohort
    from auditory_pf.runtime import load_config as pf_load
    pfc = pf_load(cfg(config, "sources.pf_config_v2"))
    co = Cohort(pfc, cfg(config, "sources.pf_prepare_v2"))
    child_of_trial = co.rec.child.to_numpy()[co.t_record]
    acc, cnt = np.zeros(co.n_trials), np.zeros(co.n_trials)
    stim_dir = ROOT / "private/auditory_pf" / cfg(config, "sources.pf_stim_v2")
    for s in co.seeds:
        for k in range(5):
            with np.load(stim_dir / f"unit_s{s}_k{k}" / "exports.npz") as z:
                m = np.isin(child_of_trial, z["test_children"])
                acc[m] += z["diff_base"][m]
                cnt[m] += 1
    out = np.full(co.n_trials, np.nan)
    out[cnt > 0] = acc[cnt > 0] / cnt[cnt > 0]
    return co, out


# ============================================================================ E (sessions)

def analyze_e(config, co: MffCohort, scores) -> tuple[dict, list]:
    from scipy.stats import binomtest, kendalltau
    times = pd.read_csv(ROOT / cfg(config, "sources.st_records"), usecols=["record_id", "_record_time"])
    tmap = dict(zip(times.record_id, pd.to_datetime(times._record_time, errors="coerce", utc=True)))
    rec = co.rec.copy()
    rec["time"] = rec.record_id.map(tmap)
    rec["auc"] = [st.auc(co.t_y[co.t_record == r], scores[co.t_record == r]) for r in rec.rec]
    rows = []
    for (c, lane), g in rec.groupby(["child", "lane"]):
        g = g.dropna(subset=["time", "auc"]).sort_values("time")
        if len(g) < 3:
            continue
        tau = kendalltau(np.arange(len(g)), g.auc.to_numpy())[0]
        tq = kendalltau(np.arange(len(g)), g.qc_over_mean.to_numpy())[0]
        rows.append({"child": int(c), "lane": lane, "n_sessions": int(len(g)), "tau_order_auc": float(tau),
                     "tau_order_qc": float(tq), "ci_label": bool(g.source.isin(["CI", "CIHA_label"]).any())})
    t = pd.DataFrame(rows)
    if t.empty:
        return {"n_children": 0}, rows
    pos = int((t.tau_order_auc > 0).sum())
    p = float(binomtest(pos, len(t), 0.5, alternative="greater").pvalue)
    return {"n_children": int(len(t)), "n_tau_positive": pos, "sign_test_p": p, "median_tau": float(t.tau_order_auc.median()),
            "median_tau_qc": float(t.tau_order_qc.median()), "n_ci_label": int(t.ci_label.sum()),
            "sessions_per_child": t.n_sessions.tolist()}, rows


# ============================================================================ G (expectation-conditioned readout)

def observer_p(seq: np.ndarray, half_life: float) -> np.ndarray:
    """Leaky Beta-Bernoulli predictive P(deviant at t | trials < t); prior Beta(1,1)."""
    lam = 2.0 ** (-1.0 / half_life)
    a = b = 0.0
    out = np.empty(len(seq))
    for t, x in enumerate(seq):
        out[t] = (a + 1.0) / (a + b + 2.0)
        a = lam * a + x
        b = lam * b + (1 - x)
    return out


def _sequence_features(config, record_ids, lane_of, binary=True):
    """Per accepted trial (staged order): predictive p, previous class, standards since last deviant."""
    stage = ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run") / "epochs"
    h = float(cfg(config, "g.half_life"))
    P, PREV, RUN = [], [], []
    for rid in record_ids:
        with np.load(stage / f"{rid}.npz", allow_pickle=False) as s:
            y = s["y"].astype(int)
            on = s["onset_seconds"]
            acc = s["accepted"].astype(bool)
        if binary:
            y = (y > 0).astype(int)
        order = np.argsort(on, kind="stable")
        seq = y[order]
        p = observer_p(seq, h)
        prev = np.concatenate([[0], seq[:-1]])
        run = np.zeros(len(seq), int)
        c = 5
        for i, x in enumerate(seq):
            run[i] = min(c, 5)
            c = 0 if x == 1 else c + 1
        inv = np.empty(len(order), int)
        inv[order] = np.arange(len(order))
        P.append(p[inv][acc]); PREV.append(prev[inv][acc]); RUN.append(run[inv][acc])
    return np.concatenate(P), np.concatenate(PREV), np.concatenate(RUN)


def _cv_ce(X, y, groups, seed=0):
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold
    p = np.full(len(y), np.nan)
    for tr, te in GroupKFold(5).split(X, y, groups):
        z = st.Standardizer().fit(X[tr])
        m = LogisticRegression(C=1.0, max_iter=2000).fit(z.transform(X[tr]), y[tr])
        p[te] = m.predict_proba(z.transform(X[te]))[:, 1]
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log2(p) + (1 - y) * np.log2(1 - p))


def analyze_g_block(s, y, p, prev, run, child) -> dict:
    ok = np.isfinite(s)
    s, y, p, prev, run, child = s[ok], y[ok], p[ok], prev[ok], run[ok], child[ok]
    zs = (s - s.mean()) / s.std()
    lp = np.log(p / (1 - p))
    R = np.eye(6)[run]
    Xh = np.column_stack([zs, prev, R[:, 1:], zs * prev, zs[:, None] * R[:, 1:]])
    Xs = np.column_stack([zs, lp, zs * lp])
    ce_h, ce_s = _cv_ce(Xh, y, child), _cv_ce(Xs, y, child)
    per_child = pd.DataFrame({"c": child, "d": ce_h - ce_s}).groupby("c").d.mean().to_numpy()
    return {"trials": int(len(y)), "children": int(len(np.unique(child))), "ce_hist": float(ce_h.mean()),
            "ce_surprisal": float(ce_s.mean()), "delta_bits": float((ce_h - ce_s).mean()),
            "delta_child_ci": boot_mean_ci(per_child, seed=7)}


# ============================================================================ D model (only if the audit passed)

def _first_float(v):
    m = re.search(r"-?\d+(?:\.\d+)?", str(v))
    return float(m.group()) if m else np.nan


def analyze_d(config, co: MffCohort, scores) -> dict:
    audit = read_json(ROOT / "results/auditory_dv" / cfg(config, "runs.audit_d") / "summary_audit_d.json")
    if not audit.get("D_pass"):
        return {"status": "not_run_gate_failed", "coverage": audit.get("eligible_participants_with_value_by_category")}
    cols = pd.read_csv(private_dir(config, cfg(config, "runs.audit_d")) / "objective_columns.csv")
    rows = pd.read_csv(ROOT / cfg(config, "sources.ci_rows"))
    elig = pd.read_csv(ROOT / cfg(config, "sources.ci_eligibility"))
    elig = elig[(elig.scope == "all_MFF_candidate_links") & (elig.stad_measurable == True)]  # noqa: E712
    rec_of = dict(zip(co.rec.record_id, co.rec.rec))          # per-visit rule: the linked record itself
    rec_age = dict(zip(co.rec.rec, co.rec.age_months))
    rec_auc = {r: st.auc(co.t_y[co.t_record == r], scores[co.t_record == r]) for r in co.rec.rec}
    out = {}
    for cat in audit["D_pass_categories"]:
        sel = cols[cols.categories.str.contains(cat)]
        vals = {}
        for r in rows.itertuples():
            cells = json.loads(r.raw_cells_json) if isinstance(r.raw_cells_json, str) else []
            v = [_first_float(cells[j - 1]) for sh, j in zip(sel.sheet, sel.column) if sh == r.source_sheet_index and j - 1 < len(cells)]
            v = [x for x in v if np.isfinite(x)]
            if v:
                vals.setdefault(r.participant_id, []).append(float(np.mean(v)))
        data = []
        for e in elig.itertuples():
            r = rec_of.get(e.container_id)
            if r is None or e.participant_id not in vals or not np.isfinite(rec_age[r]) or not np.isfinite(rec_auc[r]):
                continue
            data.append((float(np.mean(vals[e.participant_id])), rec_auc[r], float(rec_age[r])))
        if len(data) < 10:
            out[cat] = {"n": len(data), "status": "too_few_linked_with_age"}
            continue
        v, a, g = (np.array(x) for x in zip(*data))
        Z = np.column_stack([np.ones(len(g)), g])
        rv, ra = v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0], a - Z @ np.linalg.lstsq(Z, a, rcond=None)[0]
        from scipy.stats import spearmanr
        out[cat] = {"n": len(data), "partial_spearman_readout_measure_given_age": float(spearmanr(rv, ra)[0])}
    return out


# ============================================================================ driver

def cmd_analyze(args, config) -> dict:
    run = open_run("analyze", args.run, config, args=vars(args))
    res, priv = {}, {}
    a_bdf, p_bdf = analyze_a_bdf(config)
    res.update(a_bdf)
    priv.update(p_bdf)
    co = MffCohort(config, cfg(config, "runs.prepare_mff"))
    units = load_mff_units(config, co)
    res["mff_units_loaded"] = len(units)
    if len(units) == len(co.seeds) * int(cfg(config, "mff.n_outer")):
        res["A2"] = analyze_a_mff(config, co, units)
        sc = heldout_scores_mff(co, units)
        res["E"], priv["E_rows"] = analyze_e(config, co, sc)
        p, prev, run_ = _sequence_features(config, list(co.rec.record_id), None)
        res["G_mff"] = analyze_g_block(sc, co.t_y, p, prev, run_, co.child_of_trial)
        res["D_model"] = analyze_d(config, co, sc)
    bco, bsc = heldout_scores_bdf(config)
    pb, prevb, runb = _sequence_features(config, list(bco.rec.record_id), None, binary=True)
    res["G_bdf"] = analyze_g_block(bsc, bco.t_y, pb, prevb, runb, bco.rec.child.to_numpy()[bco.t_record])
    mdir = private_dir(config, cfg(config, "runs.montage_lane"))
    if mdir.exists():
        res["B"] = {p.stem: read_json(p) for p in sorted(mdir.glob("*__*.json"))}
    for a in ("audit_c", "audit_d"):
        p = ROOT / "results/auditory_dv" / cfg(config, f"runs.{a}") / f"summary_{a}.json"
        if p.exists():
            res[a] = read_json(p)
    C = claims(res)
    write_json_atomic(run["public"] / "summary_dv.json", {"results": res, "claims": C}, private=False)
    write_json_atomic(run["private"] / "private_dv.json", priv, private=True)
    return {"claims": {k: v["status"] for k, v in C.items()}}


def claims(r: dict) -> dict:
    C = {}
    a1 = r["A1"]
    ems, smj = a1["event_minus_spectral"]["mean"], a1["spectral_minus_joint"]["mean"]
    C["A1"] = {"event_minus_spectral": ems, "spectral_minus_joint": smj,
               "status": status(supported=ems <= 1.0 and smj >= 2.0, refuted=smj <= 0, partial=(ems <= 1.0) != (smj >= 2.0),
                                direction=smj > 0)}
    if "A2" in r:
        g = r["A2"]["spectral_minus_joint"]["mean"]
        C["A2"] = {"spectral_minus_joint": g, "status": status(supported=g >= 1.0, refuted=g <= 0, direction=g > 0)}
    a3 = r["A3"]
    rho, p = a3["partial_spearman_amr_logdur_given_age"], a3["perm_p_one_sided"]
    C["A3"] = {"rho": rho, "p": p, "status": status(supported=rho >= 0.2 and p < 0.05, refuted=abs(rho) < 0.1,
                                                     partial=(rho >= 0.2) != (p < 0.05), direction=rho > 0)}
    if "B" in r:
        b = r["B"]
        get = lambda m, l: b.get(f"{m}__{l}", {})  # noqa: E731
        base = get("avg", "mff_puretone").get("auc_child_mean", np.nan)
        gains = {m: get(m, "mff_puretone").get("auc_child_mean", np.nan) - base for m in ("mastoid", "rest", "csd")}
        rel = {m: get(m, "mff_puretone").get("split_half_spearman_brown", np.nan) for m in ("avg", "mastoid", "rest", "csd")}
        best_rel = np.nanmax(list(rel.values()))
        C["B1"] = {"gain_mastoid": gains["mastoid"], "gains": gains,
                   "status": status(supported=gains["mastoid"] >= 0.02,
                                    refuted=all(abs(v) < 0.01 for v in gains.values() if np.isfinite(v)), direction=gains["mastoid"] > 0)}
        C["B2"] = {"reliability": rel, "status": status(supported=best_rel >= 0.7, refuted=best_rel < 0.5, direction=best_rel >= 0.5)}
    if "audit_c" in r:
        C["C1"] = {"components_without_canonical": r["audit_c"]["components_without_canonical"],
                   "usable_segmented": r["audit_c"]["without_canonical_usable_segmented"],
                   "status": "成立" if r["audit_c"]["C1_pass"] else "推翻"}
    if "audit_d" in r:
        C["D_gate"] = {"coverage": r["audit_d"]["eligible_participants_with_value_by_category"],
                       "status": "成立" if r["audit_d"]["D_pass"] else "推翻"}
    if "E" in r and r["E"].get("n_children", 0):
        e = r["E"]
        frac = e["n_tau_positive"] / e["n_children"]
        C["E"] = {"n": e["n_children"], "frac_tau_positive": frac, "p": e["sign_test_p"],
                  "status": status(supported=frac >= 2 / 3 and e["sign_test_p"] < 0.05, refuted=frac <= 0.5,
                                   direction=frac > 0.5, not_evaluable="support" if e["n_children"] < 5 else None)}
    if "G_mff" in r:
        d = r["G_mff"]["delta_bits"]
        C["G"] = {"delta_bits": d, "status": status(supported=d >= 0.005, refuted=d <= 0, direction=d > 0)}
    return C


# ============================================================================ post-hoc sensitivity (disclosed; not a claim)

def cmd_a1_sensitivity(args, config) -> dict:
    """A1 errors split by HA / NH from the same fit, and A1 refitted on HA children only (post-hoc, disclosed)."""
    from auditory_pf.cohort import Cohort
    from auditory_pf.runtime import load_config as pf_load
    run = open_run("a1_sensitivity", args.run, config, args=vars(args))
    pfc = pf_load(cfg(config, "sources.pf_config_v2"))
    co = Cohort(pfc, cfg(config, "sources.pf_prepare_v2"))
    stim_dir = ROOT / "private/auditory_pf" / cfg(config, "sources.pf_stim_v2")
    units = {}
    for s in co.seeds:
        for k in range(5):
            with np.load(stim_dir / f"unit_s{s}_k{k}" / "exports.npz") as z:
                units[(s, k)] = z["agg_base"]
    with np.load(ROOT / cfg(config, "sources.pf_features")) as z:
        cont = z["cont"]
    ch = co.ch.set_index("child")
    rec = co.rec.set_index("rec")
    kids = [int(c) for c in ch.index if int(ch.loc[c, "primary_rec"]) in co.draw_row
            and np.isfinite(rec.loc[int(ch.loc[c, "primary_rec"]), "age_months"])]
    age = {c: float(rec.loc[int(ch.loc[c, "primary_rec"]), "age_months"]) for c in kids}
    prim = {c: int(ch.loc[c, "primary_rec"]) for c in kids}
    grp = {c: ch.loc[c, "group"] for c in kids}

    def ev(s, k, c):
        a = units[(s, k)][prim[c]].mean(0)
        return np.concatenate([a[1], a[0]])
    feats = {"event": ev, "spectral": lambda s, k, c: cont[prim[c]].ravel(),
             "joint": lambda s, k, c: np.concatenate([cont[prim[c]].ravel(), ev(s, k, c)])}
    folds = {s: co.outer(s) for s in co.seeds}
    out = {}
    pred, _ = age_models(units, folds, kids, feats, age, cfg(config, "stats.ridge_alpha"))
    for g in ("labelled", "nh"):
        cs = [c for c in kids if grp[c] == g]
        out[f"same_fit_mae_{g}"] = {n: float(np.mean([np.mean([abs(pred[n][s][c] - age[c]) for s in pred[n]]) for c in cs])) for n in pred}
        out[f"same_fit_signed_error_{g}"] = {n: float(np.mean([np.mean([pred[n][s][c] - age[c] for s in pred[n]]) for c in cs])) for n in pred}
        out[f"n_{g}"] = len(cs)
    out["nh_age_months_median"] = float(np.median([age[c] for c in kids if grp[c] == "nh"]))
    out["ha_age_months_median"] = float(np.median([age[c] for c in kids if grp[c] == "labelled"]))
    ha = [c for c in kids if grp[c] == "labelled"]
    pred_ha, _ = age_models(units, folds, ha, feats, age, cfg(config, "stats.ridge_alpha"))
    out["ha_only_refit"] = summarise_age(pred_ha, age, ha)
    tech = co.rec.set_index("rec")
    out["technical_by_group"] = {g: {col: float(np.median([tech.loc[prim[c], col] for c in kids if grp[c] == g]))
                                     for col in ("record_scale", "d1_seconds", "accept_fraction", "qc_over_mean")}
                                 for g in ("labelled", "nh")}
    write_json_atomic(run["public"] / "summary_a1_sensitivity.json", out, private=False)
    return out
