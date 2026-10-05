"""Checks required by the C3 review addendum (2026-10-05): strict-past history golden test, mixed-type CMI bound,
rare class / small strata handling, ties, the current-via-history control, and the documented nonlinear common-cause
boundary of Gaussian-copula CMI."""
import os
import sys

import numpy as np
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "AUDITORY_C3_SERVER_PACKAGE_v1_20261003", "reference"))
from auditory_c3.engine import copnorm_rows  # noqa: E402
from auditory_c3.private_mi2 import cmi_cd, hist_codes, mi_cd  # noqa: E402

rng = np.random.default_rng(5)


def test_history_golden_strict_past():
    from auditory5.events import build_event_history
    seq = ["1", "1", "2", "1", "1", "1", "2", "2"]  # 1 = standard, 2 = deviant
    ev = [{"record_id": "R", "segment_id": "s0", "trial_id": f"R:e{i:05d}", "onset_sample": 1000 * (i + 1), "event_literal": c,
           "event_kind": "target", **({"sequence_start_complete": True} if i == 0 else {})} for i, c in enumerate(seq)]
    rows = build_event_history(ev, 1000.0)
    pc = np.array([-1 if r["previous_code"] is None else (0 if r["previous_code"] == "1" else 1) for r in rows])
    prl = np.array([-1 if r["previous_run_length"] is None else r["previous_run_length"] for r in rows])
    assert pc.tolist() == [-1, 0, 0, 1, 0, 0, 0, 1]
    assert prl.tolist() == [-1, 1, 2, 1, 1, 2, 3, 1]
    h = hist_codes(pc, prl)
    # standards since the last deviant, strictly before the current event (bin index = count for 0..3)
    assert h["since_last_deviant"].tolist() == [-1, 1, 2, 0, 1, 2, 3, 0]
    # without a confirmed complete start, the first run length is unknown -> excluded, never invented
    ev[0].pop("sequence_start_complete")
    rows2 = build_event_history(ev, 1000.0)
    assert rows2[1]["previous_run_length"] is None and rows2[1]["history_status"] == "incomplete_previous_run"


def test_mixed_cmi_respects_entropy_bound():
    n = 20000
    hist = rng.integers(0, 2, n); cur = rng.integers(0, 2, n)
    T = 6 * (2 * hist - 1) + rng.standard_normal(n)
    v, info = cmi_cd(T, hist, cur)
    assert info["H_y_given_z_bits"] == pytest.approx(1.0, abs=0.01)
    assert v <= info["H_y_given_z_bits"] and not info["bound_violation"]


def test_rare_class_is_not_silently_merged():
    y = np.r_[np.zeros(181, int), np.ones(19, int)]
    T = np.r_[rng.standard_normal(181), 8 + rng.standard_normal(19)]
    v, info = mi_cd(T, y)
    assert info["status"] == "OK" and info["classes_kept"] == 2 and v > 0.2


def test_small_strata_are_not_zeroed():
    z = np.r_[np.zeros(30, int), np.ones(30, int)]
    y = np.tile([0, 1], 30)
    T = 3 * y + rng.standard_normal(60)
    v, info = cmi_cd(T, y, z)
    assert np.isfinite(v) and v > 0.2 and info["retained_mass"] == 1.0
    v2, info2 = mi_cd(rng.standard_normal(12), np.r_[np.zeros(6, int), np.ones(6, int)])
    assert np.isnan(v2) and info2["status"] == "INSUFFICIENT_SUPPORT"


def test_ties_do_not_inject_sample_order():
    from gcmi_core import gcmi_cc
    from auditory_c3.engine import ent_from_cov
    n = 4000
    t = np.linspace(0, 1, n) + 0.1 * rng.standard_normal(n)
    # reviewer's example: a constant source; the reference copula ranks it by sample order -> spurious bits
    assert gcmi_cc(np.zeros(n), t) > 0.3
    with pytest.raises(ValueError):
        copnorm_rows(np.zeros((1, n)))
    # zero-inflated source (90% exact zeros, as in silent pre-onset stretches): ties share one score
    x = np.zeros(n); x[rng.choice(n, n // 10, replace=False)] = rng.standard_normal(n // 10)
    Xn = copnorm_rows(x[None])[0]
    assert len(np.unique(Xn[x == 0])) == 1
    Tn = copnorm_rows(t[None])[0]
    C = np.cov(np.vstack([Xn, Tn]))
    ours = ent_from_cov(C[:1, :1], n) + ent_from_cov(C[1:, 1:], n) - ent_from_cov(C, n)
    assert gcmi_cc(x, t) > 0.2 and abs(ours) < 0.01


def test_current_readout_explained_by_history_only():
    n = 30000
    cur = np.zeros(n, int)
    for i in range(1, n):
        cur[i] = 0 if cur[i - 1] == 1 else int(rng.random() < 0.25)
    prev = np.r_[0, cur[:-1]]
    score = prev + rng.standard_normal(n)
    i_cur, _ = mi_cd(score, cur)
    i_cur_h, info = cmi_cd(score, cur, prev)
    # analytic: mean shift 0.25 (P(prev deviant | cur standard) = 0.25), unit noise -> about 0.007 bits
    assert i_cur > 0.004 and abs(i_cur_h) < 0.002


def test_documented_boundary_nonlinear_common_cause():
    """Known failure, kept visible: Gaussian-copula CMI is a model-conditional dependence, not a lower bound."""
    from gcmi_core import gcmi_ccc
    n = 30000
    z = rng.standard_normal(n)
    x = z**2 + 0.4 * rng.standard_normal(n); y = z**2 + 0.4 * rng.standard_normal(n)
    assert gcmi_ccc(x, y, z) > 0.4  # true I(X;Y|Z) = 0
