import numpy as np
import pandas as pd
import pytest

from auditory5.preprocessing import HA_CHANNELS, ImpulseSupport
from auditory5.routes.route_a_controls import (
    assert_trial_mask_alignment,
    balanced_control_indices,
    block_ranges,
    reset_filter_epochs,
    reset_block_mask,
    _same_rows,
)


def _balanced_rows(group="g0"):
    rows = []
    trial = 0
    # Six history×position cells per half/class, with enough block support.
    for half in (0, 1):
        for cls in (0, 1):
            for history in (0, 1):
                for position in (0, 1, 2):
                    for repeat in range(4):
                        rows.append(dict(
                            trial_id=f"t{trial}", split_group_id=group,
                            A_half=half, stimulus_local_id=cls,
                            A_boundary_eligible=True, history_target=history,
                            segment_position_fraction=(position + .2) / 3,
                            A_block_id=repeat, accepted=True))
                        trial += 1
    return pd.DataFrame(rows)


def test_block_ranges_use_original_sample_grid_and_half_open_intervals():
    assert block_ranges(2500, 250, 4.0) == [(0, 0, 1000), (1, 1000, 2000), (2, 2000, 2500)]
    with pytest.raises(ValueError, match="BLOCK_GRID"):
        block_ranges(100, 3, .1)


def test_reset_mask_requires_epoch_and_startup_guard_inside_one_block():
    result = reset_block_mask([100, 700, 990], 1000, 100, 5,
                              startup_guard_seconds=1, end_embargo_seconds=.5)
    assert result.reset_eligible.tolist() == [False, True, False]
    assert result.reset_block_id.tolist() == [0, 1, 1]


@pytest.mark.parametrize("original_fs", [250.0, 1000.0])
def test_reset_epochs_keep_fixed_ha20_and_native_post_grid(original_fs):
    """The reset path must reject aux channels and retain the .05 s grid."""
    n_samples = int(120 * original_fs)
    raw_names = ("A1",) + tuple(HA_CHANNELS) + ("A2", "Status")
    raw = np.zeros((len(raw_names), n_samples), dtype=np.float64)
    raw[0] = 1e6
    raw[-2] = -1e6
    raw[-1] = 999
    events = pd.DataFrame({
        "trial_id": ["t0", "t1"],
        "onset_sample": [int(30 * original_fs), int(90 * original_fs)],
        "event_kind": ["target", "target"],
        "stimulus_local_id": [0, 1],
    })
    support = ImpulseSupport(
        original_fs=original_fs, tolerance=1e-6, support_samples=1,
        support_seconds=1 / original_fs, guard_samples=int(20 * original_fs),
        guard_seconds=20.0, impulse_length_samples=2,
        impulse_length_seconds=2 / original_fs, absolute_sum=1.0,
        absolute_tail_fraction=0.0, terminal_half_fraction=0.0,
    )
    result = reset_filter_epochs(raw, original_fs, raw_names, events, 60.0,
                                 support, end_embargo_seconds=10.823)
    assert result.ledger.reset_eligible.tolist() == [True, True]
    assert result.pre.shape == (2, 20, 50)
    assert result.post.shape == (2, 20, 100)
    assert result.ledger.reset_pre_stop_index.tolist() == [50, 50]
    assert set(result.ledger.reset_post_start_index) <= {62, 63}
    assert set(result.ledger.reset_post_stop_index) <= {162, 163}
    assert np.all(result.ledger.reset_post_stop_index.to_numpy()
                  - result.ledger.reset_post_start_index.to_numpy() == 100)
    assert result.ledger.reset_filter_segment_id.tolist() == ["reset_block_0000", "reset_block_0001"]


def test_balanced_selection_is_deterministic_and_equal_by_history_position():
    rows = _balanced_rows()
    first = balanced_control_indices(rows, "g0", budget=12)
    second = balanced_control_indices(rows, "g0", budget=12)
    np.testing.assert_array_equal(first, second)
    selected = rows.iloc[first]
    assert len(selected) == 48  # 12 per half/class, four half/class cells
    assert selected.groupby(["A_half", "stimulus_local_id", "history_target",
                             selected.segment_position_fraction.mul(3).astype(int)]).size().eq(2).all()


def test_balanced_selection_returns_none_when_a_required_cell_lacks_support():
    rows = _balanced_rows()
    rows = rows[~((rows.A_half == 1) & (rows.stimulus_local_id == 1) &
                  (rows.history_target == 1) &
                  (rows.segment_position_fraction > .66))].reset_index(drop=True)
    assert balanced_control_indices(rows, "g0", budget=12) is None


def test_alignment_preserves_original_rejection_mask_and_trial_ids():
    reference = pd.DataFrame(dict(trial_id=["a", "b"], stimulus_local_id=[0, 1],
                                  split_group_id=["g", "g"], accepted=[True, False]))
    control = reference.assign(reset_eligible=[True, False])
    assert_trial_mask_alignment(reference, control)
    changed = control.copy()
    changed.loc[1, "accepted"] = True
    with pytest.raises(ValueError, match="rejection mask"):
        assert_trial_mask_alignment(reference, changed)

def test_unlabelled_numpy_index_retains_trial_column_name_and_order():
    frame=pd.DataFrame({'trial_id':['a','b'],'accepted':[True,False]})
    aligned=_same_rows(frame,np.array(['b','a']))
    assert aligned.trial_id.tolist()==['b','a']
    assert aligned.accepted.tolist()==[False,True]
