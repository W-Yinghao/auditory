"""Outcome-blind H_v2 features from the complete pre-QC event chain.

The functions in this module use event metadata only.  ``trial_id`` and the
source identifiers are carried for alignment, but are never feature columns.
In particular, the old B-v1 ``history_target`` exclusion is not consulted, so
a valid preceding run of length two remains represented as ``run_2``.
"""
from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd


REQUIRED = {"trial_id", "record_id", "segment_id", "onset_sample", "event_literal"}
RUN_BINS = ("run_1", "run_2", "run_3_5", "run_6_plus", "unknown")
FORBIDDEN = {
    "current_run_length", "current_is_previous", "current_equals_previous",
    "next_label", "next_code", "clinical", "muss", "age_months",
}


def _run_bin(value):
    if value is None or not np.isfinite(float(value)):
        return "unknown"
    value = int(value)
    if value == 1:
        return "run_1"
    if value == 2:
        return "run_2"
    if 3 <= value <= 5:
        return "run_3_5"
    if value >= 6:
        return "run_6_plus"
    return "unknown"


def _safe_sample(value):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("H_EVENT_SAMPLE")
    sample = int(value)
    if sample != value or sample < 0:
        raise ValueError("H_EVENT_SAMPLE")
    return sample


def _layout_columns(frame: pd.DataFrame, columns: Iterable[str]) -> tuple[str, ...]:
    columns = tuple(columns)
    for column in columns:
        if column not in frame:
            raise ValueError(f"H_LAYOUT_COLUMN:{column}")
        lowered = column.lower()
        if any(token in lowered for token in ("id", "label", "clinical", "muss", "age")):
            raise ValueError("H_LAYOUT_FORBIDDEN_INPUT")
    return columns


def build_h_v2(events: pd.DataFrame, *, original_fs: float | None = None,
               known_codes: Iterable[str] | None = None,
               layout_columns: Iterable[str] = ()) -> pd.DataFrame:
    """Build current-trial H features from a complete, ordered event ledger.

    Rows are grouped by ``record_id,segment_id`` and ordered by original
    samples.  A storage gap, explicit restart, unknown sound, or segment
    change clears the preceding sound chain.  A large ordinary gap does not.
    The output retains one row per input trial and exposes raw history metadata
    for auditing.  The safe selector exposes only past codes, run transforms,
    logged past gaps, current-gap missing/quadratic terms, position, and
    explicitly supplied layout categories.
    """
    if not isinstance(events, pd.DataFrame) or not REQUIRED.issubset(events.columns):
        raise ValueError("H_EVENT_SCHEMA")
    if events[list(REQUIRED)].isna().any().any():
        raise ValueError("H_EVENT_NULL")
    if events.trial_id.duplicated().any():
        raise ValueError("H_DUPLICATE_TRIAL")
    if original_fs is not None and (not math.isfinite(float(original_fs)) or float(original_fs) <= 0):
        raise ValueError("H_FS")
    if original_fs is None and "original_fs" not in events:
        raise ValueError("H_FS_REQUIRED")
    layout = _layout_columns(events, layout_columns)
    for column in events.columns:
        lowered = column.lower()
        if lowered in FORBIDDEN or any(token in lowered for token in ("clinical", "muss", "age_month")):
            raise ValueError("H_CURRENT_OR_CLINICAL_INPUT")
    if "event_kind" in events and not events.event_kind.isin(
            ["target", "unknown_sound", "non_sound", "restart"]).all():
        raise ValueError("H_EVENT_KIND")
    for flag in ("storage_gap_before", "task_restart_before", "sequence_start_complete"):
        if flag in events and not events[flag].map(lambda value: isinstance(value, (bool, np.bool_))).all():
            raise ValueError(f"H_FLAG:{flag}")
    frame = events.copy()
    frame["_order"] = np.arange(len(frame))
    frame["_sample"] = frame.onset_sample.map(_safe_sample)
    sort_columns = ["record_id", "segment_id", "_sample", "_order"]
    frame = frame.sort_values(sort_columns, kind="stable").reset_index(drop=True)
    codes = tuple(str(x) for x in (known_codes if known_codes is not None else
                                    sorted(frame.event_literal.dropna().astype(str).unique())))
    if len(set(codes)) != len(codes):
        raise ValueError("H_CODE_SCHEMA")
    output = []
    for _, part in frame.groupby(["record_id", "segment_id"], sort=False):
        previous = []
        previous_sample = None
        chain_complete = False
        pending_reset = "segment_start"
        for _, source in part.iterrows():
            safe_source = sorted(REQUIRED) + list(layout) + [
                "event_kind", "storage_gap_before", "task_restart_before",
                "sequence_start_complete", "segment_position_fraction", "original_fs"]
            row = {key: source[key] for key in safe_source if key in source}
            row["_input_order"] = int(source["_order"])
            kind = row.get("event_kind", "target")
            row["event_kind"] = kind
            sample = int(source["_sample"])
            reset_reason = pending_reset
            pending_reset = None
            if row.get("storage_gap_before", False):
                previous, previous_sample, chain_complete = [], None, False
                reset_reason = "storage_gap"
            if row.get("task_restart_before", False):
                previous, previous_sample, chain_complete = [], None, True
                reset_reason = "task_restart"
            if kind == "restart":
                previous, previous_sample, chain_complete = [], None, True
                reset_reason = "task_restart"
            past_codes = [item["code"] for item in previous[-3:]][::-1]
            past_gaps = [item["gap_s"] for item in previous[-3:]][::-1]
            prior = previous[-1] if previous else None
            prior_run = prior["run"] if prior else None
            current_gap = (None if prior is None else
                           (sample - prior["sample"]) / float(original_fs or row.get("original_fs", 1.0)))
            row.update({
                "previous_event_id": prior["trial_id"] if prior else None,
                "previous_code": prior["code"] if prior else None,
                "previous_gap_s": current_gap,
                "previous_run_length": prior_run,
                "previous_run_log1p": (np.log1p(float(prior_run))
                                        if prior_run is not None and np.isfinite(float(prior_run))
                                        and float(prior_run) >= 0 else np.nan),
                "previous_run_missing": int(prior_run is None or
                                             not np.isfinite(float(prior_run))),
                "previous_run_bin": _run_bin(prior_run),
                "history_status": "complete" if prior_run is not None else "unknown",
                "history_reset_reason": reset_reason,
                "current_gap_s": current_gap,
                "current_gap_s_squared": (current_gap * current_gap
                                           if current_gap is not None and np.isfinite(current_gap)
                                           else np.nan),
                "current_gap_s_missing": int(current_gap is None or
                                              not np.isfinite(current_gap)),
            })
            for run_bin in RUN_BINS:
                row[f"previous_run_{run_bin}"] = int(_run_bin(prior_run) == run_bin)
            for lag in (1, 2, 3):
                code = past_codes[lag - 1] if len(past_codes) >= lag else None
                for value in codes:
                    row[f"previous_code_{lag}_{value}"] = int(code == value)
                row[f"previous_code_{lag}_unknown"] = int(code is None or code not in codes)
                row[f"previous_gap_{lag}_s"] = past_gaps[lag - 1] if len(past_gaps) >= lag else np.nan
                gap = past_gaps[lag - 1] if len(past_gaps) >= lag else None
                row[f"previous_gap_{lag}_missing"] = int(
                    gap is None or not np.isfinite(float(gap)))
                row[f"previous_gap_{lag}_log"] = (np.log(float(gap))
                                                   if gap is not None and np.isfinite(float(gap))
                                                   and float(gap) > 0 else np.nan)
            if "segment_position_fraction" in row:
                position = float(row["segment_position_fraction"])
                if not np.isfinite(position) or not 0 <= position <= 1:
                    raise ValueError("H_POSITION")
                row["position_fraction"] = position
                row["position_fraction_squared"] = position * position
            for column in layout:
                row[f"layout_{column}"] = row[column]
            if kind == "unknown_sound":
                previous, previous_sample, chain_complete = [], None, False
                pending_reset = "unknown_sound"
            elif kind == "target":
                literal = str(row["event_literal"])
                if prior is None:
                    run = 1 if row.get("sequence_start_complete", False) or chain_complete else None
                elif literal == prior["code"]:
                    if sample <= prior["sample"]:
                        raise ValueError("H_NONINCREASING_SOUND")
                    run = prior_run + 1 if prior_run is not None else None
                else:
                    if sample <= prior["sample"]:
                        raise ValueError("H_NONINCREASING_SOUND")
                    run = 1
                if prior is None and not chain_complete and not row.get("sequence_start_complete", False):
                    row["history_reset_reason"] = reset_reason or "unknown_chain_start"
                previous.append({"trial_id": row["trial_id"], "code": literal,
                                 "sample": sample, "run": run,
                                 "gap_s": None if previous_sample is None else
                                 (sample - previous_sample) / float(original_fs or row.get("original_fs", 1.0))})
                previous_sample = sample
                chain_complete = False
                if reset_reason is not None and row["history_status"] == "complete":
                    row["history_reset_reason"] = None
            elif kind == "restart":
                pending_reset = "task_restart"
            output.append(row)
    result = pd.DataFrame(output)
    if len(result) != len(events) or set(result.trial_id) != set(events.trial_id):
        raise ValueError("H_OUTPUT_ALIGNMENT")
    return result.sort_values("_input_order", kind="stable").drop(columns=["_input_order", "_order"], errors="ignore").reset_index(drop=True)


# Descriptive alias for callers that use the plan's noun phrase.
build_history_features = build_h_v2


def history_feature_columns(frame: pd.DataFrame) -> list[str]:
    """Return the explicitly safe predictor columns; metadata stays separate."""
    columns = []
    for column in frame.columns:
        if column.startswith("previous_code_"):
            columns.append(column)
        elif column.startswith("previous_run_run_"):
            columns.append(column)
        elif column in {"previous_run_log1p", "previous_run_missing",
                        "current_gap_s_squared", "current_gap_s_missing",
                        "position_fraction", "position_fraction_squared"}:
            columns.append(column)
        elif (column.startswith("previous_gap_") and
              (column.endswith("_log") or column.endswith("_missing"))):
            columns.append(column)
        elif column.startswith("layout_"):
            columns.append(column)
    forbidden = {"current_run_length", "current_is_previous", "next_code",
                 "clinical", "muss", "age_months"}
    if any(column.lower() in forbidden for column in columns):
        raise ValueError("H_FEATURE_SELECTOR")
    return columns
