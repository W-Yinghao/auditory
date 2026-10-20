import numpy as np
from scipy.special import expit
from auditory_alignment_v3.aln35.history_interface import strict_twin_map, fit_intercept, fit_offset, objective, metrics


def test_strict_twin_never_falls_back_and_respects_source_role():
    history = np.array([0, 0, 0, 1, 2]); blocks = np.array([0, 0, 1, 0, 0])
    mapping = strict_twin_map(history, blocks, np.arange(5), 12)
    assert mapping[0] == 2 and mapping[1] == 2 and mapping[2] in (0, 1)
    assert mapping[3] == mapping[4] == -1
    es_only = strict_twin_map(history, blocks, np.array([0, 1]), 12)
    assert np.all(es_only == -1)


def test_intercept_calibration_matches_source_prevalence_for_constant_prior():
    y = np.array([0.] * 80 + [1.] * 20); off = np.full(100, np.log(.5 / .5))
    intercept, receipt = fit_intercept(y, off)
    assert abs(float(expit(intercept)) - .2) < 1e-10
    assert receipt['optimizer_success'] and receipt['gradient_maxabs_per_source_row'] < 1e-7


def test_offset_objective_gradient_and_source_convergence():
    rng = np.random.default_rng(15); x = rng.normal(size=(100, 3)); y = rng.integers(0, 2, size=100); off = rng.normal(size=100)
    w = rng.normal(size=4); _, grad = objective(w, x, y, off)
    eps = 1e-5
    numeric = np.array([(objective(w + np.eye(4)[i] * eps, x, y, off)[0] - objective(w - np.eye(4)[i] * eps, x, y, off)[0]) / (2 * eps) for i in range(4)])
    assert np.allclose(grad, numeric, atol=1e-7)
    fitted, receipt = fit_offset(x, y, off)
    assert receipt[-1]['optimizer_success'] and receipt[-1]['gradient_maxabs_per_source_row'] <= 1e-7
    assert objective(fitted, x, y, off)[0] <= objective(np.zeros(4), x, y, off)[0]


def test_empty_query_or_unavailable_twin_is_missing_not_zero():
    assert metrics({'B0': np.array([])}, np.array([]))['status'] == 'no_eligible_query_trials'
    v = metrics({'B0': np.array([.5, .5]), 'B1': np.array([.4, .4]), 'EEG': np.array([.3, .7])}, np.array([0, 1]))
    assert v['EEG_minus_strict_twin_logscore_bits'] is None
    assert v['EEG_minus_B0_logscore_bits'] > 0
