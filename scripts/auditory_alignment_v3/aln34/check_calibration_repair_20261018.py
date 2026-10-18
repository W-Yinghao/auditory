"""Slurm integration: replay training windows, check exact reuse and new routing."""
import json
import os
import numpy as np
from auditory_alignment import data
from auditory_alignment_v3.aln34 import private_current_time_v2 as V2
from private.auditory_alignment_v3.aln34 import maintain_fleet_v16 as F
from private.auditory_alignment_v3.aln34 import efficiency_loop_v2 as E
from private.auditory_alignment_v3.aln34 import milestone_monitor_v11 as M

assert os.environ.get('SLURM_JOB_ID')
plan = json.loads(V2.PLAN.read_text()); V2.verify(plan)
assert len(plan['rows']) == len({u['id'] for u in plan['rows']}) == 130
assert 'private_current_time_v2' in M.LANES and 'private_current_time_v1' not in M.LANES
reused = 0
for u in plan['rows']:
    path = V2.BASE/'units'/f'{u["id"]}.json'
    if not path.exists(): continue
    rec = json.loads(path.read_text()); source = rec['reused_from']
    old = json.loads(open(source['path']).read())
    assert V2.B.sha(source['path']) == source['sha256']
    assert rec['per_participant'] == old['per_participant'] and rec['fits'] == old['fits']
    reused += 1
assert reused == 26
u = next(u for u in plan['rows'] if u['previous_id'] == 'ALN34P_5551c74e7a9b79f8')
kids = data.load_private(); fd = V2.V1.P.Fold(kids, u['source']['subject_fold'])
V2.C.FIT_EVENTS.clear()
with np.load(V2.V1.STORE/'cache'/u['previous_id']/'arrays.npz', allow_pickle=False) as z:
    for window in V2.V1.WINDOWS:
        x = fd.es_rows({i: z[f'{window}_{i}'] for i in fd.tr})
        V2.Probe(x, fd.y_es)
assert sum(e['fallback'] for e in V2.C.FIT_EVENTS) == 1
item = F.lane('private', {})
assert item['total'] == 130 and item['remaining'] == 104 and item['state'] == 'waiting_engineering_receipt'
jobs = E.query_jobs(); assert E.gpu_count(jobs) <= 10
result = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'reused': reused,
          'plan_sha256': V2.B.sha(V2.PLAN), 'fallbacks': V2.C.FIT_EVENTS,
          'gpu_running': E.gpu_count(jobs), 'private_lane': item}
V2.B.write(V2.BASE.parent/'runtime_check_20261018'/'calibration_repair_preflight.json', result)
print(json.dumps(result), flush=True)
