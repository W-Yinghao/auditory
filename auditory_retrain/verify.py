"""Independent, read-only completion verification for corrected D retraining.

The verifier consumes saved task receipts, checkpoints, projections and OOF
tables.  It never calls a training or fitting routine.  Candidate-level rows
are written only below the private verification directory; public output is
aggregate and explicitly exploratory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from auditory5.contracts import FitScope
from auditory5.provenance import ROOT, digest, object_hash, require_slurm, write_json
from auditory5.statistics import paired_cluster_bootstrap


RUN = "verification_001"
EXPECTED_MODES = ("L0", "R_SUP", "R_SIM")
LEARNED_MODES = ("R_SUP", "R_SIM")
ALL_MODELS = ("D0_mean", "D1_C", "D2_CV", "D3_CVN", "D4_CN", "D5_CFULL", "D7_CPRE",
              *(f"D6_CRANDOM_{k}" for k in range(20)))
MAIN_MODELS = ("D1_C", "D2_CV", "D3_CVN")
SENSITIVITY_VARIANTS = ("all_trials", "budget40_count_qc", "all_trials_count_qc")


def _sha256(path: Path) -> str:
    return digest(path)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _private_root(config: dict) -> Path:
    return ROOT / config["private_relative"]


def _public_root(config: dict) -> Path:
    return ROOT / config["aggregates_relative"]


def _scope_hash(task: dict) -> str:
    fit_groups = task.get("effective_fit_groups", task["fit_groups"])
    scope = FitScope(tuple(map(str, fit_groups)),
                     tuple(map(str, task.get("validation_groups", []))),
                     tuple(map(str, task.get("test_groups", []))))
    return scope.hash


def _expected_tasks(plan: dict) -> dict:
    tasks = plan.get("tasks", [])
    if len(tasks) != 45:
        raise ValueError(f"expected 45 retraining tasks, found {len(tasks)}")
    names = {str(t.get("name")) for t in tasks}
    learned = [t for t in tasks if t.get("mode") in LEARNED_MODES]
    l0 = [t for t in tasks if t.get("mode") == "L0"]
    if len(learned) != 40 or len(l0) != 5:
        raise ValueError(f"expected 40 learned and 5 L0 tasks, found {len(learned)} and {len(l0)}")
    if sum(t.get("inner_fold") is None for t in learned) != 10 or sum(t.get("inner_fold") is not None for t in learned) != 30:
        raise ValueError("learned task scopes are not 10 outer + 30 clinical-inner")
    if any(t.get("inner_fold") is not None for t in l0):
        raise ValueError("L0 representations must be outer tasks")
    if any(t.get("branch") != "all" for t in tasks):
        raise ValueError("D retraining tasks must use branch=all")
    if sorted(t.get("mode") for t in tasks) != sorted(["L0"] * 5 + ["R_SUP"] * 20 + ["R_SIM"] * 20):
        raise ValueError("unexpected mode/task matrix")
    if any(not t.get("fit_groups") or not t.get("test_groups") for t in tasks):
        raise ValueError("every task needs explicit fit and test identity groups")
    if any(t.get("mode") in LEARNED_MODES and t.get("resource") != "gpu" for t in tasks):
        raise ValueError("learned encoder task lacks GPU resource declaration")
    return {"all": tasks, "learned": learned, "l0": l0, "names": names}


def _discover_mode_file(root: Path, mode: str, filename: str) -> Path:
    candidates = []
    direct = [root / mode / filename, root / f"{mode}_core_001" / filename,
              root / f"{mode}_core" / filename]
    candidates.extend(p for p in direct if p.is_file())
    if not candidates and root.is_dir():
        candidates = [p for p in root.rglob(filename) if mode.lower() in str(p.parent).lower()]
    candidates = sorted(set(candidates))
    if len(candidates) != 1:
        raise FileNotFoundError(f"expected one {filename} for mode {mode} below {root}")
    return candidates[0]


def _gpu_name(task: dict, completion: dict, checkpoint: dict | None = None) -> str | None:
    for source in (completion, task, checkpoint or {}, (checkpoint or {}).get("metadata") or {}):
        for key in ("actual_gpu_name", "gpu_name", "cuda_device_name", "device_name"):
            value = source.get(key) if isinstance(source, dict) else None
            if value:
                return str(value)
    return None


def _allowed_gpu(name: str, allowed: list[str]) -> bool:
    value = name.lower()
    return any(token.lower() in value for token in allowed)


def _validate_task(task: dict, task_dir: Path, plan_hash: str, config_hash: str,
                   expected_groups: set[str], general_groups: set[str], allowed_gpu: list[str]) -> dict:
    task_json = task_dir / "task.json"
    completion_json = task_dir / "completion.json"
    if not task_json.is_file() or not completion_json.is_file():
        raise FileNotFoundError(f"incomplete task receipt: {task_dir}")
    stored = _json(task_json)
    completion = _json(completion_json)
    if completion.get("status") != "PASS" or stored.get("name") != task.get("name"):
        raise ValueError(f"task did not PASS: {task.get('name')}")
    if any(stored.get(key) != value for key, value in task.items()):
        raise ValueError(f"stored task definition differs from frozen plan: {task.get('name')}")
    if stored.get("plan_hash") != plan_hash or completion.get("plan_hash") != plan_hash:
        raise ValueError(f"task plan hash mismatch: {task.get('name')}")
    output_hashes = completion.get("output_hashes")
    if not isinstance(output_hashes, dict) or not output_hashes:
        raise ValueError(f"task output hashes missing: {task.get('name')}")
    for relative, expected in output_hashes.items():
        output = (task_dir / relative).resolve()
        if not output.is_file() or not output.is_relative_to(task_dir.resolve()) or _sha256(output) != expected:
            raise ValueError(f"task output hash mismatch: {task.get('name')}/{relative}")
    if set(map(str, task["test_groups"])) & set(map(str, task["fit_groups"])):
        raise ValueError(f"task fit/test overlap: {task.get('name')}")
    requested_fit = set(map(str, task["fit_groups"]))
    effective_fit = set(map(str, task.get("effective_fit_groups", task["fit_groups"])))
    if effective_fit != requested_fit & general_groups:
        raise ValueError(f"effective fit groups disagree with general support: {task.get('name')}")
    if effective_fit & (set(map(str, task.get("validation_groups", []))) | set(map(str, task["test_groups"]))):
        raise ValueError(f"effective fit/test-validation overlap: {task.get('name')}")
    if task.get("inner_fold") is not None or task.get("stage") == "D_inner":
        if set(map(str, task.get("validation_groups", []))) & set(map(str, task["fit_groups"])):
            raise ValueError(f"inner fit/validation overlap: {task.get('name')}")
    expected_scope = _scope_hash(task)
    if completion.get("encoder_fit_scope_hash") != expected_scope:
        raise ValueError(f"completion scope hash mismatch: {task.get('name')}")
    selected_epoch = None
    diagnostics = {}
    if task.get("mode") in LEARNED_MODES:
        checkpoint_path = task_dir / "encoder.pt"
        if not checkpoint_path.is_file():
            raise FileNotFoundError(f"missing learned encoder: {checkpoint_path}")
        receipt_path = task_dir / "training_receipt.json"
        if not receipt_path.is_file():
            raise FileNotFoundError(f"missing training receipt: {receipt_path}")
        training_receipt = _json(receipt_path)
        if training_receipt.get("status") != "PASS" or training_receipt.get("plan_hash") != plan_hash:
            raise ValueError(f"training receipt status/plan mismatch: {task.get('name')}")
        state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if state.get("version") != "auditory5_training_v2" or state.get("mode") != task.get("mode"):
            raise ValueError(f"encoder checkpoint version/mode mismatch: {task.get('name')}")
        if state.get("scope_hash") != expected_scope:
            raise ValueError(f"encoder checkpoint scope mismatch: {task.get('name')}")
        saved_scope = state.get("scope", {})
        if not isinstance(saved_scope, dict):
            raise ValueError(f"encoder checkpoint scope is missing: {task.get('name')}")
        try:
            saved_scope_hash = FitScope(tuple(map(str, saved_scope["train_groups"])),
                                       tuple(map(str, saved_scope.get("validation_groups", []))),
                                       tuple(map(str, saved_scope.get("test_groups", [])))).hash
        except (KeyError, TypeError):
            raise ValueError(f"encoder checkpoint scope schema is incomplete: {task.get('name')}")
        if saved_scope_hash != expected_scope:
            raise ValueError(f"encoder checkpoint full scope mismatch: {task.get('name')}")
        if set(map(str, saved_scope.get("train_groups", []))) != effective_fit:
            raise ValueError(f"encoder checkpoint fit groups mismatch: {task.get('name')}")
        metadata = state.get("metadata") or {}
        if metadata.get("config_hash") != config_hash:
            raise ValueError(f"encoder config hash mismatch: {task.get('name')}")
        if metadata.get("scope_hash") != expected_scope:
            raise ValueError(f"encoder metadata scope mismatch: {task.get('name')}")
        gpu = _gpu_name(task, completion, state)
        if not gpu or not _allowed_gpu(gpu, allowed_gpu):
            raise ValueError(f"learned encoder has missing/unsupported GPU name: {task.get('name')}")
        receipt_gpu = _gpu_name(task, training_receipt, state)
        if receipt_gpu != gpu and receipt_gpu is not None:
            raise ValueError(f"training receipt GPU mismatch: {task.get('name')}")
        encoder_sha = training_receipt.get("encoder_sha256", training_receipt.get("encoder_sha"))
        if encoder_sha != _sha256(checkpoint_path):
            raise ValueError(f"training receipt encoder hash mismatch: {task.get('name')}")
        if training_receipt.get("scope_hash") != expected_scope:
            raise ValueError(f"training receipt scope mismatch: {task.get('name')}")
        selected_epoch = metadata.get("selected_epochs", training_receipt.get("selected_epochs"))
        if selected_epoch is None or int(selected_epoch) < 1:
            raise ValueError(f"missing selected checkpoint epoch: {task.get('name')}")
        if task.get("mode") == "R_SUP" and int(selected_epoch) > 80:
            raise ValueError(f"supervised selected epoch exceeds 80: {task.get('name')}")
        if task.get("mode") == "R_SIM" and int(selected_epoch) != 100:
            raise ValueError(f"SimCLR selected epoch is not fixed 100: {task.get('name')}")
        history = metadata.get("history", [])
        monitor_history = metadata.get("monitor_history", [])
        if task.get("mode") == "R_SIM" and len(history) != 100:
            raise ValueError(f"SimCLR history is not 100 epochs: {task.get('name')}")
        if task.get("mode") == "R_SUP" and len(history) != int(selected_epoch):
            raise ValueError(f"supervised history does not match selected epoch: {task.get('name')}")
        if task.get("mode") == "R_SUP" and len(monitor_history) < int(selected_epoch):
            raise ValueError(f"supervised monitor history is incomplete: {task.get('name')}")
        for row in history + (monitor_history if task.get("mode") == "R_SUP" else []):
            for key in ("loss_nats", "gradient_norm_before_clip_mean"):
                if key in row and (not np.isfinite(float(row[key]))):
                    raise ValueError(f"nonfinite training history: {task.get('name')}")
            if int(row.get("actual_overlap_violations", 0)) != 0:
                raise ValueError(f"training overlap violation: {task.get('name')}")
        scaler_groups = set(map(str, (state.get("scaler") or {}).get("fit_groups", [])))
        if scaler_groups != effective_fit:
            raise ValueError(f"scaler fit groups mismatch: {task.get('name')}")
        if (state.get("scaler") or {}).get("scope_hash") != expected_scope:
            raise ValueError(f"scaler scope mismatch: {task.get('name')}")
        diagnostics = {key: metadata.get(key) for key in ("encoder_variance_mean", "encoder_effective_rank")}
        if any(value is None or not np.isfinite(float(value)) or float(value) < 0 for value in diagnostics.values()):
            raise ValueError(f"invalid encoder diagnostics: {task.get('name')}")
    else:
        if (task_dir / "encoder.pt").exists():
            raise ValueError(f"L0 task unexpectedly contains encoder.pt: {task.get('name')}")
        gpu = _gpu_name(task, completion)
    all_task_groups = set(map(str, task["fit_groups"])) | set(map(str, task.get("validation_groups", []))) | set(map(str, task["test_groups"]))
    if not all_task_groups <= expected_groups:
        raise ValueError(f"malformed test groups: {task.get('name')}")
    return {"name": task["name"], "mode": task["mode"], "stage": task.get("stage"),
            "requested_fit_groups": sorted(requested_fit), "effective_fit_groups": sorted(effective_fit),
            "fit_groups": sorted(effective_fit), "validation_groups": sorted(map(str, task.get("validation_groups", []))),
            "test_groups": sorted(map(str, task["test_groups"])), "gpu_name": gpu,
            "scope_hash": expected_scope, "selected_epoch": selected_epoch,
            "job_id": completion.get("job_id"), "encoder_variance_mean": diagnostics.get("encoder_variance_mean"),
            "encoder_effective_rank": diagnostics.get("encoder_effective_rank")}


def _load_folds(split_path: Path, support_path: Path, config: dict) -> tuple[dict, set[str], dict[str, int]]:
    split = _json(split_path)
    support = pd.read_parquet(support_path)
    if "split_group_id" not in support.columns or "D" not in support.columns:
        raise ValueError("new support table lacks split_group_id/D")
    d_ids = set(support.loc[support["D"].astype(bool), "split_group_id"].astype(str))
    if len(d_ids) != int(config["expected_D_groups"]):
        raise ValueError(f"expected {config['expected_D_groups']} D groups, found {len(d_ids)}")
    folds = split.get("folds", [])
    if len(folds) != int(config["outer_folds"]):
        raise ValueError("unexpected outer fold count")
    mapping = {}
    for fold in folds:
        for group in fold.get("test_groups", []):
            group = str(group)
            if group in mapping:
                raise ValueError("group appears in multiple outer test folds")
            mapping[group] = int(fold["outer_fold"])
    outer_groups = set(mapping)
    if len(outer_groups) != int(config["expected_outer_groups"]):
        raise ValueError("outer folds do not cover the declared outer support universe")
    if not d_ids <= outer_groups:
        raise ValueError("new D cohort is not contained in outer support universe")
    if len(set(mapping.values())) != int(config["outer_folds"]):
        raise ValueError("empty outer fold")
    return split, d_ids, mapping


def _changed_assignment_count(new_map: dict[str, int], old_split_path: Path, expected_outer: int) -> int | None:
    if not old_split_path.is_file():
        return None
    old = _json(old_split_path)
    old_map = {str(g): int(f["outer_fold"]) for f in old.get("folds", []) for g in f.get("test_groups", [])}
    common = set(new_map) & set(old_map)
    changed = sum(new_map[g] != old_map[g] for g in common)
    if len(common) != expected_outer:
        raise ValueError(f"old/new outer support intersection expected {expected_outer}, found {len(common)}")
    return int(changed)


def _clinical_target_map(path: Path, d_ids: set[str]) -> dict[str, float]:
    clinical = pd.read_parquet(path)
    required = {"split_group_id", "MUSS_source_percentage"}
    if not required <= set(clinical.columns):
        raise ValueError(f"clinical manifest missing: {sorted(required - set(clinical.columns))}")
    clinical = clinical[clinical["split_group_id"].astype(str).isin(d_ids)].copy()
    clinical["split_group_id"] = clinical["split_group_id"].astype(str)
    if clinical.duplicated("split_group_id").any() or set(clinical["split_group_id"]) != d_ids:
        raise ValueError("clinical manifest does not provide one target row per D group")
    values = pd.to_numeric(clinical["MUSS_source_percentage"], errors="coerce")
    if not np.isfinite(values.to_numpy(float)).all() or not values.between(0, 100).all():
        raise ValueError("clinical manifest target is nonfinite or outside 0-100")
    return dict(zip(clinical["split_group_id"], values.astype(float)))


def _validate_oof(path: Path, mode: str, d_ids: set[str], fold_map: dict[str, int],
                  target_map: dict[str, float]) -> tuple[dict, pd.DataFrame]:
    frame = pd.read_parquet(path)
    required = {"mode", "outer_fold", "split_group_id", "model", "target", "prediction", "absolute_error"}
    if not required <= set(frame.columns):
        raise ValueError(f"OOF schema missing for {mode}: {sorted(required - set(frame.columns))}")
    frame = frame[frame["mode"].astype(str) == mode].copy()
    frame["split_group_id"] = frame["split_group_id"].astype(str)
    if set(frame["mode"].astype(str)) != {mode}:
        raise ValueError(f"OOF mode mismatch: {mode}")
    if set(frame["split_group_id"]) != d_ids or set(frame["model"]) != set(ALL_MODELS):
        raise ValueError(f"OOF cohort/model set mismatch: {mode}")
    if len(frame) != len(d_ids) * len(ALL_MODELS) or frame.duplicated(["split_group_id", "model"]).any():
        raise ValueError(f"OOF duplicate or incomplete matrix: {mode}")
    if any(fold_map[g] != int(f) for g, f in zip(frame["split_group_id"], frame["outer_fold"])):
        raise ValueError(f"OOF outer fold mismatch: {mode}")
    numeric = frame[["target", "prediction", "absolute_error"]].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(float)).all():
        raise ValueError(f"nonfinite OOF values: {mode}")
    if not np.allclose(numeric["absolute_error"], np.abs(numeric["target"] - numeric["prediction"]), atol=1e-9):
        raise ValueError(f"OOF absolute-error mismatch: {mode}")
    if not numeric["target"].between(0, 100).all():
        raise ValueError(f"OOF target outside 0-100: {mode}")
    if not numeric["prediction"].between(0, 100).all():
        raise ValueError(f"OOF prediction outside 0-100: {mode}")
    expected_targets = frame["split_group_id"].map(target_map).to_numpy(float)
    if not np.allclose(numeric["target"].to_numpy(float), expected_targets, atol=1e-9):
        raise ValueError(f"OOF target disagrees with frozen clinical manifest: {mode}")
    summaries = {"mode": mode, "rows": int(len(frame)), "n_candidates": int(len(d_ids)),
                 "MAE": {m: float(frame.loc[frame.model == m, "absolute_error"].mean()) for m in ALL_MODELS},
                 "random_control_MAE": {m: float(frame.loc[frame.model == m, "absolute_error"].mean())
                                         for m in ALL_MODELS if m.startswith("D6_CRANDOM_")}}
    errors = frame.pivot(index="split_group_id", columns="model", values="absolute_error").loc[sorted(d_ids)]
    for name, baseline, augmented in (("D2_CV_vs_D3_CVN", "D2_CV", "D3_CVN"),
                                      ("D1_C_vs_D3_CVN", "D1_C", "D3_CVN")):
        gain = paired_cluster_bootstrap(errors[baseline].to_numpy(float), errors[augmented].to_numpy(float),
                                         errors.index.to_numpy(str), n_boot=2000, seed=20260917)
        diffs = errors[baseline].to_numpy(float) - errors[augmented].to_numpy(float)
        loo = [(float(np.delete(diffs, i).mean()) if len(diffs) > 1 else float(diffs.mean())) for i in range(len(diffs))]
        summaries[name] = {**gain, "loo_min": float(min(loo)), "loo_max": float(max(loo))}
    return summaries, frame


def _validate_sensitivities(path: Path, mode: str, d_ids: set[str], fold_map: dict[str, int],
                            target_map: dict[str, float]) -> tuple[dict, pd.DataFrame]:
    frame = pd.read_parquet(path)
    required = {"mode", "outer_fold", "variant", "model", "split_group_id", "target", "prediction", "absolute_error"}
    if not required <= set(frame.columns):
        raise ValueError(f"sensitivity schema missing: {sorted(required - set(frame.columns))}")
    frame = frame[frame["mode"].astype(str) == mode].copy()
    frame["split_group_id"] = frame["split_group_id"].astype(str)
    if set(frame["mode"].astype(str)) != {mode} or set(frame["variant"]) != set(SENSITIVITY_VARIANTS):
        raise ValueError(f"sensitivity mode/variant mismatch: {mode}")
    expected = sum(len(ALL_MODELS) if v == "all_trials" else len(MAIN_MODELS) for v in SENSITIVITY_VARIANTS) * len(d_ids)
    if len(frame) != expected or frame.duplicated(["variant", "split_group_id", "model"]).any():
        raise ValueError(f"sensitivity incomplete matrix: {mode}")
    for variant in SENSITIVITY_VARIANTS:
        part = frame[frame.variant == variant]
        expected_models = set(ALL_MODELS if variant == "all_trials" else MAIN_MODELS)
        if set(part.model) != expected_models or set(part.split_group_id) != d_ids:
            raise ValueError(f"sensitivity cohort/model mismatch: {mode}/{variant}")
    if any(fold_map[g] != int(f) for g, f in zip(frame["split_group_id"], frame["outer_fold"])):
        raise ValueError(f"sensitivity outer fold mismatch: {mode}")
    numeric = frame[["target", "prediction", "absolute_error"]].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(float)).all():
        raise ValueError(f"nonfinite sensitivity values: {mode}")
    if not numeric["target"].between(0, 100).all() or not numeric["prediction"].between(0, 100).all():
        raise ValueError(f"sensitivity target/prediction outside 0-100: {mode}")
    expected_targets = frame["split_group_id"].map(target_map).to_numpy(float)
    if not np.allclose(numeric["target"].to_numpy(float), expected_targets, atol=1e-9):
        raise ValueError(f"sensitivity target disagrees with frozen clinical manifest: {mode}")
    if not np.allclose(numeric["absolute_error"], np.abs(numeric["target"] - numeric["prediction"]), atol=1e-9):
        raise ValueError(f"sensitivity absolute-error mismatch: {mode}")
    return {"mode": mode, "rows": int(len(frame)), "variants": {v: int((frame.variant == v).sum()) for v in SENSITIVITY_VARIANTS}}, frame


def _validate_controls(control_private: Path, control_public: Path, expected_modes: tuple[str, ...]) -> dict:
    status_path = control_public / "control_status.json"
    if not status_path.is_file():
        status_path = control_private / "control_status.json"
    if not status_path.is_file():
        raise FileNotFoundError("missing controls control_status.json")
    statuses = json.loads(status_path.read_text())
    if not isinstance(statuses, list) or not statuses or any(row.get("status") != "PASS" for row in statuses):
        raise ValueError("control status contains failures or is incomplete")
    status_keys = [(row.get("control"), row.get("mode"), row.get("outer_fold"), row.get("inner_fold"))
                   for row in statuses]
    if len(status_keys) != len(set(status_keys)):
        raise ValueError("control status contains duplicate coverage rows")
    expected_status = {("count_QC_source", "all", None, None)}
    for mode in expected_modes:
        for outer in range(5):
            for variant in SENSITIVITY_VARIANTS:
                expected_status.add((variant, mode, outer, None))
            for inner in (0, 1, 2):
                expected_status.add(("FP32_invariance", mode, outer, inner))
            expected_status.add(("FP32_invariance", mode, outer, None))
            expected_status.add(("null_linear_stimulus_probe", mode, outer, None))
    if set(status_keys) != expected_status:
        raise ValueError("control status does not cover all mode/fold/inner controls")
    fp32_path = control_public / "fp32_invariance.json"
    if not fp32_path.is_file():
        fp32_path = control_private / "fp32_invariance.json"
    if not fp32_path.is_file():
        raise FileNotFoundError("missing FP32 invariance report")
    fp32 = json.loads(fp32_path.read_text())
    if not isinstance(fp32, list) or not fp32 or any(row.get("status") != "PASS" for row in fp32):
        raise ValueError("FP32 invariance control did not PASS")
    fp32_keys = [(row.get("mode"), row.get("outer_fold"), row.get("inner_fold")) for row in fp32]
    if len(fp32) != len(expected_modes) * 5 * 4 or len(fp32_keys) != len(set(fp32_keys)):
        raise ValueError("FP32 invariance coverage is not 3 modes x 5 folds x 4 scopes")
    if set(fp32_keys) != {(mode, outer, inner) for mode in expected_modes for outer in range(5)
                          for inner in (0, 1, 2, None)}:
        raise ValueError("FP32 invariance rows have incomplete mode/fold/inner coverage")
    for row in fp32:
        for key in ("real_max_abs_probability_difference", "synthetic_max_abs_probability_difference"):
            if key not in row or not np.isfinite(float(row[key])) or float(row[key]) > 1e-6:
                raise ValueError("FP32 invariance threshold failure")
    null_path = control_public / "null_stimulus_probe.json"
    if not null_path.is_file():
        raise FileNotFoundError("missing null_stimulus_probe.json")
    null_rows = json.loads(null_path.read_text())
    if not isinstance(null_rows, list) or not null_rows:
        raise ValueError("null stimulus probe report is empty")
    errors_path = control_private / "errors.json"
    if errors_path.is_file() and json.loads(errors_path.read_text()):
        raise ValueError("controls errors.json is nonempty")
    completion_path = control_private / "completion.json"
    if not completion_path.is_file():
        raise FileNotFoundError("missing controls completion.json")
    completion = _json(completion_path)
    if completion.get("status") not in {"COMPLETED_DIAGNOSTICS"}:
        raise ValueError("controls completion status is not complete")
    output_hashes = completion.get("output_hashes")
    if not isinstance(output_hashes, dict) or not output_hashes:
        raise ValueError("controls output hashes are missing")
    for name, expected in output_hashes.items():
        output = control_private / name
        if not output.is_file() or _sha256(output) != expected:
            raise ValueError(f"controls output hash mismatch: {name}")
    return {"status_rows": int(len(statuses)), "fp32_rows": int(len(fp32)), "all_pass": True,
            "null_probe_rows": int(len(null_rows)),
            "gpu_names": sorted({str(row.get("gpu_name")) for row in statuses if row.get("gpu_name")})}


def _compare_old_replay(new_frame: pd.DataFrame, old_path: Path, old_ids: set[str], mode: str) -> dict:
    old = pd.read_parquet(old_path)
    required = {"mode", "split_group_id", "model", "absolute_error"}
    if not required <= set(old.columns):
        raise ValueError("old corrected replay schema is incomplete")
    old = old[old["mode"].astype(str) == mode].copy()
    old["split_group_id"] = old["split_group_id"].astype(str)
    new_ids = set(new_frame["split_group_id"])
    common = sorted(new_ids & old_ids & set(old["split_group_id"]))
    if len(common) != len(new_ids & old_ids):
        raise ValueError(f"old replay rows do not cover expected intersection for {mode}")
    old = old[old.split_group_id.isin(common)]
    new = new_frame[new_frame.split_group_id.isin(common)]
    out = {"mode": mode, "intersection_candidates": len(common), "MAE_new_minus_old": {}}
    for model in ALL_MODELS:
        a = old[old.model == model].set_index("split_group_id")["absolute_error"].reindex(common)
        b = new[new.model == model].set_index("split_group_id")["absolute_error"].reindex(common)
        if a.isna().any() or b.isna().any() or not np.isfinite(a.to_numpy(float)).all() or not np.isfinite(b.to_numpy(float)).all():
            raise ValueError(f"old/new replay matrix incomplete for {mode}/{model}")
        out["MAE_new_minus_old"][model] = float(b.mean() - a.mean())
    out["interpretation"] = "Descriptive changed-cohort/fold comparison; not an isolated causal effect of the added group."
    return out


def run(plan_path, run_name: str = RUN) -> dict:
    """Validate one completed plan without fitting or regenerating any model."""
    require_slurm()
    plan_path = Path(plan_path)
    plan_path = (plan_path if plan_path.is_absolute() else ROOT / plan_path).resolve()
    config_path = ROOT / "configs/auditory_retrain_v1.json"
    spec = _json(config_path)
    plan = _json(plan_path)
    config = plan.get("config")
    if not isinstance(config, dict) or config.get("corrected_retraining") != spec:
        raise ValueError("plan embedded config does not match retraining specification")
    if spec.get("version") != "auditory_D_corrected_full_retraining_v1":
        raise ValueError("unexpected retraining config version")
    if plan.get("split_run") != spec["split_run"] or plan.get("config_hash") != object_hash(config):
        raise ValueError("plan/config mismatch")
    if not plan.get("code_hashes") or not plan.get("source_snapshot"):
        raise ValueError("plan lacks immutable source snapshot hashes")
    task_info = _expected_tasks(plan)
    private_root = _private_root(spec)
    public_root = _public_root(spec)
    split_path = private_root / "splits" / spec["split_run"] / "folds.json"
    support_path = split_path.parent / "support.parquet"
    split, d_ids, fold_map = _load_folds(split_path, support_path, spec)
    if int(spec["expected_outer_groups"]) != len(set(fold_map)):
        raise ValueError("unexpected outer support universe")
    changed = _changed_assignment_count(fold_map, ROOT / spec["old_splits"] / "folds.json", int(spec["expected_outer_groups"]))
    if changed is not None and changed != int(spec["expected_changed_outer_assignments"]):
        raise ValueError(f"expected {spec['expected_changed_outer_assignments']} changed outer assignments, found {changed}")
    core_root = private_root / "core_001"
    controls_private = private_root / "controls_001"
    controls_public = public_root / "controls_001"
    old_replay = ROOT / "private/auditory_repair/legacy_d_002/corrected_clinical_oof.parquet"
    core_oof = core_root / "clinical_oof.parquet"
    core_aggregate = core_root / "aggregate.json"
    clinical_manifest = private_root / "data" / spec["manifest_run"] / "clinical_index.parquet"
    oof_paths = {mode: core_oof for mode in EXPECTED_MODES}
    agg_paths = {mode: core_aggregate for mode in EXPECTED_MODES}
    sensitivity_path = controls_private / "clinical_sensitivity_oof.parquet"
    if not sensitivity_path.is_file():
        raise FileNotFoundError(f"missing sensitivity OOF: {sensitivity_path}")
    old_support_path = ROOT / spec["old_splits"] / "support.parquet"
    eeg_manifest_path = plan_path.parent / "verified_EEG_inputs.json"
    input_paths = [Path(__file__), config_path, plan_path, split_path, support_path, old_support_path,
                   eeg_manifest_path, clinical_manifest, *oof_paths.values(), *agg_paths.values(), sensitivity_path,
                   old_replay]
    for task in task_info["all"]:
        task_dir = plan_path.parent / "outputs" / task["name"]
        input_paths.extend([task_dir / "task.json", task_dir / "completion.json"])
        if task["mode"] in LEARNED_MODES:
            input_paths.extend([task_dir / "encoder.pt", task_dir / "training_receipt.json"])
    input_paths.extend(p for p in (controls_private / "errors.json", controls_private / "control_status.json",
                                   controls_private / "fp32_invariance.json", controls_private / "completion.json",
                                   controls_public / "control_status.json", controls_public / "fp32_invariance.json",
                                   controls_public / "null_stimulus_probe.json", controls_public / "summary.json") if p.is_file())
    source_snapshot = Path(plan.get("source_snapshot", ""))
    if not source_snapshot.is_absolute():
        source_snapshot = (ROOT / source_snapshot).resolve()
    prehashed = {}
    for path, expected in plan.get("input_hashes", {}).items():
        actual = _sha256(Path(path)) if Path(path).is_file() else None
        if actual != expected:
            raise ValueError(f"plan input hash mismatch: {path}")
        prehashed[path] = actual
        input_paths.append(Path(path))
    eeg_manifest = _json(eeg_manifest_path)
    for path, expected in eeg_manifest.items():
        actual = _sha256(Path(path)) if Path(path).is_file() else None
        if actual != expected:
            raise ValueError(f"verified EEG input changed: {path}")
        prehashed[path] = actual
        input_paths.append(Path(path))
    if plan.get("EEG_hash_manifest_hash") != _sha256(eeg_manifest_path):
        raise ValueError("EEG hash manifest changed")
    for path, stamp in plan.get("EEG_file_stamps", {}).items():
        stat = Path(path).stat()
        if [stat.st_size, stat.st_mtime_ns] != stamp:
            raise ValueError(f"EEG file metadata changed: {path}")
    for relative, expected in plan.get("code_hashes", {}).items():
        source = source_snapshot / relative
        actual = _sha256(source) if source.is_file() else None
        if actual != expected:
            raise ValueError(f"source snapshot hash mismatch: {relative}")
        prehashed[str(source)] = actual
        input_paths.append(source)
    missing = [str(p) for p in input_paths if not p.is_file()]
    if missing:
        raise FileNotFoundError("missing verification inputs: " + ", ".join(missing[:8]))
    hashes = {str(p): (prehashed[str(p)] if str(p) in prehashed else _sha256(p))
              for p in sorted(set(input_paths))}
    if not run_name or Path(run_name).name != run_name or run_name in {".", ".."}:
        raise ValueError("run_name must be a simple new namespace name")
    private_out = private_root / run_name
    public_out = public_root / run_name
    if private_out.exists() or public_out.exists():
        raise FileExistsError("refusing to overwrite verification run")
    private_out.mkdir(parents=True, exist_ok=False, mode=0o700)
    public_out.mkdir(parents=True, exist_ok=False, mode=0o700)
    write_json(private_out / "start_receipt.json", {"status": "STARTED", "job_id": os.environ["SLURM_JOB_ID"], "plan_hash": _sha256(plan_path)})
    try:
        config_hash = plan["config_hash"]
        old_support = pd.read_parquet(old_support_path)
        old_d_ids = set(old_support.loc[old_support["D"].astype(bool), "split_group_id"].astype(str))
        old_new_intersection = d_ids & old_d_ids
        if len(old_new_intersection) != 49:
            raise ValueError(f"expected 49 old/new corrected D identities in descriptive intersection, found {len(old_new_intersection)}")
        aggregate = _json(core_aggregate)
        if aggregate.get("plan_hash") != _sha256(plan_path):
            raise ValueError("core aggregate plan hash mismatch")
        if set(row.get("mode") for row in aggregate.get("modes", [])) != set(EXPECTED_MODES):
            raise ValueError("core aggregate does not cover all three modes")
        target_map = _clinical_target_map(clinical_manifest, d_ids)
        new_support = pd.read_parquet(support_path)
        general_groups = set(new_support.loc[new_support["general"].astype(bool), "split_group_id"].astype(str))
        task_reports = [_validate_task(t, plan_path.parent / "outputs" / t["name"], _sha256(plan_path), config_hash,
                                       set(fold_map), general_groups, list(spec["allowed_GPU_names"])) for t in task_info["all"]]
        oof_reports, private_oof = [], []
        for mode in EXPECTED_MODES:
            report, frame = _validate_oof(oof_paths[mode], mode, d_ids, fold_map, target_map)
            oof_reports.append(report); private_oof.append(frame)
        sensitivity_reports = []
        sensitivity_frames = []
        old_reports = []
        for mode in EXPECTED_MODES:
            # The control output is a combined table; each mode is checked here.
            report, frame = _validate_sensitivities(sensitivity_path, mode, d_ids, fold_map, target_map)
            sensitivity_reports.append(report); sensitivity_frames.append(frame)
            old_reports.append(_compare_old_replay(new_frame=private_oof[EXPECTED_MODES.index(mode)], old_path=old_replay,
                                                   old_ids=old_d_ids, mode=mode))
        control_report = _validate_controls(controls_private, controls_public, EXPECTED_MODES)
        private_pd = pd.concat(private_oof + sensitivity_frames, ignore_index=True, sort=False)
        private_pd.to_parquet(private_out / "candidate_diagnostics.parquet", index=False)
        write_json(private_out / "task_reports.json", task_reports)
        write_json(private_out / "input_hashes.json", hashes)
        eeg_paths = set(eeg_manifest)
        for p, expected in hashes.items():
            if p in eeg_paths:
                continue
            if _sha256(Path(p)) != expected:
                raise ValueError(f"input changed during verification: {p}")
        gpu_names = sorted({x["gpu_name"] for x in task_reports if x.get("gpu_name")})
        encoder_diagnostics = {}
        for mode in LEARNED_MODES:
            rows = [x for x in task_reports if x["mode"] == mode]
            encoder_diagnostics[mode] = {
                "n": len(rows),
                "encoder_variance_mean_range": [float(min(x["encoder_variance_mean"] for x in rows)),
                                                  float(max(x["encoder_variance_mean"] for x in rows))],
                "encoder_effective_rank_range": [float(min(x["encoder_effective_rank"] for x in rows)),
                                                  float(max(x["encoder_effective_rank"] for x in rows))],
                "zero_variance_count": sum(float(x["encoder_variance_mean"]) == 0 for x in rows),
                "zero_effective_rank_count": sum(float(x["encoder_effective_rank"]) == 0 for x in rows),
            }
        summary = {"status": "VERIFIED", "verification_run": run_name, "job_id": os.environ["SLURM_JOB_ID"],
                   "plan_hash": _sha256(plan_path), "tasks": {"expected": 45, "completed": len(task_reports),
                   "learned_encoders": 40, "L0_outer_representations": 5},
                   "new_D_groups": len(d_ids), "outer_support_groups": len(fold_map),
                   "changed_outer_assignments_vs_old": changed, "modes": oof_reports,
                   "sensitivity": sensitivity_reports, "old_corrected_replay_comparison": old_reports,
                   "controls": control_report,
                   "actual_GPU_names": gpu_names, "seed": int(spec["seed"]),
                   "encoder_diagnostics": encoder_diagnostics,
                   "checkpoint_epochs": {mode: sorted({int(x["selected_epoch"]) for x in task_reports
                                                         if x["mode"] == mode and x.get("selected_epoch") is not None})
                                         for mode in LEARNED_MODES},
                   "scientific_status": "exploratory_single_seed", "independent_validation": False,
                   "no_model_refit": True, "input_hashes_private": True}
        write_json(public_out / "summary.json", summary)
        write_json(public_out / "run_receipt.json", {"status": "VERIFIED", "job_id": os.environ["SLURM_JOB_ID"],
                                                        "plan_hash": _sha256(plan_path), "private_diagnostics": True})
        write_json(private_out / "completion.json", {"status": "VERIFIED", "job_id": os.environ["SLURM_JOB_ID"],
                                                       "input_count": len(hashes), "candidate_rows_private": len(private_pd)})
        return summary
    except Exception as exc:
        write_json(private_out / "failure_receipt.json", {"status": "FAILED", "job_id": os.environ.get("SLURM_JOB_ID"),
                                                           "error_type": type(exc).__name__, "error": str(exc),
                                                           "traceback": traceback.format_exc()})
        write_json(public_out / "run_receipt.json", {"status": "FAILED", "job_id": os.environ.get("SLURM_JOB_ID"),
                                                      "details_private": True})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("plan_path")
    args = parser.parse_args()
    run(args.plan_path)
