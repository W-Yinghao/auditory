"""S35_EPISODE_PRESSURE: matched 20/100-step first-order source episodes."""
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
import torch
from torch.nn import functional as F

from ..aln34 import learning_budget as B, episode_training as E, adaptation_policy as D
from . import support_contract as K, support_runtime as R, support_coverage as S

BASE=R.ROOT/'episode_pressure_v1'
PLAN=BASE/'plan.json'
NOTE=Path(R.core.REPO)/'docs/auditory_alignment_v3/aln35/EPISODE_PRESSURE_DESIGN.md'
STORE=R.STORE/'episode_pressure_v1'
PRESSURES=(20,100)
REGIMES=('ordinary','episode')
TARGET_STEPS=(0,5,20)
ENCODER_UPDATES=100


def sources():
    out=R.source_files(__file__,NOTE)
    out[str(Path(S.__file__).relative_to(R.core.REPO))]=B.sha(S.__file__)
    return out


def make_plan():
    support_plan=R.read(S.PLAN);S.verify(support_plan);code=sources();rows=[]
    for source in R.selected_sources():
        for pressure in PRESSURES:
            row=source['outer']['row']
            unit={'workpackage_id':'S35_EPISODE_PRESSURE','design_version':'v1', 'source':source,
                  'code_sha256':K.digest(code),'support_binding_sha256':B.sha(S.GEOMETRY),
                  'objective':'NCE','seed':3401,'outer_fold':row['subject_fold'],'content_fold':row.get('content_fold'),
                  'support_steps':pressure,'encoder_updates':ENCODER_UPDATES,'regimes':list(REGIMES),
                  'adapter':'input lowrank_spatial rank4 A~N(0,.01), B=0, Adam1e-3',
                  'encoder_lr':1e-4 if source['architecture']=='lag_local_tokens' else 3e-5,
                  'encoder_optimizer':'AdamW weight_decay1e-4,100-update cosine,eval with gradients',
                  'approximation':'first order; adapted A/B frozen during query encoder gradient',
                  'target_steps':list(TARGET_STEPS),'target_support':['U10 five draws','U30'],
                  'source_sampling':'identical people/P/Q/sparse anchors per paired regime; ordinary sham adapter trained identically',
                  'target_coordinates':'original fixed audio32 / frozen native private class prototypes',
                  'selection_roles':'independent source-inner persons only; DTU original source-ES content, never outer-test content',
                  'comparison_version':'exploratory matched pressure; each pressure fixed20 and selected policy separately'}
            unit['id']='ALN35EPI_'+K.digest(unit)[:16];rows.append(unit)
    body={'version':'S35_EPISODE_PRESSURE_v1','created':datetime.now().astimezone().isoformat(),
          'rows':rows,'sources':code,'support_binding_sha256':B.sha(S.GEOMETRY), 'support_plan_sha256':B.sha(S.PLAN),
          'expected_units':60,'expected_people':{'dtu':44,'private_bdf':64},
          'families':{'fixed_terms':['episode-ordinary at target20','episode-source at target20','ordinary-source at target20'],
                      'selected_terms':['selected(source,episode)-selected(source,ordinary)'],
                      'stratification':['dataset','architecture','readout','metric','source_support_steps'],
                      'within_identity_first':'U10 five draws then repeated DTU content folds',
                      'statistics':'exploratory 4000 group-stratified whole-person bootstrap; fixed-SE max-|z*|',
                      'policy_ties':'source before continuation; then lower target adapter steps',
                      'sign':'risk reference-candidate; AUC candidate-reference'},
          'source_only_diagnostics':['BA norm','input/representation relative change','probability TV','true objective NLL',
                                     'support gradient','encoder gradient direction cosine','actual optimizer/sample counts'],
          'store':str(STORE)}
    if PLAN.exists():assert all(R.read(PLAN)[k]==v for k,v in body.items() if k!='created'),'immutable episode plan drift'
    else:B.write(PLAN,body);PLAN.chmod(0o444)
    B.write(BASE/'readiness.json',{'plan_sha256':B.sha(PLAN),'ready_units':[u['id'] for u in rows if R.ready(u['source'],True)],
                                'dependency_missing':[u['id'] for u in rows if not R.ready(u['source'],True)]})
    print('Registered',len(rows),'pressure bundles /240 paired continuations',B.sha(PLAN),flush=True)


def verify(plan):
    assert plan['sources']==sources(),'frozen S35 episode source drift'
    assert plan['support_binding_sha256']==B.sha(S.GEOMETRY) and plan['support_plan_sha256']==B.sha(S.PLAN)


def tensor_cosine(first,second):
    dot=sum(float((a.double()*b.double()).sum()) for a,b in zip(first,second))
    na=sum(float(a.double().square().sum()) for a in first)
    nb=sum(float(b.double().square().sum()) for b in second)
    return dot/np.sqrt(na*nb) if na>0 and nb>0 else None


def freeze_adapter(adapter):
    for name,p in adapter.named_parameters():
        if not name.startswith('base.'):p.requires_grad_(False)


def source_episodes(bundle,dataset):
    eligible={};unavailable=[]
    if dataset=='dtu':
        for person in sorted(bundle.bt.train_p):
            items,split=R.split_public(bundle,person,'fit')
            support=[items[i] for i in split['pool']];query=[items[i] for i in split['query']]
            if len(E.anchors(bundle,support))>=2 and len(E.anchors(bundle,query))>=2:
                eligible[person]=(support,query)
            else:unavailable.append({'identity':bundle.coh.participants[person]['id'],'reason':'insufficient_guarded_fit_anchors'})
    else:
        for person in bundle.fd.tr:
            kid=bundle.fd.kids[person];split=K.private_split(kid,True)
            if len(split['pool']) and len(split['query']):eligible[person]=(split['pool'],split['query'])
            else:unavailable.append({'identity':kid['id'],'reason':'no_guarded_fit_support_or_query'})
    if not eligible:raise ValueError('no source-only episode has usable guarded support and query')
    return eligible,unavailable


def prediction_probabilities(u,target,dataset):
    # Diagnostics only: same current-query targets and first-order model state.
    # The actual registered Objective remains authoritative for the update.
    if dataset=='private_bdf':return torch.softmax(u@F.normalize(target,dim=-1).T/.1,dim=-1)
    return torch.softmax(u@target.T/.1,dim=-1)


def continue_source(bundle,unit,stage,regime,dest,initial,smoke=False):
    dataset=unit['source']['dataset'];pressure=unit['support_steps'];updates=2 if smoke else ENCODER_UPDATES
    final=dest/f'{regime}.pt';resume=dest/f'{regime}_resume.pt';signature=B.sha(PLAN)
    if final.exists():
        saved=torch.load(final,map_location='cpu',weights_only=False)
        assert saved['plan_sha256']==signature and saved['updates']==updates and saved['pressure']==pressure
        return saved['ledger']
    model=bundle.model;model.load_state_dict(initial);model.requires_grad_(True).eval()
    pars=list(model.parameters());lr=unit['encoder_lr']
    optimizer=torch.optim.AdamW(pars,lr=lr,weight_decay=1e-4)
    scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,updates)
    eligible,unavailable=source_episodes(bundle,dataset);people=sorted(eligible)
    rng=np.random.default_rng(3401+61000)
    if dataset=='dtu':
        from auditory_alignment.train import Objective
        obj=Objective({'objective':'NCE','config':{'temperature':.1}},torch.zeros(4,32,device=bundle.bt.dev),torch.zeros(4,32,device=bundle.bt.dev))
        getid=lambda i:bundle.coh.participants[i]['id']
    else:obj=bundle.objective;getid=lambda i:bundle.fd.kids[i]['id']
    ledger={'regime':regime,'source_support_steps':pressure,'encoder_updates':0,'support_optimizer_steps':0,
            'support_exposures':0,'query_exposures':0,'diagnostic_query_forwards':0,
            'source_ids':[getid(i) for i in people],'unavailable_source_episodes':unavailable,
            'sham_support':regime=='ordinary','lr':lr,'trainable_parameters':sum(p.numel() for p in pars),
            'mode':'eval with gradients; no dropout/statistics updates','diagnostics':[],
            'sampling_stream':[],'losses':[],'diagnostics_role':'source fit only, no outer judgement or threshold'}
    if resume.exists():
        state=torch.load(resume,map_location=bundle.bt.dev,weights_only=False)
        assert state['plan_sha256']==signature and state['pressure']==pressure
        model.load_state_dict(state['model']);optimizer.load_state_dict(state['optimizer']);scheduler.load_state_dict(state['scheduler'])
        rng.bit_generator.state=state['rng'];ledger=state['ledger']
    started=time.time()
    for update in range(ledger['encoder_updates'],updates):
        person=people[int(rng.integers(len(people)))];support,query=eligible[person]
        adapter,fit=(R.fit_public(bundle,support,pressure,3401+62000+update) if dataset=='dtu'
                     else R.fit_private_spatial(bundle,person,support,pressure,3401+62000+update))
        freeze_adapter(adapter);model.requires_grad_(True).eval()
        if dataset=='dtu':
            available=E.anchors(bundle,query)
            chosen=[available[i] for i in rng.choice(len(available),size=min(64,len(available)),replace=False)]
            x,target,keys=E.tensor_batch(bundle,chosen)
            loss_of=lambda u:obj(u,target,keys=keys)[0]
            sample_ids=[(s['uid'],int(t)) for s,t in chosen]
        else:
            chosen=rng.choice(query,size=min(64,len(query)),replace=False)
            x=bundle.bt.patches(person,torch.tensor(chosen,device=bundle.bt.dev))
            target=bundle.protos
            labels=torch.tensor(bundle.fd.kids[person]['y'][chosen],device=bundle.bt.dev)
            loss_of=lambda u:obj(u,labels=labels,prototypes=target)[0]
            sample_ids=[K.stable_key(getid(person),j) for j in chosen]
        # Compute both directions at the same source state. Both regimes pay for
        # this diagnostic; only the declared query branch supplies the update.
        ordinary_u=model(x);ordinary_loss=loss_of(ordinary_u)
        if not torch.isfinite(ordinary_loss):raise FloatingPointError('nonfinite ordinary source query')
        ordinary_grads=torch.autograd.grad(ordinary_loss,pars,allow_unused=True)
        ordinary_grads=tuple(torch.zeros_like(p) if g is None else g for p,g in zip(pars,ordinary_grads))
        base_u=ordinary_u.detach();base_loss=float(ordinary_loss.detach())
        del ordinary_u,ordinary_loss
        episode_u=adapter(x);episode_loss=loss_of(episode_u)
        if not torch.isfinite(episode_loss):raise FloatingPointError('nonfinite adapted source query')
        episode_grads=torch.autograd.grad(episode_loss,pars,allow_unused=True)
        episode_grads=tuple(torch.zeros_like(p) if g is None else g for p,g in zip(pars,episode_grads))
        adapted_u=episode_u.detach();adapted_loss=float(episode_loss.detach())
        with torch.no_grad():
            changed_x=[adapter.transform(a) for a in x] if isinstance(x,list) else [adapter.transform(x)]
            original_x=x if isinstance(x,list) else [x]
            input_num=sum(float((a-b).square().sum()) for a,b in zip(changed_x,original_x))
            input_den=sum(float(a.square().sum()) for a in original_x)
            p0=prediction_probabilities(base_u,target,dataset);p1=prediction_probabilities(adapted_u,target,dataset)
            diagnostic={'step':update+1,'source_identity':getid(person),'BA_norm':float((adapter.B@adapter.A).norm()),
                'input_relative_change':float(np.sqrt(input_num)/(np.sqrt(input_den)+1e-12)),
                'representation_relative_change':float((adapted_u-base_u).norm()/(base_u.norm()+1e-12)),
                'probability_tv':float((p1-p0).abs().sum(1).mean()/2),
                'ordinary_query_objective_nats':base_loss,'adapted_query_objective_nats':adapted_loss,
                'encoder_direction_cosine_at_same_state':tensor_cosine(ordinary_grads,episode_grads),
                'support_gradient_max':max(fit['gradient_norms'],default=0.),
                'support_gradient_last':fit['gradient_norms'][-1] if fit['gradient_norms'] else None,
                'support_effective_steps':fit['effective_adapter_steps'],
                'identity_fallback_reason':fit['identity_fallback_reason']}
        grads=ordinary_grads if regime=='ordinary' else episode_grads
        optimizer.zero_grad(set_to_none=True)
        for p,g in zip(pars,grads):p.grad=g.detach()
        norm=torch.nn.utils.clip_grad_norm_(pars,5.)
        if not torch.isfinite(norm):raise FloatingPointError('nonfinite source encoder gradient')
        optimizer.step();scheduler.step()
        ledger['encoder_updates']=update+1
        ledger['support_optimizer_steps']+=fit['effective_adapter_steps']
        ledger['support_exposures']+=fit['sample_exposures'];ledger['query_exposures']+=len(chosen)
        ledger['diagnostic_query_forwards']+=2
        ledger['diagnostics'].append(diagnostic)
        ledger['sampling_stream'].append({'identity':getid(person),'query_hash':K.digest(sample_ids),
                'support_hash':K.digest([s['uid'] for s in support] if dataset=='dtu' else [K.stable_key(getid(person),j) for j in support]),
                'support_seed':3401+62000+update})
        ledger['losses'].append(base_loss if regime=='ordinary' else adapted_loss)
        del adapter,episode_u,episode_loss,ordinary_grads,episode_grads,grads,x,target,p0,p1,changed_x,original_x
        if (update+1)%20==0 or update+1==updates:
            E.atomic_torch(resume,{'model':model.state_dict(),'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),
                'rng':rng.bit_generator.state,'ledger':ledger,'plan_sha256':signature,'pressure':pressure})
    num=sum(float((p.detach()-initial[k].to(p.device)).square().sum()) for k,p in model.named_parameters())
    den=sum(float(initial[k].square().sum()) for k,_ in model.named_parameters())
    ledger.update(seconds=time.time()-started,relative_parameter_change=float(np.sqrt(num)/(np.sqrt(den)+1e-12)),
                  gpu_peak_mb=torch.cuda.max_memory_allocated()/2**20,stream_sha256=K.digest(ledger['sampling_stream']),
                  cost_scope='same support/encoder step counts and diagnostic branches; not a claim of identical FLOPs')
    E.atomic_torch(final,{'model':model.state_dict(),'ledger':ledger,'updates':updates,'pressure':pressure,'plan_sha256':signature})
    model.requires_grad_(False).eval()
    return ledger


def episode_supports(split,identity):
    pool=split['pool']
    out={f'U10_{seed}':np.sort(np.random.default_rng(seed).choice(pool,size=split['n10'],replace=False)) for seed in K.SAMPLING_SEEDS}
    out['U30']=pool.copy()
    return out


def evaluate_public(bundle,people,role,binding,unit,smoke):
    pool=bundle.eval_pool(role);values={}
    for person in (people[:1] if smoke else people):
        identity=bundle.coh.participants[person]['id'];items,split=R.split_public(bundle,person,role)
        R.check_binding(binding,split,identity,'dtu',unit['content_fold'],role)
        query=[items[i] for i in split['query']]
        entry={'group':bundle.coh.participants[person]['group'],'status':'complete' if query else 'no_query','supports':{}}
        values[identity]=entry
        if not query:continue
        base=bundle.reps.u([s['e0'] for s in query])
        for strategy,idx in episode_supports(split,identity).items():
            support=[items[j] for j in idx];candidates={}
            for steps in TARGET_STEPS:
                model,ledger=R.fit_public(bundle,support,steps,3401+person+63000)
                u=bundle.reps_of(model).u([s['e0'] for s in query]) if ledger['effective_adapter_steps'] else base.copy()
                candidates[str(steps)]={'metrics':{mode:R.public_metrics(bundle,u,query,pool,mode,base) for mode in ('native','unified')},
                                         'adaptation':ledger}
                del model
            entry['supports'][strategy]={'support':S.support_receipt(identity,split,idx,strategy,items=items),'candidates':candidates}
    return {'per_participant':values,'readouts':{'tau':bundle.readout.tau,'unified_alpha':float(bundle.readout.alpha_uni)}}


def evaluate_private(bundle,binding,smoke):
    values={}
    for person in (bundle.fd.te[:1] if smoke else bundle.fd.te):
        kid=bundle.fd.kids[person];identity=kid['id'];split=K.private_split(kid)
        R.check_binding(binding,split,identity,'private_bdf');query=split['query']
        entry={'group':kid['group'],'status':'complete' if len(query) else 'no_query','supports':{}}
        values[identity]=entry
        if not len(query):continue
        base=bundle.representations(person,query)
        for strategy,support in episode_supports(split,identity).items():
            candidates={}
            for steps in TARGET_STEPS:
                model,ledger=R.fit_private_spatial(bundle,person,support,steps,3401+person+63000)
                u=bundle.representations(person,query,model) if ledger['effective_adapter_steps'] else base.copy()
                candidates[str(steps)]={'metrics':{mode:R.private_metrics(bundle,u,kid,query,mode,base) for mode in ('native','linear')},
                                        'adaptation':ledger}
                del model
            entry['supports'][strategy]={'support':S.support_receipt(identity,split,support,strategy,kid=kid),'candidates':candidates}
    return {'per_participant':values,'readouts':bundle.readout_receipt}


def identity_risks(result,strategy,step,mode):
    out={}
    names=[f'U10_{seed}' for seed in K.SAMPLING_SEEDS] if strategy=='U10' else ['U30']
    for identity,row in result['per_participant'].items():
        if row['status']!='complete':continue
        vals=[row['supports'][name]['candidates'][str(step)]['metrics'][mode]['nll_bits'] for name in names]
        if all(v is not None and np.isfinite(v) for v in vals):out[identity]=float(np.mean(vals))
    return out


def choose(inner,outer,dataset):
    choices={}
    for mode in ('native','unified') if dataset=='dtu' else ('native','linear'):
        choices[mode]={}
        for strategy in ('U10','U30'):
            choices[mode][strategy]={}
            for regime in REGIMES:
                candidates=[(name,step) for name in ('source',regime) for step in TARGET_STEPS]
                risk_tables={f'{name}/{step}':identity_risks(inner[name],strategy,step,mode) for name,step in candidates}
                common=set.intersection(*(set(v) for v in risk_tables.values()))
                if not common:
                    choices[mode][strategy][regime]={'status':'no_complete_inner_identities','candidate_risks':risk_tables}
                    continue
                risks={name:float(np.mean([per[i] for i in sorted(common)])) for name,per in risk_tables.items()}
                selected=min(risks,key=risks.get);name,step=selected.split('/')
                choices[mode][strategy][regime]={'status':'complete','chosen':selected,'inner_risks':risks,
                    'inner_complete_ids':sorted(common),'inner_per_identity_risks':risk_tables,
                    'zero_step_selected':int(step)==0,'source_fallback_selected':name=='source',
                    'outer_per_identity_nll':identity_risks(outer[name],strategy,int(step),mode),
                    'outer_result_location':{'regime':name,'target_steps':int(step),'support':strategy,'readout':mode}}
    return choices


def update_cosine(dest,initial):
    ordinary=torch.load(dest/'ordinary.pt',map_location='cpu',weights_only=False)['model']
    episode=torch.load(dest/'episode.pt',map_location='cpu',weights_only=False)['model']
    keys=[k for k in initial if torch.is_floating_point(initial[k])]
    a=[ordinary[k]-initial[k] for k in keys];b=[episode[k]-initial[k] for k in keys]
    return tensor_cosine(a,b)


def run_unit(unit,smoke=False):
    assert R.ready(unit['source'],True),'independent inner source unavailable'
    started=time.time();binding=R.read(S.GEOMETRY);dataset=unit['source']['dataset']
    dest=STORE/('probes/'+os.environ['SLURM_JOB_ID'] if smoke else 'production')/unit['id']
    output={'id':unit['id'],'unit':unit,'probe':smoke,'stages':{},'plan_sha256':B.sha(PLAN)}
    for stage in ('inner','outer'):
        if dataset=='dtu':bundle,people,role,provenance=R.public_bundle(unit['source'],stage)
        else:bundle,provenance=R.private_bundle(unit['source'],stage)
        initial=E.cpu_state(bundle.model)
        evaluate=lambda: evaluate_public(bundle,people,role,binding,unit,smoke) if dataset=='dtu' else evaluate_private(bundle,binding,smoke)
        values={'source':evaluate()};ledgers={}
        for regime in REGIMES:
            ledgers[regime]=continue_source(bundle,unit,stage,regime,dest/stage,initial,smoke)
            state=torch.load(dest/stage/f'{regime}.pt',map_location=bundle.bt.dev,weights_only=False)
            bundle.model.load_state_dict(state['model']);bundle.model.requires_grad_(False).eval()
            if dataset=='dtu':
                bundle=D.Bundle(bundle.row,bundle.record,bundle.coh,bundle.bt,bundle.model,bundle.head,bundle.grid,bundle.local)
            else:bundle.refresh_readouts()
            values[regime]=evaluate();del state
        assert ledgers['ordinary']['stream_sha256']==ledgers['episode']['stream_sha256'],'paired sampling stream mismatch'
        assert ledgers['ordinary']['support_optimizer_steps']==ledgers['episode']['support_optimizer_steps']
        assert ledgers['ordinary']['query_exposures']==ledgers['episode']['query_exposures']
        output['stages'][stage]={'values':values,'training':ledgers,'source_provenance':provenance,
                    'paired_final_update_direction_cosine':update_cosine(dest/stage,initial),
                    'checkpoint_hashes':{name:B.sha(dest/stage/f'{name}.pt') for name in REGIMES}}
        del bundle,initial;R.cleanup()
    output.update(status='complete',choices=choose(output['stages']['inner']['values'],output['stages']['outer']['values'],dataset),
                  seconds=time.time()-started,job=os.environ['SLURM_JOB_ID'],device=torch.cuda.get_device_name(0),
                  gpu_peak_mb=torch.cuda.max_memory_allocated()/2**20,
                  fixed20_location='stages/{inner|outer}/values/{source|ordinary|episode}/per_participant/*/supports/*/candidates/20',
                  interpretation='source fallback and selected zero-step are separate from fixed nonzero intervention')
    target=BASE/'probes'/os.environ['SLURM_JOB_ID'] if smoke else BASE/'units'
    B.write(target/f'{unit["id"]}.json',output)
    print(unit['id'],'complete',round(time.time()-started,1),'probe',smoke,flush=True)


def fleet_status():
    status={'name':'c3_s35episode','lane':'s35_episode','state':'plan_missing','ready':0,'remaining':60,
            'slots':1,'initial':[],'submit':[]}
    if not PLAN.is_file():return status
    plan=R.read(PLAN);remaining=[u for u in plan['rows'] if not (BASE/'units'/f'{u["id"]}.json').is_file()]
    status['remaining']=len(remaining)
    if not remaining:status['state']='complete';return status
    receipts=[]
    for path in sorted((BASE/'probes').glob('*/receipt.json')):
        rec=R.read(path)
        if rec.get('status')=='pass' and rec.get('plan_sha256')==B.sha(PLAN):receipts.append(path)
    if not receipts:status['state']='engineering_probe_required';return status
    ready=[u for u in remaining if R.ready(u['source'],True) and not (BASE/'units'/f'{u["id"]}.FAILED.json').exists()]
    status.update(state='ready' if ready else 'independent_inner_source_or_failed_unit',ready=len(ready),
                  submit=['slurm/aln35_episode_pressure.sbatch','--smoke-job',receipts[-1].parent.name,'--max-units','1'])
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
                for arch in ('lag_local_tokens','cbramod'):
                    for pressure in PRESSURES:
                        unit=next(u for u in plan['rows'] if u['source']['dataset']==dataset and u['source']['architecture']==arch
                                  and u['support_steps']==pressure and R.ready(u['source'],True))
                        run_unit(unit,True);receipt['units'].append(unit['id'])
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=R.read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
    assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    count=0
    for unit in plan['rows']:
        target=BASE/'units'/f'{unit["id"]}.json'
        if target.exists() or not R.ready(unit['source'],True) or (BASE/'units'/f'{unit["id"]}.FAILED.json').exists():continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if target.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m',__spec__.name,'--unit',unit['id']]).returncode
            if rc or not target.exists():
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('episode pressure unit failed')
            count+=1
        if count>=a.max_units:break


if __name__=='__main__':main()
