"""Synthetic S4 provenance/status contracts; execute only inside Slurm gates."""
import copy
import csv
import json
from pathlib import Path

import pytest
import yaml

from auditory5.screening import (METRIC_COLUMNS, Source, _ci, control_evidence, evaluate_route,
    extract_metrics, read_source, representation_status, required_controls, run, scientific_screen,
    validate_registry, resolve_display_metrics)
from auditory5.provenance import ROOT, digest


def interval(value=-.02, n=40):
    return dict(estimate=value, ci_lower=value - .01, ci_upper=value + .01,
                n_candidates=n, n_bootstrap=2000)


def test_nonfinite_and_reversed_intervals_fail_instead_of_negative():
    for value in (float('nan'), float('inf'), '-inf', True):
        with pytest.raises(ValueError):
            _ci(dict(interval(), estimate=value))
    with pytest.raises(ValueError, match='REVERSED_INTERVAL'):
        _ci(dict(interval(), ci_lower=1, ci_upper=-1))
    with pytest.raises(ValueError, match='UNFROZEN_BOOTSTRAP'):
        _ci(dict(interval(), n_bootstrap=999))


def test_primary_does_not_fall_back_to_positive_supervised():
    core = Source('B', 'core', 'supervised', ('R_SUP',), state='READY', summary={})
    metrics = [dict(route='B', mode='R_SUP', statistic='calibrated_main_gain', run='supervised',
                    **interval(.2), units='bits/trial')]
    result = evaluate_route('B', [core], metrics)
    assert result['verdict'] == 'NEED_CONTROLS'
    assert result['estimate'] is None
    assert 'R_SIM:primary_estimate' in result['pending']


def test_negative_core_does_not_hide_missing_controls_or_numerical_failure():
    comparison = dict(interval(), analysis_set='all', probability_mode='calibrated', comparison='main_gain', positive_candidate_fraction=.2)
    core = Source('B', 'core', 'sim_core', ('R_SIM',), state='READY',
                  summary={'representations': {'R_SIM': {'comparisons': [comparison]}}})
    missing = Source('B', 'controls', 'sim_controls', ('R_SIM',))
    metrics = extract_metrics(core)
    assert evaluate_route('B', [core, missing], metrics)['verdict'] == 'NEED_CONTROLS'
    missing.state = 'FAIL'
    assert evaluate_route('B', [core, missing], metrics)['verdict'] == 'IMPLEMENTATION_FAIL'


def test_e_incomplete_mlp_never_aggregates_success_subset_and_preserves_linear():
    source = Source('E', 'core', 'E0', ('E0_native',), state='FAIL', summary={
        'status': 'E0_PARTIAL_NUMERICAL_FAILURE', 'family_status': {'linear': 'COMPLETE', 'MLP32': 'NUMERICAL_FAILURE'},
        'results': [dict(family='linear', calibration='calibrated', task='bapa', J_bits_interval=interval(-.01, 7))]})
    metrics = extract_metrics(source)
    assert len(metrics) == 1 and metrics[0]['estimate'] == -.01
    verdict = evaluate_route('E', [source], metrics)
    assert verdict['verdict'] == 'IMPLEMENTATION_FAIL'
    assert verdict['support_status'] == 'SUPPORT_INSUFFICIENT_FOR_E1'
    source.summary['results'].append(dict(family='MLP32', calibration='calibrated', task='bapa', J_bits_interval=interval(.2)))
    with pytest.raises(ValueError, match='INCOMPLETE_E_FAMILY_AGGREGATED'):
        extract_metrics(source)


def test_a_partial_control_keeps_valid_reset_and_correct_paired_difference():
    source = Source('A', 'controls', 'A_controls', ('R_SIM',), state='READY', summary={
        'version': 'auditory5_A_controls_v1', 'status': 'NEED_CONTROLS', 'aggregates': {
            'R_SIM:reset_unbalanced': dict(status='PASS', complete_folds=5, total_candidates=40,
                                          estimate=.04, ci95=[.01, .07]),
            'R_SIM:continuous_balanced': {'status': 'NEED_CONTROLS'},
            'R_SIM:reset_minus_continuous_same_reset_trials': dict(status='PASS', total_candidates=40,
                estimate=.08, ci95=[.06, .10], paired_direction='left_minus_right', paired_estimate=-.03, paired_ci95=[-.05, -.01])}})
    evidence = control_evidence([source])
    assert evidence[0]['estimate'] == .04
    assert evidence[1]['estimate'] == -.03
    pending, failures = required_controls(source)
    assert not failures and 'R_SIM:continuous_balanced' in pending


def test_linear_only_c_never_invents_mlp_or_replaces_full_family():
    descriptive = Source('C', 'descriptive', 'linear_only', ('R_SIM',), state='READY', summary={'status': 'NEED_CONTROLS'},
        files={'single_joint_gains.csv': [dict(interval(.03), representation='R_SIM', family='linear', probability_mode='calibrated', statistic='T_C')]})
    full = Source('C', 'core', 'full_family', ('R_SIM',), state='FAIL')
    metrics = extract_metrics(descriptive)
    assert [m['statistic'] for m in metrics] == ['T_C_linear_calibrated']
    result = evaluate_route('C', [descriptive, full], metrics)
    assert result['verdict'] == 'IMPLEMENTATION_FAIL' and result['estimate'] is None


def test_d_fp32_status_pass_cannot_hide_numeric_violation():
    numeric = dict(mode='R_SIM', status='PASS', dtype='float32', threshold=1e-6,
        real_max_abs_probability_difference=1e-3, synthetic_max_abs_probability_difference=0.,
        projector_difference_float64=0., null_projector_difference_float64=0.)
    source = Source('D', 'controls', 'D_controls', ('R_SIM',), state='READY', summary={},
                    files={'fp32_invariance.json': [numeric]})
    missing, failures = required_controls(source)
    assert 'R_SIM:FP32_invariance_numeric_failure' in failures
    assert 'R_SIM:null_linear_probe_aggregate' in missing


def test_explicit_source_does_not_discover_an_unrequested_better_run(tmp_path):
    wanted = tmp_path / 'wanted'
    unwanted = tmp_path / 'better_999'
    wanted.mkdir(); unwanted.mkdir()
    (wanted / 'summary.json').write_text('{"status":"INTERIM"}')
    (unwanted / 'summary.json').write_text('{"status":"PASS","secret":"do not read"}')
    audit = []
    source = read_source(dict(route='B', kind='core', run='wanted', modes=['L0']), tmp_path, audit)
    assert source.state == 'READY'
    assert all('better_999' not in row.get('path', '') for row in audit)
    assert any(row.get('sha256') == digest(wanted / 'summary.json') for row in audit)


def test_nan_json_is_explicit_failure(tmp_path):
    folder = tmp_path / 'bad'; folder.mkdir()
    (folder / 'summary.json').write_text('{"status":"INTERIM","estimate":NaN}')
    source = read_source(dict(route='A', kind='core', run='bad', modes=['R_SIM']), tmp_path, [])
    assert source.state == 'FAIL'


def test_s3_requires_every_exact_receipt_and_matching_task(tmp_path):
    plan_path = tmp_path / 'plan.json'
    tasks = [dict(name=f'task{i}', mode='L0', branch='all', stage='outer', outer_fold=i, inner_fold=None,
                  fit_groups=['private_synthetic_candidate']) for i in range(90)]
    plan = {'tasks': tasks}
    plan_path.write_text(json.dumps(plan))
    plan_hash = digest(plan_path)
    for task in tasks:
        folder = tmp_path / 'outputs' / task['name']; folder.mkdir(parents=True)
        (folder / 'task.json').write_text(json.dumps(dict(task, plan_hash=plan_hash)))
        (folder / 'completion.json').write_text(json.dumps(dict(task, task=task['name'], status='PASS', plan_hash=plan_hash,
            encoder_fit_scope_hash='scopehash')))
    result = representation_status(plan, plan_hash, plan_path, [])
    assert result['status'] == 'S3_COMPLETE' and result['completed'] == 90
    (tmp_path / 'outputs/task89/completion.json').unlink()
    assert representation_status(plan, plan_hash, plan_path, [])['status'] == 'IN_PROGRESS'
    (tmp_path / 'outputs/task0/task.json').unlink()
    assert representation_status(plan, plan_hash, plan_path, [])['status'] == 'IMPLEMENTATION_FAIL'


def test_registry_freezes_mode_priority_and_explicit_repaired_run():
    registry = yaml.safe_load((ROOT / 'configs/auditory5_screening_sources_v1.yaml').read_text())
    validate_registry(registry)
    assert any(s['run'] == 'C_linear_L0_SUP_RAND_002' for s in registry['sources'])
    altered = copy.deepcopy(registry); altered['primary_mode'] = 'R_SUP'
    with pytest.raises(ValueError, match='PRIORITY'):
        validate_registry(altered)
    altered = copy.deepcopy(registry); altered['sources'].append(altered['sources'][0])
    with pytest.raises(ValueError, match='DUPLICATE'):
        validate_registry(altered)


def test_missing_inputs_produce_five_honest_rows_and_no_private_identifiers(tmp_path, monkeypatch):
    repository = ROOT
    registry = yaml.safe_load((repository / 'configs/auditory5_screening_sources_v1.yaml').read_text())
    config = yaml.safe_load((repository / 'configs/auditory5_v1.yaml').read_text())
    (tmp_path / 'configs').mkdir()
    (tmp_path / registry['project_config']).write_text(yaml.safe_dump(config))
    (tmp_path / registry['protocol']).write_text('Synthetic frozen protocol')
    source_path = tmp_path / 'sources.yaml'; source_path.write_text(yaml.safe_dump(registry))
    monkeypatch.setenv('SLURM_JOB_ID', 'synthetic_test')
    result = run('screen_missing', source_path, root=tmp_path)
    assert result['status'] == 'IN_PROGRESS'
    assert result['S3']['status'] != 'S3_COMPLETE'
    assert result['all_five_scientific_routes_complete'] is False
    public = tmp_path / config['paths']['aggregates_relative'] / 'screen_missing'
    with (public / 'verdict.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    assert [r['route'] for r in rows] == list('ABCDE')
    assert all(r['verdict'] == 'NEED_CONTROLS' for r in rows)
    with (public / 'screen_metrics.csv').open() as stream:
        assert next(csv.reader(stream)) == list(METRIC_COLUMNS)
        assert list(csv.reader(stream)) == []
    public_text = '\n'.join(p.read_text() for p in public.iterdir())
    assert str(tmp_path) not in public_text
    assert 'private_synthetic_candidate' not in public_text
    report = tmp_path / config['paths']['reports_relative'] / 'screen_missing/FIVE_IDEAS_SCREENING_REPORT.md'
    assert '固定 OOF' in report.read_text()
    with pytest.raises(FileExistsError, match='ALREADY_EXISTS'):
        run('screen_missing', source_path, root=tmp_path)


def test_frozen_d_primary_not_replaced_by_better_qc_sensitivity():
    effect = interval(-.5, 51)
    core = Source('D', 'core', 'original', ('R_SIM',), summary={})
    control = Source('D', 'controls', 'sensitivity', ('R_SIM',), summary={'estimate': 1.2})
    assert scientific_screen('D', core, [control], effect) == 'NEGATIVE_SCREEN'


def test_c_duplicate_display_prefers_full_only_when_effects_and_cohort_agree():
    sources = [Source('C', 'core', 'full', ('R_SIM',)), Source('C', 'descriptive', 'linear', ('R_SIM',))]
    metrics = [dict(route='C', mode='R_SIM', statistic='T_C_linear_calibrated', units='bits/trial', run=name,
                    **interval(.01)) for name in ('linear', 'full')]
    rows, conflicts = resolve_display_metrics(metrics, sources)
    assert len(rows) == 1 and rows[0]['run'] == 'full' and not conflicts
    metrics[0]['estimate'] = .1
    rows, conflicts = resolve_display_metrics(metrics, sources)
    assert rows == [] and set(conflicts) == {'linear', 'full'}


def test_b_complete_controls_apply_fixed_threshold_without_replacing_primary():
    comparisons = []
    for probability in ('raw', 'calibrated'):
        for subset, names in (('all', ('main_gain', 'post_increment_over_pre')),
                              ('previous_response_available', ('main_gain', 'post_increment_over_pre', 'post_increment_over_previous'))):
            for name in names:
                comparisons.append(dict(interval(.03), analysis_set=subset, probability_mode=probability,
                                        comparison=name, positive_candidate_fraction=.75))
    core = Source('B', 'core', 'B_SIM', ('R_SIM',), state='READY', summary={
        'representations': {'R_SIM': {'completed_analysis_folds': 10, 'comparisons': comparisons}}})
    controls = Source('B', 'controls', 'B_SIM_controls', ('R_SIM',), state='READY', summary={
        'modes': {'R_SIM': {'completed_fold_diagnostics': {name: 5 for name in ('early', 'late', 'quality', 'circular_shift')},
            'comparisons': [dict(interval(.02), analysis_set=name, probability_mode='calibrated', comparison='main_gain')
                            for name in ('early', 'late', 'quality')], 'circular_shift': [{'estimate': .01}],
            'context_balance': [{'H': 0}, {'H': 1}]}}})
    result = evaluate_route('B', [core, controls], extract_metrics(core))
    assert result['verdict'] == 'POSITIVE_SCREEN'
    assert result['scientific_complete'] is True
    for row in comparisons:
        if row['comparison'] == 'main_gain':
            row['positive_candidate_fraction'] = .59
    assert evaluate_route('B', [core, controls], extract_metrics(core))['verdict'] == 'NEGATIVE_SCREEN'


def test_protocol_table_does_not_promote_linear_c_or_e0_or_parallel_model():
    from auditory5.screening import protocol_metric_rows, AGGREGATE_COLUMNS
    inputs = [('C', 'R_SIM', 'T_C_linear_calibrated'), ('C', 'R_SIM', 'T_C_mlp32_calibrated'),
              ('D', 'R_SUP', 'D2_minus_D3'), ('D', 'R_SIM', 'D2_minus_D3'),
              ('E', 'E0_native', 'linear_calibrated_J_bapa')]
    metrics = [dict(route=r, mode=m, statistic=s, run='source', units='source_units', **interval(.02))
               for r, m, s in inputs]
    verdicts = [dict(route=r, primary_run='source', control_status='PENDING', verdict='NEED_CONTROLS')
                for r in ('C', 'D', 'E')]
    rows = protocol_metric_rows(metrics, verdicts)
    assert [r['primary_endpoint'] for r in rows] == [False, True, False, True, False]
    assert all(set(r) == set(AGGREGATE_COLUMNS) for r in rows)
    assert all(r['n_trials'] is None and r['n_records'] is None for r in rows)
    assert rows[-1]['split_protocol'] == 'within_record_independent_filter_blocks'
