"""Frozen-source, whole-pipeline inner-person strong fusion; DTU ALN3.4."""
from __future__ import annotations

import argparse
import gc
from datetime import datetime
import fcntl
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
from torch import nn
from torch.nn import functional as F

from .. import core
from . import breadth_policy as D
from . import breadth_inner as I
from . import learning_budget as B
from auditory_alignment import evaluate as E

BASE = Path(core.OUT)/'aln34/breadth_fusion_v1'
PLAN = BASE/'plan.json'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln34_breadth_fusion_v1')
NOTE = Path(core.OUT)/'aln34/PUBLIC_BREADTH_DESIGN_20261017.md'
ARMS = ('local','cb_pre','cb_random','reve_pre')
ALPHAS = (.1,10.,1000.)
WEIGHTS = (0.,.25,.5,.75,1.)
STEPS = (0,20,50,100)


def arm(row):
    s=row['spec']
    if s['architecture']=='lag_local_tokens': return 'local'
    if s['architecture']=='cbramod': return 'cb_pre' if s['adaptation']=='pretrained_full' else 'cb_random'
    return 'reve_pre' if s['adaptation']=='pretrained_full' else 'reve_random'


def sources():
    files={Path(__file__),NOTE,Path(D.__file__),Path(I.__file__),Path(B.__file__)}
    for g in ('local_support','aligned32'):
        files.update(Path(core.REPO)/d/f for d,f in core.FAMILY_CODE[g]+core.V2_DEPS)
    return {str(f.relative_to(core.REPO)):B.sha(f) for f in sorted(files)}


def make_plan():
    ip=json.loads(I.PLAN.read_text());I.verify(ip)
    groups={}
    for row in ip['rows']:
        if row['spec']['axis']!='inner_person' or arm(row) not in ARMS: continue
        key=(row['dataset'],row['seed'],row['subject_fold'],row['content_fold'])
        groups.setdefault(key,{})[arm(row)]={'inner':row,'outer':ip['baselines'][row['spec']['baseline_id']]}
    rows=[]
    for key,models in sorted(groups.items()):
        assert set(models)==set(ARMS)
        body={'dataset':key[0],'seed':key[1],'subject_fold':key[2],'content_fold':key[3],'models':models,'design_sha256':B.sha(NOTE)}
        body['id']='ALN34BF_'+hashlib.sha256(B.dumps(body).encode()).hexdigest()[:16];rows.append(body)
    assert len(rows)==15
    body={'version':'ALN34_STRONG_FUSION_v1','created':datetime.now().astimezone().isoformat(),
          'rows':rows,'sources':sources(),'inner_plan_sha256':B.sha(I.PLAN),'store':str(STORE)}
    if PLAN.exists():
        old=json.loads(PLAN.read_text());assert all(old[k]==v for k,v in body.items() if k!='created')
    else:
        STORE.mkdir(parents=True,exist_ok=True,mode=0o700)
        B.write(PLAN,body);PLAN.chmod(0o444)
    print(f'Registered15 strong-fusion bundles; {B.sha(PLAN)}',flush=True)


def verify(plan):
    assert plan['sources']==sources() and plan['inner_plan_sha256']==B.sha(I.PLAN),'frozen provenance drift'


def ready(unit,probe_root=None):
    models={k:v for k,v in unit['models'].items() if not probe_root or k!='cb_random'}
    return all(D.ready({'inner_source':v['inner']},probe_root) for v in models.values())


def normalize(x):
    return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-12)


def probability(s,tau):
    z=np.asarray(s,dtype=np.float64)/tau;z-=z.max(1,keepdims=True)
    p=np.exp(z);return p/p.sum(1,keepdims=True)


def mix(p,q,weight):
    assert p.shape==q.shape and 0<=weight<=1
    return weight*p+(1-weight)*q


def choose(losses):
    finite=[(float(v),i,k) for i,(k,v) in enumerate(losses.items()) if np.isfinite(v)]
    if not finite: raise ValueError('no finite development candidate')
    return min(finite)[2]


def person_metrics(scores,own,people):
    result={}
    for p in sorted(set(people.tolist())):
        mask=people==p;s=scores[mask];o=own[mask]
        true=E._metrics(s,o,1.)
        mismatch=E._metrics(np.roll(s,1,axis=0),o,1.)
        result[p]={'true_nll_bits':true['logloss_bits'],'mismatch_gain_bits':mismatch['logloss_bits']-true['logloss_bits'],
                   'rank_pct':true['rank_pct'],'top1':true['top1'],'n_query':true['n_queries'],'n_candidates':true['n_candidates']}
    return result


def mean_risk(values):
    return float(np.mean([v['true_nll_bits'] for v in values.values()]))


def snapshot_cache(row,root,inner_plan=None,probe=False):
    """Cache a source once; every fitting row belongs to source-training people."""
    cp=Path(root)/'ckpt'/f'{row["experiment_id"]}_best.pt'
    rp=Path(root)/'units'/f'{row["experiment_id"]}.json'
    sig={'source':row,'record_sha256':B.sha(rp),'checkpoint_sha256':B.sha(cp),'probe':probe,
         'fusion_source_sha256':B.sha(__file__),'inner_plan_sha256':B.sha(I.PLAN)}
    key=hashlib.sha256(B.dumps(sig).encode()).hexdigest()
    dest=STORE/('probes' if probe else 'cache')/key
    meta=dest/'meta.json'
    if meta.is_file():
        old=json.loads(meta.read_text());assert old['signature']==sig
        assert old['arrays_sha256']==B.sha(dest/'arrays.npz')
        with np.load(dest/'arrays.npz',allow_pickle=False) as z: arrays={k:z[k] for k in z.files}
        return arrays,old
    bundle,provenance=D.rebuild(row,root,inner_plan,bool(probe and inner_plan))
    rng=np.random.default_rng(row['seed']+1000)
    train=[s for s in bundle.segs if s['p'] in bundle.bt.train_p and s['kind']=='ss' and s['role'] in ('fit','es')]
    picked=rng.choice(len(train),size=min(400,len(train)),replace=False)
    selected=[train[i] for i in picked]
    cal=[s for s in bundle.segs if s['p'] in bundle.bt.train_p and s['kind']=='ss' and s['role']=='es']
    cal=[cal[i] for i in rng.choice(len(cal),size=min(300,len(cal)),replace=False)]
    if probe: selected=selected[:64];cal=cal[:24]
    role='es' if inner_plan else 'test'
    held=inner_plan['splits'][row['spec']['split_key']]['inner_ids'] if inner_plan else [p['id'] for p in bundle.coh.participants if p['fold']==row['subject_fold']]
    people=[i for i,p in enumerate(bundle.coh.participants) if p['id'] in held]
    if probe: people=people[:1]
    queries=[]
    for p in people:
        q=bundle.items(p,role);queries.extend(q[:6] if probe else q)
    assert queries and not set(people)&set(bundle.bt.train_p)
    q_uid,qpool=bundle.pool(role);c_uid,cpool=bundle.pool('es')
    A={}
    for name,items in (('train',selected),('cal',cal),('query',queries)):
        A[name+'_u']=bundle.reps.u([s['e0'] for s in items])
        A[name+'_e0']=np.array([s['e0'] for s in items],dtype=np.int64)
    A['train_v'],A['train_a']=bundle.reps.va([s['s0'] for s in selected])
    A['train_roles']=np.array([s['role'] for s in selected])
    A['cal_v'],A['cal_a']=bundle.reps.va([s['s0'] for s in cpool])
    A['query_v'],A['query_a']=bundle.reps.va([s['s0'] for s in qpool])
    A['cal_own']=np.array([c_uid[s['uid']] for s in cal])
    A['query_own']=np.array([q_uid[s['uid']] for s in queries])
    A['query_people']=np.array([bundle.coh.participants[s['p']]['id'] for s in queries])
    for which in ('cal','query'):
        for mode in ('native','unified'):
            A[f'{which}_direct_{mode}']=bundle.readout.scores(A[which+'_u'],A[which+'_v'],A[which+'_a'],mode)/bundle.readout.tau[mode]
    metadata={'signature':sig,'source_provenance':provenance,'train_ids':sorted(bundle.coh.participants[i]['id'] for i in bundle.bt.train_p),
              'evaluation_ids':held,'groups':{p['id']:p['group'] for p in bundle.coh.participants},'role':role}
    dest.mkdir(parents=True,exist_ok=True,mode=0o700)
    np.savez_compressed(dest/'arrays.npz',**A)
    metadata['arrays_sha256']=B.sha(dest/'arrays.npz');B.write(meta,metadata)
    del bundle;gc.collect();torch.cuda.empty_cache()
    return A,metadata


def assert_aligned(local,other):
    for name in ('train_e0','cal_e0','query_e0','train_roles','query_people','query_own','cal_own'):
        if not np.array_equal(local[name],other[name]): raise ValueError(f'paired source access mismatch:{name}')
    for name in ('train_v','query_v','cal_v','train_a','query_a','cal_a'):
        if not np.allclose(local[name],other[name],atol=2e-6,rtol=2e-6):
            raise ValueError(f'branches do not share fixed sound coordinates:{name}')


def fit_ridge(x,y,alpha):
    x=x.reshape(-1,x.shape[-1]).astype(np.float64);y=y.reshape(-1,y.shape[-1]).astype(np.float64)
    return E._ridge(x,y,[alpha])[0]


def apply_ridge(x,b):
    return E._apply(b,x.reshape(-1,x.shape[-1])).reshape(*x.shape[:-1],-1)


def candidate_scores(local,representations):
    """Original source-only unified bridge and temperature contract for a new P."""
    u=representations['train'];a=local['train_a'];roles=local['train_roles']
    x=u.reshape(-1,u.shape[-1]);y=a.reshape(-1,a.shape[-1]);mu=y.mean(0);sd=y.std(0)+1e-8;y=(y-mu)/sd
    r=np.repeat(roles,u.shape[1]);fit=r=='fit';es=r=='es'
    if not fit.any() or not es.any(): raise ValueError('fit and ES both required')
    _,alpha=E._ridge(x[fit],y[fit],np.logspace(-4,8,13),x[es],y[es],crit='corr')
    bridge=E._ridge(x,y,[alpha])[0]
    scores={}
    for which in ('cal','query'):
        p=representations[which];pred=apply_ridge(p,bridge)
        scores[which]={
            'native':np.einsum('qtd,ctd->qc',p,local[which+'_v'])/p.shape[1],
            'unified':np.einsum('qtd,ctd->qc',E._zt(pred),E._zt((local[which+'_a']-mu)/sd))/(pred.shape[1]*pred.shape[2])}
    ro=object.__new__(E.Readouts);ro.calibrate(scores['cal'],local['cal_own'])
    return {k:scores['query'][k]/ro.tau[k] for k in ('native','unified')},{'alpha_unified':float(alpha),'temperature':ro.tau}


def residual_states(local,other,seed,steps=STEPS):
    torch.manual_seed(seed)
    dev=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    x=torch.as_tensor(other['train_u'].reshape(-1,32),device=dev)
    u=torch.as_tensor(local['train_u'].reshape(-1,32),device=dev)
    v=torch.as_tensor(local['train_v'].reshape(-1,32),device=dev)
    model=nn.Linear(32,32).to(dev);nn.init.zeros_(model.weight);nn.init.zeros_(model.bias)
    opt=torch.optim.Adam(model.parameters(),lr=1e-3)
    rng=np.random.default_rng(seed)
    states={0:{'w':np.zeros((32,32),dtype=np.float32),'b':np.zeros(32,dtype=np.float32)}}
    for step in range(1,max(steps)+1):
        ix=rng.choice(len(x),size=min(512,len(x)),replace=False)
        pred=F.normalize(u[ix]+model(x[ix]),dim=-1)
        loss=-(pred*v[ix]).sum(-1).mean()
        if not torch.isfinite(loss): raise FloatingPointError('nonfinite residual objective')
        opt.zero_grad();loss.backward();opt.step()
        if step in steps: states[step]={'w':model.weight.detach().cpu().numpy().copy(),'b':model.bias.detach().cpu().numpy().copy(),'loss':float(loss.detach())}
    return states


def residual_diagnostics(u,r,p,base_scores,new_scores,people):
    dot=(r*u).sum(-1,keepdims=True)/(np.square(u).sum(-1,keepdims=True)+1e-12)
    parallel=dot*u;orthogonal=r-parallel;norm=np.linalg.norm(u,axis=-1)+1e-12
    per={}
    for who in sorted(set(people.tolist())):
        m=people==who
        value={'relative_residual':float(np.mean(np.linalg.norm(r[m],axis=-1)/norm[m])),
               'relative_parallel':float(np.mean(np.linalg.norm(parallel[m],axis=-1)/norm[m])),
               'relative_orthogonal':float(np.mean(np.linalg.norm(orthogonal[m],axis=-1)/norm[m])),
               'before_normalization_change':float(np.mean(np.linalg.norm(r[m],axis=-1))),
               'after_normalization_change':float(np.mean(np.linalg.norm(p[m]-u[m],axis=-1))),
               'angle_radians':float(np.mean(np.arccos(np.clip((normalize(u[m])*p[m]).sum(-1),-1,1))))}
        for k in ('native','unified'):
            a,b=base_scores[k][m],new_scores[k][m]
            value[k]={'mean_abs_calibrated_score_change':float(np.mean(np.abs(a-b))),
                      'probability_total_variation':float(np.mean(np.abs(probability(a,1)-probability(b,1)).sum(1)/2)),
                      'argmax_change':float(np.mean(a.argmax(1)!=b.argmax(1)))}
        per[who]=value
    return per


def evaluate_pair(local,other,seed,probe=False):
    assert_aligned(local,other)
    direct={k:local['query_direct_'+k] for k in ('native','unified')}
    records={};diagnostics={}
    def put(key,scores,meta=None):
        records[key]={'per_person':{k:person_metrics(s,local['query_own'],local['query_people']) for k,s in scores.items()},'fit':meta or {}}
    put('local_direct',direct)
    put('fm_direct',{k:other['query_direct_'+k] for k in ('native','unified')})
    for w in WEIGHTS:
        put(f'probability/{w}',{k:np.log(np.maximum(mix(probability(local['query_direct_'+k],1),probability(other['query_direct_'+k],1),w),1e-300)) for k in direct})
    for family in ('sc_local','common_linear'):
        for alpha in ALPHAS:
            features={which:local[which+'_u'] if family=='sc_local' else np.concatenate((local[which+'_u'],other[which+'_u']),axis=-1) for which in ('train','cal','query')}
            b=fit_ridge(features['train'],local['train_v'],alpha)
            p={k:normalize(apply_ridge(v,b)).astype(np.float32) for k,v in features.items()}
            scores,meta=candidate_scores(local,p);meta['alpha_sound']=alpha;put(f'{family}/{alpha}',scores,meta)
    states=residual_states(local,other,seed,(0,2) if probe else STEPS)
    for step,state in states.items():
        r={k:other[k+'_u']@state['w'].T+state['b'] for k in ('train','cal','query')}
        p={k:normalize(local[k+'_u']+r[k]) for k in r}
        if step==0:
            scores,meta=direct,{'epoch_zero_exact_direct':True}
        else: scores,meta=candidate_scores(local,p)
        key=f'residual/{step}';put(key,scores,meta)
        diagnostics[key]=residual_diagnostics(local['query_u'],r['query'],p['query'],direct,scores,local['query_people'])
        # Same-person temporal mismatch; fixed local query and candidate pool.
        changed=other['query_u'].copy()
        for who in set(local['query_people'].tolist()):
            mask=local['query_people']==who;changed[mask]=np.roll(changed[mask],1,axis=0)
        mismatched=dict(p);mismatched['query']=normalize(local['query_u']+changed@state['w'].T+state['b'])
        if step==0: ms=direct
        else: ms,_=candidate_scores(local,mismatched)
        put(f'residual_mismatched_fm/{step}',ms,{'sensitivity':'test intervention; same-person segment shift; local held fixed'})
    return records,diagnostics


def select_family(records,family,mode):
    keys=[k for k in records if k.startswith(family+'/')]
    return choose({k:mean_risk(records[k]['per_person'][mode]) for k in keys})


def run_unit(unit,probe_root=None):
    started=time.time();probe=bool(probe_root);I.register()
    ip=json.loads(I.PLAN.read_text());I.verify(ip)
    assert ready(unit,probe_root)
    selected_models=[k for k in ARMS if not probe or k!='cb_random']
    results={};provenance={}
    for stage in ('inner','outer'):
        arrays={};prov={}
        for key in selected_models:
            info=unit['models'][key]
            row=info['inner'] if stage=='inner' else info['outer']['row']
            root=(Path(probe_root) if probe else I.BASE) if stage=='inner' else Path(core.OUT)
            arrays[key],prov[key]=snapshot_cache(row,root,ip if stage=='inner' else None,probe)
            if stage=='outer':
                assert prov[key]['signature']['record_sha256']==info['outer']['record_sha256']
                assert prov[key]['signature']['checkpoint_sha256']==info['outer']['checkpoint_sha256']
        per={};diag={}
        for key in selected_models:
            if key=='local': continue
            per[key],diag[key]=evaluate_pair(arrays['local'],arrays[key],unit['seed'],probe)
        results[stage]={'comparisons':per,'diagnostics':diag}
        provenance[stage]=prov
        del arrays;gc.collect();torch.cuda.empty_cache()
    decisions={}
    for mode in ('native','unified'):
        # The local direct candidate is present unchanged in every pair.
        first=next(iter(results['inner']['comparisons'].values()))
        risks={'local':mean_risk(first['local_direct']['per_person']['native'])}
        risks.update({k:mean_risk(v['fm_direct']['per_person']['native']) for k,v in results['inner']['comparisons'].items()})
        decisions[mode]={'strong_single':choose(risks),'strong_single_development':risks,'pairs':{}}
        for key,record in results['inner']['comparisons'].items():
            decisions[mode]['pairs'][key]={family:select_family(record,family,mode if family=='probability' else 'native') for family in ('probability','sc_local','common_linear','residual')}
    output={'status':'complete','id':unit['id'],'unit':unit,'probe':probe,'plan_sha256':B.sha(PLAN),
            'selection_level':'whole pipeline inner-person holdout; generic historical corpus unknown',
            'decisions':decisions,'stages':results,'provenance':provenance,'seconds':time.time()-started,
            'job':os.environ['SLURM_JOB_ID'],'gpu_peak_mb':torch.cuda.max_memory_allocated()/2**20}
    dest=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE/'units'
    B.write(dest/f'{unit["id"]}.json',output)
    print(unit['id'],'complete',round(time.time()-started,1),'probe',probe,flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');ap.add_argument('--unit')
    ap.add_argument('--probe-root',type=Path);ap.add_argument('--smoke-receipt',type=Path)
    args=ap.parse_args();assert os.environ.get('SLURM_JOB_ID'),'Slurm required';os.umask(0o077)
    if args.make_plan: make_plan();return
    plan=json.loads(PLAN.read_text());verify(plan)
    if args.unit:
        run_unit(next(x for x in plan['rows'] if x['id']==args.unit),args.probe_root);return
    if args.probe_root:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for ds in ('fau','federici'):
                unit=next(x for x in plan['rows'] if x['dataset']==ds and ready(x,args.probe_root))
                run_unit(unit,args.probe_root);receipt['units'].append(unit['id'])
            receipt.update(status='pass')
        except BaseException:
            receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally: B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    receipt=json.loads(args.smoke_receipt.read_text());assert receipt['status']=='pass' and receipt['plan_sha256']==B.sha(PLAN)
    for unit in plan['rows']:
        if not ready(unit) or (BASE/'units'/f'{unit["id"]}.json').exists():continue
        lock=BASE/'claims'/f'{unit["id"]}.lock';lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            rc=subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.breadth_fusion','--unit',unit['id']]).returncode
            if rc:
                B.write(BASE/'units'/f'{unit["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('fusion unit failed')


if __name__=='__main__':main()
