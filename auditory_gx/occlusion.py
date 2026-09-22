"""Temporal and spatial occlusion of trained shared decoders: where/when does the readout draw its evidence?

Not an ERP and not channel selection: the trained cross-child network is evaluated on held-out
children with one 80 ms window (or one channel group) zeroed at a time; the drop in child-mean AUC
is the importance of that window / group. Uses the saved fold models of a `shared` GX1 run.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data as gxd
from . import train as gxt
from .runtime import cfg, done, open_run, private_dir, read_json, write_json_overwrite


def cmd_occlusion(args, config) -> dict:
    import torch
    device = torch.device("cuda")
    run = open_run("occlusion", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    base_private = private_dir(config, args.base_run)
    folds = read_json(base_private / "folds.json")
    rate = float(cfg(config, "epoch.rate_hz"))
    pre_s = float(cfg(config, "epoch.pre_seconds"))
    T = lane.x.shape[2]
    win, step = int(round(0.08 * rate)), int(round(0.04 * rate))
    starts = list(range(0, T - win + 1, step))
    y = lane.y.cpu().numpy()
    rows = []
    channel_groups = _channel_groups(lane.x.shape[1])
    for seed_str, fold_list in folds.items():
        if seed_str == "model":
            continue
        seed = int(seed_str)
        for k, test_children in enumerate(fold_list):
            state = torch.load(base_private / "models" / f"shared_s{seed}_f{k}.pt", map_location=device)
            model = gxt.build_model(config, lane)
            model.load_state_dict(state)
            model.to(device).eval()
            test_idx = gxd.idx_of_children(lane, np.asarray(test_children))
            base_logits = gxt.predict(model, lane, test_idx)
            base = _child_mean_auc(lane, test_idx, base_logits, y)
            x_backup = lane.x
            for s in starts:
                lane.x = x_backup.clone()
                lane.x[:, :, s:s + win] = 0
                auc = _child_mean_auc(lane, test_idx, gxt.predict(model, lane, test_idx), y)
                rows.append({"kind": "time", "seed": seed, "fold": k, "centre_s": (s + win / 2) / rate - pre_s,
                             "auc_base": base, "auc_occluded": auc, "drop": base - auc})
            for name, chans in channel_groups.items():
                lane.x = x_backup.clone()
                lane.x[:, chans, :] = 0
                auc = _child_mean_auc(lane, test_idx, gxt.predict(model, lane, test_idx), y)
                rows.append({"kind": "space", "seed": seed, "fold": k, "group": name, "n_channels": len(chans),
                             "auc_base": base, "auc_occluded": auc, "drop": base - auc})
            lane.x = x_backup
    frame = pd.DataFrame(rows)
    frame.to_csv(run["public"] / f"occlusion_{args.lane}.csv", index=False)
    time_curve = frame[frame.kind == "time"].groupby("centre_s").drop.mean()
    space = frame[frame.kind == "space"].groupby("group").drop.mean().sort_values(ascending=False)
    summary = {"run": args.run, "lane": args.lane, "base_auc_mean": float(frame.auc_base.mean()),
               "time_drop_curve": {f"{t:.2f}": float(v) for t, v in time_curve.items()},
               "peak_time_s": float(time_curve.idxmax()), "peak_drop": float(time_curve.max()),
               "space_drop": {g: float(v) for g, v in space.items()}}
    write_json_overwrite(run["public"] / f"summary_occlusion_{args.lane}.json", summary, private=False)
    done(run["private"], "occlusion", summary)
    return summary


def _child_mean_auc(lane, idx, logits, y) -> float:
    vals = []
    for c in np.unique(lane.child[idx]):
        sel = lane.child[idx] == c
        m = gxt.child_metrics(logits[sel], y[idx[sel]], lane.n_classes)
        if np.isfinite(m["auc"]):
            vals.append(m["auc"])
    return float(np.mean(vals)) if vals else float("nan")


def _channel_groups(n_channels: int) -> dict:
    """Coarse contiguous index groups (8 groups). Native layouts differ, so groups are index bands, not anatomy."""
    n_groups = 8 if n_channels >= 64 else 4
    edges = np.linspace(0, n_channels, n_groups + 1).astype(int)
    return {f"band_{i}_{edges[i]}-{edges[i + 1] - 1}": list(range(edges[i], edges[i + 1])) for i in range(n_groups)}
