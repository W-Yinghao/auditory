"""The FFT/lookup engine (auditory_c3/engine.py) must agree with direct estimation by the package reference
implementation on explicitly lagged arrays (copula over the exact sample set) for every quantity type it serves:
lagged MI, circular-shift surrogates, CMI given a response-aligned mediator, same-lag CMI, mediator-only MI."""
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "AUDITORY_C3_SERVER_PACKAGE_v1_20261003", "reference"))
sys.path.insert(0, REPO)
from gcmi_core import gcmi_cc, gcmi_ccc  # noqa: E402
from auditory_c3.engine import Subject, ridge_loto  # noqa: E402

FS, G = 64, 64
LAGS = np.arange(-10, 41)
TOL = 0.004


def _ar(rng, d, n, phi=0.9):
    x = np.zeros((d, n)); e = rng.standard_normal((d, n)) * np.sqrt(1 - phi**2)
    for i in range(1, n):
        x[:, i] = phi * x[:, i - 1] + e[:, i]
    return x


def _data(seed=1):
    rng = np.random.default_rng(seed)
    trials = []
    for n in (6000, 7100, 6550):
        A = _ar(rng, 2, n); W = _ar(rng, 2, n)
        k = np.exp(-np.arange(-20, 21) ** 2 / 50.0); k /= k.sum()
        L = np.vstack([np.convolve(A[i], k, "same") for i in range(2)]) + W
        h = np.sin(np.pi * np.arange(16) / 15)
        T = np.vstack([np.convolve(A[0], h)[:n] + 0.4 * np.roll(W[1], 8), np.convolve(A[1], h)[:n]]) + rng.standard_normal((2, n))
        yhat = np.vstack([np.convolve(A[0], h)[:n], np.convolve(A[1], h)[:n]]) + 0.3 * rng.standard_normal((2, n))
        trials.append({"T": T, "valid": (G, n - G), "stim": {"A": A, "L": L}, "yhat": yhat})
    return trials


def _direct(trials, tau, shifts=None, kind="mi"):
    Ts, As, Ls, Ys = [], [], [], []
    for i, t in enumerate(trials):
        a, b = t["valid"]; n = t["T"].shape[1]
        s = 0 if shifts is None else shifts[i]
        idx = np.arange(a, b)
        src = (idx - tau - s) % n
        Ts.append(t["T"][:, idx]); As.append(t["stim"]["A"][:, src]); Ls.append(t["stim"]["L"][:, src])
        Ys.append(t["yhat"][:, (idx - s) % n])
    T, A, L, Y = (np.concatenate(v, axis=1).T for v in (Ts, As, Ls, Ys))
    if kind == "mi":
        return gcmi_cc(T, A)
    if kind == "cmi_med":
        return gcmi_ccc(T, L, Y)
    if kind == "cmi_stim":
        return gcmi_ccc(T, L, A)
    if kind == "mi_med":
        return gcmi_cc(T, Y)


def _subject(trials):
    S = Subject([{k: t[k] for k in ("T", "valid", "stim")} for t in trials], FS, LAGS, n_sur=5, seed=3)
    S.add_mediator("yhat", [t["yhat"] for t in trials])
    return S


def test_lagged_mi_and_surrogates_match_direct():
    tr = _data(); S = _subject(tr)
    E = S.mi("A")
    for li in (0, 10, 18, 30, 50):
        assert abs(E[0, li] - _direct(tr, LAGS[li])) < TOL
    for b in (1, 4):
        sh = [t["shifts"][b] for t in S.trials]
        assert abs(E[b, 18] - _direct(tr, LAGS[18], sh)) < TOL


def test_cmi_given_mediator_matches_direct():
    tr = _data(2); S = _subject(tr)
    E = S.cmi("L", cond_meds=("yhat",))
    for li in (5, 18, 40):
        assert abs(E[0, li] - _direct(tr, LAGS[li], kind="cmi_med")) < TOL
    sh = [t["shifts"][2] for t in S.trials]
    assert abs(E[2, 18] - _direct(tr, LAGS[18], sh, kind="cmi_med")) < TOL


def test_same_lag_cmi_matches_direct():
    tr = _data(3); S = _subject(tr)
    E = S.cmi("L", cond_stims=("A",))
    for li in (10, 18, 35):
        assert abs(E[0, li] - _direct(tr, LAGS[li], kind="cmi_stim")) < TOL


def test_mediator_mi_matches_direct():
    from auditory_c3.engine import ent_from_cov
    tr = _data(4); S = _subject(tr)
    C, off = S.med_cov(("yhat",))
    N = S.N
    i_obs = ent_from_cov(C[:, :2, :2], N) + ent_from_cov(C[:, 2:, 2:], N) - ent_from_cov(C, N)
    assert abs(i_obs[0] - _direct(tr, 0, kind="mi_med")) < TOL
    sh = [t["shifts"][3] for t in S.trials]
    assert abs(i_obs[3] - _direct(tr, 0, sh, kind="mi_med")) < TOL


def test_ridge_loto_predicts_out_of_trial():
    tr = _data(5)
    P, a, r = ridge_loto([t["stim"]["A"] for t in tr], [t["T"] for t in tr], np.arange(0, 20), [1e-3, 1e-1, 10.0])
    assert r > 0.3 and len(P) == 3 and P[0].shape == tr[0]["T"].shape
