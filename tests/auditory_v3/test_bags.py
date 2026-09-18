import numpy as np
import pandas as pd
import pytest

from auditory_v3.bags_packet import (
    H_COLUMNS,
    aggregate_bag_statistics,
    bag_history_array,
    make_n2r_views,
    quadratic_mean,
    validate_member_schema,
)


def _members(n_bags=2):
    rows = []
    for bag in range(n_bags):
        for member in range(8):
            rows.append({
                "bag_id": f"b{bag}", "matched_pair_id": f"p{bag}",
                "trial_id": f"t{bag}_{member}", "candidate_id": f"c{bag}",
                "split_group_id": f"g{bag}", "record_id": f"r{bag}",
                "segment_id": f"s{bag}", "stimulus_local_id": bag % 2,
                "A_half": "A", "A_block_id": f"ab{bag}",
                "physical_block_id": f"pb{bag}_{member // 4}",
                "previous_code": 1, "previous_run_bin": 1, "k": 8,
                **{column: float(column_index + bag)
                   for column_index, column in enumerate(H_COLUMNS)},
            })
    return pd.DataFrame(rows)


def test_member_contract_and_bag_sample_variance():
    members = _members()
    validated = validate_member_schema(members)
    assert len(validated) == 16
    post = np.arange(16 * 400, dtype=float).reshape(16, 400)
    pre = np.arange(16 * 200, dtype=float).reshape(16, 200)
    stats = aggregate_bag_statistics(members, post, pre)
    assert stats.n_bags == 2
    np.testing.assert_allclose(stats.post_var[0, 0], np.var(post[:8, 0], ddof=1))
    assert stats.h.shape == (2, 16)


def test_fixed_quadratic_and_view_dimensions():
    members = _members()
    stats = aggregate_bag_statistics(
        members, np.ones((16, 8)), np.ones((16, 8)),
    )
    assert quadratic_mean(np.ones((2, 8))).shape == (2, 44)
    full = aggregate_bag_statistics(members, np.ones((16,400)),np.ones((16,200)))
    views = make_n2r_views(stats,include_full=True,full_stats=full)
    assert tuple(views) == (
        "H", "HM", "HMV", "HQ", "HQV", "HQQ", "HPRE", "HPREQ", "HPREQV",
        "FULL_MU", "FULL_MU_VAR",
    )
    assert {name: value.shape[1] for name, value in views.items()} == {
        "H": 16, "HM": 24, "HMV": 32, "HQ": 60, "HQV": 68,
        "HQQ": 104, "HPRE": 68, "HPREQ": 112, "HPREQV": 120,
        "FULL_MU": 400, "FULL_MU_VAR": 800,
    }


def test_schema_rejects_trial_reuse_and_bad_blocking():
    members = _members()
    members.loc[1, "trial_id"] = members.loc[0, "trial_id"]
    with pytest.raises(ValueError, match="DUPLICATE_TRIAL_ID"):
        validate_member_schema(members)
    members = _members()
    members.loc[members.index[:8], "physical_block_id"] = "only_one"
    with pytest.raises(ValueError, match="BAG_NEEDS_TWO_PHYSICAL_BLOCKS"):
        validate_member_schema(members)


def test_bag_history_is_aligned_once_per_bag():
    members = _members()
    history = members[["bag_id", *H_COLUMNS]].drop_duplicates("bag_id").iloc[::-1].reset_index(drop=True)
    aligned = bag_history_array(members, history)
    assert aligned.shape == (len(members), len(H_COLUMNS))
    np.testing.assert_array_equal(aligned[:8], np.broadcast_to(aligned[0],(8,16)))
    with pytest.raises(ValueError, match="BAG_HISTORY_COVERAGE"):
        bag_history_array(members, history.iloc[:-1])
