import numpy as np
import pandas as pd
import pytest

from auditory_next.temporal import freeze_temporal_roles


def _events(duration=300., dep=1.):
    rows = []
    for block in range(1, 10):
        for cls in (0, 1):
            for j in range(20):
                onset = block * 30 + 1 + j * .01
                rows.append(dict(record_id="r", split_group_id="g", trial_id=f"t{block}_{cls}_{j}",
                                 stimulus_local_id=cls, accepted=True, time_block_id=block,
                                 onset_seconds_relative=onset, raw_dependency_start=onset-dep/2,
                                 raw_dependency_end=onset+dep/2))
    return pd.DataFrame(rows)


def test_roles_are_contiguous_60_40_physical_blocks_and_support():
    roles, support = freeze_temporal_roles(_events(), pd.DataFrame([{"record_id": "r", "n_samples": 75000, "original_fs": 250.}]))
    assert set(roles.temporal_role) == {"calibration", "test"}
    assert set(roles.loc[roles.temporal_role == "calibration", "physical_block_id"]) == {1, 2, 3, 4, 5}
    assert set(roles.loc[roles.temporal_role == "test", "physical_block_id"]) == {6, 7, 8, 9}
    assert bool(support.iloc[0].valid) and bool(support.iloc[0].conservative_group_valid)


def test_dependency_crossing_boundary_is_excluded_and_no_random_split():
    events = _events(); events.loc[events.trial_id == "t6_0_0", "raw_dependency_start"] = 149.0
    roles, _ = freeze_temporal_roles(events, pd.DataFrame([{"record_id": "r", "n_samples": 75000, "original_fs": 250.}]))
    assert "t6_0_0" not in set(roles.trial_id)
    assert roles.groupby("temporal_role").physical_block_id.nunique().to_dict() == {"calibration": 5, "test": 4}


def test_metadata_sampling_rate_changes_duration_and_partial_tail_rejected():
    e = _events()
    with pytest.raises(ValueError):
        freeze_temporal_roles(e, pd.DataFrame([{"record_id": "r", "n_samples": 75000, "original_fs": 0.}]))
    e = pd.concat([e, pd.DataFrame([dict(record_id="r", split_group_id="g", trial_id="partial", stimulus_local_id=0,
        accepted=True, time_block_id=10, onset_seconds_relative=301., raw_dependency_start=300., raw_dependency_end=302.)])], ignore_index=True)
    roles, support = freeze_temporal_roles(e, pd.DataFrame([{"record_id": "r", "n_samples": 76000, "original_fs": 250.}]))
    assert "partial" not in set(roles.trial_id)
    assert 9 in set(roles.physical_block_id)


def test_original_sampling_rate_is_used_for_duration():
    roles, support = freeze_temporal_roles(_events(), pd.DataFrame([{"record_id": "r", "n_samples": 150000, "original_fs": 500.}]))
    assert support.iloc[0].n_blocks == 10
    assert roles.physical_block_id.max() == 9


def test_internal_same_role_block_crossing_is_legal_and_unknown_labels_are_ignored():
    e = _events()
    e.loc[e.trial_id == "t2_0_0", ["raw_dependency_start", "raw_dependency_end"]] = [58.0, 62.0]
    e = pd.concat([e, pd.DataFrame([dict(record_id="r", split_group_id="g", trial_id="unknown", stimulus_local_id=-1,
        accepted=True, time_block_id=2, onset_seconds_relative=61., raw_dependency_start=60., raw_dependency_end=62.)])], ignore_index=True)
    roles, support = freeze_temporal_roles(e, pd.DataFrame([{"record_id": "r", "n_samples": 75000, "original_fs": 250.}]))
    assert "t2_0_0" in set(roles.trial_id) and "unknown" not in set(roles.trial_id)
    assert bool(support.iloc[0].valid)


def test_guard_over_one_block_changes_first_complete_block():
    roles, _ = freeze_temporal_roles(_events(), pd.DataFrame([{"record_id": "r", "n_samples": 75000, "original_fs": 250., "startup_guard_seconds": 61.}]))
    assert roles.physical_block_id.min() == 3
