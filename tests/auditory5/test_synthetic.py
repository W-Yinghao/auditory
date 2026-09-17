import numpy as np
import pytest
from auditory5.synthetic import _a_world,_b_world,_c_world,_d_world,_e_world,_mc_interval,run_synthetic_suite

def test_wilson_intervals_not_degenerate_at_zero_or_one():
    assert _mc_interval(0,100)['upper']>.03
    assert _mc_interval(100,100)['lower']<.97

def test_a_stable_background_cancels_from_condition_difference():
    pos=_a_world(np.random.default_rng(4),10,True,boot=40)
    neg=_a_world(np.random.default_rng(4),10,False,boot=40)
    assert pos['effect']>neg['effect']+.3

def test_e_gap_direction_and_invertible_control():
    pos=_e_world(np.random.default_rng(7),2,True,boot=40)
    neg=_e_world(np.random.default_rng(7),2,False,boot=40)
    assert pos['effect']>.1
    assert abs(neg['effect'])<1e-6

def test_b_binary_history_and_d_softmax_contract():
    b=_b_world(np.random.default_rng(8),2,True,boot=40)
    d=_d_world(np.random.default_rng(9),2,True,boot=40)
    assert b['effect']>.05 and b['pre_adjusted_effect']>.05
    assert d['softmax_max_error']<1e-10

def test_repetitions_must_be_positive():
    with pytest.raises(ValueError):run_synthetic_suite('/tmp/unused',repetitions=0)
