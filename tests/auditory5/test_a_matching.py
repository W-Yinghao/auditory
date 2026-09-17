import numpy as np
from auditory5.routes.a_matching import mean_matching_matrices, aggregate_match, bootstrap_match

def test_known_matrix_and_distance_sign():
    a=np.array([[[1.,0.],[0.,1.]]]); b=a.copy(); r=mean_matching_matrices(a,b)
    assert np.allclose(r['cosine'], np.eye(2), equal_nan=True)
    assert aggregate_match([r['squared_distance']], [['a','b']], metric='squared_distance')['estimate'] > 0

def test_duplicate_draws_are_not_off_match_and_no_off_is_invalid():
    m=np.eye(2); assert not np.isfinite(aggregate_match([m], [['a','a']])['estimate'])

def test_paired_identical_bootstrap_is_zero():
    m=np.eye(3); r=bootstrap_match([m], [['a','b','c']], n_boot=20, paired_matrices=[m])
    assert r['paired_ci95'] == [0., 0.]

def test_zero_norm_is_undefined():
    r=mean_matching_matrices(np.zeros((1,2,2)), np.ones((1,2,2)))
    assert r['undefined_zero_norm_count'] == 2
    assert np.isnan(r['cosine'][0,0])

def test_multifold_paired_bootstrap_uses_same_weighted_mean():
    matrices=[np.eye(4),np.eye(6)*3]
    ids=[list('abcd'),list('efghij')]
    r=bootstrap_match(matrices,ids,n_boot=100,paired_matrices=matrices)
    assert r['paired_estimate']==0 and r['paired_ci95']==[0.,0.]
    assert r['estimate']==2.2

def test_one_invalid_fold_cannot_be_silently_dropped():
    result=aggregate_match([np.eye(3),np.full((2,2),np.nan)],[list('abc'),list('de')])
    assert not np.isfinite(result['estimate']) and result['valid_folds']==1
