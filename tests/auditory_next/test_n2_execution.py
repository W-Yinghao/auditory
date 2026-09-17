import numpy as np
import pandas as pd
import pytest

from auditory_next.n2_execution import (
    VIEWS,
    calibrated_logits,
    common_sensitivity_candidates,
    expected_case_count,
    frozen_test_partition_seeds,
    inner_validation_groups,
    paired_bootstrap_gain,
    paired_window_gain,
    _view_matrix,
    evaluation_scores,
    _loss_by_candidate,
)


def test_primary_temperature_never_includes_prior_mixture_and_raw_is_retained():
    logits = np.array([-1000., -1., 1., 1000.])
    calibration = dict(temperature=2., eta=1., training_prior=.2)
    scored = evaluation_scores(logits, calibration)
    assert np.array_equal(scored['raw'], logits)
    assert np.array_equal(scored['temperature'], logits / 2.)
    np.testing.assert_allclose(scored['mixture_diagnostic'], np.log(.2 / .8))
    assert calibration['eta'] == 1.
    with pytest.raises(ValueError, match='CALIBRATION_SCHEMA'):
        calibrated_logits(logits, {**calibration, 'eta': -.1})


def test_bag_candidate_metrics_do_not_require_trial_ids_or_pool_large_candidates():
    rows = pd.DataFrame(dict(bag_id=list('abcdef'), candidate_id=['a','a','b','b','b','b'],
                             stimulus_local_id=[0,1,0,0,1,1]))
    result = _loss_by_candidate(rows, np.zeros(6), 'P_bal').set_index('candidate_id')
    assert list(result.index) == ['a','b']
    assert list(result.n_bags) == [2,4]
    assert np.allclose(result.loss_bits_per_bag, 1.)
    assert np.allclose(result.auroc, .5)
    assert np.allclose(result.brier_two_class_sum, .5)


def test_inner_validation_uses_only_recorded_mapping():
    fold = {"D_inner_fold_by_group": {"g0": 0, "g1": 1, "g2": 0}}
    assert inner_validation_groups(fold, 0, {"g0", "g1"}) == {"g0"}
    assert inner_validation_groups(fold, 2, {"g0", "g1"}) == set()
    assert inner_validation_groups(fold, None, {"g0"}) == set()


def test_expected_case_count_filters_to_frozen_n2_matrix():
    rows = []
    for mode, families in (("R_SIM", ("logistic", "mlp32")), ("L0", ("logistic",))):
        for family in families:
            for view in VIEWS:
                for window in ("post", "pre"):
                    for stage in ("inner", "final"):
                        rows.append(dict(packet="N2", mode=mode, family=family, view=view,
                                         window=window, fit_stage=stage))
    rows.append(dict(packet="N1", mode="R_SIM", family="logistic", view="H",
                     window="paired", fit_stage="final"))
    assert expected_case_count(pd.DataFrame(rows)) == 72
    assert expected_case_count(pd.DataFrame(rows), smoke=True) == 0


def test_partition_seeds_are_frozen_without_refit_semantics():
    assert frozen_test_partition_seeds(n=3, seed=11) == [11, 12, 13]
    assert common_sensitivity_candidates([{"p0", "p1"}, {"p1", "p2"}], {"p0", "p1"}) == {"p1"}


def test_calibration_reuses_frozen_temperature_and_eta():
    logits = np.asarray([-1.0, 0.0, 1.0])
    raw = calibrated_logits(logits, {"temperature": 2.0, "eta": 0.0})
    np.testing.assert_allclose(raw, logits / 2.0)
    mixture = calibrated_logits(logits, {"temperature": 2.0, "eta": 0.5, "training_prior": 0.5})
    assert mixture.shape == logits.shape
    assert np.isfinite(mixture).all()


def test_view_matrix_uses_same_bag_ids_and_expected_controls():
    bag_features = {
        "H_BAG": np.ones((2, 3)),
        "MU": np.ones((2, 2)),
        "MU_VAR": np.ones((2, 4)),
        "MU_DUP": np.ones((2, 4)),
        "VAR": np.ones((2, 2)),
        "RFF_MEAN": np.ones((2, 16)),
    }
    assert all(_view_matrix(bag_features, view).shape[0] == 2 for view in VIEWS)
    assert _view_matrix(bag_features, "HMUVAR").shape[1] == 7
    assert _view_matrix(bag_features, "HMUMU").shape[1] == 7


def test_paired_gain_is_candidate_clustered_and_deterministic():
    losses = pd.DataFrame({
        "candidate_id": ["p0", "p1", "p2"],
        "MU": [1.0, 2.0, 3.0],
        "MV": [0.5, 1.0, 2.0],
        "MM": [0.8, 1.5, 2.5],
    })
    first = paired_bootstrap_gain(losses, "MU", "MV", n_boot=100, seed=11)
    second = paired_bootstrap_gain(losses, "MU", "MV", n_boot=100, seed=11)
    assert first == second
    assert first["n_candidates"] == 3
    assert first["units"] == "bits_per_bag"
    assert paired_bootstrap_gain(losses.iloc[:1], "MU", "MV") is None


def test_post_pre_gain_requires_shared_candidates():
    post = pd.DataFrame({"candidate_id": ["p0", "p1"], "HMU": [2., 3.], "HMUVAR": [1., 1.]})
    pre = pd.DataFrame({"candidate_id": ["p1", "p2"], "HMU": [2., 3.], "HMUVAR": [1., 1.]})
    result = paired_window_gain(post, pre)
    assert result is None
