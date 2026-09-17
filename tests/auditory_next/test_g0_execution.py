"""Pure G0 contracts; real inputs and fits must be run under Slurm."""
import numpy as np
import pandas as pd
import pytest

from auditory_next import g0_execution as g0


def test_C_selection_uses_training_children_and_frozen_tie_order():
    losses = {c: [1.0, 1.0] for c in g0.C_GRID}
    losses[.1] = [.4, .6]
    losses[1.] = [.5, .5]
    chosen, means = g0.choose_C(losses)
    assert chosen == .1 and means[.1] == pytest.approx(.5)
    with pytest.raises(ValueError, match="G0_C_SELECTION"):
        g0.choose_C({c: [] for c in g0.C_GRID})


def test_candidate_balanced_weights_rejects_missing_class():
    weights = g0.candidate_balanced_weights([0, 1, 0, 1], ["a", "a", "b", "b"])
    assert weights.tolist() == [.5, .5, .5, .5]
    with pytest.raises(ValueError, match="MISSING_CANDIDATE_CLASS"):
        g0.candidate_balanced_weights([0, 0], ["a", "a"])


def test_offline_bins_use_physical_times_and_fixed_400_columns():
    times = np.arange(-.2, .5, .004)
    times = times[:175]
    x = np.zeros((2, 20, len(times)))
    for j in range(len(times)):
        x[:, :, j] = times[j]
    out = g0.offline_20bin_features(x, times, channels=[f"C{j}" for j in range(20)])
    assert out.shape == (2, 400)
    assert out[0, 0] == pytest.approx(.060)
    with pytest.raises(ValueError, match="G0_OFFLINE_TIME_BIN_EMPTY"):
        g0.offline_20bin_features(x[:, :, :1], [0.1], channels=[f"C{j}" for j in range(20)])


def test_cluster_bootstrap_is_fixed_and_requires_two_clusters():
    rows = pd.DataFrame({"record_id": ["r1", "r1", "r2", "r2"],
        "candidate_id": ["p1", "p1", "p2", "p2"],
        "stimulus_local_id": [0, 1, 0, 1], "logit": [-2., 2., -1., 1.]})
    result = g0.clustered_bootstrap(rows, n_boot=30, seed=11)
    assert result["n_clusters"] == 2 and result["n_bootstrap"] == 30
    with pytest.raises(ValueError, match="G0_BOOTSTRAP_CLUSTER"):
        g0.clustered_bootstrap(rows.iloc[:2], n_boot=5)


def test_transform_scope_is_l0_only_pca32():
    rng = np.random.default_rng(9)
    x = rng.normal(size=(12, 40)); y = np.arange(12) % 2
    candidates = np.repeat(["a", "b", "c"], 4)
    l0, _ = g0._fit_logistic(x, y, candidates, .1, "L0")
    learned, _ = g0._fit_logistic(x, y, candidates, .1, "R_SIM")
    assert l0.components.shape[0] <= 32
    assert learned.components is None
