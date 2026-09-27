"""Cohort, labels, eligibility, label-free folds and fixed-budget draws (protocol sections 1-3).

Mirrors auditory_gx.data.load_lane's record/child ordering exactly (same staged files, same
majority-channel filter, same accepted-only rule), so GPU jobs can assert equality.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .runtime import ROOT, cfg, read_json, save_npz_atomic, stable_int, write_csv_atomic, write_json_atomic

GROUP_ORDER = ("labelled", "nh", "unlabelled")


def _stage_paths(config: dict) -> list[Path]:
    stage = ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run") / "epochs"
    return sorted(stage.glob("*.npz"))


def lane_records(config: dict) -> tuple[pd.DataFrame, dict]:
    """Per-record metadata in load_lane order plus per-trial arrays (accepted trials only)."""
    lane = cfg(config, "sources.lane")
    payloads = []
    for p in _stage_paths(config):
        with np.load(p, allow_pickle=False) as s:
            if str(s["lane"]) != lane:
                continue
            payloads.append({k: s[k] for k in ("record_id", "identity_group", "y", "accepted", "onset_seconds",
                                               "n_channels", "record_scale", "qc_over_fraction", "d1_seconds")})
    counts: dict[int, int] = {}
    for d in payloads:
        counts[int(d["n_channels"])] = counts.get(int(d["n_channels"]), 0) + 1
    majority = max(counts, key=counts.get)
    payloads = [d for d in payloads if int(d["n_channels"]) == majority]
    rows, child_ids = [], []
    t_rec, t_y, t_on, t_pos = [], [], [], []
    offset = 0
    for d in payloads:
        keep = d["accepted"].astype(bool)
        if keep.sum() == 0:
            continue
        gid = str(d["identity_group"])
        if gid not in child_ids:
            child_ids.append(gid)
        y = d["y"][keep].astype(np.int64)
        n = int(keep.sum())
        ri = len(rows)
        rows.append({"rec": ri, "record_id": str(d["record_id"]), "identity_group": gid, "child": child_ids.index(gid),
                     "n_epochs": int(len(d["y"])), "n_acc": n, "n_std": int((y == 0).sum()), "n_dev": int((y == 1).sum()),
                     "offset": offset, "record_scale": float(d["record_scale"]), "d1_seconds": float(d["d1_seconds"]),
                     "qc_over_mean": float(np.mean(d["qc_over_fraction"][keep]))})
        t_rec.append(np.full(n, ri)); t_y.append(y); t_on.append(d["onset_seconds"][keep].astype(np.float64))
        t_pos.append(np.arange(n))
        offset += n
    rec = pd.DataFrame(rows)
    rec["accept_fraction"] = rec.n_acc / rec.n_epochs
    trials = {"record": np.concatenate(t_rec), "y": np.concatenate(t_y), "onset": np.concatenate(t_on),
              "pos": np.concatenate(t_pos)}
    return rec, trials


def attach_labels(config: dict, rec: pd.DataFrame) -> pd.DataFrame:
    coh = pd.read_csv(ROOT / cfg(config, "sources.ha_cohort"))
    coh = coh.drop(columns=[c for c in coh.columns if c.lower() == "name"])
    coh = coh.rename(columns={"recording": "record_id", "age": "age_months", "duration": "duration_months",
                              "V": "muss", "A": "itmais", "CAP": "cap", "SIR": "sir"})
    keep = ["record_id", "age_months", "duration_months", "itmais", "muss", "cap", "sir"]
    rec = rec.merge(coh[keep], on="record_id", how="left")
    rec["labelled"] = rec.duration_months.notna()
    nh = pd.read_csv(ROOT / cfg(config, "sources.nh_override"))
    nh_ids = set(nh.record_id)
    rec["nh"] = rec.record_id.isin(nh_ids)
    nh_age = dict(zip(nh.record_id, nh.age_months))
    rec.loc[rec.nh, "age_months"] = rec.loc[rec.nh, "record_id"].map(nh_age)
    pta = pd.read_csv(ROOT / cfg(config, "sources.pta"))
    pta = pta.rename(columns={"recording_id": "record_id", "better_unaided_pta": "pta_unaided", "better_aided_pta": "pta_aided"})
    rec = rec.merge(pta[["record_id", "pta_unaided", "pta_aided"]], on="record_id", how="left")
    st = pd.read_csv(ROOT / cfg(config, "sources.st_records"), usecols=["record_id", "_d1_container_id", "source_cohort_evidence"])
    rec = rec.merge(st.rename(columns={"_d1_container_id": "d1_container_id", "source_cohort_evidence": "source"}),
                    on="record_id", how="left")
    s1 = float(cfg(config, "labels.stage1_min_months"))
    rec["stage"] = np.where(rec.labelled, (rec.duration_months >= s1).astype(float), np.nan)
    rec["new02"] = np.where(rec.labelled, (rec.duration_months <= float(cfg(config, "labels.new_max_months"))).astype(float), np.nan)
    rec["sir_high"] = np.where(rec.labelled, (rec.sir > float(cfg(config, "labels.sir_threshold"))).astype(float), np.nan)
    rec["fitting_age"] = rec.age_months - rec.duration_months
    k = int(cfg(config, "budget.k_per_class"))
    rec["has_draws"] = (rec.n_dev >= k) & (rec.n_std >= k)
    rec["eligible"] = rec.labelled & rec.has_draws                 # stage / SI analyses
    rec["nh_eligible"] = rec.nh & rec.has_draws                    # H5
    return rec


def child_table(rec: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c, g in rec.groupby("child"):
        lab = g[g.labelled]
        if len(lab) > 1:
            raise RuntimeError(f"MULTIPLE_LABELLED_VISITS:child{c}")
        if len(lab):
            group, primary = "labelled", int(lab.rec.iloc[0])
        elif g.nh.any():
            group, primary = "nh", int(g[g.nh].rec.iloc[0])
        else:
            group, primary = "unlabelled", int(g.sort_values("record_id").rec.iloc[0])
        rows.append({"child": int(c), "identity_group": g.identity_group.iloc[0], "group": group,
                     "primary_rec": primary, "n_records": int(len(g))})
    ch = pd.DataFrame(rows)
    pr = rec.set_index("rec")
    for col in ("stage", "new02", "sir", "sir_high", "muss", "age_months", "duration_months", "fitting_age", "eligible",
                "nh_eligible", "has_draws", "pta_unaided", "pta_aided"):
        ch[col] = ch.primary_rec.map(pr[col])
    return ch


def deal(children: list[int], groups: dict[int, str], n_folds: int, rng: np.random.Generator) -> dict[int, int]:
    """Children -> fold, dealt round-robin within each group (label-free stratification)."""
    out: dict[int, int] = {}
    for gname in GROUP_ORDER:
        members = sorted(c for c in children if groups[c] == gname)
        if not members:
            continue
        order = rng.permutation(members)
        start = int(rng.integers(n_folds))
        for i, c in enumerate(order):
            out[int(c)] = (start + i) % n_folds
    return out


def make_folds(config: dict, ch: pd.DataFrame) -> dict:
    groups = dict(zip(ch.child.astype(int), ch.group))
    children = sorted(groups)
    n_outer, n_inner = int(cfg(config, "folds.n_outer")), int(cfg(config, "folds.n_inner"))
    folds = {}
    for s in cfg(config, "folds.seeds"):
        outer = deal(children, groups, n_outer, np.random.default_rng(int(s)))
        inner = {}
        for k in range(n_outer):
            train = [c for c in children if outer[c] != k]
            inner[str(k)] = {str(c): f for c, f in deal(train, groups, n_inner, np.random.default_rng(int(s) * 1000 + k)).items()}
        folds[str(s)] = {"outer": {str(c): f for c, f in outer.items()}, "inner": inner}
    return folds


def make_draws(config: dict, rec: pd.DataFrame, trials: dict) -> dict:
    K, D = int(cfg(config, "budget.k_per_class")), int(cfg(config, "budget.draws"))
    key = config["budget"].get("draw_key", "pf_draw")          # v1 default; v2 uses fresh draws
    recs = rec[rec.has_draws].rec.to_numpy()
    dev = np.zeros((len(recs), D, K), dtype=np.int64)
    std = np.zeros((len(recs), D, K), dtype=np.int64)
    for i, r in enumerate(recs):
        m = trials["record"] == r
        y, pos = trials["y"][m], trials["pos"][m]
        for d in range(D):
            rng = np.random.default_rng(stable_int(key, rec.record_id.iloc[r], d))
            dev[i, d] = np.sort(rng.choice(pos[y == 1], K, replace=False))
            std[i, d] = np.sort(rng.choice(pos[y == 0], K, replace=False))
    return {"rec": recs, "dev": dev, "std": std}


def map_gx_children(config: dict, ch: pd.DataFrame) -> dict:
    """R4 matched pairs and R5 low-AUC children, mapped from GX lane indices to identity groups."""
    meta = pd.DataFrame(read_json(ROOT / cfg(config, "sources.gx_record_meta")))
    gx_gid = meta.groupby("child").identity_group.first().to_dict()
    gid_to_child = dict(zip(ch.identity_group, ch.child.astype(int)))
    pairs = pd.read_csv(ROOT / cfg(config, "sources.r4_pairs"))
    out_pairs = []
    for r in pairs.itertuples():
        out_pairs.append({"new_child": gid_to_child.get(gx_gid.get(int(r.new_child))),
                          "exp_child": gid_to_child.get(gx_gid.get(int(r.exp_child))),
                          "duration_exp": float(r.duration_exp)})
    r5 = pd.read_csv(ROOT / cfg(config, "sources.r5_child_table"))
    low = [gid_to_child.get(gx_gid.get(int(c))) for c in r5[r5.auc < 0.5].child]
    return {"pairs": out_pairs, "low_auc_children": low}


def cmd_prepare(args, config) -> dict:
    from .runtime import open_run
    run = open_run("prepare", args.run, config, args=vars(args))
    rec, trials = lane_records(config)
    rec = attach_labels(config, rec)
    ch = child_table(rec)
    folds = make_folds(config, ch)
    draws = make_draws(config, rec, trials)
    mapped = map_gx_children(config, ch)
    priv = run["private"]
    write_csv_atomic(rec, priv / "records.csv", private=True)
    write_csv_atomic(ch, priv / "children.csv", private=True)
    write_json_atomic(priv / "folds.json", folds, private=True)
    write_json_atomic(priv / "gx_mapped.json", mapped, private=True)
    save_npz_atomic(priv / "draws.npz", **draws)
    save_npz_atomic(priv / "trials.npz", **trials)
    # public: counts only
    lab = ch[ch.group == "labelled"]
    summary = {"records": int(len(rec)), "children": int(len(ch)), "trials": int(len(trials["y"])),
               "groups": {g: int((ch.group == g).sum()) for g in GROUP_ORDER},
               "labelled_eligible": int(lab.eligible.sum()),
               "stage_counts_eligible": {"stage0": int(((lab.stage == 0) & lab.eligible).sum()),
                                         "stage1": int(((lab.stage == 1) & lab.eligible).sum()),
                                         "new02": int(((lab.new02 == 1) & lab.eligible).sum())},
               "nh_eligible": int(ch[ch.group == "nh"].nh_eligible.sum()),
               "records_with_draws": int(rec.has_draws.sum()),
               "pairs_mapped": int(sum(p["new_child"] is not None and p["exp_child"] is not None for p in mapped["pairs"])),
               "low_auc_mapped": int(sum(c is not None for c in mapped["low_auc_children"])),
               "fold_sizes": {s: {str(k): int(sum(1 for f in v["outer"].values() if f == k)) for k in range(int(cfg(config, "folds.n_outer")))}
                              for s, v in folds.items()}}
    write_json_atomic(run["public"] / "summary_prepare.json", summary, private=False)
    return summary


class Cohort:
    """Loaded prepare outputs (used by every later command)."""

    def __init__(self, config: dict, run: str = "prepare_001"):
        from .runtime import private_dir
        base = private_dir(config, run)
        self.rec = pd.read_csv(base / "records.csv")
        self.ch = pd.read_csv(base / "children.csv")
        self.folds = read_json(base / "folds.json")
        self.mapped = read_json(base / "gx_mapped.json")
        with np.load(base / "draws.npz") as z:
            self.draw_rec, self.draw_dev, self.draw_std = z["rec"], z["dev"], z["std"]
        with np.load(base / "trials.npz") as z:
            self.t_record, self.t_y, self.t_onset, self.t_pos = z["record"], z["y"], z["onset"], z["pos"]
        self.n_trials = len(self.t_y)
        self.draw_row = {int(r): i for i, r in enumerate(self.draw_rec)}
        self.offset = self.rec.offset.to_numpy()
        self.seeds = [int(s) for s in self.folds]

    def outer(self, seed: int) -> dict[int, int]:
        return {int(c): int(f) for c, f in self.folds[str(seed)]["outer"].items()}

    def inner(self, seed: int, k: int) -> dict[int, int]:
        return {int(c): int(f) for c, f in self.folds[str(seed)]["inner"][str(k)].items()}

    def trial_idx_of_records(self, recs) -> np.ndarray:
        recs = np.asarray(list(recs), dtype=int)
        return np.flatnonzero(np.isin(self.t_record, recs))

    def records_of_children(self, children) -> np.ndarray:
        return self.rec[self.rec.child.isin(list(children))].rec.to_numpy()

    def budget_idx(self, rec: int, draw: int, cls: int) -> np.ndarray:
        row = self.draw_row[int(rec)]
        pos = (self.draw_dev if cls == 1 else self.draw_std)[row, draw]
        return self.offset[int(rec)] + pos

    def val_children(self, children, key) -> np.ndarray:
        children = np.sort(np.asarray(list(children), dtype=int))
        n_val = max(1, int(round(0.15 * len(children))))
        rng = np.random.default_rng(stable_int("pf_val", key))
        return np.sort(rng.choice(children, n_val, replace=False))
