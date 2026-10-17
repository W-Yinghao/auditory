"""Bounded rotating ALN3.4 queue; squeue/sbatch only, never cancel/release holds."""
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path('/home/infres/yinwang/EEG_auditory');OUT=ROOT/'private/auditory_alignment_v3';BASE=OUT/'aln34'
CONFIG={
 'budget':('c3_aln34budget','learning_budget_v2','1044090',2,()),
 'inner':('c3_inner34','data_inner_v1','1044071',1,('1044075',)),
 'curves':('c3_datacurve34','data_inner_v1','1044071',1,('1044076',)),
 'adapt':('c3_aln34adapt','adaptation_policy_v1','1044099',1,()),
 'fusion':('c3_aln34fusion','strong_fusion_v1','1044111',1,()),
 'episode':('c3_aln34episode','episode_training_v1','1044125',1,()),
 'science':('c3_aln34science','content_time_v1',None,1,()),
 'private':('c3_privscience','private_current_time_v1','1044153',1,()),
}

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def log(s):print(datetime.now().astimezone().isoformat(),s,flush=True)
def jobs():
    return [dict(zip(('id','name','qos','state'),s.split('|'))) for s in subprocess.check_output(
        ['squeue','-u',os.environ['USER'],'-h','-o','%i|%j|%q|%T'],text=True).splitlines()]
def submit(cmd):
    jid=subprocess.check_output(['sbatch','--parsable',*cmd],text=True).strip();log(f'SUBMIT {jid}: {cmd}')
    with (OUT/'logs/operations.log').open('a') as f:f.write(f'{datetime.now().astimezone().isoformat()} fleet v2 {os.environ["SLURM_JOB_ID"]} submitted {jid}: {cmd}\n')
    return jid

def source_ready(row):
    eid=row['experiment_id'];root=BASE/'data_inner_v1';p=root/'units'/f'{eid}.json'
    if not p.is_file() or not (root/'ckpt'/f'{eid}_best.pt').is_file():return False
    r=read(p);return r.get('status')=='complete' and not r.get('truncated')

def lane(key,overrides):
    name,dirname,smokejob,slots,initial=CONFIG[key];base=BASE/dirname;pp=base/'plan.json'
    item={'name':name,'lane':key,'slots':slots,'initial':list(initial),'ready':0,'state':'unregistered','remaining':None,'failed':0}
    if not pp.exists():return item
    plan=read(pp);rows=plan['rows']
    if key in ('inner','curves'):rows=[r for r in rows if (r['spec']['axis']=='inner_person')==(key=='inner')]
    completed={p.stem for p in (base/'units').glob('*.json') if not p.name.endswith('.FAILED.json') and read(p).get('status')=='complete'}
    remaining=[r for r in rows if r.get('experiment_id',r.get('id')) not in completed]
    item.update(total=len(rows),remaining=len(remaining),failed=len(list((base/'units').glob('*.FAILED.json'))))
    if item['failed']:item['state']='technical_failure';return item
    smokejob=overrides.get(key,smokejob);receiptpath=base/'probes'/str(smokejob)/'receipt.json'
    if not receiptpath.exists():item['state']='waiting_engineering_receipt';return item
    receipt=read(receiptpath)
    if receipt['status']!='pass':item['state']='engineering_'+receipt['status'];return item
    if 'plan_sha256' in receipt and receipt['plan_sha256']!=sha(pp):item['state']='engineering_plan_mismatch';return item
    if key=='budget' and {u['code_hash'] for u in receipt['units']}!=set(plan['code_hashes'].values()):
        item['state']='engineering_code_mismatch';return item
    if key=='adapt':remaining=[r for r in remaining if source_ready(r['inner_source'])]
    if key=='fusion':remaining=[r for r in remaining if all(source_ready(v['inner']) for v in r['models'].values())]
    if key=='episode':remaining=[r for r in remaining if source_ready(r['inner'])]
    item.update(state='ready',ready=len(remaining),submit=['--job-name='+name,'slurm/aln34_rotation.sbatch','--lane',key,'--max-units','2','--smoke-job',str(smokejob)])
    return item

def main():
    assert os.environ.get('SLURM_JOB_ID');os.chdir(ROOT);os.umask(0o077)
    lock=(BASE/'.fleet_maintenance.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (OUT/'STOP_queue_v3_fm').exists()
    log('START v3: includes private science; max3 legacy FM; short2-unit GPU rotations; prior keeper max4; global10GPU cap')
    turn=0
    while not (BASE/'STOP_fleet_maintenance_v3').exists():
        try:
            jj=jobs();project=[j for j in jj if j['qos']=='runfill' and j['name'].startswith('c3_')]
            assert sum(j['state']=='RUNNING' for j in project)<=10,'GPU cap exceeded'
            pending=sum(j['state']=='PENDING' for j in project)
            overridepath=BASE/'fleet_smoke_jobs.json';overrides=read(overridepath) if overridepath.exists() else {}
            keys=list(CONFIG);keys=keys[turn%len(keys):]+keys[:turn%len(keys)];turn+=1
            lanes=[lane(k,overrides) for k in keys]
            fm=OUT/'queue_v3_fm.txt';ids=[x.split('|')[0] for x in fm.read_text().splitlines() if x.strip()]
            ready=[e for e in ids if not (OUT/'units'/f'{e}.json').exists() and not (OUT/'pool/queue_v3_fm'/f'{e}.failed').exists() and not (OUT/'pool/queue_v3_fm'/f'{e}.claim').exists()]
            lanes.append({'name':'c3_aln3fm','state':'ready','ready':len(ready),'slots':3,'initial':[],
                          'submit':['--job-name=c3_aln3fm','slurm/aln3_gpu_pool.sbatch',str(fm),'1','1']})
            for item in lanes:
                active=[j for j in jj if j['name']==item['name'] or j['id'] in item.get('initial',[])];item['jobs']=active
                if item['state']=='ready' and item['ready'] and len(active)<item['slots'] and pending<12:
                    jid=submit(item['submit']);pending+=1;jj.append({'id':jid,'name':item['name'],'qos':'runfill','state':'PENDING'});break
            value={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'source_sha256':sha(__file__),'project_gpu_jobs':project,'lanes':lanes}
            tmp=BASE/'fleet_status.json.tmp';tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(tmp,BASE/'fleet_status.json')
            log('HEARTBEAT '+json.dumps({x['name']:{k:x.get(k) for k in ('state','ready','remaining','failed')} for x in lanes}))
        except Exception as exc:log('ERROR '+repr(exc))
        time.sleep(60)

if __name__=='__main__':main()
