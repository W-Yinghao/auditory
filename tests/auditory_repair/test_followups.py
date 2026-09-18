import numpy as np
from auditory_repair.followups import kernel_predict,mixed_predict
from auditory_fseries.models import fit_predict


def record_kernel_attempt(event):
    from auditory_fseries import models
    if models.RECORDER:
        models.RECORDER(event)


def test_zero_kernel_reduces_to_clinical_ridge():
    rng=np.random.default_rng(11);n=30;C=rng.normal(size=(n,2));Z=np.zeros((n,4));y=50+3*C[:,0]
    tr=np.arange(20);te=np.arange(20,30)
    p,_=kernel_predict(C,Z,y,tr,te,('quadratic',10,1,'Z'),[0,100],record_kernel_attempt)
    q,_=fit_predict(C,Z,Z,y,tr,te,('quadratic',10,None,False,False),1,[0,100])
    np.testing.assert_allclose(p,q,atol=1e-10)


def test_kernel_bandwidth_and_predictions_ignore_heldout_outcomes():
    rng=np.random.default_rng(12);C=rng.normal(size=(30,2));Z=rng.normal(size=(30,4));y=50+Z[:,0]**2
    tr=np.arange(20);te=np.arange(20,30)
    p,state=kernel_predict(C,Z,y,tr,te,('linear',10,.1,'Z'),[0,100],record_kernel_attempt)
    changed=y.copy();changed[te]+=10000
    q,other=kernel_predict(C,Z,changed,tr,te,('linear',10,.1,'Z'),[0,100],record_kernel_attempt)
    np.testing.assert_array_equal(p,q);assert state['bandwidth']==other['bandwidth']


def test_missing_mff_EEG_is_training_imputed_and_all_missing_clinical_is_valid():
    rng=np.random.default_rng(10);C=np.full((30,3),np.nan);Q=rng.normal(size=(30,2));Z=rng.normal(size=(30,3));Z[1,0]=np.nan;y=rng.uniform(0,40,size=30)
    tr=np.arange(20);te=np.arange(20,30);candidate=('linear',10,10,True,False)
    p,state=mixed_predict(C,Q,Z,y,tr,te,candidate,12,[0,100]);different=Z.copy();different[te,0]=10000
    _,other=mixed_predict(C,Q,different,y,tr,te,candidate,12,[0,100])
    assert np.isfinite(p).all();assert state['eeg_missing_transform']==other['eeg_missing_transform']
