"""Late-bound frozen prior sources for public envelope/time and private science."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
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

from .. import core
from ..prior33 import contract as C, model as M, views as V, target_train as TT, run_target as RT
from . import learning_budget as B, content_time as T, private_current_time as P, prior_private_loo as R

ROOT=Path(core.REPO);SOURCE=Path(core.OUT)
BASE=SOURCE/'aln34/prior_science_v1';PLAN=BASE/'plan.json'
NOTE=SOURCE/'aln34/PRIOR_SCIENCE_DESIGN_20261017.md'
STORE=Path('<private checkpoint storage>/auditory_alignment_v3/aln34/prior_science_v1')
WINDOWS={'full':None,'0_200':(0,200),'200_400':(200,400),'400_600':(400,600)}

def read(p):return json.loads(Path(p).read_text())
def now():return datetime.now().astimezone().isoformat()
def slot(row):return TT.arm_of(row)[0]

def sources():
    files={Path(__file__),NOTE,Path(T.__file__),Path(P.__file__),Path(R.__file__)}
    files.update(ROOT/p for p in T.sources());files.update(ROOT/p for p in P.sources());files.update(ROOT/p for p in R.sources())
    return {str(p.relative_to(ROOT)):B.sha(p) for p in sorted(files)}

def register():
    rows=[]
    for r in R.all_rows():
        if r['family_id']!='ALN32_PUBLIC_AUDIO_PRIOR_TARGET' or r['seed']!=3401 or r['spec'].get('block')!='core':continue
        assert slot(r) in ('S','AP','XP','J*','XM') and r['spec']['objective'] in ('NCE','CS_SINGLE')
        u={'source':r,'design_sha256':B.sha(NOTE),'config':[slot(r),r['spec']['objective']]}
        u['id']='ALN34PS_'+hashlib.sha256(B.dumps(u).encode()).hexdigest()[:16];rows.append(u)
    rows.sort(key=lambda u:(u['source']['dataset'],u['source']['subject_fold'],u['source']['content_fold'],u['config']))
    assert len(rows)==len({u['id'] for u in rows})==300,len(rows)
    v={'version':'ALN34_PRIOR_SCIENCE_v1','created':now(),'rows':rows,'sources':sources(),'store':str(STORE)}
    if PLAN.exists():assert all(read(PLAN)[k]==x for k,x in v.items() if k!='created')
    else:B.write(PLAN,v);PLAN.chmod(0o444)
    STORE.mkdir(parents=True,exist_ok=True,mode=0o700)
    print('Registered300 prior science evaluations',B.sha(PLAN),flush=True)

def verify(plan):assert plan['sources']==sources(),'frozen prior science source drift'

def mask64(patches,bt,window):
    if window is None:return patches
    lo,hi=(int(round(v*C.FS/1000)) for v in window)
    out=[]
    for x,(a,b) in zip(patches,bt.W):
        offsets=torch.arange(a,b,device=x.device)
        out.append(x*((offsets>=lo)&(offsets<hi)).to(x.dtype)[None,None,:])
    return out

def public_offsets(probe=False):
    offs=np.rint(np.linspace(.8,3.6,3 if probe else 8)*C.FS).astype(int)
    for ms in T.CENTERS:
        ix=offs+round(ms*C.FS/1000)
        assert ix.min()>=1 and (ix+C.L_IN).max()<=5*C.FS
    assert (offs-round(.5*C.FS)).min()>=0
    return offs

def binding(unit,source,probe):
    r=unit['source'];eid=r['experiment_id'];p=source/'units'/f'{eid}.json';cp=source/'ckpt'/f'{eid}_best.pt';rec=read(p)
    assert rec['status']=='complete' and rec['row']==r and (probe or not rec.get('truncated'))
    assert rec['code_hash']==core.code_hash(r['family_id'])
    return dict(unit,record_sha256=B.sha(p),checkpoint_sha256=B.sha(cp))

def cache_destination(unit,probe):
    return STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'cache')/unit['id']

def cache_read(unit,probe):
    dest=cache_destination(unit,probe);path=dest/'meta.json'
    if not path.exists():return None
    meta=read(path);assert meta['unit']==unit and meta['plan_sha256']==B.sha(PLAN) and meta['probe']==probe
    assert meta['array_sha256']==B.sha(dest/'arrays.npz')
    with np.load(dest/'arrays.npz',allow_pickle=False) as z:return {k:z[k] for k in z.files},meta

def cache_write(unit,probe,arrays,meta):
    dest=cache_destination(unit,probe);dest.mkdir(parents=True,exist_ok=True,mode=0o700)
    tmp=dest/'arrays.tmp.npz';np.savez_compressed(tmp,**arrays);os.replace(tmp,dest/'arrays.npz')
    meta.update(unit=unit,probe=probe,plan_sha256=B.sha(PLAN),array_sha256=B.sha(dest/'arrays.npz'))
    B.write(dest/'meta.json',meta);return arrays,meta

def public_rebuild(unit):
    row=unit['source'];manifest=RT.open_manifest(row);coh=V.target_view(row['dataset'],row['content_fold'],manifest,'A')
    stim=coh.stim;dev=torch.device('cuda');b=TT.bind(row)
    bt=V.TickBatcher(coh,b['spec'],b,dev,manifest)
    model=M.build_shared(coh.layout,coh.layout,row['seed']).to(dev)
    sd=torch.load(Path(core.OUT)/'ckpt'/f'{row["experiment_id"]}_best.pt',map_location=dev,weights_only=False)
    model.load_state_dict(sd['enc'],strict=True);model.requires_grad_(False).eval()
    return row,coh,stim,bt,model

@torch.no_grad()
def public_extract(unit,probe=False):
    hit=cache_read(unit,probe)
    if hit is not None:return hit
    row,coh,stim,bt,model=public_rebuild(unit)
    train=[s for s in coh.segments if s['p'] in bt.train_p and s['role'] in ('fit','es') and s['kind']=='ss']
    rng=np.random.default_rng(row['seed']+44000);selected=[train[i] for i in rng.choice(len(train),size=min(400,len(train)),replace=False)]
    if probe:selected=[s for s in selected if s['role']=='fit'][:10]+[s for s in selected if s['role']=='es'][:10]
    people=V.test_queries(coh,row['subject_fold'],'ss')
    if probe:people=people[:1]
    assert not set(people)&set(bt.train_p)
    test=[]
    for p in people:
        items=sorted([s for s in coh.segments if s['p']==p and s['role']=='test' and s['kind']=='ss'],key=lambda s:s['e0'])
        test.extend(items[:2] if probe else items)
    assert test
    items=selected+test;offs=public_offsets(probe);nt=len(offs)
    e=np.array([s['e0'] for s in items]);a=np.array([s['s0'] for s in items]);idx=(a[:,None]+offs).reshape(-1)
    env=np.asarray(stim['envelope'])[0]
    arrays={'role':np.repeat([s['role'] for s in items],nt),'person':np.repeat([coh.participants[s['p']]['id'] for s in items],nt),
            'segment':np.repeat(np.arange(len(items)),nt),'source_segment_e0':e,'anchor_offsets':offs,
            'target_env':env[idx,None].astype(np.float64),'target_onset':np.maximum(env[idx]-env[idx-1],0)[:,None].astype(np.float64),
            'env_history':np.stack([env[idx-round(ms*C.FS/1000)] for ms in (20,100,200,500)],axis=1).astype(np.float64)}
    starts=np.repeat(e,nt);anchors=np.tile(offs,len(e));access={}
    for ms in T.CENTERS:
        shift=round(ms*C.FS/1000);out=[];raw=[]
        for start in range(0,len(starts),64):
            ix=torch.as_tensor(starts[start:start+64]+anchors[start:start+64]+shift,device=bt.dev)
            out.append(model(bt.patches(ix)).cpu().numpy())
            raw.append(bt.E[:,ix[:,None]+torch.arange(-1,1,device=bt.dev)[None]].float().mean(-1).T.cpu().numpy())
        arrays[f'model_{ms}']=np.concatenate(out);arrays[f'raw_{ms}']=np.concatenate(raw)
        access[str(ms)]={'start_sample':shift,'stop_sample_exclusive':shift+C.L_IN,'start_ms':shift/C.FS*1000,'stop_ms_exclusive':(shift+C.L_IN)/C.FS*1000}
    meta={'fs':C.FS,'groups':{p['id']:p['group'] for p in coh.participants},'n_training_segments':len(selected),'n_test_segments':len(test),
          'actual_model_access':access,'raw_sample_offsets':[-1,0],'raw_span_ms':2/C.FS*1000,'source_view':coh.meta,'n_anchors_per_segment':nt}
    result=cache_write(unit,probe,arrays,meta);del bt,model,coh,stim;gc.collect();torch.cuda.empty_cache();return result

@torch.no_grad()
def private_extract(unit,kids,probe=False):
    hit=cache_read(unit,probe)
    if hit is not None:return hit
    row=unit['source'];enc,_,rec,bt=R.rebuild(row,kids,torch.device('cuda'));arrays={}
    for window,bounds in WINDOWS.items():
        for i,k in enumerate(kids):
            out=[]
            for start in range(0,len(k['y']),128):
                idx=torch.arange(start,min(start+128,len(k['y'])),device=bt.dev)
                out.append(enc(mask64(bt.patches(i,idx),bt,bounds)).cpu().numpy())
            arrays[f'{window}_{i}']=np.concatenate(out)
    meta={'device':torch.cuda.get_device_name(0),'children':{str(i):k['id'] for i,k in enumerate(kids)},'windows_ms':WINDOWS,
          'onset_sample':C.ONSET64,'input_samples':list(C.PRIVATE_WIN),'sample_times_ms':[(i-C.ONSET64)/C.FS*1000 for i in range(*C.PRIVATE_WIN)],
          'recipe':rec.get('resolved_config')}
    result=cache_write(unit,probe,arrays,meta);del enc,bt;gc.collect();torch.cuda.empty_cache();return result

@contextmanager
def bindings(source,dest):
    from auditory_alignment import data
    old=(core.OUT,P.BASE,P.PLAN,P.STORE,P.WINDOWS,P.extract,data.load_private)
    loader=data.load_private
    core.OUT=str(source);P.BASE=dest;P.PLAN=PLAN;P.STORE=STORE;P.WINDOWS=WINDOWS;P.extract=private_extract
    data.load_private=lambda:V.load_private64(loader())
    try:yield
    finally:core.OUT,P.BASE,P.PLAN,P.STORE,P.WINDOWS,P.extract,data.load_private=old

def run_unit(unit,probe_source=None):
    start=time.time();probe=probe_source is not None;source=Path(probe_source) if probe else SOURCE
    bound=binding(unit,source,probe);dest=BASE/'probes'/os.environ['SLURM_JOB_ID'] if probe else BASE
    bp=dest/'bindings'/f'{unit["id"]}.json'
    if bp.exists():assert read(bp)==bound
    else:B.write(bp,bound);bp.chmod(0o444)
    with bindings(source,BASE):
        if unit['source']['dataset']=='private_bdf':
            P.run_unit(bound,probe)
            path=(dest if probe else BASE/'units')/f'{unit["id"]}.json';out=read(path)
            out['limitations']=['64Hz private prior input0..578.125ms','masked input sensitivity, not neural latency',
                               'source-ES readout development; fixed support update candidates','single representative seed3401']
        else:
            arrays,meta=public_extract(bound,probe);results=T.analyse(arrays)
            out={'status':'complete','unit':bound,'probe':probe,'plan_sha256':B.sha(PLAN),'metadata':meta,**results,
                 'seconds':time.time()-start,'job':os.environ['SLURM_JOB_ID'],'gpu_peak_mb':torch.cuda.max_memory_allocated()/2**20}
            path=(dest if probe else BASE/'units')/f'{unit["id"]}.json'
        out['binding_sha256']=B.sha(bp);B.write(path,out)
    print(unit['id'],'complete',round(time.time()-start,1),'probe',probe,flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--register',action='store_true');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--unit');ap.add_argument('--smoke-job');ap.add_argument('--max-units',type=int,default=2)
    a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.register:register();return
    plan=read(PLAN);verify(plan)
    if a.unit:run_unit(next(u for u in plan['rows'] if u['id']==a.unit));return
    if a.smoke:
        receipt={'status':'running','plan_sha256':B.sha(PLAN),'units':[]}
        try:
            for ds,obj in (('dtu','NCE'),('dtu','CS_SINGLE'),('federici','NCE'),('private_bdf','NCE'),('private_bdf','CS_SINGLE')):
                u=next(u for u in plan['rows'] if u['source']['dataset']==ds and u['config']==['S',obj])
                source=BASE/'probes'/os.environ['SLURM_JOB_ID']/'source'
                RT.run(u['source'],str(source),epochs=2,device='cuda',rows=R.all_rows())
                run_unit(u,source);receipt['units'].append(u['id'])
            receipt['status']='pass'
        except BaseException:receipt.update(status='failed',traceback=traceback.format_exc());raise
        finally:B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',receipt)
        return
    r=read(BASE/'probes'/str(a.smoke_job)/'receipt.json');assert r['status']=='pass' and r['plan_sha256']==B.sha(PLAN)
    assert not list((BASE/'units').glob('*.FAILED.json'))
    done=0
    for u in plan['rows']:
        path=BASE/'units'/f'{u["id"]}.json'
        if path.exists() or not R.ready(u['source']):continue
        lock=BASE/'claims'/f'{u["id"]}.lock';lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as f:
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            if path.exists():continue
            rc=subprocess.run([sys.executable,'-B','-u','-m','auditory_alignment_v3.aln34.prior_science','--unit',u['id']]).returncode
            if rc or not path.exists() or read(path).get('status')!='complete':
                B.write(BASE/'units'/f'{u["id"]}.FAILED.json',{'job':os.environ['SLURM_JOB_ID'],'returncode':rc});raise RuntimeError('prior science failed')
            done+=1
        if done>=a.max_units:break

if __name__=='__main__':main()
