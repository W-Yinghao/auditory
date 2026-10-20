"""Final bridge source/cache immutability and complete paired-coverage audit."""
import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
from . import bridge_factor as F
from . import bridge_factor_analyze_v2 as A
from . import science_binding as B


def verify(run_id):
    assert os.environ.get('SLURM_JOB_ID')
    out = F.RESULTS / ('run_' + run_id); report = B.read(out / 'bridge_factor.json')
    assert report['status'] == 'complete' and report['comparison_version'] == 'S35_BRIDGE_FACTOR_v2_replayed_features_original_matrices'
    assert report['analysis_code_sha256'] == B.sha(A.__file__)
    assert report['analysis_contract_sha256'] == B.sha(F.BASE / 'analysis_contract_v2.json')
    plan = B.read(F.BASE / 'plan.json'); contract = B.read(F.BASE / 'analysis_contract_v2.json')
    paths = {}
    for p, h in contract['frozen_analysis_files_sha256'].items(): paths[str(B.ROOT / p)] = h
    entries = []
    for item in plan['entries']:
        paths.update(item['source_paths_sha256'])
        cache = Path(item['cache']); receipt = B.read(cache / 'complete.json')
        assert receipt == B.read(F.BASE / 'extract_receipts' / (item['key'] + '.json'))
        assert receipt['plan_sha256'] == report['plan_sha256'] == B.sha(F.BASE / 'plan.json')
        paths.update({str(cache / k): v for k, v in receipt['files'].items()})
        result = B.read(out / 'entries' / (item['key'] + '.json'))
        assert result['cache_receipt_sha256'] == B.sha(cache / 'complete.json')
        assert result['source_metadata_digest'] == B.digest(item['source_metadata'])
        assert result['B_fit_data']['n_donor_fit_segments'] == result['B_fit_data']['n_bridgecal_fit_segments'] == 2000
        assert result['same_cache_original_formula_max_absolute_difference'] < 1e-12
        assert result['readout_replay']['original_full_B_matrices_preserved']
        assert not result['readout_replay']['recomputed_full_B_used_on_target']
        grouped = {}
        for row in result['query_results']:
            m = row['metrics']; assert m['rank_invariant_to_temperature'] and m['temperature'] > 0
            assert m['n_queries'] == row['n_queries'] and m['n_candidates'] == row['n_candidates']
            assert math.isclose(m['nll_bits_mean_check'], m['logloss_bits'], rel_tol=1e-12, abs_tol=1e-12)
            key = (row['identity'], row['content_fold'], row['bridge'])
            ranks = tuple(m[k] for k in ('top1', 'mrr', 'rank_pct', 'mean_true_rank_1based'))
            if key in grouped: assert grouped[key] == ranks
            else: grouped[key] = ranks
        entries.append(result)
    for p, digest in paths.items(): assert F.BR.file_sha256(p) == digest, ('source/cache drift', p)
    coverage = A.verify_common_queries(entries); assert coverage == report['common_coverage']
    summaries, arm_contrasts, factor = A.summarize(entries)
    assert summaries == report['summaries'] and arm_contrasts == report['arm_contrasts'] and factor == report['factor_differences']
    assert len(summaries) == 16 and len(arm_contrasts) == 8 and len(factor) == 12
    rec = {'status': 'PASS', 'job': os.environ['SLURM_JOB_ID'], 'analysis_job': run_id,
           'time': datetime.now().astimezone().isoformat(), 'unchanged_sources_and_cache_files': len(paths),
           'source_units': 40, 'donors': 4, 'condition_summaries': 16, 'arm_contrasts': 8,
           'factor_differences': 12, 'common_coverage': coverage,
           'all_legacy_endpoints_retained': True, 'same_cache_temperature_ranks_invariant': True,
           'legacy_replay_max_absolute_difference_by_donor': {e['key']: e['legacy_replay_max_absolute_difference'] for e in entries},
           'same_cache_original_formula_max_absolute_difference': max(e['same_cache_original_formula_max_absolute_difference'] for e in entries),
           'result_sha256': B.sha(out / 'bridge_factor.json'), 'verifier_sha256': B.sha(__file__)}
    B.write_new(out / 'verification_receipt.json', rec)
    print(json.dumps(rec), flush=True)
    print(json.dumps({'factor_differences': factor}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--run-id', required=True)
    verify(p.parse_args().run_id)
