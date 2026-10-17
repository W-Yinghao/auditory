from types import SimpleNamespace
import numpy as np
import pytest
import torch
from auditory_alignment.losses import cs_qmi
from auditory_alignment_v3.aln34 import cs_episode as C


def test_traditional_cs_value_and_gradient_and_binding_restore():
    torch.manual_seed(7)
    u0, v0 = torch.randn(24, 4), torch.randn(24, 4)
    obj = C.LegacyObjective({'objective':'CS_SINGLE','config':{}}, u0, v0)
    before = C.T.Objective
    u = torch.randn(12, 4, requires_grad=True); v = torch.randn(12, 4)
    with pytest.raises(RuntimeError, match='test unwind'):
        with C.objective_binding(obj):
            actual = C.T.Objective({'objective':'NCE'}, torch.zeros(4,32), torch.zeros(4,32))
            loss, _ = actual(u,v)
            reference, _ = cs_qmi(u,v,sigma_u=obj.sigma_u,sigma_v=obj.sigma_v)
            assert torch.equal(loss, -reference)
            assert torch.equal(torch.autograd.grad(loss,u,retain_graph=True)[0],
                               torch.autograd.grad(-reference,u)[0])
            raise RuntimeError('test unwind')
    assert C.T.Objective is before


def test_bandwidth_selection_excludes_all_es_and_target_people():
    rows = [{'p':p,'kind':'ss','role':role,'e0':i*1000,'s0':i*1000,'uid':f'{p}/{role}/{i}'}
            for p in range(3) for role in ('fit','es','test') for i in range(35)]
    b = SimpleNamespace(row={'seed':3401}, segs=rows, grid=4,
                        bt=SimpleNamespace(train_p={0},seg_len=640,fs=128))
    a = C.calibration_anchors(b)
    assert len(a) == 256 and all(s['p']==0 and s['role']=='fit' for s,t in a)
    digest = C.draw_digest(a)
    for s in rows:
        if s['p'] != 0 or s['role'] != 'fit':
            s['e0'] += 999999
    assert digest == C.draw_digest(C.calibration_anchors(b))


def test_both_engine_bindings_restore_on_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(C, 'BASE', tmp_path)
    for engine in C.ENGINES.values():
        before = {k:getattr(engine,k) for k in ('BASE','PLAN','STORE','continue_source','atomic_torch','tensor_batch')}
        bundle, write = engine.D.Bundle, C.B.write
        with pytest.raises(ValueError):
            with C.engine_binding(engine):
                assert engine.BASE == tmp_path and engine.D.Bundle is C.CSBundle
                C.B.write(tmp_path/'unit.json', {'status':'complete','stages':{}})
                assert __import__('json').loads((tmp_path/'unit.json').read_text())['status']=='awaiting_pair_audit'
                raise ValueError()
        assert all(getattr(engine,k) is v for k,v in before.items())
        assert engine.D.Bundle is bundle and C.B.write is write


def test_actual_continuation_has_matched_draws_and_contract(tmp_path, monkeypatch):
    """Exercise the inherited optimizer loop with CS, resume metadata and both arms."""
    monkeypatch.setattr(C, 'PLAN', tmp_path/'plan.json'); C.PLAN.write_text('{}')
    torch.manual_seed(23)
    model = torch.nn.Linear(3,3,bias=False)
    initial = C.E.cpu_state(model)
    rows = [{'p':0,'e0':i*100,'s0':i*100,'uid':str(i)} for i in range(12)]
    obj = C.LegacyObjective({'objective':'CS_SINGLE','config':{}},torch.randn(16,3),torch.randn(16,3))
    class Adapted(torch.nn.Module):
        def __init__(self):
            super().__init__();self.base=model
        def forward(self,x):return self.base(x)*torch.tensor([1.1,.9,1.2])
    bundle = SimpleNamespace(model=model, row={'seed':3401,'spec':{'architecture':'lag_local_tokens'}},
        bt=SimpleNamespace(dev=torch.device('cpu'),train_p={0},seg_len=100,fs=100), grid=4,
        coh=SimpleNamespace(participants=[{'id':'source0'}]), items=lambda p,role:rows,
        fit_adapter=lambda *args:(Adapted(),16),cs_objective=obj,cs_calibration={'sigma_u':obj.sigma_u,'sigma_v':obj.sigma_v})
    def batch(b,items):
        x=torch.tensor([[s['e0']/1000,t/100,np.sin(s['e0']+t)] for s,t in items],dtype=torch.float32)
        return x, torch.roll(x,1,1), torch.arange(len(x))
    monkeypatch.setattr(C.E,'tensor_batch',batch)
    with C.engine_binding(C.E):
        a=C.E.continue_source(bundle,'ordinary',tmp_path,initial,2,True)
        b=C.E.continue_source(bundle,'episode',tmp_path,initial,2,True)
        assert a['query_draw_sha256']==b['query_draw_sha256'] and len(a['query_draw_sha256'])==2
        assert a['objective']==b['objective']=='CS_SINGLE'
        assert a['relative_parameter_change']>0 and b['relative_parameter_change']>0
        reused=C.E.continue_source(bundle,'ordinary',tmp_path,initial,2,True)
        assert reused==a
        state=torch.load(tmp_path/'ordinary.pt',weights_only=False)
        state['cs_contract']['objective']='NCE';torch.save(state,tmp_path/'ordinary.pt')
        with pytest.raises(AssertionError,match='contract drift'):
            C.E.continue_source(bundle,'ordinary',tmp_path,initial,2,True)


def test_mismatch_gain_and_risk_keep_opposite_benefit_direction():
    from auditory_alignment_v3.aln34.cs_episode_aggregate import values
    def pp(loss,gain):
        return {'p':{m:{'true_nll_bits':loss,'mismatch_gain_bits':gain} for m in ('native','unified')}}
    reference,candidate=pp(2.,.4),pp(1.8,.3)
    risk=values(reference,'true_nll_bits')['native']['p']-values(candidate,'true_nll_bits')['native']['p']
    gain=values(reference,'mismatch_gain_bits',-1)['native']['p']-values(candidate,'mismatch_gain_bits',-1)['native']['p']
    assert risk==pytest.approx(.2) and gain==pytest.approx(-.1)
