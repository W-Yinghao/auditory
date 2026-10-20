"""S35_CBAUD_PEOPLE: auditory-continued vs direct CBraMod start at 0.25/0.5 source people (DTU, 3401).

New units copy the completed ALN3.4 data-curve rows (cbramod/pretrained_full, people axis) and change only
the starting backbone to the generic_paired donor's final state. The frozen data_inner split/evaluation
instrumentation and the cb_auditory donor loader are composed unchanged around run_aligned32.run.
See docs/auditory_alignment_v3/aln35/CBAUD_PEOPLE_DESIGN.md.
"""
from __future__ import annotations
import argparse
import contextlib
import copy
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

from .. import core
from ..aln34 import data_inner as I, learning_budget as B, cb_auditory as CA

BASE=Path(core.OUT)/'aln35/cbaud_people_v1';PLAN=BASE/'plan.json'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln35/cbaud_people_v1')
NOTE=Path(core.REPO)/'docs/auditory_alignment_v3/aln35/CBAUD_PEOPLE_DESIGN.md'
FAMILY='ALN35_CBAUD_PEOPLE';GROUP='aln35_cbaud_people'
SEED=3401;DATASET='dtu';DONOR_ARM='generic_paired';FRACTIONS=(0.25,0.5)
SELF=('auditory_alignment_v3/aln35','cbaud_people.py')
NAME,LANE,SBATCH='c3_s35cbaud','s35_cbaud_people','slurm/aln35_cbaud_people.sbatch'


def read(p):return json.loads(Path(p).read_text())


def register():
    I.register();CA.register()
    files=core.FAMILY_CODE['aligned32']+[I.SELF,B.SELF,('auditory_alignment_v3/aln34','cb_auditory.py'),SELF]
    if GROUP in core.FAMILY_CODE:assert core.FAMILY_CODE[GROUP]==files,'family registration collision'
    core.FAMILY_CODE[GROUP]=files;core.FAMILY_GROUP[FAMILY]=GROUP


def sources():
    files=[Path(__file__),NOTE,Path(I.__file__),Path(B.__file__),Path(CA.__file__),
           Path(core.REPO)/'auditory_alignment_v3/run_aligned32.py']
    return {str(p.relative_to(core.REPO)):B.sha(p) for p in sorted(files)}


def donor_record(cp):
    donor=next(u for u in cp['rows'] if CA.is_donor(u) and u['seed']==SEED and u['arm']==DONOR_ARM)
    path=CA.BASE/'units'/f'{donor["id"]}.json';rec=read(path)
    assert rec['status']=='complete' and not rec.get('probe') and Path(rec['final_checkpoint']).is_file()
    return donor,rec,path


def references(ip,cp,rows):
    """Existing comparison units, verified complete; nothing here is retrained."""
    direct={str(f):[] for f in FRACTIONS};full=[]
    for row in rows:
        ref=row['spec']['direct_reference_id'];rec=read(I.BASE/'units'/f'{ref}.json')
        assert rec['status']=='complete' and not rec.get('truncated')
        direct[str(row['spec']['fraction'])].append({'id':ref,'record_sha256':B.sha(I.BASE/'units'/f'{ref}.json')})
    donor,_,_=donor_record(cp)
    targets=[u for u in cp['rows'] if not CA.is_donor(u) and u['spec'].get('donor_id')==donor['id'] and u['dataset']==DATASET]
    for sf in range(5):
        for cf in (0,1):
            t=[u for u in targets if u['subject_fold']==sf and u['content_fold']==cf]
            assert len(t)==1,(sf,cf,len(t))
            t=t[0];baseline=t['spec']['baseline_id'];base=ip['baselines'][baseline]
            trec=CA.BASE/'units'/f'{t["experiment_id"]}.json';assert read(trec)['status']=='complete'
            brec=Path(core.OUT)/'units'/f'{baseline}.json'
            assert B.sha(brec)==base['record_sha256']
            full.append({'subject_fold':sf,'content_fold':cf,'direct':baseline,'direct_record_sha256':B.sha(brec),
                         'auditory':t['experiment_id'],'auditory_record_sha256':B.sha(trec)})
    for f in FRACTIONS:assert len(direct[str(f)])==10
    return {'direct_curves':direct,'full':full}


def make_plan():
    register();ip=read(I.PLAN);I.verify(ip);cp=read(CA.PLAN);CA.verify(cp)
    donor,drec,dpath=donor_record(cp);rows=[];design=B.sha(NOTE)
    for old in ip['rows']:
        s=old['spec']
        if (old['dataset']!=DATASET or old['seed']!=SEED or s['architecture']!='cbramod' or s['adaptation']!='pretrained_full'
                or s['axis']!='people' or s['fraction'] not in FRACTIONS):continue
        row=copy.deepcopy(old);row.pop('experiment_id');row.pop('registered',None)
        row['family_id']=FAMILY
        row['spec'].update(card='S35_CBAUD_PEOPLE',start='cb_auditory_continued',donor_id=donor['id'],donor_arm=DONOR_ARM,
                           direct_reference_id=old['experiment_id'],design_sha256=design)
        row['experiment_id']='ALN35CBA_'+hashlib.sha256(B.dumps(row).encode()).hexdigest()[:16]
        row['registered']=f"S35_CBAUD_PEOPLE v1; {NOTE.relative_to(core.REPO)} SHA256 {design}"
        rows.append(row)
    assert len(rows)==20 and {(r['subject_fold'],r['content_fold'],r['spec']['fraction']) for r in rows}=={
        (sf,cf,f) for sf in range(5) for cf in (0,1) for f in FRACTIONS}
    body={'version':'S35_CBAUD_PEOPLE_v1','rows':rows,'sources':sources(),'code_hash':core.code_hash(FAMILY),
          'data_inner_plan_sha256':B.sha(I.PLAN),'cb_auditory_plan_sha256':B.sha(CA.PLAN),
          'donor':{'id':donor['id'],'record_sha256':B.sha(dpath),'final_checkpoint':drec['final_checkpoint'],
                   'checkpoint_sha256':drec['final_checkpoint_sha256'],'updates':drec.get('updates')},
          'references':references(ip,cp,rows),'store':str(STORE),
          'analysis':'per-person true NLL bits/query native/unified; auditory-direct at .25/.5/1 and change vs 1; sci_r1 stats B=4000'}
    if PLAN.exists():
        prev=read(PLAN);assert all(prev[k]==v for k,v in body.items()),'immutable plan drift'
    else:
        STORE.mkdir(parents=True,exist_ok=True,mode=0o700);BASE.mkdir(parents=True,exist_ok=True,mode=0o700)
        link=BASE/'ckpt'
        if not link.exists():link.symlink_to(STORE,target_is_directory=True)
        assert link.is_symlink() and link.resolve()==STORE
        B.write(PLAN,{**body,'created':datetime.now().astimezone().isoformat()});PLAN.chmod(0o444)
    print('Registered',len(rows),'auditory-start units',B.sha(PLAN),flush=True)


def verify(plan):
    register()
    assert plan['sources']==sources() and plan['code_hash']==core.code_hash(FAMILY),'frozen source drift'
    assert plan['data_inner_plan_sha256']==B.sha(I.PLAN) and plan['cb_auditory_plan_sha256']==B.sha(CA.PLAN)
    assert B.sha(plan['donor']['final_checkpoint'])==plan['donor']['checkpoint_sha256']


@contextlib.contextmanager
def provenance(row,plan,probe,total):
    """Installed first, so it runs last: the record names this lane's plan and keeps inherited stamps."""
    old=core.write_record
    def write(path,rec,start):
        rec['inherited_instrumentation']={'cb_auditory_plan_sha256':rec.pop('plan_sha256',None),
                                          'data_inner_execution':rec.pop('execution',None)}
        rec.update(plan_sha256=B.sha(PLAN),probe=probe,truncated=total!=row['spec']['epochs'],
                   execution={'job':os.environ.get('SLURM_JOB_ID'),'plan_sha256':B.sha(PLAN),'design':'S35_CBAUD_PEOPLE_v1'},
                   start={'kind':'cb_auditory_continued','donor_id':plan['donor']['id'],
                          'donor_checkpoint_sha256':plan['donor']['checkpoint_sha256']},
                   direct_reference_id=row['spec']['direct_reference_id'])
        old(path,rec,start)
    core.write_record=write
    try:yield
    finally:core.write_record=old


def run_unit(row,plan,probe=False):
    from .. import run_aligned32
    register();ip=read(I.PLAN);I.verify(ip);cp=read(CA.PLAN);CA.verify(cp)
    _,drec,_=donor_record(cp)
    assert drec['final_checkpoint_sha256']==plan['donor']['checkpoint_sha256']
    out=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    if not probe:assert (BASE/'ckpt').is_symlink() and (BASE/'ckpt').resolve()==STORE
    total=2 if probe else row['spec']['epochs']
    with provenance(row,plan,probe,total),I.instrumentation(row,ip,total),CA.target_instrumentation(row,drec,False):
        run_aligned32.run(row,str(out),epochs=total)
    rec=read(out/'units'/f'{row["experiment_id"]}.json')
    assert rec['status']=='complete' and rec['epochs_completed']==total
    print(row['experiment_id'],'complete','probe',probe,flush=True)
    return rec


def receipts():
    out={'pass':[],'other':[]}
    if not PLAN.exists():return out
    digest=B.sha(PLAN)
    for path in sorted((BASE/'probes').glob('*/receipt.json')):
        rec=read(path)
        if rec.get('plan_sha256')!=digest:continue
        out['pass' if rec.get('status')=='pass' else 'other'].append(path)
    return out


def fleet_status():
    status={'name':NAME,'lane':LANE,'state':'plan_missing','ready':0,'remaining':20,'slots':1,'initial':[],'submit':[]}
    if not PLAN.exists():return status
    plan=read(PLAN);units=BASE/'units'
    remaining=[r for r in plan['rows'] if not (units/f'{r["experiment_id"]}.json').exists()]
    status['remaining']=len(remaining)
    if not remaining:status['state']='complete';return status
    rec=receipts()
    if not rec['pass']:
        if rec['other']:status['state']='engineering_probe_failed';return status
        status.update(state='ready',ready=1,submit=[SBATCH,'--smoke']);return status
    available=[r for r in remaining if not (units/f'{r["experiment_id"]}.FAILED.json').exists()]
    status.update(state='ready' if available else 'failed_unit_review',ready=len(available),slots=2,
                  submit=[SBATCH,'--smoke-job',rec['pass'][-1].parent.name,'--max-units','1'])
    return status


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--unit');ap.add_argument('--smoke-job');ap.add_argument('--max-units',type=int,default=1)
    a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.make_plan:make_plan();return
    plan=read(PLAN);verify(plan)
    if a.unit:run_unit(next(r for r in plan['rows'] if r['experiment_id']==a.unit),plan);return
    if a.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for f in FRACTIONS:
                row=next(r for r in plan['rows'] if r['spec']['fraction']==f and r['subject_fold']==0 and r['content_fold']==0)
                rec=run_unit(row,plan,True)
                assert rec['truncated'] and rec['probe'] and rec['start']['donor_id']==plan['donor']['id']
                receipt['units'].append({'id':row['experiment_id'],'fraction':f,'peak_mb':rec['gpu_peak_allocated_mb'],
                                         'seconds':rec['total_seconds'],'optimizer_steps':rec.get('optimizer_steps')})
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    rec=read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert rec['status']=='pass' and rec['plan_sha256']==B.sha(PLAN)
    count=0
    for row in plan['rows']:
        eid=row['experiment_id'];path=BASE/'units'/f'{eid}.json'
        if path.exists() or (BASE/'units'/f'{eid}.FAILED.json').exists():continue
        lock=BASE/'claims'/f'{eid}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if path.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m',__spec__.name,'--unit',eid]).returncode
            if rc or not path.exists():
                B.write(BASE/'units'/f'{eid}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc})
                raise RuntimeError('cbaud people unit failed')
            count+=1
        if count>=a.max_units:break


if __name__=='__main__':main()
