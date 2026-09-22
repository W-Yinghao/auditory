"""GX2-GX7 route commands (called from cli). Each writes public aggregates and private per-person artefacts."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import data as gxd
from . import ssl as gxs
from . import train as gxt
from .runtime import ROOT, cfg, chmod_private, done, open_run, private_dir, read_json, results_dir, write_json_overwrite as write_json


def _torch():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("GX requires a GPU")
    return torch, torch.device("cuda")


# ----------------------------------------------------------------------------- GX2: SSL + probes

def cmd_gx2_ssl(args, config) -> dict:
    torch, device = _torch()
    run = open_run("gx2_ssl", args.run, config, args=vars(args))
    branch = args.branch
    records = gxs.corpus_records(config, branch)
    wpr = int(args.windows_per_record)
    bank, owner, kept = gxs.build_window_bank(config, records, device, windows_per_record=wpr, seed=int(args.seed))
    model, history = gxs.train_masked(config, bank, device, seed=int(args.seed), steps=int(args.steps) if args.steps else None)
    torch.save(model.state_dict(), run["private"] / f"masked_{branch}_s{args.seed}.pt")
    z = gxs.embed_bank(model.encoder, bank)
    rec_emb = gxs.record_embeddings(z, owner, len(kept))
    np.savez_compressed(run["private"] / f"embeddings_{branch}_s{args.seed}.npz", record_embedding=rec_emb,
                        window_embedding=z.astype(np.float32), owner=owner,
                        container_id=np.array([r["container_id"] for r in kept]),
                        identity_group=np.array([r["identity_group"] for r in kept]),
                        age_months=np.array([r["age_months"] for r in kept], dtype=float),
                        source=np.array([r["source_cohort_evidence"] for r in kept]),
                        task=np.array([r["protocol_task"] for r in kept]))
    # probes on record embeddings: age (children with age), source label (explicit vs unknown), task literal
    seeds = [int(s) for s in cfg(config, "folds.seeds")]
    n_folds = int(cfg(config, "folds.n_child_folds"))
    ages = np.array([r["age_months"] for r in kept], dtype=float)
    groups = np.array([r["identity_group"] for r in kept])
    m = np.isfinite(ages) & (groups != "")
    probes = {}
    if m.sum() >= 20:
        probes["age_ridge"] = gxs.ridge_probe(rec_emb[m], ages[m], groups[m], n_folds=n_folds, seeds=seeds)
    tasks = np.array([r["protocol_task"] for r in kept])
    tm = np.isin(tasks, ["puretone", "bapa"]) & (groups != "")
    if tm.sum() >= 20 and len(np.unique(tasks[tm])) == 2:
        probes["task_puretone_vs_bapa"] = gxs.logistic_probe(rec_emb[tm], (tasks[tm] == "bapa").astype(int), groups[tm],
                                                            n_folds=n_folds, seeds=seeds)
    src = np.array([r["source_cohort_evidence"] for r in kept])
    sm = (groups != "") & np.isin(src, ["CI", "CIHA_label", "unknown"])
    if sm.sum() >= 20 and (src[sm] != "unknown").sum() >= 8:
        probes["source_explicit_ci_vs_unknown"] = gxs.logistic_probe(rec_emb[sm], (src[sm] != "unknown").astype(int), groups[sm],
                                                                    n_folds=n_folds, seeds=seeds)
    summary = {"run": args.run, "branch": branch, "records": len(kept), "windows": int(bank.shape[0]),
               "channels": int(bank.shape[1]), "window_samples": int(bank.shape[2]), "steps": len(history) and history[-1]["step"] + 1,
               "final": history[-1] if history else None, "history": history, "probes": probes,
               "hours_in_bank": float(bank.shape[0] * bank.shape[2] / 250.0 / 3600.0)}
    write_json(run["public"] / f"summary_ssl_{branch}_s{args.seed}.json", summary, private=False)
    chmod_private(run["private"])
    done(run["private"], "gx2_ssl", {"records": len(kept)})
    return {k: v for k, v in summary.items() if k != "history"}


def cmd_gx2_event_probe(args, config) -> dict:
    """Frozen SSL encoder applied to event-locked epochs of a lane; child-held-out logistic probe."""
    torch, device = _torch()
    run = open_run("gx2_event_probe", args.run, config, args=vars(args))
    from .models import ConvEncoder
    state = torch.load(private_dir(config, args.ssl_run) / f"masked_{args.branch}_s{args.seed}.pt", map_location=device)
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    enc = ConvEncoder(lane.x.shape[1], int(cfg(config, "ssl.width"))).to(device)
    enc.load_state_dict({k.replace("encoder.", "", 1): v for k, v in state.items() if k.startswith("encoder.")})
    z = gxs.embed_bank(enc, lane.x)
    groups = np.array(lane.child_ids)[lane.child]
    y = lane.y.cpu().numpy()
    res = {}
    if lane.n_classes == 2:
        res["ssl_frozen_logistic"] = gxs.logistic_probe(z, y, groups, n_folds=int(cfg(config, "folds.n_child_folds")),
                                                        seeds=[int(s) for s in cfg(config, "folds.seeds")])
    # random-initialised encoder control: same architecture, no pretraining
    torch.manual_seed(int(args.seed))
    rnd = ConvEncoder(lane.x.shape[1], int(cfg(config, "ssl.width"))).to(device)
    zr = gxs.embed_bank(rnd, lane.x)
    if lane.n_classes == 2:
        res["random_encoder_logistic"] = gxs.logistic_probe(zr, y, groups, n_folds=int(cfg(config, "folds.n_child_folds")),
                                                            seeds=[int(s) for s in cfg(config, "folds.seeds")])
    summary = {"run": args.run, "lane": args.lane, "children": lane.n_children, "trials": int(len(y)), **res}
    write_json(run["public"] / f"summary_event_probe_{args.lane}.json", summary, private=False)
    done(run["private"], "gx2_event_probe", summary)
    return summary


# ----------------------------------------------------------------------------- GX3: age fine-tune

def cmd_gx3_age(args, config) -> dict:
    torch, device = _torch()
    run = open_run("gx3_age", args.run, config, args=vars(args))
    branch = args.branch
    records = gxs.corpus_records(config, branch)
    bank, owner, kept = gxs.build_window_bank(config, records, device, windows_per_record=int(args.windows_per_record), seed=int(args.seed))
    init = None
    if args.ssl_run:
        init = torch.load(private_dir(config, args.ssl_run) / f"masked_{branch}_s{args.seed}.pt", map_location=device)
    seeds = [int(s) for s in cfg(config, "folds.seeds")]
    out = {"pretrained": [], "scratch": []}
    for seed in seeds:
        if init is not None:
            out["pretrained"].append(gxs.finetune_age(config, bank, owner, kept, device, seed=seed, init_state=init,
                                                      n_folds=int(cfg(config, "folds.n_child_folds"))))
        out["scratch"].append(gxs.finetune_age(config, bank, owner, kept, device, seed=seed, init_state=None,
                                               n_folds=int(cfg(config, "folds.n_child_folds"))))
    preds = {k: [r.pop("predictions") for r in v] for k, v in out.items()}
    write_json(run["private"] / f"age_predictions_{branch}.json", preds, private=True)
    summary = {"run": args.run, "branch": branch, "records_in_bank": len(kept),
               **{k: {"mae_mean": float(np.mean([r["mae"] for r in v])) if v else None,
                      "baseline_mae_mean": float(np.mean([r["baseline_mae"] for r in v])) if v else None,
                      "r_mean": float(np.mean([r["r"] for r in v])) if v else None, "per_seed": v} for k, v in out.items()}}
    write_json(run["public"] / f"summary_age_{branch}.json", summary, private=False)
    chmod_private(run["private"])
    done(run["private"], "gx3_age", {"branch": branch})
    return summary


# ----------------------------------------------------------------------------- GX4: cross-task

def cmd_gx4_crosstask(args, config) -> dict:
    """Within-child pure-tone <-> bapa transfer for children with both tasks, and a shared-trunk multi-task net."""
    torch, device = _torch()
    run = open_run("gx4", args.run, config, args=vars(args))
    stage_private = private_dir(config, args.stage_run)
    pt = gxd.load_lane(config, stage_private, "mff_puretone", device)
    bp = gxd.load_lane(config, stage_private, "mff_bapa", device)
    common = sorted(set(pt.child_ids) & set(bp.child_ids))
    seeds = [int(s) for s in cfg(config, "folds.seeds")]
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    rows = []
    for gid in common:
        cp, cb = pt.child_ids.index(gid), bp.child_ids.index(gid)
        for seed in seeds:
            for src_lane, src_c, dst_lane, dst_c, name in ((pt, cp, bp, cb, "puretone_to_bapa"), (bp, cb, pt, cp, "bapa_to_puretone")):
                mine = np.flatnonzero(src_lane.child == src_c)
                order = mine[np.argsort(src_lane.onset_s[mine])]
                n_val = max(8, int(round(val_frac * len(order))))
                tr, va = order[:-n_val], order[-n_val:]
                y_tr = src_lane.y.cpu().numpy()[tr]
                if min(np.sum(y_tr == 0), np.sum(y_tr == 1)) < 40:
                    continue
                gxt.seed_all(seed * 100 + src_c)
                model = gxt.build_model(config, src_lane)
                gxt.fit(model, src_lane, tr, va, config, seed=seed * 100 + src_c)
                # within-task reference on the held-out validation slice (same child, same task)
                same = gxt.child_metrics(gxt.predict(model, src_lane, va), src_lane.y.cpu().numpy()[va], 2)
                dst_idx = np.flatnonzero(dst_lane.child == dst_c)
                cross = gxt.child_metrics(gxt.predict(model, dst_lane, dst_idx), dst_lane.y.cpu().numpy()[dst_idx], 2)
                rows.append({"child": gid[:6], "seed": seed, "direction": name, "same_task_val_auc": same["auc"],
                             "cross_task_auc": cross["auc"], "cross_task_j_bits": cross["j_bits"], "n_train": int(len(tr)),
                             "n_cross": int(len(dst_idx))})
    frame = pd.DataFrame(rows)
    frame.to_csv(run["public"] / "within_child_cross_task.csv", index=False)
    # shared trunk + task heads across all children of both tasks (child-held-out), versus single-task nets
    multi = _multitask(config, pt, bp, seeds, device, torch)
    pd.DataFrame(multi).to_csv(run["public"] / "multitask_child_metrics.csv", index=False)
    mt = pd.DataFrame(multi)
    summary = {"run": args.run, "children_with_both_tasks": len(common),
               "within_child_cross_task_auc_mean": float(frame.cross_task_auc.mean()) if len(frame) else None,
               "within_child_same_task_val_auc_mean": float(frame.same_task_val_auc.mean()) if len(frame) else None,
               "by_direction": {d: float(s.cross_task_auc.mean()) for d, s in frame.groupby("direction")} if len(frame) else {},
               "multitask": {f"{m}/{t}": float(s.groupby("child").auc.mean().mean()) for (m, t), s in mt.groupby(["model", "task"])} if len(mt) else {}}
    write_json(run["public"] / "summary_gx4.json", summary, private=False)
    done(run["private"], "gx4", summary)
    return summary


def _multitask(config, pt, bp, seeds, device, torch):
    """One EEGNet trunk with two heads (task-specific), trained on both lanes; child-held-out by identity group."""
    from torch import nn
    import torch.nn.functional as F
    rows = []
    all_children = sorted(set(pt.child_ids) | set(bp.child_ids))
    n_folds = int(cfg(config, "folds.n_child_folds"))
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    for seed in seeds:
        rng = np.random.default_rng(seed)
        order = rng.permutation(all_children)
        folds = [order[k::n_folds] for k in range(n_folds)]
        for k, test_g in enumerate(folds):
            train_g = np.setdiff1d(order, test_g)
            n_val = max(1, int(round(val_frac * len(train_g))))
            val_g, tr_g = train_g[:n_val], train_g[n_val:]
            for mode in ("multitask", "single_puretone", "single_bapa"):
                gxt.seed_all(seed * 10 + k)
                trunk = gxt.build_model(config, pt)
                heads = nn.ModuleDict({"pt": nn.Linear(trunk.feature_dim, 2), "bp": nn.Linear(trunk.feature_dim, 2)}).to(device)
                trunk.to(device)
                lanes = {"pt": pt, "bp": bp} if mode == "multitask" else ({"pt": pt} if mode == "single_puretone" else {"bp": bp})
                params = list(trunk.parameters()) + list(heads.parameters())
                opt = torch.optim.AdamW(params, lr=float(cfg(config, "train.learning_rate")), weight_decay=float(cfg(config, "train.weight_decay")))
                gen = torch.Generator(device=device)
                gen.manual_seed(seed * 10 + k)
                idx = {t: np.flatnonzero(np.isin(np.array(l.child_ids)[l.child], tr_g)) for t, l in lanes.items()}
                vidx = {t: np.flatnonzero(np.isin(np.array(l.child_ids)[l.child], val_g)) for t, l in lanes.items()}
                weights = {t: gxt.class_weights(l.y[torch.as_tensor(idx[t], device=device)], 2) for t, l in lanes.items()}
                best, best_state, bad = float("inf"), None, 0
                bs = int(cfg(config, "train.batch_size"))
                for epoch in range(int(cfg(config, "train.max_epochs"))):
                    trunk.train()
                    perms = {t: torch.as_tensor(idx[t], device=device)[torch.randperm(len(idx[t]), generator=gen, device=device)] for t in lanes}
                    n_steps = max(len(p) for p in perms.values()) // bs + 1
                    for s in range(n_steps):
                        loss = 0.0
                        for t, l in lanes.items():
                            p = perms[t]
                            sel = p[(s * bs) % max(1, len(p)):(s * bs) % max(1, len(p)) + bs]
                            if len(sel) == 0:
                                continue
                            xb = gxt.augment(l.x[sel], config, gen)
                            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                                logits = heads[t](trunk.embed(xb))
                            loss = loss + F.cross_entropy(logits.float(), l.y[sel], weight=weights[t])
                        opt.zero_grad(set_to_none=True)
                        loss.backward()
                        opt.step()
                    val = np.mean([gxt.balanced_ce_bits(_predict_head(trunk, heads[t], l, vidx[t]), l.y.cpu().numpy()[vidx[t]], 2)
                                   for t, l in lanes.items() if len(vidx[t])])
                    if val < best - 1e-5:
                        best, bad = val, 0
                        best_state = ({k2: v.detach().clone() for k2, v in trunk.state_dict().items()},
                                      {k2: v.detach().clone() for k2, v in heads.state_dict().items()})
                    else:
                        bad += 1
                        if bad >= int(cfg(config, "train.patience")):
                            break
                if best_state is not None:
                    trunk.load_state_dict(best_state[0]); heads.load_state_dict(best_state[1])
                for t, l in lanes.items():
                    te = np.flatnonzero(np.isin(np.array(l.child_ids)[l.child], test_g))
                    if len(te) == 0:
                        continue
                    logits = _predict_head(trunk, heads[t], l, te)
                    y = l.y.cpu().numpy()
                    for c in np.unique(l.child[te]):
                        sel = te[l.child[te] == c]
                        m = gxt.child_metrics(logits[np.isin(te, sel)], y[sel], 2)
                        rows.append({"model": mode, "task": t, "seed": seed, "fold": k, "child": l.child_ids[c][:6], **m})
    return rows


def _predict_head(trunk, head, lane, idx, batch=1024):
    import torch
    trunk.eval()
    out = []
    idx_t = torch.as_tensor(idx, dtype=torch.long, device=lane.x.device)
    with torch.no_grad():
        for b in range(0, len(idx_t), batch):
            xb = lane.x[idx_t[b:b + batch]].float()
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                out.append(head(trunk.embed(xb)).float().cpu().numpy())
    trunk.train()
    return np.concatenate(out) if out else np.zeros((0, 2), dtype=np.float32)


# ----------------------------------------------------------------------------- GX5: multi-condition case series

def cmd_gx5_conditions(args, config) -> dict:
    """Per-record within-record decodability for records that carry a directory condition clue (CI/CIHA x quiet/noise x side)."""
    torch, device = _torch()
    run = open_run("gx5_conditions", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), "mff_unknown_event", device)
    seeds = [int(s) for s in cfg(config, "folds.seeds")]
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    rows = []
    cond_records = [i for i, m in enumerate(lane.record_meta) if m["condition_clue"]]
    y_all = lane.y.cpu().numpy()
    for ri in cond_records:
        meta = lane.record_meta[ri]
        mine = np.flatnonzero(lane.record == ri)
        for seed in seeds:
            for train_block in (0, 1):
                tr = mine[lane.parity[mine] == train_block]
                te = mine[lane.parity[mine] == 1 - train_block]
                if min(np.sum(y_all[tr] == 1), np.sum(y_all[te] == 1)) < 20:
                    continue
                order = tr[np.argsort(lane.onset_s[tr])]
                n_val = max(8, int(round(val_frac * len(order))))
                gxt.seed_all(seed * 100 + ri)
                model = gxt.build_model(config, lane)
                gxt.fit(model, lane, order[:-n_val], order[-n_val:], config, seed=seed * 100 + ri)
                m = gxt.child_metrics(gxt.predict(model, lane, te), y_all[te], 2)
                rows.append({"record": meta["record_id"], "child": meta["identity_group"][:6], "condition": meta["condition_clue"],
                             "seed": seed, "train_block": train_block, **m})
                # transfer to the other records (other conditions) of the same child
                for rj in cond_records:
                    if rj == ri or lane.record_meta[rj]["identity_group"] != meta["identity_group"]:
                        continue
                    other = np.flatnonzero(lane.record == rj)
                    mo = gxt.child_metrics(gxt.predict(model, lane, other), y_all[other], 2)
                    rows.append({"record": meta["record_id"], "child": meta["identity_group"][:6], "condition": meta["condition_clue"],
                                 "seed": seed, "train_block": train_block, "transfer_to_record": lane.record_meta[rj]["record_id"],
                                 "transfer_to_condition": lane.record_meta[rj]["condition_clue"], **{f"transfer_{k}": v for k, v in mo.items()}})
    frame = pd.DataFrame(rows)
    frame.to_csv(run["public"] / "condition_case_series.csv", index=False)
    within = frame[frame.transfer_to_record.isna()] if "transfer_to_record" in frame else frame
    summary = {"run": args.run, "records": len(cond_records), "children": len({lane.record_meta[i]["identity_group"] for i in cond_records}),
               "within_record_auc_by_condition": {c: float(s.auc.mean()) for c, s in within.groupby("condition")} if len(within) else {}}
    write_json(run["public"] / "summary_gx5_conditions.json", summary, private=False)
    done(run["private"], "gx5_conditions", summary)
    return summary


# ----------------------------------------------------------------------------- GX6: within-recording dynamics and repeat visits

def cmd_gx6_dynamics(args, config) -> dict:
    """Segment-wise decodability from the child_spatial predictions (test blocks), and record-to-record transfer for children with several records."""
    torch, device = _torch()
    run = open_run("gx6", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    from sklearn.metrics import roc_auc_score
    seg_s = float(cfg(config, "blocks.segment_seconds"))
    y_all = lane.y.cpu().numpy()
    rows = []
    pred_path = private_dir(config, args.child_spatial_run) / "predictions_child_spatial.npz"
    with np.load(pred_path, allow_pickle=False) as store:
        for key in store.files:
            if "odd_even_blocks" not in key:
                continue
            arr = store[key]
            idx = arr[:, 0].astype(int)
            score = arr[:, 2] - arr[:, 1] if arr.shape[1] == 3 else arr[:, 1:].argmax(1)
            seg = np.floor(lane.onset_s[idx] / seg_s).astype(int)
            for c in np.unique(lane.child[idx]):
                for s in np.unique(seg[lane.child[idx] == c]):
                    sel = (lane.child[idx] == c) & (seg == s)
                    yy = y_all[idx[sel]]
                    if np.sum(yy == 1) >= 8 and np.sum(yy == 0) >= 8 and lane.n_classes == 2:
                        rows.append({"source": key, "child": c, "segment": int(s), "segment_start_s": float(s * seg_s),
                                     "auc": float(roc_auc_score(yy, score[sel])), "n": int(sel.sum())})
    seg_frame = pd.DataFrame(rows)
    seg_frame.to_csv(run["public"] / f"segment_auc_{args.lane}.csv", index=False)
    # record-to-record transfer within child (different acquisitions), against within-record block transfer
    seeds = [int(s) for s in cfg(config, "folds.seeds")]
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    trows = []
    for c in range(lane.n_children):
        recs = sorted({int(r) for r in lane.record[lane.child == c]})
        if len(recs) < 2:
            continue
        for seed in seeds:
            for ri in recs:
                mine = np.flatnonzero(lane.record == ri)
                if min(np.sum(y_all[mine] == 1), np.sum(y_all[mine] == 0)) < 40:
                    continue
                # train on odd blocks of record ri; test on its even blocks (within) and on every other record (across)
                tr = mine[lane.parity[mine] == 0]
                te = mine[lane.parity[mine] == 1]
                if min(np.sum(y_all[tr] == 1), np.sum(y_all[te] == 1)) < 20:
                    continue
                order = tr[np.argsort(lane.onset_s[tr])]
                n_val = max(8, int(round(val_frac * len(order))))
                gxt.seed_all(seed * 1000 + ri)
                model = gxt.build_model(config, lane)
                gxt.fit(model, lane, order[:-n_val], order[-n_val:], config, seed=seed * 1000 + ri)
                within = gxt.child_metrics(gxt.predict(model, lane, te), y_all[te], lane.n_classes)
                for rj in recs:
                    if rj == ri:
                        continue
                    other = np.flatnonzero(lane.record == rj)
                    across = gxt.child_metrics(gxt.predict(model, lane, other), y_all[other], lane.n_classes)
                    trows.append({"child": c, "seed": seed, "train_record": lane.record_ids[ri], "test_record": lane.record_ids[rj],
                                  "same_day": lane.record_meta[ri]["candidate_day_id"] != "" and
                                              lane.record_meta[ri]["candidate_day_id"] == lane.record_meta[rj]["candidate_day_id"],
                                  "within_record_auc": within["auc"], "across_record_auc": across["auc"],
                                  "across_j_bits": across["j_bits"], "n_test": across["n"]})
    tframe = pd.DataFrame(trows)
    tframe.to_csv(run["public"] / f"record_transfer_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "segments_rows": int(len(seg_frame)),
               "children_with_multiple_records": int(tframe.child.nunique()) if len(tframe) else 0,
               "within_record_auc_mean": float(tframe.within_record_auc.mean()) if len(tframe) else None,
               "across_record_auc_mean": float(tframe.across_record_auc.mean()) if len(tframe) else None,
               "across_same_day_auc_mean": float(tframe[tframe.same_day].across_record_auc.mean()) if len(tframe) and tframe.same_day.any() else None,
               "across_other_day_auc_mean": float(tframe[~tframe.same_day].across_record_auc.mean()) if len(tframe) and (~tframe.same_day).any() else None}
    if len(seg_frame):
        first = seg_frame[seg_frame.segment <= seg_frame.segment.quantile(0.33)].groupby("child").auc.mean()
        last = seg_frame[seg_frame.segment >= seg_frame.segment.quantile(0.67)].groupby("child").auc.mean()
        both = first.index.intersection(last.index)
        summary["segment_auc_first_third_mean"] = float(first[both].mean())
        summary["segment_auc_last_third_mean"] = float(last[both].mean())
        summary["children_in_segment_contrast"] = int(len(both))
    write_json(run["public"] / f"summary_gx6_{args.lane}.json", summary, private=False)
    done(run["private"], "gx6", summary)
    return summary


# ----------------------------------------------------------------------------- GX7: relations with age / experience / hearing / scales

def cmd_gx7_relations(args, config) -> dict:
    """Per-child decodability (GX1 per_child + shared) against age, device duration, PTA and scales (HA), age (MFF)."""
    run = open_run("gx7", args.run, config, args=vars(args))
    from scipy.stats import spearmanr
    rows_out = []
    for lane_name, gx1_run in [x.split("=") for x in args.lane_runs.split(",")]:
        meta = json.loads((private_dir(config, gx1_run) / "record_meta.json").read_text())
        child_meta = {}
        for m in meta:
            child_meta.setdefault(m["child"], {"identity_group": m["identity_group"], "age": m["age_months"],
                                              "duration": m["device_duration_months"], "records": []})["records"].append(m["record_id"])
        tables = []
        for path in results_dir(config, gx1_run).glob("child_metrics_*.csv"):
            tables.append(pd.read_csv(path))
        if not tables:
            continue
        cm = pd.concat(tables, ignore_index=True)
        per_child = cm.groupby(["model", "child"]).agg(auc=("auc", "mean"), j_bits=("j_bits", "mean")).reset_index()
        clinical = _ha_clinical(config) if lane_name == "bdf_puretone" else {}
        for model, sub in per_child.groupby("model"):
            sub = sub.copy()
            sub["age"] = sub.child.map(lambda c: child_meta.get(c, {}).get("age", np.nan))
            sub["duration"] = sub.child.map(lambda c: child_meta.get(c, {}).get("duration", np.nan))
            for var in ("age", "duration"):
                m = np.isfinite(sub[var]) & np.isfinite(sub.auc)
                if m.sum() >= 10:
                    r, p = spearmanr(sub.auc[m], sub[var][m])
                    rows_out.append({"lane": lane_name, "model": model, "variable": var, "n": int(m.sum()), "spearman": float(r), "p": float(p)})
            if clinical:
                for var in ("unaided", "aided", "A", "V", "CAP", "SIR"):
                    vals = sub.child.map(lambda c: np.nanmean([clinical.get(rid, {}).get(var, np.nan) for rid in child_meta.get(c, {}).get("records", [])]))
                    m = np.isfinite(vals) & np.isfinite(sub.auc)
                    if m.sum() >= 10:
                        r, p = spearmanr(sub.auc[m], vals[m])
                        rows_out.append({"lane": lane_name, "model": model, "variable": var, "n": int(m.sum()), "spearman": float(r), "p": float(p)})
                        # age-adjusted: residualise both on age
                        ma = m & np.isfinite(sub.age)
                        if ma.sum() >= 12:
                            ra = _resid(sub.auc[ma].to_numpy(), sub.age[ma].to_numpy())
                            rv = _resid(vals[ma].to_numpy(), sub.age[ma].to_numpy())
                            r2, p2 = spearmanr(ra, rv)
                            rows_out.append({"lane": lane_name, "model": model, "variable": f"{var}|age", "n": int(ma.sum()), "spearman": float(r2), "p": float(p2)})
    frame = pd.DataFrame(rows_out)
    frame.to_csv(run["public"] / "relations.csv", index=False)
    write_json(run["public"] / "summary_gx7.json", {"run": args.run, "rows": int(len(frame))}, private=False)
    done(run["private"], "gx7", {"rows": int(len(frame))})
    return {"rows": int(len(frame))}


def _resid(a: np.ndarray, x: np.ndarray) -> np.ndarray:
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, a, rcond=None)
    return a - X @ beta


def _ha_clinical(config: dict) -> dict:
    import csv
    path = ROOT / cfg(config, "sources.ha_clinical")
    out = {}
    with path.open(newline="", encoding="utf-8") as h:
        for row in csv.DictReader(h):
            def num(k):
                try:
                    v = float(row[k]); return v if np.isfinite(v) else np.nan
                except (TypeError, ValueError):
                    return np.nan
            out[str(row["recording"])] = {k: num(k) for k in ("unaided", "aided", "A", "V", "CAP", "SIR", "age", "duration")}
    return out


# ----------------------------------------------------------------------------- GX8: session-level view of the fixed shared readout

def cmd_gx8_session(args, config) -> dict:
    """Per-record AUC under the held-out shared model: visit consistency, source labels, session-quality proxies."""
    torch, device = _torch()
    run = open_run("gx8", args.run, config, args=vars(args))
    from sklearn.metrics import roc_auc_score
    from scipy.stats import spearmanr
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y_all = lane.y.cpu().numpy()
    rows = []
    with np.load(private_dir(config, args.base_run) / "predictions_shared.npz", allow_pickle=False) as store:
        for key in store.files:
            arr = store[key]
            idx = arr[:, 0].astype(int)
            score = arr[:, 2] - arr[:, 1] if arr.shape[1] == 3 else arr[:, 1:].max(1)
            seed = int(key.split("_s")[1].split("_")[0])
            for r in np.unique(lane.record[idx]):
                sel = lane.record[idx] == r
                yy = y_all[idx[sel]]
                if len(np.unique(yy)) < 2:
                    continue
                m = lane.record_meta[r]
                rows.append({"seed": seed, "record": m["record_id"], "child": m["child"], "n": int(sel.sum()),
                             "n_dev": int((yy == 1).sum()), "auc": float(roc_auc_score(yy, score[sel])),
                             "source": m["source_cohort_evidence"], "condition": m["condition_clue"],
                             "day": m["candidate_day_id"], "age_months": m["age_months"],
                             "device_duration_months": m["device_duration_months"], "record_scale": m["record_scale"]})
    f = pd.DataFrame(rows)
    per_record = f.groupby(["record", "child"]).agg(auc=("auc", "mean"), n=("n", "mean"), n_dev=("n_dev", "mean"),
                                                   source=("source", "first"), condition=("condition", "first"),
                                                   day=("day", "first"), age=("age_months", "first"),
                                                   duration=("device_duration_months", "first"),
                                                   record_scale=("record_scale", "first")).reset_index()
    per_record.to_csv(run["public"] / f"record_auc_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "records": int(len(per_record)),
               "record_auc_mean": float(per_record.auc.mean()), "record_auc_sd": float(per_record.auc.std()),
               "records_auc_gt_0.5": int((per_record.auc > 0.5).sum())}
    # visit consistency: children with >= 2 records, pairwise across records (ICC-like via correlation of first two)
    multi = per_record.groupby("child").filter(lambda d: len(d) >= 2)
    if multi.child.nunique() >= 5:
        first = multi.sort_values("record").groupby("child").nth(0).set_index("child").auc
        second = multi.sort_values("record").groupby("child").nth(1).set_index("child").auc
        common = first.index.intersection(second.index)
        rho, p = spearmanr(first[common], second[common])
        summary["visit_consistency"] = {"children": int(len(common)), "spearman_record1_record2": float(rho), "p": float(p),
                                        "mean_abs_diff": float(np.mean(np.abs(first[common] - second[common]))),
                                        "between_child_sd": float(per_record.groupby("child").auc.mean().std())}
    # source labels
    by_source = per_record.groupby("source").agg(records=("auc", "size"), children=("child", "nunique"), auc_mean=("auc", "mean"),
                                                 auc_median=("auc", "median")).reset_index()
    summary["by_source"] = by_source.to_dict("records")
    # session-quality proxies
    for var in ("n", "n_dev", "record_scale", "age", "duration"):
        m = np.isfinite(per_record[var].astype(float)) & np.isfinite(per_record.auc)
        if m.sum() >= 10:
            rho, p = spearmanr(per_record.auc[m], per_record[var][m].astype(float))
            summary[f"spearman_auc_vs_{var}"] = {"n": int(m.sum()), "rho": float(rho), "p": float(p)}
    write_json(run["public"] / f"summary_gx8_{args.lane}.json", summary, private=False)
    done(run["private"], "gx8", summary)
    return summary


# ----------------------------------------------------------------------------- GX9: readout within fixed stimulus-history strata

def cmd_gx9_history(args, config) -> dict:
    """Is the shared readout stimulus-locked or expectation-driven? AUC within strata of previous run length / previous code."""
    torch, device = _torch()
    run = open_run("gx9", args.run, config, args=vars(args))
    from sklearn.metrics import roc_auc_score
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y_all = lane.y.cpu().numpy()
    names = ["prev_code_0", "prev_code_1", "prev_unknown", "log1p_gap", "prev_run_1", "prev_run_2", "prev_run_3", "prev_run_4",
             "prev_run_5plus", "prev_run_unknown", "first_in_chain"]
    H = lane.hist
    strata = {"after_standard_run1": (H[:, names.index("prev_code_0")] == 1) & (H[:, names.index("prev_run_1")] == 1),
              "after_standard_run2": (H[:, names.index("prev_code_0")] == 1) & (H[:, names.index("prev_run_2")] == 1),
              "after_standard_run3": (H[:, names.index("prev_code_0")] == 1) & (H[:, names.index("prev_run_3")] == 1),
              "after_standard_run4plus": (H[:, names.index("prev_code_0")] == 1) & ((H[:, names.index("prev_run_4")] == 1) | (H[:, names.index("prev_run_5plus")] == 1)),
              "after_deviant": H[:, names.index("prev_code_1")] == 1,
              "all": np.ones(len(y_all), dtype=bool)}
    rows = []
    with np.load(private_dir(config, args.base_run) / "predictions_shared.npz", allow_pickle=False) as store:
        for key in store.files:
            arr = store[key]
            idx = arr[:, 0].astype(int)
            score = arr[:, 2] - arr[:, 1]
            seed = int(key.split("_s")[1].split("_")[0])
            for name, mask in strata.items():
                sel_all = mask[idx]
                for c in np.unique(lane.child[idx]):
                    sel = sel_all & (lane.child[idx] == c)
                    yy = y_all[idx[sel]]
                    if np.sum(yy == 1) >= 10 and np.sum(yy == 0) >= 10:
                        rows.append({"seed": seed, "stratum": name, "child": int(c), "n": int(sel.sum()), "n_dev": int((yy == 1).sum()),
                                     "dev_rate": float((yy == 1).mean()), "auc": float(roc_auc_score(yy, score[sel]))})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"history_strata_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane,
               "by_stratum": {s: {"children": int(d.child.nunique()), "auc_child_mean": float(d.groupby("child").auc.mean().mean()),
                                  "dev_rate_mean": float(d.dev_rate.mean()), "trials_mean_per_child": float(d.groupby("child").n.mean().mean())}
                              for s, d in f.groupby("stratum")}}
    write_json(run["public"] / f"summary_gx9_{args.lane}.json", summary, private=False)
    done(run["private"], "gx9", summary)
    return summary


# ----------------------------------------------------------------------------- GX10: Riemannian covariance + per-record alignment baseline

def cmd_gx10_riemann(args, config) -> dict:
    """Per-trial shrinkage covariance, per-record recentering, tangent space, logistic; child-held-out like GX1."""
    torch, device = _torch()
    run = open_run("gx10", args.run, config, args=vars(args))
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y_all = lane.y.cpu().numpy()
    N, C, T = lane.x.shape
    pre = int(round(float(cfg(config, "epoch.pre_seconds")) * float(cfg(config, "epoch.rate_hz"))))
    seg = slice(pre, T) if args.window == "post" else slice(0, T)
    shrink = 0.1
    covs = torch.empty(N, C, C, device=device)
    for b in range(0, N, 2048):
        x = lane.x[b:b + 2048, :, seg].float()
        x = x - x.mean(-1, keepdim=True)
        S = x @ x.transpose(1, 2) / x.shape[-1]
        tr = torch.diagonal(S, dim1=1, dim2=2).mean(-1)[:, None, None]
        covs[b:b + 2048] = (1 - shrink) * S + shrink * tr * torch.eye(C, device=device)
    def inv_sqrt(M):
        w, V = torch.linalg.eigh(M)
        return V @ torch.diag_embed(w.clamp(min=1e-8).rsqrt()) @ V.transpose(-1, -2)
    def logm(M):
        w, V = torch.linalg.eigh(M)
        return V @ torch.diag_embed(w.clamp(min=1e-8).log()) @ V.transpose(-1, -2)
    # per-record recentering with the record's mean covariance (label-free)
    aligned = torch.empty_like(covs)
    for r in np.unique(lane.record):
        sel = torch.as_tensor(np.flatnonzero(lane.record == r), device=device)
        ref = inv_sqrt(covs[sel].mean(0))
        aligned[sel] = ref @ covs[sel] @ ref
    iu = torch.triu_indices(C, C, device=device)
    weight = torch.where(iu[0] == iu[1], torch.ones(iu.shape[1], device=device), torch.full((iu.shape[1],), 2 ** 0.5, device=device))
    feats = np.empty((N, iu.shape[1]), dtype=np.float32)
    for b in range(0, N, 2048):
        L = logm(aligned[b:b + 2048])
        feats[b:b + 2048] = (L[:, iu[0], iu[1]] * weight).cpu().numpy()
    del covs, aligned
    seeds = [int(s) for s in cfg(config, "folds.seeds")]
    n_folds = int(cfg(config, "folds.n_child_folds"))
    n_comp = min(200, feats.shape[1])
    rows = []
    for seed in seeds:
        folds = gxd.child_folds(lane.n_children, n_folds, seed)
        for k, test_children in enumerate(folds):
            tr = gxd.idx_of_children(lane, np.setdiff1d(np.arange(lane.n_children), test_children))
            te = gxd.idx_of_children(lane, test_children)
            sc = StandardScaler().fit(feats[tr])
            pca = PCA(n_components=n_comp, random_state=seed).fit(sc.transform(feats[tr]))
            Xtr, Xte = pca.transform(sc.transform(feats[tr])), pca.transform(sc.transform(feats[te]))
            clf = LogisticRegression(C=0.1, max_iter=3000, class_weight="balanced").fit(Xtr, y_all[tr])
            score = clf.decision_function(Xte)
            logits = np.column_stack([-score / 2, score / 2])
            for c in np.unique(lane.child[te]):
                sel = lane.child[te] == c
                m = gxt.child_metrics(logits[sel], y_all[te[sel]], 2)
                rows.append({"model": f"riemann_{args.window}", "seed": seed, "fold": k, "child": int(c), **m})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"child_metrics_riemann_{args.lane}.csv", index=False)
    per_child = f.groupby("child").auc.mean()
    summary = {"run": args.run, "lane": args.lane, "window": args.window, "children": int(len(per_child)), "features": int(feats.shape[1]),
               "pca_components": int(n_comp), "auc_child_mean": float(per_child.mean()), "auc_child_median": float(per_child.median()),
               "children_auc_gt_0.5": int((per_child > 0.5).sum()),
               "auc_seed_range": [float(v) for v in f.groupby("seed").apply(lambda d: d.groupby("child").auc.mean().mean(), include_groups=False)]}
    write_json(run["public"] / f"summary_gx10_{args.lane}_{args.window}.json", summary, private=False)
    done(run["private"], "gx10", summary)
    return summary


# ----------------------------------------------------------------------------- GX11: session-held-out vs child-held-out

def cmd_gx11_session_heldout(args, config) -> dict:
    """For children with several records: train on everyone incl. the child's OTHER records, test the held-out record."""
    torch, device = _torch()
    run = open_run("gx11", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y_all = lane.y.cpu().numpy()
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    seed = int(args.seed)
    rows = []
    multi = [c for c in range(lane.n_children) if len(np.unique(lane.record[lane.child == c])) >= 2]
    for c in multi:
        recs = sorted(np.unique(lane.record[lane.child == c]))
        for r in recs:
            test = np.flatnonzero(lane.record == r)
            if min(np.sum(y_all[test] == 1), np.sum(y_all[test] == 0)) < 20:
                continue
            others = np.setdiff1d(np.arange(lane.n_children), [c])
            rng = np.random.default_rng(seed + int(r))
            val_children = rng.choice(others, size=max(1, int(round(val_frac * len(others)))), replace=False)
            train_children = np.setdiff1d(others, val_children)
            # session-held-out: the child's other records join the training set
            tr_idx = np.concatenate([gxd.idx_of_children(lane, train_children), np.flatnonzero((lane.child == c) & (lane.record != r))])
            va_idx = gxd.idx_of_children(lane, val_children)
            gxt.seed_all(seed * 100 + int(r))
            model = gxt.build_model(config, lane)
            gxt.fit(model, lane, tr_idx, va_idx, config, seed=seed * 100 + int(r), max_epochs=25)
            m_session = gxt.child_metrics(gxt.predict(model, lane, test), y_all[test], lane.n_classes)
            # child-held-out control with the same training children (child c entirely absent)
            gxt.seed_all(seed * 100 + int(r) + 1)
            model2 = gxt.build_model(config, lane)
            gxt.fit(model2, lane, gxd.idx_of_children(lane, train_children), va_idx, config, seed=seed * 100 + int(r) + 1, max_epochs=25)
            m_child = gxt.child_metrics(gxt.predict(model2, lane, test), y_all[test], lane.n_classes)
            meta = lane.record_meta[r]
            rows.append({"child": int(c), "record": meta["record_id"], "n_other_records": len(recs) - 1,
                         "n_other_trials": int(np.sum((lane.child == c) & (lane.record != r))),
                         "session_heldout_auc": m_session["auc"], "child_heldout_auc": m_child["auc"],
                         "gain": m_session["auc"] - m_child["auc"], "n_test": int(len(test))})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"session_heldout_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "children": int(f.child.nunique()) if len(f) else 0, "records": int(len(f)),
               "session_heldout_auc_mean": float(f.session_heldout_auc.mean()) if len(f) else None,
               "child_heldout_auc_mean": float(f.child_heldout_auc.mean()) if len(f) else None,
               "gain_mean": float(f.gain.mean()) if len(f) else None,
               "gain_children_positive": int((f.groupby("child").gain.mean() > 0).sum()) if len(f) else 0}
    write_json(run["public"] / f"summary_gx11_{args.lane}.json", summary, private=False)
    done(run["private"], "gx11", summary)
    return summary
