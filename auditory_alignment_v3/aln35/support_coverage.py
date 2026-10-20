"""S35_SUPPORT_COVERAGE: fixed-Q quantity/composition and probability interfaces."""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
import torch

from ..aln34 import learning_budget as B
from . import support_contract as K, support_runtime as R

BASE = R.ROOT/'support_coverage_v1'
PLAN = BASE/'plan.json'
GEOMETRY = BASE/'restricted_support_bindings.json'
NOTE = Path(R.core.REPO)/'docs/auditory_alignment_v3/aln35/SUPPORT_COVERAGE_DESIGN.md'


def sources(): return R.source_files(__file__, NOTE)


def make_plan():
    chosen = R.selected_sources()
    code = sources()
    if not GEOMETRY.exists():
        B.write(GEOMETRY, R.bindings(chosen)); GEOMETRY.chmod(0o400)
    rows = []
    for source in chosen:
        row = source['outer']['row']
        unit = {'workpackage_id':'S35_SUPPORT_COVERAGE', 'design_version':'v1', 'source':source,
                'source_code_sha256':K.digest(code), 'source_plans':{'data_inner':B.sha(R.I.PLAN),'private_episode_v2':B.sha(R.PE.PLAN)},
                'query_binding_sha256':B.sha(GEOMETRY), 'objective':'NCE', 'seed':3401,
                'outer_fold':row['subject_fold'], 'content_fold':row.get('content_fold'),
                'support_seeds':list(K.SAMPLING_SEEDS), 'methods':list(K.METHODS),
                'rank':4, 'adapter_steps':20, 'adapter_lr':.001,
                'probability_temperatures':[.5,1.,2.], 'readouts':['native','unified'] if source['dataset']=='dtu' else ['native','linear'],
                'eeg_access':'original local/FM access, common safe P/Q guard; private cross-architecture contrast not isolated pretraining',
                'target_coordinates':'original frozen audio32 / native current-sound class coordinates',
                'fit_cal_selection_roles':'source fit/ES; personal P fitting or T selection; fixed outer Q evaluation only',
                'comparison_version':'exploratory direct paired v1'}
        unit['id']='ALN35SUP_'+K.digest(unit)[:16]; rows.append(unit)
    body={'version':'S35_SUPPORT_COVERAGE_v1','created':datetime.now().astimezone().isoformat(),
          'rows':rows,'sources':code,'query_binding_sha256':B.sha(GEOMETRY), 'expected_units':30,
          'expected_people':{'dtu':44,'private_bdf':64},
          'families':{'stratification':['dataset','architecture','readout','metric'],
                      'support_terms':['U30-U10','C10-U10','H10-U10 (private only)'],
                      'method_terms':['rank4_fixed20-zero_step','rank4_fixed20-probability_only'],
                      'within_identity_first':'U10 five draws; then two DTU content folds; no seed×person inflation',
                      'sign':'risk reference-candidate; AUC candidate-reference',
                      'statistics':'exploratory 4000 stratified whole-person fixed-SE max-|z*|; nonregular retained'}}
    if PLAN.exists(): assert all(R.read(PLAN)[k] == v for k,v in body.items() if k!='created'), 'immutable support plan drift'
    else: B.write(PLAN,body); PLAN.chmod(0o444)
    B.write(BASE/'readiness.json', {'plan_sha256':B.sha(PLAN), 'ready_units':[u['id'] for u in rows if R.ready(u['source'])],
                                 'dependency_missing':[u['id'] for u in rows if not R.ready(u['source'])]})
    print('Registered',len(rows),'support coverage source bundles',B.sha(PLAN),flush=True)


def verify(plan):
    assert plan['sources']==sources(), 'frozen S35 support source drift'
    assert plan['query_binding_sha256']==B.sha(GEOMETRY), 'support/query binding drift'


def support_receipt(identity, split, indices, strategy, kid=None, items=None):
    out={'strategy':strategy, 'n10':split['n10'], 'n30':split['n30'], 'n_support':len(indices),
         'n_query':len(split['query']), 'original_available_count':split['original_n'],
         'support_fraction':len(indices)/max(1,split['original_n']),
         'support_hash':K.digest([K.stable_key(identity,j) for j in indices]),
         'query_hash':K.digest([K.stable_key(identity,j) for j in split['query']]),
         'guard_excluded_count':len(split['guard_excluded']), 'guard':split['guard'],
         'preprocessing_access':split['preprocessing'],
         'support_id_storage':'restricted_support_bindings plus deterministic selector; raw event sequence not public'}
    if kid is not None:
        times=kid['_s35_onset_seconds'][indices]
        out.update(n_support_blocks=len(set(kid['block'][indices])), n_query_blocks=len(set(kid['block'][split['query']])),
                   class_counts=K.histogram(kid['y'][indices]), history_counts=K.histogram(kid['bin'][indices]),
                   time_span_seconds=float(np.ptp(times)) if len(times) else None,
                   effective_sound_classes=len(set(kid['y'][indices])),
                   query_identical_private_episode_v2=split['query_identical_private_episode_v2'],
                   query_identical_native_science=split['query_identical_native_science'])
    else:
        selected=[items[i] for i in indices]
        out.update(n_support_blocks=len({s['code'] for s in selected}),
                   content_counts=K.histogram(s['part'] for s in selected),
                   effective_independent_sounds=len({s['uid'] for s in selected}),
                   time_span_seconds=float(np.ptp([s['e0'] for s in selected])/split['fs']) if selected else None,
                   query_identical_adaptation_policy_v1=split['query_identical_adaptation_policy_v1'])
    return out


def evaluate_private(unit, binding, smoke):
    bundle, provenance=R.private_bundle(unit['source'],'outer'); per={}
    for child in (bundle.fd.te[:1] if smoke else bundle.fd.te):
        kid=bundle.fd.kids[child]; identity=kid['id']; split=K.private_split(kid)
        R.check_binding(binding,split,identity,'private_bdf')
        pool,query=split['pool'],split['query']
        variants=K.select_support(pool,split['n10'],identity,labels=kid['y'][pool],
                    history=kid['bin'][pool],times=kid['_s35_onset_seconds'][pool])
        person={'group':kid['group'],'status':'complete' if len(query) else 'no_query', 'conditions':{}}
        per[identity]=person
        if not len(query): continue
        u=bundle.representations(child); base=u[query]
        for strategy,support in variants.items():
            coverage=support_receipt(identity,split,support,strategy,kid=kid)
            values={}
            adapter,ledger=R.fit_private_output(bundle,u,kid['y'],support,20,3401+child+51000)
            with torch.no_grad():
                changed=adapter(torch.tensor(base,device=bundle.bt.dev)).cpu().numpy() if ledger['effective_adapter_steps'] else base.copy()
            for method in K.METHODS:
                modes={}
                for mode in ('native','linear'):
                    t,selection=K.temperature_binary(bundle.logits(u[support],mode),kid['y'][support]) if method=='probability_only' else (1.,None)
                    modes[mode]=R.private_metrics(bundle,changed if method=='rank4_fixed20' else base,kid,query,mode,base,t)
                    if selection is not None: modes[mode]['temperature_selection']=selection
                fitsteps=ledger['effective_adapter_steps'] if method=='rank4_fixed20' else 0
                values[method]={'metrics':modes,'access_budget':K.access_budget(strategy,split,support,fitsteps,True),
                                'adaptation':ledger if method=='rank4_fixed20' else {'effective_adapter_steps':0}}
            person['conditions'][strategy]={'support':coverage,'methods':values}
            del adapter
    output={'per_participant':per,'source_provenance':provenance,'source_readouts':bundle.readout_receipt,
            'primary_readout':'linear (native-current-science frozen source ES probe); native supplement',
            'source_adapter_type':'output rank4; this differs from the episode input-spatial adapter'}
    del bundle;R.cleanup();return output


def evaluate_public(unit,binding,smoke):
    bundle,people,role,provenance=R.public_bundle(unit['source'],'outer')
    pool=bundle.eval_pool(role);per={}
    for p in (people[:1] if smoke else people):
        person=bundle.coh.participants[p];identity=person['id'];items,split=R.split_public(bundle,p,role)
        R.check_binding(binding,split,identity,'dtu',unit['content_fold'],role)
        selectors=K.select_support(split['pool'],split['n10'],identity,groups=np.array([items[i]['part'] for i in split['pool']]))
        query=[items[i] for i in split['query']]
        result={'group':person['group'],'status':'complete' if query else 'no_query','conditions':{}}
        per[identity]=result
        if not query:continue
        base=bundle.reps.u([s['e0'] for s in query])
        for strategy,indices in selectors.items():
            support=[items[i] for i in indices];coverage=support_receipt(identity,split,indices,strategy,items=items)
            model,ledger=R.fit_public(bundle,support,20,3401+p+51000)
            changed=bundle.reps_of(model).u([s['e0'] for s in query]) if ledger['effective_adapter_steps'] else base.copy()
            methods={}
            for method in K.METHODS:
                values={}
                for mode in ('native','unified'):
                    t,selection=R.public_temperature(bundle,support,mode) if method=='probability_only' else (1.,None)
                    values[mode]=R.public_metrics(bundle,changed if method=='rank4_fixed20' else base,query,pool,mode,base,t)
                    if selection is not None:values[mode]['temperature_selection']=selection
                steps=ledger['effective_adapter_steps'] if method=='rank4_fixed20' else 0
                methods[method]={'metrics':values,'access_budget':K.access_budget(strategy,split,indices,steps),
                                 'adaptation':ledger if method=='rank4_fixed20' else {'effective_adapter_steps':0}}
            result['conditions'][strategy]={'support':coverage,'methods':methods}
            del model
    output={'per_participant':per,'source_provenance':provenance,
            'source_readouts':{'tau':bundle.readout.tau,'unified_alpha':float(bundle.readout.alpha_uni)},
            'primary_readout':'native and unified kept separate','source_adapter_type':'input lowrank_spatial rank4'}
    del bundle;R.cleanup();return output


def run_unit(unit,smoke=False):
    started=time.time();binding=R.read(GEOMETRY)
    assert R.ready(unit['source'])
    output=(evaluate_public if unit['source']['dataset']=='dtu' else evaluate_private)(unit,binding,smoke)
    output.update(status='complete',unit=unit,id=unit['id'],probe=smoke,plan_sha256=B.sha(PLAN),
                  job=os.environ['SLURM_JOB_ID'],seconds=time.time()-started,device=torch.cuda.get_device_name(0),
                  gpu_peak_mb=torch.cuda.max_memory_allocated()/2**20)
    dest=BASE/'probes'/os.environ['SLURM_JOB_ID'] if smoke else BASE/'units'
    B.write(dest/f'{unit["id"]}.json',output)
    print(unit['id'],'complete',round(time.time()-started,1),'probe',smoke,flush=True)


def fleet_status():
    """Read-only scheduler plugin. It never submits jobs or initializes a GPU."""
    status={'name':'c3_s35support','lane':'s35_support','state':'plan_missing','ready':0,
            'remaining':30,'slots':1,'initial':[],'submit':[]}
    if not PLAN.is_file():return status
    plan=R.read(PLAN);remaining=[u for u in plan['rows'] if not (BASE/'units'/f'{u["id"]}.json').is_file()]
    status['remaining']=len(remaining)
    if not remaining:status['state']='complete';return status
    receipts=[]
    for path in sorted((BASE/'probes').glob('*/receipt.json')):
        rec=R.read(path)
        if rec.get('status')=='pass' and rec.get('plan_sha256')==B.sha(PLAN):receipts.append(path)
    if not receipts:status['state']='engineering_probe_required';return status
    ready=[u for u in remaining if R.ready(u['source']) and not (BASE/'units'/f'{u["id"]}.FAILED.json').exists()]
    status.update(state='ready' if ready else 'source_dependency_or_failed_unit',ready=len(ready),
                  submit=['slurm/aln35_support_coverage.sbatch','--smoke-job',receipts[-1].parent.name,'--max-units','1'])
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
            for dataset in ('dtu','private_bdf'):
                for architecture in ('lag_local_tokens','cbramod'):
                    u=next(u for u in plan['rows'] if u['source']['dataset']==dataset and u['source']['architecture']==architecture and R.ready(u['source']))
                    run_unit(u,True);receipt['units'].append(u['id'])
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=R.read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    count=0
    for u in plan['rows']:
        path=BASE/'units'/f'{u["id"]}.json'
        if path.exists() or not R.ready(u['source']):continue
        if (BASE/'units'/f'{u["id"]}.FAILED.json').exists():continue
        lock=BASE/'claims'/f'{u["id"]}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if path.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m',__spec__.name,'--unit',u['id']]).returncode
            if rc or not path.exists():
                B.write(BASE/'units'/f'{u["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('support unit failed')
            count+=1
        if count>=a.max_units:break


if __name__=='__main__':main()
