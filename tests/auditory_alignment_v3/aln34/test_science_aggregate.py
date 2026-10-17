import numpy as np
import pytest
from auditory_alignment_v3.aln34.science_aggregate import difference, joint_ols


def test_undefined_mismatch_stays_missing():
    assert difference(.3, None) is None
    assert difference(None, .3) is None
    assert difference(.3, -.1) == pytest.approx(.4)


def test_age_group_coefficients_and_family_include_every_endpoint():
    ids = [str(i) for i in range(24)]
    cov = {p: {'age': 12 * (2 + i / 4), 'duration': 5 + (i % 5), 'group': 'HA' if i % 3 else 'NH'} for i, p in enumerate(ids)}
    y = {p: .2 * cov[p]['age'] / 12 + .5 * (cov[p]['group'] == 'HA') for p in ids}
    result = joint_ols({'x': y, 'negative_x': {p: -v for p, v in y.items()}}, cov, ids, False, 31, 80)
    assert result['n'] == 24
    assert result['design_rank'] == 3
    assert result['endpoints']['x']['coef']['age_per_year']['est'] == pytest.approx(.2)
    assert result['endpoints']['x']['coef']['HA_indicator']['est'] == pytest.approx(.5)
    assert result['simultaneous_coefficient_family']['n_members'] == 4


def test_duration_missingness_and_collinearity_reported():
    ids = [str(i) for i in range(12)]
    cov = {p: {'age': 12 + i, 'duration': 12 + i, 'group': 'HA'} for i, p in enumerate(ids)}
    values = {'x': {p: i for i, p in enumerate(ids)}}
    r = joint_ols(values, cov, ids, True, 10, 20)
    assert r['design_rank'] == 2 and 'rank-deficient' in r['note']
    for p in ids[:8]: cov[p]['duration'] = None
    r = joint_ols(values, cov, ids, True, 10, 20)
    assert r['n'] == 4 and r['missing_or_outside_population'] == 8
