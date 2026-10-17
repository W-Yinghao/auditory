"""Bounded rotating ALN3.4 queue; squeue/sbatch only, never cancel/release holds."""
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from private.auditory_alignment_v3.aln34 import priority_schedule as Priority

ROOT=Path('/home/infres/yinwang/EEG_auditory');OUT=ROOT/'private/auditory_alignment_v3';BASE=OUT/'aln34'
CONFIG={
 'budget':('c3_aln34budget','learning_budget_v2','1044090',1,()),
 'inner':('c3_inner34','data_inner_v1','1044071',1,('1044075',)),
 'curves':('c3_datacurve34','data_inner_v1','1044071',1,('1044076',)),
 'adapt':('c3_aln34adapt','adaptation_policy_v1','1044099',1,()),
 'fusion':('c3_aln34fusion','strong_fusion_v1','1044111',1,()),
 'episode':('c3_aln34episode','episode_training_v1','1044125',1,()),
 'science':('c3_aln34science','content_time_v1',None,1,()),
 'private':('c3_privscience','private_current_time_v1','1044153',1,()),
 'private_episode':('c3_privepisode','private_episode_v2',None,1,()),
 'cb_auditory':('c3_cbauditory','cb_auditory_v1','1044234',1,()),
 'attention':('c3_attntransfer','attention_transfer_v1','1044250',1,()),
 'private_factorial':('c3_privcbfactor','private_cb_factorial_v1','1044280',1,()),
 'prior_loo':('c3_priorloo','prior_private_loo_v1',None,1,()),
 'prior_science':('c3_priorscience','prior_science_v1',None,1,()),
 'cs_episode':('c3_csepisode','cs_episode_v1',None,1,()),
}

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def log(s):print(datetime.now().astimezone().isoformat(),s,flush=True)
def jobs():
    return [dict(zip(('id','name','qos','state'),s.split('|'))) for s in subprocess.check_output(
        ['squeue','-u',os.environ['USER'],'-h','-o','%i|%j|%q|%T'],text=True).splitlines()]
def submit(cmd):
    jid=subprocess.check_output(['sbatch','--parsable',*cmd],text=True).strip();log(f'SUBMIT {jid}: {cmd}')
    with (OUT/'logs/operations.log').open('a') as f:f.write(f'{datetime.now().astimezone().isoformat()} fleet v14 {os.environ["SLURM_JOB_ID"]} submitted {jid}: {cmd}\n')
    return jid

def seconds_left(value):
    if value in ('UNLIMITED','NOT_SET','N/A'):return None
    days,clock=value.split('-',1) if '-' in value else ('0',value)
    parts=[int(x) for x in clock.split(':')]
    if len(parts)==2:parts.insert(0,0)
    if len(parts)!=3:raise ValueError('unrecognized Slurm time-left '+value)
    h,m,s=parts
    return int(days)*86400+h*3600+m*60+s

def renew_offload(jj):
    # Renew only this exact service, near actual expiry, using its reviewed
    # stop-between-files/lock handoff. No GPU job or other project is touched.
    if (OUT/'STOP_ckpt_offload').exists():return False
    own=[j for j in jj if j['name']=='c3_ckptoff']
    if len(own)!=1 or own[0]['state']!='RUNNING':return False
    if sum(j['qos']=='normal' for j in jj)>27:return False
    old=own[0]['id']
    value=subprocess.check_output(['squeue','-j',old,'-h','-o','%L'],text=True).strip()
    if not value:return False
    remaining=seconds_left(value)
    if remaining is not None and 0<remaining<=3600:
        submit(['slurm/aln34_offload_handoff.sbatch',old]);return True
    return False

def source_ready(row, dirname='data_inner_v1'):
    eid=row['experiment_id'];root=BASE/dirname;p=root/'units'/f'{eid}.json'
    if not p.is_file() or not (root/'ckpt'/f'{eid}_best.pt').is_file():return False
    r=read(p);return r.get('status')=='complete' and not r.get('truncated')

def lane(key,overrides):
    kind=key.removeprefix('breadth_');inner_dir='breadth_inner_v1' if key.startswith('breadth_') else 'data_inner_v1'
    name,dirname,smokejob,slots,initial=CONFIG[key];base=BASE/dirname;pp=base/'plan.json'
    item={'name':name,'lane':key,'slots':slots,'initial':list(initial),'ready':0,'state':'unregistered','remaining':None,'failed':0}
    if not pp.exists():return item
    plan=read(pp);rows=plan['rows']
    if kind in ('inner','curves'):rows=[r for r in rows if (r['spec']['axis']=='inner_person')==(kind=='inner')]
    completed={p.stem for p in (base/'units').glob('*.json') if not p.name.endswith('.FAILED.json') and read(p).get('status')=='complete'}
    remaining=[r for r in rows if r.get('experiment_id',r.get('id')) not in completed]
    item.update(total=len(rows),remaining=len(remaining),failed=len(list((base/'units').glob('*.FAILED.json'))))
    if item['failed']:item['state']='technical_failure';return item
    smokejob=overrides.get(key,smokejob);receiptpath=base/'probes'/str(smokejob)/'receipt.json'
    if not receiptpath.exists():item['state']='waiting_engineering_receipt';return item
    receipt=read(receiptpath)
    if receipt['status']!='pass':item['state']='engineering_'+receipt['status'];return item
    if 'plan_sha256' in receipt and receipt['plan_sha256']!=sha(pp):item['state']='engineering_plan_mismatch';return item
    if kind=='budget' and {u['code_hash'] for u in receipt['units']}!=set(plan['code_hashes'].values()):
        item['state']='engineering_code_mismatch';return item
    if kind=='adapt':remaining=[r for r in remaining if source_ready(r['inner_source'],inner_dir)]
    if kind=='fusion':remaining=[r for r in remaining if all(source_ready(v['inner'],inner_dir) for v in r['models'].values())]
    if kind=='episode':remaining=[r for r in remaining if source_ready(r['inner'],inner_dir)]
    if key=='attention':
        remaining=[r for r in remaining if source_ready(r['inner'],'data_inner_v1' if r['source']['row']['dataset']=='dtu' else 'breadth_inner_v1')]
    if key=='cs_episode':
        remaining=[r for r in remaining if source_ready(r['inner'],'data_inner_v1' if r['dataset']=='dtu' else 'breadth_inner_v1')]
    if key=='cb_auditory':
        eligible=[]
        for row in remaining:
            if row.get('kind')=='donor':eligible.append(row);continue
            p=base/'units'/f'{row["spec"]["donor_id"]}.json'
            if p.exists():
                d=read(p)
                if d.get('status')=='complete' and not d.get('probe') and Path(d['final_checkpoint']).is_file():eligible.append(row)
        remaining=eligible
    if key in ('prior_loo','prior_science'):
        eligible=[]
        for planned in remaining:
            row=planned['source'] if key=='prior_science' else planned
            p=OUT/'units'/f'{row["experiment_id"]}.json';c=OUT/'ckpt'/f'{row["experiment_id"]}_best.pt'
            if p.is_file() and c.is_file():
                rec=read(p)
                if rec.get('status')=='complete' and not rec.get('truncated') and rec.get('row')==row:eligible.append(planned)
        remaining=eligible
    item.update(state='ready',ready=len(remaining),submit=['--job-name='+name,'slurm/aln34_priority_rotation.sbatch','--lane',key,'--max-units',str(Priority.max_units(key)),'--smoke-job',str(smokejob)])
    if key=='private_episode':
        item['submit']=['--job-name='+name,'slurm/aln34_private_episode_v2.sbatch','--max-units','2','--smoke-job',str(smokejob)]
    if key=='cb_auditory':
        item['submit']=['--job-name='+name,'slurm/aln34_cb_auditory.sbatch','--max-units','1','--smoke-job',str(smokejob)]
    if key=='attention':
        item['submit']=['--job-name='+name,'slurm/aln34_attention_transfer.sbatch','--max-units','2','--smoke-job',str(smokejob)]
    if key=='private_factorial':
        item['submit']=['--job-name='+name,'slurm/aln34_private_cb_factorial.sbatch','--max-units','2','--smoke-job',str(smokejob)]
    if key=='prior_loo':
        item['submit']=['--job-name='+name,'slurm/aln34_prior_private_loo.sbatch','--max-units','8','--smoke-job',str(smokejob)]
    if key=='prior_science':
        item['submit']=['--job-name='+name,'slurm/aln34_prior_science.sbatch','--max-units','8','--smoke-job',str(smokejob)]
    if key=='cs_episode':
        item['submit']=['--job-name='+name,'slurm/aln34_cs_episode.sbatch','--max-units','2','--smoke-job',str(smokejob)]
    return item

def main():
    assert os.environ.get('SLURM_JOB_ID');os.chdir(ROOT);os.umask(0o077)
    lock=(BASE/'.fleet_maintenance.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (OUT/'STOP_queue_v3_fm').exists()
    log('START v14: prior science/readout plus attention/CB auditory/private episode/breadth; bounded GPU rotations; prior keeper max4; global10GPU cap')
    turn=0
    while not (BASE/'STOP_fleet_maintenance_v14').exists():
        try:
            jj=jobs();project=[j for j in jj if j['qos']=='runfill' and j['name'].startswith('c3_')]
            renew_offload(jj)
            assert sum(j['state']=='RUNNING' for j in project)<=10,'GPU cap exceeded'
            pending=sum(j['state']=='PENDING' for j in project)
            overridepath=BASE/'fleet_smoke_jobs.json';overrides=read(overridepath) if overridepath.exists() else {}
            runtimepath=BASE/'fleet_runtime.json';runtime=read(runtimepath) if runtimepath.exists() else {}
            fm_slots=int(runtime.get('legacy_fm_slots',2));assert 1<=fm_slots<=3
            for key,value in runtime.get('extra_lanes',{}).items():
                assert key.startswith('breadth_') and len(value)==5
                assert value[0].startswith('c3_') and '/' not in value[1] and 1<=int(value[3])<=2
                CONFIG[key]=tuple(value)
            keys=list(CONFIG);keys=keys[turn%len(keys):]+keys[:turn%len(keys)];turn+=1
            lanes=[lane(k,overrides) for k in sorted(keys,key=lambda k:Priority.rank(k,keys.index(k)))]
            fm=OUT/'queue_v3_fm.txt';ids=[x.split('|')[0] for x in fm.read_text().splitlines() if x.strip()]
            ready=[e for e in ids if not (OUT/'units'/f'{e}.json').exists() and not (OUT/'pool/queue_v3_fm'/f'{e}.failed').exists() and not (OUT/'pool/queue_v3_fm'/f'{e}.claim').exists()]
            lanes.insert(0,{'name':'c3_aln3fm','state':'ready','ready':len(ready),'slots':fm_slots,'initial':[],
                          'submit':['--job-name=c3_aln3fm','--nice=0','slurm/aln3_gpu_pool.sbatch',str(fm),'1','1']})
            for item in lanes:
                active=[j for j in jj if j['name']==item['name'] or j['id'] in item.get('initial',[])];item['jobs']=active
                if item['state']=='ready' and item['ready'] and len(active)<item['slots'] and pending<12:
                    command=item['submit'] if item['name']=='c3_aln3fm' else ['--nice='+str(Priority.nice(item['lane'])),*item['submit']]
                    jid=submit(command);pending+=1;jj.append({'id':jid,'name':item['name'],'qos':'runfill','state':'PENDING'})
            value={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'source_sha256':sha(__file__),'project_gpu_jobs':project,'lanes':lanes}
            tmp=BASE/'fleet_status.json.tmp';tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(tmp,BASE/'fleet_status.json')
            log('HEARTBEAT '+json.dumps({x['name']:{k:x.get(k) for k in ('state','ready','remaining','failed')} for x in lanes}))
        except Exception as exc:log('ERROR '+repr(exc))
        time.sleep(60)

if __name__=='__main__':main()
