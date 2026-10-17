import numpy as np
from auditory_alignment_v3.aln34 import content_time as T


def test_temporal_windows_stay_inside_declared_segment():
    for fs in (100,128):
        t=T.valid_offsets(fs,5*fs)
        assert t.shape==(8,)
        assert t.min()-round(.6*fs)>=0
        assert t.max()+round(1.2*fs)<=5*fs


def test_no_test_target_in_model_or_residual_fit():
    rng=np.random.default_rng(1);x=rng.normal(size=(60,4));y=rng.normal(size=(60,3))
    role=np.array(['fit']*30+['es']*15+['test']*15)
    w,b,meta=T.fitted(x,y,role);changed=y.copy();changed[role=='test']*=1000
    w2,b2,meta2=T.fitted(x,changed,role)
    assert np.array_equal(w,w2) and np.array_equal(b,b2) and meta==meta2


def test_mismatch_preserves_person_and_anchor_position():
    a={'role':np.array(['test']*12),'person':np.array(['a']*6+['b']*6),'segment':np.repeat(np.arange(4),3)}
    ix,wrong=T.mismatch_indices(a,'a')
    assert np.array_equal(ix,np.arange(6)) and np.array_equal(wrong,np.array([3,4,5,0,1,2]))
    assert np.all(a['person'][wrong]=='a')


def test_federici_absent_features_are_not_fabricated():
    x=T.features({'envelope':np.arange(20)[None]},'federici',np.array([2,7]))
    assert set(x)=={'env'} and x['env'].shape==(2,1)
