"""B1 model (c): end-to-end stage (and ordinal SIR) decoders on labelled visits (protocol 4.2, 4.4).

Variants (same encoder, same batch sequence, same step budget):
  rec      record-level loss: BCE on the mean logit of each record's 16 dev + 16 std epochs
  bc       broadcast loss: per-epoch BCE with the record label (each record equal weight)
  rec_dev  record-level loss, deviant epochs only (scores on deviant budgets)
  rec_std  record-level loss, standard epochs only
  ord      record-level cumulative-logit loss on SIR (1..5)
Permutation units re-run rec/bc with child-level permuted stage labels (R2).
"""
from __future__ import annotations

import json
import math

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from auditory_gx import train as gxt
from auditory_gx.models import EEGNet

from . import gpu
from .cohort import Cohort
from .runtime import cfg, open_run, save_npz_atomic, stable_int, task_units

VARIANTS_OBS = ("rec", "bc", "rec_dev", "rec_std", "ord")
VARIANTS_PERM = ("rec", "bc")


def permuted_labels(cohort: Cohort, p: int, column: str = "stage") -> dict[int, float]:
    """Child-level permutation among eligible labelled children (p = 0 is the observed labels)."""
    ch = cohort.ch[(cohort.ch.group == "labelled") & (cohort.ch.eligible == True)].sort_values("child")  # noqa: E712
    kids, vals = ch.child.to_numpy(), ch[column].to_numpy()
    if p > 0:
        vals = vals[np.random.default_rng(stable_int("pf_perm", p)).permutation(len(vals))]
    return dict(zip(kids.astype(int), vals.astype(float)))


class OrdinalHead(nn.Module):
    """Cumulative-logit thresholds theta_1 < ... < theta_{K-1} (K = 5 SIR levels)."""

    def __init__(self, n_levels: int = 5):
        super().__init__()
        self.first = nn.Parameter(torch.tensor(-1.5))
        self.gaps = nn.Parameter(torch.zeros(n_levels - 2))

    def thresholds(self) -> torch.Tensor:
        return torch.cat([self.first.view(1), self.first + torch.cumsum(F.softplus(self.gaps) + 1e-3, 0)])

    def nll(self, z: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """z: [R] latent; y: [R] long in 0..K-1."""
        th = self.thresholds()
        cdf = torch.sigmoid(th[None, :] - z[:, None])                     # P(Y <= j), j = 0..K-2
        cdf = torch.cat([torch.zeros_like(z)[:, None], cdf, torch.ones_like(z)[:, None]], 1)
        prob = (cdf[:, 1:] - cdf[:, :-1]).clamp(min=1e-6)
        return -torch.log(prob.gather(1, y[:, None])).mean()


def _model(gx_config, lane) -> EEGNet:
    m = gx_config["model"]
    return EEGNet(lane.x.shape[1], lane.x.shape[2], 1, F1=int(m["F1"]), D=int(m["D"]), F2=int(m["F2"]),
                  k1=int(m["k1"]), k2=int(m["k2"]), dropout=float(m["dropout"]))


def _class_idx(cohort: Cohort, rec: int) -> tuple[np.ndarray, np.ndarray]:
    m = cohort.t_record == rec
    g = np.flatnonzero(m)
    y = cohort.t_y[m]
    return g[y == 0], g[y == 1]


@torch.no_grad()
def _record_scores(model, lane, cohort: Cohort, recs, *, classes=(0, 1), draws=None, occl=None) -> np.ndarray:
    """[len(recs), D] mean latent over each fixed-budget draw (only the given classes)."""
    D = cohort.draw_dev.shape[1] if draws is None else len(draws)
    draws = range(cohort.draw_dev.shape[1]) if draws is None else draws
    out = np.full((len(recs), D), np.nan, np.float32)
    for i, r in enumerate(recs):
        idx = np.concatenate([np.concatenate([cohort.budget_idx(int(r), d, c) for c in classes]) for d in draws])
        z = gpu.infer(model, lane, idx, occl=occl)
        out[i] = z.reshape(len(list(draws)), -1).mean(1)
    return out


def fit_e2e(cohort: Cohort, lane, gx_config, config, variant: str, train_recs, val_recs, labels: dict, seed: int):
    e = cfg(config, "e2e")
    B, m = int(e["records_per_batch"]), int(e["epochs_per_class"])
    spe, max_ep, patience = int(e["steps_per_epoch"]), int(e["max_epochs"]), int(e["patience"])
    dev = lane.x.device
    gxt.seed_all(seed)
    model = _model(gx_config, lane).to(dev)
    head = OrdinalHead().to(dev) if variant == "ord" else None
    params = list(model.parameters()) + (list(head.parameters()) if head is not None else [])
    t = gx_config["train"]
    opt = torch.optim.AdamW(params, lr=float(t["learning_rate"]), weight_decay=float(t["weight_decay"]))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=float(t["learning_rate"]), total_steps=max_ep * spe,
                                                pct_start=0.15, anneal_strategy="cos")
    rng = np.random.default_rng(seed)          # batch sequence: identical for rec and bc at equal seed
    gen_dev = torch.Generator(device=dev)
    gen_dev.manual_seed(seed)
    pools = {int(r): _class_idx(cohort, int(r)) for r in train_recs}
    classes = {"rec_dev": (1,), "rec_std": (0,)}.get(variant, (0, 1))
    per_class = 2 * m // len(classes)
    y_of = {int(r): labels[int(r)] for r in list(train_recs) + list(val_recs)}
    train_recs = np.asarray(sorted(int(r) for r in train_recs))
    best, best_state, bad, epochs_run = float("inf"), None, 0, 0
    for epoch in range(max_ep):
        model.train()
        for _ in range(spe):
            chosen = rng.choice(train_recs, size=min(B, len(train_recs)), replace=False)
            idx, owner = [], []
            for j, r in enumerate(chosen):
                for c in classes:
                    pool = pools[int(r)][c]
                    idx.append(rng.choice(pool, per_class, replace=len(pool) < per_class))
                    owner.append(np.full(per_class, j))
            idx, owner = np.concatenate(idx), np.concatenate(owner)
            xb = gxt.augment(lane.x[torch.as_tensor(idx, device=dev)], gx_config, gen_dev)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                z = model(xb).float()[:, 0]
            yr = torch.as_tensor([y_of[int(r)] for r in chosen], dtype=torch.float32, device=dev)
            own = torch.as_tensor(owner, device=dev)
            if variant == "bc":
                loss = F.binary_cross_entropy_with_logits(z, yr[own])
            else:
                zr = torch.zeros(len(chosen), device=dev).index_add_(0, own, z) / torch.bincount(own, minlength=len(chosen)).float()
                if variant == "ord":
                    loss = head.nll(zr, (yr - 1).long())
                else:
                    loss = F.binary_cross_entropy_with_logits(zr, yr)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(params, 5.0)
            opt.step()
            sched.step()
        epochs_run = epoch + 1
        zv = torch.as_tensor(_record_scores(model, lane, cohort, val_recs, classes=classes, draws=[0])[:, 0], device=dev)
        yv = torch.as_tensor([y_of[int(r)] for r in val_recs], dtype=torch.float32, device=dev)
        with torch.no_grad():
            val = float(head.nll(zv, (yv - 1).long()) if variant == "ord" else F.binary_cross_entropy_with_logits(zv, yv))
        if val < best - 1e-5:
            best, bad = val, 0
            best_state = ({k: v.detach().clone() for k, v in model.state_dict().items()},
                          {k: v.detach().clone() for k, v in head.state_dict().items()} if head is not None else None)
        else:
            bad += 1
            if bad >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state[0])
        if head is not None:
            head.load_state_dict(best_state[1])
    model.eval()
    info = {"best_val": best, "epochs_run": epochs_run}
    if head is not None:
        info["thresholds"] = head.thresholds().detach().cpu().numpy().tolist()
    return model, info


def run_unit(cohort: Cohort, lane, gx_config, config, variant: str, p: int, s: int, k: int, out_path, *, occlude: bool):
    outer = cohort.outer(s)
    rec = cohort.rec
    elig = rec[rec.eligible].copy()
    elig["fold"] = elig.child.map(outer)
    column = "sir" if variant == "ord" else "stage"
    lab_child = permuted_labels(cohort, p, column)
    labels = {int(r.rec): lab_child[int(r.child)] for r in elig.itertuples()}
    tr_children = sorted(elig[elig.fold != k].child.astype(int))
    val_children = set(cohort.val_children(tr_children, ("e2e", s, k)).tolist())   # same for every variant/perm
    train_recs = elig[(elig.fold != k) & ~elig.child.isin(val_children)].rec.to_numpy()
    val_recs = elig[(elig.fold != k) & elig.child.isin(val_children)].rec.to_numpy()
    test_recs = elig[elig.fold == k].rec.to_numpy()
    nh = rec[rec.nh_eligible & (rec.child.map(outer) == k)].rec.to_numpy()
    score_recs = np.concatenate([test_recs, nh]).astype(int)
    seed = stable_int("pf_e2e", variant if variant in ("ord",) else "stage", p, s, k) % (2 ** 31 - 1)
    model, info = fit_e2e(cohort, lane, gx_config, config, variant, train_recs, val_recs, labels, seed)
    classes = {"rec_dev": (1,), "rec_std": (0,)}.get(variant, (0, 1))
    scores = _record_scores(model, lane, cohort, score_recs, classes=classes)
    payload = {"recs": score_recs, "scores": scores, "n_train_recs": np.int64(len(train_recs)),
               "prior_log_odds": np.float64(np.log(max(np.mean([labels[int(r)] for r in train_recs]), 1e-6)
                                                   / max(1 - np.mean([labels[int(r)] for r in train_recs]), 1e-6)))
               if variant != "ord" else np.float64(0.0),
               "info": np.asarray(json.dumps(info))}
    if occlude:
        occl = gpu.occlusions(config, lane.x.shape[2])
        payload["occl_scores"] = np.stack([_record_scores(model, lane, cohort, test_recs, classes=classes, occl=o).mean(1)
                                           for o in occl])
        payload["occl_recs"] = test_recs
        payload["occl_names"] = np.asarray([o["name"] for o in occl])
    save_npz_atomic(out_path, **payload)
    return info


def cmd_e2e(args, config) -> dict:
    dev = gpu.device()
    run = open_run("e2e", args.run, config, args=vars(args))
    cohort = Cohort(config, args.prepare_run)
    lane, gx_config = gpu.load_lane_checked(config, cohort, dev)
    n_outer = int(cfg(config, "folds.n_outer"))
    units = []
    if args.mode == "observed":
        units = [(v, 0, s, k) for v in VARIANTS_OBS for s in cohort.seeds for k in range(n_outer)]
    elif args.mode == "perm":
        lo, hi = (int(v) for v in args.perms.split("-"))
        units = [(v, p, s, k) for p in range(lo, hi + 1) for v in VARIANTS_PERM for s in cohort.seeds for k in range(n_outer)]
    else:
        raise ValueError(args.mode)
    done = 0
    for v, p, s, k in task_units(units):
        out_path = run["private"] / v / f"p{p:03d}_s{s}_k{k}.npz"
        if out_path.exists():
            continue
        out_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = run_unit(cohort, lane, gx_config, config, v, p, s, k, out_path, occlude=(args.mode == "observed" and v == "rec"))
        done += 1
        print(json.dumps({"variant": v, "p": p, "s": s, "k": k, **{a: b for a, b in info.items() if a != "thresholds"}}), flush=True)
    return {"units_run": done}
