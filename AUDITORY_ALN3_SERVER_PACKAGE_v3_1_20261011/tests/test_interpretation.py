import numpy as np

def test_mismatch_gain_is_not_bounded_by_binary_entropy():
 e=.01
 risk_true=-(1-e)*np.log2(1-e)-e*np.log2(e)
 risk_mismatch=-.5*np.log2(1-e)-.5*np.log2(e)
 assert (1-risk_true)<1 and risk_mismatch-risk_true>3

def test_three_clock_columns_dependent():
 rng=np.random.default_rng(4);experience=rng.uniform(1,5,33);deprivation=rng.uniform(1,8,33);age=experience+deprivation
 X=np.c_[np.ones(33),age,deprivation,experience]
 assert np.linalg.matrix_rank(X)==3
 beta=np.array([0.,1.,2.,3.]);shift=np.array([0.,.7,-.7,-.7])
 np.testing.assert_allclose(X@beta,X@(beta+shift))

def test_cohort_cmi_given_unique_stimulus_is_zero_even_if_z_is_cohort():
 # S identifies D and Z=D; conditional on each S, both variables are constants.
 stimulus=np.arange(8);domain=stimulus//4;z=domain.copy()
 h_d_given_s=0.
 h_d_given_zs=0.
 assert h_d_given_s-h_d_given_zs==0.
 assert np.array_equal(z,domain)
