"""M0-M4 outer/inner protocol, the two mandated controls, and the paired intervals.

Plan sections 8, 9 and 10.

Protocol per outer fold, in this order, all selection inside the outer training set:
  1. M0  clinical family x clinical penalty, chosen on pooled inner-validation MAE.
  2. M1  same grid on C+Q. Its selected specification is then REUSED unchanged for
         M2/M3/M4 in this fold, so the comparison does not spend extra freedom.
  3. M2  block ridge on [C+Q | segment-feature mean] over the EEG penalties, with an
         explicit EEG-off candidate retained (config eeg_ridge_include_baseline).
  4. M3/M4  for each neural penalty, both seeds are trained on each inner-training set,
         their validation predictions are averaged FIRST, and the pooled MAE of that
         average selects the penalty. The final model averages the two seeds again.

Ties are broken by a fixed order - simpler basis, then stronger penalty, then EEG off -
never by outer-test risk. There is no early stopping of any kind.

The neural penalty is the plan's `lambda/2 * sum(weight^2)` with the bias unpenalised.
`train_set_network` implements `p * sum(w^2)` with gradient `2p*w`, so it is called with
`p = lambda/2`, which reproduces the plan's objective and gradient exactly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from auditory_fn1.models import (
    PARAMETER_COUNT,
    SetNetwork,
    TabularTransform,
    clip_to_bounds,
    ridge_solution,
    train_set_network,
)
from auditory_fn1.statistics import error_metrics, leave_one_identity_range, paired_identity_bootstrap, shared_draws

MODEL_IDS = ("M0_C", "M1_CQ", "M2_MEAN_RIDGE", "M3_MEAN_THEN_MLP", "M4_MLP_THEN_MEAN")
EEG_OFF = "eeg_off"


@dataclass
class Dataset:
    groups: np.ndarray          # identity per record
    clinical: np.ndarray        # C
    technical: np.ndarray       # Q
    amplitude: np.ndarray       # single amplitude-sensitivity column
    segments: np.ndarray        # (n, 32, 140)
    target: np.ndarray          # source units
    bounds: tuple[float, float]


def _design(transform: TabularTransform, matrix: np.ndarray) -> np.ndarray:
    return transform.transform(matrix)


def _fit_linear(design_train: np.ndarray, y_train: np.ndarray, design_eval: np.ndarray,
                penalties: np.ndarray, ledger, context: dict) -> np.ndarray:
    ledger.reserve("linear", context)
    coef, intercept = ridge_solution(design_train, y_train, penalties)
    centre = design_train.mean(axis=0, keepdims=True)
    return intercept + (design_eval - centre) @ coef


def _clinical_candidates(config: dict) -> list[tuple[str, float]]:
    families = list(config["models"]["clinical_families"])
    penalties = [float(p) for p in config["models"]["clinical_penalties"]]
    # Fixed tie order: simpler basis first, stronger penalty first.
    return [(family, penalty) for family in families for penalty in sorted(penalties, reverse=True)]


def _select_tabular(data: Dataset, matrix: np.ndarray, train: np.ndarray, inner: Sequence[dict],
                    config: dict, ledger, tag: str) -> dict:
    """Choose (family, penalty) on pooled inner-validation MAE in source units."""
    lo, hi = data.bounds
    best = None
    trace = []
    for family, penalty in _clinical_candidates(config):
        errors = []
        for spec in inner:
            itrain, ival = spec["train_idx"], spec["validation_idx"]
            transform = TabularTransform(family).fit(matrix[itrain])
            design_train, design_val = _design(transform, matrix[itrain]), _design(transform, matrix[ival])
            prediction = _fit_linear(design_train, data.target[itrain], design_val,
                                     np.full(design_train.shape[1], penalty), ledger,
                                     {"stage": tag, "family": family, "penalty": penalty,
                                      "inner_fold": spec["inner_fold"]})
            errors.append(np.abs(clip_to_bounds(prediction, data.bounds) - data.target[ival]))
        mae = float(np.concatenate(errors).mean())
        trace.append({"family": family, "penalty": penalty, "inner_MAE": mae})
        if best is None or mae < best["inner_MAE"] - 1e-12:
            best = {"family": family, "penalty": penalty, "inner_MAE": mae}
    return {"selected": best, "trace": trace}


def _tabular_outer(data: Dataset, matrix: np.ndarray, train: np.ndarray, test: np.ndarray,
                   spec: dict, ledger, tag: str) -> np.ndarray:
    transform = TabularTransform(spec["family"]).fit(matrix[train])
    design_train, design_test = _design(transform, matrix[train]), _design(transform, matrix[test])
    prediction = _fit_linear(design_train, data.target[train], design_test,
                             np.full(design_train.shape[1], spec["penalty"]), ledger,
                             {"stage": tag + "_final"})
    return prediction


def _segment_scaler(segments: np.ndarray, train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Identity-equal, window-equal centre and scale, fitted on training identities only."""
    block = segments[train]
    centre = block.mean(axis=(0, 1))
    spread = block.std(axis=(0, 1))
    return centre, np.where(spread <= 0, 1.0, spread)


def _m2(data: Dataset, matrix: np.ndarray, train: np.ndarray, test: np.ndarray, inner: Sequence[dict],
        clinical_spec: dict, config: dict, ledger) -> dict:
    """Block ridge on [tabular | segment mean], EEG penalty selected inner, EEG-off kept."""
    candidates: list[object] = [float(p) for p in sorted(config["models"]["eeg_ridge_penalties"], reverse=True)]
    if config["models"]["eeg_ridge_include_baseline"]:
        candidates.append(EEG_OFF)
    best, trace = None, []
    for candidate in candidates:
        errors = []
        for spec in inner:
            itrain, ival = spec["train_idx"], spec["validation_idx"]
            transform = TabularTransform(clinical_spec["family"]).fit(matrix[itrain])
            base_train, base_val = _design(transform, matrix[itrain]), _design(transform, matrix[ival])
            if candidate == EEG_OFF:
                design_train, design_val = base_train, base_val
                penalties = np.full(base_train.shape[1], clinical_spec["penalty"])
            else:
                centre, scale = _segment_scaler(data.segments, itrain)
                mean_train = ((data.segments[itrain] - centre) / scale).mean(axis=1)
                mean_val = ((data.segments[ival] - centre) / scale).mean(axis=1)
                design_train = np.hstack([base_train, mean_train])
                design_val = np.hstack([base_val, mean_val])
                penalties = np.concatenate([np.full(base_train.shape[1], clinical_spec["penalty"]),
                                            np.full(mean_train.shape[1], float(candidate))])
            prediction = _fit_linear(design_train, data.target[itrain], design_val, penalties, ledger,
                                     {"stage": "M2", "candidate": str(candidate), "inner_fold": spec["inner_fold"]})
            errors.append(np.abs(clip_to_bounds(prediction, data.bounds) - data.target[ival]))
        mae = float(np.concatenate(errors).mean())
        trace.append({"candidate": str(candidate), "inner_MAE": mae})
        if best is None or mae < best["inner_MAE"] - 1e-12:
            best = {"candidate": candidate, "inner_MAE": mae}
    transform = TabularTransform(clinical_spec["family"]).fit(matrix[train])
    base_train, base_test = _design(transform, matrix[train]), _design(transform, matrix[test])
    if best["candidate"] == EEG_OFF:
        design_train, design_test = base_train, base_test
        penalties = np.full(base_train.shape[1], clinical_spec["penalty"])
    else:
        centre, scale = _segment_scaler(data.segments, train)
        design_train = np.hstack([base_train, ((data.segments[train] - centre) / scale).mean(axis=1)])
        design_test = np.hstack([base_test, ((data.segments[test] - centre) / scale).mean(axis=1)])
        penalties = np.concatenate([np.full(base_train.shape[1], clinical_spec["penalty"]),
                                    np.full(design_train.shape[1] - base_train.shape[1], float(best["candidate"]))])
    prediction = _fit_linear(design_train, data.target[train], design_test, penalties, ledger,
                             {"stage": "M2_final"})
    return {"prediction": prediction, "selected": {"candidate": str(best["candidate"]),
                                                   "inner_MAE": best["inner_MAE"]}, "trace": trace}


def _train_network(data: Dataset, matrix: np.ndarray, order: str, train: np.ndarray, evaluate: np.ndarray,
                   clinical_spec: dict, neural_penalty: float, seed: int, config: dict, ledger,
                   context: dict) -> np.ndarray:
    lo, hi = data.bounds
    scale_span = hi - lo
    transform = TabularTransform(clinical_spec["family"]).fit(matrix[train])
    design_train, design_eval = _design(transform, matrix[train]), _design(transform, matrix[evaluate])
    centre, spread = _segment_scaler(data.segments, train)
    segments_train = (data.segments[train] - centre) / spread
    segments_eval = (data.segments[evaluate] - centre) / spread
    y_train = (data.target[train] - lo) / scale_span
    network = SetNetwork(order="mean_then_map" if order == "M3" else "map_then_mean",
                         clinical_dim=design_train.shape[1], seed=int(seed))
    ledger.reserve("neural", context)
    train_set_network(network, segments_train, design_train, y_train,
                      steps=int(config["models"]["optimization_steps"]),
                      learning_rate=float(config["models"]["learning_rate"]),
                      # plan form lambda/2 * sum(w^2); train_set_network uses p*sum(w^2)
                      neural_penalty=float(neural_penalty) / 2.0,
                      clinical_penalty=float(clinical_spec["penalty"]))
    prediction, _ = network.forward(segments_eval, design_eval)
    return prediction * scale_span + lo


def _network_model(data: Dataset, matrix: np.ndarray, order: str, train: np.ndarray, test: np.ndarray,
                   inner: Sequence[dict], clinical_spec: dict, config: dict, ledger) -> dict:
    seeds = [int(s) for s in config["models"]["seeds"]]
    penalties = [float(p) for p in sorted(config["models"]["neural_penalties"], reverse=True)]
    best, trace = None, []
    for penalty in penalties:
        errors = []
        for spec in inner:
            itrain, ival = spec["train_idx"], spec["validation_idx"]
            seed_predictions = [
                _train_network(data, matrix, order, itrain, ival, clinical_spec, penalty, seed, config, ledger,
                               {"stage": order, "penalty": penalty, "seed": seed, "inner_fold": spec["inner_fold"]})
                for seed in seeds
            ]
            # Average the two seeds BEFORE scoring, per config seed_aggregation.
            averaged = np.mean(seed_predictions, axis=0)
            errors.append(np.abs(clip_to_bounds(averaged, data.bounds) - data.target[ival]))
        mae = float(np.concatenate(errors).mean())
        trace.append({"penalty": penalty, "inner_MAE": mae})
        if best is None or mae < best["inner_MAE"] - 1e-12:
            best = {"penalty": penalty, "inner_MAE": mae}
    final = [_train_network(data, matrix, order, train, test, clinical_spec, best["penalty"], seed, config, ledger,
                            {"stage": order + "_final", "penalty": best["penalty"], "seed": seed})
             for seed in seeds]
    return {"prediction": np.mean(final, axis=0), "selected": best, "trace": trace,
            "parameter_count": PARAMETER_COUNT}


def run_outer(data: Dataset, folds: Sequence[dict], config: dict, ledger) -> dict:
    """Execute the full M0-M4 matrix over the frozen outer folds."""
    n = data.target.size
    predictions = {model: np.full(n, np.nan) for model in MODEL_IDS}
    unclipped = {model: np.full(n, np.nan) for model in MODEL_IDS}
    selections: list[dict] = []
    tabular_C = data.clinical
    tabular_CQ = np.hstack([data.clinical, data.technical])

    for fold in folds:
        train, test, inner = fold["train_idx"], fold["test_idx"], fold["inner"]
        m0_spec = _select_tabular(data, tabular_C, train, inner, config, ledger, "M0")
        m0 = _tabular_outer(data, tabular_C, train, test, m0_spec["selected"], ledger, "M0")
        m1_spec = _select_tabular(data, tabular_CQ, train, inner, config, ledger, "M1")
        m1 = _tabular_outer(data, tabular_CQ, train, test, m1_spec["selected"], ledger, "M1")
        # M1's clinical specification is reused unchanged by M2/M3/M4 in this fold.
        shared_spec = m1_spec["selected"]
        m2 = _m2(data, tabular_CQ, train, test, inner, shared_spec, config, ledger)
        m3 = _network_model(data, tabular_CQ, "M3", train, test, inner, shared_spec, config, ledger)
        m4 = _network_model(data, tabular_CQ, "M4", train, test, inner, shared_spec, config, ledger)
        raw = {"M0_C": m0, "M1_CQ": m1, "M2_MEAN_RIDGE": m2["prediction"],
               "M3_MEAN_THEN_MLP": m3["prediction"], "M4_MLP_THEN_MEAN": m4["prediction"]}
        for model, values in raw.items():
            unclipped[model][test] = values
            predictions[model][test] = clip_to_bounds(values, data.bounds)
        selections.append({
            "outer_fold": fold["outer_fold"],
            "M0": m0_spec["selected"], "M1": m1_spec["selected"],
            "shared_clinical_spec": shared_spec,
            "M2": m2["selected"], "M3": m3["selected"], "M4": m4["selected"],
            "n_train": int(train.size), "n_test": int(test.size),
        })
    return {"predictions": predictions, "unclipped": unclipped, "selections": selections}


def paired_table(data: Dataset, predictions: dict, config: dict) -> list[dict]:
    """The three mandated comparisons plus M2, all on one shared identity resample."""
    repetitions = int(config["validation"]["bootstrap_repetitions"])
    seed = int(config["validation"]["bootstrap_seed"])
    draws = shared_draws(data.target.size, repetitions=repetitions, seed=seed)
    errors = {model: np.abs(values - data.target) for model, values in predictions.items()}
    comparisons = [
        ("M0_C", "M4_MLP_THEN_MEAN", "complete method vs original clinical numbers"),
        ("M1_CQ", "M4_MLP_THEN_MEAN", "EEG increment beyond the acquisition summary (main archival increment)"),
        ("M3_MEAN_THEN_MLP", "M4_MLP_THEN_MEAN", "learn-then-aggregate vs aggregate-then-learn (main method comparison)"),
        ("M1_CQ", "M2_MEAN_RIDGE", "fixed segment-mean EEG reference"),
        ("M0_C", "M1_CQ", "technical summary alone"),
    ]
    rows = []
    for reference, candidate, meaning in comparisons:
        record = paired_identity_bootstrap(errors[reference], errors[candidate],
                                           repetitions=repetitions, seed=seed, draws=draws)
        record.update({"reference": reference, "candidate": candidate, "meaning": meaning,
                       **{f"loo_{k}": v for k, v in leave_one_identity_range(errors[reference], errors[candidate]).items()}})
        rows.append(record)
    return rows


# ----------------------------------------------------------------- mandated controls


def _derangement(rng: np.random.Generator, size: int) -> np.ndarray:
    """A permutation with no fixed point, so no package keeps its own clinical row."""
    if size < 2:
        raise ValueError("DERANGEMENT_REQUIRES_AT_LEAST_TWO_RECORDS")
    while True:
        candidate = rng.permutation(size)
        if not np.any(candidate == np.arange(size)):
            return candidate


def amplitude_control(data: Dataset, folds: Sequence[dict], selections: Sequence[dict], config: dict,
                      ledger) -> dict:
    """Refit M1 and M4 only, with one amplitude summary added to Q.

    The outer selections from the main matrix are FROZEN and reused; no new grid is
    opened. Plan section 10.1 item 2.
    """
    n = data.target.size
    augmented = np.hstack([data.clinical, data.technical, data.amplitude.reshape(-1, 1)])
    predictions = {"M1_CQ_amplitude": np.full(n, np.nan), "M4_amplitude": np.full(n, np.nan)}
    by_fold = {s["outer_fold"]: s for s in selections}
    for fold in folds:
        train, test = fold["train_idx"], fold["test_idx"]
        spec = by_fold[fold["outer_fold"]]
        m1 = _tabular_outer(data, augmented, train, test, spec["shared_clinical_spec"], ledger, "M1_amplitude")
        predictions["M1_CQ_amplitude"][test] = clip_to_bounds(m1, data.bounds)
        seeds = [int(s) for s in config["models"]["seeds"]]
        final = [_train_network(data, augmented, "M4", train, test, spec["shared_clinical_spec"],
                                float(spec["M4"]["penalty"]), seed, config, ledger,
                                {"stage": "M4_amplitude", "seed": seed, "outer_fold": fold["outer_fold"]})
                 for seed in seeds]
        predictions["M4_amplitude"][test] = clip_to_bounds(np.mean(final, axis=0), data.bounds)
    return predictions


def mismatch_control(data: Dataset, folds: Sequence[dict], selections: Sequence[dict], config: dict,
                     ledger) -> dict:
    """Break the training correspondence between a whole 32-window package and its row.

    The derangement is applied ONLY inside each outer training set; the test packages are
    left paired with their own records. This is a content diagnostic, not a formal
    conditional-exchangeability permutation p-value. Plan section 10.1 item 3.
    """
    n = data.target.size
    predictions = {"M4_mismatch": np.full(n, np.nan)}
    by_fold = {s["outer_fold"]: s for s in selections}
    seed_base = int(config["controls"]["mismatch_seed"])
    tabular_CQ = np.hstack([data.clinical, data.technical])
    for fold in folds:
        train, test = fold["train_idx"], fold["test_idx"]
        spec = by_fold[fold["outer_fold"]]
        rng = np.random.default_rng(seed_base + int(fold["outer_fold"]))
        order = _derangement(rng, train.size)
        shuffled = data.segments.copy()
        shuffled[train] = data.segments[train][order]
        scrambled = Dataset(groups=data.groups, clinical=data.clinical, technical=data.technical,
                            amplitude=data.amplitude, segments=shuffled, target=data.target,
                            bounds=data.bounds)
        seeds = [int(s) for s in config["models"]["seeds"]]
        final = [_train_network(scrambled, tabular_CQ, "M4", train, test, spec["shared_clinical_spec"],
                                float(spec["M4"]["penalty"]), seed, config, ledger,
                                {"stage": "M4_mismatch", "seed": seed, "outer_fold": fold["outer_fold"]})
                 for seed in seeds]
        predictions["M4_mismatch"][test] = clip_to_bounds(np.mean(final, axis=0), data.bounds)
    return predictions


def control_table(data: Dataset, main: dict, amplitude: dict, mismatch: dict, config: dict) -> list[dict]:
    repetitions = int(config["validation"]["bootstrap_repetitions"])
    seed = int(config["validation"]["bootstrap_seed"])
    draws = shared_draws(data.target.size, repetitions=repetitions, seed=seed)
    pool = {**main, **amplitude, **mismatch}
    errors = {model: np.abs(values - data.target) for model, values in pool.items()}
    rows = []
    for reference, candidate, meaning in (
        ("M1_CQ_amplitude", "M4_amplitude", "EEG increment after adding the amplitude summary to Q"),
        ("M0_C", "M4_amplitude", "amplitude-adjusted method against the original clinical baseline"),
        ("M1_CQ", "M4_mismatch", "training-correspondence mismatch diagnostic"),
        ("M4_mismatch", "M4_MLP_THEN_MEAN", "real correspondence against mismatched training"),
    ):
        if reference not in errors or candidate not in errors:
            continue
        record = paired_identity_bootstrap(errors[reference], errors[candidate],
                                           repetitions=repetitions, seed=seed, draws=draws)
        record.update({"reference": reference, "candidate": candidate, "meaning": meaning})
        rows.append(record)
    return rows


def metrics_table(data: Dataset, pool: dict) -> list[dict]:
    rows = []
    for model, values in pool.items():
        row = {"model": model, **error_metrics(data.target, values)}
        row["n_at_source_ceiling"] = int(np.count_nonzero(data.target >= data.bounds[1] - 1e-9))
        rows.append(row)
    return rows
