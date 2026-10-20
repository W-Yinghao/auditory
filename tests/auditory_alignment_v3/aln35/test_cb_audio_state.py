import numpy as np
import pytest
import torch
from auditory_alignment.train import _eff_rank
from auditory_alignment_v3.aln35.cb_audio_state import choose_state, effective_rank_gram, STATES


def curves(values):
    return [{"step": step, "paired_dev_nce_nats": value, "stream_sha256": "same", "batches": 32}
            for step, value in zip(STATES, values)]


def test_selector_earlier_tie_and_minimum():
    assert choose_state(curves([5., 4.2, 4.1, 4.])) == 10000
    assert choose_state(curves([4., 4., 4., 4.])) == 0
    assert choose_state(curves([5., 4., 4., 4.1])) == 2500


def test_missing_or_different_source_candidate_refused():
    with pytest.raises(ValueError):
        choose_state(curves([4., 3., 2.]))
    rows = curves([4., 3., 2., 1.])
    rows[-1]["stream_sha256"] = "different"
    with pytest.raises(ValueError):
        choose_state(rows)
    with pytest.raises(ValueError):
        choose_state(curves([4., 3., float("nan"), 1.]))


@pytest.mark.parametrize("shape", [(64, 32), (32, 128), (12, 256)])
def test_gram_effective_rank_matches_singular_value_definition(shape):
    x = torch.tensor(np.random.default_rng(20).normal(size=shape), dtype=torch.float64)
    assert abs(effective_rank_gram(x) - _eff_rank(x)) < 1e-7


def test_collapsed_representation_rank_zero():
    assert effective_rank_gram(torch.ones(32, 64)) == 0
