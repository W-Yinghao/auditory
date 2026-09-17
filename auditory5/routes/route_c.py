"""Paired independent-branch C readouts; see docs/auditory5_C_readout_v1.md.

Inner validation isolates these tabular transforms/heads, not the upstream
outer-training encoders. No clinical outcomes or full-head features are loaded.
"""

from dataclasses import dataclass
import json
import math
from pathlib import Path
import pickle
import warnings
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier

from auditory5.contracts import FitScope
from auditory5.metrics import classification_metrics
from auditory5.probes import (C_GRID, CandidateTabularScaler, candidate_class_weights,
                             fit_temperature, weighted_log_loss_nats, _fit_head, _head_logits)
from auditory5.provenance import ROOT, digest, object_hash, require_slurm, write_json


VIEWS = ("C_L", "C_R", "C_LR", "C_LL", "C_RR")
MODEL_SPECS = tuple((family, view, width) for family, width in (("linear", 0), ("mlp32", 32))
                    for view in VIEWS) + (("mlp64", "C_L", 64), ("mlp64", "C_R", 64))
INTERVENTIONS = ("zero_first", "zero_second", "same_class_first", "same_class_second",
                 "opposite_class_first", "opposite_class_second")
METADATA_COLUMNS = ("trial_id", "record_id", "candidate_id", "split_group_id",
                    "stimulus_local_id", "time_block_id")


def _pair_arrays(left, right):
    a, b = np.asarray(left, float), np.asarray(right, float)
    if (a.ndim != 2 or b.shape != a.shape or min(a.shape) < 1 or
            not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError("C_FEATURE_SUPPORT: finite nonempty equal-width paired features required")
    return a, b


def compose_view(left, right, view):
    if view == "C_L":
        return left
    if view == "C_R":
        return right
    if view == "C_LR":
        return np.c_[left, right]
    if view == "C_LL":
        return np.c_[left, left]
    if view == "C_RR":
        return np.c_[right, right]
    raise ValueError("C_MODEL: unknown paired view")


def _fit_c_head(x, y, groups, regularization, width, seed):
    if width == 0:
        return _fit_head(x, y, groups, regularization, seed)
    if width not in (32, 64):
        raise ValueError("C_MODEL: only frozen 32/64-unit MLP widths permitted")
    head = MLPClassifier(hidden_layer_sizes=(width,), activation="relu", solver="lbfgs",
                         alpha=regularization, max_iter=5000, max_fun=250000, tol=1e-6,
                         early_stopping=False, random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        try:
            head.fit(x, y, sample_weight=candidate_class_weights(y, groups))
        except ConvergenceWarning as exc:
            raise ValueError(f"C_HEAD_CONVERGENCE_FAILURE: MLP width={width}, alpha={regularization}, n={len(y)}, p={x.shape[1]} did not converge at5000") from exc
        except TypeError as exc:
            raise ValueError("C_MLP_ENVIRONMENT: weighted MLP fit support required") from exc
    if not all(np.isfinite(v).all() for v in [*head.coefs_, *head.intercepts_]):
        raise ValueError("C_HEAD_NUMERICAL_FAILURE: nonfinite MLP parameters")
    return head


def _c_logits(head, x):
    if not isinstance(head, MLPClassifier):
        return _head_logits(head, x)
    if (len(head.coefs_) != 2 or head.activation != "relu" or
            head.out_activation_ != "logistic" or not np.array_equal(head.classes_, [0, 1])):
        raise ValueError("C_MODEL: expected binary single-hidden-layer ReLU MLP")
    # Use pre-sigmoid scores; predict_proba rounding must not truncate calibration.
    hidden = np.maximum(x @ head.coefs_[0] + head.intercepts_[0], 0)
    score = (hidden @ head.coefs_[1] + head.intercepts_[1]).reshape(-1)
    if not np.isfinite(score).all():
        raise ValueError("C_HEAD_NUMERICAL_FAILURE: nonfinite logits")
    return np.c_[-score / 2, score / 2]


@dataclass
class PairedReadout:
    left_scaler: CandidateTabularScaler
    right_scaler: CandidateTabularScaler
    view: str
    family: str
    head: object
    temperature: float
    regularization: float
    evidence: dict

    def predict(self, left, right, *, intervention=None, donor_indices=None):
        left, right = _pair_arrays(left, right)
        x = compose_view(self.left_scaler.transform(left), self.right_scaler.transform(right), self.view)
        if intervention is not None:
            if self.view not in ("C_LR", "C_LL", "C_RR") or intervention not in INTERVENTIONS:
                raise ValueError("C_INTERVENTION: only frozen paired-slot interventions permitted")
            width = x.shape[1] // 2
            slot = slice(0, width) if intervention.endswith("first") else slice(width, 2 * width)
            x = x.copy()
            if intervention.startswith("zero"):
                x[:, slot] = 0
            else:
                donor = np.asarray(donor_indices)
                if (donor.shape != (len(x),) or not np.issubdtype(donor.dtype, np.integer)
                        or np.any(donor < 0) or np.any(donor >= len(x))):
                    raise ValueError("C_INTERVENTION_SUPPORT: every trial requires a valid donor")
                x[:, slot] = x[donor, slot]
        scores = _c_logits(self.head, x)
        return dict(raw=softmax(scores, axis=1), calibrated=softmax(scores / self.temperature, axis=1))


def fit_paired_readouts(left, right, y, groups, scope, *, seed=20260917, linear_only=False):
    """Fit the frozen 12-head matrix from training data only; no test arguments."""
    left, right = _pair_arrays(left, right)
    y, groups = np.asarray(y), np.asarray(groups, str)
    if y.shape != (len(left),) or groups.shape != y.shape or not np.array_equal(np.unique(y), [0, 1]):
        raise ValueError("C_CLASS_SUPPORT: aligned binary labels/groups required")
    scope.assert_fit_groups(groups)
    weights = candidate_class_weights(y, groups)
    if len(np.unique(groups)) < 3:
        raise ValueError("C_INNER_SUPPORT: at least three training identity groups required")
    y = y.astype(int)
    model_specs=tuple(spec for spec in MODEL_SPECS if not linear_only or spec[0]=='linear')
    oof = {(family, view): {r: np.full((len(y), 2), np.nan) for r in C_GRID}
           for family, view, _ in model_specs}
    fold_evidence = []
    for number, (train, validation) in enumerate(GroupKFold(3).split(left, y, groups)):
        inner_scope = FitScope(tuple(np.unique(groups[train])), tuple(np.unique(groups[validation])),
                               tuple(scope.validation_groups) + tuple(scope.test_groups))
        candidate_class_weights(y[train], groups[train])
        candidate_class_weights(y[validation], groups[validation])
        scalers = [CandidateTabularScaler().fit(x[train], groups[train], inner_scope) for x in (left, right)]
        a, b = [s.transform(x[train]) for s, x in zip(scalers, (left, right))]
        va, vb = [s.transform(x[validation]) for s, x in zip(scalers, (left, right))]
        for family, view, width in model_specs:
            x, v = compose_view(a, b, view), compose_view(va, vb, view)
            for regularization in C_GRID:
                head = _fit_c_head(x, y[train], groups[train], regularization, width, seed)
                oof[family, view][regularization][validation] = _c_logits(head, v)
        fold_evidence.append(dict(fold=number, fit_groups=list(inner_scope.train_groups),
                                  validation_groups=list(inner_scope.validation_groups), scope_hash=inner_scope.hash))
    scalers = [CandidateTabularScaler().fit(x, groups, scope) for x in (left, right)]
    a, b = [s.transform(x) for s, x in zip(scalers, (left, right))]
    fitted = {}
    for family, view, width in model_specs:
        scores = oof[family, view]
        losses = {r: weighted_log_loss_nats(scores[r], y, weights) for r in C_GRID}
        # Strongest regularization wins exact ties (C smaller; alpha larger).
        chosen = min(C_GRID, key=lambda r: (losses[r], r if width == 0 else -r))
        calibration = fit_temperature(scores[chosen], y, groups, scope)
        head = _fit_c_head(compose_view(a, b, view), y, groups, chosen, width, seed)
        evidence = dict(fit_groups=list(scalers[0].fit_groups_), scope_hash=scope.hash,
                        inner_folds=fold_evidence, calibration=calibration,
                        regularization_parameter="C" if width == 0 else "alpha",
                        inner_ce_bits={str(r): v / math.log(2) for r, v in losses.items()},
                        branch_scalers_independent=True, context="frozen outer-training representation",
                        inner_encoder_refitted=False, hidden_width=width)
        fitted[family, view] = PairedReadout(*scalers, view, family, head,
                                             calibration["temperature"], chosen, evidence)
    return fitted


def replacement_indices(rows, *, opposite=False, seed=20260917):
    """Stable same-candidate, other-original-block donors; -1 means unavailable."""
    if any(column not in rows for column in METADATA_COLUMNS) or rows[list(METADATA_COLUMNS)].isna().any().any():
        raise ValueError("C_DONOR_SCHEMA: complete trial, candidate, class and block metadata required")
    if not rows.trial_id.is_unique or not rows.stimulus_local_id.isin([0, 1]).all():
        raise ValueError("C_DONOR_SCHEMA: unique trials and binary labels required")
    result = np.full(len(rows), -1, int)
    candidate, label = rows.candidate_id.to_numpy(str), rows.stimulus_local_id.to_numpy(int)
    record, block, trials = rows.record_id.to_numpy(str), rows.time_block_id.to_numpy(), rows.trial_id.to_numpy(str)
    for i in range(len(rows)):
        pool = np.flatnonzero((candidate == candidate[i]) & (label == (1 - label[i] if opposite else label[i])) &
                             ((record != record[i]) | (block != block[i])))
        if len(pool):
            pool = pool[np.argsort(trials[pool], kind="stable")]
            index = int(object_hash(dict(seed=int(seed), trial=trials[i], opposite=bool(opposite)))[:16], 16)
            result[i] = pool[index % len(pool)]
    return result


def paired_bootstrap(table, *, seed=20260917, n_boot=2000):
    """One set of group draws for every contrast; the minimum is after averaging."""
    table = table.sort_index()
    if any(view not in table for view in VIEWS) or table.empty or not table.index.is_unique:
        raise ValueError("C_PAIRED_SUPPORT: complete unique candidate/model loss table required")
    values = table.to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError("C_PAIRED_SUPPORT: no selective model/candidate deletion permitted")
    columns = {name: i for i, name in enumerate(table.columns)}

    def statistics(mean):
        get = lambda key: mean[..., columns[key]]
        joint = get("C_LR")
        output = {"CE_" + key: get(key) for key in table.columns}
        output.update(G_R_given_L=get("C_L") - joint, G_L_given_R=get("C_R") - joint,
                      T_C=np.minimum(get("C_L"), get("C_R")) - joint, J_joint=1 - joint,
                      duplicate_margin=np.minimum(get("C_LL"), get("C_RR")) - joint)
        if "C_L64" in columns or "C_R64" in columns:
            if "C_L64" not in columns or "C_R64" not in columns:
                raise ValueError("C_CAPACITY_SUPPORT: both expanded single heads required")
            output["expanded_margin"] = np.minimum(get("C_L64"), get("C_R64")) - joint
            output["capacity_margin"] = np.minimum.reduce([get(v) for v in ("C_LL", "C_RR", "C_L64", "C_R64")]) - joint
        return output

    if n_boot != 2000:
        raise ValueError("C_BOOTSTRAP: frozen 2000 candidate draws required")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(values), size=(n_boot, len(values)))
    estimate, bootstrap = statistics(values.mean(axis=0)), statistics(values[draws].mean(axis=1))
    return [dict(statistic=name, estimate=float(value), ci_lower=float(np.quantile(bootstrap[name], .025)),
                 ci_upper=float(np.quantile(bootstrap[name], .975)), n_candidates=len(table),
                 n_bootstrap=n_boot, seed=int(seed), units="bits/trial",
                 uncertainty="fixed OOF identity-group bootstrap; no workflow refits") for name, value in estimate.items()]


def align_branch_payloads(left, right):
    """Require the same complete trial set; reorder the right branch explicitly."""
    a, b = left["rows"], right["rows"]
    if any(c not in a or c not in b for c in METADATA_COLUMNS):
        raise ValueError("C_PAIR_SCHEMA: required trial provenance is missing")
    if a.empty or not a.trial_id.is_unique or not b.trial_id.is_unique or set(a.trial_id) != set(b.trial_id):
        raise ValueError("C_PAIR_MISMATCH: branches must contain identical unique trial IDs")
    order = pd.Index(b.trial_id).get_indexer(a.trial_id)
    aligned = b.iloc[order].reset_index(drop=True)
    if not a[list(METADATA_COLUMNS)].reset_index(drop=True).equals(aligned[list(METADATA_COLUMNS)]):
        raise ValueError("C_PAIR_MISMATCH: paired labels, candidates or original blocks differ")
    x, z = _pair_arrays(left["post"], right["post"][order])
    if len(x) != len(a) or a[list(METADATA_COLUMNS)].isna().any().any():
        raise ValueError("C_PAIR_SCHEMA: feature rows or provenance are incomplete")
    return x, z, a.reset_index(drop=True)


def _load_pair(plan, plan_path, fold, mode, support):
    outputs, expected = {}, []
    eligible = set(support.loc[support.C, "split_group_id"].astype(str))
    wanted_fit = sorted(set(fold["train_groups"]) & eligible)
    scope = FitScope(tuple(wanted_fit), test_groups=tuple(fold["test_groups"]))
    source_hashes = {}
    for branch in ("left", "right"):
        name = f'outer{fold["outer_fold"]}_{branch}_{mode}'
        tasks = [task for task in plan["tasks"] if task["name"] == name]
        if len(tasks) != 1:
            raise FileNotFoundError("C_REQUIRED_BRANCH_TASK_MISSING")
        task = tasks[0]
        if (task["branch"] != branch or task["mode"] != mode or task["stage"] != "outer" or
                task["inner_fold"] is not None or set(task["fit_groups"]) != set(fold["train_groups"]) or
                set(task["test_groups"]) != set(fold["test_groups"]) or task["validation_groups"]):
            raise ValueError("C_ENCODER_SCOPE_MISMATCH: independent outer branch task required")
        folder = plan_path.parent / "outputs" / name
        paths = [folder / f for f in ("features.npz", "feature_rows.parquet", "task.json", "completion.json")]
        if mode != "L0":
            paths.append(folder / "encoder.pt")
        if not all(path.is_file() for path in paths):
            raise FileNotFoundError("C_REQUIRED_BRANCH_OUTPUT_MISSING")
        stored_task = json.loads((folder / "task.json").read_text())
        done = json.loads((folder / "completion.json").read_text())
        if (any(stored_task.get(k) != v for k, v in task.items()) or
                stored_task.get("plan_hash") != digest(plan_path) or done.get("plan_hash") != digest(plan_path) or
                done.get("status") != "PASS" or done.get("encoder_fit_scope_hash") != scope.hash or
                done.get("branch") != branch or done.get("mode") != mode):
            raise ValueError("C_ENCODER_SCOPE_MISMATCH: completion provenance differs from frozen plan")
        rows = pd.read_parquet(folder / "feature_rows.parquet")
        with np.load(folder / "features.npz", allow_pickle=False) as arrays:
            for key, column in (("trial_ids", "trial_id"), ("groups", "split_group_id"), ("y", "stimulus_local_id")):
                if column not in rows or not np.array_equal(arrays[key], rows[column].to_numpy()):
                    raise ValueError("C_PAIR_MISMATCH: NPZ and parquet order/labels differ")
            outputs[branch] = dict(rows=rows, post=np.array(arrays["post"], dtype=float))
        source_hashes.update({str(path): digest(path) for path in paths})
        expected.append(task["branch"])
    if expected != ["left", "right"]:
        raise ValueError("C_BRANCH_ISOLATION: full-head features forbidden")
    left, right, rows = align_branch_payloads(outputs["left"], outputs["right"])
    if set(rows.split_group_id) != eligible or not set(rows.split_group_id) <= set(scope.train_groups + scope.test_groups):
        raise ValueError("C_SCOPE_MISMATCH: paired features must cover the frozen eligible identity set exactly")
    if left.shape[1] != (160 if mode == "L0" else 64):
        raise ValueError("C_BRANCH_DIMENSION: expected eight-channel L0 bins or 64-dimensional branch encoder")
    for _, group in rows.groupby("split_group_id"):
        if any(int(group.stimulus_local_id.eq(c).sum()) < 20 for c in (0, 1)):
            raise ValueError("C_CLASS_SUPPORT: every paired candidate requires at least 20 trials/class")
    return left, right, rows, scope, source_hashes


def synthetic_controls(seed=20260917):
    """Three small production-head worlds; a diagnostic, not a false-positive audit."""
    bits = np.tile(np.array([[0, 0], [0, 1], [1, 0], [1, 1]]), (16, 1))
    groups = np.repeat(["synthetic_a", "synthetic_b", "synthetic_c", "synthetic_d"], 16)
    output = {}
    for world in ("copied", "left_only", "xor"):
        y = np.logical_xor(bits[:, 0], bits[:, 1]).astype(int) if world == "xor" else bits[:, 0]
        left = (2 * bits[:, 0] - 1.)[:, None]
        right = left.copy() if world == "copied" else (2 * bits[:, 1] - 1.)[:, None]
        scores = {}
        for family, width in (("linear", 0), ("mlp32", 32)):
            for view in VIEWS:
                x = compose_view(left, right, view)
                head = _fit_c_head(x, y, groups, 10. if width == 0 else .01, width, seed)
                # Repeated exact support points make train/test population identical;
                # this tests representational ability, not generalization accuracy.
                scores[family + "_" + view] = weighted_log_loss_nats(_c_logits(head, x), y,
                                                           candidate_class_weights(y, groups)) / math.log(2)
        if world == "copied":
            passed = all(abs(scores[f + "_C_L"] - scores[f + "_C_LR"]) < .05 for f in ("linear", "mlp32"))
        elif world == "left_only":
            passed = scores["mlp32_C_L"] < .2 and scores["mlp32_C_R"] > .9 and scores["mlp32_C_LR"] < .2
        else:
            passed = (scores["mlp32_C_L"] > .9 and scores["mlp32_C_R"] > .9 and
                      scores["linear_C_LR"] > .9 and scores["mlp32_C_LR"] < .3)
        output[world] = dict(status="PASS" if passed else "FAIL", ce_bits=scores)
    return dict(status="PASS" if all(v["status"] == "PASS" for v in output.values()) else "FAIL", worlds=output)


def _isolation_evidence(config, plan):
    base = ROOT / config["paths"]["private_relative"]
    gate_path = ROOT / config["paths"]["aggregates_relative"] / plan["contract_run"] / "validation.json"
    junit = base / "validation" / plan["contract_run"] / "junit.xml"
    if not gate_path.is_file() or not junit.is_file():
        return dict(status="MISSING", raw_opposite_branch_exact=False)
    gate = json.loads(gate_path.read_text())
    if digest(gate_path) != plan["contract_hash"] or gate["status"] != "PASS":
        raise ValueError("C_INPUT_ISOLATION_GATE_CHANGED")
    rel = "auditory5/preprocessing.py"
    if gate["code_hashes"][rel] != plan["code_hashes"][rel]:
        raise ValueError("C_INPUT_ISOLATION_CODE_CHANGED")
    cases = [case for case in ET.parse(junit).getroot().findall(".//testcase")
             if case.get("name") == "test_independent_spatial_branch_both_directions"]
    exact = len(cases) == 1 and len(list(cases[0])) == 0
    x = np.array([[0., 1.], [2., 3.], [4., 5.], [6., 7.]])
    groups = np.array(["a", "a", "b", "b"])
    scope = FitScope(("a", "b"))
    # Separate branch fits have no opposite-branch argument or shared moments.
    a = CandidateTabularScaler().fit(x, groups, scope).transform(x)
    CandidateTabularScaler().fit(x * 1e6 + 3, groups, scope)
    b = CandidateTabularScaler().fit(x, groups, scope).transform(x)
    scaler_exact = bool(np.array_equal(a, b))
    return dict(status="PASS" if exact and scaler_exact else "MISSING", raw_opposite_branch_exact=exact,
                branch_scaler_exact=scaler_exact, source_gate_hash=digest(gate_path), junit_hash=digest(junit),
                branch_encoder_contract="separate P2 left/right task, no full-head hidden slicing")


def _prediction_rows(rows, probabilities, *, mode, fold, family, view, intervention, donor=None):
    parts = []
    for calibration, p in probabilities.items():
        part = rows[list(METADATA_COLUMNS)].copy()
        part["representation"], part["outer_fold"], part["family"], part["model"] = mode, fold, family, view
        part["intervention"], part["probability_mode"] = intervention, calibration
        part["p0"], part["p1"] = p[:, 0], p[:, 1]
        part["OOD_diagnostic"] = intervention != "none"
        if donor is not None:
            part["donor_trial_id"] = rows.trial_id.to_numpy()[donor]
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def _candidate_losses(frame):
    result = []
    keys = ["representation", "family", "model", "intervention", "probability_mode"]
    for values, rows in frame.groupby(keys):
        for group, own in rows.groupby("split_group_id"):
            metrics = classification_metrics(own.stimulus_local_id.to_numpy(int), own[["p0", "p1"]].to_numpy(),
                                             own.split_group_id.to_numpy(str), own.trial_id.to_numpy(str))
            result.append(dict(zip(keys, values), split_group_id=group, **metrics,
                               class0_trials=int(own.stimulus_local_id.eq(0).sum()),
                               class1_trials=int(own.stimulus_local_id.eq(1).sum())))
    return result


def summarize_losses(losses, seed=20260917, *, families=("linear", "mlp32")):
    """Aggregate a complete model matrix; never inner-join away model failures."""
    gains, intervention_rows = [], []
    main = losses[losses.intervention.eq("none")]
    for (mode, calibration), subset in main.groupby(["representation", "probability_mode"]):
        if families not in (("linear",), ("linear", "mlp32")):
            raise ValueError('C_SUMMARY_FAMILY: only full matrix or explicit linear-only fallback')
        for family in families:
            rows = subset[subset.family.eq(family)]
            table = rows.pivot(index="split_group_id", columns="model", values="ce_bits")
            if family == "mlp32":
                wide = subset[subset.family.eq("mlp64")].pivot(index="split_group_id", columns="model", values="ce_bits")
                if set(wide.index) != set(table.index) or set(wide.columns) != {"C_L", "C_R"}:
                    raise ValueError("C_CAPACITY_SUPPORT: incomplete expanded single heads")
                table = table.join(wide.rename(columns={"C_L": "C_L64", "C_R": "C_R64"}))
            for row in paired_bootstrap(table, seed=seed):
                gains.append(dict(representation=mode, probability_mode=calibration, family=family, **row))
    other = losses[~losses.intervention.eq("none")]
    for keys, subset in other.groupby(["representation", "probability_mode", "family", "model", "intervention"]):
        mode, calibration, family, model, intervention = keys
        baseline = main[(main.representation == mode) & (main.probability_mode == calibration) &
                        (main.family == family) & (main.model == model)].set_index("split_group_id").ce_bits
        perturbed = subset.set_index("split_group_id").ce_bits
        if set(baseline.index) != set(perturbed.index):
            intervention_rows.append(dict(representation=mode, probability_mode=calibration, family=family,
                model=model, intervention=intervention, status="NEED_CONTROLS", OOD_diagnostic=True,
                reason="donor support missing in at least one outer fold; no subset effect reported"))
            continue
        order = sorted(baseline.index)
        change = perturbed.loc[order].to_numpy() - baseline.loc[order].to_numpy()
        draws = np.random.default_rng(seed).integers(0, len(order), (2000, len(order)))
        boot = change[draws].mean(axis=1)
        intervention_rows.append(dict(representation=mode, probability_mode=calibration, family=family,
            model=model, intervention=intervention, ce_increase_bits=float(change.mean()),
            perturbed_ce_bits=float(perturbed.mean()), ci_lower=float(np.quantile(boot, .025)),
            ci_upper=float(np.quantile(boot, .975)), n_candidates=len(order), n_bootstrap=2000,
            OOD_diagnostic=True, seed=int(seed)))
    return gains, intervention_rows


def screen(gains, missing_controls):
    def rows_for(mode, family="mlp32", calibration="calibrated"):
        return {row["statistic"]: row for row in gains if row["representation"] == mode and
                row["family"] == family and row["probability_mode"] == calibration}

    def passes(rows, capacity="capacity_margin"):
        return bool(rows and rows["T_C"]["estimate"] >= .01 and rows["T_C"]["ci_lower"] > 0 and
                    rows["J_joint"]["ci_lower"] > 0 and rows[capacity]["ci_lower"] > 0)

    primary = rows_for("R_SIM")
    parallel = rows_for("R_SUP")
    pending = list(missing_controls)
    if not primary:
        pending.append("primary independent R_SIM branch readouts")
    if not parallel:
        pending.append("parallel independent R_SUP branch readouts")
    for mode in ("R_SIM", "R_SUP"):
        for family in ("linear", "mlp32"):
            for calibration in ("raw", "calibrated"):
                required = {"T_C", "J_joint", "duplicate_margin"}
                if family == "mlp32":
                    required.add("capacity_margin")
                if not required <= set(rows_for(mode, family, calibration)):
                    pending.append(f"{mode} {family} {calibration} complete comparison matrix")
    report = dict(primary_representation="R_SIM", primary_family="mlp32", parallel_representation="R_SUP",
                  missing_controls=sorted(set(pending)), full_route_complete=False,
                  interpretation="first-pass conditional predictive complementarity; not PID synergy")
    if pending:
        return dict(report, status="NEED_CONTROLS")
    if primary["T_C"]["n_candidates"] < 25:
        return dict(report, status="SUPPORT_INSUFFICIENT")
    raw = rows_for("R_SIM", calibration="raw")
    evidence = passes(primary)
    if evidence and not passes(raw):
        status = "MIXED_SCREEN: capacity_or_calibration"
    elif evidence:
        status = "POSITIVE_SCREEN"
    elif primary["T_C"]["estimate"] >= .01 and primary["T_C"]["ci_lower"] > 0:
        status = "MIXED_SCREEN: capacity_or_calibration"
    else:
        status = "NO_POSITIVE_SCREEN"
    report.update(full_route_complete=True, status=status, parallel_R_SUP_screen=passes(parallel),
                  model_class_dependent=evidence != passes(rows_for("R_SIM", family="linear"), "duplicate_margin"),
                  replication="one frozen seed; replication seeds not evaluated")
    return report


def run(config, plan_run, output_dir, *, modes=("L0",), linear_only=False):
    """Read frozen plan branch outputs and write one immutable private C run.

    Missing representation jobs remain NEED_CONTROLS. Mathematical/schema or
    optimization failures abort all screening, preserving the partial audit.
    No models are trained on login nodes: caller must allocate Slurm first.
    """
    require_slurm()
    base = ROOT / config["paths"]["private_relative"]
    plan_path = base / "jobs" / plan_run / "plan.json"
    plan = json.loads(plan_path.read_text())
    if object_hash(config) != plan["config_hash"]:
        raise ValueError("C_CONFIG_CHANGED: readout configuration differs from representation plan")
    split_path = base / "splits" / plan["split_run"] / "folds.json"
    if digest(split_path) != plan["split_hash"]:
        raise ValueError("C_SPLIT_CHANGED")
    split = json.loads(split_path.read_text())
    support = pd.read_parquet(split_path.parent / "support.parquet")
    if not modes or len(set(modes)) != len(modes) or not set(modes) <= {"L0", "R_SIM", "R_SUP", "R_RAND"}:
        raise ValueError("C_MODE: nonempty unique predefined representation modes required")
    destination = Path(output_dir)
    destination = (destination if destination.is_absolute() else ROOT / destination).resolve()
    if not destination.is_relative_to((ROOT / "private").resolve()):
        raise ValueError("C outputs containing trials, identities and models must stay private")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    public = ROOT / config["paths"]["aggregates_relative"] / destination.name
    public.mkdir(parents=True, exist_ok=False)
    prediction_dir = destination / "paired_predictions"
    prediction_dir.mkdir(mode=0o700)
    seed = int(split["seed"])
    model_specs=tuple(spec for spec in MODEL_SPECS if not linear_only or spec[0]=='linear')
    contract = dict(version="auditory5_C_readout_v1_numerical2", plan_hash=digest(plan_path), modes=list(modes),
                    linear_only_partial=linear_only,
                    seed=seed, models=[dict(family=f, view=v, hidden=w) for f, v, w in model_specs],
                    candidate_class_weight="1/(2*n_candidate_class)", trial_cap=None,
                    scaler_weight="1/n_candidate", MLP=dict(solver="lbfgs", max_iter=5000, max_fun=250000,
                    tol=1e-6, alpha_grid=list(C_GRID)), inner_folds=3, bootstrap=2000,
                    minimum_trials_per_class=20, primary_minimum_candidates=25,
                    inner_encoder_refitted=False, same_trials_all_heads=True,
                    intervention_zero="standardized branch zero equals training mean",
                    upstream_scope="independent P2 outer-training encoders", source_hash=digest(Path(__file__)),
                    documentation_hash=digest(ROOT / "docs/auditory5_C_readout_v1.md"))
    write_json(destination / "run_contract.json", contract)
    losses, fits, coverage, missing, input_hashes = [], [], [], [], {}
    if linear_only:missing.append('all nonlinear heads and expanded capacity controls; linear-only computational fallback')
    try:
        for rid in support.loc[support.C, "record_id"]:
            path = base / "data" / plan["export_run"] / "P2_SPATIAL_SPLIT" / rid / "summary.json"
            if digest(path) != split["input_hashes"]["P2_SPATIAL_SPLIT/" + rid]:
                raise ValueError("C_EXPORT_CHANGED: new paired source differs from frozen split")
            input_hashes[str(path)] = digest(path)
        isolation = _isolation_evidence(config, plan)
        synthetic = synthetic_controls(seed)
        write_json(public / "input_isolation_tests.json", isolation)
        write_json(public / "synthetic_controls.json", synthetic)
        if isolation["status"] != "PASS":
            missing.append("exact raw opposite-branch isolation evidence")
        if synthetic["status"] != "PASS":
            raise ValueError("C_SYNTHETIC_CONTROLS_FAIL")
        for mode in modes:
            for fold in split["folds"]:
                number = fold["outer_fold"]
                try:
                    left, right, rows, scope, hashes = _load_pair(plan, plan_path, fold, mode, support)
                except FileNotFoundError:
                    missing.append(f"{mode} outer{number} branch outputs")
                    coverage.append(dict(representation=mode, outer_fold=number, status="NEED_CONTROLS"))
                    continue
                input_hashes.update(hashes)
                train = rows.split_group_id.isin(scope.train_groups).to_numpy()
                test = rows.split_group_id.isin(scope.test_groups).to_numpy()
                if not train.any() or not test.any():
                    raise ValueError("C_CLASS_SUPPORT: empty outer training or test partition")
                fitted = fit_paired_readouts(left[train], right[train], rows.stimulus_local_id.to_numpy()[train],
                                             rows.split_group_id.to_numpy()[train], scope, seed=seed, linear_only=linear_only)
                te = rows.loc[test].reset_index(drop=True)
                x, z = left[test], right[test]
                # Complete the full head matrix before persisting any fold prediction.
                with (destination / f"outer{number}_{mode}_heads.pkl").open("xb") as stream:
                    pickle.dump(fitted, stream)
                conditions = {"none": None, "zero_first": None, "zero_second": None}
                for kind, opposite in (("same_class", False), ("opposite_class", True)):
                    donors = replacement_indices(te, opposite=opposite, seed=seed)
                    if np.any(donors < 0):
                        missing.append(f"{mode} outer{number} {kind} donor support")
                        continue
                    conditions[kind + "_first"] = donors
                    conditions[kind + "_second"] = donors
                for condition, donor in conditions.items():
                    parts = []
                    for (family, view), head in fitted.items():
                        if condition != "none" and view not in ("C_LR", "C_LL", "C_RR"):
                            continue
                        p = head.predict(x, z, intervention=None if condition == "none" else condition, donor_indices=donor)
                        parts.append(_prediction_rows(te, p, mode=mode, fold=number, family=family, view=view,
                                                      intervention=condition, donor=donor))
                    prediction = pd.concat(parts, ignore_index=True)
                    prediction.to_parquet(prediction_dir / f"outer{number}_{mode}_{condition}.parquet", index=False)
                    losses.extend(_candidate_losses(prediction))
                fits.extend(dict(representation=mode, outer_fold=number, family=f, model=v,
                                 regularization=head.regularization, temperature=head.temperature, **head.evidence)
                            for (f, v), head in fitted.items())
                coverage.append(dict(representation=mode, outer_fold=number, status="COMPLETE_FOLD",
                    training_groups=int(rows.loc[train].split_group_id.nunique()), test_groups=int(te.split_group_id.nunique()),
                    training_trials=int(train.sum()), test_trials=int(test.sum()), conditions=list(conditions)))
                for path, expected in hashes.items():
                    if digest(path) != expected:
                        raise ValueError("C_INPUT_CHANGED_DURING_READOUT")
                del left, right, rows, fitted, prediction, parts
        write_json(destination / "fit_scopes.json", fits)
        write_json(destination / "input_hashes.json", input_hashes)
        pd.DataFrame(coverage).to_csv(public / "coverage.csv", index=False)
        frame = pd.DataFrame(losses)
        frame.to_parquet(destination / "candidate_losses.parquet", index=False)
        if len(frame):
            group_columns = ["representation", "family", "model", "probability_mode"]
            aggregate_metrics = frame[frame.intervention.eq("none")].groupby(group_columns).agg(
                ce_bits=("ce_bits", "mean"), bacc=("bacc", "mean"), auroc=("auroc", "mean"),
                brier=("brier", "mean"), candidate_groups=("split_group_id", "nunique"),
                class0_trials=("class0_trials", "sum"), class1_trials=("class1_trials", "sum")).reset_index()
            aggregate_metrics.to_csv(public / "classification_metrics.csv", index=False)
        gains, interventions = summarize_losses(frame, seed, families=("linear",) if linear_only else ("linear", "mlp32")) if len(frame) else ([], [])
        pd.DataFrame(gains).to_csv(public / "single_joint_gains.csv", index=False)
        pd.DataFrame([row for row in gains if "margin" in row["statistic"]]).to_csv(public / "capacity_controls.csv", index=False)
        pd.DataFrame(interventions).to_csv(public / "fixed_head_interventions.csv", index=False)
        summary = screen(gains, missing)
        summary.update(stage="C_PAIRED_READOUT", completed_model_folds=sum(v["status"] == "COMPLETE_FOLD" for v in coverage),
                       evaluated_modes=list(modes), uncertainty="2000 fixed OOF cluster draws, not full-workflow refitting")
        if digest(plan_path) != contract["plan_hash"] or digest(split_path) != plan["split_hash"]:
            raise ValueError("C_PLAN_CHANGED_DURING_READOUT")
        for path, expected in input_hashes.items():
            if digest(path) != expected:
                raise ValueError("C_INPUT_CHANGED_DURING_READOUT")
        write_json(public / "summary.json", summary)
        write_json(destination / "completion.json", dict(status=summary["status"], summary=summary,
            output_hashes={str(p.relative_to(destination)): digest(p) for p in destination.rglob("*") if p.is_file()}))
        return summary
    except Exception as exc:
        # Verbose exception messages can include private paths; public gets only type/code.
        write_json(destination / "failure.json", dict(exception_type=type(exc).__name__, detail=str(exc), coverage=coverage))
        failure = dict(stage="C_PAIRED_READOUT", status="FAIL", exception_type=type(exc).__name__,
                       reason="readout input, support, control or solver contract failed; private audit retained",
                       full_route_complete=False)
        write_json(public / "failure.json", failure)
        return failure
