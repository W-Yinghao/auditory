"""R0 diagnostic runner. Slurm only. Aggregates to results/, restricted values to private/."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np

from auditory_fn1.runtime import write_json
from auditory_fn1a.runtime import ROOT, load_config, require_config_value
from auditory_fn1a.signal_export import AMPLITUDE_COLUMN, TECHNICAL_COLUMNS

from . import probe

FN1A_PRIVATE = ROOT / "private/auditory_fn1a"
FN1A_RESULTS = ROOT / "results/auditory_fn1a"
K1_PRIVATE = ROOT / "private/auditory_k1"
PRIVATE_OUT = ROOT / "private/auditory_r0"
RESULTS_OUT = ROOT / "results/auditory_r0"

CLINICAL_COLUMNS = ["age_recorded_months", "HA_duration_months",
                    "better_unaided_pta_corrected", "better_aided_pta_corrected"]


def _load(support_run: str = "FN1A_support_001") -> dict:
    support = json.loads((FN1A_PRIVATE / support_run / "support.json").read_text())
    lock = json.loads((FN1A_PRIVATE / support["freeze_run"] / "archive_analysis_lock.json").read_text())
    with (FN1A_PRIVATE / lock["bound_runs"]["prepare"] / "archive_rows.csv").open(newline="", encoding="utf-8") as h:
        rows = {r["index_record_id"]: r for r in csv.DictReader(h)}
    with (FN1A_RESULTS / support["segments_run"] / "segment_support_summary.csv").open(newline="", encoding="utf-8") as h:
        technical = {r["index_record_id"]: r for r in csv.DictReader(h)}
    packages = FN1A_PRIVATE / support["segments_run"] / "packages"

    usable = support["usable"]
    index_of = {u["split_group_id"]: i for i, u in enumerate(usable)}
    folds = []
    for fold in support["splits"]["folds"]:
        inner = [{"inner_fold": i["inner_fold"],
                  "train_idx": np.array([index_of[g] for g in i["train"] if g in index_of], dtype=int),
                  "validation_idx": np.array([index_of[g] for g in i["validation"] if g in index_of], dtype=int)}
                 for i in fold["inner"]]
        folds.append({"outer_fold": fold["outer_fold"],
                      "train_idx": np.array([index_of[g] for g in fold["train"] if g in index_of], dtype=int),
                      "test_idx": np.array([index_of[g] for g in fold["test"] if g in index_of], dtype=int),
                      "inner": inner})

    def numeric(value):
        return float(value) if str(value) not in ("", "None", "nan") else np.nan

    clinical, technical_rows, segments, starts = [], [], [], []
    target_a, target_v, v_available, identities = [], [], [], []
    for entry in usable:
        row, tech = rows[entry["index_record_id"]], technical[entry["index_record_id"]]
        clinical.append([numeric(row[c]) for c in CLINICAL_COLUMNS])
        technical_rows.append([float(tech[f"Q_{c}"]) for c in TECHNICAL_COLUMNS])
        with np.load(packages / f"{entry['index_record_id']}.npz", allow_pickle=False) as package:
            segments.append(package["features"])
            starts.append(package["window_start_original"])
        target_a.append(numeric(row["A_raw_value"]))
        target_v.append(numeric(row["MUSS_raw_value"]))
        v_available.append(str(entry["target_V_given_A_available"]) == "True")
        identities.append(entry["split_group_id"])
    return {"folds": folds, "identities": np.asarray(identities),
            "clinical": np.asarray(clinical, float), "technical": np.asarray(technical_rows, float),
            "segments": np.asarray(segments, float), "starts": np.asarray(starts),
            "A": np.asarray(target_a, float), "V": np.asarray(target_v, float),
            "V_available": np.asarray(v_available, bool)}


def _target_structure(values: np.ndarray, ceiling: float) -> dict:
    observed = values[np.isfinite(values)]
    at_ceiling = bool_mask = np.isclose(observed, ceiling)
    return {"quantiles": probe.quantiles(observed),
            "granularity": probe.granularity(observed),
            "n_at_ceiling": int(at_ceiling.sum()),
            "fraction_at_ceiling": float(at_ceiling.mean()),
            "n_at_floor": int(np.isclose(observed, 0.0).sum())}


def _decompose(pred: np.ndarray, target: np.ndarray, ceiling: float) -> dict:
    at = np.isclose(target, ceiling)
    absolute = np.abs(pred - target)
    out = {}
    for label, mask in (("at_ceiling", at), ("below_ceiling", ~at)):
        if mask.sum() == 0:
            out[label] = {"n": 0}
            continue
        out[label] = {"n": int(mask.sum()), "MAE": float(absolute[mask].mean()),
                      "share_of_total_absolute_error": float(absolute[mask].sum() / absolute.sum())}
    return out


def run(args) -> dict:
    os.umask(0o077)
    data = _load()
    folds = data["folds"]
    config = load_config("configs/auditory_fn1a.yaml")
    ceiling = float(require_config_value(config, "archive.target_bounds_source_units")[1])
    features = probe.summarise_windows(data["segments"])
    report: dict = {"n_records": int(data["A"].size), "n_outer_folds": len(folds),
                    "feature_dimension": int(features.shape[1]),
                    "penalty_grid": [float(p) for p in probe.PENALTIES]}

    # --- R0-1 naive baselines and R0-2 error decomposition -------------------
    baselines, naive_table, decomposition = {}, [], []
    for name, values, mask in (("A_archive", data["A"], np.isfinite(data["A"])),
                               ("V_archive_given_A", data["V"], data["V_available"])):
        naive = probe.naive_oof(values, folds, mask)
        baselines[name] = naive["mean"]
        for label, prediction in naive.items():
            row = probe.errors(prediction[mask], values[mask])
            row.update({"target": name, "predictor": f"naive_{label}", "skill_vs_naive_mean":
                        probe.skill(prediction[mask], naive["mean"][mask], values[mask])})
            naive_table.append(row)
        report.setdefault("target_structure", {})[name] = _target_structure(values[mask], ceiling)

    saved = {}
    for name, run_dir in (("A_archive", "K1_fit_A_001"), ("V_archive_given_A", "K1_fit_V_001")):
        with np.load(K1_PRIVATE / run_dir / "predictions.npz", allow_pickle=False) as store:
            saved[name] = {key: store[key] for key in store.files if key not in ("groups",)}
    for name in saved:
        values = saved[name]["target"]
        baseline = baselines[name]
        mask = data["V_available"] if name == "V_archive_given_A" else np.isfinite(data["A"])
        assert np.allclose(values, (data["V"] if name == "V_archive_given_A" else data["A"])[mask]), name
        base = baseline[mask]
        for model, prediction in saved[name].items():
            if model == "target":
                continue
            row = probe.errors(prediction, values)
            row.update({"target": name, "predictor": model,
                        "skill_vs_naive_mean": probe.skill(prediction, base, values)})
            naive_table.append(row)
            entry = {"target": name, "model": model}
            entry.update({f"{k}_{m}": v for k, part in _decompose(prediction, values, ceiling).items()
                          for m, v in part.items()})
            decomposition.append(entry)

    # --- R0-3 / R0-4 EEG positive and negative controls ----------------------
    controls, penalties_used = [], []
    rng = np.random.default_rng(20260919)
    probe_targets = {"age_recorded_months": data["clinical"][:, 0],
                     "better_unaided_pta_corrected": data["clinical"][:, 2],
                     "better_aided_pta_corrected": data["clinical"][:, 3]}
    permuted = probe_targets["age_recorded_months"].copy()
    permuted = permuted[rng.permutation(permuted.size)]
    probe_targets["age_recorded_months_PERMUTED_negative_control"] = permuted
    for name, values in probe_targets.items():
        keep = np.isfinite(values)
        if keep.sum() < 20:
            controls.append({"probe_target": name, "status": "INSUFFICIENT_OBSERVED", "n": int(keep.sum())})
            continue
        filled = np.where(keep, values, 0.0)
        prediction, chosen = probe.ridge_oof(features, filled, folds, keep)
        naive = probe.naive_oof(filled, folds, keep)["mean"]
        evaluated = keep & np.isfinite(prediction)
        row = probe.errors(prediction[evaluated], values[evaluated])
        row.update({"probe_target": name, "status": "EVALUATED",
                    "skill_vs_naive_mean": probe.skill(prediction[evaluated], naive[evaluated], values[evaluated]),
                    "target_sd": float(values[keep].std(ddof=1))})
        controls.append(row)
        penalties_used.extend({"probe_target": name, **c} for c in chosen)

    # --- R0-5 split-half reliability of the 140 features ---------------------
    reliability = probe.split_half_reliability(data["segments"])
    finite = reliability[np.isfinite(reliability)]
    report["feature_split_half_reliability"] = {
        "n_features": int(reliability.size), "n_evaluated": int(finite.size),
        "quantiles": probe.quantiles(finite),
        "n_above_0_5": int((finite > 0.5).sum()), "n_above_0_8": int((finite > 0.8).sum()),
        "n_below_0_2": int((finite < 0.2).sum())}

    # --- R0-6 real window spacing -------------------------------------------
    gaps = np.diff(data["starts"].astype(np.int64), axis=1).ravel()
    report["window_spacing_original_samples"] = probe.quantiles(gaps)
    report["window_spacing_contiguous_fraction"] = float(np.mean(gaps == np.min(gaps)))

    RESULTS_OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE_OUT.mkdir(parents=True, exist_ok=True)
    run_root = RESULTS_OUT / args.run
    run_root.mkdir(parents=False, exist_ok=False)

    def table(path: Path, rows: list[dict]) -> None:
        columns: list[str] = []
        for row in rows:
            for key in row:
                if key not in columns:
                    columns.append(key)
        with path.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        path.chmod(0o644)

    table(run_root / "model_vs_naive_baseline.csv", naive_table)
    table(run_root / "ceiling_error_decomposition.csv", decomposition)
    table(run_root / "eeg_representation_controls.csv", controls)
    table(run_root / "control_penalties.csv", penalties_used)
    np.save(PRIVATE_OUT / "feature_split_half_correlations.npy", reliability)
    (PRIVATE_OUT / "feature_split_half_correlations.npy").chmod(0o600)
    report["status"] = "R0_DIAGNOSTIC_COMPLETE"
    report["job_id"] = os.environ.get("SLURM_JOB_ID")
    report["prereg_sha256"] = "042837567847652091273214dcf2c21a20a948e32d847e17e97c8d4423e4b5a3"
    write_json(run_root / "summary.json", report, private=False)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="auditory_r0")
    parser.add_argument("command", choices=["diagnose"])
    parser.add_argument("--run", required=True)
    args = parser.parse_args(argv)
    assert os.environ.get("SLURM_JOB_ID"), "Slurm only"
    report = run(args)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
