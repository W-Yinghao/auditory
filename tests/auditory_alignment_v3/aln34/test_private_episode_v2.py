import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from auditory_alignment_v3.aln34 import private_episode as Old, private_episode_v2 as New


def test_minimum_support_and_effective_steps():
    for name,minimum in [('NCE',1),('CS_SINGLE',2)]:
        for n in (0,1,2,20):
            for steps in (0,5,20):
                p=New.support_policy(name,n,steps)
                assert p['effective_adapter_steps']==(steps if n>=minimum else 0)
                assert p['insufficient_support_identity_fallback']==bool(steps and n<minimum)
                assert p['minimum_support_trials']==minimum


def test_training_and_query_partition_functions_are_unchanged():
    def funcs(module):
        tree=ast.parse(Path(module.__file__).read_text())
        return {x.name:ast.dump(x,include_attributes=False) for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
    a,b=funcs(Old),funcs(New)
    for name in ('split_blocks','partitions','inner_source','original_source','continue_source','Readouts','choose','representations','batcher','new_encoder','objective'):
        assert a[name]==b[name],name
    # The adapter differs only at the availability guard; all arithmetic is identical.
    def adapter(module):
        node=next(x for x in ast.parse(Path(module.__file__).read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='fit_adapter')
        node.body=[x for x in node.body if not isinstance(x,ast.If)]
        return ast.dump(node,include_attributes=False)
    assert adapter(Old)==adapter(New)


class Encoder(torch.nn.Module):
    def __init__(self):super().__init__();self.w=torch.nn.Linear(20,32)
    def forward(self,x):return torch.nn.functional.normalize(self.w(x[0].mean(-1)),dim=-1)


def test_singleton_cs_keeps_exact_identity_without_evaluating_invalid_objective():
    torch.manual_seed(3);enc=Encoder();x=[torch.randn(1,20,20)]
    class Invalid:
        name='CS_SINGLE'
        def __call__(self,*args,**kwargs):raise AssertionError('invalid singleton objective was evaluated')
    m=New.fit_adapter(enc,SimpleNamespace(dev='cpu'),0,np.array([0]),Invalid(),None,20,3401)
    assert torch.equal(enc(x),m(x))


def test_nce_adapter_is_numerically_compatible_and_cs_pair_can_update():
    from auditory_alignment.train import Objective
    torch.manual_seed(7);base=Encoder();x=torch.randn(2,20,20);protos=torch.nn.functional.normalize(torch.randn(2,32),dim=-1)
    bt=SimpleNamespace(dev='cpu',kids=[{'y':np.array([0,1])}],patches=lambda child,ix:[x[ix]])
    obj=Objective.__new__(Objective);obj.name='NCE';obj.temperature=.1
    for idx in (np.array([],int),np.array([0]),np.array([0,1])):
        a=Old.fit_adapter(copy.deepcopy(base),bt,0,idx,obj,protos,5,3413)
        b=New.fit_adapter(copy.deepcopy(base),bt,0,idx,obj,protos,5,3413)
        assert all(torch.equal(a.state_dict()[k],v) for k,v in b.state_dict().items())
    obj.name='CS_SINGLE';obj.sigma_u=1.;obj.sigma_v=1.
    m=New.fit_adapter(copy.deepcopy(base),bt,0,np.array([0,1]),obj,protos,5,3413)
    assert m.B.abs().sum()>0
