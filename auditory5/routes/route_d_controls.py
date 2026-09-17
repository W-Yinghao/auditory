"""Prespecified D controls on immutable core projections; no encoder training."""

import json
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
import torch

from auditory5.contracts import FitScope
from auditory5.head_geometry import decompose_head
from auditory5.metrics import candidate_log_losses_bits
from auditory5.probes import fit_probe
from auditory5.provenance import ROOT, digest, object_hash, require_slurm, write_json
from auditory5.routes.route_d import choose_penalties, grouped_ridge_predict, _payload
from auditory5.statistics import paired_cluster_bootstrap


MODES = ("L0", "R_SUP", "R_SIM")
MAIN_MODELS = ("D1_C", "D2_CV", "D3_CVN")
ALL_MODELS = ("D0_mean", *MAIN_MODELS, "D4_CN", "D5_CFULL", "D7_CPRE", *["D6_CRANDOM_" + str(k) for k in range(20)])
VARIANTS = ("all_trials", "budget40_count_qc", "all_trials_count_qc")
NUISANCE_COLUMNS = ("log1p_min_accepted_class_count", "target_rejection_fraction")


def all_trial_means(z, y, groups, wanted):
    x, labels, identities = np.asarray(z, float), np.asarray(y), np.asarray(groups, str)
    if x.ndim != 2 or labels.shape != (len(x),) or identities.shape != labels.shape or not np.isfinite(x).all():
        raise ValueError("D_ALL_TRIAL_SHAPE")
    result = []
    for group in wanted:
        classes = []
        for label in (0, 1):
            mask = (identities == group) & (labels == label)
            if mask.sum() < 40:
                raise ValueError("D_ALL_TRIAL_SUPPORT: core eligibility floor remains 40/class")
            classes.append(x[mask].mean(axis=0))
        result.append(classes)
    return np.asarray(result)


def validate_projection(artifact, train, test):
    scope = FitScope(tuple(train), test_groups=tuple(test))
    if artifact["scope_hash"] != scope.hash or list(artifact["ids"]) != list(train) + list(test) or artifact["rank"] != 1:
        raise ValueError("D_PROJECTION_SCOPE: saved clinical projection does not match frozen partition")
    for name in ("null_pca", "full_pca", "pre_pca"):
        pca = artifact[name]
        if set(pca.fit_groups_) != set(train) or pca.scope_hash_ != scope.hash:
            raise ValueError("D_PROJECTION_LEAKAGE: PCA fitted outside clinical training identities")
    if len(artifact["random_bases"]) != 20:
        raise ValueError("D_RANDOM_CONTROL_SUPPORT")
    return scope


def sensitivity_features(payload, artifact, train, test, targets, *, all_trials, nuisance=None):
    """Apply original bases only; clinical scaling stays inside grouped ridge."""
    validate_projection(artifact, train, test)
    ids = list(train) + list(test)
    if not targets.index.is_unique or not set(ids) <= set(targets.index):
        raise ValueError("D_TARGET_SUPPORT: unique core targets required")
    if all_trials:
        summaries = all_trial_means(payload["post"], payload["y"], payload["groups"], ids)
        pre = all_trial_means(payload["pre"], payload["y"], payload["groups"], ids)
        delta = summaries - artifact["center"]
        basis = artifact["visible_basis"]
        null = delta - (delta @ basis) @ basis.T
        npca, fpca, ppca = artifact["null_pca"], artifact["full_pca"], artifact["pre_pca"]
        features = dict(C=np.asarray(artifact["features"]["C"]).copy(),
            V=(delta @ basis).reshape(len(ids), -1),
            N=((null - npca.mean_) @ npca.components_.T).reshape(len(ids), -1),
            FULL=((summaries - fpca.mean_) @ fpca.components_.T).reshape(len(ids), -1),
            PRE=((pre - ppca.mean_) @ ppca.components_.T).reshape(len(ids), -1))
        features.update({"RANDOM_" + str(k): (delta @ q).reshape(len(ids), -1) for k, q in enumerate(artifact["random_bases"])})
    else:
        features = {name: np.asarray(values).copy() for name, values in artifact["features"].items()}
    if nuisance is not None:
        if tuple(nuisance.columns) != NUISANCE_COLUMNS or not nuisance.index.is_unique:
            raise ValueError("D_NUISANCE_SCHEMA: exactly the two frozen count/QC columns required")
        features["C"] = np.c_[features["C"], nuisance.loc[ids].to_numpy(float)]
    if any(len(x) != len(ids) or not np.isfinite(x).all() for x in features.values()):
        raise ValueError("D_SENSITIVITY_FEATURES: aligned finite candidate summaries required")
    n = len(train)
    return dict(train={k: x[:n] for k, x in features.items()}, test={k: x[n:] for k, x in features.items()},
                y_train=targets.loc[train].to_numpy(float), y_test=targets.loc[test].to_numpy(float))


def count_qc_covariates(events, wanted):
    """Two fixed nuisance columns from original target-event bookkeeping only."""
    required = {"trial_id", "split_group_id", "event_kind", "event_literal", "accepted", "stimulus_local_id"}
    if not required <= set(events) or not events.trial_id.is_unique:
        raise ValueError("D_QC_SCHEMA: unique original target-event ledger required")
    rows = []
    for group in wanted:
        own = events[(events.split_group_id == group) & events.event_kind.eq("target") & events.event_literal.isin(["1", "2"])]
        accepted = own[own.accepted.fillna(False)]
        counts = [int(accepted.stimulus_local_id.eq(c).sum()) for c in (0, 1)]
        if not len(own) or min(counts) < 40 or sum(counts) != len(accepted):
            raise ValueError("D_QC_SUPPORT: unchanged clinical cohort requires 40 accepted trials/class")
        rows.append(dict(split_group_id=group, log1p_min_accepted_class_count=float(np.log1p(min(counts))),
                         target_rejection_fraction=float(1 - len(accepted) / len(own))))
    return pd.DataFrame(rows).set_index("split_group_id")[list(NUISANCE_COLUMNS)]


def fp32_invariance(payload, head, artifact, *, seed=20260917):
    """Every probability and projection operation below is float32 on CPU."""
    weight, bias = head.effective_linear_head()
    center, visible = np.asarray(artifact["center"]), np.asarray(artifact["visible_basis"])
    geometry = decompose_head(torch.as_tensor(weight), torch.as_tensor(bias), torch.as_tensor(center))
    stored_projector = visible @ visible.T
    projector_error = float(np.max(np.abs(geometry.p_visible.numpy() - stored_projector)))
    null_projector_error = float(np.max(np.abs(geometry.p_null.numpy() - (np.eye(len(center)) - stored_projector))))
    if geometry.rank != artifact["rank"] or max(projector_error, null_projector_error) >= 1e-10:
        raise ValueError("D_REFIT_PROJECTOR_MISMATCH: head does not reproduce saved row/null geometry")
    w, b, mu, u = [torch.as_tensor(value, dtype=torch.float32) for value in (weight, bias, center, visible)]
    real = np.asarray(payload["post"])
    if real.ndim != 2 or real.shape[1] != len(center) or not np.isfinite(real).all():
        raise ValueError("D_FP32_INPUT_SHAPE")

    def maximum(values):
        answer = 0.
        with torch.no_grad():
            for start in range(0, len(values), 2048):
                z = torch.as_tensor(values[start:start + 2048], dtype=torch.float32)
                reduced = mu + ((z - mu) @ u) @ u.T
                a, c = torch.softmax(z @ w.T + b, dim=1), torch.softmax(reduced @ w.T + b, dim=1)
                if not torch.isfinite(a).all() or not torch.isfinite(c).all():
                    raise ValueError("D_FP32_NUMERICAL_FAILURE")
                answer = max(answer, float(torch.max(torch.abs(a - c))))
        return answer

    observed = maximum(real)
    synthetic = maximum(center + np.random.default_rng(seed).normal(size=(128, len(center))))
    return dict(status="PASS" if max(observed, synthetic) <= 1e-6 else "FAIL",
                real_max_abs_probability_difference=observed, synthetic_max_abs_probability_difference=synthetic,
                threshold=1e-6, dtype="float32", real_trials=len(real), synthetic_trials=128,
                projector_difference_float64=projector_error, null_projector_difference_float64=null_projector_error,
                probability_mode="raw fixed linear head, as used to define D geometry", rank=geometry.rank, seed=seed)


def fit_null_probe(payload, artifact, train, test, *, seed=11):
    """New linear stimulus readout on fixed-head null; no clinical target used."""
    scope = validate_projection(artifact, train, test)
    group, labels = np.asarray(payload["groups"], str), np.asarray(payload["y"], int)
    post, center, visible = np.asarray(payload["post"], float), artifact["center"], artifact["visible_basis"]
    a, b = np.isin(group, train), np.isin(group, test)
    if not a.any() or not b.any():
        raise ValueError("D_NULL_PROBE_SUPPORT")
    # Retain the full original null coordinates; probe PCA is separately train-fit.
    delta = post - center
    null = delta - (delta @ visible) @ visible.T
    fitted = fit_probe(null[a], labels[a], group[a], scope, seed=seed, pca_max_dim=32)
    probabilities = fitted.predict(null[b])
    fitted.fit_scopes.update(encoder_scope="frozen outer encoder/head/null definition; conditional readout-only inner CV",
                            new_null_probe=True, original_null_feature_dimension=post.shape[1] - artifact["rank"],
                            upstream_inner_refitted=False)
    result = []
    for mode, p in probabilities.items():
        frame = pd.DataFrame(dict(trial_id=np.asarray(payload["trial_ids"])[b], split_group_id=group[b],
                                  stimulus_local_id=labels[b], probability_mode=mode, p0=p[:, 0], p1=p[:, 1]))
        result.append(frame)
    return fitted, pd.concat(result, ignore_index=True)


def _clinical_prediction(features, penalties, mode, outer_fold, variant, model, test):
    prediction = grouped_ridge_predict(features["train"], features["test"], features["y_train"], penalties)
    return [dict(mode=mode, outer_fold=outer_fold, variant=variant, model=model, split_group_id=group,
                 target=float(target), prediction=float(value), absolute_error=float(abs(target - value)))
            for group, target, value in zip(test, features["y_test"], prediction)]


def summarize_clinical(frame, original, *, seed=20260917):
    output = []
    for (mode, variant), rows in frame.groupby(["mode", "variant"]):
        errors = rows.pivot(index="split_group_id", columns="model", values="absolute_error")
        baseline = original[original["mode"].eq(mode)].pivot(index="split_group_id", columns="model", values="absolute_error")
        if set(errors.index) != set(baseline.index) or errors.isna().any().any():
            raise ValueError("D_CONTROL_PAIRED_SUPPORT: no candidate deletion or imputed predictions")
        for name, a, b in (("D2_minus_D3", "D2_CV", "D3_CVN"), ("D1_minus_D3", "D1_C", "D3_CVN")):
            ci = paired_cluster_bootstrap(errors[a], errors[b], errors.index, n_boot=2000, seed=seed)
            diffs = (errors[a] - errors[b]).to_numpy()
            loo = [(diffs.sum() - value) / (len(diffs) - 1) for value in diffs] if len(diffs) > 1 else [float(diffs.mean())]
            output.append(dict(mode=mode, variant=variant, comparison=name, baseline_MAE=float(errors[a].mean()),
                               augmented_MAE=float(errors[b].mean()), leave_one_out_gain_minimum=float(min(loo)),
                               leave_one_out_gain_maximum=float(max(loo)), **ci))
        for model in errors.columns:
            ci = paired_cluster_bootstrap(baseline.loc[errors.index, model], errors[model], errors.index, n_boot=2000, seed=seed)
            output.append(dict(mode=mode, variant=variant, comparison="original_budget_minus_variant", model=model,
                               original_MAE=float(baseline[model].mean()), variant_MAE=float(errors[model].mean()), **ci))
    return output


def _read_pickle(path, hashes):
    hashes[str(path)] = digest(path)
    with Path(path).open("rb") as stream:
        return pickle.load(stream)


def _representation(directory, plan, plan_path, support, hashes):
    """Validate the exact saved encoder and stimulus-probe scope before reuse."""
    tasks = [t for t in plan["tasks"] if t["name"] == directory.name]
    if len(tasks) != 1 or tasks[0]["branch"] != "all":
        raise ValueError("D_CONTROL_REPRESENTATION_TASK")
    task = tasks[0]
    files = [directory / name for name in ("features.npz", "feature_rows.parquet", "probe_post.pkl", "completion.json", "task.json")]
    if task["mode"] != "L0":
        files.append(directory / "encoder.pt")
    hashes.update({str(path): digest(path) for path in files})
    payload, head, completion = _payload(directory)
    stored = json.loads((directory / "task.json").read_text())
    fit_groups = sorted(set(task["fit_groups"]) & set(support.loc[support.general, "split_group_id"]))
    scope = FitScope(tuple(fit_groups), tuple(task["validation_groups"]), tuple(task["test_groups"]))
    if (any(stored.get(k) != v for k, v in task.items()) or stored.get("plan_hash") != digest(plan_path) or
            completion.get("plan_hash") != digest(plan_path) or completion.get("encoder_fit_scope_hash") != scope.hash or
            completion.get("task") != directory.name or set(head.fit_scopes["fit_groups"]) != set(fit_groups) or
            head.fit_scopes["scope_hash"] != scope.hash or set(head.scaler.fit_groups_) != set(fit_groups)):
        raise ValueError("D_CONTROL_REPRESENTATION_SCOPE")
    if task["mode"] != "L0":
        state = torch.load(directory / "encoder.pt", map_location="cpu", weights_only=False)
        encoder_scope = FitScope(**{k: tuple(v) for k, v in state["scope"].items()})
        if (encoder_scope.hash != scope.hash or state["scope_hash"] != scope.hash or state["scaler"]["scope_hash"] != scope.hash or
                set(state["scaler"]["fit_groups"]) != set(fit_groups) or state["mode"] != task["mode"] or
                state["metadata"]["config_hash"] != plan["config_hash"]):
            raise ValueError("D_CONTROL_ENCODER_SCOPE")
        del state
    rows = pd.read_parquet(directory / "feature_rows.parquet", columns=["trial_id", "record_id", "split_group_id", "stimulus_local_id"])
    if not rows.trial_id.is_unique or any(not np.array_equal(payload[key], rows[column].to_numpy())
                for key, column in (("trial_ids", "trial_id"), ("groups", "split_group_id"), ("y", "stimulus_local_id"))):
        raise ValueError("D_CONTROL_FEATURE_ALIGNMENT")
    widths = (400, 200) if task["mode"] == "L0" else (64, 64)
    if any(payload[window].shape != (len(rows), width) or not np.isfinite(payload[window]).all()
           for window, width in zip(("post", "pre"), widths)):
        raise ValueError("D_CONTROL_FEATURE_WIDTH")
    return payload, head, task


def _qc_events(config, split, support, wanted, hashes):
    base = ROOT / config["paths"]["private_relative"]
    selected = support[support.split_group_id.isin(wanted) & support[["general", "A", "B", "D"]].any(axis=1)]
    rows, sources = [], []
    columns = ["trial_id", "record_id", "split_group_id", "event_kind", "event_literal", "accepted", "stimulus_local_id"]
    for record in selected.to_dict("records"):
        folder = base / "data" / split["export_run"] / "P1_CAUSAL20" / record["record_id"]
        summary_path, events_path = folder / "summary.json", folder / "events.parquet"
        if digest(summary_path) != split["input_hashes"]["P1_CAUSAL20/" + record["record_id"]]:
            raise ValueError("D_CONTROL_EXPORT_CHANGED")
        manifest = json.loads(summary_path.read_text())
        if digest(events_path) != manifest["output_sha256"]["events.parquet"]:
            raise ValueError("D_CONTROL_EVENT_LEDGER_CHANGED")
        hashes.update({str(summary_path): digest(summary_path), str(events_path): digest(events_path)})
        if manifest["bank"] != "P1_CAUSAL20" or manifest["offline_record_qc"] is not True:
            raise ValueError("D_CONTROL_QC_PROCESSING_CONTRACT")
        sources.append({key: manifest[key] for key in ("record_id", "bank", "original_fs", "processed_fs",
            "offline_record_qc", "persistent_raw_flat_max_fraction", "filter_support_seconds", "startup_guard_seconds",
            "accepted", "target_events")})
        part = pd.read_parquet(events_path, columns=columns)
        if not part.split_group_id.eq(record["split_group_id"]).all():
            raise ValueError("D_CONTROL_EVENT_IDENTITY")
        rows.append(part)
    if not rows:
        raise ValueError("D_CONTROL_QC_SUPPORT")
    return pd.concat(rows, ignore_index=True), sources


def _core_targets(frame, mode, expected_ids):
    own = frame[frame["mode"].eq(mode)].copy()
    errors = own.pivot(index="split_group_id", columns="model", values="absolute_error")
    if set(errors.index) != set(expected_ids) or set(errors.columns) != set(ALL_MODELS) or errors.isna().any().any():
        raise ValueError("D_CONTROL_CORE_COHORT: complete unchanged D0-D7 candidate matrix required")
    if own.groupby("split_group_id").target.nunique().max() != 1:
        raise ValueError("D_CONTROL_CORE_TARGET_CONFLICT")
    targets = own.drop_duplicates("split_group_id").set_index("split_group_id").target
    if not np.isfinite(targets).all() or not targets.between(0, 100).all():
        raise ValueError("D_CONTROL_CORE_TARGET_RANGE")
    return own, targets


def _null_summary(frame, expected_ids, *, seed):
    losses, aggregate = [], []
    for calibration, rows in frame.groupby("probability_mode"):
        values = candidate_log_losses_bits(rows.stimulus_local_id.to_numpy(int), rows[["p0", "p1"]].to_numpy(),
                                          rows.split_group_id.to_numpy(str), rows.trial_id.to_numpy(str))
        if set(values) != set(expected_ids):
            raise ValueError("D_NULL_PROBE_INCOMPLETE: no subset scientific summary permitted")
        ids = sorted(values)
        loss = np.array([values[g] for g in ids])
        ci = paired_cluster_bootstrap(np.ones(len(ids)), loss, ids, seed=seed, n_boot=2000)
        aggregate.append(dict(probability_mode=calibration, balanced_null_ce_bits=1., ce_bits=float(loss.mean()),
                              J_bits=ci, probe="new linear scaler/PCA<=32/logistic on fixed null",
                              interpretation="negative linear decoding cannot establish stimulus independence"))
        losses.extend(dict(split_group_id=group, probability_mode=calibration, ce_bits=value) for group, value in values.items())
    return losses, aggregate


def run(config, split_run, representation_plan, modes, core_runs, output_dir):
    """Independent diagnostics on existing core runs; every item has its own state."""
    require_slurm()
    if not modes or len(set(modes)) != len(modes) or not set(modes) <= set(MODES):
        raise ValueError("D_CONTROL_MODES: unique L0/R_SUP/R_SIM required")
    base = ROOT / config["paths"]["private_relative"]
    plan_path = Path(representation_plan)
    plan_path = (plan_path if plan_path.is_absolute() else ROOT / plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    split_path = base / "splits" / split_run / "folds.json"
    split = json.loads(split_path.read_text())
    if plan["split_run"] != split_run or plan["split_hash"] != digest(split_path) or plan["config_hash"] != object_hash(config):
        raise ValueError("D_CONTROL_PLAN_MISMATCH")
    hashes = {str(plan_path): digest(plan_path), str(split_path): digest(split_path)}
    for relative, expected in plan["code_hashes"].items():
        path = Path(plan["source_snapshot"]) / relative
        if digest(path) != expected:
            raise ValueError("D_CONTROL_SOURCE_SNAPSHOT_CHANGED")
        hashes[str(path)] = expected
    support_path = split_path.parent / "support.parquet"
    hashes[str(support_path)] = digest(support_path)
    support = pd.read_parquet(support_path)
    expected_ids = set(support.loc[support.D, "split_group_id"])
    if len(expected_ids) < 30:
        raise ValueError("D_CONTROL_CLINICAL_SUPPORT")
    destination = Path(output_dir)
    destination = (destination if destination.is_absolute() else ROOT / destination).resolve()
    if not destination.is_relative_to((ROOT / "private").resolve()):
        raise ValueError("D controls containing individual data must stay private")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    public = ROOT / config["paths"]["aggregates_relative"] / destination.name
    public.mkdir(parents=True, exist_ok=False)
    seed = int(split["seed"])
    write_json(destination / "run_contract.json", dict(version="auditory5_D_controls_v1", modes=list(modes),
        plan_hash=digest(plan_path), split_hash=digest(split_path), source_hash=digest(Path(__file__)),
        inherited_core_hash=digest(Path(__file__).with_name("route_d.py")), variants=list(VARIANTS),
        nuisance_columns=list(NUISANCE_COLUMNS), new_encoder_jobs=0, endpoint="unchanged HA source-percentage MUSS",
        documentation_hash=digest(ROOT / "docs/auditory5_D_controls_v1.md"), null_probe="linear only; nonlinear untested"))
    states, errors, numerical, predictions, tuning, comparisons, null_aggregates, reference_reports = [], [], [], [], [], [], [], []

    def failed(control, mode, exc, outer_fold=None, inner_fold=None):
        state = "PENDING" if isinstance(exc, FileNotFoundError) else "FAIL"
        states.append(dict(control=control, mode=mode, outer_fold=outer_fold, inner_fold=inner_fold,
                           status=state, exception_type=type(exc).__name__))
        errors.append(dict(control=control, mode=mode, outer_fold=outer_fold, inner_fold=inner_fold, detail=str(exc)))

    try:
        events, qc_sources = _qc_events(config, split, support, expected_ids, hashes)
        nuisance = count_qc_covariates(events, sorted(expected_ids))
        nuisance.to_parquet(destination / "count_qc_covariates.parquet")
        write_json(destination / "count_qc_source_metadata.json", qc_sources)
        states.append(dict(control="count_QC_source", mode="all", status="PASS"))
    except Exception as exc:
        nuisance = None
        failed("count_QC_source", "all", exc)
    for mode in modes:
        try:
            if mode not in core_runs:
                raise FileNotFoundError("required completed private core run missing")
            core_dir = Path(core_runs[mode])
            core_dir = (core_dir if core_dir.is_absolute() else ROOT / core_dir).resolve()
            if not core_dir.is_relative_to((ROOT / "private").resolve()):
                raise ValueError("D core inputs must remain private")
            core_frame_path, core_summary_path = core_dir / "clinical_oof.parquet", core_dir / "aggregate.json"
            hashes.update({str(core_frame_path): digest(core_frame_path), str(core_summary_path): digest(core_summary_path)})
            core_report = json.loads(core_summary_path.read_text())
            if core_report["plan_hash"] != digest(plan_path):
                raise ValueError("D_CONTROL_CORE_PLAN_CHANGED")
            core_frame, targets = _core_targets(pd.read_parquet(core_frame_path), mode, expected_ids)
            reference_reports.extend(row for row in core_report["modes"] if row["mode"] == mode)
        except Exception as exc:
            failed("core_dependencies", mode, exc)
            continue
        mode_predictions, null_predictions = [], []
        for outer in split["folds"]:
            of = outer["outer_fold"]
            train, test = sorted(expected_ids & set(outer["train_groups"])), sorted(expected_ids & set(outer["test_groups"]))
            try:
                payload, head, task = _representation(plan_path.parent / "outputs" / f"outer{of}_all_{mode}",
                                                     plan, plan_path, support, hashes)
                if set(task["fit_groups"]) != set(outer["train_groups"]) or set(task["test_groups"]) != set(outer["test_groups"]):
                    raise ValueError("D_CONTROL_OUTER_ENCODER_LEAKAGE")
                artifact = _read_pickle(core_dir / f"{mode}_outer{of}_projection.pkl", hashes)
                validate_projection(artifact, train, test)
                inners = {variant: [] for variant in VARIANTS}
                inner_scope_hashes = []
                for inner in range(3):
                    valid = sorted(g for g in train if outer["D_inner_fold_by_group"][g] == inner)
                    fit = sorted(set(train) - set(valid))
                    saved = _read_pickle(core_dir / f"{mode}_outer{of}_inner{inner}_projection.pkl", hashes)
                    validate_projection(saved, fit, valid)
                    inner_scope_hashes.append(saved["scope_hash"])
                    if mode == "L0":
                        ipayload, ihead = payload, None
                    else:
                        ipayload, ihead, itask = _representation(plan_path.parent / "outputs" / f"D_outer{of}_inner{inner}_{mode}",
                                                                plan, plan_path, support, hashes)
                        if (set(itask["fit_groups"]) & (set(valid) | set(outer["test_groups"])) or
                                set(itask["fit_groups"]) != set(outer["train_groups"]) - set(valid) or
                                set(itask["validation_groups"]) != set(valid)):
                            raise ValueError("D_CONTROL_INNER_ENCODER_LEAKAGE")
                    for variant in VARIANTS:
                        if "count_qc" in variant and nuisance is None:
                            continue
                        features = sensitivity_features(ipayload, saved, fit, valid, targets,
                            all_trials=variant != "budget40_count_qc", nuisance=nuisance if "count_qc" in variant else None)
                        inners[variant].append(features)
                        with (destination / f"{mode}_outer{of}_inner{inner}_{variant}_features.pkl").open("xb") as stream:
                            pickle.dump(dict(features=features, train_ids=fit, test_ids=valid, scope_hash=saved["scope_hash"]), stream)
                    try:
                        if mode == "L0":
                            eligible = set(support.loc[support.general, "split_group_id"])
                            fitting = sorted((set(outer["train_groups"]) - set(valid)) & eligible)
                            mask = np.isin(ipayload["groups"], fitting)
                            ihead = fit_probe(ipayload["post"][mask], ipayload["y"][mask], ipayload["groups"][mask],
                                FitScope(tuple(fitting), tuple(valid), tuple(test)), seed=11, pca_max_dim=32)
                            with (destination / f"{mode}_outer{of}_inner{inner}_refit_stimulus_head.pkl").open("xb") as stream:
                                pickle.dump(ihead, stream)
                        check = fp32_invariance(ipayload, ihead, saved, seed=seed)
                        numerical.append(dict(mode=mode, outer_fold=of, inner_fold=inner, **check))
                        states.append(dict(control="FP32_invariance", mode=mode, outer_fold=of, inner_fold=inner, status=check["status"]))
                    except Exception as exc:
                        failed("FP32_invariance", mode, exc, of, inner)
                for variant in VARIANTS:
                    if len(inners[variant]) != 3:
                        states.append(dict(control=variant, mode=mode, outer_fold=of, status="PENDING"))
                        continue
                    features = sensitivity_features(payload, artifact, train, test, targets,
                        all_trials=variant != "budget40_count_qc", nuisance=nuisance if "count_qc" in variant else None)
                    with (destination / f"{mode}_outer{of}_{variant}_features.pkl").open("xb") as stream:
                        pickle.dump(dict(features=features, train_ids=train, test_ids=test, scope_hash=artifact["scope_hash"]), stream)
                    models = ALL_MODELS if variant == "all_trials" else MAIN_MODELS
                    for model in models:
                        penalties, evidence = choose_penalties(inners[variant], model)
                        mode_predictions.extend(_clinical_prediction(features, penalties, mode, of, variant, model, test))
                        tuning.append(dict(mode=mode, outer_fold=of, variant=variant, model=model, penalties=penalties,
                                           clinical_outer_scope_hash=artifact["scope_hash"],
                                           clinical_inner_scope_hashes=inner_scope_hashes, **evidence))
                    states.append(dict(control=variant, mode=mode, outer_fold=of, status="PASS"))
            except Exception as exc:
                failed("clinical_sensitivity_dependencies", mode, exc, of)
                continue
            try:
                check = fp32_invariance(payload, head, artifact, seed=seed)
                numerical.append(dict(mode=mode, outer_fold=of, inner_fold=None, **check))
                states.append(dict(control="FP32_invariance", mode=mode, outer_fold=of, inner_fold=None, status=check["status"]))
            except Exception as exc:
                failed("FP32_invariance", mode, exc, of)
            try:
                null_head, probabilities = fit_null_probe(payload, artifact, train, test, seed=11)
                probabilities["outer_fold"], probabilities["mode"] = of, mode
                probabilities.to_parquet(destination / f"{mode}_outer{of}_null_stimulus_predictions.parquet", index=False)
                with (destination / f"{mode}_outer{of}_null_stimulus_probe.pkl").open("xb") as stream:
                    pickle.dump(null_head, stream)
                null_predictions.append(probabilities)
                states.append(dict(control="null_linear_stimulus_probe", mode=mode, outer_fold=of, status="PASS"))
            except Exception as exc:
                failed("null_linear_stimulus_probe", mode, exc, of)
        if mode_predictions:
            mode_frame = pd.DataFrame(mode_predictions)
            predictions.extend(mode_predictions)
            for variant in VARIANTS:
                part = mode_frame[mode_frame.variant.eq(variant)]
                if part.empty:
                    continue
                try:
                    comparisons.extend(summarize_clinical(part, core_frame, seed=seed))
                except Exception as exc:
                    failed(variant + "_complete_cohort_summary", mode, exc)
        if null_predictions:
            try:
                frame = pd.concat(null_predictions, ignore_index=True)
                losses, report = _null_summary(frame, expected_ids, seed=seed)
                pd.DataFrame(losses).to_parquet(destination / f"{mode}_null_candidate_losses.parquet", index=False)
                null_aggregates.extend(dict(mode=mode, **row) for row in report)
            except Exception as exc:
                failed("null_linear_stimulus_probe_complete_cohort", mode, exc)
    for path, expected in hashes.items():
        if digest(path) != expected:
            failed("input_hashes", "all", ValueError("immutable dependency changed during controls"))
    pd.DataFrame(predictions).to_parquet(destination / "clinical_sensitivity_oof.parquet", index=False)
    write_json(destination / "tuning.json", tuning)
    write_json(destination / "input_hashes.json", hashes)
    write_json(destination / "errors.json", errors)
    write_json(public / "control_status.json", states)
    write_json(public / "fp32_invariance.json", numerical)
    write_json(public / "null_stimulus_probe.json", null_aggregates)
    pd.DataFrame(comparisons).to_csv(public / "clinical_sensitivities.csv", index=False)
    complete = bool(states) and all(row["status"] == "PASS" for row in states)
    summary = dict(stage="D_ADDITIONAL_CONTROLS", status="COMPLETED_DIAGNOSTICS" if complete else "PARTIAL_DIAGNOSTICS",
                   modes=list(modes), new_encoder_jobs=0, full_D_positive_screen_issued=False,
                   complete_D_claim=False, original_core_reference=reference_reports,
                   pending=["nonlinear null decoding untested (not required for the new-probe control)",
                            "independent replication; source-scale/EEG concurrence limitations remain"],
                   failed_or_pending_items=sum(row["status"] != "PASS" for row in states),
                   interpretation="subsequent prespecified sensitivities; original cores and endpoints unchanged")
    write_json(public / "summary.json", summary)
    write_json(destination / "completion.json", dict(status=summary["status"],
        output_hashes={path.name: digest(path) for path in destination.iterdir() if path.is_file()}))
    return summary
