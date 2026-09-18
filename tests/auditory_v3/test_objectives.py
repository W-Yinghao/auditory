import torch

from auditory_v3.objectives import (
    match_objective, nt_xent_loss, quartet_supcon_loss, supervised_ce,
)


def test_supervised_ce_averages_two_views():
    logits = torch.tensor([[[4., 0.], [0., 4.]], [[4., 0.], [0., 4.]]])
    labels = torch.tensor([0, 1])
    assert torch.allclose(supervised_ce(logits, labels), torch.nn.functional.cross_entropy(
        logits.reshape(-1, 2), labels.repeat_interleave(2)))


def test_sim_excludes_self_and_has_finite_loss():
    z = torch.eye(2,dtype=torch.float64).repeat_interleave(2,dim=0).reshape(2,2,2).requires_grad_()
    value=nt_xent_loss(z)
    expected=torch.log1p(2*torch.exp(torch.tensor(-5.,dtype=torch.float64)))
    assert torch.allclose(value,expected)
    value.backward()
    assert torch.isfinite(z.grad).all()


def test_match_quartet_has_two_positives_and_six_denominator_terms():
    embeddings = torch.tensor([
        [[1., 0.], [1., 0.]], [[1., 0.], [1., 0.]],
        [[0., 1.], [0., 1.]], [[0., 1.], [0., 1.]],
    ])
    labels = torch.tensor([0, 0, 1, 1])
    q = torch.zeros(4, dtype=torch.long)
    value = quartet_supcon_loss(embeddings, labels, q)
    assert torch.isfinite(value)
    assert torch.allclose(value,torch.log(2+4*torch.exp(torch.tensor(-5.))))
    assert torch.allclose(match_objective(torch.zeros(4, 2), labels, embeddings, q),
                          supervised_ce(torch.zeros(4, 2), labels) + .1 * value)
