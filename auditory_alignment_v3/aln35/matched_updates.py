"""S35_MATCHED_UPDATES trajectories, also the sole source of true-risk selectors."""
from __future__ import annotations
import argparse
import copy
from datetime import datetime
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import torch
from ..aln34 import learning_budget as B
from . import selection_assets as A, selection_training as T, support_contract as K

BASE=A.ROOT/'matched_updates_v1';PLAN=BASE/'plan.json';AUDIT=BASE/'asset_audit.json'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln35/matched_updates_v1')
NOTE=Path(A.core.REPO)/'docs/auditory_alignment_v3/aln35/MATCHED_UPDATES_SELECTION_DESIGN.md'


def sources():
    files={Path(__file__),Path(A.__file__),Path(T.__file__),Path(K.__file__),NOTE,
           Path(__file__).with_name('selection_policy.py')}
    for name in ('local_support','aligned32'):
        files.update(Path(A.core.REPO)/d/f for d,f in A.core.FAMILY_CODE[name]+A.core.V2_DEPS)
    for module in (A.I,A.V,B,T.D,T.E):files.add(Path(module.__file__))
    files.update(Path(A.core.REPO)/s for s in ('auditory_alignment/evaluate.py','auditory_alignment/data.py'))
    return {str(p.relative_to(A.core.REPO)):B.sha(p) for p in sorted(files)}


def make_plan():
    audit=A.read(AUDIT);assert audit['status']=='pass';code=sources();rows=[]
    for binding in audit['bindings']:
        for stage in ('inner','outer'):
            for fraction in (.5,1.):
                compact={k:binding[k] for k in ('source','metadata_sha256','outer_reuse')}
                unit={'workpackage_id':'S35_MATCHED_UPDATES_AND_TRUE_RISK_SELECTION','design_version':'v1',
                      'binding':compact,'stage':stage,'fraction':fraction,'budget':binding['stages'][stage]['budget'],
                      'split':binding['stages'][stage]['splits'][str(fraction)],'code_sha256':K.digest(code),
                      'reuse_existing':stage=='outer' and fraction==1., 'objective':'NCE','seed':3401,
                      'source_lineage':binding['source']['source_execution_id'],
                      'EEG_access':'original matched aligned1000 local/CB; no new window',
                      'audio_coordinates':'original fixed32 source-side targets; full legal source audio stats shared across EEG fractions',
                      'readouts':['native','unified'],'personal_support_updates':0,
                      'comparison_version':'fixed U primary, independent-inner selected state supplementary'}
                unit['id']='ALN35MAT_'+K.digest(unit)[:16];rows.append(unit)
    body={'version':'S35_MATCHED_UPDATES_v1','created':datetime.now().astimezone().isoformat(),'rows':rows,'sources':code,
          'asset_audit_sha256':B.sha(AUDIT),'expected_trajectory_units':120,'new_training_trajectories':90,
          'reused_outer_full_trajectories':30,'expected_source_bundles':30,'expected_DTU_people':44,
          'candidate_fractions':[0.,.25,.5,1.],'selection':'independent inner-person equal-person query NLL or source-ES inherited gain, separately native/unified',
          'state': 'planned; CPU binding is not trained completion'}
    if PLAN.exists():assert all(A.read(PLAN)[k]==v for k,v in body.items() if k!='created'),'immutable matched plan drift'
    else:B.write(PLAN,body);PLAN.chmod(0o444)
    B.write(BASE/'readiness.json',{'plan_sha256':B.sha(PLAN),'ready_units':[u['id'] for u in rows if ready(u)],
                                'waiting_existing_budget':[u['id'] for u in rows if not ready(u)]})
    print('Registered120 trajectory units:90 new bounded trajectories,30 outer100% existing2x reuse',B.sha(PLAN),flush=True)


def verify(plan):
    A.V.register();A.I.register()
    assert plan['sources']==sources(),'matched source drift'
    assert plan['asset_audit_sha256']==B.sha(AUDIT),'asset binding drift'


def ready(unit):
    if not unit['reuse_existing']:return True
    return all(Path(x['path']).is_file() for x in unit['binding']['outer_reuse']['required_snapshots'])


def run_unit(unit,probe=False):
    started=time.time();actual=copy.deepcopy(unit)
    if probe and not unit['reuse_existing']:
        # Isolated engineering horizon; never a candidate for production reuse.
        actual['budget'].update(U=4,scheduler_horizon_updates=8,candidate_steps=[0,1,2,4],candidate_epochs=[0,1,2,4])
    dest=STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'production')/unit['id']
    context=T.Context(actual)
    try:
        result=(T.reuse_outer if unit['reuse_existing'] else T.train)(context,dest,B.sha(PLAN),probe)
        result.update(id=unit['id'],registered_unit=unit,probe=probe,job=os.environ['SLURM_JOB_ID'],
                      device=torch.cuda.get_device_name(0),seconds=time.time()-started)
        target=BASE/'probes'/os.environ['SLURM_JOB_ID']/'units' if probe else BASE/'units'
        B.write(target/f'{unit["id"]}.json',result)
    finally:
        del context;T.gc.collect();torch.cuda.empty_cache()
    print(unit['id'],'complete','probe',probe,round(time.time()-started,1),flush=True)


def fleet_status():
    status={'name':'c3_s35matched','lane':'s35_matched','state':'plan_missing','ready':0,'remaining':120,'slots':1,'initial':[],'submit':[]}
    if not PLAN.is_file():return status
    plan=A.read(PLAN);remaining=[u for u in plan['rows'] if not (BASE/'units'/f'{u["id"]}.json').is_file()]
    status['remaining']=len(remaining)
    if not remaining:status['state']='complete';return status
    receipts=[]
    for path in sorted((BASE/'probes').glob('*/receipt.json')):
        rec=A.read(path)
        if rec.get('status')=='pass' and rec.get('plan_sha256')==B.sha(PLAN):receipts.append(path)
    if not receipts:status['state']='engineering_probe_required';return status
    available=[u for u in remaining if ready(u) and not (BASE/'units'/f'{u["id"]}.FAILED.json').exists()]
    status.update(state='ready' if available else 'existing_budget_dependency_or_failed_unit',ready=len(available),
                  submit=['slurm/aln35_matched_updates.sbatch','--smoke-job',receipts[-1].parent.name,'--max-units','1'])
    return status


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--unit');ap.add_argument('--smoke-job');ap.add_argument('--max-units',type=int,default=1)
    a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.make_plan:make_plan();return
    plan=A.read(PLAN);verify(plan)
    if a.unit:run_unit(next(u for u in plan['rows'] if u['id']==a.unit));return
    if a.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for arch,adaptation in (('lag_local_tokens','local'),('cbramod','pretrained_full'),('cbramod','random_full')):
                candidates=[u for u in plan['rows'] if u['binding']['source']['architecture']==arch and u['binding']['source']['adaptation']==adaptation]
                unit=next(u for u in candidates if u['stage']=='inner' and u['fraction']==.5)
                run_unit(unit,True);receipt['units'].append(unit['id'])
                reused=next((u for u in candidates if u['reuse_existing'] and ready(u)),None)
                if reused is None:raise RuntimeError(f'no compatible existing outer100% probe asset for {arch}/{adaptation}')
                run_unit(reused,True);receipt['units'].append(reused['id'])
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=A.read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    count=0
    # Sources first, so real-risk policies can be locked as soon as their legal
    # inner trajectories exist. No model is selected by outer score here.
    ordered=sorted(plan['rows'],key=lambda u:(u['stage']!='inner',not u['reuse_existing'],u['id']))
    for unit in ordered:
        output=BASE/'units'/f'{unit["id"]}.json'
        if output.exists() or not ready(unit) or (BASE/'units'/f'{unit["id"]}.FAILED.json').exists():continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as f:
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if output.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m',__spec__.name,'--unit',unit['id']]).returncode
            if rc or not output.exists():
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('matched trajectory failed')
            count+=1
        from . import selection_policy
        selection_policy.refresh()
        if count>=a.max_units:break


if __name__=='__main__':main()
