"""A0: age information in the existing single-encoder embeddings (execution spec section 4).

Unit = (budget, view, source seed, outer fold). Every unit is one atomic JSON (predictions + the full fit ledger), so a
requeued runfill job skips finished units. The summary reads saved predictions only and never refits.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import age_readout as ar
from . import representations as rp
from .adapters import AgeSource, units
from .runtime import (ROOT, ProvenanceError, cfg, close_run, open_run, require_protocol, stable_int, write_json_atomic,
                      write_jsonl_atomic, write_parquet_atomic)

FIXED_VIEWS = ("spectral_ridge", "spectral_rbf", "technical", "technical_noscale")    # budget-free inputs
CONSTANT_VIEWS = ("median_train", "mean_train")


def work_list(config: dict) -> list[tuple[str, str]]:
    """(budget, view) pairs of A0, in run order. pair_equivalence follows joint (needs joint's alpha)."""
    a = config["age"]
    primary = list(a["primary_views"]) + ["pair_equivalence"] + list(a["baselines"]) + list(a["approved_additions"])
    out = [("single_draw80", v) for v in primary]
    out += [("draw_ensemble10", v) for v in a["sensitivity_views"]]
    return out


def unit_path(run_dir: Path, budget: str, view: str, s: int, k: int) -> Path:
    return run_dir / "units" / budget / view / f"s{s}_k{k}.json"


def inner_seed(s: int, k: int) -> int:
    return stable_int("nextmap_inner", s, k) % (2 ** 31 - 1)


def check_scope(src: AgeSource, s: int, k: int) -> None:
    """T1/T2 on the real exports: the unit's M_o test children are exactly outer fold k (all groups)."""
    ex = src.exports(s, k)
    outer = src.outer(s)
    test = sorted(c for c, f in outer.items() if f == k)
    train = sorted(c for c, f in outer.items() if f != k)
    if sorted(int(c) for c in ex["test_children"]) != test or sorted(int(c) for c in ex["train_children"]) != train:
        raise ProvenanceError(f"MODEL_SCOPE_INVALID:{s}_{k}")
    if set(test) & set(train):
        raise ProvenanceError(f"TEST_TRAIN_OVERLAP:{s}_{k}")


def split(src: AgeSource, s: int, k: int, children=None) -> tuple[list[int], list[int]]:
    children = src.main_children if children is None else children
    outer = src.outer(s)
    return [c for c in children if outer[c] != k], [c for c in children if outer[c] == k]


def design_for(src: AgeSource, config: dict, view: str, budget: str, s: int, k: int, rows: list[int]):
    floor = float(cfg(config, "age.scale_floor"))
    if view in rp.PAIRED_VIEWS:
        mu0, mu1 = src.class_means(s, k, rows, budget)
        return "ridge", (lambda tr, ev: rp.paired_design(view, mu0, mu1, tr, ev, floor=floor))
    if view in ("spectral_ridge", "spectral_rbf"):
        X = src.spectral(rows)
        return ("rbf" if view == "spectral_rbf" else "ridge"), (lambda tr, ev: rp.standard_design(X, tr, ev, floor=floor))
    if view in ("technical", "technical_noscale"):
        X = src.technical(rows, with_scale=(view == "technical"))
        return "ridge", (lambda tr, ev: rp.standard_design(X, tr, ev, floor=floor, missing_flags=True))
    raise ValueError(view)


def run_unit(src: AgeSource, config: dict, budget: str, view: str, s: int, k: int, joint_alpha: float | None) -> dict:
    tr, te = split(src, s, k)
    rows = tr + te
    y = np.array([src.age(c) for c in rows])
    key = {"budget": budget, "view": view, "seed": s, "fold": k}
    base = {**key, "train_children": tr, "test_children": te, "age_test": y[len(tr):].tolist()}
    if view in CONSTANT_VIEWS:
        ytr = y[:len(tr)]
        v = float(np.median(ytr) if view == "median_train" else np.mean(ytr))
        return {**base, "status": "COMPLETED", "pred": [v] * len(te), "n_fits": 0, "fits": []}
    ledger: list = []
    a = config["age"]
    if view == "pair_equivalence":
        # T3 on real data: pair at joint's alpha must reproduce joint's predictions and objective.
        kind, dj = design_for(src, config, "joint", budget, s, k, rows)
        _, dp = design_for(src, config, "pair", budget, s, k, rows)
        n = len(tr)
        Xj_tr, Xj_te, _ = dj(np.arange(n), np.arange(n, len(rows)))
        Xp_tr, Xp_te, _ = dp(np.arange(n), np.arange(n, len(rows)))
        mj, mp = ar.ridge_fit(Xj_tr, y[:n], joint_alpha), ar.ridge_fit(Xp_tr, y[:n], joint_alpha)
        pj, pp = ar.ridge_predict(mj, Xj_te), ar.ridge_predict(mp, Xp_te)
        rel = float(np.max(np.abs(pj - pp)) / max(np.max(np.abs(pj)), 1e-300))
        obj = abs(mj["diag"]["objective_sse_l2"] - mp["diag"]["objective_sse_l2"]) / max(mj["diag"]["objective_sse_l2"], 1e-300)
        energy = float(np.max(np.abs((Xj_tr ** 2).sum(1) - (Xp_tr ** 2).sum(1)) / np.maximum((Xp_tr ** 2).sum(1), 1e-300)))
        ok = max(rel, obj, energy) <= float(a["equivalence_rel_tol"])
        return {**base, "status": "COMPLETED" if ok else "NUMERICAL_FAILURE", "pred": pp.tolist(), "alpha": joint_alpha,
                "equivalence": {"pred_rel_diff": rel, "objective_rel_diff": float(obj), "energy_rel_diff": energy},
                "n_fits": 1, "fits": [{**key, "stage": "outer", "alpha": joint_alpha, "diag": mp["diag"]}]}
    kind, design = design_for(src, config, view, budget, s, k, rows)
    alphas = a["kernel_alpha"] if kind == "rbf" else a["alpha_sse"]
    try:
        res = ar.select_and_fit(design, y, len(tr), np.arange(len(tr), len(rows)), kind=kind, alphas=alphas,
                                inner_folds=int(a["inner_folds"]), inner_seed=inner_seed(s, k),
                                tie_tol=float(a["tie_tolerance"]), ledger=ledger, key=key,
                                gamma_fallback=float(a["kernel_gamma_fallback"]))
    except ar.FitFailure as exc:
        return {**base, "status": "NUMERICAL_FAILURE", "reason": str(exc), "pred": None,
                "n_fits": len(alphas) * int(a["inner_folds"]) + 1, "fits": ledger}
    return {**base, "status": "COMPLETED", "pred": res["pred"].tolist(), "alpha": res["alpha"], "inner_mae": res["inner_mae"],
            "constant_prediction": res["constant_prediction"], "n_fits": res["n_fits"], "fits": ledger}


def cmd_age_core(args, config) -> dict:
    require_protocol(config)
    run = open_run("age_core", args.run, config, args=vars(args))
    src = AgeSource(config)
    for s, k in units(config):
        check_scope(src, s, k)
    done = new = 0
    for budget, view in work_list(config):
        for s, k in units(config):
            path = unit_path(run["private"], budget, view, s, k)
            if path.exists():
                done += 1
                continue
            joint_alpha = None
            if view == "pair_equivalence":
                joint = json.loads(unit_path(run["private"], budget, "joint", s, k).read_text())
                if joint["status"] != "COMPLETED":
                    write_json_atomic(path, {"budget": budget, "view": view, "seed": s, "fold": k,
                                             "status": "NUMERICAL_FAILURE", "reason": "JOINT_FAILED", "pred": None,
                                             "n_fits": 0, "fits": []}, private=True)
                    continue
                joint_alpha = float(joint["alpha"])
            write_json_atomic(path, run_unit(src, config, budget, view, s, k, joint_alpha), private=True)
            new += 1
    summary = summarize(config, args.run)
    close_run(config, "age_core", args.run, "COMPLETED", units_new=new, units_reused=done)
    return {"units_new": new, "units_reused": done, "status": summary["status"]}


# ====================================================================== summary (saved predictions only)

def load_units(run_dir: Path, budget: str, view: str, unit_list) -> tuple[list[dict], str]:
    out, status = [], "COMPLETED"
    for s, k in unit_list:
        p = unit_path(run_dir, budget, view, s, k)
        if not p.exists():
            return out, "INCOMPLETE"
        u = json.loads(p.read_text())
        if u["status"] != "COMPLETED":
            status = "NUMERICAL_FAILURE"
        out.append(u)
    return out, status


def collect_predictions(unit_rows: list[dict], children: list[int]) -> dict:
    """{seed: {child: pred}} over the 5 outer folds of each source seed; T12: a missing child is an error."""
    preds: dict = {}
    for u in unit_rows:
        for c, p in zip(u["test_children"], u["pred"]):
            preds.setdefault(int(u["seed"]), {})[int(c)] = float(p)
    for s, d in preds.items():
        missing = set(children) - set(d)
        if missing:
            raise ProvenanceError(f"MISSING_PREDICTIONS:seed{s}:{len(missing)}")   # never average a subset
    return preds


def view_table(preds: dict, ages: dict, children: list[int]) -> dict:
    seeds = sorted(preds)
    e = np.array([np.mean([abs(preds[s][c] - ages[c]) for s in seeds]) for c in children])
    sq = np.array([np.mean([(preds[s][c] - ages[c]) ** 2 for s in seeds]) for c in children])
    ens = np.array([abs(np.mean([preds[s][c] for s in seeds]) - ages[c]) for c in children])
    return {"err": e, "mae": float(e.mean()), "mse": float(sq.mean()),
            "mae_per_seed": [float(np.mean([abs(preds[s][c] - ages[c]) for c in children])) for s in seeds],
            "mae_ensemble_sensitivity": float(ens.mean()),
            "child_error_quantiles": {q: float(np.quantile(e, q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}}


def paired_boot(diff: np.ndarray, idx: np.ndarray) -> dict:
    bs = diff[idx].mean(1)
    lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    reading = "gain_established" if lo > 0 else ("loss_established" if hi < 0 else "no_clear_difference")
    return {"mean": float(diff.mean()), "ci95": [lo, hi], "reading": reading,
            "status": "COMPLETED" if (lo > 0 or hi < 0) else "COMPLETED_LOW_PRECISION"}


COMPARISONS = (   # (name, budget_a, view_a, budget_b, view_b, role); value = err_a - err_b (positive: b better)
    ("G_D_given_C", "single_draw80", "common", "single_draw80", "joint", "primary"),
    ("std_minus_dev", "single_draw80", "std", "single_draw80", "dev", "secondary"),
    ("median_minus_contrast", "single_draw80", "median_train", "single_draw80", "contrast", "secondary"),
    ("spectral_ridge_minus_joint", "single_draw80", "spectral_ridge", "single_draw80", "joint", "secondary"),
    ("spectral_rbf_minus_joint", "single_draw80", "spectral_rbf", "single_draw80", "joint", "secondary"),
    ("G_D_given_C_ensemble10", "draw_ensemble10", "common", "draw_ensemble10", "joint", "sensitivity"),
    ("G_D_given_C_blockscaled", "single_draw80", "common", "single_draw80", "joint_bs", "addition_a"),
    ("median_minus_contrast_blockscaled", "single_draw80", "median_train", "single_draw80", "contrast_bs", "addition_a"),
    ("technical_noscale_minus_technical", "single_draw80", "technical_noscale", "single_draw80", "technical", "addition_b"),
)


def summarize(config: dict, run: str) -> dict:
    run_dir = ROOT / cfg(config, "paths.private_relative") / run
    pub = ROOT / cfg(config, "paths.results_relative") / run
    src = AgeSource(config)
    children = src.main_children
    ages = {c: src.age(c) for c in children}
    ul = units(config)
    tables, statuses, rows, fits, alphas, equiv = {}, {}, [], [], {}, []
    for budget, view in work_list(config):
        us, status = load_units(run_dir, budget, view, ul)
        statuses[f"{budget}/{view}"] = status
        if status != "COMPLETED":
            continue
        preds = collect_predictions(us, children)
        tables[(budget, view)] = view_table(preds, ages, children)
        alphas[f"{budget}/{view}"] = {str(a): int(sum(1 for u in us if u.get("alpha") == a))
                                      for a in sorted({u.get("alpha") for u in us if u.get("alpha") is not None})}
        for u in us:
            fits.extend(u["fits"])
            if view == "pair_equivalence":
                equiv.append(u["equivalence"])
            for c, p in zip(u["test_children"], u["pred"]):
                rows.append({"budget": budget, "view": view, "seed": u["seed"], "fold": u["fold"], "child": int(c),
                             "pred": float(p), "age": ages[int(c)], "abs_err": abs(float(p) - ages[int(c)])})
    B = int(cfg(config, "age.bootstrap_children"))
    idx = np.random.default_rng(int(cfg(config, "age.bootstrap_seed"))).integers(0, len(children), size=(B, len(children)))
    comps = {}
    for name, ba, va, bb, vb, role in COMPARISONS:
        if (ba, va) in tables and (bb, vb) in tables:
            comps[name] = {"role": role, "a": f"{ba}/{va}", "b": f"{bb}/{vb}",
                           **paired_boot(tables[(ba, va)]["err"] - tables[(bb, vb)]["err"], idx)}
        else:
            comps[name] = {"role": role, "status": "TECHNICAL_INVALID", "a": f"{ba}/{va}", "b": f"{bb}/{vb}"}
    # age range: test children outside the training range, and training-defined tertile descriptives
    out_of_range, tert = 0, {"low": [], "mid": [], "high": []}
    if ("single_draw80", "common") in tables:
        for s, k in ul:
            tr, te = split(src, s, k)
            a_tr = np.array([ages[c] for c in tr])
            q1, q2 = np.quantile(a_tr, [1 / 3, 2 / 3])
            out_of_range += sum(1 for c in te if ages[c] < a_tr.min() or ages[c] > a_tr.max())
            u = json.loads(unit_path(run_dir, "single_draw80", "common", s, k).read_text())
            for c, p in zip(u["test_children"], u["pred"]):
                band = "low" if ages[c] <= q1 else ("mid" if ages[c] <= q2 else "high")
                tert[band].append(abs(p - ages[c]))
    drawn = src.draw_unique_counts(children)
    n_fits = int(sum(json.loads(unit_path(run_dir, b, v, s, k).read_text()).get("n_fits", 0)
                     for b, v in work_list(config) for s, k in ul if unit_path(run_dir, b, v, s, k).exists()))
    summary = {
        "status": "COMPLETED" if all(v == "COMPLETED" for v in statuses.values()) else "INCOMPLETE_OR_FAILED",
        "n_children": len(children), "n_units": len(ul), "unit_status": statuses, "small_age_fits": n_fits,
        "views": {f"{b}/{v}": {k2: v2 for k2, v2 in t.items() if k2 != "err"} for (b, v), t in tables.items()},
        "alpha_counts": alphas, "comparisons": comps, "bootstrap": {"B": B, "seed": int(cfg(config, "age.bootstrap_seed")),
                                                                     "shared_indices": True, "kind": "conditional_on_fits"},
        "pair_equivalence_max": {k2: float(max(e[k2] for e in equiv)) for k2 in equiv[0]} if equiv else None,
        "age_range": {"test_out_of_training_range_unit_children": int(out_of_range),
                      "tertile_mae_common_draw0": {b: (float(np.mean(v)) if v else None) for b, v in tert.items()},
                      "tertile_n": {b: len(v) for b, v in tert.items()}},
        "trial_budget": {"single_draw80_per_class": 80,
                         "union10_std_median": float(np.median([d["std_union10"] for d in drawn.values()])),
                         "union10_dev_median": float(np.median([d["dev_union10"] for d in drawn.values()])),
                         "draw0_all_80": bool(all(d["std_draw0"] == 80 and d["dev_draw0"] == 80 for d in drawn.values()))},
    }
    write_parquet_atomic(pd.DataFrame(rows), run_dir / "age_predictions.parquet")
    write_jsonl_atomic(fits, run_dir / "age_fit_ledger.jsonl")
    write_json_atomic(pub / "summary_a0.json", summary, private=False)
    return summary


def cmd_age_summary(args, config) -> dict:
    open_run("age_summary", args.run, config, args=vars(args))
    s = summarize(config, args.run)
    close_run(config, "age_summary", args.run, s["status"])
    return {"status": s["status"], "comparisons": {k: v.get("mean") for k, v in s["comparisons"].items()}}
