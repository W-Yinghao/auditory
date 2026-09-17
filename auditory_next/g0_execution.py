"""G0 within-child readouts and the prespecified L0 offline bridge.

G0 is a diagnostic readout of frozen S0 features.  It does not train an
encoder.  Every transform and head is fit on a child's calibration blocks
only; later blocks are retained for evaluation.  The outer feature task is
also checked so that an outer-test child was absent from the encoder scope.
"""
from __future__ import annotations

import json
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from .features import LegacyFeatureRegistry
from .fitting import WeightedTransform
from .provenance import ROOT, digest, finish, require_slurm, write_json
from .readouts import ce_bits, population_weights,calibrate
from .context_execution import _calibrated_logit


MODES = ("L0", "R_RAND", "R_SUP", "R_SIM")
C_GRID = (0.01, 0.1, 1.0, 10.0)
BOOTSTRAPS = 2000
G0_RUN = "G0_metadata_002"
FIT_DEST=None
FIT_INDEX=0


def choose_C(losses_by_C):
    """Select C by training-child test-block CE, with a frozen tie rule.

    ``losses_by_C`` maps each candidate C to one finite loss per selection
    child.  Held-out children must never be included in this object.
    """
    if set(float(c) for c in losses_by_C) != set(C_GRID):
        raise ValueError("G0_C_GRID")
    means = {}
    for c in C_GRID:
        values = np.asarray(losses_by_C[c], dtype=float)
        if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
            raise ValueError("G0_C_SELECTION_SUPPORT")
        means[float(c)] = float(values.mean())
    chosen = min(C_GRID, key=lambda c: (means[float(c)], float(c)))
    return float(chosen), means


def candidate_balanced_weights(labels, candidates):
    """Return P_bal weights and reject a child missing either stimulus class."""
    labels = np.asarray(labels)
    candidates = np.asarray(candidates, dtype=str)
    if labels.ndim != 1 or candidates.shape != labels.shape:
        raise ValueError("G0_WEIGHT_ALIGNMENT")
    return population_weights(labels, candidates, "P_bal")


def _bacc(labels, logits, candidates):
    labels = np.asarray(labels, dtype=int)
    logits = np.asarray(logits, dtype=float)
    candidates = np.asarray(candidates, dtype=str)
    if logits.shape != labels.shape or candidates.shape != labels.shape:
        raise ValueError("G0_METRIC_ALIGNMENT")
    values = []
    for candidate in np.unique(candidates):
        own = candidates == candidate
        if set(labels[own]) != {0, 1}:
            raise ValueError("G0_METRIC_CLASS_SUPPORT")
        prediction = logits[own] >= 0
        values.append(float(np.mean(prediction[labels[own] == 0] == 0) * .5 +
                           np.mean(prediction[labels[own] == 1] == 1) * .5))
    return float(np.mean(values))


def clustered_bootstrap(table, *, cluster="record_id", seed=20260917,
                        n_boot=BOOTSTRAPS):
    """Cluster-bootstrap fixed predictions; no refits or support regeneration."""
    required = {cluster, "logit", "stimulus_local_id", "candidate_id"}
    if not required.issubset(table.columns) or int(n_boot) < 1:
        raise ValueError("G0_BOOTSTRAP_SCHEMA")
    data = table.copy()
    data["logit"] = pd.to_numeric(data.logit, errors="coerce")
    if data[["logit", "stimulus_local_id"]].isna().any().any():
        raise ValueError("G0_BOOTSTRAP_NONFINITE")
    per_cluster = []
    for key, part in data.groupby(cluster, sort=True):
        labels = part.stimulus_local_id.to_numpy(int)
        cand = part.candidate_id.astype(str).to_numpy()
        weights = candidate_balanced_weights(labels, cand)
        per_cluster.append((str(key), ce_bits(part.logit.to_numpy(float), labels, weights),
                            _bacc(labels, part.logit.to_numpy(float), cand)))
    if len(per_cluster) < 2:
        raise ValueError("G0_BOOTSTRAP_CLUSTER_SUPPORT")
    values = np.asarray([[x[1], x[2]] for x in per_cluster], dtype=float)
    rng = np.random.default_rng(int(seed))
    draw = rng.integers(0, len(values), size=(int(n_boot), len(values)))
    boot = values[draw].mean(axis=1)
    estimate = values.mean(axis=0)
    return {
        "n_clusters": int(len(values)), "n_bootstrap": int(n_boot), "seed": int(seed),
        "ce_bits": float(estimate[0]), "ce_ci_lower": float(np.quantile(boot[:, 0], .025)),
        "ce_ci_upper": float(np.quantile(boot[:, 0], .975)), "bacc": float(estimate[1]),
        "bacc_ci_lower": float(np.quantile(boot[:, 1], .025)),
        "bacc_ci_upper": float(np.quantile(boot[:, 1], .975)),
        "bootstrap_scope": "fixed_later_block_predictions_clustered_by_record",
    }


def offline_20bin_features(data_uv, times_s, *, channels):
    """Make the fixed old-epoch 20-channel, 50--450 ms bins.

    Times are the physical old-epoch time axis in seconds.  No event shift,
    padding, filtering, baseline, or label-dependent window is applied.
    """
    x = np.asarray(data_uv, dtype=float)
    times = np.asarray(times_s, dtype=float)
    names = tuple(str(c) for c in channels)
    if x.ndim != 3 or x.shape[1] != 20 or times.ndim != 1 or times.shape[0] != x.shape[2]:
        raise ValueError("G0_OFFLINE_ARRAY_SCHEMA")
    if len(set(names)) != 20 or not np.isfinite(x).all() or not np.isfinite(times).all():
        raise ValueError("G0_OFFLINE_CHANNEL_SCHEMA")
    pieces = []
    for start_ms in range(50, 450, 20):
        lo, hi = start_ms / 1000., (start_ms + 20) / 1000.
        select = (times >= lo - 1e-12) & (times < hi - 1e-12)
        if not select.any():
            raise ValueError("G0_OFFLINE_TIME_BIN_EMPTY")
        pieces.append(x[:, :, select].mean(axis=2))
    result = np.stack(pieces,axis=2).reshape(len(x),400)
    if result.shape != (len(x), 400) or not np.isfinite(result).all():
        raise ValueError("G0_OFFLINE_FEATURE_DIMENSION")
    return result


def _safe_name(value):
    if not isinstance(value, str) or not value or any(c not in
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in value):
        raise ValueError("G0_RUN_NAME")
    return value


def _private(path, root=ROOT):
    value = Path(path).resolve()
    if not value.is_relative_to((root / "private/auditory_next_v2").resolve()):
        raise ValueError("G0_PRIVATE_INPUT_REQUIRED")
    return value


def _load_json(path):
    return json.loads(Path(path).read_text())


def _align_feature_roles(features, feature_rows, roles, support):
    rows = pd.DataFrame(feature_rows).copy()
    rows["_feature_index"] = np.arange(len(rows), dtype=np.int64)
    role = pd.DataFrame(roles).copy()
    required = {"trial_id", "record_id", "candidate_id", "split_group_id", "stimulus_local_id"}
    if not required.issubset(rows.columns) or not required.issubset(role.columns):
        raise ValueError("G0_ROLE_FEATURE_SCHEMA")
    if not rows.trial_id.is_unique or not role.trial_id.is_unique:
        raise ValueError("G0_DUPLICATE_TRIAL")
    keep = ["trial_id", "record_id", "candidate_id", "split_group_id", "stimulus_local_id",
            "G0_role", "G0_supported"]
    if not {"G0_role", "G0_supported"}.issubset(role.columns):
        raise ValueError("G0_ROLE_COLUMNS")
    joined = rows.merge(role[keep], on="trial_id", how="inner", validate="one_to_one",
                        suffixes=("_feature", "_role"))
    if len(joined) != len(role):
        raise ValueError("G0_FROZEN_ROLE_MISSING_FEATURE")
    statuses = pd.DataFrame(support).copy()
    if not {"record_id", "supported"}.issubset(statuses.columns):
        raise ValueError("G0_SUPPORT_COLUMNS")
    statuses = statuses[["record_id", "supported"]].drop_duplicates("record_id")
    joined = joined.merge(statuses, left_on="record_id_feature", right_on="record_id",
                          how="left", validate="many_to_one", suffixes=("", "_status"))
    if joined.supported.isna().any():
        raise ValueError("G0_SUPPORT_RECORD_MISSING")
    joined["G0_supported"] = joined.G0_supported.astype(bool) & joined.supported.astype(bool)
    if not np.array_equal(joined.stimulus_local_id_feature.to_numpy(), joined.stimulus_local_id_role.to_numpy()):
        raise ValueError("G0_LABEL_MISMATCH")
    if not np.array_equal(joined.candidate_id_feature.astype(str), joined.candidate_id_role.astype(str)):
        raise ValueError("G0_CANDIDATE_MISMATCH")
    joined["stimulus_local_id"] = joined.stimulus_local_id_feature.astype(int)
    joined["candidate_id"] = joined.candidate_id_feature.astype(str)
    joined["record_id"] = joined.record_id_feature.astype(str)
    joined["split_group_id"] = joined.split_group_id_feature.astype(str)
    return joined


def _fit_logistic(x, y, candidates, C, mode):
    global FIT_INDEX
    x, y = np.asarray(x, float), np.asarray(y, int)
    candidates = np.asarray(candidates, str)
    if x.ndim != 2 or len(x) != len(y) or not np.isfinite(x).all():
        raise ValueError("G0_HEAD_INPUT")
    if set(y) != {0, 1}:
        raise ValueError("G0_HEAD_CLASS_SUPPORT")
    weights = candidate_balanced_weights(y, candidates)
    folder=None
    if FIT_DEST is not None:
        from .fitting import array_hash
        folder=FIT_DEST/str(FIT_INDEX);folder.mkdir();FIT_INDEX+=1
        write_json(folder/'start.json',dict(mode=mode,C=float(C),n=len(y),groups=sorted(set(candidates)),
            input_hash=array_hash(x),label_hash=array_hash(y),weight_hash=array_hash(weights)))
    transform = WeightedTransform(max_components=32 if mode == "L0" else None).fit(x, weights)
    head = LogisticRegression(C=float(C), solver="lbfgs", max_iter=5000,
                              tol=1e-7, random_state=11)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        head.fit(transform.transform(x), y, sample_weight=weights)
    if not np.isfinite(head.coef_).all():
        raise ValueError("G0_HEAD_NONFINITE")
    if folder is not None:
        with (folder/'model.pkl').open('xb') as f:pickle.dump((transform,head),f)
        write_json(folder/'completion.json',dict(status='OPTIMIZATION_STABLE',iterations=int(head.n_iter_.max())))
    return transform, head


def _predict(transform, head, x):
    logits = np.asarray(head.decision_function(transform.transform(x)), float)
    if logits.ndim != 1 or not np.isfinite(logits).all():
        raise ValueError("G0_PREDICTION_NONFINITE")
    return logits


def _task_catalog(task_plan):
    path = Path(task_plan["task_csv"])
    _private(path)
    catalog = pd.read_csv(path)
    if not {"packet", "fit_stage"}.issubset(catalog.columns):
        raise ValueError("G0_TASK_CATALOG_SCHEMA")
    subset = catalog[(catalog.packet == "G0") &
                     catalog.fit_stage.isin(("training_child_C_selection", "heldout_child_calibration"))]
    if len(subset) != 1028:
        raise ValueError("G0_WITHIN_CHILD_TASK_COUNT")
    return path, catalog


def _load_feature_bank(features, task, planpath, inventory):
    folder = planpath.parent / "outputs" / task["name"]
    for name in ("features.npz", "feature_rows.parquet"):
        path = folder / name
        expected = inventory.get(str(path))
        if expected is None or digest(path) != expected:
            raise ValueError("G0_FEATURE_SOURCE_HASH")
    data = features.load_features(task, planpath.parent / "outputs")
    if any(data.get("z" + window) is None for window in ("pre", "post")):
        raise ValueError("G0_FEATURE_WINDOW")
    return data, pd.DataFrame(data["rows"])


def _read_offline(record, mapping, hashes):
    source = ROOT / "results/phase1_epochs_001" / str(record) / "epochs.npz"
    expected = hashes.get(str(source))
    if expected is None or digest(source) != expected:
        raise ValueError("G0_OFFLINE_SOURCE_HASH")
    with np.load(source, allow_pickle=False) as old:
        needed = {"data_uv", "times_s", "channels", "accepted"}
        if not needed.issubset(set(old.files)):
            raise ValueError("G0_OFFLINE_SCHEMA_UNCLEAR")
        accepted = np.asarray(old["accepted"])
        if accepted.ndim != 2 or accepted.shape[1] < 1:
            raise ValueError("G0_OFFLINE_ACCEPTED_SCHEMA")
        physical = offline_20bin_features(old["data_uv"], old["times_s"], channels=old["channels"])
        indices = pd.to_numeric(mapping.offline_index, errors="coerce").to_numpy(float)
        if not np.isfinite(indices).all() or np.any(indices != np.floor(indices)):
            raise ValueError("G0_OFFLINE_INDEX_SCHEMA")
        indices = indices.astype(np.int64)
        if np.any(indices < 0) or np.any(indices >= len(physical)) or not np.asarray(accepted[indices, 0], bool).all():
            raise ValueError("G0_OFFLINE_ACCEPTED_MISMATCH")
        return physical[indices]


def _folds(registry):
    path = ROOT / registry["legacy_splits"]
    if digest(path) != registry["legacy_split_sha256"]:
        raise ValueError("G0_SPLIT_SOURCE_HASH")
    value = _load_json(path)
    if not value.get("folds"):
        raise ValueError("G0_NO_FOLDS")
    return path, value["folds"]


def _source_inputs(registry, task_plan):
    diag = str(task_plan.get("diagnostic_run", ""))
    if diag != G0_RUN:
        raise ValueError("G0_METADATA_RUN_REQUIRED")
    diag_dir = _private(ROOT / "private/auditory_next_v2" / diag)
    if _load_json(diag_dir / "completion.json").get("status") != "PASS":
        raise ValueError("G0_METADATA_GATE")
    planpath = ROOT / registry["legacy_plan"]
    if digest(planpath) != registry["legacy_plan_sha256"]:
        raise ValueError("G0_LEGACY_PLAN_HASH")
    splitpath, folds = _folds(registry)
    gate = _private(ROOT / "private/auditory_next_v2" / str(registry["preflight_run"]))
    inventory = {str(row["path"]): row["sha256"] for row in _load_json(gate / "legacy_input_hashes.json")}
    scope = gate / "feature_scope_registry.json"
    features = LegacyFeatureRegistry.from_files(planpath, scope)
    selected_path = Path(task_plan['task_csv']).parent / "G0_selection_records.json"
    selected = _load_json(selected_path)
    if len(selected) != len(folds):
        raise ValueError("G0_SELECTION_FOLD_COUNT")
    roles = pd.read_parquet(diag_dir / "G0_temporal_roles.parquet")
    support = pd.read_parquet(diag_dir / "G0_temporal_support.parquet")
    hashes = _load_json(diag_dir / "input_hashes.json").get("offline_hashes", {})
    return (diag_dir, planpath, splitpath, folds, inventory, scope, features,
            selected, roles, support, hashes)


def _within_child(config, *, features, planpath, inventory, folds, selected,
                  roles, support, dest, public, smoke):
    all_rows, receipts, public_rows, heads = [], [], [], {}
    first = True
    for mode in MODES:
        for fold in folds:
            number = int(fold["outer_fold"])
            selection = next(item for item in selected if int(item["outer_fold"]) == number)
            # One frozen all-channel outer feature task supplies every child in
            # this outer fold; its encoder scope is independently checked.
            task = features.resolve_task(stage="outer", mode=mode, branch="all",
                                         outer_fold=number, inner_fold=None)
            data, feature_rows = _load_feature_bank(features, task, planpath, inventory)
            if set(data.get("actual_fit_groups", [])) & set(map(str, fold["test_groups"])):
                raise ValueError("G0_ENCODER_OUTER_TEST_LEAKAGE")
            joined = _align_feature_roles(data, feature_rows, roles, support)
            if smoke:
                # Smoke aligns exactly one mode/fold bank and never creates a
                # synthetic or real head.
                return dict(status="SMOKE_PREP", fit_count=0, predictions=0)
            first = False
            for role_name, records, stage in (
                    ("selection", selection["selection_records"], "training_child_C_selection"),
                    ("heldout", selection["test_records"], "heldout_child_calibration")):
                for index, record in enumerate(records):
                    child = joined[(joined.record_id == str(record)) & joined.G0_supported]
                    cal = child[child.G0_role == "calibration"]
                    test = child[child.G0_role == "test"]
                    if len(cal) == 0 or len(test) == 0:
                        raise ValueError("G0_CHILD_ROLE_SUPPORT")
                    xcal = data["zpost"][cal._feature_index.to_numpy()]
                    xtest = data["zpost"][test._feature_index.to_numpy()]
                    ycal, ytest = cal.stimulus_local_id.to_numpy(int), test.stimulus_local_id.to_numpy(int)
                    ccal, ctest = cal.candidate_id.to_numpy(str), test.candidate_id.to_numpy(str)
                    if role_name == "selection":
                        for C in C_GRID:
                            transform, head = _fit_logistic(xcal, ycal, ccal, C, mode)
                            logits = _predict(transform, head, xtest)
                            loss = ce_bits(logits, ytest, candidate_balanced_weights(ytest, ctest))
                            receipts.append(dict(mode=mode, outer_fold=number, record_index=index,
                                record_scope="training_selection", fit_stage=stage, C=float(C),
                                n_calibration=len(cal), n_test=len(test), feature_scope_id=task["name"],
                                status="OPTIMIZATION_STABLE"))
                            all_rows.extend(dict(mode=mode, outer_fold=number, child_role=role_name,
                                record_id=str(record), record_index=index, C=float(C), trial_id=str(tid),
                                candidate_id=str(cand), stimulus_local_id=int(label), logit=float(logit),
                                fit_stage=stage,calibration='raw') for tid, cand, label, logit in zip(
                                    test.trial_id, ctest, ytest, logits))
                            heads[f"{mode}_f{number}_sel{index}_C{C:g}"] = (transform, head)
                    else:
                        losses = {}
                        # C losses are reconstructed from the private trial rows,
                        # never from held-out rows; child records are independent.
                        for C in C_GRID:
                            parts = pd.DataFrame([r for r in all_rows if r["mode"] == mode and
                                r["outer_fold"] == number and r["child_role"] == "selection" and r["C"] == float(C)])
                            if parts.empty:
                                raise ValueError("G0_C_SELECTION_MISSING")
                            losses[float(C)] = [ce_bits(p.logit.to_numpy(float), p.stimulus_local_id.to_numpy(int),
                                candidate_balanced_weights(p.stimulus_local_id.to_numpy(int), p.candidate_id.to_numpy(str)))
                                for _, p in parts.groupby("record_id", sort=True)]
                        chosen, means = choose_C(losses)
                        training_rows=pd.DataFrame([r for r in all_rows if r['mode']==mode and r['outer_fold']==number and
                                                    r['child_role']=='selection' and r['C']==chosen])
                        cal=calibrate(training_rows.logit.to_numpy(),training_rows.stimulus_local_id.to_numpy(),
                            candidate_balanced_weights(training_rows.stimulus_local_id.to_numpy(),training_rows.candidate_id.to_numpy()),training_prior=.5)
                        transform, head = _fit_logistic(xcal, ycal, ccal, chosen, mode)
                        logits = _predict(transform, head, xtest)
                        for kind in ('raw','temperature','mixture_diagnostic'):
                            zz=_calibrated_logit(logits,cal,kind)
                            for tid, cand, label, logit in zip(test.trial_id, ctest, ytest, zz):
                                all_rows.append(dict(mode=mode, outer_fold=number, child_role=role_name,
                                    record_id=str(record), record_index=index, C=float(chosen), trial_id=str(tid),
                                    candidate_id=str(cand), stimulus_local_id=int(label), logit=float(logit),
                                    fit_stage=stage,calibration=kind))
                        receipts.append(dict(mode=mode, outer_fold=number, record_index=index,
                            record_scope="heldout", fit_stage=stage, C=float(chosen),
                            C_training_means={str(k): float(v) for k, v in means.items()},
                            n_calibration=len(cal), n_test=len(test), feature_scope_id=task["name"],
                            status="OPTIMIZATION_STABLE"))
                        receipts[-1]['calibration']=cal
                        heads[f"{mode}_f{number}_held{index}"] = (transform, head)
    # C selection and predictions are private; public rows are record-free.
    private = pd.DataFrame(all_rows)
    private.to_parquet(dest / "within_child_predictions.parquet", index=False)
    write_json(dest / "within_child_fit_receipts.json", receipts)
    with (dest / "within_child_heads.pkl").open("wb") as stream:
        pickle.dump(heads, stream)
    if private.empty:
        return dict(status="SMOKE_PREP", fit_count=0, predictions=0)
    for (mode, fold, role,kind), part in private.groupby(["mode", "outer_fold", "child_role","calibration"], sort=True):
        if role != "heldout":
            continue
        metric = clustered_bootstrap(part, seed=20260917 + int(fold))
        public_rows.append(dict(mode=mode, outer_fold=int(fold), child_role=role,calibration=kind,
            n_records=int(part.record_id.nunique()), n_trials=int(len(part)), **metric))
    for (mode,kind),part in private[private.child_role.eq('heldout')].groupby(['mode','calibration']):
        public_rows.append(dict(mode=mode,outer_fold='ALL',child_role='heldout',n_records=int(part.record_id.nunique()),
            n_trials=len(part),calibration=kind,**clustered_bootstrap(part)))
    pd.DataFrame(public_rows).to_csv(public / "g0_within_child_metrics.csv", index=False)
    return dict(status="WITHIN_CHILD_COMPLETE", fit_count=len(receipts), predictions=len(private))


def _bridge(*, features, planpath, inventory, folds, mapping, roles, hashes,
            dest, public, smoke):
    required = {"trial_id", "record_id", "split_group_id", "stimulus_local_id", "offline_index"}
    if not required.issubset(mapping.columns):
        raise ValueError("G0_OFFLINE_MAPPING_SCHEMA")
    mapping = mapping.copy()
    mapping["record_id"] = mapping.record_id.astype(str)
    mapping["split_group_id"] = mapping.split_group_id.astype(str)
    mapping["candidate_id"] = mapping.split_group_id
    if mapping.trial_id.duplicated().any():
        raise ValueError("G0_OFFLINE_MAPPING_DUPLICATE")
    if smoke:
        first = folds[0]
        task = features.resolve_task(stage="outer", mode="L0", branch="all",
                                     outer_fold=int(first["outer_fold"]), inner_fold=None)
        data, fr = _load_feature_bank(features, task, planpath, inventory)
        subset = mapping[mapping.split_group_id.isin(set(map(str, first["test_groups"])))].head(1)
        if subset.empty:
            raise ValueError("G0_BRIDGE_SMOKE_SUPPORT")
        _read_offline(str(subset.record_id.iloc[0]), subset, hashes)
        return dict(status="SMOKE_PREP", fit_count=0)
    # A bridge must retain the exact 13 fits per bank and outer fold.
    receipts, predictions, heads = [], [], {}
    for bank in ("causal", "offline"):
        for fold in folds:
            number = int(fold["outer_fold"])
            train_groups, test_groups = set(map(str, fold["train_groups"])), set(map(str, fold["test_groups"]))
            outer = mapping[mapping.split_group_id.isin(train_groups | test_groups)].copy()
            if bank == "causal":
                task = features.resolve_task(stage="outer", mode="L0", branch="all", outer_fold=number, inner_fold=None)
                data, fr = _load_feature_bank(features, task, planpath, inventory)
                idx = fr.set_index(fr.trial_id.astype(str)).index
                if not mapping.trial_id.astype(str).isin(idx).all():
                    raise ValueError("G0_CAUSAL_MAPPING_MISSING")
                matrix_all = data["zpost"]
                row_index = {str(t): i for i, t in enumerate(fr.trial_id.astype(str))}
                x = np.vstack([matrix_all[row_index[str(t)]] for t in mapping.trial_id])
            else:
                chunks = []
                for record, part in mapping.groupby("record_id", sort=True):
                    chunks.append(part.assign(_offline_x=list(_read_offline(record, part, hashes))))
                # Lists are kept private; concatenate by the frozen mapping order.
                offline_map = pd.concat(chunks, ignore_index=True)
                offline_map = offline_map.set_index(offline_map.trial_id.astype(str)).loc[mapping.trial_id.astype(str)].reset_index(drop=True)
                x = np.stack(offline_map._offline_x.to_numpy())
            y, groups, candidates = mapping.stimulus_local_id.to_numpy(int), mapping.split_group_id.to_numpy(str), mapping.candidate_id.to_numpy(str)
            inner_losses = {float(C): [] for C in C_GRID};inner_predictions={float(C):[] for C in C_GRID}
            for inner in (0, 1, 2):
                val = {str(k) for k, v in fold.get("D_inner_fold_by_group", {}).items() if int(v) == inner} & train_groups
                tr = train_groups - val
                mask_tr, mask_va = np.isin(groups, list(tr)), np.isin(groups, list(val))
                if not mask_tr.any() or not mask_va.any():
                    raise ValueError("G0_BRIDGE_INNER_SUPPORT")
                for C in C_GRID:
                    transform, head = _fit_logistic(x[mask_tr], y[mask_tr], candidates[mask_tr], C, "L0")
                    logit = _predict(transform, head, x[mask_va])
                    loss = ce_bits(logit, y[mask_va], candidate_balanced_weights(y[mask_va], candidates[mask_va]))
                    inner_losses[float(C)].append(loss)
                    inner_predictions[float(C)].append((np.flatnonzero(mask_va),logit))
                    receipts.append(dict(bank=bank, outer_fold=number, inner_fold=inner, C=float(C),
                        fit_stage="bridge_inner", n_training=int(mask_tr.sum()), n_validation=int(mask_va.sum()),
                        status="OPTIMIZATION_STABLE"))
            combined={C:(np.concatenate([v[0] for v in a]),np.concatenate([v[1] for v in a])) for C,a in inner_predictions.items()}
            means={C:ce_bits(z,y[ix],candidate_balanced_weights(y[ix],candidates[ix])) for C,(ix,z) in combined.items()}
            chosen=min(C_GRID,key=lambda c:(means[c],c))
            ix,oo=combined[chosen]
            if len(np.unique(ix))!=len(ix):raise ValueError('G0_BRIDGE_DUPLICATE_OOF')
            cal=calibrate(oo,y[ix],candidate_balanced_weights(y[ix],candidates[ix]),training_prior=.5)
            write_json(dest/f'bridge_{bank}_outer{number}_calibration.json',dict(**cal,inner_coverage_groups=len(np.unique(groups[ix])),
                scope='declared D-inner subset, L0 encoder-free; scalar scores only'))
            mask_tr, mask_te = np.isin(groups, list(train_groups)), np.isin(groups, list(test_groups))
            transform, head = _fit_logistic(x[mask_tr], y[mask_tr], candidates[mask_tr], chosen, "L0")
            logit = _predict(transform, head, x[mask_te])
            for kind in ('raw','temperature','mixture_diagnostic'):
                zz=_calibrated_logit(logit,cal,kind)
                for tid, record, cand, label, value in zip(mapping.trial_id[mask_te], mapping.record_id[mask_te],
                                                            candidates[mask_te], y[mask_te], zz):
                    predictions.append(dict(bank=bank, outer_fold=number, trial_id=str(tid), record_id=str(record),
                        candidate_id=str(cand), stimulus_local_id=int(label), logit=float(value), C=float(chosen),calibration=kind))
            receipts.append(dict(bank=bank, outer_fold=number, inner_fold=None, C=float(chosen),
                inner_C_means={str(k): float(v) for k, v in means.items()}, fit_stage="bridge_final",
                n_training=int(mask_tr.sum()), n_test=int(mask_te.sum()), status="OPTIMIZATION_STABLE"))
            heads[f"{bank}_f{number}"] = (transform, head)
    if len(receipts) != 2 * len(folds) * 13:
        raise ValueError("G0_BRIDGE_FIT_COUNT")
    pd.DataFrame(predictions).to_parquet(dest / "bridge_predictions.parquet", index=False)
    write_json(dest / "bridge_fit_receipts.json", receipts)
    with (dest / "bridge_heads.pkl").open("wb") as stream:
        pickle.dump(heads, stream)
    public_rows = []
    frame = pd.DataFrame(predictions)
    for (bank, fold,kind), part in frame.groupby(["bank", "outer_fold","calibration"], sort=True):
        public_rows.append(dict(bank=bank, outer_fold=int(fold),calibration=kind, **clustered_bootstrap(part)))
    for (bank,kind),part in frame.groupby(['bank','calibration']):
        public_rows.append(dict(bank=bank,outer_fold='ALL',calibration=kind,**clustered_bootstrap(part)))
    pd.DataFrame(public_rows).to_csv(public / "g0_bridge_metrics.csv", index=False)
    return dict(status="BRIDGE_COMPLETE", fit_count=len(receipts), predictions=len(frame))


def run(config, registry, site, dest, public, report, task_plan, *, smoke=False):
    """Execute G0 only inside a Slurm allocation; smoke performs no fitting."""
    require_slurm()
    global FIT_DEST,FIT_INDEX
    dest, public, report = map(Path, (dest, public, report))
    if not dest.resolve().is_relative_to(ROOT / "private/auditory_next_v2"):
        raise ValueError("G0_PRIVATE_OUTPUT_REQUIRED")
    if not public.resolve().is_relative_to(ROOT / "results/auditory_next_v2"):
        raise ValueError("G0_PUBLIC_OUTPUT_REQUIRED")
    if any((p / name).exists() for p, name in ((dest, "completion.json"), (public, "summary.json"))):
        raise FileExistsError("G0_RUN_ALREADY_STARTED")
    dest.mkdir(parents=True, exist_ok=True); public.mkdir(parents=True, exist_ok=True); report.mkdir(parents=True, exist_ok=True)
    FIT_DEST=dest/'fits';FIT_DEST.mkdir();FIT_INDEX=0
    task_path, catalog = _task_catalog(task_plan)
    (diag_dir, planpath, splitpath, folds, inventory, scope, features, selected,
     roles, support, offline_hashes) = _source_inputs(registry, task_plan)
    if len(folds) != len(selected):
        raise ValueError("G0_FOLD_SELECTION_MISMATCH")
    # Keep all exact source hashes private, with no original paths in public files.
    write_json(dest / "input_hashes.json", {"task_csv": digest(task_path), "legacy_plan": digest(planpath),
        "legacy_splits": digest(splitpath), "G0_roles": digest(diag_dir / "G0_temporal_roles.parquet"),
        "G0_support": digest(diag_dir / "G0_temporal_support.parquet"),
        "offline_mapping": digest(diag_dir / "offline_common_mapping.parquet")})
    write_json(dest / "task_plan_g0_rows.json", {
        "within_child": int(len(catalog[(catalog.packet == "G0") & catalog.fit_stage.isin(
            ("training_child_C_selection", "heldout_child_calibration"))])),
        "bridge": int(len(catalog[(catalog.packet == "G0") & catalog.fit_stage.isin(
            ("bridge_inner", "bridge_final"))]))})
    within = _within_child(config, features=features, planpath=planpath, inventory=inventory,
                           folds=folds, selected=selected, roles=roles, support=support,
                           dest=dest, public=public, smoke=smoke)
    mapping = pd.read_parquet(diag_dir / "offline_common_mapping.parquet")
    bridge_support=pd.read_parquet(diag_dir/'offline_bridge_support.parquet')
    bridge_records=set(bridge_support.loc[bridge_support.status.eq('COMMON_QC_MAPPING_VERIFIED'),'record_id'])
    mapping=mapping[mapping.record_id.isin(bridge_records)].reset_index(drop=True)
    bridge = _bridge(features=features, planpath=planpath, inventory=inventory, folds=folds,
                     mapping=mapping, roles=roles, hashes=offline_hashes,
                     dest=dest, public=public, smoke=smoke)
    if not smoke and FIT_INDEX!=1158:raise ValueError('G0_ACTUAL_FIT_COUNT')
    summary = dict(status="PASS" if smoke else "G0_READOUTS_COMPLETE", diagnostic_run=G0_RUN,
                   within_child=within, offline_bridge=bridge, within_child_head_fits=0 if smoke else 1028,
                   offline_bridge_head_fits=0 if smoke else 130, encoder_fits=0,
                   public_scope="aggregate metrics only; exact predictions, heads, rows and dates private")
    (report / "G0_READOUT_REPORT.md").write_text(
        "# G0 readouts\n\nThe within-child diagnostic uses frozen calibration/test temporal roles. "
        "C is selected only from the first ten training children in each outer fold. "
        "The offline bridge uses exact common-QC trial mappings and physical 50--450 ms bins. "
        "Neither path trains an encoder or uses a held-out child's test blocks for selection.\n",
        encoding="utf-8")
    return finish(dest, public, summary)
