import numpy as np
import pandas as pd
import pytest

from auditory_v3.statistics import (hierarchical_weights, paired_contrasts,
    per_row_log_loss, stratified_identity_bootstrap, weighted_metrics)


def _population():
    rows = []
    for group in range(6):
        for half in (0, 1):
            for cell in range(1 + half):
                for label in (0, 1):
                    for obs in range(1 + group + label):
                        rows.append(dict(split_group_id=f"s{group}", A_half=half,
                            previous_code=cell, previous_run_bin="one", stimulus_local_id=label,
                            outer_fold=group % 3, observation=obs))
    return pd.DataFrame(rows)


def test_all_hierarchical_levels_have_equal_parent_mass():
    frame = _population()
    frame["w"] = hierarchical_weights(frame)
    np.testing.assert_allclose(frame.groupby("split_group_id").w.sum(), 1 / 6)
    np.testing.assert_allclose(frame.groupby(["split_group_id", "A_half"]).w.sum(), 1 / 12)
    for _, part in frame.groupby(["split_group_id", "A_half"]):
        cells = part.groupby(["previous_code", "previous_run_bin"]).w.sum()
        np.testing.assert_allclose(cells, part.w.sum() / len(cells))
    for _, part in frame.groupby(["split_group_id", "A_half", "previous_code", "previous_run_bin"]):
        np.testing.assert_allclose(part.groupby("stimulus_local_id").w.sum(), part.w.sum() / 2)


def test_missing_history_is_explicit_and_missing_class_is_rejected():
    frame = _population()
    frame["previous_code"] = np.nan
    assert np.isclose(hierarchical_weights(frame).sum(), 1)
    with pytest.raises(ValueError):
        hierarchical_weights(frame[frame.stimulus_local_id == 0])


def test_hand_ce_negative_J_and_missing_values():
    np.testing.assert_allclose(per_row_log_loss([0, 1], [.25, .75]), -np.log2(.75))
    metrics = weighted_metrics([0, 1], [.9, .1], [1, 1])
    assert metrics["J_bits"] < 0
    assert weighted_metrics([0, 1], [.5, np.nan], [1, 1])["ce_bits"] is None
    assert np.isinf(per_row_log_loss([1], [0]))[0]


def test_paired_zero_and_duplicate_observations_do_not_increase_identity_N():
    frame = _population()
    frame["p"] = .2 + frame.stimulus_local_id * .6
    first, identities = paired_contrasts(frame, {"ref": "p", "candidate": "p"}, {"gain": ("ref", "candidate")})
    assert first["contrasts"]["gain"]["gain_bits"] == 0
    assert first["contrasts"]["gain"]["ci_low"] == first["contrasts"]["gain"]["ci_high"] == 0
    assert first["n_groups"] == len(identities) == 6
    duplicated = pd.concat([frame, frame], ignore_index=True)
    second, _ = paired_contrasts(duplicated, {"ref": "p", "candidate": "p"}, {"gain": ("ref", "candidate")})
    assert second["n_groups"] == 6
    np.testing.assert_allclose(first["metrics"]["ref"]["ce_bits"], second["metrics"]["ref"]["ce_bits"])


def test_bootstrap_fold_stratification_shared_draws_and_no_success_only_average():
    ids = pd.DataFrame({"split_group_id": [f"s{i}" for i in range(6)],
                        "outer_fold": [0, 0, 1, 1, 2, 2],
                        "gain": [-1., 1., 2., 4., 7., 9.],
                        "fold_constant": [0., 0., 10., 10., 20., 20.]})
    ids["double"] = ids.gain * 2
    ids["incomplete"] = ids.gain
    ids.loc[0, "incomplete"] = np.nan
    result = stratified_identity_bootstrap(ids, ["gain", "double", "fold_constant", "incomplete"])
    np.testing.assert_allclose(result["double"]["ci_low"], 2 * result["gain"]["ci_low"])
    np.testing.assert_allclose(result["double"]["ci_high"], 2 * result["gain"]["ci_high"])
    assert result["fold_constant"]["ci_low"] == result["fold_constant"]["ci_high"] == 10
    assert result["incomplete"]["gain_bits"] is None
    assert result["incomplete"]["n_groups"] == 6
