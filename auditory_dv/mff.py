"""MFF combined event lane (puretone + bapa + unknown_event + hdev/ldev), cohort, folds and fixed-budget draws.

The four GX MFF lanes are concatenated in LANES order; inside each lane records follow auditory_gx.data.load_lane
order (sorted staged files, 128-channel majority, accepted trials only). Classes are binary: standard = 0, any
deviant literal (devt, hdev, ldev) = 1. Children are unified across lanes by identity group.
"""
from __future__ import annotations

import types
from pathlib import Path

import numpy as np
import pandas as pd

from .runtime import ROOT, cfg, read_json, save_npz_atomic, stable_int, write_csv_atomic, write_json_atomic

LANES = ("mff_puretone", "mff_bapa", "mff_unknown_event", "mff_unknown_hdev_ldev")


def _stage_dir(config) -> Path:
    return ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run") / "epochs"


def mff_records(config) -> tuple[pd.DataFrame, dict]:
    rows, t_rec, t_y, t_on, t_pos = [], [], [], [], []
    child_ids: list[str] = []
    paths = sorted(_stage_dir(config).glob("*.npz"))
    offset = 0
    for lane in LANES:
        payloads = []
        for p in paths:
            with np.load(p, allow_pickle=False) as s:
                if str(s["lane"]) != lane:
                    continue
                payloads.append({k: s[k] for k in ("record_id", "identity_group", "y", "accepted", "onset_seconds", "n_channels",
                                                   "record_scale", "qc_over_fraction", "d1_seconds", "age_months",
                                                   "source_cohort_evidence")})
        counts: dict[int, int] = {}
        for d in payloads:
            counts[int(d["n_channels"])] = counts.get(int(d["n_channels"]), 0) + 1
        majority = max(counts, key=counts.get)
        for d in payloads:
            if int(d["n_channels"]) != majority:
                continue
            keep = d["accepted"].astype(bool)
            if keep.sum() == 0:
                continue
            gid = str(d["identity_group"])
            if gid not in child_ids:
                child_ids.append(gid)
            y = (d["y"][keep] > 0).astype(np.int64)
            n = int(keep.sum())
            ri = len(rows)
            rows.append({"rec": ri, "record_id": str(d["record_id"]), "lane": lane, "identity_group": gid,
                         "child": child_ids.index(gid), "n_acc": n, "n_std": int((y == 0).sum()), "n_dev": int((y == 1).sum()),
                         "offset": offset, "age_months": float(d["age_months"]), "source": str(d["source_cohort_evidence"]),
                         "d1_seconds": float(d["d1_seconds"]), "record_scale": float(d["record_scale"]),
                         "qc_over_mean": float(np.mean(d["qc_over_fraction"][keep])), "n_channels": majority})
            t_rec.append(np.full(n, ri)); t_y.append(y); t_on.append(d["onset_seconds"][keep].astype(np.float64))
            t_pos.append(np.arange(n))
            offset += n
    rec = pd.DataFrame(rows)
    trials = {"record": np.concatenate(t_rec), "y": np.concatenate(t_y), "onset": np.concatenate(t_on), "pos": np.concatenate(t_pos)}
    return rec, trials


def child_table(rec: pd.DataFrame) -> pd.DataFrame:
    out = []
    lane_index = {l: i for i, l in enumerate(LANES)}
    for c, g in rec.groupby("child"):
        g = g.assign(li=g.lane.map(lane_index)).sort_values(["li", "record_id"])
        aged = g[np.isfinite(g.age_months)]
        primary = int(aged.rec.iloc[0]) if len(aged) else int(g.rec.iloc[0])
        out.append({"child": int(c), "identity_group": g.identity_group.iloc[0], "has_age": bool(len(aged)),
                    "age_months": float(aged.age_months.iloc[0]) if len(aged) else np.nan, "primary_rec": primary,
                    "n_records": int(len(g)), "lanes": "|".join(sorted(set(g.lane))),
                    "ci_label": bool(g.source.isin(["CI", "CIHA_label"]).any())})
    return pd.DataFrame(out)


def make_folds(config, ch: pd.DataFrame) -> dict:
    n_outer = int(cfg(config, "mff.n_outer"))
    folds = {}
    for s in cfg(config, "mff.seeds"):
        rng = np.random.default_rng(int(s))
        assign = {}
        for grp in (True, False):
            members = sorted(ch[ch.has_age == grp].child.astype(int))
            order = rng.permutation(members)
            start = int(rng.integers(n_outer))
            for i, c in enumerate(order):
                assign[int(c)] = (start + i) % n_outer
        folds[str(s)] = {str(c): f for c, f in assign.items()}
    return folds


def make_draws(config, rec: pd.DataFrame, trials: dict) -> dict:
    K, D = int(cfg(config, "budget.k_per_class")), int(cfg(config, "budget.draws"))
    ok = rec[(rec.n_dev >= K) & (rec.n_std >= K)].rec.to_numpy()
    dev = np.zeros((len(ok), D, K), np.int64)
    std = np.zeros((len(ok), D, K), np.int64)
    for i, r in enumerate(ok):
        m = trials["record"] == r
        y, pos = trials["y"][m], trials["pos"][m]
        for d in range(D):
            rng = np.random.default_rng(stable_int("dv_draw", rec.record_id.iloc[r], d))
            dev[i, d] = np.sort(rng.choice(pos[y == 1], K, replace=False))
            std[i, d] = np.sort(rng.choice(pos[y == 0], K, replace=False))
    return {"rec": ok, "dev": dev, "std": std}


def cmd_prepare_mff(args, config) -> dict:
    from .runtime import open_run
    run = open_run("prepare_mff", args.run, config, args=vars(args))
    rec, trials = mff_records(config)
    ch = child_table(rec)
    folds = make_folds(config, ch)
    draws = make_draws(config, rec, trials)
    priv = run["private"]
    write_csv_atomic(rec, priv / "records.csv", private=True)
    write_csv_atomic(ch, priv / "children.csv", private=True)
    write_json_atomic(priv / "folds.json", folds, private=True)
    save_npz_atomic(priv / "draws.npz", **draws)
    save_npz_atomic(priv / "trials.npz", **trials)
    summary = {"records": int(len(rec)), "children": int(len(ch)), "trials": int(len(trials["y"])),
               "records_by_lane": rec.lane.value_counts().to_dict(), "children_with_age": int(ch.has_age.sum()),
               "ci_label_children": int(ch.ci_label.sum()), "records_with_draws": int(len(draws["rec"])),
               "aged_children_with_draws": int(ch[ch.has_age & ch.primary_rec.isin(draws["rec"])].shape[0]),
               "hours": float(rec.d1_seconds.sum() / 3600)}
    write_json_atomic(run["public"] / "summary_prepare_mff.json", summary, private=False)
    return summary


class MffCohort:
    def __init__(self, config, run: str = "prepare_mff_001"):
        from .runtime import private_dir
        base = private_dir(config, run)
        self.rec = pd.read_csv(base / "records.csv")
        self.ch = pd.read_csv(base / "children.csv")
        self.folds = read_json(base / "folds.json")
        with np.load(base / "draws.npz") as z:
            self.draw_rec, self.draw_dev, self.draw_std = z["rec"], z["dev"], z["std"]
        with np.load(base / "trials.npz") as z:
            self.t_record, self.t_y, self.t_onset, self.t_pos = z["record"], z["y"], z["onset"], z["pos"]
        self.n_trials = len(self.t_y)
        self.offset = self.rec.offset.to_numpy()
        self.draw_row = {int(r): i for i, r in enumerate(self.draw_rec)}
        self.seeds = [int(s) for s in self.folds]
        self.child_of_trial = self.rec.child.to_numpy()[self.t_record]

    def outer(self, seed: int) -> dict[int, int]:
        return {int(c): int(f) for c, f in self.folds[str(seed)].items()}

    def trial_idx_of_children(self, children) -> np.ndarray:
        return np.flatnonzero(np.isin(self.child_of_trial, np.asarray(list(children))))

    def budget_idx(self, rec: int, draw: int, cls: int) -> np.ndarray:
        row = self.draw_row[int(rec)]
        return self.offset[int(rec)] + (self.draw_dev if cls == 1 else self.draw_std)[row, draw]

    def val_children(self, children, key) -> np.ndarray:
        children = np.sort(np.asarray(list(children), dtype=int))
        rng = np.random.default_rng(stable_int("dv_val", key))
        return np.sort(rng.choice(children, max(1, int(round(0.15 * len(children)))), replace=False))


def load_mff_lane(config, cohort: MffCohort, device):
    """GPU tensor of all accepted MFF trials in cohort order (verified against the cohort tables)."""
    import torch
    from auditory_gx import data as gxd
    from auditory_gx.runtime import load_config as gx_load_config
    gx_config = gx_load_config(cfg(config, "sources.gx_config"))
    stage_private = ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run")
    xs, ids = [], []
    for lane in LANES:
        ln = gxd.load_lane(gx_config, stage_private, lane, device)
        xs.append(ln.x)
        ids += list(ln.record_ids)
        del ln
    if ids != list(cohort.rec.record_id):
        raise RuntimeError("MFF_RECORD_ORDER_MISMATCH")
    x = torch.cat(xs)
    if x.shape[0] != cohort.n_trials:
        raise RuntimeError("MFF_TRIAL_COUNT_MISMATCH")
    y = torch.as_tensor(cohort.t_y, dtype=torch.long, device=device)
    return types.SimpleNamespace(x=x, y=y, n_classes=2), gx_config
