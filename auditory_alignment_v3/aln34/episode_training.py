"""First-order source-person episodes versus matched ordinary continuation."""
from __future__ import annotations
import argparse
import copy
from datetime import datetime
import fcntl
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
import torch
from . import adaptation_policy as D
from . import data_inner as I
from . import learning_budget as B
from .. import core

BASE=Path(core.OUT)/'aln34/episode_training_v1'
PLAN=BASE/'plan.json'
NOTE=Path(core.OUT)/'aln34/EPISODE_TRAINING_DESIGN_20261017.md'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln34_episode_training_v1')
REGIMES=('ordinary','episode')
STEPS=(0,5,20)
UPDATES=100


def sources():
    files={Path(__file__),NOTE,Path(D.__file__),Path(I.__file__),Path(B.__file__)}
    for g in ('local_support','aligned32'):
        files.update(Path(core.REPO)/d/f for d,f in core.FAMILY_CODE[g]+core.V2_DEPS)
    return {str(f.relative_to(core.REPO)):B.sha(f) for f in sorted(files)}


def make_plan():
    ip=json.loads(I.PLAN.read_text());I.verify(ip);rows=[]
    for row in ip['rows']:
        s=row['spec']
        if s['axis']!='inner_person':continue
        representative=s['architecture']=='reve' or s.get('adaptation')=='random_full'
        if representative and row['seed']!=3401:continue
        if s['architecture']=='reve' and s['adaptation']!='pretrained_full':continue
        unit={'inner':row,'outer':ip['baselines'][s['baseline_id']],'updates':UPDATES,'regimes':REGIMES,
              'design_sha256':B.sha(NOTE)}
        unit['id']='ALN34E_'+hashlib.sha256(B.dumps(unit).encode()).hexdigest()[:16];rows.append(unit)
    assert len(rows)==80
    body={'version':'ALN34_EPISODE_v1','created':datetime.now().astimezone().isoformat(),'rows':rows,
          'sources':sources(),'inner_plan_sha256':B.sha(I.PLAN),'store':str(STORE)}
    if PLAN.exists():
        old=json.loads(PLAN.read_text());assert all(old[k]==v for k,v in body.items() if k!='created')
    else:
        STORE.mkdir(parents=True,exist_ok=True,mode=0o700);B.write(PLAN,body);PLAN.chmod(0o444)
    print('Registered80 episode bundles /320 paired source continuations',B.sha(PLAN),flush=True)


def verify(plan):
    assert plan['sources']==sources() and plan['inner_plan_sha256']==B.sha(I.PLAN),'frozen episode source drift'


def ready(unit,probe_root=None):return D.ready({'inner_source':unit['inner']},probe_root)


def anchors(bundle,items,first_query=None):
    stride=max(bundle.grid,(bundle.bt.seg_len//8)//bundle.grid*bundle.grid)
    return [(s,int(t)) for s in items for t in np.arange(0,bundle.bt.seg_len,stride)[:8]
            if first_query is None or s['e0']+int(t)+int(round(.6*bundle.bt.fs))<=first_query]


def tensor_batch(bundle,items):
    bt=bundle.bt
    e=torch.tensor([s['e0']+t for s,t in items],device=bt.dev)
    a=torch.tensor([s['s0']+t for s,t in items],device=bt.dev)
    keys=torch.tensor([int(hashlib.sha256(s['uid'].encode()).hexdigest()[:12],16)*1000+t for s,t in items],device=bt.dev)
    if bundle.local:x=bt.patches(e)
    else:x=bt.windows(torch.tensor([s['e0'] for s,t in items],device=bt.dev),torch.tensor([[t] for s,t in items],device=bt.dev))
    with torch.no_grad():v=bundle.head(bt.audio(a))
    return x,v,keys


def cpu_state(model):return {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}


def atomic_torch(path,value):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);torch.save(value,str(path)+'.tmp');os.replace(str(path)+'.tmp',path)


def continue_source(bundle,regime,dest,initial,updates,probe=False):
    from auditory_alignment.train import Objective
    started=time.time();path=dest/f'{regime}.pt';resume=dest/f'{regime}_resume.pt'
    if path.is_file():
        state=torch.load(path,map_location=bundle.bt.dev,weights_only=False)
        assert state['source_sha256']==B.sha(__file__) and state['updates']==updates
        return state['ledger']
    model=bundle.model;model.load_state_dict(initial);model.requires_grad_(True).eval()
    params=list(model.parameters());lr={'lag_local_tokens':1e-4,'cbramod':3e-5,'reve':1e-6}[bundle.row['spec']['architecture']]
    opt=torch.optim.AdamW(params,lr=lr,weight_decay=1e-4)
    sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,updates)
    rng=np.random.default_rng(bundle.row['seed']+22000)
    people=sorted(bundle.bt.train_p);by={}
    for p in people:
        items=bundle.items(p,'fit')
        if len(items)>=6:
            support,query=D.split_items(items,.3)
            if len(anchors(bundle,support,query[0]['e0']))>=2:by[p]=(support,query)
    if not by:raise ValueError('no disjoint source-person episode')
    people=sorted(by)
    objective=Objective({'objective':'NCE','config':{'temperature':.1}},torch.zeros(4,32,device=bundle.bt.dev),torch.zeros(4,32,device=bundle.bt.dev))
    ledger={'regime':regime,'encoder_updates':0,'support_steps':0,'query_anchors':0,'support_eligible_anchors':0,
            'source_people':len(people),'learning_rate':lr,'sham_support':regime=='ordinary','losses':[],'source_ids':sorted(bundle.coh.participants[p]['id'] for p in people)}
    begin=0
    if resume.is_file():
        state=torch.load(resume,map_location=bundle.bt.dev,weights_only=False)
        assert state['source_sha256']==B.sha(__file__)
        model.load_state_dict(state['model']);opt.load_state_dict(state['optimizer']);sched.load_state_dict(state['scheduler'])
        rng.bit_generator.state=state['rng'];ledger=state['ledger'];begin=ledger['encoder_updates']
    for step in range(begin,updates):
        p=people[int(rng.integers(len(people)))];support,query=by[p]
        model.requires_grad_(False).eval()
        adapted,n=bundle.fit_adapter('lowrank_spatial',support,query,1 if probe else 3,bundle.row['seed']+30000+step)
        for name,param in adapted.named_parameters():
            if not name.startswith('base.'):param.requires_grad_(False)
        model.requires_grad_(True).eval()
        available=anchors(bundle,query)
        chosen=[available[i] for i in rng.choice(len(available),size=min(64,len(available)),replace=False)]
        x,v,keys=tensor_batch(bundle,chosen)
        u=(adapted if regime=='episode' else model)(x)
        loss,_=objective(u,v,keys=keys)
        if not torch.isfinite(loss):raise FloatingPointError('nonfinite episode query loss')
        opt.zero_grad();loss.backward();gn=torch.nn.utils.clip_grad_norm_(params,5.)
        if not torch.isfinite(gn):raise FloatingPointError('nonfinite episode gradient')
        opt.step();sched.step()
        ledger['encoder_updates']=step+1;ledger['support_steps']+=1 if probe else 3
        ledger['query_anchors']+=len(chosen);ledger['support_eligible_anchors']+=n
        ledger['losses'].append(float(loss.detach()))
        del adapted,x,u,v,loss
        if (step+1)%20==0 or step+1==updates:
            atomic_torch(resume,{'model':model.state_dict(),'optimizer':opt.state_dict(),'scheduler':sched.state_dict(),
                                 'rng':rng.bit_generator.state,'ledger':ledger,'source_sha256':B.sha(__file__)})
    num=den=0.
    for name,param in model.named_parameters():
        old=initial[name].to(param.device);num+=float((param.detach()-old).square().sum());den+=float(old.square().sum())
    ledger.update(seconds=time.time()-started,relative_parameter_change=float(np.sqrt(num)/(np.sqrt(den)+1e-12)),
                  trainable_parameters=sum(p.numel() for p in params),mode='eval with gradients; no dropout/stat updates')
    atomic_torch(path,{'model':model.state_dict(),'updates':updates,'ledger':ledger,'source_sha256':B.sha(__file__)})
    model.requires_grad_(False).eval();return ledger


def evaluate_model(bundle,people,role,probe=False):
    pool=bundle.eval_pool(role);values={}
    step_set=(0,1) if probe else STEPS
    for frac in D.FRACTIONS:
        candidates={}
        for steps in step_set:
            per={}
            for p in people:
                items=bundle.items(p,role)
                if len(items)<6:continue
                support,query=D.split_items(items,frac)
                if probe:query=query[:6]
                model,n=bundle.fit_adapter('lowrank_spatial',support,query,steps,bundle.row['seed']+p)
                per[bundle.coh.participants[p]['id']]={**bundle.evaluate(model,query,pool),'group':bundle.coh.participants[p]['group'],
                                                      'eligible_support_anchors':n,'n_support_segments':len(support)}
            if not per:raise ValueError('no valid evaluation identity')
            candidates[str(steps)]={'per_participant':per,'mean_native_true_nll':float(np.mean([x['native']['true_nll_bits'] for x in per.values()]))}
        values[str(frac)]=candidates
    return values


def run_unit(unit,probe_root=None):
    started=time.time();probe=bool(probe_root);ip=json.loads(I.PLAN.read_text());I.verify(ip)
    assert ready(unit,probe_root)
    dest=STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'production')/unit['id']
    output={'status':'running','id':unit['id'],'unit':unit,'probe':probe,'stages':{},'plan_sha256':B.sha(PLAN)}
    for stage in ('inner','outer'):
        row=unit['inner'] if stage=='inner' else unit['outer']['row']
        root=(Path(probe_root) if probe else I.BASE) if stage=='inner' else Path(core.OUT)
        bundle,prov=D.rebuild(row,root,ip if stage=='inner' else None,probe and stage=='inner')
        if stage=='outer':assert prov['record_sha256']==unit['outer']['record_sha256'] and prov['checkpoint_sha256']==unit['outer']['checkpoint_sha256']
        role='es' if stage=='inner' else 'test'
        ids=ip['splits'][unit['inner']['spec']['split_key']]['inner_ids'] if stage=='inner' else [p['id'] for p in bundle.coh.participants if p['fold']==row['subject_fold']]
        people=[i for i,p in enumerate(bundle.coh.participants) if p['id'] in ids]
        if probe:people=people[:1]
        initial=cpu_state(bundle.model)
        values={'source':evaluate_model(bundle,people,role,probe)};ledgers={}
        for regime in REGIMES:
            ledgers[regime]=continue_source(bundle,regime,dest/stage,initial,2 if probe else UPDATES,probe)
            state=torch.load(dest/stage/f'{regime}.pt',map_location=bundle.bt.dev,weights_only=False)
            bundle.model.load_state_dict(state['model']);bundle.model.requires_grad_(False).eval()
            changed=D.Bundle(row,bundle.record,bundle.coh,bundle.bt,bundle.model,bundle.head,bundle.grid,bundle.local)
            values[regime]=evaluate_model(changed,people,role,probe)
            del changed,state
        output['stages'][stage]={'provenance':prov,'candidates':values,'training':ledgers,
                                'checkpoints':{r:B.sha(dest/stage/f'{r}.pt') for r in REGIMES}}
        del bundle,initial;gc.collect();torch.cuda.empty_cache()
    choices={}
    for regime in REGIMES:
        choices[regime]={}
        for frac in map(str,D.FRACTIONS):
            losses={f'{source}/{step}':val['mean_native_true_nll'] for source in ('source',regime)
                    for step,val in output['stages']['inner']['candidates'][source][frac].items()}
            # In insertion order, update0 and fewer support steps win exact ties.
            chosen=min((v,i,k) for i,(k,v) in enumerate(losses.items()))[2]
            source,step=chosen.split('/')
            choices[regime][frac]={'chosen':chosen,'inner_risks':losses,
                                   'outer':output['stages']['outer']['candidates'][source][frac][step]}
    output.update(status='complete',choices=choices,job=os.environ['SLURM_JOB_ID'],seconds=time.time()-started,
                  gpu_peak_mb=torch.cuda.max_memory_allocated()/2**20)
    target=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE/'units'
    B.write(target/f'{unit["id"]}.json',output);print(unit['id'],'complete',round(time.time()-started,1),'probe',probe,flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--unit')
    ap.add_argument('--probe-root',type=Path);ap.add_argument('--smoke-receipt',type=Path)
    args=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if args.make_plan:make_plan();return
    plan=json.loads(PLAN.read_text());verify(plan)
    if args.unit:run_unit(next(u for u in plan['rows'] if u['id']==args.unit),args.probe_root);return
    if args.probe_root:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for arch in ('lag_local_tokens','cbramod','reve'):
                unit=next(u for u in plan['rows'] if u['inner']['spec']['architecture']==arch and ready(u,args.probe_root))
                run_unit(unit,args.probe_root);receipt['units'].append(unit['id'])
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    r=json.loads(args.smoke_receipt.read_text());assert r['status']=='pass' and r['plan_sha256']==B.sha(PLAN)
    for unit in plan['rows']:
        if not ready(unit) or (BASE/'units'/f'{unit["id"]}.json').exists():continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as f:
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            rc=subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.episode_training','--unit',unit['id']]).returncode
            if rc:
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('episode unit failed')


if __name__=='__main__':main()
