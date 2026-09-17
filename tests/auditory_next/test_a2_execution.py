"""Pure A2 runner statistics and train-only transform tests; Slurm gates only."""
import pickle
import numpy as np
import pytest

from auditory5.contracts import FitScope
from auditory_next.a2_execution import (DegenerateAxis, apply_summary_axis,
    fit_summary_axis, paired_matching_summary)


def records():
    result = []
    for fold in range(2):
        result.append(dict(fold=fold, groups=tuple(f'g{fold}_{i}' for i in range(4)), matrices={
            'post_delta': dict(cosine=np.eye(4), inner_product=2*np.eye(4)),
            'pre_delta': dict(cosine=np.ones((4,4)), inner_product=4*np.ones((4,4))),
            'common_response': dict(cosine=np.ones((4,4)), inner_product=np.ones((4,4)))}))
    return result


def test_post_pre_is_difference_of_scalar_statistics_with_shared_identity_draws():
    output = paired_matching_summary(records(), expected_folds=2)
    by_name = {(row['endpoint'],row['metric']):row for row in output}
    for metric, expected in (('cosine',1.),('inner_product',2.)):
        post, pre, difference = [by_name[(name,metric)] for name in ('post_delta','pre_delta','post_minus_pre')]
        assert post['estimate'] == expected and pre['estimate'] == 0.
        assert difference['estimate'] == expected
        assert difference['ci_lower'] == difference['ci_upper'] == expected
        assert difference['invalid_replicates'] == post['invalid_replicates'] == pre['invalid_replicates']
        assert difference['n_candidates'] == 8 and difference['n_bootstrap'] == 2000
        assert difference['valid_replicates'] + difference['invalid_replicates'] == 2000


def test_missing_pre_cannot_be_zero_filled_or_make_a_complete_paired_endpoint():
    rows = records()
    del rows[0]['matrices']['pre_delta']
    output = paired_matching_summary(rows, expected_folds=2)
    assert {row['endpoint'] for row in output} == {'post_delta','common_response'}
    assert all(row['n_candidates'] == 8 for row in output)
    with pytest.raises(ValueError,match='INCOMPLETE_OUTER_MATRIX'):
        paired_matching_summary(rows[:1], expected_folds=2)


def test_candidates_cannot_be_reused_across_outer_coordinate_systems():
    rows = records()
    rows[1]['groups'] = rows[0]['groups']
    with pytest.raises(ValueError,match='OUTER_CANDIDATE_OVERLAP'):
        paired_matching_summary(rows, expected_folds=2)


def test_training_axis_ignores_heldout_data_and_allows_different_pre_post_widths():
    rng = np.random.default_rng(8)
    groups = tuple(f'train{i}' for i in range(12))
    scope = FitScope(groups, test_groups=('heldout0','heldout1'))
    post = rng.normal(size=(20,12,2,14))
    pre = rng.normal(size=(20,12,2,5))
    post_axis = fit_summary_axis(post,groups,scope)
    pre_axis = fit_summary_axis(pre,groups,scope)
    assert post_axis['dimension'] == 8 and pre_axis['dimension'] == 5
    saved = pickle.dumps((post_axis,pre_axis))
    assert apply_summary_axis(rng.normal(size=(20,2,2,14)),post_axis).shape == (20,2,2,8)
    assert apply_summary_axis(rng.normal(size=(20,2,2,5))*10000,pre_axis).shape == (20,2,2,5)
    assert pickle.dumps((post_axis,pre_axis)) == saved
    np.testing.assert_allclose(post_axis['scaler'].mean_,post.mean(axis=(0,2)).mean(axis=0),atol=1e-14)
    with pytest.raises(ValueError,match='LEAKAGE'):
        fit_summary_axis(post,('heldout0',)+groups[1:],scope)


def test_zero_rank_and_zero_test_cosine_are_explicitly_unavailable():
    groups = tuple(f'train{i}' for i in range(12))
    with pytest.raises(DegenerateAxis,match='ZERO_TRAINING_CONTRAST'):
        fit_summary_axis(np.zeros((20,12,2,9)),groups,FitScope(groups))
    rows = records()
    rows[0]['matrices']['post_delta']['cosine'][:] = np.nan
    output = paired_matching_summary(rows,expected_folds=2)
    assert not any(row['endpoint'] in ('post_delta','post_minus_pre') and row['metric']=='cosine' for row in output)
    assert any(row['endpoint']=='post_delta' and row['metric']=='inner_product' for row in output)
