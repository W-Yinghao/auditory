"""Outcome-blind temporal-role freezing for auditory_next v2."""

from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_EVENTS = {"record_id", "split_group_id", "trial_id", "stimulus_local_id",
                   "accepted", "time_block_id", "onset_seconds_relative",
                   "raw_dependency_start", "raw_dependency_end"}


def freeze_temporal_roles(events: pd.DataFrame, record_metadata: pd.DataFrame, *, guard_seconds: float = 20.0):
    """Assign deterministic calibration/test roles using physical complete blocks.

    The boundary is derived from timestamps and metadata, never from observed
    EEG or labels.  Rows are retained only when their complete raw dependency
    interval lies within the assigned temporal role, including internal blocks.
    """
    if not isinstance(events, pd.DataFrame) or not isinstance(record_metadata, pd.DataFrame):
        raise TypeError("events and record_metadata must be dataframes")
    missing = REQUIRED_EVENTS - set(events.columns)
    if missing or not {"record_id", "n_samples", "original_fs"}.issubset(record_metadata.columns):
        raise ValueError("TEMPORAL_SCHEMA")
    if not record_metadata.record_id.is_unique or not events.trial_id.is_unique:
        raise ValueError("TEMPORAL_KEYS_NOT_UNIQUE")
    if not np.isfinite(guard_seconds) or guard_seconds < 0:
        raise ValueError("invalid guard_seconds")
    md = record_metadata.set_index("record_id")
    roles, supports = [], []
    for rid, frame in events.groupby("record_id", sort=False):
        if rid not in md.index:
            raise ValueError("MISSING_RECORD_METADATA")
        meta = md.loc[rid]
        fs, ns = float(meta["original_fs"]), int(meta["n_samples"])
        if not np.isfinite(fs) or fs <= 0 or ns <= 0:
            raise ValueError("INVALID_RECORD_METADATA")
        duration = ns / fs
        if frame.split_group_id.astype(str).nunique()!=1:
            raise ValueError('RECORD_HAS_MULTIPLE_SPLIT_GROUPS')
        guard = float(meta.get("startup_guard_seconds", guard_seconds))
        if not np.isfinite(guard) or guard < 0:
            raise ValueError("INVALID_RECORD_GUARD")
        n_blocks = int(np.floor(duration / 30.0))
        block_ids = list(range(int(np.ceil(guard / 30.0)), n_blocks))
        if len(block_ids) < 2:
            supports.append({"record_id": rid, "split_group_id": str(frame.iloc[0].split_group_id),
                             "n_blocks": n_blocks, "available_complete_blocks":len(block_ids), "valid": False, "reason": "TOO_FEW_BLOCKS"})
            continue
        cal_n = int(np.floor(.6 * len(block_ids)))
        cal_ids, test_ids = block_ids[:cal_n], block_ids[cal_n:]
        boundary = (test_ids[0] * 30.0) if test_ids else duration
        last_complete_end = (block_ids[-1] + 1) * 30.0
        groups_in_record = frame.split_group_id.astype(str).unique()
        if len(groups_in_record) != 1:
            raise ValueError("RECORD_HAS_MULTIPLE_SPLIT_GROUPS")
        eligible = frame.loc[frame["accepted"].astype(bool) & frame["stimulus_local_id"].isin([0, 1])].copy()
        if eligible.empty:
            supports.append({"record_id": rid, "split_group_id": str(frame.iloc[0].split_group_id),
                             "n_blocks": n_blocks, "available_complete_blocks":len(block_ids), "valid": False, "reason": "NO_ACCEPTED_EVENTS"})
            continue
        if not np.isfinite(eligible[["onset_seconds_relative", "raw_dependency_start", "raw_dependency_end"]].to_numpy(float)).all():
            raise ValueError("NONFINITE_TEMPORAL_FIELDS")
        if (eligible.raw_dependency_end < eligible.raw_dependency_start).any():
            raise ValueError("REVERSED_RAW_DEPENDENCY")
        assigned = []
        for _, row in eligible.iterrows():
            onset = float(row.onset_seconds_relative); start = float(row.raw_dependency_start); end = float(row.raw_dependency_end)
            block = int(np.floor(onset / 30.0))
            if block not in block_ids:
                continue
            if block in cal_ids and start >= 0.0 and end <= boundary:
                role = "calibration"
            elif block in test_ids and start >= boundary and end <= last_complete_end:
                role = "test"
            else:
                continue
            item = row.to_dict(); item.update({"temporal_role": role, "physical_block_id": block,
                                               "boundary_seconds": boundary,
                                               "numerical_dependency_isolation": True,
                                               "selection_isolation": False})
            assigned.append(item)
        out = pd.DataFrame(assigned)
        if out.empty:
            valid = False; reason = "NO_ROLE_ROWS"
        else:
            required_classes = (0,1)
            counts = out.groupby(["temporal_role", "stimulus_local_id"]).size().to_dict()
            blocks = out.groupby(["temporal_role", "physical_block_id"]).size().groupby(level=0).size().to_dict()
            valid = len(required_classes) >= 2 and all(counts.get((role, cls), 0) >= 20 for role in ("calibration", "test") for cls in required_classes) and all(blocks.get(role, 0) >= 3 for role in ("calibration", "test"))
            reason = "PASS" if valid else "SUPPORT_INSUFFICIENT"
            roles.extend(assigned)
        supports.append({"record_id": rid, "split_group_id": str(frame.iloc[0].split_group_id),
                         "n_blocks": n_blocks, "available_complete_blocks":len(block_ids), "calibration_blocks": len(cal_ids),
                         "test_blocks": len(test_ids), "boundary_seconds": boundary,
                         "n_calibration": int(sum(x.get("temporal_role") == "calibration" for x in assigned)),
                         "n_test": int(sum(x.get("temporal_role") == "test" for x in assigned)),
                         "valid": bool(valid), "reason": reason})
    roles_df = pd.DataFrame(roles)
    support_df = pd.DataFrame(supports)
    if not support_df.empty:
        group_ok = support_df.groupby("split_group_id")["valid"].transform("all")
        support_df["conservative_group_valid"] = group_ok.astype(bool)
    return roles_df, support_df
