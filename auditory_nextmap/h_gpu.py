"""H-series GPU work (NEXTMAP_H_PROTOCOL_FROZEN.md sections 1, 2, 3, 6).

h-infer (inference only, bf16 as stim_002): per HA unit (seed, fold) the frozen M_o gives
  H2  per-trial embeddings of every accepted trial of the 55 primary records,
  H6  draw0 class-mean embeddings under 19 time-window and 6 channel-group occlusions (index 0 = intact),
  H1  (fold 0 units only) draw0 class-mean embeddings of the MFF children's mapped 20-channel trials;
and 5 untrained same-architecture EEGNets give the H1 random reference.
h3-train: ft_from_stim (M_o initialisation, age head, lr 1e-4) and multitask (stimulus CE + 1.0 x age MSE) per unit.
Every item is one atomic npz; a requeued runfill job skips finished items.
"""
from __future__ import annotations

import copy
import json
import math

import numpy as np

from . import gpu_age as ga
from .adapters import AgeSource, units
from .runtime import (ROOT, cfg, close_run, open_run, require_protocol, save_npz_atomic, stable_int, task_units)


def _mff_inputs(config, prep_run: str) -> tuple[list[str], dict]:
    import pandas as pd
    base = ROOT / cfg(config, "paths.private_relative") / prep_run
    coh = pd.read_csv(base / "h1_cohort.csv")
    inc = coh[coh.included].record_id.tolist()
    data = {}
    for rid in inc:
        with np.load(base / "records" / f"{rid}.npz", allow_pickle=False) as z:
            data[rid] = (z["x_std"], z["x_dev"])
    return inc, data


def _class_means(model, tensors: list, dev) -> np.ndarray:
    import torch
    out = np.zeros((len(tensors), 2, 192), np.float32)
    for i, (x0, x1) in enumerate(tensors):
        for cls, x in ((0, x0), (1, x1)):
            xb = torch.from_numpy(np.asarray(x)).to(dev).float()
            with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                out[i, cls] = model.embed(xb).float().mean(0).cpu().numpy()
    return out


def _occluded_class_means(model, lane, co, recs: list[int], occl: list[dict], dev) -> np.ndarray:
    import torch
    out = np.zeros((len(occl) + 1, len(recs), 2, 192), np.float32)
    for j, r in enumerate(recs):
        for cls in (0, 1):
            idx = torch.as_tensor(co.budget_idx(r, 0, cls), dtype=torch.long, device=dev)
            base = lane.x[idx].float()
            for o, spec in enumerate([None] + occl):
                xb = base.clone()
                if spec is not None:
                    if spec["kind"] == "time":
                        xb[:, :, spec["start"]:spec["stop"]] = 0
                    else:
                        xb[:, spec["chans"], :] = 0
                with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    out[o, j, cls] = model.embed(xb).float().mean(0).cpu().numpy()
    return out


def cmd_h_infer(args, config) -> dict:
    import torch
    from auditory_gx import train as gxt
    from auditory_pf import gpu
    from .controls import _device
    require_protocol(config)
    dev, gpu_name = _device(config)
    run = open_run("h_infer", args.run, config, args=vars(args))
    src = AgeSource(config)
    co = src.co
    lane, gx = gpu.load_lane_checked(src.pfc, co, dev)
    recs = [src.primary(c) for c in src.main_children]
    all_idx = co.trial_idx_of_records(recs)
    occl = gpu.occlusions(src.pfc, lane.x.shape[2])
    mff_ids, mff = _mff_inputs(config, args.prep_run)
    mff_tensors = [mff[r] for r in mff_ids]
    h1_units = {tuple(u) for u in config["h1"]["encoder_units"]}
    items = [("ha", s, k) for s, k in units(config)] + [("rand", i, 0) for i in range(int(config["h1"]["random_inits"]))]
    done = []
    for kind, a, b in task_units(items):
        path = run["private"] / "items" / (f"ha_s{a}_k{b}.npz" if kind == "ha" else f"rand_{a}.npz")
        if path.exists():
            continue
        if kind == "ha":
            model = ga._eegnet(gx, 2)
            model.load_state_dict(torch.load(src.stim_dir / f"unit_s{a}_k{b}" / "models" / "M_o.pt", map_location="cpu"), strict=True)
            model.to(dev).eval()
            emb_all = ga.predict(model, lane, ("idx", all_idx), embed=True).astype(np.float16)
            occ = _occluded_class_means(model, lane, co, recs, occl, dev)
            payload = {"emb_all": emb_all, "all_idx": all_idx, "occl_means": occ, "recs": np.asarray(recs),
                       "occl_names": np.asarray(["intact"] + [o["name"] for o in occl])}
            if (a, b) in h1_units:
                payload["mff_means"] = _class_means(model, mff_tensors, dev)
        else:
            gxt.seed_all(stable_int(int(cfg(config, "controls.random_initialization_seed")), "h1", a) % (2 ** 31 - 1))
            model = ga._eegnet(gx, 2).eval().to(dev)
            payload = {"mff_means": _class_means(model, mff_tensors, dev)}
        payload.update(mff_ids=np.asarray(mff_ids), gpu=np.asarray(gpu_name))
        save_npz_atomic(path, **payload)
        done.append(path.stem)
        print(json.dumps({"item": path.stem}), flush=True)
    close_run(config, "h_infer", args.run, "COMPLETED", items=len(done))
    return {"items": done, "gpu": gpu_name}


# ====================================================================== H3 training

def train_multitask(model, age_head, lane, co, train_idx: np.ndarray, age_mask: np.ndarray, val_recs: list[int],
                    target: np.ndarray, gx: dict, seed: int, max_epochs: int, patience: int, lam: float) -> dict:
    """Class-weighted stimulus CE on every training trial + lam * MSE of the standardised age on trials with an age;
    otherwise auditory_gx.train.fit (AdamW + OneCycle, augmentation, clip 5, bf16); early stopping on validation
    children's age MAE (record-mean predictions)."""
    import torch
    import torch.nn.functional as F
    from auditory_gx import train as gxt
    t = gx["train"]
    gxt.seed_all(seed)
    dev = lane.x.device
    gen = torch.Generator(device=dev)
    gen.manual_seed(seed)
    model.to(dev).train()
    age_head.to(dev).train()
    params = list(model.parameters()) + list(age_head.parameters())
    lr, bs = float(t["learning_rate"]), int(t["batch_size"])
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=float(t["weight_decay"]))
    steps = max(1, math.ceil(len(train_idx) / bs))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=max_epochs * steps, pct_start=0.15,
                                                anneal_strategy="cos")
    aged = train_idx[age_mask[train_idx]]
    mu, sd = float(target[aged].mean()), float(target[aged].std())
    z = torch.as_tensor(np.nan_to_num((target - mu) / sd), dtype=torch.float32, device=dev)
    has_age = torch.as_tensor(age_mask, device=dev)
    w = gxt.class_weights(lane.y[torch.as_tensor(train_idx, device=dev)], 2)
    tr = torch.as_tensor(train_idx, dtype=torch.long, device=dev)
    age_val = {r: float(co.rec.loc[r, "age_months"]) for r in val_recs}
    best, best_state, bad, log = float("inf"), None, 0, []
    for epoch in range(max_epochs):
        perm = tr[torch.randperm(len(tr), generator=gen, device=dev)]
        for b in range(0, len(perm), bs):
            sel = perm[b:b + bs]
            xb = gxt.augment(lane.x[sel], gx, gen)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                e = model.embed(xb)
                logits = model.head(e)
                age = age_head(e)
            loss = F.cross_entropy(logits.float(), lane.y[sel], weight=w)
            m = has_age[sel]
            if m.any():
                loss = loss + lam * F.mse_loss(age.float().squeeze(1)[m], z[sel][m])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 5.0)
            opt.step()
            sched.step()
        errs = [abs(mu + sd * float(np.mean(_age_pred(model, age_head, lane, co.trial_idx_of_records([r])))) - age_val[r])
                for r in val_recs]
        model.train()
        age_head.train()
        val = float(np.mean(errs)) if errs else float("inf")
        log.append({"epoch": epoch, "val_mae_months": val})
        if val < best - 1e-6:
            best, bad = val, 0
            best_state = ({k: v.detach().clone() for k, v in model.state_dict().items()},
                          {k: v.detach().clone() for k, v in age_head.state_dict().items()})
        else:
            bad += 1
            if bad >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state[0])
        age_head.load_state_dict(best_state[1])
    model.eval()
    age_head.eval()
    return {"best_val_mae_months": best, "epochs_run": epoch + 1, "target_mean": mu, "target_sd": sd, "log": log}


def _age_pred(model, age_head, lane, idx, batch: int = 4096) -> np.ndarray:
    import torch
    model.eval()
    age_head.eval()
    out = []
    with torch.no_grad():
        idx_t = torch.as_tensor(np.asarray(idx), dtype=torch.long, device=lane.x.device)
        for b in range(0, len(idx_t), batch):
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                out.append(age_head(model.embed(lane.x[idx_t[b:b + batch]].float())).float().cpu().numpy()[:, 0])
    return np.concatenate(out) if out else np.zeros(0, np.float32)


def run_h3_unit(src: AgeSource, lane, gx, config, arm: str, s: int, k: int, dev) -> dict:
    import torch
    co = src.co
    h3 = config["h3"]
    outer = co.outer(s)
    age_rec = co.rec.set_index("rec").age_months
    train_children = sorted(c for c, f in outer.items() if f != k)
    aged = [c for c in train_children if any(np.isfinite(age_rec.loc[r]) for r in co.records_of_children([c]))]
    val_children = set(int(c) for c in co.val_children(aged, (config["g1"]["validation_key"], s, k)))
    val_recs = [int(r) for r in co.records_of_children(sorted(val_children)) if np.isfinite(age_rec.loc[int(r)])]
    target = np.full(co.n_trials, np.nan)
    for r in co.rec.rec:
        if np.isfinite(age_rec.loc[int(r)]):
            target[co.trial_idx_of_records([int(r)])] = float(age_rec.loc[int(r)])
    seed = stable_int("nextmap_h3", arm, s, k) % (2 ** 31 - 1)
    recs = sorted(co.draw_row)
    pred = np.full(len(co.rec), np.nan)
    emb = np.full((len(co.rec), 2, 192), np.nan, np.float32)
    if arm == "ft_from_stim":
        fit_children = [c for c in aged if c not in val_children]
        fit_recs = [int(r) for r in co.records_of_children(fit_children) if np.isfinite(age_rec.loc[int(r)])]
        model = ga._eegnet(gx, 1)
        state = torch.load(src.stim_dir / f"unit_s{s}_k{k}" / "models" / "M_o.pt", map_location="cpu")
        missing = model.load_state_dict({kk: v for kk, v in state.items() if not kk.startswith("head.")}, strict=False)
        if set(missing.missing_keys) != {"head.weight", "head.bias"}:
            raise RuntimeError(f"FT_INIT_KEYS:{missing}")
        gx_ft = copy.deepcopy(gx)
        gx_ft["train"]["learning_rate"] = float(h3["ft_learning_rate"])
        info = ga.train_age(model, lane, co, co.trial_idx_of_records(fit_recs), val_recs, target, "trial", gx_ft, seed,
                            int(h3["max_epochs"]), int(h3["patience"]), 20, None)
        for r in recs:
            preds = []
            for cls in (0, 1):
                idx = co.budget_idx(r, 0, cls)
                preds.append(ga.predict(model, lane, ("idx", idx)))
                emb[r, cls] = ga.predict(model, lane, ("idx", idx), embed=True).mean(0)
            pred[r] = info["target_mean"] + info["target_sd"] * float(np.mean(np.concatenate(preds)))
    else:
        fit_children = [c for c in train_children if c not in val_children]
        train_idx = co.trial_idx_of_records(co.records_of_children(fit_children))
        model = ga._eegnet(gx, 2)
        head = torch.nn.Linear(model.feature_dim, 1)
        info = train_multitask(model, head, lane, co, train_idx, np.isfinite(target), val_recs, target, gx, seed,
                               int(h3["max_epochs"]), int(h3["patience"]), float(h3["multitask_lambda"]))
        for r in recs:
            preds = []
            for cls in (0, 1):
                idx = co.budget_idx(r, 0, cls)
                preds.append(_age_pred(model, head, lane, idx))
                emb[r, cls] = ga.predict(model, lane, ("idx", idx), embed=True).mean(0)
            pred[r] = info["target_mean"] + info["target_sd"] * float(np.mean(np.concatenate(preds)))
    return {"pred_months": pred, "emb": emb, "info": {kk: v for kk, v in info.items() if kk != "log"}, "log": info["log"],
            "seed": seed, "fit_children": fit_children, "val_children": sorted(val_children)}


def cmd_h3_train(args, config) -> dict:
    from auditory_pf import gpu
    from .controls import _device
    require_protocol(config)
    dev, gpu_name = _device(config)
    run = open_run("h3_train", args.run, config, args=vars(args))
    src = AgeSource(config)
    lane, gx = gpu.load_lane_checked(src.pfc, src.co, dev)
    items = [(arm, s, k) for s, k in units(config) for arm in config["h3"]["arms"]]
    done = []
    for arm, s, k in task_units(items):
        path = run["private"] / "units" / arm / f"s{s}_k{k}.npz"
        if path.exists():
            continue
        out = run_h3_unit(src, lane, gx, config, arm, s, k, dev)
        save_npz_atomic(path, pred_months=out["pred_months"], emb=out["emb"], info=np.asarray(json.dumps(out["info"])),
                        log=np.asarray(json.dumps(out["log"])), seed=np.int64(out["seed"]),
                        fit_children=np.asarray(out["fit_children"]), val_children=np.asarray(out["val_children"]),
                        gpu=np.asarray(gpu_name))
        done.append((arm, s, k, out["info"]["epochs_run"], round(out["info"]["best_val_mae_months"], 2)))
        print(json.dumps({"arm": arm, "s": s, "k": k, **out["info"]}), flush=True)
    close_run(config, "h3_train", args.run, "COMPLETED", units=len(done))
    return {"trained": done, "gpu": gpu_name}
