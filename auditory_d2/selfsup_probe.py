"""Pretrain on unlabelled recordings, then probe age on the labelled children.

Leakage control: the pretraining pool excludes every acquisition that belongs to a
labelled child, so no window a probe is ever tested on has been seen during
pretraining, and no fold-wise re-pretraining is needed.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
import torch

from . import channels as channel_tools
from . import selfsup
from . import train as train_tools
from .budget import identity_folds
from .data import GpuWindowBank, RecordStore, record_scale
from .model import ChannelBudgetNet, parameter_count
from .ridge_budget import PENALTIES, _bin_probabilities, _ridge


def _layout(cohort, layouts):
    counts: dict[str, int] = {}
    for unit in cohort["units"]:
        counts[str(unit["layout_hash"])] = counts.get(str(unit["layout_hash"]), 0) + 1
    key = max(counts, key=counts.get)
    return key, layouts[key]


def _pretraining_pool(root: Path, run: str, labelled_containers: set[str],
                      layout_hash: str, limit: int) -> list[str]:
    plan = json.loads((root / "private/auditory_d1" / f"{run}_plan.json").read_text())
    acquisition = {row["container_id"]: row["candidate_acquisition_id"] for row in plan}
    blocked = {acquisition[c] for c in labelled_containers if c in acquisition}
    directory = root / "private/auditory_d1" / run / "receipts"
    pool = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text())
        if payload.get("status") != "D1_EXPORTED":
            continue
        container = payload["container_id"]
        if container in labelled_containers:
            continue
        if acquisition.get(container) in blocked:
            continue
        if str(payload.get("layout_hash")) != layout_hash:
            continue
        pool.append(container)
    return pool[:limit]


def run_selfsup_probe(args, root: Path, private: Path, results: Path) -> dict:
    started = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cohort = json.loads((private / f"{args.run}_cohort.json").read_text())
    layouts = json.loads((private / f"{args.run}_geometry.json").read_text())
    layout_hash, layout = _layout(cohort, layouts)
    units = [u for u in cohort["units"] if str(u["layout_hash"]) == layout_hash]
    keep = np.array([i for i, p in enumerate(layout["xyz_m"]) if p is not None], dtype=int)
    geometry = np.asarray([layout["xyz_m"][i] for i in keep], dtype=float)

    labelled_stores, labelled_scales, kept = [], [], []
    for unit in units:
        store = RecordStore(root, args.run, unit["container_id"],
                            max_bad_fraction=args.max_bad_fraction, preload=True)
        if store.starts.size < args.min_windows:
            continue
        labelled_stores.append(store)
        labelled_scales.append(record_scale(store))
        kept.append(unit)
    ages = np.array([u["age_months"] for u in kept], dtype=float)
    identities = np.array([u["identity"] for u in kept])

    pool = _pretraining_pool(root, args.run, {u["container_id"] for u in units},
                             layout_hash, args.pool_limit)
    pool_stores, pool_scales = [], []
    for container in pool:
        store = RecordStore(root, args.run, container,
                            max_bad_fraction=args.max_bad_fraction, preload=True)
        if store.starts.size < args.min_windows:
            continue
        pool_stores.append(store)
        pool_scales.append(record_scale(store))
    if len(pool_stores) < 20:
        return {"status": "D2_INSUFFICIENT_PRETRAINING_POOL", "pool": len(pool_stores)}

    pool_bank = GpuWindowBank(pool_stores, np.asarray(pool_scales, dtype=np.float32), device,
                              store_dtype="float16")
    labelled_bank = GpuWindowBank(labelled_stores, np.asarray(labelled_scales, dtype=np.float32),
                                  device, store_dtype="float16")
    all_rows = torch.arange(len(pool_bank), device=device)
    held = torch.as_tensor(np.arange(len(pool_stores))[::7].copy(), device=device)
    validation_mask = torch.isin(pool_bank.record, held)
    fit_rows = all_rows[~validation_mask]
    validation_rows = all_rows[validation_mask]

    budgets = [int(b) for b in str(args.budgets).split(",") if b]
    folds = identity_folds(identities, args.folds, args.seed)
    rows, curve = [], []
    for budget in budgets:
        subsets = channel_tools.subset_variants(geometry, min(budget, geometry.shape[0]),
                                                args.variants, seed=args.seed)
        for variant, subset in enumerate(subsets):
            picked = torch.as_tensor(keep[subset], dtype=torch.long, device=device)
            encoder = ChannelBudgetNet(int(subset.size), 1, width=args.width,
                                       blocks=args.blocks, dropout=args.dropout)
            model = selfsup.RelativePositioning(encoder, encoder.embedding_dim)
            fitted = selfsup.pretrain(
                model, pool_bank, picked,
                selfsup.PairSampler(pool_bank, fit_rows, near_seconds=args.near_seconds,
                                    far_seconds=args.far_seconds, seed=args.seed + budget),
                device=device, steps=args.ssl_steps, batch_size=args.batch_size,
                learning_rate=args.learning_rate, weight_decay=args.weight_decay,
                seed=args.seed + 7 * budget + variant,
                validation=selfsup.PairSampler(pool_bank, validation_rows,
                                               near_seconds=args.near_seconds,
                                               far_seconds=args.far_seconds,
                                               seed=args.seed + 13))
            if fitted["status"] != "D2_SSL_TRAINED":
                rows.append({"budget": budget, "variant": variant, "status": fitted["status"]})
                continue
            design, present = selfsup.embed_records(
                encoder, labelled_bank, picked, np.arange(len(kept)), device=device,
                batch_size=args.batch_size, stride=args.eval_stride)
            order = np.argsort(present)
            design, present = design[order], present[order]
            target = ages[present]
            groups = identities[present]
            local = identity_folds(groups, args.folds, args.seed)
            predicted = np.full(target.shape, np.nan)
            for fold in local:
                train_idx, test_idx = fold["train"], fold["test"]
                inner = identity_folds(groups[train_idx],
                                       min(3, max(2, len(train_idx) // 8)), args.seed + 7)
                scored = {}
                for penalty in PENALTIES:
                    errors = []
                    for part in inner:
                        a, b = train_idx[part["train"]], train_idx[part["test"]]
                        if b.size == 0:
                            continue
                        errors.append(_ridge(design[a], target[a], design[b], penalty) - target[b])
                    if errors:
                        scored[penalty] = float(np.mean(np.concatenate(errors) ** 2))
                penalty = min(scored, key=scored.get)
                residual = float(np.sqrt(scored[penalty]))
                predicted[test_idx] = _ridge(design[train_idx], target[train_idx],
                                             design[test_idx], penalty)
                edges = train_tools.quantile_bins(target[train_idx], args.bins)
                n_classes = edges.size + 1
                labels = train_tools.assign_bins(target, edges)
                marginal = train_tools.marginal_log_probabilities(labels[train_idx], n_classes)
                log_probabilities = _bin_probabilities(predicted[test_idx], residual,
                                                       edges, n_classes)
                truth = labels[test_idx]
                rows.append({"budget": budget, "variant": variant, "fold": fold["fold"],
                             "status": "OK", "n_electrodes": int(subset.size),
                             "embedding_dim": int(design.shape[1]),
                             "parameters": parameter_count(encoder),
                             "ssl_best_validation_bits": fitted["best_validation_bits"],
                             "ssl_best_step": fitted["best_step"],
                             "record_bits_recovered": train_tools.cross_entropy_bits(
                                 np.repeat(marginal[None, :], truth.size, axis=0), truth)
                             - train_tools.cross_entropy_bits(log_probabilities, truth),
                             "record_MAE": float(np.abs(predicted[test_idx]
                                                        - target[test_idx]).mean())})
            del encoder, model
            if device == "cuda":
                torch.cuda.empty_cache()

    for budget in budgets:
        good = [r for r in rows if r["budget"] == budget and r.get("status") == "OK"]
        if not good:
            curve.append({"budget": budget, "n_runs": 0})
            continue
        def stat(key):
            values = np.array([r[key] for r in good], dtype=float)
            return {"mean": float(values.mean()),
                    "sd": float(values.std(ddof=1)) if values.size > 1 else 0.0}
        curve.append({"budget": budget, "n_runs": len(good),
                      "n_electrodes": int(good[0]["n_electrodes"]),
                      "embedding_dim": int(good[0]["embedding_dim"]),
                      "record_MAE": stat("record_MAE"),
                      "record_bits_recovered": stat("record_bits_recovered"),
                      "ssl_best_validation_bits": stat("ssl_best_validation_bits")})

    payload = {"run": args.run, "arm": "selfsup", "status": "D2_SELFSUP_PROBE_COMPLETE",
               "job_id": os.environ.get("SLURM_JOB_ID"), "device": device,
               "pretraining_recordings": len(pool_stores),
               "pretraining_windows": len(pool_bank),
               "pretraining_hours": round(len(pool_bank) * pool_bank.window
                                          / pool_bank.rate / 3600.0, 2),
               "labelled_records": len(kept), "n_identities": int(len(set(identities.tolist()))),
               "near_seconds": args.near_seconds, "far_seconds": args.far_seconds,
               "ssl_steps": args.ssl_steps, "bins": args.bins, "folds": args.folds,
               "variants": args.variants, "width": args.width, "blocks": args.blocks,
               "naive_mean_MAE": float(np.abs(ages - ages.mean()).mean()),
               "elapsed_minutes": round((time.time() - started) / 60.0, 1), "curve": curve}
    name = args.out or f"{args.run}_selfsup"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{name}_curve.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}_curve.json").chmod(0o644)
    (private / f"{name}_rows.json").write_text(json.dumps(rows, indent=2) + "\n")
    (private / f"{name}_rows.json").chmod(0o600)
    return payload
