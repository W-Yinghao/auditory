"""Contract tests T1-T5 and T9-T12 of the execution spec (section 11) for the A0 / C0 code paths."""
import itertools

import numpy as np
import pytest
from sklearn.linear_model import Ridge

from auditory_nextmap import age_core as ac
from auditory_nextmap import age_readout as ar
from auditory_nextmap import headroom as hr
from auditory_nextmap import representations as rp
from auditory_nextmap.runtime import ProvenanceError


def _pair_data(n=40, p=30, seed=0):
    rng = np.random.default_rng(seed)
    mu0 = rng.normal(size=(n, p))
    mu1 = mu0 + rng.normal(scale=0.3, size=(n, p)) + 0.2
    return mu0, mu1, rng.normal(size=n) * 30 + 80


# ---------------------------------------------------------------------- T3 rotation and ridge equivalence

@pytest.mark.parametrize("p", [30, 120])            # primal (p <= n) and dual (p > n) solvers
def test_t3_pair_and_joint_are_equivalent(p):
    mu0, mu1, y = _pair_data(p=p)
    tr, te = np.arange(30), np.arange(30, 40)
    Xj_tr, Xj_te, _ = rp.paired_design("joint", mu0, mu1, tr, te)
    Xp_tr, Xp_te, _ = rp.paired_design("pair", mu0, mu1, tr, te)
    assert np.allclose((Xj_tr ** 2).sum(1), (Xp_tr ** 2).sum(1), rtol=1e-12)
    for alpha in (1.0, 100.0, 1e4):
        mj, mp = ar.ridge_fit(Xj_tr, y[tr], alpha), ar.ridge_fit(Xp_tr, y[tr], alpha)
        pj, pp = ar.ridge_predict(mj, Xj_te), ar.ridge_predict(mp, Xp_te)
        assert np.max(np.abs(pj - pp)) / np.max(np.abs(pj)) <= 1e-8
        assert abs(mj["diag"]["objective_sse_l2"] - mp["diag"]["objective_sse_l2"]) <= 1e-8 * mj["diag"]["objective_sse_l2"]


def test_block_scaled_views_change_geometry_on_purpose():
    mu0, mu1, y = _pair_data()
    tr, te = np.arange(30), np.arange(30, 40)
    Xb_tr, Xb_te, _ = rp.paired_design("joint_bs", mu0, mu1, tr, te)
    Xp_tr, Xp_te, _ = rp.paired_design("pair", mu0, mu1, tr, te)
    pb = ar.ridge_predict(ar.ridge_fit(Xb_tr, y[tr], 100.0), Xb_te)
    pp = ar.ridge_predict(ar.ridge_fit(Xp_tr, y[tr], 100.0), Xp_te)
    assert np.max(np.abs(pb - pp)) > 1e-6


def test_paired_scale_is_shared_and_training_only():
    mu0, mu1, _ = _pair_data()
    tr, te = np.arange(30), np.arange(30, 40)
    s_tr, _, _ = rp.paired_design("std", mu0, mu1, tr, te)
    d_tr, _, _ = rp.paired_design("dev", mu0, mu1, tr, te)
    m, s, _ = rp.paired_scale_fit(mu0[tr], mu1[tr], 1e-8)
    assert np.allclose(s_tr, (mu0[tr] - m) / s) and np.allclose(d_tr, (mu1[tr] - m) / s)
    mu0b, mu1b = mu0.copy(), mu1.copy()
    mu0b[te] += 1000.0                                        # test rows must not move the training design
    s_tr2, _, _ = rp.paired_design("std", mu0b, mu1b, tr, te)
    assert np.array_equal(s_tr, s_tr2)


# ---------------------------------------------------------------------- T4 SSE vs MSE scale

def test_t4_sse_and_mse_objectives_agree_only_with_alpha_over_n():
    rng = np.random.default_rng(1)
    X, y = rng.normal(size=(50, 8)), rng.normal(size=50)
    Xt = rng.normal(size=(10, 8))
    p_sse = ar.ridge_predict(ar.ridge_fit(X, y, 50.0), Xt)
    p_mse = ar.ridge_predict(ar.ridge_fit_mse(X, y, 50.0 / 50), Xt)
    p_wrong = ar.ridge_predict(ar.ridge_fit_mse(X, y, 50.0), Xt)     # the K0 error: SSE alpha fed to an MSE objective
    p_skl = Ridge(alpha=50.0).fit(X, y).predict(Xt)                 # sklearn Ridge is the SSE form
    assert np.allclose(p_sse, p_mse, atol=1e-10) and np.allclose(p_sse, p_skl, atol=1e-10)
    assert np.max(np.abs(p_sse - p_wrong)) > 1e-3


def test_dual_solver_matches_sklearn():
    rng = np.random.default_rng(2)
    X, y = rng.normal(size=(20, 60)), rng.normal(size=20)
    Xt = rng.normal(size=(5, 60))
    m = ar.ridge_fit(X, y, 3.0)
    assert m["form"] == "dual"
    assert np.allclose(ar.ridge_predict(m, Xt), Ridge(alpha=3.0).fit(X, y).predict(Xt), atol=1e-9)


def test_kernel_ridge_centering():
    rng = np.random.default_rng(3)
    X, y = rng.normal(size=(30, 5)), rng.normal(size=30)
    m = ar.kernel_fit(X, y, 1.0)
    D = ((X[:, None] - X[None]) ** 2).sum(-1)
    K = np.exp(-m["gamma"] * D)
    H = np.eye(30) - 1 / 30
    Kc = H @ K @ H
    a = np.linalg.solve(Kc + np.eye(30), y - y.mean())
    assert np.allclose(ar.kernel_predict(m, X), y.mean() + Kc @ a, atol=1e-9)
    off = D[~np.eye(30, dtype=bool)]
    assert m["gamma"] == pytest.approx(1 / np.median(off[off > 1e-12]))


def test_alpha_ties_go_to_larger_and_failures_are_explicit():
    assert ar.choose_alpha({1.0: 5.0, 100.0: 5.0, 1e4: 6.0}, 1e-12) == 100.0
    assert ar.choose_alpha({1.0: np.nan, 100.0: 7.0, 1e4: 6.0}, 1e-12) == 1e4
    with pytest.raises(ar.FitFailure):
        ar.choose_alpha({1.0: np.nan}, 1e-12)
    ledger = []

    def bad_design(tr, ev):
        n = 8
        return np.full((len(tr), n), np.nan), np.full((len(ev), n), np.nan), {}
    with pytest.raises(ar.FitFailure):
        ar.select_and_fit(bad_design, np.arange(20.0), 15, np.arange(15, 20), kind="ridge", alphas=[1.0], inner_folds=3,
                          inner_seed=0, tie_tol=1e-12, ledger=ledger, key={})
    assert ledger and all(r["status"] == "failed" for r in ledger)


# ---------------------------------------------------------------------- T1 / T2 model scope

class _Stub:
    def __init__(self, test, train, outer):
        self._ex = {"test_children": np.array(test), "train_children": np.array(train)}
        self._outer = outer

    def exports(self, s, k):
        return self._ex

    def outer(self, s):
        return self._outer


def test_t1_t2_scope_rejects_foreign_or_overlapping_units():
    outer = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2}
    ac.check_scope(_Stub([0, 1], [2, 3, 4], outer), 1, 0)
    with pytest.raises(ProvenanceError):                      # vectors of another fold's encoder
        ac.check_scope(_Stub([2, 3], [0, 1, 4], outer), 1, 0)
    with pytest.raises(ProvenanceError):                      # a test child also in the encoder's training set
        ac.check_scope(_Stub([0, 1], [1, 2, 3, 4], outer), 1, 0)


# ---------------------------------------------------------------------- T5 budgets

def test_t5_draw_counts_report_union_not_80():
    src = object.__new__(ac.AgeSource)

    class Co:
        draw_row = {7: 0}
        draw_std = np.stack([np.stack([np.arange(80) + 40 * d for d in range(10)])])
        draw_dev = np.stack([np.stack([np.arange(80) for _ in range(10)])])
    src.co = Co()
    src.primary = lambda c: 7
    d = src.draw_unique_counts([0])[0]
    assert d["std_draw0"] == 80 and d["dev_draw0"] == 80
    assert d["std_union10"] == 440 and d["dev_union10"] == 80


# ---------------------------------------------------------------------- T9 probabilities

def test_t9_probability_scores_by_hand():
    P = np.array([[0.7, 0.2, 0.1, 0.0, 0.0], [0.1, 0.1, 0.2, 0.3, 0.3]])
    Q, info = hr.floor_probabilities(P, 1e-6)
    assert np.allclose(Q.sum(1), 1) and info["fraction_floored"] == pytest.approx(0.2)
    y = np.array([1, 4])
    ce = hr.cross_entropy_bits(Q, y)
    assert ce[0] == pytest.approx(-np.log2(Q[0, 0])) and ce[1] == pytest.approx(-np.log2(Q[1, 3]))
    br = hr.brier(Q, y)
    assert br[1] == pytest.approx(((Q[1] - np.array([0, 0, 0, 1, 0])) ** 2).sum())
    with pytest.raises(ProvenanceError):
        hr.floor_probabilities(np.array([[2.0, -1.0, 0.5, 0.1, 0.0]]), 1e-6)      # logits are not probabilities
    assert hr.prior_vector(np.array([1, 1, 2]), 5, 0.5) == pytest.approx(np.array([2.5, 1.5, .5, .5, .5]) / 5.5)


def test_ordinal_closure_gives_the_fitted_objects():
    from auditory_pf import stats as st
    rng = np.random.default_rng(4)
    X = rng.normal(size=(45, 4))
    y = np.clip(np.round(3 + X[:, 0] + rng.normal(scale=0.5, size=45)), 1, 5).astype(int)
    f_lat, f_exp, _ = st.ordinal_cv(X, y, [0.1, 1.0], seed=3)
    m, scaler = hr.fitted_objects(f_lat)
    P = m.proba(scaler.transform(X))
    assert np.allclose(P.sum(1), 1) and np.allclose(P @ np.arange(1, 6), f_exp(X), atol=1e-12)
    assert np.allclose(m.latent(scaler.transform(X)), f_lat(X))


# ---------------------------------------------------------------------- T10 / T11 logic counterexamples

def test_t10_shared_duration_term_cancels_in_the_difference():
    rng = np.random.default_rng(5)
    D = rng.normal(size=20000)
    gE = 0.8 * D + rng.normal(size=D.size)
    gP = 0.8 * D + rng.normal(size=D.size)
    assert abs(np.corrcoef(gE - gP, D)[0, 1]) < 0.03          # the residual is unrelated to D ...
    assert np.corrcoef(gE, D)[0, 1] > 0.5 and np.corrcoef(gP, D)[0, 1] > 0.5     # ... although both readouts carry D


def test_t11_xor_hides_conditional_information():
    joint = {}
    for s, q in itertools.product((0, 1), (0, 1)):
        joint[(s, s ^ q, q)] = 0.25

    def H(keys):
        marg = {}
        for k, v in joint.items():
            kk = tuple(k[i] for i in keys)
            marg[kk] = marg.get(kk, 0) + v
        return -sum(v * np.log2(v) for v in marg.values() if v > 0)
    mi = H([0]) + H([1]) - H([0, 1])
    cmi = H([0, 2]) + H([1, 2]) - H([0, 1, 2]) - H([2])
    assert mi == pytest.approx(0.0) and cmi == pytest.approx(1.0)


# ---------------------------------------------------------------------- T12 completeness

def test_t12_missing_children_are_never_averaged_away():
    rows = [{"seed": 1, "test_children": [0, 1], "pred": [1.0, 2.0]}, {"seed": 1, "test_children": [2], "pred": [3.0]}]
    assert ac.collect_predictions(rows, [0, 1, 2]) == {1: {0: 1.0, 1: 2.0, 2: 3.0}}
    with pytest.raises(ProvenanceError):
        ac.collect_predictions(rows[:1], [0, 1, 2])


def test_paired_bootstrap_reading():
    idx = np.random.default_rng(0).integers(0, 50, size=(500, 50))
    assert ac.paired_boot(np.full(50, 2.0) + np.linspace(-.1, .1, 50), idx)["reading"] == "gain_established"
    assert ac.paired_boot(np.linspace(-1, 1, 50), idx)["status"] == "COMPLETED_LOW_PRECISION"


# ---------------------------------------------------------------------- inputs

def test_stage_transform_matches_float32_path():
    rng = np.random.default_rng(6)
    e = (rng.normal(size=(3, 20, 200)) * 40).astype(np.float32)
    scale = np.float64(13.37)
    out = rp.stage_transform(e, scale)
    assert out.dtype == np.float16
    assert np.array_equal(out, np.clip(e / float(scale), -60.0, 60.0).astype(np.float16))


def test_raw_bins_shape_and_values():
    x = np.arange(2 * 3 * 200, dtype=float).reshape(2, 3, 200)
    b = rp.raw_bins(x, 5)
    assert b.shape == (2, 3 * 40)
    assert b[0, 0] == pytest.approx(x[0, 0, :5].mean()) and b[1, -1] == pytest.approx(x[1, 2, 195:].mean())


def test_work_list_matches_specification():
    import yaml
    config = yaml.safe_load(open("configs/auditory_nextmap_v1.yaml"))
    wl = ac.work_list(config)
    assert ("single_draw80", "pair_equivalence") in wl and wl.index(("single_draw80", "pair_equivalence")) > wl.index(("single_draw80", "joint"))
    assert [v for b, v in wl if b == "draw_ensemble10"] == ["common", "joint"]
    assert {"contrast_bs", "joint_bs", "technical_noscale"} <= {v for _, v in wl}
