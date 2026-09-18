from types import SimpleNamespace

import numpy as np
import pytest

from auditory_v3.linear import (WeightedScaler, fit_logistic,
                                logistic_objective_gradient)


def test_normalized_objective_analytic_gradient_and_unpenalized_bias():
    rng = np.random.default_rng(61001)
    X = rng.normal(size=(31, 7))
    y = rng.integers(0, 2, size=len(X))
    weights = np.exp(rng.normal(size=len(X)))
    theta = rng.normal(size=8)
    value, gradient = logistic_objective_gradient(theta, X, y, weights, .1)
    numeric = []
    for j in range(len(theta)):
        step = np.zeros_like(theta)
        step[j] = 1e-6
        plus = logistic_objective_gradient(theta + step, X, y, weights, .1)[0]
        minus = logistic_objective_gradient(theta - step, X, y, weights, .1)[0]
        numeric.append((plus - minus) / 2e-6)
    np.testing.assert_allclose(gradient, numeric, atol=2e-9, rtol=2e-7)
    rescaled = logistic_objective_gradient(theta, X, y, weights * 12345, .1)
    np.testing.assert_allclose(value, rescaled[0], atol=1e-14)
    np.testing.assert_allclose(gradient, rescaled[1], atol=1e-14)
    no_penalty = logistic_objective_gradient(theta, X, y, weights, 0)
    np.testing.assert_allclose(value - no_penalty[0], .05 * np.sum(theta[:-1] ** 2))
    assert gradient[-1] == no_penalty[1][-1]


def test_logistic_native_probabilities_and_fit_diagnostics():
    rng = np.random.default_rng(61002)
    X = rng.normal(size=(200, 4))
    y = (X[:, 0] + rng.normal(size=200) * .3 > 0).astype(int)
    fit = fit_logistic(X, y, np.ones(200), .01, context={"fit_kind": "contract_test"})
    assert fit.success
    assert fit.predict_proba(X).shape == (200,)
    assert fit.diagnostics["final_objective"] <= fit.diagnostics["initial_objective"] + 1e-10
    assert fit.diagnostics["gradient_inf"] <= 1e-4
    assert fit.diagnostics["total_iterations"] <= 2000
    assert np.mean((fit.predict_proba(X) >= .5) == y) > .8


def test_scaler_never_reads_heldout_rows():
    X = np.array([[0., 3.], [2., 3.], [4., 3.]])
    fit = WeightedScaler().fit(X, [1, 2, 1])
    np.testing.assert_allclose(fit.mean_, [2, 3])
    np.testing.assert_allclose(fit.scale_, [np.sqrt(2), 1])
    before = fit.mean_.copy(), fit.scale_.copy()
    fit.transform(np.array([[1e9, -1e9]]))
    np.testing.assert_array_equal(fit.mean_, before[0])
    np.testing.assert_array_equal(fit.scale_, before[1])


def test_recovery_continues_same_state_with_total_iteration_limit(monkeypatch):
    import auditory_v3.linear as module
    calls, events = [], []

    def fake_minimize(function, initial, args, jac, method, options):
        calls.append((initial.copy(), options["maxiter"]))
        if len(calls) == 1:
            return SimpleNamespace(x=np.array([.1, 0.]), nit=1000, success=False, message="iteration limit")
        return SimpleNamespace(x=np.zeros(2), nit=1, success=True, message="continued")

    monkeypatch.setattr(module, "minimize", fake_minimize)
    X = np.zeros((4, 1))
    fit = fit_logistic(X, [0, 1, 0, 1], np.ones(4), .01, ledger=events.append)
    assert fit.success and fit.diagnostics["attempt_count"] == 2
    np.testing.assert_array_equal(calls[1][0], [.1, 0.])
    assert calls[1][1] == 1000
    assert [e["recovery"] for e in events] == [False, True]


def test_nonfinite_fit_cannot_produce_scored_predictions(monkeypatch):
    import auditory_v3.linear as module

    def fake_minimize(*args, **kwargs):
        return SimpleNamespace(x=np.array([np.nan, 0.]), nit=1, success=False, message="nonfinite")

    monkeypatch.setattr(module, "minimize", fake_minimize)
    fit = fit_logistic(np.zeros((4, 1)), [0, 1, 0, 1], np.ones(4), .01, ledger=lambda e: None)
    assert not fit.success
    assert np.isnan(fit.predict_proba(np.zeros((2, 1)))).all()


def test_bad_labels_or_weights_are_hard_failures():
    with pytest.raises(ValueError):
        logistic_objective_gradient([0, 0], [[1], [2]], [0, 2], [1, 1], .01)
    with pytest.raises(ValueError):
        logistic_objective_gradient([0, 0], [[1], [2]], [0, 1], [0, 0], .01)
