from types import SimpleNamespace
import numpy as np
import torch
from auditory_alignment_v3.aln34 import cb_auditory as T


def fake_index():
    s={'piece':np.arange(24),'s':np.full(24,128),'family':np.repeat(np.arange(12),2),
       'presentation':np.arange(24),'role':np.array(['fit']*24)}
    return SimpleNamespace(seg={'sparrkulee':s},keys=lambda p,s:p*100000+s)


class Bank:
    def __init__(self,*args,**kwargs):self.layout=T.C.BIOSEMI64
    def gather(self,piece,start,offs):
        x=torch.tensor(start+offs)[:,None,None]+torch.arange(38)[None,None,:]
        return x.expand(-1,64,-1).half()
    def targets(self,pres,start,offs):return torch.tensor(pres[:,None]+np.arange(8),dtype=torch.float32)


def test_stream_support_is_contiguous_and_wrong_source_has_no_fixed_family(monkeypatch):
    idx=fake_index();monkeypatch.setattr(T.V,'manifest_index',lambda m:idx);monkeypatch.setattr(T.V,'DonorBank',Bank)
    a=T.Stream({},range(24),3401,'fit','cpu');b=T.Stream({},range(24),3401,'fit','cpu')
    x,y,keys,wrong,body=a.draw();x2,y2,k2,w2,body2=b.draw()
    assert body==body2 and a.chain==b.chain and torch.equal(x,x2) and torch.equal(y,y2)
    assert x.shape==(64,64,64) and torch.all(torch.diff(x[:,0],dim=-1)==1)
    starts=128+np.array(body['offsets']).reshape(-1)-26
    assert np.array_equal(x[:,0,0].numpy(),starts)
    rows=np.array(body['rows']);family=np.repeat(idx.seg['sparrkulee']['family'][rows],8)
    assert np.all(family!=family[wrong.numpy()]) and set(wrong.tolist())==set(range(64))


def test_resume_reproduces_next_stream_without_training_rng(monkeypatch):
    idx=fake_index();monkeypatch.setattr(T.V,'manifest_index',lambda m:idx);monkeypatch.setattr(T.V,'DonorBank',Bank)
    a=T.Stream({},range(24),42,'fit','cpu');a.draw();state=a.state();expected=a.draw()
    b=T.Stream({},range(24),42,'fit','cpu');b.load(state);actual=b.draw()
    assert torch.equal(expected[0],actual[0]) and a.chain==b.chain


def test_all_target_content_exclusions_apply_before_donor_sampling(monkeypatch):
    idx=fake_index();idx.seg['sparrkulee']['role'][20:]='dev'
    monkeypatch.setattr(T.V,'manifest_index',lambda m:idx)
    m={'donor_sets':{d:{'core':{'excluded_presentations':{'sparrkulee':[p]}}} for d,p in zip(('dtu','fau','federici'),(1,7,22))},
       'pools':{'core':{'sparrkulee':list(range(20))}},'selection':{'dev_queries':list(range(20,24))}}
    pool=T.eligible(m)
    assert pool['excluded_presentations']==[1,7,22] and 1 not in pool['fit'] and 7 not in pool['fit'] and 22 not in pool['dev']


def test_loading_only_backbone_preserves_target_rng_and_restores_constructor(monkeypatch,tmp_path):
    class Backbone(torch.nn.Module):
        def __init__(self):super().__init__();self.net=torch.nn.Linear(2,3)
    monkeypatch.setattr(T.fm_aligned32,'Backbone',Backbone)
    src=Backbone();src.net.weight.data.fill_(7.);p=tmp_path/'donor.pt';torch.save({'backbone':src.net.state_dict(),'probe':True},p)
    record={'final_checkpoint':str(p),'final_checkpoint_sha256':T.B.sha(p)}
    torch.manual_seed(34);base=Backbone();expected_head=torch.nn.Linear(3,2).weight.detach().clone()
    torch.manual_seed(34)
    with T.target_instrumentation({},record,True):
        loaded=T.fm_aligned32.Backbone();actual_head=torch.nn.Linear(3,2).weight.detach().clone()
        assert torch.all(loaded.net.weight==7.)
    assert torch.equal(expected_head,actual_head) and T.fm_aligned32.Backbone is Backbone


def test_paired_donor_accounting_rejects_different_exposure():
    import pytest
    from auditory_alignment_v3.aln34.cb_auditory_aggregate import check_streams
    def rec(h):return {'unit':{'seed':3401},'updates':10000,'query_rows':640000,'stream_sha256':h}
    assert check_streams([rec('a'),rec('a')])['3401']['query_rows']==640000
    with pytest.raises(AssertionError,match='exposure'):check_streams([rec('a'),rec('b')])
