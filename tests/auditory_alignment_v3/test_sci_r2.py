"""SCI_R2 synthetic checks: sufficient-statistic ridge and Pearson r equal a direct computation; lagged indexing; grouped CV picks
a sensible alpha and recovers a planted forward relation; nested sub-selection."""
import numpy as np

from auditory_alignment_v3 import sci_r2 as R2


def test_stats_ridge_equals_direct():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((500, 6)); Y = X @ rng.standard_normal((6, 3)) + 0.5 * rng.standard_normal((500, 3)) + 2.0
    S = R2.Stats(6, 3); S.add(X[:250], Y[:250]); S.add(X[250:], Y[250:])
    B, b0 = R2.fit(S, 1e-3)
    Xc = X - X.mean(0); Yc = Y - Y.mean(0); C = Xc.T @ Xc / 500; tr = np.trace(C) / 6
    Bd = np.linalg.solve(C + 1e-3 * tr * np.eye(6), Xc.T @ Yc / 500)
    assert np.allclose(B, Bd) and np.allclose(b0, Y.mean(0) - X.mean(0) @ Bd)
    P = X @ B + b0; r_direct = np.mean([np.corrcoef(P[:, j], Y[:, j])[0, 1] for j in range(3)])
    assert abs(R2.r_of(S, B, b0) - r_direct) < 1e-9
    idx = np.array([0, 2, 4]); Bs, _ = R2.fit(S.sub(idx), 1e-3)
    S2 = R2.Stats(3, 3); S2.add(X[:, idx], Y)
    assert np.allclose(Bs, R2.fit(S2, 1e-3)[0])


def test_lagged_and_grouped_cv():
    F = np.arange(2 * 100, dtype=float).reshape(2, 100)
    X = R2.lagged(F, 10, np.array([5, 6]), np.array([-1, 0, 2]))
    assert X.shape == (2, 6) and X[0, 0] == F[0, 16] and X[0, 2] == F[0, 13] and X[1, 3] == F[1, 17]
    rng = np.random.default_rng(1); G = []
    W = rng.standard_normal((4, 2))
    for g in range(5):
        Xg = rng.standard_normal((300, 4)); S = R2.Stats(4, 2); S.add(Xg, Xg @ W + 0.3 * rng.standard_normal((300, 2))); G.append(S)
    a, curve = R2.choose(G)
    assert a <= 1.0 and max(c["grouped_cv_r"] for c in curve) > 0.9


def test_aggregate_synthetic():
    from auditory_alignment_v3 import sci_r2_aggregate as AG
    rng = np.random.default_rng(2); tasks = []
    for sf in range(2):
        ids = [f"S{sf}{j}" for j in range(10)]; groups = ["nh" if j < 5 else "hi" for j in range(10)]
        q1 = {m: {"r": [0.02 * (k + 1) + 0.001 * rng.standard_normal() for _ in ids]} for k, m in enumerate(R2.MODELS)}
        q2 = {str(L): {"r": [0.1 + 0.001 * rng.standard_normal() for _ in ids]} for L in R2.LAG_GRID_MS}
        tasks.append({"dataset": "dtu", "test_ids": ids, "test_groups": groups, "q1": q1, "q2": q2, "q3": q2})
    vals, grp, ph = AG.identities(tasks, {})
    res = AG.aggregate(vals, grp)["dtu"]
    assert res["n"] == 20 and abs(res["q1_increments"]["M1->M2"]["est"] - 0.02) < 0.002 and "sim_low" in res["q1_increments"]["M5->M6"]
    assert abs(np.mean(res["q2"]["all"]["est"]) - 0.1) < 0.01 and "hi-nh" in res["contrasts"]
