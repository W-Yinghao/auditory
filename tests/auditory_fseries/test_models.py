import copy
import numpy as np
import pytest
from auditory_fseries.models import clinical_block, evaluate_fold, fit_predict, make_splits, paired_interval


def small_config():
    return dict(validation=dict(seed=143, outer_folds=4, inner_folds=2,
        clinical_families=['linear', 'quadratic'], clinical_alphas=[1.], eeg_alphas=[1.],
        target_prediction_bounds=[0., 100.]), models=['C_LINEAR', 'C_BEST', 'C_Z', 'C_Q', 'C_Q_Z', 'C_SHUFFLED_Z'])


def synthetic():
    rng = np.random.default_rng(192)
    C = rng.normal(size=(64, 2)); Q = rng.normal(size=(64, 2)); Z = rng.normal(size=(64, 3))
    y = 50 + 7 * Z[:, 0] + 2 * C[:, 0] + rng.normal(scale=.1, size=64)
    return C, Q, Z, y


def test_training_only_imputation_and_expansion():
    train = np.array([[1., np.nan], [2., np.nan], [3., np.nan]])
    test = np.array([[100., 999.], [np.nan, np.nan]])
    a, b, state = clinical_block(train, test, quadratic=True)
    aa, _, state_again = clinical_block(train, test * 1e9, quadratic=True)
    assert np.allclose(a, aa)
    assert state == state_again and state['imputation'] == [2., 0.]
    assert np.isfinite(a).all() and np.isfinite(b).all()


def test_no_inner_or_outer_identity_overlap():
    groups = np.array([f'synthetic_{i}' for i in range(32)])
    splits = make_splits(groups, small_config())
    assert sorted(i for _, test, _ in splits for i in test) == list(range(32))
    for train, test, inner in splits:
        assert not set(train) & set(test)
        assert sorted(i for _, val in inner for i in val) == sorted(train)
        assert all(not set(a) & set(b) and not (set(a) | set(b)) & set(test) for a, b in inner)
    with pytest.raises(ValueError, match='ONE_RECORD'):
        make_splits(np.array(['same'] * 32), small_config())


def test_outer_labels_cannot_change_selected_models_or_predictions():
    C, Q, Z, y = synthetic(); cfg = small_config()
    train, test, inner = make_splits(np.arange(len(y)).astype(str), cfg)[0]
    first = evaluate_fold(C, Q, Z, y, train, test, inner, cfg)
    altered = y.copy(); altered[test] += 10000
    second = evaluate_fold(C, Q, Z, altered, train, test, inner, cfg)
    for name in cfg['models']:
        assert first[name]['selected'] == second[name]['selected']
        assert np.array_equal(first[name]['prediction'], second[name]['prediction'])


def test_known_EEG_signal_improves_and_content_control_degrades():
    C, Q, Z, y = synthetic(); cfg = small_config()
    train, test, inner = make_splits(np.arange(len(y)).astype(str), cfg)[0]
    result = evaluate_fold(C, Q, Z, y, train, test, inner, cfg)
    risk = {k: np.abs(v['prediction'] - y[test]).mean() for k, v in result.items()}
    assert risk['C_Z'] < 1. and risk['C_Z'] < .25 * risk['C_BEST']
    assert risk['C_SHUFFLED_Z'] > risk['C_Z'] + 2.


def test_zero_EEG_has_no_added_value_and_clinical_candidate_is_retained():
    C, Q, Z, y = synthetic(); Z[:] = 0; cfg = small_config()
    train, test, inner = make_splits(np.arange(len(y)).astype(str), cfg)[0]
    result = evaluate_fold(C, Q, Z, y, train, test, inner, cfg)
    assert np.allclose(result['C_Z']['prediction'], result['C_BEST']['prediction'], atol=1e-10)
    assert np.allclose(result['C_Q_Z']['prediction'], result['C_Q']['prediction'], atol=1e-10)


def test_nonfinite_EEG_cannot_yield_partial_success():
    C, Q, Z, y = synthetic(); Z[0, 0] = np.nan
    with pytest.raises(ValueError, match='NONFINITE_EEG'):
        fit_predict(C, Q, Z, y, np.arange(32), np.arange(32, 64), ('linear', 1., 1., False, False), 31, [0., 100.])


def test_paired_fixed_prediction_interval_sign_and_roundoff():
    folds = np.repeat(np.arange(4), 3)
    positive = paired_interval(np.full(12, 2.), folds, 200, 1)
    zero = paired_interval(np.full(12, 1e-14), folds, 200, 1)
    assert positive['gain_MAE'] == 2. and positive['ci_low'] == 2.
    assert zero['gain_MAE'] == zero['ci_low'] == zero['ci_high'] == 0.
