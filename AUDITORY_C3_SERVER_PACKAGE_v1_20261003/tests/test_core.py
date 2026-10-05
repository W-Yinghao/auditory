"""pytest tests for reference/gcmi_core.py — all must pass before G1."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reference"))
from gcmi_core import gcmi_cc, gcmi_ccc, gcmi_model_cd, cmi_model_gdd, pid_mmi, tmif, copnorm

rng = np.random.default_rng(7)


def test_copnorm_is_standard_normal_marginal():
    x = rng.exponential(size=(5000, 2))
    z = copnorm(x)
    assert abs(z.mean()) < 0.05 and abs(z.std() - 1) < 0.05


def test_analytic_gaussian_mi():
    rho, n = 0.5, 20000
    a = rng.standard_normal(n)
    b = rho * a + np.sqrt(1 - rho**2) * rng.standard_normal(n)
    assert abs(gcmi_cc(a, b) - (-0.5 * np.log2(1 - rho**2))) < 0.01


def test_monotone_invariance():
    a = rng.standard_normal(5000); b = 0.6 * a + 0.8 * rng.standard_normal(5000)
    assert abs(gcmi_cc(a, b) - gcmi_cc(np.exp(a), b**3)) < 1e-9


def test_cmi_common_cause_zero():
    n = 20000
    z = rng.standard_normal(n); x = z + 0.7 * rng.standard_normal(n); y = z + 0.7 * rng.standard_normal(n)
    assert gcmi_cc(x, y) > 0.3 and abs(gcmi_ccc(x, y, z)) < 0.01


def test_independent_is_near_zero_after_bias_correction():
    for d in (1, 5, 8):
        x = rng.standard_normal((500, d)); y = rng.standard_normal(500)
        assert abs(gcmi_cc(x, y)) < 0.02


def test_discrete_mi_and_cmi():
    n = 6000
    cur = (rng.random(n) < 0.2).astype(int)
    logit = cur + rng.standard_normal(n)
    assert gcmi_model_cd(logit, cur) > 0.05
    hist = rng.integers(0, 4, n)  # independent history
    assert abs(cmi_model_gdd(logit, hist, cur)) < 0.01


def test_pid_mmi_identities():
    p = pid_mmi(0.4, 0.3, 0.9)
    assert abs(p["U_A"] + p["R"] - 0.4) < 1e-12 and abs(p["U_B"] + p["R"] - 0.3) < 1e-12
    assert abs(sum(p.values()) - 0.9) < 1e-12 and min(p["U_A"], p["U_B"]) == 0.0


def test_tmif_peaks_at_true_lag():
    phi, n, lag_true = 0.9, 30000, 12
    s = np.empty(n); s[0] = 0
    for i in range(1, n):
        s[i] = phi * s[i - 1] + np.sqrt(1 - phi**2) * rng.standard_normal()
    r = np.roll(s, lag_true) + 0.5 * rng.standard_normal(n)
    lags = list(range(0, 25))
    assert lags[int(np.argmax(tmif(s, r, lags)))] == lag_true
