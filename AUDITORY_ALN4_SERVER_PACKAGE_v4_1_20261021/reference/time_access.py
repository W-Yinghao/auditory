"""Native-support reference for ALN4.1, not a preprocessing/model pipeline."""
from __future__ import annotations
from fractions import Fraction
import math
import numpy as np

WINDOWS_MS=((-200,200),(0,400),(200,600))

def _ceil_fraction(x):
    return -((-x.numerator)//x.denominator)

def native_bounds(window_ms, fs_native, *, origin_ms=0):
    if not isinstance(fs_native,int) or fs_native<=0:
        raise ValueError('positive integer native sample rate required')
    lo,hi=window_ms
    if hi<=lo:
        raise ValueError('ordered half-open window required')
    return tuple(_ceil_fraction(Fraction(t-origin_ms)*fs_native/1000) for t in (lo,hi))

def output_length(n_native,fs_native,target_hz=200):
    if n_native<=0 or fs_native<=0 or target_hz<=0:
        raise ValueError('positive lengths/rates required')
    value=Fraction(n_native*target_hz,fs_native)
    return (2*value.numerator+value.denominator)//(2*value.denominator)

def describe(window_ms, fs_native, *, origin_ms=0, target_hz=200, pad_to=200):
    lo,hi=native_bounds(window_ms,fs_native,origin_ms=origin_ms)
    n=hi-lo; n_out=output_length(n,fs_native,target_hz)
    if n_out>pad_to:
        raise ValueError('crop does not fit padded input')
    return {'window_ms':list(window_ms),'native_start':lo,'native_stop_exclusive':hi,
            'native_n':n,'first_sample_ms':origin_ms+1000*lo/fs_native,
            'last_sample_ms':origin_ms+1000*(hi-1)/fs_native,
            'native_sample_span_ms':1000*n/fs_native,
            'resampled_valid_n':n_out,'target_hz':target_hz,'pad_n':pad_to-n_out,
            'resample_input':'native_crop_only','physical_inference':'direct_sample_support_not_causality'}

def crop_resample_pad(x, window_ms, fs_native, *, anchor_index=0, origin_ms=0,
                      target_hz=200, pad_to=200):
    """x[...,time] must already use the declared amplitude preprocessing.

    The resampler only sees the native crop. Right padding follows resampling.
    Whole-record filtering/normalization in x is NOT undone by this function.
    """
    from scipy.signal import resample
    x=np.asarray(x)
    if x.ndim<1 or not np.issubdtype(x.dtype,np.number):
        raise ValueError('numeric signal required')
    meta=describe(window_ms,fs_native,origin_ms=origin_ms,target_hz=target_hz,pad_to=pad_to)
    a,b=meta['native_start']+anchor_index,meta['native_stop_exclusive']+anchor_index
    if a<0 or b>x.shape[-1]:
        raise ValueError(f'crop [{a}:{b}] outside available [0:{x.shape[-1]}]')
    crop=x[...,a:b]
    if not np.isfinite(crop).all():
        raise ValueError('nonfinite crop')
    valid=resample(crop,meta['resampled_valid_n'],axis=-1)
    out=np.pad(valid,[(0,0)]*(valid.ndim-1)+[(0,meta['pad_n'])])
    meta.update(actual_array_start=a,actual_array_stop_exclusive=b,anchor_index=anchor_index)
    return out,meta

def source_tick_offsets(*, mode='segment_contained'):
    # prior33.contract.tick(k)=(64*k+25)//50; exact source grid, not every sample.
    offsets=(64*np.arange(250,dtype=np.int64)+25)//50
    upper=281 if mode=='segment_contained' else 318 if mode=='cache_contained' else None
    if upper is None:
        raise ValueError('mode must be segment_contained or cache_contained')
    return offsets[(offsets>=26)&(offsets<=upper)]

def direct_access_interval(segment_start,offset):
    """Union of actual three crops in native 64-Hz sample indices."""
    return segment_start+offset-12,segment_start+offset+39

def disjoint_with_guard(a,b,guard_samples=0):
    if guard_samples<0 or a[1]<=a[0] or b[1]<=b[0]:
        raise ValueError('valid intervals and nonnegative guard required')
    return a[1]+guard_samples<=b[0] or b[1]+guard_samples<=a[0]
