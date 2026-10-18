"""Read-only CPU snapshot of independently registered ALN3.4 lanes."""
import json
import os
from pathlib import Path
from collections import Counter
from datetime import datetime
from auditory_alignment_v3.aln34 import learning_budget as B
assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'lanes':{}}
from private.auditory_alignment_v3.aln34.milestone_monitor_v11 import LANES
for name in LANES:
    plan=json.loads((base/name/'plan.json').read_text());rows=plan['rows'];states=Counter();complete=[];failed=[]
    for r in rows:
        eid=r.get('experiment_id',r.get('id'));path=base/name/'units'/f'{eid}.json'
        if path.exists():
            rec=json.loads(path.read_text());states[rec.get('status','unknown')]+=1
            if rec.get('status')=='complete':complete.append((eid,rec))
        else:states['pending']+=1
        if (base/name/'units'/f'{eid}.FAILED.json').exists():failed.append(eid)
    item={'plan_sha256':B.sha(base/name/'plan.json'),'total':len(rows),'states':dict(states),'failed':failed}
    if complete:
        eid,rec=complete[0];item['example_keys']={'id':eid,'keys':list(rec),'eval_keys':list(rec.get('eval',{})),
            'participant_metric_keys':list(next(iter(rec.get('eval',{}).get('per_participant',{}).values()),{}))}
        item['total_seconds_reported']=sum(r.get('total_seconds',r.get('seconds',0)) for _,r in complete)
    result['lanes'][name]=item
from auditory_alignment_v3.aln34 import private_calibration_device as D
plan=D.L.load_plan();pending=[]
for u in plan['units']:
    eid=u['row']['experiment_id']
    if not D.successes(eid):pending.append({'unit':eid,'recorded_device':u['recorded_device']})
result['private_loo']={'complete':len(plan['units'])-len(pending),'pending':pending}
B.write(base/'new_lanes_status.json',result)
print(json.dumps(result,indent=2))
