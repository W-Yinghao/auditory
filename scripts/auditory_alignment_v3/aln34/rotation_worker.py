"""Short shared GPU allocations; immutable trainers remain unchanged."""
import argparse
import fcntl
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

from auditory_alignment_v3.aln34 import learning_budget as B

CONFIG={
 'budget':('learning_budget_v2','1044090'),
 'inner':('data_inner','1044071'),
 'curves':('data_inner','1044071'),
 'adapt':('adaptation_policy','1044099'),
 'fusion':('strong_fusion','1044111'),
 'episode':('episode_training','1044125'),
 'science':('content_time',None),
 'private':('private_current_time','1044153'),
 'breadth_budget':('breadth_budget','1044177'),
 'breadth_inner':('breadth_inner','1044177'),
 'breadth_curves':('breadth_inner','1044177'),
 'breadth_adapt':('breadth_policy','1044177'),
 'breadth_fusion':('breadth_fusion','1044177'),
 'breadth_episode':('breadth_episode','1044177'),
}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--lane',choices=CONFIG,required=True);ap.add_argument('--max-units',type=int,default=2)
    ap.add_argument('--smoke-job');a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    kind=a.lane.removeprefix('breadth_')
    name,smoke_job=CONFIG[a.lane];m=importlib.import_module('auditory_alignment_v3.aln34.'+name)
    plan=json.loads(m.PLAN.read_text());(m.verify_plan if kind=='budget' else m.verify)(plan)
    receipt=json.loads((m.BASE/'probes'/str(a.smoke_job or smoke_job)/'receipt.json').read_text())
    assert receipt['status']=='pass'
    if 'plan_sha256' in receipt:assert receipt['plan_sha256']==B.sha(m.PLAN)
    if kind=='budget':
        assert {x['architecture'] for x in receipt['units']}=={'cbramod','reve','lag_local_tokens'}
        assert {x['code_hash'] for x in receipt['units']}==set(plan['code_hashes'].values())
        if a.lane=='breadth_budget':assert {x['dataset'] for x in receipt['units']}=={'fau','federici'}
    if list((m.BASE/'units').glob('*.FAILED.json')):raise RuntimeError('lane has unresolved technical failure')
    done=0
    for r in plan['rows']:
        if kind in ('inner','curves') and (r['spec']['axis']=='inner_person')!=(kind=='inner'):continue
        eid=r.get('experiment_id',r.get('id'));output=m.BASE/'units'/f'{eid}.json'
        if output.exists():
            value=json.loads(output.read_text())
            if value.get('status')=='complete':continue
            raise RuntimeError(f'unresolved output:{eid}')
        if kind in ('adapt','fusion','episode') and not m.ready(r):continue
        lock=m.BASE/'claims'/f'{eid}.lock';lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if output.exists():continue
            print(datetime.now().astimezone().isoformat(),'START',a.lane,eid,flush=True)
            rc=subprocess.run([sys.executable,'-B','-u','-m','auditory_alignment_v3.aln34.'+name,'--unit',eid]).returncode
            value=json.loads(output.read_text()) if output.exists() else {}
            if rc or value.get('status')!='complete' or value.get('probe') or value.get('truncated'):
                B.write(m.BASE/'units'/f'{eid}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'rc':rc,'status':value.get('status')})
                raise RuntimeError(f'unit failed:{eid}')
            done+=1
        if done>=a.max_units:break
    print('ROTATION COMPLETE',a.lane,done,flush=True)

if __name__=='__main__':main()
