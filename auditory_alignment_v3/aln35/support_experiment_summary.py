"""CPU-only, versioned ALN3.5 support/episode/matched/selection evidence.

Consumes immutable plans and completed JSON; never imports a training module,
selects a policy, loads EEG/checkpoints, submits work, or overwrites old output.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / 'private/auditory_alignment_v3/aln35'
BASE = ROOT / 'support_summary_v1'
PUBLIC = REPO / 'results/auditory_alignment_v3/aln35/support_summary_v1'
PACKAGE = REPO / 'AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018'
sys.path.insert(0, str(PACKAGE / 'src'))
from aln35_reference import contrasts as REF  # noqa: E402

PLAN_HASHES = {
    'support_coverage_v1': 'bd267091dab911448c6981455504f2b17f5ae782711a71ed687028a1ec832b65',
    'episode_pressure_v1': 'ae2188c200d61a0616d07ad60edb53b8fb8d96df6df5454e3665d52f2919b171',
    'episode_lineage_v2': 'aa648030ccf89a27e4a52d23862fc5454e3c20da170aa88bcee0e37f1251c359',
    'matched_updates_v1': 'b2442196bf98a2a321d8406ea2f829611bb10c6876cfff16849a8fb9ff46014e',
}
DRAW_NAMES = tuple(f'U10_{s}' for s in range(351410, 351415))
METHODS = ('zero_step', 'probability_only', 'rank4_fixed20')
MEASURES = {
    'nll_bits': ('bits/query', -1),
    'wrong_nll_bits': ('bits/query', -1),
    'mismatch_gain_bits': ('bits/query', 1),
    'auc': ('AUC', 1), 'brier': ('squared probability', -1),
    'top1': ('fraction', 1), 'rank_pct': ('fraction', -1),
}
DIAGNOSTIC_METRICS = ('probability_tv', 'entropy_bits', 'representation_relative_change', 'temperature')
CONTRACT_NOTE = REPO / 'docs/auditory_alignment_v3/aln35/SUPPORT_EXPERIMENT_SUMMARY_DESIGN.md'
ANALYSIS_VERSION = 'S35_SUPPORT_SUMMARY_v1.1_endpoint_units_and_diagnostics'


class BindingError(ValueError):
    """A completed record cannot be used as its registered paired condition."""


def require(condition, message):
    if not condition:
        raise BindingError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    # Parse the exact bytes whose hash we record. Unit writers use atomic replace.
    raw = Path(path).read_bytes()
    return REF.parse_json(raw.decode()), hashlib.sha256(raw).hexdigest()


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def metric_unit(dataset, metric):
    unit = MEASURES.get(metric, ('diagnostic', 0))[0]
    return 'bits/trial' if dataset == 'private_bdf' and unit == 'bits/query' else unit


def mean(values):
    return math.fsum(values) / len(values) if values else None


def stat(values):
    valid = [float(v) for v in values if finite(v)]
    return {'n': len(valid), 'missing': len(values)-len(valid), 'mean': mean(valid),
            'min': min(valid) if valid else None, 'max': max(valid) if valid else None,
            'last': valid[-1] if valid else None}


def configuration(source):
    if source['architecture'] == 'lag_local_tokens':
        return 'local'
    adaptation = source.get('adaptation', source['outer']['row']['spec'].get('adaptation'))
    require(source['architecture'] == 'cbramod', 'unregistered architecture')
    require(adaptation in ('pretrained_full', 'random_full'), 'unregistered CB initialization')
    return 'CBpre' if adaptation == 'pretrained_full' else 'CBrand'


def identity_roster(geometry):
    rosters = {'dtu': {}, 'private_bdf': {}}
    for identity, row in geometry['private'].items():
        rosters['private_bdf'][identity] = {'group': row['group'], 'outer_fold': row['fold']}
    for key, row in geometry['dtu'].items():
        cf, role, identity = key.split('/', 2)
        if role != 'test':
            continue
        item = {'group': row['group'], 'outer_fold': row['fold']}
        require(rosters['dtu'].get(identity, item) == item, 'DTU roster changes across content folds')
        require(f'{1-int(cf)}/test/{identity}' in geometry['dtu'], 'DTU roster missing registered content fold')
        rosters['dtu'][identity] = item
    require(len(rosters['dtu']) == 44 and len(rosters['private_bdf']) == 64, 'frozen expected roster changed')
    return rosters


def episode_units(original, successor):
    """Return exactly the original scientific cells with two versioned bindings."""
    old = {u['id']: u for u in original['rows']}
    new = {u['id']: u for u in successor['rows']}
    mapping = successor['supersedes_dependency_only']
    require(len(mapping) == 2 and len(set(mapping.values())) == 2, 'expected two unique lineage replacements')
    require(set(mapping) <= old.keys() and set(mapping.values()) == new.keys(), 'lineage replacement IDs do not bind')
    result = []
    for identity, unit in old.items():
        if identity in mapping:
            replacement = new[mapping[identity]]
            require(replacement['parent_aln35_id'] == identity, 'lineage parent mismatch')
            require({k: v for k, v in replacement['source'].items() if k != 'legacy_inner'} == unit['source'],
                    'lineage changed source beyond the explicit legacy dependency')
            require('legacy_inner' in replacement['source'], 'lineage successor lacks actual legacy dependency')
            for field in ('support_steps', 'encoder_updates', 'outer_fold', 'content_fold', 'target_steps'):
                require(replacement[field] == unit[field], f'lineage changed scientific field {field}')
            result.append(('episode_lineage_v2', replacement, identity))
        else:
            result.append(('episode_pressure_v1', unit, identity))
    require(len(result) == 60, 'episode should contain 60 scientific cells, not 62')
    return result


def valid_record(record, unit, plan_hash):
    require(record.get('status') == 'complete', 'record status is not complete')
    require(record.get('probe') is False, 'engineering probe is never a production outcome')
    require(record.get('id') == unit['id'], 'record ID differs from registered ID')
    require(record.get('plan_sha256') == plan_hash, 'record plan hash differs from frozen plan')
    require(record.get('unit') == unit, 'record unit differs from registered configuration')
    if 'registered_unit' in record:
        require(record['registered_unit'] == unit, 'registered matched unit differs')


def population_provenance(source, outer_fold, record_path, record_sha, selection_ids=()):
    return {'population_fit_identities': sorted(set(source['fit_ids']) | set(source['calibration_ids'])),
            'selection_identities': sorted(set(selection_ids)), 'outer_fold': str(outer_fold),
            'source_record': str(record_path.relative_to(REPO)), 'source_sha256': record_sha,
            'source_seed_ids': [3401]}


def same_query(entries, dataset):
    """Hash and count checks are paired-cell requirements, never performance filters."""
    require(bool(entries), 'no query entries')
    q = {e['query_hash'] for e in entries}
    n = {e['metrics'].get('n_query') for e in entries}
    require(len(q) == 1 and all(isinstance(x, str) and len(x) == 64 for x in q), 'different query hashes')
    require(len(n) == 1 and next(iter(n)) is not None, 'different or missing query counts')
    if dataset == 'dtu':
        candidates = {e['candidate_hash'] for e in entries}
        require(len(candidates) == 1 and all(isinstance(x, str) and len(x) == 64 for x in candidates),
                'different candidate-audio hashes')
    else:
        candidates = {'fixed_private_binary_labels_0_1'}
    return next(iter(q)), next(iter(candidates))


def average_draws(entries, dataset, expected):
    """An incomplete U10 set is missing, never an average over available draws."""
    require(set(entries) <= set(expected), 'unexpected support sampling draw')
    if set(entries) != set(expected):
        return None
    selected = [entries[k] for k in expected]
    query_hash, candidate_hash = same_query(selected, dataset)
    keys = set.intersection(*(set(e['metrics']) for e in selected))
    metrics = {key: mean([float(e['metrics'][key]) for e in selected])
               for key in keys if all(finite(e['metrics'][key]) for e in selected)}
    return {'metrics': metrics, 'query_hash': query_hash, 'candidate_hash': candidate_hash,
            'draws': list(expected), 'support_hashes': [e.get('support_hash') for e in selected]}


def support_entry(container, method, mode, dataset, *, episode_step=None):
    metrics = (container['methods'][method]['metrics'][mode] if episode_step is None else
               container['candidates'][str(episode_step)]['metrics'][mode])
    support = container['support']
    return {'metrics': metrics, 'query_hash': support['query_hash'], 'support_hash': support['support_hash'],
            'candidate_hash': metrics.get('candidate_hash') if dataset == 'dtu' else None}


def support_average(containers, policy, method, mode, dataset, *, episode_step=None):
    names = DRAW_NAMES if policy == 'U10' else (policy,)
    entries = {name: support_entry(containers[name], method, mode, dataset, episode_step=episode_step)
               for name in names if name in containers}
    return average_draws(entries, dataset, names)


def validate_geometry(cell, identity, unit, geometry):
    dataset = unit['source']['dataset']
    key = identity if dataset == 'private_bdf' else f'{unit["content_fold"]}/test/{identity}'
    original = geometry['private' if dataset == 'private_bdf' else 'dtu'][key]
    require(cell['query_hash'] == original['query_hash'], 'result query differs from frozen safe geometry')
    require(cell['metrics']['n_query'] == original['n_query'], 'query count differs from frozen geometry')
    return original


def contrasts_for(kind, dataset):
    """All terms are fixed here, before opening the production unit directory."""
    if kind == 'support':
        policies = ['U10', 'U30', 'C10'] + (['H10'] if dataset == 'private_bdf' else [])
        comparisons = [(f'{p}-{METHODS[0]}', f'{p}-{METHODS[2]}', f'rank4_vs_zero__{p}') for p in policies]
        comparisons += [(f'{p}-{METHODS[1]}', f'{p}-{METHODS[2]}', f'rank4_vs_probability__{p}') for p in policies]
        comparisons += [(f'U10-{method}', f'{p}-{method}', f'{p}_vs_U10__{method}')
                        for method in METHODS for p in policies[1:]]
        return comparisons
    if kind == 'episode_fixed20':
        return [(f'{p}-{reference}', f'{p}-{candidate}', f'{candidate}_vs_{reference}__{p}')
                for p in ('U10', 'U30') for reference, candidate in
                (('ordinary', 'episode'), ('source', 'episode'), ('source', 'ordinary'))]
    if kind == 'episode_selected':
        return [(f'{p}-ordinary', f'{p}-episode', f'selected_episode_vs_selected_ordinary__{p}') for p in ('U10', 'U30')]
    if kind == 'matched_U':
        return [('fraction_100', 'fraction_50', 'EEG50_vs_EEG100_at_fixed_U')]
    if kind == 'true_risk_selection':
        return [('gain_policy', 'true_risk_policy', 'true_risk_vs_inherited_gain')]
    raise BindingError(f'unknown panel {kind}')


class Export:
    def __init__(self, rosters, geometry):
        self.rosters, self.geometry = rosters, geometry
        self.panels = {}
        self.inputs = []
        self.errors = []
        self.diagnostics = {'support_coverage': [], 'episode_source': [], 'episode_policies': [],
                            'matched_trajectories': [], 'true_risk_policies': [], 'unavailable_people': []}

    def panel(self, kind, dataset, config, mode, *, pressure=None, fraction=None):
        fields = [kind, dataset, config, mode]
        if pressure is not None:
            fields.append(f'pressure{pressure}')
        if fraction is not None:
            fields.append(f'EEG{int(100*fraction)}')
        key = '__'.join(fields)
        if key not in self.panels:
            self.panels[key] = {'panel_id': key, 'kind': kind, 'dataset': dataset, 'configuration': config,
                                'readout': mode, 'source_support_steps': pressure, 'EEG_fraction': fraction,
                                'comparisons': contrasts_for(kind, dataset), 'rows': [], 'expected_units': [],
                                'available_units': []}
        return self.panels[key]

    def add(self, panel, identity, group, unit, arm, cell, provenance, extra=None):
        if cell is None:
            return
        roster = self.rosters[panel['dataset']]
        require(identity in roster and roster[identity]['group'] == group, 'person/group outside frozen roster')
        require(str(roster[identity]['outer_fold']) == provenance['outer_fold'], 'person outer-fold membership differs')
        metadata = {'draws': cell.get('draws', []), 'candidate_hash': cell['candidate_hash'],
                    'support_hashes': cell.get('support_hashes', []), **(extra or {})}
        # Candidate sets and row counts are part of the paired evaluation contract.
        query_id = digest({'query': cell['query_hash'], 'candidate': cell['candidate_hash'],
                           'n_query': cell['metrics']['n_query']})
        for metric in (*MEASURES, *DIAGNOSTIC_METRICS):
            value = cell['metrics'].get(metric)
            if not finite(value):
                continue
            row = {'dataset': panel['dataset'], 'identity': identity, 'group': group, 'stratum': group,
                   'fold': f'content_{unit["content_fold"]}' if panel['dataset'] == 'dtu' else 'evaluation',
                   'seed': 3401, 'arm': f'{panel["panel_id"]}/{arm}', 'window': 'registered_full_input',
                   'metric': metric, 'unit': metric_unit(panel['dataset'], metric), 'value': float(value),
                   'query_set_id': query_id, 'analysis_role': 'outer_test',
                   'provenance': {**provenance, 'aggregation_note':
                       'All five predeclared U10 support draws averaged within person and content cell; other support rules single. '
                       'Training seed remains 3401. Explicit support/query sample IDs are not exported; hashes and frozen geometry '
                       'bind the production checks, not a proof of raw-preprocessing isolation.'}, 'metadata': metadata}
            panel['rows'].append(row)

    def record_error(self, location, error):
        self.errors.append({'location': str(location), 'type': type(error).__name__, 'reason': str(error)})


def panel_membership(export, kind, unit, key, available=False):
    source = unit.get('source', unit.get('binding', {}).get('source'))
    dataset = source.get('dataset', 'dtu')
    modes = ('native', 'unified') if dataset == 'dtu' else ('native', 'linear')
    result = []
    for mode in modes:
        panel = export.panel(kind, dataset, configuration(source), mode,
                             pressure=unit.get('support_steps') if kind.startswith('episode') else None,
                             fraction=unit.get('fraction') if kind == 'true_risk_selection' else None)
        panel['expected_units'].append(key)
        if available:
            panel['available_units'].append(key)
        result.append(panel)
    return result


def process_support(export, record, path, record_sha):
    unit = record['unit']; dataset = unit['source']['dataset']
    provenance = population_provenance(record['source_provenance'], unit['outer_fold'], path, record_sha)
    panels = [export.panel('support', dataset, configuration(unit['source']), mode)
              for mode in unit['readouts']]
    for identity, person in record['per_participant'].items():
        if person['status'] != 'complete':
            export.diagnostics['unavailable_people'].append({'unit': unit['id'], 'identity': identity, 'status': person['status']})
            continue
        containers = person['conditions']
        for name, condition in containers.items():
            coverage = condition['support']
            export.diagnostics['support_coverage'].append({'unit': unit['id'], 'dataset': dataset,
                'configuration': configuration(unit['source']), 'identity': identity, 'group': person['group'],
                'content_fold': unit['content_fold'], 'draw_or_policy': name, 'support': coverage,
                'methods': {method: {'access_budget': value['access_budget'],
                    'adaptation': {k: v for k, v in value['adaptation'].items() if k != 'gradient_norms'},
                    'gradient_norm_summary': stat(value['adaptation'].get('gradient_norms', []))}
                    for method, value in condition['methods'].items()}})
        policies = ('U10', 'U30', 'C10', 'H10') if dataset == 'private_bdf' else ('U10', 'U30', 'C10')
        for panel in panels:
            for policy in policies:
                for method in METHODS:
                    cell = support_average(containers, policy, method, panel['readout'], dataset)
                    if cell is not None:
                        validate_geometry(cell, identity, unit, export.geometry)
                    export.add(panel, identity, person['group'], unit, f'{policy}-{method}', cell, provenance)


def episode_person_cell(values, identity, policy, regime, steps, mode, dataset):
    person = values[regime]['per_participant'].get(identity)
    if not person or person['status'] != 'complete':
        return None
    return support_average(person['supports'], policy, '', mode, dataset, episode_step=steps)


def process_episode(export, record, path, record_sha):
    unit = record['unit']; source = unit['source']; dataset = source['dataset']
    config = configuration(source); pressure = unit['support_steps']
    outer = record['stages']['outer']; values = outer['values']
    provenance = population_provenance(outer['source_provenance'], unit['outer_fold'], path, record_sha)
    people = sorted(set().union(*(v['per_participant'] for v in values.values())))
    for stage, data in record['stages'].items():
        ledgers = data['training']
        require(ledgers['ordinary']['stream_sha256'] == ledgers['episode']['stream_sha256'], 'episode sampling streams differ')
        for field in ('encoder_updates', 'support_optimizer_steps', 'query_exposures', 'support_exposures'):
            require(ledgers['ordinary'][field] == ledgers['episode'][field], f'episode matched {field} differs')
        require(ledgers['episode']['encoder_updates'] == 100, 'production episode did not complete 100 updates')
        for regime, ledger in ledgers.items():
            stats = ledger['diagnostics']; keys = sorted(set().union(*(d.keys() for d in stats))) if stats else []
            numeric = {k: stat([d.get(k) for d in stats]) for k in keys
                       if any(finite(d.get(k)) for d in stats) or k in ('encoder_direction_cosine_at_same_state', 'support_gradient_last')}
            export.diagnostics['episode_source'].append({'unit': unit['id'], 'dataset': dataset, 'configuration': config,
                'pressure': pressure, 'stage': stage, 'regime': regime,
                'ledger': {k: v for k, v in ledger.items() if k not in ('diagnostics', 'sampling_stream', 'losses')},
                'source_only_diagnostics': numeric, 'source_only_loss': stat(ledger['losses']),
                'paired_final_update_direction_cosine': data['paired_final_update_direction_cosine']})
    for mode in ('native', 'unified') if dataset == 'dtu' else ('native', 'linear'):
        fixed = export.panel('episode_fixed20', dataset, config, mode, pressure=pressure)
        selected = export.panel('episode_selected', dataset, config, mode, pressure=pressure)
        for policy in ('U10', 'U30'):
            for regime in ('ordinary', 'episode'):
                choice = record['choices'][mode][policy][regime]
                export.diagnostics['episode_policies'].append({'unit': unit['id'], 'dataset': dataset, 'configuration': config,
                    'source_support_steps': pressure, 'readout': mode, 'support': policy, 'regime': regime, **choice})
            for identity in people:
                group = export.rosters[dataset][identity]['group']
                for regime in ('source', 'ordinary', 'episode'):
                    cell = episode_person_cell(values, identity, policy, regime, 20, mode, dataset)
                    if cell is not None:
                        validate_geometry(cell, identity, unit, export.geometry)
                    export.add(fixed, identity, group, unit, f'{policy}-{regime}', cell, provenance)
                for regime in ('ordinary', 'episode'):
                    choice = record['choices'][mode][policy][regime]
                    if choice['status'] != 'complete':
                        continue
                    location = choice['outer_result_location']
                    cell = episode_person_cell(values, identity, policy, location['regime'], location['target_steps'], mode, dataset)
                    if cell is not None:
                        validate_geometry(cell, identity, unit, export.geometry)
                        saved = choice['outer_per_identity_nll'].get(identity)
                        require(saved is not None and math.isclose(cell['metrics']['nll_bits'], saved, abs_tol=1e-12),
                                'episode applied policy differs from saved policy outcome')
                    chosen_prov = {**provenance, 'selection_identities': choice['inner_complete_ids']}
                    export.add(selected, identity, group, unit, f'{policy}-{regime}', cell, chosen_prov,
                               {'chosen': choice['chosen'], 'zero_step_selected': choice['zero_step_selected'],
                                'source_fallback_selected': choice['source_fallback_selected']})


def validate_matched_pair(first, second):
    a, b = first['unit'], second['unit']
    require({a['fraction'], b['fraction']} == {.5, 1.}, 'matched pair must be EEG50/100')
    require(a['stage'] == b['stage'] and a['source_lineage'] == b['source_lineage'], 'matched source/stage differs')
    require(first['budget'] == second['budget'] == a['budget'] == b['budget'], 'same-U long-cosine budget differs')
    require(first['ledger']['initial_model_head_sha256'] == second['ledger']['initial_model_head_sha256'],
            'matched source model/head initialization differs')
    require(a['split']['full_source_audio_ids'] == b['split']['full_source_audio_ids'], 'matched audio access differs')
    require(a['split']['evaluation_ids'] == b['split']['evaluation_ids'], 'matched evaluation people differ')
    require(set(a['split']['train_ids']) <= set(b['split']['train_ids']) if a['fraction'] == .5 else
            set(b['split']['train_ids']) <= set(a['split']['train_ids']), 'EEG50 people are not nested in EEG100')


def process_matched(export, record, path, record_sha):
    unit = record['unit']; source = unit['binding']['source']; config = configuration(source)
    require(record['budget'] == unit['budget'], 'matched actual budget changed')
    require(sorted(map(int, record['candidates'])) == unit['budget']['candidate_steps'], 'missing matched trajectory state')
    require(unit['budget']['candidate_steps'][-1] == unit['budget']['U'], 'last candidate is not fixed U')
    ledger = record['ledger']
    if not unit['reuse_existing']:
        require(ledger['encoder_updates'] == unit['budget']['U'], 'matched training stopped before U')
    else:
        require(ledger['new_encoder_updates'] == 0 and ledger['reused_outer_full_doubled_horizon'], 'reuse provenance changed')
    export.diagnostics['matched_trajectories'].append({'unit': unit['id'], 'source_lineage': unit['source_lineage'],
        'configuration': config, 'stage': unit['stage'], 'fraction': unit['fraction'], 'budget': unit['budget'], 'ledger': ledger})
    if unit['stage'] != 'outer':
        return
    state = record['candidates'][str(unit['budget']['U'])]
    require(state['optimizer_steps'] == unit['budget']['U'], 'fixed-U snapshot update counter differs')
    evaluation = state['evaluation']; split = unit['split']; row = source['outer']['row']
    provenance = population_provenance(evaluation, split['outer_fold'], path, record_sha)
    # Audio statistics are a task-fitted source object even though their access
    # is intentionally common to EEG50/100. Include their people in the audit.
    provenance['population_fit_identities'] = sorted(set(provenance['population_fit_identities']) | set(split['full_source_audio_ids']))
    for identity, person in evaluation['per_participant'].items():
        if person['status'] != 'complete':
            export.diagnostics['unavailable_people'].append({'unit': unit['id'], 'identity': identity, 'status': person['status']})
            continue
        for mode in ('native', 'unified'):
            panel = export.panel('matched_U', 'dtu', config, mode)
            cell = {'metrics': person['metrics'][mode], 'query_hash': person['query_hash'], 'candidate_hash': person['candidate_hash']}
            export.add(panel, identity, person['group'], row, f'fraction_{int(100*unit["fraction"])}', cell, provenance,
                       {'actual_U': unit['budget']['U'], 'scheduler_horizon_updates': unit['budget']['scheduler_horizon_updates'],
                        'personal_adaptation_steps': 0})


def validate_policy(record, policy, inner, outer, plan_hash, policy_code_hash):
    require(inner['record']['unit']['stage'] == 'inner' and outer['record']['unit']['stage'] == 'outer',
            'selector must bind genuine inner and outer trajectory roles')
    require(record['status'] == policy['status'] == 'complete', 'selector status incomplete')
    require(record['matched_plan_sha256'] == policy['matched_plan_sha256'] == plan_hash, 'selector plan differs')
    require(record['selection_code_sha256'] == policy['selection_code_sha256'] == policy_code_hash, 'selector code differs')
    require(record['outer_data_access_for_selection'] is False and policy['outer_data_access_for_selection'] is False,
            'policy does not certify inner-only input')
    require(all(record.get(k) == v for k, v in policy.items()), 'applied result differs from immutable source policy')
    require(record['inner_record_sha256'] == inner['sha'] and record['outer_record_sha256'] == outer['sha'],
            'selector input record hash changed')
    require(record['lineage'] == inner['record']['unit']['source_lineage'] == outer['record']['unit']['source_lineage'],
            'selector source lineage differs')
    require(record['fraction'] == inner['record']['unit']['fraction'] == outer['record']['unit']['fraction'],
            'selector fraction differs')
    expected_id = 'ALN35SEL_' + digest({'lineage': record['lineage'], 'fraction': record['fraction'],
        'inner_sha256': inner['sha'], 'code_sha256': policy_code_hash, 'matched_plan_sha256': plan_hash})[:16]
    require(record['id'] == policy['id'] == expected_id, 'selector immutable ID differs from actual inputs')
    inner_split = inner['record']['unit']['split']
    require(not set(inner_split['evaluation_ids']) & set(inner_split['train_ids']), 'inner person seen during EEG training')
    require(not set(inner_split['evaluation_ids']) & set(inner_split['full_source_audio_ids']), 'inner person seen in source audio statistics')
    for choice in record['policy'].values():
        if choice['status'] == 'complete':
            require(set(choice['complete_inner_ids']) <= set(inner_split['evaluation_ids']), 'selection identity outside declared inner role')
            require(not set(choice['complete_inner_ids']) & set(outer['record']['unit']['split']['evaluation_ids']),
                    'outer identity used by selection')


def process_policy(export, record, outer, path, record_sha):
    unit = outer['unit']; source = unit['binding']['source']; config = configuration(source)
    for mode in ('native', 'unified'):
        choice = record['policy'][mode]
        export.diagnostics['true_risk_policies'].append({'unit': record['id'], 'source_lineage': record['lineage'],
            'configuration': config, 'readout': mode, 'fraction': record['fraction'], **choice})
        if choice['status'] != 'complete' or record['outer'][mode]['status'] != 'complete':
            continue
        panel = export.panel('true_risk_selection', 'dtu', config, mode, fraction=record['fraction'])
        split = unit['split']; row = source['outer']['row']
        provenance = population_provenance({'fit_ids': split['train_ids'], 'calibration_ids': split['readout_fit_cal_ids']},
            split['outer_fold'], path, record_sha, choice['complete_inner_ids'])
        provenance['population_fit_identities'] = sorted(set(provenance['population_fit_identities']) | set(split['full_source_audio_ids']))
        for identity, person in record['outer'][mode]['per_participant'].items():
            if person['status'] != 'complete':
                continue
            for arm in ('true_risk_policy', 'gain_policy'):
                name = 'true_risk' if arm == 'true_risk_policy' else 'gain'
                step = outer['budget']['candidate_steps'][choice[f'{name}_candidate_index']]
                require(record['outer'][mode][f'{name}_outer_step'] == step, 'applied relative checkpoint differs')
                source_person = outer['candidates'][str(step)]['evaluation']['per_participant'][identity]
                require(person[arm] == source_person['metrics'][mode], 'applied policy metrics differ from bound trajectory')
                require(person['query_hash'] == source_person['query_hash'] and
                        person['candidate_hash'] == source_person['candidate_hash'], 'applied policy query/candidates differ')
                cell = {'metrics': person[arm], 'query_hash': person['query_hash'], 'candidate_hash': person['candidate_hash']}
                export.add(panel, identity, person['group'], row, arm, cell, provenance,
                           {'personal_adaptation_steps': 0, 'outer_data_access_for_selection': False,
                            'true_risk_selected_epoch0': choice['true_risk_selected_epoch0'],
                            'gain_selected_epoch0': choice['gain_selected_epoch0']})


def build_spec(panel, metric, rosters):
    dataset = panel['dataset']; direction = MEASURES[metric][1]; unit = metric_unit(dataset, metric)
    comparisons = []
    for reference, candidate, label in panel['comparisons']:
        comparisons.append({'id': label, 'description':
            'candidate minus reference' if direction == 1 else 'reference minus candidate; positive means lower candidate value',
            'terms': [{'group': 'all', 'arm': f'{panel["panel_id"]}/{reference}', 'window': 'registered_full_input', 'weight': -direction},
                      {'group': 'all', 'arm': f'{panel["panel_id"]}/{candidate}', 'window': 'registered_full_input', 'weight': direction}]})
    return {'family_id': f'{panel["panel_id"]}__{metric}', 'dataset': dataset, 'metric': metric, 'unit': unit,
            'required_folds': ['content_0', 'content_1'] if dataset == 'dtu' else ['evaluation'], 'required_seeds': [3401],
            'expected_identities': {'all': sorted(rosters[dataset])},
            'group_sets': {'all': sorted({v['group'] for v in rosters[dataset].values()})},
            'minimum_n': 3, 'require_full_provenance': False, 'analysis_role': 'outer_test',
            'bootstrap': {'B': 4000, 'seed': 351001, 'alpha': .05, 'resampling': 'stratified'},
            'description': 'Exploratory fixed ALN3.5 family. All declared conditions/content cells required within identity. '
                'Five U10 draws averaged first; actual training seed3401. Source fit/selection IDs and query/candidate hashes supplied; '
                'explicit sample IDs are not in unit output, so full explicit-ID provenance is not claimed.',
            'contrasts': comparisons}


def empty_result(spec):
    REF.validate_spec(spec)
    ids = spec['expected_identities']['all']
    return {'family_id': spec['family_id'], 'dataset': spec['dataset'], 'metric': spec['metric'], 'unit': spec['unit'],
            'status': 'not_started', 'method': 'identity bootstrap with fixed original SE, max absolute centered z-star',
            'bootstrap': {**spec['bootstrap'], 'critical_value': None, 'original_se_reestimated_per_draw': False},
            'coverage': {'all': {'expected_n': len(ids), 'observed_n': 0, 'common_complete_n': 0,
                'complete_identities': [], 'missing_expected_identities': ids, 'expected_status': 'supplied',
                'row_group_levels': spec['group_sets']['all'], 'observed_outside_expected': [], 'excluded_incomplete': {}}},
            'contrasts': [{**c, 'estimate': None, 'original_se': None, 'simultaneous_ci': None,
                'status': 'not_started', 'nonregular_reasons': ['no completed production rows']} for c in spec['contrasts']],
            'simultaneous_scope': [], 'identity_values': {}, 'spec': spec,
            'validation': {'selected_rows': 0, 'provenance_limit': 'No completed production rows; no synthetic substitutions.'}}


def summarize_panels(export):
    families = []; all_rows = []; specs = []
    for panel in sorted(export.panels.values(), key=lambda p: p['panel_id']):
        all_rows.extend(panel['rows'])
        metrics = ('nll_bits', 'wrong_nll_bits', 'mismatch_gain_bits', 'auc', 'brier') if panel['dataset'] == 'private_bdf' else (
            'nll_bits', 'wrong_nll_bits', 'mismatch_gain_bits', 'top1', 'rank_pct')
        for metric in metrics:
            spec = build_spec(panel, metric, export.rosters); specs.append(spec)
            rows = [r for r in panel['rows'] if r['metric'] == metric]
            try:
                result = REF.analyze(rows, spec) if rows else empty_result(spec)
            except (BindingError, REF.ReferenceError) as error:
                export.record_error(spec['family_id'], error)
                result = {'family_id': spec['family_id'], 'dataset': spec['dataset'], 'metric': metric, 'unit': spec['unit'],
                          'status': 'invalid_pairing', 'reason': str(error), 'spec': spec, 'contrasts': [], 'coverage': {}}
            expected = sorted(set(panel['expected_units'])); available = sorted(set(panel['available_units']))
            result.update(panel_id=panel['panel_id'], configuration=panel['configuration'], readout=panel['readout'],
                          source_support_steps=panel['source_support_steps'], EEG_fraction=panel['EEG_fraction'],
                          execution_status='complete' if len(expected) == len(available) else 'interim',
                          expected_unit_count=len(expected), complete_unit_count=len(available),
                          missing_unit_ids=sorted(set(expected)-set(available)), exploratory=True)
            # reference_only refers to the numerical implementation, not fake
            # EEG data. Explicitly bind this result to actual server outcomes.
            result['actual_production_inputs'] = True
            families.append(result)
    return families, all_rows, specs


def transaction(export, operation, *args):
    """A malformed unit is excluded as a whole; unrelated work continues."""
    row_lengths = {k: len(v['rows']) for k, v in export.panels.items()}
    diagnostic_lengths = {k: len(v) for k, v in export.diagnostics.items()}
    try:
        operation(export, *args)
        return True
    except (KeyError, TypeError, ValueError, AssertionError) as error:
        for k, panel in export.panels.items():
            del panel['rows'][row_lengths.get(k, 0):]
        for k in export.diagnostics:
            del export.diagnostics[k][diagnostic_lengths[k]:]
        export.record_error(args[-2] if len(args) >= 2 else operation.__name__, error)
        return False


def collect(root=ROOT):
    plans = {}; inputs = []
    for lane, expected_hash in PLAN_HASHES.items():
        path = root / lane / 'plan.json'; plan, actual_hash = read(path)
        require(actual_hash == expected_hash, f'frozen {lane} plan changed')
        plans[lane] = plan; inputs.append({'path': str(path.relative_to(REPO)), 'sha256': actual_hash, 'role': 'frozen_plan'})
    geometry_path = root / 'support_coverage_v1/restricted_support_bindings.json'
    geometry, geometry_hash = read(geometry_path)
    require(geometry_hash == plans['support_coverage_v1']['query_binding_sha256'], 'frozen support geometry changed')
    export = Export(identity_roster(geometry), geometry)
    export.inputs = inputs + [{'path': str(geometry_path.relative_to(REPO)), 'sha256': geometry_hash, 'role': 'restricted_geometry'}]
    inventory = {'support': [], 'episode': [], 'matched': [], 'selection': []}
    merged = episode_units(plans['episode_pressure_v1'], plans['episode_lineage_v2'])
    work = [('support', 'support_coverage_v1', unit, unit['id']) for unit in plans['support_coverage_v1']['rows']]
    work += [('episode', lane, unit, original) for lane, unit, original in merged]
    work += [('matched', 'matched_updates_v1', unit, unit['id']) for unit in plans['matched_updates_v1']['rows']]
    matched = {}
    # Fixed panel definitions and expected memberships are built before reading outcomes.
    for kind, lane, unit, scientific_id in work:
        if kind == 'support':
            panel_membership(export, 'support', unit, scientific_id)
        elif kind == 'episode':
            for panelkind in ('episode_fixed20', 'episode_selected'):
                panel_membership(export, panelkind, unit, scientific_id)
        elif unit['stage'] == 'outer':
            panel_membership(export, 'matched_U', unit, scientific_id)
            panel_membership(export, 'true_risk_selection', unit, f'{unit["source_lineage"]}/{unit["fraction"]}')
    for kind, lane, unit, scientific_id in work:
        path = root / lane / 'units' / f'{unit["id"]}.json'
        entry = {'scientific_id': scientific_id, 'execution_id': unit['id'], 'lane': lane, 'state': 'missing'}
        inventory[kind].append(entry)
        if not path.is_file():
            if path.with_name(path.stem + '.FAILED.json').is_file():
                entry['state'] = 'failed_execution'
            continue
        try:
            record, record_sha = read(path); valid_record(record, unit, PLAN_HASHES[lane])
            export.inputs.append({'path': str(path.relative_to(REPO)), 'sha256': record_sha, 'role': 'production_unit'})
            if kind == 'support':
                ok = transaction(export, process_support, record, path, record_sha)
            elif kind == 'episode':
                ok = transaction(export, process_episode, record, path, record_sha)
            else:
                ok = transaction(export, process_matched, record, path, record_sha)
            entry.update(state='complete' if ok else 'invalid_record', sha256=record_sha)
            if ok and kind == 'matched':
                matched[(unit['source_lineage'], unit['stage'], unit['fraction'])] = {'record': record, 'sha': record_sha}
            if ok:
                for panel in export.panels.values():
                    if scientific_id in panel['expected_units']:
                        panel['available_units'].append(scientific_id)
        except (KeyError, ValueError, TypeError, AssertionError) as error:
            entry['state'] = 'invalid_record'; export.record_error(path, error)
    # Cross-fraction checks precede any paired 50/100 statistical inference.
    for lineage, stage, fraction in list(matched):
        if fraction != .5 or (lineage, stage, 1.) not in matched:
            continue
        try:
            validate_matched_pair(matched[(lineage, stage, .5)]['record'], matched[(lineage, stage, 1.)]['record'])
        except (BindingError, KeyError) as error:
            export.record_error(f'matched_pair/{lineage}/{stage}', error)
            for fraction2 in (.5, 1.):
                bad = matched.pop((lineage, stage, fraction2))
                badid = bad['record']['id']
                for entry in inventory['matched']:
                    if entry['execution_id'] == badid:
                        entry['state'] = 'invalid_matched_pair'
                for panel in export.panels.values():
                    panel['rows'][:] = [r for r in panel['rows'] if r['provenance']['source_sha256'] != bad['sha']]
                    panel['available_units'][:] = [u for u in panel['available_units'] if u != badid]
    policy_code_hash = plans['matched_updates_v1']['sources']['auditory_alignment_v3/aln35/selection_policy.py']
    # Files are identified from registered lineage/fraction and immutable inner hash;
    # stale alternatives never compete for an outer-favorable result.
    for unit in plans['matched_updates_v1']['rows']:
        if unit['stage'] != 'outer':
            continue
        lineage, fraction = unit['source_lineage'], unit['fraction']; key = f'{lineage}/{fraction}'
        entry = {'scientific_id': key, 'state': 'waiting_inner_and_outer'}; inventory['selection'].append(entry)
        inner = matched.get((lineage, 'inner', fraction)); outer = matched.get((lineage, 'outer', fraction))
        if not inner or not outer:
            continue
        policy_id = 'ALN35SEL_' + digest({'lineage': lineage, 'fraction': fraction, 'inner_sha256': inner['sha'],
            'code_sha256': policy_code_hash, 'matched_plan_sha256': PLAN_HASHES['matched_updates_v1']})[:16]
        entry['execution_id'] = policy_id
        policy_path = root / 'true_risk_selection_v1/policies' / f'{policy_id}.json'
        path = root / 'true_risk_selection_v1/units' / f'{policy_id}.json'
        if not path.is_file() or not policy_path.is_file():
            entry['state'] = 'waiting_cpu_policy_refresh'; continue
        try:
            policy, policy_sha = read(policy_path); record, record_sha = read(path)
            validate_policy(record, policy, inner, outer, PLAN_HASHES['matched_updates_v1'], policy_code_hash)
            export.inputs.extend([{'path': str(p.relative_to(REPO)), 'sha256': s, 'role': role} for p, s, role in (
                (policy_path, policy_sha, 'immutable_inner_policy'), (path, record_sha, 'applied_outer_policy'))])
            ok = transaction(export, process_policy, record, outer['record'], path, record_sha)
            entry.update(state='complete' if ok else 'invalid_record', sha256=record_sha)
            if ok:
                for panel in export.panels.values():
                    if key in panel['expected_units']:
                        panel['available_units'].append(key)
        except (KeyError, ValueError, TypeError, AssertionError) as error:
            entry['state'] = 'invalid_record'; export.record_error(path, error)
    return export, inventory


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False); handle.write('\n')


def diagnostic_summary(export):
    """Descriptive costs/pressure and policy rates; never a second inference n."""
    output = {'scope': 'Descriptive available-record diagnostics. People, source units and policy decisions have separate denominators; '
                       'these rates are not independent-person effect intervals.',
              'support_coverage': [], 'episode_source_pressure': [], 'episode_policy_rates': [],
              'true_risk_policy_rates': [], 'matched_costs': []}
    grouped = defaultdict(list)
    for row in export.diagnostics['support_coverage']:
        policy = 'U10' if row['draw_or_policy'].startswith('U10_') else row['draw_or_policy']
        grouped[(row['dataset'], row['configuration'], policy)].append(row)
    for (dataset, config, policy), records in sorted(grouped.items()):
        people = defaultdict(list)
        for row in records:
            people[row['identity']].append(row)
        coverage = {}
        def person_mean(rows, get_value):
            content = defaultdict(list)
            for item in rows:
                value = get_value(item)
                if finite(value):
                    content[item['content_fold']].append(value)
            return mean([mean(values) for values in content.values()])
        fields = ('n_support', 'n_query', 'original_available_count', 'support_fraction', 'n_support_blocks',
                  'n_query_blocks', 'guard_excluded_count', 'time_span_seconds', 'effective_independent_sounds', 'effective_sound_classes')
        for field in fields:
            values = [person_mean(rows, lambda r: r['support'].get(field)) for rows in people.values()]
            if any(v is not None for v in values):
                coverage[field] = {k: v for k, v in stat(values).items() if k != 'last'}
        budgets = {}
        for method in METHODS:
            budgets[method] = {}
            for field in ('selection_pool_size', 'metadata_rows_accessed', 'label_rows_accessed', 'fit_rows', 'fit_updates'):
                values = [person_mean(rows, lambda r: r['methods'][method]['access_budget'].get(field)) for rows in people.values()]
                budgets[method][field] = {k: v for k, v in stat(values).items() if k != 'last'}
        output['support_coverage'].append({'dataset': dataset, 'configuration': config, 'support': policy,
            'observed_unique_people': len(people), 'expected_people': len(export.rosters[dataset]),
            'observed_draw_content_cells': len(records),
            'people_with_both_content_cells': sum(len({r['content_fold'] for r in rows}) == 2 for rows in people.values())
                if dataset == 'dtu' else None,
            'within_person_rule': 'Mean available draws then content cells; descriptive available coverage only, not the complete paired effect panel',
            'actual_coverage': coverage, 'separate_access_budgets': budgets})
    grouped = defaultdict(list)
    for row in export.diagnostics['episode_source']:
        grouped[(row['dataset'], row['configuration'], row['pressure'], row['stage'], row['regime'])].append(row)
    for (dataset, config, pressure, stage, regime), records in sorted(grouped.items()):
        names = sorted(set().union(*(r['source_only_diagnostics'] for r in records)))
        output['episode_source_pressure'].append({'dataset': dataset, 'configuration': config,
            'source_support_steps': pressure, 'stage': stage, 'regime': regime, 'source_units': len(records),
            'expected_source_units': 10 if dataset == 'dtu' else 5,
            'mean_per_source_unit_of_update_means': {name: stat([r['source_only_diagnostics'].get(name, {}).get('mean') for r in records]) for name in names},
            'paired_final_direction_cosine': stat([r['paired_final_update_direction_cosine'] for r in records]),
            'actual_encoder_updates': sum(r['ledger']['encoder_updates'] for r in records),
            'actual_support_optimizer_steps': sum(r['ledger']['support_optimizer_steps'] for r in records),
            'query_exposures': sum(r['ledger']['query_exposures'] for r in records),
            'wall_seconds': stat([r['ledger'].get('seconds') for r in records]),
            'independent_person_n_claimed': False})
    grouped = defaultdict(list)
    for row in export.diagnostics['episode_policies']:
        grouped[(row['dataset'], row['configuration'], row['source_support_steps'], row['readout'], row['support'], row['regime'])].append(row)
    for (dataset, config, pressure, mode, support, regime), records in sorted(grouped.items()):
        complete = [r for r in records if r['status'] == 'complete']
        output['episode_policy_rates'].append({'dataset': dataset, 'configuration': config, 'source_support_steps': pressure,
            'readout': mode, 'support': support, 'regime': regime, 'expected_policy_decisions': 10 if dataset == 'dtu' else 5,
            'recorded_policy_decisions': len(records), 'complete_policy_decisions': len(complete),
            'zero_step_fraction_of_complete_decisions': mean([int(r['zero_step_selected']) for r in complete]),
            'source_fallback_fraction_of_complete_decisions': mean([int(r['source_fallback_selected']) for r in complete]),
            'independent_person_n_claimed': False})
    grouped = defaultdict(list)
    for row in export.diagnostics['true_risk_policies']:
        grouped[(row['configuration'], row['readout'], row['fraction'])].append(row)
    for (config, mode, fraction), records in sorted(grouped.items()):
        complete = [r for r in records if r['status'] == 'complete']
        output['true_risk_policy_rates'].append({'configuration': config, 'readout': mode, 'EEG_fraction': fraction,
            'expected_policy_decisions': 10, 'recorded_policy_decisions': len(records), 'complete_policy_decisions': len(complete),
            'true_risk_epoch0_fraction_of_complete_decisions': mean([int(r['true_risk_selected_epoch0']) for r in complete]),
            'gain_epoch0_fraction_of_complete_decisions': mean([int(r['gain_selected_epoch0']) for r in complete]),
            'independent_person_n_claimed': False})
    grouped = defaultdict(list)
    for row in export.diagnostics['matched_trajectories']:
        grouped[(row['configuration'], row['stage'], row['fraction'])].append(row)
    for (config, stage, fraction), records in sorted(grouped.items()):
        output['matched_costs'].append({'configuration': config, 'stage': stage, 'EEG_fraction': fraction,
            'complete_trajectory_units': len(records), 'expected_trajectory_units': 10,
            'total_actual_U_evaluated': sum(r['budget']['U'] for r in records),
            'new_encoder_updates': sum(r['ledger'].get('encoder_updates', r['ledger'].get('new_encoder_updates', 0)) for r in records),
            'reused_outer_full_units': sum(bool(r['ledger'].get('reused_outer_full_doubled_horizon')) for r in records),
            'source_EEG_people_per_unit': stat([r['ledger'].get('actual_source_people') for r in records]),
            'anchor_exposures_per_new_training_unit': stat([r['ledger'].get('anchor_exposures') for r in records]),
            'independent_person_n_claimed': False})
    return output


def markdown_report(summary):
    lines = ['# ALN3.5 support / episode / matched updates / true-risk selection', '',
             f'Job {summary["job"]}; snapshot {summary["created_utc"]}; **{summary["status"]}**.', '',
             'Only completed production records enter. Engineering probes and old blocked episode execution IDs do not count.', '',
             '| Work | Complete / expected scientific units |', '|---|---:|']
    for lane, count in summary['execution_coverage'].items():
        lines.append(f'| {lane} | {count["complete"]} / {count["expected"]} |')
    lines += ['', 'Expected independent people: DTU 44; private 64. U10 averages five fixed support draws within each person; '
              'DTU then requires both registered content folds. Outer person fold is membership, not a repeated measurement.', '',
              'The exploratory intervals use 4,000 whole-person hearing-group-stratified draws, fixed original SE and max-|z*|. '
              'No aggregate CI subtraction, result selection, performance gate, or seed-by-person sample inflation.', '',
              '| True-query NLL family | Paired people / expected | Complete units / expected |', '|---|---:|---:|']
    for family in summary['families']:
        if family['metric'] != 'nll_bits':
            continue
        coverage = family.get('coverage', {}).get('all', {})
        lines.append(f'| {family["family_id"]} | {coverage.get("common_complete_n", "invalid")} / '
                     f'{coverage.get("expected_n", "unknown")} | {family["complete_unit_count"]} / {family["expected_unit_count"]} |')
    lines += ['', 'All signed estimates, simultaneous intervals, nonregular reasons and missing cells are in summary.json. '
              'Positive NLL/Brier/rank improvement means reference minus candidate; AUC/top1/mismatch-gain use candidate minus reference. '
              'Wrong-query risk is a diagnostic with its own signed value, not an automatic criterion of improvement.', '',
              'Private support rank4 is the output adapter; private episode rank4 is the spatial input adapter. Their effects are separate. '
              'The shared direct sample guard inherits whole-record offline preprocessing; it does not establish causal preprocessing isolation. '
              'Current task-specific inner sources exclude the selected inner people, using source-ES content.', '',
              f'Validation issues: {len(summary["validation_issues"])}. Any invalid unit/pair is reported and excluded from its dependent inference; '
              'other registered work continues. No missing value is replaced by a synthetic result.', '']
    return '\n'.join(lines)


def run(output_root=BASE, public_root=PUBLIC):
    require(bool(os.environ.get('SLURM_JOB_ID')), 'all aggregation computation must run in Slurm')
    os.umask(0o077)
    started = datetime.now(timezone.utc); job = os.environ['SLURM_JOB_ID']
    snapshot_id = f'job_{job}_{started.strftime("%Y%m%dT%H%M%S%fZ")}'
    dest = Path(output_root) / 'snapshots' / snapshot_id
    require(not dest.exists(), 'snapshot must be new')
    export, inventory = collect()
    families, rows, specs = summarize_panels(export)
    coverage = {lane: {'expected': len(entries), 'complete': sum(e['state'] == 'complete' for e in entries),
                       'states': {state: sum(e['state'] == state for e in entries) for state in sorted({e['state'] for e in entries})}}
                for lane, entries in inventory.items()}
    complete = all(c['complete'] == c['expected'] for c in coverage.values())
    summary = {'schema_version': 'aln35.support-experiments-summary.v1', 'analysis_version': ANALYSIS_VERSION, 'job': job,
        'snapshot_id': snapshot_id, 'created_utc': started.isoformat(),
        'status': 'interim_validation_issues' if export.errors else 'complete' if complete else 'interim',
        'execution_coverage': coverage, 'expected_independent_people': {'dtu': 44, 'private_bdf': 64},
        'episode_merge': '58 original + 2 lineage successor = 60 scientific configurations; old outputs retained',
        'analysis_code_sha256': sha(__file__), 'analysis_design_sha256': sha(CONTRACT_NOTE),
        'reference_statistics_sha256': sha(Path(REF.__file__)), 'input_manifest_sha256': digest(export.inputs),
        'families': families, 'diagnostics': diagnostic_summary(export), 'validation_issues': export.errors,
        'provenance_limit': 'Source-fit/selection people, source records and Q/candidate hashes checked. Explicit support/query sample '
            'IDs are not exported by this summary; require_full_provenance=false is deliberate. Guard/whole-record preprocessing access '
            'remains as frozen in the source contract; this summary does not prove no raw-preprocessing overlap.',
        'diagnostic_location': 'server-only diagnostics.json and normalized_rows.jsonl beside this snapshot; original unit records remain authoritative',
        'scope': 'Exploratory NCE3401 bounded panels; no task/architecture pooling, new model selection, old-analysis rewrite or performance gates'}
    write_new(dest / 'summary.json', summary); write_new(dest / 'specs.json', specs)
    write_new(dest / 'inputs.json', export.inputs); write_new(dest / 'inventory.json', inventory)
    write_new(dest / 'diagnostics.json', export.diagnostics)
    with (dest / 'normalized_rows.jsonl').open('x') as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
    report = markdown_report(summary); (dest / 'REPORT.md').write_text(report)
    public = Path(public_root) / 'snapshots' / snapshot_id
    write_new(public / 'summary.json', summary); (public / 'REPORT.md').write_text(report)
    pointer = {'snapshot_id': snapshot_id, 'summary': str(dest / 'summary.json'),
               'public_summary': str(public / 'summary.json'), 'status': summary['status'], 'job': job,
               'execution_coverage': coverage, 'created_utc': started.isoformat(),
               'validation_issue_count': len(export.errors), 'family_count': len(families),
               'analysis_code_sha256': summary['analysis_code_sha256'], 'analysis_version': ANALYSIS_VERSION}
    # A discovery pointer may advance; snapshots and source records are immutable.
    Path(output_root).mkdir(parents=True, exist_ok=True)
    tmp = Path(output_root) / f'latest.{job}.tmp'; tmp.write_text(json.dumps(pointer, indent=2) + '\n')
    os.replace(tmp, Path(output_root) / 'latest.json')
    print(json.dumps(pointer, indent=2), flush=True)
    return 2 if export.errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, default=BASE)
    parser.add_argument('--public-root', type=Path, default=PUBLIC)
    args = parser.parse_args()
    raise SystemExit(run(args.output_root, args.public_root))


if __name__ == '__main__':
    main()
