from types import SimpleNamespace
import numpy as np
import torch
from auditory_alignment_v3.aln34 import episode_training as T


def test_direct_support_query_window_guard():
    b=SimpleNamespace(grid=4,bt=SimpleNamespace(seg_len=640,fs=128))
    items=[{'e0':0},{'e0':640}]
    selected=T.anchors(b,items,700)
    assert selected and all(s['e0']+t+77<=700 for s,t in selected)
    assert len(T.anchors(b,items))==16


def test_first_order_support_adapter_keeps_query_gradient_to_base():
    from auditory_alignment_v3.aln34.adaptation_policy import Adapter
    class Base(torch.nn.Module):
        def __init__(self):
            super().__init__();self.w=torch.nn.Linear(4,32)
        def forward(self,x):return torch.nn.functional.normalize(self.w(x.mean(-1)),dim=-1)
    base=Base();adapted=Adapter(base,'lowrank_spatial',4)
    adapted.B.data.fill_(.01)
    for name,p in adapted.named_parameters():
        if not name.startswith('base.'):p.requires_grad_(False)
    base.requires_grad_(True).eval()
    adapted(torch.randn(8,4,100))[:,0].sum().backward()
    assert base.w.weight.grad.norm()>0
    assert adapted.B.grad is None and adapted.A.grad is None


def test_snapshot_is_independent():
    m=torch.nn.Linear(3,2);old=T.cpu_state(m)
    with torch.no_grad():m.weight.add_(1)
    assert not torch.equal(old['weight'],m.weight)
