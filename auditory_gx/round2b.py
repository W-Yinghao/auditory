"""Round-2 GPU routes: cross-paradigm zero-shot transfer, child-count scaling, personal k-session curves."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data as gxd
from . import train as gxt
from .runtime import cfg, done, open_run, private_dir, write_json_overwrite as write_json


def _torch():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("GX requires a GPU")
    return torch, torch.device("cuda")


def _binary(lane: gxd.Lane, torch):
    """Fold multi-class deviants into one 'deviant' class (standard vs any deviant)."""
    if lane.n_classes > 2:
        lane.y = (lane.y >= 1).long()
        lane.n_classes = 2
    return lane


# ----------------------------------------------------------------------------- GX12: leave-one-paradigm-out

def cmd_gx12_crossparadigm(args, config) -> dict:
    torch, device = _torch()
    run = open_run("gx12", args.run, config, args=vars(args))
    names = ["mff_puretone", "mff_bapa", "mff_unknown_hdev_ldev"]
    lanes = {n: _binary(gxd.load_lane(config, private_dir(config, args.stage_run), n, device), torch) for n in names}
    seeds = [int(s) for s in cfg(config, "folds.seeds")]
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    rows = []
    for test_name in names:
        test = lanes[test_name]
        test_groups = set(test.child_ids)
        train_names = [n for n in names if n != test_name]
        # concatenate training lanes, dropping any child who also appears in the test lane
        xs, ys, gs = [], [], []
        for n in train_names:
            l = lanes[n]
            keep = ~np.isin(np.array(l.child_ids)[l.child], list(test_groups))
            xs.append(l.x[torch.as_tensor(np.flatnonzero(keep), device=device)])
            ys.append(l.y[torch.as_tensor(np.flatnonzero(keep), device=device)])
            gs.append(np.array(l.child_ids)[l.child][keep])
        X = torch.cat(xs); Y = torch.cat(ys); G = np.concatenate(gs)
        uniq = np.unique(G)
        pooled = gxd.Lane(name="pooled", x=X, y=Y, n_classes=2, child=np.searchsorted(uniq, G), child_ids=list(uniq),
                          record=np.zeros(len(G), dtype=int), record_ids=["pooled"], onset_s=np.zeros(len(G)),
                          block=np.zeros(len(G), dtype=int), half=np.zeros(len(G), dtype=int), parity=np.zeros(len(G), dtype=int),
                          hist=np.zeros((len(G), 1)), age_child=np.full(len(uniq), np.nan), record_meta=[], qc_over=np.zeros(len(G), dtype=np.float32))
        for seed in seeds:
            tr_children, va_children = gxd.split_inner(np.arange(len(uniq)), val_frac, seed)
            gxt.seed_all(seed)
            model = gxt.build_model(config, pooled)
            info = gxt.fit(model, pooled, gxd.idx_of_children(pooled, tr_children), gxd.idx_of_children(pooled, va_children), config, seed=seed)
            logits = gxt.predict(model, test, np.arange(len(test.y)))
            y = test.y.cpu().numpy()
            for c in np.unique(test.child):
                sel = test.child == c
                m = gxt.child_metrics(logits[sel], y[sel], 2)
                rows.append({"test_lane": test_name, "train_lanes": "+".join(train_names), "seed": seed, "child": int(c),
                             "n_train_children": int(len(uniq)), **m, "epochs": info["epochs_run"]})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / "crossparadigm_child_metrics.csv", index=False)
    summary = {"run": args.run, "by_test_lane": {t: {"children": int(d.child.nunique()), "auc_child_mean": float(d.groupby("child").auc.mean().mean()),
                                                        "children_auc_gt_half": int((d.groupby("child").auc.mean() > 0.5).sum()),
                                                        "seed_range": [float(v) for v in d.groupby("seed").apply(lambda q: q.groupby("child").auc.mean().mean(), include_groups=False)]}
                                                    for t, d in f.groupby("test_lane")}}
    write_json(run["public"] / "summary_gx12.json", summary, private=False)
    done(run["private"], "gx12", summary)
    return summary


# ----------------------------------------------------------------------------- GX13: children-count scaling

def cmd_gx13_scaling(args, config) -> dict:
    torch, device = _torch()
    run = open_run("gx13", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    src = {}
    for m in lane.record_meta:
        src.setdefault(m["child"], m["source_cohort_evidence"])
    labels = np.array([src.get(c, "") for c in range(lane.n_children)])
    rng = np.random.default_rng(int(args.seed))
    # fixed stratified test panel
    panel = []
    for lab in np.unique(labels):
        idx = np.flatnonzero(labels == lab)
        k = max(1, int(round(12 * len(idx) / lane.n_children)))
        panel += list(rng.choice(idx, size=min(k, len(idx)), replace=False))
    panel = np.array(sorted(panel))
    pool = np.setdiff1d(np.arange(lane.n_children), panel)
    sizes = [s for s in (5, 10, 20, 40, 60) if s <= len(pool)]
    test_idx = gxd.idx_of_children(lane, panel)
    y = lane.y.cpu().numpy()
    rows = []
    for size in sizes:
        for draw in range(3):
            # stratified draw from the pool
            chosen = []
            for lab in np.unique(labels[pool]):
                idx = pool[labels[pool] == lab]
                k = int(round(size * len(idx) / len(pool)))
                chosen += list(rng.choice(idx, size=min(k, len(idx)), replace=False))
            chosen = np.array(sorted(set(chosen)))[:size]
            tr, va = gxd.split_inner(chosen, float(cfg(config, "folds.inner_validation_fraction")), int(args.seed) * 10 + draw)
            if len(va) == 0 or len(tr) == 0:
                continue
            gxt.seed_all(int(args.seed) * 100 + size * 3 + draw)
            model = gxt.build_model(config, lane)
            info = gxt.fit(model, lane, gxd.idx_of_children(lane, tr), gxd.idx_of_children(lane, va), config, seed=int(args.seed) * 100 + size * 3 + draw)
            logits = gxt.predict(model, lane, test_idx)
            aucs = []
            for c in panel:
                sel = lane.child[test_idx] == c
                m = gxt.child_metrics(logits[sel], y[test_idx][sel], lane.n_classes)
                if np.isfinite(m["auc"]):
                    aucs.append(m["auc"])
            rows.append({"train_children": int(len(chosen)), "draw": draw, "panel_children": int(len(panel)),
                         "auc_panel_mean": float(np.mean(aucs)), "n_train_trials": int(len(gxd.idx_of_children(lane, tr))),
                         "epochs": info["epochs_run"]})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"scaling_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "panel_children": int(len(panel)),
               "curve": {int(s): {"auc_mean": float(d.auc_panel_mean.mean()), "auc_min": float(d.auc_panel_mean.min()),
                                  "auc_max": float(d.auc_panel_mean.max())} for s, d in f.groupby("train_children")}}
    write_json(run["public"] / f"summary_gx13_{args.lane}.json", summary, private=False)
    done(run["private"], "gx13", summary)
    return summary


# ----------------------------------------------------------------------------- GX14: personal k-session learning curves

def cmd_gx14_personal(args, config) -> dict:
    torch, device = _torch()
    run = open_run("gx14", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y = lane.y.cpu().numpy()
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    seed = int(args.seed)
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(lane.n_children):
        recs = sorted(np.unique(lane.record[lane.child == c]))
        if len(recs) < int(args.min_records):
            continue
        for held in rng.choice(recs, size=min(int(args.heldout_sessions), len(recs)), replace=False):
            test = np.flatnonzero(lane.record == held)
            if min(np.sum(y[test] == 1), np.sum(y[test] == 0)) < 20:
                continue
            others = [r for r in recs if r != held]
            for k in sorted({kk for kk in (1, 2, 4, 7) if kk <= len(others)}):
                for draw in range(2):
                    chosen = list(rng.choice(others, size=k, replace=False))
                    own = np.flatnonzero(np.isin(lane.record, chosen))
                    order = own[np.argsort(lane.onset_s[own])]
                    n_val = max(8, int(round(val_frac * len(order))))
                    own_tr, own_va = order[:-n_val], order[-n_val:]
                    if min(np.sum(y[own_tr] == 1), np.sum(y[own_tr] == 0)) < 20:
                        continue
                    for mode in ("personal_only", "personal_plus_population"):
                        if mode == "personal_only":
                            tr_idx, va_idx = own_tr, own_va
                        else:
                            other_children = np.setdiff1d(np.arange(lane.n_children), [c])
                            tr_c, va_c = gxd.split_inner(other_children, val_frac, seed + k)
                            tr_idx = np.concatenate([gxd.idx_of_children(lane, tr_c), own_tr])
                            va_idx = np.concatenate([gxd.idx_of_children(lane, va_c), own_va])
                        gxt.seed_all(seed * 1000 + c * 10 + k + draw)
                        model = gxt.build_model(config, lane)
                        gxt.fit(model, lane, tr_idx, va_idx, config, seed=seed * 1000 + c * 10 + k + draw, max_epochs=25)
                        m = gxt.child_metrics(gxt.predict(model, lane, test), y[test], lane.n_classes)
                        rows.append({"child": int(c), "identity_group": lane.child_ids[c][:6], "held_out_record": lane.record_ids[int(held)],
                                     "k_sessions": k, "draw": draw, "mode": mode, "n_own_train": int(len(own_tr)), **m})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"personal_curves_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "children": int(f.child.nunique()) if len(f) else 0,
               "curve": {f"{m}/k={k}": {"auc_mean": float(d.auc.mean()), "n": int(len(d))} for (m, k), d in f.groupby(["mode", "k_sessions"])} if len(f) else {}}
    write_json(run["public"] / f"summary_gx14_{args.lane}.json", summary, private=False)
    done(run["private"], "gx14", summary)
    return summary
