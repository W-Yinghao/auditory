"""SCI35-C01: append-only actual-batch audit of native private pre access."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import numpy as np
import torch

from . import science_binding as B


def input_audit(row, kid, fm=False):
    from auditory_alignment_v2.train import PrivateBatcher
    from auditory_alignment_v2.train_fm import PrivateFMBatcher
    from auditory_alignment_v3.aln34.private_current_time import mask_patches
    b = B.core.bind(row)
    if row['family_id'] == 'E_PUBLIC_TRANSFER':
        b['spec'].update(architecture='lag_local_tokens', window='full')
    # The actual production batcher, on two real retained epochs; no model or
    # fictitious EEG. Sampling fewer rows does not change input coordinates.
    n = len(kid['y'])
    small = {k: (v[:2] if isinstance(v, np.ndarray) and v.ndim and len(v) == n else v)
             for k, v in kid.items()}
    batcher = (PrivateFMBatcher if fm else PrivateBatcher)([small], b['spec'], b, torch.device('cpu'))
    patches = batcher.patches(0, torch.arange(2))
    masked = mask_patches(patches, batcher, (-200, 0))
    resolved = [[a + batcher.lo, c + batcher.lo] for a, c in batcher.W]
    retained = sum(max(0, min(c, 50) - max(a, 0)) for a, c in resolved)
    result = {'bt_lo': batcher.lo, 'bt_hi': batcher.hi, 'bt_W': [list(w) for w in batcher.W],
              'resolved_input_samples': resolved, 'requested_mask_samples': [0, 50],
              'interval_semantics': 'half_open_original_epoch_250Hz_onset_sample50',
              'retained_sample_count': retained,
              'effective_access_ms': [[(a - 50) * 4, (c - 50) * 4] for a, c in resolved],
              'actual_batch_shape': [list(x.shape) for x in patches],
              'actual_batch_input_nonzero': [int(torch.count_nonzero(x)) for x in patches],
              'actual_batch_after_keep_nonzero': [int(torch.count_nonzero(x)) for x in masked],
              'all_zero_input_after_keep_mask': all(not torch.count_nonzero(x).item() for x in masked),
              'actual_values_inspected': True, 'sampled_identity': kid['id'], 'sampled_retained_rows': [0, 1]}
    if fm:
        assert retained == 50
    else:
        assert retained == 0 and result['all_zero_input_after_keep_mask']
    return result


def run(binding, result_dir):
    from auditory_alignment_v3.aln34 import private_current_time as P, private_current_time_v2 as P2
    code = {str(p.relative_to(B.ROOT)): B.sha(p) for p in (
        B.ROOT / 'auditory_alignment/model.py', B.ROOT / 'auditory_alignment_v2/temporal.py',
        B.ROOT / 'auditory_alignment_v2/train.py', B.ROOT / 'auditory_alignment_v2/train_fm.py',
        Path(P.__file__), Path(P2.__file__), Path(__file__))}
    cache = {}
    items = []
    unaffected = []
    planned = Counter()
    for lane, module in (('private_current_time_v1', P), ('private_current_time_v2', P2)):
        plan = B.read(module.PLAN)
        module.verify(plan)
        for unit in plan['rows']:
            row = unit['source']; s = row['spec']
            hit = row['family_id'] in ('E_LOCAL', 'E_PUBLIC_TRANSFER') and (
                s.get('architecture') == 'lag_local_tokens' or s.get('source_architecture') == 'lag_local_tokens')
            if not hit:
                unaffected.append({'lane': lane, 'id': unit['id'], 'reason': 'FM input has actual pre samples'})
                continue
            planned[lane] += 1
            cfg = (row['family_id'], s.get('architecture'), s.get('source_architecture'), s.get('window', 'full'))
            if cfg not in cache:
                cache[cfg] = input_audit(row, binding.kids[0])
            path = module.BASE / 'units' / (unit['id'] + '.json')
            if not path.exists(): continue
            rec = B.read(path)
            assert rec['status'] == 'complete' and not rec.get('probe') and rec['unit'] == unit
            assert rec['plan_sha256'] == B.sha(module.PLAN)
            binding.source(row, unit['record_sha256'])
            affected = {}
            for identity, v in rec['per_participant'].items():
                paths = ['per_participant/' + identity + '/windows/pre']
                assert 'pre' in v['windows']
                tg = [key for key in v['temporal_generalization'] if 'pre' in key.split('/')]
                assert len(tg) == 7
                paths.extend('per_participant/' + identity + '/temporal_generalization/' + key for key in tg)
                affected[identity] = {'metric_paths': paths, 'original_pre_values': v['windows']['pre'],
                                      'tg_cells': tg, 'tg_calibrations': ['original_calibration', 'source_only_destination_calibration']}
            items.append({'correction_id': 'SCI35-C01', 'source_commit': B.BASELINE,
                          'source_unit_id': unit['id'], 'upstream_source_unit_id': row['experiment_id'],
                          'source_path': str(path.relative_to(B.ROOT)), 'source_record_sha256': B.sha(path),
                          'source_plan_sha256': B.sha(module.PLAN), 'dataset': row['dataset'],
                          'upstream_family_id': row['family_id'], 'objective': s['objective'],
                          'architecture': 'lag_local_tokens', 'seed': row['seed'], 'subject_fold': row['subject_fold'],
                          'condition': 'pre_and_incident_temporal_generalization', 'original_label': 'pre',
                          **cache[cfg], 'affected_metric_paths': affected,
                          'valid_for_pre_event_inference': False,
                          'unaffected_conditions': ['0_200', '200_400', '400_600', 'full_poststimulus', 'adaptation',
                                                   'full_window_development', 'FM_real_pre', 'public_science', 'prior_science'],
                          'action': 'all_zero_input_control_no_pre_access; exclude only from actual pre-event inference',
                          'execution_version': rec.get('execution_version', 'ALN34_PRIVATE_CURRENT_TIME_v1'),
                          'reused_from': rec.get('reused_from'), 'checked_at': datetime.now().astimezone().isoformat()})
    fmrow = next(r for r in binding.rows if r['family_id'] == 'E_GENERIC' and r['spec'].get('architecture') == 'cbramod')
    fm = input_audit(fmrow, binding.kids[0], fm=True)
    value = {'correction_id': 'SCI35-C01', 'status': 'complete', 'original_outputs_unchanged': True,
             'actual_batch_checks': list(cache.values()), 'unaffected_FM_positive_access_check': fm,
             'planned_affected_by_lane': dict(planned), 'existing_affected_by_lane': dict(Counter(
                 'private_current_time_v2' if i['execution_version'].endswith('_v2') else 'private_current_time_v1' for i in items)),
             'items': items, 'code_sha256': code,
             'unaffected_registered_records': unaffected,
             'interpretation': 'All-zero local pre is an input-control condition. AUC sorting noise is not physiological pre evidence.'}
    B.write_new(result_dir / 'correction_manifest.json', value)
    B.write_new(result_dir / 'affected_ids.json', {'correction_id': 'SCI35-C01', 'ids': [x['source_unit_id'] for x in items]})
    return value
