"""B1 upstream: stage-label-free stimulus decoders per outer (seed, fold) and their held-out exports.

Per unit (s, k):
  M_o      trained on all outer-training children (all visits)            -> scores outer-test children
  M_i x5   trained on 4/5 of the outer-training children (inner folds)    -> scores each training child held out
  M_pre    pre-stimulus-only EEGNet, same children as M_o                 -> H19 false-positive control
  M_13     only >=13-month labelled training children (labelled visits)   -> H8
  L_o      full-window linear baseline, same children as M_o              -> reported beside M_o
Exports: held-out trial logit differences (all lane trials), per-draw per-class aggregated embeddings,
the 19-window time-occlusion logit differences, and D-averaged aggregated embeddings under the
25 occlusions (19 windows + 6 channel groups).
"""
from __future__ import annotations

import json

import numpy as np
import torch

from . import gpu
from .cohort import Cohort
from .runtime import cfg, mark_done, open_run, save_npz_atomic, stable_int, task_units, unit_done, write_json_atomic


def unit_list(cohort: Cohort, n_outer: int) -> list[tuple[int, int]]:
    return [(s, k) for s in cohort.seeds for k in range(n_outer)]


def _seed(*key) -> int:
    return stable_int("pf_stim", *key) % (2 ** 31 - 1)


def _idx_children(cohort: Cohort, children) -> np.ndarray:
    return cohort.trial_idx_of_records(cohort.records_of_children(children))


def run_unit(cohort: Cohort, lane, lane_pre, gx_config, config, s: int, k: int, out_dir) -> dict:
    outer = cohort.outer(s)
    inner = cohort.inner(s, k)
    test_children = sorted(c for c, f in outer.items() if f == k)
    train_children = sorted(c for c, f in outer.items() if f != k)
    models, infos = {}, {}

    def fit(key, children, *, which_lane=None, linear=False, records=None):
        children = sorted(children)
        val = cohort.val_children(children, (key, s, k))
        tr = [c for c in children if c not in set(val)]
        if records is None:
            tr_idx, va_idx = _idx_children(cohort, tr), _idx_children(cohort, val)
        else:  # restricted to given records (M_13: labelled visits only)
            recs = set(int(r) for r in records)
            tr_idx = cohort.trial_idx_of_records([r for r in cohort.records_of_children(tr) if r in recs])
            va_idx = cohort.trial_idx_of_records([r for r in cohort.records_of_children(val) if r in recs])
        model, info = gpu.train_stim(which_lane or lane, gx_config, tr_idx, va_idx, _seed(key, s, k), linear=linear)
        models[key] = model
        infos[key] = {**info, "n_train_children": len(tr), "n_val_children": len(val), "n_train_trials": int(len(tr_idx))}
        torch.save(model.state_dict(), out_dir / "models" / f"{key}.pt")

    (out_dir / "models").mkdir(mode=0o700, parents=True, exist_ok=True)
    fit("M_o", train_children)
    for i in range(int(cfg(config, "folds.n_inner"))):
        fit(f"M_i{i}", [c for c in train_children if inner[c] != i])
    fit("M_pre", train_children, which_lane=lane_pre)
    ch = cohort.ch.set_index("child")
    stage1 = [c for c in train_children if ch.loc[c, "group"] == "labelled" and ch.loc[c, "stage"] == 1]
    lab_recs = cohort.rec[cohort.rec.labelled].rec.to_numpy()
    fit("M_13", stage1, records=lab_recs)
    fit("L_o", train_children, linear=True)

    N = cohort.n_trials
    n_rec = len(cohort.rec)
    D, K = cohort.draw_dev.shape[1], cohort.draw_dev.shape[2]
    occl = gpu.occlusions(config, lane.x.shape[2])
    n_time = sum(o["kind"] == "time" for o in occl)
    diff_base = np.full(N, np.nan, np.float32)
    diff_occ = np.full((len(occl), N), np.nan, np.float32)
    agg_base = np.full((n_rec, D, 2, 192), np.nan, np.float32)
    agg_occ = np.full((len(occl), n_rec, 2, 192), np.nan, np.float32)
    held_by = {}
    for c in test_children:
        held_by[c] = "M_o"
    for c in train_children:
        held_by[c] = f"M_i{inner[c]}"
    for key in ["M_o"] + [f"M_i{i}" for i in range(int(cfg(config, "folds.n_inner")))]:
        kids = [c for c, m in held_by.items() if m == key]
        recs = cohort.records_of_children(kids)
        idx = cohort.trial_idx_of_records(recs)
        passes = [None] + occl
        for pi, oc in enumerate(passes):
            d, e = gpu.infer(models[key], lane, idx, occl=oc, embed=True)
            if pi == 0:
                diff_base[idx] = d
            else:
                diff_occ[pi - 1, idx] = d
            for r in recs:
                if int(r) not in cohort.draw_row:
                    continue
                per_draw = np.zeros((D, 2, e.shape[1]), np.float32)
                for dd in range(D):
                    for cls in (0, 1):
                        gi = cohort.budget_idx(int(r), dd, cls)
                        loc = np.searchsorted(idx, gi)
                        if not np.array_equal(idx[loc], gi):
                            raise RuntimeError("BUDGET_INDEX_OUTSIDE_MODEL_SET")
                        per_draw[dd, cls] = e[loc].mean(0)
                if pi == 0:
                    agg_base[int(r)] = per_draw
                else:
                    agg_occ[pi - 1, int(r)] = per_draw.mean(0)
    test_idx = _idx_children(cohort, test_children)
    diff_pre = np.full(N, np.nan, np.float32)
    diff_13 = np.full(N, np.nan, np.float32)
    diff_lin = np.full(N, np.nan, np.float32)
    diff_pre[test_idx] = gpu.infer(models["M_pre"], lane_pre, test_idx)
    diff_13[test_idx] = gpu.infer(models["M_13"], lane, test_idx)
    diff_lin[test_idx] = gpu.infer(models["L_o"], lane, test_idx)
    save_npz_atomic(out_dir / "exports.npz", diff_base=diff_base, diff_occ=diff_occ, agg_base=agg_base, agg_occ=agg_occ,
                    diff_pre=diff_pre, diff_13=diff_13, diff_lin=diff_lin,
                    test_children=np.asarray(test_children), train_children=np.asarray(train_children),
                    held_model=np.asarray([held_by.get(int(c), "") for c in cohort.ch.child]),
                    occl_names=np.asarray([o["name"] for o in occl]), n_time=np.int64(n_time))
    write_json_atomic(out_dir / "fit_info.json", infos, private=True)
    return {"s": s, "k": k, "n_test": len(test_children), "fits": {k2: v.get("epochs_run") for k2, v in infos.items()}}


def cmd_stim(args, config) -> dict:
    dev = gpu.device()
    run = open_run("stim", args.run, config, args=vars(args))
    cohort = Cohort(config, args.prepare_run)
    lane, gx_config = gpu.load_lane_checked(config, cohort, dev)
    pre = int(round(0.2 * 250))
    lane_pre = gpu.masked_lane(lane, 0, pre)
    units = unit_list(cohort, int(cfg(config, "folds.n_outer")))
    if args.only:
        units = [u for u in units if f"{u[0]}_{u[1]}" in set(args.only.split(","))]
    out = []
    for s, k in task_units(units):
        out_dir = run["private"] / f"unit_s{s}_k{k}"
        marker = out_dir / "DONE.json"
        if unit_done(marker):
            continue
        out_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = run_unit(cohort, lane, lane_pre, gx_config, config, s, k, out_dir)
        mark_done(marker, info)
        out.append(info)
        print(json.dumps(info), flush=True)
    return {"units_run": len(out)}


# ----------------------------------------------------------------------------- correction: single-encoder embeddings
# Embeddings of separately trained networks do not share a coordinate system, so model (b) as written in the
# protocol (training children embedded by inner networks M_i, test children by M_o) is invalid by construction.
# The correction embeds EVERY child with the fold's M_o (standard frozen-encoder probe; test children are still
# never in any upstream fit). Inference only; no model is retrained.

def reembed_unit(cohort: Cohort, lane, gx_config, config, s: int, k: int, unit_dir) -> dict:
    model = gpu.gxt.build_model(gx_config, lane)
    model.load_state_dict(torch.load(unit_dir / "models" / "M_o.pt", map_location=lane.x.device))
    model.to(lane.x.device).eval()
    n_rec = len(cohort.rec)
    D = cohort.draw_dev.shape[1]
    occl = gpu.occlusions(config, lane.x.shape[2])
    recs = np.array(sorted(cohort.draw_row))
    idx = cohort.trial_idx_of_records(recs)
    agg_base = np.full((n_rec, D, 2, 192), np.nan, np.float32)
    agg_occ = np.full((len(occl), n_rec, 2, 192), np.nan, np.float32)
    for pi, oc in enumerate([None] + occl):
        _, e = gpu.infer(model, lane, idx, occl=oc, embed=True)
        for r in recs:
            per_draw = np.zeros((D, 2, e.shape[1]), np.float32)
            for dd in range(D):
                for cls in (0, 1):
                    gi = cohort.budget_idx(int(r), dd, cls)
                    loc = np.searchsorted(idx, gi)
                    if not np.array_equal(idx[loc], gi):
                        raise RuntimeError("BUDGET_INDEX_OUTSIDE_SET")
                    per_draw[dd, cls] = e[loc].mean(0)
            if pi == 0:
                agg_base[int(r)] = per_draw
            else:
                agg_occ[pi - 1, int(r)] = per_draw.mean(0)
    save_npz_atomic(unit_dir / "exports_mo.npz", agg_base=agg_base, agg_occ=agg_occ,
                    occl_names=np.asarray([o["name"] for o in occl]))
    return {"s": s, "k": k, "records": int(len(recs))}


def cmd_reembed(args, config) -> dict:
    dev = gpu.device()
    run = open_run("reembed", args.run, config, args=vars(args))
    cohort = Cohort(config, args.prepare_run)
    lane, gx_config = gpu.load_lane_checked(config, cohort, dev)
    n = 0
    for s, k in task_units(unit_list(cohort, int(cfg(config, "folds.n_outer")))):
        unit_dir = run["private"] / f"unit_s{s}_k{k}"
        if (unit_dir / "exports_mo.npz").exists():
            continue
        print(json.dumps(reembed_unit(cohort, lane, gx_config, config, s, k, unit_dir)), flush=True)
        n += 1
    return {"units": n}


# ----------------------------------------------------------------------------- round 2 (PF2): core models only
# Per unit: M_o + 5 inner M_i (curves need held-out children); the 19 time-window occlusion logit differences for
# every trial; and single-encoder (M_o) per-draw per-class aggregates for EVERY child (the corrected (b) design).

def run_unit2(cohort: Cohort, lane, gx_config, config, s: int, k: int, out_dir) -> dict:
    outer = cohort.outer(s)
    inner = cohort.inner(s, k)
    test_children = sorted(c for c, f in outer.items() if f == k)
    train_children = sorted(c for c, f in outer.items() if f != k)
    (out_dir / "models").mkdir(mode=0o700, parents=True, exist_ok=True)
    models, infos = {}, {}

    def fit(key, children):
        children = sorted(children)
        val = cohort.val_children(children, (key, s, k))
        tr = [c for c in children if c not in set(val)]
        model, info = gpu.train_stim(lane, gx_config, _idx_children(cohort, tr), _idx_children(cohort, val), _seed(key, s, k))
        models[key] = model
        infos[key] = {**info, "n_train_children": len(tr), "n_val_children": len(val)}
        torch.save(model.state_dict(), out_dir / "models" / f"{key}.pt")

    fit("M_o", train_children)
    n_inner = int(cfg(config, "folds.n_inner"))
    for i in range(n_inner):
        fit(f"M_i{i}", [c for c in train_children if inner[c] != i])
    N, n_rec = cohort.n_trials, len(cohort.rec)
    D = cohort.draw_dev.shape[1]
    times = [o for o in gpu.occlusions(config, lane.x.shape[2]) if o["kind"] == "time"]
    diff_base = np.full(N, np.nan, np.float32)
    diff_occ = np.full((len(times), N), np.nan, np.float32)
    held_by = {c: "M_o" for c in test_children}
    held_by.update({c: f"M_i{inner[c]}" for c in train_children})
    for key in ["M_o"] + [f"M_i{i}" for i in range(n_inner)]:
        idx = cohort.trial_idx_of_records(cohort.records_of_children([c for c, m in held_by.items() if m == key]))
        diff_base[idx] = gpu.infer(models[key], lane, idx)
        for w, oc in enumerate(times):
            diff_occ[w, idx] = gpu.infer(models[key], lane, idx, occl=oc)
    recs = np.array(sorted(cohort.draw_row))
    idx = cohort.trial_idx_of_records(recs)
    _, e = gpu.infer(models["M_o"], lane, idx, embed=True)
    agg = np.full((n_rec, D, 2, 192), np.nan, np.float32)
    for r in recs:
        for dd in range(D):
            for cls in (0, 1):
                gi = cohort.budget_idx(int(r), dd, cls)
                loc = np.searchsorted(idx, gi)
                if not np.array_equal(idx[loc], gi):
                    raise RuntimeError("BUDGET_INDEX_OUTSIDE_SET")
                agg[int(r), dd, cls] = e[loc].mean(0)
    save_npz_atomic(out_dir / "exports.npz", diff_base=diff_base, diff_occ=diff_occ, agg_base=agg,
                    test_children=np.asarray(test_children), train_children=np.asarray(train_children),
                    occl_names=np.asarray([o["name"] for o in times]), n_time=np.int64(len(times)),
                    agg_source=np.asarray("single_encoder_M_o"))
    write_json_atomic(out_dir / "fit_info.json", infos, private=True)
    return {"s": s, "k": k, "n_test": len(test_children), "fits": {a: v.get("epochs_run") for a, v in infos.items()}}


def cmd_stim2(args, config) -> dict:
    dev = gpu.device()
    run = open_run("stim2", args.run, config, args=vars(args))
    cohort = Cohort(config, args.prepare_run)
    lane, gx_config = gpu.load_lane_checked(config, cohort, dev)
    n = 0
    for s, k in task_units(unit_list(cohort, int(cfg(config, "folds.n_outer")))):
        out_dir = run["private"] / f"unit_s{s}_k{k}"
        marker = out_dir / "DONE.json"
        if unit_done(marker):
            continue
        out_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = run_unit2(cohort, lane, gx_config, config, s, k, out_dir)
        mark_done(marker, info)
        print(json.dumps(info), flush=True)
        n += 1
    return {"units_run": n}
