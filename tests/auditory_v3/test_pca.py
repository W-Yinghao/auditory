import numpy as np
import pytest

from auditory_v3.linear import WeightedPCA, WeightedScaler, fit_logistic
from auditory_v3.pca_packet import orthogonal_equivalence, run_pca


def test_no_whitening_no_projection_rescaling_and_true_rank():
    rng = np.random.default_rng(61003)
    X = rng.normal(size=(100, 12)) * np.linspace(.1, 3, 12)
    w = np.arange(1., 101.)
    pca = WeightedPCA().fit(X, w)
    z = pca.transform(X)
    weighted_variance = (w / w.sum()) @ (z ** 2)
    np.testing.assert_allclose(weighted_variance, pca.explained_variance_, atol=1e-12)
    assert not np.allclose(weighted_variance, 1)
    views = pca.views(X)
    np.testing.assert_array_equal(views["PC8"], z[:, :8])
    np.testing.assert_allclose(views["PC8_DUP"][:, :8], z[:, :8] / np.sqrt(2))
    low_rank = np.column_stack([X[:, 0], 2 * X[:, 0], np.ones(100)])
    reduced = WeightedPCA().fit(low_rank, w)
    assert reduced.rank_ == 1
    assert reduced.views(low_rank)["REST"].shape == (100, 0)
    assert reduced.views(low_rank)["PC8"].shape == (100, 1)


def test_full_orthogonal_and_normalized_duplicate_heads_are_equivalent():
    rng = np.random.default_rng(61004)
    X = rng.normal(size=(180, 12))
    y = (X[:, 0] + X[:, 4] + rng.normal(size=len(X)) > 0).astype(int)
    w = np.ones(len(X))
    U = WeightedScaler().fit_transform(X, w)
    pca = WeightedPCA().fit(U, w)
    views = pca.views(U)
    fitted = {key: fit_logistic(matrix, y, w, .01, context={"fit_kind": "contract_test", "view": key})
              for key, matrix in {"FULL": U, "ORTHOGONAL": pca.transform(U),
                                  "PC8": views["PC8"], "PC8_DUP": views["PC8_DUP"]}.items()}
    assert all(fit.success for fit in fitted.values())
    np.testing.assert_allclose(fitted["FULL"].predict_proba(U),
                               fitted["ORTHOGONAL"].predict_proba(pca.transform(U)), atol=2e-5, rtol=0)
    np.testing.assert_allclose(fitted["PC8"].predict_proba(views["PC8"]),
                               fitted["PC8_DUP"].predict_proba(views["PC8_DUP"]), atol=2e-5, rtol=0)
    assert orthogonal_equivalence(fitted["FULL"], U, pca)["status"] == "PASS"


def test_p0_gate_precedes_feature_loading():
    loaded = []
    with pytest.raises(RuntimeError, match="capability"):
        run_pca(None, lambda *a: loaded.append(a), capability_receipt={"status": "CAPABILITY_FAIL"})
    assert loaded == []
