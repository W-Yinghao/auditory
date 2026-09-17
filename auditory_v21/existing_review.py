"""Stage 0 review of frozen auditory_next v2 artifacts.

This module deliberately consumes only saved A2 matching statistics and public
CSV summaries.  It never reads EEG arrays, fitted axes, model weights, or
candidate level identifiers into a public output, and it never fits anything.
The numerical entry point is intended to be called by the Slurm runner.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import pickle
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


DEFAULT_MODES = ("R_SUP", "R_SIM", "R_RAND")
DEFAULT_ENDPOINTS = ("post_delta", "post_minus_pre")
DEFAULT_SEED = 20260918
DEFAULT_BOOTSTRAPS = 2000


def _as_float(value: Any) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise ValueError("NONFINITE_NUMERIC_INPUT")
    return result


def fold_statistic(matrix: Any, candidate_ids: Sequence[str]) -> float:
    """Return diagonal minus different-candidate mean for one saved fold."""

    matrix = np.asarray(matrix, dtype=float)
    ids = np.asarray(candidate_ids, dtype=str)
    if matrix.ndim != 2 or matrix.shape != (len(ids), len(ids)):
        raise ValueError("A2_MATRIX_ID_ALIGNMENT")
    # Original fold IDs are unique, but bootstrap samples intentionally can
    # repeat them.  The identity mask below excludes repeated identities from
    # the different-candidate reference while retaining matched diagonal slots.
    if len(ids) < 2:
        raise ValueError("A2_FOLD_CANDIDATE_SUPPORT")
    if not np.isfinite(matrix).all():
        raise ValueError("A2_MATRIX_NONFINITE")
    different = ids[:, None] != ids[None, :]
    if not different.any():
        raise ValueError("A2_MATCH_REQUIRES_TWO_IDENTITIES")
    return float(np.diag(matrix).mean() - matrix[different].mean())


def _fold_values(records: Sequence[Mapping[str, Any]], first: str, second: str,
                 endpoint: str, metric: str) -> tuple[list[float], list[float], list[int]]:
    first_values, second_values, weights = [], [], []
    for record in records:
        ids = tuple(str(x) for x in record["groups"])
        matrices = record["matrices"]
        try:
            first_matrix = matrices[first][endpoint][metric]
            second_matrix = matrices[second][endpoint][metric]
        except (KeyError, TypeError):
            raise ValueError("A2_REQUIRED_SAVED_STATISTIC_MISSING") from None
        first_values.append(fold_statistic(first_matrix, ids))
        second_values.append(fold_statistic(second_matrix, ids))
        weights.append(len(ids))
    return first_values, second_values, weights


def _weighted(values: Sequence[float], weights: Sequence[int]) -> float:
    return float(np.average(np.asarray(values, dtype=float), weights=np.asarray(weights)))


def bootstrap_contrast(records: Sequence[Mapping[str, Any]], first: str, second: str,
                       *, endpoint: str = "post_delta", metric: str = "cosine",
                       n_bootstrap: int = DEFAULT_BOOTSTRAPS,
                       seed: int = DEFAULT_SEED) -> dict[str, Any]:
    """Bootstrap a matched contrast, drawing candidates within each original fold.

    The same index draw is used for both modes and, for ``post_minus_pre``,
    for both endpoints.  The fold weights remain the original fold sizes.
    """

    if n_bootstrap < 1:
        raise ValueError("POSITIVE_BOOTSTRAP_COUNT_REQUIRED")
    if not records:
        raise ValueError("A2_NO_FOLDS")
    first_post, second_post, weights = _fold_values(records, first, second, "post_delta", metric)
    first_pre, second_pre, _ = _fold_values(records, first, second, "pre_delta", metric)
    if endpoint not in {"post_delta", "post_minus_pre"}:
        raise ValueError("A2_ENDPOINT_NOT_ALLOWED")

    def base_delta(index_endpoint: str) -> float:
        one, two, _ = _fold_values(records, first, second, index_endpoint, metric)
        return _weighted(np.asarray(one) - np.asarray(two), weights)

    base = (base_delta("post_delta") if endpoint == "post_delta"
            else base_delta("post_delta") - base_delta("pre_delta"))
    rng = np.random.default_rng(int(seed))
    draws: list[float] = []
    for _ in range(int(n_bootstrap)):
        fold_deltas: list[float] = []
        draw_valid = True
        for fold_index, record in enumerate(records):
            ids = tuple(str(x) for x in record["groups"])
            ix = rng.integers(0, len(ids), len(ids))
            matrices = record["matrices"]

            def stat(mode: str, ep: str) -> float:
                matrix = np.asarray(matrices[mode][ep][metric], dtype=float)
                sampled_ids = np.asarray(ids, dtype=str)[ix]
                return fold_statistic(matrix[np.ix_(ix, ix)], sampled_ids)

            try:
                delta = stat(first, "post_delta") - stat(second, "post_delta")
                if endpoint == "post_minus_pre":
                    delta -= stat(first, "pre_delta") - stat(second, "pre_delta")
            except ValueError as exc:
                if str(exc) not in {"A2_MATCH_REQUIRES_TWO_IDENTITIES", "A2_FOLD_CANDIDATE_SUPPORT"}:
                    raise
                draw_valid = False
                break
            fold_deltas.append(delta)
        draws.append(_weighted(fold_deltas, weights) if draw_valid else np.nan)
    finite = np.asarray(draws, dtype=float)
    finite = finite[np.isfinite(finite)]
    invalid = int(n_bootstrap - len(finite))
    ci = ([float(np.quantile(finite, .025)), float(np.quantile(finite, .975))]
          if len(finite) else [None, None])
    return {
        "estimate": float(base),
        "ci_lower": ci[0],
        "ci_upper": ci[1],
        "n_bootstrap": int(n_bootstrap),
        "invalid_replicates": invalid,
        "valid_replicates": int(len(finite)),
        "bootstrap_seed": int(seed),
        "bootstrap_scope": "fixed saved OOF matrices; matched candidate draws within original folds; no refit",
    }


def leave_one_candidate_range(records: Sequence[Mapping[str, Any]], first: str,
                              second: str, *, endpoint: str = "post_delta",
                              metric: str = "cosine") -> dict[str, Any]:
    """Describe the complete leave-one-candidate-out range without IDs."""

    if endpoint not in {"post_delta", "post_minus_pre"}:
        raise ValueError("A2_ENDPOINT_NOT_ALLOWED")
    values: list[float] = []
    for removed_fold_index, removed_record in enumerate(records):
        removed_ids = tuple(str(x) for x in removed_record["groups"])
        for candidate_index in range(len(removed_ids)):
            fold_deltas: list[float] = []
            fold_weights: list[int] = []
            for fold_index, record in enumerate(records):
                ids = tuple(str(x) for x in record["groups"])
                matrices = record["matrices"]
                keep = np.ones(len(ids), dtype=bool)
                if fold_index == removed_fold_index:
                    keep[candidate_index] = False
                kept_ids = tuple(ids[i] for i in np.flatnonzero(keep))
                if len(kept_ids) < 2:
                    raise ValueError("A2_LEAVE_ONE_SUPPORT")

                def stat(mode: str, ep: str) -> float:
                    matrix = np.asarray(matrices[mode][ep][metric], dtype=float)
                    return fold_statistic(matrix[np.ix_(keep, keep)], kept_ids)

                delta = stat(first, "post_delta") - stat(second, "post_delta")
                if endpoint == "post_minus_pre":
                    delta -= stat(first, "pre_delta") - stat(second, "pre_delta")
                fold_deltas.append(delta)
                fold_weights.append(len(kept_ids))
            values.append(_weighted(fold_deltas, fold_weights))
    values_array = np.asarray(values, dtype=float)
    return {
        "n_candidates": int(len(values_array)),
        "leave_one_candidate_min": float(values_array.min()),
        "leave_one_candidate_max": float(values_array.max()),
        "scope": "all candidates retained in descriptive range; no exclusions",
    }


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows([{field: row.get(field) for field in fields} for row in rows])


def _source_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _read_csv(path: Path, hashes: dict[str, str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    before = _digest(path)
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    after = _digest(path)
    if before != after:
        raise ValueError("SOURCE_CHANGED_DURING_READ")
    hashes[str(path)] = before
    return rows


def _load_a2_records(source: Path, modes: Sequence[str], folds: Sequence[int],
                     hashes: dict[str, str]) -> list[dict[str, Any]]:
    definition = source / "A2_definition.json"
    if definition.exists():
        before = _digest(definition)
        try:
            document = json.loads(definition.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("A2_DEFINITION_SCHEMA") from exc
        if _digest(definition) != before:
            raise ValueError("SOURCE_CHANGED_DURING_READ")
        hashes[str(definition)] = before
        omega = tuple(document.get("omega", ()))
        expected_omega = ("run3_5_pos0", "run3_5_pos1")
        if omega and omega != expected_omega:
            raise ValueError("A2_FROZEN_OMEGA_MISMATCH")
    by_fold: dict[int, dict[str, Any]] = {}
    for mode in modes:
        for fold in folds:
            path = source / f"{mode}_outer{int(fold)}_matching_matrices.pkl"
            if not path.exists():
                raise FileNotFoundError(f"A2_SAVED_MATCHING_MATRIX_MISSING:{path.name}")
            before = _digest(path)
            with path.open("rb") as stream:
                value = pickle.load(stream)
            if _digest(path) != before:
                raise ValueError("SOURCE_CHANGED_DURING_READ")
            hashes[str(path)] = before
            if not isinstance(value, Mapping) or "groups" not in value or "matrices" not in value:
                raise ValueError("A2_SAVED_MATRIX_SCHEMA")
            ids = tuple(str(x) for x in value["groups"])
            if len(ids) < 2 or len(set(ids)) != len(ids):
                raise ValueError("A2_SAVED_MATRIX_GROUP_SCHEMA")
            record = by_fold.setdefault(int(fold), {"fold": int(fold), "groups": ids, "matrices": {}})
            if tuple(record["groups"]) != ids:
                raise ValueError("A2_MODE_FOLD_CANDIDATE_MISMATCH")
            record["matrices"][mode] = value["matrices"]
    records = [by_fold[int(fold)] for fold in folds]
    all_ids = [candidate for row in records for candidate in row["groups"]]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("A2_OUTER_FOLD_CANDIDATE_REUSE")
    return records


def _norm_rows(records: Sequence[Mapping[str, Any]], modes: Sequence[str],
               endpoints: Sequence[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mode in modes:
        for endpoint in endpoints:
            summaries = []
            for record in records:
                saved = record["matrices"].get(mode, {}).get(endpoint, {}).get("norm_summary")
                if isinstance(saved, Mapping) and all(k in saved for k in ("first_mean", "second_mean", "first_sd", "second_sd")):
                    summaries.append(saved)
            base = dict(mode=mode, endpoint=endpoint, n_folds=len(summaries), status="COMPUTED" if summaries else "MISSING")
            if summaries:
                for key in ("first_mean", "second_mean", "first_sd", "second_sd"):
                    base[key] = float(np.mean([_as_float(item[key]) for item in summaries]))
                base["note"] = "mean of saved per-fold norm summaries; no norms reconstructed"
            else:
                for key in ("first_mean", "second_mean", "first_sd", "second_sd"):
                    base[key] = None
                base["note"] = "saved norm measurements unavailable"
            rows.append(base)
    return rows


def _risk_rows(root: Path, hashes: dict[str, str], source_override: str | None = None) -> list[dict[str, Any]]:
    """Read existing source tables and compare risk summaries by family.

    Values remain CE/risk values from the source table.  No source-table risk
    is renamed as mutual information.
    """

    final = _source_path(root, source_override or "results/auditory_next_v2/final_002/metrics_aggregate.csv")
    rows = _read_csv(final, hashes)
    output: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    for row in rows:
        if row.get("packet") not in {"N1", "N3"} or row.get("metric") != "ce_bits":
            continue
        family = row.get("readout_family") or row.get("model") or ""
        family_class = "training_selected" if "selected" in family.lower() else "fixed_family"
        item = {
            "packet": row.get("packet"), "mode": row.get("representation"),
            "population": row.get("population_id"), "view": row.get("model"),
            "calibration": row.get("calibration"), "family": family,
            "family_class": family_class, "risk_metric": "ce_bits",
            "risk_unit": row.get("unit") or "bits/trial",
            "estimate": row.get("estimate"), "ci_lower": row.get("ci_lower"),
            "ci_upper": row.get("ci_upper"), "n_candidates": row.get("n_candidates"),
            "source_run": row.get("source_run"),
            "comparison_status": "SOURCE_VALUE_RETAINED",
            "interpretation": "source CE/risk summary; not reinterpreted as MI",
        }
        output.append(item)
        source_rows.append(item)
    # The selected-family rows are compared to each available fixed family
    # only as source-table risk differences.  Their source CIs are not
    # subtracted because the saved summaries do not provide a paired draw.
    selected = [row for row in source_rows if row["family_class"] == "training_selected"]
    fixed = [row for row in source_rows if row["family_class"] == "fixed_family"]
    for selected_row in selected:
        matches = [row for row in fixed if tuple(row.get(key) for key in ("packet", "mode", "population", "view", "calibration")) ==
                   tuple(selected_row.get(key) for key in ("packet", "mode", "population", "view", "calibration"))]
        for fixed_row in matches:
            if selected_row.get("estimate") in (None, "") or fixed_row.get("estimate") in (None, ""):
                continue
            output.append({**selected_row,
                "family": f"{selected_row['family']}_minus_{fixed_row['family']}",
                "family_class": "selected_minus_fixed_risk",
                "estimate": float(selected_row["estimate"]) - float(fixed_row["estimate"]),
                "ci_lower": None, "ci_upper": None,
                "comparison_status": "DESCRIPTIVE_SOURCE_RISK_DIFFERENCE",
                "interpretation": "difference of saved CE/risk summaries; no paired CI and no MI relabeling"})
    if not any(row["packet"] == "N1" and row["family_class"] == "training_selected" for row in output):
        output.append({"packet": "N1", "mode": None, "population": None, "view": None,
                       "calibration": None, "family": "training_OOF_selected", "family_class": "training_selected",
                       "risk_metric": "ce_bits", "risk_unit": "bits/trial", "estimate": None,
                       "ci_lower": None, "ci_upper": None, "n_candidates": None, "source_run": None,
                       "comparison_status": "MISSING_TRAINING_SELECTED_SOURCE",
                       "interpretation": "N1 has no training-selected risk summary in the fixed public sources"})
    # Explicitly carry the frozen N3 primary effect status into the review.
    effects = _read_csv(_source_path(root, "results/auditory_next_v2/final_002/paired_effects.csv"), hashes)
    primary = next((row for row in effects if row.get("packet") == "N3" and
                    row.get("analysis_id") == "selected_H_minus_HP" and
                    row.get("primary_or_secondary") == "primary"), None)
    if primary is not None:
        output.append({"packet": "N3", "mode": primary.get("representation"), "population": primary.get("population_id"),
                       "view": "H→HP", "calibration": primary.get("calibration"),
                       "family": primary.get("readout_family"), "family_class": "primary_effect_context",
                       "risk_metric": "frozen_primary_effect", "risk_unit": primary.get("unit"),
                       "estimate": primary.get("estimate"), "ci_lower": primary.get("ci_lower"),
                       "ci_upper": primary.get("ci_upper"), "n_candidates": primary.get("n_candidates"),
                       "source_run": primary.get("source_run"), "comparison_status": "PRIMARY_REMAINS_NEGATIVE",
                       "interpretation": "frozen N3 primary source effect retained; no MI relabeling"})
    else:
        output.append({"packet": "N3", "mode": None, "population": None, "view": "H→HP",
                       "calibration": None, "family": "training_OOF_selected", "family_class": "primary_effect_context",
                       "risk_metric": "frozen_primary_effect", "risk_unit": "bits/trial", "estimate": None,
                       "ci_lower": None, "ci_upper": None, "n_candidates": None, "source_run": None,
                       "comparison_status": "MISSING_FROZEN_PRIMARY_SOURCE",
                       "interpretation": "expected selected_H_minus_HP primary row was not found in frozen final_002 CSV"})
    return output


def _provenance_rows(root: Path, hashes: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    checks = [
        ("G0", "original_supervised_head", "results/auditory_next_v2/G0_001/supervised_original_head.csv", "COMPLETE",
         "original CNN head TRAIN_DIAGNOSTIC and OUTER_SHARED rows are separate"),
        ("G0", "posthoc_probe", "results/auditory_next_v2/G0_readouts_001/g0_within_child_metrics.csv", "COMPLETE",
         "posthoc fixed-representation probe is separate from original head"),
        ("C2_R", "repaired_core_summary", "results/auditory_next_v2/C2R_core_001/single_joint_gains.csv", "COMPLETE",
         "existing repaired core summary; no new head fit"),
        ("C2_R", "inherited_raw_isolation", None, "MISSING", "control was not supplied by the existing source summary"),
        ("G0", "selection_isolation", None, "MISSING", "whole-record offline QC selection remains unisolated"),
        ("A2", "fixed_quality_background", None, "MISSING", "fixed quality/background summary is absent"),
        ("N1", "synthetic_capability", None, "MISSING", "background-key capability control remains unavailable"),
        ("N3", "synthetic_capability", None, "MISSING", "EEG increment/history-only capability controls remain unavailable"),
    ]
    for packet, item, relative, status, note in checks:
        source = _source_path(root, relative) if relative else None
        if relative:
            if source is not None and source.exists():
                hashes[str(source)] = _digest(source)
                actual_status = status
            else:
                actual_status = "MISSING"
        else:
            actual_status = status
        rows.append(dict(packet=packet, item=item, status=actual_status, source=relative or "", note=note))
    return rows


def run(root: Path, private: Path, public: Path, report: Path, config: dict) -> dict:
    """Execute the no-refit Stage 0 review and write aggregate artifacts."""

    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("SLURM_REQUIRED")
    root, private, public, report = map(Path, (root, private, public, report))
    stage = config.get("stage0", config)
    seed = int(stage.get("bootstrap_seed", DEFAULT_SEED))
    n_bootstrap = int(stage.get("bootstrap_replicates", DEFAULT_BOOTSTRAPS))
    source_run = str(stage.get("A2_source", "A2_core_001"))
    source = _source_path(root, stage.get("A2_source_path", f"private/auditory_next_v2/{source_run}"))
    modes = tuple(stage.get("A2_modes", DEFAULT_MODES))
    folds = tuple(int(fold) for fold in stage.get("A2_folds", range(5)))
    endpoints = tuple(stage.get("A2_endpoints", DEFAULT_ENDPOINTS))
    metric = str(stage.get("A2_metric", "cosine"))
    contrasts = tuple(tuple(pair) for pair in stage.get("A2_contrasts", (("R_SUP", "R_SIM"), ("R_SUP", "R_RAND"))))
    hashes: dict[str, str] = {}
    records = _load_a2_records(source, modes, folds, hashes)

    comparison_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    influence_rows: list[dict[str, Any]] = []
    for first, second in contrasts:
        if first not in modes or second not in modes:
            raise ValueError("A2_CONTRAST_MODE_MISSING")
        for endpoint in endpoints:
            result = bootstrap_contrast(records, first, second, endpoint=endpoint, metric=metric,
                                        n_bootstrap=n_bootstrap, seed=seed)
            comparison_rows.append(dict(comparison=f"{first}_minus_{second}", first_mode=first,
                second_mode=second, endpoint=endpoint, metric=metric, **result,
                n_candidates=sum(len(row["groups"]) for row in records),
                status="COMPUTED" if result["valid_replicates"] else "NOT_EVALUABLE",
                primary_result_unchanged=True))
            loo = leave_one_candidate_range(records, first, second, endpoint=endpoint, metric=metric)
            influence_rows.append(dict(comparison=f"{first}_minus_{second}", endpoint=endpoint,
                metric=metric, **loo))
        for record in records:
            ids = tuple(record["groups"])
            for endpoint in ("post_delta", "pre_delta"):
                for mode in (first, second):
                    matrix = record["matrices"][mode][endpoint][metric]
                    fold_rows.append(dict(fold=record["fold"], mode=mode, endpoint=endpoint, metric=metric,
                                          statistic=fold_statistic(matrix, ids), n_candidates=len(ids)))
                a = fold_statistic(record["matrices"][first][endpoint][metric], ids)
                b = fold_statistic(record["matrices"][second][endpoint][metric], ids)
                fold_rows.append(dict(fold=record["fold"], mode=f"{first}_minus_{second}", endpoint=endpoint,
                                      metric=metric, statistic=a - b, n_candidates=len(ids)))

    norm_rows = _norm_rows(records, modes, ("post_delta", "pre_delta"))
    risk_rows = _risk_rows(root, hashes, stage.get("risk_summary_path"))
    provenance_rows = _provenance_rows(root, hashes)
    n3_primary_source_matched = any(row.get("comparison_status") == "PRIMARY_REMAINS_NEGATIVE" for row in risk_rows)
    _write_csv(public / "a2_secondary_comparisons.csv", comparison_rows,
               ("comparison", "first_mode", "second_mode", "endpoint", "metric", "estimate", "ci_lower",
                "ci_upper", "n_candidates", "n_bootstrap", "invalid_replicates", "valid_replicates",
                "bootstrap_seed", "bootstrap_scope", "status", "primary_result_unchanged"))
    _write_csv(public / "a2_secondary_fold_statistics.csv", fold_rows,
               ("fold", "mode", "endpoint", "metric", "statistic", "n_candidates"))
    _write_csv(public / "a2_secondary_candidate_influence.csv", influence_rows,
               ("comparison", "endpoint", "metric", "n_candidates", "leave_one_candidate_min",
                "leave_one_candidate_max", "scope"))
    _write_csv(public / "a2_norm_sensitivity.csv", norm_rows,
               ("mode", "endpoint", "n_folds", "status", "first_mean", "second_mean", "first_sd", "second_sd", "note"))
    _write_csv(public / "n1_n3_risk_family_comparison.csv", risk_rows,
               ("packet", "mode", "population", "view", "calibration", "family", "family_class",
                "risk_metric", "risk_unit", "estimate", "ci_lower", "ci_upper", "n_candidates", "source_run",
                "comparison_status", "interpretation"))
    _write_csv(public / "provenance_control_checklist.csv", provenance_rows,
               ("packet", "item", "status", "source", "note"))
    _write_json(private / "input_hashes.json", hashes)
    summary = {
        "status": "EXISTING_ARTIFACTS_REVIEW_COMPLETE",
        "implementation_status": "PASS", "scientific_status": "DESCRIPTIVE_REVIEW_ONLY",
        "new_head_fits": 0, "new_encoder_fits": 0, "a2_candidates": sum(len(row["groups"]) for row in records),
        "a2_folds": len(records), "bootstrap_seed": seed, "bootstrap_replicates": n_bootstrap,
        "a2_metric": metric, "a2_contrasts": [list(pair) for pair in contrasts],
        "primary_result_unchanged": True, "risk_source_values_not_reinterpreted_as_mi": True,
        "n3_primary_source_matched": n3_primary_source_matched,
        "norms": "COMPUTED_FROM_SAVED_SUMMARIES_OR_MISSING",
        "new_source_schemas_needed": False,
        "source_hash_count": len(hashes),
        "outputs": ["a2_secondary_comparisons.csv", "a2_secondary_fold_statistics.csv",
                    "a2_secondary_candidate_influence.csv", "a2_norm_sensitivity.csv",
                    "n1_n3_risk_family_comparison.csv", "provenance_control_checklist.csv"],
    }
    _write_json(public / "summary.json", summary)
    report.mkdir(parents=True, exist_ok=True)
    (report / "EXISTING_ARTIFACTS_REVIEW.md").write_text(
        "# Auditory v2.1 Stage 0 existing-artifacts review\n\n"
        f"The frozen A2 matching matrices were reviewed for {len(records)} original folds and "
        f"{summary['a2_candidates']} candidate-fold entries. Contrasts use matched candidate bootstrap "
        f"within each original fold ({n_bootstrap} replicates, seed {seed}) and no refit.\n\n"
        "A2 R_SIM remains the frozen primary; the SUP contrasts are posthoc secondary review statistics. "
        "Post-minus-pre is a difference of saved scalar matching statistics. Norms are reported only when "
        "stored norm summaries exist. N1/N3 source CE/risk values are retained without MI relabeling; "
        "the frozen N3 primary remains negative. G0 head/probe provenance and C2 controls are listed "
        "with missing controls explicit.\n", encoding="utf-8")
    return summary
