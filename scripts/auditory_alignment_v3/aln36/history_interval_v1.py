"""ALN3.6 R1 supplement: intervals for the ALN3.5 history-interface descriptive means (CPU, no refit).

Reads the completed per-child results of results/auditory_alignment_v3/aln35/history/run_1047305 (S, AP, J*, XM x 5 outer
folds; each of the 64 children appears once per arm). Members: EEG-B1 log-score (full_query/all_queries) and
EEG-strict twin (strict_other_block/all_queries), per arm; positive favours the EEG readout. sci_r1 identity
bootstrap-t, B = 4000, simultaneous over the 8 members with shared replicate indices (same children).
"""
import json
import os
from pathlib import Path

import numpy as np

from auditory_alignment_v3.sci_r1 import stats as S
from auditory_alignment_v3.aln36 import common as C

RUN = C.REPO / 'results/auditory_alignment_v3/aln35/history/run_1047305'
OUT = C.REPO / 'results/auditory_alignment_v3/aln36/history_interval_v1'
MEMBERS = (('full_query', 'EEG_minus_B1_logscore_bits'), ('strict_other_block', 'EEG_minus_strict_twin_logscore_bits'))


def main():
    assert os.environ.get('SLURM_JOB_ID')
    values, files = {}, {}
    for path in sorted((RUN / 'units').glob('*.json')):
        rec = C.read(path); assert rec['status'] == 'complete'
        files[path.name] = C.sha(path)
        for child, r in rec['per_participant'].items():
            for scope, key in MEMBERS:
                v = r['scopes'][scope]['all_queries'][key]
                slot = values.setdefault(f'{rec["arm"]}/{key.replace("_logscore_bits", "")}', {})
                assert child not in slot; slot[child] = v
    children = sorted(next(iter(values.values())))
    assert len(children) == 64 and all(sorted(v) == children and None not in v.values() for v in values.values())
    idx = S.draws(64, S.NB, 361021)
    items, members = {}, []
    for name in sorted(values):
        y = np.array([values[name][c] for c in children]); s = S.summary(y, idx=idx)
        items[name] = (s['est'], s['se'], s['T'])
        members.append({'name': name, 'n': 64, 'estimate': float(s['est']), 'se': float(s['se']),
                        'pointwise_95': [float(s['ci_low']), float(s['ci_high'])]})
    fam = S.family_maxt(items)
    for m in members:
        iv = fam['intervals'][m['name']]; m['simultaneous_95'] = [iv['sim_low'], iv['sim_high']]
    OUT.mkdir(parents=True, exist_ok=True)
    C.write(OUT / 'summary.json', {'version': 'ALN36_HISTORY_INTERVAL_v1', 'analysis_origin': C.ORIGIN, 'unit': 'bits/trial',
                                   'source_run': str(RUN.relative_to(C.REPO)), 'source_files_sha256': files,
                                   'method': 'sci_r1 identity bootstrap-t, B=4000, family max-|T*| over 8 members', 'critical': fam['crit'],
                                   'members': members, 'job': os.environ['SLURM_JOB_ID']})
    print(json.dumps({m['name']: [round(m['estimate'], 6), [round(x, 6) for x in m['simultaneous_95']]] for m in members}))


if __name__ == '__main__':
    main()
