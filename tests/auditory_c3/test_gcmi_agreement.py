"""P1 (07 §7.1): production GCMI (Ince, vendored f14aae8) must agree with the package reference implementation
(reference/gcmi_core.py) to < 1e-6 bits on synthetic data before the production estimator may be used."""
import os
import sys

import numpy as np
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "AUDITORY_C3_SERVER_PACKAGE_v1_20261003", "reference"))
sys.path.insert(0, REPO)
import gcmi_core as ref  # noqa: E402
from auditory_c3.vendor import gcmi_ince as ince  # noqa: E402

TOL = 1e-6
rng = np.random.default_rng(20261004)


def _pair(n, dx, dy, rho):
    z = rng.standard_normal((n, max(dx, dy)))
    x = z[:, :dx] + rng.standard_normal((n, dx))
    y = rho * z[:, :dy] + rng.standard_normal((n, dy))
    return np.exp(x), y**3  # monotone distortions: copula estimators must not care


@pytest.mark.parametrize("n", [200, 1000, 5000])
@pytest.mark.parametrize("dx,dy", [(1, 1), (3, 1), (5, 3), (8, 1), (5, 5)])
def test_gcmi_cc(n, dx, dy):
    x, y = _pair(n, dx, dy, 0.7)
    assert abs(ref.gcmi_cc(x, y) - ince.gcmi_cc(x.T, y.T)) < TOL


@pytest.mark.parametrize("n", [500, 5000])
@pytest.mark.parametrize("dx,dy,dz", [(1, 1, 1), (3, 5, 5), (1, 5, 13)])
def test_gccmi_ccc(n, dx, dy, dz):
    z = rng.standard_normal((n, dz))
    x = z[:, :1] @ np.ones((1, dx)) + rng.standard_normal((n, dx))
    y = z[:, :1] @ np.ones((1, dy)) + rng.standard_normal((n, dy))
    assert abs(ref.gcmi_ccc(x, y, z) - ince.gccmi_ccc(x.T, y.T, z.T)) < TOL


@pytest.mark.parametrize("n", [400, 4000])
@pytest.mark.parametrize("k", [2, 4])
def test_gcmi_model_cd(n, k):
    y = rng.permutation(np.arange(n) % k)  # balanced, no rare classes (reference collapses classes < 20)
    x = y[:, None] * 0.4 + rng.standard_normal((n, 3))
    assert abs(ref.gcmi_model_cd(x, y) - ince.gcmi_model_cd(x.T, y, k)) < TOL


@pytest.mark.parametrize("n", [300, 3000])
def test_raw_gaussian_entropy_and_mi(n):
    x = rng.standard_normal((n, 4)); y = x[:, :2] + rng.standard_normal((n, 2))
    for bc in (True, False):
        assert abs(ref.ent_g(x, bc) - ince.ent_g(x.T, bc)) < TOL
        assert abs(ref.mi_gg(x, y, bc) - ince.mi_gg(x.T, y.T, bc)) < TOL
        assert abs(ref.cmi_ggg(x[:, :1], y, x[:, 1:], bc) - ince.cmi_ggg(x[:, :1].T, y.T, x[:, 1:].T, bc)) < TOL


def test_copnorm_identical():
    x = rng.exponential(size=(1000, 3))
    assert np.max(np.abs(ref.copnorm(x) - ince.copnorm(x.T).T)) < 1e-12
