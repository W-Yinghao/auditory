from pathlib import Path
import importlib.util
import numpy as np
import pytest
import torch
import yaml
from reference.metrics import score_sir,equal_child_mean,low_label_risk
from reference.contracts import check_scopes,redact_targets,temporary_eval
from reference.srp import PopulationResponse,ResponseProfile,balanced_profile_loss


def toy():
    torch.manual_seed(20)
    pop=PopulationResponse(torch.randn(2,4,6)*0.1,torch.zeros(2,6))
    model=ResponseProfile(pop,latent_dim=3,hidden=8,phi_dim=4)
    support=torch.randn(2,2,5,6)
    mask=torch.ones(2,2,5,dtype=torch.bool)
    qs=torch.tensor([[0,0,1,1],[0,0,1,1]])
    h=torch.randn(2,4,3)
    return model,support,mask,qs,h


def test_rps_exact_and_order():
    y=np.array([1,3,5]);p=np.eye(5)[y-1]
    a=score_sir(p,y)
    assert np.allclose(a['rps'],0)
    assert np.all(a['nll_bits']>=0)
    near=score_sir(np.eye(5)[[1]],np.array([1]))['rps'][0]
    far=score_sir(np.eye(5)[[4]],np.array([1]))['rps'][0]
    assert near < far


def test_child_equal_weight():
    assert equal_child_mean(np.array([0.,0.,0.,1.]),np.array(['a','a','a','b']))==0.5
    assert low_label_risk(.2,.4)==pytest.approx(.3)


def test_hidden_labels_are_removed():
    mask=np.array([True,False,True,False])
    a=redact_targets({'sir':np.array([1,2,3,4])},mask)
    b=redact_targets({'sir':np.array([1,999,3,-999])},mask)
    assert np.array_equal(a['sir'],b['sir'],equal_nan=True)


def test_scope_rejects_upstream_leak():
    kw=dict(outer_train=['a','b'],outer_test=['c'],encoder_train=['a','b'],transform_fit=['a'],profile_fit=['b'],label_train=['a'],label_budget=1)
    check_scopes(**kw)
    kw['encoder_train']=['a','c']
    with pytest.raises(ValueError): check_scopes(**kw)


def test_mode_restores_on_exception():
    m=torch.nn.Sequential(torch.nn.Linear(2,2),torch.nn.Dropout(.5))
    m.train()
    with pytest.raises(RuntimeError):
        with temporary_eval(m):
            assert not m.training
            raise RuntimeError('synthetic')
    assert all(x.training for x in m.modules())


def test_conditionwise_set_permutation_invariance():
    m,x,mask,s,h=toy();m.eval()
    a=m(x,mask,s,h).latent_mean
    b=m(x[:,:,torch.tensor([4,0,3,2,1])],mask,s,h).latent_mean
    assert torch.allclose(a,b,atol=1e-6)


def test_zero_latent_recovers_population():
    m,x,mask,s,h=toy()
    mean,lv=m.decode(torch.zeros(2,3),s,h)
    base,blv=m.population(s,h)
    assert torch.equal(mean,base) and torch.equal(lv,blv)


def test_loss_finite_gradient_and_no_clinical_input():
    m,x,mask,s,h=toy();m.train()
    out=m(x,mask,s,h)
    losses=balanced_profile_loss(torch.randn(2,4,6),out,s,2)
    losses['loss'].backward()
    assert torch.isfinite(losses['loss'])
    assert m.mean_map.grad is not None and torch.isfinite(m.mean_map.grad).all()
    assert m.posterior.weight.grad is not None
    assert len(list(m.population.parameters()))==0


def test_missing_class_not_silently_accepted():
    m,x,mask,s,h=toy();mask[0,1]=False
    with pytest.raises(ValueError): m(x,mask,s,h)


def test_objective_broadcast_identity():
    x=np.array([-2.,1.,4.]);y=2.
    lhs=np.mean((x-y)**2);rhs=(x.mean()-y)**2+np.mean((x-x.mean())**2)
    assert lhs==pytest.approx(rhs)


def test_task_budget_and_optional_disabled():
    root=Path(__file__).parents[1]
    cfg=yaml.safe_load((root/'config/story_v1.yaml').read_text())
    spec=importlib.util.spec_from_file_location('tasks',root/'scripts/build_task_manifest.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    task=mod.build(cfg)
    assert task['small_profile_fits']==30
    assert task['clinical_optimizer_calls']==8250
    assert task['new_raw_backbones']==0
    assert not task['competitor_enabled'] and not task['optional_mff_enabled']
