import numpy as np
import pytest
from scipy.special import expit
from types import SimpleNamespace
from auditory_alignment_v3.aln34 import calibration_retry as C


def original_failure(*args, **kwargs):
    raise RuntimeError('Calibration optimizer did not converge: ABNORMAL: ')


def test_successful_original_fit_is_unchanged():
    x = np.linspace(-2, 2, 80); y = np.tile([0., 1., 0., 1.], 20)
    expected = C.Legacy.fit(x, y).to_dict()
    C.FIT_EVENTS.clear()
    assert C.AffineLogitCalibrator.fit(x, y).to_dict() == expected
    assert C.FIT_EVENTS == [{'solver': 'original', 'fallback': False}]


def test_boundary_recovery_preserves_positive_slope_and_weighted_prior(monkeypatch):
    x = np.linspace(-2, 2, 100); y = (x < 0).astype(float)
    w = np.linspace(.1, 2, len(x))
    monkeypatch.setattr(C.Legacy, 'fit', original_failure)
    C.FIT_EVENTS.clear()
    fit = C.AffineLogitCalibrator.fit(x, y, sample_weight=w)
    assert fit.slope == pytest.approx(1e-8, abs=1e-12)
    assert np.mean(fit.predict(x)) == pytest.approx(np.average(y, weights=w), abs=1e-5)
    assert C.FIT_EVENTS[0]['fallback'] and C.FIT_EVENTS[0]['projected_gradient_inf'] <= 1e-7


def test_unconverged_retry_cannot_be_reported_as_success(monkeypatch):
    monkeypatch.setattr(C.Legacy, 'fit', original_failure)
    monkeypatch.setattr(C, 'minimize', lambda *a, **k: SimpleNamespace(success=True, x=np.array([1., 20.]), message='fake success', nit=1))
    with pytest.raises(RuntimeError, match='recovery failed'):
        C.AffineLogitCalibrator.fit([-1., 1., 2.], [0., 1., 0.])


def test_invalid_inputs_never_enter_recovery():
    with pytest.raises(ValueError): C.AffineLogitCalibrator.fit([1., 2.], [0., 0.])
    with pytest.raises(ValueError): C.AffineLogitCalibrator.fit([1., float('nan')], [0., 1.])
