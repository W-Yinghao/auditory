"""Historical auditory5 route-D replay after the corrected PTA linkage.

The 51-group D cohort, outer/inner folds, and cached representation
projections are immutable inputs.  Only the clinical covariate table changes.
All participant-level predictions and tuning records stay private.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import pickle
import traceback
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from auditory5.provenance import require_slurm
import auditory5.routes.route_d as route_d
from auditory5.statistics import paired_cluster_bootstrap


ROOT = Path(__file__).resolve().parents[1]
RUN = "legacy_d_002"
PRIVATE = ROOT / "private" / "auditory_repair" / f"legacy_d_{RUN.split('_')[-1]}"
PUBLIC = ROOT / "results" / "auditory_repair" / f"legacy_d_{RUN.split('_')[-1]}"
BASE = ROOT / "private" / "auditory5_v1"
SPLIT_DIR = BASE / "splits" / "splits_001"
CLINICAL_OLD = BASE / "data" / "manifest_001" / "clinical_index.parquet"
CORRECTED = ROOT / "private" / "auditory_repair" / "pta_007" / "candidate_covariates.csv"
MODES = ("L0", "R_SUP", "R_SIM")
MODE_MODELS = ("D0_mean", "D1_C", "D2_CV", "D3_CVN", "D4_CN", "D5_CFULL", "D7_CPRE", *tuple(f"D6_CRANDOM_{k}" for k in range(20)))
EEG_FEATURES = ("V", "N", "FULL", "PRE", *tuple(f"RANDOM_{k}" for k in range(20)))
MODE_DIR = {"L0": "D_L0_core_001", "R_SUP": "D_SUP_core_001", "R_SIM": "D_SIM_core_001"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def model_list():
    return list(MODE_MODELS)


def _as_float(values):
    return pd.to_numeric(values, errors="coerce").astype(float)


def _column(frame, names, required=True):
    for name in names:
        if name in frame.columns:
            return name
    if required:
        raise KeyError(f"missing corrected PTA column alternatives: {names}")
    return None


def load_corrected_table(path: Path, old: pd.DataFrame, expected_ids):
    frame = pd.read_csv(path)
    group_col = _column(frame, ["split_group_id"], required=False)
    if group_col is None:
        candidate_col = _column(frame, ["candidate_id", "participant_id"], required=True)
        mapping = old.reset_index().set_index("candidate_id")["split_group_id"].to_dict()
        mapped = frame[candidate_col].map(mapping)
        frame = frame.loc[mapped.notna()].copy()
        frame["split_group_id"] = mapped.loc[mapped.notna()].astype(str).to_numpy()
        group_col = "split_group_id"
    else:
        valid = frame[group_col].notna()
        frame = frame.loc[valid].copy()
        frame[group_col] = frame[group_col].astype(str)
    target_col = _column(frame, ["MUSS_source_percentage", "MUSS", "muss"], required=True)
    age_col = _column(frame, ["age_months", "clinical_age_months"], required=True)
    duration_col = _column(frame, ["log1p_device_duration_months", "duration_months", "HA使用时长（月）"], required=True)
    pta_col = _column(frame, ["better_ear_4freq_source_units", "better_unaided_pta", "better_unaided_PTA", "better_ear_unaided_pta"], required=True)
    out = pd.DataFrame(index=frame[group_col].astype(str))
    out["target"] = _as_float(frame[target_col].to_numpy())
    out["age"] = _as_float(frame[age_col].to_numpy())
    duration = _as_float(frame[duration_col].to_numpy())
    if duration_col in {"duration_months", "HA使用时长（月）"}:
        out["log_duration"] = np.log1p(duration)
    else:
        out["log_duration"] = duration
    out["pta"] = _as_float(frame[pta_col].to_numpy())
    out = out[out.index.notna()]
    if not out.index.is_unique:
        raise ValueError("corrected PTA table has duplicate split groups")
    out.index = out.index.astype(str)
    if not set(expected_ids) <= set(out.index):
        raise ValueError("corrected PTA table does not cover unchanged old D cohort")
    out = out.loc[list(expected_ids)]
    if not np.isfinite(out[["target", "age", "log_duration"]]).all().all():
        raise ValueError("corrected target/age/duration contains missing or nonfinite values")
    return out, {"source_columns": {"target": target_col, "age": age_col, "duration": duration_col, "pta": pta_col}, "rows": len(frame), "covered_old_groups": len(out), "pta_missing": int(out.pta.isna().sum())}


def clinical_features(clinical: pd.DataFrame, train_ids, test_ids):
    train_ids, test_ids = list(train_ids), list(test_ids)
    pta_train = clinical.loc[train_ids, "pta"].to_numpy(float)
    observed = pta_train[np.isfinite(pta_train)]
    if len(observed) == 0:
        raise ValueError("corrected PTA is absent in a training fold")
    median = float(np.median(observed))
    def make(ids):
        pta = clinical.loc[ids, "pta"].to_numpy(float)
        missing = ~np.isfinite(pta)
        pta = np.where(missing, median, pta)
        x = np.column_stack([clinical.loc[ids, "age"].to_numpy(float), clinical.loc[ids, "log_duration"].to_numpy(float), pta, missing.astype(float)])
        if not np.isfinite(x).all():
            raise ValueError("clinical feature imputation produced nonfinite values")
        return x
    return make(train_ids), make(test_ids), {"pta_train_median": median, "pta_test_missing": int(clinical.loc[test_ids, "pta"].isna().sum())}


def _artifact(path: Path):
    with path.open("rb") as f:
        return pickle.load(f)


def _aligned(artifact, ids, names=EEG_FEATURES):
    order = {str(g): i for i, g in enumerate(artifact["ids"])}
    if set(map(str, ids)) - set(order):
        raise ValueError("projection artifact missing requested group")
    ix = [order[str(g)] for g in ids]
    return {name: np.asarray(artifact["features"][name], float)[ix] for name in names}


def _groups(train_x, test_x, clinical_train, clinical_test):
    train = {"C": clinical_train, **train_x}
    test = {"C": clinical_test, **test_x}
    return train, test


def _old_verify(mode, folds, old, output_rows):
    """Replay cached outer predictions using the original cached C columns."""
    route = BASE / "routes" / MODE_DIR[mode]
    old_oof = pd.read_parquet(route / "clinical_oof.parquet")
    expected_ids = set(old.index.astype(str))
    tuning = json.loads((route / "tuning.json").read_text())
    tune = {(int(r["outer_fold"]), r["model"]): r["penalties"] for r in tuning}
    rows = []
    for fold in folds:
        of = int(fold["outer_fold"])
        train, test = sorted(set(fold["train_groups"]) & expected_ids), sorted(set(fold["test_groups"]) & expected_ids)
        if set(train) & set(test) or len(train) + len(test) != len(expected_ids):
            raise ValueError("old fold does not partition exact 51-group cohort")
        artifact = _artifact(route / f"{mode}_outer{of}_projection.pkl")
        order = {str(g): i for i, g in enumerate(artifact["ids"])}
        tx, vx = _aligned(artifact, train), _aligned(artifact, test)
        old_train = old.loc[train, "MUSS_source_percentage"].to_numpy(float) if "MUSS_source_percentage" in old else old.loc[train, "target"].to_numpy(float)
        for model in MODE_MODELS:
            penalties = tune[(of, model)]
            pred = route_d.grouped_ridge_predict({"C": artifact["features"]["C"][[order[str(g)] for g in train]], **tx}, {"C": artifact["features"]["C"][[order[str(g)] for g in test]], **vx}, old_train, penalties)
            for group, value in zip(test, pred):
                expected_pred = old_oof[(old_oof.outer_fold == of) & old_oof.split_group_id.eq(group) & old_oof.model.eq(model)].prediction
                if len(expected_pred) != 1:
                    raise ValueError("old cached OOF row missing")
                target = old_oof[(old_oof.outer_fold == of) & old_oof.split_group_id.eq(group) & old_oof.model.eq(model)].target
                if len(target) != 1 or not np.isclose(float(target.iloc[0]), float(old.loc[group, "MUSS_source_percentage"])):
                    raise ValueError("old cached OOF target differs from old clinical table")
                rows.append(abs(float(value) - float(expected_pred.iloc[0])))
    return {"mode": mode, "rows_checked": len(rows), "max_abs_prediction_difference": float(max(rows) if rows else 0.0), "status": "PASS" if rows and max(rows) < 1e-9 else "FAIL"}


def _gain(a, b, ids):
    values = np.asarray(a, float) - np.asarray(b, float)
    ci = paired_cluster_bootstrap(np.asarray(a, float), np.asarray(b, float), np.asarray(ids, str), n_boot=2000, seed=20260917)
    loo = [float(np.delete(values, i).mean()) for i in range(len(values))] if len(values) > 1 else [float(values.mean())]
    return {"estimate": float(values.mean()), "ci_lower": float(ci["ci_lower"]), "ci_upper": float(ci["ci_upper"]), "n_candidates": len(values), "n_bootstrap": 2000, "leave_one_out_min": float(min(loo)), "leave_one_out_max": float(max(loo)), "gain_definition": "MAE(first)-MAE(second)"}


def _summarize(frame, mode):
    own = frame[frame["mode"].eq(mode)]
    errors = own.pivot(index="split_group_id", columns="model", values="absolute_error")
    if set(errors.columns) != set(MODE_MODELS) or errors.isna().any().any():
        raise ValueError("incomplete corrected D model matrix")
    ids = errors.index.to_numpy(str)
    gains = {"C_vs_CV": _gain(errors.D1_C, errors.D2_CV, ids), "CV_vs_CVN": _gain(errors.D2_CV, errors.D3_CVN, ids), "C_vs_CVN": _gain(errors.D1_C, errors.D3_CVN, ids), "C_vs_FULL": _gain(errors.D1_C, errors.D5_CFULL, ids), "C_vs_PRE": _gain(errors.D1_C, errors.D7_CPRE, ids)}
    gains["C_vs_random"] = {f"random_{k}": _gain(errors.D1_C, errors[f"D6_CRANDOM_{k}"], ids) for k in range(20)}
    return {"mode": mode, "n_candidates": len(errors), "MAE": {str(k): float(v) for k, v in errors.mean().items()}, "gains": gains, "ceiling_fraction": float((own.drop_duplicates("split_group_id").target == 100).mean())}


def main():
    require_slurm()
    os.umask(0o077)
    if PRIVATE.exists() or PUBLIC.exists():
        raise FileExistsError("refusing to overwrite legacy D replay outputs")
    PRIVATE.mkdir(parents=True, exist_ok=False, mode=0o700)
    PUBLIC.mkdir(parents=True, exist_ok=False, mode=0o700)
    # Hash and snapshot every source before importing/reading clinical values.
    sources = [Path(__file__), ROOT / "auditory5/routes/route_d.py", ROOT / "auditory5/probes.py", ROOT / "auditory5/statistics.py", ROOT / "configs/auditory5_v1.yaml", SPLIT_DIR / "folds.json", SPLIT_DIR / "support.parquet", CLINICAL_OLD, CORRECTED]
    for mode in MODES:
        route = BASE / "routes" / MODE_DIR[mode]
        sources.extend([route / f"{mode}_outer{of}_projection.pkl" for of in range(5)])
        sources.extend([route / f"{mode}_outer{of}_inner{inner}_projection.pkl" for of in range(5) for inner in range(3)])
        sources.extend([route / "tuning.json", route / "clinical_oof.parquet"])
    missing = [str(p) for p in sources if not p.exists()]
    receipt = {"job_id": os.environ["SLURM_JOB_ID"], "run": RUN, "status": "sources_hashed_before_analysis", "missing_sources": missing, "sources": {str(p): {"sha256": digest(p), "size_bytes": p.stat().st_size} for p in sources if p.exists()}}
    write_json(PRIVATE / "source_manifest.json", receipt)
    write_json(PUBLIC / "start_receipt.json", {"job_id": receipt["job_id"], "run": RUN, "status": receipt["status"], "source_manifest_private": True})
    if missing:
        raise FileNotFoundError("required replay sources unavailable; see private source manifest")
    old = pd.read_parquet(CLINICAL_OLD).set_index("split_group_id")
    split = json.loads((SPLIT_DIR / "folds.json").read_text())
    support = pd.read_parquet(SPLIT_DIR / "support.parquet")
    expected = set(support.loc[support.D, "split_group_id"].astype(str))
    if len(expected) != 51:
        raise ValueError("old D cohort is not exactly 51 groups")
    old_d = old.loc[sorted(expected)].copy()
    corrected, correction_meta = load_corrected_table(CORRECTED, old, expected)
    for col in ("MUSS_source_percentage", "age_months", "log1p_device_duration_months"):
        if not np.allclose(corrected["target" if col == "MUSS_source_percentage" else ("age" if col == "age_months" else "log_duration")], old.loc[corrected.index, col].to_numpy(float), equal_nan=False):
            raise ValueError(f"corrected table changed frozen clinical field {col}")
    fit_ledger = {"attempts": 0, "failures": 0, "limit": 100000}
    original_grouped = route_d.grouped_ridge_predict
    def counted_grouped(*args, **kwargs):
        fit_ledger["attempts"] += 1
        if fit_ledger["attempts"] > fit_ledger["limit"]:
            raise RuntimeError("D_FIT_ATTEMPT_LIMIT")
        try:
            return original_grouped(*args, **kwargs)
        except Exception:
            fit_ledger["failures"] += 1
            raise
    route_d.grouped_ridge_predict = counted_grouped
    # The old table has been independently reproduced only from cached projections.
    old_verification = [_old_verify(mode, split["folds"], old_d, []) for mode in MODES]
    if any(row["status"] != "PASS" for row in old_verification):
        raise ValueError("old cached prediction replay failed")
    write_json(PRIVATE / "old_replay_verification.json", old_verification)
    predictions, tuning, failures = [], [], []
    for mode in MODES:
        mode_predictions = []
        try:
            route = BASE / "routes" / MODE_DIR[mode]
            for fold in split["folds"]:
                of = int(fold["outer_fold"])
                train, test = sorted(set(fold["train_groups"]) & expected), sorted(set(fold["test_groups"]) & expected)
                inner = []
                for inner_fold in range(3):
                    valid = sorted(g for g in train if fold["D_inner_fold_by_group"][g] == inner_fold)
                    fit = sorted(set(train) - set(valid))
                    artifact = _artifact(route / f"{mode}_outer{of}_inner{inner_fold}_projection.pkl")
                    eeg = _aligned(artifact, fit + valid)
                    c_train, c_valid, impute = clinical_features(corrected, fit, valid)
                    inner.append({"train": {"C": c_train, **{k: v[:len(fit)] for k, v in eeg.items()}}, "test": {"C": c_valid, **{k: v[len(fit):] for k, v in eeg.items()}}, "y_train": corrected.loc[fit, "target"].to_numpy(float), "y_test": corrected.loc[valid, "target"].to_numpy(float)})
                    tuning.append({"mode": mode, "outer_fold": of, "inner_fold": inner_fold, "impute": impute})
                artifact = _artifact(route / f"{mode}_outer{of}_projection.pkl")
                eeg = _aligned(artifact, train + test)
                c_train, c_test, impute = clinical_features(corrected, train, test)
                train_features, test_features = _groups({k: v[:len(train)] for k, v in eeg.items()}, {k: v[len(train):] for k, v in eeg.items()}, c_train, c_test)
                for model in MODE_MODELS:
                    penalties, info = route_d.choose_penalties(inner, model)
                    pred = route_d.grouped_ridge_predict(train_features, test_features, corrected.loc[train, "target"].to_numpy(float), penalties)
                    tuning.append({"mode": mode, "outer_fold": of, "model": model, "penalties": penalties, **info, "impute": impute})
                    for group, target, value in zip(test, corrected.loc[test, "target"], pred):
                        mode_predictions.append({"mode": mode, "outer_fold": of, "split_group_id": group, "model": model, "target": float(target), "prediction": float(value), "absolute_error": float(abs(target - value))})
            predictions.extend(mode_predictions)
        except Exception as exc:
            failures.append({"mode": mode, "error_type": type(exc).__name__, "error": repr(exc), "traceback": traceback.format_exc()})
    frame = pd.DataFrame(predictions)
    frame.to_parquet(PRIVATE / "corrected_clinical_oof.parquet", index=False)
    pd.DataFrame(tuning).to_json(PRIVATE / "corrected_tuning.json", orient="records", indent=2)
    write_json(PRIVATE / "failures.json", failures)
    modes_summary = []
    for mode in MODES:
        if mode in set(frame["mode"]) if len(frame) else False:
            modes_summary.append(_summarize(frame, mode))
    write_json(PRIVATE / "fit_attempt_ledger.json", fit_ledger)
    public = {"job_id": os.environ["SLURM_JOB_ID"], "run": RUN, "status": "COMPLETE" if not failures and len(modes_summary) == len(MODES) else "PARTIAL_FAILURE", "old_D_cohort_groups": 51, "modes": modes_summary, "failed_modes": [x["mode"] for x in failures], "correction": correction_meta, "old_replay_verification": [{k: v for k, v in row.items() if k != "mode"} | {"mode": row["mode"]} for row in old_verification], "fit_attempts": {"attempts": fit_ledger["attempts"], "failures": fit_ledger["failures"], "limit": fit_ledger["limit"]}, "no_screening_stop": True, "bootstrap": "2000 identity-fixed OOF bootstrap per gain; LOO ranges reported", "private_predictions": True}
    write_json(PUBLIC / "aggregate.json", public)
    write_json(PUBLIC / "run_receipt.json", {"job_id": os.environ["SLURM_JOB_ID"], "run": RUN, "status": public["status"], "private_outputs": True})
    return public


def run_with_failure_receipt():
    try:
        return main()
    except Exception as exc:
        if PRIVATE.exists():
            write_json(PRIVATE / "failure_receipt.json", {"job_id": os.environ.get("SLURM_JOB_ID", "unknown"), "run": RUN, "status": "FAILED", "error_type": type(exc).__name__, "error": repr(exc), "traceback": traceback.format_exc()})
        if PUBLIC.exists():
            write_json(PUBLIC / "run_receipt.json", {"job_id": os.environ.get("SLURM_JOB_ID", "unknown"), "run": RUN, "status": "FAILED", "details_private": True})
        raise


if __name__ == "__main__":
    run_with_failure_receipt()
