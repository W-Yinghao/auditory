"""Receipt-bound R3 checkpoint inference and private probe persistence."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
import torch

from auditory5.models.small_cnn import SmallEEGCNN_v1
from .data import load_support, load_epochs, l0
from .evaluate import select_probes, evaluate_representations
from .gates import PACKET_SOURCES, require_capability
from .runtime import Ledger, digest, require_slurm, safe_run, write_json
from .train import channel_scaler, infer_features, _state_hash


OBJECTIVES = ("SUP", "SIM", "MATCH")


def _json(path):
    return json.loads(Path(path).read_text())


def _restricted_path(value, parent):
    path, parent = Path(value).resolve(), Path(parent).resolve()
    if path != parent and parent not in path.parents:
        raise ValueError("Checkpoint or exposure artifact escapes its authorized private directory")
    return path


def _check_sources(reference, current):
    if reference.get("config_sha256") != current.get("config_sha256"):
        raise ValueError("R3 encoder/probe configuration hashes differ")
    source_keys = [f"auditory_v3/{module}.py" for module in PACKET_SOURCES["R3"]]
    source_keys.append("auditory5/models/small_cnn.py")
    for key in source_keys:
        original = reference["source_hashes"].get(key)
        if not original or original != current["source_hashes"].get(key):
            raise ValueError("R3 encoder/probe source mismatch: " + key)


def audit_checkpoints(root, private, prefix, stage, split_run, members, splits):
    """Read and verify every required task before loading EEG for inference."""
    root, private = Path(root), Path(private)
    current = _json(private / "start.json")
    prefix = safe_run(prefix)
    fold_lookup = {int(item["outer_fold"]): item for item in splits["folds"]}
    states, bindings, records = {}, {}, []
    same_exposure, initial_hashes = {}, set()
    for task_index in range(15):
        objective, number = OBJECTIVES[task_index // 5], task_index % 5
        folder = root / "private/auditory_v3" / f"{prefix}_task{task_index:03d}"
        completion = _json(folder / "completion.json")
        if (completion.get("status") != "ENCODER_COMPLETE" or completion.get("objective") != objective
                or int(completion.get("outer_fold", -1)) != number or completion.get("stage") != stage
                or completion.get("split_run") != split_run or completion.get("seed") != 11
                or completion.get("epochs") != 60):
            raise ValueError("R3 task completion does not match its frozen objective/fold/stage")
        _check_sources(_json(folder / "start.json"), current)
        training = _json(folder / "training/training_receipt.json")
        for field in ("status", "objective", "seed", "epochs", "fit_groups", "exposure_hash",
                      "initial_encoder_sha256", "checkpoint"):
            if completion.get(field) != training.get(field):
                raise ValueError("R3 completion and training receipt disagree: " + field)
        scope_key = "R3_fit_groups" if stage == "selection" else "train_groups"
        expected_scope = sorted(map(str, fold_lookup[number][scope_key]))
        if sorted(map(str, completion["fit_groups"])) != expected_scope:
            raise ValueError("R3 encoder was fitted on the wrong identity scope")
        if set(expected_scope) & set(map(str, fold_lookup[number]["test_groups"])):
            raise ValueError("R3 encoder scope includes outer-test identities")
        if stage == "selection" and set(expected_scope) & set(map(str, fold_lookup[number]["R3_validation_groups"])):
            raise ValueError("R3 selection encoder scope includes validation identities")
        checkpoint = _restricted_path(completion["checkpoint"], folder / "training")
        if digest(checkpoint) != completion.get("checkpoint_sha256"):
            raise ValueError("R3 checkpoint bytes changed after completion")
        plan_run = safe_run(completion["plan_run"])
        exposure = _restricted_path(completion["exposure_path"], root / "private/auditory_v3" / plan_run)
        expected_exposure = (root / "private/auditory_v3" / plan_run / f"fold{number}_{stage}.npy").resolve()
        if exposure != expected_exposure or digest(exposure) != completion.get("exposure_file_sha256"):
            raise ValueError("R3 shared exposure artifact differs from its receipt")
        plan = np.load(exposure, allow_pickle=False)
        fit_mask = members.split_group_id.astype(str).isin(expected_scope).to_numpy()
        expected_shape = (60, math.ceil(int(fit_mask.sum()) / 64), 64)
        if (plan.shape != expected_shape or not np.issubdtype(plan.dtype, np.integer)
                or plan.min() < 0 or plan.max() >= len(members) or not fit_mask[plan].all()):
            raise ValueError("R3 exposure is malformed or includes a held-out identity")
        exposure_hash = hashlib.sha256(plan.tobytes()).hexdigest()
        if exposure_hash != completion["exposure_hash"]:
            raise ValueError("R3 exposure-array hash differs from the actual training plan")
        state = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if (state.get("epoch") != 60 or state.get("objective") != objective
                or state.get("exposure_hash") != exposure_hash
                or sorted(map(str, state.get("fit_groups", []))) != expected_scope
                or state.get("initial_encoder_sha256") != completion["initial_encoder_sha256"]):
            raise ValueError("R3 checkpoint state does not match its actual training receipt")
        if state.get("config", {}).get("epochs", 60) != 60 or state.get("config", {}).get("formal_seeds", [11]) != [11]:
            raise ValueError("R3 checkpoint violates the fixed epoch/seed contract")
        exposure_binding = (str(exposure), completion["exposure_file_sha256"], exposure_hash)
        if number in same_exposure and same_exposure[number] != exposure_binding:
            raise ValueError("R3 objectives used different exposure plans")
        same_exposure[number] = exposure_binding
        initial_hashes.add(completion["initial_encoder_sha256"])
        key = (objective, number)
        # Drop optimizer/projector tensors from the inference object. Their
        # source checkpoint remains intact and checksummed in private storage.
        states[key] = {name: state[name] for name in ("model", "scaler_mean", "scaler_std",
                                                     "fit_groups", "initial_encoder_sha256")}
        bindings[f"{objective}_fold{number}"] = {
            "task_run": folder.name, "checkpoint_sha256": completion["checkpoint_sha256"],
            "exposure_hash": exposure_hash, "exposure_file_sha256": completion["exposure_file_sha256"],
            "initial_encoder_sha256": completion["initial_encoder_sha256"], "fit_groups": expected_scope,
            "objective": objective, "outer_fold": number, "stage": stage,
            "plan_run": plan_run, "capability_run": completion.get("capability_run"),
            "test_run": completion.get("test_run")}
        history = completion.get("history", [])
        last = history[-1] if history else {}
        records.append({"objective": objective, "outer_fold": number, "stage": stage,
            "epochs": completion["epochs"], "fit_identity_groups": len(expected_scope),
            "unique_fit_trials": int(fit_mask.sum()), "steps_per_epoch": plan.shape[1],
            "original_trial_exposures": int(plan.size),
            "parameter_count_encoder": completion.get("parameter_count_encoder"),
            "parameter_count_projector": completion.get("parameter_count_projector"),
            "elapsed_seconds": completion.get("elapsed_seconds"),
            "final_training_loss": last.get("loss"),
            "original_head_accuracy_diagnostic": last.get("original_head_accuracy_diagnostic"),
            "final_representation_std": last.get("representation_std")})
    if len(initial_hashes) != 1:
        raise ValueError("R3 objectives/folds did not start from identical encoder parameters")
    return states, bindings, pd.DataFrame(records)


def checkpoint_feature_loader(members, post, pre, splits, states, stage):
    """Build an index-only loader; selection cannot infer outer-test rows."""
    fold_lookup = {int(fold["outer_fold"]): fold for fold in splits["folds"]}
    random_states = {}
    for number, fold in fold_lookup.items():
        groups = fold["R3_fit_groups"] if stage == "selection" else fold["train_groups"]
        fit_indices = np.flatnonzero(members.split_group_id.astype(str).isin(set(map(str, groups))).to_numpy())
        mean, scale = channel_scaler(post, members, fit_indices)
        for objective in OBJECTIVES:
            state = states[(objective, number)]
            if not np.array_equal(state["scaler_mean"], mean) or not np.array_equal(state["scaler_std"], scale):
                raise ValueError("Saved encoder input scaler differs from its exact fit-only recomputation")
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(11)
            random_model = SmallEEGCNN_v1(20, 2)
        initial = _state_hash(random_model)
        if initial != states[("SUP", number)]["initial_encoder_sha256"]:
            raise ValueError("Random encoder initialization differs from the three trained objectives")
        random_states[number] = {"model": random_model.state_dict(), "scaler_mean": mean,
            "scaler_std": scale, "fit_groups": sorted(map(str, groups)), "initial_encoder_sha256": initial}

    def load(objective, number, requested_stage, window, indices):
        number = int(number)
        indices = np.asarray(indices)
        if requested_stage != stage or window not in ("post", "pre"):
            raise ValueError("R3 requested the wrong encoder stage or window")
        if (indices.ndim != 1 or not np.issubdtype(indices.dtype, np.integer) or len(indices) == 0
                or indices.min() < 0 or indices.max() >= len(members) or len(np.unique(indices)) != len(indices)):
            raise ValueError("R3 feature indices must be distinct valid global member rows")
        groups = set(members.iloc[indices].split_group_id.astype(str))
        fold = fold_lookup[number]
        allowed = set(map(str, fold["train_groups"])) if stage == "selection" else set(members.split_group_id.astype(str))
        if not groups <= allowed:
            raise ValueError("R3 selection inference attempted to load outer-test rows")
        if objective == "L0":
            if window != "post":
                raise ValueError("The common L0 probe uses its prescribed post window")
            return l0(post[indices], pre[indices])[0]
        if objective == "RAND":
            state = random_states[number]
        elif objective in OBJECTIVES:
            state = states[(objective, number)]
        else:
            raise ValueError("Unknown R3 representation objective")
        raw = post[indices] if window == "post" else pre[indices]
        result = infer_features(state, raw, device="cpu")
        if result.shape != (len(indices), 64) or not np.isfinite(result).all():
            raise ValueError("R3 encoder inference is nonfinite or has the wrong latent dimension")
        return result

    load.random_states = random_states
    return load


def _private_pickle(path, value):
    with Path(path).open("xb") as handle:
        pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)
    Path(path).chmod(0o600)


def _private_frame(path, frame):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path.name)
    frame.to_parquet(path, index=False)
    path.chmod(0o600)


def probe_packet(root, private, public, report, config, args):
    """Select probes or evaluate final encoders; called by the snapshot worker."""
    require_slurm()
    root, private, public, report = map(Path, (root, private, public, report))
    command = args["command"]
    if command not in ("select-probes", "evaluate-representations"):
        raise ValueError("R3 probe wrapper received the wrong command")
    stage = "selection" if command == "select-probes" else "final"
    gate = require_capability(root, private, args["gate_run"], "R3", args["split_run"])
    members, splits, _, registry, support = load_support(root, args["split_run"])
    if support["R3_support"] != "SUFFICIENT":
        raise ValueError("R3_SUPPORT_LIMITED")
    selection = None
    selected_bindings = None
    if stage == "final":
        selected = root / "private/auditory_v3" / safe_run(args["selection_run"])
        receipt = _json(selected / "completion.json")
        if (receipt.get("status") not in ("PROBES_SELECTED", "COMPLETED_WITH_NUMERICAL_FAILURES")
                or receipt.get("split_run") != args["split_run"]
                or receipt.get("selection_complete") is not True):
            raise ValueError("Final R3 probes require a completed selection packet for this support")
        _check_sources(_json(selected / "start.json"), _json(private / "start.json"))
        selection = _json(selected / "selection_receipt.json")
        if digest(selected / "selection_receipt.json") != receipt.get("selection_receipt_sha256"):
            raise ValueError("R3 probe selection receipt changed after completion")
        selected_bindings = _json(selected / "checkpoint_bindings.json")
        if digest(selected / "checkpoint_bindings.json") != receipt.get("checkpoint_bindings_sha256"):
            raise ValueError("Selection encoder bindings changed after completion")
    states, bindings, training = audit_checkpoints(root, private, args["representation_run"], stage,
                                                  args["split_run"], members, splits)
    if any(item["capability_run"] != args["gate_run"] or item["test_run"] != gate["test_run"]
           for item in bindings.values()):
        raise ValueError("R3 encoder tasks belong to a different capability/test receipt")
    if selected_bindings is not None:
        for key, item in bindings.items():
            if item["initial_encoder_sha256"] != selected_bindings[key]["initial_encoder_sha256"]:
                raise ValueError("Final encoder restarted from different initial parameters")
    write_json(private / "checkpoint_bindings.json", bindings)
    post, pre = load_epochs(members, registry)
    loader = checkpoint_feature_loader(members, post, pre, splits, states, stage)
    ledger = Ledger(private)
    if stage == "selection":
        output = select_probes(members, loader, splits, ledger=ledger)
        selection = output["selection_receipt"]
        write_json(private / "selection_receipt.json", selection)
        choices = pd.DataFrame(selection["selections"])
        _private_frame(private / "probe_choices.parquet", choices)
        summary = {"status": "PROBES_SELECTED" if selection["status"] == "PASS" else "COMPLETED_WITH_NUMERICAL_FAILURES",
            "packet": "R3", "stage": stage,
            "execution": "COMPLETE" if selection["status"] == "PASS" else "NUMERICAL_FAIL",
            "selection_status": selection["status"], "selection_complete": selection["selection_complete"],
            "selection_heads": selection["selection_heads"], "optimizer_attempts": selection["optimizer_attempts"],
            "selected_choices": int(choices.selected_lambda.notna().sum()), "expected_choices": 60,
            "selection_receipt_sha256": digest(private / "selection_receipt.json"),
            "research": "NOT_EVALUATED_OUTER_TEST_NOT_SCORED", "algorithm_hash": selection["algorithm_hash"]}
        (report / "R3_SELECTION.md").write_text(
            "# R3 probe selection\n\nAll selection encoders and probe transforms exclude the fixed validation identities. "
            "Each probe's three penalties were evaluated only on that validation split. "
            "Outer-test EEG was not passed to selection feature inference. Incomplete grids retain missing choices.\n")
    else:
        output = evaluate_representations(members, loader, splits, selection, ledger=ledger)
        for name in ("predictions", "identity_risks"):
            _private_frame(private / (name + ".parquet"), output[name])
        summary = dict(output["summary"], status="R3_RECORDED", stage=stage,
                       selection_run=args["selection_run"])
        pd.DataFrame([dict(model=name, **metric) for name, metric in summary["metrics"].items()]).to_csv(public / "R3_metrics.csv", index=False)
        pd.DataFrame([dict(contrast=name, **result) for name, result in summary["contrasts"].items()]).to_csv(public / "R3_paired_effects.csv", index=False)
        (report / "R3_PROBES.md").write_text(
            "# R3 final probes\n\nFinal encoders were refitted on all outer-training identities after the selection packet completed. "
            "All full 64-coordinate probes, common baselines, and pre controls retain their complete five-fold denominator. "
            "Pre and post windows have unequal length; their comparison is diagnostic. Identity bootstrap intervals condition "
            "on these fixed OOF predictions and do not establish exact conditional information or cortical origin.\n")
    _private_pickle(private / "probe_models.pkl", output["models"])
    _private_pickle(private / "fit_diagnostics.pkl", output["fit_diagnostics"])
    _private_pickle(private / "random_encoder_states.pkl", loader.random_states)
    training.to_csv(public / "training_summary.csv", index=False)
    summary.update(split_run=args["split_run"], capability_run=args["gate_run"],
        capability="PASS", capability_test_run=gate["test_run"],
        checkpoint_bindings_sha256=digest(private / "checkpoint_bindings.json"),
        encoder_tasks_verified=15, shared_exposure_verified=True, identical_initialization_verified=True,
        new_encoder_fits=0, participant_predictions_public=False)
    return summary
