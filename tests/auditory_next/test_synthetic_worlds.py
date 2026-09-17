import numpy as np
import pytest

from auditory_next.synthetic_worlds import *


def test_n1_world_mapping_and_seed_reproducibility():
    for name, factory in N1_WORLDS.items():
        a, b = factory(80, 7), factory(80, 7)
        assert a["world"] == name
        assert np.array_equal(a["y"], b["y"]) and np.array_equal(a["P"], b["P"])
        assert set(a["train_mask"]) == {True, False}


def test_background_key_is_signed_by_background_and_prior_only_has_no_post_signal():
    d = n1_background_key(200, 2)
    signed = d["P"][:, 0] * d["B"][:, 0]
    assert np.corrcoef(signed, d["y"])[0, 1] > .9
    d = n1_prior_only(200, 2)
    assert d["P"].shape[1] == 2 and d["B"].shape[1] == 1


def test_n2_shapes_and_covariance_world_equal_means():
    m = n2_mean_sufficient(40, 8, 3)
    c = n2_covariance_signal(40, 8, 3)
    assert m["bags"].shape == (40, 8, 2) and m["k"] == 8
    assert np.allclose(c["bags"][c["y"] == 0].mean((0, 1)), c["bags"][c["y"] == 1].mean((0, 1)), atol=.25)
    assert np.allclose(c["bags"].mean(axis=1), 0.0)
    v0 = np.var(c["bags"][c["y"] == 0], axis=(0, 1)).mean()
    v1 = np.var(c["bags"][c["y"] == 1], axis=(0, 1)).mean()
    assert v1 > 5 * v0
    assert not np.array_equal(c["H_BAG"][:, :2], c["bags"].mean(axis=1))


def test_n2_invalid_k_and_n3_world_directions():
    with pytest.raises(ValueError): n2_mean_sufficient(4, 8, 1)
    h = n3_history_only(104, 4); e = n3_eeg_increment(104, 4)
    assert np.corrcoef(h["H"][:, 0], h["y"])[0, 1] > .8
    assert np.corrcoef(e["P"][:, 0], e["y"])[0, 1] > .8
