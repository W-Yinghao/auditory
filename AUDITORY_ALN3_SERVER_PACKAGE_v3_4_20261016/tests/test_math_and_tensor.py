import numpy as np
import pytest
import torch
from aln34_reference.residuals import normalize_rows, residual_diagnostics, ridge_fit_predict
from aln34_reference.attention import summaries, antisymmetric_logit, sigmoid, paired_order_metrics
from aln34_reference.adapters import SpatialAdapter

def test_radial_residual_can_be_large_and_functionally_zero():
    u=np.random.default_rng(4).normal(size=(17,8)); out=residual_diagnostics(u,2*u)
    assert out['relative_residual_norm_mean']==pytest.approx(2)
    assert out['relative_orthogonal_norm_mean']<1e-12
    assert out['normalized_change_mean']<1e-12

def test_nonradial_residual_changes_representation():
    u=np.array([[1.,0.],[1.,0.]]); r=np.array([[0.,1.],[0.,2.]])
    assert residual_diagnostics(u,r)['normalized_change_mean']>0.1

def test_negative_radial_can_flip():
    u=np.array([[1.,2.],[3.,4.]])
    assert np.allclose(normalize_rows(-u),-normalize_rows(u))
    assert residual_diagnostics(u,-2*u)['normalized_change_mean']==pytest.approx(2)

def test_zero_rows_recorded():
    out=residual_diagnostics(np.zeros((2,3)),np.ones((2,3)))
    assert out['n_zero_or_tiny_base_rows']==2
    assert np.isnan(out['normalized_change_mean'])

@pytest.mark.parametrize('bad',[np.ones(3),np.ones((0,3)),np.array([[np.nan]])])
def test_bad_matrix_rejected(bad):
    with pytest.raises(ValueError):normalize_rows(bad)

def test_shape_mismatch_rejected():
    with pytest.raises(ValueError):residual_diagnostics(np.ones((2,3)),np.ones((2,4)))

def test_orthogonal_ridge_prediction_invariance():
    g=np.random.default_rng(5); x=g.normal(size=(200,16));y=g.normal(size=(200,7));xt=g.normal(size=(70,16))
    q,_=np.linalg.qr(g.normal(size=(16,16)))
    p=ridge_fit_predict(x,y,xt,.4);p2=ridge_fit_predict(x@q,y,xt@q,.4)
    assert np.max(np.abs(p-p2))<1e-11

def test_dual_ridge_case():
    g=np.random.default_rng(6); x=g.normal(size=(5,20)); y=g.normal(size=(5,2))
    assert ridge_fit_predict(x,y,x).shape==(5,2)

def test_nonisometric_rescaling_not_covered_by_theorem():
    g=np.random.default_rng(5);x=g.normal(size=(30,4));y=g.normal(size=(30,1));xt=g.normal(size=(10,4));s=np.diag([.1,1,5,10])
    assert np.max(np.abs(ridge_fit_predict(x,y,xt,10)-ridge_fit_predict(x@s,y,xt@s,10)))>1e-5

def test_constant_positive_logit_is_half_under_paired_order():
    d=np.ones((20,4)); h=lambda z:np.full(len(z),5.)
    m=paired_order_metrics(h,d)
    assert m['accuracy']==.5 and m['n_physical_windows']==20

def test_antisymmetric_logits_and_probabilities():
    d=np.random.default_rng(2).normal(size=(30,4))
    h=lambda z:summaries(z)@np.array([2,7,1,-3,.5])+9
    l=antisymmetric_logit(h,d);lm=antisymmetric_logit(h,-d)
    assert np.allclose(l,-lm)
    assert np.allclose(sigmoid(l)+sigmoid(lm),1)

def test_zero_logit_half_credit():
    m=paired_order_metrics(lambda z:np.zeros(len(z)),np.ones((8,1)))
    assert m['accuracy']==.5 and m['logloss_bits']==pytest.approx(1)

def test_good_mean_integrator():
    m=paired_order_metrics(lambda z:z.mean(1),np.ones((8,4)))
    assert m['accuracy']==1 and m['swap_logit_error_max']==0

def test_single_segment_features_not_time_integration():
    s=summaries(np.array([[2.],[-1.]]))
    assert np.allclose(s[:,1],0) and np.allclose(s[:,-1],0)

def test_sigmoid_large_values_finite():
    p=sigmoid(np.array([-1000.,0,1000.]))
    assert np.isfinite(p).all() and np.allclose(p,[0,.5,1])

def test_score_wrong_shape_rejected():
    with pytest.raises(ValueError):antisymmetric_logit(lambda z:np.ones((len(z),1)),np.ones((2,3)))

@pytest.mark.parametrize('kind',['diagonal','lowrank','full'])
def test_adapter_identity_and_finite_gradients(kind):
    torch.manual_seed(2); m=SpatialAdapter(8,kind,rank=3); x=torch.randn(4,8,17)
    assert torch.equal(m(x),x)
    (m(x)-torch.randn_like(x)).square().mean().backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters())
    assert sum(p.grad.abs().sum().item() for p in m.parameters())>0

def test_lowrank_not_dead_init():
    torch.manual_seed(3); m=SpatialAdapter(8,'lowrank',rank=4);x=torch.randn(3,8,11)
    (m(x)**2).mean().backward()
    assert m.V.grad.abs().sum()>0
    assert m.U.grad.abs().sum()==0

def test_actual_parameter_counts():
    assert SpatialAdapter(64,'full').trainable_parameter_count()==4096
    assert SpatialAdapter(64,'lowrank',4).trainable_parameter_count()==512
    assert SpatialAdapter(64,'diagonal').trainable_parameter_count()==64

def test_adapter_does_not_change_time_axis():
    m=SpatialAdapter(4,'full');x=torch.zeros(1,4,12);x[:,:,5]=1
    with torch.no_grad():m.delta.add_(.05)
    out=m(x)
    assert out[:,:,:5].abs().sum()==0 and out[:,:,6:].abs().sum()==0

def test_bad_adapter_dimensions():
    with pytest.raises(ValueError):SpatialAdapter(4,'lowrank',8)
    with pytest.raises(ValueError):SpatialAdapter(4)(torch.zeros(2,3,10))
