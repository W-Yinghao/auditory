import pytest
import numpy as np
from aln32_reference.geometry import aligned_windows,support_counts,require_equal_access

def test_128_support():
    c=support_counts(128)
    assert c['pre_samples']==51 and c['post_samples']==77 and c['n_samples']==128

def test_100_support():assert support_counts(100)['n_samples']==100

def test_boundary_exact():
    x=np.arange(200)[None].astype(float)
    w,m=aligned_windows(x,np.array([20]),np.array([[0,10]]),4,6,np.array([[0,200]]))
    assert (w[0,0,0,:4]==0).all()
    np.testing.assert_equal(w[0,0,0,4:],x[0,20:26])
    np.testing.assert_equal(w[0,1,0],x[0,26:36])
    assert m[0,0].sum()==6 and m[0,1].sum()==10

def test_postonly_masks_past():
    x=np.ones((2,100))
    w,m=aligned_windows(x,np.array([0]),np.array([[20]]),4,6,np.array([[0,100]]),post_only=True)
    assert (w[...,:4]==0).all() and m.sum()==6

def test_no_adjacent_record_read():
    x=np.zeros((1,100));x[:,50:]=999
    with pytest.raises(ValueError):
        aligned_windows(x,np.array([40]),np.array([[6]]),4,6,np.array([[0,50]]))
    w,m=aligned_windows(x,np.array([40]),np.array([[6]]),4,6,np.array([[0,50]]),right_policy='zero')
    assert (w==0).all() and m.sum()==8

def test_window_outside_perturbation():
    x=np.random.default_rng(1).normal(size=(2,200));xx=x.copy();xx[:,80:]+=999
    a,_=aligned_windows(x,np.array([0]),np.array([[40]]),4,6,np.array([[0,200]]))
    b,_=aligned_windows(xx,np.array([0]),np.array([[40]]),4,6,np.array([[0,200]]))
    np.testing.assert_equal(a,b)

def test_access_check():
    require_equal_access(np.array([[0,1,1]]),np.array([[0,1,2]]),np.array([[1,1]]),np.array([[1,2]]))
    with pytest.raises(ValueError):
        require_equal_access(np.array([[1,1]]),np.array([[0,1]]),np.array([[1,1]]),np.array([[1,2]]))

def test_bounds_required_shape():
    with pytest.raises(ValueError):
        aligned_windows(np.ones((1,10)),np.array([0]),np.array([[1]]),1,1,np.array([0,10]))
