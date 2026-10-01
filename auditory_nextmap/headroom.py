"""C0: SIR five-class probabilities and predictive headroom (execution spec section 10).

PF's H14 saved only per-child seed-mean |E[Y] - SIR| (analyze_004 private_real.json), no probabilities or parameters.
Path taken (spec 10.2, second bullet): the exact clinical-only refit with the ORIGINAL functions (clinical_design,
stats.ordinal_cv) on the round-1 folds. The probabilities are exported from the very fitted objects that produced the
latent / E[Y] (read from the returned closures), and the refit counts as the H14 model only if it reproduces the stored
per-child errors (<= 1e-9) and the stored per-seed AUCs. Otherwise C0 ends as PROBABILITY_SOURCE_UNRESOLVED.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pandas as pd

from auditory_pf import stats as st
from auditory_pf.analysis_b1 import clinical_design

from .adapters import h14_errors, round1_cohort
from .runtime import (ROOT, ProvenanceError, cfg, close_run, open_run, require_protocol, write_json_atomic,
                      write_parquet_atomic)


def fitted_objects(fn) -> tuple:
    """(OrdinalLogistic, Standardizer) captured by the closure that stats.ordinal_cv returned."""
    cells = dict(zip(fn.__code__.co_freevars, (c.cell_contents for c in fn.__closure__)))
    if set(cells) != {"m", "st"} or not isinstance(cells["m"], st.OrdinalLogistic):
        raise ProvenanceError(f"ORDINAL_CLOSURE_LAYOUT:{sorted(cells)}")
    return cells["m"], cells["st"]


def floor_probabilities(P: np.ndarray, floor: float) -> tuple[np.ndarray, dict]:
    P = np.asarray(P, np.float64)
    if P.ndim != 2 or not np.isfinite(P).all():
        raise ProvenanceError("PROBABILITIES_NOT_FINITE_2D")
    if (P < -1e-12).any() or np.abs(P.sum(1) - 1.0).max() > 1e-8:
        raise ProvenanceError("NOT_A_PROBABILITY_VECTOR")       # e.g. logits or latents passed by mistake (T9)
    Q = np.maximum(P, floor)
    Q = Q / Q.sum(1, keepdims=True)
    return Q, {"min_raw_probability": float(P.min()), "fraction_floored": float((P < floor).mean())}


def cross_entropy_bits(Q: np.ndarray, y_levels: np.ndarray) -> np.ndarray:
    return -np.log2(Q[np.arange(len(y_levels)), np.asarray(y_levels, int) - 1])


def brier(Q: np.ndarray, y_levels: np.ndarray) -> np.ndarray:
    onehot = np.zeros_like(Q)
    onehot[np.arange(len(y_levels)), np.asarray(y_levels, int) - 1] = 1.0
    return ((Q - onehot) ** 2).sum(1)


def prior_vector(y_train: np.ndarray, levels: int, pseudo: float) -> np.ndarray:
    counts = np.bincount(np.asarray(y_train, int) - 1, minlength=levels).astype(float) + pseudo
    return counts / counts.sum()


def run_unit(co, ch, E, sir, grid, s: int, k: int) -> dict:
    fold = co.outer(s)
    tr = [c for c in E if fold[c] != k]
    te = [c for c in E if fold[c] == k]
    Xtr, Xte = clinical_design(SimpleNamespace(ch=ch), tr, te)
    y = np.array([sir[c] for c in tr]).astype(int)
    f_lat, f_exp, info = st.ordinal_cv(Xtr, y, grid, seed=s * 10 + k)
    m, scaler = fitted_objects(f_lat)
    if fitted_objects(f_exp)[0] is not m:
        raise ProvenanceError("LATENT_AND_EXPECTED_FROM_DIFFERENT_FITS")
    P = m.proba(scaler.transform(Xte))
    lat, ex = f_lat(Xte), f_exp(Xte)
    gap = float(np.max(np.abs(P @ np.arange(1, m.L + 1) - ex)))
    if gap > 1e-10:
        raise ProvenanceError(f"PROBA_EXPECTED_MISMATCH:{gap}")
    n_splits = min(5, len(y))
    return {"seed": s, "fold": k, "train_children": tr, "test_children": te, "latent": lat.tolist(), "expected": ex.tolist(),
            "proba_raw": P.tolist(), "lambda": info["lambda"], "inner_mae": info["inner_mae"], "converged": info["converged"],
            "thresholds": m.theta.tolist(), "n_ordinal_fits": (len(grid) * n_splits if len(grid) > 1 else 0) + 1,
            "train_levels": y.tolist()}


def cmd_headroom(args, config) -> dict:
    require_protocol(config)
    run = open_run("headroom", args.run, config, args=vars(args))
    pfc, co = round1_cohort(config)
    ch = co.ch.set_index("child")
    E = sorted(co.ch[(co.ch.group == "labelled") & (co.ch.eligible == True)].child.astype(int))   # noqa: E712 (as PF)
    sir = {c: float(ch.loc[c, "sir"]) for c in E}
    grid = cfg(pfc, "stats.ordinal_lambda")
    unit_dir = run["private"] / "units"
    units = []
    for s in co.seeds:
        for k in range(int(cfg(pfc, "folds.n_outer"))):
            p = unit_dir / f"s{s}_k{k}.json"
            if not p.exists():
                write_json_atomic(p, run_unit(co, ch, E, sir, grid, int(s), k), private=True)
            units.append(json.loads(p.read_text()))
    n_calls = int(sum(u["n_ordinal_fits"] for u in units))
    if n_calls > int(cfg(config, "resources.ordinal_optimizer_calls_max")):
        raise ProvenanceError(f"ORDINAL_CAP_EXCEEDED:{n_calls}")
    out = evaluate(config, co, E, sir, units, run)
    out["ordinal_optimizer_calls"] = n_calls
    write_json_atomic(run["public"] / "summary_c0.json", out, private=False)
    close_run(config, "headroom", args.run, out["status"], ordinal_calls=n_calls)
    return {"status": out["status"], "ordinal_optimizer_calls": n_calls,
            "reproduction": out["reproduction"], "primary": out.get("primary")}


def _load_units(run_dir) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((run_dir / "units").glob("s*_k*.json"))]


def cmd_headroom_diag(args, config) -> dict:
    """Addendum 001 evidence: the same unit fitted with 1 and 4 BLAS threads (62 ordinal calls)."""
    from threadpoolctl import threadpool_limits
    run = open_run("headroom_diag", args.run, config, args=vars(args))
    am = config["headroom"]["amendment_001"]
    pfc, co = round1_cohort(config)
    ch = co.ch.set_index("child")
    E = sorted(co.ch[(co.ch.group == "labelled") & (co.ch.eligible == True)].child.astype(int))   # noqa: E712
    sir = {c: float(ch.loc[c, "sir"]) for c in E}
    grid = cfg(pfc, "stats.ordinal_lambda")
    s, k = (int(v) for v in am["diag_unit"])
    src_unit = json.loads((ROOT / cfg(config, "paths.private_relative") / am["source_run"] / "units" / f"s{s}_k{k}.json").read_text())
    prior_calls = sum(u["n_ordinal_fits"] for u in _load_units(ROOT / cfg(config, "paths.private_relative") / am["source_run"]))
    out = {}
    for n in (1, 4):
        p = run["private"] / f"threads{n}.json"
        if not p.exists():
            with threadpool_limits(limits=n):
                write_json_atomic(p, run_unit(co, ch, E, sir, grid, s, k), private=True)
        out[n] = json.loads(p.read_text())
    calls = prior_calls + sum(u["n_ordinal_fits"] for u in out.values())
    if calls > int(cfg(config, "resources.ordinal_optimizer_calls_max")):
        raise ProvenanceError(f"ORDINAL_CAP_EXCEEDED:{calls}")

    def gap(a, b, key):
        return float(np.max(np.abs(np.asarray(a[key]) - np.asarray(b[key]))))
    summary = {"unit": [s, k], "n_test": len(out[1]["test_children"]),
               "expected_gap_threads1_vs_threads4": gap(out[1], out[4], "expected"),
               "proba_gap_threads1_vs_threads4": gap(out[1], out[4], "proba_raw"),
               "expected_gap_c0_001_vs_threads4": gap(src_unit, out[4], "expected"),
               "expected_gap_c0_001_vs_threads1": gap(src_unit, out[1], "expected"),
               "lambda": {n: u["lambda"] for n, u in out.items()}, "ordinal_calls_cumulative": int(calls)}
    write_json_atomic(run["public"] / "summary_c0_diag.json", summary, private=False)
    close_run(config, "headroom_diag", args.run, "COMPLETED", ordinal_calls_cumulative=int(calls))
    return summary


def cmd_headroom_rescore(args, config) -> dict:
    """Score the saved c0_001 unit outputs under addendum 001's tolerance (no refit, 0 ordinal calls)."""
    require_protocol(config)
    run = open_run("headroom_rescore", args.run, config, args=vars(args))
    am = config["headroom"]["amendment_001"]
    _, co = round1_cohort(config)
    ch = co.ch.set_index("child")
    E = sorted(co.ch[(co.ch.group == "labelled") & (co.ch.eligible == True)].child.astype(int))   # noqa: E712
    sir = {c: float(ch.loc[c, "sir"]) for c in E}
    units = _load_units(ROOT / cfg(config, "paths.private_relative") / am["source_run"])
    out = evaluate(config, co, E, sir, units, run, gate=am)
    out.update({"source_run": am["source_run"], "gate": "addendum_001", "ordinal_optimizer_calls_new": 0,
                "note": "exact refit of the original H14 specification within optimizer tolerance; not a bitwise "
                        "restoration of the archived parameters"})
    write_json_atomic(run["public"] / "summary_c0.json", out, private=False)
    close_run(config, "headroom_rescore", args.run, out["status"])
    return {"status": out["status"], "reproduction": out["reproduction"], "primary": out.get("primary"),
            "references": out.get("references")}


def evaluate(config, co, E, sir, units, run, gate: dict | None = None) -> dict:
    seeds = sorted({int(u["seed"]) for u in units})
    lat = {s: {} for s in seeds}
    ex = {s: {} for s in seeds}
    prob = {s: {} for s in seeds}
    prior = {s: {} for s in seeds}
    h = config["headroom"]
    L, floor, pseudo = int(h["levels"]), float(h["probability_floor"]), float(h["prior_pseudocount"])
    for u in units:
        pv = prior_vector(np.array(u["train_levels"]), L, pseudo)
        for i, c in enumerate(u["test_children"]):
            lat[u["seed"]][c], ex[u["seed"]][c] = u["latent"][i], u["expected"][i]
            prob[u["seed"]][c] = np.array(u["proba_raw"][i])
            prior[u["seed"]][c] = pv
    for s in seeds:
        if set(prob[s]) != set(E):
            raise ProvenanceError(f"C0_MISSING_CHILDREN:seed{s}")
    # ---- reproduction gate against the stored H14 outputs
    stored = h14_errors(config)["C"]
    err = {c: float(np.mean([abs(ex[s][c] - sir[c]) for s in seeds])) for c in E}
    max_err_diff = float(max(abs(err[c] - stored[c]) for c in E)) if set(stored) == set(E) else float("inf")
    high = {c: float(sir[c] > 3) for c in E}
    auc_seed = [st.auc([high[c] for c in E], [lat[s][c] for c in E]) for s in seeds]
    pub = json.loads((ROOT / cfg(config, "sources.pf_h14_public") / "summary_real.json").read_text())["b1"]["si"]["h14"]
    auc_gap = float(np.max(np.abs(np.array(auc_seed) - np.array(pub["auc_C"]["per_seed"]))))
    mae_gap = abs(float(np.mean(list(err.values()))) - float(pub["mae_C"]))
    if gate is None:                       # frozen protocol section 3
        tol_child, tol_mae, tol_auc = float(h["reproduce_tolerance"]), float(h["reproduce_tolerance"]), 1e-12
    else:                                  # addendum 001 (optimizer end-point tolerance)
        tol_child, tol_mae, tol_auc = float(gate["child_error_tol"]), float(gate["mae_tol"]), float(gate["auc_tol"])
    reproduced = max_err_diff <= tol_child and auc_gap <= tol_auc and mae_gap <= tol_mae
    out = {"n_children": len(E), "seeds": seeds,
           "reproduction": {"max_child_error_diff": max_err_diff, "auc_per_seed": auc_seed, "auc_gap": auc_gap,
                            "mae_gap": mae_gap, "stored_auc_mean": pub["auc_C"]["mean"], "stored_mae": pub["mae_C"],
                            "tolerances": {"child": tol_child, "mae": tol_mae, "auc": tol_auc},
                            "reproduced": bool(reproduced)}}
    if not reproduced:
        out["status"] = "PROBABILITY_SOURCE_UNRESOLVED"
        return out
    # ---- scoring of the probabilities (floor 1e-6 + renormalisation for every model alike)
    y = np.array([int(sir[c]) for c in E])
    per_seed, floors, rows = [], [], []
    ce_child = np.zeros((len(seeds), len(E)))
    br_child = np.zeros_like(ce_child)
    ce_prior = np.zeros_like(ce_child)
    br_prior = np.zeros_like(ce_child)
    Qs = []
    for j, s in enumerate(seeds):
        Q, fl = floor_probabilities(np.stack([prob[s][c] for c in E]), floor)
        Qp, _ = floor_probabilities(np.stack([prior[s][c] for c in E]), floor)
        floors.append(fl)
        Qs.append(Q)
        ce_child[j], br_child[j] = cross_entropy_bits(Q, y), brier(Q, y)
        ce_prior[j], br_prior[j] = cross_entropy_bits(Qp, y), brier(Qp, y)
        p_high = Q[:, 3:].sum(1)
        yb = (y > 3).astype(float)
        p_hb = np.clip(p_high, floor, 1 - floor)
        per_seed.append({"seed": s, "ce_bits": float(ce_child[j].mean()), "brier": float(br_child[j].mean()),
                         "mae_expected": float(np.mean([abs(ex[s][c] - sir[c]) for c in E])),
                         "auc_sir_gt3_from_proba": st.auc(yb, p_high), "binary_brier": float(np.mean((p_high - yb) ** 2)),
                         "binary_ce_bits": float(np.mean(-(yb * np.log2(p_hb) + (1 - yb) * np.log2(1 - p_hb)))),
                         "prior_ce_bits": float(ce_prior[j].mean()), "prior_brier": float(br_prior[j].mean())})
        for i, c in enumerate(E):
            rows.append({"seed": s, "child": c, "sir": int(sir[c]), **{f"p{l + 1}": float(Q[i, l]) for l in range(L)},
                         "latent": lat[s][c], "expected": ex[s][c], "ce_bits": float(ce_child[j, i]), "brier": float(br_child[j, i])})
    Qens = np.mean(Qs, 0)
    B = int(h["bootstrap_children"])
    idx = np.random.default_rng(int(h["bootstrap_seed"])).integers(0, len(E), size=(B, len(E)))

    def boot(v):
        bs = v[idx].mean(1)
        return {"mean": float(v.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}

    levels = {int(l): int((y == l).sum()) for l in range(1, L + 1)}
    out.update({
        "status": "COMPLETED",
        "target": "SIR 1-5 (archival, not contemporaneous validity)",
        "probability_floor": floor, "floor_effects": floors,
        "primary": {"ce_bits_mean_over_seeds": float(ce_child.mean()), "brier_mean_over_seeds": float(br_child.mean()),
                    "mae_expected_mean_over_seeds": float(np.mean([p["mae_expected"] for p in per_seed])),
                    "auc_sir_gt3_mean": float(np.mean([p["auc_sir_gt3_from_proba"] for p in per_seed]))},
        "per_seed": per_seed,
        "ensemble_sensitivity": {"ce_bits": float(cross_entropy_bits(Qens, y).mean()), "brier": float(brier(Qens, y).mean())},
        "references": {"train_prior_ce_bits": float(ce_prior.mean()), "train_prior_brier": float(br_prior.mean()),
                       "uniform_ce_bits": float(np.log2(L)), "uniform_brier": float(1 - 1 / L)},
        "child_bootstrap": {"ce_prior_minus_clinical": boot(ce_prior.mean(0) - ce_child.mean(0)),
                            "brier_prior_minus_clinical": boot(br_prior.mean(0) - br_child.mean(0)),
                            "clinical_ce_bits": boot(ce_child.mean(0)),
                            "note": "conditional on the fitted OOF predictions; not a coverage guarantee for CMI"},
        "calibration": {"level_counts": levels,
                        "observed_level_distribution": {l: levels[l] / len(E) for l in levels},
                        "mean_predicted_level_distribution": {l + 1: float(np.mean([Q[:, l].mean() for Q in Qs])) for l in range(L)},
                        "sir_gt3_observed_rate": float((y > 3).mean()),
                        "sir_gt3_mean_predicted": float(np.mean([Q[:, 3:].sum(1).mean() for Q in Qs])),
                        "ce_by_true_level": {int(l): (float(ce_child.mean(0)[y == l].mean()) if (y == l).any() else None)
                                             for l in range(1, L + 1)}},
        "identity": "I(Y;X|C) <= H(Y|C) <= CE(q_C); empirical OOF CE is not the population CE",
    })
    write_parquet_atomic(pd.DataFrame(rows), run["private"] / "sir_probabilities.parquet")
    return out
