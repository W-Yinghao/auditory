import numpy as np
import pytest
from aln32_reference.diagnostics import query_content_diagnostic,risk_increment,phase_coordinate_example

def test_time_only_not_eeg():
    q=np.arange(20)[None,:,None];u=np.tile(q,(10,1,3))
    d=query_content_diagnostic(u)
    assert d['template_fraction']==1 and d['content_fraction']==0

def test_components_sum():
    d=query_content_diagnostic(np.random.default_rng(1).normal(size=(8,12,3)))
    assert abs(d['total_variance']-d['common_query_template_variance']-d['fixed_query_between_segment_variance'])<1e-12

def test_constant_is_descriptive():assert query_content_diagnostic(np.ones((2,3,4)))['content_fraction'] is None

def test_phase_counterexample():
    d=phase_coordinate_example()
    assert abs(d['linear_unaligned_r'])<.05
    assert d['linear_aligned_r']>.99 and d['phase_interaction_r']>.99

def test_risk_sign():assert risk_increment(np.array([1,2]),np.array([.8,1.8]))==pytest.approx(.2)
def test_risk_invalid():
    with pytest.raises(ValueError):risk_increment(np.array([1]),np.array([1,2]))
