"""auditory_story unit tests (synthetic tensors only; run through Slurm: slurm/auditory_story_tests.sbatch)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
import yaml

from auditory_story import clinical as cl
from auditory_story import metrics as mt
from auditory_story import profile as prof
from auditory_story import transform as tf
from auditory_story.data import inner_folds, label_sets
from auditory_story.srp import (PopulationResponse, ResponseProfile, balanced_profile_loss, condition_phi_means,
                                encode_from_means)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = yaml.safe_load((ROOT / "configs/auditory_story_v1.yaml").read_text())


def toy_model(conditioned=True):
    torch.manual_seed(20)
    pop = PopulationResponse(torch.randn(2, 4, 6) * 0.1, torch.zeros(2, 6))
    return ResponseProfile(pop, latent_dim=3, hidden=8, phi_dim=4, conditioned=conditioned)


# ---------------------------------------------------------------------- package reference behaviour

def test_conditionwise_permutation_invariance_and_zero_latent():
    m = toy_model().eval()
    x = torch.randn(2, 2, 5, 6)
    mask = torch.ones(2, 2, 5, dtype=torch.bool)
    s = torch.tensor([[0, 0, 1, 1], [0, 0, 1, 1]])
    h = torch.randn(2, 4, 3)
    a = m(x, mask, s, h).latent_mean
    b = m(x[:, :, torch.tensor([4, 0, 3, 2, 1])], mask, s, h).latent_mean
    assert torch.allclose(a, b, atol=1e-6)
    mean, lv = m.decode(torch.zeros(2, 3), s, h)
    base, blv = m.population(s, h)
    assert torch.equal(mean, base) and torch.equal(lv, blv)


def test_missing_condition_rejected():
    m = toy_model()
    mask = torch.ones(2, 2, 5, dtype=torch.bool)
    mask[0, 1] = False
    with pytest.raises(ValueError):
        m(torch.randn(2, 2, 5, 6), mask, torch.tensor([[0, 1]] * 2), torch.randn(2, 2, 3))


def test_loss_child_condition_equal_weight():
    m = toy_model().train()
    s = torch.tensor([[0, 0, 0, 1], [0, 1, 1, 1]])
    out = m(torch.randn(2, 2, 5, 6), torch.ones(2, 2, 5, dtype=torch.bool), s, torch.randn(2, 4, 3))
    target = torch.randn(2, 4, 6)
    L = balanced_profile_loss(target, out, s, 2, beta=0.0)
    nll = 0.5 * (np.log(2 * np.pi) + out.logvar + (target - out.mean) ** 2 * torch.exp(-out.logvar)).mean(-1)
    manual = torch.stack([nll[0, :3].mean(), nll[0, 3], nll[1, 0], nll[1, 1:].mean()]).mean()
    assert torch.allclose(L["nll_per_dimension"], manual, atol=1e-6)


def test_streaming_phi_means_exact_and_encode_agree():
    m = toy_model().eval()
    x0, x1 = torch.randn(7, 6), torch.randn(11, 6)
    means = condition_phi_means(m, [x0, x1], batch=4)
    assert torch.allclose(means[0], m.phi(x0).mean(0), atol=1e-6)
    assert torch.allclose(means[1], m.phi(x1).mean(0), atol=1e-6)
    sup = torch.stack([x0[:5], x1[:5]])[None]
    mu_a, lv_a = m.encode(sup, torch.ones(1, 2, 5, dtype=torch.bool))
    mu_b, lv_b = encode_from_means(m, condition_phi_means(m, [x0[:5], x1[:5]])[None])
    assert torch.allclose(mu_a, mu_b, atol=1e-6) and torch.allclose(lv_a, lv_b, atol=1e-6)
    p = toy_model(conditioned=False).eval()
    mu_p, _ = p.encode(sup, torch.ones(1, 2, 5, dtype=torch.bool))
    mu_q, _ = encode_from_means(p, condition_phi_means(p, [x0[:5], x1[:5]])[None])
    assert torch.allclose(mu_p, mu_q, atol=1e-6)
    swapped, _ = p.encode(sup[:, [1, 0]], torch.ones(1, 2, 5, dtype=torch.bool))
    assert torch.allclose(mu_p, swapped, atol=1e-6)                      # pooled arm ignores support condition labels


# ---------------------------------------------------------------------- transforms

def test_cell_weights_and_whitened_projection():
    rng = np.random.default_rng(0)
    child = np.repeat(np.arange(6), 50)
    cls = np.tile(np.r_[np.zeros(40), np.ones(10)].astype(int), 6)
    x = rng.normal(size=(300, 10)) @ rng.normal(size=(10, 10))
    w = tf.cell_weights(child, cls)
    assert np.isclose(w.sum(), 1.0)
    cells = pd.Series(w).groupby([child, cls]).sum()
    assert np.allclose(cells, 1 / 12)
    T = tf.fit_projection(x, child, cls, 4)
    e = tf.apply_projection(T, x).astype(np.float64)
    var = w @ (e - w @ e) ** 2
    assert np.allclose(var, 1.0, atol=1e-5) and T["dim"] == 4
    rank_def = np.column_stack([x[:, :2], x[:, :2] @ np.ones((2, 3))])
    T2 = tf.fit_projection(rank_def, child, cls, 4)
    assert T2["rank"] == 2 and T2["dim"] == 2                            # never padded with random directions


def test_pca_sample_caps_cells():
    child = np.repeat(np.arange(3), 300)
    cls = np.tile(np.r_[np.zeros(200), np.ones(100)].astype(int), 3)
    idx = tf.pca_sample(child, cls, 128, 7)
    counts = pd.Series(1, index=idx).groupby([child[idx], cls[idx]]).sum()
    assert counts.max() == 128 and np.array_equal(idx, tf.pca_sample(child, cls, 128, 7))


def test_population_intercept_unpenalised_and_weights():
    rng = np.random.default_rng(1)
    child = np.repeat(np.arange(4), 20)
    cls = np.tile(np.r_[np.zeros(10), np.ones(10)].astype(int), 4)
    e = rng.normal(size=(80, 3)) + 5.0
    h = np.zeros((80, 3))
    pop = tf.fit_population(e, h, cls, child, alpha=0.1)
    for s in (0, 1):
        w = tf.cell_weights(child[cls == s], cls[cls == s])
        assert np.allclose(pop["coefficients"][s, 0], w @ e[cls == s], atol=1e-10)
        assert np.isclose(pop["info"][s]["weight_sum"], 1.0)
    assert (pop["logvar"] >= -4).all() and (pop["logvar"] <= 3).all()


def test_history_imputation_uses_training_median():
    h = np.array([[np.nan, 1.0, 0.1], [1.0, np.nan, 0.5], [3.0, 3.0, 0.9]])
    Hs = tf.fit_history(h, np.array([0, 1, 2]), np.zeros(3, int))
    assert np.allclose(Hs["median"], [2.0, 2.0, 0.5])
    out = tf.apply_history(Hs, np.array([[np.nan, np.nan, np.nan]]))
    assert np.isfinite(out).all()


# ---------------------------------------------------------------------- episodes, training, checkpoints

def synthetic_trials(n_child=8, n=80, D=6, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_child):
        for k in (0, 1):
            for i in range(n):
                rows.append((c, k, i % 2))
    tt = pd.DataFrame(rows, columns=["child", "cls", "group"])
    tt["guard_ok"] = True
    E = rng.normal(size=(len(tt), D)).astype(np.float32)
    H = rng.normal(size=(len(tt), 3)).astype(np.float32)
    return tt, E, H


def test_episode_sampler_disjoint_groups_and_alternation():
    tt, E, H = synthetic_trials()
    cells = prof.cells_of(tt, list(range(8)))
    smp = prof.EpisodeSampler(cells, list(range(8)), 32, 4, 3)
    for step in range(4):
        kids, sup, qry, qcond, d = smp.sample(step)
        assert d == step % 2 and len(set(kids)) == 4
        assert (tt.group.to_numpy()[sup] == d).all() and (tt.group.to_numpy()[qry] == 1 - d).all()
        assert not set(sup.ravel()) & set(qry.ravel())
        for b, c in enumerate(kids):
            assert (tt.child.to_numpy()[sup[b]] == c).all() and (tt.cls.to_numpy()[sup[b, 1]] == 1).all()


def small_config(steps):
    c = json.loads(json.dumps(CONFIG))
    c["profile"]["steps"] = steps
    c["profile"]["checkpoint_every_steps"] = 50
    c["profile"]["latent_dim"] = 3
    c["profile"]["phi_hidden"] = 8
    c["profile"]["phi_output"] = 4
    return c


def test_checkpoint_resume_is_exact(tmp_path):
    tt, E, H = synthetic_trials()
    child, cls = tt.child.to_numpy(), tt.cls.to_numpy()
    pop = tf.fit_population(E, H, cls, child)
    cells = prof.cells_of(tt, list(range(8)))
    c200, c100 = small_config(200), small_config(100)
    m_full = prof.build_model(pop, c200, "conditional", 5)
    prof.train_arm(m_full, E, H, prof.EpisodeSampler(cells, list(range(8)), 32, 4, 9), c200, tmp_path / "a.pt", 11)
    m_part = prof.build_model(pop, c200, "conditional", 5)
    prof.train_arm(m_part, E, H, prof.EpisodeSampler(cells, list(range(8)), 32, 4, 9), c100, tmp_path / "b.pt", 11)
    m_res = prof.build_model(pop, c200, "conditional", 5)
    info = prof.train_arm(m_res, E, H, prof.EpisodeSampler(cells, list(range(8)), 32, 4, 9), c200, tmp_path / "b.pt", 11)
    assert info["resumed_from"] == 100
    for a, b in zip(m_full.state_dict().values(), m_res.state_dict().values()):
        assert torch.equal(a, b)


def test_arms_share_initialisation():
    tt, E, H = synthetic_trials()
    pop = tf.fit_population(E, H, tt.cls.to_numpy(), tt.child.to_numpy())
    c = small_config(10)
    a, b = prof.build_model(pop, c, "conditional", 5), prof.build_model(pop, c, "pooled", 5)
    assert all(torch.equal(x, y) for x, y in zip(a.state_dict().values(), b.state_dict().values()))
    assert a.conditioned and not b.conditioned


def test_profile_code_never_reads_targets():
    for name in ("profile.py", "transform.py", "srp.py"):
        text = (ROOT / "auditory_story" / name).read_text().lower()
        for token in ("sir", "muss", "records.csv", "label_masks"):
            assert token not in text.replace("sirable", ""), (name, token)


# ---------------------------------------------------------------------- clinical heads

def test_ordinal_gradient_matches_finite_differences():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(30, 4))
    y = rng.integers(1, 6, size=30)
    theta = np.r_[rng.normal(size=4) * 0.3, -1.0, rng.normal(size=3) * 0.2]
    f, g = cl.objective(theta, X, y, 0.1, 0.001)
    num = np.zeros_like(theta)
    for i in range(len(theta)):
        e = np.zeros_like(theta)
        e[i] = 1e-6
        num[i] = (cl.objective(theta + e, X, y, 0.1, 0.001)[0] - cl.objective(theta - e, X, y, 0.1, 0.001)[0]) / 2e-6
    assert np.allclose(g, num, atol=1e-6)


def test_ordinal_probabilities_valid_with_missing_levels():
    rng = np.random.default_rng(4)
    X = rng.normal(size=(12, 3))
    y = np.array([3, 4, 4, 5, 5, 5, 4, 3, 4, 5, 4, 3])                   # no level 1 or 2 in training
    m = cl.fit_ordinal(X, y, 0.1)
    P = cl.predict_ordinal(m, rng.normal(size=(5, 3)))
    assert P.shape == (5, 5) and np.allclose(P.sum(1), 1) and (P > 0).all()
    assert np.all(np.diff(m["t"]) >= 1e-4 - 1e-12) and m["converged"]
    lp = cl.level_logprob(m["t"], np.array([0.0, 50.0, -50.0]))
    assert np.isfinite(lp).all()


def test_ordinal_objective_is_mean_scaled():
    rng = np.random.default_rng(5)
    X = rng.normal(size=(10, 2))
    y = rng.integers(1, 6, size=10)
    th = np.r_[0.2, -0.1, -1.0, 0.1, 0.2, 0.3]
    f1, _ = cl.objective(th, X, y, 0.0, 0.0)
    f2, _ = cl.objective(th, np.vstack([X, X]), np.r_[y, y], 0.0, 0.0)
    assert np.isclose(f1, f2)                                             # mean, not sum, of the NLL


def test_ridge_closed_form_uses_n_lambda():
    rng = np.random.default_rng(6)
    X = rng.normal(size=(20, 3))
    y = rng.normal(size=20) * 10 + 50
    m = cl.fit_ridge(X, y, 0.5)
    yz = (y - y.mean()) / y.std()
    grad = 2 * X.T @ (X @ m["w"] - yz) / 20 + 2 * 0.5 * m["w"]
    assert np.allclose(grad, 0, atol=1e-10)


def test_design_fitted_on_fit_rows_only_and_fallback():
    spl = CONFIG["clinical"]["clinical_spline"]
    rng = np.random.default_rng(7)
    clin = np.column_stack([rng.uniform(10, 100, 12), np.log1p(rng.uniform(0, 60, 12))])
    D = cl.Design(spl).fit(clin[:8], None)
    a = D.transform(clin[8:], None)
    D2 = cl.Design(spl).fit(clin[:8], None)
    assert np.array_equal(a, D2.transform(clin[8:], None))
    assert D.transform(clin[:8], None).shape[1] == 2 * (spl["n_knots"] + spl["degree"] - 1 - (0 if spl["include_bias"] else 1))
    flat = np.column_stack([np.r_[np.ones(6), 2 * np.ones(2)], clin[:8, 1]])
    D3 = cl.Design(spl).fit(flat, None)
    assert D3.n_linear_fallback == 1


def test_fit_head_counts_calls_and_breaks_ties_to_larger_lambda():
    rng = np.random.default_rng(8)
    clin = np.ones((12, 2))                                               # constant design -> all lambdas tie
    y = rng.integers(1, 6, size=12)
    folds = np.arange(12) % 3
    out = cl.fit_head("sir", clin, None, y, folds, np.ones((4, 2)), None, CONFIG)
    assert len(out["calls"]) == 10 and out["lambda"] == 1.0
    out = cl.fit_head("muss", clin, None, rng.uniform(0, 100, 12), folds, np.ones((4, 2)), None, CONFIG)
    assert len(out["calls"]) == 10 and out["lambda"] == 1.0 and (out["pred"] >= 0).all() and (out["pred"] <= 100).all()


def test_prior_probabilities_pseudocount():
    p = cl.prior_probabilities(np.array([3, 3, 4]), 0.5)
    assert np.allclose(p, np.array([0.5, 0.5, 2.5, 1.5, 0.5]) / 5.5)


# ---------------------------------------------------------------------- label sets, scoring, aggregation

def test_label_sets_nested_and_target_blind():
    train = list(range(100, 144))
    a = label_sets(train, 2026100212, 404, 0, [12, 24, "all"], {"12": 3, "24": 3, "all": 1})
    b = label_sets(list(reversed(train)), 2026100212, 404, 0, [12, 24, "all"], {"12": 3, "24": 3, "all": 1})
    assert a == b
    for r in range(3):
        assert set(a["12"][r]) <= set(a["24"][r]) and len(a["12"][r]) == 12 and len(a["24"][r]) == 24
    assert a["all"] == [train] and len({tuple(x) for x in a["12"]}) == 3
    f = inner_folds(a["12"][0], 3, 1, 404, 0, "12", 0)
    assert sorted(pd.Series(f).value_counts().tolist()) == [4, 4, 4]


def test_rps_auc_bootstrap_holm():
    y = np.array([1, 3, 5])
    sc = mt.score_sir(np.eye(5)[y - 1], y)
    assert np.allclose(sc["rps"], 0) and np.all(sc["nll_bits"] >= 0)
    near = mt.score_sir(np.eye(5)[[1]], np.array([1]))["rps"][0]
    far = mt.score_sir(np.eye(5)[[4]], np.array([1]))["rps"][0]
    assert near < far
    assert mt.auc(np.array([0.1, 0.4, 0.4, 0.8]), np.array([0, 0, 1, 1])) == pytest.approx(0.875)
    b = mt.bootstrap(np.ones(10) * 0.2, 200, 1)
    assert b["ci_low"] == pytest.approx(0.2) and b["p_boot_two_sided"] == 0.0
    h = mt.holm({"a": 0.01, "b": 0.04})
    assert h["a"] == pytest.approx(0.02) and h["b"] == pytest.approx(0.04)


def test_planned_budget():
    c = CONFIG
    units = len(c["splits"]["outer_seeds"]) * c["splits"]["outer_folds"]
    calls = c["splits"]["clinical_inner_folds"] * len(c["clinical"]["lambda_mean_loss"]) + 1
    reps = sum(int(c["label_budgets"]["repeats"][str(b)]) for b in c["label_budgets"]["values"])
    total = units * calls * (reps * len(c["clinical"]["fitted_sir_arms"]) + len(c["clinical"]["muss_arms"]) +
                             len(c["clinical"]["technical_full_label_arms"]))
    assert total == 8250 <= c["resources"]["clinical_optimizer_calls_max"]
    assert units * len(c["profile"]["arms"]) == 30
    assert not c["mff_validation"]["enabled"] and not c["competitor"]["enabled"]
