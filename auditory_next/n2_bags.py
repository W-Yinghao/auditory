"""Fixed, non-overlapping N2 repeated-trial bags from metadata only."""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pandas as pd


REQUIRED = {"trial_id", "candidate_id", "record_id", "segment_id", "split_group_id",
            "stimulus_local_id", "A_half", "A_boundary_eligible", "A_block_id"}


def _key(seed: int, *parts) -> str:
    payload = "|".join([str(seed), *map(str, parts)]).encode()
    return hashlib.sha256(payload).hexdigest()


def _choose(pool: pd.DataFrame, k: int, seed: int, *, block_column: str = "A_block_id") -> list[int] | None:
    """Greedily choose a valid bag, with deterministic block coverage."""
    if len(pool) < k:
        return None
    ordered = sorted(pool.index.tolist(), key=lambda i: _key(seed, pool.at[i, "trial_id"]))
    # The multi-block constraint is specified for k>=4.  Smaller sensitivity
    # bags remain deterministic but do not acquire an extra, unstated gate.
    if k < 4:
        return ordered[:k]
    block_counts = {}
    selected = []
    max_per_block = int(math.ceil(k / 2))
    # Seed the bag from two different source blocks when possible.
    for index in ordered:
        block = pool.at[index, block_column]
        if block not in block_counts:
            selected.append(index)
            block_counts[block] = 1
            if len(block_counts) >= 2:
                break
    if len(selected) < 2:
        return None
    for index in ordered:
        if index in selected:
            continue
        block = pool.at[index, block_column]
        if block_counts.get(block, 0) >= max_per_block:
            continue
        selected.append(index)
        block_counts[block] = block_counts.get(block, 0) + 1
        if len(selected) == k:
            return selected
    return None


def make_n2_bags(rows: pd.DataFrame, *, k: int = 8, seed: int = 20260917,
                 require_min_bags: int = 2, require_min_blocks: int = 3):
    """Return ``(bags, unused)`` for one fixed N2 bagging scheme.

    Bags are created independently within record × class × half.  For
    ``k>=4`` each bag spans at least two physical blocks and uses at most
    ceil(k/2) trials from any block.  A candidate is admitted only when all
    four class × half cells exist upstream; each record/segment group must
    then yield the required number of bags and block coverage.  Otherwise
    every row remains in ``unused`` with an explicit reason.
    """
    if not isinstance(rows, pd.DataFrame) or not REQUIRED.issubset(rows.columns):
        raise ValueError("N2_BAG_SCHEMA")
    if k < 1 or require_min_bags < 1 or require_min_blocks < 1:
        raise ValueError("N2_BAG_PARAMETER")
    if rows.trial_id.duplicated().any():
        raise ValueError("N2_DUPLICATE_TRIAL")
    if rows[["candidate_id", "record_id", "segment_id", "split_group_id"]].isna().any().any():
        raise ValueError("N2_IDENTITY_SCHEMA")
    if not rows.stimulus_local_id.isin([0, 1]).all() or not rows.A_half.isin([0, 1]).all():
        raise ValueError("N2_LABEL_OR_HALF")
    if rows.groupby("candidate_id").split_group_id.nunique().gt(1).any():
        raise ValueError("N2_CANDIDATE_SPLIT_GROUP_MISMATCH")
    eligible = rows.A_boundary_eligible.fillna(False).astype(bool)
    # The four candidate × class × half cells are an upstream support gate;
    # this function never fills a missing cell by creating a pseudo-bag.
    support_rows = rows.loc[eligible].assign(_candidate_key=lambda frame: frame.candidate_id.astype(str))
    cell_counts = support_rows.groupby(["_candidate_key", "stimulus_local_id", "A_half"]).size()
    complete_candidates = set(rows.candidate_id.astype(str))
    complete_candidates = {
        candidate for candidate in complete_candidates
        if all((candidate, cls, half) in cell_counts.index
               for cls in (0, 1) for half in (0, 1))
    }
    if complete_candidates != set(rows.candidate_id.astype(str)):
        # Preserve all rows as explicit unused records for incomplete support.
        incomplete = rows.loc[~rows.candidate_id.astype(str).isin(complete_candidates)]
    else:
        incomplete = rows.iloc[0:0]
    records, unused = [], []
    for _, row in incomplete.iterrows():
        unused.append(dict(trial_id=str(row.trial_id), reason="candidate_missing_class_half",
                           group_key=str(row.candidate_id)))
    rows = rows.loc[rows.candidate_id.astype(str).isin(complete_candidates)]
    eligible = eligible.loc[rows.index]
    grouped = rows.groupby(["candidate_id", "record_id", "segment_id", "stimulus_local_id", "A_half"], sort=True)
    for key, part in grouped:
        if part.split_group_id.astype(str).nunique() != 1:
            raise ValueError("N2_RECORD_SPLIT_GROUP_MISMATCH")
        ineligible = part.loc[~eligible.loc[part.index]]
        for trial_id in ineligible.trial_id.astype(str):
            unused.append(dict(trial_id=trial_id, reason="not_boundary_eligible",
                               group_key="|".join(map(str, key))))
        part = part.loc[eligible.loc[part.index]]
        if part.empty:
            continue
        # Keep the physical key fully textual so parquet/object serializers do
        # not encounter mixed str/int tuples (and preserve block identity).
        part = part.assign(_physical_block=list(zip(part.record_id.astype(str),
                                                     part.segment_id.astype(str),
                                                     part.A_block_id.astype(str))))
        blocks = part._physical_block.nunique()
        candidates = part.copy()
        local = []
        ordinal = 0
        while len(candidates) >= k:
            chosen = _choose(candidates, k, seed + ordinal, block_column="_physical_block")
            if chosen is None:
                break
            selected = candidates.loc[chosen]
            if k >= 4 and selected._physical_block.nunique() < 2:
                break
            bag_id = "bag_" + _key(seed, *key, ordinal)[:20]
            for _, selected_row in selected.iterrows():
                trial_id = str(selected_row.trial_id)
                local.append(dict(bag_id=bag_id, trial_id=trial_id,
                                  candidate_id=str(key[0]), record_id=str(key[1]),
                                  segment_id=str(key[2]), stimulus_local_id=int(key[3]),
                                  A_half=int(key[4]), split_group_id=str(selected.iloc[0].split_group_id),
                                  A_block_id=selected_row.A_block_id,
                                  physical_block_id=json.dumps(list(selected_row._physical_block),
                                                               ensure_ascii=False, separators=(",", ":")),
                                  k=int(k), variance_defined=bool(k >= 2),
                                  bag_ordinal=int(ordinal), bag_seed=int(seed),
                                  bag_block_count=int(selected._physical_block.nunique())))
            candidates = candidates.drop(index=chosen)
            ordinal += 1
        if blocks < require_min_blocks or ordinal < require_min_bags:
            for trial_id in part.trial_id.astype(str):
                unused.append(dict(trial_id=trial_id, reason=(
                    "insufficient_source_blocks" if blocks < require_min_blocks
                    else "insufficient_bags"), group_key="|".join(map(str, key))))
            continue
        records.extend(local)
        for trial_id in candidates.trial_id.astype(str):
            unused.append(dict(trial_id=trial_id, reason="remainder_below_k",
                               group_key="|".join(map(str, key))))
    bags = pd.DataFrame(records)
    unused_frame = pd.DataFrame(unused)
    if not bags.empty:
        if bags.trial_id.duplicated().any() or bags.groupby("bag_id").trial_id.nunique().lt(k).any():
            raise ValueError("N2_BAG_INTERNAL_DUPLICATE")
    return bags, unused_frame


build_n2_bags = make_n2_bags
construct_bags = make_n2_bags
