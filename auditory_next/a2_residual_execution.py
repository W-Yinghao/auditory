"""A2 fixed-background residual audit on the frozen Ω trial draws.

This module is deliberately separate from the unadjusted A2 core.  It reuses
the core's exact trial draws and saved post-delta axes, fits one candidate
weighted ridge predictor per outer fold and mode, and reports Delta, P and R
with the exact four-term inner-product decomposition.  It never uses residuals
to select candidates, axes, trials, or modes.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from auditory5.contracts import FitScope
from auditory5.routes.a_matching import bootstrap_match
from .a2_execution import _load_task, apply_summary_axis, fit_summary_axis
from .a2_overlap import TrialDraws, summarize_draws
from .a2_residual_audit import (fit_background, inner_product_decomposition,
                                matching_statistics)
from .provenance import ROOT, digest, finish, require_slurm, write_json


MODES = ("L0", "R_RAND", "R_SUP", "R_SIM")
QUALITY_UNAVAILABLE = "FEATURE_TASK_HAS_NO_FIXED_QUALITY_ARRAY"


def build_background(post_common, pre_common, pre_delta, quality=None):
    """Concatenate the declared background banks without label or residual data."""
    arrays = [np.asarray(value, dtype=float) for value in (post_common, pre_common, pre_delta)]
    if any(value.ndim != 4 or value.shape[2] != 2 or not np.isfinite(value).all() for value in arrays):
        raise ValueError("A2_BACKGROUND_BANK_SCHEMA")
    if any(value.shape[:3] != arrays[0].shape[:3] for value in arrays[1:]):
        raise ValueError("A2_BACKGROUND_BANK_ALIGNMENT")
    names = ["post_common_response", "pre_common_response", "pre_delta"]
    if quality is not None:
        q = np.asarray(quality, dtype=float)
        if q.ndim != 4 or q.shape[:3] != arrays[0].shape[:3] or not np.isfinite(q).all():
            raise ValueError("A2_QUALITY_BANK_SCHEMA")
        arrays.append(q)
        names.append("quality_summary")
    return np.concatenate(arrays, axis=-1), tuple(names)


def _group_bootstrap(matrix, groups, *, seed=20260917, n_boot=2000):
    """Use the audited fixed identity bootstrap on one outer fold matrix."""
    value = np.asarray(matrix, dtype=float)
    ids = [str(group) for group in groups]
    if value.ndim != 2 or value.shape[0] != value.shape[1] or value.shape[0] != len(ids):
        raise ValueError("A2_RESIDUAL_MATRIX_SCHEMA")
    if len(set(ids)) != len(ids) or len(ids) < 2 or not np.isfinite(value).all():
        raise ValueError("A2_RESIDUAL_MATRIX_SUPPORT")
    result = bootstrap_match([value], [ids], n_boot=int(n_boot), seed=int(seed))
    return dict(estimate=float(result["estimate"]), ci_lower=float(result["ci95"][0]),
                ci_upper=float(result["ci95"][1]), n_candidates=len(ids),
                n_bootstrap=int(n_boot), invalid_replicates=int(result["invalid_replicates"]),
                bootstrap_scope="fixed_outer_candidate_identity_draws_no_refit")


def _pair_matrix(vectors, metric):
    """Build the fold-local candidate pair matrix in matching_statistics units."""
    value = np.asarray(vectors, dtype=float)
    if value.ndim != 4 or value.shape[2] != 2 or not np.isfinite(value).all():
        raise ValueError("A2_RESIDUAL_PAIR_INPUT")
    dots = np.einsum("rnf,rmf->rnm", value[:, :, 0], value[:, :, 1])
    if metric == "inner_product":
        return dots.mean(axis=0)
    if metric == "cosine":
        norms = np.linalg.norm(value, axis=-1)
        if np.any(norms == 0):
            raise ValueError("A2_RESIDUAL_ZERO_NORM")
        return (dots / (norms[:, :, 0][:, :, None] * norms[:, :, 1][:, None, :])).mean(axis=0)
    raise ValueError("A2_RESIDUAL_METRIC")


def residual_statistics(delta, background, train_groups, test_groups, *, scope):
    """Fit B only on training candidates and return test Delta/P/R diagnostics."""
    d, b = np.asarray(delta, float), np.asarray(background, float)
    if d.ndim != 4 or b.ndim != 4 or d.shape[:3] != b.shape[:3] or d.shape[2] != 2:
        raise ValueError("A2_RESIDUAL_INPUT_SCHEMA")
    groups = np.asarray(scope.train_groups + tuple(scope.test_groups), dtype=str)
    if len(groups) != d.shape[1] or len(set(groups)) != len(groups):
        raise ValueError("A2_RESIDUAL_GROUP_ALIGNMENT")
    train_groups, test_groups = set(map(str, train_groups)), set(map(str, test_groups))
    if train_groups & test_groups or not train_groups | test_groups <= set(groups):
        raise ValueError("A2_RESIDUAL_SCOPE_OVERLAP")
    train = np.isin(groups, list(train_groups)); test = np.isin(groups, list(test_groups))
    if train.sum() < 2 or test.sum() < 2:
        raise ValueError("A2_RESIDUAL_FOLD_SUPPORT")
    axis = fit_summary_axis(b[:, train], tuple(groups[train]), scope)
    b_projected = apply_summary_axis(b, axis)
    predictor = fit_background(b_projected[:, train].mean(axis=0), d[:, train].mean(axis=0), alpha=10.)
    prediction = predictor.predict(b_projected)
    residual = d - prediction
    return dict(axis=axis, predictor=predictor, prediction=prediction,
                residual=residual, train_mask=train, test_mask=test)


def decomposition_table(delta, prediction, groups):
    """Return private per-pair matrices and public-safe scalar summaries."""
    d, p = np.asarray(delta, float), np.asarray(prediction, float)
    if d.shape != p.shape or d.ndim != 4 or d.shape[2] != 2:
        raise ValueError("A2_RESIDUAL_DECOMPOSITION_SHAPE")
    result = inner_product_decomposition(d[:, :, 0], d[:, :, 1], p[:, :, 0], p[:, :, 1], groups)
    residual = d - p
    stats = {name: matching_statistics(value[:, :, 0], value[:, :, 1], groups)
             for name, value in (("Delta", d), ("P", p), ("R", residual))}
    pair_matrices = {}
    for name, value in (("Delta", d), ("P", p), ("R", residual)):
        for metric in ("inner_product", "cosine"):
            pair_matrices[f"{name}_{metric}"] = _pair_matrix(value, metric)
    return dict(decomposition=result, vector_statistics=stats,
                matrices=result["matrices"], pair_matrices=pair_matrices,
                groups=tuple(map(str, groups)))


def _json(path):
    return json.loads(Path(path).read_text())


def _private(path):
    value = Path(path).resolve()
    if not value.is_relative_to((ROOT / "private/auditory_next_v2").resolve()):
        raise ValueError("A2R_PRIVATE_PATH")
    return value


def _load_frozen_inputs(registry, task_plan, core_run):
    support_run = str(task_plan.get("support_run", registry.get("support_run", "")))
    support = _private(ROOT / "private/auditory_next_v2" / support_run)
    if _json(support / "completion.json").get("status") != "PASS":
        raise ValueError("A2R_SUPPORT_GATE")
    core = _private(ROOT / "private/auditory_next_v2" / core_run)
    core_completion = _json(core / "completion.json")
    if core_completion.get("status") not in ("A2_CORE_RECORDED", "PASS"):
        raise ValueError("A2R_CORE_GATE")
    definition = _json(support / "A2_overlap.json")
    if _json(support / "A2_draw_definition.json").get("definition_hash") != definition["definition_hash"]:
        raise ValueError("A2R_DRAW_DEFINITION")
    with (support / "A2_overlap.pkl").open("rb") as stream:
        frozen = pickle.load(stream)
    draws = TrialDraws(frozen.groups, frozen.omega, frozen.cell_weights,
                       np.load(support / "A2_trial_draws.npy", allow_pickle=False),
                       frozen.definition_hash, 20260917)
    if draws.trial_ids.shape != (20, len(frozen.groups), 2, 2, len(frozen.omega), 6):
        raise ValueError("A2R_DRAW_SHAPE")
    planpath = ROOT / registry["legacy_plan"]
    splitpath = ROOT / registry["legacy_splits"]
    if digest(planpath) != registry["legacy_plan_sha256"] or digest(splitpath) != registry["legacy_split_sha256"]:
        raise ValueError("A2R_PLAN_HASH")
    plan, split = _json(planpath), _json(splitpath)
    gate = _private(ROOT / "private/auditory_next_v2" / str(registry["preflight_run"]))
    inventory = {row["path"]: row["sha256"] for row in _json(gate / "legacy_input_hashes.json")}
    scopes = _json(gate / "feature_scope_registry.json")
    return support, core, frozen, draws, planpath, splitpath, plan, split, inventory, scopes


def _features_for_fold(plan, planpath, split, mode, fold, scopes, inventory, hashes, draws, core):
    folder, rows, evidence, scope_hash = _load_task(plan, planpath, fold, mode, scopes, inventory, hashes)
    with np.load(folder / "features.npz", allow_pickle=False) as arrays:
        trial_ids, groups, labels = arrays["trial_ids"].astype(str), arrays["groups"].astype(str), arrays["y"]
        if not np.array_equal(trial_ids, rows.trial_id.to_numpy(str)) or not np.array_equal(groups, rows.split_group_id.to_numpy(str)):
            raise ValueError("A2R_FEATURE_LEDGER")
        if not np.array_equal(labels, rows.stimulus_local_id.to_numpy(int)):
            raise ValueError("A2R_FEATURE_LABEL_LEDGER")
        expected_ids = set(draws.trial_ids.ravel())
        if not expected_ids <= set(trial_ids):
            raise ValueError("A2R_DRAW_FEATURE_ALIGNMENT")
        means = {}
        for window in ("post", "pre"):
            means[window] = summarize_draws(arrays[window], trial_ids, draws,
                                            feature_scope_id=scope_hash)
        quality = None
        quality_status = QUALITY_UNAVAILABLE
        if "quality" in arrays.files:
            q = summarize_draws(arrays["quality"], trial_ids, draws, feature_scope_id=scope_hash)
            # Quality is a fixed metadata/measurement summary per half.  It
            # has no stimulus-difference axis, so average the two declared
            # classes before adding it to B.
            quality = q["means"].mean(axis=3)
            quality_status = "FIXED_FEATURE_QUALITY_ARRAY"
        axes = {}
        for endpoint, filename in (("post_delta", "post_delta"), ("post_common_response", "common_response"),
                                   ("pre_delta", "pre_delta")):
            window = "post" if endpoint.startswith("post") else "pre"
            axis_path = core / f"{mode}_outer{int(fold['outer_fold'])}_{filename}_axis.pkl"
            if not axis_path.exists():
                raise ValueError("A2R_CORE_AXIS_MISSING")
            hashes[str(axis_path)] = digest(axis_path)
            with axis_path.open("rb") as stream:
                axes[endpoint] = pickle.load(stream)
        by_group = {group: i for i, group in enumerate(means["post"]["groups"])}
        train = tuple(sorted(set(fold["train_groups"]) & set(by_group)))
        test = tuple(sorted(set(fold["test_groups"]) & set(by_group)))
        if len(train) < 2 or len(test) < 2:
            raise ValueError("A2R_OUTER_SUPPORT")
        scope=FitScope(train,test_groups=test)
        axes['pre_common_response']=fit_summary_axis(means['pre']['common_response'][:,[by_group[g] for g in train]],train,scope)
        post_delta = apply_summary_axis(means["post"]["delta"], axes["post_delta"])
        post_common = apply_summary_axis(means["post"]["common_response"], axes["post_common_response"])
        pre_delta = apply_summary_axis(means["pre"]["delta"], axes["pre_delta"])
        pre_common = apply_summary_axis(means["pre"]["common_response"], axes["pre_common_response"])
        selected = [by_group[g] for g in train + test]
        q = quality[:, selected] if quality is not None else None
        b, names = build_background(post_common[:, selected], pre_common[:, selected], pre_delta[:, selected], q)
        d = post_delta[:, selected]
        return dict(delta=d, background=b, background_names=names, groups=np.asarray(train + test, str),
                    train_groups=train, test_groups=test, quality_status=quality_status,
                    feature_scope_hash=scope_hash, axis=axes, trial_ids=trial_ids, rows=rows)


def run(config, registry, site, dest, public, report, task_plan, *, core_run="A2_core_001", smoke=False):
    """Run the fixed A2 residual audit inside Slurm; smoke performs input gates only."""
    require_slurm()
    dest, public, report = map(Path, (dest, public, report))
    if not dest.resolve().is_relative_to(ROOT / "private/auditory_next_v2"):
        raise ValueError("A2R_PRIVATE_OUTPUT_REQUIRED")
    if not public.resolve().is_relative_to(ROOT / "results/auditory_next_v2"):
        raise ValueError("A2R_PUBLIC_OUTPUT_REQUIRED")
    if any((path / name).exists() for path, name in ((dest, "completion.json"), (public, "summary.json"))):
        raise FileExistsError("A2R_RUN_ALREADY_STARTED")
    dest.mkdir(parents=True, exist_ok=True); public.mkdir(parents=True, exist_ok=True); report.mkdir(parents=True, exist_ok=True)
    catalog_path = Path(task_plan["task_csv"]); _private(catalog_path)
    catalog = pd.read_csv(catalog_path)
    real = catalog[(catalog.packet == "A2") & (catalog.fit_stage == "real_train_only_audit")]
    if len(real) != 20:
        raise ValueError("A2R_TASK_PLAN_FIT_COUNT")
    (support, core, frozen, draws, planpath, splitpath, plan, split,
     inventory, scopes) = _load_frozen_inputs(registry, task_plan, core_run)
    hashes = {str(path): digest(path) for path in (catalog_path, support / "A2_overlap.json",
        support / "A2_draw_definition.json", support / "A2_trial_draws.npy", core / "completion.json",
        planpath, splitpath)}
    write_json(dest / "initial_input_hashes.json", hashes)
    if smoke:
        fold = split["folds"][0]
        _features_for_fold(plan, planpath, split, "L0", fold, scopes, inventory, hashes, draws, core)
        write_json(dest / "input_hashes.json", hashes)
        (report / "A2_RESIDUAL_REPORT.md").write_text(
            "# A2 residual input smoke\n\nFrozen support, draws, S0 feature ledgers and the core post-delta axis were aligned. "
            "No background predictor was fitted.\n", encoding="utf-8")
        return finish(dest, public, dict(status="SMOKE_INPUT_GATE", new_readout_fits=0,
            expected_real_fits=20, quality_status=QUALITY_UNAVAILABLE))
    private_decomp, public_rows, receipts, predictors = [], [], [], {};all_matrices={}
    for mode in MODES:
        for fold in split["folds"]:
            number = int(fold["outer_fold"])
            values = _features_for_fold(plan, planpath, split, mode, fold, scopes, inventory, hashes, draws, core)
            scope = FitScope(tuple(values["train_groups"]), test_groups=tuple(values["test_groups"]))
            fitted = residual_statistics(values["delta"], values["background"], values["train_groups"],
                                         values["test_groups"], scope=scope)
            test_idx = fitted["test_mask"]
            test_delta, test_pred = values["delta"][:, test_idx], fitted["prediction"][:, test_idx]
            test_groups = values["groups"][test_idx]
            details = decomposition_table(test_delta, test_pred, test_groups)
            all_matrices.setdefault(mode,[]).append(details)
            predictors[f"{mode}_outer{number}"] = fitted["predictor"]
            with (dest / f"{mode}_outer{number}_background_axis.pkl").open("xb") as stream:
                pickle.dump(fitted["axis"], stream)
            with (dest / f"{mode}_outer{number}_predictor.pkl").open("xb") as stream:
                pickle.dump(fitted["predictor"], stream)
            with (dest / f"{mode}_outer{number}_pair_matrices.pkl").open("xb") as stream:
                pickle.dump(details, stream)
            for endpoint, metric in (("Delta", "inner_product"), ("P", "inner_product"), ("R", "inner_product"),
                                     ("Delta", "cosine"), ("P", "cosine"), ("R", "cosine")):
                stat = details["vector_statistics"][endpoint][metric]
                # matching_statistics averages repeat-level pair values; use
                # the same operation for the fixed identity bootstrap.
                vectors = test_delta if endpoint == "Delta" else test_pred if endpoint == "P" else test_delta - test_pred
                matrix = _pair_matrix(vectors, metric)
                boot = _group_bootstrap(matrix, test_groups, seed=20260917 + number)
                public_rows.append(dict(mode=mode, outer_fold=number, quantity=endpoint, metric=metric,
                    matched=float(stat["matched"]), mismatched=float(stat["mismatched"]), gain=float(stat["gain"]), **boot,
                    quality_status=values["quality_status"], background_components="|".join(values["background_names"])))
            for name, summary in details["decomposition"]["summaries"].items():
                private_decomp.append(dict(mode=mode, outer_fold=number, term=name, **summary))
            receipts.append(dict(mode=mode, outer_fold=number, status="PASS", fit_scope=scope.train_groups,
                test_scope=scope.test_groups, background_components=values["background_names"],
                background_dimension=int(values["background"].shape[-1]), target_dimension=int(values["delta"].shape[-1]),
                quality_status=values["quality_status"], max_pair_error=details["decomposition"]["max_pair_error"],
                matching_gain_error=details["decomposition"]["matching_gain_error"], alpha=10.))
    if len(receipts) != 20:
        raise ValueError("A2R_REAL_FIT_COUNT")
    for mode,details in all_matrices.items():
        ids=[list(d['groups']) for d in details]
        for key in details[0]['pair_matrices']:
            boot=bootstrap_match([d['pair_matrices'][key] for d in details],ids,n_boot=2000,seed=20260917)
            quantity,metric=key.split('_',1)
            public_rows.append(dict(mode=mode,outer_fold='ALL',quantity=quantity,metric=metric,estimate=boot['estimate'],
                ci_lower=boot['ci95'][0],ci_upper=boot['ci95'][1],n_candidates=sum(map(len,ids)),n_bootstrap=2000,
                invalid_replicates=boot['invalid_replicates'],bootstrap_scope='fixed candidate draws within original folds; no refits'))
    pd.DataFrame(private_decomp).to_parquet(dest / "residual_inner_product_decomposition.parquet", index=False)
    # The decomposition summaries contain no trial, path, or identity fields;
    # pair matrices themselves remain private.
    pd.DataFrame(private_decomp).to_csv(public / "residual_inner_product_decomposition.csv", index=False)
    if any(digest(Path(path)) != value for path, value in hashes.items()):
        raise ValueError("A2R_IMMUTABLE_DEPENDENCY_CHANGED")
    write_json(dest / "input_hashes.json", hashes)
    write_json(dest / "fit_receipts.json", receipts)
    with (dest / "predictors.pkl").open("xb") as stream:
        pickle.dump(predictors, stream)
    pd.DataFrame(public_rows).to_csv(public / "residual_aggregate.csv", index=False)
    (report / "A2_RESIDUAL_REPORT.md").write_text(
        "# A2 background residual audit\n\nEach outer fold and mode fit one candidate-weighted alpha=10 ridge predictor "
        "from post common response, pre common response and pre delta summaries. The target post Delta uses the saved "
        "A2-core training-only axis. Four-term inner-product identities are retained per pair in private outputs. "
        "Quality arrays are included only when present in the frozen feature task; otherwise the audit records that limitation. "
        "Residual results are diagnostic and do not replace the unadjusted A2 endpoint.\n", encoding="utf-8")
    return finish(dest, public, dict(status="A2_RESIDUAL_RECORDED", new_readout_fits=20,
        encoder_fits=0, decomposition_rows=len(private_decomp), quality_status=sorted(set(r["quality_status"] for r in receipts)),
        scientific_status="DIAGNOSTIC_ONLY", residual_primary=False))
