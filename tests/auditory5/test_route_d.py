import numpy as np
from auditory5.routes.route_d import grouped_ridge_predict,choose_penalties,candidate_means

def test_drop_is_exact_baseline_not_large_penalty():
    rng=np.random.default_rng(8);c=rng.normal(size=(12,3));z=rng.normal(size=(12,6));y=rng.normal(size=12)+50
    train={'C':c[:9],'N':z[:9]};test={'C':c[9:],'N':z[9:]}
    a=grouped_ridge_predict(train,test,y[:9],{'C':1,'N':'drop'});b=grouped_ridge_predict(train,test,y[:9],{'C':1})
    np.testing.assert_array_equal(a,b)
    changed={'C':c[9:],'N':z[9:]*1e12};np.testing.assert_array_equal(a,grouped_ridge_predict(train,changed,y[:9],{'C':1,'N':'drop'}))

def test_target_bounds_and_mean_without_eeg():
    x={'C':np.ones((5,3))};test={'C':np.ones((2,3))};p=grouped_ridge_predict(x,test,np.array([10,20,30,40,50]),{})
    np.testing.assert_array_equal(p,[30,30])

def test_trial_budget_repetitions_are_one_candidate_summary():
    groups=np.repeat(['a','b'],80);y=np.tile(np.repeat([0,1],40),2);z=np.arange(160*3).reshape(160,3)
    means=candidate_means(z,y,groups,['a','b'],np.arange(160).astype(str))
    assert means.shape==(2,2,3)
    np.testing.assert_allclose(means[0,0],z[:40].mean(axis=0))

def test_penalty_selection_prefers_dropping_uninformative_eeg_on_tie():
    train={'C':np.zeros((6,3)),'V':np.zeros((6,2)),'N':np.zeros((6,6))};test={k:x[:2] for k,x in train.items()}
    inner=[{'train':train,'test':test,'y_train':np.full(6,50.),'y_test':np.full(2,50.)} for _ in range(3)]
    p,s=choose_penalties(inner,'D3_CVN');assert p=={'C':10.,'V':'drop','N':'drop'}
