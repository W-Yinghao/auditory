"""H-series building blocks: spectral-plus features, joint designs, occlusion mixing, age residualisation."""
import numpy as np
import pytest
import yaml

from auditory_nextmap import h_prep as hp
from auditory_nextmap import h_readout as hr
from auditory_nextmap import representations as rp

H4 = yaml.safe_load(open("configs/auditory_nextmap_h_v1.yaml"))["h4"]


def test_specplus_recovers_exponent_and_alpha_peak():
    f = np.arange(0, 125.5, 0.5)
    f1 = np.where(f == 0, 0.5, f)
    psd = np.vstack([10 ** (2.0 - e * np.log10(f1)) for e in (1.0, 2.0)])
    psd = psd * (1 + 3.0 * np.exp(-0.5 * ((f1 - 9.5) / 1.0) ** 2))      # alpha bump at 9.5 Hz
    out = hp.specplus_from_psd(f, psd, H4)
    assert out.shape == (2, 8)
    assert out[0, 0] == pytest.approx(1.0, abs=0.08) and out[1, 0] == pytest.approx(2.0, abs=0.08)
    assert out[0, 2] == pytest.approx(9.5, abs=0.4) and out[1, 2] == pytest.approx(9.5, abs=0.4)
    assert np.all(out[:, 3:].sum(1) <= 1.0 + 1e-9) and np.all(out[:, 3:] > 0)


def test_welch_mean_averages_windows():
    rng = np.random.default_rng(0)
    w = [rng.normal(size=(3, 2000)) for _ in range(4)]
    f, p = hp.welch_mean(w, 250.0)
    assert p.shape == (3, len(f)) and f[1] - f[0] == pytest.approx(0.5)


def test_joint_design_scales_on_training_rows_only():
    rng = np.random.default_rng(1)
    mu0, mu1, X = rng.normal(size=(20, 5)), rng.normal(size=(20, 5)), rng.normal(size=(20, 3))
    d = hr.joint_design(mu0, mu1, X)
    tr, te = np.arange(15), np.arange(15, 20)
    a_tr, a_te, _ = d(tr, te)
    X2 = X.copy()
    X2[te] += 100
    b_tr, _, _ = hr.joint_design(mu0, mu1, X2)(tr, te)
    assert a_tr.shape == (15, 8) and np.array_equal(a_tr, b_tr)


def test_occlusion_mixing_keeps_training_scaling():
    rng = np.random.default_rng(2)
    m0, m1 = rng.normal(size=(12, 4)), rng.normal(size=(12, 4))
    tr, te = np.arange(9), np.arange(9, 12)
    _, x_int, _ = rp.paired_design("common", m0, m1, tr, te)
    o0, o1 = m0.copy(), m1.copy()
    o0[9:] = 0.0
    o1[9:] = 0.0
    tr_occ, x_occ, _ = rp.paired_design("common", o0, o1, tr, te)
    tr_int, _, _ = rp.paired_design("common", m0, m1, tr, te)
    assert np.array_equal(tr_int, tr_occ) and not np.allclose(x_int, x_occ)


def test_residualise_removes_quadratic_age():
    age = np.linspace(6, 186, 50)
    v = 3 + 0.5 * age - 0.002 * age ** 2
    assert np.max(np.abs(hr._residualise(v, age))) < 1e-8


def test_split_half_reliability_detects_signal():
    from auditory_nextmap import h_extra as hx
    rng = np.random.default_rng(3)
    sig = rng.normal(size=(20, 200))
    x0 = sig[None] + 0.5 * rng.normal(size=(80, 20, 200))
    x1 = sig[None] + 0.5 * rng.normal(size=(80, 20, 200))
    sb, rms = hx._split_half(x0, x1)
    noise0, noise1 = rng.normal(size=(80, 20, 200)), rng.normal(size=(80, 20, 200))
    sb_n, _ = hx._split_half(noise0, noise1)
    assert sb > 0.95 and abs(sb_n) < 0.2 and rms > 0.5


def test_ridge_fast_matches_d2_primal():
    from auditory_d2.ridge_budget import _ridge
    from auditory_nextmap import h_extra as hx
    rng = np.random.default_rng(4)
    for p in (10, 300):
        X, y, Xt = rng.normal(size=(40, p)), rng.normal(size=40), rng.normal(size=(7, p))
        assert np.allclose(hx.ridge_fast(X, y, Xt, 3.0), _ridge(X, y, Xt, 3.0), atol=1e-8)
