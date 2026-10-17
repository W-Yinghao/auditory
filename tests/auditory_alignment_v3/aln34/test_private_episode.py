from types import SimpleNamespace
import numpy as np
import torch
from auditory_alignment_v3.aln34 import private_episode as T


def kid():
    return {'y':np.tile([0,1],50), 'block':np.repeat(np.arange(10),10), 'es_mask':np.repeat(np.arange(10)>=8,10)}


def test_inner_people_never_enter_source_fit_and_outer_stays_excluded():
    kids=[{'fold':i%5} for i in range(20)]
    for sf in range(5):
        tr,dv,te=T.partitions(kids,sf)
        assert len(tr)==12 and len(dv)==len(te)==4
        assert set(tr).isdisjoint(dv) and set(tr).isdisjoint(te) and set(dv).isdisjoint(te)
        outer,_,_=T.partitions(kids,sf,inner=False)
        assert set(outer)==set(tr)|set(dv)


def test_query_fixed_across_support_fractions_and_es_never_enters_source_episode():
    k=kid();s1,q1=T.split_blocks(k,.1);s3,q3=T.split_blocks(k,.3)
    assert np.array_equal(q1,q3) and set(s1)<set(s3)
    assert q1[0]==31 and s3[-1]==28
    s,q=T.split_blocks(k,.3,True)
    assert not k['es_mask'][s].any() and not k['es_mask'][q].any()
    assert set(k['block'][s]).isdisjoint(k['block'][q])


def test_low_support_keeps_identity_fallback_and_query():
    k={'y':np.array([0,1,0,1]),'block':np.array([0,1,1,1]),'es_mask':np.zeros(4,bool)}
    s,q=T.split_blocks(k,.1)
    assert len(s)==0 and np.array_equal(q,[2,3])


def candidate(risk,marker):return {'mean_native_true_nll':risk,'marker':marker}


def test_inner_choice_includes_epoch_zero_and_does_not_follow_outer_risk():
    inner={};outer={}
    for regime in ('source','ordinary','episode'):
        inner[regime]={'candidates':{f:{s:candidate(2.,'inner') for s in ('0','5','20')} for f in ('0.1','0.3')}}
        outer[regime]={'candidates':{f:{s:candidate(9.,regime+'/'+s) for s in ('0','5','20')} for f in ('0.1','0.3')}}
    inner['episode']['candidates']['0.3']['5']['mean_native_true_nll']=1.
    outer['episode']['candidates']['0.3']['20']['mean_native_true_nll']=-999
    chosen=T.choose(inner,outer)
    assert chosen['ordinary']['0.1']['chosen']=='source/0'
    assert chosen['episode']['0.3']['chosen']=='episode/5'
    assert chosen['episode']['0.3']['outer']['marker']=='episode/5'


def test_private_adapter_query_gradient_updates_base_only_in_outer_step():
    class Base(torch.nn.Module):
        def __init__(self):super().__init__();self.w=torch.nn.Linear(20,32)
        def forward(self,x):return torch.nn.functional.normalize(self.w(x[0].mean(-1)),dim=-1)
    m=Base();a=T.D.Adapter(m,'lowrank_spatial',20)
    with torch.no_grad():a.B.fill_(.01)
    for n,p in a.named_parameters():
        if not n.startswith('base.'):p.requires_grad_(False)
    m.requires_grad_(True).eval();a([torch.randn(8,20,20)])[:,0].sum().backward()
    assert m.w.weight.grad.norm()>0 and a.B.grad is None


def test_cs_calibration_removes_own_reference_trial_across_child_boundaries(monkeypatch):
    # Inspect the actual inputs to the native calibrator, independent of the LR calibration.
    x={0:np.array([[0.,0.],[1.,0.],[0.,1.]]),1:np.array([[1.,1.],[2.,0.],[0.,2.]])}
    y=np.array([0,1,0,1,0,1]);fd=SimpleNamespace(tr=[0,1],es={0:np.ones(3,bool),1:np.ones(3,bool)},
        y_es=y,off_es=np.zeros(6),base=.5,es_rows=lambda u:np.concatenate([u[0],u[1]]))
    rec={'row':{'seed':3401,'spec':{'objective':'CS_SINGLE'}},'objective_calibration':{'sigma_u':1.}}
    seen=[]
    class Cal:
        @staticmethod
        def fit(s,labels):seen.append(np.array(s));return Cal()
    monkeypatch.setattr(T,'AffineLogitCalibrator',Cal)
    obj=T.Readouts(rec,None,fd,x)
    bank=np.concatenate(list(x.values()));K=np.exp(-((bank[:,None]-bank[None,:])**2).sum(2)/2)
    expected=(K@y+.5-y)/(K.sum(1)+1-1)
    assert np.allclose(seen[-1],np.log(expected)-np.log1p(-expected),atol=1e-10)
    assert obj.calibration_kind.endswith('leave_self_out')
