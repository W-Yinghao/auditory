"""MFF combined-lane stimulus decoders per outer (seed, fold): exports for directions A (age), E (sessions), G (surprisal).

Per unit: one EEGNet M_o trained on the fold's training children (stimulus labels only, never age or clinical
labels). Exports: logit difference for every trial (held out for the fold's test children), and per-draw per-class
M_o embeddings for EVERY record with a fixed budget (single encoder -> commensurable across children).
"""
from __future__ import annotations

import json

import numpy as np
import torch

from auditory_pf import gpu

from .mff import MffCohort, load_mff_lane
from .runtime import cfg, mark_done, open_run, save_npz_atomic, stable_int, task_units, unit_done, write_json_atomic


def run_unit(cohort: MffCohort, lane, gx_config, config, s: int, k: int, out_dir) -> dict:
    outer = cohort.outer(s)
    test = sorted(c for c, f in outer.items() if f == k)
    train = sorted(c for c, f in outer.items() if f != k)
    val = set(cohort.val_children(train, ("M_o", s, k)).tolist())
    tr = [c for c in train if c not in val]
    model, info = gpu.train_stim(lane, gx_config, cohort.trial_idx_of_children(tr), cohort.trial_idx_of_children(sorted(val)),
                                 stable_int("dv_stim_mff", s, k) % (2 ** 31 - 1))
    (out_dir / "models").mkdir(mode=0o700, parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "models" / "M_o.pt")
    all_idx = np.arange(cohort.n_trials)
    diff = gpu.infer(model, lane, all_idx)
    recs = np.array(sorted(cohort.draw_row))
    idx = np.flatnonzero(np.isin(cohort.t_record, recs))
    _, e = gpu.infer(model, lane, idx, embed=True)
    D = cohort.draw_dev.shape[1]
    agg = np.full((len(cohort.rec), D, 2, e.shape[1]), np.nan, np.float32)
    for r in recs:
        for d in range(D):
            for cls in (0, 1):
                gi = cohort.budget_idx(int(r), d, cls)
                loc = np.searchsorted(idx, gi)
                if not np.array_equal(idx[loc], gi):
                    raise RuntimeError("BUDGET_INDEX_OUTSIDE_SET")
                agg[int(r), d, cls] = e[loc].mean(0)
    save_npz_atomic(out_dir / "exports.npz", diff=diff.astype(np.float32), agg=agg, test_children=np.asarray(test),
                    train_children=np.asarray(train))
    write_json_atomic(out_dir / "fit_info.json", {**info, "n_train_children": len(tr), "n_val": len(val), "n_test": len(test)}, private=True)
    return {"s": s, "k": k, "n_test": len(test), "epochs_run": info.get("epochs_run")}


def cmd_stim_mff(args, config) -> dict:
    dev = gpu.device()
    run = open_run("stim_mff", args.run, config, args=vars(args))
    cohort = MffCohort(config, args.prepare_run)
    lane, gx_config = load_mff_lane(config, cohort, dev)
    units = [(s, k) for s in cohort.seeds for k in range(int(cfg(config, "mff.n_outer")))]
    n = 0
    for s, k in task_units(units):
        out_dir = run["private"] / f"unit_s{s}_k{k}"
        if unit_done(out_dir / "DONE.json"):
            continue
        out_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = run_unit(cohort, lane, gx_config, config, s, k, out_dir)
        mark_done(out_dir / "DONE.json", info)
        print(json.dumps(info), flush=True)
        n += 1
    return {"units": n}
