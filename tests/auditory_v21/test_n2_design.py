import pandas as pd

from auditory_v21.n2_design import (
    H_BAG_COLUMNS,
    construct_matched_bags,
    build_h_bag_metadata,
    metadata_ablation_plan,
)


def _history(class_cells=("run_1", "run_1"), *, n_per_class=16):
    rows = []
    for cls in (0, 1):
        for i in range(n_per_class):
            trial = f"c{cls}_{i}"
            rows.append({
                "trial_id": trial, "candidate_id": "cand0", "record_id": "rec0",
                "segment_id": "seg0", "split_group_id": "group0",
                "stimulus_local_id": cls, "accepted": True, "A_half": 0,
                "A_block_id": i % 4, "onset_sample": i + cls * 100,
                "previous_event_id": None, "previous_code": "1",
                "previous_run_bin": class_cells[cls], "previous_gap_s": 1.0,
                "position_fraction": (i % 8) / 8, "onset_seconds_relative": float(i),
                "original_fs": 10.0,
            })
    return pd.DataFrame(rows)


def test_common_cell_design_is_deterministic_paired_and_without_replacement():
    history = _history()
    first = construct_matched_bags(history)
    second = construct_matched_bags(history)
    pd.testing.assert_frame_equal(first["matched_bags"], second["matched_bags"])
    detail = first["candidate_detail"]
    eligible = detail.loc[(detail.candidate_id == "cand0") & (detail.A_half == 0)].iloc[0]
    assert bool(eligible.eligible)
    assert int(eligible.matched_pair_bags) == 2
    bags = first["matched_bags"]
    assert len(bags) == 32
    assert bags.trial_id.is_unique
    assert bags.groupby("matched_pair_id").stimulus_local_id.nunique().eq(2).all()
    assert bags.groupby("bag_id").size().eq(8).all()
    assert bags.groupby("bag_id").A_block_id.nunique().ge(2).all()
    assert bags.groupby(["bag_id", "A_block_id"]).size().le(4).all()


def test_sparse_common_cell_is_fixed_exclusion_without_effect_based_cell_selection():
    history = _history()
    extra = _history(n_per_class=1)
    extra["trial_id"] = [f"weak_{i}" for i in range(2)]
    extra["previous_run_bin"] = "run_2"
    history = pd.concat([history, extra], ignore_index=True)
    result = construct_matched_bags(history)
    detail = result["candidate_detail"].loc[lambda frame: (frame.candidate_id == "cand0") & (frame.A_half == 0)].iloc[0]
    assert int(detail.common_cell_count) == 2
    assert bool(detail.common_cells_all_paired)
    assert int(detail.sparse_common_cell_excluded_count) == 1
    assert int(detail.matched_pair_bags) == 2
    assert not result["matched_bags"].empty
    assert result["aggregate"]["old_imbalance_does_not_rule_out_new_balanced_design"] is True


def test_no_common_cell_is_observational_support_limit_only():
    history = _history(class_cells=("run_1", "run_2"))
    result = construct_matched_bags(history)
    assert result["aggregate"]["candidate_half_common_cell_denominator"] == 0
    assert result["aggregate"]["support_status"] == "OBSERVATIONAL_SUPPORT_LIMITED"
    assert result["aggregate"]["old_imbalance_does_not_rule_out_new_balanced_design"] is True


def test_metadata_ablation_plan_has_exact_five_by_five_catalog_and_hbag_shape():
    folds = [{"outer_fold": i, "train_groups": [], "test_groups": []} for i in range(5)]
    planned = metadata_ablation_plan(folds)
    assert planned["aggregate"]["head_count"] == 25
    assert planned["aggregate"]["fits_executed"] == 0
    assert planned["aggregate"]["h_bag_column_count"] == len(H_BAG_COLUMNS) == 16
    assert planned["aggregate"]["mu_dimension_required"] == 8
    assert planned["aggregate"]["var_dimension_required"] == 8
    metadata = build_h_bag_metadata(
        construct_matched_bags(_history())["matched_bags"], _history()
    )
    assert set(H_BAG_COLUMNS).issubset(metadata.columns)
    assert len(metadata) == 4
