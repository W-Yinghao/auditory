"""R34_ATTENTION_ORDER v2 synthetic checks (private/auditory_alignment_v3/aln34/ATTENTION_ORDER_NOTE.md, sections 6, 10 and 11).

- swap antisymmetry of the new score: l(-d) = -l(d), p(-d) = 1 - p(d);
- no label leakage through candidate position: both presentations of a window share its split side, swap-invariant features carry no
  label information, a position-only logit scores exactly chance under paired orders (but 1 or 0 in the legacy fixed-order test), and
  fixed - paired = 0.5[P(s > |a|) - P(s < -|a|)];
- agreement with the package reference src/aln34_reference/attention.py (summaries, antisymmetric logit, paired-order accuracy / logloss,
  ties) and with the frozen run_attention legacy integrator (segment lists, windows, margins, accuracies, flip stream and coefficients);
- v2 (note 11.4): the scaled antisymmetric fit does not collapse at the native-CS scale of d (the legacy settings do), its decisions do
  not depend on the scale of d, zero fits get their own status and are never scored, contrasts are paired at the unit level;
- v2 (note 11.5 / 11.12): QC tiers (tier 2 inactive while kappa is None), device mismatch never enters tier 1, device guard;
- v2 (note 11.6): empty reproductions are reported as not established; the panel reconciliation reproduces d_multiseed's construction;
- end-to-end score extraction on CPU on tiny synthetic cohorts with the real lag encoder and the real dense / complement policy-arm
  checkpoints (CBraMod), against run_attention.attention_windows / run_attention_policy._windows; aggregation and report on
  synthetic score files.
No EEG is read.
"""
import copy
import importlib.util
import json
import os
import stat
import types

import numpy as np
import pytest
import torch

from auditory_alignment_v3 import run_attention as RA
from auditory_alignment_v3.aln34 import attention_order as AO

REF = os.path.join(AO.REPO, "AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016", "src", "aln34_reference", "attention.py")


def _ref():
    spec = importlib.util.spec_from_file_location("aln34_reference_attention", REF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mode600(p):
    return stat.S_IMODE(os.stat(p).st_mode) == 0o600


# ------------------------------------------------------------------------------------------------ scoring math
@pytest.mark.parametrize("k", [1, 2, 4])
def test_summaries_match_legacy_and_reference(k):
    D = np.random.default_rng(k).normal(size=(60, k))
    S = AO.summaries(D)
    np.testing.assert_array_equal(S, np.array([RA._summ(d) for d in D]))
    np.testing.assert_array_equal(S, _ref().summaries(D))


def test_antisymmetry_p_minus_d_is_one_minus_p():
    rng = np.random.default_rng(0)
    Dtr, Dte = rng.normal(0.3, 1.0, (400, 4)), rng.normal(0.1, 1.0, (200, 4))
    fit = AO.fit_antisymmetric(Dtr)
    assert fit["status"] == "ok"
    lo = AO.antisym_scorer(fit)
    np.testing.assert_array_equal(lo(-Dte), -lo(Dte))
    np.testing.assert_allclose(AO.sigmoid(lo(-Dte)), 1.0 - AO.sigmoid(lo(Dte)), rtol=0, atol=1e-15)
    h = lambda D: 3.0 + 5.0 * D.std(1) + D[:, 0] - 0.2 * D.max(1)          # any h, deliberately not antisymmetric
    np.testing.assert_array_equal(AO.antisymmetric_logit(h, -Dte), -AO.antisymmetric_logit(h, Dte))
    la = lo(Dte)                                                         # both presentations earn the same credit
    np.testing.assert_array_equal(AO.order_credit(la, -la), (la > 0) + 0.5 * (la == 0))


def test_matches_reference_attention_semantics():
    ref = _ref()
    rng = np.random.default_rng(1)
    D = rng.normal(0.2, 1.0, (300, 4))
    coef, b0 = [0.8, -2.0, 0.3, 0.1, 0.2], 0.7                           # intercept, sd and unequal min/max weights: order-dependent
    h = lambda X: AO.linear_logit(coef, b0, X)
    r = ref.paired_order_metrics(h, D)
    lp, lm = h(D), h(-D)
    assert r["n_physical_windows"] == len(D)
    assert abs(AO.order_credit(lp, lm).mean() - r["accuracy"]) < 1e-12
    assert abs(AO.order_logloss_bits(lp, lm).mean() - r["logloss_bits"]) < 1e-12
    assert r["swap_logit_error_max"] > 0.1                               # the legacy-type logit is not swap-consistent
    np.testing.assert_array_equal(AO.antisymmetric_logit(h, D), ref.antisymmetric_logit(h, D))
    lo = AO.antisym_scorer(AO.fit_antisymmetric(D[:200]))
    r2 = ref.paired_order_metrics(lo, D[200:])
    assert r2["swap_logit_error_max"] == 0.0
    assert abs(AO.order_credit(lo(D[200:]), -lo(D[200:])).mean() - r2["accuracy"]) < 1e-12
    assert abs(AO.order_logloss_bits(lo(D[200:]), -lo(D[200:])).mean() - r2["logloss_bits"]) < 1e-12
    z = lambda X: np.zeros(len(X))                                       # ties: tie_credit 0.5 in both
    assert ref.paired_order_metrics(z, D)["accuracy"] == 0.5 == AO.order_credit(z(D), z(-D)).mean() == AO.TIE_CREDIT
    m = np.r_[0.0, 1.0, -1.0]
    np.testing.assert_array_equal(AO.order_credit(m, -m), [0.5, 1.0, 0.0])


# ------------------------------------------------------------------------------------------------ candidate position / leakage
def test_position_only_logit_is_chance_under_paired_orders():
    D = np.random.default_rng(2).normal(0.0, 1.0, (500, 2))
    for b0 in (5.0, -5.0):                                               # 'the first candidate is attended' / 'the second'
        lp = lm = np.full(len(D), b0)
        assert AO.legacy_fixed_correct(lp).mean() == (1.0 if b0 > 0 else 0.0)   # the fixed-order test rewards / punishes position
        assert AO.order_credit(lp, lm).mean() == 0.5
    coef, b0 = [1.0, 2.0, 0.0, 0.5, 0.0], -1.0                           # mixed logit: exact decomposition of the order bias
    cell, _ = AO.evaluate_cell(np.zeros((0, 2)), D, {"coef": coef, "intercept": b0})
    lhs = (cell["lt_fixed_logit"] - cell["lt_paired"]).mean()
    rhs = 0.5 * (cell["pos_plus"] - cell["pos_minus"]).mean()
    assert abs(lhs - rhs) < 1e-12 and abs(rhs) > 0.01


def test_paired_training_set_carries_no_order_information():
    D = np.random.default_rng(3).normal(0.4, 1.0, (100, 4))
    X, y, w, win = AO.paired_training_set(D)
    assert np.bincount(win).tolist() == [2] * 100                        # each physical window twice, on the same (training) side
    for j in range(100):
        r = np.flatnonzero(win == j)
        assert sorted(y[r].tolist()) == [0, 1] and w[r].sum() == 1.0
        assert X[r[0], 1] == X[r[1], 1]                                  # sd identical in both orders
        assert X[r[0], 3] - X[r[0], 2] == X[r[1], 3] - X[r[1], 2]          # range identical in both orders
    for f in (X[:, 1], X[:, 3] - X[:, 2]):                               # swap-invariant features: identical label-conditional means
        assert abs(f[y == 1].mean() - f[y == 0].mean()) < 1e-12


def test_fit_uses_training_windows_only():
    rng = np.random.default_rng(4)
    Dtr, Dte = rng.normal(0.3, 1.0, (300, 4)), rng.normal(0.3, 1.0, (50, 4))
    _, f1 = AO.evaluate_cell(Dtr, Dte)
    _, f2 = AO.evaluate_cell(Dtr, 1000.0 * Dte + 7.0)
    assert f1["status"] == f2["status"] == "ok"
    assert f1["coef_scaled"] == f2["coef_scaled"] and f1["intercept"] == f2["intercept"] and f1["sigma"] == f2["sigma"]


def test_paired_training_removes_symmetric_part_and_5s_equals_mean_score():
    rng = np.random.default_rng(5)
    f = AO.fit_antisymmetric(rng.normal(0.3, 1.0, (2000, 4)))
    assert f["status"] == "ok" and f["sym_over_antisym_train"] < 1e-6      # tight tolerance: the exact optimum has no symmetric part
    cell, f1 = AO.evaluate_cell(rng.normal(0.5, 1.0, (500, 1)), rng.normal(0.05, 1.0, (300, 1)))
    assert f1["status"] == "ok" and f1["coef_sum_5s"] > 0
    np.testing.assert_array_equal(cell["as"], cell["ms"])                # one segment: a threshold, identical to mean_score


# ------------------------------------------------------------------------------------------------ v2: scaling, convergence, statuses
def _legacy_unscaled_fit(Dtr):
    """v1's fit: legacy estimator settings (tol 1e-4) on unscaled summaries."""
    from sklearn.linear_model import LogisticRegression
    X, y, w, _ = AO.paired_training_set(Dtr)
    return LogisticRegression(**AO.LR_KW).fit(X, y, sample_weight=w)


@pytest.mark.parametrize("scale", [1e-4, 3e-4])
def test_v1_collapses_at_native_cs_scale_and_v2_does_not(scale):
    rng = np.random.default_rng(6)
    Z, Zte = rng.normal(0.3, 1.0, (600, 4)), rng.normal(0.3, 1.0, (300, 4))
    old = _legacy_unscaled_fit(scale * Z)                                 # the verifier's finding, reproduced
    assert int(old.n_iter_[0]) == 0 and not np.any(old.coef_)
    la_old = AO.antisymmetric_logit(lambda X: AO.linear_logit(old.coef_[0], old.intercept_[0], X), scale * Zte)
    assert np.all(la_old == 0) and AO.order_credit(la_old, -la_old).mean() == 0.5   # every window a tie
    fit = AO.fit_antisymmetric(scale * Z)
    assert fit["status"] == "ok" and fit["n_iter"] > 0 and abs(fit["antisym_weights_scaled"]["mean"]) > 0
    la = AO.antisym_scorer(fit)(scale * Zte)
    assert np.all(la != 0) and AO.order_credit(la, -la).mean() > 0.5


def test_v2_decisions_do_not_depend_on_the_scale_of_d():
    rng = np.random.default_rng(7)
    Z, Zte = rng.normal(0.15, 1.0, (800, 4)), rng.normal(0.15, 1.0, (400, 4))
    dec = {}
    for c in (1e-4, 3e-4, 1e-3, 1.0, 1e3):
        fit = AO.fit_antisymmetric(c * Z)
        assert fit["status"] == "ok"
        np.testing.assert_allclose(fit["coef_scaled"], AO.fit_antisymmetric(Z)["coef_scaled"], rtol=1e-6, atol=1e-7)   # symmetric weights ~1e-8 (optimiser residual)
        dec[c] = np.sign(AO.antisym_scorer(fit)(c * Zte))
    for c in dec:
        np.testing.assert_array_equal(dec[c], dec[1.0])
    # the v2 fit agrees with a tight-tolerance optimum of the same scaled problem (decisions)
    from sklearn.linear_model import LogisticRegression
    sig = AO.train_scale(Z)
    X, y, w, _ = AO.paired_training_set(Z / sig)
    tight = LogisticRegression(C=1.0, tol=1e-14, max_iter=100000).fit(X, y, sample_weight=w)
    lt = AO.antisymmetric_logit(lambda D: AO.linear_logit(tight.coef_[0], tight.intercept_[0], D / sig), Zte)
    np.testing.assert_array_equal(np.sign(lt), dec[1.0])


def test_zero_fit_and_zero_scale_get_their_own_status_and_are_never_scored():
    rng = np.random.default_rng(8)
    Z = rng.normal(0.3, 1.0, (100, 4))
    sym = np.vstack([Z, -Z])                                              # no antisymmetric signal at all: exact zero gradient
    f = AO.fit_antisymmetric(sym)
    assert f["status"] == "zero_fit" and f["n_iter"] == 0
    cell, f2 = AO.evaluate_cell(sym, Z)
    assert f2["status"] == "zero_fit" and "as" not in cell and "ll_as" not in cell
    cell, f3 = AO.evaluate_cell(np.zeros((50, 4)), Z)
    assert f3["status"] == "zero_scale" and "as" not in cell
    cell, f4 = AO.evaluate_cell(Z[:10], Z)
    assert f4["status"] == "no_fit" and "as" not in cell
    assert set(AO.FIT_STATUSES) == {"ok", "zero_fit", "not_converged", "zero_scale", "no_fit"}


def test_contrasts_are_paired_at_the_unit_level():
    acc = AO.Acc()
    x_ok = {"n_windows": 10, "ms": 0.6, "ms_fixed": 0.6, "margin": 0.1, "lt_fixed": 0.5, "lt_paired": 0.55, "as": 0.7}
    x_zero = {"n_windows": 10, "ms": 0.9, "ms_fixed": 0.9, "margin": 0.2, "lt_fixed": 0.8, "lt_paired": 0.85}   # 'as' missing (zero fit)
    fits_ok = {f"{L}s|{kr}": {"status": "ok"} for L in AO.SECONDS for kr in AO.READOUTS}
    fits_zero = {f"{L}s|{kr}": {"status": "zero_fit"} for L in AO.SECONDS for kr in AO.READOUTS}
    acc.add_unit(AO.LAG, "dtu", "attended_alignment", "NCE", 3401, {"P1": {"10s|unified": x_ok}}, fits_ok)
    acc.add_unit(AO.LAG, "dtu", "attended_alignment", "NCE", 3401, {"P1": {"10s|unified": x_zero}}, fits_zero)
    vals, _ = AO.contrast_vals(acc)
    R = ("AOP", "AO-ANTISYM", AO.LAG, "dtu", "attended_alignment", "NCE", "ref", 10, 3401)
    C = ("AOP", "AO-ANTISYM", AO.LAG, "dtu", "attended_alignment", "NCE", "cand", 10, 3401)
    assert vals[R]["P1"]["acc"] == 0.6 and vals[C]["P1"]["acc"] == 0.7     # the zero-fit unit leaves both sides
    Rl = ("AOP", "AO-PAIRED-LEGACY", AO.LAG, "dtu", "attended_alignment", "NCE", "ref", 10, 3401)
    assert vals[Rl]["P1"]["acc"] == pytest.approx(0.75)                  # ... but stays in the legacy contrast
    assert acc.excl[("AO-ANTISYM", AO.LAG, "dtu", "attended_alignment", "NCE", 3401, 10, "unified", "zero_fit")] == 1


def test_legacy_flip_stream_vectorises():
    a = np.random.default_rng(3401 + 4242)
    b = np.random.default_rng(3401 + 4242)
    assert np.array_equal(np.array([a.random() for _ in range(500)]), b.random(500))


# ------------------------------------------------------------------------------------------------ against the frozen legacy integrator
class _FakeReps:
    def __init__(self, enc, aud, bt, stride=4, chunk=2048):
        pass

    def u(self, e0s):
        return np.asarray(e0s, np.float64)[:, None, None]

    def va(self, s0s):
        a = np.asarray(s0s, np.float64)[:, None, None]
        return a, a


def _fake_readouts(table):
    class _R:
        alpha_uni = 1.0

        def __init__(self, objective, reps, train_segs, rng, **kw):
            pass

        def scores(self, Uq, Vc, Ac, kind):
            return np.array([[table[(int(Uq[0, 0, 0]), int(Vc[0, 0, 0]), kind)]]])
    return _R


def _fake_cohort(seed, n_train=6, n_test=5, trials=3, per_trial=9, seg=640):
    """Competing-speech segments in runs (a gap after 5 segments -> runs of 5 and 4) + a few single-speaker segments; d per segment
    = table[attended] - table[ignored]."""
    rng = np.random.default_rng(seed)
    parts = [{"id": f"P{i:02d}", "group": "nh" if i % 2 else "hi", "fold": 1 + i % 3} for i in range(n_train)] + \
            [{"id": f"T{i:02d}", "group": "nh" if i % 2 else "hi", "fold": 0} for i in range(n_test)]
    segs, table, e0, s0 = [], {}, 0, 10 ** 6
    for p, part in enumerate(parts):
        bias = rng.normal(0.0, 0.3)
        for t in range(trials):
            role = "test" if part["fold"] == 0 else ("es" if t == 0 else "fit")
            for j in range(per_trial):
                e = e0 + j * seg + (seg if j >= 5 else 0)
                sa, si = s0, s0 + 1; s0 += 2
                d = {"unified": rng.normal(0.25 + bias, 1.0), "native": rng.normal(4.0, 25.0)}
                for kr in AO.READOUTS:
                    table[(e, sa, kr)], table[(e, si, kr)] = d[kr] + 0.5, 0.5
                segs.append({"p": p, "e0": e, "s0": sa, "s0_ign": si, "role": role, "kind": "cs", "code": f"c{t}", "uid": f"c{t}@{j}"})
            e0 += (per_trial + 3) * seg
        for j in range(2):
            segs.append({"p": p, "e0": e0, "s0": s0, "s0_ign": None, "role": "fit", "kind": "ss", "code": "s", "uid": f"s@{j}"})
            e0 += seg; s0 += 1
    coh = types.SimpleNamespace(segments=segs, participants=parts)
    bt = types.SimpleNamespace(train_p={p for p, q in enumerate(parts) if q["fold"] != 0}, seg_len=seg)
    return coh, bt, table


def _legacy_and_new(monkeypatch, seed=11, run_seed=3401):
    from auditory_alignment import evaluate as ev1
    coh, bt, table = _fake_cohort(seed)
    monkeypatch.setattr(ev1, "Reps", _FakeReps)
    monkeypatch.setattr(ev1, "Readouts", _fake_readouts(table))
    b = {"spec": {"objective": "NCE"}, "seed": run_seed, "subject_fold": 0}
    legacy = json.loads(json.dumps(RA.attention_windows(b, None, None, bt, coh, 1), default=float))   # as stored in a unit record
    arrays, info = AO.legacy_attention_scores(b, None, None, bt, coh, 1)
    return legacy, AO.scores_from_arrays(arrays), arrays, info


def test_reproduces_frozen_run_attention(monkeypatch):
    legacy, sc, arrays, info = _legacy_and_new(monkeypatch)
    assert {L: {"train": len(sc["win_train"][L]), "test": len(sc["win_test"][L])} for L in AO.SECONDS} == \
        {L: legacy["window_counts"][str(L)] for L in AO.SECONDS}
    assert all(len(sc["win_train"][L]) >= AO.MIN_TRAIN_WINDOWS for L in AO.SECONDS)
    np.testing.assert_array_equal(sc["d"]["unified"], sc["s_att"]["unified"] - sc["s_ign"]["unified"])
    per, fits = AO.evaluate_unit(sc, legacy)
    for p, r in legacy["per_participant"].items():
        for key, v in r.items():
            if isinstance(v, dict):
                x = per[p][key]
                assert x["n_windows"] == v["n_windows"]
                assert x["margin"] == v["mean_margin"] and x["ms_fixed"] == v["mean_score_accuracy"]
                assert x["lt_fixed"] == v["learned_temporal_accuracy"] and x["rms_s"] > 0
    refit = AO.legacy_refit(sc, 3401)
    for k, v in legacy["integrators"].items():                          # same flip stream, same windows -> same coefficients
        assert refit[k]["coef"] == v["coef"] and refit[k]["intercept"] == v["intercept"]
    qc = AO.unit_qc(sc, per, legacy, refit)
    assert qc["pass"] and qc["tier"] == 1 and not qc["flags"] and max(qc["max_errors"].values()) == 0.0
    test_ids = set(arrays["test_part_id"].tolist())                     # test windows never enter a fit; both orders on the test side
    for L in AO.SECONDS:
        assert not set(sc["seg_pid"][sc["win_train"][L].ravel()].tolist()) & test_ids
        assert set(sc["seg_pid"][sc["win_test"][L].ravel()].tolist()) <= test_ids
        assert fits[f"{L}s|unified"]["n_train_windows"] == legacy["window_counts"][str(L)]["train"]
        assert fits[f"{L}s|unified"]["status"] == "ok"


def test_qc_tiers_and_device_mismatch(monkeypatch):
    legacy, sc, _, _ = _legacy_and_new(monkeypatch)
    per, _ = AO.evaluate_unit(sc, legacy)
    tol2_on = dict(AO.QC_TOL2, kappa_rms_s=1e-2)
    assert AO.QC_TOL2["kappa_rms_s"] is None                             # tier 2 inactive in v2 (note 11.12)
    sc2 = copy.deepcopy(sc); sc2["d"]["unified"] = sc2["d"]["unified"] + 1e-4   # numerics-size shift: tier 1 fails
    per2, _ = AO.evaluate_unit(sc2, legacy)
    q = AO.unit_qc(sc2, per2, legacy)
    assert not q["pass"] and q["tier"] == 0 and any("mean margin" in r for r in q["reasons"])
    assert AO.unit_qc(sc2, per2, legacy, tol2=tol2_on)["tier"] == 2      # would be tier 2 if kappa were set
    sc3 = copy.deepcopy(sc); sc3["d"]["unified"] = sc3["d"]["unified"] + 0.5     # configuration-size error: never included
    per3, _ = AO.evaluate_unit(sc3, legacy)
    assert AO.unit_qc(sc3, per3, legacy, tol2=tol2_on)["tier"] == 0
    sc4 = copy.deepcopy(sc); sc4["meta"] = {"checkpoint": {"manifest_match": True}, "stats_qc": {"sd_max_rel": 0.0, "mu_max_over_sd": 0.0}, "device_match": False}
    q4 = AO.unit_qc(sc4, per, legacy, tol2=tol2_on)
    assert not q4["pass"] and q4["device_mismatch"] and q4["tier"] == 2  # a device-mismatched extraction never enters tier 1
    assert AO.unit_qc(sc4, per, legacy)["tier"] == 0
    sc5 = copy.deepcopy(sc4); sc5["meta"]["device_match"] = True; sc5["win_test"][10] = sc5["win_test"][10][:-1]
    per5, _ = AO.evaluate_unit(sc5, legacy)
    assert AO.unit_qc(sc5, per5, legacy, tol2=tol2_on)["tier"] == 0     # structural mismatch: excluded in every tier


# ------------------------------------------------------------------------------------------------ end-to-end extraction on CPU (tiny input)
def _tiny_cohort(seed=0, n_ch=31, ds="fau", cf=0):
    from auditory_alignment.data import Cohort
    rng = np.random.default_rng(seed)
    fs, C, seg = 128, n_ch, 640
    parts = [{"id": f"p{i}", "group": g, "fold": f, "dev": False} for i, (g, f) in enumerate([("th", 1), ("ha", 2), ("ci", 3), ("th", 0)])]
    segs, E, S = [], 0, 0
    for p, part in enumerate(parts):
        for t in range(2):
            role = "test" if part["fold"] == 0 else ("fit" if t == 0 else "es")
            for j in range(4):
                segs.append({"p": p, "e0": E + j * seg, "s0": S + j * seg, "s0_ign": S + 4 * seg + 100 + j * seg, "role": role, "kind": "cs",
                             "uid": f"2{t}@{j}", "hard_key": "x", "part": "0", "code": f"2{t}"})
            E += 4 * seg + 200; S += 8 * seg + 300
        for t in range(2):
            for j in range(2):
                segs.append({"p": p, "e0": E + j * seg, "s0": S + j * seg, "s0_ign": None, "role": "fit" if t == 0 else "es", "kind": "ss",
                             "uid": f"1{t}@{j}", "hard_key": "x", "part": "0", "code": f"1{t}"})
            E += 2 * seg + 200; S += 2 * seg + 100
    eeg = rng.standard_normal((C, E)).astype(np.float32)
    stim = {"Local": rng.standard_normal((6, S)).astype(np.float32)}
    for s in segs:
        s["feat"] = np.zeros(2)
    return Cohort(fs, C, parts, eeg, stim, segs, {"dataset": ds, "content_fold": cf, "seg_len": seg})


def test_extract_unit_end_to_end_cpu(tmp_path):
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v3 import core, local_train
    dev = torch.device("cpu")
    eid = "ALN3_test_attention_order"
    row = {"experiment_id": eid, "family_id": "D_ATTENTION", "dataset": "fau", "subject_fold": 0, "content_fold": 0, "seed": 3401,
           "spec": {"architecture": "lag_local_tokens", "integrator": "mean_score", "objective": "NCE", "projection_dim": 32, "target": "local",
                    "training_task": "attended_alignment", "evaluation_seconds": [5, 10, 20]}}
    b = AO.bound_row(row)
    coh = _tiny_cohort(); g = core.grid_samples(coh.fs)
    bt = local_train.GridBatcher(coh, b["spec"], b, dev, g)
    torch.manual_seed(0)
    enc = build_encoder("lag_local_tokens", coh.n_ch, 32, bt.W, coh.fs)
    head = build_head("fixed_features", bt.audio_dim, 32, "fau", target_stats(bt, np.random.default_rng(b["seed"] + 5)))
    enc.eval(); head.eval()
    with torch.no_grad():
        legacy = json.loads(json.dumps(RA.attention_windows(b, enc, head, bt, coh, g), default=float))
    out, ck = tmp_path / "private", tmp_path / "ckpt"
    (out / "units").mkdir(parents=True); ck.mkdir()
    fname = f"{eid}_best.pt"
    torch.save({"enc": enc.state_dict(), "head": head.state_dict()}, ck / fname)
    rec = {"experiment_id": eid, "status": "complete", "code_hash": "test", "code_group": "attention", "device": "cpu", "bound_row": b,
           "eval": {"attention_windows": legacy}}
    (out / "units" / f"{eid}.json").write_text(json.dumps(rec))
    cache = AO.CohortCache(dev, loader=lambda b_: _tiny_cohort())
    scores = tmp_path / "scores"
    man = {fname: AO.sha256_file(str(ck / fname))}
    jp = AO.extract_unit(row, "ALN3_twin", cache, dev, scores_dir=str(scores), out=str(out), man=man, ckpt_dir=str(ck))
    meta = json.load(open(jp))
    assert meta["checkpoint"]["manifest_match"] and meta["window_counts_match_record"] and meta["evaluation_version"] == AO.EVAL_VERSION
    assert meta["device_match"] and meta["binding_matches_reconstruction"] and meta["numerics"]["device"] == "cpu"
    assert {"torch", "cudnn_allow_tf32", "matmul_allow_tf32"} <= set(meta["numerics"])
    assert meta["stats_qc"]["mu_max_abs"] == 0.0 and meta["stats_qc"]["mu_max_over_sd"] == 0.0 and meta["stats_qc"]["sd_max_rel"] == 0.0
    assert _mode600(jp) and _mode600(str(scores / f"{eid}.npz"))
    sc = AO.load_scores(str(scores), eid)
    per, fits = AO.evaluate_unit(sc, legacy)
    qc = AO.unit_qc(sc, per, legacy, AO.legacy_refit(sc, 3401))
    assert qc["pass"] and max(qc["max_errors"].values()) == 0.0, qc
    assert fits["5s|unified"]["status"] in ("ok", "zero_fit", "not_converged") and fits["10s|unified"]["status"] == "no_fit"   # < 20 windows: legacy has no integrator either
    assert AO.extract_unit(row, "ALN3_twin", cache, dev, scores_dir=str(scores), out=str(out), ckpt_dir=str(ck)) == jp   # skip when present
    rec["device"] = "NVIDIA A40"; (out / "units" / f"{eid}.json").write_text(json.dumps(rec))       # device guard
    with pytest.raises(AO.DeviceMismatch):
        AO.extract_unit(row, "ALN3_twin", cache, dev, scores_dir=str(tmp_path / "s2"), out=str(out), man=man, ckpt_dir=str(ck))
    jp2 = AO.extract_unit(row, "ALN3_twin", cache, dev, scores_dir=str(tmp_path / "s2"), out=str(out), man=man, ckpt_dir=str(ck), allow_device_mismatch=True)
    sc2 = AO.load_scores(str(tmp_path / "s2"), eid)
    assert json.load(open(jp2))["device_match"] is False
    q2 = AO.unit_qc(sc2, AO.evaluate_unit(sc2, legacy)[0], legacy)
    assert q2["device_mismatch"] and not q2["pass"]
    cache.release()


POLICY_UNITS = [("ALN3_9f9b6ff8587cf546", "dense_fm_policy"),   # FAU, CBraMod pretrained_full, dense_query, CS_SINGLE
                ("ALN3_9ffd0be6d1fe9cec", "complement_policy"),  # FAU, CBraMod residual_pretrained_full, NCE
                ("ALN3_1a30e54b5f7d4331", "dense_fm_policy"),    # FAU, REVE pretrained_peft (LoRA), channel_phase_linear, NCE
                ("ALN3_4fa4894c702f0d39", "complement_policy"),  # FAU, REVE concat_pretrained, NCE
                ("ALN3_893f044794111f5e", "dense_fm_policy"),    # FAU, REVE pretrained_peft, alignment_plus_selection (chosen candidate _c0)
                ("ALN3_3974a9eed1d6cfc4", "complement_policy")]  # FAU, REVE concat_pretrained, alignment_plus_selection


@pytest.mark.parametrize("eid,arm", POLICY_UNITS)
def test_policy_arm_extraction_matches_run_attention_policy_cpu(eid, arm, tmp_path):
    """Real policy-arm checkpoint (strict load into the rebuilt DenseFM / Complement), tiny synthetic cohort, CPU: the recomputed
    scores reproduce run_attention_policy._windows (= the frozen attention_windows on FM representations) exactly."""
    from auditory_alignment_v3 import fm_complement, fm_dense
    from auditory_alignment_v3 import run_attention_policy as RAP
    rec = AO.load_record(eid)
    if rec is None or rec.get("status") != "complete":
        pytest.skip("record not available")
    rows = AO._all_rows()
    row = next(r for r in rows if r["experiment_id"] == eid)
    fname, _ = AO.checkpoint_file(row, rec)
    dep = AO.dependency_files(row, rec, rows)
    if not os.path.exists(os.path.join(AO.OUT, "ckpt", fname)) or not all(os.path.exists(os.path.join(AO.OUT, "ckpt", f)) for f in dep.values() if f):
        pytest.skip("checkpoint not available")
    torch.set_num_threads(2)
    dev = torch.device("cpu")
    b = copy.deepcopy(rec["bound_row"])
    cache = AO.CohortCache(dev, loader=lambda b_: _tiny_cohort(n_ch=31, ds=b_["dataset"], cf=b_["content_fold"]))
    coh = cache.get(b)
    reps, bt, info = AO.build_unit_model(row, rec, b, coh, cache, dev, os.path.join(AO.OUT, "ckpt"), rows)   # strict state-dict loads
    assert isinstance(reps, fm_dense.DenseReps if arm == AO.DENSE else fm_complement.CompReps)
    assert info["stats_qc"] is not None and info["dependency_file"] == (dep.get("base") or dep.get("lag_twin"))
    model, head = reps.model, reps.aud
    reps_cls = fm_dense.DenseReps if arm == AO.DENSE else fm_complement.CompReps
    with torch.no_grad():
        legacy = json.loads(json.dumps(RAP._windows(b, model, head, bt, coh, info["grid"], reps_cls), default=float))
        arrays, _ = AO.legacy_attention_scores(b, None, None, bt, coh, info["grid"], reps=reps)
    sc = AO.scores_from_arrays(arrays)
    per, fits = AO.evaluate_unit(sc, legacy)
    qc = AO.unit_qc(sc, per, legacy, AO.legacy_refit(sc, b["seed"]))
    assert qc["pass"] and max(qc["max_errors"].values()) == 0.0, qc
    cache.release()


@pytest.mark.parametrize("eid,ds,n_ch", [("ALN3_44093548e46f8d49", "fau", 31), ("ALN3_ef62d70847871c28", "dtu", 64)])
def test_real_checkpoint_matches_rebuilt_architecture(eid, ds, n_ch):
    from auditory_alignment_v2.audio_targets import build_head
    from auditory_alignment_v2.temporal import build_encoder, window_ranges
    p = os.path.join(AO.OUT, "ckpt", f"{eid}_best.pt")
    if not os.path.exists(p):
        pytest.skip("checkpoint not available")
    sd = torch.load(p, map_location="cpu", weights_only=True)
    enc = build_encoder("lag_local_tokens", n_ch, 32, window_ranges("lag_local_tokens", ds, "full", 128), 128)
    head = build_head("fixed_features", 48, 32, ds, (np.zeros(48, np.float32), np.ones(48, np.float32)))
    enc.load_state_dict(sd["enc"]); head.load_state_dict(sd["head"])


# ------------------------------------------------------------------------------------------------ reproduction / reconciliation
def _att_vals(rng, ids, ds="dtu", task="attended_alignment", obj="NCE", shift=-0.02):
    vals = {}
    for L in AO.SECONDS:
        ms = {i: {"acc": float(rng.uniform(0.5, 0.9)), "acc_native": float(rng.uniform(0.4, 0.8))} for i in ids}
        lt = {i: {"acc": ms[i]["acc"] + float(rng.normal(shift, 0.01)), "acc_native": ms[i]["acc_native"] + float(rng.normal(-0.1, 0.05))} for i in ids}
        vals[("ATT", ds, task, obj, "ms", L)], vals[("ATT", ds, task, obj, "lt", L)] = ms, lt
    return vals


def test_reproduce_old_uses_the_original_labels_and_draws(tmp_path):
    from auditory_alignment_v3 import bc_interim as BI
    for m in ("acc", "acc_native"):
        BI.PDIR.setdefault(m, "higher")
    ids = [f"sub-{i:03d}" for i in range(12)]
    vals = _att_vals(np.random.default_rng(7), ids)
    label = "AT-INTEGRATOR|dtu|attended_alignment|NCE"                   # d_lag_interim.att_families() label and member names
    members = AO._att_members("dtu", "attended_alignment", "NCE")
    old = BI.run_family(label, members, vals, "acc", [], True)
    oldsec = {"acc_native": BI.run_family(f"{label}|sec", members, vals, "acc_native", [], False)}
    p = tmp_path / "d_lag.json"
    p.write_text(json.dumps({"attention": {"families": {label: old}, "secondary": {label: oldsec}}}, default=float))
    rep = AO.reproduce_old(vals, str(p), BI, [])
    assert rep["available"] and rep["members_compared"] == 3 and rep["max_abs_diff"] == 0.0 and rep["class_agreement"] == "3/3"
    assert rep["native"]["members_compared"] == 3 and rep["native"]["max_abs_diff"] == 0.0
    assert "3 members compared" in AO.repro_sentence(rep, "Seed 3401")
    vals2 = copy.deepcopy(vals); vals2[("ATT", "dtu", "attended_alignment", "NCE", "lt", 20)]["sub-000"]["acc"] += 0.1
    assert AO.reproduce_old(vals2, str(p), BI, [])["max_abs_diff"] > 0


def test_empty_reproduction_is_reported_as_not_established(tmp_path):
    from auditory_alignment_v3 import bc_interim as BI
    p = tmp_path / "d_lag.json"
    p.write_text(json.dumps({"attention": {"families": {}}}))
    rep = AO.reproduce_old({}, str(p), BI, [])
    assert rep["members_compared"] == 0 and rep["max_abs_diff"] is None
    s = AO.repro_sentence(rep, "Seed 3401")
    assert "not established" in s and "0.00e+00" not in s and "0/0" not in s
    assert "not established" in AO.repro_sentence(AO.reproduce_old({}, None, BI, []), "x")
    assert "not established" in AO.repro_sentence(AO.reconcile_panel({}, str(tmp_path / "missing.json"), BI, []), "x")


def test_reconcile_panel_reproduces_d_multiseed_construction(tmp_path):
    from auditory_alignment_v3 import bc_interim as BI
    DM = pytest.importorskip("auditory_alignment_v3.aln34.d_multiseed")
    DM.setup()
    rng = np.random.default_rng(9)
    ids = [f"S{i:02d}" for i in range(14)]
    by_seed = {s: _att_vals(rng, ids if s != 3413 else ids[:-2]) for s in AO.SEEDS}   # one seed with 2 identities missing
    label = "AT-INTEGRATOR|dtu|attended_alignment|NCE"
    fams = [{"family": "AT-INTEGRATOR", "scope": "dtu|attended_alignment|NCE", "label": label, "kind": "att",
             "members": AO._att_members("dtu", "attended_alignment", "NCE")}]
    notes = []
    grp = {("dtu", i): "x" for i in ids}
    per_seed = {str(s): DM.run_per_seed(fams, by_seed[s], grp, notes) for s in AO.SEEDS}
    sm, _ = DM.run_seed_mean(fams, by_seed, grp, notes)
    p = tmp_path / "d_multiseed.json"
    p.write_text(json.dumps({"meta": {"generated": "test"}, "per_seed": per_seed, "seed_mean": sm}, default=float))
    rep = AO.reconcile_panel(by_seed, str(p), BI, [])
    assert rep["available"] and rep["members_compared"] == 12 and rep["max_abs_diff"] == 0.0 and rep["class_agreement"] == "12/12"
    assert rep["native"]["members_compared"] == 12 and rep["native"]["max_abs_diff"] == 0.0


# ------------------------------------------------------------------------------------------------ unit list, plan
def test_unit_list_covers_every_completed_arm_and_groups_by_device(tmp_path):
    rows = AO._all_rows()
    p, n, plan = AO.write_unit_list(str(tmp_path / "units.txt"), rows=rows)
    assert _mode600(p)
    table, skipped = AO.unit_table(rows=rows)
    assert n == len(table) == len(AO.read_unit_list(p)) == len(set(AO.read_unit_list(p)))
    arms = {a: sum(u["arm"] == a for u in table) for a in AO.ARMS}
    assert arms[AO.LAG] == 180 and arms[AO.DENSE] + arms[AO.COMP] > 0
    assert all(u["partition"] in AO.DEVICE_PARTITION.values() for u in table)
    assert all(u["partition"] == "A40" for u in table if u["arm"] == AO.LAG)
    assert all(u["dep"] != "-" for u in table if u["arm"] == AO.COMP)
    txt = open(p).read()
    assert "--qos=runfill" in txt and "MaxTRESPU" in txt and "Do not run several stage-1 processes inside one job" in txt
    assert "four processes" not in txt and "any pool GPU" not in txt
    for part in plan:
        assert f"--partition={part}" in txt
    units = AO.unit_rows(rows)
    for ds in AO.DATASETS:
        for cf in (0, 1):
            args = types.SimpleNamespace(unit=None, unit_list=p, arm=AO.LAG, dataset=ds, content_fold=cf, shard=None)
            sel = AO._select(units, args)
            assert len(sel) == 45 and {(r["dataset"], r["content_fold"]) for r, _ in sel} == {(ds, cf)}
            assert sorted({r["seed"] for r, _ in sel}) == [3401, 3407, 3413]


# ------------------------------------------------------------------------------------------------ aggregation + report
def _synthetic_scores(tmp_path, monkeypatch, arms=(AO.LAG,), seeds=AO.SEEDS):
    from auditory_alignment import evaluate as ev1
    rows, recs, scores = [], {}, tmp_path / "scores"
    for arm in arms:
        for seed in (seeds if arm == AO.LAG else (3401,)):
            for fold in (0, 1):
                coh, bt, table = _fake_cohort(100 * seed + fold + 7 * AO.ARMS.index(arm))
                for p in coh.participants:                                 # fold-specific identities, 5 per fold
                    p["id"] = p["id"] if p["fold"] else f"{p['id']}f{fold}"
                monkeypatch.setattr(ev1, "Reps", _FakeReps); monkeypatch.setattr(ev1, "Readouts", _fake_readouts(table))
                b = {"spec": {"objective": "NCE"}, "seed": seed, "subject_fold": 0}
                aw = json.loads(json.dumps(RA.attention_windows(b, None, None, bt, coh, 1), default=float))
                arrays, _ = AO.legacy_attention_scores(b, None, None, bt, coh, 1)
                eid, twin = f"E{arm[:3]}{seed}_{fold}", f"T{arm[:3]}{seed}_{fold}"
                spec = {"architecture": arm, "objective": "NCE", "training_task": "attended_alignment"}
                rows.append({"experiment_id": eid, "family_id": "D_ATTENTION", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": seed,
                             "spec": {**spec, "integrator": "mean_score"}})
                rows.append({"experiment_id": twin, "family_id": "D_ATTENTION", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": seed,
                             "spec": {**spec, "integrator": "learned_temporal"}})
                recs[eid] = {"status": "complete", "eval": {"attention_windows": aw}}
                recs[twin] = {"status": "complete", "shared_model_with": eid}
                scores.mkdir(exist_ok=True)
                AO._write_npz(str(scores / f"{eid}.npz"), arrays)
                AO._write_json(str(scores / f"{eid}.json"), {"arm": arm, "checkpoint": {"manifest_match": True}, "stats_qc": {"mu_max_over_sd": 0.0, "sd_max_rel": 0.0},
                                                            "device_match": True, "numerics": {"device": "test"}})
    return rows, recs, scores


def test_analyze_end_to_end_synthetic(tmp_path, monkeypatch):
    rows, recs, scores = _synthetic_scores(tmp_path, monkeypatch, arms=(AO.LAG, AO.DENSE))
    res = AO.analyze(scores_dir=str(scores), res_dir=str(tmp_path / "res"), docs_dir=str(tmp_path / "docs"), rows=rows, load=recs.get,
                     old_d_lag=None, old_d_multi=None)
    sc = res["meta"]["status_counts"]
    assert sc == {**{f"{AO.LAG}|{s}|dtu|attended_alignment|NCE|included": 2 for s in AO.SEEDS}, f"{AO.DENSE}|3401|dtu|attended_alignment|NCE|included": 2}
    assert all(c["twin_shared_model"] for c in res["coverage"])
    fam = res["primary"]["attention_order"]["families"]
    for s in list(AO.SEEDS) + ["mean"]:
        for f in ("AO-ANTISYM", "AO-PAIRED-LEGACY"):
            m = fam[f"{f}|dtu|attended_alignment|NCE|{s}"]["members"]
            assert set(m) == {"5s", "10s", "20s"} and all(x["n"] == 10 for x in m.values())
        assert f"AO-FIXED|dtu|attended_alignment|NCE|{s}" not in fam       # lag arm: AO-FIXED only as the original-label reproduction
        assert fam[f"AO-ANTISYM|dtu|attended_alignment|NCE|{s}"]["members"]["5s"]["est"] == 0.0     # 5 s: antisymmetric = mean_score
    for f in ("AO-ANTISYM", "AO-PAIRED-LEGACY", "AO-FIXED"):               # policy arm: own labels incl. AO-FIXED, seed 3401 only
        assert f"{f}|{AO.DENSE}|dtu|attended_alignment|NCE|3401" in fam
    assert not any(k.startswith(f"AO-ANTISYM|{AO.DENSE}") and k.endswith("|mean") for k in fam)
    assert res["primary"]["seed_mean_coverage"][f"AO-ANTISYM|{AO.LAG}|dtu|attended_alignment|NCE|20s"]["identities_all_seeds"]["acc"] == 10
    assert "AO-ANTISYM|dtu|attended_alignment|NCE|10s" in res["primary"]["between_seed"]
    for k, r in res["primary"]["diagnostics"].items():                   # exact decomposition of the fixed-order bias
        if "fixed_minus_paired" in r:
            assert abs(r["fixed_minus_paired"]["mean"] - r["identity_rhs"]["mean"]) < 1e-12
    ll = res["primary"]["logloss"][f"{AO.LAG}|dtu|attended_alignment|NCE|3401|10s|unified"]
    assert ll["n"] == 10 and {"ci_low", "ci_high"} <= set(ll["antisym_minus_legacy"]) and {"ci_low", "ci_high"} <= set(ll["legacy_paired"])
    assert res["primary"]["reproduction_d_lag_3401"]["members_compared"] == 0 and res["sensitivity_tier2"] is None
    fd = res["antisymmetric_fit_diagnostics"][f"{AO.LAG}|10s|unified"]
    assert fd["n"] == 6 and fd["ok"] == 6
    doc = tmp_path / "docs" / "ATTENTION_ORDER_CORRECTION.md"
    txt = doc.read_text()
    assert "## 1. 当前观察" in txt and "## 6. 暂不决定" in txt and "AO-ANTISYM · dtu · attended_alignment · NCE · mean" in txt
    assert "not established" in txt and "were not read before this run" not in txt and "R34_D_PANEL" in txt
    assert f"AO-FIXED · {AO.DENSE} · dtu" in txt
    for p in (doc, tmp_path / "res" / "attention_order.json", tmp_path / "res" / "per_identity.json"):
        assert _mode600(str(p))
