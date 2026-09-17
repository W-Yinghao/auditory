import pandas as pd
import pytest

from auditory_next.donors import select_donors
from auditory_next.history import build_h_v2, history_feature_columns
from auditory_next.n2_bags import make_n2_bags


def _events():
    return pd.DataFrame([
        dict(trial_id="e0", record_id="r", segment_id="s", onset_sample=0,
             event_literal="1", event_kind="target", sequence_start_complete=True),
        dict(trial_id="e1", record_id="r", segment_id="s", onset_sample=100,
             event_literal="1", event_kind="target"),
        dict(trial_id="e2", record_id="r", segment_id="s", onset_sample=200,
             event_literal="1", event_kind="target"),
        dict(trial_id="u", record_id="r", segment_id="s", onset_sample=300,
             event_literal="x", event_kind="unknown_sound"),
        dict(trial_id="e3", record_id="r", segment_id="s", onset_sample=400,
             event_literal="2", event_kind="target"),
    ]).fillna({"sequence_start_complete": False})


def test_history_is_pre_qc_and_run_two_is_not_old_b_excluded():
    events = _events()
    history = build_h_v2(events, original_fs=100.0, known_codes=("1", "2"))
    assert history.trial_id.tolist() == events.trial_id.tolist()
    assert history.loc[history.trial_id == "e2", "previous_run_length"].item() == 2
    assert history.loc[history.trial_id == "e2", "history_status"].item() == "complete"
    assert history.loc[history.trial_id == "e2", "previous_gap_s"].item() == pytest.approx(1.0)
    assert history.loc[history.trial_id == "e3", "history_status"].item() == "unknown"
    assert history.loc[history.trial_id == "e3", "history_reset_reason"].item() == "unknown_sound"


def test_current_label_mutation_does_not_change_h_features():
    events = _events()
    altered = events.copy()
    altered.loc[altered.trial_id == "e2", "event_literal"] = "2"
    a = build_h_v2(events, original_fs=100.0, known_codes=("1", "2"))
    b = build_h_v2(altered, original_fs=100.0, known_codes=("1", "2"))
    feature_columns = [c for c in a.columns if c.startswith("previous_") or c.startswith("position_")]
    keep = a.trial_id.isin(["e0", "e1", "e2"])
    pd.testing.assert_frame_equal(a.loc[keep, feature_columns].reset_index(drop=True),
                                  b.loc[keep, feature_columns].reset_index(drop=True))


def test_history_layout_is_explicit_and_run_bins_are_safe_features():
    events = _events().assign(layout_category="ha20")
    history = build_h_v2(events, original_fs=100.0, known_codes=("1", "2"),
                          layout_columns=("layout_category",))
    assert "layout_layout_category" in history
    features = history_feature_columns(history)
    assert "previous_run_run_2" in features
    assert "current_run_length" not in features


def _bag_rows():
    rows = []
    number = 0
    for cls in (0, 1):
        for half in (0, 1):
            for block in (0, 1, 2):
                for _ in range(4):
                    rows.append(dict(trial_id=f"t{number}", candidate_id="p0", record_id="r0",
                                     segment_id="s0",
                                     split_group_id="g0", stimulus_local_id=cls,
                                     A_half=half, A_boundary_eligible=True,
                                     A_block_id=block))
                    number += 1
    return pd.DataFrame(rows)


def test_n2_bags_are_fixed_same_class_half_unique_and_block_bounded():
    bags, unused = make_n2_bags(_bag_rows(), k=4, seed=11)
    assert not bags.empty
    assert not bags.trial_id.duplicated().any()
    assert bags.groupby("bag_id").trial_id.nunique().eq(4).all()
    assert bags.groupby("bag_id")[["record_id", "stimulus_local_id", "A_half"]].nunique().max().max() == 1
    assert bags.physical_block_id.map(lambda value: isinstance(value, str)).all()
    assert bags.groupby("bag_id").bag_block_count.min().ge(2).all()
    assert bags.groupby("bag_id").apply(
        lambda x: x.groupby("A_block_id").size().max() <= 2).all()
    assert bags.groupby(["A_half", "stimulus_local_id"]).bag_id.nunique().ge(2).all()


def test_n2_k1_declares_variance_undefined_and_rejects_duplicate_trial():
    rows = _bag_rows()
    bags, _ = make_n2_bags(rows, k=1, seed=11)
    assert not bags.empty
    assert not bags.variance_defined.any()
    duplicate = pd.concat([rows, rows.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="DUPLICATE"):
        make_n2_bags(duplicate, k=4)


def _donor_row(trial, candidate, record, start, end, *, training=False,
               onset=None, split_group="g", segment="s"):
    return dict(trial_id=trial, candidate_id=candidate, record_id=record,
                segment_id=segment, onset_sample=(start if onset is None else onset),
                split_group_id=split_group, previous_code="1", previous_run_bin="run_2",
                previous_gap_s=1.0, layout_id="ha20", raw_dependency_start=start,
                raw_dependency_end=end, is_training=training)


def test_donor_selection_uses_past_context_and_rejects_dependency_overlap():
    query = pd.DataFrame([_donor_row("q", "p1", "r1", 100, 110, onset=200)])
    pool = pd.DataFrame([
        _donor_row("overlap", "p1", "r1", 105, 115, onset=150),
        _donor_row("legal", "p1", "r1", 120, 130, onset=100),
    ])
    links, alternatives = select_donors(query, pool, role="same_child_remote", seed=3)
    assert links.donor_trial_id.item() == "legal"
    assert links.n_candidates.item() == 1
    assert alternatives.donor_trial_id.tolist() == ["legal"]
    altered = query.assign(stimulus_local_id=1)
    altered_links, _ = select_donors(altered, pool, role="same_child_remote", seed=3)
    assert altered_links.donor_trial_id.item() == "legal"


def test_cross_record_same_numeric_dependency_times_are_legal():
    query = pd.DataFrame([_donor_row("q", "p1", "r1", 10, 20, onset=100)])
    pool = pd.DataFrame([_donor_row("remote", "p1", "r2", 10, 20, onset=1)])
    links, _ = select_donors(query, pool, role="same_child_remote")
    assert links.donor_trial_id.item() == "remote"


def test_training_donor_requires_explicit_training_pool_flag_and_different_person():
    query = pd.DataFrame([_donor_row("q", "p1", "r1", 10, 20, split_group="g1")])
    pool = pd.DataFrame([_donor_row("d", "p2", "r2", 30, 40, training=True, split_group="g2")])
    links, _ = select_donors(query, pool, role="training_remote")
    assert links.donor_trial_id.item() == "d"
