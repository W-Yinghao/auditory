"""The channel-budget information curve: how many bits about age survive B electrodes."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch

from . import channels as channel_tools
from . import train as train_tools
from .data import GpuWindowBank, RecordStore, record_scale
from .model import ChannelBudgetNet, parameter_count


def identity_folds(identities: np.ndarray, n_folds: int, seed: int) -> list[dict]:
    """Grouped K-fold: every recording of one child lands in exactly one fold."""
    unique = np.array(sorted(set(identities.tolist())))
    order = np.random.default_rng(seed).permutation(unique.size)
    assignment = {unique[order[i]]: i % n_folds for i in range(unique.size)}
    fold_of = np.array([assignment[g] for g in identities], dtype=int)
    return [{"fold": f,
             "train": np.nonzero(fold_of != f)[0],
             "test": np.nonzero(fold_of == f)[0]} for f in range(n_folds)]


def run_budget(args, root: Path, private: Path, results: Path) -> dict:
    started = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cohort = json.loads((private / f"{args.run}_cohort.json").read_text())
    layouts = json.loads((private / f"{args.run}_geometry.json").read_text())

    # One layout only: mixing electrode arrays would confound the budget with the net.
    counts: dict[str, int] = {}
    for unit in cohort["units"]:
        counts[str(unit["layout_hash"])] = counts.get(str(unit["layout_hash"]), 0) + 1
    layout_hash = max(counts, key=counts.get)
    layout = layouts[layout_hash]
    units = [u for u in cohort["units"] if str(u["layout_hash"]) == layout_hash]
    positions = np.asarray([p for p in layout["xyz_m"]], dtype=object)
    have = np.array([p is not None for p in positions])
    if not have.all():
        keep = np.nonzero(have)[0]
    else:
        keep = np.arange(len(layout["channels"]))
    geometry = np.asarray([layout["xyz_m"][i] for i in keep], dtype=float)

    stores, scales, kept_units = [], [], []
    for unit in units:
        store = RecordStore(root, args.run, unit["container_id"], preload=True,
                            max_bad_fraction=args.max_bad_fraction)
        if store.starts.size < args.min_windows:
            continue
        stores.append(store)
        scales.append(record_scale(store))
        kept_units.append(unit)
    if len(kept_units) < 20:
        return {"status": "D2_INSUFFICIENT_RECORDS", "records": len(kept_units)}

    ages = np.array([u["age_months"] for u in kept_units], dtype=float)
    identities = np.array([u["identity"] for u in kept_units])
    bank = GpuWindowBank(stores, np.asarray(scales, dtype=np.float32), device,
                         normalisation="record_robust")
    keep_device = torch.as_tensor(keep, dtype=torch.long, device=device)
    folds = identity_folds(identities, args.folds, args.seed)
    budgets = [int(b) for b in str(args.budgets).split(",") if b]
    rng = np.random.default_rng(args.seed)

    rows = []
    for budget in budgets:
        subsets = channel_tools.subset_variants(geometry, min(budget, geometry.shape[0]),
                                                args.variants, seed=args.seed)
        for variant, subset in enumerate(subsets):
            picked = keep_device[torch.as_tensor(subset, dtype=torch.long, device=device)]
            spread = channel_tools.coverage(geometry, subset)
            for fold in folds:
                train_records, test_records = fold["train"], fold["test"]
                edges = train_tools.quantile_bins(ages[train_records], args.bins)
                n_classes = edges.size + 1
                labels = train_tools.assign_bins(ages, edges)
                fit_labels = labels.copy()
                if args.shuffle_control:
                    permuted = rng.permutation(train_records)
                    fit_labels[train_records] = labels[permuted]
                marginal = train_tools.marginal_log_probabilities(
                    fit_labels[train_records], n_classes)
                centres = np.array([ages[labels == k].mean() if (labels == k).any()
                                    else float(np.median(ages)) for k in range(n_classes)])
                # Hold out whole children from the training fold for checkpoint choice.
                inner_rng = np.random.default_rng(args.seed + 31 * fold["fold"])
                train_ids = np.array(sorted(set(identities[train_records].tolist())))
                held = set(inner_rng.choice(
                    train_ids, size=max(2, int(round(0.2 * train_ids.size))), replace=False))
                validation_records = np.array([r for r in train_records
                                               if identities[r] in held], dtype=int)
                fit_records = np.array([r for r in train_records
                                        if identities[r] not in held], dtype=int)
                train_rows = bank.rows_for(fit_records)
                validation_rows = bank.rows_for(validation_records)
                label_tensor = torch.as_tensor(fit_labels, dtype=torch.long, device=device)
                model = ChannelBudgetNet(int(subset.size), n_classes, width=args.width,
                                         blocks=args.blocks, dropout=args.dropout)
                fitted = train_tools.train_one(
                    model, bank, picked, label_tensor, train_rows, device=device,
                    steps=args.steps, batch_size=args.batch_size,
                    learning_rate=args.learning_rate, weight_decay=args.weight_decay,
                    seed=args.seed + 1000 * budget + 97 * variant + fold["fold"],
                    validation_rows=validation_rows)
                if fitted["status"] != "D2_TRAINED":
                    rows.append({"budget": budget, "variant": variant, "fold": fold["fold"],
                                 "status": fitted["status"]})
                    continue
                evaluation = train_tools.evaluate(model, bank, picked, test_records,
                                                  device=device, batch_size=args.batch_size,
                                                  stride=args.eval_stride)
                if evaluation["status"] != "D2_EVALUATED":
                    rows.append({"budget": budget, "variant": variant, "fold": fold["fold"],
                                 "status": evaluation["status"]})
                    continue
                measures = train_tools.readout(evaluation, labels, marginal, centres)
                rows.append({"budget": budget, "variant": variant, "fold": fold["fold"],
                             "status": "OK", "n_electrodes": int(subset.size),
                             "parameters": parameter_count(model),
                             "coverage_max_distance_m": spread["max_distance_m"],
                             "final_train_loss_bits": fitted["final_loss_bits"],
                             "best_validation_bits": fitted.get("best_validation_bits"),
                             "best_step": fitted.get("best_step"),
                             "n_fit_records": int(fit_records.size),
                             "n_validation_records": int(validation_records.size), **measures})
                del model
                if device == "cuda":
                    torch.cuda.empty_cache()

    summary = aggregate(rows, budgets)
    payload = {
        "run": args.run, "out": args.out, "status": "D2_BUDGET_COMPLETE",
        "job_id": __import__("os").environ.get("SLURM_JOB_ID"), "device": device,
        "shuffle_control": bool(args.shuffle_control),
        "layout_hash": layout_hash, "sensor_net": layout["sensor_net"],
        "n_records": len(kept_units), "n_identities": int(len(set(identities.tolist()))),
        "n_windows": len(bank), "electrodes_available": int(geometry.shape[0]),
        "bins": args.bins, "folds": args.folds, "variants": args.variants,
        "max_bad_fraction": args.max_bad_fraction, "min_windows": args.min_windows,
        "steps": args.steps, "batch_size": args.batch_size,
        "window_seconds": stores[0].window / stores[0].rate,
        "total_usable_hours": round(sum(s.starts.size for s in stores)
                                    * (stores[0].window / stores[0].rate) / 3600.0, 2),
        "elapsed_minutes": round((time.time() - started) / 60.0, 1),
        "curve": summary,
    }
    name = args.out or f"{args.run}_budget"
    (results).mkdir(parents=True, exist_ok=True)
    (results / f"{name}_curve.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (results / f"{name}_curve.json").chmod(0o644)
    (private / f"{name}_rows.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    (private / f"{name}_rows.json").chmod(0o600)
    return payload


def aggregate(rows: list[dict], budgets: list[int]) -> list[dict]:
    out = []
    for budget in budgets:
        good = [r for r in rows if r["budget"] == budget and r.get("status") == "OK"]
        if not good:
            out.append({"budget": budget, "n_runs": 0,
                        "failures": sum(1 for r in rows if r["budget"] == budget)})
            continue
        def stat(key):
            values = np.array([r[key] for r in good], dtype=float)
            return {"mean": float(values.mean()), "sd": float(values.std(ddof=1)) if values.size > 1
                    else 0.0, "min": float(values.min()), "max": float(values.max())}
        out.append({"budget": budget, "n_runs": len(good),
                    "n_electrodes": int(good[0]["n_electrodes"]),
                    "record_bits_recovered": stat("record_bits_recovered"),
                    "window_bits_recovered": stat("window_bits_recovered"),
                    "record_expected_value_MAE": stat("record_expected_value_MAE"),
                    "record_top1_accuracy": stat("record_top1_accuracy"),
                    "record_marginal_bits": stat("record_marginal_bits")})
    return out
