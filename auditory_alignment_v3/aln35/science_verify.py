"""Final source/cache immutability checks for completed ALN3.5 CPU science."""
from datetime import datetime
import json
import os
from pathlib import Path
from . import science_binding as B


def main():
    assert os.environ.get('SLURM_JOB_ID')
    run_id = '1047290'
    private = B.PRIVATE / ('run_' + run_id)
    result_dir = B.RESULTS / ('run_' + run_id)
    manifest = B.read(private / 'binding_manifest.json')
    paths = dict(manifest['source_records_and_caches'])
    paths.update(manifest['code_and_analysis_note_sha256'])
    checked = 0
    for name, digest in paths.items():
        path = Path(name) if Path(name).is_absolute() else B.ROOT / name
        assert B.sha(path) == digest, ('source drift', name)
        checked += 1
    assert B.sha(private / 'observations.jsonl') == manifest['observation_sha256']
    correction = B.read(result_dir / 'correction_manifest.json')
    cache_root = Path('<private checkpoint storage>/auditory_alignment_v3/aln34_private_current_time_v1/cache')
    cache_checks = []
    for item in correction['items']:
        path = B.ROOT / item['source_path']
        assert B.sha(path) == item['source_record_sha256']
        rec = B.read(path)
        u = rec['unit']; previous = u.get('previous_id', u['id'])
        cache = cache_root / previous
        meta = B.read(cache / 'meta.json')
        assert meta == rec['cache_metadata']
        assert B.sha(cache / 'arrays.npz') == meta['array_sha256']
        assert meta['source_sha256'] == B.sha(B.ROOT / 'auditory_alignment_v3/aln34/private_current_time.py')
        assert meta['unit']['id'] == previous and meta['unit']['source'] == u['source']
        assert item['retained_sample_count'] == 0 and item['all_zero_input_after_keep_mask']
        cache_checks.append({'source_unit_id': item['source_unit_id'], 'cache_unit_id': previous,
                             'cache_meta_sha256': B.sha(cache / 'meta.json'), 'cache_array_sha256': meta['array_sha256']})
    result = B.read(result_dir / 'contrasts.json')
    assert result['n_families'] == 13 and result['n_contrasts'] == 40 and not result['missingness']
    assert all(v['common_complete_n'] == v['expected_n'] and not v['excluded_incomplete'] and
               not v['observed_outside_expected'] for f in result['families'] for v in f['coverage'].values())
    receipt = {'status': 'PASS', 'job': os.environ['SLURM_JOB_ID'], 'analysis_job': run_id,
               'time': datetime.now().astimezone().isoformat(), 'unchanged_source_paths': checked,
               'unchanged_normalized_observations': True, 'correction_cache_checks': cache_checks,
               'all_expected_people_cells_seeds_complete': True,
               'verifier_sha256': B.sha(__file__), 'result_sha256': B.sha(result_dir / 'contrasts.json')}
    B.write_new(result_dir / 'verification_receipt.json', receipt)
    B.write_new(B.RESULTS / 'INDEX.json', {'current_completed_analysis': str(result_dir.relative_to(B.ROOT)),
                                        'analysis_job': run_id, 'verification_job': os.environ['SLURM_JOB_ID'],
                                        'status': 'complete_and_verified', 'baseline_commit': B.BASELINE})
    for name in ('correction_manifest.json', 'affected_ids.json', 'coverage.json', 'binding_manifest.json'):
        B.write_new(B.RESULTS / name, B.read(result_dir / name))
    for name, select in (('paired_science.json', lambda f: f['family_id'].startswith('SCI35_')),
                         ('group_effects.json', lambda f: f['family_id'].startswith('S35_MAIN_'))):
        copy = {k: v for k, v in result.items() if k not in ('families', 'n_families', 'n_contrasts')}
        copy['families'] = [f for f in result['families'] if select(f)]
        copy['n_families'] = len(copy['families'])
        copy['n_contrasts'] = sum(len(f['contrasts']) for f in copy['families'])
        copy['parent_result_sha256'] = receipt['result_sha256']
        B.write_new(B.RESULTS / name, copy)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'correction_cache_checks'}), flush=True)


if __name__ == '__main__': main()
