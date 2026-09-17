import numpy as np
import pandas as pd

from auditory_next.n2_features import (
    build_bag_features,
    fit_rff16,
    fit_weighted_pca8,
    fit_weighted_scale,
    transform_pca8,
    transform_rff16,
    _history_matrix,
)


def _h_rows(trials):
    n = len(trials)
    def cycle(values):
        return [values[i % len(values)] for i in range(n)]
    return pd.DataFrame({
        "trial_id": trials,
        "previous_code": cycle(["1", "1", "2", None]),
        "previous_run_bin": cycle(["run_1", "run_2", "run_3_5", "unknown"]),
        "previous_gap_s": cycle([1.0, 2.0, np.nan, 4.0]),
        "position_fraction": cycle([0.1, 0.3, 0.7, 0.9]),
        "A_block_id": cycle([0, 1, 1, 2]),
        "onset_sample": cycle([10, 30, 50, 70]),
        "original_fs": [10.0] * n,
    })


def test_weighted_scale_and_pca_are_candidate_equal_and_training_scoped():
    train = np.asarray([[0.0, 0.0], [0.0, 0.0], [10.0, 10.0]])
    fit = fit_weighted_scale(train, ["p0", "p0", "p1"])
    np.testing.assert_allclose(fit["center"], [5.0, 5.0])
    pca = fit_weighted_pca8(train, ["p0", "p0", "p1"], scaler=fit)
    assert pca["n_components"] == 1
    before = pca["components"].copy()
    transform_pca8(np.asarray([[100.0, -2.0]]), pca)
    np.testing.assert_array_equal(before, pca["components"])


def test_rff_bandwidth_is_unlabeled_and_transform_is_fixed():
    x = np.arange(20, dtype=float).reshape(10, 2)
    fit = fit_rff16(x, seed=11, pair_budget=20)
    z1 = transform_rff16(x, fit)
    z2 = transform_rff16(x, fit)
    assert z1.shape == (10, 16)
    np.testing.assert_array_equal(z1, z2)


def test_bag_features_include_mean_unbiased_logvar_controls_and_hbag():
    trials = [f"t{i}" for i in range(8)]
    x = np.arange(16, dtype=float).reshape(8, 2)
    trial_rows = pd.DataFrame({"trial_id": trials})
    bags = pd.DataFrame({
        "bag_id": ["b0"] * 4 + ["b1"] * 4,
        "trial_id": trials,
        "k": [4] * 8,
    })
    features = build_bag_features(x, trial_rows, bags, h_rows=_h_rows(trials),
                                  known_codes=("1", "2"), rff_fit=fit_rff16(x, seed=11))
    assert features["MU"].shape == (2, 2)
    assert features["VAR"].shape == (2, 2)
    assert features["MU_VAR"].shape == (2, 4)
    assert features["MU_DUP"].shape == (2, 4)
    assert features["RFF_MEAN"].shape == (2, 16)
    assert features["H_BAG"].shape[1] == len(features["H_BAG_columns"])
    for column in ("gap_std", "position_std", "block_count", "time_coverage_s"):
        assert column in features["H_BAG_columns"]
    for i in range(2):
        h,names=_history_matrix(_h_rows(trials),trials[i*4:(i+1)*4],known_codes=('1','2'))
        np.testing.assert_allclose(features['H_BAG'][i,:len(names)],np.nanmean(h,axis=0))


def test_k1_variance_is_undefined_and_duplicate_trials_are_rejected():
    trial_rows = pd.DataFrame({"trial_id": ["t0", "t1"]})
    bags = pd.DataFrame({"bag_id": ["b0", "b1"], "trial_id": ["t0", "t1"], "k": [1, 1]})
    result = build_bag_features(np.ones((2, 2)), trial_rows, bags)
    assert not result["variance_defined"].any()
    assert np.isnan(result["VAR"]).all()
    duplicate = pd.DataFrame({"bag_id": ["b0", "b1"], "trial_id": ["t0", "t0"]})
    try:
        build_bag_features(np.ones((2, 2)), trial_rows, duplicate)
    except ValueError as error:
        assert "OVERLAP" in str(error)
    else:
        raise AssertionError("duplicate trial was accepted")
