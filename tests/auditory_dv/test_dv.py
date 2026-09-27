import numpy as np
import pytest

from auditory_dv import analyze as an
from auditory_dv import audit as au


def test_observer_predictive_probabilities():
    seq = np.array([0] * 20 + [1] + [0] * 5 + [1])
    p = an.observer_p(seq, 20)
    assert p[0] == pytest.approx(0.5)
    assert np.all((p > 0) & (p < 1))
    assert p[21] > p[20]            # after a deviant the predicted deviant probability rises
    assert p[20] < 0.1              # after 20 standards it is low


def test_first_float_and_num():
    assert an._first_float("左 45dB / 右 50") == 45.0
    assert np.isnan(an._first_float("无"))
    assert au._num("35 dB") and not au._num(None) and not au._num("nan")


def test_norm_and_unionfind_and_categories():
    assert au._norm("/a/b/Rec_01.mff/") == "rec_01"
    uf = au._UF()
    uf.union("a", "b"); uf.union("b", "c")
    assert uf.find("a") == uf.find("c") and uf.find("d") != uf.find("a")
    assert au._cat_counts('{"Standard": 80, "Deviant": 20}') == {"standard": 80, "deviant": 20}


def test_mastoid_operator():
    eye = np.eye(128)
    mast = eye.copy(); mast[:, 56] -= 0.5; mast[:, 99] -= 0.5
    x = np.random.default_rng(0).normal(size=(128, 50))
    assert np.allclose(mast @ x, x - x[[56, 99]].mean(0))


def test_bias_corrected_gaps_remove_regression_to_mean():
    rng = np.random.default_rng(1)
    age = rng.uniform(10, 150, 60)
    # a shrunk predictor: pred = 0.5*age + const + noise -> uncorrected gap correlates with age
    X = np.column_stack([age + rng.normal(0, 25, 60), rng.normal(size=(60, 3))])
    kids = list(range(60)); a = dict(zip(kids, age))
    folds = {1: {c: c % 5 for c in kids}}
    feats = {"event": lambda s, k, c: X[c], "spectral": lambda s, k, c: X[c], "joint": lambda s, k, c: X[c]}
    pred, gaps = an.age_models({}, folds, kids, feats, a, [1.0, 10.0, 100.0], bias_correct=True)
    g = np.array([gaps["event"][1][c] for c in kids]); raw = np.array([pred["event"][1][c] - a[c] for c in kids])
    assert abs(np.corrcoef(g, age)[0, 1]) < abs(np.corrcoef(raw, age)[0, 1])


def test_g_block_runs_on_synthetic():
    rng = np.random.default_rng(2)
    n = 3000
    child = np.repeat(np.arange(30), 100)
    y = (rng.random(n) < 0.2).astype(int)
    s = y * 0.3 + rng.normal(size=n)
    p = np.clip(0.2 + rng.normal(0, 0.05, n), 0.01, 0.99)
    prev = np.roll(y, 1); run = rng.integers(0, 6, n)
    out = an.analyze_g_block(s, y, p, prev, run, child)
    assert np.isfinite(out["delta_bits"]) and out["children"] == 30


def test_claims_minimal():
    r = {"A1": {"event_minus_spectral": {"mean": -3.0}, "spectral_minus_joint": {"mean": 5.0}},
         "A3": {"partial_spearman_amr_logdur_given_age": 0.05, "perm_p_one_sided": 0.4}}
    C = an.claims(r)
    assert C["A1"]["status"] == "成立" and C["A3"]["status"] == "推翻"
