"""Bounded C2-R/E0-R repair of legacy objectives, never legacy result mutation.

All neural inner alpha models AND all four final-alpha models finish 1000
steps before any alpha selection or test prediction. If any member is unstable,
EVERY member continues to 2000 with the original schedule. Selection/calibration
then use the common final-budget inner OOF predictions. Unselected final-alpha
fits remain saved and counted. A packet is the entire compared neural family,
including every requested outer fold/record, not one convenient subset.

C2-R: 7 neural specs x 5 folds x 16 fits = 560 per mode; 5 linear specs
x 5 folds x 13 fits = 325. E0-R: 16 records x 4 folds x 16 = 1024 neural
fits; the exact complete legacy linear OOF predictions/scopes are reused.
E0's legacy weighting groups are filter blocks within one record; they are not
additional children. C2's weighting groups remain candidate identity groups.
No new encoder, new PCA for C2-R, changed population weighting or third solver.
"""
from dataclasses import asdict
import json
import os
from pathlib import Path
import pickle
import traceback

import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.model_selection import GroupKFold
import torch

from auditory5.contracts import FitScope
from auditory5.probes import (C_GRID, CandidateTabularScaler, CandidateWeightedPCA,
    bin_20ms, candidate_class_weights, fit_temperature, weighted_log_loss_nats,
    _fit_head, _head_logits)
from auditory5.metrics import classification_metrics
from auditory5.statistics import paired_cluster_bootstrap
from auditory5.routes import route_c as old_c, route_e as old_e
from .readouts import start_fit, advance_fit, stability, _fit_input_hash
from .provenance import ROOT, digest, object_hash, write_json, require_slurm, finish


def fit_counts(packet, *, modes=1, records=16):
    if packet == "C2_R":
        return dict(neural=7 * 5 * 16 * modes, linear=5 * 5 * 13 * modes)
    if packet == "E0_R":
        return dict(neural=records * 4 * 16, linear=0)
    raise ValueError("REPAIR_PACKET")


def family_budget(diagnostics):
    """No performance enters the single, global extension decision."""
    if not diagnostics or any(d.get("attempted_budget", d.get("steps")) != 1000 for d in diagnostics):
        raise ValueError("REPAIR_INITIAL_FAMILY_INCOMPLETE")
    return 1000 if all(d["status"] == "OPTIMIZATION_STABLE" for d in diagnostics) else 2000


def require_complete_family(diagnostics, expected, budget):
    if len(diagnostics) != expected or any(d.get("steps") != budget or
            d.get("status") != "OPTIMIZATION_STABLE" for d in diagnostics):
        raise ValueError("INCOMPLETE_PRIMARY_MATRIX")


def select_alpha(oof, y, groups):
    if set(oof) != set(C_GRID):
        raise ValueError("REPAIR_ALPHA_GRID_INCOMPLETE")
    weights = candidate_class_weights(y, groups)
    losses = {a: weighted_log_loss_nats(oof[a], y, weights) for a in C_GRID}
    chosen = min(C_GRID, key=lambda a: (losses[a], -a))
    return chosen, {str(a): float(v / np.log(2)) for a, v in losses.items()}


def _name(value):
    if not isinstance(value, str) or not value or any(c not in
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in value):
        raise ValueError("REPAIR_EXPLICIT_NAME")
    return value


def _read(path, hashes, inventory=None):
    path = Path(path)
    h = digest(path)
    if inventory is not None and inventory.get(str(path)) != h:
        raise ValueError("REPAIR_FROZEN_SOURCE_HASH")
    hashes[str(path)] = h
    return path


def _json(path, hashes, inventory=None):
    path = _read(path, hashes, inventory)
    value = json.loads(path.read_text())
    if digest(path) != hashes[str(path)]:
        raise ValueError("REPAIR_SOURCE_CHANGED")
    return value


def _pickle(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    pending = path.with_suffix(path.suffix + ".pending")
    with pending.open("wb") as stream:
        pickle.dump(value, stream, protocol=pickle.HIGHEST_PROTOCOL)
    os.link(pending, path)  # Atomic publication, refuses overwriting a final file.
    pending.unlink()


def _fixed_json(path, value):
    """Resume a completed receipt only if its complete content is identical."""
    path = Path(path)
    if path.exists():
        if object_hash(json.loads(path.read_text())) != object_hash(value):
            raise ValueError("REPAIR_RECEIPT_CHANGED_ON_RESUME")
    else:
        write_json(path, value)


def _unpickle(path):
    # Only generated private packet inputs/checkpoints or S0-hashed legacy models.
    with Path(path).open("rb") as stream:
        return pickle.load(stream)


def _save_partition(folder, left, right, y, groups, train, validation, scope, kind):
    """One transform fit shared across this split's models/alpha grid."""
    candidate_class_weights(y[train], groups[train])
    candidate_class_weights(y[validation], groups[validation])
    scope.assert_fit_groups(groups[train])
    scalers = [CandidateTabularScaler().fit(x[train], groups[train], scope)
               for x in ((left, right) if kind == "C2_R" else (left,))]
    a = scalers[0].transform(left[train])
    va = scalers[0].transform(left[validation])
    pca = None
    if kind == "E0_R":
        pca = CandidateWeightedPCA(32).fit(a, groups[train], scope)
        a, va = pca.transform(a), pca.transform(va)
        b, vb = np.empty((len(train), 0)), np.empty((len(validation), 0))
    else:
        b, vb = scalers[1].transform(right[train]), scalers[1].transform(right[validation])
    folder.mkdir(mode=0o700)
    np.savez(folder / "train.npz", left=a, right=b, y=y[train], groups=groups[train])
    # Validation arrays are never loaded by a model-fitting call.
    np.savez(folder / "evaluation.npz", left=va, right=vb, indices=validation)
    _pickle(folder / "transform.pkl", dict(scalers=scalers, pca=pca, scope=scope))
    write_json(folder / "receipt.json", dict(scope=asdict(scope), scope_hash=scope.hash,
        train_data_hash=digest(folder / "train.npz"), evaluation_data_hash=digest(folder / "evaluation.npz"),
        transform_hash=digest(folder / "transform.pkl"), kind=kind))


def prepare_case(folder, left, right, rows, train, test, scope, *, kind, metadata,inner_definitions=None):
    """Freeze three training-group folds and full-fit transforms, no heads."""
    folder = Path(folder)
    if kind not in ("C2_R", "E0_R"):
        raise ValueError("REPAIR_CASE_KIND")
    if folder.exists():
        raise FileExistsError("REPAIR_CASE_EXISTS")
    left = np.asarray(left, float)
    y = rows.stimulus_local_id.to_numpy(int)
    groups = (rows.split_group_id if kind == "C2_R" else rows.filter_block_id).to_numpy(str)
    if (left.ndim != 2 or len(left) != len(rows) or not np.isfinite(left).all() or
            not rows.trial_id.is_unique or not np.isin(y, [0, 1]).all()):
        raise ValueError("REPAIR_CASE_SCHEMA")
    if set(train) & set(test) or set(train) | set(test) != set(range(len(rows))):
        raise ValueError("REPAIR_OUTER_PARTITION")
    if set(groups[train]) != set(scope.train_groups) or set(groups[test]) != set(scope.test_groups):
        raise ValueError("REPAIR_CASE_SCOPE")
    if kind == "C2_R":
        left, right = old_c._pair_arrays(left, right)
    folder.mkdir(mode=0o700)
    rows.iloc[test].reset_index(drop=True).to_parquet(folder / "test_rows.parquet", index=False)
    np.savez(folder / "training_labels.npz", y=y[train], groups=groups[train], trial_ids=rows.trial_id.to_numpy(str)[train])
    specs = old_c.MODEL_SPECS if kind == "C2_R" else (("MLP32", "native", 32),)
    if inner_definitions is None:
        inner_splits=list(GroupKFold(3).split(left[train],y[train],groups[train]))
    else:
        if len(inner_definitions)!=3:raise ValueError('REPAIR_FROZEN_INNER_COUNT')
        inner_splits=[]
        for definition in inner_definitions:
            tr=np.flatnonzero(np.isin(groups[train],definition['fit_groups']))
            va=np.flatnonzero(np.isin(groups[train],definition['validation_groups']))
            if set(tr)&set(va) or set(tr)|set(va)!=set(range(len(train))):raise ValueError('REPAIR_FROZEN_INNER_PARTITION')
            inner_splits.append((tr,va))
    for inner, (tr, va) in enumerate(inner_splits):
        inner_scope = FitScope(tuple(np.unique(groups[train][tr])), tuple(np.unique(groups[train][va])), scope.test_groups)
        if inner_definitions is not None and inner_scope.hash!=inner_definitions[inner]['scope_hash']:
            raise ValueError('REPAIR_FROZEN_INNER_SCOPE_HASH')
        _save_partition(folder / f"inner{inner}", left[train], None if right is None else right[train],
                        y[train], groups[train], tr, va, inner_scope, kind)
    _save_partition(folder / "final", left, right, y, groups, train, test, scope, kind)
    case = dict(metadata, key=folder.name, kind=kind, specs=list(specs), scope=asdict(scope),
                train_rows=len(train), test_rows=len(test), training_groups=len(scope.train_groups),
                test_groups=len(scope.test_groups), inner_encoder_refitted=False)
    write_json(folder / "case.json", case)
    return case


def neural_members(cases):
    result = []
    for case in cases:
        for family, view, width in case["specs"]:
            if not width:
                continue
            for part in ("inner0", "inner1", "inner2", "final"):
                for alpha in C_GRID:
                    key = f'{case["key"]}__{family}__{view}__{part}__a{str(alpha).replace(".", "p")}'
                    result.append(dict(key=key, case=case["key"], family=family, view=view,
                                       width=width, part=part, alpha=alpha))
    if len({m["key"] for m in result}) != len(result):
        raise ValueError("REPAIR_DUPLICATE_MEMBER")
    return result


def _partition(case_root, member, *, evaluation=False):
    folder = case_root / member["case"] / member["part"]
    receipt = json.loads((folder / "receipt.json").read_text())
    path = folder / ("evaluation.npz" if evaluation else "train.npz")
    key = "evaluation_data_hash" if evaluation else "train_data_hash"
    if digest(path) != receipt[key]:
        raise ValueError("REPAIR_PREPARED_INPUT_MUTATION")
    with np.load(path, allow_pickle=False) as arrays:
        a, b = arrays["left"], arrays["right"]
        x = a if member["view"] == "native" else old_c.compose_view(a, b, member["view"])
        if evaluation:
            return x, arrays["indices"], receipt
        y, groups = arrays["y"], arrays["groups"]
        return x, y, candidate_class_weights(y, groups), receipt


def _member_pass(case_root, states, member, steps, *, device):
    saved = states / f'{member["key"]}_{steps}.pkl'
    diagnostic = states / f'{member["key"]}_{steps}.json'
    if diagnostic.exists():
        result = json.loads(diagnostic.read_text())
        if result.get("state_sha256") and digest(saved) != result["state_sha256"]:
            raise ValueError("REPAIR_CHECKPOINT_MUTATION")
        return result
    x, y, weights, receipt = _partition(case_root, member)
    recovered = saved.exists()
    if recovered:
        state = _unpickle(saved)
        if (state.steps != steps or state.fit_scope_hash != receipt["scope_hash"] or
                state.fit_input_hash != _fit_input_hash(x, y, weights)):
            raise ValueError("REPAIR_RECOVERED_CHECKPOINT_SCOPE")
    elif steps == 1000:
        state = start_fit(x, y, weights, width=member["width"], alpha=member["alpha"],
                          seed=11, device=device, fit_scope_hash=receipt["scope_hash"])
    else:
        previous = states / f'{member["key"]}_1000.pkl'
        if not previous.exists():
            result = dict(member, status="OPTIMIZATION_UNRESOLVED", steps=0, attempted_budget=steps,
                          reason="initial_numerical_failure_no_resumable_state")
            write_json(diagnostic, result)
            return result
        state = _unpickle(previous)
    try:
        result = stability(state) if recovered else advance_fit(state, x, y, weights, target_steps=steps,
                                                                 fit_scope_hash=receipt["scope_hash"])
        training_logits = _scores(state, x)
    except (RuntimeError, FloatingPointError, ValueError) as error:
        # Preserve and isolate numerical failures; schema/ValueError stays fail-fast.
        if isinstance(error, ValueError) and str(error) not in ("OPTIMIZATION_NONFINITE", "FINAL_OPTIMIZATION_NONFINITE", "REPAIR_PREDICTION_NONFINITE"):
            raise
        if isinstance(error, RuntimeError) and "non-finite" not in str(error).lower() and "nonfinite" not in str(error).lower():
            raise
        result = dict(status="OPTIMIZATION_UNRESOLVED", steps=state.steps,
                      attempted_history_steps=len(state.history), reason="nonfinite_training_numerics")
        (states / f'{member["key"]}_{steps}_failure.txt').write_text(traceback.format_exc())
        failed_state = states / f'{member["key"]}_{steps}_failed.pkl'
        _pickle(failed_state, state)
        result["failed_state_sha256"] = digest(failed_state)
    else:
        if not recovered:
            _pickle(saved, state)
        result["state_sha256"] = digest(saved)
        logits_path = states / f'{member["key"]}_{steps}_training_logits.npy'
        np.save(logits_path, training_logits, allow_pickle=False)
        result["training_logits_sha256"] = digest(logits_path)
    result.update(member, attempted_budget=steps, fit_scope_hash=receipt["scope_hash"], fit_input_hash=state.fit_input_hash)
    write_json(diagnostic, result)
    return result


def fit_neural_family(case_root, states, members, *, device="cpu"):
    """Global two-pass barrier; this API has no held-out prediction callback."""
    states.mkdir(mode=0o700, exist_ok=True)
    initial = [_member_pass(case_root, states, m, 1000, device=device) for m in members]
    budget = family_budget(initial)
    decision = dict(steps=budget, members=len(members), extend_all=budget == 2000,
                    decision_inputs="training optimization diagnostics only", alpha_selection_started=False)
    decision_path = states / "family_decision.json"
    if decision_path.exists() and json.loads(decision_path.read_text()) != decision:
        raise ValueError("REPAIR_FAMILY_DECISION_CHANGED")
    if not decision_path.exists():
        write_json(decision_path, decision)
    final = initial if budget == 1000 else [_member_pass(case_root, states, m, 2000, device=device) for m in members]
    complete = len(final) == len(members) and all(d["status"] == "OPTIMIZATION_STABLE" and d["steps"] == budget for d in final)
    return dict(status="OPTIMIZATION_STABLE" if complete else "INCOMPLETE_PRIMARY_MATRIX",
                budget=budget, initial=initial, final=final, neural_fits=len(members),
                continuation_fits=0, extended_members=len(members) if budget == 2000 else 0)


def _scores(state, x):
    device = next(state.model.parameters()).device
    with torch.no_grad():
        chunks = [state.model(torch.as_tensor(x[i:i+8192], dtype=torch.float64, device=device)).cpu().numpy()
                  for i in range(0, len(x), 8192)]
    score = np.concatenate(chunks)
    if not np.isfinite(score).all():
        raise ValueError("REPAIR_PREDICTION_NONFINITE")
    return np.c_[-score / 2, score / 2]


def select_neural_models(case_root, states, cases, members, family):
    require_complete_family(family["final"], len(members), family["budget"])
    selected = {}
    for case in cases:
        with np.load(case_root / case["key"] / "training_labels.npz", allow_pickle=False) as labels:
            y, groups = labels["y"], labels["groups"]
        scope = FitScope(**{k: tuple(v) for k, v in case["scope"].items()})
        for name, view, width in case["specs"]:
            if not width:
                continue
            matching = [m for m in members if m["case"] == case["key"] and m["family"] == name and m["view"] == view]
            oof = {a: np.full((len(y), 2), np.nan) for a in C_GRID}
            for member in matching:
                if member["part"] == "final":
                    continue
                x, index, _ = _partition(case_root, member, evaluation=True)
                state = _checked_state(states, member["key"], family["budget"])
                oof[member["alpha"]][index] = _scores(state, x)
            chosen, losses = select_alpha(oof, y, groups)
            calibration = fit_temperature(oof[chosen], y, groups, scope)
            final = next(m for m in matching if m["part"] == "final" and m["alpha"] == chosen)
            receipt = dict(case=case["key"], family=name, view=view, alpha=chosen, inner_ce_bits=losses,
                calibration=calibration, temperature=calibration["temperature"], selected_state=final["key"],
                budget=family["budget"], scope_hash=scope.hash, all_final_alphas_fitted=True,
                inner_encoder_refitted=False, fit_count_including_unselected=16)
            target = case_root / case["key"] / f'{name}_{view}_selection.json'
            if target.exists() and json.loads(target.read_text()) != json.loads(json.dumps(receipt)):
                raise ValueError("REPAIR_SELECTION_CHANGED_ON_RESUME")
            if not target.exists():
                write_json(target, receipt)
                np.savez(target.with_suffix(".npz"), **{f'alpha_{a}': oof[a] for a in C_GRID})
            selected[case["key"], name, view] = receipt
    return selected


def _checked_state(states, key, budget):
    path = states / f"{key}_{budget}.pkl"
    receipt = json.loads(path.with_suffix(".json").read_text())
    if receipt["status"] != "OPTIMIZATION_STABLE" or digest(path) != receipt["state_sha256"]:
        raise ValueError("REPAIR_CHECKPOINT_MUTATION_OR_UNSTABLE")
    state = _unpickle(path)
    if state.steps != budget or state.fit_scope_hash != receipt["fit_scope_hash"] or state.fit_input_hash != receipt["fit_input_hash"]:
        raise ValueError("REPAIR_CHECKPOINT_SCOPE")
    return state


def _source_context(registry, source_run, contract_run, hashes):
    source_run = _name(source_run or registry["preflight_run"])
    contract_run = _name(contract_run or registry["repair_contract_run"])
    gate = ROOT / "private/auditory_next_v2" / source_run
    complete = _json(gate / "completion.json", hashes)
    contracts = _json(ROOT / "private/auditory_next_v2" / contract_run / "completion.json", hashes)
    if complete["status"] != "PASS" or contracts["status"] != "PASS" or contracts["objective_parity"]["status"] != "PASS":
        raise ValueError("REPAIR_PREFLIGHT_OR_OBJECTIVE_PARITY_GATE")
    inventory = {r["path"]: r["sha256"] for r in _json(gate / "legacy_input_hashes.json", hashes)}
    scopes = _json(gate / "feature_scope_registry.json", hashes)
    planpath, splitpath = ROOT / registry["legacy_plan"], ROOT / registry["legacy_splits"]
    plan, split = _json(planpath, hashes, inventory), _json(splitpath, hashes, inventory)
    if digest(planpath) != registry["legacy_plan_sha256"] or digest(splitpath) != registry["legacy_split_sha256"] or plan["split_hash"] != digest(splitpath):
        raise ValueError("REPAIR_PLAN_SPLIT_HASH")
    support_path = _read(splitpath.parent / "support.parquet", hashes, inventory)
    return planpath, plan, split, pd.read_parquet(support_path), inventory, scopes


def _prepare_c(case_root, planpath, plan, split, support, modes, inventory, scopes, hashes):
    cases = []
    for mode in modes:
        prior_root=ROOT/'private/auditory5_v1/routes'/('C_linear_SIM_001' if mode=='R_SIM' else 'C_linear_L0_SUP_RAND_002')
        prior_path=prior_root/'fit_scopes.json'
        prior_scopes=_json(prior_path,hashes,inventory if str(prior_path) in inventory else None)
        for fold in split["folds"]:
            old_definitions=[r for r in prior_scopes if r['representation']==mode and r['outer_fold']==fold['outer_fold']]
            if len(old_definitions)!=5 or len({object_hash(r['inner_folds']) for r in old_definitions})!=1:
                raise ValueError('REPAIR_C_FROZEN_INNER_CONSISTENCY')
            frozen_inner=old_definitions[0]['inner_folds']
            for branch in ("left", "right"):
                tasks = [t for t in plan["tasks"] if t["stage"] == "outer" and t["mode"] == mode and
                         t["outer_fold"] == fold["outer_fold"] and t["branch"] == branch]
                if len(tasks) != 1:
                    raise ValueError("REPAIR_EXPLICIT_BRANCH_TASK")
                task = tasks[0]
                audit = [r for r in scopes if r["task"] == task["name"]]
                expected = set(fold["train_groups"]) & set(support.loc[support.C, "split_group_id"])
                if (len(audit) != 1 or audit[0]["status"] != "PASS" or set(audit[0]["fit_groups"]) != expected or
                        audit[0]["validation_groups"] or set(audit[0]["test_groups"]) != set(fold["test_groups"])):
                    raise ValueError("REPAIR_ENCODER_SCOPE")
                directory = planpath.parent / "outputs" / _name(task["name"])
                for filename in ("features.npz", "feature_rows.parquet", "task.json", "completion.json"):
                    _read(directory / filename, hashes, inventory)
                if mode != "L0":
                    _read(directory / "encoder.pt", hashes, inventory)
            left, right, rows, scope, sources = old_c._load_pair(plan, planpath, fold, mode, support)
            if any(inventory.get(path) != h for path, h in sources.items()):
                raise ValueError("REPAIR_LEGACY_PAIR_CHANGED")
            hashes.update(sources)
            train = np.flatnonzero(rows.split_group_id.isin(scope.train_groups))
            test = np.flatnonzero(rows.split_group_id.isin(scope.test_groups))
            head_scope = FitScope(tuple(np.unique(rows.split_group_id.to_numpy(str)[train])),
                                  test_groups=tuple(np.unique(rows.split_group_id.to_numpy(str)[test])))
            cases.append(prepare_case(case_root / f'{mode}_outer{fold["outer_fold"]}', left, right, rows,
                train, test, head_scope,inner_definitions=frozen_inner, kind="C2_R", metadata=dict(mode=mode, fold=int(fold["outer_fold"]),
                source_scope_hash=scope.hash, source_feature_hashes=sources)))
    return cases, None


def _prepare_e(case_root, registry, inventory, hashes):
    legacy = ROOT / registry["legacy_e0"]
    support = pd.read_parquet(_read(legacy / "support.parquet", hashes, inventory))
    if support.empty or not support.record_id.is_unique:
        raise ValueError("REPAIR_E0_REQUEST_SCHEMA")
    eligible = support[support.status.eq("PASS")]
    if len(eligible) != 16 or not set(eligible.task) <= {"puretone", "bapa"}:
        raise ValueError("REPAIR_E0_FROZEN_16_RECORD_SUPPORT")
    # This explicit source was not necessarily in S0's feature inventory: retain
    # its own exact hash and require the original E0 request set to agree.
    pairs_path = ROOT / "private/auditory5_v1/data/manifest_001/E_existing_pairs.parquet"
    pairs = pd.read_parquet(_read(pairs_path, hashes), columns=["participant_id", "container_a", "container_b"])
    if set(pairs.container_a) | set(pairs.container_b) != set(support.record_id):
        raise ValueError("REPAIR_E0_REQUESTS_CHANGED")
    source_candidates = support.set_index("record_id").candidate_id
    for pair in pairs.to_dict("records"):
        if any(source_candidates.loc[rid] != pair["participant_id"] for rid in (pair["container_a"], pair["container_b"])):
            raise ValueError("REPAIR_E0_PAIR_IDENTITY_CHANGED")
    cases = []
    for row in eligible.to_dict("records"):
        rid = _name(row["record_id"])
        folder = ROOT / "private/auditory5_v1/data/mff_e0_export_001/P1_CAUSAL20" / rid
        summary = _json(folder / "summary.json", hashes, inventory)
        if (summary.get("within_record_filter_state_isolation") is not True or
                summary["preprocessing_id"] != "P1_CAUSAL_NATIVE" or summary["physical_channels"] != 128 or
                summary["processed_fs"] != 250):
            raise ValueError("REPAIR_E0_NATIVE_ISOLATED_128_REQUIRED")
        for name, expected in summary["output_sha256"].items():
            if digest(_read(folder / name, hashes, inventory)) != expected:
                raise ValueError("REPAIR_E0_EXPORT_CHANGED")
        events = pd.read_parquet(folder / "events.parquet")
        accepted = events[events.accepted].reset_index(drop=True)
        keep, folds = old_e.block_folds(accepted)
        if (len(folds) != 4 or len(accepted) != row["accepted_before_block_support"] or
                int(keep.sum()) != row["retained_for_decoding"]):
            raise ValueError("REPAIR_E0_BLOCK_SUPPORT_CHANGED")
        rows = accepted.loc[keep].reset_index(drop=True)
        arrays = np.load(folder / "all.npy", mmap_mode="r")
        if arrays.shape[1] != 128:
            raise ValueError("REPAIR_E0_CHANNEL_COUNT")
        x = np.empty((len(rows), 128 * 20), dtype=np.float64)
        for first in range(0, len(rows), 32):
            batch = rows.iloc[first:first+32]
            epochs = arrays[batch.stored_epoch_index.to_numpy(int)]
            starts = batch.post_start_index.to_numpy(int)
            if np.any(starts < 0) or np.any(starts + 100 > epochs.shape[-1]):
                raise ValueError("REPAIR_E0_POST_WINDOW_SAMPLE_BOUNDS")
            x[first:first+len(batch)] = bin_20ms(np.stack([v[:, j:j+100] for v, j in zip(epochs, starts)]))
        del arrays
        linear_path = _read(legacy / f"{rid}_linear_oof.parquet", hashes, inventory)
        linear_rows = pd.read_parquet(linear_path)
        if set(linear_rows.calibration) != {"raw", "calibrated"} or not linear_rows.family.eq("linear").all():
            raise ValueError("REPAIR_E0_LEGACY_LINEAR_MATRIX")
        for calibration, part in linear_rows.groupby("calibration"):
            if not part.trial_id.is_unique or set(part.trial_id) != set(rows.trial_id):
                raise ValueError("REPAIR_E0_LEGACY_LINEAR_TRIALS")
            aligned = part.set_index("trial_id").loc[rows.trial_id]
            for column in ("record_id", "candidate_id", "split_group_id", "stimulus_local_id", "filter_block_id"):
                if not np.array_equal(aligned[column].to_numpy(), rows[column].to_numpy()):
                    raise ValueError("REPAIR_E0_LEGACY_LINEAR_METADATA")
        groups = rows.filter_block_id.to_numpy(str)
        # Reuse actual stored assignments. GroupKFold recomputation can assign
        # equal-size blocks differently across numerical runtimes; matching
        # the old model requires the recorded partitions, not a new sort tie.
        raw_linear=linear_rows[linear_rows.calibration.eq('raw')]
        if set(raw_linear.fold)!={0,1,2,3}:raise ValueError('REPAIR_E0_FROZEN_OUTER_COUNT')
        folds=[]
        for fold in range(4):
            ids=set(raw_linear.loc[raw_linear.fold.eq(fold),'trial_id'])
            te=np.flatnonzero(rows.trial_id.isin(ids).to_numpy());tr=np.flatnonzero(~rows.trial_id.isin(ids).to_numpy())
            if set(groups[tr])&set(groups[te]):raise ValueError('REPAIR_E0_FROZEN_BLOCK_OVERLAP')
            folds.append((tr,te))
        for fold, (tr, te) in enumerate(folds):
            scope = FitScope(tuple(np.unique(groups[tr])), test_groups=tuple(np.unique(groups[te])))
            original = _unpickle(_read(legacy / f"{rid}_linear_fold{fold}.pkl", hashes, inventory))
            if original["scope"].hash != scope.hash or original["within_record_only"] is not True:
                raise ValueError("REPAIR_E0_LEGACY_LINEAR_SCOPE")
            probe = original["model"]
            if (probe.input_shape != (2560,) or probe.seed != 11 or probe.fit_scopes["scope_hash"] != scope.hash or
                    set(probe.scaler.fit_groups_) != set(scope.train_groups) or probe.pca is None or
                    probe.pca.max_components != 32 or set(probe.pca.fit_groups_) != set(scope.train_groups)):
                raise ValueError("REPAIR_E0_LEGACY_LINEAR_ESTIMATOR")
            if set(linear_rows.loc[linear_rows.fold.eq(fold), "trial_id"]) != set(rows.iloc[te].trial_id):
                raise ValueError("REPAIR_E0_LEGACY_LINEAR_FOLDS")
            cases.append(prepare_case(case_root / f"{rid}_outer{fold}", x, None, rows, tr, te, scope,inner_definitions=probe.fit_scopes['inner_folds'],
                kind="E0_R", metadata=dict(record_id=rid, candidate_id=row["candidate_id"], task=row["task"],
                fold=fold, mode="native128", legacy_linear=str(linear_path),
                legacy_linear_sha256=hashes[str(linear_path)])))
    return cases, dict(support=support, pairs=pairs)


def _fit_linear(case_root, model_root, cases, *, seed):
    selected = {}
    for case in cases:
        with np.load(case_root / case["key"] / "training_labels.npz", allow_pickle=False) as arrays:
            y, groups = arrays["y"], arrays["groups"]
        scope = FitScope(**{k: tuple(v) for k, v in case["scope"].items()})
        for name, view, width in case["specs"]:
            if width:
                continue
            oof = {a: np.full((len(y), 2), np.nan) for a in C_GRID}
            for part in ("inner0", "inner1", "inner2"):
                member = dict(case=case["key"], part=part, view=view)
                x, labels, _, receipt = _partition(case_root, member)
                with np.load(case_root / case["key"] / part / "train.npz", allow_pickle=False) as arrays:
                    train_groups = arrays["groups"]
                vx, index, _ = _partition(case_root, member, evaluation=True)
                for c in C_GRID:
                    path = model_root / f'{case["key"]}_{view}_{part}_C{c}.pkl'
                    if path.exists():
                        saved = _unpickle(path)
                        if saved["input_hash"] != receipt["train_data_hash"] or saved["scope_hash"] != receipt["scope_hash"]:
                            raise ValueError("REPAIR_LINEAR_RESUME_SCOPE")
                        head = saved["head"]
                    else:
                        head = _fit_head(x, labels, train_groups, c, seed)
                        _pickle(path, dict(head=head, C=c, scope_hash=receipt["scope_hash"], input_hash=receipt["train_data_hash"]))
                    oof[c][index] = _head_logits(head, vx)
            weights = candidate_class_weights(y, groups)
            losses = {c: weighted_log_loss_nats(oof[c], y, weights) for c in C_GRID}
            chosen = min(C_GRID, key=lambda c: (losses[c], c))
            calibration = fit_temperature(oof[chosen], y, groups, scope)
            member = dict(case=case["key"], part="final", view=view)
            x, labels, _, receipt = _partition(case_root, member)
            path = model_root / f'{case["key"]}_{view}_final_C{chosen}.pkl'
            if path.exists():
                saved = _unpickle(path)
                if saved["input_hash"] != receipt["train_data_hash"] or saved["scope_hash"] != receipt["scope_hash"]:
                    raise ValueError("REPAIR_LINEAR_RESUME_SCOPE")
            else:
                _pickle(path, dict(head=_fit_head(x, labels, groups, chosen, seed), C=chosen,
                    input_hash=receipt["train_data_hash"], scope_hash=receipt["scope_hash"]))
            result = dict(case=case["key"], family=name, view=view, C=chosen,
                temperature=calibration["temperature"], calibration=calibration, head_file=str(path),
                scope_hash=scope.hash, inner_ce_bits={str(c): float(v / np.log(2)) for c, v in losses.items()}, fit_count=13)
            selected[case["key"], name, view] = result
    return selected


def _selected_scores(case_root, states, case, family, view, selection, condition=None, donors=None):
    member = dict(case=case["key"], part="final", view=view)
    x, _, _ = _partition(case_root, member, evaluation=True)
    if condition is not None:
        if view not in ("C_LR", "C_LL", "C_RR") or condition not in old_c.INTERVENTIONS:
            raise ValueError("REPAIR_FIXED_HEAD_INTERVENTION")
        slot = slice(0, x.shape[1] // 2) if condition.endswith("first") else slice(x.shape[1] // 2, x.shape[1])
        x = x.copy()
        if condition.startswith("zero"):
            x[:, slot] = 0
        else:
            if donors is None or np.shape(donors) != (len(x),) or np.any(donors < 0):
                raise ValueError("REPAIR_DONOR_SUPPORT")
            x[:, slot] = x[donors, slot]
    if family == "linear":
        logits = _head_logits(_unpickle(selection["head_file"])["head"], x)
    else:
        state = _checked_state(states, selection["selected_state"], selection["budget"])
        logits = _scores(state, x)
    return dict(raw=softmax(logits, axis=1), calibrated=softmax(logits / selection["temperature"], axis=1))


def _score_c(dest, public, cases, selected, family, *, seed):
    case_root, states = dest / "cases", dest / "states"
    prediction_dir = dest / "predictions"
    prediction_dir.mkdir(mode=0o700, exist_ok=True)
    losses, missing = [], []
    for case in cases:
        rows = pd.read_parquet(case_root / case["key"] / "test_rows.parquet")
        conditions = {"none": None, "zero_first": None, "zero_second": None}
        for kind, opposite in (("same_class", False), ("opposite_class", True)):
            donors = old_c.replacement_indices(rows, opposite=opposite, seed=seed)
            if np.any(donors < 0):
                missing.append(f'{case["mode"]} fold {case["fold"]} {kind} donor support')
            else:
                conditions[kind + "_first"] = conditions[kind + "_second"] = donors
        for condition, donors in conditions.items():
            path = prediction_dir / f'{case["key"]}_{condition}.parquet'
            if path.exists():
                frame = pd.read_parquet(path)
            else:
                pieces = []
                for name, view, _ in case["specs"]:
                    if condition != "none" and view not in ("C_LR", "C_LL", "C_RR"):
                        continue
                    result = selected[case["key"], name, view]
                    p = _selected_scores(case_root, states, case, name, view, result,
                        None if condition == "none" else condition, donors)
                    pieces.append(old_c._prediction_rows(rows, p, mode=case["mode"], fold=case["fold"],
                        family=name, view=view, intervention=condition, donor=donors))
                frame = pd.concat(pieces, ignore_index=True)
                frame.to_parquet(path, index=False)
            losses.extend(old_c._candidate_losses(frame))
    table = pd.DataFrame(losses)
    table.to_parquet(dest / "candidate_losses.parquet", index=False)
    gains, interventions = old_c.summarize_losses(table, seed)
    pd.DataFrame(gains).to_csv(public / "single_joint_gains.csv", index=False)
    pd.DataFrame(interventions).to_csv(public / "fixed_head_interventions.csv", index=False)
    # The legacy R_SUP/L0 matrix and raw-isolation gates remain separately needed.
    verdict = old_c.screen(gains, missing + ["complete parallel L0/R_SUP repair and inherited raw-isolation audit"])
    return dict(results=gains, fixed_head_interventions=interventions, missing_controls=verdict["missing_controls"],
        core_status="COMPLETE_REPAIRED_MATRIX", scientific_status="NOT_EVALUABLE",
        candidates=int(table.split_group_id.nunique()), controls_status="PARTIAL")


def _score_e(dest, public, cases, selected, extra, hashes, inventory):
    case_root, states = dest / "cases", dest / "states"
    prediction_dir = dest / "predictions"
    prediction_dir.mkdir(mode=0o700, exist_ok=True)
    pieces = []
    for case in cases:
        path = prediction_dir / f'{case["key"]}_MLP32.parquet'
        if path.exists():
            pieces.append(pd.read_parquet(path))
            continue
        rows = pd.read_parquet(case_root / case["key"] / "test_rows.parquet")
        probabilities = _selected_scores(case_root, states, case, "MLP32", "native",
            selected[case["key"], "MLP32", "native"])
        parts = []
        for calibration, p in probabilities.items():
            part = rows[["trial_id", "record_id", "candidate_id", "split_group_id", "stimulus_local_id", "filter_block_id"]].copy()
            part["task"], part["fold"], part["family"], part["calibration"] = case["task"], case["fold"], "MLP32", calibration
            part["p0"], part["p1"] = p[:, 0], p[:, 1]
            parts.append(part)
        frame = pd.concat(parts, ignore_index=True)
        frame.to_parquet(path, index=False)
        pieces.append(frame)
    for path in sorted({case["legacy_linear"] for case in cases}):
        pieces.append(pd.read_parquet(_read(Path(path), hashes, inventory)))
    frame = pd.concat(pieces, ignore_index=True)
    frame.to_parquet(dest / "oof_predictions.parquet", index=False)
    expected = set(extra["support"].loc[extra["support"].status.eq("PASS"), "record_id"])
    score_rows = []
    for (rid, model, calibration), rows in frame.groupby(["record_id", "family", "calibration"]):
        if not rows.trial_id.is_unique:
            raise ValueError("REPAIR_E0_DUPLICATE_OOF")
        metric = classification_metrics(rows.stimulus_local_id.to_numpy(), rows[["p0", "p1"]].to_numpy(),
            rows.candidate_id.to_numpy(), rows.trial_id.to_numpy())
        score_rows.append(dict(record_id=rid, family=model, calibration=calibration,
                              candidate_id=rows.candidate_id.iloc[0], task=rows.task.iloc[0], **metric))
    scores = pd.DataFrame(score_rows)
    scores.to_parquet(dest / "record_metrics.parquet", index=False)
    aggregates = []
    for (model, calibration), rows in scores.groupby(["family", "calibration"]):
        if set(rows.record_id) != expected:
            raise ValueError("REPAIR_E0_INCOMPLETE_FAMILY")
        lookup = rows.set_index("record_id")
        pairs = [p for p in extra["pairs"].to_dict("records") if p["container_a"] in expected and p["container_b"] in expected]
        for task in ("puretone", "bapa"):
            values, groups = [], []
            for pair in pairs:
                matching = [rid for rid in (pair["container_a"], pair["container_b"]) if lookup.loc[rid, "task"] == task]
                if len(matching) != 1:
                    raise ValueError("REPAIR_E0_PAIR_TASK_SCHEMA")
                values.append(float(lookup.loc[matching[0], "ce_bits"]))
                groups.append(pair["participant_id"])
            if values:
                aggregates.append(dict(family=model, calibration=calibration, task=task, complete_pairs=len(pairs),
                    mean_CE_bits=float(np.mean(values)), J_bits_interval=paired_cluster_bootstrap(
                        np.ones(len(values)), values, groups, n_boot=2000, seed=20260917)))
    _fixed_json(public / "e0_aggregate.json", aggregates)
    return dict(results=aggregates, core_status="COMPLETE_REPAIRED_MATRIX", scientific_status="NOT_EVALUABLE",
        records_requested=len(extra["support"]), records_with_block_support=len(expected),
        family_status={"linear": "COMPLETE_REUSED", "MLP32": "COMPLETE_REPAIRED"},
        source_scope="mixed MFF sources; not all CI", E1_status="NOT_STARTED", controls_status="DESCRIPTIVE_WITHIN_RECORD")


def run(config, registry, site, dest, public, report, packet, *, modes=("R_SIM",), source_run=None, contract_run=None, smoke=False):
    """Run one complete packet; resumes only its own saved identical inputs.

    Directories and immutable source snapshot must be created by the parent
    executor. Public receipts contain no original IDs, paths or model keys.
    ``contract_run`` names a completed v2 objective-parity gate; it is required.
    """
    require_slurm()
    dest, public, report = map(Path, (dest, public, report))
    for path, base in ((dest, "private"), (public, "results"), (report, "reports")):
        if not path.resolve().is_relative_to(ROOT / base / "auditory_next_v2"):
            raise ValueError("REPAIR_OUTPUT_ROOT")
    if (dest / "completion.json").exists():
        raise FileExistsError("REPAIR_COMPLETED_RUN_IMMUTABLE")
    if packet not in ("C2_R", "E0_R") or not modes or len(set(modes)) != len(modes) or not set(modes) <= {"R_SIM", "R_SUP", "L0"}:
        raise ValueError("REPAIR_PACKET_OR_MODES")
    if packet == "E0_R" and tuple(modes) != ("R_SIM",):
        raise ValueError("REPAIR_E0_HAS_NO_ENCODER_MODE_ARGUMENT")
    ro = config["readouts"]
    if (ro["legacy_C_or_alpha_grid"] != list(C_GRID) or ro["repair_solver"] != "torch_adam_full_batch" or
            ro["precision"] != "float64" or ro["seed"] != 11 or ro["steps_initial"] != 1000 or
            ro["steps_extension_once"] != 1000 or ro["schedule_horizon_steps"] != 2000 or ro["learning_rate"] != .001):
        raise ValueError("REPAIR_FROZEN_SOLVER_CONFIG")
    hashes = {}
    planpath, plan, split, support, inventory, scopes = _source_context(registry, source_run, contract_run, hashes)
    contract = dict(packet=packet, modes=list(modes), config_hash=object_hash(config), registry_hash=object_hash(registry),
        plan_hash=digest(planpath), source_gate=source_run or registry["preflight_run"],
        contract_gate=contract_run or registry["repair_contract_run"], seed=11, linear_seed=int(split["seed"]),
        final_alpha_grid_all_fitted=True, alpha_selection="after global final-budget stability gate",
        neural_family="all neural specs and all requested folds/records in this packet",
        fit_counts=fit_counts(packet, modes=len(modes)), objective="legacy_weighted_BCE_explicit_alpha_L2",
        temperature_bounds=[.25, 4], clinical_inputs=False, new_encoder_fits=0,
        estimator_status="SOLVER_REPAIR", fit_scope="frozen outer encoders; head/scaler inner GroupKFold3 only")
    contract_path = dest / "repair_definition.json"
    if contract_path.exists() and json.loads(contract_path.read_text()) != contract:
        raise ValueError("REPAIR_CONTRACT_CHANGED_ON_RESUME")
    if not contract_path.exists():
        write_json(contract_path, contract)
    prepared = dest / "prepared.pkl"
    if prepared.exists():
        data = _unpickle(prepared)
        cases, extra = data["cases"], data["extra"]
        for path, old in data["input_hashes"].items():
            if digest(Path(path)) != old:
                raise ValueError("REPAIR_INPUT_CHANGED_ON_RESUME")
        hashes.update(data["input_hashes"])
        for path, old in data["prepared_hashes"].items():
            if digest(Path(path)) != old:
                raise ValueError("REPAIR_PREPARED_CASE_CHANGED_ON_RESUME")
    else:
        case_root = dest / "cases"
        case_root.mkdir(mode=0o700)
        cases, extra = (_prepare_c(case_root, planpath, plan, split, support, modes, inventory, scopes, hashes)
                        if packet == "C2_R" else _prepare_e(case_root, registry, inventory, hashes))
        prepared_hashes = {str(p): digest(p) for p in case_root.rglob("*") if p.is_file()}
        data = dict(cases=cases, extra=extra, input_hashes=hashes, prepared_hashes=prepared_hashes)
        _pickle(prepared, data)
    members = neural_members(cases)
    expected = contract["fit_counts"]
    if len(members) != expected["neural"]:
        raise ValueError("REPAIR_FROZEN_FIT_COUNT_MISMATCH")
    _fixed_json(dest / "member_manifest.json", members)
    if smoke:
        return finish(dest,public,dict(status='PASS',packet=packet,scope='complete frozen case preparation; no head fits',
                      prepared_cases=len(cases),planned_neural_members=len(members),head_fits=0,new_encoder_fits=0))
    device='cuda' if torch.cuda.is_available() else 'cpu'
    if device!='cuda':raise ValueError('REPAIR_REQUIRES_GPU_ALLOCATION')
    # Only one full-batch model is resident on the allocated GPU at a time.
    family = fit_neural_family(dest / "cases", dest / "states", members, device=device)
    _fixed_json(dest / "family_training_diagnostics.json", family)
    summary = dict(stage=packet, status=family["status"], implementation_status="PASS",
        optimization_status=family["status"], scientific_status="NOT_EVALUABLE", clinical_inputs=False,
        new_encoder_fits=0, new_neural_head_fits=len(members), new_linear_head_fits=0,
        selected_budget=family["budget"], extended_members=family["extended_members"],
        stable_members=sum(d["status"] == "OPTIMIZATION_STABLE" for d in family["final"]),
        required_members=len(members), final_alpha_fits_including_unselected=True,
        uncertainty="2000 fixed OOF paired identity bootstrap; no pipeline refits", results=[])
    if family["status"] == "OPTIMIZATION_STABLE":
        for path, old in data["prepared_hashes"].items():
            if digest(Path(path)) != old:
                raise ValueError("REPAIR_PREPARED_CASE_CHANGED_DURING_FIT")
        selected = select_neural_models(dest / "cases", dest / "states", cases, members, family)
        if packet == "C2_R":
            linear_root = dest / "linear_models"
            linear_root.mkdir(mode=0o700, exist_ok=True)
            selected.update(_fit_linear(dest / "cases", linear_root, cases, seed=int(split["seed"])))
            summary["new_linear_head_fits"] = expected["linear"]
            outcome = _score_c(dest, public, cases, selected, family, seed=int(split["seed"]))
        else:
            outcome = _score_e(dest, public, cases, selected, extra, hashes, inventory)
        _fixed_json(dest / "selection_inventory.json", {"|".join(k): v for k, v in selected.items()})
        if not (dest / "selected_heads.pkl").exists():
            _pickle(dest / "selected_heads.pkl", selected)
        summary.update(outcome, status="COMPLETE_REPAIRED_CORE")
    else:
        summary.update(core_status="INCOMPLETE_PRIMARY_MATRIX", test_predictions_generated=False,
                       incomplete_family_aggregates_withheld=True)
    for path, expected_hash in hashes.items():
        if digest(Path(path)) != expected_hash:
            raise ValueError("REPAIR_IMMUTABLE_SOURCE_CHANGED")
    _fixed_json(dest / "input_hashes.json", hashes)
    (report / "SOLVER_REPAIR.md").write_text(
        "# Bounded legacy readout repair\n\nAll neural members, including all four full-training alpha models, "
        "first run 1000 steps. Any unstable training member extends the entire packet to 2000 using the original "
        "cosine schedule. Selection and temperature use only final-budget training OOF logits, after the global "
        "stability barrier; test predictions never determine extension. Unselected final-alpha models remain counted. "
        "The objective is weighted mean BCE plus alpha/(2*sum(weights)) times squared weight matrices; biases "
        "are unpenalized. Float64 full-batch Adam uses explicit L2, seed 11 and weight_decay=0.\n\n"
        "C2-R retains independent branch scalers, the complete linear/MLP32/MLP64 matrix, and fixed-head "
        "zero/same-class/opposite-class interventions (OOD diagnostics). Inner head validation does not refit "
        "the original outer encoders. E0-R retains native128, PCA32 and the original four isolated block folds; "
        "E0 fit weights balance filter blocks/classes within a record, not extra children. "
        "its legacy linear predictions are source-verified and reused. MFF sources are mixed and not all CI. "
        "E1 is not run. Probability metrics retain the legacy clipping definition for estimator comparisons.\n\n"
        "Incomplete neural matrices have no neural test aggregate. All bootstrap intervals are fixed OOF, "
        "not full workflow refits. The old failed runs remain untouched. This repair alone does not complete "
        "all C2 controls or provide independent scientific confirmation.\n", encoding="utf-8")
    return finish(dest, public, summary)
