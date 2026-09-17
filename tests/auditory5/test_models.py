"""Synthetic contract tests for auditory5 model primitives.

These are intended for execution through the project's Slurm test wrapper.
"""

import pytest
torch = pytest.importorskip("torch")
from torch import nn

from auditory5.models import SmallEEGCNN_v1, ProjectionHead, nt_xent_loss, make_noise_views
from auditory5.head_geometry import decompose_head, max_softmax_difference, split_features


def test_small_cnn_structure_and_shapes():
    model = SmallEEGCNN_v1(20, 2)
    assert not any(isinstance(m, nn.BatchNorm1d) for m in model.modules())
    assert [m.out_channels for m in model.modules() if isinstance(m, nn.Conv1d)] == [32, 64, 64]
    z, logits = model(torch.randn(3, 20, 100), return_logits=True)
    assert z.shape == (3, 64) and logits.shape == (3, 2)
    assert isinstance(model.features[-1], nn.AdaptiveAvgPool1d)


def test_simclr_loss_matches_direct_symmetric_reference():
    z1, z2 = torch.tensor([[1., 0.], [0., 1.]]), torch.tensor([[1., 0.], [0., 1.]])
    got = nt_xent_loss(z1, z2, temperature=0.2)
    reps = torch.nn.functional.normalize(torch.cat([z1, z2]), dim=1)
    logits = reps @ reps.T / 0.2
    vals = []
    for i in range(4):
        keep = torch.arange(4) != i
        target = (i + 2) % 4
        vals.append(-logits[i, target] + torch.logsumexp(logits[i, keep], 0))
    assert torch.allclose(got, torch.stack(vals).mean())


def test_noise_views_are_independent_and_projector_normalized():
    x = torch.zeros(4, 20, 10)
    a, b = make_noise_views(x, torch.ones(20), noise_fraction=.02)
    assert not torch.equal(a, b)
    assert torch.allclose(ProjectionHead()(torch.randn(4, 64)).norm(dim=1), torch.ones(4), atol=1e-6)


def test_nan_empty_rejected():
    with pytest.raises(ValueError): SmallEEGCNN_v1(2)(torch.empty(0, 2, 3))
    with pytest.raises(ValueError): nt_xent_loss(torch.ones(1, 2), torch.ones(1, 2))
    with pytest.raises(ValueError): nt_xent_loss(torch.tensor([[float('nan'), 0.], [0., 1.]]), torch.ones(2, 2))


def test_head_geometry_softmax_invariance_and_binary_rank():
    w = torch.tensor([[1., 2., 3.], [2., 4., 6.]])
    g = decompose_head(w, torch.zeros(2), torch.tensor([.2, .3, .4]))
    assert g.rank <= 1
    assert float(max_softmax_difference(torch.randn(9, 3), g)) < 1e-10
    z = torch.randn(4, 3, dtype=torch.float64)
    visible, null = split_features(z, g)
    assert visible.shape == z.shape and null.shape == z.shape
    assert torch.allclose(visible + null, z - g.center, atol=1e-12)
    assert (visible * null).sum(1).abs().max() < 1e-12


def test_degenerate_head_is_explicit_rank_zero():
    g = decompose_head(torch.zeros(3, 4), torch.ones(3))
    assert g.rank == 0 and g.visible_basis.shape == (4, 0) and g.null_basis.shape == (4, 4)
    assert float(max_softmax_difference(torch.randn(3, 4), g)) < 1e-10
