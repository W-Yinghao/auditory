import numpy as np
import pytest
from aln3_reference.calibration import AffineLogitCalibrator
from aln3_reference.metrics import binary_logloss_bits_from_logits, retrieval_logloss_bits, paired_risk_gain


def test_constant_scores_recover_prior():
    y=np.r_[np.zeros(80),np.ones(20)]; x=np.zeros(100)
    m=AffineLogitCalibrator.fit(x,y)
    np.testing.assert_allclose(m.predict(x),.2)


def test_prior_recovery_improves_nll_not_discrimination():
    y=np.r_[np.zeros(80),np.ones(20)]; x=np.zeros(100); m=AffineLogitCalibrator.fit(x,y)
    old=binary_logloss_bits_from_logits(x,y).mean(); new=binary_logloss_bits_from_logits(m.logits(x),y).mean()
    assert new<old and np.unique(m.predict(x)).size==1
    np.testing.assert_allclose(old-new,.2780719051,atol=1e-9)


def test_positive_slope_keeps_ranking():
    r=np.random.default_rng(9); x=r.normal(size=400); y=(x+r.normal(size=400)>.5).astype(int)
    m=AffineLogitCalibrator.fit(x,y)
    assert m.slope>0
    np.testing.assert_array_equal(np.argsort(x),np.argsort(m.logits(x)))


def test_calibration_weighted_prior():
    x=np.zeros(4); y=[0,0,0,1]; w=[1,1,1,3]
    m=AffineLogitCalibrator.fit(x,y,w)
    np.testing.assert_allclose(m.predict(x),.5)


def test_calibration_rejects_one_class():
    with pytest.raises(ValueError): AffineLogitCalibrator.fit([0,1],[0,0])


def test_calibration_rejects_nonfinite():
    with pytest.raises(ValueError): AffineLogitCalibrator.fit([np.nan,1],[0,1])


def test_extreme_logits_are_finite():
    assert np.isfinite(binary_logloss_bits_from_logits([-1000,1000],[1,0])).all()


def test_uniform_retrieval_matches_log_candidates():
    np.testing.assert_allclose(retrieval_logloss_bits(np.zeros((3,8)),np.array([0,2,7])),3.)


def test_retrieval_rejects_invalid_labels():
    with pytest.raises(ValueError): retrieval_logloss_bits(np.zeros((3,2)),np.array([0,2,1]))


def test_query_risk_gain_preserves_negative_values():
    np.testing.assert_allclose(paired_risk_gain([1,1],[.5,2],['a','b'],['a','b']),[.5,-1.])


def test_query_risk_rejects_mismatched_identity():
    with pytest.raises(ValueError): paired_risk_gain([1,1],[.5,2],['a','b'],['b','a'])


def test_mismatch_difference_not_true_risk_increment():
    r_e,r_el,mm_e,mm_el=2.,1.8,3.,4.
    increment=r_e-r_el
    difference_of_gains=(mm_el-r_el)-(mm_e-r_e)
    assert not np.isclose(increment,difference_of_gains)
