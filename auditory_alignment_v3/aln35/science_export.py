"""Export the exact ALN3.5 science and original-endpoint observations."""
from collections import defaultdict
import math
from pathlib import Path
import numpy as np

from . import science_binding as B


def missing(binding, row, scope, reason, **extra):
    binding.missing.append({'source_unit_id': row['experiment_id'], 'dataset': row['dataset'],
                            'scope': scope, 'reason': reason, **extra})


def keep_value(binding, row, scope, identity, value):
    if value is None or not math.isfinite(float(value)):
        missing(binding, row, scope, 'missing_or_nonfinite_metric', identity=identity)
        return False
    return True


def public_records(binding, row, rec, path, arrays, arm, windows, source_lane, prior=False):
    ds = row['dataset']; cf = int(row['content_fold'] or 0)
    fs = int(rec['metadata']['fs']); out = []
    source_population = rec['decoding']['model/env/direct']['0/0']['per_participant']
    grouped = defaultdict(list)
    for pid in source_population:
        ident, group, human = binding.identity(ds, pid)
        if human: grouped[(ident, group)].append(pid)
    for (ident, group), pids in sorted(grouped.items()):
        if set(pids) != set(binding.sessions[(ds, ident)]):
            missing(binding, row, source_lane, 'missing_registered_identity_session', identity=ident,
                    expected=binding.sessions[(ds, ident)], observed=pids)
            continue
        queries = []
        for pid in sorted(pids):
            q = B.public_queries(arrays, pid, ds, cf, fs)
            assert len(q) == source_population[pid]['n_anchors']
            queries.extend(q)
        for window in windows:
            target, cell = window.split('@')
            per = rec['decoding']['model/' + target][cell]['per_participant']
            values = [per[p]['r'] for p in pids]
            if not all(keep_value(binding, row, source_lane, ident, v) for v in values): continue
            out.append(binding.observation(row, path, ident, group, arm, window, 'r', 'Pearson_r',
                math.fsum(values) / len(values), queries, prior=prior, source_lane=source_lane,
                extra={'session_record_ids': sorted(pids), 'session_aggregation': 'equal mean within identity, before content and seed means',
                       'cache_array_sha256': rec['metadata']['array_sha256'],
                       'representation_access': rec['metadata'].get('actual_model_access', rec['metadata'].get('model_access_ms'))}))
    return out


def run(binding):
    from auditory_alignment_v3.prior33 import target_train as TT
    observations = []
    plans = {lane: binding.load_lane(lane) for lane in ('content_time_v1', 'prior_science_v1')}
    for lane, plan in plans.items():
        for unit in plan['rows']:
            row = unit['source']; ds = row['dataset']
            if row['spec']['objective'] != 'NCE': continue
            prior = lane == 'prior_science_v1'
            arm = TT.arm_of(row)[0] if prior else B.native_arm(row)
            if arm is None: continue
            if prior and ds not in ('private_bdf', 'fau'): continue
            hit = binding.lane_record(lane, unit)
            if hit is None: continue
            rec, path = hit
            cp, meta = binding.cache(lane, plan, rec)
            if ds == 'private_bdf':
                assert meta['sample_times_ms'][0] == 0 and meta['sample_times_ms'][-1] == 578.125
                assert meta['children'] == {str(i): k['id'] for i, k in enumerate(binding.kids)}
                with np.load(cp / 'arrays.npz', allow_pickle=False) as z:
                    for i, k in enumerate(binding.kids): assert z[f'full_{i}'].shape == (len(k['y']), 32)
                for ident, values in rec['per_participant'].items():
                    kid = binding.kid_by_id[ident]
                    assert kid['fold'] == row['subject_fold'] and kid['group'] == values['group']
                    # Context levels are exported symmetrically for all five prior
                    # arms, while tests remain the exact declared small families.
                    windows = ('full', '0_200', '200_400', '400_600')
                    for window in windows:
                        for metric, unitname in (('auc', 'AUC'), ('history_gain_bits', 'bits/trial'), ('history_minus_twin_bits', 'bits/trial')):
                            value = values['windows'][window][metric]
                            if keep_value(binding, row, lane, ident, value):
                                observations.append(binding.observation(row, path, ident, kid['group'], arm, window, metric,
                                    unitname, value, binding.private_query[ident], prior=True, source_lane=lane,
                                    extra={'private_trial_binding': binding.private_trial_bindings[ident],
                                           'cache_array_sha256': meta['array_sha256'], 'input_sample_times_ms': [0, 578.125]}))
                continue
            with np.load(cp / 'arrays.npz', allow_pickle=False) as z:
                arrays = {k: z[k] for k in ('role', 'person', 'segment', 'source_segment_e0', 'anchor_offsets')}
            key = (ds, row['subject_fold'], int(row['content_fold'] or 0))
            dest = binding.prior_cache if prior else binding.native_cache
            # Any representative cache for the same cohort/fold is lawful for
            # the original full 5s query list; compare explicit physical IDs.
            view = {}
            for pid in rec['decoding']['model/env/direct']['0/0']['per_participant']:
                view[pid] = B.public_queries(arrays, pid, ds, key[2], int(meta['fs']), anchors=False)
            if key in dest: assert dest[key]['queries'] == view
            else: dest[key] = {'queries': view, 'source_path': str(cp / 'arrays.npz'), 'array_sha256': meta['array_sha256']}
            if prior:
                windows = ('env/history_conditional@0/0',)
            else:
                windows = ['env/history_conditional@0/0']
                if ds != 'federici': windows += ['spec/conditional@0/0', 'flux/conditional@0/0']
                if arm == 'CB_PRE' and ds in ('dtu', 'fau'):
                    windows += ['env/direct@0/0', 'env/direct@0/600', 'env/direct@600/600']
            observations.extend(public_records(binding, row, rec, path, arrays, arm, windows, lane, prior))
    observations.extend(main_endpoints(binding))
    return observations


def main_endpoints(binding):
    from auditory_alignment_v3.prior33 import target_train as TT
    from auditory_alignment_v3.aln34 import tf_l1_pairs as F
    out = []
    # A complete matched-cell contract audit from the original analysis source;
    # used to detect changes in target, access or query population, not select.
    fingerprints = defaultdict(list)
    for row in binding.rows:
        ds = row['dataset']; sf = row['subject_fold']; cf = int(row.get('content_fold') or 0)
        prior = row['family_id'] == 'ALN32_PUBLIC_AUDIO_PRIOR_TARGET'
        arm = TT.arm_of(row)[0] if prior else B.native_arm(row)
        if prior:
            if (row['spec'].get('objective') != 'NCE' or row['spec'].get('block') not in ('core', 'panel')
                    or arm not in ('S', 'AP')): continue
            if ds == 'fau' and row['seed'] == 3401:
                metric, unitname = 'main_prior_true_query_risk', 'bits/5s_query'
            elif ds == 'private_bdf' and row['seed'] in (3401, 3407, 3413):
                metric, unitname = 'main_native_auc', 'AUC'
            else: continue
        elif ds == 'fau' and arm and row['seed'] in (3401, 3407, 3413):
            metric, unitname = 'main_TF_true_query_risk', 'bits/5s_query'
        else: continue
        try: rec, path, _ = binding.source(row)
        except FileNotFoundError:
            missing(binding, row, metric, 'source_record_missing'); continue
        pop = rec['eval']['per_participant']
        if ds == 'private_bdf':
            for pid, v in rec['eval']['native_calibration']['per_participant'].items():
                value = v['positive_affine']['auc_score']
                kid = binding.kid_by_id[pid]
                assert kid['fold'] == sf and len(binding.private_query[pid]) == pop[pid]['n']
                if keep_value(binding, row, metric, pid, value):
                    out.append(binding.observation(row, path, pid, kid['group'], arm, 'full', metric, unitname,
                        value, binding.private_query[pid], prior=True, source_lane='original_main_endpoint',
                        extra={'private_trial_binding': binding.private_trial_bindings[pid],
                               'original_endpoint': 'eval.native_calibration.per_participant.positive_affine.auc_score'}))
        else:
            cache = binding.prior_cache if prior else binding.native_cache
            if (ds, sf, cf) not in cache:
                missing(binding, row, metric, 'exact_query_cache_missing'); continue
            query = cache[(ds, sf, cf)]
            assert set(query['queries']) == set(pop)
            if prior:
                fingerprints[(metric, sf, cf, row['seed'])].append({k: rec[k] for k in
                    ('split_hash', 'manifest_sha256', 'target_contract', 'pool_sha256', 'view_sha256')})
            else:
                fp, _ = F.fingerprints(rec, 'L1' if arm == 'LOCAL' else 'TF', row,
                    {f: B.core.code_hash(f) for f in F.FAMILY.values()}, F.file_sha(*F.EVAL_FILES))
                assert fp['row_consistent'] and fp['code_hash_reproduced']
                fingerprints[(metric, sf, cf, row['seed'])].append({k: fp[k] for k in ('split', 'target', 'access_key', 'evaluation')})
            for pid, v in pop.items():
                ident, group, human = binding.identity(ds, pid)
                assert human
                value = v['unified/regular']['logloss_bits']
                queries = query['queries'][pid]
                assert len(queries) == v['unified/regular']['n_queries'] == v['n_segments']
                if keep_value(binding, row, metric, pid, value):
                    out.append(binding.observation(row, path, ident, group, arm, 'full', metric, unitname, value,
                        queries, prior=prior, source_lane='original_main_endpoint',
                        extra={'query_metadata_cache': query['source_path'], 'query_metadata_cache_sha256': query['array_sha256'],
                               'original_endpoint': 'eval.per_participant.unified/regular.logloss_bits'}))
    for cell, values in fingerprints.items():
        assert all(x == values[0] for x in values), ('original main endpoint contract mismatch', cell, values)
    return out


def bind_families(binding):
    science = B.read(B.PACKAGE / 'plans/science_contrasts.json')['families']
    originals = B.read(B.PACKAGE / 'plans/main_endpoint_group_contrasts.json')['families']
    compiled = []
    for family in science:
        keep = ('family_id', 'dataset', 'metric', 'unit', 'required_seeds', 'required_folds', 'group_sets', 'contrasts')
        spec = {k: family[k] for k in keep if k in family}
        compiled.append((family, spec))
    for family in originals:
        private = family['dataset'] == 'private_bdf'; tf = family['family_id'] == 'S35_MAIN_FAU_TF_GROUP'
        metric = 'main_native_auc' if private else 'main_TF_true_query_risk' if tf else 'main_prior_true_query_risk'
        effects = [('AP', 'S', 'AP_minus_S', 1)] if private else (
            [('CB_PRE', 'LOCAL', 'LOCAL_minus_CBpre', -1), ('CB_PRE', 'CB_RANDOM', 'CBrand_minus_CBpre', -1)] if tf else
            [('AP', 'S', 'S_minus_AP', -1)])
        comparisons = [('HA', 'NH')] if private else [('ha', 'ci'), ('ha', 'th'), ('ci', 'th')]
        contrasts = []
        for candidate, reference, label, sign in effects:
            for first, second in comparisons:
                terms = [{'group': first, 'arm': candidate, 'window': 'full', 'weight': sign},
                         {'group': first, 'arm': reference, 'window': 'full', 'weight': -sign},
                         {'group': second, 'arm': candidate, 'window': 'full', 'weight': -sign},
                         {'group': second, 'arm': reference, 'window': 'full', 'weight': sign}]
                contrasts.append({'id': first + '_minus_' + second + '_' + label, 'terms': terms})
        assert len(contrasts) == family['n_contrasts']
        spec = {'family_id': family['family_id'], 'dataset': family['dataset'], 'metric': metric,
                'unit': 'AUC' if private else 'bits/5s_query', 'required_seeds': family['required_seeds'],
                'required_folds': ['evaluation'] if private else ['content_0', 'content_1'],
                'group_sets': {g: [g] for pair in comparisons for g in pair}, 'contrasts': contrasts}
        compiled.append((family, spec))
    for original, spec in compiled:
        spec.update(expected_identities=B.expected_for(spec, binding.expected[spec['dataset']]),
                    minimum_n=3, require_full_provenance=True, analysis_role='outer_test',
                    bootstrap={'B': 4000, 'seed': original['bootstrap_seed'], 'alpha': .05, 'resampling': 'independent'})
    assert len(compiled) == 13 and sum(len(s['contrasts']) for _, s in compiled) == 40
    return compiled
