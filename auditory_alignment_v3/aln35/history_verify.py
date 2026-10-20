"""Independent coverage/source audit of the frozen history-interface execution."""
from collections import defaultdict
from datetime import datetime
import json
import math
import os
from pathlib import Path
import numpy as np
from . import science_binding as B
from . import history_interface as H


def main():
    assert os.environ.get('SLURM_JOB_ID')
    run_id = '1047305'
    root = H.RESULTS / ('run_' + run_id)
    report = B.read(root / 'history_interface.json')
    provenance = B.read(H.BASE / ('run_' + run_id) / 'provenance.json')
    for name, digest in provenance['sources'].items():
        assert B.sha(Path(name) if Path(name).is_absolute() else B.ROOT / name) == digest, name
    assert B.sha(H.__file__) == report['source_code_sha256']
    assert B.sha(B.__file__) == report['binding_code_sha256']
    binding = B.Binding()
    assert binding.private_trial_bindings == provenance['private_trial_bindings']
    units = [B.read(p) for p in sorted((root / 'units').glob('*.json'))]
    assert len(units) == 20
    assert {(u['arm'], u['subject_fold']) for u in units} == {(a, f) for a in H.ARMS for f in range(5)}
    gradients = []; retries = 0; fits = 0
    folds = defaultdict(list); by_arm = defaultdict(dict)
    from auditory_alignment_v3.sci_r1.private_task import Fold
    for u in units:
        assert B.sha(B.ROOT / u['source_record']) == u['source_record_sha256']
        fd = Fold(binding.kids, u['subject_fold'])
        expected_sources = [binding.kids[i]['id'] for i in fd.tr]
        expected_targets = [binding.kids[i]['id'] for i in fd.te]
        assert set(u['per_participant']) == set(expected_targets)
        maps = {}
        for i, k in enumerate(binding.kids):
            allowed = np.flatnonzero(k['es_mask']) if i in fd.tr else np.arange(len(k['y']))
            maps[i] = H.strict_twin_map(k['bin'], k['block'], allowed, H.SEED + int(B.digest(k['id'])[:8], 16))
        assert B.digest({binding.kids[i]['id']: maps[i].tolist() for i in fd.tr}) == u['strict_source_es_twin_map_hash']
        assert B.digest({binding.kids[i]['id']: maps[i].tolist() for i in fd.te}) == u['strict_query_twin_map_hash']
        for scope, s in u['source_fits'].items():
            assert s['source_child_ids'] == expected_sources and not set(expected_sources) & set(expected_targets)
            source_ids = []
            for i in fd.tr:
                k = binding.kids[i]; ix = np.flatnonzero(k['es_mask'])
                if scope == 'strict_other_block': ix = ix[maps[i][ix] >= 0]
                source_ids.extend(binding.private_query[k['id']][int(j)] for j in ix)
            assert B.digest(source_ids) == s['source_row_hash'] and len(source_ids) == s['n_source_ES']
            for receipts in s['fits'].values():
                fits += 1; retries += len(receipts) - 1; r = receipts[-1]
                assert r['optimizer_success'] and r['objective_finite'] and math.isfinite(r['objective'])
                assert r['gradient_maxabs_per_source_row'] <= H.GRAD_PER_ROW_TOL
                gradients.append(r['gradient_maxabs_per_source_row'])
        for identity, p in u['per_participant'].items():
            assert identity not in by_arm[u['arm']]
            by_arm[u['arm']][identity] = p
            i = next(i for i in fd.te if binding.kids[i]['id'] == identity)
            k = binding.kids[i]
            for scope, s in p['scopes'].items():
                ix = np.arange(len(k['y']))
                if scope == 'strict_other_block': ix = ix[maps[i][ix] >= 0]
                q = [binding.private_query[identity][int(j)] for j in ix]
                assert B.digest(q) == s['query_row_hash'] and len(q) == s['all_queries']['n_trials']
                common = (.01 < fd.q0[k['bin'][ix]]) & (fd.q0[k['bin'][ix]] < .99)
                assert B.digest([v for v, keep in zip(q, common) if keep]) == s['common_query_row_hash']
                if scope == 'strict_other_block':
                    assert B.digest([[binding.private_query[identity][int(j)], binding.private_query[identity][int(maps[i][j])]] for j in ix]) == s['twin_map_hash']
        folds[u['subject_fold']].append(u)
    for arm in H.ARMS: assert set(by_arm[arm]) == set(binding.expected['private_bdf'])
    for fold_units in folds.values():
        first = fold_units[0]
        for u in fold_units[1:]:
            for key in ('strict_source_es_twin_map_hash', 'strict_query_twin_map_hash'): assert u[key] == first[key]
            for scope in ('full_query', 'strict_other_block'):
                assert u['source_fits'][scope]['source_row_hash'] == first['source_fits'][scope]['source_row_hash']
                for identity in u['per_participant']:
                    one = u['per_participant'][identity]['scopes'][scope]; two = first['per_participant'][identity]['scopes'][scope]
                    for key in ('query_row_hash', 'common_query_row_hash', 'twin_map_hash'): assert one[key] == two[key]
                    for query in ('all_queries', 'q0_common_support'):
                        for key in ('B0', 'B1'): assert one[query][key] == two[query][key]
    people = list(by_arm['S'].values())
    coverage = {name: sum(p[name] for p in people) for name in ('n_trials', 'n_standard', 'n_deviant', 'n_strict_twin', 'n_fallback_same_block', 'n_self_twin')}
    coverage['n_children'] = len(people)
    coverage['strict_fraction_min'] = min(p['strict_fraction'] for p in people)
    coverage['strict_fraction_max'] = max(p['strict_fraction'] for p in people)
    coverage['q0_common_support_trials'] = sum(p['scopes']['full_query']['n_common_support'] for p in people)
    drift = {arm: {'max_absolute': max(abs(p['scopes']['full_query']['difference_from_original_history_gain_bits']) for p in by_arm[arm].values()),
                   'mean_signed': math.fsum(p['scopes']['full_query']['difference_from_original_history_gain_bits'] for p in by_arm[arm].values()) / len(people)} for arm in H.ARMS}
    receipt = {'status': 'PASS', 'job': os.environ['SLURM_JOB_ID'], 'analysis_job': run_id,
               'time': datetime.now().astimezone().isoformat(), 'unchanged_source_paths': len(provenance['sources']),
               'complete_units': len(units), 'all_arms_expected_identity_coverage': True,
               'cross_arm_query_source_and_twin_hashes_equal': True, 'cross_arm_history_only_predictions_equal': True,
               'independent_reconstruction_of_real_query_source_twin_bindings': True,
               'optimizer_fits': fits, 'optimizer_retries': retries, 'max_gradient_per_source_row': max(gradients),
               'unique_target_coverage': coverage, 'new_minus_original_full_history_gain_bits': drift,
               'numerical_execution_difference': 'float64 features and same-source-ES scaler; stricter source-only convergence criteria; original legacy fit retained',
               'result_sha256': B.sha(root / 'history_interface.json'), 'verifier_sha256': B.sha(__file__)}
    B.write_new(root / 'verification_receipt.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__': main()
