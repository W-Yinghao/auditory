"""P1 (03 §3.5): checks of the I_ccs port (auditory_c3/pid_ccs.py) before the PID layer may be used.

1. Univariate sources: identical to the upstream Python port (pid_mvn_ince.py, correct for 1-d variables) on the same
   Monte Carlo samples, over the Barrett (2015) Fig. 3 covariances used in Ince's examples_2dmvn.m.
2. Multivariate sources (where the upstream port's fancy indexing fails): invariance to invertible linear maps within a
   source and to swapping sources, applied to the same samples; exact lattice identities.
3. Near-identical sources: redundancy approaches the single-source MI.
A comparison with the MATLAB reference on multivariate cases still needs Octave (not available on this cluster).
"""
import os
import sys

import numpy as np
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from auditory_c3 import pid_ccs  # noqa: E402
from auditory_c3.vendor import pid_mvn_ince as upstream  # noqa: E402


def _barrett(a, b, c):
    return np.array([[1, b, a], [b, 1, c], [a, c, 1.0]])


@pytest.mark.parametrize("a,c,b", [(0.5, 0.5, -0.4), (0.5, 0.5, 0.0), (0.5, 0.5, 0.5), (0.5, 0.5, 0.9),
                                   (0.4, 0.6, -0.3), (0.4, 0.6, 0.2), (0.4, 0.6, 0.8)])
def test_univariate_matches_upstream_on_same_samples(a, c, b):
    C = _barrett(a, b, c)
    np.random.seed(11)
    x = np.random.multivariate_normal(mean=np.zeros(3), cov=C, size=100000)
    np.random.seed(11)
    ref = upstream.Iccs_mvn([1, 2], C, [1, 1, 1])
    ours = pid_ccs.iccs_redundancy(C, 1, 1, 1, samples=x)
    assert abs(ours - ref) < 1e-9


def _random_cov(rng, d):
    A = rng.standard_normal((d, d)) + 0.5 * np.eye(d)
    C = A @ A.T + 0.3 * np.eye(d)
    s = np.sqrt(np.diag(C))
    return C / np.outer(s, s)


@pytest.mark.parametrize("n1,n2,ns", [(3, 2, 2), (5, 5, 3), (1, 4, 1)])
def test_multivariate_invariances(n1, n2, ns):
    rng = np.random.default_rng(n1 * 100 + n2 * 10 + ns)
    d = n1 + n2 + ns
    C = _random_cov(rng, d)
    x = rng.multivariate_normal(np.zeros(d), C, size=50000)
    r0 = pid_ccs.iccs_redundancy(C, n1, n2, ns, samples=x)
    # invertible linear map within source 1 (and within the target)
    T = np.eye(d)
    T[:n1, :n1] = rng.standard_normal((n1, n1)) + 2 * np.eye(n1)
    T[n1 + n2:, n1 + n2:] = rng.standard_normal((ns, ns)) + 2 * np.eye(ns)
    r1 = pid_ccs.iccs_redundancy(T @ C @ T.T, n1, n2, ns, samples=x @ T.T)
    assert abs(r1 - r0) < 1e-8
    # swapping the two sources
    perm = np.r_[np.arange(n1, n1 + n2), np.arange(n1), np.arange(n1 + n2, d)]
    r2 = pid_ccs.iccs_redundancy(C[np.ix_(perm, perm)], n2, n1, ns, samples=x[:, perm])
    assert abs(r2 - r0) < 1e-8


def test_lattice_identities():
    C = _random_cov(np.random.default_rng(3), 7)
    p = pid_ccs.pid_ccs(C, 3, 2, 2, n_mc=20000, rng=1)
    assert abs(p["R"] + p["U1"] + p["U2"] + p["S"] - p["I_S_X1X2"]) < 1e-12
    assert abs(p["U1"] + p["R"] - p["I_S_X1"]) < 1e-12 and abs(p["U2"] + p["R"] - p["I_S_X2"]) < 1e-12
    m = pid_ccs.pid_mmi(C, 3, 2, 2)
    assert min(m["U1"], m["U2"]) == 0.0


def test_near_identical_sources_redundancy_equals_source_mi():
    # X2 = X1 + tiny noise, S = X1 + noise: all information is shared
    eps, rho = 1e-3, 0.7
    C = np.array([[1, 1, rho], [1, 1 + eps**2, rho], [rho, rho, 1.0]])
    r = pid_ccs.iccs_redundancy(C, 1, 1, 1, n_mc=200000, rng=5)
    i = -0.5 * np.log2(1 - rho**2)
    assert abs(r - i) < 0.01
