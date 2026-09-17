import pickle
import numpy as np
import pandas as pd
import pytest
from auditory5.contracts import FitScope
from auditory5.routes.route_b_controls import (QualityContext,quality_values,reaction_windows,
    stable_shift_segments,shift_permutation,fit_quality_readouts)


def rows(groups=('a','b','c','d','e','f'),n=120):
    rng=np.random.default_rng(41);size=len(groups)*n
    return pd.DataFrame(dict(split_group_id=np.repeat(groups,n),candidate_id=np.repeat(groups,n),
        trial_id=[f't{i}' for i in range(size)],record_id=np.repeat(groups,n),segment_id=np.repeat(groups,n),
        previous_gap_s=.7,segment_position_fraction=.5,history_target=np.tile(np.arange(n)%2,len(groups)),
        time_block_id=np.tile(np.arange(n)//20,len(groups)),onset_sample=np.tile(np.arange(n)*700,len(groups)),
        all_ptp_uv=rng.uniform(10,100,size),pre_ptp_uv=rng.uniform(3,15,size)))


def test_quality_transform_never_fits_test_or_uses_history():
    train=rows();scope=FitScope(tuple(train.split_group_id.unique()),test_groups=('heldout',))
    context=QualityContext().fit(train,scope);test=rows(('heldout',));before=pickle.dumps(context)
    a=context.transform(test);test.history_target=1-test.history_target
    np.testing.assert_array_equal(a,context.transform(test));assert before==pickle.dumps(context)
    assert a.shape[1]==context.strong_scaler_.n_features_in_+2 if hasattr(context.strong_scaler_,'n_features_in_') else a.shape[1]>4
    with pytest.raises(ValueError,match='LEAKAGE'):QualityContext().fit(test,scope)
    test.all_ptp_uv=-1
    with pytest.raises(ValueError,match='QUALITY'):quality_values(test)


def test_quality_nested_fit_keeps_quality_outside_pca_and_outer_test():
    train=rows();g=tuple(train.split_group_id.unique());scope=FitScope(g,test_groups=('heldout',))
    eeg=np.random.default_rng(5).normal(size=(len(train),3))
    models=fit_quality_readouts(train,{'B0_context_spline':None,'B2_post':eeg},scope,31)
    model=models['B2_post'];assert model.eeg_pca.n_features_in_==3
    assert model.fit_scope['quality_outside_eeg_pca']
    for f in model.fit_scope['inner_folds']:
        assert set(f['fit_groups']).isdisjoint(f['validation_groups'])
        assert 'heldout' not in f['fit_groups']
    test=rows(('heldout',));z=eeg[:len(test)];p=model.predict(test,z)
    test.history_target=1-test.history_target
    np.testing.assert_array_equal(p['raw'],model.predict(test,z)['raw'])


def test_windows_preserve_per_trial_actual_grid_start_and_partition():
    epochs=np.arange(2*3*175).reshape(2,3,175);r=pd.DataFrame({'post_start_index':[62,63]})
    x=reaction_windows(epochs,r)
    assert x['early'].shape==(2,3,50) and x['late'].shape==(2,3,50)
    for i,start in enumerate(r.post_start_index):
        np.testing.assert_array_equal(np.concatenate([x['early'][i],x['late'][i]],axis=-1),epochs[i,:,start:start+100])


def test_circular_diagnostic_never_crosses_record_segment_and_keeps_labels():
    r=rows(('a','b'));original=r.copy();segments,keep=stable_shift_segments(r)
    assert len(segments)==2 and keep.all()
    order=shift_permutation(len(r),segments,91)
    assert len(np.unique(order))==len(r) and np.all(order!=np.arange(len(r)))
    np.testing.assert_array_equal(r.record_id,r.record_id.iloc[order])
    np.testing.assert_array_equal(r.segment_id,r.segment_id.iloc[order])
    pd.testing.assert_frame_equal(r,original)
    r.loc[r.record_id.eq('a'),'previous_gap_s']=np.tile([.1,2],60)
    segments,keep=stable_shift_segments(r)
    assert len(segments)==1 and not keep[:120].any()


def test_short_or_one_history_segments_are_not_used_as_shift_null():
    r=rows(('a',),80);assert not stable_shift_segments(r)[1].any()
    r=rows(('a',));r.history_target=0;assert not stable_shift_segments(r)[1].any()
    with pytest.raises(ValueError,match='SHORT'):shift_permutation(10,[np.arange(10)],1)
