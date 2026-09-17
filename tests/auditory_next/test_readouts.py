import numpy as np
import pytest
import torch
from auditory_next.readouts import population_weights, ce_bits, objective_parity, BinaryMLP, objective, start_fit, stability


def test_population_changes_weights_not_observations():
    y=np.array([0,0,0,1,0,1]);g=np.array(['a']*4+['b']*2)
    natural=population_weights(y,g,'P_nat'); balanced=population_weights(y,g,'P_bal')
    for group in ('a','b'):
        assert natural[g==group].sum()==pytest.approx(1)
        assert balanced[g==group].sum()==pytest.approx(1)
        for label in (0,1): assert balanced[(g==group)&(y==label)].sum()==pytest.approx(.5)
    assert np.dot(natural,y)/natural.sum()==pytest.approx(.375)
    assert np.dot(balanced,y)/balanced.sum()==pytest.approx(.5)


def test_extreme_logits_are_not_clipped():
    assert ce_bits(np.array([10000.,-10000.]),np.array([0,1]),np.ones(2))==pytest.approx(10000/np.log(2))
    assert ce_bits(np.zeros(2),np.array([0,1]),np.ones(2))==pytest.approx(1.)


def test_installed_sklearn_objective_parity():
    assert objective_parity()['status']=='PASS'


def test_explicit_lambda_invariant_to_weight_scale_alpha_not():
    model=BinaryMLP(3,4);x=torch.ones((5,3),dtype=torch.float64);y=torch.tensor([0,1,0,1,0],dtype=torch.float64);w=torch.ones(5,dtype=torch.float64)
    a=objective(model,x,y,w,lam=.001);b=objective(model,x,y,2*w,lam=.001)
    assert float(a[0].detach())==pytest.approx(float(b[0].detach()))
    a=objective(model,x,y,w,alpha=.1);b=objective(model,x,y,2*w,alpha=.1)
    assert float(a[2].detach())==pytest.approx(2*float(b[2].detach()))
    with pytest.raises(ValueError):objective(model,x,y,w,alpha=.1,lam=.001)


def test_budget_is_not_convergence():
    state=start_fit(np.zeros((4,2)),np.array([0,1,0,1]),np.ones(4),lam=.001)
    assert stability(state)['status']=='OPTIMIZATION_UNRESOLVED'
    state.steps=2000
    state.history=[dict(objective=10-.001*i,parameter_norm=1.) for i in range(2000)]
    assert stability(state)['status']=='OPTIMIZATION_UNRESOLVED'
