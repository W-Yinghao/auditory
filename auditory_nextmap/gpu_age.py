"""G1: equal-capacity age models on HA/BDF (NEXTMAP_GPU_PROTOCOL_FROZEN.md section 1).

Per PF2 unit (seed, outer fold) and the same lane / folds / validation-children rule as the stimulus encoders M_o:
  age_trial   EEGNet (identical architecture and optimiser to M_o) trained to predict the record's age from single trials
  age_subavg  the same network trained on 20-trial same-record same-class sub-averages (evoked input)
  stim_avginput  frozen M_o applied to the draw0 class-average waveform (inference only)
Outputs per record with draws: draw0 direct predictions (months) and draw0 class-mean embeddings. g1-readout (CPU) scores
them with the A0 rules and compares with the saved A0 / A1 predictions. Units are atomic; a requeued job skips them.
"""
from __future__ import annotations

import json
import math

import numpy as np

from . import age_core
from . import age_readout as ar
from . import representations as rp
from .adapters import AgeSource, units
from .runtime import (ROOT, ProvenanceError, cfg, close_run, open_run, require_protocol, save_npz_atomic, stable_int,
                      task_units, write_json_atomic)


def _gx(config):
    from auditory_gx.runtime import load_config as gx_load
    return gx_load(cfg(config, "sources.gx_config"))


def _eegnet(gx, n_out: int):
    from auditory_gx.models import EEGNet
    m = gx["model"]
    return EEGNet(20, 200, n_out, F1=int(m["F1"]), D=int(m["D"]), F2=int(m["F2"]), k1=int(m["k1"]), k2=int(m["k2"]),
                  dropout=float(m["dropout"]))


class Groups:
    """Trial indices of each (record, class) of the lane, contiguous, for on-device sub-average sampling."""

    def __init__(self, co, device):
        import torch
        order = np.lexsort((co.t_y, co.t_record))
        rec, y = co.t_record[order], co.t_y[order]
        key = rec * 2 + y
        starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        sizes = np.diff(np.r_[starts, len(key)])
        self.order = torch.as_tensor(order, dtype=torch.long, device=device)
        self.group_of_trial = torch.empty(len(order), dtype=torch.long, device=device)
        gid = np.repeat(np.arange(len(starts)), sizes)
        self.group_of_trial[torch.as_tensor(order, device=device)] = torch.as_tensor(gid, device=device)
        self.start = torch.as_tensor(starts, dtype=torch.long, device=device)
        self.size = torch.as_tensor(sizes, dtype=torch.long, device=device)
        self.max_size = int(sizes.max())

    def partners(self, sel, m: int, gen):
        """[B, m] lane-trial indices: m distinct trials of the same record and class as each selected trial."""
        import torch
        g = self.group_of_trial[sel]
        size = self.size[g]
        keys = torch.rand(len(sel), self.max_size, generator=gen, device=sel.device)
        keys[torch.arange(self.max_size, device=sel.device)[None, :] >= size[:, None]] = 2.0
        pos = keys.argsort(dim=1)[:, :m]
        pos = torch.minimum(pos, (size[:, None] - 1).clamp(min=0))
        return self.order[self.start[g][:, None] + pos]


def subaverage_inputs(lane_x, idx_groups: list[np.ndarray]):
    """Mean waveform of each index group -> [G, C, T] float32 (deterministic evaluation inputs)."""
    import torch
    return torch.stack([lane_x[torch.as_tensor(g, device=lane_x.device)].float().mean(0) for g in idx_groups])


def chunks(idx: np.ndarray, m: int) -> list[np.ndarray]:
    """Consecutive disjoint groups of m (a trailing remainder smaller than m is dropped)."""
    return [idx[i:i + m] for i in range(0, len(idx) - m + 1, m)]


def train_age(model, lane, co, train_idx: np.ndarray, val_recs: list[int], target: np.ndarray, mode: str, gx: dict,
              seed: int, max_epochs: int, patience: int, m: int, groups: Groups | None) -> dict:
    """auditory_gx.train.fit with an MSE age head: AdamW + OneCycle, augmentation, clip 5, bf16; early stopping on
    the validation children's MAE (months) of record-mean predictions."""
    import torch
    import torch.nn.functional as F
    from auditory_gx import train as gxt
    t = gx["train"]
    gxt.seed_all(seed)
    dev = lane.x.device
    gen = torch.Generator(device=dev)
    gen.manual_seed(seed)
    model.to(dev).train()
    lr, bs = float(t["learning_rate"]), int(t["batch_size"])
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=float(t["weight_decay"]))
    steps = max(1, math.ceil(len(train_idx) / bs))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=max_epochs * steps, pct_start=0.15,
                                                anneal_strategy="cos")
    mu, sd = float(target[train_idx].mean()), float(target[train_idx].std())
    z = torch.as_tensor((target - mu) / sd, dtype=torch.float32, device=dev)
    tr = torch.as_tensor(train_idx, dtype=torch.long, device=dev)
    val_inputs = {}
    for r in val_recs:
        idx = co.trial_idx_of_records([r])
        if mode == "trial":
            val_inputs[r] = ("idx", idx)
        else:
            grp = [g for cls in (0, 1) for g in chunks(idx[co.t_y[idx] == cls], m)]
            val_inputs[r] = ("avg", subaverage_inputs(lane.x, grp)) if grp else None
    age_val = {r: float(co.rec.loc[r, "age_months"]) for r in val_recs}
    best, best_state, bad, log = float("inf"), None, 0, []
    for epoch in range(max_epochs):
        perm = tr[torch.randperm(len(tr), generator=gen, device=dev)]
        for b in range(0, len(perm), bs):
            sel = perm[b:b + bs]
            if mode == "trial":
                xb = lane.x[sel]
            else:
                xb = lane.x[groups.partners(sel, m, gen)].float().mean(1)
            xb = gxt.augment(xb, gx, gen)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                out = model(xb)
            loss = F.mse_loss(out.float().squeeze(1), z[sel])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
        errs = []
        for r, v in val_inputs.items():
            if v is None:
                continue
            p = predict(model, lane, v)
            errs.append(abs(mu + sd * float(np.mean(p)) - age_val[r]))
        val = float(np.mean(errs)) if errs else float("inf")
        log.append({"epoch": epoch, "val_mae_months": val})
        if val < best - 1e-6:
            best, bad = val, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    return {"best_val_mae_months": best, "epochs_run": epoch + 1, "target_mean": mu, "target_sd": sd, "log": log}


def predict(model, lane, spec, batch: int = 4096, embed: bool = False):
    import torch
    kind, val = spec
    outs = []
    model.eval()
    with torch.no_grad():
        if kind == "idx":
            idx_t = torch.as_tensor(np.asarray(val), dtype=torch.long, device=lane.x.device)
            batches = [lane.x[idx_t[b:b + batch]].float() for b in range(0, len(idx_t), batch)]
        else:
            batches = [val[b:b + batch] for b in range(0, len(val), batch)]
        for xb in batches:
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                o = model.embed(xb) if embed else model(xb)
            outs.append(o.float().cpu().numpy())
    out = np.concatenate(outs) if outs else np.zeros((0, 1), np.float32)
    return out if embed else out[:, 0]


def run_unit(src: AgeSource, lane, gx, config, arm: str, s: int, k: int, groups: Groups, dev) -> dict:
    import torch
    co = src.co
    g = config["g1"]
    outer = co.outer(s)
    rec = co.rec
    train_children = sorted(c for c, f in outer.items() if f != k)
    age_rec = rec.set_index("rec").age_months
    aged = [c for c in train_children if any(np.isfinite(age_rec.loc[r]) for r in co.records_of_children([c]))]
    val_children = set(int(c) for c in co.val_children(aged, (g["validation_key"], s, k)))
    fit_children = [c for c in aged if c not in val_children]
    fit_recs = [int(r) for r in co.records_of_children(fit_children) if np.isfinite(age_rec.loc[int(r)])]
    val_recs = [int(r) for r in co.records_of_children(sorted(val_children)) if np.isfinite(age_rec.loc[int(r)])]
    target = np.full(co.n_trials, np.nan)
    for r in fit_recs + val_recs:
        target[co.trial_idx_of_records([r])] = float(age_rec.loc[r])
    train_idx = co.trial_idx_of_records(fit_recs)
    seed = stable_int("nextmap_g1", arm, s, k) % (2 ** 31 - 1)
    model = _eegnet(gx, 1)
    info = train_age(model, lane, co, train_idx, val_recs, target, "trial" if arm == "age_trial" else "subavg", gx, seed,
                     int(g["max_epochs"]), int(g["patience"]), int(g["subavg_trials"]), groups)
    recs = sorted(co.draw_row)
    pred = np.full(len(rec), np.nan)
    emb = np.full((len(rec), 2, 192), np.nan, np.float32)
    m = int(g["subavg_trials"])
    for r in recs:
        spec_c, preds = [], []
        for cls in (0, 1):
            idx = co.budget_idx(r, 0, cls)
            spec = ("idx", idx) if arm == "age_trial" else ("avg", subaverage_inputs(lane.x, chunks(idx, m)))
            preds.append(predict(model, lane, spec))
            emb[r, cls] = predict(model, lane, spec, embed=True).mean(0)
        pred[r] = info["target_mean"] + info["target_sd"] * float(np.mean(np.concatenate(preds)))
    return {"pred_months": pred, "emb": emb, "info": {k2: v for k2, v in info.items() if k2 != "log"}, "log": info["log"],
            "fit_children": fit_children, "val_children": sorted(val_children), "seed": seed}


def stim_avginput(src: AgeSource, lane, gx, config, s: int, k: int, dev) -> np.ndarray:
    import torch
    co = src.co
    model = _eegnet(gx, 2)
    model.load_state_dict(torch.load(src.stim_dir / f"unit_s{s}_k{k}" / "models" / "M_o.pt", map_location="cpu"), strict=True)
    model.to(dev).eval()
    emb = np.full((len(co.rec), 2, 192), np.nan, np.float32)
    for r in sorted(co.draw_row):
        for cls in (0, 1):
            avg = subaverage_inputs(lane.x, [co.budget_idx(r, 0, cls)])
            emb[r, cls] = predict(model, lane, ("avg", avg), embed=True)[0]
    return emb


def cmd_g1_train(args, config) -> dict:
    from auditory_pf import gpu
    from .controls import _device
    require_protocol(config)
    dev, gpu_name = _device(config)
    run = open_run("g1_train", args.run, config, args=vars(args))
    src = AgeSource(config)
    lane, gx = gpu.load_lane_checked(src.pfc, src.co, dev)
    groups = Groups(src.co, dev)
    done = []
    for s, k in task_units(units(config)):
        p = run["private"] / "units" / "stim_avginput" / f"s{s}_k{k}.npz"
        if not p.exists():
            save_npz_atomic(p, emb=stim_avginput(src, lane, gx, config, s, k, dev), gpu=np.asarray(gpu_name))
        for arm in config["g1"]["arms"]:
            p = run["private"] / "units" / arm / f"s{s}_k{k}.npz"
            if p.exists():
                continue
            out = run_unit(src, lane, gx, config, arm, s, k, groups, dev)
            save_npz_atomic(p, pred_months=out["pred_months"], emb=out["emb"], fit_children=np.asarray(out["fit_children"]),
                            val_children=np.asarray(out["val_children"]), info=np.asarray(json.dumps(out["info"])),
                            log=np.asarray(json.dumps(out["log"])), seed=np.int64(out["seed"]), gpu=np.asarray(gpu_name))
            done.append((arm, s, k, out["info"]["epochs_run"], round(out["info"]["best_val_mae_months"], 2)))
            print(json.dumps({"arm": arm, "s": s, "k": k, **out["info"]}), flush=True)
    close_run(config, "g1_train", args.run, "COMPLETED", units=len(done))
    return {"trained": done, "gpu": gpu_name}


# ====================================================================== CPU readout

def _load(run_dir, arm, s, k):
    with np.load(run_dir / "units" / arm / f"s{s}_k{k}.npz", allow_pickle=False) as z:
        return {n: z[n] for n in z.files}


def cmd_g1_readout(args, config) -> dict:
    require_protocol(config)
    run = open_run("g1_readout", args.run, config, args=vars(args))
    src = AgeSource(config)
    kids = src.main_children
    ages = {c: src.age(c) for c in kids}
    priv = ROOT / cfg(config, "paths.private_relative")
    tr_dir = priv / args.train_run
    a = config["age"]
    ul = units(config)
    # raw class-mean bins (A1 inputs)
    raw0, raw1 = [], []
    for c in kids:
        rid = str(src.rec.loc[src.primary(c), "record_id"])
        with np.load(priv / config["g1"]["inputs_run"] / "inputs" / f"{rid}.npz", allow_pickle=False) as z:
            raw0.append(z["raw_mu0"]); raw1.append(z["raw_mu1"])
    raw0, raw1 = np.stack(raw0).astype(np.float64), np.stack(raw1).astype(np.float64)
    views, n_fits = {}, 0
    for view in config["g1"]["readout_views"]:
        rows = []
        for s, k in ul:
            path = run["private"] / "units" / view / f"s{s}_k{k}.json"
            if path.exists():
                rows.append(json.loads(path.read_text()))
                continue
            tr, te = age_core.split(src, s, k)
            order = tr + te
            pos = [kids.index(c) for c in order]
            y = np.array([ages[c] for c in order])
            if view.endswith("_direct"):
                u = _load(tr_dir, view.replace("_direct", ""), s, k)
                pred = [float(u["pred_months"][src.primary(c)]) for c in te]
                res = {"pred": pred, "n_fits": 0, "alpha": None}
            else:
                if view == "raw_common_rbf":
                    m0, m1, kind, alphas = raw0[pos], raw1[pos], "rbf", a["kernel_alpha"]
                else:
                    u = _load(tr_dir, view.replace("_common_ridge", ""), s, k)
                    e = u["emb"][[src.primary(c) for c in order]].astype(np.float64)
                    m0, m1, kind, alphas = e[:, 0], e[:, 1], "ridge", a["alpha_sse"]
                fit = ar.select_and_fit(lambda trr, evr: rp.paired_design("common", m0, m1, trr, evr, floor=float(a["scale_floor"])),
                                        y, len(tr), np.arange(len(tr), len(order)), kind=kind, alphas=alphas,
                                        inner_folds=int(a["inner_folds"]), inner_seed=age_core.inner_seed(s, k),
                                        tie_tol=float(a["tie_tolerance"]), ledger=[], key={"view": view, "seed": s, "fold": k},
                                        gamma_fallback=float(a["kernel_gamma_fallback"]))
                res = {"pred": fit["pred"].tolist(), "n_fits": fit["n_fits"], "alpha": fit["alpha"]}
            row = {"seed": s, "fold": k, "view": view, "test_children": te, **res, "status": "COMPLETED"}
            write_json_atomic(path, row, private=True)
            rows.append(row)
        n_fits += sum(r["n_fits"] for r in rows)
        views[view] = age_core.view_table(age_core.collect_predictions(rows, kids), ages, kids)
    # saved references (no refit)
    refs = {}
    for name, ref in config["g1"]["references"].items():
        run_name, key = ref.split(":")
        if "/" in key:
            budget, view = key.split("/")
            rows = [json.loads(age_core.unit_path(priv / run_name, budget, view, s, k).read_text()) for s, k in ul]
        else:
            rows = [json.loads((priv / run_name / "units" / key / f"s{s}_k{k}.json").read_text()) for s, k in ul]
        refs[name] = age_core.view_table(age_core.collect_predictions(rows, kids), ages, kids)
    tables = {**refs, **views}
    B = int(a["bootstrap_children"])
    idx = np.random.default_rng(int(a["bootstrap_seed"])).integers(0, len(kids), size=(B, len(kids)))
    comps = {}
    for name, (va, vb, role) in {
            "trained_common_minus_age_trial_direct": ("trained_common", "age_trial_direct", "primary"),
            "raw_common_minus_age_trial_direct": ("raw_common", "age_trial_direct", "secondary"),
            "random_common_minus_age_trial_direct": ("random_common", "age_trial_direct", "secondary"),
            "age_trial_direct_minus_age_subavg_direct": ("age_trial_direct", "age_subavg_direct", "secondary"),
            "trained_common_minus_stim_avginput": ("trained_common", "stim_avginput_common_ridge", "secondary"),
            "raw_common_minus_raw_common_rbf": ("raw_common", "raw_common_rbf", "secondary"),
            "trained_common_minus_age_trial_common_ridge": ("trained_common", "age_trial_common_ridge", "descriptive"),
            "age_trial_direct_minus_age_trial_common_ridge": ("age_trial_direct", "age_trial_common_ridge", "descriptive")}.items():
        comps[name] = {"role": role, "a": va, "b": vb, **age_core.paired_boot(tables[va]["err"] - tables[vb]["err"], idx)}
    infos = {}
    for arm in config["g1"]["arms"]:
        ep, vm = [], []
        for s, k in ul:
            u = _load(tr_dir, arm, s, k)
            inf = json.loads(str(u["info"]))
            ep.append(inf["epochs_run"]); vm.append(inf["best_val_mae_months"])
        infos[arm] = {"epochs_median": float(np.median(ep)), "epochs_range": [int(min(ep)), int(max(ep))],
                      "val_mae_median": float(np.median(vm))}
    summary = {"status": "COMPLETED", "n_children": len(kids), "small_age_fits": n_fits,
               "views": {v: {k2: x for k2, x in t.items() if k2 != "err"} for v, t in tables.items()},
               "comparisons": comps, "training": infos,
               "sign_convention": "error(a) - error(b); positive = b better"}
    write_json_atomic(run["public"] / "summary_g1.json", summary, private=False)
    close_run(config, "g1_readout", args.run, "COMPLETED", small_age_fits=n_fits)
    return {"views": {v: round(t["mae"], 2) for v, t in tables.items()},
            "comparisons": {k2: (round(v["mean"], 2), [round(x, 2) for x in v["ci95"]]) for k2, v in comps.items()}}
