import numpy as np
import pandas as pd
from auditory5.routes.route_e import block_folds,_mlp,_logits,family_is_complete
from scipy.special import softmax

def test_e0_blocks_never_cross_folds_and_classes_preserved():
    rows=pd.DataFrame({'filter_block_id':np.repeat(np.arange(8),16),'stimulus_local_id':np.tile([0,1],64)})
    keep,folds=block_folds(rows);assert keep.all() and len(folds)==4
    for train,test in folds:assert set(rows.filter_block_id.iloc[train]).isdisjoint(rows.filter_block_id.iloc[test])

def test_e0_missing_class_blocks_cannot_fake_support():
    rows=pd.DataFrame({'filter_block_id':np.repeat(np.arange(8),16),'stimulus_local_id':np.zeros(128,int)})
    keep,folds=block_folds(rows);assert not keep.any() and not folds

def test_small_network_logits_match_probabilities():
    rng=np.random.default_rng(19);x=rng.normal(size=(80,3));y=np.tile([0,1],40);g=np.repeat(np.arange(4),20)
    head=_mlp(x,y,g,10.)
    np.testing.assert_allclose(softmax(_logits(head,x),axis=1),head.predict_proba(x),atol=1e-12)

def test_failed_head_cannot_be_aggregated_over_successful_records_only():
    support=[dict(status='PASS',families={'linear':'PASS','MLP32':'PASS'}),
             dict(status='PASS',families={'linear':'PASS','MLP32':'NUMERICAL_FAILURE'}),
             dict(status='SUPPORT_INSUFFICIENT')]
    assert family_is_complete(support,'linear')
    assert not family_is_complete(support,'MLP32')
    assert not family_is_complete([], 'linear')
