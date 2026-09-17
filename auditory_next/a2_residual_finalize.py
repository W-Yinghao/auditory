"""Recover a completed A2 residual matrix after the exclusive-output bug.

No scaler, PCA, background regression, encoder or readout is fitted here.
The twenty original ridge fits remain charged to their source task allowance.
Only saved matrices and vector statistics enter recovered effect aggregates.
"""
import json
from pathlib import Path
import pickle
import re
import zipfile

import numpy as np
import pandas as pd
import yaml

from auditory5.contracts import FitScope
from auditory5.routes.a_matching import bootstrap_match
from .a2_execution import _load_task
from .a2_residual_audit import identity_contrast
from .provenance import ROOT, digest, object_hash, write_json, require_slurm, finish

MODES = ("L0", "R_RAND", "R_SUP", "R_SIM")
QUANTITIES = ("Delta", "P", "R")
METRICS = ("inner_product", "cosine")
TERMS = ("delta_delta", "minus_delta_prediction", "minus_prediction_delta", "prediction_prediction")
QUALITY_UNAVAILABLE = "FEATURE_TASK_HAS_NO_FIXED_QUALITY_ARRAY"


def validate_saved_details(details, expected_groups):
    """Recheck every saved pair, exact identity and matching scalar; no vectors fit."""
    groups = tuple(map(str, details["groups"]))
    if groups != tuple(map(str, expected_groups)) or len(groups) < 2 or len(set(groups)) != len(groups):
        raise ValueError("A2RF_SAVED_GROUP_ALIGNMENT")
    decomposition = details["decomposition"]
    matrices = decomposition["matrices"]
    if set(matrices) != set(TERMS) | {"residual"}:
        raise ValueError("A2RF_FOUR_TERM_MATRIX_KEYS")
    tolerance = float(decomposition["tolerance"])
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("A2RF_IDENTITY_TOLERANCE")
    for key, value in matrices.items():
        matrix = np.asarray(value, float)
        if matrix.shape != (len(groups), len(groups)) or not np.isfinite(matrix).all():
            raise ValueError("A2RF_PAIR_SHAPE_FINITE")
        if not np.allclose(matrix, details["matrices"][key], rtol=0, atol=tolerance):
            raise ValueError("A2RF_DUPLICATE_MATRIX_MISMATCH")
        summary = identity_contrast(matrix, groups)
        for name in ("matched", "mismatched", "gain"):
            if not np.isclose(summary[name], decomposition["summaries"][key][name], rtol=0, atol=tolerance):
                raise ValueError("A2RF_DECOMPOSITION_SCALAR_MISMATCH")
    expected_tolerance = 1e-11 * max(1., *(float(np.max(np.abs(value))) for value in matrices.values()))
    if not np.isclose(tolerance, expected_tolerance, rtol=1e-12, atol=0):
        raise ValueError("A2RF_IDENTITY_TOLERANCE_CHANGED")
    maximum = float(np.max(np.abs(matrices["residual"] - sum(matrices[key] for key in TERMS))))
    gain_error = abs(decomposition["summaries"]["residual"]["gain"] -
                     sum(decomposition["summaries"][key]["gain"] for key in TERMS))
    for error in (maximum, gain_error, decomposition["max_pair_error"], decomposition["matching_gain_error"]):
        if not np.isfinite(error) or error < 0 or error > tolerance:
            raise ValueError("A2RF_FOUR_TERM_IDENTITY")
    pair = details["pair_matrices"]
    if set(pair) != {q + "_" + m for q in QUANTITIES for m in METRICS}:
        raise ValueError("A2RF_COMPLETE_QUANTITY_METRIC_MATRIX")
    for quantity in QUANTITIES:
        stats = details["vector_statistics"][quantity]
        if stats["cosine_status"] != "DEFINED" or stats["zero_norm_vectors"] != 0:
            raise ValueError("A2RF_UNRESOLVED_SOURCE_COSINE")
        for metric in METRICS:
            value = np.asarray(pair[quantity + "_" + metric], float)
            if value.shape != (len(groups), len(groups)) or not np.isfinite(value).all():
                raise ValueError("A2RF_PAIR_SHAPE_FINITE")
            if metric == "cosine" and np.max(np.abs(value)) > 1 + 1e-9:
                raise ValueError("A2RF_COSINE_RANGE")
            for name, scalar in identity_contrast(value, groups).items():
                if not np.isclose(scalar, stats[metric][name], rtol=1e-10, atol=1e-11):
                    raise ValueError("A2RF_VECTOR_STATISTIC_MISMATCH")
        key = {"Delta": "delta_delta", "P": "prediction_prediction", "R": "residual"}[quantity]
        if not np.allclose(pair[quantity + "_inner_product"], matrices[key], rtol=0, atol=tolerance):
            raise ValueError("A2RF_PAIR_DECOMPOSITION_MISMATCH")
    return dict(max_pair_error=maximum, matching_gain_error=float(gain_error), tolerance=tolerance)


def reconstruct_aggregates(records, *, n_boot=2000, seed=20260917):
    """Complete 4x5 saved matrix, with the original fold ordering and RNG draws."""
    if len(records) != 20 or {(r["mode"], r["outer_fold"]) for r in records} != {
            (mode, fold) for mode in MODES for fold in range(5)}:
        raise ValueError("A2RF_COMPLETE_TWENTY_FOLD_MATRIX")
    fold_groups, results, decomposition_rows = {}, [], []
    for record in records:
        mode, number, details = record["mode"], record["outer_fold"], record["details"]
        groups = tuple(details["groups"])
        validate_saved_details(details, groups)
        if number in fold_groups and fold_groups[number] != groups:
            raise ValueError("A2RF_DIFFERENT_MODE_COHORT")
        fold_groups[number] = groups
        for term, summary in details["decomposition"]["summaries"].items():
            decomposition_rows.append(dict(mode=mode, outer_fold=number, term=term, **summary))
        for quantity in QUANTITIES:
            for metric in METRICS:
                boot = bootstrap_match([details["pair_matrices"][quantity + "_" + metric]], [groups],
                                       n_boot=n_boot, seed=seed + number)
                results.append(dict(mode=mode, outer_fold=number, quantity=quantity, metric=metric,
                    **details["vector_statistics"][quantity][metric], **_boot_row(boot, len(groups), n_boot),
                    quality_status=record["quality_status"], background_components="|".join(record["background_components"])))
    flattened = [g for groups in fold_groups.values() for g in groups]
    if len(set(flattened)) != len(flattened):
        raise ValueError("A2RF_OUTER_TEST_IDENTITY_OVERLAP")
    for mode in MODES:
        own = [r for r in records if r["mode"] == mode]
        ids = [r["details"]["groups"] for r in own]
        for quantity in QUANTITIES:
            for metric in METRICS:
                matrices = [r["details"]["pair_matrices"][quantity + "_" + metric] for r in own]
                boot = bootstrap_match(matrices, ids, n_boot=n_boot, seed=seed)
                results.append(dict(mode=mode, outer_fold="ALL", quantity=quantity, metric=metric,
                    **_boot_row(boot, sum(map(len, ids)), n_boot)))
    return pd.DataFrame(results), pd.DataFrame(decomposition_rows)


def _boot_row(boot, n_candidates, n_boot):
    values = [boot["estimate"], *boot["ci95"]]
    return dict(estimate=float(values[0]) if np.isfinite(values[0]) else None,
        ci_lower=float(values[1]) if np.isfinite(values[1]) else None,
        ci_upper=float(values[2]) if np.isfinite(values[2]) else None,
        status="COMPUTED" if np.isfinite(values).all() else "BOOTSTRAP_NOT_EVALUABLE",
        n_candidates=n_candidates, n_bootstrap=n_boot, invalid_replicates=int(boot["invalid_replicates"]),
        bootstrap_scope="fixed candidate identity draws within original folds; shared across quantities; no refits")


def validate_output_failure(failure, source, source_text):
    """Accept only the final duplicate input_hashes write after matrix completion."""
    trace = failure.get("traceback", "")
    expected = str(Path(source) / "input_hashes.json")
    frames = re.findall(r'File "([^"]*a2_residual_execution\.py)", line (\d+), in run', trace)
    if (failure.get("status") != "FAILED" or failure.get("command") != "run-packet" or not frames or
            "FileExistsError:" not in trace.splitlines()[-1] or expected not in trace.splitlines()[-1]):
        raise ValueError("A2RF_NOT_THE_OUTPUT_ONLY_FAILURE")
    filename, number = frames[-1]
    if Path(filename).resolve() != (Path(source) / "source/auditory_next/a2_residual_execution.py").resolve():
        raise ValueError("A2RF_FAILURE_SOURCE_SNAPSHOT")
    lines = source_text.splitlines()
    index = int(number) - 1
    if (not 0 <= index < len(lines) or "write_json" not in lines[index] or "input_hashes.json" not in lines[index] or
            "A2R_IMMUTABLE_DEPENDENCY_CHANGED" not in "\n".join(lines[:index]) or
            "fit_receipts.json" not in "\n".join(lines[index+1:])):
        raise ValueError("A2RF_NOT_FINAL_OUTPUT_WRITE")


def _read(path, hashes, *, expected=None, kind="json"):
    path = Path(path)
    before = digest(path)
    if expected is not None and before != expected:
        raise ValueError("A2RF_SOURCE_HASH_MISMATCH")
    if kind == "json":
        value = json.loads(path.read_text())
    elif kind == "pickle":
        with path.open("rb") as stream:
            value = pickle.load(stream)
    elif kind == "text":
        value = path.read_text()
    else:
        raise ValueError("A2RF_READ_KIND")
    if digest(path) != before:
        raise ValueError("A2RF_SOURCE_CHANGED_DURING_READ")
    hashes[str(path)] = before
    return value


def _private(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT / "private"):
        raise ValueError("A2RF_PRIVATE_SOURCE_REQUIRED")
    return path


def _catalog(path, hashes, expected):
    path = _private(path)
    hashes[str(path)] = digest(path)
    if hashes[str(path)] != expected:
        raise ValueError("A2RF_CATALOG_HASH")
    frame = pd.read_csv(path)
    own = frame[frame.packet.eq("A2") & frame.fit_stage.eq("real_train_only_audit")]
    if (len(own) != 20 or not own.fit_index.is_unique or not own.family.eq("ridge").all() or
            set(zip(own["mode"], own.outer_fold.astype(int))) != {(m, f) for m in MODES for f in range(5)}):
        raise ValueError("A2RF_ORIGINAL_TWENTY_RIDGE_ALLOWANCES")
    return own


def _check_axis(axis, scope):
    if set(axis["fit_groups"]) != set(scope.train_groups) or axis["scope_hash"] != scope.hash or not 1 <= axis["dimension"] <= 8:
        raise ValueError("A2RF_SAVED_AXIS_SCOPE")
    for key in ("scaler", "pca"):
        fitted = axis[key]
        if set(fitted.fit_groups_) != set(scope.train_groups) or fitted.scope_hash_ != scope.hash:
            raise ValueError("A2RF_SAVED_TRANSFORM_SCOPE")
    if (axis["dimension"] > axis["pca"].n_components_ or
            not all(np.isfinite(v).all() for v in (axis["scaler"].mean_, axis["scaler"].scale_,
                axis["pca"].mean_, axis["pca"].components_)) or np.any(axis["scaler"].scale_ <= 0)):
        raise ValueError("A2RF_SAVED_TRANSFORM_NONFINITE")


def run(config, registry, site, dest, public, report, task_plan=None, source_run="A2_residual_001"):
    require_slurm()
    dest, public, report = map(Path, (dest, public, report))
    for path, base in ((dest, "private"), (public, "results"), (report, "reports")):
        if not path.resolve().is_relative_to(ROOT / base / "auditory_next_v2"):
            raise ValueError("A2RF_OUTPUT_ROOT")
    if not source_run or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in source_run):
        raise ValueError("A2RF_EXPLICIT_SOURCE_RUN")
    source = ROOT / "private/auditory_next_v2" / source_run
    if source.resolve() == dest.resolve() or (source / "completion.json").exists():
        raise ValueError("A2RF_SOURCE_MUST_BE_FAILED_AND_PRESERVED")
    if (dest / "recovery_receipt.json").exists() or (dest / "completion.json").exists():
        raise FileExistsError("A2RF_DESTINATION_IMMUTABLE")
    hashes = {}
    start = _read(source / "start.json", hashes)
    failure = _read(source / "failure.json", hashes)
    for rel, expected in start["source_hashes"].items():
        path = (source / "source" / rel).resolve()
        if not path.is_relative_to(source / "source") or digest(path) != expected:
            raise ValueError("A2RF_ORIGINAL_CODE_SNAPSHOT_CHANGED")
        hashes[str(path)] = expected
    text = _read(source / "source/auditory_next/a2_residual_execution.py", hashes, kind="text")
    validate_output_failure(failure, source, text)
    original_config = yaml.safe_load(_read(source / "source/configs/auditory_next_v2.yaml", hashes, kind="text"))
    old_registry = yaml.safe_load(_read(source / "source/configs/auditory_next_sources_v2.yaml", hashes, kind="text"))
    if object_hash(original_config) != object_hash(config) or any(old_registry[k] != registry[k] for k in (
            "legacy_plan", "legacy_plan_sha256", "legacy_splits", "legacy_split_sha256", "preflight_run")):
        raise ValueError("A2RF_ESTIMATOR_OR_SOURCE_CONFIG_CHANGED")
    initial = _read(source / "input_hashes.json", hashes)
    for path, expected in initial.items():
        path = _private(path)
        if digest(path) != expected:
            raise ValueError("A2RF_INITIAL_INPUT_CHANGED")
        hashes[str(path)] = expected
    catalog_paths = [Path(p) for p in initial if Path(p).name == "TASK_PLAN.csv"]
    core_paths = [Path(p).parent for p in initial if Path(p).name == "completion.json"]
    support_paths = [Path(p).parent for p in initial if Path(p).name == "A2_overlap.json"]
    if len(catalog_paths) != 1 or len(core_paths) != 1 or len(support_paths) != 1:
        raise ValueError("A2RF_ORIGINAL_INPUT_MANIFEST")
    catalog = _catalog(catalog_paths[0], hashes, initial[str(catalog_paths[0])])
    # Recovery consumes no task allowance. The original catalog provides the
    # twenty already-consumed fit indices; no new plan or FINALIZE row is needed.
    support = support_paths[0]
    if str(support / "A2_overlap.json") not in initial or str(support / "A2_trial_draws.npy") not in initial:
        raise ValueError("A2RF_DIFFERENT_FROZEN_SUPPORT")
    overlap = _read(support / "A2_overlap.json", hashes)
    if _read(core_paths[0] / "completion.json", hashes)["status"] not in ("A2_CORE_RECORDED", "PASS"):
        raise ValueError("A2RF_ORIGINAL_CORE_GATE")
    planpath, splitpath = [_private(ROOT / registry[k]) for k in ("legacy_plan", "legacy_splits")]
    plan = _read(planpath, hashes, expected=registry["legacy_plan_sha256"])
    split = _read(splitpath, hashes, expected=registry["legacy_split_sha256"])
    gate = ROOT / "private/auditory_next_v2" / registry["preflight_run"]
    if _read(gate / "completion.json", hashes)["status"] != "PASS":
        raise ValueError("A2RF_S0_GATE")
    inventory = {r["path"]: r["sha256"] for r in _read(gate / "legacy_input_hashes.json", hashes)}
    scopes = _read(gate / "feature_scope_registry.json", hashes)
    records, receipts = [], []
    for mode in MODES:
        for fold in split["folds"]:
            number = int(fold["outer_fold"])
            folder, _, evidence, _ = _load_task(plan, planpath, fold, mode, scopes, inventory, hashes)
            if mode != "L0":
                checkpoint = folder / "encoder.pt"
                hashes[str(checkpoint)] = digest(checkpoint)
                if hashes[str(checkpoint)] != inventory.get(str(checkpoint)):
                    raise ValueError("A2RF_RELEVANT_CHECKPOINT_CHANGED")
            train = tuple(sorted(set(overlap["groups"]) & set(fold["train_groups"])))
            test = tuple(sorted(set(overlap["groups"]) & set(fold["test_groups"])))
            scope = FitScope(train, test_groups=test)
            axis = _read(source / f"{mode}_outer{number}_background_axis.pkl", hashes, kind="pickle")
            predictor = _read(source / f"{mode}_outer{number}_predictor.pkl", hashes, kind="pickle")
            details = _read(source / f"{mode}_outer{number}_pair_matrices.pkl", hashes, kind="pickle")
            target_axis = _read(core_paths[0] / f"{mode}_outer{number}_post_delta_axis.pkl", hashes, kind="pickle")
            _check_axis(axis, scope)
            _check_axis(target_axis, scope)
            if (predictor.alpha != 10. or predictor.n_training_candidates != len(train) or
                    np.shape(predictor.coefficient) != (axis["dimension"], target_axis["dimension"]) or
                    np.shape(predictor.center) != (axis["dimension"],) or
                    np.shape(predictor.target_center) != (target_axis["dimension"],) or
                    not all(np.isfinite(v).all() for v in (predictor.coefficient, predictor.center, predictor.target_center))):
                raise ValueError("A2RF_PERSISTED_PREDICTOR_SCHEMA")
            identity = validate_saved_details(details, test)
            with zipfile.ZipFile(folder / "features.npz") as archive:
                quality = "quality.npy" in archive.namelist()
            quality_status = "FIXED_FEATURE_QUALITY_ARRAY" if quality else QUALITY_UNAVAILABLE
            names = ["post_common_response", "pre_common_response", "pre_delta"] + (["quality_summary"] if quality else [])
            records.append(dict(mode=mode, outer_fold=number, details=details,
                quality_status=quality_status, background_components=names))
            allowance = catalog[catalog["mode"].eq(mode) & catalog.outer_fold.eq(number)].iloc[0]
            receipts.append(dict(mode=mode, outer_fold=number, status="REUSED_COMPLETED_FIT", alpha=10.,
                source_task_fit_index=int(allowance.fit_index), fit_scope=train, test_scope=test,
                encoder_scope=evidence, background_components=names, quality_status=quality_status,
                background_dimension=axis["scaler"].n_features_in_, target_dimension=target_axis["dimension"],
                **identity, new_readout_fits=0))
    aggregate, decomposition = reconstruct_aggregates(records)
    # These source summaries were written before the duplicate output failure.
    # Verify them against all twenty saved mathematical decompositions.
    for path in (source / "residual_inner_product_decomposition.parquet",
                 ROOT / "results/auditory_next_v2" / source_run / "residual_inner_product_decomposition.csv"):
        hashes[str(path)] = digest(path)
        saved = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        key = ["mode", "outer_fold", "term"]
        first, second = [table.sort_values(key).reset_index(drop=True) for table in (saved, decomposition)]
        if not first[key].equals(second[key]) or not np.allclose(first[["matched", "mismatched", "gain"]],
                second[["matched", "mismatched", "gain"]], rtol=1e-12, atol=1e-12):
            raise ValueError("A2RF_SOURCE_DECOMPOSITION_CHANGED")
    for path, expected in hashes.items():
        if digest(Path(path)) != expected:
            raise ValueError("A2RF_DEPENDENCY_CHANGED_DURING_FINALIZATION")
    write_json(dest / "source_file_hashes.json", hashes)
    write_json(dest / "reused_fit_receipts.json", receipts)
    receipt = dict(status="OUTPUT_FINALIZATION_REPAIRED", source_run=source_run,
        failure="FileExistsError at final exclusive input_hashes.json write after twenty completed fits",
        source_failure_hash=hashes[str(source / "failure.json")], source_snapshot_hash=object_hash(start["source_hashes"]),
        task_plan_hash=object_hash(task_plan) if task_plan is not None else None,
        new_task_allowances_consumed=0, reused_readout_fits=20, new_readout_fits=0,
        new_encoder_fits=0, new_scaler_fits=0, new_pca_fits=0, source_modified=False,
        provenance_limit="saved outputs receive their first complete digest manifest at recovery; original final expanded input manifest was not written")
    write_json(dest / "recovery_receipt.json", receipt)
    aggregate.to_csv(public / "residual_aggregate.csv", index=False)
    decomposition.to_csv(public / "residual_inner_product_decomposition.csv", index=False)
    decomposition.to_parquet(dest / "residual_inner_product_decomposition.parquet", index=False)
    (report / "A2_RESIDUAL_REPORT.md").write_text(
        "# A2 残差审计输出恢复\n\n原运行已完成四种表示、五个外折的20次alpha=10背景ridge，并保存每折predictor、background_axis和完整pair_matrices。"
        "随后重复独占写入input_hashes.json导致FileExistsError。此次仅修复输出终结：新增回归/PCA/scaler/encoder拟合均为0；原20次拟合保留在原任务预算。原失败目录完整保留。\n\n"
        "恢复程序核验原失败位置、原代码快照、初始依赖哈希及20个相关S0任务和15个encoder checkpoint；"
        "重新校验训练/测试scope、模型维度、每对候选四项内积恒等式及已存向量统计。原最终扩展输入清单未成功写入，因此完整输出摘要哈希首次在本次恢复建立，此限制保留在私有回执。\n\n"
        "Delta、P、R的cosine和内积按原外折匹配矩阵汇总；每折描述和全五折区间复用原seed及2000次候选身份抽样，重复身份不进入异候选参照。"
        "这些是fixed OOF区间，不包含模型重拟合。未定义bootstrap保留状态，不能填0。"
        "背景为post共同响应、pre共同响应和pre差异；固定quality数组缺失时明确保留缺失限制。"
        "本结果始终DIAGNOSTIC_ONLY，残差转正不替代未校正A2主终点，不构成刺激特异性或临床有效性证据。\n", encoding="utf-8")
    return finish(dest, public, dict(status="OUTPUT_FINALIZATION_REPAIRED", scientific_status="DIAGNOSTIC_ONLY",
        reused_readout_fits=20, new_readout_fits=0, encoder_fits=0, new_pca_fits=0, new_scaler_fits=0,
        modes=list(MODES), outer_folds=5, aggregate_rows=len(aggregate), decomposition_rows=len(decomposition),
        n_candidates=len(overlap["groups"]), quality_status=sorted({r["quality_status"] for r in receipts}),
        residual_primary=False, source_preserved=True, bootstrap_scope="fixed OOF; no refits"))
