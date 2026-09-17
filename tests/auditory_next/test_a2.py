"""A2 synthetic support and residual contracts; run through Slurm only."""
from dataclasses import replace
import numpy as np
import pytest

from auditory_next.a2_overlap import CELLS, freeze_overlap, draw_trials, summarize_draws
from auditory_next.a2_residual_audit import (MECHANISMS, audit_residual_world, fit_background,
    identity_contrast, inner_product_decomposition, make_residual_world, matching_statistics)


def metadata(n=30, cells_by_group=None, quota=6):
    rows = []
    for group in range(n):
        for cell in (range(4) if cells_by_group is None else cells_by_group[group]):
            for half in range(2):
                for label in range(2):
                    for j in range(quota):
                        rows.append(dict(trial_id=f'synthetic_{group}_{cell}_{half}_{label}_{j}',
                            split_group_id=f'g{group:03d}', record_id=f'record{group}', segment_id='segment0',
                            stimulus_local_id=label, previous_event_id=f'previous_{group}_{cell}_{half}_{label}_{j}',
                            previous_code='1', previous_run_length=3 if cell < 2 else 6,
                            history_chain_complete=True, accepted=True, A_boundary_eligible=True,
                            A_half=half, A_block_id=2 * (j % 3) + half,
                            segment_position_fraction=.25 if cell % 2 == 0 else .75))
    groups = [f'g{i:03d}' for i in range(n)]
    folds = [dict(outer_fold=k, train_groups=[g for i, g in enumerate(groups) if i % 5 != k],
                  test_groups=[g for i, g in enumerate(groups) if i % 5 == k]) for k in range(5)]
    return rows, folds


def test_all_eleven_regions_and_largest_region_before_candidate_count():
    rows, folds = metadata(cells_by_group=[range(4)] * 25 + [(0, 1)] * 5)
    frozen = freeze_overlap(rows, folds)
    assert len(frozen.candidates) == 11
    assert frozen.omega == CELLS and len(frozen.groups) == 25
    assert frozen.status == 'SUFFICIENT_FOR_SCREEN'
    assert frozen.cell_weights == (.25,) * 4
    assert any(len(region.groups) == 30 for region in frozen.candidates)


def test_region_tie_is_lexical_and_insufficiency_never_lowers_quota():
    rows, folds = metadata(50, [(0, 1, 2)] * 25 + [(0, 1, 3)] * 25)
    assert freeze_overlap(rows, folds).omega == CELLS[:3]
    rows, folds = metadata(20, [range(4)] * 5 + [(0, 1)] * 15)
    frozen = freeze_overlap(rows, folds)
    assert frozen.status == 'DESCRIPTIVE_ONLY'
    assert frozen.omega == CELLS[:2] and len(frozen.groups) == 20
    rows, folds = metadata(30, quota=5)
    empty = freeze_overlap(rows, folds)
    assert empty.status == 'INSUFFICIENT' and empty.groups == ()
    assert empty.trials_per_cell == 6 and len(empty.omega) >= 2


def test_per_fold_test_and_training_support_and_leakage_are_enforced():
    rows, folds = metadata()
    groups = [f'g{i:03d}' for i in range(30)]
    tests = [groups[:1], groups[1:8], groups[8:15], groups[15:22], groups[22:]]
    unequal = [dict(outer_fold=k, test_groups=test, train_groups=sorted(set(groups) - set(test))) for k, test in enumerate(tests)]
    assert freeze_overlap(rows, unequal).status == 'DESCRIPTIVE_ONLY'
    broken = [dict(f) for f in folds]
    broken[0]['train_groups'] = broken[0]['train_groups'] + broken[0]['test_groups'][:1]
    with pytest.raises(ValueError, match='FOLD_LEAKAGE'):
        freeze_overlap(rows, broken)


def test_block_identifiers_use_record_and_segment_and_actual_draw_has_three():
    rows, folds = metadata()
    for row in rows:
        # Same local block number is not the same physical block across segments.
        row['segment_id'] = 'segment' + str(row['A_block_id'] // 2)
        row['A_block_id'] = row['A_half']
    frozen = freeze_overlap(rows, folds)
    draws = draw_trials(frozen)
    lookup = {r.trial_id: r for r in frozen.trials}
    assert draws.trial_ids.shape == (20, 30, 2, 2, 4, 6)
    assert draws.trial_ids.flags.writeable is False
    for trial_ids in draws.trial_ids.reshape(-1, 24):
        assert len(set(trial_ids)) == 24
        assert len({lookup[tid].block for tid in trial_ids}) >= 3
    np.testing.assert_array_equal(draws.trial_ids, draw_trials(freeze_overlap(list(reversed(rows)), folds)).trial_ids)


def test_history_is_past_chain_not_old_b_target_and_freeze_is_not_refit():
    rows, folds = metadata()
    for row in rows:
        row.update(history_target=None, current_run_length=999, history_status='irrelevant_old_field')
    frozen = freeze_overlap(rows, folds)
    original_draws = draw_trials(frozen)
    original_previous = [(r['previous_event_id'], r['previous_run_length']) for r in rows]
    for row in rows:
        row['stimulus_local_id'] = 1 - row['stimulus_local_id']
        row['accepted'] = False
        row['current_run_length'] = -1
    np.testing.assert_array_equal(draw_trials(frozen).trial_ids, original_draws.trial_ids)
    assert original_previous == [(r['previous_event_id'], r['previous_run_length']) for r in rows]
    assert freeze_overlap(rows, folds).status == 'INSUFFICIENT'  # a NEW design, not mutated old support


def test_unknown_history_and_wrong_previous_code_do_not_enter_overlap():
    rows, folds = metadata()
    for row in rows:
        if row['split_group_id'] == 'g000':
            row['history_chain_complete'] = False
        elif row['split_group_id'] == 'g001':
            row['previous_code'] = '2'
        elif row['split_group_id'] == 'g002':
            row['previous_run_length'] = 2
    result = freeze_overlap(rows, folds)
    assert len(result.groups) == 27
    assert not {'g000', 'g001', 'g002'} & set(result.groups)


def test_selected_cell_summary_is_uniform_and_features_cannot_select_trials():
    rows, folds = metadata()
    frozen = freeze_overlap(rows, folds)
    draws = draw_trials(frozen)
    ids = [row['trial_id'] for row in rows]
    cells = {row.trial_id: CELLS.index(row.cell) for row in frozen.trials}
    features = np.array([[10 * row['stimulus_local_id'] + cells[row['trial_id']]]
                         for row in rows])
    summary = summarize_draws(features, ids, draws, feature_scope_id='synthetic_outer0')
    np.testing.assert_allclose(summary['delta'], 10.)
    np.testing.assert_allclose(summary['common_response'], 6.5)
    altered = features[::-1].copy()
    summarize_draws(altered, ids, draws, feature_scope_id='synthetic_outer0')
    np.testing.assert_array_equal(draws.trial_ids, draw_trials(frozen).trial_ids)
    with pytest.raises(ValueError, match='SINGLE_FEATURE_SCOPE'):
        summarize_draws(features, ids, draws, feature_scope_id=['fold0', 'fold1'])
    with pytest.raises(ValueError, match='COMMON_CELL_DISTRIBUTION'):
        draw_trials(replace(frozen, cell_weights=(.7, .1, .1, .1)))


def test_four_term_identity_every_pair_and_identity_difference():
    rng = np.random.default_rng(2)
    arrays = [rng.normal(size=(4, 7, 5)) for _ in range(4)]
    ids = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    audit = inner_product_decomposition(*arrays, ids)
    terms = audit['matrices']
    np.testing.assert_allclose(terms['residual'], terms['delta_delta'] + terms['minus_delta_prediction'] +
                              terms['minus_prediction_delta'] + terms['prediction_prediction'], atol=1e-12)
    assert audit['matching_gain_error'] < 1e-12
    assert abs(audit['summaries']['residual']['matched'] - sum(audit['summaries'][k]['matched'] for k in terms if k != 'residual')) < 1e-12
    assert abs(audit['summaries']['residual']['mismatched'] - sum(audit['summaries'][k]['mismatched'] for k in terms if k != 'residual')) < 1e-12


def test_bootstrap_repeated_identity_is_not_an_other_person():
    matrix = np.array([[10., 10., 1.], [10., 10., 1.], [1., 1., 10.]])
    summary = identity_contrast(matrix, ['same', 'same', 'other'])
    assert summary == dict(matched=10., mismatched=1., gain=9.)
    with pytest.raises(ValueError, match='TWO_IDENTITIES'):
        identity_contrast(np.ones((2, 2)), ['same', 'same'])


def test_shared_prediction_can_create_repeatability_with_no_delta():
    background = np.eye(8)
    zero = np.zeros_like(background)
    audit = inner_product_decomposition(zero, zero, 2 * background, 2 * background, list('abcdefgh'))
    assert audit['summaries']['delta_delta']['gain'] == 0.
    assert audit['summaries']['residual']['gain'] == 4.
    assert audit['summaries']['prediction_prediction']['gain'] == 4.
    undefined = matching_statistics(zero, zero, list('abcdefgh'))
    assert undefined['cosine'] is None and undefined['cosine_status'] == 'UNDEFINED_ZERO_NORM'
    assert undefined['inner_product']['gain'] == 0.


def test_three_worlds_share_conditions_and_fit_never_sees_test_values():
    for world_name in MECHANISMS:
        world = make_residual_world(world_name, n_train=18, n_test=10, n_features=5, n_background=4, seed=5)
        result = audit_residual_world(world)
        assert result['world_draws'] == 1 and set(result['conditions']) == {'zero', 'fixed', 'fitted'}
        assert all(row['shared_draw_seed'] == 5 and row['max_pair_error'] < 1e-10 for row in result['conditions'].values())
        coefficient = result['fitted_predictor'].coefficient.copy()
        world['test']['delta'] *= -1000
        world['test']['background'] += 10000
        again = audit_residual_world(world)
        np.testing.assert_array_equal(again['fitted_predictor'].coefficient, coefficient)
        if world_name == 'null':
            assert not np.any(world['train']['stimulus']) and not np.any(world['train']['nuisance'])
        if world_name == 'predictable_nuisance':
            assert not np.any(world['train']['stimulus'])


def test_real_predictable_nuisance_and_signal_are_distinct_constructed_cases():
    world = make_residual_world('predictable_nuisance', seed=8)
    delta = world['test']['delta']
    predicted = 2 * world['test']['background'] @ world['true_weight']
    np.testing.assert_allclose(delta - predicted, world['test']['epsilon'], atol=1e-12)
    world = make_residual_world('individual_stimulus', seed=8)
    np.testing.assert_array_equal(world['test']['stimulus'][:, 0], world['test']['stimulus'][:, 1])
    assert not np.any(world['test']['nuisance'])
    with pytest.raises(ValueError, match='FIXED_AUDIT_RIDGE'):
        fit_background(world['train']['background'], world['train']['delta'], alpha=.1)
