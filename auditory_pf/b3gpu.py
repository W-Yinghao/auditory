"""B3 GPU parts: H18 (children x trials at equal total) and H20 (leave-one-child-out scaling)."""
from __future__ import annotations

import json

import numpy as np
from sklearn.metrics import roc_auc_score

from . import gpu
from .cohort import Cohort
from .runtime import cfg, open_run, save_npz_atomic, stable_int, task_units


def child_trial_order(cohort: Cohort, child: int) -> np.ndarray:
    """Global trial indices of one child: primary visit first (time order), then other visits by record id."""
    ch = cohort.ch.set_index("child")
    primary = int(ch.loc[child, "primary_rec"])
    recs = cohort.rec[cohort.rec.child == child].sort_values("record_id").rec.tolist()
    recs = [primary] + [r for r in recs if r != primary]
    out = []
    for r in recs:
        idx = np.flatnonzero(cohort.t_record == r)
        out.append(idx[np.argsort(cohort.t_onset[idx], kind="stable")])
    return np.concatenate(out)


def primary_auc(cohort: Cohort, lane, model, child: int) -> float:
    r = int(cohort.ch.set_index("child").loc[child, "primary_rec"])
    idx = np.flatnonzero(cohort.t_record == r)
    d = gpu.infer(model, lane, idx)
    y = cohort.t_y[idx]
    return float(roc_auc_score(y, d)) if len(np.unique(y)) == 2 else float("nan")


def _fit_on(cohort, lane, gx_config, children_trials: dict[int, np.ndarray], key) -> object:
    kids = sorted(children_trials)
    val = set(cohort.val_children(kids, key).tolist())
    tr = np.concatenate([children_trials[c] for c in kids if c not in val])
    va = np.concatenate([children_trials[c] for c in kids if c in val])
    model, _ = gpu.train_stim(lane, gx_config, np.sort(tr), np.sort(va), stable_int("pf_b3", *key) % (2 ** 31 - 1))
    return model


def h18_units(cohort: Cohort, config) -> list:
    return [(p, r, a) for p in range(int(cfg(config, "b3.h18_panels"))) for r in cfg(config, "b3.h18_seeds")
            for a in range(len(cfg(config, "b3.h18_alloc")))]


def run_h18(cohort, lane, gx_config, config, p, r, a, out_path):
    kids = cohort.ch.child.to_numpy().astype(int)
    order = np.random.default_rng(stable_int("pf_h18_panels")).permutation(kids)
    size = int(cfg(config, "b3.h18_panel_size"))
    panel = np.sort(order[p * size:(p + 1) * size])
    n_child, per_child = cfg(config, "b3.h18_alloc")[a]
    pool = [int(c) for c in kids if c not in set(panel)]
    trials = {c: child_trial_order(cohort, c) for c in pool}
    elig = sorted(c for c in pool if len(trials[c]) >= per_child)
    rng = np.random.default_rng(stable_int("pf_h18_pick", p, r, a))
    chosen = sorted(rng.choice(elig, min(n_child, len(elig)), replace=False).tolist())
    model = _fit_on(cohort, lane, gx_config, {c: trials[c][:per_child] for c in chosen}, ("h18", p, r, a))
    aucs = np.array([primary_auc(cohort, lane, model, int(c)) for c in panel])
    save_npz_atomic(out_path, panel=panel, auc=aucs, n_children=np.int64(len(chosen)), per_child=np.int64(per_child),
                    n_eligible=np.int64(len(elig)))
    return {"p": p, "r": r, "alloc": a, "n_children": len(chosen), "eligible": len(elig), "mean_auc": float(np.nanmean(aucs))}


def run_h20(cohort, lane, gx_config, config, c, r, out_dir):
    kids = cohort.ch.child.to_numpy().astype(int)
    pool = np.array([k for k in kids if k != c])
    perm = np.random.default_rng(stable_int("pf_h20", c, r)).permutation(pool)
    res = {}
    for n in cfg(config, "b3.h20_sizes"):
        path = out_dir / f"c{c}_r{r}_n{n}.npz"
        if path.exists():
            continue
        subset = sorted(perm[:int(n)].tolist())
        model = _fit_on(cohort, lane, gx_config, {k: child_trial_order(cohort, k) for k in subset}, ("h20", c, r, n))
        auc = primary_auc(cohort, lane, model, int(c))
        save_npz_atomic(path, auc=np.float64(auc), child=np.int64(c), n=np.int64(n), seed=np.int64(r))
        res[int(n)] = auc
    return res


def cmd_b3gpu(args, config) -> dict:
    dev = gpu.device()
    run = open_run(f"b3gpu_{args.part}", args.run, config, args=vars(args))
    cohort = Cohort(config, args.prepare_run)
    lane, gx_config = gpu.load_lane_checked(config, cohort, dev)
    n = 0
    if args.part == "h18":
        for p, r, a in task_units(h18_units(cohort, config)):
            path = run["private"] / "h18" / f"p{p}_r{r}_a{a}.npz"
            if path.exists():
                continue
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            print(json.dumps(run_h18(cohort, lane, gx_config, config, p, r, a, path)), flush=True)
            n += 1
    elif args.part == "h20":
        units = [(int(c), int(r)) for c in cohort.ch.child for r in cfg(config, "b3.h20_seeds")]
        out_dir = run["private"] / "h20"
        out_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        for c, r in task_units(units):
            res = run_h20(cohort, lane, gx_config, config, c, r, out_dir)
            print(json.dumps({"c": c, "r": r, **{str(k): v for k, v in res.items()}}), flush=True)
            n += 1
    else:
        raise ValueError(args.part)
    return {"units": n}
