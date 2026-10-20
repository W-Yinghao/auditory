"""Two scoped episode successors: reuse a proven v1-compatible inner source.

Only provenance resolution differs. Frozen v1 methods and live sources remain
byte-identical; substitutions below are confined to this fresh worker process.
"""
from __future__ import annotations
import argparse
import contextlib
import copy
from datetime import datetime
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import traceback

import torch
from . import episode_pressure as E, support_runtime as R, support_contract as K
from ..aln34 import learning_budget as B,private_episode as P1,private_episode_v2 as P2

BASE=R.ROOT/'episode_lineage_v2';PLAN=BASE/'plan.json'
STORE=R.STORE/'episode_lineage_v2'
NOTE=Path(R.core.REPO)/'docs/auditory_alignment_v3/aln35/EPISODE_LINEAGE_CORRECTION.md'
V1_PLAN=E.PLAN
V1_BASE=E.BASE
MISSING_PARENT='ALN34PE2_a41f82a0348a5b42'
LEGACY_PARENT='ALN34PE_909c395faaddca63'


def sources():
    return {**E.sources(),str(Path(__file__).relative_to(R.core.REPO)):B.sha(__file__),
            str(NOTE.relative_to(R.core.REPO)):B.sha(NOTE)}


def validate_legacy(source,legacy,record):
    current=source['private_parent']
    assert legacy['source']==current['source']==record['row']
    assert legacy['inner_train_ids']==current['inner_train_ids']==sorted(record['train_ids'])
    assert legacy['inner_dev_ids']==current['inner_dev_ids']
    assert legacy['outer_test_ids']==current['outer_test_ids']
    assert not set(record['train_ids'])&set(current['inner_dev_ids'])
    assert not set(record['train_ids'])&set(current['outer_test_ids'])
    assert record['status']=='complete' and record['probe'] is False


def make_plan():
    original=R.read(V1_PLAN);E.verify(original);legacy_plan=R.read(P1.PLAN)
    legacy=next(u for u in legacy_plan['rows'] if u['id']==LEGACY_PARENT)
    directory=P1.STORE/'production'/LEGACY_PARENT/'inner_source'
    record=R.read(directory/'record.json');checkpoint=directory/'model_best.pt'
    assert record['plan_sha256']==B.sha(P1.PLAN) and B.sha(checkpoint)==record['checkpoint_sha256']
    rows=[];code=sources()
    for old in original['rows']:
        if old['source'].get('private_parent',{}).get('id')!=MISSING_PARENT:continue
        validate_legacy(old['source'],legacy,record)
        reused=R.read(P2.BASE/'units'/f'{MISSING_PARENT}.json')
        assert reused['execution_version']=='v1_compatible_reuse'
        assert Path(reused['reused_from']['record']).name==LEGACY_PARENT+'.json'
        unit=copy.deepcopy(old)
        unit.update(parent_aln35_id=old['id'],execution_version='S35_EPISODE_PRESSURE_lineage_v2',
                    code_sha256=K.digest(code))
        unit['source']['legacy_inner']={'directory':str(directory),'record_sha256':B.sha(directory/'record.json'),
                'checkpoint_sha256':B.sha(checkpoint),'legacy_unit':legacy,'legacy_plan_sha256':B.sha(P1.PLAN),
                'v2_reuse_record_sha256':B.sha(P2.BASE/'units'/f'{MISSING_PARENT}.json')}
        unit.pop('id');unit['id']='ALN35EPIL2_'+K.digest(unit)[:16];rows.append(unit)
    assert len(rows)==2 and {u['support_steps'] for u in rows}=={20,100}
    body={'version':'S35_EPISODE_LINEAGE_v2','created':datetime.now().astimezone().isoformat(),
          'rows':rows,'sources':code,'parent_plan_sha256':B.sha(V1_PLAN),
          'supersedes_dependency_only':{u['parent_aln35_id']:u['id'] for u in rows},
          'method_change':False,'new_inner_training':False}
    if PLAN.exists():assert all(R.read(PLAN)[k]==v for k,v in body.items() if k!='created')
    else:B.write(PLAN,body);PLAN.chmod(0o444)
    print('Registered2 exact-lineage episode successors',B.sha(PLAN),flush=True)


def verify(plan):
    assert plan['sources']==sources() and plan['parent_plan_sha256']==B.sha(V1_PLAN)


def ready(source,inner=False):
    legacy=source.get('legacy_inner')
    if not legacy:return ORIGINAL_READY(source,inner)
    directory=Path(legacy['directory'])
    return ORIGINAL_READY(source,False) and (directory/'record.json').is_file() and (directory/'model_best.pt').is_file()


ORIGINAL_READY=R.ready
ORIGINAL_PRIVATE_BUNDLE=R.private_bundle


def private_bundle(source,stage,kids=None):
    if stage!='inner' or 'legacy_inner' not in source:return ORIGINAL_PRIVATE_BUNDLE(source,stage,kids)
    kids=R.load_kids() if kids is None else kids;legacy=source['legacy_inner'];directory=Path(legacy['directory'])
    record=R.read(directory/'record.json');path=directory/'model_best.pt'
    assert B.sha(directory/'record.json')==legacy['record_sha256'] and B.sha(path)==legacy['checkpoint_sha256']
    assert record['plan_sha256']==legacy['legacy_plan_sha256']==B.sha(P1.PLAN)
    validate_legacy(source,legacy['legacy_unit'],record)
    row=source['outer']['row'];tr,dev,te=P2.partitions(kids,row['subject_fold'])
    assert sorted(kids[i]['id'] for i in tr)==source['private_parent']['inner_train_ids']
    assert sorted(kids[i]['id'] for i in dev)==source['private_parent']['inner_dev_ids']
    torch.manual_seed(row['seed']);device=torch.device('cuda')
    bt=P2.batcher(row,kids,device,tr);model=P2.new_encoder(row,bt,device)
    state=torch.load(path,map_location=device,weights_only=False);model.load_state_dict(state['enc'],strict=True)
    model.requires_grad_(False).eval();fd=P2.Fold(kids,tr,dev)
    bundle=R.PrivateBundle(row,model,state['protos'].detach(),record,bt,fd)
    provenance={'checkpoint_sha256':legacy['checkpoint_sha256'],'record_sha256':legacy['record_sha256'],
                'inner_source_execution':LEGACY_PARENT,'original_plan_sha256':legacy['legacy_plan_sha256'],
                'compatible_v2_parent':MISSING_PARENT,'v2_reuse_record_sha256':legacy['v2_reuse_record_sha256'],
                'fit_ids':[kids[i]['id'] for i in tr],'calibration_ids':[kids[i]['id'] for i in tr],
                'evaluation_ids':[kids[i]['id'] for i in dev],'outer_excluded_ids':[kids[i]['id'] for i in te],
                'selection_level':'actual whole-model independent inner source, original execution identity preserved'}
    return bundle,provenance


@contextlib.contextmanager
def execution_context():
    before=(E.BASE,E.PLAN,E.STORE,R.ready,R.private_bundle)
    E.BASE,E.PLAN,E.STORE,R.ready,R.private_bundle=BASE,PLAN,STORE,ready,private_bundle
    try:yield
    finally:E.BASE,E.PLAN,E.STORE,R.ready,R.private_bundle=before


def run_unit(unit,smoke=False):
    with execution_context():E.run_unit(unit,smoke)


def fleet_status():
    status={'name':'c3_s35epiline2','lane':'s35_episode_lineage','state':'plan_missing','ready':0,'remaining':2,'slots':1,'initial':[],'submit':[]}
    if not PLAN.exists():return status
    plan=R.read(PLAN);remaining=[u for u in plan['rows'] if not (BASE/'units'/f'{u["id"]}.json').exists()]
    status['remaining']=len(remaining)
    if not remaining:status['state']='complete';return status
    receipts=[]
    for path in sorted((BASE/'probes').glob('*/receipt.json')):
        rec=R.read(path)
        if rec.get('status')=='pass' and rec.get('plan_sha256')==B.sha(PLAN):receipts.append(path)
    if not receipts:status['state']='lineage_probe_required';return status
    available=[u for u in remaining if ready(u['source'],True) and not (BASE/'units'/f'{u["id"]}.FAILED.json').exists()]
    status.update(state='ready' if available else 'source_dependency_or_failed_unit',ready=len(available),
                  submit=['slurm/aln35_episode_lineage.sbatch','--smoke-job',receipts[-1].parent.name])
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
            # Scientific method already covered by v1 smoke; both pressure
            # endpoints still exercise this actual legacy resolver once.
            for unit in plan['rows']:run_unit(unit,True);receipt['units'].append(unit['id'])
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=R.read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    count=0
    for unit in plan['rows']:
        path=BASE/'units'/f'{unit["id"]}.json'
        if path.exists() or not ready(unit['source'],True):continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if path.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m',__spec__.name,'--unit',unit['id']]).returncode
            if rc or not path.exists():
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('lineage episode failed')
            count+=1
        if count>=a.max_units:break


if __name__=='__main__':main()
