import copy
import numpy as np
from auditory_repair.extended import bank_features,evaluate_fold,repeated_interval
from auditory_fseries.models import make_splits


def test_literal_code_swap_only_changes_condition_axes_and_contrast_sign():
    rng=np.random.default_rng(3);x=rng.normal(size=(16,20,176));t=np.linspace(-.2,.5,176);c=np.tile([1,2],8)
    a=bank_features(x,t,c);b=bank_features(x,t,3-c)
    assert {k:len(v) for k,v in a.items()}==dict(HJORTH=60,POST=320,CONTRAST=160,PRE=160,SPATIAL=210)
    np.testing.assert_allclose(a['CONTRAST'],-b['CONTRAST'])
    np.testing.assert_allclose(a['POST'][:160],b['POST'][160:])
    np.testing.assert_allclose(a['HJORTH'],b['HJORTH']);np.testing.assert_allclose(a['SPATIAL'],b['SPATIAL'])


def test_amplitude_scaling_has_expected_variance_and_correlation_effects():
    rng=np.random.default_rng(8);x=rng.normal(size=(16,20,176));t=np.linspace(-.2,.5,176);c=np.tile([1,2],8)
    a=bank_features(x,t,c);b=bank_features(x*2,t,c)
    np.testing.assert_allclose(b['POST'],a['POST']*2)
    np.testing.assert_allclose(b['SPATIAL'][:190],a['SPATIAL'][:190])
    np.testing.assert_allclose(b['HJORTH'][:20]-a['HJORTH'][:20],np.log(4))
    np.testing.assert_allclose(b['HJORTH'][20:],a['HJORTH'][20:])


def test_joint_bank_selection_is_heldout_label_blind_and_keeps_all_models():
    rng=np.random.default_rng(7);n=40;data={'Q':rng.normal(size=(n,2)),'bank_a':rng.normal(size=(n,3)),'bank_b':rng.normal(size=(n,3))}
    C=rng.normal(size=(n,2));C[3,1]=np.nan;y=50+data['bank_b'][:,0]*10
    config=dict(banks=['bank_a','bank_b'],clinical_families=['linear'],clinical_alphas=[1],eeg_alphas=[10])
    tr,te,inner=make_splits(np.arange(n),{'validation':dict(seed=5,outer_folds=4,inner_folds=2)})[0]
    a=evaluate_fold(data,y,C,tr,te,inner,config,7,[0,100]);changed=y.copy();changed[te]+=1000
    b=evaluate_fold(data,changed,C,tr,te,inner,config,7,[0,100])
    assert {'C_bank_a','C_bank_b','BEST_CZ','BEST_CQZ','BEST_SHUFFLED','Z_ONLY'}<=set(a)
    for name in a:
        assert a[name]['candidate']==b[name]['candidate']
        np.testing.assert_array_equal(a[name]['prediction'],b[name]['prediction'])


def test_repeats_do_not_multiply_bootstrap_identity_count():
    d=np.tile(np.arange(12),(5,1))/10
    result=repeated_interval(d,200,7)
    assert result['n']==12 and len(result['repeat_gains'])==5
    assert np.isclose(result['gain_MAE'],.55)
