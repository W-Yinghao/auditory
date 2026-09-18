import numpy as np
import pytest
from auditory_v3.train import TrainingContractError,_validate_batch_plan,generate_smoke_data,channel_scaler
from auditory_v3.representation_data import sample_quartets


def test_batch_identity_exposure_and_test_mutation_isolation():
    x,y,m=generate_smoke_data(train_groups=16,test_groups=2)
    groups=[f'synthetic_{i}' for i in range(16)]
    plan=sample_quartets(m,groups,epochs=1)['batch_indices']
    _validate_batch_plan(x,y,m,groups,plan,epochs=1)
    fit=np.flatnonzero(m.split_group_id.isin(groups));before=channel_scaler(x,m,fit)
    changed=x.copy();changed[~m.split_group_id.isin(groups)]=1000
    after=channel_scaler(changed,m,fit)
    np.testing.assert_array_equal(before[0],after[0]);np.testing.assert_array_equal(before[1],after[1])
    bad=plan.copy();bad[0,0,-1]=bad[0,0,0]
    with pytest.raises(TrainingContractError):_validate_batch_plan(x,y,m,groups,bad,epochs=1)
    bad=plan.copy();bad[0,0,-1]=len(x)-1
    with pytest.raises(TrainingContractError):_validate_batch_plan(x,y,m,groups,bad,epochs=1)


def test_training_scaler_is_hierarchically_weighted():
    x,y,m=generate_smoke_data(train_groups=16,test_groups=0)
    idx=np.arange(len(m));mean,scale=channel_scaler(x,m,idx)
    from auditory_v3.statistics import hierarchical_weights
    weights=hierarchical_weights(m)
    np.testing.assert_allclose(mean[:,0],np.sum(x.astype(float).mean(axis=2)*weights[:,None],axis=0),atol=1e-7)
    assert np.isfinite(scale).all() and (scale>0).all()
