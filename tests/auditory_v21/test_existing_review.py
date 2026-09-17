import numpy as np
import pytest

import auditory_v21.existing_review as review
from auditory_v21.existing_review import (
    bootstrap_contrast,
    fold_statistic,
    leave_one_candidate_range,
)


def _records():
    records = []
    for fold in range(2):
        ids = tuple(f"f{fold}_{i}" for i in range(3))
        base = np.eye(3)
        records.append({
            "fold": fold,
            "groups": ids,
            "matrices": {
                "R_SUP": {"post_delta": {"cosine": 2 * base}, "pre_delta": {"cosine": base}},
                "R_SIM": {"post_delta": {"cosine": base}, "pre_delta": {"cosine": base}},
                "R_RAND": {"post_delta": {"cosine": np.zeros((3, 3))}, "pre_delta": {"cosine": base}},
            },
        })
    return records


def test_fold_statistic_checks_diagonal_and_cross_identity_pairs():
    assert fold_statistic(np.eye(3), ("a", "b", "c")) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="NONFINITE"):
        fold_statistic(np.array([[1.0, np.nan], [0.0, 1.0]]), ("a", "b"))


def test_matched_post_pre_contrast_uses_same_candidate_draws():
    result = bootstrap_contrast(_records(), "R_SUP", "R_SIM", endpoint="post_minus_pre", seed=20260918)
    assert result["estimate"] == pytest.approx(1.0)
    assert result["ci_lower"] == pytest.approx(1.0)
    assert result["ci_upper"] == pytest.approx(1.0)
    assert result["valid_replicates"] > 0
    assert result["valid_replicates"] + result["invalid_replicates"] == result["n_bootstrap"]


def test_contrasts_and_leave_one_range_do_not_mix_fold_candidates():
    records = _records()
    result = bootstrap_contrast(records, "R_SUP", "R_RAND", endpoint="post_delta", seed=20260918)
    assert result["estimate"] == pytest.approx(2.0)
    influence = leave_one_candidate_range(records, "R_SUP", "R_SIM", endpoint="post_delta")
    assert influence["n_candidates"] == 6
    assert influence["leave_one_candidate_min"] == pytest.approx(1.0)
    assert influence["leave_one_candidate_max"] == pytest.approx(1.0)


def test_bootstrap_duplicate_identity_draws_are_valid_and_all_one_draw_is_invalid(monkeypatch):
    # Repeated sampled IDs are allowed; different-identity pairs are masked.
    result = bootstrap_contrast(_records(), "R_SUP", "R_SIM", n_bootstrap=2000)
    repeat = bootstrap_contrast(_records(), "R_SUP", "R_SIM", n_bootstrap=2000)
    assert result == repeat
    assert result["valid_replicates"] + result["invalid_replicates"] == 2000
    assert result["invalid_replicates"] > 0

    class AlwaysFirst:
        def integers(self, low, high, size):
            return np.zeros(size, dtype=int)

    monkeypatch.setattr(review.np.random, "default_rng", lambda seed: AlwaysFirst())
    invalid = bootstrap_contrast(_records(), "R_SUP", "R_SIM", n_bootstrap=4)
    assert invalid["invalid_replicates"] == 4
    assert invalid["valid_replicates"] == 0
    assert invalid["ci_lower"] is None and invalid["ci_upper"] is None


def test_leave_one_range_recomputes_the_global_fold_weighted_effect():
    records = _records()
    records[1]["matrices"]["R_SUP"]["post_delta"]["cosine"] = 3 * np.eye(3)
    influence = leave_one_candidate_range(records, "R_SUP", "R_SIM", endpoint="post_delta")
    assert influence["n_candidates"] == 6
    assert influence["leave_one_candidate_min"] == pytest.approx(1.4)
    assert influence["leave_one_candidate_max"] == pytest.approx(1.6)
