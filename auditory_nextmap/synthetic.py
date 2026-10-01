"""Recoverable synthetic worlds for the age pipeline (execution spec section 11, at most 24 worlds).

Three world types x 8 fixed seeds, each with independent training and test children and the real fold geometry
(55 children, 5 outer folds x inner 3-fold selection): common-only (age lives in the class mean), contrast-only (age
lives in the deviant-minus-standard difference) and pure noise. The check is that the implementation can express a
strong planted signal in the right view and keeps negative risk differences; it is not a power estimate.
"""
from __future__ import annotations

import numpy as np

from . import age_readout as ar
from . import representations as rp
from .runtime import close_run, open_run, write_json_atomic

WORLD_TYPES = ("common_only", "contrast_only", "noise")


def make_world(kind: str, seed: int, n: int = 55, p: int = 192, signal: float = 3.0):
    rng = np.random.default_rng(seed)
    age = rng.uniform(6, 186, n)
    a = (age - age.mean()) / age.std()
    load = rng.normal(size=p) / np.sqrt(p)
    base = rng.normal(size=(n, p))                      # child-specific background shared by both classes
    mu0 = base + 0.5 * rng.normal(size=(n, p))
    mu1 = base + 0.5 * rng.normal(size=(n, p)) + 0.3     # constant deviant offset (no age information)
    if kind == "common_only":
        mu0 = mu0 + signal * np.outer(a, load)
        mu1 = mu1 + signal * np.outer(a, load)
    elif kind == "contrast_only":
        mu1 = mu1 + signal * np.outer(a, load)
    elif kind != "noise":
        raise ValueError(kind)
    return age, mu0, mu1


def evaluate_world(kind: str, seed: int, config: dict) -> dict:
    age, mu0, mu1 = make_world(kind, seed)
    n = len(age)
    folds = np.random.default_rng(seed + 1).permutation(n) % 5
    a = config["age"]
    errs = {v: np.zeros(n) for v in ("common", "contrast", "joint", "median")}
    for k in range(5):
        tr = np.flatnonzero(folds != k)
        te = np.flatnonzero(folds == k)
        rows = np.concatenate([tr, te])
        y = age[rows]
        for view in ("common", "contrast", "joint"):
            design = (lambda trr, evr, view=view: rp.paired_design(view, mu0[rows], mu1[rows], trr, evr))
            res = ar.select_and_fit(design, y, len(tr), np.arange(len(tr), n), kind="ridge", alphas=a["alpha_sse"],
                                    inner_folds=int(a["inner_folds"]), inner_seed=seed * 10 + k,
                                    tie_tol=float(a["tie_tolerance"]), ledger=[], key={"world": kind, "seed": seed})
            errs[view][te] = np.abs(res["pred"] - age[te])
        errs["median"][te] = np.abs(np.median(age[tr]) - age[te])
    mae = {v: float(e.mean()) for v, e in errs.items()}
    g = float((errs["common"] - errs["joint"]).mean())
    if kind == "common_only":
        ok = mae["common"] < 0.6 * mae["median"]
    elif kind == "contrast_only":
        ok = mae["joint"] < 0.8 * mae["common"] and g > 0
    else:
        ok = min(mae["common"], mae["joint"], mae["contrast"]) > 0.8 * mae["median"]
    return {"world": kind, "seed": seed, "mae": mae, "G_D_given_C": g, "expected_pattern": bool(ok)}


def cmd_synthetic(args, config) -> dict:
    run = open_run("synthetic", args.run, config, args=vars(args))
    seeds = list(range(8))
    if len(WORLD_TYPES) * len(seeds) > int(config["resources"]["synthetic_worlds_max"]):
        raise RuntimeError("SYNTHETIC_CAP")
    worlds = [evaluate_world(kind, 900 + s, config) for kind in WORLD_TYPES for s in seeds]
    out = {"n_worlds": len(worlds), "worlds": worlds,
           "pattern_rate": {kind: float(np.mean([w["expected_pattern"] for w in worlds if w["world"] == kind]))
                            for kind in WORLD_TYPES},
           "negative_G_kept": bool(any(w["G_D_given_C"] < 0 for w in worlds))}
    write_json_atomic(run["public"] / "summary_synthetic.json", out, private=False)
    close_run(config, "synthetic", args.run, "COMPLETED")
    return {"pattern_rate": out["pattern_rate"], "negative_G_kept": out["negative_G_kept"]}
