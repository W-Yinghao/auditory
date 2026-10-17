import numpy as np
import pytest

from auditory_alignment_v3.aln34 import private_calibration_diagnosis as D


def test_child_mean_not_seed_pseudoreplication():
    configs = (("a",), ("b",))
    values = {c[0]: {str(s): {i: {"delta": {m: j + s for m in D.METRICS}}
                             for j, i in enumerate(("child1", "child2", "child3"))}
                      for s in (1, 3)} for c in configs}
    ids, matrices = D.identity_matrix(values, configs, (1, 3))
    assert len(ids) == 3
    assert matrices["nll_bits"].shape == (3, 2)
    np.testing.assert_array_equal(matrices["nll_bits"][:, 0], [2, 3, 4])
    del values["b"]["3"]["child2"]
    with pytest.raises(ValueError, match="coverage"):
        D.identity_matrix(values, configs, (1, 3))


def test_loss_direction_and_same_base():
    a = dict(n=10, nll_bits=0.5, brier=0.1, auc_score=0.7, gain_vs_base_bits=0.2)
    b = dict(n=10, nll_bits=0.8, brier=0.2, auc_score=0.7, gain_vs_base_bits=-0.1)
    pair = dict(class_kernel=a, positive_affine=b)
    assert D.validate_pair(pair)["nll_bits"] == pytest.approx(0.3)
    b["gain_vs_base_bits"] = 0.0
    with pytest.raises(ValueError, match="entropy"):
        D.validate_pair(pair)


def test_auc_is_same_score_not_clipped_probability_ranking():
    a = dict(n=10, nll_bits=0.5, brier=0.1, auc_score=0.7, gain_vs_base_bits=0.2)
    b = dict(a, auc_score=0.71)
    with pytest.raises(ValueError, match="AUC"):
        D.validate_pair(dict(class_kernel=a, positive_affine=b))
