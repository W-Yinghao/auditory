"""Outcome-blind Stage 0 audit of the frozen N2 metadata design.

This module reads the already saved ``N2_k8_bags.parquet`` membership and
``full_event_history.parquet`` only.  It does not call the bag constructor,
open an EEG feature array, fit a predictor, or inspect a prediction.  The
small dataframe helpers are deliberately independent of the filesystem so
that the history and support rules can be checked with synthetic ledgers.

The detailed tables made by :func:`run` contain participant/source identifiers
and therefore stay under the private output directory.  The returned summary
and the report contain aggregate numerators and denominators only.
"""
from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .runtime import digest, require_slurm


K_MAIN = 8
MIN_BAGS_PER_CLASS_HALF = 2
MIN_SOURCE_BLOCKS = 3
MAX_MEMBERS_PER_BLOCK = 4  # ceil(k/2) for the frozen k=8 constructor

_BAG_ID_COLUMNS = (
    "bag_id", "trial_id", "candidate_id", "record_id", "segment_id",
    "stimulus_local_id", "A_half", "split_group_id", "A_block_id", "k",
)
_HISTORY_ID_COLUMNS = (
    "trial_id", "candidate_id", "record_id", "segment_id", "split_group_id",
    "stimulus_local_id", "accepted", "A_half", "A_block_id", "onset_sample",
    "previous_event_id", "previous_code", "previous_run_bin",
)


def h_bag_column_trace(known_codes: Iterable[str] = ("1", "2")) -> list[dict[str, str]]:
    """Describe the frozen ``H_BAG`` columns without reading EEG.

    This is a source/formula trace of ``auditory_next.n2_features``.  It is
    intentionally a fixed description: a column is never removed because it
    happens to predict the current class in this audit.
    """
    codes = tuple(str(code) for code in known_codes)
    if not codes or len(set(codes)) != len(codes):
        raise ValueError("N2_H_TRACE_CODES")
    trace: list[dict[str, str]] = []
    for code in codes:
        trace.append({
            "column": f"previous_code_{code}_proportion",
            "source": "previous_code",
            "formula": f"mean(previous_code == {code!r}) over the saved bag members",
            "role": "metadata history",
        })
    trace.append({
        "column": "previous_code_unknown_proportion",
        "source": "previous_code",
        "formula": "mean(previous_code is missing or outside known_codes)",
        "role": "metadata history",
    })
    for run_bin in ("run_1", "run_2", "run_3_5", "run_6_plus", "unknown"):
        trace.append({
            "column": f"previous_run_{run_bin}_proportion",
            "source": "previous_run_bin",
            "formula": f"mean(previous_run_bin == {run_bin!r}) over the saved bag members",
            "role": "metadata history",
        })
    trace.extend([
        {"column": "gap_mean", "source": "previous_gap_s", "formula": "mean(previous_gap_s with missing values mapped to 0)", "role": "metadata history"},
        {"column": "gap_present", "source": "previous_gap_s", "formula": "mean(isfinite(previous_gap_s))", "role": "metadata history"},
        {"column": "position_mean", "source": "position_fraction", "formula": "mean(position_fraction)", "role": "metadata/layout"},
        {"column": "position_squared", "source": "position_fraction", "formula": "mean(position_fraction ** 2)", "role": "metadata/layout"},
        {"column": "gap_std", "source": "previous_gap_s", "formula": "nanstd(previous_gap_s)", "role": "metadata history"},
        {"column": "position_std", "source": "position_fraction", "formula": "std(position_fraction, ddof=1)", "role": "metadata/layout"},
        {"column": "block_count", "source": "A_block_id", "formula": "number of distinct physical A blocks in the bag", "role": "metadata/layout"},
        {"column": "time_coverage_s", "source": "onset_seconds or onset_sample/original_fs", "formula": "max(member time) - min(member time)", "role": "metadata/timing"},
    ])
    return trace


def _missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        result = pd.isna(value)
        return bool(result) if np.ndim(result) == 0 else False
    except (TypeError, ValueError):
        return False


def _text(value: Any, *, missing: str = "__MISSING__") -> str:
    return missing if _missing(value) else str(value)


def _cell(value: Any, *, unknown: str = "unknown") -> str:
    """Canonical, conservative categorical value used by support auditing."""
    return unknown if _missing(value) else str(value)


def _group_tuple(row: pd.Series | dict[str, Any]) -> tuple[str, str, str, int, int]:
    return (
        _text(row["candidate_id"]), _text(row["record_id"]), _text(row["segment_id"]),
        int(row["stimulus_local_id"]), int(row["A_half"]),
    )


def _normalise_history(history: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(history, pd.DataFrame):
        raise ValueError("N2_HISTORY_TYPE")
    missing = sorted(set(_HISTORY_ID_COLUMNS) - set(history.columns))
    if missing:
        raise ValueError("N2_HISTORY_SCHEMA:" + ",".join(missing))
    frame = history.copy()
    if frame.trial_id.isna().any() or frame.trial_id.astype(str).duplicated().any():
        raise ValueError("N2_HISTORY_DUPLICATE_TRIAL")
    # The immutable history is the complete event ledger.  It may contain
    # rejected/non-target markers; only saved bag rows are required to carry
    # the two current class labels.
    if frame.A_half.notna().any():
        halves = pd.to_numeric(frame.A_half, errors="coerce")
        if halves.notna().any() and not halves.dropna().isin([0, 1]).all():
            raise ValueError("N2_HISTORY_HALF")
    return frame


def _normalise_bags(bags: pd.DataFrame, k: int = K_MAIN) -> pd.DataFrame:
    if not isinstance(bags, pd.DataFrame):
        raise ValueError("N2_BAGS_TYPE")
    missing = sorted(set(_BAG_ID_COLUMNS) - set(bags.columns))
    if missing:
        raise ValueError("N2_BAGS_SCHEMA:" + ",".join(missing))
    frame = bags.copy()
    if frame.empty:
        raise ValueError("N2_BAGS_EMPTY")
    if frame.trial_id.isna().any() or frame.bag_id.isna().any():
        raise ValueError("N2_BAGS_NULL_ID")
    if frame.trial_id.astype(str).duplicated().any():
        raise ValueError("N2_BAGS_TRIAL_OVERLAP")
    if not frame.stimulus_local_id.isin([0, 1]).all() or not frame.A_half.isin([0, 1]).all():
        raise ValueError("N2_BAGS_LABEL_OR_HALF")
    if int(k) != K_MAIN:
        raise ValueError("N2_FIXED_K8_REQUIRED")
    return frame


def _eligibility_mask(history: pd.DataFrame) -> tuple[pd.Series, str]:
    """Use the saved support eligibility flag, without rebuilding bags."""
    mask = history.accepted.astype(bool) & history.stimulus_local_id.isin([0, 1]) & history.A_half.notna()
    if "v2_context_boundary_eligible" in history:
        return mask & history.v2_context_boundary_eligible.fillna(False).astype(bool), "v2_context_boundary_eligible"
    if "A_boundary_eligible" in history:
        return mask & history.A_boundary_eligible.fillna(False).astype(bool), "A_boundary_eligible"
    return mask, "accepted_label_half_only_no_boundary_column"


def _physical_block(row: pd.Series | dict[str, Any]) -> tuple[str, str, str]:
    return (_text(row["record_id"]), _text(row["segment_id"]), _text(row["A_block_id"]))


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if _missing(value):
        return None
    return value


def audit_saved_bags(
    bags: pd.DataFrame,
    history: pd.DataFrame,
    *,
    k: int = K_MAIN,
    min_bags_per_group: int = MIN_BAGS_PER_CLASS_HALF,
    min_source_blocks: int = MIN_SOURCE_BLOCKS,
) -> dict[str, Any]:
    """Check frozen bag invariants and source quotas; never construct bags.

    ``bag_checks`` and ``source_checks`` retain identifiers for private audit
    tables.  Aggregate values use the actual saved bag/member/source-group
    denominators and are suitable for the public summary.
    """
    bags = _normalise_bags(bags, k)
    history = _normalise_history(history)
    h = history.copy()
    h["_trial_key"] = h.trial_id.astype(str)
    h_lookup = h.set_index("_trial_key", drop=False)
    bag_group_counts = bags.groupby(
        ["candidate_id", "record_id", "segment_id", "stimulus_local_id", "A_half"],
        dropna=False, sort=False,
    ).bag_id.nunique()
    eligible, eligibility_source = _eligibility_mask(h)
    source = h.loc[eligible].copy()
    source["_group_key"] = list(source.apply(_group_tuple, axis=1))
    source["_physical_block"] = list(source.apply(_physical_block, axis=1))
    source_checks_rows = []
    for key, part in source.groupby("_group_key", sort=True):
        candidate, record, segment, cls, half = key
        represented = bags.loc[
            (bags.candidate_id.astype(str) == candidate)
            & (bags.record_id.astype(str) == record)
            & (bags.segment_id.astype(str) == segment)
            & (bags.stimulus_local_id.astype(int) == cls)
            & (bags.A_half.astype(int) == half)
        ]
        n_bags = int(represented.bag_id.nunique())
        source_blocks = int(part["_physical_block"].nunique())
        source_checks_rows.append({
            "candidate_id": candidate, "record_id": record, "segment_id": segment,
            "stimulus_local_id": cls, "A_half": half,
            "source_n_trials": int(part.trial_id.nunique()),
            "source_n_blocks": source_blocks, "saved_n_bags": n_bags,
            "min_bags_ok": bool(n_bags >= int(min_bags_per_group)),
            "min_source_blocks_ok": bool(source_blocks >= int(min_source_blocks)),
            "represented_in_saved_bags": bool(n_bags > 0),
        })
    source_checks = pd.DataFrame(source_checks_rows)
    source_by_key = {
        (str(row.candidate_id), str(row.record_id), str(row.segment_id),
         int(row.stimulus_local_id), int(row.A_half)): row
        for row in source_checks.itertuples()
    }
    record_cell_sets = {
        (str(candidate), str(record)): set(zip(
            part.A_half.astype(int), part.stimulus_local_id.astype(int)))
        for (candidate, record), part in bags.groupby(["candidate_id", "record_id"], sort=False)
    }
    required_record_cells = {(0, 0), (0, 1), (1, 0), (1, 1)}

    bag_checks_rows = []
    for bag_id, part in bags.groupby(bags.bag_id.astype(str), sort=True):
        key_row = part.iloc[0]
        key = _group_tuple(key_row)
        member_keys = part.trial_id.astype(str).tolist()
        present = [trial_id in h_lookup.index for trial_id in member_keys]
        members = h_lookup.reindex(member_keys)
        blocks = []
        if all(present):
            blocks = [_physical_block(members.iloc[i]) for i in range(len(members))]
        block_counts = pd.Series(blocks).value_counts() if blocks else pd.Series(dtype=int)
        source_row = source_by_key.get(key)
        record_four_cell_ok = record_cell_sets.get((key[0], key[1]), set()) == required_record_cells
        constant_bags = all(part[col].astype(str).nunique(dropna=False) == 1 for col in (
            "candidate_id", "record_id", "segment_id", "stimulus_local_id", "A_half", "split_group_id"))
        history_matches = bool(all(present))
        if history_matches:
            history_matches = all(
                _text(members.iloc[i].candidate_id) == _text(part.iloc[i].candidate_id)
                and _text(members.iloc[i].record_id) == _text(part.iloc[i].record_id)
                and _text(members.iloc[i].segment_id) == _text(part.iloc[i].segment_id)
                and int(members.iloc[i].stimulus_local_id) == int(part.iloc[i].stimulus_local_id)
                and int(members.iloc[i].A_half) == int(part.iloc[i].A_half)
                for i in range(len(part))
            )
        stored_block_count = int(part.bag_block_count.iloc[0]) if "bag_block_count" in part else None
        derived_block_count = int(len(block_counts)) if blocks else 0
        size_ok = len(part) == int(k) and part.k.astype(int).eq(int(k)).all()
        block_ok = bool(derived_block_count >= 2 and (block_counts <= int(math.ceil(int(k) / 2))).all())
        stored_block_ok = stored_block_count is None or stored_block_count == derived_block_count
        bag_checks_rows.append({
            "bag_id": str(bag_id), "candidate_id": key[0], "record_id": key[1],
            "segment_id": key[2], "stimulus_local_id": key[3], "A_half": key[4],
            "n_members": int(len(part)), "n_blocks": derived_block_count,
            "max_members_in_block": int(block_counts.max()) if len(block_counts) else 0,
            "size_k8_ok": bool(size_ok), "multi_block_ok": block_ok,
            "stored_block_count_ok": bool(stored_block_ok),
            "constant_bag_metadata_ok": bool(constant_bags),
            "history_alignment_ok": bool(history_matches),
            "source_min_bags_ok": bool(source_row is not None and source_row.min_bags_ok),
            "source_min_blocks_ok": bool(source_row is not None and source_row.min_source_blocks_ok),
            "eligible_source_group_present": bool(source_row is not None),
            "record_four_cell_support_ok": bool(record_four_cell_ok),
        })
    bag_checks = pd.DataFrame(bag_checks_rows)

    n_bags = int(bags.bag_id.astype(str).nunique())
    n_members = int(len(bags))
    n_source_groups = int(len(source_checks))
    represented_source = source_checks.loc[source_checks.represented_in_saved_bags] if not source_checks.empty else source_checks
    aggregate = {
        "k": int(k), "n_bags_denominator": n_bags, "n_member_rows_denominator": n_members,
        "n_source_groups_denominator": n_source_groups,
        "n_represented_source_groups_denominator": int(len(represented_source)),
        "n_bags_bad_k": int((~bag_checks.size_k8_ok).sum()),
        "n_bags_bad_multi_block": int((~bag_checks.multi_block_ok).sum()),
        "n_bags_bad_history_alignment": int((~bag_checks.history_alignment_ok).sum()),
        "n_bags_bad_source_quota": int((~(bag_checks.source_min_bags_ok & bag_checks.source_min_blocks_ok)).sum()),
        "n_bags_bad_record_four_cell_support": int((~bag_checks.record_four_cell_support_ok).sum()),
        "n_source_groups_below_min_bags": int((~source_checks.min_bags_ok).sum()) if not source_checks.empty else 0,
        "n_source_groups_below_min_blocks": int((~source_checks.min_source_blocks_ok).sum()) if not source_checks.empty else 0,
        "min_bags_per_class_half": int(min_bags_per_group),
        "min_source_blocks": int(min_source_blocks),
        "max_members_per_block": int(math.ceil(int(k) / 2)),
        "eligibility_source": eligibility_source,
    }
    return {"aggregate": aggregate, "bag_checks": bag_checks, "source_checks": source_checks}


def _history_chain(history_lookup: pd.DataFrame, trial_id: Any) -> dict[str, Any]:
    """Walk saved complete-chain links, retaining rejected events in the walk.

    ``history_lookup`` may be a dataframe for small callers or a mapping of
    trial key to row mapping for the real audit.  The latter avoids a pandas
    ``.loc`` operation for every edge in every member's chain.
    """
    records = history_lookup if isinstance(history_lookup, Mapping) else {
        str(index): row.to_dict() if isinstance(row, pd.Series) else row
        for index, row in history_lookup.iterrows()
    }
    current = _text(trial_id)
    visited: set[str] = set()
    chain: list[str] = []
    rejected: list[str] = []
    missing_link = False
    cycle = False
    while current in records:
        if current in visited:
            cycle = True
            break
        visited.add(current)
        row = records[current]
        previous = row.get("previous_event_id")
        if _missing(previous):
            break
        previous_key = _text(previous)
        chain.append(previous_key)
        if previous_key not in records:
            missing_link = True
            break
        previous_row = records[previous_key]
        if not bool(previous_row.get("accepted", True)):
            rejected.append(previous_key)
        current = previous_key
    return {
        "chain": chain, "rejected_chain": rejected,
        "missing_link": bool(missing_link), "cycle": bool(cycle),
    }


def _cached_history_chain(
    records: Mapping[str, Mapping[str, Any]],
    trial_id: Any,
    cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Memoized complete-chain walk for the many members in saved bags."""
    start = _text(trial_id)
    if start in cache:
        return cache[start]
    current = start
    visited: dict[str, int] = {}
    path: list[str] = []
    chain: list[str] = []
    rejected: list[str] = []
    missing_link = False
    cycle = False
    while current in records:
        if current in visited:
            cycle = True
            break
        if current in cache:
            tail = cache[current]
            chain.extend(tail["chain"])
            rejected.extend(tail["rejected_chain"])
            missing_link = bool(tail["missing_link"])
            cycle = bool(tail["cycle"])
            break
        visited[current] = len(path)
        path.append(current)
        previous = records[current].get("previous_event_id")
        if _missing(previous):
            break
        previous_key = _text(previous)
        chain.append(previous_key)
        if previous_key not in records:
            missing_link = True
            break
        if not bool(records[previous_key].get("accepted", True)):
            rejected.append(previous_key)
        current = previous_key
    result = {
        "chain": chain, "rejected_chain": rejected,
        "missing_link": bool(missing_link), "cycle": bool(cycle),
    }
    # Acyclic walks can safely be reused: every suffix has the same terminal
    # status.  Cycles depend on the starting point and are left uncached.
    if not cycle:
        for offset, node in enumerate(path):
            suffix_chain = chain[offset:]
            cache[node] = {
                "chain": suffix_chain,
                # ``rejected_chain`` is a filtered projection of chain, so it
                # cannot be sliced at the same offset as the full chain.
                "rejected_chain": [
                    ancestor for ancestor in suffix_chain
                    if ancestor in records and not bool(records[ancestor].get("accepted", True))
                ],
                "missing_link": bool(missing_link), "cycle": False,
            }
    return result


def audit_member_history(bags: pd.DataFrame, history: pd.DataFrame, *, k: int = K_MAIN) -> dict[str, Any]:
    """Audit direct/earlier same-bag history links over the full event ledger."""
    bags = _normalise_bags(bags, k)
    history = _normalise_history(history)
    keyed = history.copy()
    keyed["_trial_key"] = keyed.trial_id.astype(str)
    records = {
        str(row["_trial_key"]): row
        for row in keyed.to_dict("records")
    }
    chain_cache: dict[str, dict[str, Any]] = {}
    relation_rows = []
    bag_relation_count = 0
    for bag_id, part in bags.groupby(bags.bag_id.astype(str), sort=True):
        members = set(part.trial_id.astype(str))
        has_relation = False
        for trial_id in part.trial_id.astype(str):
            walk = _cached_history_chain(records, trial_id, chain_cache)
            direct = bool(walk["chain"] and walk["chain"][0] in members and walk["chain"][0] != trial_id)
            earlier_members = sorted({node for node in walk["chain"] if node in members and node != trial_id})
            within2 = {node for node in walk["chain"][:2] if node in members and node != trial_id}
            within3 = {node for node in walk["chain"][:3] if node in members and node != trial_id}
            if direct or earlier_members:
                has_relation = True
            relation_rows.append({
                "bag_id": str(bag_id), "trial_id": str(trial_id),
                "direct_previous_member": direct,
                "earlier_member_count": int(len(earlier_members)),
                "any_earlier_member": bool(earlier_members),
                "earlier_member_count_within2": int(len(within2)),
                "earlier_member_count_within3": int(len(within3)),
                "chain_length": int(len(walk["chain"])),
                "rejected_chain_length": int(len(walk["rejected_chain"])),
                "has_rejected_earlier_event": bool(walk["rejected_chain"]),
                "chain_missing_link": bool(walk["missing_link"]),
                "chain_cycle": bool(walk["cycle"]),
            })
        if has_relation:
            bag_relation_count += 1
    relations = pd.DataFrame(relation_rows)
    n_members = int(len(relations))
    aggregate = {
        "n_bags_denominator": int(bags.bag_id.astype(str).nunique()),
        "n_member_rows_denominator": n_members,
        "n_member_rows_with_nonnull_previous_denominator": int((relations.chain_length > 0).sum()),
        "n_members_direct_previous_member": int(relations.direct_previous_member.sum()),
        "n_members_any_earlier_member": int(relations.any_earlier_member.sum()),
        "n_members_within2_earlier_member": int((relations.earlier_member_count_within2 > 0).sum()),
        "n_members_within3_earlier_member": int((relations.earlier_member_count_within3 > 0).sum()),
        "n_bags_with_any_member_history_relation": int(bag_relation_count),
        "n_members_with_rejected_earlier_event": int(relations.has_rejected_earlier_event.sum()),
        "n_member_walks_missing_link": int(relations.chain_missing_link.sum()),
        "n_member_walks_cycle": int(relations.chain_cycle.sum()),
        "history_chain_uses_rejected_events": True,
        "ancestor_relation_scope": "all saved previous_event_id ancestors, including rejected events",
        "h_bag_dependency_scope": "member-level previous_code, previous_run_bin, previous_gap_s, position_fraction, A_block_id, and onset time; previous_event_id ancestor identity is not an H_BAG column",
    }
    return {"aggregate": aggregate, "relations": relations}


def _support_cell(row: pd.Series) -> tuple[str, str]:
    return (_cell(row.get("previous_code")), _cell(row.get("previous_run_bin")))


def audit_common_history_support(
    bags: pd.DataFrame,
    history: pd.DataFrame,
    bag_audit: dict[str, Any] | None = None,
    *,
    k: int = K_MAIN,
    min_bags_per_class_half: int = MIN_BAGS_PER_CLASS_HALF,
) -> dict[str, Any]:
    """Audit exact and coarse history support for every candidate×half pair.

    Exact cells are the frozen ``previous_code × previous_run_bin`` pairs.
    Code-only and run-bin-only intersections are descriptive marginals; they
    never replace, or select a favorable subset of, the exact support.
    """
    bags = _normalise_bags(bags, k)
    history = _normalise_history(history)
    keyed = history.copy()
    keyed["_trial_key"] = keyed.trial_id.astype(str)
    records = {str(row["_trial_key"]): row for row in keyed.to_dict("records")}
    rows = []
    for bag_id, part in bags.groupby(bags.bag_id.astype(str), sort=False):
        for _, member in part.iterrows():
            trial = _text(member.trial_id)
            if trial not in records:
                raise ValueError("N2_SUPPORT_HISTORY_ALIGNMENT")
            hrow = records[trial]
            if (
                _text(hrow["candidate_id"]) != _text(member.candidate_id)
                or _text(hrow["record_id"]) != _text(member.record_id)
                or _text(hrow["segment_id"]) != _text(member.segment_id)
                or int(hrow["stimulus_local_id"]) != int(member.stimulus_local_id)
                or int(hrow["A_half"]) != int(member.A_half)
            ):
                raise ValueError("N2_SUPPORT_METADATA_ALIGNMENT")
            rows.append({
                "candidate_id": _text(member.candidate_id), "A_half": int(member.A_half),
                "stimulus_local_id": int(member.stimulus_local_id),
                "bag_id": str(bag_id), "trial_id": trial,
                "cell": _support_cell(hrow),
            })
    members = pd.DataFrame(rows)
    details = []
    for (candidate, half), part in members.groupby(["candidate_id", "A_half"], sort=True):
        class_info: dict[int, dict[str, Any]] = {}
        for cls in (0, 1):
            cls_part = part.loc[part.stimulus_local_id == cls]
            counts = cls_part.cell.value_counts().to_dict()
            class_info[cls] = {
                "cells": set(counts), "codes": {cell[0] for cell in counts},
                "runs": {cell[1] for cell in counts},
                "n_members": int(len(cls_part)),
                "n_bags": int(cls_part.bag_id.nunique()),
                "cell_counts": counts,
            }
        both_classes = all(class_info[cls]["n_bags"] > 0 for cls in (0, 1))
        exact = class_info[0]["cells"] & class_info[1]["cells"]
        common_codes = class_info[0]["codes"] & class_info[1]["codes"]
        common_runs = class_info[0]["runs"] & class_info[1]["runs"]
        quota_ok = all(class_info[cls]["n_bags"] >= int(min_bags_per_class_half) for cls in (0, 1))
        equal_bag_quota = bool(
            both_classes and class_info[0]["n_bags"] == class_info[1]["n_bags"] and quota_ok
        )
        equal_cell_quota = bool(
            exact and all(
                class_info[0]["cell_counts"].get(cell, 0) == class_info[1]["cell_counts"].get(cell, 0)
                for cell in exact
            )
        )
        source_quota_ok = True
        construction_feasible = False
        if bag_audit is not None:
            source_checks = bag_audit.get("source_checks", pd.DataFrame())
            bag_checks = bag_audit.get("bag_checks", pd.DataFrame())
            if not source_checks.empty:
                represented = source_checks.loc[
                    source_checks.candidate_id.astype(str).eq(str(candidate))
                    & source_checks.A_half.astype(int).eq(int(half))
                    & source_checks.represented_in_saved_bags
                ]
                source_quota_ok = bool(
                    not represented.empty
                    and represented.min_bags_ok.astype(bool).all()
                    and represented.min_source_blocks_ok.astype(bool).all()
                )
            if not bag_checks.empty:
                represented_bags = bag_checks.loc[
                    bag_checks.candidate_id.astype(str).eq(str(candidate))
                    & bag_checks.A_half.astype(int).eq(int(half))
                ]
                source_quota_ok = bool(
                    source_quota_ok
                    and not represented_bags.empty
                    and represented_bags.record_four_cell_support_ok.astype(bool).all()
                )
                valid_saved_bags = bool(
                    not represented_bags.empty
                    and represented_bags.size_k8_ok.astype(bool).all()
                    and represented_bags.multi_block_ok.astype(bool).all()
                    and represented_bags.history_alignment_ok.astype(bool).all()
                    and represented_bags.source_min_bags_ok.astype(bool).all()
                    and represented_bags.source_min_blocks_ok.astype(bool).all()
                    and represented_bags.record_four_cell_support_ok.astype(bool).all()
                )
                construction_feasible = bool(
                    equal_bag_quota and equal_cell_quota and source_quota_ok and valid_saved_bags
                )
        design_eligible = bool(both_classes and quota_ok and source_quota_ok)
        details.append({
            "candidate_id": str(candidate), "A_half": int(half),
            "class0_n_bags": class_info[0]["n_bags"], "class1_n_bags": class_info[1]["n_bags"],
            "class0_n_members": class_info[0]["n_members"], "class1_n_members": class_info[1]["n_members"],
            "both_classes_present": bool(both_classes), "fixed_quota_ok": bool(quota_ok),
            "equal_bag_quota": bool(equal_bag_quota), "equal_cell_quota": bool(equal_cell_quota),
            "source_quota_ok": bool(source_quota_ok), "design_eligible": design_eligible,
            "construction_feasible_from_saved_membership": bool(construction_feasible),
            "exact_common_cell_count": int(len(exact)),
            "code_marginal_common_count": int(len(common_codes)),
            "run_marginal_common_count": int(len(common_runs)),
            "exact_common_support": bool(exact),
            "code_marginal_common_support": bool(common_codes),
            "run_marginal_common_support": bool(common_runs),
            "exact_common_member_capacity": int(sum(min(class_info[0]["cell_counts"].get(cell, 0), class_info[1]["cell_counts"].get(cell, 0)) for cell in exact)),
        })
    details = pd.DataFrame(details)
    denominator = int(len(details))
    eligible_details = details.loc[details.design_eligible] if denominator else details
    aggregate = {
        "candidate_half_denominator": denominator,
        "candidate_half_both_classes_denominator": int(details.both_classes_present.sum()) if denominator else 0,
        "candidate_half_fixed_quota_denominator": int((details.both_classes_present & details.fixed_quota_ok).sum()) if denominator else 0,
        "candidate_half_design_eligible_denominator": int(len(eligible_details)),
        "candidate_half_exact_common_numerator": int(details.exact_common_support.sum()) if denominator else 0,
        "candidate_half_design_exact_common_numerator": int(eligible_details.exact_common_support.sum()) if denominator else 0,
        "candidate_half_construction_feasible_numerator": int(eligible_details.construction_feasible_from_saved_membership.sum()) if denominator else 0,
        "candidate_half_code_marginal_common_numerator": int(details.code_marginal_common_support.sum()) if denominator else 0,
        "candidate_half_run_marginal_common_numerator": int(details.run_marginal_common_support.sum()) if denominator else 0,
        "exact_support_is_frozen_cell_intersection": True,
        "coarse_marginals_descriptive_only": True,
        "posthoc_cell_selection": False,
        "observed_imbalance_is_necessary_support_limit_only": True,
        "new_balanced_reconstruction_ruled_out": False,
        "support_status": (
            "COMMON_HISTORY_SUPPORT_WITH_FIXED_QUOTAS"
            if denominator and bool(eligible_details.construction_feasible_from_saved_membership.any())
            else "NECESSARY_SUPPORT_ONLY"
        ),
        "k": int(k),
    }
    return {"aggregate": aggregate, "details": details}


def _resolve_support_paths(root: Path, config: dict[str, Any]) -> tuple[Path, Path, Path]:
    stage = config.get("stage0", config)
    support_source = stage.get("support_source", config.get("support_source", "S1_support_004"))
    explicit = stage.get("support_dir") or config.get("support_dir")
    if explicit:
        support_dir = Path(explicit)
        if not support_dir.is_absolute():
            support_dir = root / support_dir
    else:
        support_dir = root / "private" / "auditory_next_v2" / str(support_source)
    bags_value = stage.get("bags_path") or config.get("bags_path")
    history_value = stage.get("history_path") or config.get("history_path")
    bags_path = Path(bags_value) if bags_value else support_dir / "N2_k8_bags.parquet"
    history_path = Path(history_value) if history_value else support_dir / "full_event_history.parquet"
    if not bags_path.is_absolute():
        bags_path = root / bags_path
    if not history_path.is_absolute():
        history_path = root / history_path
    return support_dir, bags_path, history_path


def _write_private_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_jsonable(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    path.chmod(0o600)


def _write_private_frame(path: Path, frame: pd.DataFrame) -> None:
    frame.to_parquet(path, index=False)
    path.chmod(0o600)


def _report_text(summary: dict[str, Any], trace: list[dict[str, str]]) -> str:
    bag = summary["bag_audit"]
    relation = summary["member_history_audit"]
    support = summary["common_history_support"]
    lines = [
        "# N2 v2.1 Stage 0 metadata support audit",
        "",
        "This is an outcome-blind metadata audit of the immutable saved k=8 bags and complete event history. It opened no EEG feature array, fit no head, and read no prediction.",
        "",
        "## Frozen bag and source constraints",
        "",
        f"Saved bag denominator: {bag['n_bags_denominator']}; saved member-row denominator: {bag['n_member_rows_denominator']}. Bad k=8 bags: {bag['n_bags_bad_k']}; bad multi-block bags: {bag['n_bags_bad_multi_block']}; bad history alignment: {bag['n_bags_bad_history_alignment']}; bags lacking the original four class×half record support: {bag['n_bags_bad_record_four_cell_support']}.",
        f"Source-group denominator: {bag['n_represented_source_groups_denominator']}; groups below the frozen two-bag quota: {bag['n_source_groups_below_min_bags']}; groups below the frozen three-source-block requirement: {bag['n_source_groups_below_min_blocks']}.",
        "",
        "## Complete-chain member relation audit",
        "",
        f"Member-row denominator: {relation['n_member_rows_denominator']}; direct previous-member numerator: {relation['n_members_direct_previous_member']}; within-two-link numerator: {relation['n_members_within2_earlier_member']}; within-three-link numerator: {relation['n_members_within3_earlier_member']}; any earlier-chain member numerator: {relation['n_members_any_earlier_member']}. Bag denominator: {relation['n_bags_denominator']}; bags with any relation: {relation['n_bags_with_any_member_history_relation']}.",
        f"The walk follows the saved complete history, including rejected events: {relation['history_chain_uses_rejected_events']}. Members whose earlier chain contains a rejected event: {relation['n_members_with_rejected_earlier_event']}. This all-ancestor audit is a diagnostic; H_BAG itself uses member-level previous_code, previous_run_bin, previous_gap_s, position, block, and timing summaries, not arbitrary ancestor identity.",
        "",
        "## Common history support",
        "",
        f"Candidate×half denominator: {support['candidate_half_denominator']}; both-class denominator: {support['candidate_half_both_classes_denominator']}; design-eligible denominator after fixed quotas: {support['candidate_half_design_eligible_denominator']}; exact common-cell numerator: {support['candidate_half_design_exact_common_numerator']}; saved-membership construction-feasibility numerator under equal exact-cell quotas and multi-block checks: {support['candidate_half_construction_feasible_numerator']}.",
        f"Support status: {support['support_status']}. Descriptive code-marginal numerator: {support['candidate_half_code_marginal_common_numerator']}; run-bin-marginal numerator: {support['candidate_half_run_marginal_common_numerator']}. These marginals do not replace the exact previous_code×previous_run_bin intersection. Posthoc cell selection: {support['posthoc_cell_selection']}. Observed member imbalance limits necessary support only and does not rule out constructing a new balanced bag design.",
        "",
        "## H_BAG source trace",
        "",
        "H_BAG is assembled from member-level event metadata. Its columns are documented below; no current label or EEG array is a source column.",
        "",
        "| column | source | frozen formula | role |",
        "|---|---|---|---|",
    ]
    lines.extend(f"| {item['column']} | {item['source']} | {item['formula']} | {item['role']} |" for item in trace)
    lines.extend([
        "", "The support count documents an observational design property only. No N2 EEG contrast or scientific effect was computed in Stage 0.", "",
    ])
    return "\n".join(lines)


def run(root: Path, private: Path, public: Path, report: Path, config: dict) -> dict:
    """Run the bounded metadata-only audit in a Slurm worker.

    Required inputs are the frozen support run named by ``stage0.support_source``
    (default ``S1_support_004``), with its ``N2_k8_bags.parquet`` and
    ``full_event_history.parquet``.  Optional ``support_dir``, ``bags_path`` or
    ``history_path`` config keys may point to those immutable files.  The
    destination directories must be the new v2.1 private/results/reports run.
    """
    require_slurm()
    root, private, public, report = map(Path, (root, private, public, report))
    stage = config.get("stage0", config)
    if int(stage.get("N2_k", K_MAIN)) != K_MAIN:
        raise ValueError("N2_FIXED_K8_REQUIRED")
    support_dir, bags_path, history_path = _resolve_support_paths(root, config)
    for path in (bags_path, history_path):
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(str(path))
    if bags_path.resolve() == (private / "N2_k8_bags.parquet").resolve() or history_path.resolve() == (private / "full_event_history.parquet").resolve():
        raise ValueError("N2_INPUT_OUTPUT_COLLISION")
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    public.mkdir(parents=True, exist_ok=True, mode=0o700)
    report.mkdir(parents=True, exist_ok=True, mode=0o700)
    private.chmod(0o700)

    hashes = {str(path): digest(path) for path in (bags_path, history_path)}
    for extra in (support_dir / "support_definition.json", support_dir / "N2_groups.json"):
        if extra.exists():
            hashes[str(extra)] = digest(extra)
    _write_private_json(private / "input_hashes.json", hashes)

    bags = pd.read_parquet(bags_path)
    history = pd.read_parquet(history_path)
    bag_audit = audit_saved_bags(
        bags, history, k=K_MAIN,
        min_bags_per_group=int(stage.get("N2_min_bags_per_class_half", MIN_BAGS_PER_CLASS_HALF)),
        min_source_blocks=int(stage.get("N2_min_source_blocks", MIN_SOURCE_BLOCKS)),
    )
    relation_audit = audit_member_history(bags, history, k=K_MAIN)
    support_audit = audit_common_history_support(bags, history, bag_audit, k=K_MAIN,
                                                  min_bags_per_class_half=int(stage.get("N2_min_bags_per_class_half", MIN_BAGS_PER_CLASS_HALF)))
    trace = h_bag_column_trace()

    _write_private_frame(private / "bag_checks.parquet", bag_audit["bag_checks"])
    _write_private_frame(private / "source_checks.parquet", bag_audit["source_checks"])
    _write_private_frame(private / "member_history_relations.parquet", relation_audit["relations"])
    _write_private_frame(private / "candidate_half_common_support.parquet", support_audit["details"])
    _write_private_json(private / "h_bag_column_trace.json", trace)

    summary = {
        "status": "N2_METADATA_AUDIT_COMPLETE",
        "scientific_effects_viewed": False,
        "new_head_fits": 0,
        "new_encoder_fits": 0,
        "input_hashes_recorded": True,
        "bag_audit": bag_audit["aggregate"],
        "member_history_audit": relation_audit["aggregate"],
        "common_history_support": support_audit["aggregate"],
        "design_support_status": (
            "COMMON_HISTORY_SUPPORT_WITH_FIXED_QUOTAS"
            if support_audit["aggregate"]["candidate_half_construction_feasible_numerator"] > 0
            else "NECESSARY_SUPPORT_ONLY"
        ),
    }
    _write_private_json(private / "n2_metadata_audit_summary.json", summary)
    report_path = report / "N2_METADATA_SUPPORT_AUDIT.md"
    report_path.write_text(_report_text(summary, trace))
    report_path.chmod(0o600)
    return summary


__all__ = [
    "K_MAIN", "h_bag_column_trace", "audit_saved_bags", "audit_member_history",
    "audit_common_history_support", "run",
]
