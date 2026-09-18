import numpy as np
import pandas as pd
from scipy.special import expit

from auditory_v3.r3_stable_risk import (per_row_logit_loss, stable_metrics,
                                       paired_logit_contrasts)
from auditory_v3.statistics import weighted_metrics


def _frame():
    return pd.DataFrame([dict(split_group_id=f"s{group}", outer_fold=group % 5,
                             A_half=half, previous_code="1", previous_run_bin="run_1",
                             stimulus_local_id=label)
                        for group in range(10) for half in (0, 1) for label in (0, 1)])


def test_extreme_finite_logits_have_analytic_finite_bce_without_clipping():
    y = np.array([0, 1, 0, 1])
    logits = np.array([1000., -1000., -1000., 1000.])
    loss = per_row_logit_loss(y, logits)
    np.testing.assert_allclose(loss[:2], 1000. / np.log(2.), atol=1e-12)
    np.testing.assert_array_equal(loss[2:], [0., 0.])
    metric = stable_metrics(y, logits, [1, 1, 1, 1])
    assert metric["status"] == "PASS"
    np.testing.assert_allclose(metric["ce_bits"], 500. / np.log(2.))
    assert metric["J_bits"] < -700
    assert metric["bacc"] == .5
    assert metric["brier"] == .5


def test_stable_metrics_agree_with_probability_scoring_at_moderate_logits():
    y = np.array([0, 1, 0, 1, 0, 1])
    logits = np.array([-3., 2., .7, -.9, 0., .2])
    weights = np.array([1., 2., 3., 4., 5., 6.])
    stable = stable_metrics(y, logits, weights)
    probability = weighted_metrics(y, expit(logits), weights)
    assert stable["status"] == probability["status"] == "PASS"
    for metric in ("ce_bits", "J_bits", "bacc", "auc", "brier"):
        np.testing.assert_allclose(stable[metric], probability[metric], atol=1e-14)


def test_auc_preserves_logit_order_after_probability_saturation():
    result = stable_metrics([0, 1], [999., 1000.], [1, 1])
    assert expit(999.) == expit(1000.) == 1.
    assert result["auc"] == 1.
    assert result["status"] == "PASS"


def test_identical_extreme_logits_produce_zero_identity_bootstrap_contrast():
    frame = _frame()
    frame["logit"] = 1000. * (2 * frame.stimulus_local_id - 1)
    summary, identities = paired_logit_contrasts(frame, {"reference": "logit", "candidate": "logit"},
                                                 {"gain": ("reference", "candidate")})
    gain = summary["contrasts"]["gain"]
    assert gain["gain_bits"] == gain["ci_low"] == gain["ci_high"] == 0.
    assert gain["bootstrap_repetitions"] == 2000
    assert summary["n_groups"] == len(identities) == 10
    assert len(summary["fold_metrics"]) == 5
    assert len(summary["half_metrics"]) == 2


def test_missing_fold_logits_invalidate_entire_model_and_contrast():
    frame = _frame()
    frame["reference"] = 2. * (2 * frame.stimulus_local_id - 1)
    frame["candidate"] = frame.reference
    frame.loc[frame.outer_fold == 3, "candidate"] = np.nan
    summary, identities = paired_logit_contrasts(frame, {"reference": "reference", "candidate": "candidate"},
                                                 {"gain": ("reference", "candidate")})
    assert summary["metrics"]["reference"]["status"] == "PASS"
    assert summary["metrics"]["candidate"]["ce_bits"] is None
    assert summary["contrasts"]["gain"]["gain_bits"] is None
    assert summary["contrasts"]["gain"]["n_groups"] == summary["n_groups"] == 10
    assert identities.loc[identities.outer_fold == 3, "candidate"].isna().all()
    assert len(identities) == 10


def test_nonfinite_logits_never_count_as_perfect_predictions():
    for logits in ([np.inf, -np.inf], [np.nan, 0.]):
        metric = stable_metrics([1, 0], logits, [1, 1])
        assert metric["status"] == "INCOMPLETE_OR_NONFINITE"
        assert metric["ce_bits"] is None
