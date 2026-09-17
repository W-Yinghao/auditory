"""Outcome-blind stimulus history on the complete, pre-QC event chain.

Roles must come from source evidence, never from event frequency. All source
rows, including rejected EEG trials and non-sound logs, remain in the output.
No function here reads EEG, clinical values, or an ``accepted`` field.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any


EVENT_KINDS = frozenset({"target", "non_sound", "unknown_sound", "restart"})


def _sample(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("onset_sample must be an integer sample index")
    converted = int(value)
    if converted != value or converted < 0:
        raise ValueError("onset_sample must be a nonnegative integer sample index")
    return converted


def build_event_history(
    events: Iterable[Mapping[str, Any]],
    original_fs: float,
    *,
    target_codes: Iterable[Any] | None = None,
) -> list[dict[str, Any]]:
    """Annotate an ordered complete chain without selecting accepted trials.

    Required keys: ``record_id``, ``segment_id``, ``trial_id``, ``onset_sample``,
    and ``event_literal``. ``event_kind`` is target, non_sound, unknown_sound,
    or restart. With explicit ``target_codes``, a mapped code may omit its role;
    other rows still need a role. A new segment, ``storage_gap_before=True``,
    ``task_restart_before=True``, or an unknown sound breaks the chain. An
    ordinary non-sound log does not. Large interstimulus intervals alone are
    not evidence of a storage gap.

    ``previous_run_length`` counts the equal-code run ending at the previous
    *sound*, before current EEG QC. H is 0 for length 1, 1 for length >=3, and
    None otherwise. At a recording/gap boundary, the first same-code run has
    unknown true length until a code change. A confirmed complete sequence
    start can explicitly set ``sequence_start_complete=True`` on its first
    sound. An explicit task restart also establishes a complete new start.

    Output includes every source row and adds current_run_length,
    previous_event_id/code/gap_s/run_length, history_target/status/reset_reason.
    Timing uses original samples divided by original Hz, never processed Hz.
    """
    fs = float(original_fs)
    if not math.isfinite(fs) or fs <= 0:
        raise ValueError("original_fs must be finite positive Hz")
    codes = None if target_codes is None else frozenset(target_codes)
    result: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()
    completed_segments: set[tuple[Any, Any]] = set()
    segment = None
    previous = None
    previous_sample_in_segment = -1
    complete_start = False
    pending_reset = "segment_start"

    for source in events:
        row = dict(source)
        for key in ("record_id", "segment_id", "trial_id", "onset_sample", "event_literal"):
            if key not in row or row[key] is None:
                raise ValueError(f"missing required event field: {key}")
        if row["trial_id"] in seen_ids:
            raise ValueError("trial_id must be unique across the complete chain")
        seen_ids.add(row["trial_id"])
        onset = _sample(row["onset_sample"])
        current_segment = (row["record_id"], row["segment_id"])
        if current_segment != segment:
            if current_segment in completed_segments:
                raise ValueError("event segments must be contiguous in input order")
            if segment is not None:
                completed_segments.add(segment)
            segment = current_segment
            previous = None
            previous_sample_in_segment = -1
            complete_start = False
            pending_reset = "segment_start"
        if onset < previous_sample_in_segment:
            raise ValueError("event samples must be ordered inside each segment")
        previous_sample_in_segment = onset
        kind = row.get("event_kind")
        if kind is None and codes is not None and row["event_literal"] in codes:
            kind = "target"
        if kind not in EVENT_KINDS:
            raise ValueError("every unmapped event requires an explicit event_kind")
        if codes is not None and kind == "target" and row["event_literal"] not in codes:
            raise ValueError("target event is absent from the frozen code mapping")
        row["event_kind"] = kind

        for flag in ("storage_gap_before", "task_restart_before", "sequence_start_complete"):
            if flag in row and not isinstance(row[flag], bool):
                raise ValueError(f"{flag} must be an explicit boolean")
        if row.get("storage_gap_before", False):
            previous = None
            complete_start = False
            pending_reset = "storage_gap"
        if row.get("task_restart_before", False):
            previous = None
            complete_start = True
            pending_reset = "task_restart"

        row.update(
            previous_event_id=None,
            previous_code=None,
            previous_gap_s=None,
            previous_run_length=None,
            current_run_length=None,
            history_target=None,
            history_status="not_target",
            history_reset_reason=None,
        )
        if kind == "restart":
            previous = None
            complete_start = True
            pending_reset = "task_restart"
        elif kind == "unknown_sound":
            previous = None
            complete_start = False
            pending_reset = "unknown_sound"
        elif kind == "target":
            if row.get("sequence_start_complete", False):
                if previous is not None:
                    raise ValueError("complete-start evidence requires an explicit chain boundary")
                complete_start = True
            if previous is None:
                run = 1 if complete_start else None
                row["history_status"] = "no_previous_sound"
                row["history_reset_reason"] = pending_reset
            else:
                if onset <= previous["onset_sample"]:
                    raise ValueError("sound events need strictly increasing sample positions")
                previous_run = previous["run"]
                row.update(
                    previous_event_id=previous["trial_id"],
                    previous_code=previous["code"],
                    previous_gap_s=(onset - previous["onset_sample"]) / fs,
                    previous_run_length=previous_run,
                )
                if previous_run is None:
                    row["history_status"] = "incomplete_previous_run"
                elif previous_run == 2:
                    row["history_status"] = "excluded_run_length_2"
                else:
                    row["history_target"] = 0 if previous_run == 1 else 1
                    row["history_status"] = "complete"
                if row["event_literal"] != previous["code"]:
                    run = 1
                else:
                    run = None if previous_run is None else previous_run + 1
            row["current_run_length"] = run
            previous = {
                "trial_id": row["trial_id"],
                "code": row["event_literal"],
                "onset_sample": onset,
                "run": run,
            }
            pending_reset = None
            complete_start = False
        result.append(row)
    return result
