"""Freeze the repair plan and explicitly reuse compatible completed NCE results."""
import copy
import os
from auditory_alignment_v3.aln34 import private_episode as V1, private_episode_v2 as V2
assert os.environ.get('SLURM_JOB_ID')
V1.verify(V1.read(V1.PLAN))
V2.make_plan()
old=V1.read(V1.PLAN);new=V2.read(V2.PLAN);reused=[]
lookup={u['source']['experiment_id']:u for u in new['rows']}
for unit in old['rows']:
    path=V1.BASE/'units'/f"{unit['id']}.json"
    if not path.exists():continue
    rec=V1.read(path)
    if rec.get('status')!='complete' or rec.get('probe') or unit['source']['spec']['objective']!='NCE':continue
    fresh=lookup[unit['source']['experiment_id']]
    assert {k:v for k,v in unit.items() if k not in ('id','design_sha256')}=={k:v for k,v in fresh.items() if k not in ('id','design_sha256')}
    target=V2.BASE/'units'/f"{fresh['id']}.json"
    value=copy.deepcopy(rec)
    value.update(id=fresh['id'],unit=fresh,plan_sha256=V2.B.sha(V2.PLAN),execution_version='v1_compatible_reuse',
        reused_from={'id':unit['id'],'record':str(path),'record_sha256':V2.B.sha(path),
                     'plan_sha256':rec['plan_sha256'],'source_sha256':rec['source_sha256'],
                     'reason':'NCE arithmetic unchanged; only deterministic support availability metadata added',
                     'receipt_job':os.environ['SLURM_JOB_ID']})
    for stage in value['stages'].values():
        for regime in stage['values'].values():
            for candidates in regime['candidates'].values():
                for step,candidate in candidates.items():
                    for v in candidate['per_participant'].values():
                        if v['status']=='complete':v.update(V2.support_policy('NCE',v['n_support_trials'],int(step)))
    # Regenerate selected references from unchanged inner risks/outer predictions.
    value['choices']=V2.choose(value['stages']['inner']['values'],value['stages']['outer']['values'])
    if target.exists():assert V2.read(target)==value
    else:V2.B.write(target,value)
    reused.append(value['reused_from'])
V2.B.write(V2.BASE/'compatibility_reuse.json',{'job':os.environ['SLURM_JOB_ID'],'plan_sha256':V2.B.sha(V2.PLAN),'records':reused})
print({'reused':len(reused),'remaining':len(new['rows'])-len(reused),'plan_sha256':V2.B.sha(V2.PLAN)},flush=True)
