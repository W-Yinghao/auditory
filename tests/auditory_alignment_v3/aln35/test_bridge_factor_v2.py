import numpy as np
import pytest
from auditory_alignment_v3.aln35.bridge_factor_analyze_v2 import validate_same_cache_score


def test_same_cache_reduction_error_is_bounded():
    reference = np.asarray([[.1, .2], [-.3, .4]])
    assert validate_same_cache_score(reference + 1e-14, reference) < 2e-14


def test_real_score_change_cannot_be_accepted_as_archival_replay_drift():
    reference = np.asarray([[.1, .2], [-.3, .4]])
    with pytest.raises(AssertionError, match='same-cache original score formula mismatch'):
        validate_same_cache_score(reference + 1e-5, reference)
