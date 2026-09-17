"""Interim B L0_HISTORY: group-held-out conditional history readouts.

This module consumes stored pre-QC history. It never rebuilds the event chain
after EEG rejection. See docs/auditory5_B_readout_v1.md for frozen support,
context and reporting rules. R_SIM/R_SUP and remaining diagnostics are pending.
"""

from dataclasses import dataclass
import json
import math
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import SplineTransformer

from auditory5.contracts import FitScope, validate_history_context
from auditory5.datasets import load_dataset
from auditory5.metrics import candidate_log_losses_bits
from auditory5.probes import (C_GRID, CandidateTabularScaler, CandidateWeightedPCA, bin_20ms,
                             candidate_class_weights, fit_temperature, weighted_log_loss_nats,
                             _fit_head, _head_logits)
from auditory5.provenance import ROOT, digest, require_slurm, write_json
from auditory5.statistics import paired_cluster_bootstrap


CONTEXT_COLUMNS = ("log_previous_gap_s", "record_position_fraction",
                   "log_previous_gap_s_squared", "record_position_fraction_squared")
CORE_MODELS = ("B0_context_linear", "B0_context_spline", "B1_pre", "B2_post", "B3_pre_post")


def context_frame(rows):
    """Only gap and position generate C; no history target, run length or ID."""
    gap = rows.previous_gap_s.to_numpy(float)
    position = rows.segment_position_fraction.to_numpy(float)
    if (not np.isfinite(gap).all() or np.any(gap <= 0) or not np.isfinite(position).all()
            or np.any((position < 0) | (position > 1))):
        raise ValueError("B_CONTEXT_SUPPORT: finite positive gap and position in [0,1] required")
    log_gap = np.log(gap)
    frame = pd.DataFrame(dict(zip(CONTEXT_COLUMNS, (log_gap, position, log_gap ** 2, position ** 2))))
    validate_history_context(frame.columns)
    return frame


def history_eligible(rows):
    """Fixed current/previous literal pair and known binary original history."""
    return (rows.event_literal.eq("1") & rows.previous_code.eq("1") &
            rows.history_target.isin([0, 1]) & rows.accepted.fillna(False)).to_numpy(bool)


@dataclass
class CommonSupport:
    gap_edges: np.ndarray
    minimum_log_gap: float
    maximum_log_gap: float
    strata: tuple
    fit_groups: tuple
    support_counts: list

    @classmethod
    def fit(cls, rows, scope):
        scope.assert_fit_groups(rows.split_group_id)
        if rows.empty:
            raise ValueError("B_CONTEXT_SUPPORT: empty training context")
        base = context_frame(rows).to_numpy()[:, :2]
        edges = np.unique(np.quantile(base[:, 0], [1 / 3, 2 / 3]))
        provisional = cls(edges, float(base[:, 0].min()), float(base[:, 0].max()), (),
                          tuple(sorted(rows.split_group_id.unique())), [])
        strata = provisional.stratum_ids(rows)
        counts = []
        supported = []
        for value in sorted(set(strata)):
            count = [int(np.sum((strata == value) & rows.history_target.eq(h).to_numpy())) for h in (0, 1)]
            keep = min(count) >= 5
            counts.append(dict(stratum=int(value), history0=count[0], history1=count[1], supported=keep))
            if keep:
                supported.append(int(value))
        provisional.strata, provisional.support_counts = tuple(supported), counts
        return provisional

    def stratum_ids(self, rows):
        base = context_frame(rows).to_numpy()[:, :2]
        gap_bin = np.searchsorted(self.gap_edges, base[:, 0], side="right")
        position_bin = np.minimum(np.floor(base[:, 1] * 3).astype(int), 2)
        return gap_bin * 3 + position_bin

    def mask(self, rows):
        if rows.empty:
            return np.zeros(0, bool)
        log_gap = context_frame(rows).iloc[:, 0].to_numpy()
        return (np.isin(self.stratum_ids(rows), self.strata) &
                (log_gap >= self.minimum_log_gap - 1e-12) &
                (log_gap <= self.maximum_log_gap + 1e-12))

    def to_dict(self):
        return dict(gap_log_quantile_edges=self.gap_edges.tolist(),
                    minimum_log_gap=self.minimum_log_gap, maximum_log_gap=self.maximum_log_gap,
                    position_edges=[0., 1 / 3, 2 / 3, 1.], supported_strata=list(self.strata),
                    fit_groups=list(self.fit_groups), initial_training_support_counts=self.support_counts,
                    per_stratum_each_history_minimum=5)


def candidate_support_mask(rows, initial=None):
    """Both H need >=20 trials spanning >=4 original 30 s blocks, per identity group."""
    selected = np.ones(len(rows), bool) if initial is None else np.asarray(initial, bool)
    result = np.zeros(len(rows), bool)
    for group in rows.split_group_id.unique():
        own = rows.split_group_id.eq(group).to_numpy() & selected
        valid = all(np.sum(own & rows.history_target.eq(h).to_numpy()) >= 20 and
                    rows.loc[own & rows.history_target.eq(h).to_numpy(), "time_block_id"].nunique() >= 4
                    for h in (0, 1))
        if valid:
            result |= own
    return result


def select_common_support(train_rows, test_rows, scope, *, frozen_gate=None):
    """Fit only on train, then freeze before observing test support/labels.

    Candidate removal can invalidate a pooled stratum. A monotone training-only
    fixed point removes such strata, retaining the initially fitted gap edges.
    No test observations or test counts can add/remove a training stratum.
    """
    if frozen_gate is None:
        gate = CommonSupport.fit(train_rows, scope)
    else:
        scope.assert_fit_groups(train_rows.split_group_id)
        gate = CommonSupport(frozen_gate.gap_edges.copy(), frozen_gate.minimum_log_gap,
                             frozen_gate.maximum_log_gap, frozen_gate.strata,
                             tuple(sorted(train_rows.split_group_id.unique())), frozen_gate.support_counts)
    while True:
        train_mask = candidate_support_mask(train_rows, gate.mask(train_rows))
        strata = gate.stratum_ids(train_rows)
        supported = tuple(value for value in gate.strata
                          if all(np.sum(train_mask & (strata == value) &
                                        train_rows.history_target.eq(h).to_numpy()) >= 5 for h in (0, 1)))
        if supported == gate.strata:
            break
        gate.strata = supported
    test_mask = candidate_support_mask(test_rows, gate.mask(test_rows))
    return train_mask, test_mask, gate


class ContextFeatures:
    """Four fixed C terms plus train-only three-knot cubic splines of gap/position."""

    def fit(self, rows, scope):
        scope.assert_fit_groups(rows.split_group_id)
        c = context_frame(rows).to_numpy()
        self.active_ = np.ptp(c[:, :2], axis=0) > 1e-12
        self.spline_ = None
        if self.active_.any():
            self.spline_ = SplineTransformer(n_knots=3, degree=3, knots="uniform",
                                              include_bias=False, extrapolation="constant")
            self.spline_.fit(c[:, :2][:, self.active_])
        self.linear_scaler_ = CandidateTabularScaler().fit(c, rows.split_group_id, scope)
        self.strong_scaler_ = CandidateTabularScaler().fit(self._strong(c), rows.split_group_id, scope)
        self.fit_groups_ = tuple(sorted(rows.split_group_id.unique()))
        return self

    def _strong(self, c):
        return np.c_[c, self.spline_.transform(c[:, :2][:, self.active_])] if self.spline_ is not None else c

    def transform(self, rows, *, strong=True):
        c = context_frame(rows).to_numpy()
        return self.strong_scaler_.transform(self._strong(c)) if strong else self.linear_scaler_.transform(c)


@dataclass
class HistoryReadout:
    context: ContextFeatures
    strong: bool
    eeg_scaler: object
    eeg_pca: object
    head: object
    temperature: float
    selected_C: float
    fit_scope: dict

    def transform(self, rows, eeg):
        context = self.context.transform(rows, strong=self.strong)
        if self.eeg_pca is None:
            return context
        return np.c_[context, self.eeg_pca.transform(self.eeg_scaler.transform(eeg))]

    def predict(self, rows, eeg):
        logits = _head_logits(self.head, self.transform(rows, eeg))
        return dict(raw=softmax(logits, axis=1), calibrated=softmax(logits / self.temperature, axis=1))


def _fit_transform(rows, eeg, context, strong, scope):
    c = context.transform(rows, strong=strong)
    if eeg is None:
        return c, None, None
    scaler = CandidateTabularScaler().fit(eeg, rows.split_group_id, scope)
    pca = CandidateWeightedPCA(32).fit(scaler.transform(eeg), rows.split_group_id, scope)
    return np.c_[c, pca.transform(scaler.transform(eeg))], scaler, pca


def fit_history_readouts(rows, eeg_by_model, scope, *, seed=20260917, inner_folds=3):
    """All EEG PCA and context spline fits exclude inner-validation groups.

    Inner folds independently fit the context support gate as well. Only common
    OOF rows with prespecified candidate support calibrate/select every model;
    their coverage is a training diagnostic. Context is never passed through PCA.
    """
    scope.assert_fit_groups(rows.split_group_id)
    groups = rows.split_group_id.to_numpy(str)
    y = rows.history_target.to_numpy(int)
    if len(np.unique(groups)) < inner_folds:
        raise ValueError("B_INNER_SUPPORT: fewer candidate groups than inner folds")
    candidate_class_weights(y, groups)
    oof = {name: {C: np.full((len(rows), 2), np.nan) for C in C_GRID} for name in eeg_by_model}
    folds = []
    for fold, (train, validation) in enumerate(GroupKFold(inner_folds).split(np.zeros(len(rows)), y, groups)):
        inner_scope = FitScope(tuple(np.unique(groups[train])), tuple(np.unique(groups[validation])),
                               tuple(scope.validation_groups) + tuple(scope.test_groups))
        a, b, gate = select_common_support(rows.iloc[train], rows.iloc[validation], inner_scope)
        train, validation = train[a], validation[b]
        if not len(train) or not len(validation):
            raise ValueError("B_INNER_SUPPORT: common-support/candidate gate emptied an inner fold")
        tr, va = rows.iloc[train], rows.iloc[validation]
        context = ContextFeatures().fit(tr, inner_scope)
        for name, eeg in eeg_by_model.items():
            strong = name != "B0_context_linear"
            z, scaler, pca = _fit_transform(tr, None if eeg is None else eeg[train], context, strong, inner_scope)
            valid = context.transform(va, strong=strong)
            if eeg is not None:
                valid = np.c_[valid, pca.transform(scaler.transform(eeg[validation]))]
            for C in C_GRID:
                head = _fit_head(z, y[train], groups[train], C, seed)
                oof[name][C][validation] = _head_logits(head, valid)
        folds.append(dict(fold=fold, fit_groups=sorted(set(groups[train])),
                          validation_groups=sorted(set(groups[validation])), support_gate=gate.to_dict(),
                          scope_hash=inner_scope.hash, training_trials=len(train), validation_trials=len(validation)))
    first_name = next(iter(eeg_by_model))
    available = np.isfinite(oof[first_name][C_GRID[0]]).all(axis=1)
    if not available.any():
        raise ValueError("B_INNER_SUPPORT: no calibratable OOF observations")
    weight = candidate_class_weights(y[available], groups[available])
    context = ContextFeatures().fit(rows, scope)
    result = {}
    for name, eeg in eeg_by_model.items():
        losses = {C: weighted_log_loss_nats(oof[name][C][available], y[available], weight) for C in C_GRID}
        chosen = min(C_GRID, key=lambda C: (losses[C], C))
        calibration = fit_temperature(oof[name][chosen][available], y[available], groups[available], scope)
        z, scaler, pca = _fit_transform(rows, eeg, context, name != "B0_context_linear", scope)
        head = _fit_head(z, y, groups, chosen, seed)
        evidence = dict(fit_groups=sorted(set(groups)), scope_hash=scope.hash, inner_folds=folds,
                        calibration=calibration, C_inner_ce_bits={str(C): value / math.log(2) for C, value in losses.items()},
                        calibration_oof_trials=int(available.sum()), available_training_trials=len(rows),
                        context_dimension=context.transform(rows, strong=name != "B0_context_linear").shape[1],
                        eeg_pca_dimension=0 if pca is None else pca.n_components_,
                        context_reduced_by_PCA=False, encoder_scope="L0 fixed bins; no fitted encoder",
                        weighting_unit="safe identity component used as candidate group")
        result[name] = HistoryReadout(context, name != "B0_context_linear", scaler, pca,
                                      head, calibration["temperature"], chosen, evidence)
    return result


def _features(dataset):
    rows = dataset.rows
    x = dataset.X
    if x.shape[-1] != 175 or not np.all(rows.processed_fs.to_numpy(float) == 250):
        raise ValueError("B_L0_WINDOW: expected new 250 Hz half-open native HA epochs")
    pre = bin_20ms(x[:, :, :50])
    starts = rows.post_start_index.to_numpy(int)
    post = bin_20ms(np.stack([trial[:, start:start + 100] for trial, start in zip(x, starts)]))
    return pre, post


def _summaries(predictions, seed):
    losses = []
    if predictions.empty:
        return pd.DataFrame(), []
    for (analysis_set, model, mode), rows in predictions.groupby(["analysis_set", "model", "probability_mode"]):
        values = candidate_log_losses_bits(rows.history_target.to_numpy(int), rows[["p0", "p1"]].to_numpy(),
                                          rows.split_group_id.to_numpy(str), rows.trial_id.to_numpy(str))
        for group, loss in values.items():
            losses.append(dict(analysis_set=analysis_set, model=model, probability_mode=mode,
                               split_group_id=group, ce_bits=loss))
    frame = pd.DataFrame(losses)
    comparisons = [("main_gain", "B0_context_spline", "B2_post"),
                   ("post_increment_over_pre", "B1_pre", "B3_pre_post"),
                   ("post_increment_over_previous", "B4_previous", "B5_previous_post")]
    output = []
    for (analysis_set, mode), rows in frame.groupby(["analysis_set", "probability_mode"]):
        table = rows.pivot(index="split_group_id", columns="model", values="ce_bits")
        for comparison, baseline, augmented in comparisons:
            if baseline not in table or augmented not in table:
                continue
            paired = table[[baseline, augmented]].dropna()
            if paired.empty:
                continue
            ci = paired_cluster_bootstrap(paired[baseline], paired[augmented], paired.index,
                                          n_boot=2000, seed=seed)
            output.append(dict(analysis_set=analysis_set, probability_mode=mode, comparison=comparison,
                               baseline=baseline, augmented=augmented, **ci,
                               positive_candidate_fraction=float((paired[baseline] > paired[augmented]).mean()),
                               unit="bits/trial of held-out predictive gain",
                               ci_scope="fixed OOF candidate-group cluster bootstrap; no workflow refitting"))
    return frame, output


def run_l0(config, split_run, output_dir):
    """Execute the restricted B L0 first pass; never label this full route B."""
    require_slurm()
    base = ROOT / config["paths"]["private_relative"]
    split_dir = base / "splits" / split_run
    split = json.loads((split_dir / "folds.json").read_text())
    support = pd.read_parquet(split_dir / "support.parquet")
    for record_id in support.loc[support.B, "record_id"]:
        source = base / "data" / split["export_run"] / "P1_CAUSAL20" / record_id / "summary.json"
        if digest(source) != split["input_hashes"]["P1_CAUSAL20/" + record_id]:
            raise ValueError("B_INPUT_CHANGED: reviewed export differs from frozen split inputs")
    destination = Path(output_dir)
    if not destination.is_absolute():
        destination = ROOT / destination
    destination = destination.resolve()
    if not destination.is_relative_to((ROOT / "private").resolve()):
        raise ValueError("B per-trial predictions and models must remain under private")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    public = ROOT / config["paths"]["aggregates_relative"] / destination.name
    public.mkdir(parents=True, exist_ok=False)
    seed = int(split["seed"])
    pending = ["R_SIM", "R_SUP", "early_late_window_diagnostics", "quality_covariate_sensitivity",
               "within-candidate circular-shift diagnostic",
               "previous-response checks do not eliminate all physiological/artifact residuals"]
    contract = dict(stage="B_L0_ONLY", split_run=split_run, split_hash=digest(split_dir / "folds.json"),
                    export_run=split["export_run"], model_names=list(CORE_MODELS),
                    context_columns=list(CONTEXT_COLUMNS), pending=pending,
                    gap_bins="training thirds", position_bins=3, each_stratum_each_H_minimum=5,
                    each_candidate_each_H_minimum=20, each_candidate_each_H_original_blocks=4,
                    primary_minimum_candidate_groups=20,
                    encoder="none; fixed 20ms bins", outcomes_not_clinical=True)
    write_json(destination / "run_contract.json", contract)
    if not support.B.any() or not split["folds"]:
        summary = dict(stage="B_L0_ONLY", status="SUPPORT_INSUFFICIENT", reason="no preliminary B support or outer folds",
                       pending=pending, full_B_complete=False)
        write_json(public / "summary.json", summary)
        write_json(destination / "completion.json", summary)
        return summary
    dataset = load_dataset(split["export_run"], support, branch="all", window="epoch", route="B")
    pre, post = _features(dataset)
    selected = np.flatnonzero(history_eligible(dataset.rows))
    rows = dataset.rows.iloc[selected].reset_index(drop=True)
    trial_lookup = {trial: i for i, trial in enumerate(dataset.trial_ids)}
    previous = np.array([trial_lookup.get(value, -1) for value in rows.previous_event_id], dtype=int)
    current_pre, current_post = pre[selected], post[selected]
    # Previous features exist only for accepted EEG already in this dataset.
    previous_features = np.full((len(previous), post.shape[1]), np.nan)
    has_previous = previous >= 0
    previous_features[has_previous] = post[previous[has_previous]]
    eeg_core = dict(B0_context_linear=None, B0_context_spline=None,
                    B1_pre=current_pre, B2_post=current_post, B3_pre_post=np.c_[current_pre, current_post])
    predictions, flows, fit_evidence = [], [], []
    for fold in split["folds"]:
        scope = FitScope(tuple(fold["train_groups"]), test_groups=tuple(fold["test_groups"]))
        train_index = np.flatnonzero(rows.split_group_id.isin(scope.train_groups))
        test_index = np.flatnonzero(rows.split_group_id.isin(scope.test_groups))
        if not len(train_index):
            flows.append(dict(outer_fold=fold["outer_fold"], analysis_set="all", status="SUPPORT_INSUFFICIENT", reason="no train histories"))
            continue
        train_mask, test_mask, gate = select_common_support(rows.iloc[train_index], rows.iloc[test_index], scope)
        train_index, test_index = train_index[train_mask], test_index[test_mask]
        for analysis_set in ("all", "previous_response_available"):
            train, test = train_index.copy(), test_index.copy()
            model_features = dict(eeg_core)
            if analysis_set != "all":
                train, test = train[previous[train] >= 0], test[previous[test] >= 0]
                # Keep the main gap-bin definition, but recheck both-history
                # overlap on this training subset before any test eligibility.
                a, b, subset_gate = select_common_support(rows.iloc[train], rows.iloc[test], scope,
                                                          frozen_gate=gate)
                train, test = train[a], test[b]
                model_features.update(B4_previous=previous_features,
                                      B5_previous_post=np.c_[previous_features, current_post])
            else:
                subset_gate = gate
            flow = dict(outer_fold=fold["outer_fold"], analysis_set=analysis_set,
                        train_trials=len(train), test_trials=len(test),
                        train_groups=int(rows.iloc[train].split_group_id.nunique()),
                        test_groups=int(rows.iloc[test].split_group_id.nunique()),
                        common_strata=len(subset_gate.strata), outer_support_gate=subset_gate.to_dict())
            if len(train) == 0 or len(test) == 0 or rows.iloc[train].split_group_id.nunique() < 3:
                flow.update(status="SUPPORT_INSUFFICIENT", reason="history_context_common_support_or_candidate_counts")
                flows.append(flow)
                continue
            tr, te = rows.iloc[train].reset_index(drop=True), rows.iloc[test].reset_index(drop=True)
            try:
                fitted = fit_history_readouts(tr, {name: None if values is None else values[train]
                                                   for name, values in model_features.items()}, scope,
                                              seed=seed, inner_folds=3)
            except ValueError as exc:
                if str(exc).startswith("B_INNER_SUPPORT"):
                    flow.update(status="SUPPORT_INSUFFICIENT", reason=str(exc))
                    flows.append(flow)
                    continue
                raise
            for name, model in fitted.items():
                probabilities = model.predict(te, None if model_features[name] is None else model_features[name][test])
                for mode, p in probabilities.items():
                    part = te[["trial_id", "record_id", "candidate_id", "split_group_id", "history_target"]].copy()
                    part["outer_fold"], part["analysis_set"], part["model"], part["probability_mode"] = fold["outer_fold"], analysis_set, name, mode
                    part["p0"], part["p1"] = p[:, 0], p[:, 1]
                    predictions.append(part)
                fit_evidence.append(dict(outer_fold=fold["outer_fold"], analysis_set=analysis_set,
                                         model=name, fit_scope=model.fit_scope, selected_C=model.selected_C,
                                         temperature=model.temperature))
            with (destination / f'fold_{fold["outer_fold"]}_{analysis_set}_readouts.pkl').open("xb") as stream:
                pickle.dump(fitted, stream)
            flow.update(status="COMPLETED_L0_FOLD")
            flows.append(flow)
    frame = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    frame.to_parquet(destination / "oof_history_predictions.parquet", index=False)
    rows.to_parquet(destination / "history_events.parquet", index=False)
    write_json(destination / "fit_scopes.json", fit_evidence)
    write_json(destination / "eligibility_flow.json", flows)
    losses, comparisons = _summaries(frame, seed)
    losses.to_parquet(destination / "candidate_losses.parquet", index=False)
    pd.DataFrame(comparisons).to_csv(public / "conditional_gains.csv", index=False)
    public_flows = [{key: value for key, value in row.items() if key != "outer_support_gate"} for row in flows]
    pd.DataFrame(public_flows).to_csv(public / "eligibility_flow.csv", index=False)
    primary_groups = int(frame.loc[frame.analysis_set.eq("all"), "split_group_id"].nunique()) if len(frame) else 0
    primary_support = primary_groups >= 20
    summary = dict(stage="B_L0_ONLY", status="INTERIM_B_L0_ONLY" if primary_support else "SUPPORT_INSUFFICIENT",
                   full_B_complete=False, scientific_claim="conditional predictive readout, not Shannon CMI or neural memory",
                   completed_model_folds=sum(row["status"] == "COMPLETED_L0_FOLD" for row in flows),
                   candidate_groups=int(frame.split_group_id.nunique()) if len(frame) else 0,
                   primary_candidate_groups=primary_groups, primary_minimum_candidate_groups=20,
                   primary_candidate_support_met=primary_support,
                   all_models_share_test_trials_within_each_analysis_set=True,
                   previous_subset_not_directly_subtracted_from_full_sample=True,
                   pending=pending, representation="L0_HISTORY", comparisons=comparisons,
                   uncertainty="fixed OOF 2000 candidate-group cluster bootstrap, no pipeline refitting")
    write_json(public / "summary.json", summary)
    write_json(destination / "completion.json", dict(status=summary["status"],
               output_hashes={path.name: digest(path) for path in destination.iterdir() if path.is_file()}))
    return summary
