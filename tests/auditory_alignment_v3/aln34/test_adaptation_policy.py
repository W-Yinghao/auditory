import pytest
import torch
from torch import nn
from torch.nn import functional as F

from auditory_alignment_v3.aln34.adaptation_policy import ADAPTERS, Adapter, split_items, select_step


class Base(nn.Module):
    def __init__(self):
        super().__init__()
        self.drop = nn.Dropout(.7)
        self.linear = nn.Linear(4, 8)

    def forward(self, x):
        x = x[0] if isinstance(x, list) else x
        return F.normalize(self.linear(self.drop(x).mean(-1)), dim=-1)


@pytest.mark.parametrize('kind', ADAPTERS)
def test_identity_and_frozen_eval_base(kind):
    torch.manual_seed(0)
    b = Base().eval()
    x = torch.randn(7,4,30)
    ref = b(x).detach()
    a = Adapter(b,kind,4,dim=8)
    a.train()
    assert not b.training and not b.drop.training
    assert torch.allclose(a(x),ref,atol=2e-7,rtol=2e-7)
    assert torch.allclose(a([x]),ref,atol=2e-7,rtol=2e-7)
    assert all(not p.requires_grad for p in b.parameters())
    if kind != 'none':
        a(x).square().sum().backward()
        assert any(p.grad is not None for p in a.parameters() if p.requires_grad)
        assert all(p.grad is None for p in b.parameters())


def test_support_query_pairing_and_epoch_zero():
    s10,q10=split_items(list(range(100)),.1)
    s30,q30=split_items(list(range(100)),.3)
    assert q10 == q30 == list(range(30,100))
    assert set(s10) < set(s30) and not set(s30)&set(q30)
    assert select_step({0:1.0,20:1.0,50:1.2,100:1.1}) == 0
    assert select_step({0:1.0,20:.9,50:.8,100:.85}) == 50


def test_temporal_residual_has_declared_three_tap_support():
    a=Adapter(Base(),'declared_window_temporal',4,dim=8)
    with torch.no_grad():a.taps[:] = torch.tensor([.1,.2,.3])
    x=torch.zeros(2,4,20);x[...,10]=1
    y=a.transform(x)
    assert torch.all(y[...,:9] == 0) and torch.all(y[...,12:] == 0)
    assert y.shape == x.shape
