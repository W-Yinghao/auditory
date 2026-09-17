import numpy as np
import pytest

from auditory5.metrics import candidate_balanced_ce_bits, classification_metrics
from auditory5.statistics import a_candidate_bootstrap, a_matching_statistic, paired_cluster_bootstrap


def test_uniform_probability_is_one_bit_and_negative_j_is_kept():
    y = [0, 1, 0, 1]
    assert candidate_balanced_ce_bits(y, np.full((4, 2), .5), [0, 0, 1, 1]) == pytest.approx(1.)
    wrong = np.array([[.1,.9],[.9,.1],[.1,.9],[.9,.1]])
    assert candidate_balanced_ce_bits(y, wrong, [0,0,1,1]) == pytest.approx(-np.log2(.1))
    assert classification_metrics(y, wrong, [0,0,1,1])['J_bits'] == pytest.approx(1+np.log2(.1))


def test_candidate_weight_is_unchanged_by_long_candidate():
    p = np.tile([[.9, .1], [.1, .9]], (1, 1))
    y = np.array([0, 1, *([0] * 20), *([1] * 20)])
    probs = np.vstack([p, np.tile([[.9, .1]], (20, 1)), np.tile([[.1, .9]], (20, 1))])
    assert candidate_balanced_ce_bits(y, probs, [0, 0] + [1] * 40) == pytest.approx(candidate_balanced_ce_bits([0, 1, 0, 1], np.vstack([p, p]), [0, 0, 1, 1]))


def test_a_excludes_same_id_from_nonmatching_pairs_and_zero_is_undefined():
    a = np.array([[1., 0.], [1., 0.], [0., 1.]])
    b = np.array([[1., 0.], [1., 0.], [0., 1.]])
    s = a_matching_statistic(a, b, ["x", "x", "y"])
    assert s["undefined_zero_vector"] is False
    assert s["cosine"] == pytest.approx(1.0)
    z = a_matching_statistic(np.zeros((2, 2)), b[:2], [0, 1])
    assert z["undefined_zero_vector"] is True and np.isnan(z["cosine"])


def test_a_bootstrap_reports_invalid_duplicate_identity_draws():
    a = np.eye(3); b = np.eye(3)
    r = a_candidate_bootstrap(a, b, [0, 1, 2], n_boot=20, seed=3)
    assert r["requested_bootstrap"] == 20 and r["invalid_replicates"] >= 0


def test_paired_gain_is_baseline_minus_augmented():
    r = paired_cluster_bootstrap([2., 4.], [1., 1.], ["a", "b"], n_boot=100, seed=1)
    assert r["estimate"] == pytest.approx(2.)
    assert r["gain_definition"] == "baseline - augmented"


def test_probability_contract_rejects_bad_rows_and_duplicate_trials():
    with pytest.raises(ValueError): candidate_balanced_ce_bits([0, 1], [[.2, .2], [.5, .5]], [0, 0])
    with pytest.raises(ValueError): candidate_balanced_ce_bits([0, 1], [[.5, .5], [.5, .5]], [0, 0], ["same", "same"])


def test_classification_metrics_are_candidate_macro_not_pooled_trial():
    # Candidate 0 is perfect (2 trials); candidate 1 is poor (20 trials).
    y = np.array([0, 1] + [0] * 10 + [1] * 10)
    p = np.vstack([[[.99, .01], [.01, .99]],
                   np.tile([[.6, .4]], (10, 1)), np.tile([[.4, .6]], (10, 1))])
    r = classification_metrics(y, p, [0, 0] + [1] * 20)
    expected_candidate1_brier = 2 * (.4 ** 2)
    expected_candidate0_brier = 2 * (.01 ** 2)
    assert r["brier"] == pytest.approx((expected_candidate0_brier + expected_candidate1_brier) / 2, abs=1e-6)
    assert r["auroc_definition"].startswith("candidate-macro")
