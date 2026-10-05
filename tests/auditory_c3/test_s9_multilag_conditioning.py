"""S9 (C3 amendment candidate, docs/auditory_c3/C3_LANDING_PLAN_v1.md §2.1): a long-receptive-field representation L
that carries no information beyond the acoustic variable Ac still shows I(T; L_tau | Ac_tau) > 0 when conditioning on
the same lag only; conditioning on the whole acoustic lag window (or on its ridge prediction) removes it, while a real
extra component W survives all three. Full-size run: private/auditory_c3/p1_synthetic_001/s9_multilag_conditioning.*"""
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "AUDITORY_C3_SERVER_PACKAGE_v1_20261003", "reference"))
from gcmi_core import gcmi_ccc  # noqa: E402

FS, N, TAU = 64, 20000, 6
LAGS = np.arange(-13, 39)
VALID = slice(64, N - 64)


def _ar1(rng, phi, n):
    e = rng.standard_normal(n) * np.sqrt(1 - phi**2)
    x = np.empty(n); x[0] = rng.standard_normal()
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def _smooth2(x, tc):
    a = np.exp(-1.0 / tc)
    y = np.empty_like(x); y[0] = x[0]
    for i in range(1, len(x)):
        y[i] = a * y[i - 1] + (1 - a) * x[i]
    z = np.empty_like(y); z[-1] = y[-1]
    for i in range(len(y) - 2, -1, -1):
        z[i] = a * z[i + 1] + (1 - a) * y[i]
    return z / z.std()


def _ridge_pred(X, y, alpha=1.0, k=5):
    yhat = np.empty_like(y); edges = np.linspace(0, len(y), k + 1).astype(int)
    for a, b in zip(edges[:-1], edges[1:]):
        tr = np.ones(len(y), bool); tr[max(0, a - 64):b + 64] = False
        Xm, ym = X[tr].mean(0), y[tr].mean(); Xt = X[tr] - Xm
        w = np.linalg.solve(Xt.T @ Xt + alpha * np.eye(X.shape[1]), Xt.T @ (y[tr] - ym))
        yhat[a:b] = (X[a:b] - Xm) @ w + ym
    return yhat


def _three(T, L, Ac):
    Lt = np.roll(L, TAU)[VALID]
    W = np.column_stack([np.roll(Ac, k) for k in LAGS])[VALID]
    return (gcmi_ccc(T[VALID], Lt, np.roll(Ac, TAU)[VALID]), gcmi_ccc(T[VALID], Lt, W),
            gcmi_ccc(T[VALID], Lt, _ridge_pred(W, T[VALID])))


def test_single_lag_conditioning_leaks_acoustic_information():
    rng = np.random.default_rng(7)
    Ac = _ar1(rng, 0.9, N)
    sig = np.convolve(Ac, np.sin(np.pi * np.arange(20) / 19))[:N]
    T0 = sig + sig.std() * rng.standard_normal(N)
    L0 = _smooth2(Ac, 0.3 * FS) + 0.3 * rng.standard_normal(N)
    single, multi, mediated = _three(T0, L0, Ac)
    assert single > 0.03          # spurious "linguistic" information under 03 §3.4 as written
    assert abs(multi) < 0.005     # removed by whole-window conditioning
    assert abs(mediated) < 0.005  # removed by the prediction-mediated path
    W = _ar1(rng, 0.9, N)
    T1 = T0 + 0.5 * sig.std() * np.roll(W, TAU)
    s1, m1, d1 = _three(T1, L0 + W, Ac)
    assert min(s1, m1, d1) > 0.05  # a real extra component survives every variant
