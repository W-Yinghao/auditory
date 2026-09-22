"""auditory_gx runner. Slurm only. GPU for every model; CPU only for the one-time staging.

  stage   --run S                                   [array] event-locked epoch tensors per record
  gx1     --run R --stage-run S --lane L --model M  shared | film_age | film_age_shuffled | child_spatial | per_child | adapt
  collect --run R                                   aggregate child tables of finished gx1 runs into one summary
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from auditory_st import runtime as st_runtime

from . import routes as rt
from . import stage as stg
from . import summarize as sm
from . import occlusion as oc
from . import round2 as r2
from . import round2b as r2b
from . import round3 as r3
from . import round4 as r4
from . import round5 as r5
from .runtime import (ROOT, array_slice, cfg, chmod_private, done, load_config, open_run, private_dir, read_json, results_dir,
                      write_json, write_json_overwrite)


# ----------------------------------------------------------------------------- stage

def cmd_stage(args, config) -> dict:
    run = open_run("stage", args.run, config, args=vars(args))
    config_st = st_runtime.load_config()
    scope_private = ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run")
    records = pd.read_parquet(scope_private / "records.parquet")
    lanes = [x for x in args.lanes.split(",") if x] if args.lanes_subset else list(cfg(config, "lanes"))
    keep = records[records.lane.isin(lanes) & records.d1_exported.astype(bool)
                   & records.source_gate.isin(["eligible", "eligible_technical_measurement"])]
    keep = keep.sort_values("record_id").to_dict("records")
    cond = stg.condition_map(config)
    out_dir, sum_dir = run["private"] / "epochs", run["private"] / "summaries"
    for d in (out_dir, sum_dir):
        d.mkdir(mode=0o700, exist_ok=True)
    mine = array_slice(keep)
    n_done = n_fail = n_skip = 0
    for rec in mine:
        rid = rec["record_id"]
        target = sum_dir / f"{rid}.json"
        if target.exists():
            n_skip += 1
            continue
        try:
            payload = stg.stage_record(rec, scope_private, config, config_st, cond, variant=args.variant)
            np.savez(out_dir / f"{rid}.npz", **payload)
            (out_dir / f"{rid}.npz").chmod(0o600)
            summary = {"status": "OK", **stg.summary_of(payload)}
            n_done += 1
        except Exception as exc:
            summary = {"status": "FAILED", "record_id": rid, "lane": rec["lane"], "error_class": type(exc).__name__,
                       "error": str(exc)[:400], "traceback_tail": traceback.format_exc()[-1200:]}
            n_fail += 1
        write_json(target, summary, private=True)
    result = {"assigned": len(mine), "done": n_done, "failed": n_fail, "skipped": n_skip}
    done(run["private"], "stage", result)
    return result


def cmd_stage_summary(args, config) -> dict:
    run = open_run("stage_summary", args.run, config, args=vars(args))
    rows = [read_json(p) for p in sorted((run["private"] / "summaries").glob("*.json"))]
    frame = pd.DataFrame([{k: v for k, v in r.items() if k not in ("traceback_tail", "identity_group")} for r in rows])
    frame.to_csv(run["public"] / "stage_records.csv", index=False)
    by = {}
    for lane, sub in frame[frame.status == "OK"].groupby("lane"):
        by[lane] = {"records": int(len(sub)), "epochs": int(sub.n_epochs.sum()), "accepted": int(sub.n_accepted.sum()),
                    "children": int(pd.DataFrame(rows)[(pd.DataFrame(rows).lane == lane)].identity_group.nunique())}
    summary = {"run": args.run, "status_counts": {k: int(v) for k, v in frame.status.value_counts().items()}, "by_lane": by}
    write_json_overwrite(run["public"] / "stage_summary.json", summary, private=False)
    return summary


# ----------------------------------------------------------------------------- gx1

def _torch():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("GX requires a GPU (submit through slurm/auditory_gx_gpu.sbatch)")
    return torch, torch.device("cuda")


def _age_cond(lane, children_idx_train, device, torch, *, shuffle_seed: int | None = None):
    """Per-trial z-scored age tensor (train statistics). Optionally permute ages across training children."""
    ages = lane.age_child.copy()
    if shuffle_seed is not None:
        rng = np.random.default_rng(shuffle_seed)
        tr = np.asarray(children_idx_train)
        ages[tr] = ages[tr][rng.permutation(len(tr))]
    mu, sd = np.nanmean(ages[children_idx_train]), np.nanstd(ages[children_idx_train]) + 1e-6
    z = (ages - mu) / sd
    per_trial = z[lane.child]
    return torch.as_tensor(np.nan_to_num(per_trial, nan=0.0), dtype=torch.float32, device=device).unsqueeze(1)


def _metrics_rows(lane, logits, idx, tag: dict, train_module) -> list[dict]:
    y = lane.y.cpu().numpy()
    rows = []
    for c in np.unique(lane.child[idx]):
        sel = idx[lane.child[idx] == c]
        m = train_module.child_metrics(logits[np.isin(idx, sel)], y[sel], lane.n_classes)
        rows.append({**tag, "child": int(c), "n_records": int(len(np.unique(lane.record[sel]))),
                     "age_months": float(lane.age_child[c]), **m})
    return rows


def cmd_gx1(args, config) -> dict:
    from . import data as gxd
    from . import train as gxt
    torch, device = _torch()
    run = open_run("gx1", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device, accepted_only=not args.include_rejected)
    if args.include_rejected:
        gxt.TRIAL_WEIGHTS = torch.as_tensor(1.0 / (1.0 + 5.0 * lane.qc_over), dtype=torch.float32, device=device)
    if args.whiten:
        gxd.whiten_records(lane)
    if args.time_mask:
        pre = int(round(float(cfg(config, "epoch.pre_seconds")) * float(cfg(config, "epoch.rate_hz"))))
        keep = torch.zeros(lane.x.shape[2], dtype=lane.x.dtype, device=device)
        if args.time_mask == "pre_only":
            keep[:pre] = 1
        elif args.time_mask == "post_only":
            keep[pre:] = 1
        else:
            raise ValueError(args.time_mask)
        lane.x = lane.x * keep            # architecture unchanged; only the informative samples differ
    seeds = [int(s) for s in (args.seeds.split(",") if args.seeds else cfg(config, "folds.seeds"))]
    n_folds = int(cfg(config, "folds.n_child_folds"))
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    min_pc = int(cfg(config, "qc.min_trials_per_class_for_within_child"))
    models_dir = run["private"] / "models"
    models_dir.mkdir(mode=0o700, exist_ok=True)
    rows, logs, pred_store = [], [], {}
    y_all = lane.y.cpu().numpy()
    kind = args.model

    if kind in ("shared", "film_age", "film_age_shuffled"):
        pool = np.arange(lane.n_children)
        if kind != "shared":
            pool = np.flatnonzero(np.isfinite(lane.age_child))
            if len(pool) < 15:
                raise RuntimeError(f"AGE_CHILDREN_TOO_FEW:{len(pool)}")
        if len(pool) < n_folds:
            raise RuntimeError(f"CHILDREN_FEWER_THAN_FOLDS:{len(pool)}")
        folds_record = {"model": kind}
        for seed in seeds:
            folds = gxd.child_folds(len(pool), n_folds, seed)
            folds_record[str(seed)] = [pool[f].tolist() for f in folds]
            for k, f in enumerate(folds):
                test_children = pool[f]
                train_children = np.setdiff1d(pool, test_children)
                inner_tr, inner_val = gxd.split_inner(train_children, val_frac, seed * 10 + k)
                cond = None
                if kind != "shared":
                    cond = _age_cond(lane, train_children, device, torch,
                                     shuffle_seed=(seed * 100 + k) if kind == "film_age_shuffled" else None)
                gxt.seed_all(seed * 10 + k)          # seed BEFORE construction so initial weights follow the seed
                model = gxt.build_model(config, lane, cond_dim=1 if cond is not None else 0)
                log = []
                info = gxt.fit(model, lane, gxd.idx_of_children(lane, inner_tr), gxd.idx_of_children(lane, inner_val),
                               config, seed=seed * 10 + k, cond=cond, log=log)
                test_idx = gxd.idx_of_children(lane, test_children)
                logits = gxt.predict(model, lane, test_idx, cond=cond)
                tag = {"model": kind, "seed": seed, "fold": k}
                rows += _metrics_rows(lane, logits, test_idx, tag, gxt)
                pred_store[f"{kind}_s{seed}_f{k}"] = np.column_stack([test_idx, logits])
                torch.save(model.state_dict(), models_dir / f"{kind}_s{seed}_f{k}.pt")
                logs.append({**tag, **info, "n_train": int(len(inner_tr)), "n_test_children": int(len(test_children))})
        write_json_overwrite(run["private"] / "folds.json", folds_record, private=True)

    elif kind == "child_spatial":
        for seed in seeds:
            for part_name, part in (("odd_even_blocks", lane.parity), ("early_late_halves", lane.half)):
                for train_block in (0, 1):
                    eligible, tr_idx, va_idx, te_idx = [], [], [], []
                    for c in range(lane.n_children):
                        split = gxd.within_child_split(lane, c, part, train_block, val_fraction=val_frac, seed=seed,
                                                       min_per_class=min_pc)
                        if split is None:
                            continue
                        eligible.append(c); tr_idx.append(split[0]); va_idx.append(split[1]); te_idx.append(split[2])
                    if not eligible:
                        continue
                    tr_idx, va_idx, te_idx = map(np.concatenate, (tr_idx, va_idx, te_idx))
                    gxt.seed_all(seed * 10 + train_block)
                    model = gxt.build_model(config, lane, n_children=lane.n_children)
                    child_t = lane.child_index_tensor(device)
                    log = []
                    info = gxt.fit(model, lane, tr_idx, va_idx, config, seed=seed * 10 + train_block, child=child_t, log=log)
                    logits = gxt.predict(model, lane, te_idx, child=child_t)
                    tag = {"model": kind, "seed": seed, "partition": part_name, "train_block": train_block}
                    rows += _metrics_rows(lane, logits, te_idx, tag, gxt)
                    # the same trained network with the MEAN spatial filter: how much is child-specific?
                    model.share_child_filters_from_mean()
                    fallback = torch.full_like(child_t, lane.n_children)
                    logits_mean = gxt.predict(model, lane, te_idx, child=fallback)
                    rows += _metrics_rows(lane, logits_mean, te_idx, {**tag, "model": "child_spatial_meanfilter"}, gxt)
                    pred_store[f"{kind}_s{seed}_{part_name}_b{train_block}"] = np.column_stack([te_idx, logits])
                    torch.save(model.state_dict(), models_dir / f"{kind}_s{seed}_{part_name}_b{train_block}.pt")
                    logs.append({**tag, **info, "n_children": len(eligible), "n_train": int(len(tr_idx))})

    elif kind == "per_child":
        for seed in seeds:
            for part_name, part in (("odd_even_blocks", lane.parity), ("early_late_halves", lane.half)):
                for c in range(lane.n_children):
                    for train_block in (0, 1):
                        split = gxd.within_child_split(lane, c, part, train_block, val_fraction=val_frac, seed=seed,
                                                       min_per_class=min_pc)
                        if split is None:
                            continue
                        gxt.seed_all(seed * 1000 + c * 2 + train_block)
                        model = gxt.build_model(config, lane)
                        info = gxt.fit(model, lane, split[0], split[1], config, seed=seed * 1000 + c * 2 + train_block)
                        logits = gxt.predict(model, lane, split[2])
                        tag = {"model": kind, "seed": seed, "partition": part_name, "train_block": train_block}
                        rows += _metrics_rows(lane, logits, split[2], tag, gxt)
                        logs.append({**tag, "child": c, **info, "n_train": int(len(split[0]))})

    elif kind == "adapt":
        base_private = private_dir(config, args.base_run)
        folds_record = read_json(base_private / "folds.json")
        if folds_record.get("model", "shared") != "shared":
            raise RuntimeError("ADAPT_BASE_MUST_BE_SHARED")
        adapt_epochs, adapt_lr = 8, float(cfg(config, "train.learning_rate")) / 5
        part = lane.parity
        for seed_str, folds in folds_record.items():
            if seed_str == "model":
                continue
            seed = int(seed_str)
            for k, test_children in enumerate(folds):
                state = torch.load(base_private / "models" / f"shared_s{seed}_f{k}.pt", map_location=device)
                for c in test_children:
                    split = gxd.within_child_split(lane, int(c), part, 0, val_fraction=val_frac, seed=seed, min_per_class=min_pc)
                    if split is None:
                        continue
                    model = gxt.build_model(config, lane)
                    model.load_state_dict(state)
                    model.to(device)
                    zero = gxt.predict(model, lane, split[2])
                    tag = {"model": "adapt_zero_shot", "seed": seed, "fold": k, "partition": "odd_even_blocks", "train_block": 0}
                    rows += _metrics_rows(lane, zero, split[2], tag, gxt)
                    info = gxt.fit(model, lane, split[0], split[1], config, seed=seed * 1000 + int(c), max_epochs=adapt_epochs,
                                   learning_rate=adapt_lr)
                    adapted = gxt.predict(model, lane, split[2])
                    rows += _metrics_rows(lane, adapted, split[2], {**tag, "model": "adapt_finetuned"}, gxt)
                    logs.append({**tag, "child": int(c), **info, "n_train": int(len(split[0]))})
    elif kind == "adabn":
        # test-time BatchNorm recalibration on the held-out child's own trials (no labels, no weight update)
        base_private = private_dir(config, args.base_run)
        folds_record = read_json(base_private / "folds.json")
        for seed_str, fold_list in folds_record.items():
            if seed_str == "model":
                continue
            seed = int(seed_str)
            for k, test_children in enumerate(fold_list):
                state = torch.load(base_private / "models" / f"shared_s{seed}_f{k}.pt", map_location=device)
                for c in test_children:
                    idx = np.flatnonzero(lane.child == int(c))
                    model = gxt.build_model(config, lane)
                    model.load_state_dict(state)
                    model.to(device)
                    base = gxt.predict(model, lane, idx)
                    rows += _metrics_rows(lane, base, idx, {"model": "adabn_zero_shot", "seed": seed, "fold": k}, gxt)
                    for mod in model.modules():
                        if isinstance(mod, torch.nn.BatchNorm2d):
                            mod.reset_running_stats()
                            mod.momentum = None            # cumulative average over the child's trials
                            mod.train()
                    with torch.no_grad():
                        for b in range(0, len(idx), 512):
                            xb = lane.x[torch.as_tensor(idx[b:b + 512], device=device)].float()
                            model(xb)
                    model.eval()
                    recal = gxt.predict(model, lane, idx)
                    rows += _metrics_rows(lane, recal, idx, {"model": "adabn_recalibrated", "seed": seed, "fold": k}, gxt)
    else:
        raise ValueError(f"unknown model {kind}")

    frame = pd.DataFrame(rows)
    frame.to_csv(run["public"] / f"child_metrics_{kind}.csv", index=False)
    (run["public"] / f"child_metrics_{kind}.csv").chmod(0o644)
    if pred_store:
        np.savez_compressed(run["private"] / f"predictions_{kind}.npz", **pred_store)
    pd.DataFrame(logs).to_csv(run["private"] / f"fit_log_{kind}.csv", index=False)
    with (run["private"] / "record_meta.json").open("w") as h:
        json.dump(lane.record_meta, h, indent=1)
    chmod_private(run["private"])
    summary = {"run": args.run, "lane": args.lane, "model": kind, "children": lane.n_children,
               "records": len(lane.record_ids), "trials": int(lane.x.shape[0]), "n_classes": lane.n_classes,
               "channels": int(lane.x.shape[1]), "times": int(lane.x.shape[2]), "seeds": seeds,
               "by_model": {m: {"children": int(sub.child.nunique()),
                                "auc_mean_over_children": float(sub.groupby("child").auc.mean().mean()),
                                "auc_median_child": float(sub.groupby("child").auc.mean().median()),
                                "j_bits_mean": float(sub.groupby("child").j_bits.mean().mean()),
                                "bacc_mean": float(sub.groupby("child").bacc.mean().mean()),
                                **({"auc_pitch_direction_mean": float(sub.groupby("child").auc_pitch_direction.mean().mean())}
                                   if "auc_pitch_direction" in sub else {})}
                            for m, sub in frame.groupby("model")} if len(frame) else {}}
    write_json_overwrite(run["public"] / f"summary_{kind}.json", summary, private=False)
    done(run["private"], f"gx1_{kind}", summary)
    return summary


# ----------------------------------------------------------------------------- collect

def cmd_collect(args, config) -> dict:
    run = open_run("collect", args.run, config, args=vars(args))
    frames = []
    for path in sorted((ROOT / cfg(config, "paths.results_relative")).glob("GX1_*/child_metrics_*.csv")):
        f = pd.read_csv(path)
        f["source_run"] = path.parent.name
        frames.append(f)
    if not frames:
        raise RuntimeError("NO_GX1_RESULTS")
    allf = pd.concat(frames, ignore_index=True)
    allf.to_csv(run["public"] / "gx1_all_child_metrics.csv", index=False)
    table = (allf.groupby(["source_run", "model"])
             .agg(children=("child", "nunique"), auc_child_mean=("auc", "mean"), j_bits_child_mean=("j_bits", "mean"),
                  bacc_child_mean=("bacc", "mean"))
             .reset_index())
    table.to_csv(run["public"] / "gx1_table.csv", index=False)
    return {"rows": int(len(allf)), "runs": sorted(allf.source_run.unique().tolist())}


# ----------------------------------------------------------------------------- main

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="auditory_gx")
    parser.add_argument("command", choices=["stage", "stage-summary", "gx1", "collect", "gx2-ssl", "gx2-event-probe",
                                            "gx3-age", "gx4", "gx5-conditions", "gx6", "gx7", "summarize", "occlusion", "gx8", "gx9", "gx10", "gx11",
                                            "r2-expectation", "r2-repetition", "r2-embed-age", "r2-fingerprint", "r2-instrument", "r2-nh",
                                            "gx12", "gx13", "gx14",
                                            "r3-artefact", "r3-peaks", "r3-memory", "r3-pitch", "r3-records", "r3-agematrix", "r3-nh-classify",
                                            "r4-experience", "r4-pitch-attr", "r4-ci-memory", "r4-trait", "r4-inverted", "r4-literals", "r4-direction", "r4-hf-topo",
                                            "r5-curves", "r5-wlate", "r5-templates", "r5-align", "r5-memory", "r5-hf", "r5-joint"])
    parser.add_argument("--run", required=True)
    parser.add_argument("--config", default="configs/auditory_gx_v1.yaml")
    parser.add_argument("--stage-run", default="GX_stage_001")
    parser.add_argument("--lanes", default="mff_puretone,mff_bapa,bdf_puretone")
    parser.add_argument("--lane")
    parser.add_argument("--model")
    parser.add_argument("--seeds")
    parser.add_argument("--base-run")
    parser.add_argument("--branch", default="MFF")
    parser.add_argument("--seed", default="11")
    parser.add_argument("--steps")
    parser.add_argument("--windows-per-record", default="120")
    parser.add_argument("--ssl-run")
    parser.add_argument("--child-spatial-run")
    parser.add_argument("--lane-runs", default="")
    parser.add_argument("--time-mask", default="")
    parser.add_argument("--window", default="post")
    parser.add_argument("--preonly-run", default="")
    parser.add_argument("--variant", default="")
    parser.add_argument("--lanes-subset", action="store_true")
    parser.add_argument("--include-rejected", action="store_true")
    parser.add_argument("--min-records", default="5")
    parser.add_argument("--whiten", action="store_true")
    parser.add_argument("--curves-run", default="R5_curves_bdf_puretone")
    parser.add_argument("--hf-run", default="GX1_mff_unknown_event_shared_allqc_band_30_45")
    parser.add_argument("--wlate-run", default="R5_wlate")
    parser.add_argument("--memory-run", default="R5_memory_bdf_puretone")
    parser.add_argument("--heldout-sessions", default="2")
    parser.add_argument("--bapa-run", default="GX1_mff_bapa_shared")
    parser.add_argument("--puretone-run", default="GX1_mff_puretone_shared")
    args = parser.parse_args(argv)
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Slurm only")
    os.umask(0o077)
    config = load_config(args.config)
    result = {"stage": cmd_stage, "stage-summary": cmd_stage_summary, "gx1": cmd_gx1, "collect": cmd_collect,
              "gx2-ssl": rt.cmd_gx2_ssl, "gx2-event-probe": rt.cmd_gx2_event_probe, "gx3-age": rt.cmd_gx3_age,
              "gx4": rt.cmd_gx4_crosstask, "gx5-conditions": rt.cmd_gx5_conditions, "gx6": rt.cmd_gx6_dynamics,
              "gx7": rt.cmd_gx7_relations, "summarize": sm.cmd_summarize,
              "occlusion": oc.cmd_occlusion, "gx8": rt.cmd_gx8_session,
              "gx9": rt.cmd_gx9_history, "gx10": rt.cmd_gx10_riemann, "gx11": rt.cmd_gx11_session_heldout,
              "r2-expectation": r2.cmd_r2_expectation, "r2-repetition": r2.cmd_r2_repetition, "r2-embed-age": r2.cmd_r2_embed_age,
              "r2-fingerprint": r2.cmd_r2_fingerprint, "r2-instrument": r2.cmd_r2_instrument, "r2-nh": r2.cmd_r2_nh,
              "gx12": r2b.cmd_gx12_crossparadigm, "gx13": r2b.cmd_gx13_scaling, "gx14": r2b.cmd_gx14_personal,
              "r3-artefact": r3.cmd_r3_artefact, "r3-peaks": r3.cmd_r3_peaks, "r3-memory": r3.cmd_r3_memory, "r3-pitch": r3.cmd_r3_pitch,
              "r3-records": r3.cmd_r3_records, "r3-agematrix": r3.cmd_r3_agematrix, "r3-nh-classify": r3.cmd_r3_nh_classify,
              "r4-experience": r4.cmd_r4_experience, "r4-pitch-attr": r4.cmd_r4_pitch_attr, "r4-ci-memory": r4.cmd_r4_ci_memory, "r4-trait": r4.cmd_r4_trait,
              "r4-inverted": r4.cmd_r4_inverted, "r4-literals": r4.cmd_r4_literals, "r4-direction": r4.cmd_r4_direction, "r4-hf-topo": r4.cmd_r4_hf_topo,
              "r5-curves": r5.cmd_r5_curves, "r5-wlate": r5.cmd_r5_wlate, "r5-templates": r5.cmd_r5_templates, "r5-align": r5.cmd_r5_align,
              "r5-memory": r5.cmd_r5_memory, "r5-hf": r5.cmd_r5_hf, "r5-joint": r5.cmd_r5_joint}[args.command](args, config)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
