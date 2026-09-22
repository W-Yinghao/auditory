"""Lane banks: all staged epochs of one lane resident on the GPU, with child/record/time structure."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from auditory_st.readout import history_design, partitions

from .runtime import cfg


@dataclass
class Lane:
    name: str
    x: torch.Tensor                 # [N, C, T] float16 on device
    y: torch.Tensor                 # [N] long on device
    n_classes: int
    child: np.ndarray               # [N] int
    child_ids: list                 # index -> identity group
    record: np.ndarray              # [N] int
    record_ids: list
    onset_s: np.ndarray
    block: np.ndarray
    half: np.ndarray                # early/late with embargo (-1 excluded)
    parity: np.ndarray              # odd/even 60 s blocks with embargo
    hist: np.ndarray                # [N, F]
    age_child: np.ndarray           # [n_children] months (nan if unknown)
    record_meta: list               # per record dict
    qc_over: np.ndarray = None      # [N] fraction of channels over the ptp threshold

    @property
    def n_children(self) -> int:
        return len(self.child_ids)

    def child_index_tensor(self, device) -> torch.Tensor:
        return torch.as_tensor(self.child, dtype=torch.long, device=device)


def list_stage(stage_private: Path, lane: str) -> list[Path]:
    paths = []
    for p in sorted((stage_private / "epochs").glob("*.npz")):
        with np.load(p, allow_pickle=False) as s:
            if str(s["lane"]) == lane:
                paths.append(p)
    return paths


def load_lane(config: dict, stage_private: Path, lane: str, device, *, accepted_only: bool = True,
              records: list[str] | None = None) -> Lane:
    paths = list_stage(stage_private, lane)
    if records is not None:
        paths = [p for p in paths if p.stem in set(records)]
    payloads = []
    for p in paths:
        with np.load(p, allow_pickle=False) as s:
            d = {k: s[k] for k in s.files}
        payloads.append(d)
    if not payloads:
        raise RuntimeError(f"LANE_EMPTY:{lane}")
    counts = {}
    for d in payloads:
        counts[int(d["n_channels"])] = counts.get(int(d["n_channels"]), 0) + 1
    majority = max(counts, key=counts.get)
    payloads = [d for d in payloads if int(d["n_channels"]) == majority]
    block_s = float(cfg(config, "blocks.block_seconds"))
    embargo_s = float(cfg(config, "blocks.embargo_seconds"))
    pre_s, post_s = float(cfg(config, "epoch.pre_seconds")), float(cfg(config, "epoch.post_seconds"))
    xs, ys, childs, recs, onsets, blocks, halves, parities = [], [], [], [], [], [], [], []
    pcs, pgs, prs, sts, meta, qcs = [], [], [], [], [], []
    child_ids: list = []
    ages: dict = {}
    for ri, d in enumerate(payloads):
        keep = d["accepted"].astype(bool) if accepted_only else np.ones(len(d["y"]), dtype=bool)
        if keep.sum() == 0:
            continue
        gid = str(d["identity_group"])
        if gid not in child_ids:
            child_ids.append(gid)
        ci = child_ids.index(gid)
        age = float(d["age_months"])
        if np.isfinite(age):
            ages.setdefault(ci, []).append(age)
        onset = d["onset_seconds"][keep]
        half, parity = partitions(onset, pre_s=pre_s, post_s=post_s, block_s=block_s, embargo_s=embargo_s)
        xs.append(d["x"][keep]); ys.append(d["y"][keep]); onsets.append(onset); qcs.append(d["qc_over_fraction"][keep])
        childs.append(np.full(int(keep.sum()), ci)); recs.append(np.full(int(keep.sum()), len(meta)))
        blocks.append(d["block_id"][keep]); halves.append(half); parities.append(parity)
        pcs.append(d["previous_code"][keep]); pgs.append(d["previous_gap_s"][keep])
        prs.append(d["previous_run_length"][keep]); sts.append(d["history_status"][keep])
        meta.append({"record_id": str(d["record_id"]), "identity_group": gid, "child": ci,
                     "n_trials": int(keep.sum()), "condition_clue": str(d["condition_clue"]),
                     "source_cohort_evidence": str(d["source_cohort_evidence"]),
                     "candidate_day_id": str(d["candidate_day_id"]), "age_months": age,
                     "device_duration_months": float(d["device_duration_months"]),
                     "record_scale": float(d["record_scale"]), "d1_seconds": float(d["d1_seconds"]),
                     "first_onset_s": float(onset.min()), "last_onset_s": float(onset.max())})
    H, _names, _first = history_design(np.concatenate(pcs), np.concatenate(pgs), np.concatenate(prs), np.concatenate(sts))
    x = torch.from_numpy(np.concatenate(xs)).to(device)
    y_np = np.concatenate(ys).astype(np.int64)
    age_child = np.full(len(child_ids), np.nan)
    for ci, vals in ages.items():
        age_child[ci] = float(np.mean(vals))
    return Lane(name=lane, x=x, y=torch.from_numpy(y_np).to(device), n_classes=int(y_np.max()) + 1,
                child=np.concatenate(childs), child_ids=child_ids, record=np.concatenate(recs),
                record_ids=[m["record_id"] for m in meta], onset_s=np.concatenate(onsets),
                block=np.concatenate(blocks), half=np.concatenate(halves), parity=np.concatenate(parities),
                hist=H, age_child=age_child, record_meta=meta, qc_over=np.concatenate(qcs).astype(np.float32))


def child_folds(n_children: int, n_folds: int, seed: int) -> list[np.ndarray]:
    """Held-out child sets: children shuffled by seed and dealt into n_folds."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(n_children)
    return [np.sort(order[k::n_folds]) for k in range(n_folds)]


def split_inner(train_children: np.ndarray, fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed + 1000)
    order = rng.permutation(train_children)
    n_val = max(1, int(round(fraction * len(order))))
    return np.sort(order[n_val:]), np.sort(order[:n_val])


def idx_of_children(lane: Lane, children: np.ndarray) -> np.ndarray:
    return np.flatnonzero(np.isin(lane.child, children))


def within_child_split(lane: Lane, child: int, part: np.ndarray, train_block: int, *,
                       val_fraction: float, seed: int, min_per_class: int) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Trials of one child: train on `train_block` of the partition, test on the other block."""
    mine = np.flatnonzero(lane.child == child)
    tr = mine[part[mine] == train_block]
    te = mine[part[mine] == 1 - train_block]
    y = lane.y.cpu().numpy()
    for k in range(lane.n_classes):
        if np.sum(y[tr] == k) < min_per_class or np.sum(y[te] == k) < min_per_class:
            return None
    # validation: the last `val_fraction` of the training block by time, so no trial-level leakage
    order = tr[np.argsort(lane.onset_s[tr])]
    n_val = max(8, int(round(val_fraction * len(order))))
    return order[:-n_val], order[-n_val:], te


def whiten_records(lane: Lane) -> None:
    """Euclidean alignment: per record, x <- R^{-1/2} x with R the mean trial covariance (label-free, all trials)."""
    dev = lane.x.device
    for r in np.unique(lane.record):
        sel = torch.as_tensor(np.flatnonzero(lane.record == r), device=dev)
        x = lane.x[sel].float()
        xc = x - x.mean(-1, keepdim=True)
        R = (xc @ xc.transpose(1, 2)).mean(0) / x.shape[-1]
        R = 0.9 * R + 0.1 * torch.diagonal(R).mean() * torch.eye(R.shape[0], device=dev)
        w, V = torch.linalg.eigh(R)
        Ri = V @ torch.diag(w.clamp(min=1e-8).rsqrt()) @ V.T
        lane.x[sel] = (Ri @ x).to(lane.x.dtype)
