"""Pure A2 residual execution contracts; real fits run through Slurm only."""
import numpy as np
import pytest

from auditory_next.a2_residual_execution import (build_background, decomposition_table,
    residual_statistics)
from auditory5.contracts import FitScope


def test_background_has_only_declared_banks_and_optional_quality():
    shape = (20, 6, 2, 3)
    values = [np.ones(shape) * i for i in range(3)]
    b, names = build_background(*values)
    assert b.shape == (20, 6, 2, 9)
    assert names == ("post_common_response", "pre_common_response", "pre_delta")
    q, names = build_background(*values, quality=np.ones((20, 6, 2, 2)))
    assert q.shape[-1] == 11 and names[-1] == "quality_summary"
    with pytest.raises(ValueError, match="BACKGROUND_BANK_ALIGNMENT"):
        build_background(values[0], np.ones((20, 5, 2, 3)), values[2])


def _arrays(seed=4):
    rng = np.random.default_rng(seed)
    return rng.normal(size=(20, 6, 2, 5)), rng.normal(size=(20, 6, 2, 7))


def test_residual_fit_uses_training_candidate_means_only():
    delta, background = _arrays()
    groups = tuple(f"g{i}" for i in range(6))
    scope = FitScope(groups[:4], test_groups=groups[4:])
    fitted = residual_statistics(delta, background, groups[:4], groups[4:], scope=scope)
    assert fitted["prediction"].shape == delta.shape
    coefficient = fitted["predictor"].coefficient.copy()
    changed = background.copy(); changed[:, 4:] += 1e9
    again = residual_statistics(delta, changed, groups[:4], groups[4:], scope=scope)
    np.testing.assert_array_equal(coefficient, again["predictor"].coefficient)
    with pytest.raises(ValueError, match="SCOPE_OVERLAP"):
        residual_statistics(delta, background, groups[:4], groups[3:], scope=scope)


def test_four_term_decomposition_is_kept_with_delta_p_and_r():
    delta, background = _arrays()
    groups = tuple(f"g{i}" for i in range(6))
    scope = FitScope(groups[:4], test_groups=groups[4:])
    fitted = residual_statistics(delta, background, groups[:4], groups[4:], scope=scope)
    details = decomposition_table(delta[:, 4:], fitted["prediction"][:, 4:], groups[4:])
    assert details["decomposition"]["max_pair_error"] < 1e-10
    assert set(details["vector_statistics"]) == {"Delta", "P", "R"}
    assert "delta_delta" in details["decomposition"]["summaries"]
