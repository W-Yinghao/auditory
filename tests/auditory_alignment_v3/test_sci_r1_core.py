"""Synthetic tests for auditory_alignment_v3.sci_r1 (no data): readout core vs auditory_alignment.evaluate, ridge rule, Haufe,
bootstrap, lag tables vs instantiated encoders, evaluation sets vs evaluate_continuous on a toy cohort."""
import sys

import numpy as np
import pytest
import torch

sys.dont_write_bytecode = True

from auditory_alignment import evaluate as ev1  # noqa: E402
from auditory_alignment_v2 import temporal as T2  # noqa: E402
from auditory_alignment_v3.sci_r1 import continuous as C  # noqa: E402
from auditory_alignment_v3.sci_r1 import lags as L  # noqa: E402
from auditory_alignment_v3.sci_r1 import readout as R  # noqa: E402
from auditory_alignment_v3.sci_r1 import stats as S  # noqa: E402


def test_scores_metrics_tau_match_ev1():
    rng = np.random.default_rng(0)
    P = rng.normal(size=(30, 20, 6)); Ac = rng.normal(size=(12, 20, 6)); mu, sd = Ac.reshape(-1, 6).mean(0), Ac.reshape(-1, 6).std(0) + 1e-8
    ref = np.einsum("qtd,ctd->qc", ev1._zt(P), ev1._zt((Ac - mu) / sd)) / (20 * 6)
    got = R.unified_scores(P, R.cand_matrix(Ac, mu, sd))
    assert np.allclose(ref, got, atol=1e-12)
    own = rng.integers(0, 12, 30)
    tau = R.calibrate_tau(got, own)

    class Dummy:
        pass
    d = Dummy(); ev1.Readouts.calibrate(d, {"unified": got}, own)
    assert tau == pytest.approx(d.tau["unified"])
    m1, m2 = ev1._metrics(got, own, tau), R.metrics(got, own, tau)
    for k in m1:
        assert m1[k] == pytest.approx(m2[k], abs=1e-12), k


def test_mismatch_roll_equals_scoring_rolled_queries():
    rng = np.random.default_rng(1)
    U = rng.normal(size=(9, 15, 4)); B = rng.normal(size=(5, 3)); Zc = R.cand_matrix(rng.normal(size=(7, 15, 3)), 0.0, 1.0)
    P = lambda u: R.apply(B, u.reshape(-1, 4)).reshape(len(u), 15, 3)
    assert np.allclose(np.roll(R.unified_scores(P(U), Zc), 1, axis=0), R.unified_scores(P(np.roll(U, 1, axis=0)), Zc))


def test_relridge_selects_and_extends():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(2000, 10)); Wt = rng.normal(size=(10, 3)); Y = X @ Wt + 0.1 * rng.normal(size=(2000, 3))
    fit = np.arange(2000) < 1500; es = ~fit
    rr = R.RelRidge(X, Y, fit, es)
    assert rr.lam <= 1e-2 and np.corrcoef(rr.predict(X[es])[:, 0], Y[es, 0])[0, 1] > 0.99
    # pure noise: the correlation criterion is scale-free, so the optimum can sit at either edge; whenever the base-grid
    # optimum is an edge the search must extend by decades and flag the final edge
    for s in range(5):
        Yn = np.random.default_rng(10 + s).normal(size=(2000, 3))
        rn = R.RelRidge(X, Yn, fit, es)
        keys = {float(k) for k in rn.curve}
        if rn.lam <= 1e-4 * (1 + 1e-9):
            assert min(keys) < 1e-4 * 0.99
        if rn.lam >= 1e4 * (1 - 1e-9):
            assert max(keys) > 1e4 * 1.01
        if rn.lam < 1.1e-8 or rn.lam > 0.9e8:
            assert rn.on_edge
    # unpenalised intercept: constant shift recovered
    r2 = R.RelRidge(X, Y + 5.0, fit, es)
    assert np.allclose(r2.predict(X[es]) - rr.predict(X[es]), 5.0, atol=0.05)


def test_haufe_recovers_generative_pattern():
    rng = np.random.default_rng(3)
    a = rng.normal(size=8); s = rng.normal(size=20000); N = rng.normal(size=(20000, 8)) @ np.diag(rng.uniform(0.5, 2, 8))
    X = np.outer(s, a) + 0.3 * N
    w = np.linalg.lstsq(X, s, rcond=None)[0]
    A = R.haufe(R.cov(X), w)
    assert abs(np.corrcoef(A, a)[0, 1]) > 0.99
    Am = R.haufe(R.cov(X), np.c_[w, -w + 0.01 * rng.normal(size=8)])
    assert Am.shape == (8, 2)
    c = R.channel_summary(np.tile(np.arange(4.0), 3), 4)
    assert c.shape == (4,) and np.isclose(np.linalg.norm(c), 1.0)


def test_stats_summary_contrast_ols_maxt():
    rng = np.random.default_rng(4)
    Y = rng.normal(0.3, 1.0, size=(60, 12))
    s = S.summary(Y, B=1000)
    assert (s["band_high"] - s["band_low"] >= s["ci_high"] - s["ci_low"] - 1e-12).all()
    c = S.contrast(Y[:30], Y[30:], B=500)
    assert c["n_a"] == 30 and c["est"].shape == (12,)
    o = S.ols(rng.normal(size=(50, 1)), rng.normal(size=50), ["x"], B=300)
    assert set(o["coef"]) == {"intercept", "x"} and o["coef"]["x"]["ci_low"] < o["coef"]["x"]["ci_high"]
    sa = S.summary(rng.normal(size=40), B=500); sb = S.summary(rng.normal(size=40), B=500)
    f = S.family_maxt({"a": (sa["est"], sa["se"], sa["T"]), "b": (sb["est"], sb["se"], sb["T"])})
    assert f["crit"] > 1.9
    assert S.summary(np.ones(2))["n"] == 2
    with pytest.raises(ValueError):
        S.summary(np.array([1.0, np.nan, 2.0]))


def test_bootstrap_t_band_coverage_small_n():
    """methods review B1: per-replicate studentised max-t band keeps ~95% simultaneous coverage at n = 9."""
    rng = np.random.default_rng(5)
    L_, n, hits = 15, 9, 0
    Cm = 0.8 ** np.abs(np.subtract.outer(np.arange(L_), np.arange(L_))); Lc = np.linalg.cholesky(Cm)
    reps = 150
    for r in range(reps):
        Y = rng.normal(size=(n, L_)) @ Lc.T
        s = S.summary(Y, B=600, seed=r)
        hits += bool(((s["band_low"] <= 0) & (s["band_high"] >= 0)).all())
    assert hits / reps >= 0.90


def test_filter_energy_invariant_to_remixing():
    rng = np.random.default_rng(6)
    C_, F_ = 10, 4
    X = rng.normal(size=(5000, C_)) @ rng.normal(size=(C_, C_)); Sx = R.cov(X)
    W1 = rng.normal(size=(F_, C_)); M = rng.normal(size=(F_, F_)) + 3 * np.eye(F_)
    _, e1 = R.filter_energy(W1, Sx); _, e2 = R.filter_energy(M @ W1, Sx)
    assert np.allclose(e1, e2, atol=1e-8) and (e1 >= -1e-9).all() and (e1 <= 1 + 1e-9).all()


@pytest.mark.parametrize("ds", ["fau", "dtu", "federici"])
def test_window_tokens_match_encoder(ds):
    fs = L.FS[ds]
    W = T2.window_ranges("lag_local_tokens", ds, "full", fs)
    enc = T2.build_encoder("lag_local_tokens", L.N_CH[ds], 32, W, fs)
    (starts, w), = L.branch_starts(enc, W)
    for win in ("early", "late"):
        assert L.tokens_in_window(starts, w, ds, win) == L.WINDOW_TOKENS[ds][win]
    assert len(starts) == {"fau": 25, "dtu": 25, "federici": 29}[ds]
    tab = L.lag_table(starts, w, fs)
    assert tab[0]["stim_lag_lo"] == -7 and tab[0]["stim_lag_hi"] == w - 1


def test_private_window_tokens():
    W = T2.window_ranges("lag_local_tokens", "private_bdf", "full", 250, pre=50)
    lo = min(a for a, _ in W)
    enc = T2.build_encoder("lag_local_tokens", 20, 32, [(a - lo, b - lo) for a, b in W], 250)
    (starts, w), = L.branch_starts(enc, W, rebase=50)
    assert starts[:3] == [0, 5, 10] and w == 10 and len(starts) == 29
    for win in ("early", "late"):
        assert L.tokens_in_window(starts, w, "private_bdf", win) == L.WINDOW_TOKENS["private_bdf"][win]
    assert L.NEG_OFFS["private_bdf"][0] == -50 and len(L.NEG_OFFS["private_bdf"]) == 9
    assert len(L.NEG_OFFS["fau"]) == 8 and len(L.NEG_OFFS["federici"]) == 9


# ------------------------------------------------------------------------------------------------ toy cohort
class Coh:
    pass


def toy_cohort(seed=0, n_part=6, C=4, fs=100):  # C * w = 16 = audio dim (2 x 8 frames) so the native NCE einsum is defined
    rng = np.random.default_rng(seed)
    seg_len = 50; parts, segs = [], []
    stim = rng.normal(size=(2, 4000)).astype(np.float32)
    eeg = rng.normal(size=(C, 60000)).astype(np.float32)
    e = 30
    for p in range(n_part):
        parts.append({"id": f"P{p}", "group": "a" if p % 2 else "b", "fold": p % 3, "dev": False})
        for j in range(24):
            role = ("fit", "fit", "es", "test")[j % 4]
            uid = f"u{j % 12}"
            s0 = 100 + (j % 12) * 200
            segs.append({"p": p, "e0": e, "s0": s0, "s0_ign": None, "role": role, "kind": "ss", "uid": uid, "hard_key": "h", "part": str(j % 3),
                         "feat": stim[:, s0:s0 + seg_len].mean(1).tolist() + stim[:, s0:s0 + seg_len].std(1).tolist()})
            e += seg_len + 40
    coh = Coh(); coh.fs, coh.n_ch, coh.participants, coh.eeg, coh.stim, coh.segments = fs, C, parts, eeg, {"envelope": stim}, segs
    coh.meta = {"dataset": "federici", "seg_len": seg_len}
    return coh


class FlatEnc(torch.nn.Module):
    def __init__(self, W):
        super().__init__(); self.W = W

    def forward(self, patches):
        return torch.cat([p.flatten(1) for p in patches], 1)


def test_eval_sets_and_scoring_reproduce_evaluate_continuous():
    """pooled representation + original ridge through C.eval_sets / Targets / Scorer == ev1.evaluate_continuous unified."""
    from auditory_alignment_v3.sci_r1.probe import Ev1Scorer, ev1_targets
    coh = toy_cohort()
    W = [(0, 4)]; sf, seed, grid = 1, 7, 2
    bank = C.Bank(coh, ["envelope"])

    class BT:  # minimal Batcher for ev1
        pass
    bt = BT(); bt.dev = torch.device("cpu"); bt.W = W; bt.seg_len = 50; bt.kind = "ss"
    bt.train_p = {i for i, p in enumerate(coh.participants) if p["fold"] != sf}
    bt.patches = lambda e: bank.patches(e.numpy(), W)
    bt.audio = lambda s: torch.as_tensor(bank.audio(s.numpy(), "envelope"))
    enc = FlatEnc(W); aud = torch.nn.Identity()
    import functools
    orig = ev1.Reps; ev1.Reps = functools.partial(orig, stride=grid)
    orig_dep = ev1.test_cs_dependence; ev1.test_cs_dependence = lambda *a, **k: None
    try:
        ref = ev1.evaluate_continuous("NCE", enc, aud, bt, coh, {"subject_fold": sf}, np.random.default_rng(seed + 1000), {"sigma_u": 1, "sigma_v": 1})
    finally:
        ev1.Reps = orig; ev1.test_cs_dependence = orig_dep
    offs = np.arange(0, 50, grid); T = len(offs)
    ev = C.eval_sets(bank, sf, seed)
    tg = ev1_targets(bank, ev, "envelope", offs)
    U = {s: np.concatenate([enc(bank.patches(C.e_index(rows, offs), W)).numpy()]) for s, rows in (("tr", ev["tr"]), ("es", ev["q_es"]), ("te", ev["queries"]))}
    sc = Ev1Scorer(ev, tg, T)
    rr = sc.fit(U["tr"]); tau = sc.tau(rr, U["es"])
    got = sc.per_participant(sc.test_scores(rr, U["te"]), tau)
    for j, pid in enumerate(ev["ids"]):
        r = ref["per_participant"][pid]
        g = r["unified/mismatched_eeg"]["logloss_bits"] - r["unified/regular"]["logloss_bits"]
        assert got[j, 0] == pytest.approx(g, abs=1e-5)
    assert sorted(ev["ids"]) == sorted(ref["per_participant"])
    assert rr.alpha == pytest.approx(ref["readout"]["alpha_unified"])
