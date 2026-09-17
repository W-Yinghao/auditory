"""Frozen-Ω A2 unadjusted readout runner; no encoder or residual-model fits.

One fold's candidate mean contrasts fit candidate-equal scaler -> PCA<=8.
Pre/post widths may differ: paired post-minus-pre is a difference of matching
STATISTICS, never subtraction/padding of different feature coordinates. The
common-response axis is fitted separately. PCA is not additionally whitened.
Real residual regression and the 300 synthetic mechanism draws remain pending.
"""
from dataclasses import asdict
import json
from pathlib import Path
import pickle

import numpy as np
import pandas as pd

from auditory5.contracts import FitScope
from auditory5.probes import CandidateTabularScaler, CandidateWeightedPCA
from auditory5.routes.a_matching import mean_matching_matrices, bootstrap_match
from auditory5.provenance import require_slurm
from .a2_overlap import TrialDraws, summarize_draws
from .provenance import ROOT, digest, object_hash, write_json, finish

MODES = ("L0", "R_RAND", "R_SUP", "R_SIM")
ENDPOINTS = ("post_delta", "pre_delta", "common_response")


class DegenerateAxis(ValueError):
    """A supported dataset can still lack a nonzero training contrast axis."""


def fit_summary_axis(training, groups, scope):
    """Fit only [repeat, training_candidate, half, feature] summary arrays."""
    x, groups = np.asarray(training, float), tuple(groups)
    if (x.ndim != 4 or x.shape[1] != len(groups) or x.shape[2] != 2 or
            len(groups) < 2 or len(set(groups)) != len(groups) or not np.isfinite(x).all()):
        raise ValueError("A2_TRAINING_SUMMARY_SHAPE")
    scope.assert_fit_groups(groups)
    means = x.mean(axis=(0, 2))
    scaler = CandidateTabularScaler().fit(means, groups, scope)
    pca = CandidateWeightedPCA(max_components=8).fit(scaler.transform(means), groups, scope)
    dimension = min(pca.n_components_, pca.rank_)
    if dimension < 1:
        raise DegenerateAxis("A2_ZERO_TRAINING_CONTRAST_RANK")
    return dict(scaler=scaler, pca=pca, dimension=int(dimension), rank=int(pca.rank_),
                scope_hash=scope.hash, fit_groups=groups, weighting="one mean contrast per training candidate",
                transform="candidate scaler then PCA<=8; no additional whitening")


def apply_summary_axis(values, axis):
    x = np.asarray(values, float)
    if x.ndim != 4 or x.shape[2] != 2 or not np.isfinite(x).all():
        raise ValueError("A2_EVALUATION_SUMMARY_SHAPE")
    transformed = axis["pca"].transform(axis["scaler"].transform(x.reshape(-1, x.shape[-1])))
    return transformed[:, :axis["dimension"]].reshape(*x.shape[:-1], axis["dimension"])


def paired_matching_summary(records, *, expected_folds=5, seed=20260917):
    """Paired fixed-OOF bootstrap of fold-local matrices, never pooled embeddings.

    All repetitions already averaged inside each matching matrix. Repeated
    bootstrap identities are excluded from the different-person reference by
    the existing audited a_matching implementation. Invalid degenerate draws
    remain counted; no zero fill and no regeneration until a favorable draw.
    """
    if len(records) != expected_folds or len({r["fold"] for r in records}) != expected_folds:
        raise ValueError("A2_INCOMPLETE_OUTER_MATRIX")
    ids = [list(r["groups"]) for r in records]
    flat = [group for own in ids for group in own]
    if len(set(flat)) != len(flat) or any(len(own) < 2 for own in ids):
        raise ValueError("A2_OUTER_CANDIDATE_OVERLAP_OR_SUPPORT")
    output = []
    for metric in ("cosine", "inner_product"):
        available = {}
        for endpoint in ENDPOINTS:
            matrices = [r.get("matrices", {}).get(endpoint, {}).get(metric) for r in records]
            if any(m is None for m in matrices):
                continue
            if any(np.asarray(m).shape != (len(g), len(g)) or not np.isfinite(m).all() for m, g in zip(matrices, ids)):
                continue
            available[endpoint] = matrices
        for endpoint, matrices in available.items():
            paired = available.get("pre_delta") if endpoint == "post_delta" else None
            result = bootstrap_match(matrices, ids, n_boot=2000, seed=seed, paired_matrices=paired)
            row = dict(endpoint=endpoint, metric=metric, estimate=result["estimate"], ci_lower=result["ci95"][0],
                ci_upper=result["ci95"][1], n_candidates=len(flat), n_bootstrap=2000,
                invalid_replicates=result["invalid_replicates"], valid_replicates=2000 - result["invalid_replicates"],
                bootstrap_scope="fixed_oof_no_refit; shared identity draws within original folds",
                comparison="matched_minus_different_identity", units="cosine_difference" if metric == "cosine" else "projected_inner_product")
            output.append(row)
            if paired is not None:
                output.append(dict(row, endpoint="post_minus_pre", estimate=result["paired_estimate"],
                    ci_lower=result["paired_ci95"][0], ci_upper=result["paired_ci95"][1],
                    invalid_replicates=result["paired_invalid_replicates"], valid_replicates=2000 - result["paired_invalid_replicates"],
                    comparison="T_post_minus_T_pre; separate training-only feature axes"))
    for row in output:
        finite = all(np.isfinite(row[key]) for key in ("estimate", "ci_lower", "ci_upper"))
        row["status"] = "COMPUTED" if finite else "BOOTSTRAP_NOT_EVALUABLE"
        for key in ("estimate", "ci_lower", "ci_upper"):
            if not np.isfinite(row[key]):
                row[key] = None
    return output


def _name(value):
    if not isinstance(value, str) or not value or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in value):
        raise ValueError("A2_EXPLICIT_RUN_NAME")
    return value


def _load_json(path, hashes, inventory=None):
    before = digest(path)
    if inventory is not None and inventory.get(str(path)) != before:
        raise ValueError("A2_FROZEN_SOURCE_HASH")
    value = json.loads(path.read_text())
    if digest(path) != before:
        raise ValueError("A2_SOURCE_CHANGED_DURING_READ")
    hashes[str(path)] = before
    return value


def _check(path, hashes, inventory=None):
    current = digest(path)
    if inventory is not None and inventory.get(str(path)) != current:
        raise ValueError("A2_FROZEN_SOURCE_HASH")
    hashes[str(path)] = current


def _load_task(plan, planpath, fold, mode, scope_registry, inventory, hashes):
    tasks = [t for t in plan["tasks"] if t["stage"] == "outer" and t["branch"] == "all" and
             t["outer_fold"] == fold["outer_fold"] and t["mode"] == mode]
    if len(tasks) != 1:
        raise ValueError("A2_EXACT_OUTER_TASK_REQUIRED")
    task = tasks[0]
    name = _name(task["name"])
    directory = planpath.parent / "outputs" / name
    evidence = [row for row in scope_registry if row["task"] == name]
    if len(evidence) != 1 or evidence[0]["status"] != "PASS":
        raise ValueError("A2_S0_SCOPE_REGISTRY")
    evidence = evidence[0]
    if (set(task["fit_groups"]) != set(fold["train_groups"]) or set(task["test_groups"]) != set(fold["test_groups"]) or
            evidence["stage"] != "outer" or evidence["branch"] != "all" or evidence["mode"] != mode or
            evidence["outer_fold"] != fold["outer_fold"] or evidence["inner_fold"] is not None or
            not set(evidence["fit_groups"]) <= set(fold["train_groups"]) or
            set(evidence["test_groups"]) != set(fold["test_groups"]) or evidence["validation_groups"]):
        raise ValueError("A2_ENCODER_SCOPE_MISMATCH")
    encoder_scope = FitScope(tuple(evidence["fit_groups"]), test_groups=tuple(evidence["test_groups"]))
    done = _load_json(directory / "completion.json", hashes, inventory)
    submitted = _load_json(directory / "task.json", hashes, inventory)
    if (done["status"] != "PASS" or done["plan_hash"] != digest(planpath) or done["task"] != name or
            done["encoder_fit_scope_hash"] != encoder_scope.hash or submitted["plan_hash"] != digest(planpath) or
            any(submitted.get(k) != v for k, v in task.items())):
        raise ValueError("A2_TASK_RECEIPT_MISMATCH")
    for filename in ("features.npz", "feature_rows.parquet"):
        _check(directory / filename, hashes, inventory)
    rows = pd.read_parquet(directory / "feature_rows.parquet", columns=["trial_id", "split_group_id", "stimulus_local_id"])
    if not rows.trial_id.is_unique:
        raise ValueError("A2_DUPLICATE_FEATURE_ROW")
    return directory, rows, evidence, encoder_scope.hash


def run(config, registry, site, dest, public, report, support_run):
    require_slurm()
    dest, public, report = map(Path, (dest, public, report))
    if not dest.resolve().is_relative_to(ROOT / "private/auditory_next_v2"):
        raise ValueError("A2_PRIVATE_OUTPUT_REQUIRED")
    if (not public.resolve().is_relative_to(ROOT / "results/auditory_next_v2") or
            not report.resolve().is_relative_to(ROOT / "reports/auditory_next_v2")):
        raise ValueError("A2_PUBLIC_OUTPUT_ROOT")
    if any((dest / name).exists() for name in ("completion.json", "A2_definition.json")):
        raise FileExistsError("A2_RUN_ALREADY_STARTED")
    support_run = _name(support_run or registry["support_run"])
    support_dir = ROOT / "private/auditory_next_v2" / support_run
    hashes = {}
    completion = _load_json(support_dir / "completion.json", hashes)
    definition = _load_json(support_dir / "support_definition.json", hashes)
    if completion["status"] != "PASS" or definition.get("frozen_before_features") is not True:
        raise ValueError("A2_SUPPORT_FREEZE_GATE")
    # The support completion records the run name; its frozen definition binds
    # the exact gate completion hash without duplicating that name.
    gate = ROOT / "private/auditory_next_v2" / _name(completion["source_gate"])
    gate_done = _load_json(gate / "completion.json", hashes)
    if gate_done["status"] != "PASS" or digest(gate / "completion.json") != definition["source_gate_hash"]:
        raise ValueError("A2_PREFLIGHT_GATE")
    inventory = {row["path"]: row["sha256"] for row in _load_json(gate / "legacy_input_hashes.json", hashes)}
    scopes = _load_json(gate / "feature_scope_registry.json", hashes)
    planpath, splitpath = ROOT / registry["legacy_plan"], ROOT / registry["legacy_splits"]
    plan, split = _load_json(planpath, hashes, inventory), _load_json(splitpath, hashes, inventory)
    if digest(planpath) != registry["legacy_plan_sha256"] or digest(splitpath) != registry["legacy_split_sha256"] or digest(splitpath) != definition["fold_hash"]:
        raise ValueError("A2_PLAN_SPLIT_DEFINITION")
    _check(support_dir / "A2_overlap.pkl", hashes)
    with (support_dir / "A2_overlap.pkl").open("rb") as stream:
        frozen = pickle.load(stream)  # trusted restricted artifact from this project's support gate
    overlap_document = _load_json(support_dir / "A2_overlap.json", hashes)
    if object_hash(asdict(frozen)) != object_hash(overlap_document):
        raise ValueError("A2_FROZEN_PICKLE_DOCUMENT_MISMATCH")
    write_json(dest / "A2_definition.json", dict(overlap_definition_hash=frozen.definition_hash,
        omega=frozen.omega, q=frozen.cell_weights, support_status=frozen.status, support_run=support_run,
        main="unadjusted post conditional difference; R_SIM", transforms="candidate means -> scaler -> PCA<=8; no whitening",
        paired_pre="difference of fold-local matching statistics, never feature subtraction",
        modes=list(MODES), clinical_inputs=False, new_encoder_fits=0, residual_controls="NOT_RUN"))
    if not frozen.groups:
        write_json(dest / "input_hashes.json", hashes)
        pd.DataFrame(columns=["mode", "endpoint", "metric", "estimate", "ci_lower", "ci_upper", "n_candidates", "status"]).to_csv(
            public / "repeatability_aggregate.csv", index=False)
        (report / "A2_REPORT.md").write_text("# A2 support insufficient\n\nThe frozen metadata design has no eligible candidate. "
            "No quota was relaxed, no feature or model was evaluated, and no scientific negative result is inferred.\n", encoding="utf-8")
        return finish(dest, public, dict(status="SUPPORT_INSUFFICIENT", implementation_status="PASS",
            support_status="INSUFFICIENT", control_status="MISSING", scientific_status="NOT_EVALUABLE",
            candidates=0, omega=frozen.omega, new_encoder_fits=0, new_readout_fits=0, results=[]))
    draw_definition = _load_json(support_dir / "A2_draw_definition.json", hashes)
    _check(support_dir / "A2_trial_draws.npy", hashes)
    if (draw_definition["definition_hash"] != frozen.definition_hash or tuple(draw_definition["omega"]) != frozen.omega or
            tuple(draw_definition["groups"]) != frozen.groups or tuple(draw_definition["cell_weights"]) != frozen.cell_weights or
            draw_definition["seed"] != 20260917):
        raise ValueError("A2_DRAW_FREEZE_MISMATCH")
    draws = TrialDraws(frozen.groups, frozen.omega, frozen.cell_weights,
        np.load(support_dir / "A2_trial_draws.npy", allow_pickle=False), frozen.definition_hash, int(draw_definition["seed"]))
    if draws.trial_ids.shape != (20, len(frozen.groups), 2, 2, len(frozen.omega), 6):
        raise ValueError("A2_SAVED_DRAW_SHAPE")
    # Verify every frozen trial's metadata at each feature scope; never relabel.
    trial_metadata = {row.trial_id: (row.group, row.label) for row in frozen.trials}
    expected_ids = set(draws.trial_ids.ravel())
    if not expected_ids <= set(trial_metadata):
        raise ValueError("A2_DRAW_OUTSIDE_FROZEN_POOL")
    trial_records = {row.trial_id: row for row in frozen.trials}
    for repeat in range(20):
        for index, group in enumerate(frozen.groups):
            for half in range(2):
                for label in range(2):
                    selected = draws.trial_ids[repeat, index, half, label]
                    if len(set(selected.ravel())) != selected.size or len({trial_records[t].block for t in selected.ravel()}) < 3:
                        raise ValueError("A2_SAVED_DRAW_DUPLICATE_OR_BLOCK_SUPPORT")
                    for cell_index, cell in enumerate(frozen.omega):
                        if any((trial_records[t].group, trial_records[t].half, trial_records[t].label, trial_records[t].cell) !=
                               (group, half, label, cell) for t in selected[cell_index]):
                            raise ValueError("A2_SAVED_DRAW_ROLE_MISMATCH")
    aggregates, diagnostics, fit_receipts = [], [], []
    for mode in MODES:
        fold_records = []
        for fold in split["folds"]:
            train = tuple(sorted(set(frozen.groups) & set(fold["train_groups"])))
            test = tuple(sorted(set(frozen.groups) & set(fold["test_groups"])))
            number = int(fold["outer_fold"])
            record = dict(fold=number, groups=test, matrices={})
            fold_records.append(record)
            if len(train) < 2 or len(test) < 2:
                diagnostics.append(dict(mode=mode, fold=number, endpoint="all", status="DESCRIPTIVE_FOLD_SUPPORT_INSUFFICIENT",
                                        train_candidates=len(train), test_candidates=len(test)))
                continue
            scope = FitScope(train, test_groups=test)
            folder, rows, evidence, encoder_hash = _load_task(plan, planpath, fold, mode, scopes, inventory, hashes)
            with np.load(folder / "features.npz", allow_pickle=False) as arrays:
                trial_ids = arrays["trial_ids"].astype(str)
                groups = arrays["groups"].astype(str)
                labels = arrays["y"]
                if (not np.array_equal(trial_ids, rows.trial_id.to_numpy(str)) or
                        not np.array_equal(groups, rows.split_group_id.to_numpy(str)) or
                        not np.array_equal(labels, rows.stimulus_local_id.to_numpy(int))):
                    raise ValueError("A2_FEATURE_LEDGER_ALIGNMENT")
                lookup = {tid: (group, int(label)) for tid, group, label in zip(trial_ids, groups, labels)}
                if any(lookup.get(tid) != trial_metadata[tid] for tid in expected_ids):
                    raise ValueError("A2_FROZEN_EVENT_FEATURE_ALIGNMENT")
                for window in ("post", "pre"):
                    features = arrays[window]
                    if list(features.shape) != evidence["feature_shapes"][window]:
                        raise ValueError("A2_PREFLIGHT_FEATURE_SHAPE")
                    means = summarize_draws(features, trial_ids, draws, feature_scope_id=encoder_hash)
                    by_group = {group: i for i, group in enumerate(means["groups"])}
                    train_index, test_index = [by_group[g] for g in train], [by_group[g] for g in test]
                    names = [(window + "_delta", means["delta"])]
                    if window == "post":
                        names.append(("common_response", means["common_response"]))
                    for endpoint, values in names:
                        try:
                            axis = fit_summary_axis(values[:, train_index], train, scope)
                        except DegenerateAxis:
                            diagnostics.append(dict(mode=mode, fold=number, endpoint=endpoint, status="ZERO_TRAINING_AXIS",
                                                    train_candidates=len(train), test_candidates=len(test)))
                            continue
                        transformed = apply_summary_axis(values[:, test_index], axis)
                        matrices = mean_matching_matrices(transformed[:, :, 0], transformed[:, :, 1])
                        record["matrices"][endpoint] = matrices
                        with (dest / f"{mode}_outer{number}_{endpoint}_axis.pkl").open("xb") as stream:
                            pickle.dump(axis, stream)
                        diag = dict(mode=mode, fold=number, endpoint=endpoint, dimension=axis["dimension"], rank=axis["rank"],
                            train_candidates=len(train), test_candidates=len(test),
                            zero_norm_vectors=matrices["undefined_zero_norm_count"], norms=matrices["norm_summary"],
                            status="PASS" if matrices["undefined_zero_norm_count"] == 0 else "UNDEFINED_TEST_COSINE")
                        diagnostics.append(diag)
                        fit_receipts.append(dict(diag, fit_scope=asdict(scope), scope_hash=scope.hash,
                            encoder_scope_hash=encoder_hash, task=folder.name, source_feature_hash=hashes[str(folder / "features.npz")]))
            with (dest / f"{mode}_outer{number}_matching_matrices.pkl").open("xb") as stream:
                pickle.dump(record, stream)
        if all(len(row["groups"]) >= 2 for row in fold_records):
            measurements = paired_matching_summary(fold_records)
        else:
            measurements = []
        for row in measurements:
            aggregates.append(dict(mode=mode, support_status=frozen.status, primary=mode == "R_SIM" and row["endpoint"] == "post_delta" and row["metric"] == "cosine", **row))
    for path, old_hash in hashes.items():
        if digest(Path(path)) != old_hash:
            raise ValueError("A2_IMMUTABLE_DEPENDENCY_CHANGED")
    write_json(dest / "input_hashes.json", hashes)
    write_json(dest / "fit_receipts.json", fit_receipts)
    write_json(dest / "fold_diagnostics.json", diagnostics)
    pd.DataFrame(aggregates).to_csv(public / "repeatability_aggregate.csv", index=False)
    write_json(public / "fold_diagnostics.json", diagnostics)
    required = {(mode, endpoint, "cosine") for mode in MODES for endpoint in (*ENDPOINTS, "post_minus_pre")}
    completed = {(r["mode"], r["endpoint"], r["metric"]) for r in aggregates if r["status"] == "COMPUTED"}
    main = next((r for r in aggregates if r["primary"] and r["status"] == "COMPUTED"), None)
    pending = ["real Delta/P/residual background-regression audit", "300 shared-draw synthetic residual mechanisms",
               "no independent confirmation; already explored cohort"]
    if not required <= completed:
        pending.append("at least one required fold-local matching endpoint is not evaluable")
    summary = dict(stage="A2_FROZEN_OVERLAP_UNADJUSTED_CORE", status="A2_CORE_RECORDED",
        implementation_status="PASS", support_status=frozen.status, control_status="MISSING",
        scientific_status="NOT_EVALUABLE",
        candidates=len(frozen.groups), omega=frozen.omega, cell_weights=frozen.cell_weights,
        core_matrix_complete=required <= completed, results=aggregates, pending=pending,
        overlap_definition_hash=frozen.definition_hash, bootstrap_scope="fixed_oof_no_refit", bootstrap_seed=20260917,
        main_threshold_met_before_missing_controls=(None if main is None else
            bool(frozen.status == "SUFFICIENT_FOR_SCREEN" and main["estimate"] >= .05 and main["ci_lower"] > 0)),
        new_encoder_fits=0, new_readout_fits=0, fitted_summary_axes=len(fit_receipts), clinical_inputs=False,
        pre_width_handling="separate training-only axes; paired difference of T statistics, no feature padding")
    (report / "A2_REPORT.md").write_text("# A2 frozen-overlap unadjusted core\n\n"
        "The selected Omega, uniform cell weights and 20 trial draws were reused without new support selection. "
        "Each outer fold fitted candidate-equal scaler/PCA axes only on qualified training candidates. "
        "Post and pre may have different raw widths; post-minus-pre is a paired difference of their cosine matching statistics. "
        "The common response has its own training axis and is not called pure artifact. "
        "No embeddings were pooled across fold coordinates. All bootstrap intervals condition on frozen OOF matrices; "
        "invalid identity-resampling draws remain counted, never zero-filled. "
        "Public repeatability and fold-diagnostic files contain aggregates only. Individual matrices/fit scopes stay private.\n\n"
        "Real background-residual regression and its 300 shared-draw synthetic audit are NOT_RUN here. "
        "A positive corrected residual would not replace the unadjusted primary. "
        "This is an interim core record, not a completed A2 positive screen.\n", encoding="utf-8")
    return finish(dest, public, summary)
