"""CPU unit tests for paper/w7_objectives.py (synthetic data only; no production writes).

Run as a Slurm CPU step: python -m pytest -q auditory_alignment_v3/paper/test_w7_objectives.py
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
import torch

from auditory_alignment_v3.aln41 import temporal_objectives_torch as TO
from auditory_alignment_v3.aln41.cs_qmi_reference import cs_qmi, gaussian_log_gram
from auditory_alignment_v3.paper import w7_objectives as W


def rand(n, d, seed):
    return torch.randn(n, d, generator=torch.Generator().manual_seed(seed), dtype=torch.float64)


def brute_force(u, a, h, su, sa, sh):
    """Explicit quadruple sums of the three D_CS integrals (common constants dropped)."""
    Lu, La, G = (gaussian_log_gram(x, s) for x, s in ((u, su), (a, sa), (h, sh)))
    n = len(u); t1 = t2 = t3 = 0.0
    for i, j, k, l in itertools.product(range(n), repeat=4):
        hh = .5 * (G[i, j] + G[i, k] + G[i, l] + G[j, k] + G[j, l] + G[k, l])
        t1 += math.exp(Lu[i, k] + La[i, k] + hh); t2 += math.exp(Lu[i, k] + La[j, l] + hh); t3 += math.exp(Lu[i, k] + La[i, l] + hh)
    return math.log(t1), math.log(t2), math.log(t3)


def test_closed_form_matches_explicit_quadruple_sums():
    u, a, h = rand(5, 3, 1), rand(5, 2, 2), rand(5, 4, 3)
    _, (p1, p2, p3) = W.conditional_cs(u, a, h, sigma_u=1.1, sigma_a=.8, sigma_h=1.7)
    b1, b2, b3 = brute_force(u, a, h, 1.1, .8, 1.7)
    assert abs(float(p1[0]) - b1) < 1e-10 and abs(float(p2[0]) - b2) < 1e-10 and abs(float(p3[0]) - b3) < 1e-10


def test_closed_form_matches_numerical_integration_of_kde_products():
    """1-D u, a, h, N = 3: f1 = p(u,a,h) p(h), f2 = p(u,h) p(a,h) from NORMALISED Gaussian KDE components with SD sigma/sqrt(2)
    (the overlap-SD convention), integrated on a grid; D_CS must equal the closed form."""
    g = torch.Generator().manual_seed(5)
    u, a, h = (torch.randn(3, 1, generator=g, dtype=torch.float64) for _ in range(3))
    su, sa, sh = 1.0, 1.3, .9
    d_closed, _ = W.conditional_cs(u, a, h, sigma_u=su, sigma_a=sa, sigma_h=sh)
    grid = np.linspace(-9, 9, 241); dx = grid[1] - grid[0]

    def k(x, c, s):                                      # KDE component, SD = s / sqrt(2)
        sd = s / math.sqrt(2)
        return np.exp(-.5 * ((x - c) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
    U, A, H = np.meshgrid(grid, grid, grid, indexing='ij')
    un, an, hn = u.numpy().ravel(), a.numpy().ravel(), h.numpy().ravel()
    puah = sum(k(U, un[i], su) * k(A, an[i], sa) * k(H, hn[i], sh) for i in range(3)) / 3
    ph = sum(k(H, hn[i], sh) for i in range(3)) / 3
    puh = sum(k(U, un[i], su) * k(H, hn[i], sh) for i in range(3)) / 3
    pah = sum(k(A, an[i], sa) * k(H, hn[i], sh) for i in range(3)) / 3
    f1, f2 = puah * ph, puh * pah
    num = math.log((f1 ** 2).sum() * dx ** 3) + math.log((f2 ** 2).sum() * dx ** 3) - 2 * math.log((f1 * f2).sum() * dx ** 3)
    assert abs(num - float(d_closed)) < 1e-6


def test_constant_history_reduces_to_marginal_cs_qmi():
    u, a = rand(9, 4, 11), rand(9, 3, 12)
    h = torch.zeros(9, 2, dtype=torch.float64)
    d, _ = W.conditional_cs(u, a, h, sigma_u=1.2, sigma_a=.9, sigma_h=1.0)
    ref, _ = cs_qmi(u, a, sigma_u=1.2, sigma_v=.9)
    assert abs(float(d) - float(ref)) < 1e-10


def test_nonnegative_and_row_permutation_invariant():
    for s in range(5):
        u, a, h = rand(12, 4, 20 + s), rand(12, 3, 30 + s), rand(12, 4, 40 + s)
        d, _ = W.conditional_cs(u, a, h, sigma_u=1.5, sigma_a=1.1, sigma_h=1.9)
        p = torch.randperm(12, generator=torch.Generator().manual_seed(s))
        dp, _ = W.conditional_cs(u[p], a[p], h[p], sigma_u=1.5, sigma_a=1.1, sigma_h=1.9)
        assert float(d) >= -1e-10 and abs(float(d) - float(dp)) < 1e-9


def test_identical_slots_are_q_independent_and_equal_single_slot():
    u, a, h = rand(10, 4, 50), rand(10, 3, 51), rand(10, 4, 52)
    d1, _ = W.conditional_cs(u, a, h, sigma_u=1.4, sigma_a=1.0, sigma_h=1.6)
    view = W.CondViewBatch(torch.stack([u, u, u], 1), a, 1.4, 1.0, None, 'env', h, 1.6)
    for lg in (torch.zeros(3, dtype=torch.float64), torch.tensor([.3, -1., 2.], dtype=torch.float64)):
        s, _ = TO.tcs_from_log_potentials(W.ccs_slot_log_potentials(view), lg)
        assert abs(float(s) - float(d1)) < 1e-10


def test_all_tcs_roster_reproduces_reference_episode_exactly():
    g = torch.Generator().manual_seed(9)

    def views(seed, grad):
        U = torch.nn.functional.normalize(torch.randn(32, 3, 32, generator=torch.Generator().manual_seed(seed)), dim=-1)
        if grad:
            U.requires_grad_(True)
        return U, [TO.ViewBatch(U, torch.nn.functional.normalize(torch.randn(32, 32, generator=g), dim=-1).double(), 1.06, 1.41, .8, n)
                   for n in ('env', 'ss', 'sc')]
    _, sv = views(1, False); Uq, qv = views(2, True)
    prior = torch.tensor([.1, -.2, .05], requires_grad=True)
    l_ref, r_ref = TO.episode_loss_fo('TCS', sv, qv, prior)
    gu_ref, gp_ref = torch.autograd.grad(l_ref, (Uq, prior))
    l_new, r_new = W.ccs_episode_loss_fo(sv, qv, prior)
    gu_new, gp_new = torch.autograd.grad(l_new, (Uq, prior))
    assert float(l_ref) == float(l_new) and torch.equal(r_ref['delta'], r_new['delta'])
    assert torch.equal(gu_ref, gu_new) and torch.equal(gp_ref, gp_new)


def test_ccs_episode_is_finite_and_rejects_bad_inputs():
    synth = W.Synth(); g = torch.Generator().manual_seed(3)

    def views(grad):
        u, a, h = synth.sample('coupled', 32, g, 1.0)
        U = torch.stack([u, u, u], 1).float()
        if grad:
            U.requires_grad_(True)
        return U, [W.CondViewBatch(U, a, 1.06, 1.41, .8, 'env', h.float(), 1.5), TO.ViewBatch(U, a, 1.06, 1.41, .8, 'ss')]
    _, sv = views(False); Uq, qv = views(True)
    prior = torch.zeros(3, requires_grad=True)
    loss, rep = W.ccs_episode_loss_fo(sv, qv, prior)
    loss.backward()
    assert math.isfinite(float(loss)) and torch.isfinite(Uq.grad).all() and rep['query']['views'][0]['estimator'] == 'CCS'
    bad = W.CondViewBatch(qv[0].u, qv[0].v, 1.06, 1.41, .8, 'env', qv[0].h.clone().requires_grad_(True), 1.5)
    with pytest.raises(ValueError):
        W.ccs_slot_log_potentials(bad)


def test_history_map_recovers_linear_relation_and_uses_fit_rows_only():
    rng = np.random.default_rng(0)
    H = rng.normal(size=(400, 4)); B = rng.normal(size=(4, 8)); A = H @ B + .5 + .1 * rng.normal(size=(400, 8))
    hm = W.fit_history_map(H[:300], A[:300], H[300:], A[300:])
    assert np.allclose(np.array(hm['coef']), B, atol=.05) and hm['n_fit'] == 300 and hm['n_dev'] == 100
    r = W.apply_history_map(A, H, hm)
    assert r.shape == A.shape and np.abs(r).mean() < .2
    rt = W.apply_history_map(torch.as_tensor(A, dtype=torch.float32), torch.as_tensor(H, dtype=torch.float32), hm)
    assert rt.dtype == torch.float32 and np.allclose(rt.numpy(), r, atol=1e-5)
    assert W.lag_samples(64) == (1, 6, 13, 32) and W.lag_samples(128) == (3, 13, 26, 64)


def test_pres_dependence_requires_fixed_z0_and_characterises_fixed_bandwidth_dispersion():
    """z0 must be gradient-free. Characterisation (not a design choice): with the fixed bandwidth, the KDE CS-QMI of
    (P z_theta, P z0) is NOT maximal at z_theta = z0 -- scaling P z_theta up increases it (reported in the W7 smoke receipt)."""
    g = torch.Generator().manual_seed(4)
    z0 = torch.randn(32, 3, 50, generator=g)
    pca = {'mu': z0.reshape(-1, 50).mean(0), 'sd': z0.reshape(-1, 50).std(0), 'components': torch.linalg.qr(torch.randn(50, 8, generator=g))[0].T}
    sig = W.pooled_slot_sigma(torch.stack([W.pca_project(z0[:, k], pca) for k in range(3)], 1))
    zt = z0.clone().requires_grad_(True)
    same, rep = W.pres_dependence(zt, z0, pca, sig)
    same.backward()
    assert float(same) > 0 and torch.isfinite(zt.grad).all() and len(rep['slot_cs_qmi_nats']) == 3
    mu = pca['mu']
    scaled, _ = W.pres_dependence(mu + 1.5 * (z0 - mu), z0, pca, sig)
    assert float(scaled) > float(same)
    with pytest.raises(AssertionError):
        W.pres_dependence(zt, z0.clone().requires_grad_(True), pca, sig)


def test_gradient_check():
    out = W.gradient_check()
    assert out['pass'], out


def test_episode_factory_dispatch_and_pres():
    state = {'beta': .3, 'trace': [], 'pres': lambda q: (q[0].u.sum() * 0 + torch.tensor(2.0, dtype=torch.float64), {'pres_cs_qmi_nats': 2.0})}
    U = torch.nn.functional.normalize(torch.randn(32, 3, 32, generator=torch.Generator().manual_seed(1)), dim=-1)
    a = torch.nn.functional.normalize(torch.randn(32, 32, generator=torch.Generator().manual_seed(2)), dim=-1).double()
    v = [TO.ViewBatch(U, a, 1.06, 1.41, .8, n) for n in ('env', 'ss', 'sc')]
    prior = torch.zeros(3, requires_grad=True)
    ref, _ = TO.episode_loss_fo('TCS', v, v, prior)
    f = W.make_episode_loss('TCS_PRES', {'ccs': False, 'pres': True}, state)
    got, rep = f('TCS_PRES', v, v, prior)
    assert abs(float(got) - (float(ref) - .3 * 2.0)) < 1e-12 and state['trace'] == [2.0] and rep['pres']['beta'] == .3
    with pytest.raises(ValueError):
        f('TCS', v, v, prior)


def test_episode_factory_ccs_roster():
    synth = W.Synth(); g = torch.Generator().manual_seed(8)
    u, a, h = synth.sample('coupled', 32, g, 1.0)
    U = torch.stack([u, u, u], 1).float()
    v = [W.CondViewBatch(U, a, 1.06, 1.41, .8, 'env', h.float(), 1.5)] + [TO.ViewBatch(U, a, 1.06, 1.41, .8, n) for n in ('ss', 'sc')]
    state = {'beta': None, 'trace': []}
    f = W.make_episode_loss('TCS_CCS', {'ccs': True, 'pres': False}, state)
    loss, rep = f('TCS_CCS', v, v, torch.zeros(3, requires_grad=True))
    ref, _ = W.ccs_episode_loss_fo(v, v, torch.zeros(3, requires_grad=True))
    assert float(loss) == float(ref) and state['ccs_calls'] == 1
    g2 = W.make_episode_loss('TCS_RES', {'ccs': False, 'pres': False}, {'beta': None, 'trace': []})
    with pytest.raises(ValueError):
        g2('TCS_RES', v, v, torch.zeros(3, requires_grad=True))


def test_fast_fixed_terms_match_log_domain_reference():
    for seed, (sh, sa) in enumerate(((1.7, .8), (.3, .2), (6.0, 3.0))):
        a, h = rand(32, 8, 60 + seed), rand(32, 4, 70 + seed)
        fast = W.ccs_fixed_terms(a, h, sa, sh); ref = W.ccs_fixed_terms_reference(a, h, sa, sh)
        assert all(torch.allclose(x, y, rtol=0, atol=1e-10) for x, y in zip(fast, ref))
