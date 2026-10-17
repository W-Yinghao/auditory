import numpy as np
import pytest
from auditory_alignment_v3.aln34 import strong_fusion as F


def test_probability_endpoints_and_simple_ties():
    p=np.array([[.1,.9],[.8,.2]]);q=p[:,::-1]
    assert np.array_equal(F.mix(p,q,1),p)
    assert np.array_equal(F.mix(p,q,0),q)
    assert F.choose({'zero':1.,'trained':1.})=='zero'
    assert F.choose({'zero':1.,'trained':.9})=='trained'


def test_parallel_residual_is_removed_by_normalization():
    rng=np.random.default_rng(0);u=F.normalize(rng.normal(size=(4,8,32)));r=2*u
    p=F.normalize(u+r);s={'native':np.zeros((4,5)),'unified':np.ones((4,5))}
    d=F.residual_diagnostics(u,r,p,s,s,np.array(['a','a','b','b']))
    assert all(v['after_normalization_change']<1e-12 for v in d.values())
    assert all(v['relative_orthogonal']<1e-10 for v in d.values())
    assert all(v['native']['probability_total_variation']==0 for v in d.values())


def test_person_loss_averaging_does_not_weight_query_counts():
    s=np.array([[5.,0.],[0.,5.],[0.,5.]])
    values=F.person_metrics(s,np.zeros(3,dtype=int),np.array(['one','two','two']))
    assert np.isclose(F.mean_risk(values),(values['one']['true_nll_bits']+values['two']['true_nll_bits'])/2)


def test_sound_coordinate_mismatch_rejected():
    names=('train_e0','cal_e0','query_e0','train_roles','query_people','query_own','cal_own')
    a={k:np.array([1]) for k in names}
    a.update({k:np.ones((2,3,32)) for k in ('train_v','query_v','cal_v','train_a','query_a','cal_a')})
    b={k:v.copy() for k,v in a.items()};b['query_v']+=.01
    with pytest.raises(ValueError,match='sound coordinates'):F.assert_aligned(a,b)


def test_zero_residual_state_and_training_change():
    rng=np.random.default_rng(13)
    a={'train_u':F.normalize(rng.normal(size=(4,8,32))).astype('float32'),
       'train_v':F.normalize(rng.normal(size=(4,8,32))).astype('float32')}
    b={'train_u':F.normalize(rng.normal(size=(4,8,32))).astype('float32')}
    states=F.residual_states(a,b,1,(0,2))
    assert not states[0]['w'].any() and not states[0]['b'].any()
    assert np.linalg.norm(states[2]['w'])>0
