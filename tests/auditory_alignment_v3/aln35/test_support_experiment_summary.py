"""Synthetic exporter tests; these values are never EEG evidence."""
import copy
import math

import pytest

from auditory_alignment_v3.aln35 import support_experiment_summary as S


def test_u10_five_draws_average_once_and_never_fill_missing():
    entries = {name: {'query_hash': 'a'*64, 'candidate_hash': 'b'*64,
                     'metrics': {'n_query': 20, 'nll_bits': i, 'top1': .2}}
               for i, name in enumerate(S.DRAW_NAMES)}
    value = S.average_draws(entries, 'dtu', S.DRAW_NAMES)
    assert value['metrics']['nll_bits'] == 2
    assert len(value['draws']) == 5
    missing = {k: v for k, v in entries.items() if k != S.DRAW_NAMES[-1]}
    assert S.average_draws(missing, 'dtu', S.DRAW_NAMES) is None
    entries[S.DRAW_NAMES[-1]]['candidate_hash'] = 'c'*64
    with pytest.raises(S.BindingError, match='candidate'):
        S.average_draws(entries, 'dtu', S.DRAW_NAMES)


def test_query_hash_and_count_are_both_pairing_requirements():
    first = {'query_hash': 'a'*64, 'candidate_hash': 'b'*64, 'metrics': {'n_query': 10}}
    second = copy.deepcopy(first); second['query_hash'] = 'c'*64
    with pytest.raises(S.BindingError, match='query hashes'):
        S.same_query([first, second], 'dtu')
    second = copy.deepcopy(first); second['metrics']['n_query'] = 9
    with pytest.raises(S.BindingError, match='query counts'):
        S.same_query([first, second], 'dtu')


def synthetic_panel():
    people = {f'p{i}': {'group': 'HA' if i < 3 else 'NH', 'outer_fold': 0} for i in range(6)}
    export = S.Export({'dtu': people}, {})
    panel = export.panel('matched_U', 'dtu', 'local', 'native')
    for i, (identity, person) in enumerate(people.items()):
        for cf in (0, 1):
            for fraction in (50, 100):
                # reference minus candidate = i+cf; equal content mean i+.5.
                cell = {'metrics': {'nll_bits': 10+i if fraction == 100 else 10-cf, 'n_query': 20},
                        'query_hash': S.digest([identity, cf]), 'candidate_hash': 'b'*64}
                prov = {'population_fit_identities': ['source'], 'selection_identities': [],
                        'outer_fold': '0', 'source_record': 'SYNTHETIC_ONLY', 'source_sha256': 'd'*64}
                export.add(panel, identity, person['group'], {'content_fold': cf}, f'fraction_{fraction}', cell, prov)
    return export, panel


def test_fixed_se_whole_people_and_content_means():
    export, panel = synthetic_panel()
    spec = S.build_spec(panel, 'nll_bits', export.rosters)
    result = S.REF.analyze(panel['rows'], spec)
    contrast = result['contrasts'][0]
    assert result['coverage']['all']['common_complete_n'] == 6
    assert contrast['estimate'] == 3
    assert math.isclose(contrast['original_se'], math.sqrt(1/6))
    assert result['bootstrap']['B'] == 4000
    assert result['bootstrap']['original_se_reestimated_per_draw'] is False
    assert result['identity_values']['all']['p2'][contrast['id']] == 2.5
    assert contrast['simultaneous_ci'][0] < 3 < contrast['simultaneous_ci'][1]


def test_missing_content_fold_excludes_whole_person_not_fold_replicate():
    export, panel = synthetic_panel()
    rows = [r for r in panel['rows'] if not (r['identity'] == 'p0' and r['fold'] == 'content_1')]
    result = S.REF.analyze(rows, S.build_spec(panel, 'nll_bits', export.rosters))
    coverage = result['coverage']['all']
    assert coverage['expected_n'] == 6 and coverage['common_complete_n'] == 5
    assert coverage['excluded_incomplete']['p0']['reason'] == 'missing_required_cells'


def test_pairing_mismatch_and_outer_seen_person_fail():
    export, panel = synthetic_panel(); spec = S.build_spec(panel, 'nll_bits', export.rosters)
    rows = copy.deepcopy(panel['rows']); rows[0]['query_set_id'] = 'different'
    with pytest.raises(S.REF.ReferenceError, match='query_set_id'):
        S.REF.analyze(rows, spec)
    rows = copy.deepcopy(panel['rows']); rows[0]['provenance']['selection_identities'] = [rows[0]['identity']]
    with pytest.raises(S.REF.ReferenceError, match='selection_identities'):
        S.REF.analyze(rows, spec)


def test_nonregular_zero_difference_kept_without_equivalence_interval():
    export, panel = synthetic_panel()
    for row in panel['rows']:
        row['value'] = 1
    result = S.REF.analyze(panel['rows'], S.build_spec(panel, 'nll_bits', export.rosters))
    assert result['status'] == 'nonregular'
    assert result['contrasts'][0]['estimate'] == 0
    assert result['contrasts'][0]['simultaneous_ci'] is None
    assert result['coverage']['all']['common_complete_n'] == 6


def test_no_results_reports_roster_and_null_not_zero_effect():
    export, panel = synthetic_panel()
    result = S.empty_result(S.build_spec(panel, 'nll_bits', export.rosters))
    assert result['coverage']['all']['expected_n'] == 6
    assert result['coverage']['all']['common_complete_n'] == 0
    assert result['contrasts'][0]['estimate'] is None


def test_episode_merge_58_plus_2_and_no_method_change():
    original = {'rows': [{'id': f'old{i}', 'source': {'source_execution_id': 'source'}, 'support_steps': 20 if i%2 == 0 else 100,
                         'encoder_updates': 100, 'outer_fold': i//2, 'content_fold': 0, 'target_steps': [0, 5, 20]}
                        for i in range(60)]}
    replacements = []
    for i in (0, 1):
        row = copy.deepcopy(original['rows'][i]); row.update(id=f'new{i}', parent_aln35_id=f'old{i}')
        row['source']['legacy_inner'] = {'checkpoint_sha256': 'a'*64}
        replacements.append(row)
    successor = {'rows': replacements, 'supersedes_dependency_only': {'old0': 'new0', 'old1': 'new1'}}
    merged = S.episode_units(original, successor)
    assert len(merged) == 60
    assert sum(lane == 'episode_pressure_v1' for lane, _, _ in merged) == 58
    assert {unit['id'] for lane, unit, _ in merged if lane == 'episode_lineage_v2'} == {'new0', 'new1'}
    successor['rows'][0]['target_steps'] = [20]
    with pytest.raises(S.BindingError, match='target_steps'):
        S.episode_units(original, successor)


def test_probe_and_unit_drift_never_enter_production():
    unit = {'id': 'expected', 'seed': 3401}
    record = {'id': 'expected', 'unit': unit, 'status': 'complete', 'probe': False, 'plan_sha256': 'a'*64}
    S.valid_record(record, unit, 'a'*64)
    record['probe'] = True
    with pytest.raises(S.BindingError, match='probe'):
        S.valid_record(record, unit, 'a'*64)
    record['probe'] = False; record['unit'] = {**unit, 'seed': 3407}
    with pytest.raises(S.BindingError, match='configuration'):
        S.valid_record(record, unit, 'a'*64)


def matched_pair():
    out = []
    for fraction in (.5, 1.):
        budget = {'U': 20, 'scheduler_horizon_updates': 39, 'candidate_steps': [0, 5, 10, 20]}
        unit = {'fraction': fraction, 'source_lineage': 'source', 'stage': 'outer', 'budget': budget,
                'split': {'full_source_audio_ids': ['a', 'b'], 'evaluation_ids': ['test'],
                          'train_ids': ['a'] if fraction == .5 else ['a', 'b']}}
        out.append({'unit': unit, 'budget': budget, 'ledger': {'initial_model_head_sha256': 'c'*64}})
    return out


def test_matching_rejects_short_cosine_or_initialization_drift():
    pair = matched_pair(); S.validate_matched_pair(*pair)
    pair[0]['budget']['scheduler_horizon_updates'] = 20
    with pytest.raises(S.BindingError, match='long-cosine'):
        S.validate_matched_pair(*pair)
    pair = matched_pair(); pair[0]['ledger']['initial_model_head_sha256'] = 'd'*64
    with pytest.raises(S.BindingError, match='initialization'):
        S.validate_matched_pair(*pair)


def test_family_contains_all_registered_support_terms_and_correct_signs():
    people = {'p': {'group': 'HA', 'outer_fold': 0}}
    export = S.Export({'private_bdf': people}, {})
    panel = export.panel('support', 'private_bdf', 'local', 'linear')
    nll = S.build_spec(panel, 'nll_bits', export.rosters)
    auc = S.build_spec(panel, 'auc', export.rosters)
    assert len(nll['contrasts']) == 17
    assert nll['contrasts'][0]['terms'][0]['weight'] == 1
    assert auc['contrasts'][0]['terms'][0]['weight'] == -1
    assert any(c['id'] == 'H10_vs_U10__rank4_fixed20' for c in nll['contrasts'])


def test_private_bits_per_trial_matches_rows_and_specs_dtu_per_query():
    people = {'p': {'group': 'HA', 'outer_fold': 0}}
    export = S.Export({'private_bdf': people}, {})
    panel = export.panel('support', 'private_bdf', 'local', 'linear')
    cell = {'metrics': {'n_query': 20, 'nll_bits': 1., 'wrong_nll_bits': 2., 'mismatch_gain_bits': 1.},
            'query_hash': 'a'*64, 'candidate_hash': 'fixed_private_binary_labels_0_1'}
    provenance = {'population_fit_identities': ['source'], 'selection_identities': [], 'outer_fold': '0'}
    S.Export.add(export, panel, 'p', 'HA', {'content_fold': 0}, 'U10-zero_step', cell, provenance)
    for metric in ('nll_bits', 'wrong_nll_bits', 'mismatch_gain_bits'):
        row = next(r for r in panel['rows'] if r['metric'] == metric)
        spec = S.build_spec(panel, metric, export.rosters)
        assert row['unit'] == spec['unit'] == 'bits/trial'
        assert S.metric_unit('dtu', metric) == 'bits/query'
    assert S.metric_unit('private_bdf', 'auc') == 'AUC'


def test_whole_unit_transaction_rolls_back_but_other_work_remains():
    export, panel = synthetic_panel(); before = len(panel['rows'])
    def bad(ex, record, path, checksum):
        panel['rows'].append({'partial': 'must not survive'})
        ex.diagnostics['unavailable_people'].append({'partial': True})
        raise S.BindingError('deliberate failed unit')
    assert not S.transaction(export, bad, {}, 'synthetic_unit', 'a'*64)
    assert len(panel['rows']) == before
    assert not export.diagnostics['unavailable_people']
    assert len(export.errors) == 1


def test_snapshot_outputs_are_exclusive_and_do_not_overwrite(tmp_path):
    path = tmp_path/'snapshot.json'
    S.write_new(path, {'version': 1})
    with pytest.raises(FileExistsError):
        S.write_new(path, {'version': 2})
    assert S.read(path)[0] == {'version': 1}


def episode_fixture():
    unit = {'id': 'SYNTHETIC_EPISODE', 'source': {'dataset': 'private_bdf', 'architecture': 'lag_local_tokens'},
            'support_steps': 20, 'outer_fold': 0, 'content_fold': 0}
    geometry = {'private': {'p': {'query_hash': 'a'*64, 'n_query': 20}}}
    export = S.Export({'private_bdf': {'p': {'group': 'HA', 'outer_fold': 0}}}, geometry)
    values = {}
    for regime, base in (('source', 1.), ('ordinary', 2.), ('episode', 3.)):
        supports = {}
        for index, name in enumerate((*S.DRAW_NAMES, 'U30')):
            offset = index/100 if name.startswith('U10') else 0
            supports[name] = {'support': {'query_hash': 'a'*64, 'support_hash': 'b'*64},
                'candidates': {str(step): {'metrics': {mode: {'n_query': 20, 'nll_bits': base+offset+step/1000,
                                                            'auc': None if step == 0 else .6}
                                                     for mode in ('native', 'linear')}} for step in (0, 5, 20)}}
        values[regime] = {'per_participant': {'p': {'status': 'complete', 'group': 'HA', 'supports': supports}}}
    training = {regime: {'stream_sha256': 'c'*64, 'encoder_updates': 100, 'support_optimizer_steps': 2000,
                        'query_exposures': 200, 'support_exposures': 300, 'losses': [1., 2.],
                        'diagnostics': [{'BA_norm': .1, 'encoder_direction_cosine_at_same_state': None}]}
                for regime in ('ordinary', 'episode')}
    source_provenance = {'fit_ids': ['source'], 'calibration_ids': ['source'], 'evaluation_ids': ['p']}
    stage = {'values': values, 'training': training, 'source_provenance': source_provenance,
             'paired_final_update_direction_cosine': None}
    choices = {}
    for mode in ('native', 'linear'):
        choices[mode] = {}
        for support in ('U10', 'U30'):
            offset = .02 if support == 'U10' else 0
            choices[mode][support] = {}
            for regime, chosen, step, base in (('ordinary', 'source', 0, 1.), ('episode', 'episode', 5, 3.)):
                choices[mode][support][regime] = {'status': 'complete', 'chosen': f'{chosen}/{step}',
                    'inner_complete_ids': ['inner'], 'zero_step_selected': step == 0,
                    'source_fallback_selected': chosen == 'source', 'outer_per_identity_nll': {'p': base+offset+step/1000},
                    'outer_result_location': {'regime': chosen, 'target_steps': step, 'support': support, 'readout': mode}}
    return export, {'unit': unit, 'stages': {'inner': copy.deepcopy(stage), 'outer': stage}, 'choices': choices}


def test_episode_parser_separates_fixed20_selected_zero_and_source_diagnostics():
    export, record = episode_fixture()
    S.process_episode(export, record, S.REPO/'private/SYNTHETIC_EPISODE.json', 'd'*64)
    fixed = export.panels['episode_fixed20__private_bdf__local__linear__pressure20']['rows']
    selected = export.panels['episode_selected__private_bdf__local__linear__pressure20']['rows']
    fixed_value = next(r for r in fixed if r['arm'].endswith('/U10-episode') and r['metric'] == 'nll_bits')
    selected_value = next(r for r in selected if r['arm'].endswith('/U10-episode') and r['metric'] == 'nll_bits')
    assert math.isclose(fixed_value['value'], 3.04)
    assert math.isclose(selected_value['value'], 3.025)
    fallback = next(r for r in selected if r['arm'].endswith('/U10-ordinary') and r['metric'] == 'nll_bits')
    assert fallback['metadata']['zero_step_selected'] and fallback['metadata']['source_fallback_selected']
    assert fallback['provenance']['selection_identities'] == ['inner']
    assert not any(r['arm'].endswith('/U10-ordinary') and r['metric'] == 'auc' for r in selected)
    assert len(export.diagnostics['episode_source']) == 4
    assert all(d['paired_final_update_direction_cosine'] is None for d in export.diagnostics['episode_source'])


def test_episode_mismatched_sham_cost_is_a_validation_error():
    export, record = episode_fixture()
    record['stages']['inner']['training']['ordinary']['query_exposures'] += 1
    with pytest.raises(S.BindingError, match='query_exposures'):
        S.process_episode(export, record, S.REPO/'private/SYNTHETIC_EPISODE.json', 'd'*64)


def test_diagnostic_policy_rates_use_decisions_not_people_or_draws():
    export, record = episode_fixture()
    S.process_episode(export, record, S.REPO/'private/SYNTHETIC_EPISODE.json', 'd'*64)
    value = S.diagnostic_summary(export)
    ordinary = next(r for r in value['episode_policy_rates'] if r['regime'] == 'ordinary')
    assert ordinary['complete_policy_decisions'] == 1
    assert ordinary['expected_policy_decisions'] == 5
    assert ordinary['zero_step_fraction_of_complete_decisions'] == 1
    assert ordinary['source_fallback_fraction_of_complete_decisions'] == 1
    assert ordinary['independent_person_n_claimed'] is False
    assert all(r['source_units'] == 1 for r in value['episode_source_pressure'])


def trajectory_fixture():
    row = {'subject_fold': 0, 'content_fold': 0, 'spec': {'adaptation': 'local'}}
    source = {'architecture': 'lag_local_tokens', 'outer': {'row': row}}
    budget = {'U': 20, 'candidate_steps': [0, 5, 10, 20], 'scheduler_horizon_updates': 39}
    split = {'outer_fold': 0, 'train_ids': ['source'], 'readout_fit_cal_ids': ['source'],
             'full_source_audio_ids': ['source', 'audio_only'], 'evaluation_ids': ['p']}
    unit = {'id': 'SYNTHETIC_MATCHED', 'binding': {'source': source}, 'stage': 'outer', 'fraction': .5,
            'source_lineage': 'source_execution', 'split': split, 'budget': budget, 'reuse_existing': False}
    candidates = {}
    for step in budget['candidate_steps']:
        metrics = {mode: {'nll_bits': 10-step/10, 'n_query': 20, 'top1': .2} for mode in ('native', 'unified')}
        candidates[str(step)] = {'optimizer_steps': step, 'evaluation': {'fit_ids': ['source'], 'calibration_ids': ['source'],
            'evaluation_ids': ['p'], 'per_participant': {'p': {'status': 'complete', 'group': 'hi', 'metrics': metrics,
                'query_hash': 'a'*64, 'candidate_hash': 'b'*64}}}}
    record = {'id': unit['id'], 'unit': unit, 'budget': budget, 'candidates': candidates,
              'ledger': {'encoder_updates': 20, 'initial_model_head_sha256': 'c'*64}}
    return record


def test_matched_parser_uses_U_and_records_audio_only_population_access():
    record = trajectory_fixture()
    export = S.Export({'dtu': {'p': {'group': 'hi', 'outer_fold': 0}}}, {})
    S.process_matched(export, record, S.REPO/'private/SYNTHETIC_MATCHED.json', 'd'*64)
    rows = export.panels['matched_U__dtu__local__native']['rows']
    nll = next(r for r in rows if r['metric'] == 'nll_bits')
    assert nll['value'] == 8
    assert nll['provenance']['population_fit_identities'] == ['audio_only', 'source']
    assert nll['metadata']['actual_U'] == 20
    record['candidates']['20']['optimizer_steps'] = 10
    with pytest.raises(S.BindingError, match='counter'):
        S.process_matched(export, record, S.REPO/'private/SYNTHETIC_MATCHED.json', 'd'*64)


def policy_fixture():
    trajectory = trajectory_fixture()
    policy = {'status': 'complete', 'matched_plan_sha256': 'd'*64, 'selection_code_sha256': 'e'*64,
              'inner_record_sha256': 'f'*64, 'outer_data_access_for_selection': False, 'lineage': 'source_execution',
              'fraction': .5, 'policy': {mode: {'status': 'complete', 'true_risk_candidate_index': 0, 'gain_candidate_index': 3,
                  'true_risk_selected_epoch0': True, 'gain_selected_epoch0': False, 'complete_inner_ids': ['inner']}
                                       for mode in ('native', 'unified')}}
    policy['id'] = 'ALN35SEL_' + S.digest({'lineage': policy['lineage'], 'fraction': .5, 'inner_sha256': 'f'*64,
                                         'code_sha256': 'e'*64, 'matched_plan_sha256': 'd'*64})[:16]
    record = copy.deepcopy(policy); record.update(outer_record_sha256='a'*64, outer={})
    for mode in ('native', 'unified'):
        person = {'status': 'complete', 'group': 'hi', 'query_hash': 'a'*64, 'candidate_hash': 'b'*64,
                  'true_risk_policy': copy.deepcopy(trajectory['candidates']['0']['evaluation']['per_participant']['p']['metrics'][mode]),
                  'gain_policy': copy.deepcopy(trajectory['candidates']['20']['evaluation']['per_participant']['p']['metrics'][mode])}
        record['outer'][mode] = {'status': 'complete', 'true_risk_outer_step': 0, 'gain_outer_step': 20,
                                 'per_participant': {'p': person}}
    return trajectory, policy, record


def test_policy_binding_keeps_epoch0_and_rejects_outer_selection_or_reapplied_metrics():
    trajectory, policy, record = policy_fixture()
    inner_trajectory = copy.deepcopy(trajectory)
    inner_trajectory['unit']['stage'] = 'inner'
    inner_trajectory['unit']['split']['evaluation_ids'] = ['inner']
    inner = {'record': inner_trajectory, 'sha': 'f'*64}; outer = {'record': trajectory, 'sha': 'a'*64}
    S.validate_policy(record, policy, inner, outer, 'd'*64, 'e'*64)
    export = S.Export({'dtu': {'p': {'group': 'hi', 'outer_fold': 0}}}, {})
    S.process_policy(export, record, trajectory, S.REPO/'private/SYNTHETIC_POLICY.json', 'c'*64)
    rows = export.panels['true_risk_selection__dtu__local__native__EEG50']['rows']
    true_nll = next(r for r in rows if r['arm'].endswith('/true_risk_policy') and r['metric'] == 'nll_bits')
    assert true_nll['value'] == 10 and true_nll['metadata']['true_risk_selected_epoch0']
    record['outer']['native']['per_participant']['p']['true_risk_policy']['nll_bits'] = 1
    with pytest.raises(S.BindingError, match='metrics differ'):
        S.process_policy(export, record, trajectory, S.REPO/'private/SYNTHETIC_POLICY.json', 'c'*64)
    record['outer_data_access_for_selection'] = True
    with pytest.raises(S.BindingError, match='inner-only'):
        S.validate_policy(record, policy, inner, outer, 'd'*64, 'e'*64)
