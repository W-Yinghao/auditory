"""B core on frozen outer-fold features; no new B measurement/tuning rules.

Inner CV refits the inherited context/EEG transforms and heads, not upstream
encoders. Different outer-fold feature coordinates are never fitted together.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import pickle

import numpy as np
import pandas as pd

from auditory5.contracts import FitScope
from auditory5.provenance import ROOT, digest, object_hash, require_slurm, write_json
from auditory5.routes.route_b import (CORE_MODELS, CONTEXT_COLUMNS, history_eligible,
    select_common_support, fit_history_readouts, _summaries)


MODES = ("R_SIM", "R_SUP", "R_RAND")
ROW_COLUMNS = ("trial_id", "record_id", "candidate_id", "split_group_id", "segment_id",
               "onset_sample", "stimulus_local_id", "accepted", "event_literal", "previous_code",
               "previous_event_id", "previous_gap_s", "history_target", "segment_position_fraction",
               "time_block_id")
PENDING = ("early_late_window_diagnostics", "quality_covariate_sensitivity",
           "within-candidate circular-shift diagnostic", "replication seeds",
           "previous-response checks do not eliminate all physiological/artifact residuals")


def validate_feature_ledger(payload, rows, support=None):
    """Validate complete pre-existing accepted features without selecting on labels."""
    if rows.empty or any(c not in rows for c in ROW_COLUMNS) or not rows.trial_id.is_unique:
        raise ValueError("B_FEATURE_LEDGER: complete unique feature-row schema required")
    if any(c in rows for c in ("MUSS", "MUSS_source_percentage", "age_months", "duration_months",
                                "better_ear_4freq_source_units")):
        raise ValueError("B_CLINICAL_FIELDS_FORBIDDEN")
    nonnullable = [c for c in ROW_COLUMNS if c not in
                   ("previous_code", "previous_event_id", "previous_gap_s", "history_target")]
    if rows[nonnullable].isna().any().any() or not rows.accepted.eq(True).all():
        raise ValueError("B_FEATURE_LEDGER: only complete accepted rows belong in encoder features")
    for key, column in (("trial_ids", "trial_id"), ("groups", "split_group_id"), ("y", "stimulus_local_id")):
        if key not in payload or not np.array_equal(payload[key], rows[column].to_numpy()):
            raise ValueError("B_FEATURE_ALIGNMENT: feature IDs/groups/labels must exactly match row order")
    for window in ("pre", "post"):
        values = np.asarray(payload.get(window))
        if values.shape != (len(rows), 64) or not np.isfinite(values).all():
            raise ValueError("B_FEATURE_DIMENSION: finite pre and post features must each be [trials,64]")
    if support is not None:
        expected = support[support[["general", "A", "B", "D"]].any(axis=1)]
        if not expected.record_id.is_unique or set(rows.record_id) != set(expected.record_id):
            raise ValueError("B_FEATURE_COVERAGE: full frozen representation record set required")
        for record in expected.to_dict("records"):
            own = rows[rows.record_id.eq(record["record_id"])]
            if (len(own) != record["accepted_P1"] or not own.candidate_id.eq(record["candidate_id"]).all() or
                    not own.split_group_id.eq(record["split_group_id"]).all()):
                raise ValueError("B_FEATURE_COVERAGE: accepted record counts or identity assignments changed")
    return rows[list(ROW_COLUMNS)].copy().reset_index(drop=True)


def validate_encoder_scope(checkpoint, task, scope, config_hash):
    """Inspect the actual checkpoint's encoder/scaler scopes, not only its filename."""
    stored_scope = FitScope(**{key: tuple(value) for key, value in checkpoint["scope"].items()})
    metadata, scaler = checkpoint["metadata"], checkpoint["scaler"]
    if (checkpoint.get("version") != "auditory5_training_v2" or checkpoint.get("mode") != task["mode"] or
            checkpoint.get("seed") != task["seed"] or stored_scope.hash != scope.hash or
            checkpoint.get("scope_hash") != scope.hash or scaler.get("scope_hash") != scope.hash or
            metadata.get("scope_hash") != scope.hash or set(scaler["fit_groups"]) != set(scope.train_groups) or
            set(metadata["train_groups"]) != set(scope.train_groups) or metadata.get("config_hash") != config_hash or
            metadata.get("input_channels") != 20 or metadata.get("input_time_samples") != 100):
        raise ValueError("B_ENCODER_SCOPE_MISMATCH: checkpoint/scaler scope or input contract differs")
    return dict(scope_hash=scope.hash, train_groups=list(scope.train_groups), test_groups=list(scope.test_groups),
                mode=task["mode"], seed=int(task["seed"]), scaler_scope_hash=scaler["scope_hash"],
                input_channels=20, input_time_samples=100)


def validate_original_history(rows, original_rows):
    """Check copied history against the accepted slice of the original event ledger."""
    original = original_rows.loc[original_rows.accepted.eq(True), list(ROW_COLUMNS)]
    if not original.trial_id.is_unique or set(rows.trial_id) != set(original.trial_id):
        raise ValueError("B_ORIGINAL_EVENT_MISMATCH: accepted original trial set differs")
    a = rows[list(ROW_COLUMNS)].sort_values("trial_id").reset_index(drop=True)
    b = original.sort_values("trial_id").reset_index(drop=True)
    # Concatenated parquet ledgers may represent nullable numeric columns with
    # different dtypes; values and missingness must still be exactly equivalent.
    same = a.eq(b) | (a.isna() & b.isna())
    if not same.fillna(False).to_numpy(bool).all():
        raise ValueError("B_ORIGINAL_EVENT_MISMATCH: stored pre-QC history or provenance changed")


@dataclass
class HistoryFeatures:
    rows: pd.DataFrame
    pre: np.ndarray
    post: np.ndarray
    previous_post: np.ndarray
    ledger_indices: np.ndarray
    previous_indices: np.ndarray

    def model_features(self, *, previous=False):
        values = dict(B0_context_linear=None, B0_context_spline=None, B1_pre=self.pre,
                      B2_post=self.post, B3_pre_post=np.c_[self.pre, self.post])
        if previous:
            values.update(B4_previous=self.previous_post, B5_previous_post=np.c_[self.previous_post, self.post])
        return values


def build_history_features(payload, rows, record_ids):
    """Previous lookup uses the same original record's entire accepted ledger."""
    rows = validate_feature_ledger(payload, rows)
    selected = np.flatnonzero(history_eligible(rows) & rows.record_id.isin(record_ids).to_numpy())
    current = rows.iloc[selected].reset_index(drop=True)
    lookup = {(record, trial): i for i, (record, trial) in enumerate(zip(rows.record_id, rows.trial_id))}
    global_ids = set(rows.trial_id)
    previous = np.full(len(current), -1, int)
    for i, row in enumerate(current.to_dict("records")):
        previous_id = row["previous_event_id"]
        if pd.isna(previous_id):
            raise ValueError("B_HISTORY_SCHEMA: known history must retain its original preceding event ID")
        index = lookup.get((row["record_id"], previous_id), -1)
        if index < 0 and previous_id in global_ids:
            raise ValueError("B_PREVIOUS_RECORD_MISMATCH: no cross-record previous feature substitution")
        if index >= 0:
            prior = rows.iloc[index]
            if (prior.segment_id != row["segment_id"] or prior.split_group_id != row["split_group_id"] or
                    prior.candidate_id != row["candidate_id"] or prior.onset_sample >= row["onset_sample"] or
                    prior.event_literal != row["previous_code"]):
                raise ValueError("B_PREVIOUS_HISTORY_MISMATCH: stored predecessor provenance is inconsistent")
        previous[i] = index
    before = np.full((len(current), 64), np.nan, dtype=np.float32)
    available = previous >= 0
    before[available] = payload["post"][previous[available]]
    return HistoryFeatures(current, np.asarray(payload["pre"])[selected].copy(),
                           np.asarray(payload["post"])[selected].copy(), before, selected, previous)


def _load_fold(plan, plan_path, fold, mode, support, original_rows):
    name = f'outer{fold["outer_fold"]}_all_{mode}'
    tasks = [task for task in plan["tasks"] if task["name"] == name]
    if len(tasks) != 1:
        raise FileNotFoundError("B_REQUIRED_ENCODER_TASK_MISSING")
    task = tasks[0]
    if (task["branch"] != "all" or task["mode"] != mode or task["stage"] != "outer" or task["inner_fold"] is not None or
            set(task["fit_groups"]) != set(fold["train_groups"]) or set(task["test_groups"]) != set(fold["test_groups"]) or
            task["validation_groups"]):
        raise ValueError("B_ENCODER_TASK_MISMATCH: correct outer all-channel task required")
    folder = plan_path.parent / "outputs" / name
    paths = [folder / f for f in ("task.json", "completion.json", "features.npz", "feature_rows.parquet", "encoder.pt")]
    if not all(path.is_file() for path in paths):
        raise FileNotFoundError("B_REQUIRED_ENCODER_OUTPUT_MISSING")
    hashes = {str(path): digest(path) for path in paths}
    stored_task = json.loads((folder / "task.json").read_text())
    done = json.loads((folder / "completion.json").read_text())
    fit_groups = sorted(set(task["fit_groups"]) & set(support.loc[support.general, "split_group_id"]))
    encoder_scope = FitScope(tuple(fit_groups), test_groups=tuple(task["test_groups"]))
    if (any(stored_task.get(k) != v for k, v in task.items()) or stored_task.get("plan_hash") != digest(plan_path) or
            done.get("status") != "PASS" or done.get("plan_hash") != digest(plan_path) or done.get("task") != name or
            done.get("branch") != "all" or done.get("mode") != mode or done.get("encoder_fit_scope_hash") != encoder_scope.hash):
        raise ValueError("B_ENCODER_COMPLETION_MISMATCH")
    import torch
    checkpoint = torch.load(folder / "encoder.pt", map_location="cpu", weights_only=False)
    evidence = validate_encoder_scope(checkpoint, task, encoder_scope, plan["config_hash"])
    del checkpoint
    raw_rows = pd.read_parquet(folder / "feature_rows.parquet")
    with np.load(folder / "features.npz", allow_pickle=False) as arrays:
        payload = {key: arrays[key].copy() for key in ("pre", "post", "trial_ids", "groups", "y")}
    rows = validate_feature_ledger(payload, raw_rows, support)
    validate_original_history(rows, original_rows)
    if not set(rows.split_group_id) <= set(fold["train_groups"]) | set(fold["test_groups"]):
        raise ValueError("B_FEATURE_SCOPE_MISMATCH: undeclared identity group in ledger")
    return payload, rows, evidence, hashes


def fit_outer_history(features, scope, *, seed):
    """One fold in its own feature coordinates; inherit all frozen B selection."""
    rows = features.rows
    train = np.flatnonzero(rows.split_group_id.isin(scope.train_groups))
    test = np.flatnonzero(rows.split_group_id.isin(scope.test_groups))
    if not len(train):
        return {}, [dict(analysis_set="all", status="INSUFFICIENT", reason="no training histories")]
    a, b, gate = select_common_support(rows.iloc[train], rows.iloc[test], scope)
    main_train, main_test = train[a], test[b]
    outputs, flows = {}, []
    for analysis_set in ("all", "previous_response_available"):
        train, test = main_train.copy(), main_test.copy()
        previous = analysis_set != "all"
        selected_gate = gate
        if previous:
            train, test = train[features.previous_indices[train] >= 0], test[features.previous_indices[test] >= 0]
            a, b, selected_gate = select_common_support(rows.iloc[train], rows.iloc[test], scope, frozen_gate=gate)
            train, test = train[a], test[b]
        flow = dict(analysis_set=analysis_set, train_trials=len(train), test_trials=len(test),
                    train_groups=int(rows.iloc[train].split_group_id.nunique()), test_groups=int(rows.iloc[test].split_group_id.nunique()),
                    support_gate=selected_gate.to_dict())
        if not len(train) or not len(test) or flow["train_groups"] < 3:
            flows.append(dict(flow, status="INSUFFICIENT", reason="frozen history/context/candidate support"))
            continue
        values = features.model_features(previous=previous)
        tr, te = rows.iloc[train].reset_index(drop=True), rows.iloc[test].reset_index(drop=True)
        try:
            models = fit_history_readouts(tr, {name: None if x is None else x[train] for name, x in values.items()},
                                         scope, seed=seed, inner_folds=3)
        except ValueError as exc:
            if not str(exc).startswith("B_INNER_SUPPORT"):
                raise
            flows.append(dict(flow, status="INSUFFICIENT", reason=str(exc)))
            continue
        predictions = []
        for name, model in models.items():
            # The reused function labels L0 by default; replace its descriptive
            # scope explicitly before persisting a learned-feature readout.
            model.fit_scope.update(encoder_scope="frozen outer-training encoder; inner readout-only validation",
                                   inner_encoder_refitted=False, input_representation_dimension=64)
            probabilities = model.predict(te, None if values[name] is None else values[name][test])
            for calibration, p in probabilities.items():
                part = te[["trial_id", "record_id", "candidate_id", "split_group_id", "history_target"]].copy()
                part["analysis_set"], part["model"], part["probability_mode"] = analysis_set, name, calibration
                part["p0"], part["p1"] = p[:, 0], p[:, 1]
                predictions.append(part)
        outputs[analysis_set] = dict(predictions=pd.concat(predictions, ignore_index=True), models=models,
                                    train_indices=train, test_indices=test)
        flows.append(dict(flow, status="COMPLETE_FOLD"))
    return outputs, flows


def summarize_mode(predictions, flows, fold_count, *, seed):
    """Reuse B's paired CE contrasts, with explicit requested-core support state."""
    losses, comparisons = _summaries(predictions, seed)
    counts = {analysis_set: int(predictions.loc[predictions.analysis_set.eq(analysis_set), "split_group_id"].nunique())
              if len(predictions) else 0 for analysis_set in ("all", "previous_response_available")}
    complete = sum(row["status"] == "COMPLETE_FOLD" for row in flows)
    adequate = min(counts.values()) >= 20 and complete == 2 * fold_count and fold_count > 0
    summary = dict(status="INTERIM_B_LEARNED_CORE_COMPLETE" if adequate else "INSUFFICIENT",
                   candidate_groups=counts, minimum_candidate_groups=20, completed_analysis_folds=complete,
                   expected_analysis_folds=2 * fold_count, comparisons=comparisons, full_B_complete=False,
                   inner_encoder_refitted=False, validation_scope="outer inductive; conditional readout-only inner CV")
    return losses, summary


def run(config, split_run, representation_plan, modes, output_dir):
    """Run requested frozen modes from a plan JSON path, exclusively in Slurm."""
    require_slurm()
    if not modes or len(set(modes)) != len(modes) or not set(modes) <= set(MODES):
        raise ValueError("B_LEARNED_MODE: use unique R_SIM/R_SUP/R_RAND; L0 has a separate frozen runner")
    base = ROOT / config["paths"]["private_relative"]
    plan_path = Path(representation_plan)
    plan_path = (plan_path if plan_path.is_absolute() else ROOT / plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    split_path = base / "splits" / split_run / "folds.json"
    split = json.loads(split_path.read_text())
    if (plan["split_run"] != split_run or plan["split_hash"] != digest(split_path) or
            plan["export_run"] != split["export_run"] or plan["config_hash"] != object_hash(config)):
        raise ValueError("B_PLAN_SPLIT_CONFIG_MISMATCH")
    source = Path(plan["source_snapshot"])
    input_hashes = {str(plan_path): digest(plan_path), str(split_path): digest(split_path)}
    for relative, expected in plan["code_hashes"].items():
        path = source / relative
        if digest(path) != expected:
            raise ValueError("B_ENCODER_SOURCE_SNAPSHOT_CHANGED")
        input_hashes[str(path)] = expected
    support_path = split_path.parent / "support.parquet"
    support = pd.read_parquet(support_path)
    input_hashes[str(support_path)] = digest(support_path)
    original_parts = []
    for record in support[support[["general", "A", "B", "D"]].any(axis=1)].to_dict("records"):
        path = base / "data" / split["export_run"] / "P1_CAUSAL20" / record["record_id"] / "summary.json"
        if digest(path) != split["input_hashes"]["P1_CAUSAL20/" + record["record_id"]]:
            raise ValueError("B_P1_EXPORT_CHANGED")
        input_hashes[str(path)] = digest(path)
        events_path = path.with_name("events.parquet")
        input_hashes[str(events_path)] = digest(events_path)
        events = pd.read_parquet(events_path, columns=list(ROW_COLUMNS))
        original_parts.append(events[events.accepted.eq(True)])
    original_rows = pd.concat(original_parts, ignore_index=True) if original_parts else pd.DataFrame(columns=ROW_COLUMNS)
    del original_parts
    destination = Path(output_dir)
    destination = (destination if destination.is_absolute() else ROOT / destination).resolve()
    if not destination.is_relative_to((ROOT / "private").resolve()):
        raise ValueError("B learned features/predictions/scopes must remain private")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    public = ROOT / config["paths"]["aggregates_relative"] / destination.name
    public.mkdir(parents=True, exist_ok=False)
    pending = list(PENDING) + ["unrequested " + mode for mode in ("R_SIM", "R_SUP") if mode not in modes]
    contract = dict(version="auditory5_B_learned_v1", representation_modes=list(modes),
                    split_hash=digest(split_path), plan_hash=digest(plan_path), seed=int(split["seed"]),
                    source_hash=digest(Path(__file__)), inherited_B_hash=digest(Path(__file__).with_name("route_b.py")),
                    documentation_hash=digest(ROOT / "docs/auditory5_B_learned_v1.md"),
                    context_columns=list(CONTEXT_COLUMNS), core_models=list(CORE_MODELS),
                    previous_subset_additions=["B4_previous", "B5_previous_post"],
                    learned_input_dimension_per_window=64, inherited_EEG_PCA_max_dimension=32,
                    inner_encoder_refitted=False, outer_test_encoder_excluded=True,
                    pending=pending, no_new_B_hyperparameters=True, full_B_complete=False)
    write_json(destination / "run_contract.json", contract)
    mode_summaries, all_flows, all_comparisons = {}, [], []
    b_records = set(support.loc[support.B, "record_id"])
    for mode in modes:
        folder = destination / mode
        folder.mkdir(mode=0o700)
        mode_predictions, mode_flows, mode_fits = [], [], []
        for fold in split["folds"]:
            number = fold["outer_fold"]
            try:
                payload, rows, encoder_evidence, hashes = _load_fold(plan, plan_path, fold, mode, support, original_rows)
            except FileNotFoundError:
                mode_flows.append(dict(representation=mode, outer_fold=number, analysis_set="all", status="INSUFFICIENT",
                                       reason="required representation task/output missing"))
                continue
            input_hashes.update(hashes)
            features = build_history_features(payload, rows, b_records)
            del payload, rows
            scope = FitScope(tuple(fold["train_groups"]), test_groups=tuple(fold["test_groups"]))
            selected_rows = features.rows.copy()
            selected_rows["feature_ledger_index"] = features.ledger_indices
            selected_rows["previous_feature_ledger_index"] = features.previous_indices
            selected_rows.to_parquet(folder / f"outer{number}_history_rows.parquet", index=False)
            np.savez_compressed(folder / f"outer{number}_selected_features.npz", pre=features.pre, post=features.post,
                                previous_post=features.previous_post, trial_ids=features.rows.trial_id.to_numpy(str),
                                ledger_indices=features.ledger_indices, previous_indices=features.previous_indices)
            outcomes, flows = fit_outer_history(features, scope, seed=int(split["seed"]))
            mode_flows.extend(dict(flow, outer_fold=number, representation=mode) for flow in flows)
            for analysis_set, result in outcomes.items():
                frame = result["predictions"]
                frame["representation"], frame["outer_fold"] = mode, number
                frame.to_parquet(folder / f"outer{number}_{analysis_set}_predictions.parquet", index=False)
                mode_predictions.append(frame)
                for name, model in result["models"].items():
                    model.fit_scope["upstream_encoder"] = encoder_evidence
                    mode_fits.append(dict(representation=mode, outer_fold=number, analysis_set=analysis_set, model=name,
                                          fit_scope=model.fit_scope, selected_C=model.selected_C, temperature=model.temperature))
                with (folder / f"outer{number}_{analysis_set}_readouts.pkl").open("xb") as stream:
                    pickle.dump(result["models"], stream)
                # These indices belong only to this fold's private selected feature copy.
                write_json(folder / f"outer{number}_{analysis_set}_selected_indices.json",
                           dict(train=result["train_indices"].tolist(), test=result["test_indices"].tolist(),
                                readout_scope_hash=scope.hash, encoder_scope=encoder_evidence))
            for path, expected in hashes.items():
                if digest(path) != expected:
                    raise ValueError("B_ENCODER_ARTIFACT_CHANGED_DURING_READOUT")
            del features, outcomes
        predictions = pd.concat(mode_predictions, ignore_index=True) if mode_predictions else pd.DataFrame()
        # Aggregate only OOF probabilities across folds; feature coordinates never mix.
        losses, summary = summarize_mode(predictions, mode_flows, len(split["folds"]), seed=int(split["seed"]))
        predictions.to_parquet(folder / "oof_history_predictions.parquet", index=False)
        losses.to_parquet(folder / "candidate_losses.parquet", index=False)
        write_json(folder / "fit_scopes.json", mode_fits)
        write_json(folder / "eligibility_flow.json", mode_flows)
        mode_summaries[mode] = summary
        all_flows.extend(mode_flows)
        all_comparisons.extend(dict(row, representation=mode) for row in summary["comparisons"])
        del predictions, mode_predictions, losses
    for path, expected in input_hashes.items():
        if digest(path) != expected:
            raise ValueError("B_SOURCE_CHANGED_DURING_READOUT")
    write_json(destination / "input_hashes.json", input_hashes)
    pd.DataFrame(all_comparisons).to_csv(public / "conditional_gains.csv", index=False)
    pd.DataFrame([{k: v for k, v in row.items() if k != "support_gate"} for row in all_flows]).to_csv(
        public / "eligibility_flow.csv", index=False)
    complete = all(summary["status"] == "INTERIM_B_LEARNED_CORE_COMPLETE" for summary in mode_summaries.values())
    summary = dict(stage="B_LEARNED_CORE", status="INTERIM_B_LEARNED_CORE_COMPLETE" if complete else "INSUFFICIENT",
                   representations=mode_summaries, full_B_complete=False, pending=pending, no_positive_screen_issued=True,
                   validation_scope="outer inductive; readout-only inner CV conditional on frozen encoder",
                   scientific_claim="conditional predictive gain, not Shannon CMI or neural memory",
                   uncertainty="fixed OOF 2000 candidate-group cluster bootstrap; no pipeline refitting")
    write_json(public / "summary.json", summary)
    write_json(destination / "completion.json", dict(status=summary["status"],
        output_hashes={str(path.relative_to(destination)): digest(path) for path in destination.rglob("*") if path.is_file()}))
    return summary
