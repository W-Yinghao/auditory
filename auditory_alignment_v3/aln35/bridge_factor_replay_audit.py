"""Distinguish original-score CPU reduction from frozen-encoder replay drift."""
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import numpy as np
from . import bridge_factor as F
from . import bridge_factor_analyze as A
from . import science_binding as B


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077); plan = B.read(F.BASE / 'plan.json')
    item = next(e for e in plan['entries'] if e['key'] == 'dtu_AP')
    cache = Path(item['cache']); bridge = F.BR.load_bridge(item['bridge_file'])
    maximum = defaultdict(float); changed = Counter(); devices = Counter(); details = []
    for cf in (0, 1):
        meta = B.read(cache / f'target_cf{cf}_metadata.json')
        z = np.load(cache / f'target_cf{cf}.npz', allow_pickle=False); Ac = z['Ac']; old = {}
        for row in item['rows']:
            if row['content_fold'] != cf: continue
            rec = B.read(B.BASE / 'units' / (row['experiment_id'] + '.json'))
            devices[rec['device']] += 1
            for person in rec['eval']['per_participant']:
                old[person] = [rec['eval']['per_participant'][person]['unified/regular'],
                               rec['eval_uni_cal']['per_participant'][person]['unified/regular']]
        for person in meta['people']:
            i = person['array_index']; U, own = z[f'U_{i}'], z[f'own_{i}']
            for view, j in (('primary', 0), ('uni_cal', 1)):
                ro = F.BR.FrozenBridge.from_bridge(bridge, len(Ac), view)
                reference = ro.scores(U, np.empty(0), Ac, 'unified')
                fast = A.unified_scores(ro.B_uni, U, Ac, bridge.a_mu, bridge.a_sd)
                err = float(np.max(np.abs(reference - fast))); maximum['fast_vs_original_score_absolute'] = max(maximum['fast_vs_original_score_absolute'], err)
                assert np.allclose(reference, fast, rtol=1e-10, atol=1e-12)
                mr = F.query_metrics(reference, own, ro.tau['unified']); mf = F.query_metrics(fast, own, ro.tau['unified'])
                diff = {}
                for metric in ('logloss_bits', 'top1', 'mrr', 'rank_pct'):
                    computational = abs(mr[metric] - mf[metric]); maximum['fast_vs_original_formula_' + metric] = max(maximum['fast_vs_original_formula_' + metric], computational)
                    value = mr[metric] - old[person['id']][j][metric]
                    maximum['original_formula_replay_vs_archived_' + metric] = max(maximum['original_formula_replay_vs_archived_' + metric], abs(value))
                    if abs(value) > 1e-12: changed[metric] += 1
                    diff[metric] = value
                if abs(diff['rank_pct']) > 1e-12:
                    details.append({'identity': person['id'], 'content_fold': cf, 'view': view,
                                    'n_queries': len(U), 'n_candidates': len(Ac),
                                    'replay_minus_archive_using_original_formula': diff,
                                    'fast_vs_original_score_max_absolute': err})
        z.close()
    result = {'status': 'complete', 'job': os.environ['SLURM_JOB_ID'], 'key': 'dtu_AP',
              'maximum_absolute_differences': dict(maximum), 'changed_person_content_bridge_cells': dict(changed),
              'original_devices_unit_counts': dict(devices), 'new_cache_device': B.read(cache / 'complete.json')['device'],
              'rank_drift_cells': details,
              'interpretation': 'original formula on the replay cache isolates feature replay from BLAS reduction; archived query-level scores/features were not saved, so exact historical numeric cause is not identified',
              'source_code_sha256': B.sha(__file__), 'analysis_contract_sha256': B.sha(F.BASE / 'analysis_contract.json')}
    B.write_new(F.BASE / ('replay_audit_' + os.environ['SLURM_JOB_ID'] + '.json'), result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rank_drift_cells'}), flush=True)


if __name__ == '__main__': main()
