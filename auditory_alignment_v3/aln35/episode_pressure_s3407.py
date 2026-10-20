"""S35 episode replication: DTU local pressure-100 with independently trained seed-3407 sources.

Frozen v1 methods (episode_pressure, support_runtime) are reused unchanged; only source selection
and lane paths differ, swapped inside this worker process as in episode_lineage_v2.
See docs/auditory_alignment_v3/aln35/EPISODE_REPLICATION_S3407_DESIGN.md.
"""
from __future__ import annotations
import argparse
import contextlib
from datetime import datetime
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import traceback

from . import episode_pressure as E, support_runtime as R, support_contract as K, support_coverage as S
from ..aln34 import learning_budget as B, data_inner as I

BASE=R.ROOT/'episode_pressure_s3407_v1';PLAN=BASE/'plan.json'
STORE=R.STORE/'episode_pressure_s3407_v1'
NOTE=Path(R.core.REPO)/'docs/auditory_alignment_v3/aln35/EPISODE_REPLICATION_S3407_DESIGN.md'
SEED=3407;PRESSURE=100;ARCH='lag_local_tokens'
NAME,LANE,SBATCH='c3_s35epirep','s35_episode_rep','slurm/aln35_episode_rep.sbatch'


def sources():
    return {**E.sources(),str(Path(__file__).relative_to(R.core.REPO)):B.sha(__file__),
            str(NOTE.relative_to(R.core.REPO)):B.sha(NOTE)}


def selected_sources():
    ip=R.read(I.PLAN);I.verify(ip);I.register();out=[]
    for inner in ip['rows']:
        s=inner['spec']
        if s['axis']!='inner_person' or inner['seed']!=SEED or s['objective']!='NCE' or s['architecture']!=ARCH:continue
        outer=ip['baselines'][s['baseline_id']]
        out.append({'dataset':'dtu','architecture':ARCH,'outer':outer,'inner':inner,'inner_plan_sha256':B.sha(I.PLAN),
                    'inner_split':ip['splits'][s['split_key']],'source_execution_id':outer['row']['experiment_id']})
    assert len(out)==10 and len({r['source_execution_id'] for r in out})==10
    assert {(r['outer']['row']['subject_fold'],r['outer']['row']['content_fold']) for r in out}=={(sf,cf) for sf in range(5) for cf in (0,1)}
    return sorted(out,key=lambda x:x['source_execution_id'])


def original_units():
    """The seed-3401 v1 units being replicated (local, pressure 100), keyed by fold."""
    v1=R.read(E.PLAN);E.verify(v1)
    found={(u['outer_fold'],u['content_fold']):u['id'] for u in v1['rows']
           if u['source']['dataset']=='dtu' and u['source']['architecture']==ARCH and u['support_steps']==PRESSURE}
    assert len(found)==10
    return found


def make_plan():
    support_plan=R.read(S.PLAN);S.verify(support_plan);code=sources();originals=original_units();rows=[]
    for source in selected_sources():
        row=source['outer']['row']
        unit={'workpackage_id':'S35_EPISODE_REPLICATION_S3407','design_version':'v1','source':source,
              'code_sha256':K.digest(code),'support_binding_sha256':B.sha(S.GEOMETRY),
              'objective':'NCE','seed':SEED,'outer_fold':row['subject_fold'],'content_fold':row.get('content_fold'),
              'support_steps':PRESSURE,'encoder_updates':E.ENCODER_UPDATES,'regimes':list(E.REGIMES),
              'adapter':'input lowrank_spatial rank4 A~N(0,.01), B=0, Adam1e-3','encoder_lr':1e-4,
              'encoder_optimizer':'AdamW weight_decay1e-4,100-update cosine,eval with gradients',
              'approximation':'first order; adapted A/B frozen during query encoder gradient',
              'target_steps':list(E.TARGET_STEPS),'target_support':['U10 five draws','U30'],
              'sampling_streams':'frozen v1 constants (3401+61000, 3401+62000+update, 3401+person+63000) kept',
              'replicates':{'plan_sha256':B.sha(E.PLAN),'unit_id':originals[(row['subject_fold'],row.get('content_fold'))]},
              'selection_roles':'independent source-inner persons only; DTU original source-ES content, never outer-test content',
              'comparison_version':'exploratory source-seed replication of the v1 local pressure-100 cell'}
        unit['id']='ALN35EPR_'+K.digest(unit)[:16];rows.append(unit)
    body={'version':'S35_EPISODE_REPLICATION_S3407_v1','rows':rows,'sources':code,
          'support_binding_sha256':B.sha(S.GEOMETRY),'support_plan_sha256':B.sha(S.PLAN),
          'parent_plan_sha256':B.sha(E.PLAN),'expected_units':10,'expected_people':{'dtu':44},'store':str(STORE)}
    if PLAN.exists():
        old=R.read(PLAN);assert all(old[k]==v for k,v in body.items()),'immutable replication plan drift'
    else:
        BASE.mkdir(parents=True,exist_ok=True,mode=0o700);B.write(PLAN,{**body,'created':datetime.now().astimezone().isoformat()})
        PLAN.chmod(0o444)
    ready=[u['id'] for u in rows if R.ready(u['source'],True)]
    assert len(ready)==10,'seed-3407 sources missing'
    print('Registered',len(rows),'replication units',B.sha(PLAN),flush=True)


def verify(plan):
    assert plan['sources']==sources(),'frozen replication source drift'
    assert plan['support_binding_sha256']==B.sha(S.GEOMETRY) and plan['support_plan_sha256']==B.sha(S.PLAN)
    assert plan['parent_plan_sha256']==B.sha(E.PLAN)


@contextlib.contextmanager
def execution_context():
    before=(E.BASE,E.PLAN,E.STORE)
    E.BASE,E.PLAN,E.STORE=BASE,PLAN,STORE
    try:yield
    finally:E.BASE,E.PLAN,E.STORE=before


def run_unit(unit,smoke=False):
    with execution_context():E.run_unit(unit,smoke)


def receipts():
    out={'pass':[],'other':[]}
    if not PLAN.exists():return out
    digest=B.sha(PLAN)
    for path in sorted((BASE/'probes').glob('*/receipt.json')):
        rec=R.read(path)
        if rec.get('plan_sha256')!=digest:continue
        out['pass' if rec.get('status')=='pass' else 'other'].append(path)
    return out


def fleet_status():
    status={'name':NAME,'lane':LANE,'state':'plan_missing','ready':0,'remaining':10,'slots':1,'initial':[],'submit':[]}
    if not PLAN.exists():return status
    plan=R.read(PLAN);remaining=[u for u in plan['rows'] if not (BASE/'units'/f'{u["id"]}.json').exists()]
    status['remaining']=len(remaining)
    if not remaining:status['state']='complete';return status
    rec=receipts()
    if not rec['pass']:
        if rec['other']:status['state']='engineering_probe_failed';return status
        # The single coordinator launches the engineering smoke itself, inside the GPU cap.
        status.update(state='ready',ready=1,submit=[SBATCH,'--smoke'])
        return status
    available=[u for u in remaining if R.ready(u['source'],True) and not (BASE/'units'/f'{u["id"]}.FAILED.json').exists()]
    status.update(state='ready' if available else 'source_dependency_or_failed_unit',ready=len(available),slots=2,
                  submit=[SBATCH,'--smoke-job',rec['pass'][-1].parent.name,'--max-units','1'])
    return status


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--unit');ap.add_argument('--smoke-job');ap.add_argument('--max-units',type=int,default=1)
    a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.make_plan:make_plan();return
    plan=R.read(PLAN);verify(plan)
    if a.unit:run_unit(next(u for u in plan['rows'] if u['id']==a.unit));return
    if a.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            unit=plan['rows'][0];run_unit(unit,True);receipt['units'].append(unit['id']);receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    rec=R.read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert rec['status']=='pass' and rec['plan_sha256']==B.sha(PLAN)
    count=0
    for unit in plan['rows']:
        path=BASE/'units'/f'{unit["id"]}.json'
        if path.exists() or (BASE/'units'/f'{unit["id"]}.FAILED.json').exists() or not R.ready(unit['source'],True):continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if path.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m',__spec__.name,'--unit',unit['id']]).returncode
            if rc or not path.exists():
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc})
                raise RuntimeError('episode replication unit failed')
            count+=1
        if count>=a.max_units:break


if __name__=='__main__':main()
