"""C2-S: six NEW_ESTIMATOR L0 spatial views from the same P1 trial bank.

All views use channel-major five-sample means at 250 Hz, a training-candidate
scaler and logistic C in [.01,.1,1,10], with three fresh GroupKFold transforms.
There is no PCA. Single temperature calibration uses selected-C training OOF
logits and the new [.25,16] bounds; no prior-mixture model is added. Six views
x five outer folds x (3x4+1) = 390 fits. Secondary MLP is BUDGET_LIMITED.

The complete frozen P1/P2 accepted-trial intersection is retained. A missing
candidate class or inadequate identity-fold support makes the whole matrix
unsupported; it never causes a model-specific deletion. Local numeric
isolation does not imply selection isolation: whole-head offline QC is shared.
"""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import pickle
import traceback

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.model_selection import GroupKFold

from auditory5.contracts import FitScope
from auditory5.probes import (C_GRID, CandidateTabularScaler, candidate_class_weights,
    weighted_log_loss_nats, _fit_head, _head_logits)
from auditory5.metrics import classification_metrics
from .c2_spatial import (CHANNELS, RIGHT, decompose20, reconstruct20, l0_views,
    coordinates19, from_coordinates19)
from .readouts import ce_bits
from .provenance import ROOT, digest, object_hash, write_json, require_slurm, finish

VIEWS = ("S0", "S1", "S2", "FULL20", "S0_DUP_S1", "S0_DUP_S2")
WIDTHS = dict(S0=320, S1=340, S2=440, FULL20=400, S0_DUP_S1=340, S0_DUP_S2=440)
CONTRASTS = {"G_crossmean": ("S0", "S1"), "G_midline": ("S1", "S2"),
    "crossmean_matched_width_margin": ("S0_DUP_S1", "S1"),
    "complete_spatial_matched_width_margin": ("S0_DUP_S2", "S2"),
    "S0_minus_FULL20": ("S0", "FULL20"), "S2_minus_FULL20": ("S2", "FULL20")}


def _integers(values):
    original = np.asarray(values)
    value = np.asarray(values, float)
    if (original.dtype.kind == "b" or value.ndim != 1 or not np.isfinite(value).all() or
            np.any(value != np.floor(value)) or np.any(value < 0) or np.any(value >= np.iinfo(np.int64).max)):
        raise ValueError("C2S_EXACT_INTEGER_SAMPLE_INDEX")
    return value.astype(np.int64)


def extract_views(epochs, post_starts, channel_names, *, processed_fs=250.):
    """Extract exactly each row's 100-sample post window and audit geometry."""
    x = np.asarray(epochs, dtype=np.float64)
    starts = _integers(post_starts)
    if (x.ndim != 3 or x.shape[1] != 20 or not len(x) or starts.shape != (len(x),) or
            np.any(starts + 100 > x.shape[2]) or not np.isfinite(x).all() or processed_fs != 250.):
        raise ValueError("C2S_EXACT_POST_SAMPLE_LAYOUT")
    full_parts = decompose20(x, channel_names)
    full_error = float(np.max(abs(reconstruct20(full_parts) - (x - x.mean(axis=1, keepdims=True)))))
    post = np.stack([trial[:, start:start+100] for trial, start in zip(x, starts)])
    parts = decompose20(post, channel_names)
    expected = post - post.mean(axis=1, keepdims=True)
    error = float(np.max(abs(reconstruct20(parts) - expected)))
    error19 = float(np.max(abs(reconstruct20(from_coordinates19(coordinates19(parts), channel_names)) - expected)))
    if max(full_error, error, error19) > 1e-10:
        raise ValueError("C2S_RECONSTRUCTION_FAILURE")
    changed = post.copy()
    changed[:, [tuple(channel_names).index(c) for c in RIGHT]] += 13.0
    changed_parts = decompose20(changed, channel_names)
    if not np.array_equal(parts.u_L, changed_parts.u_L):
        raise ValueError("C2S_LOCAL_NUMERIC_ISOLATION")
    result = l0_views(parts, sfreq=processed_fs)
    if set(result) != set(VIEWS) or any(result[k].shape != (len(x), WIDTHS[k]) for k in VIEWS):
        raise ValueError("C2S_FIXED_VIEW_DIMENSIONS")
    return result, dict(trials=len(x), max_reconstruction_error=error, max_full_epoch_reconstruction_error=full_error,
        max_19dim_reconstruction_error=error19,
        effective_spatial_dimensions=19, numeric_isolation=True, selection_isolation=False)


def fit_temperature_new(scores, y, groups, scope, bounds=(.25, 16.)):
    """Only scalar T; natural-log optimization, explicit endpoint comparison."""
    if tuple(bounds) != (.25, 16.):
        raise ValueError("C2S_FROZEN_NEW_TEMPERATURE_BOUNDS")
    scope.assert_fit_groups(groups)
    weight = candidate_class_weights(y, groups)
    scores = np.asarray(scores, float)
    objective = lambda logt: weighted_log_loss_nats(scores / np.exp(logt), y, weight)
    baseline = objective(0.)
    result = minimize_scalar(objective, bounds=tuple(np.log(bounds)), method="bounded", options={"xatol": 1e-8})
    if not result.success or not np.isfinite(result.fun):
        raise ValueError("C2S_TEMPERATURE_NUMERICAL_FAILURE")
    choices = [(1., baseline), (bounds[0], objective(np.log(bounds[0]))),
               (bounds[1], objective(np.log(bounds[1]))), (float(np.exp(result.x)), float(result.fun))]
    temperature, loss = min(choices, key=lambda item: (item[1], abs(np.log(item[0]))))
    return dict(temperature=temperature, bounds=list(bounds), at_bound=temperature in bounds,
        fit_scope_hash=scope.hash, fit_groups=sorted(set(groups)), objective_units="nats",
        inner_oof_ce_bits=loss / np.log(2), prior_mixture="NOT_USED")


@dataclass
class SpatialProbe:
    scaler: object
    head: object
    selected_C: float
    temperature: float
    evidence: dict

    def predict(self, x):
        logits = _head_logits(self.head, self.scaler.transform(x))
        return dict(raw_logits=logits[:, 1] - logits[:, 0],
            calibrated_logits=(logits[:, 1] - logits[:, 0]) / self.temperature,
            raw=softmax(logits, axis=1), calibrated=softmax(logits / self.temperature, axis=1))


def fit_spatial_probe(x, y, groups, scope, *, seed=11, bounds=(.25, 16.), on_fit=None):
    """Training-only readout; no held-out feature or label argument exists."""
    x, y, groups = np.asarray(x, float), np.asarray(y), np.asarray(groups, str)
    if x.ndim != 2 or not len(x) or y.shape != (len(x),) or groups.shape != y.shape or not np.isfinite(x).all():
        raise ValueError("C2S_TRAIN_FEATURE_SCHEMA")
    scope.assert_fit_groups(groups)
    weights = candidate_class_weights(y, groups)
    if not np.array_equal(np.unique(y), [0, 1]) or len(set(groups)) < 3:
        raise ValueError("C2S_BINARY_GROUP_SUPPORT")
    oof = {c: np.full((len(x), 2), np.nan) for c in C_GRID}
    inner_scopes = []

    def head_fit(features, labels, identities, c, fit_scope, inner):
        evidence = dict(C=c, inner_fold=inner, scope=asdict(fit_scope), scope_hash=fit_scope.hash)
        if on_fit:
            on_fit(dict(evidence, status="STARTED"))
        head = _fit_head(features, labels, identities, c, seed)
        if on_fit:
            on_fit(dict(evidence, status="PASS"))
        return head

    for inner, (tr, va) in enumerate(GroupKFold(3).split(x, y, groups)):
        candidate_class_weights(y[tr], groups[tr])
        candidate_class_weights(y[va], groups[va])
        inside = FitScope(tuple(np.unique(groups[tr])), tuple(np.unique(groups[va])),
                          tuple(scope.validation_groups) + tuple(scope.test_groups))
        scaler = CandidateTabularScaler().fit(x[tr], groups[tr], inside)
        train, validation = scaler.transform(x[tr]), scaler.transform(x[va])
        for c in C_GRID:
            head = head_fit(train, y[tr], groups[tr], c, inside, inner)
            oof[c][va] = _head_logits(head, validation)
        inner_scopes.append(dict(scope=asdict(inside), scope_hash=inside.hash))
    losses = {c: weighted_log_loss_nats(oof[c], y, weights) for c in C_GRID}
    chosen = min(C_GRID, key=lambda c: (losses[c], c))
    calibration = fit_temperature_new(oof[chosen], y, groups, scope, bounds)
    scaler = CandidateTabularScaler().fit(x, groups, scope)
    head = head_fit(scaler.transform(x), y, groups, chosen, scope, None)
    return SpatialProbe(scaler, head, chosen, calibration["temperature"], dict(scope=asdict(scope),
        scope_hash=scope.hash, inner_folds=inner_scopes, calibration=calibration,
        inner_ce_bits={str(c): float(v / np.log(2)) for c, v in losses.items()},
        selected_inner_oof_logits=oof[chosen], head_fits=13, PCA="NONE", new_encoder_fits=0))


def paired_spatial_summary(losses, *, seed=20260917):
    """All six views on identical candidates; one bootstrap draw table."""
    if set(losses) != set(VIEWS) or not losses.index.is_unique or len(losses) < 2:
        raise ValueError("C2S_COMPLETE_SIX_VIEW_COHORT_REQUIRED")
    values = losses.loc[:, list(VIEWS)].to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError("C2S_FAILED_MODEL_CANNOT_BE_DROPPED_OR_ZERO_FILLED")
    order = np.argsort(losses.index.to_numpy(str), kind="stable")
    values = values[order]
    draws = np.random.default_rng(seed).integers(0, len(values), (2000, len(values)))
    mean, boot = values.mean(axis=0), values[draws].mean(axis=1)
    rows = []
    for name, (baseline, augmented) in CONTRASTS.items():
        a, b = VIEWS.index(baseline), VIEWS.index(augmented)
        samples = boot[:, a] - boot[:, b]
        rows.append(dict(statistic=name, estimate=float(mean[a] - mean[b]),
            ci_lower=float(np.quantile(samples, .025)), ci_upper=float(np.quantile(samples, .975)),
            n_candidates=len(values), n_bootstrap=2000, seed=seed, units="bits/trial",
            bootstrap_scope="fixed_oof_no_refit; same candidate draws for all contrasts"))
    for index, view in enumerate(VIEWS):
        rows.append(dict(statistic="CE_" + view, estimate=float(mean[index]),
            ci_lower=float(np.quantile(boot[:, index], .025)), ci_upper=float(np.quantile(boot[:, index], .975)),
            n_candidates=len(values), n_bootstrap=2000, seed=seed, units="bits/trial",
            bootstrap_scope="fixed_oof_no_refit; same candidate draws for all contrasts"))
    return rows


def _name(value):
    if not isinstance(value, str) or not value or any(c not in
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in value):
        raise ValueError("C2S_EXPLICIT_RUN_NAME")
    return value


def _read(path, hashes, inventory=None):
    path = Path(path)
    current = digest(path)
    if inventory is not None and inventory.get(str(path)) != current:
        raise ValueError("C2S_FROZEN_SOURCE_HASH")
    if str(path) in hashes and hashes[str(path)] != current:
        raise ValueError("C2S_SOURCE_CHANGED")
    hashes[str(path)] = current
    return path


def _json(path, hashes, inventory=None):
    path = _read(path, hashes, inventory)
    value = json.loads(path.read_text())
    if digest(path) != hashes[str(path)]:
        raise ValueError("C2S_SOURCE_CHANGED_DURING_READ")
    return value


def _sources(registry, task_plan, hashes):
    task_csv = Path(task_plan["task_csv"])
    if not task_csv.resolve().is_relative_to(ROOT / "private/auditory_next_v2"):
        raise ValueError("C2S_PRIVATE_TASK_PLAN_REQUIRED")
    if object_hash(_json(task_csv.parent / "plan.json", hashes)) != object_hash(task_plan):
        raise ValueError("C2S_TASK_PLAN_CHANGED")
    if _json(task_csv.parent / "completion.json", hashes)["status"] != "PASS":
        raise ValueError("C2S_TASK_PLAN_GATE")
    catalog = pd.read_csv(_read(task_csv, hashes))
    if digest(task_csv) != task_plan["task_csv_hash"]:
        raise ValueError("C2S_TASK_CATALOG_HASH")
    own = catalog[catalog.packet.eq("C2_S")]
    if (len(own) != 390 or not own.fit_index.is_unique or not own["family"].eq("logistic").all() or
            not own["mode"].eq("L0").all() or not own.population.eq("P_bal").all() or not own.neural.eq(False).all()):
        raise ValueError("C2S_FROZEN_390_FIT_CATALOG")
    contract_dir = ROOT / "private/auditory_next_v2" / _name(task_plan["contract_run"])
    if _json(contract_dir / "completion.json", hashes)["status"] != "PASS":
        raise ValueError("C2S_CONTRACT_GATE")
    support_dir = ROOT / "private/auditory_next_v2" / _name(task_plan["support_run"])
    done = _json(support_dir / "completion.json", hashes)
    definition = _json(support_dir / "support_definition.json", hashes)
    if done["status"] != "PASS" or definition["frozen_before_features"] is not True:
        raise ValueError("C2S_SUPPORT_GATE")
    if done["source_gate"] != task_plan["preflight_run"]:
        raise ValueError("C2S_PREFLIGHT_PLAN_MISMATCH")
    gate = ROOT / "private/auditory_next_v2" / _name(done["source_gate"])
    if _json(gate / "completion.json", hashes)["status"] != "PASS" or digest(gate / "completion.json") != definition["source_gate_hash"]:
        raise ValueError("C2S_PREFLIGHT_HASH")
    inventory = {r["path"]: r["sha256"] for r in _json(gate / "legacy_input_hashes.json", hashes)}
    legacy_path, split_path = ROOT / registry["legacy_plan"], ROOT / registry["legacy_splits"]
    legacy, split = _json(legacy_path, hashes, inventory), _json(split_path, hashes, inventory)
    if (digest(legacy_path) != registry["legacy_plan_sha256"] or digest(split_path) != registry["legacy_split_sha256"] or
            digest(split_path) != definition["fold_hash"] or legacy["split_hash"] != digest(split_path)):
        raise ValueError("C2S_PLAN_SPLIT_HASH")
    if len(split["folds"]) != 5:
        raise ValueError("C2S_FIVE_OUTER_FOLDS_REQUIRED")
    for fold in split["folds"]:
        for view in VIEWS:
            cell = own[own.outer_fold.eq(fold["outer_fold"]) & own.view.eq(view)]
            final = cell[cell.fit_stage.eq("final_selected_C")]
            if len(cell) != 13 or len(final) != 1 or not final.inner_fold.isna().all():
                raise ValueError("C2S_TASK_GRID_MISMATCH")
            for inner in range(3):
                part = cell[cell.fit_stage.eq("inner") & cell.inner_fold.eq(inner)]
                if len(part) != 4 or set(part.C) != set(C_GRID):
                    raise ValueError("C2S_TASK_C_GRID_MISMATCH")
    ids = _json(support_dir / "C2S_common_P1_P2_trials.json", hashes)
    if not isinstance(ids, list) or len(set(ids)) != len(ids) or any(not isinstance(t, str) for t in ids):
        raise ValueError("C2S_UNIQUE_FROZEN_TRIAL_LIST")
    columns = ["trial_id", "record_id", "candidate_id", "split_group_id", "stimulus_local_id", "accepted",
               "stored_epoch_index", "post_start_index", "time_block_id"]
    events_path = _read(support_dir / "full_event_history.parquet", hashes)
    if digest(events_path) != definition["metadata_hash"]:
        raise ValueError("C2S_FROZEN_METADATA_HASH")
    all_rows = pd.read_parquet(events_path, columns=columns)
    if not all_rows.trial_id.is_unique or not set(ids) <= set(all_rows.trial_id):
        raise ValueError("C2S_TRIAL_METADATA_ALIGNMENT")
    rows = all_rows[all_rows.trial_id.isin(ids)].sort_values(["record_id", "trial_id"], kind="stable").reset_index(drop=True)
    if not rows.accepted.eq(True).all() or not rows.stimulus_local_id.isin([0, 1]).all():
        raise ValueError("C2S_ACCEPTED_TARGET_INTERSECTION")
    return legacy, split, inventory, rows, own


def _feature_bank(dest, legacy, rows, inventory, hashes, *, smoke):
    selected = rows[rows.record_id.eq(sorted(rows.record_id.unique())[0])].copy() if smoke else rows
    features = {}
    if not smoke:
        folder = dest / "L0_views"
        folder.mkdir(mode=0o700)
        features = {view: np.lib.format.open_memmap(folder / (view + ".npy"), mode="w+", dtype="float64",
                    shape=(len(selected), WIDTHS[view])) for view in VIEWS}
    geometry = []
    for _, part in selected.groupby("record_id", sort=True):
        rid = _name(part.record_id.iloc[0])
        base = ROOT / "private/auditory5_v1/data" / legacy["export_run"]
        p1, p2 = base / "P1_CAUSAL20" / rid, base / "P2_SPATIAL_SPLIT" / rid
        summary = _json(p1 / "summary.json", hashes, inventory)
        names = tuple(summary["branch_channels"]["all"])
        if summary["bank"] != "P1_CAUSAL20" or summary["processed_fs"] != 250 or set(names) != set(CHANNELS) or len(names) != 20:
            raise ValueError("C2S_P1_COMPLETE_LAYOUT_AND_RATE")
        one = pd.read_parquet(_read(p1 / "events.parquet", hashes, inventory))
        two = pd.read_parquet(_read(p2 / "events.parquet", hashes, inventory))
        common = set(one.loc[one.accepted, "trial_id"]) & set(two.loc[two.accepted, "trial_id"])
        if common != set(part.trial_id) or not one.trial_id.is_unique or not two.trial_id.is_unique:
            raise ValueError("C2S_INTERSECTION_CHANGED")
        for source, columns in ((one, list(part.columns)),
                (two, ["record_id", "candidate_id", "split_group_id", "stimulus_local_id"])):
            aligned = source.set_index("trial_id", drop=False).loc[part.trial_id]
            if any(not np.array_equal(aligned[c].to_numpy(), part[c].to_numpy()) for c in columns):
                raise ValueError("C2S_P1_P2_FROZEN_ROW_METADATA")
        array_path = _read(p1 / "all.npy", hashes, inventory)
        if digest(array_path) != summary["output_sha256"]["all.npy"]:
            raise ValueError("C2S_P1_SIGNAL_HASH")
        epochs = np.load(array_path, mmap_mode="r")
        if epochs.ndim != 3 or len(epochs) != summary["stored_epochs"]:
            raise ValueError("C2S_STORED_EPOCH_SHAPE")
        for first in range(0, len(part), 32):
            batch = part.iloc[first:first+32]
            index = _integers(batch.stored_epoch_index.to_numpy())
            if np.any(index >= len(epochs)):
                raise ValueError("C2S_STORED_EPOCH_INDEX")
            views, audit = extract_views(epochs[index], batch.post_start_index.to_numpy(), names, processed_fs=summary["processed_fs"])
            geometry.append(dict(record_id=rid, **audit))
            if not smoke:
                for view in VIEWS:
                    features[view][batch.index.to_numpy()] = views[view]
        del epochs
    for values in features.values():
        values.flush()
        values.flags.writeable = False
    write_json(dest / "geometry_private.json", geometry)
    report = dict(records=int(selected.record_id.nunique()), trials=len(selected),
        max_reconstruction_error=max(r["max_reconstruction_error"] for r in geometry),
        max_full_epoch_reconstruction_error=max(r["max_full_epoch_reconstruction_error"] for r in geometry),
        max_19dim_reconstruction_error=max(r["max_19dim_reconstruction_error"] for r in geometry),
        numeric_isolation=True, selection_isolation=False, effective_spatial_dimensions=19,
        source="P1 shared full-head reference and causal filter; P1/P2 accepted-trial intersection",
        same_signals_for_all_views=True, status="PASS")
    return features, report


def support_audit(rows, folds):
    """Preserve the entire frozen pool; no additional per-class trial quota."""
    groups = set(rows.split_group_id.astype(str))
    counts = rows.groupby(["split_group_id", "stimulus_local_id"]).size().unstack(fill_value=0).reindex(columns=[0, 1], fill_value=0)
    outer, heldout = [], []
    for fold in folds:
        train, test = set(fold["train_groups"]), set(fold["test_groups"])
        if train & test or not groups <= train | test:
            raise ValueError("C2S_OUTER_IDENTITY_SCOPE")
        heldout.extend(groups & test)
        outer.append(dict(outer_fold=int(fold["outer_fold"]), train_candidates=len(groups & train), test_candidates=len(groups & test)))
    if len(heldout) != len(groups) or set(heldout) != groups:
        raise ValueError("C2S_TEST_IDENTITIES_MUST_OCCUR_ONCE")
    complete_classes = not counts.empty and bool((counts > 0).all().all())
    enough = len(groups) >= 20 and complete_classes and all(r["train_candidates"] >= 12 and r["test_candidates"] >= 2 for r in outer)
    return dict(status="SUFFICIENT_FOR_SCREEN" if enough else "SUPPORT_INSUFFICIENT", candidates=len(groups),
        trials=len(rows), all_candidates_have_both_classes=complete_classes,
        minimum_trials_class0=int(counts[0].min()) if len(counts) else 0,
        minimum_trials_class1=int(counts[1].min()) if len(counts) else 0,
        outer_counts=outer, extra_trial_count_exclusions=0)


def _verify_hashes(hashes):
    for path, before in hashes.items():
        if digest(Path(path)) != before:
            raise ValueError("C2S_IMMUTABLE_SOURCE_CHANGED")


def run(config, registry, site, dest, public, report, task_plan, smoke=False):
    """Frozen-plan C2-S linear matrix; smoke audits one metadata-selected record."""
    require_slurm()
    dest, public, report = map(Path, (dest, public, report))
    for path, base in ((dest, "private"), (public, "results"), (report, "reports")):
        if not path.resolve().is_relative_to(ROOT / base / "auditory_next_v2"):
            raise ValueError("C2S_OUTPUT_ROOT")
    if (dest / "C2S_definition.json").exists() or (dest / "completion.json").exists():
        raise FileExistsError("C2S_RUN_IMMUTABLE")
    if not isinstance(smoke, bool) or tuple(config["calibration"]["new_T_bounds"]) != (.25, 16.):
        raise ValueError("C2S_FROZEN_CALIBRATION_CONFIG")
    if (config["readouts"]["legacy_C_or_alpha_grid"] != list(C_GRID) or
            config["preprocessing"]["sample_rate"] != 250 or config["readouts"]["seed"] != 11 or
            config["preprocessing"]["post_seconds"] != [.05, .45] or
            config["preprocessing"]["default_source"] != "P1_CAUSAL20"):
        raise ValueError("C2S_FROZEN_FEATURE_AND_HEAD_CONFIG")
    hashes = {}
    legacy, split, inventory, rows, catalog = _sources(registry, task_plan, hashes)
    support = support_audit(rows, split["folds"])
    write_json(dest / "C2S_definition.json", dict(estimator="NEW_ESTIMATOR", task_plan_hash=object_hash(task_plan),
        support_run=task_plan["support_run"], views=list(VIEWS), widths=WIDTHS, PCA="NONE", C_grid=list(C_GRID),
        temperature_bounds=[.25, 16], inner_folds=3, outer_folds=5, seed=11,
        feature_source="same P1 whole-head reference/causal processing", shared_trial_pool=True,
        sample_window="row.post_start_index : row.post_start_index+100 at250Hz", bin_samples=5,
        trial_id_hash=object_hash(rows.trial_id.to_list()), selection_isolation=False, numeric_isolation=True,
        scaler_weights="1/n_candidate", head_weights="1/(2*n_candidate_class)",
        declared_head_fits=0 if smoke else 390, secondary_MLP="BUDGET_LIMITED", clinical_inputs=False))
    rows.to_parquet(dest / "trial_rows.parquet", index=False)
    write_json(public / "support_aggregate.json", support)
    base_summary = dict(stage="C2_S", estimator="NEW_ESTIMATOR", support=support, new_encoder_fits=0,
        neural_head_fits=0, secondary_MLP="BUDGET_LIMITED", scientific_status="NOT_EVALUABLE",
        numeric_isolation=True, selection_isolation=False, selection_scope="shared whole-record offline full-head QC",
        bootstrap_scope="fixed_oof_no_refit", clinical_inputs=False)
    if rows.empty or (not smoke and support["status"] != "SUFFICIENT_FOR_SCREEN"):
        _verify_hashes(hashes)
        write_json(dest / "input_hashes.json", hashes)
        return finish(dest, public, dict(base_summary, status="SUPPORT_INSUFFICIENT", head_fits_attempted=0,
            head_fits_completed=0, main_matrix_complete=False, results=[]))
    features, geometry = _feature_bank(dest, legacy, rows, inventory, hashes, smoke=smoke)
    write_json(public / "geometry_aggregate.json", geometry)
    if smoke:
        _verify_hashes(hashes)
        write_json(dest / "input_hashes.json", hashes)
        return finish(dest, public, dict(base_summary, status="PASS", scope="one metadata-selected record geometry smoke; no heads",
            geometry=geometry, head_fits_attempted=0, head_fits_completed=0, main_matrix_complete=False, results=[]))
    feature_hashes = {view: digest(dest / "L0_views" / (view + ".npy")) for view in VIEWS}
    write_json(dest / "feature_hashes.json", feature_hashes)
    write_json(dest / "input_hashes.json", hashes)
    losses, head_receipts, ledger = [], [], []
    heads_dir, predictions_dir = dest / "heads", dest / "predictions"
    heads_dir.mkdir(mode=0o700)
    predictions_dir.mkdir(mode=0o700)
    try:
        for fold in split["folds"]:
            number = int(fold["outer_fold"])
            train = rows.split_group_id.isin(fold["train_groups"]).to_numpy()
            test = rows.split_group_id.isin(fold["test_groups"]).to_numpy()
            scope = FitScope(tuple(sorted(rows.loc[train, "split_group_id"].unique())),
                             test_groups=tuple(sorted(rows.loc[test, "split_group_id"].unique())))
            models = {}
            for view in VIEWS:
                def record_fit(event, view=view):
                    item = dict(event, view=view, outer_fold=number)
                    ledger.append(item)
                    with (dest / "fit_ledger.jsonl").open("a") as stream:
                        stream.write(json.dumps(item, allow_nan=False) + "\n")
                model = fit_spatial_probe(features[view][train], rows.loc[train, "stimulus_local_id"].to_numpy(int),
                    rows.loc[train, "split_group_id"].to_numpy(str), scope, seed=11, on_fit=record_fit)
                models[view] = model
                with (heads_dir / f"outer{number}_{view}.pkl").open("xb") as stream:
                    pickle.dump(model, stream)
                head_receipts.append(dict(outer_fold=number, view=view, selected_C=model.selected_C,
                    temperature=model.temperature, at_bound=model.evidence["calibration"]["at_bound"],
                    fit_scope=asdict(scope), scope_hash=scope.hash, head_fits=13, source_feature_hash=feature_hashes[view]))
            # Every view in this outer fold fitted before any of its test scores.
            te = rows.loc[test].reset_index(drop=True)
            for view, model in models.items():
                p = model.predict(features[view][test])
                parts = []
                for calibration in ("raw", "calibrated"):
                    part = te.copy()
                    part["view"], part["outer_fold"], part["calibration"] = view, number, calibration
                    part["logit"] = p[calibration + "_logits"]
                    part["p0"], part["p1"] = p[calibration][:, 0], p[calibration][:, 1]
                    parts.append(part)
                    for group, group_rows in part.groupby("split_group_id", sort=True):
                        y = group_rows.stimulus_local_id.to_numpy(int)
                        g = group_rows.split_group_id.to_numpy(str)
                        metric = classification_metrics(y, group_rows[["p0", "p1"]].to_numpy(), g, group_rows.trial_id.to_numpy(str))
                        ce = ce_bits(group_rows.logit.to_numpy(), y, candidate_class_weights(y, g))
                        metric.update(ce_bits=ce, J_bits=1 - ce)
                        losses.append(dict(split_group_id=group, view=view, outer_fold=number,
                            calibration=calibration, **metric))
                pd.concat(parts, ignore_index=True).to_parquet(predictions_dir / f"outer{number}_{view}.parquet", index=False)
    except ValueError as error:
        if losses:
            pd.DataFrame(losses).to_parquet(dest / "partial_candidate_losses.parquet", index=False)
        write_json(dest / "spatial_failure.json", dict(error=str(error), traceback=traceback.format_exc(),
            head_fits_attempted=sum(r["status"] == "STARTED" for r in ledger),
            head_fits_completed=sum(r["status"] == "PASS" for r in ledger)))
        if "CONVERGENCE" not in str(error) and "NUMERICAL" not in str(error):
            raise
        return finish(dest, public, dict(base_summary, status="IMPLEMENTATION_FAIL", main_matrix_complete=False,
            reason="a required numerical readout failed; no success-subset aggregate",
            head_fits_attempted=sum(r["status"] == "STARTED" for r in ledger),
            head_fits_completed=sum(r["status"] == "PASS" for r in ledger), results=[]))
    attempted, completed = [sum(r["status"] == status for r in ledger) for status in ("STARTED", "PASS")]
    if attempted != 390 or completed != 390 or len(head_receipts) != 30:
        raise ValueError("C2S_COMPLETE_390_FIT_RECEIPT_REQUIRED")
    loss_frame = pd.DataFrame(losses)
    loss_frame.to_parquet(dest / "candidate_losses.parquet", index=False)
    write_json(dest / "fit_scopes.json", head_receipts)
    aggregates = []
    for calibration in ("raw", "calibrated"):
        part = loss_frame[loss_frame.calibration.eq(calibration)]
        table = part.pivot(index="split_group_id", columns="view", values="ce_bits")
        if set(table.index) != set(rows.split_group_id):
            raise ValueError("C2S_INCOMPLETE_OOF_COHORT")
        aggregates.extend(dict(calibration=calibration, **item) for item in paired_spatial_summary(table))
    _verify_hashes(hashes)
    for view, before in feature_hashes.items():
        if digest(dest / "L0_views" / (view + ".npy")) != before:
            raise ValueError("C2S_FEATURE_BANK_CHANGED")
    pd.DataFrame(aggregates).to_csv(public / "spatial_gains.csv", index=False)
    loss_frame.groupby(["view", "calibration"])[["ce_bits", "J_bits", "bacc", "auroc", "brier"]].mean().reset_index().to_csv(
        public / "classification_metrics.csv", index=False)
    (report / "C2S_REPORT.md").write_text(
        "# C2-S 共同试次上的空间成分线性读出\n\n六个视图复用冻结的 P1/P2 accepted 交集和 P1 全20通道参考/因果滤波。"
        "每条 trial 严格使用其 post_start_index 起100个250Hz样本，5样本形成20ms箱。逐批核验完整epoch及post重建、19维有效坐标和右侧扰动不改变左局部数值。"
        "所有候选保留原共同trial；只检查每候选两类存在、总候选至少20和每外折训练至少12/测试至少2，不追加20试次/类排除。\n\n"
        "六视图各自训练内候选等权 scaler，不做PCA；GroupKFold3选择四值C，内折重新拟合scaler/head。"
        "本路线是NEW_ESTIMATOR，采用新温度范围[0.25,16]，仅训练OOF校准，不加先验混合。"
        "共390次logistic拟合。raw和cal使用稳定logit交叉熵，以候选/类别等权的bits/trial报告；FULL20与S2可逆，正则化性能无需相等。\n\n"
        "主增益为S0−S1、S1−S2，另报两个同宽度重复输入对照及FULL20参考。2000次候选bootstrap共享抽样，属于fixed OOF，不含流程重拟合。"
        "局部数值隔离不代表选择隔离：原整记录全头QC及P1/P2交集共同决定试次集合，selection_isolation=False。"
        "次要MLP受预算限制未运行，不能写成阴性；此结果不完成所有C2科学对照，也不证明解剖来源或PID协同。\n", encoding="utf-8")
    return finish(dest, public, dict(base_summary, status="C2S_LINEAR_MATRIX_COMPLETE", main_matrix_complete=True,
        head_fits_attempted=attempted, head_fits_completed=completed, geometry=geometry, results=aggregates,
        calibration_bounds=[.25, 16], temperature_boundary_heads=sum(r["at_bound"] for r in head_receipts),
        pending=["secondary MLP32: BUDGET_LIMITED", "independent confirmation after previous cohort exploration"]))
