"""G2: protocol-conditioned sharing on MFF canonical lanes (NEXTMAP_GPU_PROTOCOL_FROZEN.md section 2).

Adds to GX4 (pure tone + bapa shared trunk vs single task, already closed): a third protocol (mff_unknown_event), a naive
pooling arm, one optimisation budget for every arm (max_steps with OneCycle) and per-target-lane early stopping.
Folds are dealt over identity groups of the UNION of the three lanes (a child's records in every lane share its fold).
Arms per unit (seed, fold): target_only (one EEGNet per lane), naive_pool (one EEGNet, one head, all lanes) and
shared_heads (one trunk, one head per lane). Pooled arms keep a separate best checkpoint per lane (that lane's
validation children), so each target lane is evaluated with its own early stopping. Metric: per-child AUC on the test
children's trials of the target lane, child-mean; units are atomic JSON files (per-child values stay private).
"""
from __future__ import annotations

import json

import numpy as np

from .runtime import (ROOT, cfg, close_run, open_run, require_protocol, stable_int, task_units, write_json_atomic)


def _gx(config):
    from auditory_gx.runtime import load_config as gx_load
    return gx_load(cfg(config, "sources.gx_config"))


def load_lanes(config, gx, dev) -> dict:
    from auditory_gx import data as gxd
    stage = ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run")
    return {name: gxd.load_lane(gx, stage, name, dev) for name in config["g2"]["lanes"]}


def group_of_trial(lane) -> np.ndarray:
    return np.asarray(lane.child_ids, dtype=object)[lane.child]


def make_folds(groups: list[str], seed: int, n_folds: int, val_fraction: float) -> dict:
    """Identity groups -> outer fold (round-robin over a seeded permutation); per fold a seeded validation subset."""
    rng = np.random.default_rng(seed)
    order = list(rng.permutation(sorted(groups)))
    outer = {g: i % n_folds for i, g in enumerate(order)}
    val = {}
    for k in range(n_folds):
        train = sorted(g for g in groups if outer[g] != k)
        n_val = max(1, int(round(val_fraction * len(train))))
        val[k] = sorted(np.random.default_rng(seed * 100 + k).choice(train, n_val, replace=False).tolist())
    return {"outer": outer, "val": val}


def split_indices(lanes: dict, folds: dict, k: int) -> dict:
    out = {}
    for name, lane in lanes.items():
        g = group_of_trial(lane)
        test = np.array([folds["outer"][x] == k for x in g])
        val = np.isin(g, folds["val"][k])
        out[name] = {"train": np.flatnonzero(~test & ~val), "val": np.flatnonzero(val), "test": np.flatnonzero(test)}
    return out


class LaneModel:
    """EEGNet trunk with either one shared head or one head per lane."""

    def __init__(self, gx, n_channels: int, n_times: int, lane_names: list[str], per_lane_heads: bool, dev):
        import torch
        from auditory_gx.models import EEGNet
        m = gx["model"]
        self.trunk = EEGNet(n_channels, n_times, 2, F1=int(m["F1"]), D=int(m["D"]), F2=int(m["F2"]), k1=int(m["k1"]),
                            k2=int(m["k2"]), dropout=float(m["dropout"])).to(dev)
        self.lanes = list(lane_names)
        self.heads = torch.nn.ModuleDict({n: torch.nn.Linear(self.trunk.feature_dim, 2) for n in self.lanes}).to(dev) \
            if per_lane_heads else None

    def parameters(self):
        return list(self.trunk.parameters()) + (list(self.heads.parameters()) if self.heads is not None else [])

    def logits(self, x, lane_name: str):
        if self.heads is None:
            return self.trunk(x)
        return self.heads[lane_name](self.trunk.embed(x))

    def state(self):
        out = {"trunk": {k: v.detach().clone() for k, v in self.trunk.state_dict().items()}}
        if self.heads is not None:
            out["heads"] = {k: v.detach().clone() for k, v in self.heads.state_dict().items()}
        return out

    def load(self, st):
        self.trunk.load_state_dict(st["trunk"])
        if self.heads is not None:
            self.heads.load_state_dict(st["heads"])

    def train(self, flag=True):
        self.trunk.train(flag)
        if self.heads is not None:
            self.heads.train(flag)


def predict_lane(model: LaneModel, lane, lane_name: str, idx: np.ndarray, batch: int = 2048) -> np.ndarray:
    import torch
    model.train(False)
    out = []
    with torch.no_grad():
        idx_t = torch.as_tensor(idx, dtype=torch.long, device=lane.x.device)
        for b in range(0, len(idx_t), batch):
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                out.append(model.logits(lane.x[idx_t[b:b + batch]].float(), lane_name).float().cpu().numpy())
    return np.concatenate(out) if out else np.zeros((0, 2), np.float32)


def train_arm(model: LaneModel, lanes: dict, splits: dict, train_lanes: list[str], gx, config, seed: int) -> dict:
    """Uniform sampling over the pooled training trials of `train_lanes`; lane-specific class weights; OneCycle over
    max_steps; every eval_every steps the balanced validation CE of each lane; best state kept per lane."""
    import torch
    import torch.nn.functional as F
    from auditory_gx import train as gxt
    g2, t = config["g2"], gx["train"]
    dev = next(iter(lanes.values())).x.device
    gxt.seed_all(seed)
    gen = torch.Generator(device=dev)
    gen.manual_seed(seed)
    lane_id = np.concatenate([np.full(len(splits[n]["train"]), i) for i, n in enumerate(train_lanes)])
    trial = np.concatenate([splits[n]["train"] for n in train_lanes])
    lane_id_t = torch.as_tensor(lane_id, device=dev)
    trial_t = torch.as_tensor(trial, dtype=torch.long, device=dev)
    weights = {n: gxt.class_weights(lanes[n].y[torch.as_tensor(splits[n]["train"], device=dev)], 2) for n in train_lanes}
    opt = torch.optim.AdamW(model.parameters(), lr=float(t["learning_rate"]), weight_decay=float(t["weight_decay"]))
    max_steps = int(g2["max_steps"])
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=float(t["learning_rate"]), total_steps=max_steps,
                                                pct_start=0.15, anneal_strategy="cos")
    bs = int(t["batch_size"])
    best = {n: (float("inf"), None, 0) for n in train_lanes}          # (val, state, bad)
    yv = {n: lanes[n].y.cpu().numpy()[splits[n]["val"]] for n in train_lanes}
    log, step = [], 0
    model.train(True)
    while step < max_steps:
        pick = torch.randint(0, len(trial_t), (bs,), generator=gen, device=dev)
        loss = 0.0
        for i, n in enumerate(train_lanes):
            sel = pick[lane_id_t[pick] == i]
            if len(sel) == 0:
                continue
            ti = trial_t[sel]
            xb = gxt.augment(lanes[n].x[ti], gx, gen)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                lg = model.logits(xb, n)
            loss = loss + F.cross_entropy(lg.float(), lanes[n].y[ti], weight=weights[n], reduction="sum")
        loss = loss / bs
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()
        sched.step()
        step += 1
        if step % int(g2["eval_every_steps"]) == 0 or step == max_steps:
            row = {"step": step}
            for n in train_lanes:
                v = gxt.balanced_ce_bits(predict_lane(model, lanes[n], n, splits[n]["val"]), yv[n], 2)
                bv, bst, bad = best[n]
                if v < bv - 1e-5:
                    best[n] = (v, model.state(), 0)
                else:
                    best[n] = (bv, bst, bad + 1)
                row[n] = v
            model.train(True)
            log.append(row)
            if all(best[n][2] >= int(g2["patience_evals"]) for n in train_lanes):
                break
    return {"best": {n: {"val_ce_bal_bits": best[n][0], "state": best[n][1]} for n in train_lanes}, "steps": step, "log": log}


def child_aucs(model: LaneModel, lane, lane_name: str, test_idx: np.ndarray) -> dict:
    from auditory_gx import train as gxt
    logits = predict_lane(model, lane, lane_name, test_idx)
    y = lane.y.cpu().numpy()[test_idx]
    g = group_of_trial(lane)[test_idx]
    out = {}
    for child in sorted(set(g)):
        m = g == child
        met = gxt.child_metrics(logits[m], y[m], 2)
        out[str(child)] = {"auc": met["auc"], "n": int(m.sum())}
    return out


def cmd_g2_train(args, config) -> dict:
    from .controls import _device
    require_protocol(config)
    dev, gpu_name = _device(config)
    run = open_run("g2_train", args.run, config, args=vars(args))
    gx = _gx(config)
    lanes = load_lanes(config, gx, dev)
    names = list(lanes)
    groups = sorted({g for lane in lanes.values() for g in group_of_trial(lane)})
    g2 = config["g2"]
    work = [(int(s), k) for s in g2["seeds"] for k in range(int(g2["n_folds"]))]
    shapes = {n: tuple(lanes[n].x.shape[1:]) for n in names}
    if len(set(shapes.values())) != 1:
        raise RuntimeError(f"LANE_SHAPES_DIFFER:{shapes}")
    C, T = next(iter(shapes.values()))
    done = []
    for s, k in task_units(work):
        path = run["private"] / "units" / f"s{s}_k{k}.json"
        if path.exists():
            continue
        folds = make_folds(groups, s, int(g2["n_folds"]), float(g2["validation_fraction"]))
        sp = split_indices(lanes, folds, k)
        result = {"seed": s, "fold": k, "n_test_children": {n: int(len(set(group_of_trial(lanes[n])[sp[n]["test"]]))) for n in names},
                  "arms": {}}
        plans = [("target_only", [n], False, n) for n in names] + [("naive_pool", names, False, None), ("shared_heads", names, True, None)]
        for arm, tl, heads, tag in plans:
            seed = stable_int("nextmap_g2", arm, tag or "all", s, k) % (2 ** 31 - 1)
            model = LaneModel(gx, C, T, tl, heads, dev)
            fit = train_arm(model, lanes, sp, tl, gx, config, seed)
            for n in tl:
                st = fit["best"][n]["state"]
                if st is not None:
                    model.load(st)
                result["arms"].setdefault(arm, {})[n] = {"val_ce_bal_bits": fit["best"][n]["val_ce_bal_bits"],
                                                         "steps": fit["steps"], "children": child_aucs(model, lanes[n], n, sp[n]["test"])}
            print(json.dumps({"s": s, "k": k, "arm": arm, "lanes": tl, "steps": fit["steps"]}), flush=True)
        result["gpu"] = gpu_name
        write_json_atomic(path, result, private=True)
        done.append((s, k))
    close_run(config, "g2_train", args.run, "COMPLETED", units=len(done))
    return {"units": done, "gpu": gpu_name, "lanes": {n: {"trials": int(len(lanes[n].y)), "children": int(lanes[n].n_children)} for n in names}}


def cmd_g2_summary(args, config) -> dict:
    require_protocol(config)
    run = open_run("g2_summary", args.run, config, args=vars(args))
    g2 = config["g2"]
    src_dir = ROOT / cfg(config, "paths.private_relative") / args.train_run / "units"
    units = [json.loads((src_dir / f"s{s}_k{k}.json").read_text()) for s in g2["seeds"] for k in range(int(g2["n_folds"]))]
    out, rng = {}, np.random.default_rng(int(config["age"]["bootstrap_seed"]))
    for lane in g2["lanes"]:
        per = {}
        for arm in g2["arms"]:
            vals = {}
            for u in units:
                for child, v in u["arms"][arm][lane]["children"].items():
                    if np.isfinite(v["auc"]):
                        vals.setdefault(child, []).append(v["auc"])
            per[arm] = {c: float(np.mean(v)) for c, v in vals.items()}
        kids = sorted(set.intersection(*[set(per[a]) for a in g2["arms"]]))
        A = {a: np.array([per[a][c] for c in kids]) for a in g2["arms"]}
        idx = rng.integers(0, len(kids), size=(int(config["age"]["bootstrap_children"]), len(kids)))

        def boot(d):
            bs = d[idx].mean(1)
            lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
            return {"mean": float(d.mean()), "ci95": [lo, hi], "reading": "gain" if lo > 0 else ("loss" if hi < 0 else "no_clear_difference")}
        seeds = {a: [float(np.nanmean([v["auc"] for u in units if u["seed"] == s for v in u["arms"][a][lane]["children"].values()]))
                     for s in g2["seeds"]] for a in g2["arms"]}
        out[lane] = {"children": len(kids), "child_mean_auc": {a: float(A[a].mean()) for a in g2["arms"]},
                     "per_seed_child_mean_auc": seeds,
                     "shared_heads_minus_target_only": boot(A["shared_heads"] - A["target_only"]),
                     "naive_pool_minus_target_only": boot(A["naive_pool"] - A["target_only"]),
                     "shared_heads_minus_naive_pool": boot(A["shared_heads"] - A["naive_pool"]),
                     "steps_median": {a: float(np.median([u["arms"][a][lane]["steps"] for u in units])) for a in g2["arms"]}}
    summary = {"status": "COMPLETED", "lanes": out, "units": len(units),
               "note": "GX4 already compared shared trunk + 2 task heads vs single task on pure tone + bapa (closed)"}
    write_json_atomic(run["public"] / "summary_g2.json", summary, private=False)
    close_run(config, "g2_summary", args.run, "COMPLETED")
    return {lane: {"auc": {a: round(v, 4) for a, v in d["child_mean_auc"].items()},
                   "shared-target": round(d["shared_heads_minus_target_only"]["mean"], 4),
                   "naive-target": round(d["naive_pool_minus_target_only"]["mean"], 4)} for lane, d in out.items()}
