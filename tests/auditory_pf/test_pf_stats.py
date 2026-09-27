import numpy as np
import pytest
from scipy.optimize import check_grad
from sklearn.metrics import roc_auc_score

from auditory_pf import stats as st
from auditory_pf.cohort import deal
from auditory_pf.runtime import stable_int


def test_auc_matches_sklearn_with_ties():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 300)
    s = np.round(rng.normal(size=300) + 0.3 * y, 1)
    assert abs(st.auc(y, s) - roc_auc_score(y, s)) < 1e-12
    assert np.isnan(st.auc(np.zeros(5), np.arange(5)))


def test_perm_p_and_cliff():
    assert st.perm_p(1.0, [0.0] * 99) == pytest.approx(0.01)
    assert st.cliff_delta([2, 3], [0, 1]) == 1.0
    assert st.cliff_delta([0, 1], [0, 1]) == 0.0


def test_ordinal_gradient_and_recovery():
    rng = np.random.default_rng(1)
    n, p = 400, 3
    X = rng.normal(size=(n, p))
    beta = np.array([1.5, -1.0, 0.0])
    theta = np.array([-2.0, -0.5, 0.7, 2.0])
    eta = X @ beta
    u = rng.logistic(size=n)
    y = 1 + np.sum((eta + u)[:, None] > theta[None, :], axis=1)
    m = st.OrdinalLogistic(lam=0.01)
    # gradient check through the internal objective
    w0 = rng.normal(size=p + 4) * 0.1
    Xc = X.copy()

    def f(w):
        mm = st.OrdinalLogistic(0.01)
        beta_, theta_ = mm._unpack(w, p)
        eta_ = Xc @ beta_
        th = np.concatenate([[-np.inf], theta_, [np.inf]])
        from scipy.special import expit
        prob = np.clip(expit(th[y] - eta_) - expit(th[y - 1] - eta_), 1e-12, None)
        return -np.log(prob).sum() + 0.01 * beta_ @ beta_

    m.fit(X, y)
    assert m.converged
    assert np.allclose(m.beta, beta, atol=0.35)
    e = m.expected(X)
    assert e.min() >= 1 and e.max() <= 5
    assert np.corrcoef(e, y)[0, 1] > 0.5
    # numerical gradient of the fitted objective is ~0 at the optimum
    w_opt = np.concatenate([m.beta, [m.theta[0]], np.log(np.expm1(np.diff(m.theta) - 1e-4))])
    from scipy.optimize import approx_fprime
    g = approx_fprime(w_opt, f, 1e-6)
    assert np.max(np.abs(g)) < 0.5


def test_query_test_null_calibration():
    rng = np.random.default_rng(2)
    ps = []
    for _ in range(200):
        y = rng.integers(0, 2, 120)
        s = rng.normal(size=120)
        _, p = st.query_block_test(y, s, 1, 500, rng)
        ps.append(p)
    assert 0.02 < np.mean(np.array(ps) < 0.05) < 0.10


def test_blocks_guard():
    from auditory_pf.analysis_b1 import blocks_of
    cfg = {"blocks": {"block_seconds": 60, "guard_seconds": 5}}
    on = np.array([0.0, 4.0, 5.3, 30.0, 54.3, 55.0, 60.0, 65.3, 119.0])
    blk, keep = blocks_of(on, cfg)
    assert blk.tolist() == [0, 0, 0, 0, 0, 0, 1, 1, 1]
    assert keep.tolist() == [False, False, True, True, True, False, False, True, False]


def test_deal_balanced_and_complete():
    groups = {i: ("labelled" if i < 57 else "nh" if i < 66 else "unlabelled") for i in range(73)}
    out = deal(list(groups), groups, 5, np.random.default_rng(101))
    assert sorted(out) == list(range(73))
    sizes = np.bincount(list(out.values()), minlength=5)
    assert sizes.max() - sizes.min() <= 3
    lab = np.bincount([out[i] for i in range(57)], minlength=5)
    assert lab.max() - lab.min() <= 1


def test_stable_int_deterministic():
    assert stable_int("a", 1) == stable_int("a", 1)
    assert stable_int("a", 1) != stable_int("a", 2)


def test_spline_fallback_many_zeros():
    from auditory_pf.analysis_b1 import _spline
    v = np.log1p(np.array([0] * 11 + [1, 1, 3, 5, 12, 13, 20, 36, 40, 60, 90, 120], float))
    f = _spline(v)
    B = f(v)
    assert B.shape[0] == len(v) and np.isfinite(B).all()


def test_logistic_and_ordinal_cv_run():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(45, 50))
    y = (X[:, 0] + rng.normal(size=45) > 0).astype(int)
    f, info = st.logistic_cv(X, y, [0.01, 0.1, 1.0])
    assert np.isfinite(f(X)).all() and info["C"] in (0.01, 0.1, 1.0)
    ys = np.clip(np.round(3 + X[:, 0] + rng.normal(size=45) * 0.5), 1, 5).astype(int)
    fl, fe, inf = st.ordinal_cv(X, ys, [0.1, 1.0, 10.0])
    assert np.isfinite(fe(X)).all()
