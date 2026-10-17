import numpy as np
import pytest
from scipy.signal import sosfreqz
from auditory_alignment_v3.aln34 import causal_filter as C


def test_causal_prefix_invariant_but_zero_phase_detects_future():
    rng=np.random.default_rng(882);x=rng.normal(size=(2,8192));y=x.copy();y[:,4096:]+=rng.normal(size=y[:,4096:].shape)*10
    sos=C.filters(512)
    a=C.apply_filter(x,sos,'causal_cascade');b=C.apply_filter(y,sos,'causal_cascade')
    np.testing.assert_array_equal(a[:,:4096],b[:,:4096])
    a=C.apply_filter(x,sos,'zero_phase');b=C.apply_filter(y,sos,'zero_phase')
    assert np.max(np.abs(a[:,4000:4096]-b[:,4000:4096]))>.01


def test_interior_magnitude_and_native_stride():
    fs=512;sos=C.filters(fs);t=np.arange(100*fs)/fs;x=np.sin(2*np.pi*7*t)[None]
    z=C.apply_filter(x,sos,'zero_phase')[0,20*fs:-20*fs]
    c=C.apply_filter(x,sos,'causal_cascade')[0,20*fs:-20*fs]
    _,h=sosfreqz(sos,worN=[7],fs=fs)
    expected=np.abs(h[0])**2/np.sqrt(2)
    np.testing.assert_allclose([np.std(z),np.std(c)],expected,rtol=1e-7)
    assert C.native_stride(512)==4
    with pytest.raises(ValueError):C.native_stride(1000)


def test_every_lag_uses_identical_guarded_anchors():
    for guard in C.GUARDS:
        t=C.keep_anchors(64,(0,1280),guard)
        assert len(t)>0
        for lag in C.LAGS:
            ix=64+t[:,None]+round(lag*.128)+np.arange(3)
            assert ix.min()>=round(guard*128) and ix.max()<1280-round(guard*128)
    assert set(C.keep_anchors(64,(0,1280),2))<=set(C.keep_anchors(64,(0,1280),.5))


def test_sufficient_statistic_mse_matches_direct():
    rng=np.random.default_rng(72);x=rng.normal(size=(91,5));y=rng.normal(size=(91,1));s=C.S.Stats(5,1);s.add(x,y)
    w,b=C.S.fit(s,.3)
    np.testing.assert_allclose(C.mse_of(s,w,b),np.mean((y-x@w-b)**2),rtol=1e-12)


def test_native_metadata_preserves_legacy_first64_access():
    channels=[f'EEG{i}' for i in range(64)]+[f'EXG{i}' for i in range(8)]
    assert C.eeg_channels(channels)==channels[:64]
    with pytest.raises(AssertionError):C.eeg_channels(channels[:63])
