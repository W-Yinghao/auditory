"""Matched-cohort, outcome-blind HA trial-budget reliability audit.

The existing preparation summary reports a different candidate set at each
trial budget.  This audit first requires every record to support every frozen
budget and both frozen split layouts, then computes all reliability summaries
on that one intersection.  It consumes only record/epoch metadata and the
outcome-blind feature-bank implementation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

from auditory_repair.extended import ROOT, bank_features


COHORT = ROOT / "private/auditory_repair/ha_prepare_001/cohort.csv"
EPOCHS = ROOT / "results/phase1_epochs_001"
BUDGETS = (32, 64, 128, 256)
SPLITS = ("odd_even", "early_late")
BANKS = ("HJORTH", "POST", "CONTRAST", "PRE", "SPATIAL")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_cohort() -> list[dict[str, str]]:
    with COHORT.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 57:
        raise AssertionError(f"expected 57 prepared HA records, got {len(rows)}")
    required = {"recording", "group"}
    if not required.issubset(rows[0]):
        raise AssertionError(f"cohort is missing required record columns: {required - set(rows[0])}")
    if len({row["recording"] for row in rows}) != len(rows):
        raise AssertionError("cohort recordings are not unique")
    return rows


def _uniform_indices(n: int, budget: int) -> np.ndarray | None:
    if n < budget:
        return None
    indices = np.rint(np.linspace(0, n - 1, budget)).astype(np.int64)
    if len(np.unique(indices)) != budget:
        raise AssertionError("uniform budget sampling produced duplicate indices")
    return indices


def _split(indices: np.ndarray, split: str) -> tuple[np.ndarray, np.ndarray]:
    if split == "odd_even":
        # Preserve chronological order while alternating the selected trials.
        return indices[::2], indices[1::2]
    if split == "early_late":
        midpoint = len(indices) // 2
        return indices[:midpoint], indices[midpoint:]
    raise ValueError(split)


def _codes_supported(codes: np.ndarray, halves: tuple[np.ndarray, np.ndarray]) -> bool:
    return all(all(int(np.sum(codes[half] == code)) >= 1 for code in (1, 2)) for half in halves)


def _pearson_by_feature(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Cross-identity Pearson correlation for each feature, preserving missingness."""
    if left.ndim != 2 or right.shape != left.shape:
        raise ValueError("paired feature arrays must have the same two-dimensional shape")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("nonfinite feature pair")
    x = left - left.mean(axis=0, keepdims=True)
    y = right - right.mean(axis=0, keepdims=True)
    denom = np.sqrt(np.sum(x * x, axis=0) * np.sum(y * y, axis=0))
    result = np.full(left.shape[1], np.nan, dtype=np.float64)
    valid = denom > 1e-12
    result[valid] = np.sum(x[:, valid] * y[:, valid], axis=0) / denom[valid]
    return result


def _summary(values: np.ndarray, n_candidates: int, bank: str, budget: int, split: str) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    valid = values[np.isfinite(values)]
    if len(valid) == 0:
        return {
            "bank": bank, "budget": budget, "split": split,
            "n_common_candidates": n_candidates, "valid_features": 0,
            "median_correlation": None, "q25": None, "q75": None,
            "fraction_positive": None, "median_spearman_brown_heuristic": None,
            "status": "NO_NONCONSTANT_FEATURES",
        }
    sb = 2.0 * valid / (1.0 + valid)
    return {
        "bank": bank, "budget": budget, "split": split,
        "n_common_candidates": n_candidates, "valid_features": int(len(valid)),
        "median_correlation": float(np.median(valid)),
        "q25": float(np.quantile(valid, 0.25)),
        "q75": float(np.quantile(valid, 0.75)),
        "fraction_positive": float(np.mean(valid > 0.0)),
        "median_spearman_brown_heuristic": float(np.median(sb)),
        "status": "ESTIMATED" if n_candidates >= 3 else "DESCRIPTIVE_SUPPORT_ONLY",
    }


def run(private: Path, public: Path) -> dict[str, Any]:
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("matched reliability audit must run under Slurm")
    private = Path(private)
    public = Path(public)
    private.mkdir(parents=True, exist_ok=False, mode=0o700)
    public.mkdir(parents=True, exist_ok=False)
    os.chmod(private, 0o700)

    started = time.time()
    cohort = _read_cohort()
    support: list[dict[str, Any]] = []
    features: dict[tuple[str, int, str], dict[str, np.ndarray]] = {}
    source_hashes = {"cohort.csv": sha256(COHORT), "extended.py": sha256(ROOT / "auditory_repair/extended.py")}
    dimensions: dict[str, int] = {}

    for row in cohort:
        recording = row["recording"]
        epoch_path = EPOCHS / recording / "epochs.npz"
        if not epoch_path.exists():
            raise FileNotFoundError(epoch_path)
        source_hashes[f"epochs/{recording}/epochs.npz"] = sha256(epoch_path)
        with np.load(epoch_path, allow_pickle=False) as package:
            x_all = np.asarray(package["data_uv"], dtype=np.float64)
            t = np.asarray(package["times_s"], dtype=np.float64)
            accepted = np.asarray(package["accepted"])
            codes_all = np.asarray(package["codes"])
            samples = np.asarray(package["samples_0based"])
            event_ordinals = np.asarray(package["event_indices_1based"])
            if accepted.ndim != 2 or accepted.shape[0] != len(x_all) or accepted.shape[1] < 1:
                raise AssertionError(f"{recording}: accepted mask shape mismatch")
            primary = accepted[:, 0].astype(bool) & np.isin(codes_all, (1, 2))
            indices = np.flatnonzero(primary)
            order = np.lexsort((event_ordinals[indices], samples[indices]))
            chronological = indices[order]
            x = x_all[chronological]
            codes = codes_all[chronological]

        row_support: dict[str, Any] = {"group": row["group"], "recording": recording, "accepted_code1": int(np.sum(codes == 1)), "accepted_code2": int(np.sum(codes == 2))}
        for budget in BUDGETS:
            chosen = _uniform_indices(len(x), budget)
            for split in SPLITS:
                key = f"b{budget}_{split}"
                if chosen is None:
                    row_support[key] = False
                    continue
                halves = _split(chosen, split)
                ok = _codes_supported(codes, halves)
                row_support[key] = bool(ok)
                if ok:
                    for half_label, half in zip(("first", "second"), halves):
                        bank_key = (recording, budget, f"{split}_{half_label}")
                        bank_values = bank_features(x[half], t, codes[half])
                        features[bank_key] = {name: np.asarray(bank_values[name], dtype=np.float64) for name in BANKS}
                        dimensions.update({name: int(values.size) for name, values in bank_values.items()})
        support.append(row_support)

    required_keys = [f"b{budget}_{split}" for budget in BUDGETS for split in SPLITS]
    common = [row for row in support if all(bool(row[key]) for key in required_keys)]
    common_recordings = {row["recording"] for row in common}
    common_groups = {row["group"] for row in common}
    if len(common_recordings) != len(common_groups):
        raise AssertionError("common cohort contains duplicate identity groups")

    rows: list[dict[str, Any]] = []
    for budget in BUDGETS:
        for split in SPLITS:
            first = {name: [] for name in BANKS}
            second = {name: [] for name in BANKS}
            for recording in sorted(common_recordings):
                for name in BANKS:
                    first[name].append(features[(recording, budget, f"{split}_first")][name])
                    second[name].append(features[(recording, budget, f"{split}_second")][name])
            for name in BANKS:
                left = np.asarray(first[name], dtype=np.float64)
                right = np.asarray(second[name], dtype=np.float64)
                correlations = _pearson_by_feature(left, right)
                rows.append(_summary(correlations, len(common_recordings), name, budget, split))

    with (private / "support_by_record.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(support[0]))
        writer.writeheader()
        writer.writerows(support)
    with (private / "common_candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["group", "recording"])
        writer.writeheader()
        writer.writerows({"group": row["group"], "recording": row["recording"]} for row in common)
    with (private / "source_hashes.json").open("w", encoding="utf-8") as handle:
        json.dump(source_hashes, handle, indent=2)

    import pandas as pd
    frame = pd.DataFrame(rows)
    frame.to_csv(public / "reliability_matched.csv", index=False)
    support_counts = []
    for budget in BUDGETS:
        for split in SPLITS:
            key = f"b{budget}_{split}"
            support_counts.append({"budget": budget, "split": split, "available_candidates": int(sum(bool(row[key]) for row in support)), "common_candidates": len(common)})
    pd.DataFrame(support_counts).to_csv(public / "support_by_budget.csv", index=False)
    summary = {
        "status": "COMPLETED_MATCHED_COHORT",
        "input_records": len(cohort),
        "common_candidate_records": len(common),
        "common_identity_groups": len(common_groups),
        "budgets": list(BUDGETS),
        "splits": list(SPLITS),
        "banks": list(BANKS),
        "bank_dimensions": dimensions,
        "support_by_budget_split": support_counts,
        "correlation_rows": len(rows),
        "outcome_blind": True,
        "clinical_fields_read": False,
        "feature_selection": False,
        "early_late_is_separate_from_interleaved": True,
        "source_hashes": {"cohort.csv": source_hashes["cohort.csv"], "extended.py": source_hashes["extended.py"]},
        "elapsed_seconds": time.time() - started,
        "job_id": os.environ["SLURM_JOB_ID"],
    }
    (public / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--private", required=True)
    parser.add_argument("--public", required=True)
    args = parser.parse_args()
    print(json.dumps(run(Path(args.private), Path(args.public)), indent=2))
