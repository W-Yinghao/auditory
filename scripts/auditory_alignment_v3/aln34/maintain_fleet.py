"""Keep authorized, ready ALN3.4 work queued. Never cancel jobs or release holds.

This CPU coordinator supplements the four-worker public-prior keeper. It uses
squeue/sbatch only, immutable source plans, passing engineering receipts, and
exact project job names. Scientific failures are reported and stop that lane.
"""
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/home/infres/yinwang/EEG_auditory')
OUT = ROOT/'private/auditory_alignment_v3'
BASE = OUT/'aln34'


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jobs():
    lines = subprocess.check_output(['squeue','-u',os.environ['USER'],'-h','-o','%i|%j|%q|%T'],text=True).splitlines()
    return [dict(zip(('id','name','qos','state'),line.split('|'))) for line in lines]


def log(message):
    print(f'{datetime.now().astimezone().isoformat()} {message}',flush=True)


def submit(command):
    jid = subprocess.check_output(['sbatch','--parsable',*command],text=True).strip()
    log(f'SUBMIT {jid}: {command}')
    with (OUT/'logs/operations.log').open('a') as f:
        f.write(f'{datetime.now().astimezone().isoformat()} fleet coordinator {os.environ["SLURM_JOB_ID"]} submitted {jid}: {command}\n')
    return jid


def lane(name, base, smoke, script, args, slots=1, initial=(), predicate=None):
    planpath=base/'plan.json'
    if not planpath.exists():
        return {'name':name,'state':'no_registered_plan','ready':0}
    plan=read(planpath)
    rows=[r for r in plan['rows'] if predicate is None or predicate(r)]
    results=base/'units'
    failed=list(results.glob('*.FAILED.json'))
    completed={p.stem for p in results.glob('*.json') if not p.name.endswith('.FAILED.json')}
    unfinished=[r for r in rows if r['experiment_id'] not in completed]
    state='ready'
    if failed:
        state='technical_failure'
    elif not smoke.is_file():
        state='waiting_engineering_receipt'
    else:
        receipt=read(smoke)
        if receipt['status']!='pass':
            state='engineering_'+receipt['status']
        elif 'plan_sha256' in receipt and receipt['plan_sha256'] != sha(planpath):
            state='engineering_plan_mismatch'
    return {'name':name,'state':state,'ready':len(unfinished) if state=='ready' else 0,
            'remaining':len(unfinished),'total':len(rows),'failed':len(failed),'slots':slots,'initial':list(initial),
            'submit':['--job-name='+name,script,*args]}


def main():
    assert os.environ.get('SLURM_JOB_ID'),'CPU Slurm job required'
    os.chdir(ROOT);os.umask(0o077)
    lock=(BASE/'.fleet_maintenance.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    # The old FM keeper has explicitly stopped; its STOP marker stays as evidence.
    assert (OUT/'STOP_queue_v3_fm').exists()
    log('START: max 3 FM, max 2 budget, one inner and one data worker; prior keeper retains max 4')
    while not (BASE/'STOP_fleet_maintenance').exists():
        try:
            jj=jobs()
            project=[j for j in jj if j['name'].startswith('c3_') and j['qos']=='runfill']
            assert sum(j['state']=='RUNNING' for j in project)<=10,'project GPU cap exceeded'
            pending=sum(j['state']=='PENDING' for j in project)
            budget=BASE/'learning_budget_v2'
            split=BASE/'data_inner_v1'
            lanes=[lane('c3_aln34budget',budget,budget/'probes/1044090/receipt.json','slurm/aln34_learning_budget_v2.sbatch',[],2),
                   lane('c3_inner34',split,split/'probes/1044071/receipt.json','slurm/aln34_data_inner.sbatch',
                        ['--lane','inner','--smoke-receipt',str(split/'probes/1044071/receipt.json')],initial=('1044075',),
                        predicate=lambda r:r['spec']['axis']=='inner_person'),
                   lane('c3_datacurve34',split,split/'probes/1044071/receipt.json','slurm/aln34_data_inner.sbatch',
                        ['--lane','curves','--smoke-receipt',str(split/'probes/1044071/receipt.json')],initial=('1044076',),
                        predicate=lambda r:r['spec']['axis']!='inner_person')]
            # New D is submitted only when an actual independent inner checkpoint exists.
            ad=BASE/'adaptation_policy_v1'
            apath,smoke=ad/'plan.json',ad/'probes/1044099/receipt.json'
            if apath.exists():
                ap=read(apath)
                ready=[]
                for r in ap['rows']:
                    iid=r['inner_source']['experiment_id']
                    ip=split/'units'/f'{iid}.json'
                    if ip.is_file() and (split/'ckpt'/f'{iid}_best.pt').is_file() and not (ad/'units'/f'{r["id"]}.json').exists():
                        ir=read(ip)
                        if ir['status']=='complete' and not ir.get('truncated'):
                            ready.append(r['id'])
                good=smoke.exists() and read(smoke).get('status')=='pass' and read(smoke).get('plan_sha256')==sha(apath)
                failure_logs=[]
                for lp in (OUT/'logs').glob('c3_aln34adapt-*.log'):
                    with lp.open('rb') as handle:
                        handle.seek(max(0,lp.stat().st_size-16384))
                        if b'Traceback (most recent call last)' in handle.read():
                            failure_logs.append(str(lp))
                state='technical_failure' if failure_logs else ('ready' if good else 'waiting_engineering_receipt')
                lanes.append({'name':'c3_aln34adapt','state':state,'failure_logs':failure_logs,
                              'ready':len(ready) if state=='ready' else 0,'slots':1,'initial':[],
                              'submit':['--job-name=c3_aln34adapt','slurm/aln34_adaptation_policy.sbatch','--smoke-receipt',str(smoke)]})
            # The existing FM plan and per-unit holds are untouched.
            fm=OUT/'queue_v3_fm.txt'
            ids=[line.split('|')[0] for line in fm.read_text().splitlines() if line.strip()]
            ready_fm=[e for e in ids if not (OUT/'units'/f'{e}.json').exists()
                      and not (OUT/'pool/queue_v3_fm'/f'{e}.failed').exists()
                      and not (OUT/'pool/queue_v3_fm'/f'{e}.claim').exists()]
            lanes.append({'name':'c3_aln3fm','state':'ready','ready':len(ready_fm),'slots':3,'initial':[],
                          'submit':['--job-name=c3_aln3fm','slurm/aln3_gpu_pool.sbatch',str(fm),'1','1']})
            for item in lanes:
                active=[j for j in jj if j['name']==item['name'] or j['id'] in item.get('initial',[])]
                item['jobs']=active
                # At most one new submission per pass; keep queue bounded and avoid races.
                if item['state']=='ready' and item['ready'] and len(active)<item['slots'] and pending<12:
                    jid=submit(item['submit']);pending+=1
                    jj.append({'id':jid,'name':item['name'],'qos':'runfill','state':'PENDING'})
                    break
            status={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],
                    'project_gpu_jobs':project,'lanes':lanes,'source_sha256':sha(__file__)}
            tmp=BASE/'fleet_status.json.tmp';tmp.write_text(json.dumps(status,indent=2)+'\n');os.replace(tmp,BASE/'fleet_status.json')
            log('HEARTBEAT '+json.dumps({x['name']:{k:x.get(k) for k in ('state','ready','remaining','failed')} for x in lanes}))
        except Exception as ex:
            log('ERROR '+repr(ex))
        time.sleep(60)


if __name__=='__main__':main()
