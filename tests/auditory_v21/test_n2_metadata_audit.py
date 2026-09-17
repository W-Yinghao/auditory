import numpy as np
import pandas as pd

from auditory_v21.n2_metadata_audit import (
    audit_common_history_support,
    audit_member_history,
    audit_saved_bags,
    h_bag_column_trace,
)


def _history(rows):
    return pd.DataFrame(rows, columns=[
        "trial_id", "candidate_id", "record_id", "segment_id", "split_group_id",
        "stimulus_local_id", "accepted", "A_half", "A_block_id", "onset_sample",
        "previous_event_id", "previous_code", "previous_run_bin",
    ])


def _bags(groups, *, k=8):
    rows = []
    for bag_id, (candidate, record, segment, cls, half, trial_ids, blocks) in enumerate(groups):
        for trial_id, block in zip(trial_ids, blocks):
            rows.append({
                "bag_id": f"b{bag_id}", "trial_id": trial_id,
                "candidate_id": candidate, "record_id": record, "segment_id": segment,
                "stimulus_local_id": cls, "A_half": half, "split_group_id": "g0",
                "A_block_id": block, "k": k,
            })
    return pd.DataFrame(rows)


def test_history_relation_walk_keeps_rejected_events_and_distinguishes_direct_from_earlier():
    rows = []
    # t0 and t2 are members of the same bag.  A rejected event and an
    # accepted event sit between them in the complete saved chain.
    rows.append(["t0", "c0", "r0", "s0", "g0", 0, True, 0, 0, 0, None, None, "unknown"])
    rows.append(["rej", "c0", "r0", "s0", "g0", 0, False, 0, 0, 1, "t0", "1", "run_1"])
    rows.append(["t1", "c0", "r0", "s0", "g0", 0, True, 0, 1, 2, "rej", "1", "run_1"])
    rows.append(["t2", "c0", "r0", "s0", "g0", 0, True, 0, 2, 3, "t1", "1", "run_2"])
    for i in range(3, 8):
        rows.append([f"t{i}", "c0", "r0", "s0", "g0", 0, True, 0, i % 4, i + 1, f"t{i-1}", "1", "run_2"])
    for i in range(8):
        rows.append([f"u{i}", "c0", "r0", "s0", "g0", 1, True, 0, i % 4, 20 + i, None, "2", "run_1"])
    history = _history(rows)
    bags = _bags([("c0", "r0", "s0", 0, 0, [f"t{i}" for i in range(8)], [0, 1, 2, 3, 0, 1, 2, 3])])

    result = audit_member_history(bags, history)
    detail = result["relations"].set_index("trial_id")
    assert bool(detail.loc["t2", "any_earlier_member"])
    assert bool(detail.loc["t2", "direct_previous_member"])
    assert not bool(detail.loc["t1", "direct_previous_member"])
    assert bool(detail.loc["t1", "any_earlier_member"])
    assert bool(detail.loc["t1", "has_rejected_earlier_event"])
    assert result["aggregate"]["n_members_any_earlier_member"] >= 1
    assert result["aggregate"]["history_chain_uses_rejected_events"] is True


def test_exact_common_cells_are_conservative_and_marginals_are_descriptive():
    groups = []
    history_rows = []
    for cls, run_bin in ((0, "run_1"), (1, "run_2")):
        for ordinal in range(2):
            trial_ids = [f"t{cls}_{ordinal}_{i}" for i in range(8)]
            blocks = [0, 1, 2, 3, 0, 1, 2, 3]
            groups.append(("c0", "r0", "s0", cls, 0, trial_ids, blocks))
            for i, (trial_id, block) in enumerate(zip(trial_ids, blocks)):
                history_rows.append([
                    trial_id, "c0", "r0", "s0", "g0", cls, True, 0, block, ordinal * 20 + i,
                    None, "1", run_bin,
                ])
    bags = _bags(groups)
    history = _history(history_rows)
    result = audit_common_history_support(bags, history, min_bags_per_class_half=2)
    aggregate = result["aggregate"]
    assert aggregate["candidate_half_denominator"] == 1
    assert aggregate["candidate_half_design_eligible_denominator"] == 1
    assert aggregate["candidate_half_design_exact_common_numerator"] == 0
    assert aggregate["candidate_half_code_marginal_common_numerator"] == 1
    assert aggregate["candidate_half_run_marginal_common_numerator"] == 0
    assert aggregate["coarse_marginals_descriptive_only"] is True
    assert aggregate["posthoc_cell_selection"] is False


def test_saved_bag_audit_reports_k8_and_original_multi_block_violations():
    groups = [
        ("c0", "r0", "s0", 0, 0, [f"a{i}" for i in range(8)], [0, 0, 0, 0, 0, 1, 1, 1]),
        ("c0", "r0", "s0", 1, 0, [f"b{i}" for i in range(8)], [0, 1, 2, 3, 0, 1, 2, 3]),
    ]
    history_rows = []
    for _, (candidate, record, segment, cls, half, trial_ids, blocks) in enumerate(groups):
        for i, (trial_id, block) in enumerate(zip(trial_ids, blocks)):
            history_rows.append([
                trial_id, candidate, record, segment, "g0", cls, True, half, block, i,
                None, "1", "run_1",
            ])
    result = audit_saved_bags(_bags(groups), _history(history_rows), min_bags_per_group=1)
    assert result["aggregate"]["n_bags_denominator"] == 2
    assert result["aggregate"]["n_bags_bad_multi_block"] == 1
    assert result["aggregate"]["n_bags_bad_k"] == 0


def test_h_bag_trace_is_fixed_and_contains_timing_and_history_sources():
    trace = h_bag_column_trace()
    columns = {item["column"] for item in trace}
    assert "previous_code_1_proportion" in columns
    assert "previous_run_run_3_5_proportion" in columns
    assert "gap_mean" in columns
    assert "time_coverage_s" in columns
    assert all("EEG" not in item["source"] for item in trace)
