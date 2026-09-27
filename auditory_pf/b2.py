"""B2 (H7, H10): stage-conditioned shared stimulus decoders vs stage-blind, with random-group controls.

Training/test data: labelled visits of labelled children only (their stage is known per visit).
Models per outer (s, k): blind; heads_stage (shared trunk, one head per stage); heads_rand{r}
(same architecture, groups = stage labels permuted among labelled children); film_stage (FiLM
gating on a +-1 stage indicator); film_rand{r}. H8 uses M_13 vs M_o from the stim run.
"""
from __future__ import annotations

import json

import numpy as np
import torch
from torch import nn

from auditory_gx import train as gxt

from . import gpu
from .cohort import Cohort
from .runtime import cfg, open_run, save_npz_atomic, stable_int, task_units


class HeadsNet(nn.Module):
    """EEGNet trunk + one 2-class head per group; `child` carries the per-trial group id."""

    def __init__(self, trunk: nn.Module, n_groups: int = 2):
        super().__init__()
        self.trunk = trunk
        self.heads = nn.ModuleList([nn.Linear(trunk.feature_dim, 2) for _ in range(n_groups)])

    def embed(self, x, child=None, cond=None):
        return self.trunk.embed(x)

    def forward(self, x, child=None, cond=None):
        e = self.trunk.embed(x)
        out = self.heads[0](e)
        if child is not None:
            for g in range(1, len(self.heads)):
                out = torch.where((child == g)[:, None], self.heads[g](e), out)
        return out


def _groups(cohort: Cohort, r: int | None, s: int, k: int) -> dict[int, int]:
    """Child -> group (stage, or stage labels permuted among labelled children for r >= 0)."""
    lab = cohort.ch[cohort.ch.group == "labelled"].sort_values("child")
    kids, st = lab.child.to_numpy().astype(int), lab.stage.to_numpy().astype(int)
    if r is not None:
        st = st[np.random.default_rng(stable_int("pf_b2_rand", r, s, k)).permutation(len(st))]
    return dict(zip(kids, st))


def run_unit(cohort: Cohort, lane, gx_config, config, s: int, k: int, out_dir) -> dict:
    outer = cohort.outer(s)
    rec = cohort.rec
    lab = rec[rec.labelled].copy()
    lab["fold"] = lab.child.map(outer)
    tr_children = sorted(lab[lab.fold != k].child.astype(int))
    val = set(cohort.val_children(tr_children, ("b2", s, k)).tolist())
    tr_idx = cohort.trial_idx_of_records(lab[(lab.fold != k) & ~lab.child.isin(val)].rec)
    va_idx = cohort.trial_idx_of_records(lab[(lab.fold != k) & lab.child.isin(val)].rec)
    test_recs = rec[rec.eligible & (rec.child.map(outer) == k)].rec.to_numpy()
    te_idx = cohort.trial_idx_of_records(test_recs)
    dev = lane.x.device
    child_of_trial = cohort.rec.child.to_numpy()[cohort.t_record]
    R = int(cfg(config, "b2.random_draws"))
    specs = [("blind", None, None)] + [("heads_stage", "heads", None)] + [(f"heads_rand{r}", "heads", r) for r in range(R)] \
        + [("film_stage", "film", None)] + [(f"film_rand{r}", "film", r) for r in range(R)]
    out = {}
    for name, kind, r in specs:
        path = out_dir / f"{name}.npz"
        if path.exists():
            continue
        seed = stable_int("pf_b2", s, k) % (2 ** 31 - 1)       # same init/batches across specs
        gxt.seed_all(seed)
        grp_child = _groups(cohort, r, s, k)
        g_trial = np.array([grp_child.get(int(c), 0) for c in child_of_trial], dtype=np.int64)
        g_t = torch.as_tensor(g_trial, device=dev)
        child_t, cond_t = None, None
        if kind == "heads":
            model = HeadsNet(gxt.build_model(gx_config, lane))
            child_t = g_t
        elif kind == "film":
            model = gxt.build_model(gx_config, lane, cond_dim=1)
            cond_t = (g_t.float() * 2 - 1).unsqueeze(1)
        else:
            model = gxt.build_model(gx_config, lane)
        info = gxt.fit(model, lane, tr_idx, va_idx, gx_config, seed=seed, child=child_t, cond=cond_t)
        diff = gpu.infer(model, lane, te_idx, child=child_t, cond=cond_t)
        save_npz_atomic(path, idx=te_idx, diff=diff, group_of_test_child=np.asarray([grp_child.get(int(c), -1) for c in
                                                                                    cohort.rec.child.to_numpy()[test_recs]]),
                        test_recs=test_recs, info=np.asarray(json.dumps(info)))
        out[name] = info.get("epochs_run")
    return out


def cmd_b2(args, config) -> dict:
    dev = gpu.device()
    run = open_run("b2", args.run, config, args=vars(args))
    cohort = Cohort(config, args.prepare_run)
    lane, gx_config = gpu.load_lane_checked(config, cohort, dev)
    units = [(s, k) for s in cohort.seeds for k in range(int(cfg(config, "folds.n_outer")))]
    n = 0
    for s, k in task_units(units):
        out_dir = run["private"] / f"unit_s{s}_k{k}"
        out_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = run_unit(cohort, lane, gx_config, config, s, k, out_dir)
        n += 1
        print(json.dumps({"s": s, "k": k, **info}), flush=True)
    return {"units": n}
